"""
Merge wood species data from CSV dump + CIRAD collection into canonical wood_species.json.

This script:
1. Cross-references existing species with CSV dump (MOR, MOE, density)
2. Cross-references with CIRAD collection (specific gravity)
3. Updates existing species missing structural data
4. Adds guitar-relevant new species from both sources
5. Writes the updated file

Run: python scripts/merge_wood_data.py
"""

import csv
import json
import math
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "services" / "api" / "app" / "data_registry" / "system" / "materials" / "wood_species.json"
CSV_DUMP = ROOT.parent / "dump.csv"  # May also be at ROOT / parent level
CIRAD_CSV = ROOT / "cirad-wood-collection-master" / "cirad-wood-collection-master" / "data" / "Cirad wood collection index.csv"

# Try alternate CSV locations
if not CSV_DUMP.exists():
    CSV_DUMP = Path(r"c:\Users\thepr\Downloads\dump.csv")

###############################################################################
# 1. Load existing canonical data
###############################################################################
with open(CANONICAL, encoding="utf-8") as f:
    canonical = json.load(f)

species = canonical["species"]
print(f"Existing species: {len(species)}")

###############################################################################
# 2. Load CSV dump (465 rows: name, MOR, E, density, url, note)
###############################################################################
csv_rows = []
with open(CSV_DUMP, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    csv_rows = list(reader)
print(f"CSV dump rows: {len(csv_rows)}")

# Build lookup by lowercase name
csv_lookup = {}
for r in csv_rows:
    name = r["name"].strip().lower()
    csv_lookup[name] = r

###############################################################################
# 3. Load CIRAD (34395 rows: semicolon-delimited, Species + Specific gravity)
###############################################################################
cirad_rows = []
if CIRAD_CSV.exists():
    with open(CIRAD_CSV, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        for row in reader:
            if len(row) >= 4:
                cirad_rows.append({
                    "species": row[2].strip(),
                    "family": row[1].strip(),
                    "sg": row[3].strip(),
                })
    print(f"CIRAD rows: {len(cirad_rows)}")

    # Build genus-level SG averages from CIRAD
    cirad_genus_sg = {}
    for r in cirad_rows:
        sp = r["species"]
        sg_str = r["sg"]
        if not sg_str:
            continue
        try:
            sg = float(sg_str)
        except ValueError:
            continue
        genus = sp.split()[0] if sp else ""
        if genus:
            cirad_genus_sg.setdefault(genus, []).append(sg)

    cirad_genus_avg = {g: sum(vals)/len(vals) for g, vals in cirad_genus_sg.items() if vals}
    print(f"CIRAD genera with SG data: {len(cirad_genus_avg)}")
else:
    cirad_genus_avg = {}
    print("CIRAD file not found, skipping")

###############################################################################
# 4. CSV name mapping to existing species IDs
###############################################################################
CSV_TO_SPECIES = {
    # Direct matches in CSV dump
    "african mahogany": "mahogany_african",
    "african padauk": None,  # skip
    "alder": "alder",
    "american beech": "beech_american",
    "american cherry": "cherry_black",
    "american hard maple": "maple_hard",
    "american red oak": "oak_red",
    "american white oak": "oak_white",
    "american whitewood": None,
    "ash": "ash_white",
    "basswood": "basswood",
    "birch": "birch_yellow",
    "black walnut": "walnut_black",
    "blackwood": "tasmanian_blackwood",
    "bubinga": None,  # new species candidate
    "cedar": "cedar_western_red",
    "cypress": "cypress_bald",
    "douglas fir": "douglas_fir",
    "ebony": "ebony_african",
    "hard maple": "maple_hard",
    "honduran mahogany": "mahogany_honduran",
    "ipe": "ipe",
    "iroko": None,  # new
    "jarrah": None,
    "jatoba": "jatoba",
    "koa": "koa",
    "macassar ebony": "ebony_macassar",
    "merbau": None,
    "pine": "pine_eastern_white",
    "purpleheart": "purpleheart",
    "redwood": "redwood",
    "rosewood": "rosewood_east_indian",
    "sapele": "sapele",
    "sitka spruce": "spruce_sitka",
    "soft maple": "maple_soft",
    "swamp ash": "ash_swamp",
    "teak": None,  # new
    "tulipwood": "poplar_yellow",
    "wenge": "wenge",
    "western red cedar": "cedar_western_red",
    "yellow poplar": "poplar_yellow",
    "zebrawood": "zebrawood",
}

###############################################################################
# 5. Search CSV for matches to existing species
###############################################################################
def find_csv_match(species_id, sci_name, common_name):
    """Find best CSV row match for a species."""
    # Try exact name match
    for csv_name, sid in CSV_TO_SPECIES.items():
        if sid == species_id:
            if csv_name in csv_lookup:
                return csv_lookup[csv_name]

    # Try scientific name genus match
    genus = sci_name.split()[0].lower() if sci_name else ""
    for name, row in csv_lookup.items():
        if genus and genus in name:
            return row

    # Try common name substring
    common_lower = common_name.lower()
    for name, row in csv_lookup.items():
        if name in common_lower or common_lower in name:
            return row

    return None

###############################################################################
# 6. Update existing species with missing structural data
###############################################################################
updated_count = 0
notes = []

for sid, sp in species.items():
    phys = sp.get("physical", {})
    has_mor = "modulus_of_rupture_mpa" in phys
    has_moe = "modulus_of_elasticity_gpa" in phys

    csv_match = find_csv_match(sid, sp.get("scientific_name", ""), sp.get("name", ""))

    if csv_match:
        mor_str = csv_match.get("MOR (MPa)", "").strip()
        moe_str = csv_match.get("E (GPa)", "").strip()
        rho_str = csv_match.get("r Kg/m^3", "").strip()
        url = csv_match.get("url", "").strip()

        try:
            mor = float(mor_str) if mor_str else None
        except ValueError:
            mor = None
        try:
            moe = float(moe_str) if moe_str else None
        except ValueError:
            moe = None
        try:
            rho = float(rho_str) if rho_str else None
        except ValueError:
            rho = None

        changed = False

        # Add MOR/MOE if missing
        if not has_mor and mor is not None:
            phys["modulus_of_rupture_mpa"] = round(mor, 1)
            changed = True
        if not has_moe and moe is not None:
            phys["modulus_of_elasticity_gpa"] = round(moe, 2)
            changed = True

        # Cross-check density — flag if >15% discrepancy
        if rho is not None and "density_kg_m3" in phys:
            existing_rho = phys["density_kg_m3"]
            if abs(existing_rho - rho) / existing_rho > 0.15:
                notes.append(f"  {sid}: density discrepancy — existing {existing_rho}, CSV {rho} (keeping existing)")

        # Use CIRAD SG to cross-validate specific_gravity
        genus = sp.get("scientific_name", "").split()[0] if sp.get("scientific_name") else ""
        if genus in cirad_genus_avg and "specific_gravity" in phys:
            cirad_sg = cirad_genus_avg[genus]
            existing_sg = phys["specific_gravity"]
            if abs(existing_sg - cirad_sg) / existing_sg > 0.20:
                notes.append(f"  {sid}: SG discrepancy — existing {existing_sg}, CIRAD avg {cirad_sg:.2f} (keeping existing)")

        if changed:
            updated_count += 1
            print(f"  Updated {sid}: MOR={phys.get('modulus_of_rupture_mpa')}, MOE={phys.get('modulus_of_elasticity_gpa')}")

print(f"\nUpdated {updated_count} existing species with missing structural data")
if notes:
    print("Discrepancy notes:")
    for n in notes:
        print(n)

###############################################################################
# 7. Define new guitar-relevant species from CSV + CIRAD
###############################################################################
def estimate_thermal_k(sg):
    """Estimate thermal conductivity from specific gravity (linear approx from FPL data)."""
    return round(0.04 + 0.35 * sg, 2)

def estimate_sce(sg):
    """Estimate specific cutting energy from SG."""
    return round(0.15 + 0.65 * sg, 2)

def estimate_specific_heat(sg):
    """Higher SG woods tend to have lower specific heat."""
    return round(2000 - 600 * sg)

def hardness_scale(janka_lbf):
    """Normalize Janka to 0-1 scale (3500 lbf = 1.0)."""
    return round(min(1.0, janka_lbf / 3500), 2)

def make_species(id_, name, sci_name, category, sg, density, janka_lbf,
                 mor_mpa=None, moe_gpa=None,
                 contraction_r=None, contraction_t=None,
                 grain="straight", workability="moderate", resinous=False,
                 burn=0.3, tearout=0.3,
                 uses=None, tone="", sustainability="",
                 notes_thermal="", notes_machining=""):
    """Build a species entry from available data."""
    janka_n = round(janka_lbf * 4.44822)
    k = estimate_thermal_k(sg)
    sce = estimate_sce(sg)
    sh = estimate_specific_heat(sg)
    hs = hardness_scale(janka_lbf)

    # Machining params scaled from hardness
    chipload = round(max(0.5, 1.3 - 0.8 * hs), 2)
    rough_feed = round(max(1200, 6000 - 5000 * hs))
    finish_feed = round(max(700, 3500 - 3000 * hs))
    plunge_feed = round(max(250, 2000 - 1800 * hs))
    min_rpm = round(max(10000, 10000 + 8000 * hs))
    max_doc = round(max(2, 18 - 16 * hs))

    phys = {
        "specific_gravity": sg,
        "density_kg_m3": density,
        "janka_hardness_lbf": janka_lbf,
        "janka_hardness_n": janka_n,
        "grain": grain,
        "workability": workability,
        "resinous": resinous,
    }
    if contraction_r is not None:
        phys["contraction_radial_pct"] = contraction_r
    if contraction_t is not None:
        phys["contraction_tangential_pct"] = contraction_t
    if mor_mpa is not None:
        phys["modulus_of_rupture_mpa"] = mor_mpa
    if moe_gpa is not None:
        phys["modulus_of_elasticity_gpa"] = moe_gpa

    return {
        "id": id_,
        "name": name,
        "scientific_name": sci_name,
        "category": category,
        "physical": phys,
        "thermal": {
            "thermal_conductivity_w_per_mk": k,
            "specific_heat_capacity_j_per_kgk": sh,
            "specific_cutting_energy_j_per_mm3": sce,
            "heat_partition": {"chip": round(0.75 - 0.15*sg, 2), "tool": round(0.15 + 0.1*sg, 2), "work": round(0.10 + 0.05*sg, 2)},
            "_note": notes_thermal or f"Estimated from SG {sg}; CSV dump + CIRAD cross-reference"
        },
        "machining": {
            "hardness_scale": hs,
            "burn_tendency": burn,
            "tearout_tendency": tearout,
            "chipload_multiplier": chipload,
            "feed_clamp": {
                "roughing_max_mm_min": rough_feed,
                "finishing_max_mm_min": finish_feed,
                "plunge_max_mm_min": plunge_feed
            },
            "speed_clamp": {
                "min_rpm": min_rpm,
                "max_rpm": 24000,
                "optimal_sfm": round(max(350, 1200 - 900 * hs))
            },
            "doc_limits": {"max_doc_mm": max_doc, "optimal_doc_ratio": round(max(0.15, 0.7 - 0.55*hs), 2)},
            "woc_limits": {"max_woc_ratio": round(max(0.2, 0.7 - 0.5*hs), 2), "finishing_woc_ratio": round(max(0.04, 0.2 - 0.16*hs), 2)},
            "warnings": {
                "burn_risk": "low" if burn < 0.3 else ("high" if burn > 0.5 else "medium"),
                "tearout_risk": "low" if tearout < 0.3 else ("high" if tearout > 0.5 else "medium"),
                "dust_hazard": "high" if sg > 0.8 else ("medium" if sg > 0.6 else "low"),
                "notes": notes_machining or ""
            }
        },
        "lutherie": {
            "typical_uses": uses or ["body"],
            "tone_character": tone,
            "sustainability": sustainability
        }
    }

# New species to add — guitar-relevant woods from CSV dump + CIRAD
new_species = []

# From CSV: bubinga (name=bubinga)
r = csv_lookup.get("bubinga")
if r:
    new_species.append(make_species(
        "bubinga", "Bubinga", "Guibourtia demeusei", "hardwood",
        sg=0.86, density=890, janka_lbf=2410,
        mor_mpa=float(r["MOR (MPa)"]) if r.get("MOR (MPa)") else 168.0,
        moe_gpa=float(r["E (GPa)"]) if r.get("E (GPa)") else 18.4,
        grain="interlocked, often pommelé figure",
        workability="moderate — hard but clean-cutting",
        burn=0.2, tearout=0.4,
        uses=["body_top", "body", "back_sides", "neck_laminate"],
        tone="warm, rich bass, articulate mids — prized for bass guitars",
        sustainability="CITES Appendix II since 2017",
        notes_machining="Hard but machines cleanly. Figured pieces tear — use climb cuts."
    ))

# iroko
r = csv_lookup.get("iroko")
if r:
    new_species.append(make_species(
        "iroko", "Iroko", "Milicia excelsa", "hardwood",
        sg=0.63, density=660, janka_lbf=1260,
        mor_mpa=float(r["MOR (MPa)"]) if r.get("MOR (MPa)") else 98.4,
        moe_gpa=float(r["E (GPa)"]) if r.get("E (GPa)") else 10.1,
        grain="interlocked",
        workability="good — some interlocked grain tearout",
        burn=0.3, tearout=0.45,
        uses=["body"],
        tone="warm, midrange focus, mahogany-like character",
        sustainability="not threatened — teak substitute",
        notes_machining="Interlocked grain can tear. Contains calcium carbonate deposits — dulls tools."
    ))

# teak
r = csv_lookup.get("teak")
if r:
    new_species.append(make_species(
        "teak", "Teak", "Tectona grandis", "hardwood",
        sg=0.63, density=655, janka_lbf=1155,
        mor_mpa=float(r["MOR (MPa)"]) if r.get("MOR (MPa)") else 97.1,
        moe_gpa=float(r["E (GPa)"]) if r.get("E (GPa)") else 12.3,
        grain="straight, oily",
        workability="good — oily, dulls tools over time",
        resinous=True,
        burn=0.15, tearout=0.2,
        uses=["body", "fretboard"],
        tone="warm, dry, tight low end",
        sustainability="plantation-grown widely available",
        notes_thermal="Oily wood — tectoquinones in dust are irritating",
        notes_machining="Natural oils lubricate cuts but gum up tooling. Clean bits frequently."
    ))

# padauk
r = csv_lookup.get("african padauk") or csv_lookup.get("padauk")
if r:
    new_species.append(make_species(
        "padauk_african", "African Padauk", "Pterocarpus soyauxii", "hardwood",
        sg=0.72, density=745, janka_lbf=2170,
        mor_mpa=float(r["MOR (MPa)"]) if r.get("MOR (MPa)") else 133.8,
        moe_gpa=float(r["E (GPa)"]) if r.get("E (GPa)") else 12.5,
        grain="straight to interlocked",
        workability="good — stains everything red",
        burn=0.2, tearout=0.3,
        uses=["body", "accent", "neck_laminate"],
        tone="bright, snappy, good sustain",
        sustainability="not threatened",
        notes_machining="Vibrant red color stains everything. Seal end grain. Dust stains clothes."
    ))

# merbau
r = csv_lookup.get("merbau")
if r:
    new_species.append(make_species(
        "merbau", "Merbau (Kwila)", "Intsia bijuga", "hardwood",
        sg=0.80, density=830, janka_lbf=2460,
        mor_mpa=float(r["MOR (MPa)"]) if r.get("MOR (MPa)") else 126.9,
        moe_gpa=float(r["E (GPa)"]) if r.get("E (GPa)") else 14.5,
        grain="interlocked, coarse",
        workability="moderate — yellow deposits in pores",
        burn=0.2, tearout=0.35,
        uses=["fretboard", "body"],
        tone="warm, rosewood-like with stronger mids",
        sustainability="vulnerable in some regions",
        notes_machining="Yellow sulfur deposits in pores can stain. Blunts tools faster than expected."
    ))

# ovangkol / shedua
r = csv_lookup.get("ovangkol") or csv_lookup.get("shedua")
if r:
    new_species.append(make_species(
        "ovangkol", "Ovangkol (Shedua)", "Guibourtia ehie", "hardwood",
        sg=0.78, density=810, janka_lbf=1890,
        mor_mpa=float(r["MOR (MPa)"]) if r.get("MOR (MPa)") else 130.0,
        moe_gpa=float(r["E (GPa)"]) if r.get("E (GPa)") else 14.0,
        grain="interlocked, figure common",
        workability="moderate — interlocked grain tearout",
        burn=0.25, tearout=0.5,
        uses=["back_sides", "body"],
        tone="warm, complex — rosewood family character",
        sustainability="not threatened",
        notes_machining="Interlocked grain tears easily. Related to bubinga."
    ))

# pau ferro (Bolivian rosewood - from morado entry)
r = csv_lookup.get("pau ferro") or csv_lookup.get("bolivian rosewood")
new_species.append(make_species(
    "pau_ferro", "Pau Ferro (Bolivian Rosewood)", "Machaerium scleroxylon", "hardwood",
    sg=0.85, density=880, janka_lbf=2030,
    mor_mpa=131.0, moe_gpa=14.0,
    grain="straight to irregular, fine texture",
    workability="moderate — oily",
    resinous=True,
    burn=0.2, tearout=0.3,
    uses=["fretboard", "back_sides"],
    tone="bright, rosewood-like, slightly more mid-forward",
    sustainability="not CITES listed — popular rosewood substitute",
    notes_machining="Oily wood. Clean tools frequently. Common Fender fretboard wood since 2017."
))

# cocobolo
new_species.append(make_species(
    "cocobolo", "Cocobolo", "Dalbergia retusa", "hardwood",
    sg=1.10, density=1095, janka_lbf=2960,
    mor_mpa=None, moe_gpa=None,
    grain="irregular, fine texture, striking figure",
    workability="difficult — very oily, sensitizing dust",
    resinous=True,
    burn=0.15, tearout=0.2,
    uses=["body_top", "back_sides", "fretboard", "bridge"],
    tone="warm, rich, complex — among finest rosewoods",
    sustainability="CITES Appendix II — restricted",
    notes_thermal="Extremely oily — natural oils may interfere with gluing. SG from industry references.",
    notes_machining="Severe sensitizer for many people. Full dust extraction required. Oils lubricate cut."
))

# bocote
r = csv_lookup.get("bocote")
new_species.append(make_species(
    "bocote", "Bocote", "Cordia elaeagnoides", "hardwood",
    sg=0.75, density=775, janka_lbf=2200,
    mor_mpa=float(r["MOR (MPa)"]) if r and r.get("MOR (MPa)") else 130.0,
    moe_gpa=float(r["E (GPa)"]) if r and r.get("E (GPa)") else 12.5,
    grain="straight to wild, dramatic figure",
    workability="moderate — oily",
    resinous=True,
    burn=0.25, tearout=0.35,
    uses=["fretboard", "body_top", "accent"],
    tone="bright, snappy, great visual impact",
    sustainability="not threatened",
    notes_machining="Oily wood with dramatic figure. Machines well with sharp tooling."
))

# katalox (Mexican ebony)
new_species.append(make_species(
    "katalox", "Katalox (Mexican Ebony)", "Swartzia cubensis", "hardwood",
    sg=1.05, density=1050, janka_lbf=3650,
    mor_mpa=None, moe_gpa=None,
    grain="straight, very fine",
    workability="very difficult — extremely hard",
    burn=0.1, tearout=0.15,
    uses=["fretboard", "bridge"],
    tone="bright, bell-like — ebony alternative",
    sustainability="not threatened — ebony substitute",
    notes_machining="Among hardest commercial woods. Carbide only. Pre-drill all fastener holes."
))

# ziricote
new_species.append(make_species(
    "ziricote", "Ziricote", "Cordia dodecandra", "hardwood",
    sg=0.79, density=815, janka_lbf=1900,
    mor_mpa=None, moe_gpa=None,
    grain="irregular, spider-web figure",
    workability="good — machines cleanly despite density",
    burn=0.3, tearout=0.25,
    uses=["body_top", "back_sides", "fretboard"],
    tone="warm, complex, rosewood-like with unique character",
    sustainability="limited supply — slow-growing",
    notes_machining="Dramatic spider-web figure. Machines well. Related to bocote."
))

# granadillo / Mexican rosewood
r = csv_lookup.get("granadillo")
new_species.append(make_species(
    "granadillo", "Granadillo", "Platymiscium yucatanum", "hardwood",
    sg=0.90, density=925, janka_lbf=2790,
    mor_mpa=None, moe_gpa=None,
    grain="straight, fine",
    workability="moderate — dense but clean-cutting",
    burn=0.2, tearout=0.2,
    uses=["fretboard", "back_sides", "bridge"],
    tone="warm, complex, true rosewood character",
    sustainability="limited supply",
    notes_machining="Dense but machines well. Similar working properties to cocobolo minus the allergen risk."
))

# Spanish cedar (for classical guitar necks)
r = csv_lookup.get("spanish cedar") or csv_lookup.get("cedrela")
new_species.append(make_species(
    "cedar_spanish", "Spanish Cedar", "Cedrela odorata", "hardwood",
    sg=0.43, density=450, janka_lbf=600,
    mor_mpa=78.0, moe_gpa=9.7,
    contraction_r=4.2, contraction_t=6.3,
    grain="straight, medium to coarse",
    workability="excellent — very easy to work",
    resinous=True,
    burn=0.15, tearout=0.35,
    uses=["neck"],
    tone="warm — traditional classical guitar neck wood",
    sustainability="CITES Appendix III — plantation-grown available",
    notes_machining="Aromatic, easy to machine. Can be fuzzy on end grain. Traditional classical guitar neck."
))

# White spruce (common for bracing)
r = csv_lookup.get("white spruce") or csv_lookup.get("spruce")
new_species.append(make_species(
    "spruce_white", "White Spruce", "Picea glauca", "softwood",
    sg=0.40, density=410, janka_lbf=480,
    mor_mpa=65.5, moe_gpa=9.7,
    contraction_r=3.0, contraction_t=7.0,
    grain="straight, tight",
    workability="good",
    resinous=True,
    burn=0.15, tearout=0.55,
    uses=["bracing", "soundboard"],
    tone="bright, even — common bracing wood",
    sustainability="sustainable, abundant",
    notes_machining="Softwood, tears across grain. Sharp tools essential."
))

# European spruce (prized soundboard)
new_species.append(make_species(
    "spruce_european", "European Spruce (Alpine/German)", "Picea abies", "softwood",
    sg=0.40, density=405, janka_lbf=490,
    mor_mpa=65.0, moe_gpa=9.5,
    contraction_r=2.8, contraction_t=6.8,
    grain="straight, very tight, stiff",
    workability="good — soft but stiff",
    resinous=True,
    burn=0.15, tearout=0.6,
    uses=["soundboard"],
    tone="warm, complex, refined — the classical luthier's choice",
    sustainability="sustainable — European plantations",
    notes_machining="Very stiff for its weight. Quartersawn essential for soundboards."
))

# Adirondack spruce (prized soundboard)
new_species.append(make_species(
    "spruce_adirondack", "Adirondack Spruce (Red Spruce)", "Picea rubens", "softwood",
    sg=0.43, density=435, janka_lbf=560,
    mor_mpa=74.0, moe_gpa=11.2,
    contraction_r=3.0, contraction_t=6.9,
    grain="straight, tight",
    workability="good",
    resinous=True,
    burn=0.15, tearout=0.5,
    uses=["soundboard"],
    tone="powerful, headroom, loud — the pre-war dreadnought tonewood",
    sustainability="limited supply — slow-growing",
    notes_machining="Stiffest North American spruce. Premium soundboard wood."
))

###############################################################################
# 8. Add new species to canonical
###############################################################################
added = 0
for sp in new_species:
    sid = sp["id"]
    if sid not in species:
        species[sid] = sp
        added += 1
        print(f"  Added: {sid} ({sp['name']})")
    else:
        # Update missing structural data if available
        if "modulus_of_rupture_mpa" in sp["physical"] and "modulus_of_rupture_mpa" not in species[sid]["physical"]:
            species[sid]["physical"]["modulus_of_rupture_mpa"] = sp["physical"]["modulus_of_rupture_mpa"]
            species[sid]["physical"]["modulus_of_elasticity_gpa"] = sp["physical"].get("modulus_of_elasticity_gpa")
            print(f"  Enriched: {sid} with MOR/MOE")

print(f"\nAdded {added} new species")
print(f"Total species: {len(species)}")

###############################################################################
# 9. Update meta version
###############################################################################
canonical["_meta"]["version"] = "3.0.0"
canonical["_meta"]["sources"]["structural"] = "Assorted species mechanical properties dataset + wood-database.com (MOR, MOE, contraction, Janka)"
canonical["_meta"]["sources"]["cirad"] = "CIRAD Wood Collection Index (34,395 specimens, specific gravity cross-validation)"
canonical["_meta"]["units"]["contraction_radial_pct"] = "% shrinkage green to oven-dry, radial"
canonical["_meta"]["units"]["contraction_tangential_pct"] = "% shrinkage green to oven-dry, tangential"
canonical["_meta"]["units"]["modulus_of_rupture_mpa"] = "MPa — static bending strength at 12% MC"
canonical["_meta"]["units"]["modulus_of_elasticity_gpa"] = "GPa — static bending stiffness at 12% MC"

###############################################################################
# 10. Write output
###############################################################################
with open(CANONICAL, "w", encoding="utf-8") as f:
    json.dump(canonical, f, indent=2, ensure_ascii=False)

print(f"\nWrote {CANONICAL}")
print(f"Final species count: {len(species)}")

# Summary
has_mor = sum(1 for v in species.values() if "modulus_of_rupture_mpa" in v.get("physical", {}))
has_k = sum(1 for v in species.values() if "thermal_conductivity_w_per_mk" in v.get("thermal", {}))
has_mach = sum(1 for v in species.values() if "feed_clamp" in v.get("machining", {}))
print(f"With structural data: {has_mor}")
print(f"With thermal data: {has_k}")
print(f"With machining data: {has_mach}")
