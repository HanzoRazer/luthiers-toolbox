"""
Profile N.17 Polygon Offset Performance

Identifies bottlenecks in the polygon offsetting algorithm.
"""

import sys
import time
from pathlib import Path

# Add API to path
api_path = Path(__file__).parent.parent / "services" / "api"
sys.path.insert(0, str(api_path))

from app.cam.polygon_offset_n17 import toolpath_offsets, offset_polygon_mm
from app.util.gcode_emit_advanced import emit_xy_with_arcs
from app.util.gcode_emit_basic import emit_xy_polyline_nc


def profile_offset_generation():
    """Profile the core offset generation"""
    print("\n=== PROFILING OFFSET GENERATION ===\n")
    
    test_cases = [
        ("Small (30x20mm)", [(0,0), (30,0), (30,20), (0,20)], 6.0, 2.0),
        ("Medium (50x30mm)", [(0,0), (50,0), (50,30), (0,30)], 6.0, 2.0),
        ("Large (100x60mm)", [(0,0), (100,0), (100,60), (0,60)], 6.0, 2.0),
    ]
    
    for name, poly, tool_dia, stepover in test_cases:
        print(f"{name}:")
        
        # Time individual offset operations
        t_start = time.perf_counter()
        first_offset = offset_polygon_mm(poly, -stepover, "round", 0.25)
        t_first = (time.perf_counter() - t_start) * 1000
        
        # Time full pass generation
        t_start = time.perf_counter()
        paths = toolpath_offsets(poly, tool_dia, stepover, inward=True, join_type="round")
        t_total = (time.perf_counter() - t_start) * 1000
        
        num_passes = len(paths)
        avg_per_pass = t_total / num_passes if num_passes > 0 else 0
        
        print(f"  First offset: {t_first:.1f}ms")
        print(f"  Total passes: {num_passes} in {t_total:.1f}ms")
        print(f"  Avg per pass: {avg_per_pass:.1f}ms")
        print()


def profile_arc_generation():
    """Profile the arc G-code generation"""
    print("\n=== PROFILING ARC GENERATION ===\n")
    
    # Generate a medium polygon with multiple passes
    poly = [(0,0), (50,0), (50,30), (0,30)]
    
    t_start = time.perf_counter()
    paths = toolpath_offsets(poly, 6.0, 2.0, inward=True)
    t_offset = (time.perf_counter() - t_start) * 1000
    
    print(f"Offset generation: {len(paths)} paths in {t_offset:.1f}ms")
    
    # Time arc G-code generation
    t_start = time.perf_counter()
    gcode = emit_xy_with_arcs(
        paths,
        z=-1.5,
        safe_z=5.0,
        units="mm",
        feed=600.0,
        link_radius=1.0
    )
    t_arc = (time.perf_counter() - t_start) * 1000
    
    print(f"Arc G-code emit: {len(gcode)} chars in {t_arc:.1f}ms")
    print()


def profile_linear_generation():
    """Profile the linear G-code generation"""
    print("\n=== PROFILING LINEAR GENERATION ===\n")
    
    # Generate a medium polygon with multiple passes
    poly = [(0,0), (50,0), (50,30), (0,30)]
    
    t_start = time.perf_counter()
    paths = toolpath_offsets(poly, 6.0, 2.0, inward=True)
    t_offset = (time.perf_counter() - t_start) * 1000
    
    print(f"Offset generation: {len(paths)} paths in {t_offset:.1f}ms")
    
    # Time linear G-code generation
    t_start = time.perf_counter()
    gcode = emit_xy_polyline_nc(
        paths,
        z=-1.5,
        safe_z=5.0,
        units="mm",
        feed=600.0,
        spindle=12000
    )
    t_linear = (time.perf_counter() - t_start) * 1000
    
    print(f"Linear G-code emit: {len(gcode)} chars in {t_linear:.1f}ms")
    print()


def profile_outward_offset():
    """Profile outward offsetting (profiling mode)"""
    print("\n=== PROFILING OUTWARD OFFSETTING ===\n")
    
    test_cases = [
        ("Small (30x20mm)", [(0,0), (30,0), (30,20), (0,20)]),
        ("Medium (40x30mm)", [(0,0), (40,0), (40,30), (0,30)]),
    ]
    
    for name, poly in test_cases:
        print(f"{name} outward:")
        
        t_start = time.perf_counter()
        paths = toolpath_offsets(poly, 6.0, 2.0, inward=False)
        t_total = (time.perf_counter() - t_start) * 1000
        
        num_passes = len(paths)
        
        print(f"  Passes: {num_passes} in {t_total:.1f}ms")
        if num_passes > 0:
            print(f"  Avg: {t_total/num_passes:.1f}ms per pass")
        print()


def profile_stepover_impact():
    """Test impact of stepover on performance"""
    print("\n=== PROFILING STEPOVER IMPACT ===\n")
    
    poly = [(0,0), (50,0), (50,30), (0,30)]
    tool_dia = 6.0
    
    stepovers = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    for stepover in stepovers:
        t_start = time.perf_counter()
        paths = toolpath_offsets(poly, tool_dia, stepover, inward=True)
        t_total = (time.perf_counter() - t_start) * 1000
        
        num_passes = len(paths)
        
        print(f"Stepover {stepover}mm: {num_passes} passes in {t_total:.1f}ms")


def main():
    print("=" * 60)
    print("N.17 POLYGON OFFSET PERFORMANCE PROFILING")
    print("=" * 60)
    
    profile_offset_generation()
    profile_arc_generation()
    profile_linear_generation()
    profile_outward_offset()
    profile_stepover_impact()
    
    print("\n" + "=" * 60)
    print("PROFILING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
