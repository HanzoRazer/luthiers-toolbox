from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


DIFF_PREVIEW_MAX_CHARS_DEFAULT = 20_000


@dataclass
class DiffAttachmentResult:
    preview: str
    truncated: bool
    full_bytes: int
    attachment_sha256: Optional[str] = None
    attachment_filename: Optional[str] = None
    attachment_content_type: Optional[str] = None


def _safe_str(x: Any) -> str:
    if x is None:
        return ""
    return x if isinstance(x, str) else str(x)


def _make_filename(left_id: str, right_id: str) -> str:
    # stable + editor-friendly extension
    return f"diff_{left_id}__{right_id}"


def persist_diff_as_attachment_if_needed(
    *,
    left_id: str,
    right_id: str,
    diff_text: str,
    preview_max_chars: int = DIFF_PREVIEW_MAX_CHARS_DEFAULT,
    force_attachment: bool = False,
) -> DiffAttachmentResult:
    """
    Prevents "diff is truncated" permanently:
      - always returns bounded preview inline
      - persists *full* diff to content-addressed attachments when needed
    Uses existing attachment API shape:
      GET /api/rmos/runs/{run_id}/attachments/{sha256}
    """
    from .attachments import put_bytes_attachment

    diff_text = _safe_str(diff_text)
    diff_bytes = diff_text.encode("utf-8", errors="replace")
    full_bytes = len(diff_bytes)

    truncated = bool(force_attachment or (len(diff_text) > int(preview_max_chars)))
    preview = diff_text[: int(preview_max_chars)]

    if not truncated:
        return DiffAttachmentResult(
            preview=preview,
            truncated=False,
            full_bytes=full_bytes,
        )

    # IMPORTANT: put_bytes_attachment signature (known):
    # (data: bytes, kind: str, mime: str, filename: str, ext: str = "") -> Tuple[RunAttachment, str]
    _att, sha256 = put_bytes_attachment(
        diff_bytes,
        kind="run_diff",
        mime="text/plain; charset=utf-8",
        filename=_make_filename(left_id, right_id),
        ext=".diff",
    )

    return DiffAttachmentResult(
        preview=preview,
        truncated=True,
        full_bytes=full_bytes,
        attachment_sha256=sha256,
        attachment_filename=f"{_make_filename(left_id, right_id)}.diff",
        attachment_content_type="text/plain; charset=utf-8",
    )
