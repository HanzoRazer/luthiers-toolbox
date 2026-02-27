#!/usr/bin/env python3
"""
API Smoke Posts Test (v15.5)

Smoke test for post-processor endpoints. Produces smoke_posts.json
for the API Health + Smoke workflow.

Usage:
    python api_smoke_posts.py http://127.0.0.1:8000
"""
import json
import sys
import time

try:
    import requests
except ImportError:
    print("ERROR: requests library required. pip install requests")
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: api_smoke_posts.py <API_BASE>")
        sys.exit(1)

    api_base = sys.argv[1].rstrip("/")
    results = {}
    errors = []

    # Test 1: Health check
    try:
        r = requests.get(f"{api_base}/health", timeout=10)
        results["health"] = {
            "status": r.status_code,
            "bytes": len(r.content),
            "ok": r.status_code == 200,
        }
        if r.status_code != 200:
            errors.append(f"Health check returned {r.status_code}")
    except Exception as e:
        results["health"] = {"status": 0, "bytes": 0, "ok": False, "error": str(e)}
        errors.append(f"Health check failed: {e}")

    # Test 2: Post-processor presets endpoint
    try:
        r = requests.get(f"{api_base}/api/tooling/posts", timeout=10)
        posts = r.json() if r.ok else []
        results["posts"] = {
            "status": r.status_code,
            "bytes": len(r.content),
            "count": len(posts) if isinstance(posts, list) else 0,
            "ok": r.status_code == 200,
        }
        if r.status_code != 200:
            errors.append(f"Posts endpoint returned {r.status_code}")
    except Exception as e:
        results["posts"] = {"status": 0, "bytes": 0, "count": 0, "ok": False, "error": str(e)}
        errors.append(f"Posts endpoint failed: {e}")

    # Test 3: Adaptive pocket plan (quick sanity check)
    try:
        payload = {
            "loops": [{"pts": [[0, 0], [50, 0], [50, 30], [0, 30]]}],
            "units": "mm",
            "tool_d": 6.0,
            "stepover": 0.45,
            "stepdown": 1.5,
            "margin": 0.5,
            "strategy": "Spiral",
            "smoothing": 0.8,
            "climb": True,
            "feed_xy": 1200,
            "safe_z": 5,
            "z_rough": -1.5,
        }
        r = requests.post(
            f"{api_base}/api/cam/pocket/adaptive/plan",
            json=payload,
            timeout=30,
        )
        results["adaptive_plan"] = {
            "status": r.status_code,
            "bytes": len(r.content),
            "ok": r.status_code == 200,
        }
        if r.status_code != 200:
            errors.append(f"Adaptive plan returned {r.status_code}")
    except Exception as e:
        results["adaptive_plan"] = {"status": 0, "bytes": 0, "ok": False, "error": str(e)}
        errors.append(f"Adaptive plan failed: {e}")

    # Overall result
    all_ok = all(v.get("ok", False) for v in results.values())

    output = {
        "ok": all_ok,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "api_base": api_base,
        "results": results,
        "errors": errors if errors else None,
    }

    # Write output
    with open("smoke_posts.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"smoke_posts.json: {'OK' if all_ok else 'FAILED'}")
    if errors:
        for e in errors:
            print(f"  - {e}")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
