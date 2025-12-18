"""
RMOS Feasibility Engine Base Types

Protocol definitions and validation for feasibility engines.
Ensures consistent output contract across all engine implementations.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Literal

RiskStatus = Literal["GREEN", "YELLOW", "RED", "ERROR"]

_ENGINE_ID_RE = re.compile(r"^[A-Za-z0-9_]+$")
_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


@dataclass(frozen=True)
class EngineInfo:
    """Metadata for a feasibility engine."""
    engine_id: str
    version: str
    description: str

    def validate(self) -> None:
        """Validate engine_id and version format."""
        if not _ENGINE_ID_RE.match(self.engine_id):
            raise ValueError(f"Invalid engine_id '{self.engine_id}'. Use alphanumeric + underscore only.")
        if not _SEMVER_RE.match(self.version):
            raise ValueError(f"Invalid version '{self.version}'. Must be semver, e.g. 1.2.3")


class FeasibilityEngine(Protocol):
    """Protocol for feasibility engine implementations."""
    info: EngineInfo

    def compute(
        self,
        *,
        spec: Optional[Dict[str, Any]],
        ctx: Any,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute feasibility for given design spec and context.

        Returns dict with required fields:
            - engine_id: str
            - engine_version: str
            - status: GREEN | YELLOW | RED | ERROR
            - reasons: List[str]
            - compute_ms: float
            - request_id: Optional[str]
        """
        ...


def validate_result_contract(result: Dict[str, Any]) -> None:
    """
    Validate that engine result contains all required fields.

    Raises ValueError if contract is violated.
    """
    # Required provenance
    if "engine_id" not in result or "engine_version" not in result:
        raise ValueError("Engine result missing engine_id/engine_version")

    # status
    status = result.get("status")
    if status not in ("GREEN", "YELLOW", "RED", "ERROR"):
        raise ValueError(f"Invalid status '{status}'. Must be GREEN/YELLOW/RED/ERROR")

    # reasons list
    reasons = result.get("reasons")
    if reasons is None or not isinstance(reasons, list):
        raise ValueError("reasons must be a list")

    # compute_ms (optional but recommended; enforce numeric if present)
    if "compute_ms" in result:
        if not isinstance(result["compute_ms"], (int, float)):
            raise ValueError("compute_ms must be numeric")
