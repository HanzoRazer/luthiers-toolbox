"""
Blueprint Phase 2 -> CAM Pipeline Integration Test

Tests the complete workflow:
1. Blueprint Phase 2 DXF generation (synthetic test)
2. Pipeline router with adaptive planning
3. Full pipeline: DXF -> Preflight -> Adaptive -> Post -> Sim

Run: python test_blueprint_pipeline.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

from fastapi.testclient import TestClient
from app.main import app
import json
import io
import tempfile

client = TestClient(app)

def create_test_dxf():
    """Create a simple test DXF with LWPOLYLINE"""
    import ezdxf
    
    doc = ezdxf.new('R2000')
    msp = doc.modelspace()
    
    # Add a simple rectangle on GEOMETRY layer
    doc.layers.add('GEOMETRY')
    points = [(0, 0), (100, 0), (100, 60), (0, 60), (0, 0)]
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'GEOMETRY'})
    
    # Add an island (hole)
    island_points = [(30, 15), (70, 15), (70, 45), (30, 45), (30, 15)]
    msp.add_lwpolyline(island_points, close=True, dxfattribs={'layer': 'GEOMETRY'})
    
    # Save to bytes
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.dxf', delete=False) as tmp:
        doc.saveas(tmp.name)
        tmp_path = tmp.name
    
    with open(tmp_path, 'rb') as f:
        dxf_bytes = f.read()
    
    os.unlink(tmp_path)
    return dxf_bytes

print("=" * 60)
print("Blueprint Phase 2 -> CAM Pipeline Integration Test")
print("=" * 60)

# Test 1: Create test DXF
print("\n1. Creating test DXF...")
try:
    dxf_bytes = create_test_dxf()
    print(f"   ✓ DXF created: {len(dxf_bytes)} bytes")
except Exception as e:
    print(f"   ✗ Failed to create DXF: {e}")
    exit(1)

# Test 2: Test adaptive_plan operation only
print("\n2. Testing adaptive_plan operation...")
try:
    pipeline_spec = {
        "ops": [
            {"kind": "adaptive_plan", "params": {}}
        ],
        "tool_d": 6.0,
        "units": "mm",
        "geometry_layer": "GEOMETRY"
    }
    
    response = client.post(
        "/cam/pipeline/run",
        data={"pipeline": json.dumps(pipeline_spec)},
        files={"file": ("test_body.dxf", dxf_bytes, "application/dxf")}
    )
    
    if response.status_code == 200:
        result = response.json()
        ops = result.get("ops", [])
        if ops and ops[0]["ok"]:
            payload = ops[0]["payload"]
            print(f"   ✓ Loops extracted: {payload['count']} loops")
            print(f"   ✓ Loop details: {len(payload['loops'][0]['pts'])} points in first loop")
        else:
            print(f"   ✗ Operation failed: {ops[0].get('error')}")
    else:
        print(f"   ✗ HTTP {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Exception: {e}")

# Test 3: Test adaptive_plan + adaptive_plan_run
print("\n3. Testing adaptive planning + execution...")
try:
    pipeline_spec = {
        "ops": [
            {"kind": "adaptive_plan", "params": {}},
            {"kind": "adaptive_plan_run", "params": {
                "tool_d": 6.0,
                "stepover": 0.45,
                "strategy": "Spiral",
                "feed_xy": 1200
            }}
        ],
        "tool_d": 6.0,
        "units": "mm",
        "geometry_layer": "GEOMETRY"
    }
    
    response = client.post(
        "/cam/pipeline/run",
        data={"pipeline": json.dumps(pipeline_spec)},
        files={"file": ("test_body.dxf", dxf_bytes, "application/dxf")}
    )
    
    if response.status_code == 200:
        result = response.json()
        ops = result.get("ops", [])
        
        # Check both operations
        if len(ops) == 2 and all(op["ok"] for op in ops):
            plan_result = ops[1]["payload"]
            stats = plan_result.get("stats", {})
            print(f"   ✓ Adaptive planning successful")
            print(f"   ✓ Toolpath length: {stats.get('length_mm', 0):.2f} mm")
            print(f"   ✓ Time estimate: {stats.get('time_s', 0):.2f} s")
            print(f"   ✓ Move count: {stats.get('move_count', 0)}")
            print(f"   ✓ Summary: {result.get('summary', {})}")
        else:
            for i, op in enumerate(ops):
                if not op["ok"]:
                    print(f"   ✗ Op {i+1} ({op['kind']}) failed: {op.get('error')}")
    else:
        print(f"   ✗ HTTP {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Exception: {e}")

# Test 4: Test full pipeline (without simulation for now)
print("\n4. Testing full pipeline (DXF -> Adaptive -> Post)...")
try:
    pipeline_spec = {
        "ops": [
            {"id": "preflight", "kind": "dxf_preflight", "params": {"debug": False}},
            {"id": "extract", "kind": "adaptive_plan"},
            {"id": "plan", "kind": "adaptive_plan_run", "params": {
                "tool_d": 6.0,
                "stepover": 0.45,
                "strategy": "Spiral"
            }},
            {"id": "post", "kind": "export_post", "params": {"post_id": "GRBL"}}
        ],
        "tool_d": 6.0,
        "units": "mm"
    }
    
    response = client.post(
        "/cam/pipeline/run",
        data={"pipeline": json.dumps(pipeline_spec)},
        files={"file": ("test_body.dxf", dxf_bytes, "application/dxf")}
    )
    
    if response.status_code == 200:
        result = response.json()
        ops = result.get("ops", [])
        
        print(f"   ✓ Pipeline executed: {len(ops)} operations")
        for op in ops:
            status = "✓" if op["ok"] else "✗"
            op_id = op.get("id", "")
            op_kind = op["kind"]
            print(f"     {status} {op_id or op_kind}: {'OK' if op['ok'] else op.get('error', 'Failed')}")
        
        # Check post-processor result
        if len(ops) >= 4 and ops[3]["ok"]:
            post_payload = ops[3]["payload"]
            print(f"   ✓ Post-processor: {post_payload['post_id']}")
            print(f"   ✓ G-code lines: {post_payload['total_lines']}")
            print(f"   ✓ Preview (first 5 lines):")
            preview = post_payload.get('gcode_preview', '')
            for line in preview.split('\n')[:5]:
                print(f"      {line}")
    else:
        print(f"   ✗ HTTP {response.status_code}: {response.text[:500]}")
except Exception as e:
    print(f"   ✗ Exception: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test Blueprint -> CAM Bridge endpoint
print("\n5. Testing Blueprint -> CAM Bridge endpoint...")
try:
    response = client.post(
        "/cam/blueprint/to-adaptive",
        params={
            "layer_name": "GEOMETRY",
            "tool_d": 6.0,
            "stepover": 0.45,
            "strategy": "Spiral",
            "feed_xy": 1200
        },
        files={"file": ("test_body.dxf", dxf_bytes, "application/dxf")}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Bridge endpoint successful")
        print(f"   ✓ Loops extracted: {result.get('loops_extracted', 0)}")
        print(f"   ✓ Moves generated: {len(result.get('moves', []))}")
        stats = result.get('stats', {})
        print(f"   ✓ Length: {stats.get('length_mm', 0):.2f} mm")
        print(f"   ✓ Time: {stats.get('time_min', 0):.2f} min")
    else:
        print(f"   ✗ HTTP {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Exception: {e}")

print("\n" + "=" * 60)
print("Integration Test Complete")
print("=" * 60)
print("\nNext Steps:")
print("1. Test with real guitar blueprint DXF files")
print("2. Add simulation to pipeline (once sim endpoint is stable)")
print("3. Create PipelineLab.vue for full UI workflow")
print("4. Test full workflow: PDF -> Phase 2 -> DXF -> Pipeline -> G-code")
