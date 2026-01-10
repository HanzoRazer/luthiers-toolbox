"""
Diff Attachments Helper

Fixes "diff is truncated" by:
  - Returns bounded preview inline
  - Persists full diff to content-addressed attachments when large
  - Returns sha256 pointer so UI can download full diff via /diff/download/{sha256}

The diff is stored content-addressed (by SHA256) and retrievable via
GET /api/rmos/runs/diff/download/{sha256} - does not require run ownership.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


DIFF_PREVIEW_MAX_CHARS_DEFAULT = 20_000


@dataclass
class DiffAttachmentResult:
    """Result of diff attachment persistence."""
    preview: str
    truncated: bool
    full_bytes: int
    attachment_sha256: Optional[str] = None
    attachment_filename: Optional[str] = None


def _safe_str(x: Any) -> str:
    """Safely convert value to string."""
    if x is None:
        return ""
    return x if isinstance(x, str) else str(x)


def _make_filename(left_id: str, right_id: str) -> str:
    """Generate stable, safe filename for diff attachment."""
    # Sanitize IDs to be filesystem-safe
    left_safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in left_id)[:32]
    right_safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in right_id)[:32]
    return f"diff_{left_safe}__{right_safe}.diff"


def _serialize_diff_for_attachment(diff_result: Dict[str, Any]) -> str:
    """
    Serialize structured diff result to text for attachment storage.
    
    Uses pretty-printed JSON for human readability.
    """
    return json.dumps(diff_result, indent=2, sort_keys=True, ensure_ascii=False, default=str)


def persist_diff_as_attachment_if_needed(
    *,
    left_id: str,
    right_id: str,
    diff_result: Dict[str, Any],
    preview_max_chars: int = DIFF_PREVIEW_MAX_CHARS_DEFAULT,
    force_attachment: bool = False,
) -> DiffAttachmentResult:
    """
    Persist large diffs as content-addressed attachments.

    Args:
        left_id: Left run artifact ID (a)
        right_id: Right run artifact ID (b)
        diff_result: Structured diff from diff_runs()
        preview_max_chars: Max chars to include in preview
        force_attachment: Always persist as attachment even if small

    Returns:
        DiffAttachmentResult with preview and optional attachment pointer.
        If truncated, attachment is stored content-addressed and retrievable
        via GET /api/rmos/runs/diff/download/{sha256}
    """
    from .attachments import put_bytes_attachment

    # Serialize diff to text
    diff_text = _serialize_diff_for_attachment(diff_result)
    diff_bytes = diff_text.encode("utf-8", errors="replace")
    full_bytes = len(diff_bytes)

    truncated = force_attachment or (len(diff_text) > preview_max_chars)
    preview = diff_text[:preview_max_chars]

    if not truncated:
        return DiffAttachmentResult(
            preview=preview,
            truncated=False,
            full_bytes=full_bytes,
        )

    # Store full diff content-addressed
    filename = _make_filename(left_id, right_id)
    attachment, _path = put_bytes_attachment(
        data=diff_bytes,
        kind="run_diff",
        mime="application/json",
        filename=filename,
        ext=".diff",
    )

    return DiffAttachmentResult(
        preview=preview,
        truncated=True,
        full_bytes=full_bytes,
        attachment_sha256=attachment.sha256,
        attachment_filename=filename,
    )
