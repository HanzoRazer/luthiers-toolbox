Here’s a drop-in Saw Lab 2.0 Code Skeleton bundle you can wire into the existing ToolBox / RMOS repo.

I’ll assume backend layout like:

services/api/app/
  rmos/
  toolpath/
  calculators/
  ...


Saw Lab 2.0 will live under:

services/api/app/saw_lab/


and plug into RMOS via toolpath/saw_engine.py.

🗂 Folder + File Layout

Create these:

services/api/app/saw_lab/
  __init__.py
  models.py
  geometry.py
  path_planner.py
  toolpath_builder.py
  risk_evaluator.py
  calculators/
    __init__.py
    saw_heat.py
    saw_deflection.py
    saw_rimspeed.py
    saw_bite_load.py
    saw_kickback.py


Plus one integration file:

services/api/app/toolpath/saw_engine.py


And a small patch to your existing toolpath/service.py to delegate saw jobs.

1️⃣ services/api/app/saw_lab/__init__.py
"""
saw_lab/__init__.py

Saw Lab 2.0 – RMOS-integrated CNC saw-blade toolpath mode.

This package provides:
- Blade + material models
- Saw-specific calculators (heat, deflection, rim speed, kickback)
- Kerf-aware path planner
- Toolpath builder that emits RmosToolpathPlan-compatible operations
- Risk evaluator used by RMOS feasibility engine

Saw Lab 2.0 is activated when RmosContext.tool_id
identifies a saw blade (e.g. "saw:thin_kerf_140mm").
"""

from .models import (
    SawBladeSpec,
    SawMaterialSpec,
    SawCutMode,
    SawLabConfig,
)

__all__ = [
    "SawBladeSpec",
    "SawMaterialSpec",
    "SawCutMode",
    "SawLabConfig",
]

2️⃣ services/api/app/saw_lab/models.py
"""
saw_lab/models.py

Core data models for Saw Lab 2.0.

These models are used by:
- calculators/*
- path_planner.py
- toolpath_builder.py
- risk_evaluator.py
- toolpath/saw_engine.py
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class SawCutMode(str, Enum):
    RIP = "RIP"
    CROSSCUT = "CROSSCUT"
    COMPOUND = "COMPOUND"
    UNKNOWN = "UNKNOWN"


class SawBladeSpec(BaseModel):
    """
    Basic saw blade geometry + limits.

    In a real system, this would be loaded from a tool library.
    """

    blade_id: str
    diameter_mm: float = Field(..., gt=0.0)
    kerf_mm: float = Field(..., gt=0.0)
    plate_thickness_mm: float = Field(..., gt=0.0)

    tooth_count: int = Field(..., gt=0)
    hook_angle_deg: float = 0.0  # positive = more aggressive
    top_grind: str = "ATB"  # e.g. ATB, TCG, FTG

    max_rim_speed_m_per_min: float = 4000.0
    recommended_feed_mm_per_tooth: float = 0.03
    max_depth_of_cut_mm: float = 40.0

    # Extra metadata
    manufacturer: Optional[str] = None
    notes: Optional[str] = None


class SawMaterialSpec(BaseModel):
    """
    Saw-specific material properties (species-level).
    """

    material_id: str
    density_kg_m3: float = 700.0
    burn_risk_threshold: float = 0.7  # 0..1
    tearout_sensitivity: float = 0.5  # 0..1
    hardness_scale: float = 0.5       # 0..1


class SawCutContext(BaseModel):
    """
    Per-cut context passed around inside Saw Lab.
    """

    blade: SawBladeSpec
    material: SawMaterialSpec
    cut_mode: SawCutMode = SawCutMode.UNKNOWN

    feed_mm_min: float = 1500.0
    rpm: float = 4000.0

    # For kerf planner / BOM:
    stock_length_mm: Optional[float] = None
    desired_piece_lengths_mm: List[float] = []


class SawLabConfig(BaseModel):
    """
    Global tuning knobs for Saw Lab 2.0.
    """

    # Risk thresholds
    max_allowed_rim_speed_m_per_min: float = 4500.0
    max_allowed_burn_risk: float = 0.8
    max_allowed_kickback_risk: float = 0.8

    # Planning
    min_piece_gap_mm: float = 2.0
    default_cut_mode: SawCutMode = SawCutMode.RIP

3️⃣ services/api/app/saw_lab/geometry.py
"""
saw_lab/geometry.py

Geometry helpers for Saw Lab 2.0.

All geometry operations go through the shared RMOS geometry engine
(ML or Shapely), never directly to Shapely here. This keeps Saw Lab
aligned with the rest of RMOS.
"""

from __future__ import annotations

from typing import List

from rmos import get_geometry_engine
from rmos.api_contracts import RmosContext
from toolpath.geometry_engine import MLPath  # shared path representation


def offset_kerf_region(
    path: MLPath,
    kerf_mm: float,
    context: RmosContext,
) -> List[MLPath]:
    """
    Compute the swept kerf region for a saw cut around a given path.

    For a thin-kerf blade, kerf_mm ≈ blade.kerf_mm.
    """
    geom = get_geometry_engine(context)
    # Half-offset on each side of the cut centerline.
    return geom.offset_path(path, kerf_mm / 2.0)


def boolean_subtract_kerf(
    stock_outline: MLPath,
    kerf_regions: List[MLPath],
    context: RmosContext,
) -> List[MLPath]:
    """
    Subtract kerf regions from stock outline (simulate material removal).
    """
    geom = get_geometry_engine(context)
    return geom.subtract_paths(stock_outline, kerf_regions)

4️⃣ services/api/app/saw_lab/path_planner.py
"""
saw_lab/path_planner.py

Kerf-aware path planner for Saw Lab 2.0.

Responsible for:
- Creating saw-cut paths for strips/pieces
- Respecting cut_mode (RIP, CROSSCUT, COMPOUND)
- Producing MLPath sequences that the toolpath builder can turn into
  RmosToolpathOperations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

from toolpath.geometry_engine import MLPath
from .models import SawCutContext, SawCutMode


Point2D = Tuple[float, float]


@dataclass
class SawCutPath:
    """
    Simple wrapper representing a planned cut path.

    In future this could include cut order, direction, etc.
    """
    path: MLPath
    cut_mode: SawCutMode
    label: str


def plan_basic_rip_cuts(
    stock_outline: MLPath,
    desired_piece_lengths_mm: List[float],
    ctx: SawCutContext,
) -> List[SawCutPath]:
    """
    Skeleton: plan a series of simple rip cuts along the X axis
    to slice a board into the desired lengths.

    For now this is just a placeholder that generates N parallel
    lines; real logic will consider stock_outline geometry.
    """
    cuts: List[SawCutPath] = []

    x0, y0 = 0.0, 0.0
    spacing = (ctx.blade.kerf_mm + 2.0)  # placeholder gap

    for i, length in enumerate(desired_piece_lengths_mm):
        # Very naive: vertical line at x = i * spacing
        x = i * spacing
        path = MLPath(
            points=[(x, y0), (x, y0 + length)],
            is_closed=False,
        )
        cuts.append(
            SawCutPath(
                path=path,
                cut_mode=ctx.cut_mode or SawCutMode.RIP,
                label=f"rip_cut_{i+1}",
            )
        )

    return cuts

5️⃣ services/api/app/saw_lab/toolpath_builder.py
"""
saw_lab/toolpath_builder.py

Converts SawCutPath objects into RmosToolpathOperations and assembles
an RmosToolpathPlan for RMOS.
"""

from __future__ import annotations

from typing import List

from rmos.api_contracts import (
    RmosToolpathOperation,
    RmosToolpathPlan,
    RmosContext,
)
from .path_planner import SawCutPath
from .models import SawCutContext


def estimate_runtime_for_cut(
    cut: SawCutPath,
    ctx: SawCutContext,
) -> float:
    """
    Very rough runtime estimate for a single cut.

    Placeholder: length / feed.
    """
    if not cut.path.points:
        return 0.0

    p0 = cut.path.points[0]
    p1 = cut.path.points[-1]
    length_mm = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
    feed_mm_min = max(ctx.feed_mm_min, 1.0)
    return length_mm / feed_mm_min


def build_toolpath_plan_for_cuts(
    cuts: List[SawCutPath],
    cut_ctx: SawCutContext,
    rmos_ctx: RmosContext,
) -> RmosToolpathPlan:
    """
    Build a high-level RMOS toolpath plan from basic saw cuts.
    """
    ops: List[RmosToolpathOperation] = []

    for idx, cut in enumerate(cuts):
        est_runtime = estimate_runtime_for_cut(cut, cut_ctx)
        ops.append(
            RmosToolpathOperation(
                op_id=cut.label,
                description=f"Saw cut ({cut.cut_mode})",
                strategy="SAW_CUT",
                estimated_runtime_min=est_runtime,
            )
        )

    total_runtime = sum(op.estimated_runtime_min for op in ops)

    return RmosToolpathPlan(
        operations=ops,
        total_estimated_runtime_min=total_runtime,
        notes="Skeleton Saw Lab 2.0 toolpath plan – replace with full kerf planner.",
    )

6️⃣ services/api/app/saw_lab/risk_evaluator.py
"""
saw_lab/risk_evaluator.py

Aggregates saw-specific risk metrics:
- rim speed vs blade/material limits
- bite per tooth
- kickback risk
- burn risk

Feeds into:
- RMOS feasibility scorer (via calculators/service.py)
- Saw Lab-specific warnings / risk overlays
"""

from __future__ import annotations

from .models import SawCutContext, SawLabConfig
from .calculators.saw_rimspeed import compute_rim_speed
from .calculators.saw_bite_load import compute_bite_per_tooth
from .calculators.saw_kickback import compute_kickback_risk
from .calculators.saw_heat import compute_saw_heat_risk


class SawRiskSummary:
    def __init__(
        self,
        rim_speed_risk: float,
        bite_risk: float,
        kickback_risk: float,
        heat_risk: float,
    ) -> None:
        self.rim_speed_risk = rim_speed_risk
        self.bite_risk = bite_risk
        self.kickback_risk = kickback_risk
        self.heat_risk = heat_risk

    @property
    def max_risk(self) -> float:
        return max(
            self.rim_speed_risk,
            self.bite_risk,
            self.kickback_risk,
            self.heat_risk,
        )


def evaluate_saw_risk(
    cut_ctx: SawCutContext,
    config: SawLabConfig,
) -> SawRiskSummary:
    rim_speed = compute_rim_speed(cut_ctx)
    bite = compute_bite_per_tooth(cut_ctx)
    kickback = compute_kickback_risk(cut_ctx, config)
    heat = compute_saw_heat_risk(cut_ctx, config)

    return SawRiskSummary(
        rim_speed_risk=rim_speed.risk_score,
        bite_risk=bite.risk_score,
        kickback_risk=kickback.risk_score,
        heat_risk=heat.risk_score,
    )

7️⃣ services/api/app/saw_lab/calculators/__init__.py
"""
saw_lab/calculators/__init__.py

Saw-specific calculator exports so RMOS calculator layer can call into
Saw Lab when tool_id indicates a saw blade.
"""

from .saw_heat import SawHeatResult, compute_saw_heat_risk
from .saw_deflection import SawDeflectionResult, compute_saw_deflection
from .saw_rimspeed import SawRimSpeedResult, compute_rim_speed
from .saw_bite_load import SawBiteResult, compute_bite_per_tooth
from .saw_kickback import SawKickbackResult, compute_kickback_risk

__all__ = [
    "SawHeatResult",
    "compute_saw_heat_risk",
    "SawDeflectionResult",
    "compute_saw_deflection",
    "SawRimSpeedResult",
    "compute_rim_speed",
    "SawBiteResult",
    "compute_bite_per_tooth",
    "SawKickbackResult",
    "compute_kickback_risk",
]

8️⃣ Example calculator skeletons

You can fill in real math later. Here are minimal stubs for each.

saw_heat.py
from __future__ import annotations

from pydantic import BaseModel
from ..models import SawCutContext, SawLabConfig


class SawHeatResult(BaseModel):
    estimated_temp_rise: float = 0.0
    risk_score: float = 0.3  # 0..1
    warning: str | None = None


def compute_saw_heat_risk(
    cut_ctx: SawCutContext,
    config: SawLabConfig,
) -> SawHeatResult:
    """
    Placeholder heat risk computation. Replace with real model later.
    """
    # TODO: use chipload/bite, material burn threshold, cut length, etc.
    return SawHeatResult()

saw_deflection.py
from __future__ import annotations

from pydantic import BaseModel
from ..models import SawCutContext


class SawDeflectionResult(BaseModel):
    estimated_deflection_mm: float = 0.0
    risk_score: float = 0.2
    warning: str | None = None


def compute_saw_deflection(cut_ctx: SawCutContext) -> SawDeflectionResult:
    """
    Placeholder blade deflection model.
    """
    # TODO: implement beam/plate deflection based on plate_thickness, span, load.
    return SawDeflectionResult()

saw_rimspeed.py
from __future__ import annotations

from math import pi
from pydantic import BaseModel
from ..models import SawCutContext


class SawRimSpeedResult(BaseModel):
    rim_speed_m_per_min: float = 0.0
    risk_score: float = 0.0  # 0..1
    warning: str | None = None


def compute_rim_speed(cut_ctx: SawCutContext) -> SawRimSpeedResult:
    blade = cut_ctx.blade
    rpm = cut_ctx.rpm

    circumference_m = (blade.diameter_mm / 1000.0) * pi
    rim_speed = circumference_m * rpm

    # TODO: compare to blade.max_rim_speed_m_per_min and material constraints
    return SawRimSpeedResult(
        rim_speed_m_per_min=rim_speed,
        risk_score=0.3,
    )

saw_bite_load.py
from __future__ import annotations

from pydantic import BaseModel
from ..models import SawCutContext


class SawBiteResult(BaseModel):
    bite_mm_per_tooth: float = 0.0
    risk_score: float = 0.0
    warning: str | None = None


def compute_bite_per_tooth(cut_ctx: SawCutContext) -> SawBiteResult:
    blade = cut_ctx.blade
    feed = cut_ctx.feed_mm_min
    rpm = cut_ctx.rpm

    # mm/min → mm/rev
    feed_per_rev = feed / max(rpm, 1.0)
    bite = feed_per_rev / max(blade.tooth_count, 1)

    # TODO: compare to blade.recommended_feed_mm_per_tooth.
    return SawBiteResult(
        bite_mm_per_tooth=bite,
        risk_score=0.3,
    )

saw_kickback.py
from __future__ import annotations

from pydantic import BaseModel
from ..models import SawCutContext, SawLabConfig


class SawKickbackResult(BaseModel):
    risk_score: float = 0.0  # 0..1
    warning: str | None = None


def compute_kickback_risk(
    cut_ctx: SawCutContext,
    config: SawLabConfig,
) -> SawKickbackResult:
    """
    Placeholder kickback model.

    In a real implementation, this would consider:
    - hook angle
    - feed direction
    - cut mode (rip vs cross)
    - depth of cut
    - blade sharpness
    """
    return SawKickbackResult(
        risk_score=0.2,
    )

9️⃣ services/api/app/toolpath/saw_engine.py

This is the RMOS-facing integration point.

"""
toolpath/saw_engine.py

RMOS-facing entrypoint for Saw Lab 2.0 toolpath planning.

Called from toolpath/service.py when RmosContext.tool_id identifies a saw blade.
"""

from __future__ import annotations

from typing import List

from rmos.api_contracts import (
    RmosContext,
    RmosToolpathPlan,
)
from art_studio.schemas.rosette_params import RosetteParamSpec

from saw_lab.models import SawBladeSpec, SawMaterialSpec, SawCutContext, SawLabConfig
from saw_lab.path_planner import plan_basic_rip_cuts
from saw_lab.toolpath_builder import build_toolpath_plan_for_cuts
from toolpath.geometry_engine import MLPath


def plan_saw_toolpaths_for_design(
    design: RosetteParamSpec,
    ctx: RmosContext,
) -> RmosToolpathPlan:
    """
    High-level skeleton:

    - Look up blade + material (stubbed for now).
    - Build SawCutContext.
    - Use path_planner to get SawCutPath objects.
    - Convert to RmosToolpathPlan via toolpath_builder.
    """
    # TODO: replace with real lookups from tool/material libraries.
    blade = SawBladeSpec(
        blade_id=ctx.tool_id,
        diameter_mm=140.0,
        kerf_mm=1.2,
        plate_thickness_mm=0.9,
        tooth_count=40,
        hook_angle_deg=15.0,
        top_grind="ATB",
    )
    material = SawMaterialSpec(
        material_id=ctx.material_id,
    )

    cut_ctx = SawCutContext(
        blade=blade,
        material=material,
        cut_mode=None,  # default from config
        feed_mm_min=1500.0,
        rpm=4000.0,
        stock_length_mm=600.0,
        desired_piece_lengths_mm=[200.0, 200.0, 200.0],
    )

    config = SawLabConfig()

    # Placeholder stock outline and simple rip cut plan.
    stock_outline = MLPath(
        points=[(0.0, 0.0), (0.0, 600.0)],
        is_closed=False,
    )

    cuts = plan_basic_rip_cuts(
        stock_outline=stock_outline,
        desired_piece_lengths_mm=cut_ctx.desired_piece_lengths_mm,
        ctx=cut_ctx,
    )

    plan = build_toolpath_plan_for_cuts(
        cuts=cuts,
        cut_ctx=cut_ctx,
        rmos_ctx=ctx,
    )

    return plan

🔟 Small patch to services/api/app/toolpath/service.py

Inside your plan_toolpaths_for_design function, add a branch for saw tools. Something like:

from toolpath.saw_engine import plan_saw_toolpaths_for_design

def plan_toolpaths_for_design(
    design: RosetteParamSpec,
    ctx: RmosContext,
) -> RmosToolpathPlan:
    # Saw mode switch
    if ctx.tool_id.startswith("saw:"):
        return plan_saw_toolpaths_for_design(design, ctx)

    # ... existing router / placeholder logic below ...


That’s the Saw Lab 2.0 Code Skeleton: everything wired structurally, nothing dangerous or over-committed mathematically yet.

From here you can:

Gradually port your old risk_engine.py and kerf_planner.py logic into the new calculators and path planner.

Hook real tool/material libraries instead of hardcoded values.

Tighten integration with the RMOS feasibility engine.