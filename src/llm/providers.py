"""Multi-provider OpenAI-compatible LLM configuration (ECNU + N1N).

Resolves API key / base URL from .env:

  ECNU_API_KEY / ECNU_BASE_URL   — campus gateway (default)
  N1N_API_KEY  / N1N_BASE_URL    — commercial aggregator (gpt/claude/gemini/...)
  OPENAI_API_KEY / OPENAI_BASE_URL — optional generic fallback

Provider is inferred from model id unless ``provider=`` is set explicitly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ECNU_DEFAULT_BASE = "https://chat.ecnu.edu.cn/open/api/v1"
N1N_DEFAULT_BASE = "https://api.n1n.ai/v1"
DEFAULT_MODEL = "ecnu-plus"

# Models that always route to the campus gateway
ECNU_MODEL_PREFIXES = ("ecnu-", "educhat-", "InnoSpark", "ChatECNU")

# Heuristic: everything else with a known commercial family → N1N
N1N_MODEL_HINTS = (
    "gpt-",
    "o1",
    "o3",
    "o4",
    "claude",
    "gemini",
    "deepseek",
    "qwen",
    "llama",
    "mistral",
    "grok",
    "command-",
)


@dataclass(frozen=True)
class ProviderConfig:
    name: str  # "ecnu" | "n1n" | "openai"
    api_key: str
    base_url: str


def _read_env_file_key(names: set[str]) -> str | None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() in names:
            return v.strip().strip('"').strip("'")
    return None


def _env_or_file(*names: str) -> str | None:
    for name in names:
        val = os.getenv(name)
        if val:
            return val
    return _read_env_file_key(set(names))


def infer_provider(model: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit.lower().strip()
    m = (model or "").strip()
    if any(m.startswith(p) or m == p for p in ECNU_MODEL_PREFIXES):
        return "ecnu"
    low = m.lower()
    if any(h in low for h in N1N_MODEL_HINTS):
        return "n1n"
    # Default campus for legacy bare ids
    if m in {"", DEFAULT_MODEL} or m.startswith("ecnu"):
        return "ecnu"
    return "n1n"


def resolve_provider(
    *,
    model: str = DEFAULT_MODEL,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> ProviderConfig:
    """Pick provider credentials for a model."""
    name = infer_provider(model, provider)

    if api_key and base_url:
        return ProviderConfig(name=name, api_key=api_key, base_url=base_url)

    if name == "n1n":
        key = api_key or _env_or_file("N1N_API_KEY")
        url = base_url or _env_or_file("N1N_BASE_URL") or N1N_DEFAULT_BASE
        if not key:
            raise ValueError(
                "Missing N1N_API_KEY in .env (required for commercial models via n1n.ai)"
            )
        return ProviderConfig(name="n1n", api_key=key, base_url=url.rstrip("/"))

    if name == "openai":
        key = api_key or _env_or_file("OPENAI_API_KEY")
        url = base_url or _env_or_file("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        if not key:
            raise ValueError("Missing OPENAI_API_KEY")
        return ProviderConfig(name="openai", api_key=key, base_url=url.rstrip("/"))

    # ecnu (default)
    key = api_key or _env_or_file("ECNU_API_KEY", "OPENAI_API_KEY")
    if not key:
        # legacy bare sk- line
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("sk-") and "=" not in line:
                    key = line
                    break
    url = base_url or _env_or_file("ECNU_BASE_URL") or ECNU_DEFAULT_BASE
    if not key:
        raise ValueError(
            "Missing ECNU_API_KEY (or OPENAI_API_KEY / bare sk- line) in .env"
        )
    return ProviderConfig(name="ecnu", api_key=key, base_url=url.rstrip("/"))
