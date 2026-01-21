"""
Mesh Pipeline runner (scaffold):
 - intake/heal (stub)
 - choose adapter (miq|qrm) via preset
 - emit qa_core.json and cam_policy.json per contracts
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from app.retopo import miq_adapter, qrm_adapter
from app.mesh.o3d_heal import heal_mesh, HealReport
from app.fields.grain_field.service import GrainFieldService
from app.fields.brace_graph.service import BraceGraphService
from app.fields.thickness_map.service import ThicknessMapService


def now() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def write_json(p: Path, d: Dict[str, Any]) -> None:
    """Write a dict as JSON to a file, creating parent dirs as needed."""
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")


def _heal_mesh(input_mesh: Path, out_dir: Path) -> HealReport:
    """Mesh healing step using Open3D (or fallback OBJ parser).
    
    Computes real topology QA counts: holes (boundary loops), non-manifold edges,
    edge length stats, and performs basic cleanup when Open3D is available.
    """
    healed = out_dir / "healed.obj"
    report = heal_mesh(input_mesh, healed, weld_tol=0.0)
    return report


def run_pipeline(
    input_mesh: str,
    model_id: str,
    preset: str,
    out_dir: str,
    session_id: str | None = None
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
    
    # Step 1: Heal mesh (Open3D when available, else fallback OBJ parser)
    heal_report = _heal_mesh(src, out)
    healed = Path(heal_report.out_mesh_path)
    
    # Step 2: Choose retopo adapter and run
    presets_root = Path("presets/retopo")
    if preset == "miq":
        preset_path = presets_root / "miq" / "preset.json"
        retopo_result = miq_adapter.run(str(healed), str(preset_path), str(out))
    else:
        preset_path = presets_root / "qrm" / "preset.json"
        retopo_result = qrm_adapter.run(str(healed), str(preset_path), str(out))
    
    retopo_path = Path(retopo_result["retopo_mesh_path"])
    retopo_path.write_text("# stub retopo OBJ\n")
    
    # Step 3: Compute fields (use existing services)
    grain_svc = GrainFieldService()
    brace_svc = BraceGraphService()
    thick_svc = ThicknessMapService()
    
    # These would normally take real mesh data; stubs for now
    # Services return typed dataclass results
    grain_result = grain_svc.analyze(model_id=model_id, geometry=None)
    brace_result = brace_svc.analyze(model_id=model_id, geometry=None)
    thick_result = thick_svc.analyze(model_id=model_id, geometry=None)
    
    # Step 4: Compose QA Core artifact
    qa_core = {
        "version": "1.0.0",
        "timestamp_utc": now(),
        "model_id": model_id,
        "session_id": session_id,
        "mesh_healing": {
            "status": "clean" if heal_report.holes == 0 and heal_report.nonmanifold_edges == 0 else "issues_detected",
            "holes": heal_report.holes,
            "nonmanifold_edges": heal_report.nonmanifold_edges,
            "vertices": heal_report.vertices,
            "faces": heal_report.faces,
            "self_intersections": heal_report.self_intersections,
            "edge_length_mean": heal_report.edge_length_mean,
            "edge_length_std": heal_report.edge_length_std,
            "notes": heal_report.notes
        },
        "thickness_zones": {
            "zone_count": len(thick_result.zones) if hasattr(thick_result, 'zones') else 0,
            "zones": []
        },
        "grain_analysis": {
            "coverage_pct": grain_result.coverage_pct if hasattr(grain_result, 'coverage_pct') else 0,
            "mean_confidence": grain_result.mean_confidence if hasattr(grain_result, 'mean_confidence') else 0,
            "runout_zones": [],
            "checking_zones": []
        },
        "brace_graph": {
            "node_count": brace_result.node_count if hasattr(brace_result, 'node_count') else 0,
            "edge_count": brace_result.edge_count if hasattr(brace_result, 'edge_count') else 0,
            "topology_valid": brace_result.topology_valid if hasattr(brace_result, 'topology_valid') else True
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
        grain_result=grain_result,
        brace_result=brace_result,
        thick_result=thick_result,
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
    grain_result: Any,
    brace_result: Any,
    thick_result: Any,
    preset: str
) -> Dict[str, Any]:
    """Compose a CAM policy from QA results.
    
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
    
    # Add grain-sensitive regions from grain analysis
    if hasattr(grain_result, 'cam_policy_overrides'):
        for override in grain_result.cam_policy_overrides:
            regions.append({
                "region_id": override.get("zone_id", "grain_zone"),
                "type": "grain_sensitive",
                **override
            })
    
    # Add no-cut zones from brace intersections
    if hasattr(brace_result, 'no_cut_zones'):
        for zone in brace_result.no_cut_zones:
            regions.append({
                "region_id": zone,
                "type": "no_cut"
            })
    
    # Add thickness-critical zones
    if hasattr(thick_result, 'thickness_critical_zones'):
        for zone in thick_result.thickness_critical_zones:
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
