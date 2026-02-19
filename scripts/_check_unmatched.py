"""One-off script to count CSV dump species not in canonical file."""
import csv, json

d = json.load(open(r"c:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\data_registry\system\materials\wood_species.json"))
canonical_keys = set()
for v in d["species"].values():
    canonical_keys.add(v["name"].lower())
    genus = v.get("scientific_name", "").split()[0].lower()
    if genus:
        canonical_keys.add(genus)
    canonical_keys.add(v["id"].replace("_", " "))

with open(r"c:\Users\thepr\Downloads\dump.csv", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

print(f"CSV dump total: {len(rows)}")
print(f"Canonical species: {len(d['species'])}")

unmatched = []
matched = []
for r in rows:
    name = r["name"].strip().lower()
    found = False
    for ck in canonical_keys:
        if ck in name or name in ck:
            found = True
            break
    if found:
        matched.append(r["name"].strip())
    else:
        unmatched.append(r["name"].strip())

print(f"Matched to canonical: {len(matched)}")
print(f"NOT in canonical: {len(unmatched)}")
print()
print("--- Unmatched species ---")
for u in sorted(unmatched):
    print(f"  {u}")
