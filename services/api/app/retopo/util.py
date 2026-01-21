"""
Retopo adapter utilities.

Shared helpers for subprocess execution, preset loading, sidecar logging,
and post-run metric computation.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# Default timeout for retopo operations (5 minutes)
DEFAULT_TIMEOUT_S = 300

# Max bytes to capture from stdout/stderr
MAX_OUTPUT_BYTES = 32 * 1024  # 32 KB


def run_cmd(
    cmd: List[str],
    timeout: int = DEFAULT_TIMEOUT_S,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Run a subprocess command with timeout and capture output.
    
    Args:
        cmd: Command and arguments as list
        timeout: Max seconds before killing process
        cwd: Working directory (optional)
        env: Environment variables (merged with os.environ)
    
    Returns:
        Dict with:
            - cmd: the command list
            - rc: return code (or -1 if timeout/error)
            - stdout: captured stdout (truncated)
            - stderr: captured stderr (truncated)
            - dur_s: wall clock duration
            - timeout: True if process was killed
            - error: error message if exception occurred
    """
    start = time.perf_counter()
    result: Dict[str, Any] = {
        "cmd": cmd,
        "rc": -1,
        "stdout": "",
        "stderr": "",
        "dur_s": 0.0,
        "timeout": False,
        "error": None,
    }
    
    # Merge environment
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            cwd=cwd,
            env=run_env,
        )
        result["rc"] = proc.returncode
        result["stdout"] = _truncate(proc.stdout.decode("utf-8", errors="replace"))
        result["stderr"] = _truncate(proc.stderr.decode("utf-8", errors="replace"))
        
    except subprocess.TimeoutExpired as e:
        result["timeout"] = True
        result["error"] = f"Process killed after {timeout}s"
        if e.stdout:
            result["stdout"] = _truncate(e.stdout.decode("utf-8", errors="replace"))
        if e.stderr:
            result["stderr"] = _truncate(e.stderr.decode("utf-8", errors="replace"))
            
    except FileNotFoundError:
        result["error"] = f"Binary not found: {cmd[0]}"
        
    except PermissionError:
        result["error"] = f"Permission denied: {cmd[0]}"
        
    except Exception as e:
        result["error"] = f"Unexpected error: {type(e).__name__}: {e}"
    
    result["dur_s"] = round(time.perf_counter() - start, 3)
    return result


def _truncate(s: str, max_bytes: int = MAX_OUTPUT_BYTES) -> str:
    """Truncate string to max bytes with marker."""
    encoded = s.encode("utf-8")
    if len(encoded) <= max_bytes:
        return s
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + f"\n... [truncated, {len(encoded)} bytes total]"


def load_preset(preset_path: str) -> Dict[str, Any]:
    """Load a preset JSON file.
    
    Args:
        preset_path: Path to preset JSON
    
    Returns:
        Parsed preset dict
    
    Raises:
        FileNotFoundError: If preset doesn't exist
        json.JSONDecodeError: If preset is invalid JSON
    """
    path = Path(preset_path)
    if not path.exists():
        raise FileNotFoundError(f"Preset not found: {preset_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_sidecar(
    out_dir: str,
    adapter: str,
    cmd: List[str],
    result: Dict[str, Any],
    preset: Dict[str, Any],
    tool_version: Optional[str] = None
) -> Path:
    """Write sidecar log for a retopo run.
    
    Args:
        out_dir: Output directory
        adapter: Adapter name ("qrm", "miq", etc.)
        cmd: Command that was executed
        result: Result dict from run_cmd
        preset: Preset dict that was used
        tool_version: Optional version string from tool
    
    Returns:
        Path to the written sidecar file
    """
    sidecar = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "adapter": adapter,
        "preset": preset.get("name", "unknown"),
        "cmd": cmd,
        "rc": result.get("rc", -1),
        "dur_s": result.get("dur_s", 0),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "timeout": result.get("timeout", False),
        "error": result.get("error"),
        "tool_version": tool_version,
    }
    
    out_path = Path(out_dir) / "retopo_sidecar.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return out_path


def get_tool_version(binary: str, version_flag: str = "--version") -> Optional[str]:
    """Try to get version string from a tool.
    
    Args:
        binary: Path to binary
        version_flag: Flag to get version (default: --version)
    
    Returns:
        Version string or None if failed
    """
    try:
        result = subprocess.run(
            [binary, version_flag],
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace").strip()
    except Exception:
        pass
    return None


def compute_basic_metrics(mesh_path: str) -> Dict[str, Any]:
    """Compute basic mesh metrics post-retopo.
    
    Uses trimesh if available, otherwise returns empty metrics.
    
    Args:
        mesh_path: Path to mesh file
    
    Returns:
        Dict with vertex_count, face_count, quad_pct, aspect_ratio_p95, etc.
    """
    metrics: Dict[str, Any] = {
        "vertex_count": 0,
        "face_count": 0,
        "quad_pct": 0.0,
        "edge_length_mean": 0.0,
        "edge_length_std": 0.0,
        "aspect_ratio_p95": 0.0,
    }
    
    try:
        import trimesh
        mesh = trimesh.load(mesh_path, force="mesh")
        
        metrics["vertex_count"] = len(mesh.vertices)
        metrics["face_count"] = len(mesh.faces)
        
        # Edge lengths
        edges = mesh.edges_unique_length
        if len(edges) > 0:
            import numpy as np
            metrics["edge_length_mean"] = float(np.mean(edges))
            metrics["edge_length_std"] = float(np.std(edges))
        
        # Aspect ratio (approximate via face areas / edge lengths)
        if hasattr(mesh, "face_adjacency_angles"):
            # Use triangle aspect ratios if available
            pass  # TODO: compute proper aspect ratios
        
        # Quad percentage (for quad meshes loaded as triangulated)
        # This is approximate; proper quad detection needs original format
        metrics["quad_pct"] = 0.0  # Placeholder
        
    except ImportError:
        # trimesh not available, return empty metrics
        pass
    except Exception:
        # Mesh loading failed, return empty metrics
        pass
    
    return metrics
