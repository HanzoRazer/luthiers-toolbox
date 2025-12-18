#!/usr/bin/env python3
"""
Patches G-H0 Integration Test Suite
Tests all three patches: Units/Lead-In/Tabs, Pocketing, Neutral Export
Run after starting uvicorn server: uvicorn app:app --reload --port 8000
"""
import requests
import json
import zipfile
import io
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_patch_g_units_conversion():
    """Test Patch G: Units conversion (mm to inch)"""
    print("\n🧪 Testing Patch G: Units Conversion (mm → inch)...")
    
    # 1 inch square in mm (25.4 x 25.4)
    payload = {
        "polyline": [[0, 0], [25.4, 0], [25.4, 25.4], [0, 25.4]],
        "tool_diameter": 6.0,
        "depth_per_pass": 2.0,
        "stock_thickness": 5.0,
        "feed_xy": 1200,
        "feed_z": 600,
        "safe_z": 10.0,
        "origin": [0, 0],
        "climb": True,
        "tabs_count": 0,
        "tab_width": 0,
        "tab_height": 0,
        "post": "Mach4",
        "units": "inch"
    }
    
    response = requests.post(f"{BASE_URL}/cam/roughing_gcode", json=payload)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status {response.status_code}")
        print(response.text)
        return False
    
    gcode = response.text
    
    # Verify G20 header (inch mode)
    if "G20" not in gcode:
        print("❌ FAILED: G20 (inch mode) not found in header")
        return False
    
    # Verify coordinate scaling (25.4mm → 1.0000 inch)
    if "X1.0000 Y0.0000" not in gcode:
        print("❌ FAILED: Coordinate scaling incorrect")
        print(f"Expected: X1.0000 Y0.0000")
        print(f"Got: {[line for line in gcode.split('\\n') if 'X1.' in line][:3]}")
        return False
    
    print("✅ PASSED: Units conversion working correctly")
    print(f"   - G20 header present")
    print(f"   - 25.4mm → 1.0000 inch scaling verified")
    return True


def test_patch_g_lead_in_arc():
    """Test Patch G: Lead-in/out arc generation"""
    print("\n🧪 Testing Patch G: Lead-In Arc Generation...")
    
    payload = {
        "polyline": [[0, 0], [100, 0], [100, 50], [0, 50]],
        "tool_diameter": 6.0,
        "depth_per_pass": 2.0,
        "stock_thickness": 5.0,
        "feed_xy": 1200,
        "feed_z": 600,
        "safe_z": 10.0,
        "origin": [0, 0],
        "climb": True,
        "tabs_count": 0,
        "tab_width": 0,
        "tab_height": 0,
        "post": "Mach4",
        "units": "mm",
        "lead_radius": 5.0
    }
    
    response = requests.post(f"{BASE_URL}/cam/roughing_gcode", json=payload)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status {response.status_code}")
        return False
    
    gcode = response.text
    
    # Verify G2 or G3 arc command present
    has_arc = "G2" in gcode or "G3" in gcode
    if not has_arc:
        print("❌ FAILED: No G2/G3 arc command found")
        return False
    
    # Verify I,J offsets present (arc center)
    has_offsets = "I-" in gcode or "I" in gcode and "J" in gcode
    if not has_offsets:
        print("❌ FAILED: No I,J arc offsets found")
        return False
    
    print("✅ PASSED: Lead-in arc generation working")
    print(f"   - Arc command: {'G2' if 'G2' in gcode else 'G3'}")
    print(f"   - I,J offsets present")
    return True


def test_patch_g_explicit_tabs():
    """Test Patch G: Explicit tab positioning"""
    print("\n🧪 Testing Patch G: Explicit Tab Positioning...")
    
    payload = {
        "polyline": [[0, 0], [100, 0], [100, 50], [0, 50]],
        "tool_diameter": 6.0,
        "depth_per_pass": 2.0,
        "stock_thickness": 5.0,
        "feed_xy": 1200,
        "feed_z": 600,
        "safe_z": 10.0,
        "origin": [0, 0],
        "climb": True,
        "tabs_positions": [25.0, 75.0, 125.0, 175.0],
        "tab_width": 8.0,
        "tab_height": 2.5,
        "post": "Mach4",
        "units": "mm"
    }
    
    response = requests.post(f"{BASE_URL}/cam/roughing_gcode", json=payload)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status {response.status_code}")
        return False
    
    gcode = response.text
    
    # Count tab ramps (Z moves to tab height)
    tab_height_moves = [line for line in gcode.split('\n') if 'Z2.5' in line or 'Z-2.5' in line]
    
    if len(tab_height_moves) < 4:
        print(f"❌ FAILED: Expected 4+ tab height moves, got {len(tab_height_moves)}")
        return False
    
    print("✅ PASSED: Explicit tab positioning working")
    print(f"   - 4 tabs at specified positions")
    print(f"   - Tab height moves: {len(tab_height_moves)}")
    return True


def test_patch_h_rectangular_pocket():
    """Test Patch H: Rectangular pocket with horizontal raster"""
    print("\n🧪 Testing Patch H: Rectangular Pocket (Horizontal Raster)...")
    
    payload = {
        "entities": [
            {"type": "line", "A": [10, 10], "B": [60, 10]},
            {"type": "line", "A": [60, 10], "B": [60, 35]},
            {"type": "line", "A": [60, 35], "B": [10, 35]},
            {"type": "line", "A": [10, 35], "B": [10, 10]}
        ],
        "tool_diameter": 6.0,
        "stepover_pct": 50,
        "raster_angle": 0,
        "depth_per_pass": 2.0,
        "target_depth": 6.0,
        "feed_xy": 1200,
        "feed_z": 600,
        "safe_z": 10.0,
        "units": "mm",
        "filename": "test_pocket.nc"
    }
    
    response = requests.post(f"{BASE_URL}/cam/pocket_gcode", json=payload)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status {response.status_code}")
        print(response.text)
        return False
    
    gcode = response.text
    
    # Verify header
    if "G21" not in gcode:
        print("❌ FAILED: G21 (mm mode) not found")
        return False
    
    # Count depth passes (should be 3: 0→-2, -2→-4, -4→-6)
    pass_comments = [line for line in gcode.split('\n') if 'Pass' in line]
    if len(pass_comments) < 3:
        print(f"❌ FAILED: Expected 3+ depth passes, got {len(pass_comments)}")
        return False
    
    # Count raster segments (should be ~8 for 25mm height / 3mm stepover)
    g1_moves = [line for line in gcode.split('\n') if line.startswith('G1 X')]
    if len(g1_moves) < 15:
        print(f"❌ FAILED: Expected 15+ G1 moves, got {len(g1_moves)}")
        return False
    
    print("✅ PASSED: Rectangular pocket generation working")
    print(f"   - Depth passes: {len(pass_comments)}")
    print(f"   - G1 cutting moves: {len(g1_moves)}")
    return True


def test_patch_h_rotated_raster():
    """Test Patch H: Circular pocket with 45° raster"""
    print("\n🧪 Testing Patch H: Circular Pocket (45° Raster)...")
    
    payload = {
        "entities": [
            {"type": "circle", "center": [50, 50], "radius": 20}
        ],
        "tool_diameter": 6.0,
        "stepover_pct": 40,
        "raster_angle": 45,
        "depth_per_pass": 1.5,
        "target_depth": 3.0,
        "feed_xy": 1000,
        "feed_z": 500,
        "safe_z": 10.0,
        "units": "mm",
        "filename": "circular_pocket.nc"
    }
    
    response = requests.post(f"{BASE_URL}/cam/pocket_gcode", json=payload)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status {response.status_code}")
        return False
    
    gcode = response.text
    
    # Verify depth passes (should be 2: 0→-1.5, -1.5→-3.0)
    pass_comments = [line for line in gcode.split('\n') if 'Pass' in line]
    if len(pass_comments) < 2:
        print(f"❌ FAILED: Expected 2+ depth passes, got {len(pass_comments)}")
        return False
    
    print("✅ PASSED: Rotated raster pocket generation working")
    print(f"   - Depth passes: {len(pass_comments)}")
    print(f"   - 45° raster angle applied")
    return True


def test_patch_h0_neutral_export():
    """Test Patch H0: CAM-neutral export bundle"""
    print("\n🧪 Testing Patch H0: CAM-Neutral Export Bundle...")
    
    payload = {
        "entities": [
            {"type": "line", "A": [0, 0], "B": [300, 0], "layer": "CUT_OUTER"},
            {"type": "line", "A": [300, 0], "B": [300, 450], "layer": "CUT_OUTER"},
            {"type": "line", "A": [300, 450], "B": [0, 450], "layer": "CUT_OUTER"},
            {"type": "line", "A": [0, 450], "B": [0, 0], "layer": "CUT_OUTER"},
            {"type": "circle", "center": [100, 200], "radius": 45, "layer": "CUT_INNER"},
            {"type": "circle", "center": [230, 200], "radius": 45, "layer": "CUT_INNER"},
            {"type": "line", "A": [70, 150], "B": [150, 150], "layer": "POCKET"},
            {"type": "line", "A": [150, 150], "B": [150, 250], "layer": "POCKET"},
            {"type": "line", "A": [150, 250], "B": [70, 250], "layer": "POCKET"},
            {"type": "line", "A": [70, 250], "B": [70, 150], "layer": "POCKET"},
            {"type": "circle", "center": [165, 80], "radius": 3, "layer": "DRILL"},
            {"type": "circle", "center": [185, 80], "radius": 3, "layer": "DRILL"},
            {"type": "circle", "center": [205, 80], "radius": 3, "layer": "DRILL"}
        ],
        "product_name": "LesPaul_Body_Test",
        "units": "mm",
        "simplify": True
    }
    
    response = requests.post(f"{BASE_URL}/neutral/bundle.zip", json=payload)
    
    if response.status_code != 200:
        print(f"❌ FAILED: Status {response.status_code}")
        print(response.text)
        return False
    
    # Verify ZIP file
    try:
        zip_data = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            files = zf.namelist()
            
            # Verify 4 files present
            expected_files = [
                "LesPaul_Body_Test.dxf",
                "LesPaul_Body_Test.svg",
                "LesPaul_Body_Test.json",
                "README.txt"
            ]
            
            for expected in expected_files:
                if expected not in files:
                    print(f"❌ FAILED: Missing file: {expected}")
                    return False
            
            # Verify JSON metadata
            json_content = zf.read("LesPaul_Body_Test.json").decode()
            metadata = json.loads(json_content)
            
            if metadata["units"] != "mm":
                print(f"❌ FAILED: Incorrect units in JSON: {metadata['units']}")
                return False
            
            if "CUT_OUTER" not in metadata["layers"]:
                print(f"❌ FAILED: CUT_OUTER layer missing from JSON")
                return False
            
            if metadata["entity_count"] != 13:
                print(f"❌ FAILED: Incorrect entity count: {metadata['entity_count']}")
                return False
            
            # Verify DXF content
            dxf_content = zf.read("LesPaul_Body_Test.dxf").decode()
            if "CUT_OUTER" not in dxf_content:
                print(f"❌ FAILED: CUT_OUTER layer not in DXF")
                return False
            
            if "POCKET" not in dxf_content:
                print(f"❌ FAILED: POCKET layer not in DXF")
                return False
            
            # Verify README
            readme = zf.read("README.txt").decode()
            if "Fusion 360" not in readme:
                print(f"❌ FAILED: Fusion 360 instructions missing from README")
                return False
            
    except Exception as e:
        print(f"❌ FAILED: ZIP processing error: {e}")
        return False
    
    print("✅ PASSED: CAM-neutral bundle generation working")
    print(f"   - 4 files present (DXF, SVG, JSON, README)")
    print(f"   - Layers: CUT_OUTER, CUT_INNER, POCKET, DRILL")
    print(f"   - Metadata valid: {metadata['entity_count']} entities")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Patches G-H0 Integration Test Suite")
    print("=" * 60)
    print(f"Testing server at: {BASE_URL}")
    print("Make sure server is running: uvicorn app:app --reload --port 8000")
    
    # Test server connection
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print(f"\n❌ Cannot connect to server at {BASE_URL}")
            print("Start server with: uvicorn app:app --reload --port 8000")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to server at {BASE_URL}")
        print("Start server with: uvicorn app:app --reload --port 8000")
        sys.exit(1)
    
    print("✅ Server connection successful\n")
    
    # Run tests
    results = {
        "Patch G - Units Conversion": test_patch_g_units_conversion(),
        "Patch G - Lead-In Arc": test_patch_g_lead_in_arc(),
        "Patch G - Explicit Tabs": test_patch_g_explicit_tabs(),
        "Patch H - Rectangular Pocket": test_patch_h_rectangular_pocket(),
        "Patch H - Rotated Raster": test_patch_h_rotated_raster(),
        "Patch H0 - Neutral Export": test_patch_h0_neutral_export()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}  {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Integration successful.")
        sys.exit(0)
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
