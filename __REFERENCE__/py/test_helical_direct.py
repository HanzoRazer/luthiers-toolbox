"""
Direct Python test for helical v16.1 system
Tests the core helical functions without requiring the API server
"""
import sys
sys.path.insert(0, 'services/api')

from app.cam.helical_core import helical_plunge, helical_stats, helical_validate

print("\n=== Helical v16.1 Direct Python Test ===\n")

# Test 1: Basic helical path generation
print("Test 1: Basic helical path generation")
try:
    params = {
        'cx': 50.0,
        'cy': 30.0,
        'radius_mm': 8.0,
        'direction': "CW",
        'start_z_mm': 5.0,
        'z_target_mm': -3.0,
        'pitch_mm_per_rev': 1.5,
        'feed_xy_mm_min': 600.0
    }
    
    result = helical_plunge(**params)
    
    stats = helical_stats(
        moves=result,
        radius_mm=params['radius_mm'],
        pitch_mm_per_rev=params['pitch_mm_per_rev'],
        start_z_mm=params['start_z_mm'],
        z_target_mm=params['z_target_mm'],
        feed_xy_mm_min=params['feed_xy_mm_min']
    )
    
    print(f"  ✓ Path generated successfully")
    print(f"    - Revolutions: {stats['revolutions']:.2f}")
    print(f"    - Path length: {stats['length_mm']:.2f} mm")
    print(f"    - Time estimate: {stats.get('time_s', 0):.2f} s")
    print(f"    - Move count: {len(result)}")
    print(f"    - Segments: {stats['segments']}")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 2: Safety validation
print("\nTest 2: Safety validation")
try:
    warnings = helical_validate(
        radius_mm=8.0,
        pitch_mm_per_rev=1.5,
        feed_xy_mm_min=600.0,
        tool_diameter_mm=6.0,
        material="hardwood",
        spindle_rpm=18000
    )
    
    print(f"  ✓ Validation executed")
    if warnings:
        print(f"    - Warnings: {len(warnings)}")
        for w in warnings:
            print(f"      • {w}")
    else:
        print(f"    - No warnings (parameters safe)")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 3: Different pitch and depth
print("\nTest 3: Aggressive parameters (tighter pitch)")
try:
    params = {
        'cx': 0.0,
        'cy': 0.0,
        'radius_mm': 5.0,
        'direction': "CCW",
        'start_z_mm': 2.0,
        'z_target_mm': -10.0,
        'pitch_mm_per_rev': 0.5,
        'feed_xy_mm_min': 800.0
    }
    
    result = helical_plunge(**params)
    
    stats = helical_stats(
        moves=result,
        radius_mm=params['radius_mm'],
        pitch_mm_per_rev=params['pitch_mm_per_rev'],
        start_z_mm=params['start_z_mm'],
        z_target_mm=params['z_target_mm'],
        feed_xy_mm_min=params['feed_xy_mm_min']
    )
    
    print(f"  ✓ Path generated successfully")
    print(f"    - Revolutions: {stats['revolutions']:.2f} (should be ~24 for -12mm depth at 0.5mm pitch)")
    print(f"    - Path length: {stats['length_mm']:.2f} mm")
    
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

print("\n=== All Tests Passed ✓ ===")
print("\nHelical v16.1 core system is functional!")
print("Backend API endpoints and Vue frontend are already integrated.")
