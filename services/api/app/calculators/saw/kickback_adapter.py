"""
Kickback Risk Adapter (Saw Blades)

Assesses kickback risk for table saw operations.

MODEL NOTES:
- Kickback occurs when:
  - Work binds on blade
  - Work lifts off table
  - Back of blade catches work
- Risk factors:
  - Blade height too high (more teeth engaged above work)
  - No riving knife/splitter
  - No anti-kickback pawls
  - Aggressive bite per tooth
  - Cross-grain cutting of bowed material
- This model focuses on the physics factors we can calculate

SAFETY WARNING:
This calculator provides estimates only. Always use proper safety equipment:
- Riving knife
- Anti-kickback pawls
- Push sticks/blocks
- Proper stance and technique
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, List

RiskCategory = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass
class KickbackRiskResult:
    """Result from kickback risk assessment."""
    risk_score: float  # 0-1 scale
    category: RiskCategory
    risk_factors: List[str]
    message: str


def assess_kickback_risk(
    blade_diameter_mm: float,
    blade_height_above_work_mm: float,
    depth_of_cut_mm: float,
    bite_mm: float,
    *,
    has_riving_knife: bool = True,
    has_anti_kickback: bool = False,
    is_ripping: bool = True,
) -> KickbackRiskResult:
    """
    Assess kickback risk for a table saw operation.

    Args:
        blade_diameter_mm: Blade diameter
        blade_height_above_work_mm: How much blade protrudes above work
        depth_of_cut_mm: Depth of cut
        bite_mm: Bite per tooth
        has_riving_knife: Whether riving knife is installed
        has_anti_kickback: Whether anti-kickback pawls are used
        is_ripping: True for rip cuts, False for crosscuts

    Returns:
        KickbackRiskResult with risk score and factors
    """
    risk_factors: List[str] = []
    risk_score = 0.0

    # Factor 1: Blade height above work
    # Ideal: blade just clears work (3-6mm above)
    # Risk: more blade above = more teeth to catch on kickback
    ideal_height = 6.0  # mm
    if blade_height_above_work_mm > ideal_height * 2:
        height_risk = 0.15
        risk_factors.append(f"Blade height {blade_height_above_work_mm:.0f}mm - lower blade")
    elif blade_height_above_work_mm < 3.0:
        height_risk = 0.05
        risk_factors.append("Blade very low - reduced power, may burn")
    else:
        height_risk = 0.0

    risk_score += height_risk

    # Factor 2: Bite aggressiveness
    if bite_mm > 0.4:
        bite_risk = 0.20
        risk_factors.append(f"Aggressive bite {bite_mm:.3f}mm - reduce feed")
    elif bite_mm < 0.05:
        bite_risk = 0.10
        risk_factors.append("Low bite - may cause binding/burning")
    else:
        bite_risk = 0.0

    risk_score += bite_risk

    # Factor 3: Safety equipment
    if not has_riving_knife:
        risk_score += 0.30
        risk_factors.append("NO RIVING KNIFE - HIGH KICKBACK RISK")

    if not has_anti_kickback and is_ripping:
        risk_score += 0.10
        risk_factors.append("No anti-kickback pawls for rip cut")

    # Factor 4: Cut type
    if not is_ripping:
        # Crosscuts have different risk profile
        risk_score += 0.05
        if depth_of_cut_mm > blade_diameter_mm * 0.4:
            risk_score += 0.10
            risk_factors.append("Deep crosscut - use sled or miter gauge")

    # Normalize to 0-1
    risk_score = min(1.0, max(0.0, risk_score))

    # Categorize
    if risk_score < 0.20:
        category: RiskCategory = "LOW"
        message = "Kickback risk low with proper technique"
    elif risk_score < 0.40:
        category = "MEDIUM"
        message = "Moderate kickback risk - use caution"
    elif risk_score < 0.65:
        category = "HIGH"
        message = "HIGH kickback risk - review setup before cutting"
    else:
        category = "CRITICAL"
        message = "CRITICAL kickback risk - DO NOT CUT until issues resolved"

    if not risk_factors:
        risk_factors.append("Setup appears safe")

    return KickbackRiskResult(
        risk_score=risk_score,
        category=category,
        risk_factors=risk_factors,
        message=message,
    )
