"""Find near-duplicate species (same wood, different naming convention)."""
import json

d = json.load(open(r'services/api/app/data_registry/system/materials/wood_species.json', 'r', encoding='utf-8'))
sp = d['species']

# Build word-set index for fuzzy matching
from collections import defaultdict

word_sets = {}
for sid, entry in sp.items():
    words = set(sid.replace("_", " ").split())
    word_sets[sid] = words

# Find pairs where word sets overlap significantly
potential_dupes = []
keys = list(sp.keys())
for i, k1 in enumerate(keys):
    for k2 in keys[i+1:]:
        w1, w2 = word_sets[k1], word_sets[k2]
        if w1 == w2 or (len(w1 & w2) >= 1 and len(w1 | w2) <= 3):
            # Check if they share key words
            shared = w1 & w2
            if any(w in shared for w in ["maple", "ash", "oak", "beech", "cherry", 
                   "birch", "cedar", "cypress", "elm", "walnut", "spruce", "pine",
                   "ebony", "rosewood", "mahogany", "poplar", "hemlock", "fir",
                   "larch", "palm", "chestnut", "locust", "hickory"]):
                t1 = sp[k1].get("guitar_relevance", "?")
                t2 = sp[k2].get("guitar_relevance", "?")
                d1 = sp[k1]["physical"]["density_kg_m3"]
                d2 = sp[k2]["physical"]["density_kg_m3"]
                print(f"  {k1} ({t1}, {d1} kg/m³) <-> {k2} ({t2}, {d2} kg/m³)")

print(f"\nTotal species: {len(sp)}")
