"""
CAM Intent Schema v1 - Frozen Contract

This module defines the canonical request envelope for CAM operations.
The schema is frozen and CI-guarded to prevent accidental drift.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CamUnitsV1(str, Enum):
    """Units for intent payloads. v1 supports mm/inch."""

    MM = "mm"
    INCH = "inch"


class CamModeV1(str, Enum):
    """
    CAM modes supported by v1 intent.

    NOTE: Extending this list is a versioned contract change.
    If/when you add more modes, bump the schema version (v2) or add a
    forward-compat strategy explicitly.
    """

    ROUTER_3AXIS = "router_3axis"
    SAW = "saw"
    # Legacy alias for router_3axis roughing operations
    ROUGHING = "roughing"


class CamIntentV1(BaseModel):
    """
    Canonical "CAM Intent" request surface (v1).

    This is *not* a toolpath or a run artifact. It's the normalized request envelope
    RMOS uses to:
      (1) validate inputs
      (2) plan/feasibility check
      (3) generate toolpaths
      (4) persist runs + attachments
    """

    schema_version: str = Field(default="cam_intent_v1", frozen=True)

    # Correlation / idempotency helpers (caller controlled)
    intent_id: Optional[str] = Field(
        default=None,
        description="Optional caller-provided idempotency/correlation ID.",
        examples=["intent_9f2c8c9e2a4b4f1a"],
    )

    # Mode selection for engine routing
    mode: CamModeV1 = Field(
        ...,
        description="Which CAM engine/mode should execute this intent.",
    )

    units: CamUnitsV1 = Field(
        default=CamUnitsV1.MM,
        description="Units used inside `design`/`context`/`options` payloads.",
    )

    # Optional catalog references (domain chooses how to interpret)
    tool_id: Optional[str] = Field(default=None, description="Tool identifier (e.g., endmill, saw blade).")
    material_id: Optional[str] = Field(default=None, description="Material identifier (e.g., spruce, maple).")
    machine_id: Optional[str] = Field(default=None, description="Machine identifier (router, saw station).")

    # Freeform but structured payload blocks. These are the workhorse surfaces.
    #
    # Contract:
    #   - `design` is REQUIRED and must contain the minimal design descriptor for the mode.
    #   - `context` is OPTIONAL operational context (feeds/speeds caps, fixtures, limits).
    #   - `options` is OPTIONAL execution options (preview flags, tolerances, etc.).
    design: Dict[str, Any] = Field(
        ...,
        description="Mode-specific design descriptor. Required.",
        examples=[{"geometry": {"type": "polyline", "points": [[0, 0], [10, 0]]}}],
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Operational context (feeds/speeds, constraints, environment).",
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution options (preview/quality flags, tolerances, etc.).",
    )

    # Audit-friendly metadata (caller controlled)
    requested_by: Optional[str] = Field(default=None, description="Optional user/session label (not auth).")
    created_at_utc: Optional[datetime] = Field(
        default=None,
        description="Optional caller-provided timestamp. If omitted, the server may set it.",
    )

    def with_created_now(self) -> "CamIntentV1":
        """Convenience for callers that want a timestamp but don't control the router."""
        if self.created_at_utc:
            return self
        return CamIntentV1(**{**self.model_dump(), "created_at_utc": datetime.utcnow()})


def _normalized_schema_json_for(model: type[BaseModel]) -> str:
    """
    Convert a Pydantic model JSON schema into a stable, normalized string
    for hashing in CI.
    """
    schema = model.model_json_schema()
    # Ensure stable output: sort keys, minimal separators
    return json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def cam_intent_schema_hash_v1() -> str:
    """
    Canonical hash for CamIntentV1 JSON schema (used for contract freeze).
    """
    normalized = _normalized_schema_json_for(CamIntentV1)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------------
# H7.1 Freeze Pin
#
# This constant is the "frozen contract" pin.
# If the schema changes intentionally, update:
#   1) docs/governance/CAM_INTENT_SCHEMA_V1.md
#   2) CAM_INTENT_SCHEMA_HASH_V1 below
#   3) any downstream SDK surface expecting the old schema
# ------------------------------------------------------------------------------

CAM_INTENT_SCHEMA_HASH_V1 = "9e2f47d2736314e91bf36196083a49b59c52373b0b9ec479d2e2533ac8e18b94"


def assert_cam_intent_schema_frozen_v1() -> None:
    """
    Raise AssertionError if the CamIntentV1 JSON schema differs from the pinned hash.
    Used by CI and unit tests to prevent accidental drift.
    """
    actual = cam_intent_schema_hash_v1()
    expected = CAM_INTENT_SCHEMA_HASH_V1
    if expected == "REPLACE_ME_AFTER_FIRST_RUN":
        raise AssertionError(
            "CAM_INTENT_SCHEMA_HASH_V1 is not pinned yet. "
            "Run `python -m app.ci.check_cam_intent_schema_hash --print` once, "
            "copy the printed hash into CAM_INTENT_SCHEMA_HASH_V1, and re-run CI."
        )
    if actual != expected:
        raise AssertionError(
            "CamIntentV1 schema hash mismatch (contract drift).\n"
            f"expected={expected}\n"
            f"actual={actual}\n"
            "If this change is intentional, bump/pin the schema hash and update docs."
        )
