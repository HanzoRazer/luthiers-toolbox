"""Acoustics router helpers — URL enrichment and pagination utilities."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from .signed_urls import make_signed_query


def signed_urls_enabled() -> bool:
    """If secret is set, signed URLs feature is enabled."""
    return bool(os.getenv("RMOS_SIGNED_URL_SECRET", "").strip())


def enrich_with_urls(
    items: List[Dict[str, Any]],
    *,
    include_urls: bool = False,
    signed_urls: bool = False,
    url_ttl_s: int = 300,
    url_scope: str = "download",
    base_prefix: str = "/api/rmos/acoustics/attachments",
) -> None:
    """Add attachment_url (and optionally signed params) to each item in-place."""
    if not (include_urls or signed_urls):
        return

    for it in items:
        sha = it.get("sha256")
        if not sha:
            continue
        base_path = f"{base_prefix}/{sha}"
        url = base_path

        if signed_urls and signed_urls_enabled():
            method = "HEAD" if url_scope == "head" else "GET"
            download_flag = (url_scope != "head")
            fname = it.get("filename") or None
            params = make_signed_query(
                method=method, path=base_path, sha256=sha,
                ttl_seconds=url_ttl_s, scope=url_scope,
                download=download_flag, filename=fname,
            )
            q_parts = {"expires": params.expires, "sig": params.sig, "scope": params.scope}
            if download_flag:
                q_parts["download"] = "true"
            if fname:
                q_parts["filename"] = fname
            url = f"{base_path}?{urlencode(q_parts)}"

        it["attachment_url"] = url


def apply_cursor_pagination(
    items: List[Dict[str, Any]],
    *,
    cursor: Optional[str],
    limit: int,
    cursor_key: str = "sha256",
) -> tuple:
    """Apply cursor-based pagination. Returns (page, next_cursor)."""
    if cursor:
        pos = next((i for i, it in enumerate(items) if it.get(cursor_key) == cursor), None)
        if pos is not None:
            items = items[pos + 1:]

    page = items[:limit]
    next_cursor = page[-1][cursor_key] if (len(page) == limit and len(items) > limit) else None
    return page, next_cursor
