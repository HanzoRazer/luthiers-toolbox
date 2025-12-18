"""
RMOS Baseline Feasibility Engine v1

Wraps the existing feasibility_fusion.evaluate_feasibility() with:
- Structured error handling (never throws to router)
- Timing instrumentation (compute_ms)
- Provenance stamping (engine_id, engine_version)
- Request correlation (request_id)
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from .base import EngineInfo, validate_result_contract


def _safe_import_fusion():
    """
    Safely import feasibility_fusion at module load.
    Captures import errors instead of crashing.
    """
    try:
        from services.api.app.rmos.feasibility_fusion import evaluate_feasibility
        return evaluate_feasibility, None
    except Exception as e:
        # Try relative import as fallback
        try:
            from ..feasibility_fusion import evaluate_feasibility
            return evaluate_feasibility, None
        except Exception as e2:
            return None, e2


_EVALUATE_FEASIBILITY, _IMPORT_ERR = _safe_import_fusion()


class BaselineFeasibilityEngineV1:
    """
    Baseline feasibility engine wrapping feasibility_fusion.

    This is the production engine that delegates to the full
    feasibility_fusion scoring pipeline (chipload, heat, deflection,
    rimspeed, BOM efficiency).
    """
    info = EngineInfo(
        engine_id="baseline_v1",
        version="1.0.0",
        description="Deterministic baseline feasibility (wraps feasibility_fusion + scorer policies).",
    )

    def __init__(self):
        # Validate metadata early (fail fast on bad engine metadata)
        self.info.validate()

    def compute(
        self,
        *,
        spec: Optional[Dict[str, Any]],
        ctx: Any,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute feasibility by delegating to feasibility_fusion.

        Args:
            spec: Design parameters dict (passed as 'design' to fusion)
            ctx: RmosContext (passed as 'context' to fusion)
            request_id: Optional correlation ID for tracing

        Returns:
            Dict with status, reasons, engine provenance, and timing.
        """
        t0 = time.perf_counter()

        # Guard: fusion import failed
        if _IMPORT_ERR is not None or _EVALUATE_FEASIBILITY is None:
            out = {
                "status": "ERROR",
                "reasons": [f"feasibility_fusion import failed: {_IMPORT_ERR}"],
                "engine_id": self.info.engine_id,
                "engine_version": self.info.version,
                "request_id": request_id,
                "compute_ms": (time.perf_counter() - t0) * 1000.0,
            }
            validate_result_contract(out)
            return out

        # Guard: null design
        design = spec or {}

        try:
            # NOTE: keep wrapper thin. Fusion owns scoring logic.
            # Fusion signature: evaluate_feasibility(design: Dict[str, Any], context: RmosContext)
            result = _EVALUATE_FEASIBILITY(design=design, context=ctx)

            # Normalize to dict (FeasibilityReport is a dataclass)
            if hasattr(result, "__dict__") and not isinstance(result, dict):
                # Dataclass - convert to dict
                from dataclasses import asdict
                result = asdict(result)
            elif hasattr(result, "model_dump"):
                # Pydantic model
                result = result.model_dump()
            elif not isinstance(result, dict):
                result = {"result": result}

            # Map overall_risk enum to status string
            overall_risk = result.get("overall_risk")
            if hasattr(overall_risk, "value"):
                status = overall_risk.value
            elif isinstance(overall_risk, str):
                status = overall_risk
            else:
                status = "ERROR"

            # Build standardized output
            out = {
                "status": status if status in ("GREEN", "YELLOW", "RED") else "ERROR",
                "reasons": result.get("recommendations", []),
                "overall_score": result.get("overall_score", 0.0),
                "assessments": [],
                "is_feasible": result.get("is_feasible", False) if callable(result.get("is_feasible")) is False else status != "RED",
                "needs_review": status in ("YELLOW", "RED"),
            }

            # Convert assessments if present
            assessments = result.get("assessments", [])
            for a in assessments:
                if hasattr(a, "__dict__") and not isinstance(a, dict):
                    from dataclasses import asdict
                    a = asdict(a)
                if isinstance(a, dict):
                    # Convert risk enum to string
                    risk = a.get("risk")
                    if hasattr(risk, "value"):
                        a["risk"] = risk.value
                    out["assessments"].append(a)

        except Exception as e:
            out = {
                "status": "ERROR",
                "reasons": [f"engine exception: {type(e).__name__}: {e}"],
                "overall_score": 0.0,
                "assessments": [],
                "is_feasible": False,
                "needs_review": True,
            }

        # Stamp provenance + observability
        out["engine_id"] = self.info.engine_id
        out["engine_version"] = self.info.version
        out["request_id"] = request_id
        out["compute_ms"] = (time.perf_counter() - t0) * 1000.0

        # Contract validation (fail-safe to ERROR)
        try:
            validate_result_contract(out)
        except Exception as e:
            out = {
                "status": "ERROR",
                "reasons": [f"result contract violation: {type(e).__name__}: {e}"],
                "engine_id": self.info.engine_id,
                "engine_version": self.info.version,
                "request_id": request_id,
                "compute_ms": (time.perf_counter() - t0) * 1000.0,
            }
            validate_result_contract(out)

        return out
