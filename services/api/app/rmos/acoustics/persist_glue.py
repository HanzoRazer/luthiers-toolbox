from __future__ import annotations

import json
import os
import shutil
import uuid
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .importer import ImportPlan
from .schemas_manifest_v1 import TapToneBundleManifestV1


# Defaults align with your existing RMOS attachments env convention
RUNS_ROOT_DEFAULT = "services/api/data/runs_v2"
ATTACHMENTS_ROOT_DEFAULT = "services/api/data/run_attachments"
INDEX_FILENAME = "_index.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_partition(iso_utc: str) -> str:
    # iso_utc: "YYYY-MM-DDTHH:MM:SSZ"
    return iso_utc.split("T", 1)[0]


def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _json_dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _get_runs_root() -> Path:
    return Path(os.getenv("RMOS_RUNS_ROOT", RUNS_ROOT_DEFAULT)).expanduser().resolve()


def _get_attachments_root() -> Path:
    return Path(os.getenv("RMOS_RUN_ATTACHMENTS_DIR", ATTACHMENTS_ROOT_DEFAULT)).expanduser().resolve()


def _sharded_path(attachments_root: Path, sha256_hex: str, ext: str) -> Path:
    shard1 = sha256_hex[:2]
    shard2 = sha256_hex[2:4]
    # ext should include dot or be ""
    return attachments_root / shard1 / shard2 / f"{sha256_hex}{ext}"


def _safe_ext_from_relpath(relpath: str) -> str:
    # Preserve extension for convenience (.wav, .json, .csv, .png), empty if none.
    # We do not trust relpath for directories; only take suffix of final component.
    name = relpath.replace("\\", "/").split("/")[-1]
    p = Path(name)
    return p.suffix if p.suffix else ""


@dataclass(frozen=True)
class PersistResult:
    run_id: str
    run_json_path: Path
    date_partition_dir: Path
    attachments_written: int
    attachments_deduped: int
    index_updated: bool


def persist_import_plan(
    *,
    plan: ImportPlan,
    # Where to read actual bundle files from:
    # Expect exporter pack layout:
    #   <package_root>/manifest.json
    #   <package_root>/attachments/<relpath...>
    package_root: Path,
    # Optional manifest object if already parsed upstream
    manifest: Optional[TapToneBundleManifestV1] = None,
    # Run lifecycle fields
    status: str = "completed",
) -> PersistResult:
    """
    Consume ImportPlan and persist into RMOS runs_v2 split store.

    This function assumes:
      - package_root contains "attachments/" subdir with original relpaths
      - attachments are addressed by plan.attachments[*].sha256 and relpath
      - we verify sha256 matches file content before storing
    """
    runs_root = _get_runs_root()
    attachments_root = _get_attachments_root()
    runs_root.mkdir(parents=True, exist_ok=True)
    attachments_root.mkdir(parents=True, exist_ok=True)

    attachments_dir = package_root / "attachments"
    if not attachments_dir.exists() or not attachments_dir.is_dir():
        raise FileNotFoundError(f"Expected attachments/ dir under package_root: {attachments_dir}")

    # If manifest not provided, try to load from package_root/manifest.json
    manifest_path = package_root / "manifest.json"
    if manifest is None and manifest_path.exists():
        manifest = TapToneBundleManifestV1.model_validate(_json_load(manifest_path))

    created_at = _utc_now_iso()
    date_dir = runs_root / _date_partition(created_at)
    date_dir.mkdir(parents=True, exist_ok=True)

    run_id = uuid.uuid4().hex  # stable id for this persisted run
    run_json_path = date_dir / f"run_{run_id}.json"

    # Persist attachments into content-addressed store
    written = 0
    deduped = 0

    # Optional: store the manifest.json itself as an attachment and include it
    attachments_payload = list(plan.attachments)

    if plan.include_manifest_as_attachment and manifest_path.exists():
        manifest_sha = _sha256_file(manifest_path)
        attachments_payload.append({
            "sha256": manifest_sha,
            "relpath": "manifest.json",
            "bytes": manifest_path.stat().st_size,
            "mime": "application/json",
            "kind": "manifest",
            "point_id": None,
        })

    # Copy each attachment by sha into sharded path, verifying hash.
    for a in attachments_payload:
        sha = a["sha256"]
        relpath = a.get("relpath") or ""
        ext = _safe_ext_from_relpath(relpath)

        # Find source file in package
        src = manifest_path if relpath == "manifest.json" else (attachments_dir / relpath)
        if not src.exists() or not src.is_file():
            raise FileNotFoundError(f"Attachment source missing: {src} (relpath={relpath})")

        # Verify sha256
        actual_sha = _sha256_file(src)
        if actual_sha != sha:
            raise ValueError(f"SHA mismatch for {relpath}: manifest={sha} actual={actual_sha}")

        dst = _sharded_path(attachments_root, sha, ext)
        if dst.exists():
            deduped += 1
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            # Copy bytes atomically-ish: write temp then replace
            tmp = dst.with_suffix(dst.suffix + ".tmp")
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)
            written += 1

    # Build run JSON pointer
    # Keep this compatible with your described shape: metadata + attachments list.
    run_obj: Dict[str, Any] = {
        "run_id": run_id,
        "created_at": created_at,
        "status": status,
        # Merge in plan.run_meta fields (mode, tool_id, event_type, bundle_id, etc.)
        **plan.run_meta,
        # Canonical attachment refs: include sha + relpath + kind (+ optional fields)
        "attachments": attachments_payload,
    }

    _json_dump(run_json_path, run_obj)

    # Update _index.json (best effort; safe if missing/corrupt)
    index_updated = _update_index(
        runs_root=runs_root,
        run_obj=run_obj,
        run_json_path=run_json_path,
    )

    return PersistResult(
        run_id=run_id,
        run_json_path=run_json_path,
        date_partition_dir=date_dir,
        attachments_written=written,
        attachments_deduped=deduped,
        index_updated=index_updated,
    )


def _update_index(*, runs_root: Path, run_obj: Dict[str, Any], run_json_path: Path) -> bool:
    """
    Minimal global index cache. Keeps fast filter metadata.
    Format:
      {
        "version": 1,
        "updated_at": "...Z",
        "runs": [
          { "run_id": ..., "created_at": ..., "mode": ..., "tool_id": ..., "path": "YYYY-MM-DD/run_<id>.json", ... }
        ]
      }
    """
    idx_path = runs_root / INDEX_FILENAME
    rel_path = str(run_json_path.relative_to(runs_root)).replace("\\", "/")

    entry = {
        "run_id": run_obj.get("run_id"),
        "created_at": run_obj.get("created_at"),
        "status": run_obj.get("status"),
        "mode": run_obj.get("mode"),
        "event_type": run_obj.get("event_type"),
        "tool_id": run_obj.get("tool_id"),
        "app_version": run_obj.get("app_version"),
        "bundle_id": run_obj.get("bundle_id"),
        "bundle_sha256": run_obj.get("bundle_sha256"),
        "instrument_id": (run_obj.get("instrument") or {}).get("instrument_id"),
        "build_stage": (run_obj.get("instrument") or {}).get("build_stage"),
        "path": rel_path,
        "attachments_count": len(run_obj.get("attachments", [])),
    }

    try:
        if idx_path.exists():
            idx = _json_load(idx_path)
            if not isinstance(idx, dict):
                idx = {}
        else:
            idx = {}

        runs = idx.get("runs")
        if not isinstance(runs, list):
            runs = []

        # Replace if run_id already present (shouldn't happen, but safe)
        runs = [r for r in runs if r.get("run_id") != entry["run_id"]]
        runs.append(entry)

        idx_out = {
            "version": int(idx.get("version", 1)),
            "updated_at": _utc_now_iso(),
            "runs": runs,
        }
        _json_dump(idx_path, idx_out)
        return True
    except Exception:
        # Index is best-effort; do not fail ingestion because of cache.
        return False
