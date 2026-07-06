"""ECNU OpenAI-compatible LLM adapter with retry, logging, and cost tracking."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def _resolve_api_key(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    key = os.getenv("ECNU_API_KEY") or os.getenv("OPENAI_API_KEY")
    if key:
        return key
    # Support bare-key .env (single line starting with sk-)
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() in {"ECNU_API_KEY", "OPENAI_API_KEY"}:
                    return v.strip().strip('"').strip("'")
            elif line.startswith("sk-"):
                return line
    return None

DEFAULT_BASE_URL = "https://chat.ecnu.edu.cn/open/api/v1"
DEFAULT_MODEL = "ecnu-plus"


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    latency_ms: float = 0.0

    def add(self, other: "LLMUsage") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        self.calls += other.calls
        self.latency_ms += other.latency_ms


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: LLMUsage
    raw: dict[str, Any] = field(default_factory=dict)


class ECNUClient:
    """Thin wrapper around ECNU's OpenAI-compatible chat API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = DEFAULT_MODEL,
        log_dir: str | Path | None = None,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        request_timeout_s: float = 90.0,
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        if not self.api_key:
            raise ValueError("Missing API key. Set ECNU_API_KEY or OPENAI_API_KEY in .env")
        self.base_url = base_url or os.getenv("ECNU_BASE_URL", DEFAULT_BASE_URL)
        self.model = model
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.request_timeout_s = request_timeout_s
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.request_timeout_s)
        self.log_dir = Path(log_dir) if log_dir else None
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        self.cumulative_usage = LLMUsage()

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        top_p: float = 0.95,
        max_tokens: int = 2048,
        thinking: bool = False,
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        model_name = model or self.model
        kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        if thinking:
            kwargs["extra_body"] = {"thinking": {"type": "enabled"}}

        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                start = time.perf_counter()
                completion = self.client.chat.completions.create(**kwargs)
                latency = (time.perf_counter() - start) * 1000
                content = completion.choices[0].message.content or ""
                usage = LLMUsage(
                    prompt_tokens=getattr(completion.usage, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(completion.usage, "completion_tokens", 0) or 0,
                    total_tokens=getattr(completion.usage, "total_tokens", 0) or 0,
                    calls=1,
                    latency_ms=latency,
                )
                self.cumulative_usage.add(usage)
                raw = completion.model_dump() if hasattr(completion, "model_dump") else {}
                self._log_call(messages, content, usage, model_name, metadata)
                return LLMResponse(content=content, model=model_name, usage=usage, raw=raw)
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_backoff ** attempt)
        raise RuntimeError(f"LLM call failed after {self.max_retries} retries: {last_err}")

    def _log_call(
        self,
        messages: list[dict[str, str]],
        content: str,
        usage: LLMUsage,
        model: str,
        metadata: dict[str, Any] | None,
    ) -> None:
        if not self.log_dir:
            return
        ts = int(time.time() * 1000)
        payload = {
            "timestamp": ts,
            "model": model,
            "messages": messages,
            "response": content,
            "usage": usage.__dict__,
            "metadata": metadata or {},
        }
        path = self.log_dir / f"llm_{ts}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def usage_summary(self) -> dict[str, Any]:
        return self.cumulative_usage.__dict__
