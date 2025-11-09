"""
CAM Console Notifier Utility

Bridges external systems to Luthier's Tool Box CAM endpoints for:
- G-code simulation
- Feed/stepover/RPM optimization
- Energy metrics calculation

Usage:
    from app.util.cam_notifier import notify_cam_consoles
    
    results = notify_cam_consoles(
        project_id="les_paul_body",
        payload={
            "gcode": "G90\nG1 X10 Y10 F1200\n...",
            "target": "grbl",
            "settings": {
                "feed_rate_mm_min": 1200,
                "stepover_mm": 0.5,
                "rpm": 12000
            },
            "run_opt": True,
            "run_metrics": True
        }
    )
"""

from typing import Dict, Any, List
import httpx
import os

# Internal API base URL (overridable via environment variable)
INTERNAL_API_BASE = os.environ.get("LTB_INTERNAL_API_BASE", "http://localhost:8000")

# Exact endpoints in your Luthier's Tool Box API
EXACT_ENDPOINTS = {
    "simulate": "/api/cam_sim/simulate_gcode",
    "optimize": "/api/cam_opt/what_if",
    "energy": "/api/cam_metrics/energy",
}


def notify_cam_consoles(project_id: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Send payloads to your running CAM routers for simulation, optimization, and metrics.
    
    Args:
        project_id: Unique identifier for the project (e.g., "les_paul_body")
        payload: Dictionary containing:
            - gcode (str): G-code program to process
            - target (str): Target post-processor (e.g., "grbl", "mach4")
            - settings (dict): CAM settings with feed_rate_mm_min, stepover_mm, rpm
            - run_opt (bool): Whether to run optimization (default: True)
            - run_metrics (bool): Whether to calculate energy metrics (default: False)
    
    Returns:
        List of result dictionaries with status codes or error messages:
        [
            {"simulate": 200},
            {"optimize": 200},
            {"energy": 200}
        ]
    
    Example:
        results = notify_cam_consoles(
            project_id="pocket_operation",
            payload={
                "gcode": "G90\\nG1 X100 Y60 F1200\\n...",
                "target": "grbl",
                "settings": {
                    "feed_rate_mm_min": 1200,
                    "stepover_mm": 0.45,
                    "rpm": 18000
                },
                "run_opt": True,
                "run_metrics": True
            }
        )
    """
    results = []
    base = INTERNAL_API_BASE.rstrip("/")

    with httpx.Client(timeout=5.0) as client:
        # 1. Send to simulation endpoint
        try:
            r = client.post(f"{base}{EXACT_ENDPOINTS['simulate']}", json={
                "projectId": project_id,
                "gcode": payload.get("gcode"),
                "target": payload.get("target"),
                "settings": payload.get("settings"),
            })
            results.append({"simulate": r.status_code})
        except Exception as e:
            results.append({"simulate_error": str(e)})

        # 2. Optional optimization pass
        if payload.get("run_opt", True):
            try:
                r = client.post(f"{base}{EXACT_ENDPOINTS['optimize']}", json={
                    "projectId": project_id,
                    "target": payload.get("target"),
                    "feed_rate": payload["settings"].get("feed_rate_mm_min"),
                    "stepover": payload["settings"].get("stepover_mm", 0.5),
                    "rpm": payload["settings"].get("rpm", 12000),
                })
                results.append({"optimize": r.status_code})
            except Exception as e:
                results.append({"optimize_error": str(e)})

        # 3. Optional metrics
        if payload.get("run_metrics", False):
            try:
                r = client.post(f"{base}{EXACT_ENDPOINTS['energy']}", json={
                    "projectId": project_id,
                    "gcode": payload.get("gcode"),
                })
                results.append({"energy": r.status_code})
            except Exception as e:
                results.append({"energy_error": str(e)})

    return results
