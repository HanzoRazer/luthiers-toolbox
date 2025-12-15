"""Quick test of parser fixes without needing FastAPI server."""
import sys
sys.path.insert(0, 'c:\\Users\\thepr\\Downloads\\Luthiers ToolBox\\services\\api')

from app.util.gcode_parser import simulate
import math

print("\n╔══════════════════════════════════════╗")
print("║  N.15 PARSER FIX VALIDATION  ║")
print("╚══════════════════════════════════════╝\n")

# Fix 1: Full Circle Arc (Test 4.4)
print("Testing Fix 1: Full Circle Arc")
print("  G-code: G2 X10 Y0 I5 J0 (360° at radius 5mm)")

gcode1 = "G17\nG21\nG0 X10 Y0\nG2 X10 Y0 I5 J0"
result1 = simulate(gcode1, rapid_mm_min=3000, default_feed_mm_min=1200, units="mm")
cut1 = result1['cut_mm']
expected1 = 2 * math.pi * 5  # 31.42mm

print(f"  Result: {cut1:.2f}mm")
print(f"  Expected: {expected1:.2f}mm (2π×5)")

if 31.0 < cut1 < 32.0:
    print("  ✓ PASS - Full circle arcs now working!")
    fix1_pass = True
else:
    print(f"  ✗ FAIL - Got {cut1:.2f}mm instead of {expected1:.2f}mm")
    fix1_pass = False

print()

# Fix 2: Malformed Arc (Test 4.8)
print("Testing Fix 2: Malformed Arc Handling")
print("  G-code: G2 X20 Y0 (no IJ or R specified)")

gcode2 = "G17\nG21\nG0 X10 Y0\nG2 X20 Y0"
result2 = simulate(gcode2, rapid_mm_min=3000, default_feed_mm_min=1200, units="mm")
cut2 = result2['cut_mm']
expected2 = 10.0  # Chord distance

print(f"  Result: {cut2:.2f}mm")
print(f"  Expected: {expected2:.2f}mm (chord distance fallback)")

if 9.9 <= cut2 <= 10.1:
    print("  ✓ PASS - Chord fallback working!")
    fix2_pass = True
else:
    print(f"  ✗ FAIL - Got {cut2:.2f}mm instead of {expected2:.2f}mm")
    fix2_pass = False

print()
print("══════════════════════════════════════")

if fix1_pass and fix2_pass:
    print("✓ BOTH FIXES VERIFIED - Ready for field testing!")
    sys.exit(0)
elif fix1_pass or fix2_pass:
    print("⚠ PARTIAL SUCCESS - One fix needs work")
    sys.exit(1)
else:
    print("✗ FIXES NEED DEBUGGING")
    sys.exit(1)
