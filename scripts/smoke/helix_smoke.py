#!/usr/bin/env python3
"""Helix post-processor smoke test."""
import json
import sys
import urllib.request

API_BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
presets = ["GRBL", "Mach3", "Haas", "Marlin"]
ok = True

for p in presets:
    payload = {
        "cx": 0, "cy": 0, "radius_mm": 6.0, "direction": "CCW",
        "plane_z_mm": 5.0, "start_z_mm": 0.0, "z_target_mm": -3.0,
        "pitch_mm_per_rev": 1.5, "feed_xy_mm_min": 600,
        "ij_mode": True, "absolute": True, "units_mm": True, "safe_rapid": True,
        "dwell_ms": 0, "max_arc_degrees": 180,
        "post_preset": p
    }
    req = urllib.request.Request(
        API_BASE + "/api/cam/toolpath/helical_entry",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        gcode = data.get("gcode", "")
        stats = data.get("stats", {})
        if not gcode.strip():
            print(f"[FAIL] {p}: empty gcode")
            ok = False
        else:
            segments = stats.get("segments", 0)
            arc_mode = stats.get("arc_mode", "?")
            print(f"[OK]   {p}: {len(gcode)} bytes; segments={segments}, arc_mode={arc_mode}")

            # Validate preset-specific features
            if p == "Haas":
                if " R" not in gcode:
                    print(f"[WARN] {p}: Expected R-mode arcs")
            elif " I" not in gcode and " J" not in gcode:
                print(f"[WARN] {p}: Expected I,J arcs")

    except Exception as e:
        print(f"[ERR]  {p}: {e}")
        ok = False

sys.exit(0 if ok else 2)
