"""
MIQ adapter: Mixed-Integer Quadrangulation integration for retopology.

Shells out to an MIQ CLI or Python binding, normalizes outputs to contract format.

Environment:
    MIQ_BIN: Path to MIQ CLI executable
    PYTHON_MIQ: Alternative Python entry point (module.path:function_name)
    MIQ_TIMEOUT_S: Optional timeout in seconds (default: 300)
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .util import (
    run_cmd,
    load_preset,
    write_sidecar,
    get_tool_version,
    compute_basic_metrics,
    DEFAULT_TIMEOUT_S,
)


def _get_binary() -> Optional[str]:
    """Get MIQ binary path from environment."""
    binary = os.environ.get("MIQ_BIN", "")
    if binary and Path(binary).exists():
        return binary
    return None


def _get_python_entry() -> Optional[Callable]:
    """Get MIQ Python entry point from environment.
    
    Format: module.path:function_name
    """
    entry_spec = os.environ.get("PYTHON_MIQ", "")
    if not entry_spec or ":" not in entry_spec:
        return None
    
    try:
        module_path, func_name = entry_spec.rsplit(":", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
    except Exception:
        return None


def _get_timeout() -> int:
    """Get timeout from environment or default."""
    try:
        return int(os.environ.get("MIQ_TIMEOUT_S", DEFAULT_TIMEOUT_S))
    except ValueError:
        return DEFAULT_TIMEOUT_S


def _build_cmd(binary: str, input_mesh: str, output_mesh: str, preset: Dict[str, Any]) -> List[str]:
    """Build MIQ command from preset.
    
    Maps preset fields to CLI flags. Adjust based on your MIQ wrapper.
    """
    cmd = [binary, "--input", input_mesh, "--output", output_mesh]
    
    # Scale / density
    if "target_density" in preset:
        cmd.extend(["--density", str(preset["target_density"])])
    
    # Hard feature preservation
    if "scale_hard_features" in preset:
        cmd.extend(["--scale_hard_features", str(preset["scale_hard_features"])])
    
    # Smoothness
    if "smoothness" in preset:
        cmd.extend(["--smoothness", str(preset["smoothness"])])
    
    # Singularity optimization
    if preset.get("singularity_opt", False):
        cmd.extend(["--singularity_opt", "1"])
    
    # Boundary preservation
    boundary = preset.get("boundary_preservation", "strict")
    if boundary:
        cmd.extend(["--boundary", boundary])
    
    # Random seed
    if "seed" in preset:
        cmd.extend(["--seed", str(preset["seed"])])
    
    return cmd


def _run_python_miq(
    entry: Callable,
    input_mesh: str,
    output_mesh: str,
    preset: Dict[str, Any]
) -> Dict[str, Any]:
    """Run MIQ via Python binding.
    
    Expects entry function signature:
        def miq_run(input_path: str, output_path: str, **kwargs) -> None
    """
    import time
    
    start = time.perf_counter()
    try:
        # Pass preset fields as kwargs
        entry(
            input_mesh,
            output_mesh,
            density=preset.get("target_density", 1.0),
            smoothness=preset.get("smoothness", 0.2),
            singularity_opt=preset.get("singularity_opt", True),
            boundary=preset.get("boundary_preservation", "strict"),
            seed=preset.get("seed", 42),
        )
        return {
            "rc": 0,
            "dur_s": round(time.perf_counter() - start, 3),
            "stdout": "Python MIQ completed",
            "stderr": "",
        }
    except Exception as e:
        return {
            "rc": 1,
            "dur_s": round(time.perf_counter() - start, 3),
            "stdout": "",
            "stderr": f"{type(e).__name__}: {e}",
            "error": str(e),
        }


def run(input_mesh: str, preset_path: str, out_dir: str) -> Dict[str, Any]:
    """Run MIQ retopology on input mesh.
    
    Args:
        input_mesh: Path to input mesh file
        preset_path: Path to MIQ preset JSON
        out_dir: Output directory for results
    
    Returns:
        Dict with:
            - retopo_mesh_path: Path to output mesh
            - metrics: Basic mesh metrics
        Or on error:
            - error: Error code
            - detail: Error message
            - sidecar_path: Path to sidecar log (if written)
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    output_mesh = str(out_path / "retopo_miq.obj")
    
    # Check for stub mode (no real binary or Python entry)
    binary = _get_binary()
    py_entry = _get_python_entry()
    
    if not binary and not py_entry:
        # Stub mode: create placeholder output
        Path(output_mesh).write_text("# stub retopo OBJ (MIQ_BIN/PYTHON_MIQ not set)\n")
        return {
            "retopo_mesh_path": output_mesh,
            "metrics": {"aspect_ratio_p95": 1.8, "stub": True}
        }
    
    try:
        preset = load_preset(preset_path)
        timeout = _get_timeout()
        
        if py_entry:
            # Python binding mode
            result = _run_python_miq(py_entry, input_mesh, output_mesh, preset)
            cmd = ["python", "-c", f"PYTHON_MIQ({input_mesh}, {output_mesh})"]
            version = "Python binding"
        else:
            # CLI mode
            version = get_tool_version(binary)
            cmd = _build_cmd(binary, input_mesh, output_mesh, preset)
            result = run_cmd(cmd, timeout=timeout)
        
        # Write sidecar
        sidecar_path = write_sidecar(out_dir, "miq", cmd, result, preset, version)
        
        # Check for errors
        if result.get("error"):
            return {
                "error": "MIQ_ERROR",
                "detail": result["error"],
                "sidecar_path": str(sidecar_path)
            }
        
        if result.get("timeout"):
            return {
                "error": "MIQ_TIMEOUT",
                "detail": f"Process killed after {timeout}s",
                "sidecar_path": str(sidecar_path)
            }
        
        if result["rc"] != 0:
            return {
                "error": "MIQ_NONZERO_EXIT",
                "detail": f"Exit code {result['rc']}: {result['stderr'][:500]}",
                "sidecar_path": str(sidecar_path)
            }
        
        # Check output exists
        if not Path(output_mesh).exists():
            return {
                "error": "MIQ_NO_OUTPUT",
                "detail": "Output mesh not created",
                "sidecar_path": str(sidecar_path)
            }
        
        # Compute metrics
        metrics = compute_basic_metrics(output_mesh)
        
        return {
            "retopo_mesh_path": output_mesh,
            "metrics": metrics
        }
        
    except FileNotFoundError as e:
        return {"error": "MIQ_PRESET_NOT_FOUND", "detail": str(e)}
    except Exception as e:
        return {"error": "MIQ_UNEXPECTED", "detail": f"{type(e).__name__}: {e}"}
