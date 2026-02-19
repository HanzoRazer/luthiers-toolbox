import json, os

d = json.load(open(r'services/api/app/data_registry/system/materials/wood_species.json', 'r', encoding='utf-8'))
sp = d['species']

for sid in ['mahogany_honduran', 'sapele', 'bloodwood', 'balsa']:
    e = sp[sid]
    tier = e["guitar_relevance"]
    name = e["name"]
    sg = e["physical"]["specific_gravity"]
    dens = e["physical"]["density_kg_m3"]
    mor = e["physical"].get("modulus_of_rupture_mpa", "N/A")
    moe = e["physical"].get("modulus_of_elasticity_gpa", "N/A")
    k = e["thermal"]["thermal_conductivity_w_per_mk"]
    hs = e["machining"]["hardness_scale"]
    aliases = e.get("aliases", [])
    print(f"--- {sid} ({tier}) ---")
    print(f"  Name: {name}")
    print(f"  SG: {sg}  Density: {dens}")
    print(f"  MOR: {mor}  MOE: {moe}")
    print(f"  Thermal k: {k}")
    print(f"  Hardness: {hs}")
    print(f"  Aliases: {aliases}")
    print()

size = os.path.getsize(r'services/api/app/data_registry/system/materials/wood_species.json')
print(f"File size: {size:,} bytes ({size/1024:.0f} KB)")
print(f"Total species: {len(sp)}")
