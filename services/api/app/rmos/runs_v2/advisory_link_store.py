"""Advisory Link Store - Extracted from RunStoreV2 for Single Responsibility."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .schemas import RunArtifact, AdvisoryInputRef
from .schemas_advisories import (
    RunAdvisoryLinkV1,
    IndexRunAdvisorySummaryV1,
    IndexAdvisoryLookupV1,
)

_log = logging.getLogger(__name__)


class AdvisoryLinkStore:
    """
    Manages advisory links for run artifacts.

    Extracted from RunStoreV2 to enforce Single Responsibility Principle.
    Advisory links are append-only references that connect runs to AI advisories.

    Responsibilities:
    - Write/read advisory link files (run_{id}_advisory_{id}.json)
    - Maintain global advisory lookup index (_advisory_lookup.json)
    - Maintain per-run advisory rollups in the main index
    - Attach advisory references to runs
    """

    def __init__(
        self,
        root: Path,
        read_index: Callable[[], Dict[str, Dict[str, Any]]],
        write_index: Callable[[Dict[str, Dict[str, Any]]], None],
        get_artifact: Callable[[str], Optional[RunArtifact]],
    ):
        """
        Initialize AdvisoryLinkStore.

        Args:
            root: Root directory for run storage
            read_index: Callback to read the main index
            write_index: Callback to write the main index
            get_artifact: Callback to retrieve a run artifact by ID
        """
        self.root = root
        self._read_index = read_index
        self._write_index = write_index
        self._get_artifact = get_artifact
        self._advisory_lookup_path = root / "_advisory_lookup.json"

    # =========================================================================
    # Advisory Lookup Index
    # =========================================================================

    def _read_advisory_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Read global advisory lookup mapping advisory_id -> entry dict."""
        if not self._advisory_lookup_path.exists():
            return {}
        try:
            txt = self._advisory_lookup_path.read_text(encoding="utf-8")
            obj = json.loads(txt) if txt.strip() else {}
            return obj if isinstance(obj, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_advisory_lookup(self, lookup: Dict[str, Dict[str, Any]]) -> None:
        """Write advisory lookup atomically."""
        tmp = self._advisory_lookup_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(lookup, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(str(tmp), str(self._advisory_lookup_path))

    def _upsert_advisory_lookup(self, entry: IndexAdvisoryLookupV1) -> None:
        """Add or update an entry in the advisory lookup."""
        lookup = self._read_advisory_lookup()
        lookup[entry.advisory_id] = entry.dict()
        self._write_advisory_lookup(lookup)

    # =========================================================================
    # Per-Run Advisory Rollup
    # =========================================================================

    def _append_run_advisory_rollup(
        self, run_id: str, summary: IndexRunAdvisorySummaryV1
    ) -> None:
        """Store run-local advisory summaries in _index.json for fast listing."""
        index = self._read_index()
        meta = index.get(run_id) or {}
        advs = meta.get("advisories") or []
        existing_ids = {a.get("advisory_id") for a in advs if isinstance(a, dict)}
        if summary.advisory_id not in existing_ids:
            advs.append(summary.dict())
            meta["advisories"] = advs
            index[run_id] = meta
            self._write_index(index)

    # =========================================================================
    # Advisory Link CRUD
    # =========================================================================

    def put_advisory_link(self, link: RunAdvisoryLinkV1) -> None:
        """
        Append-only: write a run_{run_id}_advisory_{advisory_id}.json link file.

        Also updates:
        - Run-local rollup in _index.json
        - Global advisory lookup
        """
        # Get artifact to determine partition
        artifact = self._get_artifact(link.run_id)
        if artifact is None:
            raise FileNotFoundError(f"run_id not found: {link.run_id}")

        created = getattr(artifact, "created_at_utc", None)
        if created is None:
            raise ValueError("run artifact missing created_at_utc")

        # Get date partition
        try:
            date_part = created.date().isoformat()
        except (AttributeError, TypeError):
            date_part = str(created)[:10]

        part_dir = self.root / date_part
        part_dir.mkdir(parents=True, exist_ok=True)

        # Write link file
        link_path = part_dir / f"run_{link.run_id}_advisory_{link.advisory_id}.json"
        tmp = link_path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(link.dict(), indent=2, sort_keys=True), encoding="utf-8"
        )
        os.replace(str(tmp), str(link_path))

        # Update run-local rollup
        summary = IndexRunAdvisorySummaryV1(
            advisory_id=link.advisory_id,
            sha256=link.advisory_sha256,
            kind=link.kind,
            mime=link.mime,
            size_bytes=link.size_bytes,
            created_at_utc=link.created_at_utc,
            status=link.status,
            tags=link.tags,
            confidence_max=link.confidence_max,
        )
        self._append_run_advisory_rollup(link.run_id, summary)

        # Update global lookup
        lookup_entry = IndexAdvisoryLookupV1(
            advisory_id=link.advisory_id,
            run_id=link.run_id,
            sha256=link.advisory_sha256,
            kind=link.kind,
            mime=link.mime,
            size_bytes=link.size_bytes,
            created_at_utc=link.created_at_utc,
            status=link.status,
            tags=link.tags,
            confidence_max=link.confidence_max,
            bundle_sha256=link.bundle_sha256,
            manifest_sha256=link.manifest_sha256,
        )
        self._upsert_advisory_lookup(lookup_entry)

    def list_run_advisories(self, run_id: str) -> List[Dict[str, Any]]:
        """Fast path: read from _index.json rollup."""
        meta = self._read_index().get(run_id) or {}
        advs = meta.get("advisories") or []
        return [a for a in advs if isinstance(a, dict)] if isinstance(advs, list) else []

    def resolve_advisory(self, advisory_id: str) -> Optional[Dict[str, Any]]:
        """Resolve advisory_id -> lookup entry dict."""
        entry = self._read_advisory_lookup().get(advisory_id)
        return entry if isinstance(entry, dict) else None

    # =========================================================================
    # Advisory Attachment
    # =========================================================================

    def _advisory_link_path(
        self, run_id: str, advisory_id: str, created_at: datetime
    ) -> Path:
        """Get the file path for an advisory link."""
        partition = created_at.strftime("%Y-%m-%d")
        safe = lambda s: s.replace("/", "_").replace(chr(92), "_")
        return self.root / partition / f"{safe(run_id)}_advisory_{safe(advisory_id)}.json"

    def attach_advisory(
        self,
        run_id: str,
        advisory_id: str,
        kind: str = "unknown",
        engine_id: Optional[str] = None,
        engine_version: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[AdvisoryInputRef]:
        """Attach an advisory reference to a run (append-only)."""
        artifact = self._get_artifact(run_id)
        if artifact is None:
            return None

        existing = artifact.advisory_inputs or []
        if any(a.advisory_id == advisory_id for a in existing):
            return next(a for a in existing if a.advisory_id == advisory_id)

        ref = AdvisoryInputRef(
            advisory_id=advisory_id,
            kind=kind,
            engine_id=engine_id,
            engine_version=engine_version,
            request_id=request_id,
        )

        link_path = self._advisory_link_path(run_id, advisory_id, artifact.created_at_utc)
        link_path.parent.mkdir(parents=True, exist_ok=True)

        tmp = link_path.with_suffix(".json.tmp")
        try:
            tmp.write_text(ref.model_dump_json(indent=2), encoding="utf-8")
            os.replace(tmp, link_path)
        except OSError:
            if tmp.exists():
                tmp.unlink()
            raise

        return ref

    def load_advisory_links(
        self, artifact: RunArtifact, partition: Path
    ) -> RunArtifact:
        """Load append-only advisory links for an artifact."""
        safe_id = artifact.run_id.replace("/", "_").replace(chr(92), "_")
        advisory_inputs = list(artifact.advisory_inputs) if artifact.advisory_inputs else []

        for link_path in partition.glob(f"{safe_id}_advisory_*.json"):
            try:
                ref = AdvisoryInputRef.model_validate(
                    json.loads(link_path.read_text(encoding="utf-8"))
                )
                if not any(a.advisory_id == ref.advisory_id for a in advisory_inputs):
                    advisory_inputs.append(ref)
            except (json.JSONDecodeError, ValueError, OSError, KeyError):
                continue

        return artifact.model_copy(update={"advisory_inputs": advisory_inputs})
