"""Explore rosette design options available in the API."""
import requests
import json

BASE = "http://127.0.0.1:8000"

# 1. Recipes
r = requests.get(f"{BASE}/api/art/rosette-designer/recipes")
print("=== AVAILABLE RECIPE PRESETS ===")
if r.status_code == 200:
    data = r.json()
    recipes = data.get("recipes", data)
    if isinstance(recipes, list):
        for rec in recipes:
            rid = rec.get("id", "?")
            name = rec.get("name", "?")
            segs = rec.get("num_segs", "?")
            sym = rec.get("sym_mode", "?")
            grid = rec.get("grid", {})
            print(f"  [{rid}] {name}  segs={segs} sym={sym} tiles={len(grid)}")
    else:
        print(json.dumps(recipes, indent=2)[:600])
else:
    print(f"Status {r.status_code}: {r.text[:200]}")

# 2. Tile catalog
print("\n=== TILE CATALOG ===")
r2 = requests.get(f"{BASE}/api/art/rosette-designer/catalog")
if r2.status_code == 200:
    data = r2.json()
    for cat in data.get("categories", []):
        label = cat.get("label", "?")
        tiles = [t.get("id") for t in cat.get("tiles", [])]
        print(f"  {label}: {tiles}")
    rings = data.get("ring_defs", [])
    print(f"\n  Ring zones ({len(rings)}):")
    for ring in rings:
        print(f"    {ring['label']}: {ring['inch1']} - {ring['inch2']}")
    print(f"  Segment options: {data.get('seg_options', [])}")
else:
    print(f"Status {r2.status_code}")
