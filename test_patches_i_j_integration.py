"""
Test script for Patches I, I1, J integration
Tests all new API endpoints with various scenarios
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
VERBOSE = True

def log_test(name: str, passed: bool, details: str = ""):
    """Log test results"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details and (VERBOSE or not passed):
        print(f"  → {details}")
    print()

def test_simulation_safe_gcode():
    """Test 1: Simulate safe G-code (no issues expected)"""
    test_name = "Simulate Safe G-code"
    
    payload = {
        "gcode": "G0 Z10\nG0 X50 Y50\nG1 Z-3 F1200\nG1 X100 Y100",
        "safe_z": 5.0,
        "units": "mm",
        "feed_xy": 1200.0,
        "feed_z": 600.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cam/simulate_gcode", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Validate response structure
        assert "moves" in data, "Missing 'moves' key"
        assert "issues" in data, "Missing 'issues' key"
        assert "summary" in data, "Missing 'summary' key"
        assert "safety" in data, "Missing 'safety' key"
        
        # Validate safety
        assert data["safety"]["safe"] == True, "Expected safe=true"
        assert data["safety"]["error_count"] == 0, "Expected no errors"
        assert len(data["issues"]) == 0, "Expected no issues"
        
        # Validate moves
        assert len(data["moves"]) == 4, f"Expected 4 moves, got {len(data['moves'])}"
        
        log_test(test_name, True, f"4 moves, 0 issues, safe=true")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def test_simulation_unsafe_rapid():
    """Test 2: Simulate unsafe rapid (error expected)"""
    test_name = "Simulate Unsafe Rapid"
    
    payload = {
        "gcode": "G0 X50 Y50\nG0 Z2\nG1 X100",
        "safe_z": 5.0,
        "units": "mm"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cam/simulate_gcode", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Validate unsafe condition detected
        assert data["safety"]["safe"] == False, "Expected safe=false"
        assert data["safety"]["error_count"] > 0, "Expected errors"
        assert len(data["issues"]) > 0, "Expected issues"
        
        # Validate issue type
        issue = data["issues"][0]
        assert issue["type"] == "unsafe_rapid", f"Expected 'unsafe_rapid', got '{issue['type']}'"
        assert issue["severity"] == "error", "Expected severity='error'"
        
        log_test(test_name, True, f"Detected unsafe rapid at line {issue['line']}")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def test_simulation_cut_below_safe():
    """Test 3: Simulate cut below safe after rapid (warning expected)"""
    test_name = "Simulate Cut Below Safe After Rapid"
    
    payload = {
        "gcode": "G0 Z10\nG0 X50\nG1 Z2 F600",
        "safe_z": 5.0,
        "units": "mm"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cam/simulate_gcode", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Validate warning detected
        assert len(data["issues"]) > 0, "Expected issues"
        
        # Check for cut_below_safe_after_rapid warning
        has_warning = any(
            issue["type"] == "cut_below_safe_after_rapid" 
            for issue in data["issues"]
        )
        assert has_warning, "Expected 'cut_below_safe_after_rapid' warning"
        
        log_test(test_name, True, f"{len(data['issues'])} warnings detected")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def test_simulation_csv_export():
    """Test 4: CSV export format"""
    test_name = "CSV Export Format"
    
    payload = {
        "gcode": "G0 Z10\nG1 Z-5 F600\nG1 X100 F1200",
        "safe_z": 5.0,
        "as_csv": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cam/simulate_gcode", json=payload)
        response.raise_for_status()
        
        # Validate CSV format
        assert response.headers["content-type"] == "text/csv; charset=utf-8", \
            "Expected CSV content type"
        
        csv_data = response.text
        assert "i,code,x,y,z,dx,dy,dz,dxy" in csv_data, "CSV header missing"
        assert "G0" in csv_data, "Expected G0 in CSV"
        assert "G1" in csv_data, "Expected G1 in CSV"
        
        lines = csv_data.strip().split('\n')
        assert len(lines) > 1, "CSV should have header + data rows"
        
        log_test(test_name, True, f"{len(lines)-1} data rows exported")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def test_get_tools():
    """Test 5: Get tool library"""
    test_name = "Get Tool Library"
    
    try:
        response = requests.get(f"{BASE_URL}/cam/tools")
        response.raise_for_status()
        
        data = response.json()
        
        # Validate structure
        assert "units" in data, "Missing 'units' key"
        assert "materials" in data, "Missing 'materials' key"
        assert "tools" in data, "Missing 'tools' key"
        
        # Validate counts
        assert len(data["materials"]) >= 7, f"Expected >=7 materials, got {len(data['materials'])}"
        assert len(data["tools"]) >= 12, f"Expected >=12 tools, got {len(data['tools'])}"
        
        # Validate tool structure
        tool = data["tools"][0]
        required_fields = ["id", "type", "diameter_mm", "flutes", "default_rpm", "default_fxy", "default_fz"]
        for field in required_fields:
            assert field in tool, f"Tool missing field: {field}"
        
        log_test(test_name, True, f"{len(data['tools'])} tools, {len(data['materials'])} materials")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def test_get_posts():
    """Test 6: Get post-processor profiles"""
    test_name = "Get Post-Processor Profiles"
    
    try:
        response = requests.get(f"{BASE_URL}/cam/posts")
        response.raise_for_status()
        
        data = response.json()
        
        # Validate structure
        assert isinstance(data, dict), "Expected dict of post-processors"
        assert len(data) >= 10, f"Expected >=10 controllers, got {len(data)}"
        
        # Check for key controllers
        expected_controllers = ["grbl", "mach4", "linuxcnc", "fusion360", "vcarve"]
        for controller in expected_controllers:
            assert controller in data, f"Missing controller: {controller}"
        
        # Validate post structure
        post = data["grbl"]
        required_fields = ["name", "header", "footer"]
        for field in required_fields:
            assert field in post, f"Post missing field: {field}"
        
        log_test(test_name, True, f"{len(data)} controllers available")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def test_calculate_feeds():
    """Test 7: Calculate optimized feeds"""
    test_name = "Calculate Optimized Feeds"
    
    try:
        # Test with Hard Maple (k=0.9)
        response = requests.post(
            f"{BASE_URL}/cam/tools/flat_6.0/calculate_feeds",
            params={
                "material": "Hard Maple",
                "doc": 3.0,
                "woc": 4.0
            }
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Validate structure
        assert "tool_id" in data, "Missing 'tool_id'"
        assert "material" in data, "Missing 'material'"
        assert "optimized" in data, "Missing 'optimized'"
        
        # Validate optimized values
        opt = data["optimized"]
        assert "rpm" in opt, "Missing 'rpm'"
        assert "feed_xy" in opt, "Missing 'feed_xy'"
        assert "feed_z" in opt, "Missing 'feed_z'"
        assert "chip_load_mm" in opt, "Missing 'chip_load_mm'"
        
        # Validate material coefficient applied
        # Hard Maple k=0.9, default feed_xy=1800
        # Expected: 1800 * 0.9 = 1620
        expected_feed = 1620.0
        assert abs(opt["feed_xy"] - expected_feed) < 1.0, \
            f"Expected feed_xy~{expected_feed}, got {opt['feed_xy']}"
        
        log_test(test_name, True, 
                f"RPM={opt['rpm']}, Feed XY={opt['feed_xy']}, Chip Load={opt['chip_load_mm']:.4f}mm")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def test_calculate_feeds_invalid_tool():
    """Test 8: Calculate feeds with invalid tool (should fail gracefully)"""
    test_name = "Calculate Feeds - Invalid Tool"
    
    try:
        response = requests.post(
            f"{BASE_URL}/cam/tools/nonexistent_tool/calculate_feeds",
            params={"material": "Hard Maple"}
        )
        
        # Expect 404 or 400
        assert response.status_code in [404, 400], \
            f"Expected 404/400, got {response.status_code}"
        
        log_test(test_name, True, f"Properly rejected with {response.status_code}")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def test_calculate_feeds_invalid_material():
    """Test 9: Calculate feeds with invalid material (should fail gracefully)"""
    test_name = "Calculate Feeds - Invalid Material"
    
    try:
        response = requests.post(
            f"{BASE_URL}/cam/tools/flat_6.0/calculate_feeds",
            params={"material": "NonexistentWood"}
        )
        
        # Expect 404 or 400
        assert response.status_code in [404, 400], \
            f"Expected 404/400, got {response.status_code}"
        
        log_test(test_name, True, f"Properly rejected with {response.status_code}")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def test_simulation_response_headers():
    """Test 10: Validate custom response headers"""
    test_name = "Simulation Response Headers"
    
    payload = {
        "gcode": "G0 Z10\nG1 Z-3 F1200",
        "safe_z": 5.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/cam/simulate_gcode", json=payload)
        response.raise_for_status()
        
        # Check for custom headers
        assert "x-cam-summary" in response.headers, "Missing X-CAM-Summary header"
        assert "x-cam-safe" in response.headers, "Missing X-CAM-Safe header"
        assert "x-cam-issues" in response.headers, "Missing X-CAM-Issues header"
        
        # Validate header values
        assert response.headers["x-cam-safe"] in ["true", "false"], \
            "X-CAM-Safe should be 'true' or 'false'"
        
        issues_count = int(response.headers["x-cam-issues"])
        assert issues_count >= 0, "X-CAM-Issues should be non-negative"
        
        log_test(test_name, True, 
                f"Safe={response.headers['x-cam-safe']}, Issues={issues_count}")
        
    except Exception as e:
        log_test(test_name, False, str(e))

def run_all_tests():
    """Run all test cases"""
    print("=" * 60)
    print("Patches I, I1, J Integration Tests")
    print("=" * 60)
    print()
    
    start_time = time.time()
    
    # Run tests
    tests = [
        test_simulation_safe_gcode,
        test_simulation_unsafe_rapid,
        test_simulation_cut_below_safe,
        test_simulation_csv_export,
        test_get_tools,
        test_get_posts,
        test_calculate_feeds,
        test_calculate_feeds_invalid_tool,
        test_calculate_feeds_invalid_material,
        test_simulation_response_headers
    ]
    
    for test in tests:
        test()
    
    elapsed = time.time() - start_time
    
    print("=" * 60)
    print(f"All tests completed in {elapsed:.2f}s")
    print("=" * 60)

if __name__ == "__main__":
    print("NOTE: This script requires the server to be running at http://localhost:8000")
    print()
    input("Press Enter to start tests... (or Ctrl+C to cancel)")
    print()
    
    run_all_tests()
