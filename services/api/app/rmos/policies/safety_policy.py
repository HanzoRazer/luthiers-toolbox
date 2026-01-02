"""
RMOS Safety Policy - Centralized Feasibility Gate Logic

Per ADR-003 and OPERATION_EXECUTION_GOVERNANCE_v1.md:

- RED always blocks (when RMOS_BLOCK_ON_RED=true)
- UNKNOWN is treated as RED (when RMOS_TREAT_UNKNOWN_AS_RED=true)

Routers should:
  1) Compute feasibility via compute_feasibility_internal()
  2) decision = SafetyPolicy.extract_safety_decision(feasibility)
  3) if SafetyPolicy.should_block(decision.risk_level):
        create BLOCKED artifact, raise HTTP 409

Environment Variables:
  RMOS_BLOCK_ON_RED (default: true) - Block on RED risk level
  RMOS_TREAT_UNKNOWN_AS_RED (default: true) - Treat UNKNOWN/ERROR as RED

This module is governance-critical and must remain free of RMOS-only
business logic dependencies (no RunStore writes, no workflow imports).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class RiskLevel(str, Enum):
    """Risk levels for feasibility assessment."""
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


def _env_bool(name: str, default: bool) -> bool:
    """Parse boolean from environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "y", "on")


@dataclass(frozen=True)
class SafetyDecision:
    """
    Normalized safety decision extracted from feasibility payload.

    Immutable to prevent accidental mutation after extraction.
    """
    risk_level: RiskLevel
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def risk_level_str(self) -> str:
        """Return risk level as string for serialization."""
        return self.risk_level.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for artifact persistence."""
        return {
            "risk_level": self.risk_level.value,
            "score": self.score,
            "block_reason": self.block_reason,
            "warnings": self.warnings,
        }


class SafetyPolicy:
    """
    Central safety gate policy.

    Defaults are strict (block on RED and UNKNOWN).
    Configure via environment variables:
      - RMOS_BLOCK_ON_RED (default: true)
      - RMOS_TREAT_UNKNOWN_AS_RED (default: true)
    """

    BLOCK_ON_RED: bool = _env_bool("RMOS_BLOCK_ON_RED", True)
    TREAT_UNKNOWN_AS_RED: bool = _env_bool("RMOS_TREAT_UNKNOWN_AS_RED", True)

    @classmethod
    def should_block(cls, risk_level: Union[RiskLevel, str, None]) -> bool:
        """
        Determine if operation should be blocked based on risk level.

        Per governance contract:
        - RED always blocks (if BLOCK_ON_RED)
        - UNKNOWN/ERROR blocks (if TREAT_UNKNOWN_AS_RED)
        - GREEN/YELLOW never block
        """
        level = cls._to_risk_level(risk_level)

        if level == RiskLevel.RED and cls.BLOCK_ON_RED:
            return True

        if level in (RiskLevel.UNKNOWN, RiskLevel.ERROR) and cls.TREAT_UNKNOWN_AS_RED:
            return True

        return False

    @staticmethod
    def _to_risk_level(val: Union[RiskLevel, str, None]) -> RiskLevel:
        """
        Safely convert any value to RiskLevel.

        Returns UNKNOWN for invalid/missing values (fail-safe).
        """
        if isinstance(val, RiskLevel):
            return val
        if not val:
            return RiskLevel.UNKNOWN
        s = str(val).strip().upper()
        return RiskLevel.__members__.get(s, RiskLevel.UNKNOWN)

    @classmethod
    def extract_safety_decision(cls, feasibility: Optional[Dict[str, Any]]) -> SafetyDecision:
        """
        Normalize nested/flat feasibility payloads into a consistent SafetyDecision.

        Supported shapes (checked in order):
          1. Flat: {"risk_level": "...", "score": ..., "warnings": [...]}
          2. Nested decision: {"decision": {"risk_level": "...", ...}}
          3. Nested safety: {"safety": {"risk_level": "...", ...}}

        INVARIANT: This function NEVER throws on weird inputs.
        If it can't parse, it returns UNKNOWN (which blocks by default policy).
        """
        if not isinstance(feasibility, dict):
            return SafetyDecision(
                risk_level=RiskLevel.UNKNOWN,
                block_reason="Feasibility payload missing or not a dict",
                warnings=["Missing feasibility payload"],
            )

        # Candidate locations (flat or nested)
        candidates: List[Dict[str, Any]] = [feasibility]

        for key in ("decision", "safety"):
            nested = feasibility.get(key)
            if isinstance(nested, dict):
                candidates.append(nested)

        # Find first candidate with a valid risk_level
        for d in candidates:
            rl = d.get("risk_level")
            if isinstance(rl, str) and rl.strip():
                level = cls._to_risk_level(rl)
                warnings = cls._normalize_warnings(d.get("warnings"))
                return SafetyDecision(
                    risk_level=level,
                    score=cls._safe_float(d.get("score")),
                    block_reason=d.get("block_reason"),
                    warnings=warnings,
                )

        # No risk level found anywhere
        return SafetyDecision(
            risk_level=RiskLevel.UNKNOWN,
            block_reason="Could not extract risk_level from feasibility payload",
            warnings=["Missing risk_level in feasibility payload"],
        )

    @staticmethod
    def _normalize_warnings(warnings: Any) -> List[str]:
        """Safely normalize warnings to list of strings."""
        if warnings is None:
            return []
        if isinstance(warnings, list):
            return [str(w) for w in warnings]
        return [str(warnings)]

    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        """Safely convert to float, return None on failure."""
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None
