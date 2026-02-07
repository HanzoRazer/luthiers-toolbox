"""
AI-Assisted CAM Advisor (Wave 11)

Uses:
- Calculator Spine
- RMOS context
- Tool/material profiles
- AI large-model reasoning (stub hooks included)

This is the central brain analyzing toolpaths before export.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any

from .models import CAMAdvisory, CAMAnalysisResult

# Import Calculator Spine service
try:
    from ..calculators.service import (
        CutOperationSpec,
        evaluate_cut_operation,
    )
    CALCULATOR_AVAILABLE = True
except ImportError:
    CALCULATOR_AVAILABLE = False
    CutOperationSpec = None


class CAMAdvisor:
    """
    The central brain analyzing toolpaths before export.
    Produces warnings, errors, and recommended parameter changes.
    """

    def analyze_operation(
        self,
        tool_id: str,
        material_id: str,
        tool_kind: str,
        feed_mm_min: float,
        rpm: float,
        depth_of_cut_mm: float,
        width_of_cut_mm: Optional[float] = None,
        machine_id: Optional[str] = None,
    ) -> CAMAnalysisResult:
        """
        Analyze a cut operation and return advisories + recommendations.
        
        Args:
            tool_id: Tool identifier
            material_id: Material identifier
            tool_kind: "router_bit" or "saw_blade"
            feed_mm_min: Feed rate in mm/min
            rpm: Spindle speed
            depth_of_cut_mm: Depth of cut in mm
            width_of_cut_mm: Width of cut in mm (optional)
            machine_id: Machine profile ID (optional)
        
        Returns:
            CAMAnalysisResult with advisories, recommendations, and physics
        """
        advisories: List[CAMAdvisory] = []
        physics_results: Dict[str, Any] = {}
        
        # Evaluate physics if Calculator Spine is available
        if CALCULATOR_AVAILABLE and CutOperationSpec:
            try:
                spec = CutOperationSpec(
                    tool_id=tool_id,
                    material_id=material_id,
                    tool_kind=tool_kind,
                    feed_mm_min=feed_mm_min,
                    rpm=rpm,
                    depth_of_cut_mm=depth_of_cut_mm,
                    width_of_cut_mm=width_of_cut_mm,
                    machine_id=machine_id,
                )
                physics = evaluate_cut_operation(spec)
                physics_results = physics.as_dict() if hasattr(physics, 'as_dict') else {}
                
                # Chipload advisories
                chipload = physics_results.get("chipload", {})
                if chipload and not chipload.get("in_range", True):
                    advisories.append(
                        CAMAdvisory(
                            severity="warning",
                            message=f"Chipload is out of range: {chipload.get('chipload_mm', 'N/A')} mm/tooth",
                            context={"chipload": chipload.get("chipload_mm")},
                        )
                    )

                # Heat advisories
                heat = physics_results.get("heat", {})
                if heat and heat.get("category") == "HOT":
                    advisories.append(
                        CAMAdvisory(
                            severity="error",
                            message="Heat risk is high — consider lowering RPM or increasing feed.",
                            context={"heat_risk": heat.get("heat_risk")},
                        )
                    )

                # Deflection advisories
                deflection = physics_results.get("deflection", {})
                if deflection and deflection.get("risk") == "RED":
                    advisories.append(
                        CAMAdvisory(
                            severity="error",
                            message="Tool deflection is unsafe — reduce DOC or switch to stiffer tool.",
                            context={"deflection": deflection.get("deflection_mm")},
                        )
                    )

                # Saw kickback advisories
                kickback = physics_results.get("kickback", {})
                if kickback and kickback.get("category") == "HIGH":
                    advisories.append(
                        CAMAdvisory(
                            severity="error",
                            message="Kickback risk HIGH — change sequencing or blade.",
                        )
                    )

            except Exception as e:  # WP-1: keep broad — calculator spine can raise anything
                advisories.append(
                    CAMAdvisory(
                        severity="info",
                        message=f"Physics calculation unavailable: {str(e)}",
                    )
                )
        else:
            advisories.append(
                CAMAdvisory(
                    severity="info",
                    message="Calculator Spine not available — physics advisories disabled.",
                )
            )

        # Stub: potential AI-generated suggestions
        recommended_changes = {
            "feed_mm_min": None,
            "rpm": None,
            "depth_of_cut_mm": None,
            "note": "AI tuning stub — real tuning arrives in Wave 11.2",
        }

        return CAMAnalysisResult(
            advisories=advisories,
            recommended_changes=recommended_changes,
            physics_results=physics_results,
        )

    def analyze_toolpath(
        self,
        moves: List[Dict[str, Any]],
        tool_id: str,
        material_id: str,
    ) -> CAMAnalysisResult:
        """
        Analyze a full toolpath (list of moves) for safety issues.
        
        Args:
            moves: List of move dictionaries with x, y, z, f keys
            tool_id: Tool identifier
            material_id: Material identifier
        
        Returns:
            CAMAnalysisResult with advisories for the entire toolpath
        """
        advisories: List[CAMAdvisory] = []
        
        # Check for missing safe-Z retracts
        prev_z = None
        for i, move in enumerate(moves):
            z = move.get("z")
            if z is not None and prev_z is not None:
                # Plunge without retract warning
                if prev_z < 0 and z < prev_z:
                    advisories.append(
                        CAMAdvisory(
                            severity="warning",
                            message=f"Move {i}: Deep plunge without safe-Z retract",
                            context={"move_index": i, "z": z, "prev_z": prev_z},
                        )
                    )
            prev_z = z if z is not None else prev_z

        return CAMAnalysisResult(
            advisories=advisories,
            recommended_changes={},
            physics_results={},
        )
