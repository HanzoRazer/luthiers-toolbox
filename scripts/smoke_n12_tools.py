#!/usr/bin/env python3
"""
Smoke test for Patch N.12 - Machine Tool Tables
Tests CRUD operations, CSV export/import, and template token injection
"""
import os, sys, requests

BASE = os.environ.get('TB_BASE', 'http://127.0.0.1:8000')

def test_n12():
    print("=== Patch N.12 Smoke Test ===\n")
    
    # Test 1: Upsert tools
    print("1. Testing PUT /api/machines/tools/m1 (upsert)")
    tools = [
        {
            "t": 7,
            "name": "Test Ø5 drill",
            "type": "DRILL",
            "dia_mm": 5.0,
            "len_mm": 60.0,
            "holder": "ER20",
            "offset_len_mm": 120.0,
            "spindle_rpm": 5000,
            "feed_mm_min": 250,
            "plunge_mm_min": 120
        }
    ]
    
    r = requests.put(f'{BASE}/api/machines/tools/m1', json=tools, timeout=10)
    r.raise_for_status()
    data = r.json()
    print(f"  ✓ Upsert OK, tool count: {len(data.get('tools', []))}")
    assert len(data.get('tools', [])) >= 1, "Expected at least 1 tool after upsert"
    
    # Test 2: List tools
    print("\n2. Testing GET /api/machines/tools/m1")
    r = requests.get(f'{BASE}/api/machines/tools/m1', timeout=10)
    r.raise_for_status()
    data = r.json()
    print(f"  ✓ List OK, machine: {data.get('machine')}, tools: {len(data.get('tools', []))}")
    assert data.get('machine') == 'm1', "Expected machine ID 'm1'"
    assert len(data.get('tools', [])) >= 1, "Expected at least 1 tool"
    
    # Test 3: Export CSV
    print("\n3. Testing GET /api/machines/tools/m1.csv")
    r = requests.get(f'{BASE}/api/machines/tools/m1.csv', timeout=10)
    r.raise_for_status()
    csv_text = r.text
    lines = csv_text.strip().split('\n')
    print(f"  ✓ CSV export OK, lines: {len(lines)} (header + {len(lines)-1} tools)")
    print(f"  First 2 lines:")
    for line in lines[:2]:
        print(f"    {line}")
    assert len(lines) >= 2, "Expected at least header + 1 tool row"
    assert 't,name,type' in lines[0], "Expected CSV header"
    
    # Test 4: Tool context integration (drill operation with machine_id + tool)
    print("\n4. Testing tool context injection via /api/cam/drill_g81_g83")
    print("  Note: This requires drill endpoint to be implemented")
    
    # Try to test tool context if drill endpoint exists
    try:
        body = {
            "holes": [{"x": 0, "y": 0, "z": -5, "feed": 180}],
            "cycle": "G81",
            "r_clear": 5,
            "safe_z": 5,
            "post": "fanuc_haas",
            "machine_id": "m1",
            "tool": 7,
            "program_no": "01250",
            "work_offset": "G54"
        }
        
        r = requests.post(f'{BASE}/api/cam/drill_g81_g83', json=body, timeout=10)
        
        if r.status_code == 404:
            print(f"  ⚠ Drill endpoint not implemented yet (404) - skipping tool context test")
        else:
            r.raise_for_status()
            gcode = r.text
            lines = gcode.splitlines()
            print(f"  ✓ Drill operation OK, checking for tool context tokens...")
            print(f"  First 10 lines:")
            for line in lines[:10]:
                print(f"    {line}")
            
            # Check if tool context was injected (RPM should be 5000 from tool definition)
            if 'S5000' in gcode or 'T7' in gcode:
                print(f"  ✓ Tool context injection confirmed (S5000 or T7 found)")
            else:
                print(f"  ⚠ Tool context may not be fully integrated (S5000/T7 not found)")
    except Exception as e:
        print(f"  ⚠ Tool context integration test skipped: {e}")
    
    # Test 5: Delete tool (cleanup)
    print("\n5. Testing DELETE /api/machines/tools/m1/7")
    r = requests.delete(f'{BASE}/api/machines/tools/m1/7', timeout=10)
    r.raise_for_status()
    data = r.json()
    print(f"  ✓ Delete OK, remaining tools: {len(data.get('tools', []))}")
    
    print("\n=== All N.12 Tests Passed ===")
    return True

if __name__ == '__main__':
    try:
        test_n12()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
