"""
Phase 1 Blueprint Import Testing Script
Tests API endpoints using FastAPI TestClient (no uvicorn required)
"""
import sys
from pathlib import Path

# Add services/api to path
API_DIR = Path(__file__).parent / "services" / "api"
sys.path.insert(0, str(API_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 60)
print("Phase 1 Blueprint Import - API Testing")
print("=" * 60)

# Test 1: Main health endpoint
print("\n1. Testing /health endpoint")
response = client.get("/health")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 200
assert response.json()["ok"] == True
print("   ✓ Main health endpoint working")

# Test 2: Blueprint health endpoint
print("\n2. Testing /blueprint/health endpoint")
try:
    response = client.get("/blueprint/health")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data}")
        print(f"   Phase: {data.get('phase')}")
        print(f"   Status: {data.get('status')}")
        print(f"   ✓ Blueprint health endpoint working")
    else:
        print(f"   ⚠ Blueprint health endpoint returned {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ✗ Blueprint health endpoint failed: {e}")

# Test 3: Analyzer module import
print("\n3. Testing analyzer module import")
try:
    BLUEPRINT_SERVICE_PATH = Path(__file__).parent / "services" / "blueprint-import"
    sys.path.insert(0, str(BLUEPRINT_SERVICE_PATH))
    from analyzer import create_analyzer
    print("   ✓ Analyzer module imported successfully")
    
    # Check if API key is configured
    import os
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("EMERGENT_LLM_KEY")
    if api_key:
        print(f"   ✓ API key configured (length: {len(api_key)})")
    else:
        print("   ⚠ No API key configured (ANTHROPIC_API_KEY or EMERGENT_LLM_KEY)")
        print("   Note: Analysis will fail without API key")
except Exception as e:
    print(f"   ✗ Analyzer import failed: {e}")

# Test 4: Vectorizer module import
print("\n4. Testing vectorizer module import")
try:
    from vectorizer import create_vectorizer
    print("   ✓ Vectorizer module imported successfully")
except Exception as e:
    print(f"   ✗ Vectorizer import failed: {e}")

# Test 5: Dependencies check
print("\n5. Checking dependencies")
dependencies = {
    "anthropic": "Claude SDK",
    "pdf2image": "PDF conversion",
    "PIL": "Image processing (Pillow)",
    "cv2": "OpenCV",
    "svgwrite": "SVG generation",
    "ezdxf": "DXF generation (Phase 2)"
}

for module, desc in dependencies.items():
    try:
        __import__(module)
        print(f"   ✓ {module} ({desc})")
    except ImportError:
        print(f"   ✗ {module} ({desc}) - NOT INSTALLED")

print("\n" + "=" * 60)
print("Phase 1 Testing Summary")
print("=" * 60)
print("✓ API endpoints accessible via TestClient")
print("⚠ Uvicorn server has startup issues (use TestClient for now)")
print("\nNext Steps:")
print("1. Configure ANTHROPIC_API_KEY environment variable")
print("2. Install poppler-utils for PDF support (Windows: download from GitHub)")
print("3. Test blueprint analysis with sample image")
print("=" * 60)
