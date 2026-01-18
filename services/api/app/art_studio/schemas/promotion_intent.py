from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field

from app.art_studio.schemas.rosette_params import RosetteParamSpec
from app.art_studio.schemas.rosette_feasibility import RosetteFeasibilitySummary


class PromotionIntentV1(BaseModel):
    """
    Canonical, non-executing promotion intent emitted by Art Studio.

    This payload expresses:
      - WHAT the design intent is
      - WHY it is considered feasible (RMOS output)
      - HOW it should be interpreted downstream (refs only)

    It does NOT:
      - generate toolpaths
      - execute CAM
      - create manufacturing authority
    """

    intent_version: Literal["v1"] = "v1"

    # Identity / governance
    session_id: str
    mode: str  # WorkflowMode
    created_at: datetime

    # Design intent (ornamental only)
    design: RosetteParamSpec

    # Feasibility context (read-only, RMOS-derived)
    feasibility: RosetteFeasibilitySummary

    # Deterministic fingerprints for traceability + caching
    design_fingerprint: str
    feasibility_fingerprint: str

    # Optional downstream hints (references only)
    requested_cam_profile_id: Optional[str] = None

    context_refs: Optional[Dict[str, str]] = None
    """
    Example:
      {
        "tool_id": "vbit_60",
        "material_id": "ebony",
        "machine_profile_id": "shopbot_alpha"
      }
    """

    risk_tolerance: Optional[Literal["GREEN_ONLY", "ALLOW_YELLOW"]] = None

    # Human-readable explanation (32.8.2)
    explain: Optional[Dict[str, List[str]]] = None
