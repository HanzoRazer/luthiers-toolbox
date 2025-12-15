import sqlite3
import csv

db = 'IDC Woodcraft Vectric Tool Database Library Update rev 25-5.vtdb'
conn = sqlite3.connect(db)
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables in database:')
for table in tables:
    print(f'  - {table[0]}')

if not tables:
    print("No tables found")
    exit()

# Export tool_entity table (the actual tools)
table_name = 'tool_entity'

# Get table schema
cursor.execute(f"PRAGMA table_info({table_name})")
columns = cursor.fetchall()
print(f'\nColumns in {table_name}:')
for col in columns:
    print(f'  - {col[1]} ({col[2]})')

# Count rows
cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
count = cursor.fetchone()[0]
print(f'\nTotal tools: {count}')

# Export to CSV
output_file = 'IDC-Woodcraft-Vectric-Tools-exported.csv'
cursor.execute(f"SELECT * FROM {table_name}")
rows = cursor.fetchall()
column_names = [col[1] for col in columns]

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(column_names)
    writer.writerows(rows)

print(f'\n✓ Exported {count} tools to {output_file}')
print(f'\nFirst 3 tools (first 5 columns):')
for i, row in enumerate(rows[:3]):
    print(f'  {i+1}: {row[:5]}')

conn.close()
