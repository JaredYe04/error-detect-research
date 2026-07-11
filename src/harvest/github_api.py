"""Thin GitHub REST helpers (token auth). Prefer gh CLI when available."""

from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"


class GitHubClient:
    def __init__(self, token: str, *, user_agent: str = "hsp-agile-harvest") -> None:
        self.token = token
        self.user_agent = user_agent
        self._sleep = 0.4

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": self.user_agent,
        }

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        qs = f"?{urllib.parse.urlencode(params)}" if params else ""
        url = path if path.startswith("http") else f"{API}{path}{qs}"
        if path.startswith("http") and params:
            url = f"{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                time.sleep(self._sleep)
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub HTTP {exc.code} for {url}: {detail[:400]}") from exc

    def search_code(self, query: str, *, per_page: int = 30, page: int = 1) -> dict[str, Any]:
        return self.get_json(
            "/search/code",
            {"q": query, "per_page": per_page, "page": page},
        )

    def search_repos(self, query: str, *, per_page: int = 20, page: int = 1) -> dict[str, Any]:
        return self.get_json(
            "/search/repositories",
            {"q": query, "per_page": per_page, "page": page, "sort": "stars"},
        )

    def get_raw_file(self, full_name: str, path: str, ref: str = "HEAD") -> str:
        # Prefer Contents API (works for private if token allows; public always)
        enc_path = "/".join(urllib.parse.quote(p) for p in path.split("/"))
        meta = self.get_json(f"/repos/{full_name}/contents/{enc_path}", {"ref": ref})
        if isinstance(meta, dict) and meta.get("download_url"):
            req = urllib.request.Request(meta["download_url"], headers=self._headers())
            with urllib.request.urlopen(req, timeout=60) as resp:
                time.sleep(self._sleep)
                return resp.read().decode("utf-8", errors="replace")
        # Fallback raw
        url = f"{RAW}/{full_name}/{ref}/{path}"
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=60) as resp:
            time.sleep(self._sleep)
            return resp.read().decode("utf-8", errors="replace")

    def try_gh_search_code(self, query: str, limit: int = 30) -> list[dict[str, Any]]:
        """Optional faster path via gh CLI (uses same auth)."""
        try:
            proc = subprocess.run(
                [
                    "gh",
                    "search",
                    "code",
                    query,
                    "--limit",
                    str(limit),
                    "--json",
                    "repository,path,url,textMatches",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
                env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
            )
            if proc.returncode != 0:
                return []
            return json.loads(proc.stdout or "[]")
        except Exception:  # noqa: BLE001
            return []
