import sqlite3
import csv

db = 'IDC Woodcraft Vectric Tool Database Library Update rev 25-5.vtdb'
conn = sqlite3.connect(db)
cursor = conn.cursor()

# Join tables to get complete tool information
query = """
SELECT 
    tg.name_format as tool_name,
    tg.tool_type,
    tg.diameter,
    tg.flute_length,
    tg.num_flutes,
    tg.included_angle,
    tg.flat_diameter,
    tg.tip_radius,
    tcd.spindle_speed,
    tcd.feed_rate,
    tcd.plunge_rate,
    tcd.stepdown,
    tcd.stepover,
    tcd.tool_number,
    tcd.notes as cutting_notes,
    m.name as material,
    ma.name as machine,
    ma.make as machine_make,
    ma.model as machine_model
FROM tool_entity te
LEFT JOIN tool_geometry tg ON te.tool_geometry_id = tg.id
LEFT JOIN tool_cutting_data tcd ON te.tool_cutting_data_id = tcd.id
LEFT JOIN material m ON te.material_id = m.id
LEFT JOIN machine ma ON te.machine_id = ma.id
ORDER BY tg.name_format
"""

cursor.execute(query)
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

output_file = 'IDC-Woodcraft-Vectric-Tools-FULL.csv'

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)

print(f'✓ Exported {len(rows)} complete tool records to {output_file}')
print(f'\nColumns: {", ".join(columns)}')
print(f'\nFirst 5 tools:')
for i, row in enumerate(rows[:5]):
    name = row[0] if row[0] else "Unnamed"
    diameter = row[2] if row[2] else 0
    rpm = row[8] if row[8] else 0
    feed = row[9] if row[9] else 0
    print(f'  {i+1}: {name} - Ø{diameter}mm, {rpm}RPM, {feed}mm/min')

conn.close()
