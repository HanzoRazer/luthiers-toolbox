"""
Rosette Feasibility Schemas - Bundle 31.0.27

Lightweight feasibility preview response models for Art Studio rosette designs.
"""

from typing import List, Optional
from pydantic import BaseModel

from ...rmos.api_contracts import RiskBucket
from .rosette_params import RosetteParamSpec


class RosetteFeasibilitySummary(BaseModel):
    """
    Lightweight feasibility preview for a single rosette design.
    """
    suggestion_id: Optional[str] = None
    run_id: Optional[str] = None  # Points to persisted RunArtifact

    overall_score: float
    risk_bucket: RiskBucket

    material_efficiency: float
    estimated_cut_time_min: float
    warnings: List[str] = []


class RosetteFeasibilityBatchRequest(BaseModel):
    specs: List[RosetteParamSpec]
    suggestion_ids: Optional[List[str]] = None


class RosetteFeasibilityBatchResponse(BaseModel):
    summaries: List[RosetteFeasibilitySummary]
