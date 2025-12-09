"""
Saw Lab 2.0 - Bite Load Calculator

Calculates tooth bite load (chip load per tooth) for saw operations.
"""
from __future__ import annotations

from ..models import SawContext, SawDesign, SawCalculatorResult


class SawBiteLoadCalculator:
    """
    Calculates bite load (chip load) per tooth.
    
    Bite load = material removed per tooth per revolution.
    Critical for cut quality and blade life:
        - Too low: friction, burning, poor surface
        - Too high: tearout, overloading, blade wear
    
    Optimal ranges (mm/tooth):
        - Softwood: 0.05-0.15
        - Hardwood: 0.03-0.10
        - Plywood: 0.03-0.08
        - MDF: 0.05-0.12
    """
    
    # Material-specific bite load ranges (mm/tooth)
    OPTIMAL_RANGES = {
        "softwood": (0.05, 0.15),
        "hardwood": (0.03, 0.10),
        "plywood": (0.03, 0.08),
        "mdf": (0.05, 0.12),
        "acrylic": (0.02, 0.06),
        "aluminum": (0.01, 0.04),
        "default": (0.03, 0.10)
    }
    
    def calculate(
        self,
        design: SawDesign,
        ctx: SawContext
    ) -> SawCalculatorResult:
        """
        Calculate bite load score.
        
        Args:
            design: Cut design parameters
            ctx: Saw context
        
        Returns:
            SawCalculatorResult with score and bite load data
        """
        try:
            # Calculate bite load: feed_rate / (RPM * tooth_count)
            bite_load_mm = ctx.feed_rate_mm_per_min / (ctx.max_rpm * ctx.tooth_count)
            
            # Get optimal range for material
            material_key = self._get_material_key(ctx.material_id)
            min_optimal, max_optimal = self.OPTIMAL_RANGES.get(
                material_key, self.OPTIMAL_RANGES["default"]
            )
            
            # Calculate score based on bite load
            if min_optimal <= bite_load_mm <= max_optimal:
                score = 100.0
                warning = None
            elif bite_load_mm < min_optimal * 0.5:
                score = 40.0
                warning = f"Bite load very low ({bite_load_mm:.4f} mm); friction and burning likely"
            elif bite_load_mm < min_optimal:
                score = 70.0
                warning = f"Bite load below optimal ({bite_load_mm:.4f} mm); increase feed rate"
            elif bite_load_mm <= max_optimal * 1.3:
                score = 70.0
                warning = f"Bite load above optimal ({bite_load_mm:.4f} mm); reduce feed rate"
            elif bite_load_mm <= max_optimal * 1.5:
                score = 45.0
                warning = f"Bite load high ({bite_load_mm:.4f} mm); tearout and overload risk"
            else:
                score = 20.0
                warning = f"Bite load excessive ({bite_load_mm:.4f} mm); blade damage likely"
            
            # Calculate recommended feed rate for optimal bite load
            optimal_bite = (min_optimal + max_optimal) / 2
            recommended_feed = optimal_bite * ctx.max_rpm * ctx.tooth_count
            
            return SawCalculatorResult(
                calculator_name="bite_load",
                score=score,
                warning=warning,
                metadata={
                    "bite_load_mm": round(bite_load_mm, 5),
                    "optimal_range_mm": [min_optimal, max_optimal],
                    "current_feed_mm_per_min": ctx.feed_rate_mm_per_min,
                    "recommended_feed_mm_per_min": round(recommended_feed, 0),
                    "tooth_count": ctx.tooth_count,
                    "rpm": ctx.max_rpm
                }
            )
            
        except Exception as e:
            return SawCalculatorResult(
                calculator_name="bite_load",
                score=50.0,
                warning=f"Bite load calculation error: {str(e)}"
            )
    
    def _get_material_key(self, material_id: str | None) -> str:
        """Map material_id to optimal range key."""
        if not material_id:
            return "default"
        
        material_lower = material_id.lower()
        
        if any(k in material_lower for k in ["soft", "pine", "cedar", "spruce"]):
            return "softwood"
        elif any(k in material_lower for k in ["hard", "oak", "maple", "walnut"]):
            return "hardwood"
        elif "plywood" in material_lower or "ply" in material_lower:
            return "plywood"
        elif "mdf" in material_lower:
            return "mdf"
        elif "acrylic" in material_lower or "plastic" in material_lower:
            return "acrylic"
        elif "alum" in material_lower:
            return "aluminum"
        
        return "default"
