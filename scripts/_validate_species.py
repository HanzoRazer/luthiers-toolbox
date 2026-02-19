import json
d = json.load(open(r'services/api/app/data_registry/system/materials/wood_species.json', 'r', encoding='utf-8'))
sp = d['species']
keys = list(sp.keys())
print(f'Valid JSON: True')
print(f'Total species: {len(sp)}')
print(f'Version: {d["_meta"]["version"]}')
print()

# Show tier ordering
tiers = {}
for k in keys:
    t = sp[k].get("guitar_relevance", "?")
    tiers.setdefault(t, []).append(k)

for t in ["primary", "established", "emerging", "exploratory"]:
    items = tiers.get(t, [])
    print(f"\n=== {t.upper()} ({len(items)}) ===")
    for k in items[:8]:
        print(f"  {k}: {sp[k]['name']}")
    if len(items) > 8:
        print(f"  ... and {len(items)-8} more")

# Check required fields
missing = []
for k, v in sp.items():
    for field in ["id", "name", "category", "guitar_relevance", "physical", "thermal", "machining", "lutherie"]:
        if field not in v:
            missing.append(f"{k} missing {field}")
print(f"\nMissing required fields: {len(missing)}")
if missing[:5]:
    for m in missing[:5]:
        print(f"  {m}")
