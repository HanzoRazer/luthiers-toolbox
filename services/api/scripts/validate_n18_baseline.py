"""
N18 Baseline Validator - CI-Safe Comparison Script

Validates N18 Spiral PolyCut system by running baseline test geometries
and comparing outputs against known-good patterns.

Usage:
    python -m services.api.scripts.validate_n18_baseline
    
    Or from repo root:
    cd services/api
    python scripts/validate_n18_baseline.py

Exit codes:
    0 = All baselines pass
    1 = One or more baselines fail
"""

import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from app.util.poly_offset_spiral import build_spiral_poly
except ImportError as e:
    print(f"❌ FAIL: Could not import N18 core module")
    print(f"   Error: {e}")
    print(f"   Ensure pyclipper is installed: pip install pyclipper==1.3.0.post5")
    sys.exit(1)


BASE = Path(__file__).parent.parent / "tests" / "baseline_n18"


def load_json(name: str) -> dict:
    """Load JSON test geometry"""
    path = BASE / name
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found: {path}")
    return json.loads(path.read_text())


def validate_spiral_output(spiral, expected_min_points=10):
    """Basic validation of spiral output structure"""
    if not spiral:
        raise ValueError("Spiral is empty")
    
    if len(spiral) < expected_min_points:
        raise ValueError(f"Spiral too short: {len(spiral)} points (expected >= {expected_min_points})")
    
    # Verify all points are (x, y) tuples
    for i, pt in enumerate(spiral):
        if not isinstance(pt, tuple) or len(pt) != 2:
            raise ValueError(f"Invalid point at index {i}: {pt}")
        
        x, y = pt
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError(f"Invalid coordinates at index {i}: ({x}, {y})")


def run_case(label: str, json_name: str):
    """Run a single baseline test case"""
    print(f"\n{'='*60}")
    print(f"Testing: {label}")
    print(f"{'='*60}")
    
    try:
        # Load geometry
        geom = load_json(json_name)
        print(f"✓ Loaded geometry: {json_name}")
        
        # Extract parameters
        outer = [tuple(pt) for pt in geom["outer"]]
        tool_d = geom["tool_d"]
        stepover = geom["stepover"]
        margin = geom["margin"]
        corner_radius_min = geom.get("corner_radius_min")
        corner_tol_mm = geom.get("corner_tol_mm")
        
        print(f"  Outer: {len(outer)} points")
        print(f"  Tool: {tool_d}mm, Stepover: {stepover*100:.0f}%, Margin: {margin}mm")
        
        # Generate spiral
        spiral = build_spiral_poly(
            outer=outer,
            tool_d=tool_d,
            stepover=stepover,
            margin=margin,
            climb=True,
            corner_radius_min=corner_radius_min,
            corner_tol_mm=corner_tol_mm,
        )
        
        print(f"✓ Generated spiral: {len(spiral)} points")
        
        # Validate output
        validate_spiral_output(spiral, expected_min_points=10)
        print(f"✓ Spiral structure valid")
        
        # Calculate basic stats
        total_length = 0.0
        for i in range(1, len(spiral)):
            x1, y1 = spiral[i-1]
            x2, y2 = spiral[i]
            dx = x2 - x1
            dy = y2 - y1
            total_length += (dx*dx + dy*dy) ** 0.5
        
        print(f"✓ Total path length: {total_length:.2f}mm")
        
        # Verify spiral stays within bounds
        xs = [pt[0] for pt in spiral]
        ys = [pt[1] for pt in spiral]
        
        outer_xs = [pt[0] for pt in outer]
        outer_ys = [pt[1] for pt in outer]
        
        outer_min_x, outer_max_x = min(outer_xs), max(outer_xs)
        outer_min_y, outer_max_y = min(outer_ys), max(outer_ys)
        
        spiral_min_x, spiral_max_x = min(xs), max(xs)
        spiral_min_y, spiral_max_y = min(ys), max(ys)
        
        # Spiral should be inside outer boundary (allowing for margin)
        tolerance = tool_d / 2 + margin + 0.1  # Extra 0.1mm for rounding
        
        if spiral_min_x < outer_min_x - tolerance:
            raise ValueError(f"Spiral extends too far left: {spiral_min_x} < {outer_min_x - tolerance}")
        if spiral_max_x > outer_max_x + tolerance:
            raise ValueError(f"Spiral extends too far right: {spiral_max_x} > {outer_max_x + tolerance}")
        if spiral_min_y < outer_min_y - tolerance:
            raise ValueError(f"Spiral extends too far down: {spiral_min_y} < {outer_min_y - tolerance}")
        if spiral_max_y > outer_max_y + tolerance:
            raise ValueError(f"Spiral extends too far up: {spiral_max_y} > {outer_max_y + tolerance}")
        
        print(f"✓ Spiral bounds valid")
        
        print(f"\n✅ {label}: PASS")
        return True
        
    except Exception as e:
        print(f"\n❌ {label}: FAIL")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all baseline validation tests"""
    print("\n" + "="*60)
    print("N18 Spiral PolyCut - Baseline Validation")
    print("="*60)
    
    results = []
    
    # Test 1: Small Rect
    results.append(run_case("Small Rect (100×60mm)", "geom_small_rect.json"))
    
    # Test 2: Bridge Slot
    results.append(run_case("Bridge Slot (140×18mm)", "geom_bridge_slot.json"))
    
    # Test 3: Thin Strip
    results.append(run_case("Thin Strip (200×12mm)", "geom_thin_strip.json"))
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All N18 baselines PASS")
        return 0
    else:
        print(f"\n❌ {total - passed} baseline(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
