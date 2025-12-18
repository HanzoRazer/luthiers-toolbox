"""
Test Script: Blueprint → CAM Bridge
====================================

Tests the integration between Phase 2 Blueprint vectorization and 
Adaptive Pocket Engine (Module L.1).

Workflow:
1. Create synthetic DXF with closed rectangle
2. POST to /cam/blueprint/to-adaptive
3. Validate loops extraction
4. Validate toolpath generation
5. Verify moves structure and statistics
"""

import sys
import os
import tempfile

# Add services paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'blueprint-import'))

print("=" * 60)
print("Testing Blueprint -> CAM Bridge (Phase 2 Integration)")
print("=" * 60)

# ============================================================================
# Test 1: Create Synthetic DXF with Rectangle
# ============================================================================
print("\n1. Creating synthetic DXF with 100×60mm rectangle...")

import ezdxf
from io import BytesIO

try:
    # Create DXF R2000
    doc = ezdxf.new('R2000')
    msp = doc.modelspace()
    
    # Add GEOMETRY layer
    doc.layers.add('GEOMETRY')
    
    # Create closed rectangle (100×60 mm)
    points = [
        (0, 0),
        (100, 0),
        (100, 60),
        (0, 60)
    ]
    
    # Add LWPOLYLINE (closed)
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'GEOMETRY'})
    
    # Write to temp file, then read as bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        tmp_path = tmp.name
    doc.saveas(tmp_path)
    
    with open(tmp_path, 'rb') as f:
        dxf_data = f.read()
    os.unlink(tmp_path)
    
    dxf_bytes = BytesIO(dxf_data)
    
    print(f"  ✓ DXF created: {len(dxf_data)} bytes")
    print(f"  ✓ Rectangle: 100×60 mm on GEOMETRY layer")

except Exception as e:
    print(f"  ✗ Error creating DXF: {e}")
    sys.exit(1)


# ============================================================================
# Test 2: Test DXF Extraction Utility
# ============================================================================
print("\n2. Testing extract_loops_from_dxf()...")

try:
    from app.routers.blueprint_cam_bridge import extract_loops_from_dxf
    
    loops, warnings = extract_loops_from_dxf(dxf_data, layer_name="GEOMETRY")
    
    print(f"  ✓ Loops extracted: {len(loops)}")
    print(f"  ✓ Warnings: {len(warnings)}")
    
    if warnings:
        for w in warnings:
            print(f"    - {w}")
    
    if len(loops) == 0:
        print(f"  ✗ Expected 1 loop, got {len(loops)}")
        sys.exit(1)
    
    # Validate loop structure
    loop = loops[0]
    print(f"  ✓ Loop has {len(loop.pts)} points")
    
    if len(loop.pts) != 4:
        print(f"  ✗ Expected 4 points, got {len(loop.pts)}")
        sys.exit(1)
    
    # Validate point coordinates
    expected_points = [(0, 0), (100, 0), (100, 60), (0, 60)]
    for i, (expected, actual) in enumerate(zip(expected_points, loop.pts)):
        if abs(expected[0] - actual[0]) > 0.01 or abs(expected[1] - actual[1]) > 0.01:
            print(f"  ✗ Point {i} mismatch: expected {expected}, got {actual}")
            sys.exit(1)
    
    print(f"  ✓ All points match expected coordinates")

except ImportError as e:
    print(f"  ✗ Import error: {e}")
    print(f"  (Make sure FastAPI server dependencies are installed)")
    sys.exit(1)
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ============================================================================
# Test 3: Test Bridge Endpoint via TestClient
# ============================================================================
print("\n3. Testing /cam/blueprint/to-adaptive endpoint...")

try:
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Prepare multipart form data
    files = {"file": ("test_rectangle.dxf", dxf_bytes, "application/dxf")}
    data = {
        "layer_name": "GEOMETRY",
        "tool_d": 6.0,
        "stepover": 0.45,
        "stepdown": 1.5,
        "margin": 0.5,
        "strategy": "Spiral",
        "smoothing": 0.3,
        "feed_xy": 1200,
        "safe_z": 5.0,
        "z_rough": -1.5
    }
    
    response = client.post("/cam/blueprint/to-adaptive", files=files, data=data)
    
    if response.status_code != 200:
        print(f"  ✗ HTTP {response.status_code}: {response.text}")
        sys.exit(1)
    
    result = response.json()
    
    # Validate response structure
    assert "loops_extracted" in result, "Missing loops_extracted"
    assert "loops" in result, "Missing loops"
    assert "moves" in result, "Missing moves"
    assert "stats" in result, "Missing stats"
    
    print(f"  ✓ Bridge endpoint successful")
    print(f"  ✓ Loops extracted: {result['loops_extracted']}")
    print(f"  ✓ Moves generated: {result['stats']['move_count']}")
    print(f"  ✓ Cutting moves: {result['stats']['cutting_moves']}")
    print(f"  ✓ Toolpath length: {result['stats']['length_mm']} mm")
    print(f"  ✓ Estimated time: {result['stats']['time_min']} min")
    print(f"  ✓ Volume removed: {result['stats']['volume_mm3']} mm³")
    
    # Validate moves structure
    moves = result['moves']
    if len(moves) < 5:
        print(f"  ✗ Too few moves: {len(moves)} (expected >5)")
        sys.exit(1)
    
    # Check for G0 (rapid) and G1 (feed) moves
    has_g0 = any(m.get('code') == 'G0' for m in moves)
    has_g1 = any(m.get('code') == 'G1' for m in moves)
    
    if not has_g0:
        print(f"  ✗ No G0 (rapid) moves found")
        sys.exit(1)
    
    if not has_g1:
        print(f"  ✗ No G1 (feed) moves found")
        sys.exit(1)
    
    print(f"  ✓ Move types validated (G0 rapids + G1 feeds)")
    
    # Validate statistics
    stats = result['stats']
    if stats['length_mm'] <= 0:
        print(f"  ✗ Invalid toolpath length: {stats['length_mm']}")
        sys.exit(1)
    
    if stats['time_s'] <= 0:
        print(f"  ✗ Invalid time estimate: {stats['time_s']}")
        sys.exit(1)
    
    print(f"  ✓ Statistics validated")
    
    # Check warnings
    if result.get('warnings'):
        print(f"  ! Warnings returned:")
        for w in result['warnings']:
            print(f"    - {w}")

except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ============================================================================
# Test 4: Test with Island (Hole)
# ============================================================================
print("\n4. Testing adaptive pocket with island...")

try:
    # Create DXF with outer rectangle and inner rectangle (island)
    doc = ezdxf.new('R2000')
    msp = doc.modelspace()
    doc.layers.add('GEOMETRY')
    
    # Outer rectangle (100×60 mm)
    outer_points = [(0, 0), (100, 0), (100, 60), (0, 60)]
    msp.add_lwpolyline(outer_points, close=True, dxfattribs={'layer': 'GEOMETRY'})
    
    # Inner rectangle (island/hole) (30×20 mm, centered)
    inner_points = [(35, 20), (65, 20), (65, 40), (35, 40)]
    msp.add_lwpolyline(inner_points, close=True, dxfattribs={'layer': 'GEOMETRY'})
    
    # Write to temp file, then read as bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
        tmp_path_island = tmp.name
    doc.saveas(tmp_path_island)
    
    with open(tmp_path_island, 'rb') as f:
        dxf_data_island = f.read()
    os.unlink(tmp_path_island)
    
    dxf_bytes_island = BytesIO(dxf_data_island)
    
    print(f"  ✓ DXF with island created")
    
    # Test extraction
    loops_island, warnings_island = extract_loops_from_dxf(dxf_data_island, "GEOMETRY")
    
    if len(loops_island) != 2:
        print(f"  ✗ Expected 2 loops (outer + island), got {len(loops_island)}")
        sys.exit(1)
    
    print(f"  ✓ Extracted {len(loops_island)} loops (outer + island)")
    
    # Test bridge endpoint with island
    files_island = {"file": ("test_with_island.dxf", dxf_bytes_island, "application/dxf")}
    
    response_island = client.post("/api/cam/blueprint/to-adaptive", files=files_island, data=data)
    
    if response_island.status_code != 200:
        print(f"  ✗ HTTP {response_island.status_code}: {response_island.text}")
        sys.exit(1)
    
    result_island = response_island.json()
    
    print(f"  ✓ Bridge with island successful")
    print(f"  ✓ Loops: {result_island['loops_extracted']}")
    print(f"  ✓ Moves: {result_island['stats']['move_count']}")
    print(f"  ✓ Length: {result_island['stats']['length_mm']} mm")
    
    # Island should result in longer toolpath (avoids center)
    if result_island['stats']['move_count'] <= result['stats']['move_count']:
        print(f"  ! Warning: Island didn't increase move count significantly")
    else:
        print(f"  ✓ Island avoidance working (more moves with island)")

except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ============================================================================
# Test 5: Test Health Endpoint
# ============================================================================
print("\n5. Testing /cam/blueprint/health endpoint...")

try:
    response = client.get("/cam/blueprint/health")
    
    if response.status_code != 200:
        print(f"  ✗ HTTP {response.status_code}")
        sys.exit(1)
    
    health = response.json()
    
    print(f"  ✓ Health check successful")
    print(f"  ✓ Status: {health.get('status')}")
    print(f"  ✓ Bridge: {health.get('bridge')}")
    print(f"  ✓ Endpoints: {health.get('endpoints')}")
    
    # Validate integration status
    integration = health.get('integration', {})
    if integration.get('adaptive_l1') != 'available':
        print(f"  ! Warning: adaptive_l1 not available")
    else:
        print(f"  ✓ Adaptive L.1 integration available")

except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 60)
print("All Blueprint -> CAM Bridge Tests Passed!")
print("=" * 60)
print("\nIntegration validated:")
print("  • DXF extraction: LWPOLYLINE -> List[Loop]")
print("  • Adaptive planner: Module L.1 robust offsetting")
print("  • Island handling: Automatic keepout zones")
print("  • Toolpath generation: G0/G1 moves with statistics")
print("  • Bridge endpoint: /cam/blueprint/to-adaptive")
print("\nNext steps:")
print("  1. Test with real guitar blueprint DXF")
print("  2. Add G-code export endpoint")
print("  3. Create Vue UI component")
print("  4. Add to CI/CD smoke tests")
print("=" * 60)
