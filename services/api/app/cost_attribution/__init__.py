"""
Cost Attribution Module

Maps validated Smart Guitar telemetry to internal manufacturing cost dimensions.
Treats telemetry as untrusted input -> validated -> mapped -> internal cost facts.
"""

from .models import CostFact, CostDimension
from .policy import load_policy
from .mapper import telemetry_to_cost_facts
from .store import append_cost_facts, summarize_by_batch, summarize_by_instrument
from .api import router as cost_router

__all__ = [
    "CostFact",
    "CostDimension",
    "load_policy",
    "telemetry_to_cost_facts",
    "append_cost_facts",
    "summarize_by_batch",
    "summarize_by_instrument",
    "cost_router",
]
