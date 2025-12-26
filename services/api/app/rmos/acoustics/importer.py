from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .schemas_manifest_v1 import TapToneBundleManifestV1, ManifestFileV1


@dataclass(frozen=True)
class ImportPlan:
    """
    A pure planning object describing what the importer will do.

    This is intentionally decoupled from storage IO so:
      - tests can validate deterministic mapping
      - future agents can implement the actual blob-copy + run write
    """
    run_meta: dict[str, Any]
    attachments: list[dict[str, Any]]
    # Optional: include manifest as an attachment reference too (recommended)
    include_manifest_as_attachment: bool = True


def import_acoustics_bundle(
    *,
    manifest: TapToneBundleManifestV1,
    # RMOS-side concerns: caller supplies session/batch context (optional)
    session_id: Optional[str] = None,
    batch_label: Optional[str] = None,
    # Policy knobs:
    analysis_is_derived: bool = True,
) -> ImportPlan:
    """
    ToolBox/RMOS-side importer signature (stable contract).

    Inputs:
      - manifest: TapToneBundleManifestV1 (canonical contract)
      - session_id, batch_label: optional RMOS metadata
      - analysis_is_derived: if True, importer records algorithm_id/analysis_version as derived provenance

    Outputs:
      - ImportPlan with:
          run_meta: dict compatible with "run pointer JSON" shape (runs_v2 philosophy)
          attachments: list of attachment references (sha256 + relpath + kind + mime + bytes + point_id)
        The actual persistence step (copy blobs into content store, write run JSON) is implemented elsewhere.

    Invariants:
      - Run JSON is a pointer (metadata + attachment refs)
      - Attachments are immutable content-addressed by sha256
      - No special casing by Phase 1 vs Phase 3; manifest.files drives everything
    """
    # 1) Flatten attachments from manifest.files
    attachments: list[dict[str, Any]] = []
    for f in manifest.files:
        attachments.append(_manifest_file_to_run_attachment(f))

    # 2) Build stable run_meta "domain block" so tooling stays generic
    acoustics_domain: dict[str, Any] = {}

    if manifest.domain and manifest.domain.acoustics:
        acoustics_domain.update(manifest.domain.acoustics.model_dump(exclude_none=True))

    if analysis_is_derived:
        # Encourage downstream RMOS tooling to treat audio as evidence and analysis as derived.
        # This does not change attachments; it's interpretive metadata.
        acoustics_domain.setdefault("analysis_authority", "derived")
    else:
        acoustics_domain.setdefault("analysis_authority", "authoritative")

    instrument = manifest.instrument.model_dump(exclude_none=True) if manifest.instrument else {}
    provenance = manifest.provenance.model_dump(exclude_none=True) if manifest.provenance else {}

    run_meta: dict[str, Any] = {
        "mode": manifest.mode,  # "acoustics"
        "event_type": manifest.event_type,
        "tool_id": manifest.tool_id,
        "app_version": manifest.app_version,
        "units": manifest.units,  # "mm"

        # Identity + dedupe keys
        "bundle_id": manifest.bundle_id,
        "bundle_sha256": manifest.bundle_sha256,

        # Capture timestamps
        "capture_started_at_utc": manifest.capture_started_at_utc.isoformat().replace("+00:00", "Z"),
        "capture_finished_at_utc": manifest.capture_finished_at_utc.isoformat().replace("+00:00", "Z"),

        # Optional indexing fields
        "instrument": instrument,
        "provenance": provenance,

        # RMOS context (optional)
        "session_id": session_id,
        "batch_label": batch_label,

        # Evolvable domain namespace
        "meta": {
            "acoustics": acoustics_domain,
        },
    }

    return ImportPlan(run_meta=run_meta, attachments=attachments, include_manifest_as_attachment=True)


def _manifest_file_to_run_attachment(f: ManifestFileV1) -> dict[str, Any]:
    """
    Convert one manifest file record into a runs_v2 RunAttachment-like dict.
    Keep this mapping stable.
    """
    return {
        "sha256": f.sha256,
        "relpath": f.relpath,
        "bytes": f.bytes,
        "mime": f.mime,
        "kind": f.kind,
        "point_id": f.point_id,
    }
