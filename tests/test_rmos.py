"""Quick RMOS 2.0 endpoint test

Tests the RMOS 2.0 API endpoints on port 8010.
Run with: python tests/test_rmos.py
"""
import requests
import json

BASE_URL = "http://localhost:8010"

def test_health():
    """Test RMOS health check endpoint."""
    print("=== Testing RMOS 2.0 Health ===")
    try:
        resp = requests.get(f"{BASE_URL}/api/rmos/health", timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"
        assert data.get("module") == "RMOS 2.0"
        print("✓ Health check passed\n")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}\n")
        return False

def test_feasibility():
    """Test RMOS feasibility endpoint."""
    print("=== Testing RMOS 2.0 Feasibility ===")
    payload = {
        "design": {
            "outer_diameter_mm": 100.0,
            "inner_diameter_mm": 20.0,
            "ring_count": 3,
            "pattern_type": "herringbone"
        },
        "context": {
            "material_id": "maple",
            "tool_id": "end_mill_6mm",
            "use_shapely_geometry": True
        }
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/rmos/feasibility",
            json=payload,
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        result = resp.json()
        print(f"Score: {result.get('score')}")
        print(f"Risk: {result.get('risk_bucket')}")
        print(f"Efficiency: {result.get('efficiency')}%")
        print(f"Warnings: {len(result.get('warnings', []))}")
        assert resp.status_code == 200
        assert 0 <= result.get("score", -1) <= 100
        assert result.get("risk_bucket") in ["GREEN", "YELLOW", "RED"]
        print("✓ Feasibility check passed\n")
        return True
    except Exception as e:
        print(f"✗ Feasibility check failed: {e}\n")
        return False

def test_bom():
    """Test RMOS BOM endpoint."""
    print("=== Testing RMOS 2.0 BOM ===")
    payload = {
        "design": {
            "outer_diameter_mm": 100.0,
            "inner_diameter_mm": 20.0,
            "ring_count": 3,
            "pattern_type": "herringbone"
        },
        "context": {
            "use_shapely_geometry": True
        }
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/rmos/bom",
            json=payload,
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        result = resp.json()
        print(f"Material required: {result.get('material_required_mm2')} mm²")
        print(f"Tools: {result.get('tool_ids')}")
        print(f"Waste estimate: {result.get('estimated_waste_percent')}%")
        assert resp.status_code == 200
        assert result.get("material_required_mm2", 0) > 0
        print("✓ BOM check passed\n")
        return True
    except Exception as e:
        print(f"✗ BOM check failed: {e}\n")
        return False

def test_toolpaths():
    """Test RMOS toolpaths endpoint."""
    print("=== Testing RMOS 2.0 Toolpaths ===")
    payload = {
        "design": {
            "outer_diameter_mm": 100.0,
            "inner_diameter_mm": 20.0,
            "ring_count": 3,
            "pattern_type": "herringbone"
        },
        "context": {
            "use_shapely_geometry": True
        }
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/rmos/toolpaths",
            json=payload,
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        result = resp.json()
        print(f"Total length: {result.get('total_length_mm')} mm")
        print(f"Estimated time: {result.get('estimated_time_seconds')} seconds")
        print(f"Toolpath count: {len(result.get('toolpaths', []))}")
        assert resp.status_code == 200
        assert result.get("total_length_mm", 0) > 0
        assert len(result.get("toolpaths", [])) > 0
        print("✓ Toolpaths check passed\n")
        return True
    except Exception as e:
        print(f"✗ Toolpaths check failed: {e}\n")
        return False

def test_saw_mode_detection():
    """Test that saw: prefix triggers saw mode (when implemented)."""
    print("=== Testing Saw Mode Detection ===")
    payload = {
        "design": {
            "outer_diameter_mm": 100.0,
            "inner_diameter_mm": 20.0,
            "ring_count": 3,
            "pattern_type": "herringbone"
        },
        "context": {
            "material_id": "maple",
            "tool_id": "saw:10_inch_blade",  # Saw prefix
            "use_shapely_geometry": True
        }
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/api/rmos/feasibility",
            json=payload,
            timeout=10
        )
        print(f"Status: {resp.status_code}")
        # Note: Saw mode implementation pending, just verify endpoint doesn't crash
        assert resp.status_code == 200
        print("✓ Saw mode detection test passed (mode implementation pending)\n")
        return True
    except Exception as e:
        print(f"✗ Saw mode detection failed: {e}\n")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("RMOS 2.0 Endpoint Tests (Port 8010)")
    print("=" * 50 + "\n")
    
    results = {
        "health": test_health(),
        "feasibility": test_feasibility(),
        "bom": test_bom(),
        "toolpaths": test_toolpaths(),
        "saw_mode": test_saw_mode_detection(),
    }
    
    print("=" * 50)
    print("Summary:")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"  {passed}/{total} tests passed")
    
    for name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
    
    print("=" * 50)
    
    if not all(results.values()):
        exit(1)
