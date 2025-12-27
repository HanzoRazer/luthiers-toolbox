"""
RMOS CAM domain package.

H7.1: CAM Intent Schema Freeze
------------------------------
The canonical CAM "Intent" payload is defined in `schemas_intent.py`.

Invariant:
  - All CAM entrypoints (routers, SDK, CLI, internal callers) should accept/emit
    `CamIntentV1` for the *request* surface unless explicitly version-bumped.
"""

from .normalize_intent import (
    CamIntentIssue,
    CamIntentValidationError,
    normalize_cam_intent_v1,
)
from .schemas_intent import (
    CamIntentV1,
    CamModeV1,
    CamUnitsV1,
    cam_intent_schema_hash_v1,
)

__all__ = [
    "CamIntentIssue",
    "CamIntentV1",
    "CamIntentValidationError",
    "CamModeV1",
    "CamUnitsV1",
    "cam_intent_schema_hash_v1",
    "normalize_cam_intent_v1",
]
