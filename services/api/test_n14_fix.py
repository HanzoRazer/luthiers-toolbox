"""
N14 Validation Fix - Complete Test Suite
Tests the N11.1 schema patch and RMOS rosette endpoints
"""
import sys
from pathlib import Path

print("=" * 60)
print("N14 VALIDATION FIX - COMPLETE TEST SUITE")
print("=" * 60)

# Test 1: Schema Verification
print("\n[TEST 1] Schema Version and Structure")
print("-" * 60)

from app.core.rmos_db import get_rmos_db
import sqlite3

db = get_rmos_db()
schema_version = db.get_schema_version()
print(f"✓ Schema version: {schema_version}")

if schema_version != 2:
    print(f"❌ FAIL: Expected schema version 2, got {schema_version}")
    sys.exit(1)

# Check columns
db_path = Path(__file__).parent / "data" / "rmos.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(patterns)")
cols = {c[1] for c in cursor.fetchall()}

required_columns = {'id', 'name', 'ring_count', 'geometry_json', 'pattern_type', 'rosette_geometry'}
missing = required_columns - cols

if missing:
    print(f"❌ FAIL: Missing columns: {missing}")
    sys.exit(1)

print(f"✓ All required columns present: {len(required_columns)}")

# Check indexes
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='patterns'")
indexes = {idx[0] for idx in cursor.fetchall()}

if 'idx_patterns_pattern_type' not in indexes:
    print("❌ FAIL: Missing pattern_type index")
    sys.exit(1)

print(f"✓ Pattern type index exists")
conn.close()

# Test 2: Endpoint Functionality
print("\n[TEST 2] RMOS Rosette Endpoints")
print("-" * 60)

from app.api.routes.rmos_rosette_api import list_rosette_patterns

try:
    result = list_rosette_patterns()
    print(f"✓ list_rosette_patterns() executed successfully")
    print(f"  Result: {result}")
except Exception as e:
    print(f"❌ FAIL: Endpoint error: {e}")
    sys.exit(1)

# Test 3: Pattern Store Operations
print("\n[TEST 3] SQLitePatternStore Operations")
print("-" * 60)

from app.stores.sqlite_pattern_store import SQLitePatternStore

store = SQLitePatternStore()

try:
    # Test list_by_type (this was the failing method)
    rosette_patterns = store.list_by_type('rosette')
    print(f"✓ list_by_type('rosette') executed successfully")
    print(f"  Found {len(rosette_patterns)} rosette patterns")
    
    generic_patterns = store.list_by_type('generic')
    print(f"✓ list_by_type('generic') executed successfully")
    print(f"  Found {len(generic_patterns)} generic patterns")
    
except Exception as e:
    print(f"❌ FAIL: Store operation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create and Query Pattern
print("\n[TEST 4] Pattern Creation and Retrieval")
print("-" * 60)

try:
    # Clean up any existing test pattern first
    test_pattern_id = "test-rosette-001"
    try:
        store.delete(test_pattern_id)
        print(f"✓ Cleaned up existing test pattern")
    except:
        pass
    
    # Create a test rosette pattern
    store.create({
        'id': test_pattern_id,
        'name': 'Test Rosette Pattern',
        'ring_count': 5,
        'geometry_json': '{"rings": []}',
        'pattern_type': 'rosette',
        'rosette_geometry': '{"type": "concentric"}',
        'metadata_json': '{}'
    })
    print(f"✓ Created test rosette pattern: {test_pattern_id}")
    
    # Retrieve by type
    rosette_patterns = store.list_by_type('rosette')
    if len(rosette_patterns) != 1:
        print(f"❌ FAIL: Expected 1 rosette pattern, found {len(rosette_patterns)}")
        sys.exit(1)
    
    print(f"✓ Retrieved rosette pattern by type")
    
    # Retrieve by ID
    retrieved = store.get_by_id(test_pattern_id)
    if not retrieved:
        print(f"❌ FAIL: Could not retrieve pattern by ID")
        sys.exit(1)
    
    print(f"✓ Retrieved pattern by ID: {retrieved['name']}")
    
    # Cleanup
    store.delete(test_pattern_id)
    print(f"✓ Deleted test pattern (cleanup)")
    
except Exception as e:
    print(f"❌ FAIL: Pattern operation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final Summary
print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED")
print("=" * 60)
print("\nN11.1 Schema Patch Status:")
print("  • Schema version: 2")
print("  • pattern_type column: ✅ Added")
print("  • rosette_geometry column: ✅ Added")
print("  • pattern_type index: ✅ Created")
print("  • Endpoint functionality: ✅ Working")
print("  • Store operations: ✅ Working")
print("\nN14 Validation Issue: RESOLVED ✅")
