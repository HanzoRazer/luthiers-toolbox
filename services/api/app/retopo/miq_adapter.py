"""
Mixed-Integer Quadrangulation (MIQ) adapter.
Looks for MIQ CLI via env var MIQ_BIN and maps preset.json → flags.
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

# Default timeout for MIQ (5 minutes)
MIQ_TIMEOUT_SEC = int(os.getenv("MIQ_TIMEOUT_SEC", "300"))


def _load_preset(preset_path: str) -> dict:
    """Load preset JSON file."""
    return json.loads(Path(preset_path).read_text(encoding="utf-8"))


def _build_args(miq_bin: str, input_mesh: Path, output_mesh: Path, preset: dict) -> list[str]:
    """
    Map preset.json fields to MIQ CLI flags.
    ⚠ Adjust flags to match your MIQ CLI/libigl version.
    """
    args = [
        miq_bin,
        "--input", str(input_mesh),
        "--output", str(output_mesh),
    ]

    if "gradient_size" in preset:
        args += ["--gradient_size", str(preset["gradient_size"])]
    if "stiffness" in preset:
        args += ["--stiffness", str(preset["stiffness"])]
    if "direct_round" in preset and preset["direct_round"]:
        args += ["--direct_round"]
    if "iter" in preset:
        args += ["--iter", str(int(preset["iter"]))]

    return args


def _stub_fallback(input_mesh: str, out_dir: str, reason: str) -> dict:
    """
    Fallback when MIQ is unavailable: copy input to output (identity).
    Returns contract-compatible output with stub metrics.
    """
    _log.warning("MIQ fallback: %s", reason)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    output_mesh = out_path / "retopo_miq.obj"
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
    Run MIQ retopology on input mesh.

    Args:
        input_mesh: Path to input mesh file.
        preset_path: Path to MIQ preset JSON.
        out_dir: Output directory for results.

    Returns:
        dict with retopo_mesh_path and metrics.
        Falls back to copy-through if MIQ_BIN is unset or execution fails.
    """
    miq_bin = os.getenv("MIQ_BIN")
    if not miq_bin:
        return _stub_fallback(input_mesh, out_dir, "MIQ_BIN not set")

    if not Path(miq_bin).exists():
        return _stub_fallback(input_mesh, out_dir, f"MIQ_BIN not found: {miq_bin}")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    output_mesh = out_path / "retopo_miq.obj"

    try:
        preset = _load_preset(preset_path)
    except Exception as e:
        return _stub_fallback(input_mesh, out_dir, f"Failed to load preset: {e}")

    args = _build_args(miq_bin, Path(input_mesh), output_mesh, preset)

    returncode, stdout, stderr, elapsed = run_cmd(args, timeout_sec=MIQ_TIMEOUT_SEC)

    # Write sidecar log regardless of success/failure
    write_sidecar(
        out_dir,
        "miq",
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        elapsed_sec=elapsed,
        args=args,
        extra={"preset": preset_path},
    )

    if returncode != 0:
        return _stub_fallback(input_mesh, out_dir, f"MIQ exited with code {returncode}: {stderr[:200]}")

    if not output_mesh.exists():
        return _stub_fallback(input_mesh, out_dir, "MIQ produced no output file")

    # TODO: Compute real metrics from output mesh (aspect ratio, etc.)
    return {
        "retopo_mesh_path": str(output_mesh),
        "metrics": {
            "aspect_ratio_p95": None,  # Placeholder until mesh analysis is wired
            "elapsed_sec": round(elapsed, 3),
        },
    }

