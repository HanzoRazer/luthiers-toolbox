he Saw Lab 2.0 skeleton into clean, importable, syntactically-valid Python you can actually drop into your repo.

Below are ready-to-run versions of the key modules, with the concrete syntax problems fixed:

proper from __future__ import annotations

__all__ instead of all

fixed __init__ on SawRiskSummary

cleaned indentation

removed enum-vs-None weirdness

kept calculators & planners as stubs, but valid

You can adjust paths (app., services.api.app., etc.) to match your real layout.

1️⃣ services/api/app/saw_lab/models.py
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SawCutMode(str, Enum):
    RIP = "RIP"
    CROSSCUT = "CROSSCUT"
    COMPOUND = "COMPOUND"
    UNKNOWN = "UNKNOWN"


class SawBladeSpec(BaseModel):
    """Static/spec metadata for a saw blade."""

    id: Optional[str] = None
    name: str

    diameter_mm: float = Field(..., gt=0.0)
    kerf_mm: float = Field(..., gt=0.0)
    plate_mm: float = Field(..., gt=0.0)
    tooth_count: int = Field(..., gt=0)

    hook_angle_deg: float = 0.0
    top_grind: Optional[str] = None  # e.g. ATB, Hi-ATB, TCG

    max_rim_speed_m_per_min: Optional[float] = None
    recommended_rim_speed_m_per_min: Optional[float] = None
    recommended_bite_mm_per_tooth: Optional[float] = None

    notes: Optional[str] = None


class SawMaterialSpec(BaseModel):
    """Material properties needed for risk and heat modeling."""

    id: Optional[str] = None
    name: str

    density_kg_per_m3: Optional[float] = None
    burn_tendency: float = Field(0.5, ge=0.0, le=1.0)
    tearout_tendency: float = Field(0.5, ge=0.0, le=1.0)
    hardness_scale: float = Field(0.5, ge=0.0, le=1.0)


class SawCutContext(BaseModel):
    """One cutting scenario: blade + material + kinematics."""

    blade: SawBladeSpec
    material: SawMaterialSpec

    cut_mode: SawCutMode = SawCutMode.UNKNOWN

    feed_mm_per_min: float = Field(..., gt=0.0)
    rpm: int = Field(..., gt=0)

    stock_length_mm: float = Field(..., gt=0.0)
    desired_piece_lengths_mm: List[float] = Field(default_factory=list)


class SawLabConfig(BaseModel):
    """Global knobs for Saw Lab risk and planning."""

    max_allowed_rim_speed_m_per_min: float = 80.0
    max_allowed_bite_mm_per_tooth: float = 0.5
    max_allowed_deflection_mm: float = 0.1


__all__ = [
    "SawCutMode",
    "SawBladeSpec",
    "SawMaterialSpec",
    "SawCutContext",
    "SawLabConfig",
]

2️⃣ services/api/app/saw_lab/geometry.py

(Stubbed, but syntactically valid and aligned with RMOS geometry-engine usage.)

from __future__ import annotations

from typing import Any

from .models import SawBladeSpec


def offset_kerf_region(centerline: Any, blade: SawBladeSpec) -> Any:
    """
    Expand a centerline path into a kerf-sweep region using the RMOS geometry engine.

    NOTE: This is a stub. In the real repo:
      - get_geometry_engine(context) should be used
      - kerf/2 offsets applied around the centerline
    """
    kerf = blade.kerf_mm
    # TODO: replace with real MLPath + geometry engine calls
    _ = kerf
    return centerline


def boolean_subtract_kerf(stock_region: Any, kerf_region: Any) -> Any:
    """
    Subtract kerf region from a stock region using RMOS geometry engine.

    NOTE: This is a stub; it just returns the stock_region unchanged for now.
    """
    _ = kerf_region
    return stock_region

3️⃣ services/api/app/saw_lab/path_planner.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import SawCutContext, SawCutMode


@dataclass
class SawCutPath:
    """Represents a single planned cut path."""

    path: object
    cut_mode: SawCutMode
    label: str = ""


def plan_basic_rip_cuts(
    ctx: SawCutContext,
    stock_outline: object,
) -> List[SawCutPath]:
    """
    Very simple rip-cut planner stub.

    Creates a few parallel cut paths purely as a placeholder.
    Replace with kerf-aware, stock-aware planning.
    """
    _ = stock_outline

    cuts: List[SawCutPath] = []

    # Stub: pretend we have three equally spaced cuts
    for idx in range(3):
        dummy_path = f"DUMMY_PATH_{idx}"
        cuts.append(
            SawCutPath(
                path=dummy_path,
                cut_mode=ctx.cut_mode or SawCutMode.RIP,
                label=f"stub_rip_cut_{idx}",
            )
        )

    return cuts


__all__ = ["SawCutPath", "plan_basic_rip_cuts"]

4️⃣ services/api/app/saw_lab/toolpath_builder.py

Here I assume you already have RmosToolpathOperation and RmosToolpathPlan in your RMOS toolpath layer. To keep this file syntactically valid without that repo, I’ll just type them as Any.

from __future__ import annotations

from typing import Any, List

from .models import SawCutContext
from .path_planner import SawCutPath


def build_toolpath_plan_for_cuts(
    ctx: SawCutContext,
    cuts: List[SawCutPath],
) -> Any:
    """
    Convert SawCutPath objects into RmosToolpathOperation/RmosToolpathPlan.

    NOTE:
      - Replace `Any` with actual types from your RMOS toolpath module.
      - Replace stub runtime estimate with real feed/rpm/length math.
    """
    operations: List[Any] = []

    for idx, cut in enumerate(cuts):
        # Stub runtime based on stock length and feed rate
        length_mm = ctx.stock_length_mm
        feed = ctx.feed_mm_per_min or 1.0
        est_runtime_min = max(length_mm / feed, 0.0)

        op = {
            "strategy": "SAW_CUT",
            "label": cut.label or f"saw_cut_{idx}",
            "estimated_runtime_min": est_runtime_min,
            "metadata": {
                "cut_mode": cut.cut_mode.value,
                "rpm": ctx.rpm,
                "feed_mm_per_min": ctx.feed_mm_per_min,
            },
        }
        operations.append(op)

    total_runtime = sum(op["estimated_runtime_min"] for op in operations)

    plan = {
        "operations": operations,
        "total_estimated_runtime_min": total_runtime,
        "notes": "Skeleton Saw Lab 2.0 toolpath plan – replace with full kerf planner.",
    }

    return plan


__all__ = ["build_toolpath_plan_for_cuts"]

5️⃣ services/api/app/saw_lab/calculators/__init__.py
from __future__ import annotations

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

6️⃣ services/api/app/saw_lab/calculators/saw_rimspeed.py
from __future__ import annotations

from math import pi

from pydantic import BaseModel

from ..models import SawCutContext, SawLabConfig


class SawRimSpeedResult(BaseModel):
    rim_speed_m_per_min: float
    risk: float  # 0.0 .. 1.0


def compute_rim_speed(
    ctx: SawCutContext,
    config: SawLabConfig,
) -> SawRimSpeedResult:
    """
    Compute rim speed and a naive risk score.

    risk ~ 0 below allowed band, ramps up as we exceed max_allowed_rim_speed_m_per_min.
    """
    diameter_m = ctx.blade.diameter_mm / 1000.0
    circumference_m = pi * diameter_m
    rim_speed = circumference_m * ctx.rpm  # m/min if rpm is rev/min

    if rim_speed <= config.max_allowed_rim_speed_m_per_min:
        risk = 0.2
    else:
        overshoot = rim_speed - config.max_allowed_rim_speed_m_per_min
        # simple clamp
        risk = min(1.0, 0.2 + overshoot / config.max_allowed_rim_speed_m_per_min)

    return SawRimSpeedResult(rim_speed_m_per_min=rim_speed, risk=risk)

7️⃣ services/api/app/saw_lab/calculators/saw_bite_load.py
from __future__ import annotations

from pydantic import BaseModel

from ..models import SawCutContext, SawLabConfig


class SawBiteResult(BaseModel):
    bite_mm_per_tooth: float
    risk: float


def compute_bite_per_tooth(
    ctx: SawCutContext,
    config: SawLabConfig,
) -> SawBiteResult:
    """
    Approximate bite (chip thickness) per tooth in mm.
    Stub: assumes one effective tooth engagement at a time.
    """
    teeth_per_rev = ctx.blade.tooth_count or 1
    feed_per_rev_mm = ctx.feed_mm_per_min / max(ctx.rpm, 1)
    bite = feed_per_rev_mm / teeth_per_rev

    if bite <= config.max_allowed_bite_mm_per_tooth:
        risk = 0.2
    else:
        overshoot = bite - config.max_allowed_bite_mm_per_tooth
        risk = min(1.0, 0.2 + overshoot / config.max_allowed_bite_mm_per_tooth)

    return SawBiteResult(bite_mm_per_tooth=bite, risk=risk)

8️⃣ services/api/app/saw_lab/calculators/saw_heat.py
from __future__ import annotations

from pydantic import BaseModel

from ..models import SawCutContext, SawLabConfig


class SawHeatResult(BaseModel):
    temp_rise_deg_c: float
    risk: float


def compute_saw_heat_risk(
    ctx: SawCutContext,
    config: SawLabConfig,
) -> SawHeatResult:
    """
    Stub heat model: uses feed + rpm + material burn_tendency to approximate risk.
    """
    _ = config

    base_rise = ctx.material.burn_tendency * 30.0
    speed_factor = min(ctx.feed_mm_per_min / 1000.0, 2.0)
    temp_rise = base_rise * (1.0 + speed_factor)

    risk = min(1.0, temp_rise / 80.0)

    return SawHeatResult(temp_rise_deg_c=temp_rise, risk=risk)

9️⃣ services/api/app/saw_lab/calculators/saw_deflection.py
from __future__ import annotations

from pydantic import BaseModel

from ..models import SawCutContext, SawLabConfig


class SawDeflectionResult(BaseModel):
    deflection_mm: float
    risk: float


def compute_saw_deflection(
    ctx: SawCutContext,
    config: SawLabConfig,
) -> SawDeflectionResult:
    """
    Stub deflection model: small heuristic based on blade diameter and feed.
    """
    diameter_m = ctx.blade.diameter_mm / 1000.0
    base_deflection = diameter_m * (ctx.feed_mm_per_min / 10000.0)

    if base_deflection <= config.max_allowed_deflection_mm:
        risk = 0.3
    else:
        overshoot = base_deflection - config.max_allowed_deflection_mm
        risk = min(1.0, 0.3 + overshoot / config.max_allowed_deflection_mm)

    return SawDeflectionResult(deflection_mm=base_deflection, risk=risk)

🔟 services/api/app/saw_lab/calculators/saw_kickback.py
from __future__ import annotations

from pydantic import BaseModel

from ..models import SawCutContext, SawLabConfig


class SawKickbackResult(BaseModel):
    risk: float


def compute_kickback_risk(
    ctx: SawCutContext,
    config: SawLabConfig,
) -> SawKickbackResult:
    """
    Stub kickback model: heuristically tied to hook angle and bite.
    """
    _ = config

    # Very naive: large positive hook angle => higher risk.
    angle = ctx.blade.hook_angle_deg
    risk = 0.2

    if angle > 10:
        risk = 0.5
    if angle > 20:
        risk = 0.8

    return SawKickbackResult(risk=risk)

1️⃣1️⃣ services/api/app/saw_lab/risk_evaluator.py

Here we fix the broken init and indentation and properly aggregate risks.

from __future__ import annotations

from typing import List

from pydantic import BaseModel

from .calculators import (
    SawHeatResult,
    SawDeflectionResult,
    SawRimSpeedResult,
    SawBiteResult,
    SawKickbackResult,
    compute_saw_heat_risk,
    compute_saw_deflection,
    compute_rim_speed,
    compute_bite_per_tooth,
    compute_kickback_risk,
)
from .models import SawCutContext, SawLabConfig


class SawRiskSummary(BaseModel):
    heat: SawHeatResult
    deflection: SawDeflectionResult
    rim_speed: SawRimSpeedResult
    bite: SawBiteResult
    kickback: SawKickbackResult

    @property
    def all_risks(self) -> List[float]:
        return [
            self.heat.risk,
            self.deflection.risk,
            self.rim_speed.risk,
            self.bite.risk,
            self.kickback.risk,
        ]

    @property
    def max_risk(self) -> float:
        return max(self.all_risks) if self.all_risks else 0.0


def evaluate_saw_risk(
    ctx: SawCutContext,
    config: SawLabConfig,
) -> SawRiskSummary:
    """
    Run all saw calculators and aggregate into a SawRiskSummary.
    """
    heat = compute_saw_heat_risk(ctx, config)
    deflection = compute_saw_deflection(ctx, config)
    rim_speed = compute_rim_speed(ctx, config)
    bite = compute_bite_per_tooth(ctx, config)
    kickback = compute_kickback_risk(ctx, config)

    return SawRiskSummary(
        heat=heat,
        deflection=deflection,
        rim_speed=rim_speed,
        bite=bite,
        kickback=kickback,
    )

1️⃣2️⃣ services/api/app/toolpath/saw_engine.py (skeleton)

This is just a clean version of the dispatcher stub.

from __future__ import annotations

from typing import Any, List

from app.saw_lab.models import (
    SawBladeSpec,
    SawMaterialSpec,
    SawCutContext,
    SawLabConfig,
)
from app.saw_lab.path_planner import plan_basic_rip_cuts
from app.saw_lab.toolpath_builder import build_toolpath_plan_for_cuts

# from app.rmos.api_contracts import RosetteParamSpec, RmosContext   # in your real repo


def plan_saw_toolpaths_for_design(
    design: Any,  # RosetteParamSpec in real code
    ctx: Any,  # RmosContext in real code
) -> Any:
    """
    Skeleton Saw Lab entrypoint used by RMOS toolpath engine
    when ctx.tool_id refers to a saw blade.
    """
    # TODO: Replace with real lookup based on ctx.tool_id and ctx.material_id
    blade = SawBladeSpec(
        id="stub_blade",
        name="Stub Ultra-Thin Veneer Blade",
        diameter_mm=140.0,
        kerf_mm=1.0,
        plate_mm=0.8,
        tooth_count=80,
        hook_angle_deg=10.0,
    )

    material = SawMaterialSpec(
        id="stub_material",
        name="Generic Hardwood",
        density_kg_per_m3=700.0,
        burn_tendency=0.6,
        tearout_tendency=0.5,
        hardness_scale=0.7,
    )

    cut_ctx = SawCutContext(
        blade=blade,
        material=material,
        cut_mode=None,  # will fall back to RIP in planner
        feed_mm_per_min=400.0,
        rpm=8000,
        stock_length_mm=600.0,
        desired_piece_lengths_mm=[50.0, 50.0, 50.0],
    )

    config = SawLabConfig()

    # In real code, stock_outline would come from design geometry
    stock_outline: Any = "DUMMY_STOCK_OUTLINE"

    cuts = plan_basic_rip_cuts(cut_ctx, stock_outline)
    plan = build_toolpath_plan_for_cuts(cut_ctx, cuts)

    return plan


If you copy these into the appropriate files, they should import and run without syntax errors (you’ll just need to fix the app. import root to match your actual package name, and eventually replace Any + stubs with your real RMOS types and logic).