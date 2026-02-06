"""
Saw Lab 2.0 - Calculators Package

Provides feasibility calculators for saw blade operations:
    - saw_heat: Thermodynamic heat buildup model
    - saw_deflection: Beam theory blade deflection
    - saw_rimspeed: Rim speed safety checks
    - saw_bite_load: Tooth bite load analysis
    - saw_kickback: Kickback risk evaluation
    - saw_cutting_force: C-axis force decomposition and power check
    - saw_blade_dynamics: Critical speed and vibration mode analysis

All calculators follow the same interface:
    - calculate(design, ctx) -> SawCalculatorResult
"""
from __future__ import annotations

from typing import Dict, List

from ..models import (
    SawContext,
    SawDesign,
    SawCalculatorResult,
    SawFeasibilityResult,
    SawRiskLevel,
)

from .saw_heat import SawHeatCalculator
from .saw_deflection import SawDeflectionCalculator
from .saw_rimspeed import SawRimSpeedCalculator
from .saw_bite_load import SawBiteLoadCalculator
from .saw_kickback import SawKickbackCalculator
from .saw_cutting_force import SawCuttingForceCalculator
from .saw_blade_dynamics import SawBladeDynamicsCalculator


class FeasibilityCalculatorBundle:
    """
    Bundle of all saw feasibility calculators.
    
    Provides weighted aggregation of individual calculator scores
    to produce overall feasibility result.
    
    Weights:
        - Heat: 20%
        - Deflection: 15%
        - Rim Speed: 20%
        - Bite Load: 25%
        - Kickback: 20%
    """
    
    # Calculator weights for aggregation
    # 7 calculators: force/dynamics are physics-critical, so weighted accordingly
    WEIGHTS = {
        "heat": 0.15,
        "deflection": 0.12,
        "rim_speed": 0.13,
        "bite_load": 0.15,
        "kickback": 0.15,
        "cutting_force": 0.18,    # Power overload = hard stop
        "blade_dynamics": 0.12,   # Resonance avoidance
    }
    
    def __init__(self):
        self._calculators = {
            "heat": SawHeatCalculator(),
            "deflection": SawDeflectionCalculator(),
            "rim_speed": SawRimSpeedCalculator(),
            "bite_load": SawBiteLoadCalculator(),
            "kickback": SawKickbackCalculator(),
            "cutting_force": SawCuttingForceCalculator(),
            "blade_dynamics": SawBladeDynamicsCalculator(),
        }
    
    def evaluate(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawFeasibilityResult:
        """
        Evaluate overall feasibility for saw operation.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            SawFeasibilityResult with aggregated score and details
        """
        calculator_results: Dict[str, SawCalculatorResult] = {}
        warnings: List[str] = []
        weighted_sum = 0.0
        
        # Run each calculator
        for name, calculator in self._calculators.items():
            try:
                result = calculator.calculate(design, ctx)
                calculator_results[name] = result
                
                # Add to weighted sum
                weight = self.WEIGHTS.get(name, 0.1)
                weighted_sum += result.score * weight
                
                # Collect warnings
                if result.warning:
                    warnings.append(result.warning)
                    
            except (ZeroDivisionError, ValueError, TypeError, ArithmeticError, OverflowError) as e:  # WP-1: narrowed from except Exception
                # Calculator failed - add warning and default score
                warnings.append(f"{name} calculator error: {str(e)}")
                calculator_results[name] = SawCalculatorResult(
                    calculator_name=name,
                    score=50.0,
                    warning=f"Calculator error: {str(e)}"
                )
                weighted_sum += 50.0 * self.WEIGHTS.get(name, 0.1)
        
        # Calculate final score
        final_score = min(100.0, max(0.0, weighted_sum))
        
        # Determine risk level
        risk_level = self._classify_risk(final_score, calculator_results)
        
        # Estimate cut time
        estimated_time = self._estimate_cut_time(design, ctx)
        
        # Calculate efficiency
        efficiency = self._estimate_efficiency(final_score, calculator_results)
        
        return SawFeasibilityResult(
            score=round(final_score, 1),
            risk_level=risk_level,
            warnings=warnings,
            calculator_results=calculator_results,
            efficiency=round(efficiency, 1),
            estimated_cut_time_seconds=round(estimated_time, 2)
        )
    
    def _classify_risk(
        self,
        score: float,
        results: Dict[str, SawCalculatorResult]
    ) -> SawRiskLevel:
        """Classify risk level from score and individual results."""
        # Worst-case propagation: any RED result = overall RED
        for result in results.values():
            if result.score < 30:
                return SawRiskLevel.RED
        
        # Score-based classification
        if score >= 80:
            return SawRiskLevel.GREEN
        elif score >= 50:
            return SawRiskLevel.YELLOW
        return SawRiskLevel.RED
    
    def _estimate_cut_time(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> float:
        """Estimate time for cut operation."""
        # Simple estimate: (cut_length / feed_rate) * repeat_count
        # Plus overhead for rapids and plunges
        cut_time_per_pass = (design.cut_length_mm / ctx.feed_rate_mm_per_min) * 60
        rapid_overhead = 5.0  # seconds per pass for positioning
        
        total_time = (cut_time_per_pass + rapid_overhead) * design.repeat_count
        
        # Additional time for dado passes
        if design.dado_width_mm > 0:
            passes = max(1, int(design.dado_width_mm / ctx.blade_kerf_mm))
            total_time *= passes
        
        return total_time
    
    def _estimate_efficiency(
        self,
        score: float,
        results: Dict[str, SawCalculatorResult]
    ) -> float:
        """Estimate cut efficiency percentage."""
        # Base efficiency from score
        base_efficiency = score
        
        # Penalty for low individual scores
        for result in results.values():
            if result.score < 60:
                base_efficiency -= 5.0
        
        return max(0.0, min(100.0, base_efficiency))


__all__ = [
    "FeasibilityCalculatorBundle",
    "SawHeatCalculator",
    "SawDeflectionCalculator",
    "SawRimSpeedCalculator",
    "SawBiteLoadCalculator",
    "SawKickbackCalculator",
    "SawCuttingForceCalculator",
    "SawBladeDynamicsCalculator",
]
