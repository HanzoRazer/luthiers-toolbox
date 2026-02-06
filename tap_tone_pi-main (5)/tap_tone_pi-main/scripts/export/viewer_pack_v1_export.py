#!/usr/bin/env python3
"""
viewer_pack_v1_export.py — Export Phase 2 sessions to viewer_pack_v1 format

Usage:
    python scripts/export/viewer_pack_v1_export.py \
        --session runs_phase2/session_20260101T235209Z \
        --out out/viewer_packs/session_20260101T235209Z.zip

Mapping (Phase 2 session → viewer_pack_v1):
    session/grid.json                    → meta/grid.json
    session/metadata.json                → meta/metadata.json
    session/points/point_A1/audio.wav    → audio/points/A1.wav
    session/points/point_A1/spectrum.csv → spectra/points/A1/spectrum.csv
    session/points/point_A1/analysis.json→ spectra/points/A1/analysis.json
    session/points/point_A1/capture_meta.json → provenance/points/A1/capture_meta.json
    session/derived/ods_snapshot.json    → ods/ods_snapshot.json
    session/derived/wolf_candidates.json → wolf/wolf_candidates.json
    session/derived/wsi_curve.csv        → wolf/wsi_curve.csv
    session/plots/*                      → plots/*
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# Constants
# ============================================================================

SCHEMA_VERSION = "v1"
SCHEMA_ID = "viewer_pack_v1"

# Kind assignments by filename/location pattern
KIND_MAP = {
    "audio.wav": "audio_raw",
    "spectrum.csv": "spectrum_csv",
    "analysis.json": "analysis_peaks",
    "capture_meta.json": "provenance",
    "ods_snapshot.json": "ods_snapshot",
    "wolf_candidates.json": "wolf_candidates",
    "wsi_curve.csv": "wsi_curve",
    "grid.json": "session_meta",
    "metadata.json": "session_meta",
}

MIME_MAP = {
    ".wav": "audio/wav",
    ".csv": "text/csv",
    ".json": "application/json",
    ".png": "image/png",
    ".txt": "text/plain",
}


# ============================================================================
# Data classes
# ============================================================================

@dataclass
class FileEntry:
    relpath: str
    sha256: str
    bytes: int
    mime: str
    kind: str


@dataclass
class PackContents:
    audio: bool = False
    spectra: bool = False
    coherence: bool = False
    ods: bool = False
    wolf: bool = False
    plots: bool = False
    provenance: bool = False


@dataclass
class ExportResult:
    pack_path: Path
    manifest: Dict[str, Any]
    files_copied: int
    points: List[str]


# ============================================================================
# Layer A: Discovery
# ============================================================================

def detect_phase(session_dir: Path) -> str:
    """Detect if session is phase1, phase2, or unknown."""
    has_points = (session_dir / "points").is_dir()
    has_derived = (session_dir / "derived").is_dir()
    
    if has_points and has_derived:
        return "phase2"
    
    # Phase 1: has audio.wav + analysis.json at root or capture_* subdirs
    if (session_dir / "audio.wav").exists():
        return "phase1"
    
    # Check for capture_* subdirs (phase1 session)
    capture_dirs = list(session_dir.glob("capture_*"))
    if capture_dirs and (capture_dirs[0] / "audio.wav").exists():
        return "phase1"
    
    return "unknown"


def enumerate_points(session_dir: Path) -> List[str]:
    """Return sorted list of point IDs from points/point_* folders."""
    points_dir = session_dir / "points"
    if not points_dir.is_dir():
        return []
    
    point_ids = []
    for p in sorted(points_dir.iterdir()):
        if p.is_dir() and p.name.startswith("point_"):
            # point_A1 → A1
            point_id = p.name.replace("point_", "", 1)
            point_ids.append(point_id)
    
    return point_ids


def validate_session(session_dir: Path) -> None:
    """Raise if session doesn't meet minimum requirements."""
    if not session_dir.is_dir():
        raise ValueError(f"Session directory not found: {session_dir}")
    
    phase = detect_phase(session_dir)
    if phase == "unknown":
        raise ValueError(f"Cannot detect session phase: {session_dir}")
    
    if phase == "phase2":
        points = enumerate_points(session_dir)
        if not points:
            raise ValueError(f"Phase 2 session has no points: {session_dir}")


# ============================================================================
# Layer B: Copy + Structure
# ============================================================================

def _copy_file(src: Path, dst: Path) -> Optional[Path]:
    """Copy file if exists, return dst path or None."""
    if not src.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def _get_mime(path: Path) -> str:
    return MIME_MAP.get(path.suffix.lower(), "application/octet-stream")


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


def _get_kind(relpath: str, filename: str) -> str:
    """Determine kind from relpath pattern or filename."""
    # Path-based patterns (take priority)
    if relpath.startswith("audio/points/") and relpath.endswith(".wav"):
        return "audio_raw"
    if relpath.startswith("spectra/") and filename == "spectrum.csv":
        return "spectrum_csv"
    if relpath.startswith("spectra/") and filename == "analysis.json":
        return "analysis_peaks"
    if relpath.startswith("provenance/") and filename == "capture_meta.json":
        return "provenance"
    if relpath.startswith("meta/"):
        return "session_meta"
    if relpath.startswith("plots/") and filename.endswith(".png"):
        return "plot_png"
    if relpath.startswith("ods/"):
        return "transfer_function"  # ODS = transfer_function
    if filename == "README.txt":
        return "provenance"
    
    # Direct filename match
    if filename in KIND_MAP:
        return KIND_MAP[filename]
    
    return "unknown"


def build_pack_tree_phase2(session_dir: Path, pack_dir: Path) -> tuple[List[FileEntry], PackContents, List[str]]:
    """
    Build viewer pack tree from Phase 2 session.
    Returns (file_entries, contents_flags, point_ids).
    """
    entries: List[FileEntry] = []
    contents = PackContents()
    point_ids = enumerate_points(session_dir)
    
    # --- Meta files ---
    for fname in ["grid.json", "metadata.json"]:
        src = session_dir / fname
        dst_relpath = f"meta/{fname}"
        if _copy_file(src, pack_dir / dst_relpath):
            entries.append(_make_entry(pack_dir / dst_relpath, dst_relpath))
    
    # --- Per-point files ---
    for pid in point_ids:
        point_src = session_dir / "points" / f"point_{pid}"
        
        # audio.wav → audio/points/PID.wav
        src = point_src / "audio.wav"
        dst_relpath = f"audio/points/{pid}.wav"
        if _copy_file(src, pack_dir / dst_relpath):
            entries.append(_make_entry(pack_dir / dst_relpath, dst_relpath))
            contents.audio = True
        
        # spectrum.csv → spectra/points/PID/spectrum.csv
        src = point_src / "spectrum.csv"
        dst_relpath = f"spectra/points/{pid}/spectrum.csv"
        if _copy_file(src, pack_dir / dst_relpath):
            entries.append(_make_entry(pack_dir / dst_relpath, dst_relpath))
            contents.spectra = True
        
        # analysis.json → spectra/points/PID/analysis.json
        src = point_src / "analysis.json"
        dst_relpath = f"spectra/points/{pid}/analysis.json"
        if _copy_file(src, pack_dir / dst_relpath):
            entries.append(_make_entry(pack_dir / dst_relpath, dst_relpath))
        
        # capture_meta.json → provenance/points/PID/capture_meta.json
        src = point_src / "capture_meta.json"
        dst_relpath = f"provenance/points/{pid}/capture_meta.json"
        if _copy_file(src, pack_dir / dst_relpath):
            entries.append(_make_entry(pack_dir / dst_relpath, dst_relpath))
            contents.provenance = True
    
    # --- Derived artifacts ---
    derived_dir = session_dir / "derived"
    
    # ods_snapshot.json
    src = derived_dir / "ods_snapshot.json"
    dst_relpath = "ods/ods_snapshot.json"
    if _copy_file(src, pack_dir / dst_relpath):
        entries.append(_make_entry(pack_dir / dst_relpath, dst_relpath))
        contents.ods = True
        contents.coherence = True  # ODS includes coherence
    
    # wolf_candidates.json
    src = derived_dir / "wolf_candidates.json"
    dst_relpath = "wolf/wolf_candidates.json"
    if _copy_file(src, pack_dir / dst_relpath):
        entries.append(_make_entry(pack_dir / dst_relpath, dst_relpath))
        contents.wolf = True
    
    # wsi_curve.csv
    src = derived_dir / "wsi_curve.csv"
    dst_relpath = "wolf/wsi_curve.csv"
    if _copy_file(src, pack_dir / dst_relpath):
        entries.append(_make_entry(pack_dir / dst_relpath, dst_relpath))
    
    # --- Plots ---
    plots_dir = session_dir / "plots"
    if plots_dir.is_dir():
        for plot_file in sorted(plots_dir.glob("*.png")):
            dst_relpath = f"plots/{plot_file.name}"
            if _copy_file(plot_file, pack_dir / dst_relpath):
                entries.append(_make_entry(pack_dir / dst_relpath, dst_relpath))
                contents.plots = True
    
    return entries, contents, point_ids


def _make_entry(path: Path, relpath: str) -> FileEntry:
    """Create FileEntry with hash and metadata."""
    data = path.read_bytes()
    return FileEntry(
        relpath=relpath,
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
        mime=_get_mime(path),
        kind=_get_kind(relpath, path.name),
    )


# ============================================================================
# Layer C: Hashing + Manifest
# ============================================================================

def compute_bundle_hash(entries: List[FileEntry]) -> str:
    """
    Compute deterministic bundle hash from all file entries.
    Hash of sorted (sha256 + relpath + bytes) concatenation.
    """
    h = hashlib.sha256()
    for e in sorted(entries, key=lambda x: x.relpath):
        h.update(f"{e.sha256}|{e.relpath}|{e.bytes}\n".encode("utf-8"))
    return h.hexdigest()


def _utcnow() -> dt.datetime:
    """Return current UTC time (timezone-aware)."""
    return dt.datetime.now(dt.timezone.utc)


def build_manifest(
    *,
    session_name: str,
    detected_phase: str,
    entries: List[FileEntry],
    contents: PackContents,
    points: List[str],
) -> Dict[str, Any]:
    """Build the manifest.json structure."""
    
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "schema_id": SCHEMA_ID,
        "created_at_utc": _utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_capdir": session_name,
        "detected_phase": detected_phase,
        "measurement_only": True,
        "interpretation": "deferred",
        "points": points,  # Extension: list of point IDs for easy enumeration
        "contents": {
            "audio": contents.audio,
            "spectra": contents.spectra,
            "coherence": contents.coherence,
            "ods": contents.ods,
            "wolf": contents.wolf,
            "plots": contents.plots,
            "provenance": contents.provenance,
        },
        "files": [
            {
                "relpath": e.relpath,
                "sha256": e.sha256,
                "bytes": e.bytes,
                "mime": e.mime,
                "kind": e.kind,
            }
            for e in sorted(entries, key=lambda x: x.relpath)
        ],
        "bundle_sha256": "",  # Filled below
    }
    
    # Compute bundle hash (excluding bundle_sha256 itself)
    manifest["bundle_sha256"] = compute_bundle_hash(entries)
    
    return manifest


def write_readme(pack_dir: Path, session_name: str, points: List[str]) -> Path:
    """Write a simple README.txt."""
    readme_path = pack_dir / "README.txt"
    readme_path.write_text(
        f"Viewer Pack v1\n"
        f"==============\n"
        f"Source: {session_name}\n"
        f"Created: {_utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"Points: {len(points)}\n"
        f"\n"
        f"This bundle contains measurement data only.\n"
        f"No interpretation, scoring, or recommendations are included.\n",
        encoding="utf-8",
    )
    return readme_path


# ============================================================================
# Main Export Function
# ============================================================================

def export_viewer_pack(
    session_dir: Path,
    out_path: Path,
    *,
    keep_unzipped: bool = False,
) -> ExportResult:
    """
    Export a Phase 2 session to viewer_pack_v1 format.
    
    Args:
        session_dir: Path to session directory (e.g., runs_phase2/session_...)
        out_path: Output path for .zip file
        keep_unzipped: If True, also keep the unzipped directory
    
    Returns:
        ExportResult with manifest and stats
    """
    session_dir = Path(session_dir).resolve()
    out_path = Path(out_path).resolve()
    
    # Validate
    validate_session(session_dir)
    detected_phase = detect_phase(session_dir)
    
    if detected_phase != "phase2":
        raise NotImplementedError(f"Only phase2 export implemented; got {detected_phase}")
    
    # Build pack in temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        pack_dir = Path(tmpdir) / "viewer_pack_v1"
        pack_dir.mkdir()
        
        # Layer B: Copy files
        entries, contents, points = build_pack_tree_phase2(session_dir, pack_dir)
        
        # Write README
        readme_path = write_readme(pack_dir, session_dir.name, points)
        entries.append(_make_entry(readme_path, "README.txt"))
        
        # Layer C: Build manifest
        manifest = build_manifest(
            session_name=session_dir.name,
            detected_phase=detected_phase,
            entries=entries,
            contents=contents,
            points=points,
        )
        
        # Write manifest
        manifest_path = pack_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=False),
            encoding="utf-8",
        )
        
        # Add manifest to entries (but don't re-hash bundle)
        manifest_entry = _make_entry(manifest_path, "manifest.json")
        
        # Create zip
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(pack_dir.rglob("*")):
                if file.is_file():
                    arcname = file.relative_to(pack_dir).as_posix()
                    zf.write(file, arcname)
        
        # Optionally keep unzipped copy
        if keep_unzipped:
            unzipped_dir = out_path.with_suffix("")
            if unzipped_dir.exists():
                shutil.rmtree(unzipped_dir)
            shutil.copytree(pack_dir, unzipped_dir)
    
    return ExportResult(
        pack_path=out_path,
        manifest=manifest,
        files_copied=len(entries),
        points=points,
    )


# ============================================================================
# CLI
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Phase 2 session to viewer_pack_v1 format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--session",
        required=True,
        type=Path,
        help="Path to session directory (e.g., runs_phase2/session_20260101T235209Z)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output path for .zip file (required unless --dry-run)",
    )
    parser.add_argument(
        "--keep-unzipped",
        action="store_true",
        help="Keep unzipped directory alongside .zip",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate session without exporting",
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        validate_session(args.session)
        phase = detect_phase(args.session)
        points = enumerate_points(args.session)
        print(f"Session: {args.session}")
        print(f"Phase:   {phase}")
        print(f"Points:  {len(points)} ({', '.join(points[:5])}{'...' if len(points) > 5 else ''})")
        print("Validation passed.")
        return
    
    if args.out is None:
        parser.error("--out is required unless --dry-run")
    
    result = export_viewer_pack(
        args.session,
        args.out,
        keep_unzipped=args.keep_unzipped,
    )
    
    print(f"Exported: {result.pack_path}")
    print(f"Points:   {len(result.points)}")
    print(f"Files:    {result.files_copied}")
    print(f"Bundle:   {result.manifest['bundle_sha256'][:16]}...")


if __name__ == "__main__":
    main()
