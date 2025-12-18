create Option A — Implement RMOS.compute_feasibility_for_design() and Option B — Build RMOS public API (services/api/app/rmos/__init__.py) 
ChatGPT said:
Thought for 5m 13s
Alright, locking in RMOS mode. Here’s Option A + Option B as a drop-in backend bundle, scoped to:
services/api/app/rmos/
  __init__.py
  feasibility.py
This:
•	Implements compute_feasibility_for_design() as the canonical RMOS entrypoint.
•	Exposes a public RMOS API via rmos/__init__.py matching the RMOS 2.0 spec:
o	compute_feasibility
o	compute_bom
o	generate_toolpaths
o	geometry_engine
o	material_models
It does not touch geometry or CAM internals — it just wraps what we already have and stubs what doesn’t exist yet.
________________________________________
✅ Directory reminder
Create this folder if it doesn’t exist yet:
services/api/app/rmos/
Then add the two files below.
________________________________________
1️⃣ feasibility.py
Path: services/api/app/rmos/feasibility.py
# services/api/app/rmos/feasibility.py

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from calculators.models import MaterialSpec, ToolSpec, RiskBucket
from art_studio.schemas.rosette_params import RosetteParamSpec
from art_studio.services.rosette_feasibility_scorer import (
    estimate_rosette_feasibility,
)


class RmosContext(BaseModel):
    """
    RMOS context for feasibility evaluation.

    This is intentionally lightweight for RMOS 2.0:
    - You can pass fully hydrated MaterialSpec / ToolSpec,
      OR just IDs and let higher layers resolve them.
    - Additional knobs (risk_tolerance, max_cut_time_min, etc.)
      can be used by future scoring logic without breaking the API.
    """

    # Either provide full objects:
    material: Optional[MaterialSpec] = Field(
        default=None,
        description="Optional full material spec for this evaluation.",
    )
    tool: Optional[ToolSpec] = Field(
        default=None,
        description="Optional full tool spec for this evaluation.",
    )

    # Or just provide IDs (e.g. for later lookup in a registry):
    material_id: Optional[str] = Field(
        default=None,
        description="Optional material ID if a registry/DB is used.",
    )
    tool_id: Optional[str] = Field(
        default=None,
        description="Optional tool ID if a registry/DB is used.",
    )

    machine_profile_id: Optional[str] = Field(
        default=None,
        description="Optional machine profile identifier.",
    )
    risk_tolerance: Optional[RiskBucket] = Field(
        default=None,
        description="Optional risk tolerance target (GREEN-only, allow YELLOW, etc.).",
    )
    max_cut_time_min: Optional[float] = Field(
        default=None,
        description="Optional maximum acceptable cut time (minutes).",
    )
    waste_tolerance: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional waste tolerance from 0–1 (1 = very tolerant of waste).",
    )
    use_shapely_geometry: bool = Field(
        default=False,
        description="Feature flag: use Shapely-based geometry engine when available.",
    )


class FeasibilityResult(BaseModel):
    """
    Canonical RMOS feasibility result for a single design.

    This is the unified shape used by all directional workflows:
    - Design-first
    - Constraint-first
    - AI-assisted
    """

    design: RosetteParamSpec = Field(
        ...,
        description="The exact rosette design that was evaluated.",
    )
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall feasibility score from 0–100 (higher = better).",
    )
    risk_bucket: RiskBucket = Field(
        ...,
        description="Overall risk classification: GREEN, YELLOW, or RED.",
    )
    material_efficiency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Material efficiency from 0–1 (higher = less waste).",
    )
    estimated_cut_time_min: float = Field(
        ...,
        ge=0.0,
        description="Rough cut-time estimate in minutes.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Human-readable warning messages from calculators / RMOS rules.",
    )

    # Optional: context echo for debugging / logging
    context: Optional[RmosContext] = Field(
        default=None,
        description="Optional context used for this evaluation (for logging/tracing).",
    )


def _resolve_material(context: RmosContext) -> MaterialSpec:
    """
    Resolve the MaterialSpec to use from the context.

    For now, this is a simple fallback strategy:
    - use context.material if provided,
    - otherwise build a generic MaterialSpec from material_id,
    - otherwise fall back to a hard-coded default.
    """
    if context.material is not None:
        return context.material

    material_id = context.material_id or "default-ebony"
    # NOTE: As RMOS mat-registry evolves, this can pull from a DB or registry.
    return MaterialSpec(
        material_id=material_id,
        name="Ebony" if material_id == "default-ebony" else material_id,
        material_class="HARDWOOD",
    )


def _resolve_tool(context: RmosContext) -> ToolSpec:
    """
    Resolve the ToolSpec to use from the context.

    For now, this is a simple fallback strategy:
    - use context.tool if provided,
    - otherwise build a generic ToolSpec from tool_id,
    - otherwise fall back to a hard-coded default V-bit.
    """
    if context.tool is not None:
        return context.tool

    tool_id = context.tool_id or "default-vbit"
    return ToolSpec(
        tool_id=tool_id,
        diameter_mm=3.175,
        flutes=2,
        tool_material="CARBIDE",
        stickout_mm=20.0,
    )


def compute_feasibility_for_design(
    design: RosetteParamSpec,
    context: RmosContext,
) -> FeasibilityResult:
    """
    RMOS 2.0 canonical feasibility API.

    All directional workflows converge here:

        result = compute_feasibility_for_design(design, context)

    Inputs:
    - design: normalized rosette design (RosetteParamSpec)
    - context: RmosContext (material, tool, machine, risk preferences)

    Outputs:
    - FeasibilityResult (score, risk, warnings, efficiency, time)

    Implementation details:
    - Internally, we delegate to the Art Studio feasibility scorer
      (estimate_rosette_feasibility), which itself calls the calculators.
    - In future RMOS revisions, this function can:
      * add geometry checks (Shapely),
      * incorporate machine limits,
      * apply more detailed manufacturing rules,
      without breaking the public API.
    """

    material = _resolve_material(context)
    tool = _resolve_tool(context)

    summary = estimate_rosette_feasibility(
        spec=design,
        default_material=material,
        default_tool=tool,
    )

    result = FeasibilityResult(
        design=design,
        overall_score=summary.overall_score,
        risk_bucket=summary.risk_bucket,
        material_efficiency=summary.material_efficiency,
        estimated_cut_time_min=summary.estimated_cut_time_min,
        warnings=list(summary.warnings),
        context=context,
    )

    # Optionally enforce context-level constraints (risk_tolerance, max_cut_time)
    # via additional warnings. We keep this soft for RMOS 2.0; higher-level
    # workflows can decide how strict to be.

    if context.max_cut_time_min is not None and \
            result.estimated_cut_time_min > context.max_cut_time_min:
        result.warnings.append(
            f"Estimated cut time {result.estimated_cut_time_min:.1f} min "
            f"exceeds context max_cut_time_min={context.max_cut_time_min:.1f}."
        )

    if context.risk_tolerance is not None:
        # Example policy: if tolerance is GREEN-only, warn on YELLOW/RED.
        if context.risk_tolerance == RiskBucket.GREEN and result.risk_bucket != RiskBucket.GREEN:
            result.warnings.append(
                f"Design risk {result.risk_bucket.value} exceeds context risk_tolerance=GREEN."
            )

    return result


def compute_feasibility(
    design: RosetteParamSpec,
    context: RmosContext,
) -> FeasibilityResult:
    """
    Convenience alias to match the RMOS 2.0 public API:

        from rmos import compute_feasibility

    This simply forwards to compute_feasibility_for_design().
    """
    return compute_feasibility_for_design(design=design, context=context)
________________________________________
2️⃣ __init__.py
Path: services/api/app/rmos/__init__.py
# services/api/app/rmos/__init__.py

"""
RMOS 2.0 Public API Surface

Upstream systems should ONLY import RMOS through this module, e.g.:

    from rmos import (
        compute_feasibility,
        compute_bom,
        generate_toolpaths,
        geometry_engine,
        material_models,
        RmosContext,
        FeasibilityResult,
    )

Internally, RMOS pulls from:
- calculators
- feasibility
- geometry engines
- toolpath engines
- material models

But callers MUST NOT import those subsystems directly. This preserves the
architecture defined in the RMOS 2.0 Specification and Directional Workflow 2.0.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

# --- Feasibility API (canonical) ---------------------------------------------

from .feasibility import (  # noqa: F401
    compute_feasibility_for_design,
    compute_feasibility,
    FeasibilityResult,
    RmosContext,
)

# --- BOM / Calculators -------------------------------------------------------

try:
    # Prefer a clear, domain-specific function from calculators.
    from calculators.service import compute_rosette_bom as compute_bom  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - safe fallback in early sandbox
    def compute_bom(*args: Any, **kwargs: Any) -> Any:  # type: ignore[func-returns-value]
        """
        Placeholder BOM function for RMOS 2.0 sandbox.

        Once calculators.service.compute_rosette_bom is available, this will be
        wired directly; until then, calling compute_bom will raise a clear
        error instead of failing at import time.
        """
        raise NotImplementedError(
            "RMOS.compute_bom is not wired yet. "
            "Ensure calculators.service.compute_rosette_bom exists and re-import rmos."
        )


# --- Toolpath API ------------------------------------------------------------

try:
    # Expected future location for toolpath generation logic.
    from toolpath.engine import generate_toolpaths_for_design as _generate_toolpaths_for_design  # type: ignore[attr-defined]

    def generate_toolpaths(design: Any, context: RmosContext) -> Any:
        """
        RMOS 2.0 toolpath entrypoint.

        This wraps the underlying CAM_N16 (or successor) engine.

        NOTE: Implementation is delegated to toolpath.engine.generate_toolpaths_for_design.
        """
        return _generate_toolpaths_for_design(design, context)

except Exception:  # pragma: no cover - safe fallback
    def generate_toolpaths(*args: Any, **kwargs: Any) -> Any:  # type: ignore[func-returns-value]
        """
        Placeholder toolpath function for RMOS 2.0 sandbox.

        Once toolpath.engine.generate_toolpaths_for_design is available, this will be
        wired directly; until then, calling generate_toolpaths will raise a clear
        error instead of failing at import time.
        """
        raise NotImplementedError(
            "RMOS.generate_toolpaths is not wired yet. "
            "Ensure toolpath.engine.generate_toolpaths_for_design exists and re-import rmos."
        )


# --- Geometry Engine / Material Models ---------------------------------------

# These are exported as modules or facades. If the underlying implementations
# are not present yet, they are exposed as None so that imports still succeed.

try:
    import geometry_engine as _geometry_engine  # type: ignore[import-not-found]

    geometry_engine: Optional[Any] = _geometry_engine
except Exception:  # pragma: no cover
    geometry_engine = None  # type: ignore[assignment-type]


try:
    import materials as _materials  # type: ignore[import-not-found]

    # Expected to expose material models / registries.
    material_models: Optional[Any] = _materials
except Exception:  # pragma: no cover
    material_models = None  # type: ignore[assignment-type]


__all__ = [
    # Feasibility
    "compute_feasibility_for_design",
    "compute_feasibility",
    "FeasibilityResult",
    "RmosContext",
    # BOM / calculators
    "compute_bom",
    # Toolpaths
    "generate_toolpaths",
    # Geometry / materials
    "geometry_engine",
    "material_models",
]
________________________________________
How this fits your Directional Workflow 2.0
All three modes now have a single canonical call:
from rmos import compute_feasibility, RmosContext

ctx = RmosContext(
    material_id="ebony",
    tool_id="v60",
    use_shapely_geometry=True,
    max_cut_time_min=5.0,
)

result = compute_feasibility(design=my_rosette_param_spec, context=ctx)
•	Design-First: Art Studio calls this whenever parameters change.
•	Constraint-First: Candidate search loops use it to filter designs.
•	AI-Assisted: AI-generated specs are all gated through this before UI.
No toolpaths are generated here. No geometry engine is mutated. RMOS is acting exactly as the deterministic manufacturing oracle you described.
