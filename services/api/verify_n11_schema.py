"""
Verify N11.1 schema patch was applied correctly.
"""
import sqlite3
from pathlib import Path

print("=== Testing N11.1 Schema Patch ===\n")

# Import and initialize database
from app.core.rmos_db import get_rmos_db

db = get_rmos_db()
print(f"Schema version: {db.get_schema_version()}")

# Check table structure
db_path = Path(__file__).parent / "data" / "rmos.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get column information
cursor.execute("PRAGMA table_info(patterns)")
cols = cursor.fetchall()

print("\nPatterns table columns:")
for c in cols:
    print(f"  {c[1]} ({c[2]})")

# Check for N11.1 columns
pattern_type_found = any(c[1] == 'pattern_type' for c in cols)
rosette_geometry_found = any(c[1] == 'rosette_geometry' for c in cols)

# Get indexes
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='patterns'")
indexes = cursor.fetchall()

print("\nPatterns table indexes:")
for idx in indexes:
    print(f"  {idx[0]}")

pattern_type_index_found = any('pattern_type' in idx[0] for idx in indexes)

conn.close()

# Validation
print("\n=== Validation Results ===")
print(f"✓ pattern_type column: {'✅ FOUND' if pattern_type_found else '❌ MISSING'}")
print(f"✓ rosette_geometry column: {'✅ FOUND' if rosette_geometry_found else '❌ MISSING'}")
print(f"✓ pattern_type index: {'✅ FOUND' if pattern_type_index_found else '❌ MISSING'}")

if pattern_type_found and rosette_geometry_found and pattern_type_index_found:
    print("\n✅ N11.1 Schema patch applied successfully!")
else:
    print("\n❌ Schema patch incomplete - some elements missing")
