"""
Bulk-import all remaining CSV dump species into canonical wood_species.json.

Adds a `guitar_relevance` tier to every species:
  - "primary"      Traditional tonewoods (mahogany, spruce, rosewood, ebony, etc.)
  - "established"  Well-known guitar woods (sapele, wenge, jatoba, etc.)
  - "emerging"     Woods gaining popularity as sustainable/affordable alternatives
  - "exploratory"  Valid CNC-machinable hardwoods/softwoods not yet common in guitars

Existing 49 species are classified into primary/established.
New species get emerging or exploratory based on known guitar usage.

Run: python scripts/bulk_import_wood_species.py
"""

import csv
import json
import math
from pathlib import Path

ROOT = Path(r"c:\Users\thepr\Downloads\luthiers-toolbox")
CANONICAL = ROOT / "services" / "api" / "app" / "data_registry" / "system" / "materials" / "wood_species.json"
CSV_DUMP = Path(r"c:\Users\thepr\Downloads\dump.csv")
CIRAD_CSV = ROOT / "cirad-wood-collection-master" / "cirad-wood-collection-master" / "data" / "Cirad wood collection index.csv"

###############################################################################
# Classification tiers
###############################################################################
PRIMARY_TONEWOODS = {
    "mahogany_honduran", "mahogany_african", "maple_hard", "maple_soft",
    "rosewood_east_indian", "rosewood_brazilian", "ebony_african", "ebony_macassar",
    "alder", "ash_swamp", "basswood", "spruce_sitka", "spruce_engelmann",
    "spruce_adirondack", "spruce_european", "cedar_western_red", "walnut_black",
    "koa", "cocobolo",
}

ESTABLISHED_GUITAR = {
    "ash_white", "beech_american", "birch_yellow", "cherry_black", "cypress_bald",
    "douglas_fir", "ipe", "jatoba", "oak_red", "oak_white", "pine_eastern_white",
    "poplar_yellow", "purpleheart", "redwood", "sapele", "tasmanian_blackwood",
    "wenge", "zebrawood", "bubinga", "iroko", "teak", "merbau", "ovangkol",
    "pau_ferro", "bocote", "katalox", "ziricote", "granadillo",
    "cedar_spanish", "spruce_white", "padauk_african",
}

# Species from CSV that ARE used in guitars — get "emerging" tier
EMERGING_GUITAR_NAMES = {
    "african-blackwood", "african-padauk", "bloodwood", "brazilian-rosewood",
    "black-locust", "black-palm", "camphor", "canarywood", "chechen",
    "cumaru", "curupay", "east-indian-rosewood", "gaboon-ebony",
    "goncalo-alves", "greenheart", "honduran-mahogany", "imbuia",
    "jarrah", "lacewood", "leadwood", "lignum-vitae", "macassar-ebony",
    "madagascar-rosewood", "makore", "mango", "marblewood", "mora",
    "mulberry", "muninga", "narra", "olive", "osage-orange",
    "pacific-yew", "panga-panga", "partridgewood", "pau-ferro",
    "pau-santo", "peroba-rosa", "pink-ivory", "redheart",
    "santos-mahogany", "sassafras", "siamese-rosewood", "snakewood",
    "sucupira", "tatajuba", "texas-ebony", "yellowheart",
    "yucatan-rosewood", "australian-blackwood", "black-cherry",
    "english-walnut", "european-beech", "european-yew", "hard-maple",
    "mopane", "queensland-maple", "rubberwood", "tiete-rosewood",
    "western-red-cedar", "white-ash", "white-oak", "red-oak",
    "yellow-poplar", "american-beech", "american-chestnut",
    "bald-cypress", "sitka-spruce", "engelmann-spruce",
    "norway-spruce", "european-ash", "lyptus",
    "spanish-cedar", "australian-cypress", "huon-pine",
    "monterey-cypress", "new-zealand-kauri",
}

# Hardwood/softwood classification by family keywords
SOFTWOOD_FAMILIES = {
    "pine", "spruce", "fir", "cedar", "cypress", "hemlock", "larch",
    "redwood", "yew", "kauri", "juniper", "araucaria",
}

###############################################################################
# Load data
###############################################################################
with open(CANONICAL, encoding="utf-8") as f:
    canonical = json.load(f)
species = canonical["species"]
print(f"Existing species: {len(species)}")

with open(CSV_DUMP, encoding="utf-8-sig") as f:
    csv_rows = list(csv.DictReader(f))
print(f"CSV rows: {len(csv_rows)}")

# Load CIRAD for SG cross-reference
cirad_genus_sg = {}
if CIRAD_CSV.exists():
    with open(CIRAD_CSV, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # skip header
        for row in reader:
            if len(row) >= 4 and row[3].strip():
                try:
                    sg = float(row[3].strip())
                    genus = row[2].strip().split()[0]
                    cirad_genus_sg.setdefault(genus, []).append(sg)
                except (ValueError, IndexError):
                    pass
    cirad_avg = {g: sum(v)/len(v) for g, v in cirad_genus_sg.items() if v}
    print(f"CIRAD genera: {len(cirad_avg)}")
else:
    cirad_avg = {}

###############################################################################
# Step 1: Add guitar_relevance to existing species
###############################################################################
for sid, sp in species.items():
    if sid in PRIMARY_TONEWOODS:
        sp["guitar_relevance"] = "primary"
    elif sid in ESTABLISHED_GUITAR:
        sp["guitar_relevance"] = "established"
    else:
        sp["guitar_relevance"] = "established"  # all existing 49 are at least established

print(f"Tagged {len(species)} existing species with guitar_relevance")

###############################################################################
# Helpers
###############################################################################
def estimate_sg_from_density(density_kgm3):
    """Approximate SG from air-dry density."""
    return round(density_kgm3 / 1000, 2)

def estimate_thermal_k(sg):
    return round(0.04 + 0.35 * sg, 2)

def estimate_sce(sg):
    return round(0.15 + 0.65 * sg, 2)

def estimate_specific_heat(sg):
    return round(2000 - 600 * sg)

def hardness_scale(janka_lbf):
    return round(min(1.0, janka_lbf / 3500), 2)

def janka_from_density(density_kgm3):
    """Estimate Janka from density using regression: Janka ≈ 0.00355 * density^1.85"""
    return round(0.00355 * (density_kgm3 ** 1.85))

def is_softwood(name):
    name_l = name.lower()
    for kw in SOFTWOOD_FAMILIES:
        if kw in name_l:
            return True
    return False

def name_to_id(name):
    """Convert CSV name like 'african-blackwood' to 'african_blackwood'."""
    return name.strip().lower().replace("-", "_").replace(" ", "_").replace("(", "").replace(")", "")

def name_to_display(name):
    """Convert CSV name to display name."""
    return name.strip().replace("-", " ").title()

def lb_ft3_to_kg_m3(lb_ft3):
    """Convert lb/ft³ to kg/m³."""
    return round(lb_ft3 * 16.0185)

###############################################################################
# Scientific name lookup from CSV URL (wood-database.com slug match)
###############################################################################
# We'll include scientific names where possible, leave blank otherwise.
# The CSV has URLs we could scrape, but we'll use a curated mapping for 
# known guitar-relevant species and leave others with family-level info.

KNOWN_SCIENTIFIC = {
    "african-blackwood": "Dalbergia melanoxylon",
    "african-padauk": "Pterocarpus soyauxii",
    "african-walnut": "Lovoa trichilioides",
    "alaskan-yellow-cedar": "Cupressus nootkatensis",
    "american-chestnut": "Castanea dentata",
    "american-elm": "Ulmus americana",
    "apple": "Malus domestica",
    "atlantic-white-cedar": "Chamaecyparis thyoides",
    "australian-buloke": "Allocasuarina luehmannii",
    "australian-cypress": "Callitris spp.",
    "avocado": "Persea americana",
    "balsa": "Ochroma pyramidale",
    "bamboo": "Bambusoideae spp.",
    "bigleaf-maple": "Acer macrophyllum",
    "black-ash": "Fraxinus nigra",
    "black-cottonwood": "Populus trichocarpa",
    "black-locust": "Robinia pseudoacacia",
    "black-mesquite": "Prosopis nigra",
    "black-oak": "Quercus velutina",
    "black-palm": "Borassus flabellifer",
    "black-spruce": "Picea mariana",
    "bloodwood": "Brosimum rubescens",
    "blue-gum": "Eucalyptus globulus",
    "boxwood": "Buxus sempervirens",
    "brazilwood": "Paubrasilia echinata",
    "butternut": "Juglans cinerea",
    "california-red-fir": "Abies magnifica",
    "camphor": "Cinnamomum camphora",
    "canarywood": "Centrolobium spp.",
    "catalpa": "Catalpa speciosa",
    "cerejeira": "Amburana cearensis",
    "chechen": "Metopium brownei",
    "cumaru": "Dipteryx odorata",
    "curupay": "Anadenanthera colubrina",
    "dogwood": "Cornus florida",
    "eastern-hemlock": "Tsuga canadensis",
    "eastern-red-cedar": "Juniperus virginiana",
    "english-elm": "Ulmus minor",
    "english-oak": "Quercus robur",
    "english-walnut": "Juglans regia",
    "european-ash": "Fraxinus excelsior",
    "european-beech": "Fagus sylvatica",
    "european-larch": "Larix decidua",
    "european-yew": "Taxus baccata",
    "gaboon-ebony": "Diospyros crassiflora",
    "garapa": "Apuleia leiocarpa",
    "goncalo-alves": "Astronium graveolens",
    "greenheart": "Chlorocardium rodiei",
    "hackberry": "Celtis occidentalis",
    "holly": "Ilex opaca",
    "honey-locust": "Gleditsia triacanthos",
    "huon-pine": "Lagarostrobos franklinii",
    "imbuia": "Ocotea porosa",
    "incense-cedar": "Calocedrus decurrens",
    "jack-pine": "Pinus banksiana",
    "jarrah": "Eucalyptus marginata",
    "jelutong": "Dyera costulata",
    "karri": "Eucalyptus diversicolor",
    "kempas": "Koompassia malaccensis",
    "lacewood": "Panopsis spp.",
    "leadwood": "Combretum imberbe",
    "lignum-vitae": "Guaiacum officinale",
    "limba": "Terminalia superba",
    "live-oak": "Quercus virginiana",
    "loblolly-pine": "Pinus taeda",
    "lodgepole-pine": "Pinus contorta",
    "london-plane": "Platanus × acerifolia",
    "longleaf-pine": "Pinus palustris",
    "lyptus": "Eucalyptus grandis × urophylla",
    "madagascar-rosewood": "Dalbergia baronii",
    "madrone": "Arbutus menziesii",
    "makore": "Tieghmella heckelii",
    "mango": "Mangifera indica",
    "marblewood": "Marmaroxylon racemosum",
    "monterey-cypress": "Hesperocyparis macrocarpa",
    "mopane": "Colophospermum mopane",
    "mora": "Mora excelsa",
    "mountain-ash": "Eucalyptus regnans",
    "mulberry": "Morus spp.",
    "muninga": "Pterocarpus angolensis",
    "narra": "Pterocarpus dalbergioides",
    "new-zealand-kauri": "Agathis australis",
    "norway-spruce": "Picea abies",
    "obeche": "Triplochiton scleroxylon",
    "olive": "Olea europaea",
    "osage-orange": "Maclura pomifera",
    "pacific-yew": "Taxus brevifolia",
    "panga-panga": "Millettia stuhlmannii",
    "partridgewood": "Caesalpinia granadillo",
    "paulownia": "Paulownia tomentosa",
    "pear": "Pyrus communis",
    "pecan": "Carya illinoinensis",
    "peroba-rosa": "Aspidosperma polyneuron",
    "persimmon": "Diospyros virginiana",
    "peruvian-walnut": "Juglans neotropica",
    "pink-ivory": "Berchemia zeyheri",
    "plum": "Prunus domestica",
    "ponderosa-pine": "Pinus ponderosa",
    "port-orford-cedar": "Chamaecyparis lawsoniana",
    "radiata-pine": "Pinus radiata",
    "red-elm": "Ulmus rubra",
    "red-palm": "Cyrtostachys renda",
    "red-pine": "Pinus resinosa",
    "redheart": "Erythroxylum spp.",
    "rubberwood": "Hevea brasiliensis",
    "santos-mahogany": "Myroxylon balsamum",
    "sassafras": "Sassafras albidum",
    "scots-pine": "Pinus sylvestris",
    "siamese-rosewood": "Dalbergia cochinchinensis",
    "silver-birch": "Betula pendula",
    "silver-maple": "Acer saccharinum",
    "snakewood": "Brosimum guianense",
    "sucupira": "Bowdichia nitida",
    "sugar-pine": "Pinus lambertiana",
    "sugi": "Cryptomeria japonica",
    "sweet-birch": "Betula lenta",
    "sweet-cherry": "Prunus avium",
    "sweet-chestnut": "Castanea sativa",
    "sweetgum": "Liquidambar styraciflua",
    "sycamore": "Platanus occidentalis",
    "tamarack": "Larix laricina",
    "tamarind": "Tamarindus indica",
    "tatajuba": "Bagassa guianensis",
    "texas-ebony": "Ebenopsis ebano",
    "tiete-rosewood": "Goniorrhachis marginata",
    "timborana": "Pseudopiptadenia suaveolens",
    "utile": "Entandrophragma utile",
    "western-hemlock": "Tsuga heterophylla",
    "western-larch": "Larix occidentalis",
    "western-white-pine": "Pinus monticola",
    "white-fir": "Abies concolor",
    "white-poplar": "Populus alba",
    "yellowheart": "Euxylophora paraensis",
}

###############################################################################
# Step 2: Build index of existing species (by id and by scientific genus)
###############################################################################
existing_ids = set(species.keys())
existing_genera = set()
for sp in species.values():
    sci = sp.get("scientific_name", "")
    if sci:
        existing_genera.add(sci.split()[0].lower())

# Also build a set of existing common name fragments for dedup
existing_names = set()
for sp in species.values():
    existing_names.add(sp["name"].lower())
    existing_names.add(sp["id"])

###############################################################################
# Step 3: Process all CSV rows and add missing species
###############################################################################
added = 0
skipped_existing = 0
skipped_dupe = 0

for row in csv_rows:
    csv_name = row["name"].strip()
    sid = name_to_id(csv_name)
    
    # Skip if already exists by ID
    if sid in species:
        skipped_existing += 1
        continue
    
    # Skip exact duplicates of existing species (different CSV name, same wood)
    display = name_to_display(csv_name)
    
    # Check if this is a duplicate of an existing species
    skip = False
    for existing_id, existing_sp in species.items():
        existing_sci = existing_sp.get("scientific_name", "").lower()
        new_sci = KNOWN_SCIENTIFIC.get(csv_name, "").lower()
        if new_sci and existing_sci and new_sci.split()[0] == existing_sci.split()[0]:
            # Same genus — might be duplicate
            if new_sci == existing_sci:
                skip = True
                break
    if skip:
        skipped_dupe += 1
        continue

    # Parse CSV data
    try:
        mor = float(row["MOR (MPa)"].strip())
    except (ValueError, KeyError):
        mor = None
    try:
        moe = float(row["E (GPa)"].strip())
    except (ValueError, KeyError):
        moe = None
    try:
        density = float(row["r Kg/m^3"].strip())
    except (ValueError, KeyError):
        density = None

    if density is None:
        continue  # Can't do much without density

    density_int = round(density)
    sg = estimate_sg_from_density(density_int)
    
    # Estimate Janka from density
    janka = janka_from_density(density_int)
    janka_n = round(janka * 4.44822)

    # Determine category
    category = "softwood" if is_softwood(csv_name) else "hardwood"

    # Determine guitar_relevance
    if csv_name in EMERGING_GUITAR_NAMES:
        relevance = "emerging"
    else:
        relevance = "exploratory"

    # Get scientific name if known
    sci_name = KNOWN_SCIENTIFIC.get(csv_name, "")

    # Cross-ref CIRAD for SG if we have scientific name
    if sci_name:
        genus = sci_name.split()[0]
        if genus in cirad_avg:
            cirad_sg = cirad_avg[genus]
            # Use CIRAD SG if significantly different and seems more reliable
            if abs(sg - cirad_sg) > 0.1:
                # Note the discrepancy but keep density-derived SG
                pass  # We trust the CSV density

    # Thermal estimates
    k = estimate_thermal_k(sg)
    sce = estimate_sce(sg)
    sh = estimate_specific_heat(sg)
    hs = hardness_scale(janka)

    # Build machining estimates from hardness
    chipload = round(max(0.5, 1.3 - 0.8 * hs), 2)
    rough_feed = round(max(1200, 6000 - 5000 * hs))
    finish_feed = round(max(700, 3500 - 3000 * hs))
    plunge_feed = round(max(250, 2000 - 1800 * hs))
    min_rpm = round(max(10000, 10000 + 8000 * hs))
    max_doc = round(max(2, 18 - 16 * hs))

    burn = round(min(0.8, 0.1 + 0.5 * hs), 2)
    tearout = round(min(0.8, 0.2 + 0.3 * hs), 2)

    entry = {
        "id": sid,
        "name": display,
        "scientific_name": sci_name,
        "category": category,
        "guitar_relevance": relevance,
        "physical": {
            "specific_gravity": sg,
            "density_kg_m3": density_int,
            "janka_hardness_lbf": janka,
            "janka_hardness_n": janka_n,
            "grain": "",
            "workability": "",
            "resinous": category == "softwood",
        },
        "thermal": {
            "thermal_conductivity_w_per_mk": k,
            "specific_heat_capacity_j_per_kgk": sh,
            "specific_cutting_energy_j_per_mm3": sce,
            "heat_partition": {
                "chip": round(0.75 - 0.15 * sg, 2),
                "tool": round(0.15 + 0.1 * sg, 2),
                "work": round(0.10 + 0.05 * sg, 2),
            },
            "_note": "All thermal values estimated from density/SG"
        },
        "machining": {
            "hardness_scale": hs,
            "burn_tendency": burn,
            "tearout_tendency": tearout,
            "chipload_multiplier": chipload,
            "feed_clamp": {
                "roughing_max_mm_min": rough_feed,
                "finishing_max_mm_min": finish_feed,
                "plunge_max_mm_min": plunge_feed,
            },
            "speed_clamp": {
                "min_rpm": min_rpm,
                "max_rpm": 24000,
                "optimal_sfm": round(max(350, 1200 - 900 * hs)),
            },
            "doc_limits": {
                "max_doc_mm": max_doc,
                "optimal_doc_ratio": round(max(0.15, 0.7 - 0.55 * hs), 2),
            },
            "woc_limits": {
                "max_woc_ratio": round(max(0.2, 0.7 - 0.5 * hs), 2),
                "finishing_woc_ratio": round(max(0.04, 0.2 - 0.16 * hs), 2),
            },
            "warnings": {
                "burn_risk": "low" if burn < 0.3 else ("high" if burn > 0.5 else "medium"),
                "tearout_risk": "low" if tearout < 0.3 else ("high" if tearout > 0.5 else "medium"),
                "dust_hazard": "high" if sg > 0.8 else ("medium" if sg > 0.6 else "low"),
            }
        },
        "lutherie": {
            "typical_uses": [],
            "tone_character": "",
            "sustainability": "",
        },
    }

    # Add structural data if available
    if mor is not None:
        entry["physical"]["modulus_of_rupture_mpa"] = round(mor, 1)
    if moe is not None:
        entry["physical"]["modulus_of_elasticity_gpa"] = round(moe, 2)

    # Source reference
    url = row.get("url", "").strip()
    if url:
        entry["_source_url"] = url

    species[sid] = entry
    added += 1

print(f"Added: {added}")
print(f"Skipped (already existed): {skipped_existing}")
print(f"Skipped (genus duplicate): {skipped_dupe}")
print(f"Total species: {len(species)}")

###############################################################################
# Step 4: Sort species — primary first, then established, emerging, exploratory
###############################################################################
tier_order = {"primary": 0, "established": 1, "emerging": 2, "exploratory": 3}

sorted_species = dict(
    sorted(
        species.items(),
        key=lambda item: (
            tier_order.get(item[1].get("guitar_relevance", "exploratory"), 3),
            item[0],  # alphabetical within tier
        ),
    )
)
canonical["species"] = sorted_species

###############################################################################
# Step 5: Update meta
###############################################################################
canonical["_meta"]["version"] = "4.0.0"
canonical["_meta"]["description"] = (
    "Canonical wood species reference — physical, thermal, machining, and lutherie properties. "
    "Single source of truth. Species are classified by guitar_relevance: "
    "primary (traditional tonewoods), established (well-known guitar woods), "
    "emerging (gaining popularity), exploratory (valid woods, not yet common in guitars)."
)

###############################################################################
# Step 6: Write
###############################################################################
with open(CANONICAL, "w", encoding="utf-8") as f:
    json.dump(canonical, f, indent=2, ensure_ascii=False)

print(f"\nWrote {CANONICAL}")

# Summary by tier
tier_counts = {}
for sp in sorted_species.values():
    t = sp.get("guitar_relevance", "exploratory")
    tier_counts[t] = tier_counts.get(t, 0) + 1

print("\nSpecies by guitar_relevance tier:")
for t in ["primary", "established", "emerging", "exploratory"]:
    print(f"  {t}: {tier_counts.get(t, 0)}")

has_mor = sum(1 for v in sorted_species.values() if "modulus_of_rupture_mpa" in v.get("physical", {}))
has_sci = sum(1 for v in sorted_species.values() if v.get("scientific_name", ""))
print(f"\nWith structural data (MOR): {has_mor}")
print(f"With scientific name: {has_sci}")
