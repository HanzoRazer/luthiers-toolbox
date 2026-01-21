"""
QuadRemesher (QRM) adapter.
Looks for QRM CLI via env var QRM_BIN and maps preset.json → flags.
If the binary is missing or fails, falls back to a safe stub (copy-through)
and still returns contract-compatible outputs with a sidecar log.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path

from .util import run_cmd, write_sidecar

_log = logging.getLogger(__name__)

# Default timeout for QRM (5 minutes)
QRM_TIMEOUT_SEC = int(os.getenv("QRM_TIMEOUT_SEC", "300"))


def _load_preset(preset_path: str) -> dict:
    """Load preset JSON file."""
    return json.loads(Path(preset_path).read_text(encoding="utf-8"))


def _build_args(qrm_bin: str, input_mesh: Path, output_mesh: Path, preset: dict) -> list[str]:
    """
    Map preset.json fields to QRM CLI flags.
    ⚠ Adjust flags to match your QRM CLI version.
    """
    args = [
        qrm_bin,
        "--input", str(input_mesh),
        "--output", str(output_mesh),
    ]

    if "target_count" in preset:
        args += ["--target_count", str(int(preset["target_count"]))]
    if "adaptive_size" in preset:
        args += ["--adaptive_size", str(preset["adaptive_size"])]
    if "symmetry" in preset and preset["symmetry"]:
        args += ["--symmetry"]
    if "curvature_adapt" in preset:
        args += ["--curvature_adapt", str(preset["curvature_adapt"])]

    return args


def _stub_fallback(input_mesh: str, out_dir: str, reason: str) -> dict:
    """
    Fallback when QRM is unavailable: copy input to output (identity).
    Returns contract-compatible output with stub metrics.
    """
    _log.warning("QRM fallback: %s", reason)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    output_mesh = out_path / "retopo_qrm.obj"
    shutil.copy2(input_mesh, output_mesh)

    return {
        "retopo_mesh_path": str(output_mesh),
        "metrics": {
            "aspect_ratio_p95": None,
            "fallback": True,
            "fallback_reason": reason,
        },
    }


def run(input_mesh: str, preset_path: str, out_dir: str) -> dict:
    """
    Run QuadRemesher retopology on input mesh.

    Args:
        input_mesh: Path to input mesh file.
        preset_path: Path to QRM preset JSON.
        out_dir: Output directory for results.

    Returns:
        dict with retopo_mesh_path and metrics.
        Falls back to copy-through if QRM_BIN is unset or execution fails.
    """
    qrm_bin = os.getenv("QRM_BIN")
    if not qrm_bin:
        return _stub_fallback(input_mesh, out_dir, "QRM_BIN not set")

    if not Path(qrm_bin).exists():
        return _stub_fallback(input_mesh, out_dir, f"QRM_BIN not found: {qrm_bin}")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    output_mesh = out_path / "retopo_qrm.obj"

    try:
        preset = _load_preset(preset_path)
    except Exception as e:
        return _stub_fallback(input_mesh, out_dir, f"Failed to load preset: {e}")

    args = _build_args(qrm_bin, Path(input_mesh), output_mesh, preset)

    returncode, stdout, stderr, elapsed = run_cmd(args, timeout_sec=QRM_TIMEOUT_SEC)

    # Write sidecar log regardless of success/failure
    write_sidecar(
        out_dir,
        "qrm",
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        elapsed_sec=elapsed,
        args=args,
        extra={"preset": preset_path},
    )

    if returncode != 0:
        return _stub_fallback(input_mesh, out_dir, f"QRM exited with code {returncode}: {stderr[:200]}")

    if not output_mesh.exists():
        return _stub_fallback(input_mesh, out_dir, "QRM produced no output file")

    # TODO: Compute real metrics from output mesh (aspect ratio, etc.)
    return {
        "retopo_mesh_path": str(output_mesh),
        "metrics": {
            "aspect_ratio_p95": None,  # Placeholder until mesh analysis is wired
            "elapsed_sec": round(elapsed, 3),
        },
    }

