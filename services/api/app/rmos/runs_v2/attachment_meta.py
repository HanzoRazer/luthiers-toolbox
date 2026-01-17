"""
Global sha256 → meta index for RMOS attachments.

Provides content-addressed metadata lookup without requiring run_id.
Tracks ref_count, first/last seen for dedupe-aware storage.

Invariants:
  - No shard path disclosure
  - Immutable blobs, mutable index (like _index.json)
  - Atomic writes (.tmp + os.replace)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .schemas import RunArtifact, RunAttachment


@dataclass(frozen=True)
class AttachmentMeta:
    sha256: str
    kind: str
    mime: str
    filename: str
    size_bytes: int
    created_at_utc: str
    # global index tracking
    first_seen_run_id: str
    last_seen_run_id: str
    first_seen_at_utc: str
    last_seen_at_utc: str
    ref_count: int


def _atomic_write_json(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(str(tmp), str(path))


class AttachmentMetaIndex:
    """
    Global sha256 -> meta index.

    Stored at:
      {runs_root}/_attachment_meta.json

    Shape (top-level dict):
      {
        "<sha256>": {
          "sha256": "...",
          "kind": "...",
          "mime": "...",
          "filename": "...",
          "size_bytes": 123,
          "created_at_utc": "...",
          "first_seen_run_id": "...",
          "last_seen_run_id": "...",
          "first_seen_at_utc": "...",
          "last_seen_at_utc": "...",
          "ref_count": 7
        },
        ...
      }
    """

    def __init__(self, root_dir: Path):
        self.root = root_dir
        self.path = self.root / "_attachment_meta.json"

    def read(self) -> Dict[str, Dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            # If corrupted, fail safe: treat as empty (caller may rebuild later)
            return {}

    def write(self, data: Dict[str, Dict[str, Any]]) -> None:
        _atomic_write_json(self.path, data)

    def get(self, sha256: str) -> Optional[Dict[str, Any]]:
        sha = sha256.lower().strip()
        data = self.read()
        return data.get(sha)

    def list_all(self) -> list:
        """
        Return all index entries as a list of dicts.

        Useful for browse endpoints that need to filter/sort/paginate.
        """
        data = self.read()
        return list(data.values())

    def update_from_artifact(self, artifact: RunArtifact) -> None:
        """
        Update global meta index using attachments referenced by this artifact.

        NOTE: This index is best-effort metadata. The authoritative record of
        "what attachments belong to a run" remains RunArtifact.attachments.
        """
        atts = getattr(artifact, "attachments", None) or []
        if not atts:
            return

        run_id = getattr(artifact, "run_id")
        created_at_utc = str(getattr(artifact, "created_at_utc"))

        idx = self.read()

        for a in atts:
            if not isinstance(a, RunAttachment):
                # Pydantic models still behave like objects; treat generically
                sha = str(getattr(a, "sha256", "")).lower().strip()
                if not sha:
                    continue
                kind = str(getattr(a, "kind", "unknown"))
                mime = str(getattr(a, "mime", "application/octet-stream"))
                filename = str(getattr(a, "filename", "attachment"))
                size_bytes = int(getattr(a, "size_bytes", 0) or 0)
                a_created = str(getattr(a, "created_at_utc", created_at_utc))
            else:
                sha = a.sha256.lower().strip()
                kind = a.kind
                mime = a.mime
                filename = a.filename
                size_bytes = int(a.size_bytes)
                a_created = str(a.created_at_utc)

            existing = idx.get(sha)

            if existing is None:
                idx[sha] = {
                    "sha256": sha,
                    "kind": kind,
                    "mime": mime,
                    "filename": filename,
                    "size_bytes": size_bytes,
                    "created_at_utc": a_created,
                    "first_seen_run_id": run_id,
                    "last_seen_run_id": run_id,
                    "first_seen_at_utc": created_at_utc,
                    "last_seen_at_utc": created_at_utc,
                    "ref_count": 1,
                }
            else:
                # Keep the original "created_at_utc" as stored; update last_seen, ref_count.
                existing["last_seen_run_id"] = run_id
                existing["last_seen_at_utc"] = created_at_utc
                existing["ref_count"] = int(existing.get("ref_count", 0) or 0) + 1

                # If later runs provide better metadata, fill missing/unknown fields.
                if (existing.get("kind") in (None, "", "unknown")) and kind:
                    existing["kind"] = kind
                if (existing.get("mime") in (None, "", "application/octet-stream")) and mime:
                    existing["mime"] = mime
                if (existing.get("filename") in (None, "", "attachment")) and filename:
                    existing["filename"] = filename

                # Prefer non-zero size if missing
                if int(existing.get("size_bytes", 0) or 0) <= 0 and size_bytes > 0:
                    existing["size_bytes"] = size_bytes

                idx[sha] = existing

        self.write(idx)

    def rebuild_from_index(self, run_index: Dict[str, Dict[str, Any]]) -> int:
        """
        Optional utility: rebuild meta index *only from _index.json*, if you stored
        enough attachment info there (often you do not).

        If your _index.json does NOT include attachments, you should not rely on this.
        """
        # left as a stub by design; keep rebuild explicit and safe
        return 0

    def rebuild_from_run_artifacts(self) -> Dict[str, int]:
        """
        Rebuild _attachment_meta.json by scanning authoritative run artifacts on disk.

        Returns stats:
          {
            "runs_scanned": int,
            "attachments_indexed": int,
            "unique_sha256": int
          }
        """
        runs_scanned = 0
        attachments_indexed = 0

        idx: Dict[str, Dict[str, Any]] = {}

        # Date-partitioned directories: {YYYY-MM-DD}/
        # Run artifact files are typically: {YYYY-MM-DD}/{run_id}.json
        # Advisory link files should be ignored: run_{run_id}_advisory_{id}.json (or similar)
        for date_dir in sorted(self.root.iterdir()):
            if not date_dir.is_dir():
                continue
            name = date_dir.name
            # Skip index/meta files that might be directories (defensive)
            if name.startswith("_"):
                continue

            for p in sorted(date_dir.glob("*.json")):
                fn = p.name
                # Ignore advisory link files and any other non-run artifacts
                if "_advisory_" in fn:
                    continue

                try:
                    raw = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue

                # Minimum fields for a run artifact
                run_id = raw.get("run_id")
                created_at_utc = raw.get("created_at_utc")
                atts = raw.get("attachments") or []
                if not run_id or not created_at_utc:
                    continue

                runs_scanned += 1

                for a in atts:
                    try:
                        sha = str(a.get("sha256", "")).lower().strip()
                        if not sha:
                            continue
                        kind = str(a.get("kind", "unknown"))
                        mime = str(a.get("mime", "application/octet-stream"))
                        filename = str(a.get("filename", "attachment"))
                        size_bytes = int(a.get("size_bytes", 0) or 0)
                        a_created = str(a.get("created_at_utc", created_at_utc))
                    except Exception:
                        continue

                    attachments_indexed += 1

                    existing = idx.get(sha)
                    if existing is None:
                        idx[sha] = {
                            "sha256": sha,
                            "kind": kind,
                            "mime": mime,
                            "filename": filename,
                            "size_bytes": size_bytes,
                            "created_at_utc": a_created,
                            "first_seen_run_id": run_id,
                            "last_seen_run_id": run_id,
                            "first_seen_at_utc": str(created_at_utc),
                            "last_seen_at_utc": str(created_at_utc),
                            "ref_count": 1,
                        }
                    else:
                        existing["last_seen_run_id"] = run_id
                        existing["last_seen_at_utc"] = str(created_at_utc)
                        existing["ref_count"] = int(existing.get("ref_count", 0) or 0) + 1

                        # Fill missing/unknown values if improved metadata exists
                        if (existing.get("kind") in (None, "", "unknown")) and kind:
                            existing["kind"] = kind
                        if (existing.get("mime") in (None, "", "application/octet-stream")) and mime:
                            existing["mime"] = mime
                        if (existing.get("filename") in (None, "", "attachment")) and filename:
                            existing["filename"] = filename
                        if int(existing.get("size_bytes", 0) or 0) <= 0 and size_bytes > 0:
                            existing["size_bytes"] = size_bytes

                        idx[sha] = existing

        # Atomic write of rebuilt index
        self.write(idx)

        return {
            "runs_scanned": runs_scanned,
            "attachments_indexed": attachments_indexed,
            "unique_sha256": len(idx),
        }


# =============================================================================
# Facets (Attachment Meta Inventory)
# =============================================================================


@dataclass(frozen=True)
class AttachmentMetaFacets:
    """Facet counts over the attachment meta index."""
    kind: Dict[str, int]
    mime: Dict[str, int]
    total_attachments: int
    index_version: str = "attachment_meta_v1"


def compute_facets(meta_index: "AttachmentMetaIndex") -> AttachmentMetaFacets:
    """
    Compute facet counts from the attachment meta index.

    Index-only operation: no filesystem access, no blob resolution.

    Returns deterministic output with sorted keys.
    """
    entries = meta_index.list_all()

    kind_counts: Dict[str, int] = {}
    mime_counts: Dict[str, int] = {}

    for e in entries:
        k = e.get("kind") or "unknown"
        m = e.get("mime") or "application/octet-stream"

        kind_counts[k] = kind_counts.get(k, 0) + 1
        mime_counts[m] = mime_counts.get(m, 0) + 1

    # Sorted keys for deterministic output
    return AttachmentMetaFacets(
        kind=dict(sorted(kind_counts.items())),
        mime=dict(sorted(mime_counts.items())),
        total_attachments=len(entries),
    )


# =============================================================================
# Recency Index (H7.2.2.3)
# =============================================================================


MAX_RECENT_ENTRIES = 5000  # configurable cap


class AttachmentRecentIndex:
    """
    Precomputed recency index for fast "recent" browsing.

    Stored at:
      {runs_root}/_attachment_recent.json

    Shape:
      {
        "schema_version": "acoustics_attachment_recent_index_v1",
        "max_entries": 5000,
        "built_at_utc": "2026-01-01T01:23:45Z",
        "entries": [ ... ]  # sorted by created_at_utc DESC
      }
    """

    def __init__(self, root_dir: Path, max_entries: int = MAX_RECENT_ENTRIES):
        self.root = root_dir
        self.max_entries = max_entries
        self.path = self.root / "_attachment_recent.json"

    def read(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {
                "schema_version": "acoustics_attachment_recent_index_v1",
                "max_entries": self.max_entries,
                "built_at_utc": None,
                "entries": [],
            }
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "schema_version": "acoustics_attachment_recent_index_v1",
                "max_entries": self.max_entries,
                "built_at_utc": None,
                "entries": [],
            }

    def write(self, data: Dict[str, Any]) -> None:
        _atomic_write_json(self.path, data)

    def list_entries(self) -> list:
        """Return entries from the recent index (already sorted by recency)."""
        data = self.read()
        return data.get("entries", [])

    def rebuild_from_meta_index(self, meta_idx: AttachmentMetaIndex) -> Dict[str, int]:
        """
        Rebuild _attachment_recent.json from _attachment_meta.json.

        Sorts all entries by created_at_utc DESC and keeps top max_entries.

        Returns stats:
          {
            "total_in_meta": int,
            "recent_indexed": int
          }
        """
        from datetime import datetime

        all_entries = meta_idx.list_all()
        total_in_meta = len(all_entries)

        # Sort by created_at_utc descending (most recent first)
        # Handle missing/invalid timestamps gracefully
        def _sort_key(e: Dict[str, Any]) -> str:
            ts = e.get("created_at_utc") or ""
            # Fallback for missing timestamps: use empty string (sorts last)
            return ts if ts else ""

        sorted_entries = sorted(all_entries, key=_sort_key, reverse=True)

        # Keep only top max_entries
        recent_entries = sorted_entries[: self.max_entries]

        # Build output shape (strip tracking fields for compactness)
        compact_entries = []
        for e in recent_entries:
            compact_entries.append({
                "sha256": e.get("sha256"),
                "kind": e.get("kind"),
                "mime": e.get("mime"),
                "filename": e.get("filename"),
                "size_bytes": e.get("size_bytes"),
                "created_at_utc": e.get("created_at_utc"),
            })

        data = {
            "schema_version": "acoustics_attachment_recent_index_v1",
            "max_entries": self.max_entries,
            "built_at_utc": datetime.utcnow().isoformat() + "Z",
            "entries": compact_entries,
        }

        self.write(data)

        return {
            "total_in_meta": total_in_meta,
            "recent_indexed": len(compact_entries),
        }
