"""
Business Startup Suite — Financial Planning for Luthiers

ARCHITECTURAL BOUNDARY:
    This module handles business/financial calculations.
    It does NOT touch manufacturing or safety systems.

ALLOWED IMPORTS:
    - app.core.*           (shared types, math)
    - app.calculators.*    (domain calculations for material estimates)

FORBIDDEN IMPORTS:
    - app.cam.*            (manufacturing, not business)
    - app.rmos.*           (safety, not business)
    - app.saw_lab.*        (production ops, not business)
    - app.analyzer.*       (acoustic analysis, not business)

PURPOSE:
    Help luthiers answer:
    - "What does it cost to build this guitar?"
    - "What should I charge?"
    - "When do I break even?"
    - "Can I afford to quit my day job?"

See: docs/BUSINESS_SUITE_SPEC.md
"""

from .schemas import (
    Material,
    LaborRate,
    BOMItem,
    BillOfMaterials,
    COGSBreakdown,
    PricingStrategy,
    BreakEvenAnalysis,
    CashFlowProjection,
)
from .bom_service import BOMService
from .cogs_service import COGSService
from .pricing_service import PricingService
from .breakeven_service import BreakEvenService
from .cashflow_service import CashFlowService

__all__ = [
    # Schemas
    "Material",
    "LaborRate",
    "BOMItem",
    "BillOfMaterials",
    "COGSBreakdown",
    "PricingStrategy",
    "BreakEvenAnalysis",
    "CashFlowProjection",
    # Services
    "BOMService",
    "COGSService",
    "PricingService",
    "BreakEvenService",
    "CashFlowService",
]
