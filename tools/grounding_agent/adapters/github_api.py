"""Read-only GitHub adapter (REST GET only).

The transport is a plain callable ``(url, headers) -> HttpResponse``. Because
the signature has no HTTP-method parameter, the adapter is structurally
incapable of issuing anything other than a GET: there is no code path for
POST/PATCH/PUT/DELETE (D1). The default transport uses the standard library.

Tests inject a fake transport so no network access is required.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

GITHUB_API_ROOT = "https://api.github.com"


@dataclass
class HttpResponse:
    """Minimal HTTP response returned by a transport."""

    status_code: int
    body: str

    def json(self) -> Any:
        return json.loads(self.body)


# A transport takes a URL and headers and returns an HttpResponse. No method
# argument exists, so only GETs can be expressed.
Transport = Callable[[str, Dict[str, str]], HttpResponse]


class GitHubError(RuntimeError):
    """Base class for GitHub adapter failures."""


class GitHubAuthError(GitHubError):
    """No usable token, or GitHub rejected the credentials (401/403)."""


class GitHubUnavailable(GitHubError):
    """Network failure, 5xx, or a malformed/undecodable response body."""


class GitHubNotFound(GitHubError):
    """The requested resource returned 404."""


def _default_transport(url: str, headers: Dict[str, str]) -> HttpResponse:
    """Standard-library GET. Never sets a method other than GET."""
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:  # noqa: S310 (https only)
            charset = resp.headers.get_content_charset() or "utf-8"
            return HttpResponse(status_code=resp.status, body=resp.read().decode(charset))
    except urllib.error.HTTPError as exc:  # non-2xx
        try:
            body = exc.read().decode("utf-8")
        except Exception:  # pragma: no cover - defensive
            body = ""
        return HttpResponse(status_code=exc.code, body=body)
    except urllib.error.URLError as exc:  # DNS/connection failure
        raise GitHubUnavailable(f"GitHub request failed: {exc}") from exc


class GitHubAdapter:
    """Read-only GitHub REST access limited to ref and PR metadata."""

    def __init__(
        self,
        token: Optional[str] = None,
        *,
        transport: Optional[Transport] = None,
        api_root: str = GITHUB_API_ROOT,
    ) -> None:
        self._token = token if token is not None else (
            os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        )
        self._transport = transport or _default_transport
        self._api_root = api_root.rstrip("/")

    # -- internal ---------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "grounding-agent/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get(self, path: str) -> Dict[str, Any]:
        if not self._token:
            # A material GitHub claim without credentials must BLOCK, never
            # silently fall back to a stale assumption.
            raise GitHubAuthError("no GITHUB_TOKEN/GH_TOKEN available for GitHub read")
        url = f"{self._api_root}{path}"
        try:
            resp = self._transport(url, self._headers())
        except GitHubUnavailable:
            raise
        except Exception as exc:  # unexpected transport failure
            raise GitHubUnavailable(f"transport error: {exc}") from exc

        if resp.status_code in (401, 403):
            raise GitHubAuthError(f"GitHub auth failed (HTTP {resp.status_code})")
        if resp.status_code == 404:
            raise GitHubNotFound(f"not found (HTTP 404): {path}")
        if resp.status_code >= 500:
            raise GitHubUnavailable(f"GitHub server error (HTTP {resp.status_code})")
        if resp.status_code >= 300:
            raise GitHubUnavailable(f"unexpected GitHub status HTTP {resp.status_code}")
        try:
            data = resp.json()
        except Exception as exc:
            raise GitHubUnavailable(f"malformed GitHub JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise GitHubUnavailable("unexpected GitHub payload shape (expected object)")
        return data

    # -- read operations --------------------------------------------------

    def get_pull_request(self, repo: str, number: int) -> Dict[str, Any]:
        """GET /repos/{repo}/pulls/{number}. Raises on auth/unavailable/not-found."""
        return self._get(f"/repos/{repo}/pulls/{number}")

    def get_ref(self, repo: str, ref: str) -> Dict[str, Any]:
        """GET /repos/{repo}/commits/{ref}. Raises on auth/unavailable/not-found."""
        return self._get(f"/repos/{repo}/commits/{ref}")
