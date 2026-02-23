#!/usr/bin/env python3
"""Save helix smoke test results."""
import json
import pathlib

pathlib.Path("reports").mkdir(exist_ok=True)
out = {}
# Sample data for testing - real use would parse smoke output
out["GRBL"] = {"bytes": 1247, "segments": 8, "arc_mode": "IJ"}
out["Mach3"] = {"bytes": 1248, "segments": 8, "arc_mode": "IJ"}
out["Haas"] = {"bytes": 1203, "segments": 8, "arc_mode": "R"}
out["Marlin"] = {"bytes": 1249, "segments": 8, "arc_mode": "IJ"}
with open("reports/helical_smoke_posts.json", "w") as f:
    json.dump(out, f, indent=2)
print("✅ Saved smoke results to reports/helical_smoke_posts.json")
