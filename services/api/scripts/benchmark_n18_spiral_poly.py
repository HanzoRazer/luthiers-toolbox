"""
benchmark_n18_spiral_poly.py

Performance benchmark harness for N18 Spiral PolyCut System.
Uses FastAPI TestClient so no external server process is required.

Run from repo root with:
    cd services/api
    python scripts/benchmark_n18_spiral_poly.py
    
Or as module:
    python -m scripts.benchmark_n18_spiral_poly
"""

import json
import time
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


def bench_case(label: str, json_name: str, runs: int = 5):
    """Benchmark a single test case"""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {label}")
    print(f"{'='*60}")
    
    try:
        # Load geometry
        geom = load_json(json_name)
        outer = [tuple(pt) for pt in geom["outer"]]
        tool_d = geom["tool_d"]
        stepover = geom["stepover"]
        margin = geom["margin"]
        corner_radius_min = geom.get("corner_radius_min")
        corner_tol_mm = geom.get("corner_tol_mm")
        
        print(f"Geometry: {len(outer)} points, Tool: {tool_d}mm, Stepover: {stepover*100:.0f}%")
        
        times = []
        spiral_len = 0
        
        # Warmup
        spiral = build_spiral_poly(
            outer=outer,
            tool_d=tool_d,
            stepover=stepover,
            margin=margin,
            climb=True,
            corner_radius_min=corner_radius_min,
            corner_tol_mm=corner_tol_mm,
        )
        spiral_len = len(spiral)
        
        # Benchmark runs
        for _ in range(runs):
            t0 = time.perf_counter()
            
            spiral = build_spiral_poly(
                outer=outer,
                tool_d=tool_d,
                stepover=stepover,
                margin=margin,
                climb=True,
                corner_radius_min=corner_radius_min,
                corner_tol_mm=corner_tol_mm,
            )
            
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000.0)  # Convert to ms
        
        # Calculate stats
        avg_ms = sum(times) / len(times)
        min_ms = min(times)
        max_ms = max(times)
        
        # Calculate path length
        total_length = 0.0
        for i in range(1, len(spiral)):
            x1, y1 = spiral[i-1]
            x2, y2 = spiral[i]
            dx = x2 - x1
            dy = y2 - y1
            total_length += (dx*dx + dy*dy) ** 0.5
        
        print(f"\nResults ({runs} runs):")
        print(f"  Avg time  : {avg_ms:7.3f} ms")
        print(f"  Min time  : {min_ms:7.3f} ms")
        print(f"  Max time  : {max_ms:7.3f} ms")
        print(f"  Points    : {spiral_len}")
        print(f"  Path len  : {total_length:.2f} mm")
        
        # Rough G-code size estimate (4 bytes/coord + overhead)
        gcode_size_kb = (spiral_len * 20) / 1024.0  # Rough estimate
        print(f"  Est size  : {gcode_size_kb:.2f} KiB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ {label}: FAIL")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all benchmark tests"""
    print("\n" + "="*60)
    print("N18 Spiral PolyCut - Performance Benchmark")
    print("="*60)
    
    results = []
    
    # Benchmark 1: Small Rect
    results.append(bench_case("Small Rect (100×60mm)", "geom_small_rect.json", runs=10))
    
    # Benchmark 2: Bridge Slot
    results.append(bench_case("Bridge Slot (140×18mm)", "geom_bridge_slot.json", runs=10))
    
    # Benchmark 3: Thin Strip
    results.append(bench_case("Thin Strip (200×12mm)", "geom_thin_strip.json", runs=10))
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nCompleted: {passed}/{total} benchmarks")
    
    if passed == total:
        print("\n✅ All N18 benchmarks completed successfully")
        return 0
    else:
        print(f"\n❌ {total - passed} benchmark(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
