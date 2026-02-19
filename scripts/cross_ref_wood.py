"""Cross-reference dump.csv and CIRAD data with existing wood_species.json."""
import csv, json

# Load existing species
with open(r'services/api/app/data_registry/system/materials/wood_species.json') as f:
    existing = json.load(f)['species']

# Load dump.csv
dump = {}
with open(r'c:\Users\thepr\Downloads\dump.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        dump[r['name']] = r

# Map existing species IDs to dump.csv names
mapping = {
    'mahogany_honduran': 'honduran-mahogany',
    'mahogany_african': 'african-mahogany',
    'maple_hard': 'hard-maple',
    'maple_soft': 'red-maple',
    'rosewood_east_indian': 'east-indian-rosewood',
    'rosewood_brazilian': 'brazilian-rosewood',
    'ebony_macassar': 'macassar-ebony',
    'alder': 'red-alder',
    'ash_white': 'white-ash',
    'basswood': 'basswood',
    'cherry_black': 'black-cherry',
    'poplar_yellow': 'yellow-poplar',
    'oak_white': 'white-oak',
    'oak_red': 'red-oak',
    'beech_american': 'american-beech',
    'birch_yellow': 'yellow-birch',
    'spruce_sitka': 'sitka-spruce',
    'spruce_engelmann': 'engelmann-spruce',
    'cedar_western_red': 'western-red-cedar',
    'walnut_black': 'black-walnut',
    'douglas_fir': 'douglas-fir',
    'pine_eastern_white': 'eastern-white-pine',
    'redwood': 'coast-redwood',
    'koa': 'koa',
    'sapele': 'sapele',
    'wenge': 'wenge',
    'purpleheart': 'purpleheart',
    'jatoba': 'jatoba',
    'zebrawood': 'zebrawood',
    'cypress_bald': 'bald-cypress',
    'ipe': 'ipe',
    'tasmanian_blackwood': 'australian-blackwood',
}

print("=== Existing species: dump.csv comparison ===")
for our_id, dump_name in sorted(mapping.items()):
    if dump_name in dump:
        d = dump[dump_name]
        e = existing.get(our_id, {}).get('physical', {})
        mor_ours = e.get('modulus_of_rupture_mpa', None)
        mor_csv = float(d['MOR (MPa)'])
        moe_ours = e.get('modulus_of_elasticity_gpa', None)
        moe_csv = float(d['E (GPa)'])
        dens_ours = e.get('density_kg_m3', None)
        dens_csv = float(d['r Kg/m^3'])
        flags = []
        if mor_ours is not None and abs(mor_ours - mor_csv) / mor_csv > 0.15:
            flags.append(f"MOR diff {mor_ours:.1f} vs {mor_csv:.1f}")
        if moe_ours is not None and abs(moe_ours - moe_csv) / moe_csv > 0.15:
            flags.append(f"MOE diff {moe_ours:.1f} vs {moe_csv:.1f}")
        if dens_ours is not None and abs(dens_ours - dens_csv) / dens_csv > 0.1:
            flags.append(f"density diff {dens_ours} vs {dens_csv}")
        need_mor = mor_ours is None
        need_moe = moe_ours is None
        status = "OK" if not flags else " | ".join(flags)
        missing = []
        if need_mor:
            missing.append("needs MOR")
        if need_moe:
            missing.append("needs MOE")
        if missing:
            status += (" | " if flags else "") + " | ".join(missing)
        print(f"  {our_id}: {status} (csv: MOR={mor_csv} MOE={moe_csv} dens={dens_csv})")
    else:
        print(f"  {our_id}: NOT FOUND as '{dump_name}'")

# New guitar-relevant species from dump.csv not in existing
print("\n=== Guitar-relevant species in dump.csv NOT in registry ===")
guitar_new = [
    'african-blackwood', 'african-padauk', 'bocote', 'bubinga', 'cocobolo',
    'spanish-cedar', 'teak', 'iroko', 'ovangkol', 'pau-ferro',
    'ziricote', 'gaboon-ebony', 'madagascar-rosewood', 'merbau',
    'santos-mahogany', 'bloodwood', 'cumaru', 'katalox', 'snakewood',
    'lignum-vitae', 'olive', 'osage-orange', 'persimmon', 'holly',
    'black-locust', 'hackberry', 'sassafras', 'butternut', 'paulownia',
    'balsa', 'bamboo', 'canarywood', 'cuban-mahogany', 'english-walnut',
    'european-ash', 'european-beech', 'european-larch', 'european-yew',
    'hickory', 'jarrah', 'london-plane', 'mulberry', 'norway-spruce',
    'pear', 'scots-pine', 'silver-birch', 'sycamore-maple',
    'pink-ivory', 'lacewood', 'partridgewood', 'imbuia',
]
for name in sorted(guitar_new):
    if name in dump:
        d = dump[name]
        print(f"  {name}: MOR={d['MOR (MPa)']} MOE={d['E (GPa)']} dens={d['r Kg/m^3']}")
    else:
        print(f"  {name}: NOT in dump.csv")

# Count what's missing from the Macassar ebony entry
print("\n=== Macassar ebony (not directly in dump, using name search) ===")
for k,v in dump.items():
    if 'macassar' in k.lower() or 'ebony' in k.lower():
        print(f"  {k}: MOR={v['MOR (MPa)']} MOE={v['E (GPa)']} dens={v['r Kg/m^3']}")
