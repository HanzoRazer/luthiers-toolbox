"""
Quick test to determine correct JSON format for /geometry/import endpoint.
"""
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)

# Test geometry
geom = {
    "units": "mm",
    "paths": [
        {"type": "line", "x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 0.0}
    ]
}

print("=" * 60)
print("Test 1: Send geometry fields directly (FastAPI Body() default)")
print("=" * 60)
resp1 = client.post('/geometry/import', json=geom)
print(f"Status: {resp1.status_code}")
if resp1.status_code == 200:
    print("✓ SUCCESS")
    print(f"Response: {resp1.json()}")
else:
    print("✗ FAILED")
    print(f"Response: {resp1.text}")

print("\n" + "=" * 60)
print("Test 2: Send nested under 'geometry' key (per docs example)")
print("=" * 60)
resp2 = client.post('/geometry/import', json={"geometry": geom})
print(f"Status: {resp2.status_code}")
if resp2.status_code == 200:
    print("✓ SUCCESS")
    print(f"Response: {resp2.json()}")
else:
    print("✗ FAILED")
    print(f"Response: {resp2.text}")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
if resp1.status_code == 200:
    print("✓ Use direct geometry fields: json=sample_geometry_simple")
elif resp2.status_code == 200:
    print("✓ Use nested structure: json={'geometry': sample_geometry_simple}")
else:
    print("✗ NEITHER WORKS - endpoint may have issues")
