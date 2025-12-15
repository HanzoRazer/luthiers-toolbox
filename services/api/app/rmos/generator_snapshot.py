# services/api/app/rmos/generator_snapshot.py
"""
Generator Behavior Snapshot - Sample the constraint-aware generator and compute stats.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .api_contracts import RmosContext
from .models import SearchBudgetSpec, RosetteParamSpec
from .constraint_profiles import (
    RosetteGeneratorConstraints,
    resolve_constraints_for_context,
)
from .ai_policy import apply_global_policy_to_constraints

# Lazy import for structured generator
try:
    from ..ai_core.structured_generator import generate_constrained_candidate
except (ImportError, AttributeError, ModuleNotFoundError):
    def generate_constrained_candidate(**kwargs) -> RosetteParamSpec:  # type: ignore
        """Stub if ai_core not available."""
        return RosetteParamSpec()


@dataclass
class GeneratorSampleStats:
    """Summary statistics for a batch of generator samples."""

    tool_id: Optional[str]
    material_id: Optional[str]
    machine_id: Optional[str]

    n_samples: int
    profile: RosetteGeneratorConstraints

    ring_count_min: int
    ring_count_max: int
    ring_count_avg: float

    total_width_min_mm: float
    total_width_max_mm: float
    total_width_avg_mm: float


def _ring_count(design) -> int:
    rings = getattr(design, "rings", None)
    if not isinstance(rings, list):
        return 0
    return len(rings)


def _total_width_mm(design) -> float:
    """Estimate total radial width based on ring.width_mm fields."""
    rings = getattr(design, "rings", None)
    if not isinstance(rings, list):
        return 0.0

    total = 0.0
    for ring in rings:
        if not isinstance(ring, dict):
            continue
        w = ring.get("width_mm")
        if isinstance(w, (int, float)):
            total += float(w)
    return total


def snapshot_generator_behavior(
    *,
    ctx: RmosContext,
    budget: SearchBudgetSpec,
    n_samples: int = 50,
) -> GeneratorSampleStats:
    """
    Sample the constraint-aware generator n_samples times for a given
    RmosContext + SearchBudgetSpec and compute basic statistics.
    """
    if n_samples <= 0:
        raise ValueError("n_samples must be > 0")

    profile = resolve_constraints_for_context(ctx)
    profile = apply_global_policy_to_constraints(profile)

    ring_counts: List[int] = []
    total_widths: List[float] = []

    for i in range(1, n_samples + 1):
        design = generate_constrained_candidate(
            prev_design=None,
            constraints=profile,
            budget=budget,
            attempt_index=i,
        )
        rc = _ring_count(design)
        tw = _total_width_mm(design)

        ring_counts.append(rc)
        total_widths.append(tw)

    ring_count_min = min(ring_counts) if ring_counts else 0
    ring_count_max = max(ring_counts) if ring_counts else 0
    ring_count_avg = sum(ring_counts) / len(ring_counts) if ring_counts else 0.0

    total_width_min = min(total_widths) if total_widths else 0.0
    total_width_max = max(total_widths) if total_widths else 0.0
    total_width_avg = sum(total_widths) / len(total_widths) if total_widths else 0.0

    return GeneratorSampleStats(
        tool_id=getattr(ctx, "tool_id", None),
        material_id=getattr(ctx, "material_id", None),
        machine_id=getattr(ctx, "machine_profile_id", None),
        n_samples=n_samples,
        profile=profile,
        ring_count_min=ring_count_min,
        ring_count_max=ring_count_max,
        ring_count_avg=ring_count_avg,
        total_width_min_mm=total_width_min,
        total_width_max_mm=total_width_max,
        total_width_avg_mm=total_width_avg,
    )
