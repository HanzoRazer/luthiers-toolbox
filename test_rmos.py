"""Quick RMOS 2.0 endpoint test"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Health check
print("=== Testing RMOS 2.0 Health ===")
try:
    resp = requests.get(f"{BASE_URL}/api/rmos/health", timeout=5)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    print("✓ Health check passed\n")
except Exception as e:
    print(f"✗ Health check failed: {e}\n")

# Test 2: Feasibility endpoint
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
    print(f"Warnings: {len(result.get('warnings', []))}")
    print("✓ Feasibility check passed\n")
except Exception as e:
    print(f"✗ Feasibility check failed: {e}\n")

print("=== RMOS 2.0 Tests Complete ===")
