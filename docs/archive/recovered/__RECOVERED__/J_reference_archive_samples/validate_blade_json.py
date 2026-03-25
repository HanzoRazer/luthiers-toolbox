import json
import sys

filepath = 'saw_lab_blades_FIXED.json'

# 1. JSON Syntax Check
try:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('[OK] JSON syntax valid')
except json.JSONDecodeError as e:
    print(f'[ERROR] JSON syntax error: {e}')
    sys.exit(1)

errors = []
warnings = []

if 'blades' not in data:
    errors.append('Missing required key: blades')
else:
    blades = data['blades']
    print(f'[INFO] Found {len(blades)} blades')
    
    required_blade_fields = ['id', 'name', 'diameter_mm', 'kerf_mm', 'tooth_count', 'max_rpm']
    required_preset_fields = ['name', 'feed_mm_per_min', 'rpm']
    
    blade_ids = set()
    for i, blade in enumerate(blades):
        blade_id = blade.get('id', f'blade_{i}')
        
        if blade_id in blade_ids:
            errors.append(f'Duplicate blade ID: {blade_id}')
        blade_ids.add(blade_id)
        
        for field in required_blade_fields:
            if field not in blade:
                errors.append(f'Blade [{blade_id}]: Missing required field "{field}"')
        
        # Type checks
        if 'diameter_mm' in blade and not isinstance(blade['diameter_mm'], (int, float)):
            errors.append(f'Blade [{blade_id}]: diameter_mm must be numeric')
        if 'kerf_mm' in blade and not isinstance(blade['kerf_mm'], (int, float)):
            errors.append(f'Blade [{blade_id}]: kerf_mm must be numeric')
        
        if 'presets' in blade:
            for j, preset in enumerate(blade['presets']):
                preset_name = preset.get('name', f'preset_{j}')
                for field in required_preset_fields:
                    if field not in preset:
                        errors.append(f'Blade [{blade_id}] Preset [{preset_name}]: Missing "{field}"')
                if 'risk_band' in preset and preset['risk_band'] not in ['GREEN', 'YELLOW', 'RED']:
                    warnings.append(f'Blade [{blade_id}] Preset [{preset_name}]: Unknown risk_band "{preset["risk_band"]}"')

print()
print('=' * 50)
print('VALIDATION REPORT')
print('=' * 50)

if errors:
    print(f'\n[ERRORS] {len(errors)}:')
    for e in errors[:20]:
        print(f'  - {e}')
    if len(errors) > 20:
        print(f'  ... and {len(errors) - 20} more')
else:
    print('\n[ERRORS] None')

if warnings:
    print(f'\n[WARNINGS] {len(warnings)}:')
    for w in warnings[:10]:
        print(f'  - {w}')
    if len(warnings) > 10:
        print(f'  ... and {len(warnings) - 10} more')
else:
    print('\n[WARNINGS] None')

print('\nSTATISTICS:')
print(f'  Total Blades: {len(blades)}')
total_presets = sum(len(b.get('presets', [])) for b in blades)
print(f'  Total Presets: {total_presets}')
diameters = sorted(set(b.get('diameter_mm', 0) for b in blades))
print(f'  Diameters (mm): {diameters}')
materials = set()
for b in blades:
    materials.update(b.get('material_class', []))
print(f'  Material Classes: {sorted(materials)}')

print()
if errors:
    print('[RESULT] FAILED - Fix errors before use')
    sys.exit(1)
else:
    print('[RESULT] PASSED - JSON is valid')
