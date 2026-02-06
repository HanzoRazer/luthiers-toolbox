"""Chladni manifest utilities — append artifacts to run-level manifest."""
from __future__ import annotations
import json, hashlib, os
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable, List

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def append_chladni_to_run_manifest(
    run_dir: str | Path,
    *,
    wav_path: str | Path,
    peaks_json_path: str | Path,
    image_paths: Iterable[str | Path],
    chladni_run_json_path: str | Path,
    manifest_name: str = "manifest.json",
) -> Path:
    """
    Append Chladni artifacts to out/<RUN_ID>/manifest.json, idempotently.
    Uses modes._shared.emit_manifest if available; falls back to a minimal writer.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / manifest_name

    def rel(p: str | Path) -> str:
        return os.path.relpath(Path(p), start=run_dir)

    images: List[Path] = [Path(p) for p in image_paths]
    entries = [
        {"path": rel(wav_path),             "sha256": _sha256_file(Path(wav_path)),             "artifact_type": "chladni_wav"},
        {"path": rel(peaks_json_path),      "sha256": _sha256_file(Path(peaks_json_path)),      "artifact_type": "chladni_peaks"},
        *[
            {"path": rel(ip),               "sha256": _sha256_file(ip),                         "artifact_type": "chladni_image"}
            for ip in sorted(images, key=lambda x: x.name.lower())
        ],
        {"path": rel(chladni_run_json_path),"sha256": _sha256_file(Path(chladni_run_json_path)),"artifact_type": "chladni_run"},
    ]

    # Preferred path: shared manifest utility
    try:
        from modes._shared import emit_manifest  # type: ignore
        doc = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else emit_manifest.new_manifest()
        for e in entries:
            emit_manifest.append_entry(doc, e["path"], e["sha256"], e.get("artifact_type"))
        emit_manifest.save_manifest(doc, manifest_path)
        return manifest_path
    except Exception:
        # Fallback path: minimal manifest writer
        if manifest_path.exists():
            try:
                doc = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                doc = {}
        else:
            doc = {}
        if not isinstance(doc, dict) or "schema_id" not in doc:
            doc = {
                "schema_id": "measurement_manifest",
                "schema_version": "1.0",
                "created_utc": _now_utc_iso(),
                "artifacts": [],
            }
        arts = doc.get("artifacts")
        if not isinstance(arts, list):
            arts = []
            doc["artifacts"] = arts
        existing_paths = {a["path"] for a in arts if isinstance(a, dict) and "path" in a}
        for e in entries:
            if e["path"] not in existing_paths:
                arts.append(e)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        return manifest_path
