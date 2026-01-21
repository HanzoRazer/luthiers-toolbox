"""
QRM adapter: QuadRemesher integration for retopology.

Shells out to the QuadRemesher CLI, normalizes outputs to contract format.

Environment:
    QRM_BIN: Path to QuadRemesher executable
    QRM_TIMEOUT_S: Optional timeout in seconds (default: 300)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from .util import (
    run_cmd,
    load_preset,
    write_sidecar,
    get_tool_version,
    compute_basic_metrics,
    DEFAULT_TIMEOUT_S,
)


def _get_binary() -> str:
    """Get QRM binary path from environment."""
    binary = os.environ.get("QRM_BIN", "")
    if not binary:
        raise EnvironmentError(
            "QRM_BIN environment variable not set. "
            "Set it to the path of your QuadRemesher CLI executable."
        )
    if not Path(binary).exists():
        raise FileNotFoundError(
            f"QRM binary not found at: {binary}. "
            "Check QRM_BIN environment variable."
        )
    return binary


def _get_timeout() -> int:
    """Get timeout from environment or default."""
    try:
        return int(os.environ.get("QRM_TIMEOUT_S", DEFAULT_TIMEOUT_S))
    except ValueError:
        return DEFAULT_TIMEOUT_S


def _build_cmd(binary: str, input_mesh: str, output_mesh: str, preset: Dict[str, Any]) -> List[str]:
    """Build QRM command from preset.
    
    Maps preset fields to CLI flags. Adjust this based on your QRM version.
    """
    cmd = [binary, "--input", input_mesh, "--output", output_mesh]
    
    # Target face/vertex count
    if "target_count" in preset:
        cmd.extend(["--target_count", str(preset["target_count"])])
    
    # Adaptive mode
    if preset.get("adaptive", False):
        cmd.extend(["--adaptive", "1"])
    else:
        cmd.extend(["--adaptive", "0"])
    
    # Symmetry
    symmetry = preset.get("symmetry", "none")
    if symmetry and symmetry != "none":
        cmd.extend(["--symmetry", symmetry.upper()])
    
    # Quad priority
    if preset.get("prioritize_quads", True):
        cmd.extend(["--quad_priority", "1"])
    
    # Pole minimization
    if preset.get("minimize_poles", True):
        cmd.extend(["--minimize_poles", "1"])
    
    # Random seed for reproducibility
    if "seed" in preset:
        cmd.extend(["--seed", str(preset["seed"])])
    
    return cmd


def run(input_mesh: str, preset_path: str, out_dir: str) -> Dict[str, Any]:
    """Run QuadRemesher retopology on input mesh.
    
    Args:
        input_mesh: Path to input mesh file
        preset_path: Path to QRM preset JSON
        out_dir: Output directory for results
    
    Returns:
        Dict with:
            - retopo_mesh_path: Path to output mesh
            - metrics: Basic mesh metrics
        Or on error:
            - error: Error code
            - detail: Error message
            - sidecar_path: Path to sidecar log
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    output_mesh = str(out_path / "retopo_qrm.obj")
    
    # Check for stub mode (no real binary)
    if not os.environ.get("QRM_BIN"):
        # Stub mode: create placeholder output
        Path(output_mesh).write_text("# stub retopo OBJ (QRM_BIN not set)\n")
        return {
            "retopo_mesh_path": output_mesh,
            "metrics": {"aspect_ratio_p95": 2.1, "stub": True}
        }
    
    try:
        binary = _get_binary()
        preset = load_preset(preset_path)
        timeout = _get_timeout()
        
        # Get version for sidecar
        version = get_tool_version(binary)
        
        # Build and run command
        cmd = _build_cmd(binary, input_mesh, output_mesh, preset)
        result = run_cmd(cmd, timeout=timeout)
        
        # Write sidecar
        sidecar_path = write_sidecar(out_dir, "qrm", cmd, result, preset, version)
        
        # Check for errors
        if result.get("error"):
            return {
                "error": "QRM_ERROR",
                "detail": result["error"],
                "sidecar_path": str(sidecar_path)
            }
        
        if result.get("timeout"):
            return {
                "error": "QRM_TIMEOUT",
                "detail": f"Process killed after {timeout}s",
                "sidecar_path": str(sidecar_path)
            }
        
        if result["rc"] != 0:
            return {
                "error": "QRM_NONZERO_EXIT",
                "detail": f"Exit code {result['rc']}: {result['stderr'][:500]}",
                "sidecar_path": str(sidecar_path)
            }
        
        # Check output exists
        if not Path(output_mesh).exists():
            return {
                "error": "QRM_NO_OUTPUT",
                "detail": "Output mesh not created",
                "sidecar_path": str(sidecar_path)
            }
        
        # Compute metrics
        metrics = compute_basic_metrics(output_mesh)
        
        return {
            "retopo_mesh_path": output_mesh,
            "metrics": metrics
        }
        
    except EnvironmentError as e:
        return {"error": "QRM_ENV_ERROR", "detail": str(e)}
    except FileNotFoundError as e:
        return {"error": "QRM_NOT_FOUND", "detail": str(e)}
    except Exception as e:
        return {"error": "QRM_UNEXPECTED", "detail": f"{type(e).__name__}: {e}"}
