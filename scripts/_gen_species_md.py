"""Generate a Markdown reference document for all wood species."""
import json
from pathlib import Path

CANONICAL = Path(r"services/api/app/data_registry/system/materials/wood_species.json")
OUTPUT = Path(r"services/api/app/data_registry/system/materials/WOOD_SPECIES_REFERENCE.md")

with open(CANONICAL, encoding="utf-8") as f:
    data = json.load(f)

species = data["species"]
meta = data["_meta"]

# Group by tier
tiers = {"primary": [], "established": [], "emerging": [], "exploratory": []}
for sid, sp in species.items():
    t = sp.get("guitar_relevance", "exploratory")
    tiers.setdefault(t, []).append(sp)


def fmt(val, fallback="—"):
    if val is None or val == "":
        return fallback
    return str(val)


def write_detail(sp, lines):
    """Full profile for primary/established species."""
    phys = sp.get("physical", {})
    therm = sp.get("thermal", {})
    mach = sp.get("machining", {})
    luth = sp.get("lutherie", {})
    aliases = sp.get("aliases", [])

    name = sp["name"]
    sci = sp.get("scientific_name", "")
    cat = sp.get("category", "")
    sid = sp.get("id", "")

    lines.append(f"<a id=\"{sid}\"></a>")
    lines.append(f"#### {name}")
    lines.append("")
    header = f"**ID:** `{sid}` · **Category:** {cat}"
    if sci:
        header += f" · **Scientific name:** *{sci}*"
    if aliases:
        header += f" · **Also known as:** {', '.join(aliases)}"
    lines.append(header)
    lines.append("")

    # Physical
    lines.append("| Property | Value |")
    lines.append("|----------|-------|")
    lines.append(f"| Specific Gravity | {fmt(phys.get('specific_gravity'))} |")
    lines.append(f"| Density | {fmt(phys.get('density_kg_m3'))} kg/m³ |")
    lines.append(f"| Janka Hardness | {fmt(phys.get('janka_hardness_lbf'))} lbf / {fmt(phys.get('janka_hardness_n'))} N |")
    if "modulus_of_rupture_mpa" in phys:
        lines.append(f"| Modulus of Rupture | {phys['modulus_of_rupture_mpa']} MPa |")
    if "modulus_of_elasticity_gpa" in phys:
        lines.append(f"| Modulus of Elasticity | {phys['modulus_of_elasticity_gpa']} GPa |")
    if phys.get("grain"):
        lines.append(f"| Grain | {phys['grain']} |")
    if phys.get("workability"):
        lines.append(f"| Workability | {phys['workability']} |")
    lines.append(f"| Resinous | {'Yes' if phys.get('resinous') else 'No'} |")
    if "contraction_radial_pct" in phys:
        lines.append(f"| Shrinkage (radial) | {phys['contraction_radial_pct']}% |")
    if "contraction_tangential_pct" in phys:
        lines.append(f"| Shrinkage (tangential) | {phys['contraction_tangential_pct']}% |")

    # Thermal
    lines.append(f"| Thermal Conductivity | {fmt(therm.get('thermal_conductivity_w_per_mk'))} W/(m·K) |")
    lines.append(f"| Specific Heat | {fmt(therm.get('specific_heat_capacity_j_per_kgk'))} J/(kg·K) |")
    lines.append(f"| Specific Cutting Energy | {fmt(therm.get('specific_cutting_energy_j_per_mm3'))} J/mm³ |")

    # Machining
    lines.append(f"| Hardness Scale | {fmt(mach.get('hardness_scale'))} |")
    lines.append(f"| Burn Tendency | {fmt(mach.get('burn_tendency'))} |")
    lines.append(f"| Tearout Tendency | {fmt(mach.get('tearout_tendency'))} |")

    feed = mach.get("feed_clamp", {})
    if feed:
        lines.append(f"| Roughing Feed Max | {fmt(feed.get('roughing_max_mm_min'))} mm/min |")
        lines.append(f"| Finishing Feed Max | {fmt(feed.get('finishing_max_mm_min'))} mm/min |")

    speed = mach.get("speed_clamp", {})
    if speed:
        lines.append(f"| RPM Range | {fmt(speed.get('min_rpm'))}–{fmt(speed.get('max_rpm'))} |")

    warn = mach.get("warnings", {})
    if warn:
        risks = []
        if warn.get("burn_risk"):
            risks.append(f"Burn: {warn['burn_risk']}")
        if warn.get("tearout_risk"):
            risks.append(f"Tearout: {warn['tearout_risk']}")
        if warn.get("dust_hazard"):
            risks.append(f"Dust: {warn['dust_hazard']}")
        if risks:
            lines.append(f"| CNC Risks | {', '.join(risks)} |")

    # Lutherie
    if luth.get("typical_uses"):
        lines.append(f"| Guitar Uses | {', '.join(luth['typical_uses'])} |")
    if luth.get("tone_character"):
        lines.append(f"| Tone Character | {luth['tone_character']} |")
    if luth.get("sustainability"):
        lines.append(f"| Sustainability | {luth['sustainability']} |")

    lines.append("")


def write_compact(sp, lines):
    """Compact entry for emerging species."""
    phys = sp.get("physical", {})
    mach = sp.get("machining", {})
    luth = sp.get("lutherie", {})

    name = sp["name"]
    sci = sp.get("scientific_name", "")
    sid = sp.get("id", "")

    sci_str = f" (*{sci}*)" if sci else ""
    lines.append(f"**{name}**{sci_str} — `{sid}`")

    parts = []
    parts.append(f"SG {fmt(phys.get('specific_gravity'))}")
    parts.append(f"{fmt(phys.get('density_kg_m3'))} kg/m³")
    parts.append(f"Janka {fmt(phys.get('janka_hardness_lbf'))} lbf")
    if "modulus_of_rupture_mpa" in phys:
        parts.append(f"MOR {phys['modulus_of_rupture_mpa']} MPa")
    if "modulus_of_elasticity_gpa" in phys:
        parts.append(f"MOE {phys['modulus_of_elasticity_gpa']} GPa")
    parts.append(f"Hardness scale {fmt(mach.get('hardness_scale'))}")

    warn = mach.get("warnings", {})
    risks = []
    if warn.get("burn_risk") and warn["burn_risk"] != "low":
        risks.append(f"burn:{warn['burn_risk']}")
    if warn.get("dust_hazard") and warn["dust_hazard"] != "low":
        risks.append(f"dust:{warn['dust_hazard']}")
    if risks:
        parts.append(f"Warnings: {', '.join(risks)}")

    if luth.get("tone_character"):
        parts.append(f"Tone: {luth['tone_character']}")
    if luth.get("typical_uses"):
        parts.append(f"Uses: {', '.join(luth['typical_uses'])}")

    lines.append(f"> {' · '.join(parts)}")
    lines.append("")


# ============================================================
# Build document
# ============================================================
lines = []
w = lines.append

w("# Wood Species Reference")
w("")
w(f"**Version:** {meta['version']}  ")
w(f"**Total species:** {len(species)}  ")
w("**Last updated:** February 2026  ")
w("**Source data:** [`wood_species.json`](wood_species.json)  ")
w("**Methodology & citations:** [`SOURCES.md`](SOURCES.md)")
w("")
w("---")
w("")
w("## Data Sources")
w("")
w("| Source | Description | License |")
w("|--------|-------------|---------|")
src = meta["sources"]
for key in ["fpl", "wood_database", "cirad"]:
    s = src[key]
    title = s.get("title", key)
    url = s.get("url", "")
    provides = s.get("provides", "")
    lic = s.get("license", "")
    w(f"| [{title}]({url}) | {provides} | {lic} |")
w("")
w(f"> **Estimation note:** {src['estimation_methods']}")
w("")
w("---")
w("")
w("## Guitar Relevance Tiers")
w("")
w("| Tier | Count | Description |")
w("|------|-------|-------------|")
w(f"| **Primary** | {len(tiers['primary'])} | Traditional tonewoods — the classic guitar species |")
w(f"| **Established** | {len(tiers['established'])} | Well-known guitar woods with proven track records |")
w(f"| **Emerging** | {len(tiers['emerging'])} | Species gaining popularity as sustainable or affordable alternatives |")
w(f"| **Exploratory** | {len(tiers['exploratory'])} | Valid machinable woods — available for experimentation |")
w("")
w("---")
w("")

# Units legend
w("## Units")
w("")
w("| Abbreviation | Unit | Description |")
w("|-------------|------|-------------|")
w("| SG | — | Specific gravity (oven-dry weight / green volume) |")
w("| Density | kg/m³ | Air-dry density |")
w("| Janka | lbf | Side hardness, pound-force |")
w("| MOR | MPa | Modulus of rupture — static bending strength at 12% MC |")
w("| MOE | GPa | Modulus of elasticity — static bending stiffness at 12% MC |")
w("| k | W/(m·K) | Thermal conductivity at 12% MC, across grain |")
w("| SCE | J/mm³ | Specific cutting energy |")
w("| Feeds | mm/min | CNC feed rates |")
w("| RPM | rev/min | Spindle speed |")
w("")
w("---")
w("")

# ============================================================
# Per-tier sections
# ============================================================
tier_labels = {
    "primary": "Primary Tonewoods",
    "established": "Established Guitar Woods",
    "emerging": "Emerging Alternatives",
    "exploratory": "Exploratory Species",
}

tier_descriptions = {
    "primary": "The core species that have defined the sound and feel of electric and acoustic guitars for decades.",
    "established": "Proven guitar woods in regular use by luthiers, with well-understood tonal and machining characteristics.",
    "emerging": "Species gaining traction as luthiers seek sustainable, cost-effective, and tonally interesting alternatives to traditional tonewoods.",
    "exploratory": "Valid CNC-machinable species not yet widely used in guitar building. Included to support experimentation with underutilized and sustainable wood sources.",
}

for tier_key in ["primary", "established", "emerging", "exploratory"]:
    tier_species = tiers[tier_key]
    label = tier_labels[tier_key]
    desc = tier_descriptions[tier_key]

    w(f"## {label}")
    w("")
    w(f"*{desc}*")
    w("")

    # Summary table
    w("| # | Species | Scientific Name | Type | SG | Density | Janka | MOR | MOE | k |")
    w("|--:|---------|-----------------|------|----|---------|-------|-----|-----|---|")

    for i, sp in enumerate(tier_species, 1):
        name = sp["name"]
        sci = sp.get("scientific_name", "")
        cat = sp.get("category", "")[0].upper() if sp.get("category") else ""
        phys = sp.get("physical", {})
        therm = sp.get("thermal", {})

        sg = fmt(phys.get("specific_gravity"))
        dens = fmt(phys.get("density_kg_m3"))
        janka = fmt(phys.get("janka_hardness_lbf"))
        mor = fmt(phys.get("modulus_of_rupture_mpa"))
        moe = fmt(phys.get("modulus_of_elasticity_gpa"))
        k = fmt(therm.get("thermal_conductivity_w_per_mk"))

        sci_fmt = f"*{sci}*" if sci else "—"
        w(f"| {i} | **{name}** | {sci_fmt} | {cat} | {sg} | {dens} | {janka} | {mor} | {moe} | {k} |")

    w("")

    # Detailed entries for primary and established
    if tier_key in ("primary", "established"):
        w(f"### Detailed Profiles")
        w("")
        for sp in tier_species:
            write_detail(sp, lines)

    # Compact notes for emerging
    elif tier_key == "emerging":
        w(f"### Species Notes")
        w("")
        for sp in tier_species:
            write_compact(sp, lines)

    # Exploratory just gets the summary table — no per-species detail
    w("---")
    w("")

# ============================================================
# Appendix: Full alphabetical index
# ============================================================
w("## Appendix: Alphabetical Index")
w("")
w("| Species | ID | Tier | SG | Density | Janka | MOR | MOE |")
w("|---------|-----|------|-----|---------|-------|-----|-----|")

all_sorted = sorted(species.values(), key=lambda s: s["name"].lower())
for sp in all_sorted:
    name = sp["name"]
    sid = sp["id"]
    tier = sp.get("guitar_relevance", "exploratory")
    phys = sp.get("physical", {})
    sg = fmt(phys.get("specific_gravity"))
    dens = fmt(phys.get("density_kg_m3"))
    janka = fmt(phys.get("janka_hardness_lbf"))
    mor = fmt(phys.get("modulus_of_rupture_mpa"))
    moe = fmt(phys.get("modulus_of_elasticity_gpa"))
    tier_badge = {"primary": "🟢", "established": "🔵", "emerging": "🟡", "exploratory": "⚪"}.get(tier, "⚪")
    w(f"| {name} | `{sid}` | {tier_badge} {tier} | {sg} | {dens} | {janka} | {mor} | {moe} |")

w("")
w("---")
w("")
w("*Generated from `wood_species.json` v4.0.0. See [SOURCES.md](SOURCES.md) for full data provenance and estimation methodology.*")

# Write
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Wrote {OUTPUT}")
print(f"  {len(lines)} lines")
print(f"  {len(species)} species")
