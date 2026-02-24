"""
Engineering Cost Estimator — Parametric estimation for lutherie.

This module provides aerospace/automotive-style cost estimation:
- Complexity factors for design choices
- Learning curves for batch production
- Work breakdown structures
- Material yield/waste factors

ALLOWED IMPORTS:
    - Parent business module (..schemas, ..cogs_service, ..bom_service)
    - app.core.* (shared types)

FORBIDDEN IMPORTS:
    - app.cam.* (manufacturing execution, not estimation)
    - app.rmos.* (safety/feasibility, not costing)
"""

from .schemas import (
    EstimateRequest,
    EstimateResult,
    ComplexitySelections,
    WBSTask,
    LearningCurveProjection,
)
from .estimator_service import EngineeringEstimatorService

__all__ = [
    "EstimateRequest",
    "EstimateResult",
    "ComplexitySelections",
    "WBSTask",
    "LearningCurveProjection",
    "EngineeringEstimatorService",
]
