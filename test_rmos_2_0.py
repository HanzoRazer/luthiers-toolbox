import requests
import json

# Test RMOS 2.0 feasibility endpoint
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

print("=== Testing RMOS 2.0 Feasibility Endpoint ===\n")

try:
    response = requests.post(
        "http://localhost:8000/api/rmos/feasibility",
        json=payload,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Feasibility Score: {result['score']}")
        print(f"✓ Risk Bucket: {result['risk_bucket']}")
        print(f"✓ Efficiency: {result.get('efficiency', 'N/A')}%")
        print(f"✓ Est. Cut Time: {result.get('estimated_cut_time_seconds', 'N/A')}s")
        print(f"✓ Warnings: {len(result.get('warnings', []))}")
        print(f"\nFull Response:\n{json.dumps(result, indent=2)}")
    else:
        print(f"\n✗ Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("✗ Server not running on localhost:8000")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n=== Testing RMOS 2.0 Health Endpoint ===\n")

try:
    response = requests.get("http://localhost:8000/api/rmos/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"✗ Error: {e}")
