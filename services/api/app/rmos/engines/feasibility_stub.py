"""
RMOS Stub Feasibility Engine

Test/dev engine that returns deterministic results.
Disabled in production by default (requires ALLOW_STUB_ENGINE=true).

Features:
- Always returns GREEN unless force_status is specified
- Supports force_status in spec for test injection
- Fast execution (no real calculations)
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from .base import EngineInfo, validate_result_contract


class StubFeasibilityEngine:
    """
    Stub feasibility engine for testing and development.

    Returns GREEN by default, or can be forced to return specific
    status via spec['force_status'].

    IMPORTANT: Disabled in production. Set ALLOW_STUB_ENGINE=true
    to enable (only for dev/test environments).
    """
    info = EngineInfo(
        engine_id="stub",
        version="0.0.0",
        description="Stub feasibility engine for tests/dev (disabled in production by default).",
    )

    def __init__(self):
        self.info.validate()

    def compute(
        self,
        *,
        spec: Optional[Dict[str, Any]],
        ctx: Any,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return stubbed feasibility result.

        Args:
            spec: Design parameters dict. Supports 'force_status' key
                  to inject specific status (GREEN, YELLOW, RED, ERROR).
            ctx: RmosContext (ignored by stub).
            request_id: Optional correlation ID.

        Returns:
            Dict with stubbed status and metadata.
        """
        t0 = time.perf_counter()

        # Production guard: disabled unless explicitly enabled
        allow = os.environ.get("ALLOW_STUB_ENGINE", "false").strip().lower()
        if allow not in ("1", "true", "yes", "on"):
            out = {
                "status": "ERROR",
                "reasons": ["stub engine disabled (set ALLOW_STUB_ENGINE=true to enable)"],
                "engine_id": self.info.engine_id,
                "engine_version": self.info.version,
                "request_id": request_id,
                "compute_ms": (time.perf_counter() - t0) * 1000.0,
                "overall_score": 0.0,
                "assessments": [],
                "is_feasible": False,
                "needs_review": True,
            }
            validate_result_contract(out)
            return out

        spec = spec or {}
        forced = spec.get("force_status")

        # Validate forced status is a valid enum value
        status = forced if forced in ("GREEN", "YELLOW", "RED", "ERROR") else "GREEN"

        # Build stubbed assessments
        assessments = [
            {
                "category": "chipload",
                "score": 90.0 if status == "GREEN" else 50.0,
                "risk": status if status != "ERROR" else "RED",
                "warnings": [] if status == "GREEN" else ["stub-forced"],
                "details": {"stub": True},
            },
            {
                "category": "heat",
                "score": 85.0 if status == "GREEN" else 45.0,
                "risk": status if status != "ERROR" else "RED",
                "warnings": [],
                "details": {"stub": True},
            },
        ]

        out = {
            "status": status,
            "reasons": [] if status == "GREEN" else ["stub-forced" if forced else "stub-non-green"],
            "engine_id": self.info.engine_id,
            "engine_version": self.info.version,
            "request_id": request_id,
            "compute_ms": (time.perf_counter() - t0) * 1000.0,
            "overall_score": 90.0 if status == "GREEN" else 40.0,
            "assessments": assessments,
            "is_feasible": status in ("GREEN", "YELLOW"),
            "needs_review": status in ("YELLOW", "RED", "ERROR"),
        }
        validate_result_contract(out)
        return out
