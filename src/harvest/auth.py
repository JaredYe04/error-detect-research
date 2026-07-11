"""Resolve GitHub authentication for live harvest.

Accepted (first match wins):
1. Environment ``GH_TOKEN`` or ``GITHUB_TOKEN``
2. ``gh auth token`` (GitHub CLI logged in)

Never print the token value.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthStatus:
    ok: bool
    method: str  # env | gh_cli | none
    login: str | None
    message: str

    @property
    def token_present(self) -> bool:
        return self.ok


def _token_from_env() -> str | None:
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        val = (os.environ.get(key) or "").strip()
        if val:
            return val
    return None


def _token_from_gh_cli() -> tuple[str | None, str | None]:
    try:
        proc = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        if proc.returncode != 0:
            return None, (proc.stderr or proc.stdout or "gh auth token failed").strip()
        tok = (proc.stdout or "").strip()
        return (tok or None), None
    except FileNotFoundError:
        return None, "gh CLI not found on PATH"
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def _gh_login_name() -> str | None:
    try:
        proc = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        if proc.returncode == 0:
            return (proc.stdout or "").strip() or None
    except Exception:  # noqa: BLE001
        return None
    return None


def resolve_github_auth() -> tuple[AuthStatus, str | None]:
    """Return (status, token_or_none). Token is for callers only — never log it."""
    env_tok = _token_from_env()
    if env_tok:
        login = _gh_login_name()
        return (
            AuthStatus(
                ok=True,
                method="env",
                login=login,
                message="Using GH_TOKEN/GITHUB_TOKEN from environment.",
            ),
            env_tok,
        )

    cli_tok, err = _token_from_gh_cli()
    if cli_tok:
        login = _gh_login_name()
        return (
            AuthStatus(
                ok=True,
                method="gh_cli",
                login=login,
                message="Using token from `gh auth token`.",
            ),
            cli_tok,
        )

    return (
        AuthStatus(
            ok=False,
            method="none",
            login=None,
            message=(
                "No GitHub auth. Provide one of:\n"
                "  1) setx GH_TOKEN <classic_pat_with_public_repo_read>\n"
                "  2) gh auth login\n"
                f"Detail: {err or 'no token'}"
            ),
        ),
        None,
    )


def require_auth() -> tuple[AuthStatus, str]:
    status, token = resolve_github_auth()
    if not status.ok or not token:
        raise SystemExit(status.message)
    return status, token
