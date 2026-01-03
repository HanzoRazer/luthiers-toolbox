#!/usr/bin/env python3
"""
Blueprint Phase 3.2 CI Tests - DXF Preflight & Contour Reconstruction

Uses DXF fixtures from tests/fixtures/dxf/
"""

import sys
from pathlib import Path

import requests

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "dxf"
BASE_URL = "http://localhost:8000"


def load_fixture(name: str) -> bytes:
    """Load DXF fixture file."""
    path = FIXTURES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing fixture: {path}")
    return path.read_bytes()


def test_health_check():
    """Test Phase 3.2 health endpoint."""
    print("\n=== Test: Health Check ===")
    r = requests.get(f"{BASE_URL}/cam/blueprint/health")
    
    if r.status_code != 200:
        print(f"FAIL: Health check returned {r.status_code}")
        return False
    
    data = r.json()
    if data.get("phase") != "3.2":
        print(f"FAIL: Wrong phase: {data.get('phase')}")
        return False
    
    endpoints = data.get("endpoints", [])
    required = ["/reconstruct-contours", "/preflight", "/to-adaptive"]
    missing = [e for e in required if e not in endpoints]
    
    if missing:
        print(f"FAIL: Missing endpoints: {missing}")
        return False
    
    print(f"PASS: Phase 3.2 health check")
    print(f"  Endpoints: {endpoints}")
    return True


def test_preflight_json():
    """Test DXF preflight with JSON response."""
    print("\n=== Test: DXF Preflight (JSON) ===")
    dxf_content = load_fixture("minimal.dxf")
    
    files = {"file": ("test.dxf", dxf_content, "application/dxf")}
    data = {"format": "json"}
    
    r = requests.post(f"{BASE_URL}/cam/blueprint/preflight", files=files, data=data)
    
    if r.status_code != 200:
        print(f"FAIL: Preflight returned {r.status_code}")
        print(f"  Response: {r.text[:500]}")
        return False
    
    report = r.json()
    required_fields = ["filename", "passed", "issues", "summary"]
    missing = [f for f in required_fields if f not in report]
    
    if missing:
        print(f"FAIL: Missing response fields: {missing}")
        return False
    
    print(f"PASS: DXF preflight JSON")
    print(f"  Filename: {report.get('filename')}")
    print(f"  Passed: {report.get('passed')}")
    return True


def test_preflight_html():
    """Test DXF preflight with HTML response."""
    print("\n=== Test: DXF Preflight (HTML) ===")
    dxf_content = load_fixture("minimal.dxf")
    
    files = {"file": ("test.dxf", dxf_content, "application/dxf")}
    data = {"format": "html"}
    
    r = requests.post(f"{BASE_URL}/cam/blueprint/preflight", files=files, data=data)
    
    if r.status_code != 200:
        print(f"FAIL: HTML preflight returned {r.status_code}")
        return False
    
    html = r.text
    required_strings = ["DXF Preflight Report", "test.dxf", "Summary", "Issues"]
    missing = [s for s in required_strings if s not in html]
    
    if missing:
        print(f"FAIL: HTML missing content: {missing}")
        return False
    
    print(f"PASS: DXF preflight HTML")
    print(f"  HTML size: {len(html)} bytes")
    return True


def test_contour_reconstruction():
    """Test contour reconstruction from DXF."""
    print("\n=== Test: Contour Reconstruction ===")
    dxf_content = load_fixture("contours_rectangle.dxf")
    
    files = {"file": ("test_lines.dxf", dxf_content, "application/dxf")}
    data = {
        "layer_name": "Contours",
        "tolerance": "0.1",
        "min_loop_points": "3"
    }
    
    r = requests.post(f"{BASE_URL}/cam/blueprint/reconstruct-contours", files=files, data=data)
    
    if r.status_code != 200:
        print(f"FAIL: Reconstruction returned {r.status_code}")
        print(f"  Response: {r.text[:500]}")
        return False
    
    result = r.json()
    required_fields = ["message", "loops", "stats"]
    missing = [f for f in required_fields if f not in result]
    
    if missing:
        print(f"FAIL: Missing response fields: {missing}")
        return False
    
    print(f"PASS: Contour reconstruction")
    print(f"  Message: {result.get('message')}")
    print(f"  Loops found: {len(result.get('loops', []))}")
    return True


def test_om_router():
    """Test OM router endpoints."""
    print("\n=== Test: OM Router ===")
    
    r = requests.get(f"{BASE_URL}/cam/om/templates")
    if r.status_code != 200:
        print(f"FAIL: OM templates returned {r.status_code}")
        return False
    
    data = r.json()
    print(f"  Templates available: {len(data.get('templates', []))}")
    
    r = requests.get(f"{BASE_URL}/cam/om/specs")
    if r.status_code != 200:
        print(f"FAIL: OM specs returned {r.status_code}")
        return False
    
    specs = r.json()
    print(f"PASS: OM router")
    print(f"  Scale: {specs.get('scale_length_mm')}mm, Nut: {specs.get('nut_width_mm')}mm")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Blueprint Phase 3.2 CI Tests")
    print("=" * 60)
    
    tests = [
        test_health_check,
        test_preflight_json,
        test_preflight_html,
        test_contour_reconstruction,
        test_om_router,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"ERROR: {test.__name__} raised {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
