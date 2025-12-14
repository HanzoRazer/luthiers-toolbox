"""
================================================================================
CAM Stock Material Operations Module
================================================================================

PURPOSE:
--------
Provides utilities for calculating material removal volumes, rates, and 
coverage percentages during CNC machining operations. Used to estimate 
material removal rate (MRR) and validate toolpath efficiency.

CORE FUNCTIONS:
--------------
1. rough_mrr_estimate()
   - Calculates material volume removed (area × depth)
   - Used in adaptive pocketing for volume statistics
   - Does NOT estimate time (caller provides feed rates)

2. calculate_removal_percentage()
   - Estimates percentage of pocket area covered by tool
   - Useful for stepover validation
   - Range: 0-100% (clamped)

ALGORITHM OVERVIEW:
------------------
**Material Removal Rate (MRR) Calculation:**

    Volume = Pocket_Area × Stepdown
    
    Where:
    - Pocket_Area: Cleared area in mm²
    - Stepdown: Depth per pass in mm
    - Result: Volume in mm³

**Coverage Percentage:**

    Coverage = (Tool_Swept_Area / Pocket_Area) × 100
    
    Where:
    - Tool_Swept_Area: Effective area covered by tool centerline path
    - Pocket_Area: Total boundary area
    - Clamped to 100% max

USAGE EXAMPLE:
-------------
    from .stock_ops import rough_mrr_estimate, calculate_removal_percentage
    
    # Calculate volume removed in a 100×60mm pocket, 3mm deep
    area = 100 * 60  # 6000 mm²
    depth = 3.0      # mm
    volume = rough_mrr_estimate(area, depth, path_len=0, tool_d=0)
    # Result: 18000 mm³
    
    # Calculate toolpath coverage
    pocket_area = 6000    # mm²
    swept_area = 5400     # mm² (90% coverage)
    coverage = calculate_removal_percentage(pocket_area, swept_area)
    # Result: 90.0%

INTEGRATION POINTS:
------------------
- Used by: adaptive_router.py (pocket statistics)
- Exports: rough_mrr_estimate(), calculate_removal_percentage()
- Dependencies: None (math only)

CRITICAL SAFETY RULES:
---------------------
1. **Volume ≠ Time**: MRR volume does NOT predict machining time
   - Time depends on feed rates, rapids, tool changes
   - Use feedtime.py or feedtime_l3.py for time estimation

2. **Coverage ≠ Quality**: High coverage % does NOT guarantee smooth finish
   - Stepover and strategy affect surface quality
   - Use adaptive stepover (L.2) for uniform engagement

3. **Theoretical Values**: Estimates assume ideal conditions
   - Actual removal may vary due to deflection, chip evacuation
   - Use as planning tool, not precision measurement

4. **Area Validation**: Zero or negative pocket area returns 0% coverage
   - Prevents division by zero errors
   - Always validate geometry before calling

5. **Clamped Output**: Coverage percentage clamped to 100% max
   - Prevents misleading >100% values from overlapping passes
   - Tool swept area may exceed pocket area in spiral strategies

================================================================================
"""
from typing import List, Tuple


# =============================================================================
# MATERIAL REMOVAL CALCULATIONS
# =============================================================================

def rough_mrr_estimate(area_mm2: float, stepdown: float, path_len_mm: float, tool_d: float) -> float:
    """
    Crude estimate of material removal rate.
    
    Volume removed ≈ area * stepdown
    Time ~ path_len / avg_feed (caller provides time)
    
    Args:
        area_mm2: Pocket area in square millimeters
        stepdown: Depth of cut in mm
        path_len_mm: total toolpath length in mm
        tool_d: Tool diameter in mm
    
    Returns:
        Estimated volume removed in mm³
    """
    return area_mm2 * stepdown


# =============================================================================
# TOOLPATH COVERAGE ANALYSIS
# =============================================================================

def calculate_removal_percentage(pocket_area: float, tool_swept_area: float) -> float:
    """
    Calculate approximate percentage of material removed.
    
    Args:
        pocket_area: Total pocket area in mm²
        tool_swept_area: Area covered by tool in mm²
    
    Returns:
        Percentage of material removed (0-100)
    """
    if pocket_area <= 0:
        return 0.0
    return min(100.0, (tool_swept_area / pocket_area) * 100.0)
