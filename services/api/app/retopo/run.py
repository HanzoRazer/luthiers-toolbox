"""
Mesh Pipeline runner (v0.1.0):
 - intake/heal mesh
 - choose adapter (miq|qrm) via preset
 - compute fields (grain, brace, thickness)
 - emit qa_core.json and cam_policy.json per contracts
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from . import miq_adapter, qrm_adapter


def now() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def write_json(p: Path, d: Dict[str, Any]) -> None:
    """Write a dict as JSON to a file, creating parent dirs as needed."""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")


def _heal_mesh(input_mesh: Path, out_dir: Path) -> Dict[str, Any]:
    """Stub mesh healing step.
    
    TODO: Wire to Open3D or similar for actual hole-filling, non-manifold repair.
    """
    healed = out_dir / "healed.obj"
    # Stub: just create marker file
    healed.write_text("# stub healed OBJ\n")
    return {
        "healed_path": str(healed),
        "status": "clean",  # or "healed" if ops performed
        "operations": [],
        "input_faces": 0,
        "output_faces": 0,
        "holes_filled": 0,
        "non_manifold_fixed": 0
    }


def _analyze_fields(model_id: str, mesh_path: str) -> Dict[str, Any]:
    """Analyze fields using existing services.
    
    Returns combined field analysis results.
    """
    try:
        from app.fields.grain_field.service import GrainFieldService
        from app.fields.brace_graph.service import BraceGraphService
        from app.fields.thickness_map.service import ThicknessMapService
        
        grain_svc = GrainFieldService()
        brace_svc = BraceGraphService()
        thick_svc = ThicknessMapService()
        
        grain_result = grain_svc.analyze(model_id=model_id, geometry=None)
        brace_result = brace_svc.analyze(model_id=model_id, geometry=None)
        thick_result = thick_svc.analyze(model_id=model_id, geometry=None)
        
        return {
            "grain": {
                "coverage_pct": getattr(grain_result, 'coverage_pct', 0),
                "mean_confidence": getattr(grain_result, 'mean_confidence', 0),
                "runout_zones": getattr(grain_result, 'runout_zones', []),
                "checking_zones": getattr(grain_result, 'checking_zones', []),
                "cam_policy_overrides": getattr(grain_result, 'cam_policy_overrides', []),
            },
            "brace": {
                "node_count": getattr(brace_result, 'node_count', 0),
                "edge_count": getattr(brace_result, 'edge_count', 0),
                "topology_valid": getattr(brace_result, 'topology_valid', True),
                "no_cut_zones": getattr(brace_result, 'no_cut_zones', []) if hasattr(brace_result, 'no_cut_zones') else [],
            },
            "thickness": {
                "zone_count": len(getattr(thick_result, 'zones', [])),
                "overall_compliance": getattr(thick_result, 'overall_compliance', 'unknown'),
                "thickness_critical_zones": getattr(thick_result, 'thickness_critical_zones', []),
                "cam_policy_overrides": getattr(thick_result, 'cam_policy_overrides', []),
            },
        }
    except ImportError:
        # Fields services not available, return empty
        return {
            "grain": {"coverage_pct": 0, "mean_confidence": 0, "runout_zones": [], "checking_zones": [], "cam_policy_overrides": []},
            "brace": {"node_count": 0, "edge_count": 0, "topology_valid": True, "no_cut_zones": []},
            "thickness": {"zone_count": 0, "overall_compliance": "unknown", "thickness_critical_zones": [], "cam_policy_overrides": []},
        }


def run_pipeline(
    input_mesh: str,
    model_id: str,
    preset: str,
    out_dir: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Run the mesh pipeline from intake through CAM policy export.
    
    Args:
        input_mesh: Path to input mesh file (OBJ, STL, etc.)
        model_id: Unique identifier for this model/part
        preset: "miq" or "qrm" for retopology adapter selection
        out_dir: Output directory for all artifacts
        session_id: Optional session identifier for provenance
    
    Returns:
        Dict with paths to qa_core.json and cam_policy.json
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    src = Path(input_mesh)
    
    # Step 1: Heal mesh
    heal_result = _heal_mesh(src, out)
    healed = Path(heal_result["healed_path"])
    
    # Step 2: Choose retopo adapter and run
    presets_root = Path("presets/retopo")
    if preset == "miq":
        preset_path = presets_root / "miq" / "preset.json"
        retopo_result = miq_adapter.run(str(healed), str(preset_path), str(out))
    else:
        preset_path = presets_root / "qrm" / "preset.json"
        retopo_result = qrm_adapter.run(str(healed), str(preset_path), str(out))
    
    # Check for retopo errors
    if "error" in retopo_result:
        return {
            "error": retopo_result["error"],
            "detail": retopo_result.get("detail", ""),
            "sidecar_path": retopo_result.get("sidecar_path"),
            "qa_core_path": None,
            "cam_policy_path": None,
        }
    
    retopo_path = Path(retopo_result["retopo_mesh_path"])
    
    # Step 3: Analyze fields
    fields = _analyze_fields(model_id, str(retopo_path))
    
    # Step 4: Compose QA Core artifact
    qa_core = {
        "version": "1.0.0",
        "timestamp_utc": now(),
        "model_id": model_id,
        "session_id": session_id,
        "mesh_healing": {
            "status": heal_result["status"],
            "operations": heal_result["operations"],
            "input_faces": heal_result["input_faces"],
            "output_faces": heal_result["output_faces"],
            "holes_filled": heal_result["holes_filled"],
            "non_manifold_fixed": heal_result["non_manifold_fixed"]
        },
        "thickness_zones": {
            "zone_count": fields["thickness"]["zone_count"],
            "zones": []
        },
        "grain_analysis": {
            "coverage_pct": fields["grain"]["coverage_pct"],
            "mean_confidence": fields["grain"]["mean_confidence"],
            "runout_zones": fields["grain"]["runout_zones"],
            "checking_zones": fields["grain"]["checking_zones"]
        },
        "brace_graph": {
            "node_count": fields["brace"]["node_count"],
            "edge_count": fields["brace"]["edge_count"],
            "topology_valid": fields["brace"]["topology_valid"]
        },
        "retopo_metrics": retopo_result.get("metrics", {}),
        "overall_status": "pass",
        "provenance": {
            "tool_versions": {},
            "preset": preset,
            "source_mesh": str(src),
            "healed_mesh": str(healed),
            "retopo_mesh": str(retopo_path),
            "commit": None
        }
    }
    
    qa_path = out / "qa_core.json"
    write_json(qa_path, qa_core)
    
    # Step 5: Compose CAM Policy artifact
    cam_policy = _compose_cam_policy(
        model_id=model_id,
        qa_core=qa_core,
        fields=fields,
        preset=preset
    )
    
    policy_path = out / "cam_policy.json"
    write_json(policy_path, cam_policy)
    
    return {
        "qa_core_path": str(qa_path),
        "cam_policy_path": str(policy_path),
        "model_id": model_id,
        "preset": preset
    }


def _compose_cam_policy(
    *,
    model_id: str,
    qa_core: Dict[str, Any],
    fields: Dict[str, Any],
    preset: str
) -> Dict[str, Any]:
    """Compose a CAM policy from QA results and field analysis.
    
    This is the deterministic scaffold; real implementation will apply
    luthiery-specific heuristics from fields.
    """
    regions = [
        {
            "region_id": "global",
            "type": "standard",
            "stepdown_max_mm": 2.0,
            "stepover_max_pct": 40,
            "feed_rate_max_mm_min": 3000,
            "min_tool_diameter_mm": 3.0,
            "cut_direction": "climb"
        }
    ]
    
    # Add grain-sensitive regions
    for override in fields["grain"].get("cam_policy_overrides", []):
        regions.append({
            "region_id": override.get("zone_id", f"grain_zone_{len(regions)}"),
            "type": "grain_sensitive",
            **{k: v for k, v in override.items() if k != "zone_id"}
        })
    
    # Add no-cut zones from brace intersections
    for zone in fields["brace"].get("no_cut_zones", []):
        regions.append({
            "region_id": zone,
            "type": "no_cut"
        })
    
    # Add thickness-critical zones
    for zone in fields["thickness"].get("thickness_critical_zones", []):
        regions.append({
            "region_id": zone,
            "type": "thickness_critical",
            "stepdown_max_mm": 0.5,
            "stock_to_leave_mm": 0.2
        })
    
    return {
        "version": "1.0.0",
        "timestamp_utc": now(),
        "model_id": model_id,
        "source_qa_id": qa_core.get("session_id"),
        "global_defaults": {
            "stepdown_max_mm": 2.0,
            "stepover_max_pct": 40,
            "feed_rate_max_mm_min": 3000,
            "spindle_rpm_range": {"min": 10000, "max": 24000},
            "min_tool_diameter_mm": 3.0,
            "default_cut_direction": "climb"
        },
        "regions": regions,
        "coupling_flags": {
            "grain_coupled": True,
            "brace_coupled": True,
            "thickness_coupled": True
        },
        "provenance": {
            "preset": preset,
            "runner": "retopo.run",
            "commit": None
        }
    }
