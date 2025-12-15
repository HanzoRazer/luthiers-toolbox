"""Debug script to test import endpoint fix."""
from fastapi.testclient import TestClient
import sys
from pathlib import Path

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
print("Testing /geometry/import with embed=True")
print("=" * 60)

# Test with nested structure (embed=True format)
resp = client.post('/geometry/import', json={"geometry": geom})
print(f"\nStatus: {resp.status_code}")
print(f"Response: {resp.text[:200]}")

if resp.status_code == 200:
    print("\n✅ SUCCESS! Import endpoint is working!")
    result = resp.json()
    print(f"Units: {result.get('units')}")
    print(f"Paths: {len(result.get('paths', []))} segments")
else:
    print("\n❌ FAILED")
    print("Full response:", resp.text)
