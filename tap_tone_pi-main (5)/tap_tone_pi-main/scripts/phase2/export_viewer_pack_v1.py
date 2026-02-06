#!/usr/bin/env python3
"""
Phase 2 Viewer Pack Exporter (viewer_pack_v1)

Input:
  runs_phase2/session_YYYYMMDDTHHMMSSZ/

Output (dir or zip):
  viewer_pack_v1/
    manifest.json
    README.txt
    audio/points/<PID>.wav
    spectra/points/<PID>/spectrum.csv
    spectra/points/<PID>/analysis.json
    provenance/points/<PID>/capture_meta.json
    meta/grid.json
    meta/metadata.json
    ods/ods_snapshot.json
    wolf/wolf_candidates.json
    wolf/wsi_curve.csv
    plots/*.png

Phase 2 assumptions:
  - points live in points/point_<PID>/
  - audio is 2-ch wav (ref=ch0, roving=ch1) kept as-is
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zipfile import ZipFile, ZIP_DEFLATED

# Pre-export validation gate
from tap_tone.validate.viewer_pack_v1 import validate_pack, write_validation_report


# Canonical kind vocabulary (single source of truth)
# ToolBox viewer dispatches on these exact strings
KIND_VOCAB = {
    "audio_raw",
    "spectrum_csv",
    "analysis_peaks",
    "coherence",
    "transfer_function",  # ODS data (ods_snapshot.json)
    "wolf_candidates",
    "wsi_curve",
    "provenance",
    "plot_png",
    "session_meta",
    "manifest",
    "unknown",
}

KIND_BY_RELPATH_RULES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"^audio/points/.+\.wav$", re.I), "audio_raw"),
    (re.compile(r"^spectra/points/.+/spectrum\.csv$", re.I), "spectrum_csv"),
    (re.compile(r"^spectra/points/.+/analysis\.json$", re.I), "analysis_peaks"),
    (re.compile(r"^coherence/.+\.json$", re.I), "coherence"),
    (re.compile(r"^ods/.+\.json$", re.I), "transfer_function"),  # ODS = transfer_function
    (re.compile(r"^wolf/.+candidates\.json$", re.I), "wolf_candidates"),
    (re.compile(r"^wolf/wsi_curve\.csv$", re.I), "wsi_curve"),
    (re.compile(r"^provenance/.+\.json$", re.I), "provenance"),
    (re.compile(r"^plots/.+\.png$", re.I), "plot_png"),
    (re.compile(r"^meta/.+\.json$", re.I), "session_meta"),
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def detect_kind(relpath: str) -> str:
    rp = relpath.replace("\\", "/")
    for pat, kind in KIND_BY_RELPATH_RULES:
        if pat.search(rp):
            return kind
    return "unknown"


def guess_mime(path: Path) -> str:
    mt, _ = mimetypes.guess_type(str(path))
    return mt or "application/octet-stream"


def point_id_from_folder(folder_name: str) -> Optional[str]:
    # point_A1 -> A1
    if folder_name.startswith("point_"):
        return folder_name.split("point_", 1)[1]
    return None


@dataclass
class FileEntry:
    relpath: str
    sha256: str
    bytes: int
    mime: str
    kind: str


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_text(dst: Path, text: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def build_readme(session_dir: Path) -> str:
    return "\n".join([
        "Tap Tone Viewer Pack v1",
        "",
        f"Source session: {session_dir.name}",
        "Contents:",
        "- audio/points/*.wav (2-ch: ch0 reference, ch1 roving)",
        "- spectra/points/*/spectrum.csv (freq_hz,H_mag,coherence,phase_deg)",
        "- spectra/points/*/analysis.json (summary/peaks metadata)",
        "- meta/grid.json + meta/metadata.json",
        "- ods/, wolf/, plots/ as available",
        "",
        "Viewer rule: dispatch by manifest.files[].kind",
        ""
    ])


def export_viewer_pack(
    session_dir: Path,
    out_dir: Path,
    *,
    as_zip: bool,
) -> Path:
    if not session_dir.exists():
        raise FileNotFoundError(f"session_dir not found: {session_dir}")

    # pack root
    pack_root = out_dir / "viewer_pack_v1"
    if pack_root.exists():
        shutil.rmtree(pack_root)
    pack_root.mkdir(parents=True, exist_ok=True)

    files: List[FileEntry] = []

    def add_file(src: Path, relpath: str):
        dst = pack_root / relpath
        copy_file(src, dst)
        entry = FileEntry(
            relpath=relpath.replace("\\", "/"),
            sha256=sha256_file(dst),
            bytes=dst.stat().st_size,
            mime=guess_mime(dst),
            kind=detect_kind(relpath),
        )
        files.append(entry)

    # README
    readme_text = build_readme(session_dir)
    readme_path = pack_root / "README.txt"
    write_text(readme_path, readme_text)
    files.append(FileEntry(
        relpath="README.txt",
        sha256=sha256_file(readme_path),
        bytes=readme_path.stat().st_size,
        mime="text/plain",
        kind="provenance",
    ))

    # session meta
    grid = session_dir / "grid.json"
    metadata = session_dir / "metadata.json"
    if grid.exists():
        add_file(grid, "meta/grid.json")
    if metadata.exists():
        add_file(metadata, "meta/metadata.json")

    # points
    points_dir = session_dir / "points"
    if not points_dir.exists():
        raise FileNotFoundError(f"Phase2 points/ missing: {points_dir}")

    point_ids: List[str] = []

    for point_folder in sorted([p for p in points_dir.iterdir() if p.is_dir()]):
        pid = point_id_from_folder(point_folder.name)
        if not pid:
            continue
        point_ids.append(pid)

        wav = point_folder / "audio.wav"
        cap = point_folder / "capture_meta.json"
        spectrum = point_folder / "spectrum.csv"
        analysis = point_folder / "analysis.json"

        if wav.exists():
            add_file(wav, f"audio/points/{pid}.wav")
        if spectrum.exists():
            add_file(spectrum, f"spectra/points/{pid}/spectrum.csv")
        if analysis.exists():
            add_file(analysis, f"spectra/points/{pid}/analysis.json")
        if cap.exists():
            add_file(cap, f"provenance/points/{pid}/capture_meta.json")

    # derived
    derived_dir = session_dir / "derived"
    if derived_dir.exists():
        ods = derived_dir / "ods_snapshot.json"
        wc = derived_dir / "wolf_candidates.json"
        wsi = derived_dir / "wsi_curve.csv"
        if ods.exists():
            add_file(ods, "ods/ods_snapshot.json")
        if wc.exists():
            add_file(wc, "wolf/wolf_candidates.json")
        if wsi.exists():
            add_file(wsi, "wolf/wsi_curve.csv")

    # coherence (optional separate dir)
    coh_dir = session_dir / "coherence"
    if coh_dir.exists():
        coh = coh_dir / "coherence_summary.json"
        if coh.exists():
            add_file(coh, "coherence/coherence_summary.json")

    # plots
    plots_dir = session_dir / "plots"
    if plots_dir.exists():
        for png in sorted(plots_dir.glob("*.png")):
            add_file(png, f"plots/{png.name}")

    # manifest (schema_version matches contracts/viewer_pack_v1.schema.json)
    manifest: Dict[str, Any] = {
        "schema_version": "v1",
        "schema_id": "viewer_pack_v1",
        "created_at_utc": utc_now_iso(),
        "source_capdir": session_dir.name,
        "detected_phase": "phase2",
        "measurement_only": True,
        "interpretation": "deferred",
        "points": point_ids,
        "contents": {
            "audio": any(e.relpath.startswith("audio/") for e in files),
            "spectra": any(e.relpath.startswith("spectra/") for e in files),
            "coherence": any(e.relpath.startswith("coherence/") for e in files),
            "ods": any(e.relpath.startswith("ods/") for e in files),
            "wolf": any(e.relpath.startswith("wolf/") for e in files),
            "plots": any(e.relpath.startswith("plots/") for e in files),
            "provenance": any(e.relpath.startswith("provenance/") for e in files),
        },
        "files": [
            {
                "relpath": e.relpath,
                "sha256": e.sha256,
                "bytes": e.bytes,
                "mime": e.mime,
                "kind": e.kind,
            }
            for e in sorted(files, key=lambda x: x.relpath)
        ],
    }

    # bundle sha = sha256 of manifest JSON bytes (before adding bundle_sha256)
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    bundle_sha = sha256_bytes(manifest_bytes)

    manifest["bundle_sha256"] = bundle_sha
    manifest_path = pack_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    # ========================================
    # Pre-export validation gate
    # ========================================
    # Manifest uses viewer_pack.json internally but validator expects it
    # Rename for validation compatibility
    viewer_pack_json = pack_root / "viewer_pack.json"
    if not viewer_pack_json.exists():
        shutil.copy2(manifest_path, viewer_pack_json)

    report = validate_pack(pack_root)
    report_path = write_validation_report(pack_root, report)

    if not report.passed:
        excerpt = []
        for e in (report.errors or [])[:3]:
            rule = e.get("rule", "?")
            msg = e.get("message", "")
            path = e.get("path")
            if path:
                excerpt.append(f"{rule}: {msg} ({path})")
            else:
                excerpt.append(f"{rule}: {msg}")

        excerpt_txt = "; ".join(excerpt) if excerpt else "No error details available."
        raise ValueError(
            f"viewer_pack_v1 validation failed: "
            f"errors={len(report.errors)} warnings={len(report.warnings)}. "
            f"{excerpt_txt}. "
            f"See {report_path}"
        )

    # Zip if requested
    if as_zip:
        zip_path = out_dir / f"{session_dir.name}__viewer_pack_v1.zip"
        if zip_path.exists():
            zip_path.unlink()
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as z:
            for fp in pack_root.rglob("*"):
                if fp.is_file():
                    arc = fp.relative_to(pack_root.parent).as_posix()
                    z.write(fp, arcname=arc)
        return zip_path

    return pack_root


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Export Phase 2 session to viewer_pack_v1 format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--session-dir", required=True, help="runs_phase2/session_*/ directory")
    ap.add_argument("--out", required=True, help="output directory for pack or zip")
    ap.add_argument("--zip", action="store_true", help="emit a .zip bundle")
    args = ap.parse_args()

    session_dir = Path(args.session_dir).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    result = export_viewer_pack(session_dir, out_dir, as_zip=args.zip)
    print(f"[viewer-pack] wrote: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
