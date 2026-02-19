"""
Remove true duplicate species where CSV name is the reverse of existing canonical name.
Keep the original (richer data), remove the CSV import.
Also add aliases/cross-references.
"""
import json

CANONICAL = r'services/api/app/data_registry/system/materials/wood_species.json'

with open(CANONICAL, encoding='utf-8') as f:
    d = json.load(f)

sp = d['species']

# True duplicates: imported_id -> existing_id (same exact wood species)
DUPES_TO_REMOVE = {
    # Same species, reversed naming convention
    "brazilian_rosewood": "rosewood_brazilian",
    "east_indian_rosewood": "rosewood_east_indian",
    "engelmann_spruce": "spruce_engelmann",
    "sitka_spruce": "spruce_sitka",
    "norway_spruce": "spruce_european",       # Norway spruce = P. abies = European spruce
    "black_walnut": "walnut_black",
    "white_ash": "ash_white",
    "american_beech": "beech_american",
    "black_cherry": "cherry_black",
    "spanish_cedar": "cedar_spanish",
    "bald_cypress": "cypress_bald",
    "red_oak": "oak_red",
    "white_oak": "oak_white",
    "yellow_birch": "birch_yellow",
    "white_spruce": "spruce_white",
    "red_spruce": "spruce_adirondack",        # Red spruce = Adirondack spruce
    "hard_maple": "maple_hard",
    "yellow_poplar": "poplar_yellow",
    "african_padauk": "padauk_african",       # If padauk_african exists
    "european_beech": "beech_american",       # Different species but "beech_american" covers US guitar usage
    # Note: european_beech IS a distinct species (Fagus sylvatica vs F. grandifolia)
    # but beech_american is already established. Keep european_beech as distinct.
    "gaboon_ebony": "ebony_african",          # Gaboon ebony = African ebony (D. crassiflora)
    "macassar_ebony": "ebony_macassar",       # Already exists
    "honduran_mahogany": "mahogany_honduran",
    "african_mahogany": "mahogany_african",
    "western_red_cedar": "cedar_western_red",
}

# Remove european_beech from dupes - it IS a distinct species
# Keep it as emerging
del DUPES_TO_REMOVE["european_beech"]

# Also check if the "existing" ID actually exists
removed = 0
kept = []
for dupe_id, existing_id in DUPES_TO_REMOVE.items():
    if dupe_id in sp and existing_id in sp:
        # Add alias to existing
        existing = sp[existing_id]
        aliases = existing.get("aliases", [])
        dupe_name = sp[dupe_id]["name"]
        if dupe_name not in aliases:
            aliases.append(dupe_name)
        existing["aliases"] = aliases
        
        # Remove duplicate
        del sp[dupe_id]
        removed += 1
        print(f"  Removed {dupe_id} -> alias of {existing_id}")
    elif dupe_id in sp:
        kept.append(dupe_id)
        print(f"  Kept {dupe_id} (target {existing_id} not found)")
    else:
        print(f"  {dupe_id} already absent")

# Also handle macassar_ebony if it was imported as a duplicate
if "macassar_ebony" in sp and "ebony_macassar" in sp and "macassar_ebony" != "ebony_macassar":
    # Already handled above
    pass

print(f"\nRemoved: {removed}")
print(f"Remaining species: {len(sp)}")

# Recount tiers
tiers = {}
for v in sp.values():
    t = v.get("guitar_relevance", "exploratory")
    tiers[t] = tiers.get(t, 0) + 1

print("\nTier counts:")
for t in ["primary", "established", "emerging", "exploratory"]:
    print(f"  {t}: {tiers.get(t, 0)}")

# Write back
with open(CANONICAL, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print(f"\nWrote updated {CANONICAL}")
