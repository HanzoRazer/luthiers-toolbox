#!/usr/bin/env python3
"""
Run helical post-processor smoke tests and save results to JSON.

This script tests all 4 helical post-processor presets (GRBL, Mach3, Haas, Marlin)
against a running API server and saves the results to reports/helical_smoke_posts.json
for badge generation.

Usage:
    python tools/run_helical_smoke.py [--api-base http://localhost:8000]
"""

import json
import sys
import urllib.request
import pathlib
import argparse

def run_smoke_tests(api_base="http://127.0.0.1:8000"):
    """Run smoke tests for all presets and return results."""
    presets = ["GRBL", "Mach3", "Haas", "Marlin"]
    results = {}
    all_passed = True
    
    print("=== Helical Post-Processor Smoke Test ===\n")
    
    for preset in presets:
        print(f"[Testing] {preset}...", end=" ", flush=True)
        
        payload = {
            "cx": 0,
            "cy": 0,
            "radius_mm": 6.0,
            "direction": "CCW",
            "plane_z_mm": 5.0,
            "start_z_mm": 0.0,
            "z_target_mm": -3.0,
            "pitch_mm_per_rev": 1.5,
            "feed_xy_mm_min": 600,
            "ij_mode": True,
            "absolute": True,
            "units_mm": True,
            "safe_rapid": True,
            "dwell_ms": 0,
            "max_arc_degrees": 180,
            "post_preset": preset
        }
        
        req = urllib.request.Request(
            f"{api_base}/api/cam/toolpath/helical_entry",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode("utf-8"))
            
            gcode = data.get("gcode", "")
            stats = data.get("stats", {})
            
            if not gcode.strip():
                print(f"[FAIL] empty gcode")
                all_passed = False
                continue
            
            segments = stats.get("segments", 0)
            arc_mode = stats.get("arc_mode", "?")
            bytes_count = len(gcode)
            
            results[preset] = {
                "bytes": bytes_count,
                "segments": segments,
                "arc_mode": arc_mode
            }
            
            print(f"[OK] {bytes_count}b, {segments} segs, {arc_mode} mode")
            
        except Exception as e:
            print(f"[ERR] {e}")
            all_passed = False
    
    return results, all_passed

def main():
    parser = argparse.ArgumentParser(description="Run helical smoke tests")
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="API base URL (default: http://127.0.0.1:8000)"
    )
    args = parser.parse_args()
    
    # Run tests
    results, all_passed = run_smoke_tests(args.api_base)
    
    # Save results
    reports_dir = pathlib.Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    results_path = reports_dir / "helical_smoke_posts.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Saved results to {results_path}")
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 2)

if __name__ == "__main__":
    main()
