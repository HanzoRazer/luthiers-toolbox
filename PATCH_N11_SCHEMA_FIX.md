# PATCH: N11.1 Schema Migration Fix

**Issue:** Database schema missing `pattern_type` and `rosette_geometry` columns  
**Error:** `sqlite3.OperationalError: no such column: pattern_type`  
**Impact:** All RMOS rosette endpoints return 500 Internal Server Error  
**Priority:** 🔴 CRITICAL - Blocks N11.1, N12, N14 rosette functionality  
**Date:** December 10, 2025

---

## Problem Statement

The N11.1 rosette scaffolding added two columns to the `patterns` table:
- `pattern_type` (distinguishes 'rosette' vs 'generic' patterns)
- `rosette_geometry` (stores RMOS Studio rosette definitions)

These columns were documented in `docs/N11_1_ROSETTE_SCAFFOLDING_QUICKREF.md` but were **never added** to the database schema initialization code in `services/api/app/core/rmos_db.py`.

**Result:** Any code calling `store.list_by_type('rosette')` crashes with "no such column" error.

---

## File to Patch

**Location:** `services/api/app/core/rmos_db.py`

**Function:** `_initialize_schema()` (lines 83-178)

---

## CUT & PASTE PATCH

### Step 1: Update Patterns Table Schema

**Find this code block (lines 108-122):**

```python
            # Patterns table (rosette designs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    ring_count INTEGER NOT NULL,
                    geometry_json TEXT NOT NULL,
                    strip_family_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT
                )
            """)
```

**Replace with:**

```python
            # Patterns table (rosette designs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    ring_count INTEGER NOT NULL,
                    geometry_json TEXT NOT NULL,
                    strip_family_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    pattern_type TEXT NOT NULL DEFAULT 'generic',
                    rosette_geometry TEXT
                )
            """)
```

### Step 2: Add Migration Logic for Existing Databases

**Find this code block (lines 151-156):**

```python
            # Indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_name 
                ON patterns(name)
            """)
```

**Insert BEFORE the indexes section (after line 122):**

```python
            
            # N11.1 Migration: Add columns if they don't exist (for existing databases)
            cursor.execute("PRAGMA table_info(patterns)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            if 'pattern_type' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE patterns 
                    ADD COLUMN pattern_type TEXT NOT NULL DEFAULT 'generic'
                """)
                logger.info("Applied N11.1 migration: added pattern_type column")
            
            if 'rosette_geometry' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE patterns 
                    ADD COLUMN rosette_geometry TEXT
                """)
                logger.info("Applied N11.1 migration: added rosette_geometry column")
```

### Step 3: Add Pattern Type Index

**Find this code block (lines 166-169):**

```python
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_joblogs_created 
                ON joblogs(created_at DESC)
            """)
```

**Insert AFTER (add new index for pattern_type):**

```python
            
            # N11.1: Pattern type index for efficient filtering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_pattern_type 
                ON patterns(pattern_type)
            """)
```

---

## Complete Patched Function

For reference, here's the complete updated `_initialize_schema()` function:

<details>
<summary>Click to expand full function</summary>

```python
    def _initialize_schema(self):
        """
        Create database tables if they don't exist.
        
        Schema includes:
        - patterns: Rosette pattern definitions (N11.1: pattern_type, rosette_geometry)
        - strip_families: Material strip configurations
        - joblogs: Manufacturing run records
        - schema_version: Migration tracking
        """
        with self.get_connection(row_factory=False) as conn:
            cursor = conn.cursor()
            
            # Schema version tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Patterns table (rosette designs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    ring_count INTEGER NOT NULL,
                    geometry_json TEXT NOT NULL,
                    strip_family_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT,
                    pattern_type TEXT NOT NULL DEFAULT 'generic',
                    rosette_geometry TEXT
                )
            """)
            
            # N11.1 Migration: Add columns if they don't exist (for existing databases)
            cursor.execute("PRAGMA table_info(patterns)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            if 'pattern_type' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE patterns 
                    ADD COLUMN pattern_type TEXT NOT NULL DEFAULT 'generic'
                """)
                logger.info("Applied N11.1 migration: added pattern_type column")
            
            if 'rosette_geometry' not in existing_columns:
                cursor.execute("""
                    ALTER TABLE patterns 
                    ADD COLUMN rosette_geometry TEXT
                """)
                logger.info("Applied N11.1 migration: added rosette_geometry column")
            
            # Strip families table (material configurations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strip_families (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    strip_width_mm REAL NOT NULL,
                    strip_thickness_mm REAL NOT NULL,
                    material_type TEXT NOT NULL,
                    strips_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT
                )
            """)
            
            # JobLogs table (manufacturing runs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS joblogs (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    pattern_id TEXT,
                    strip_family_id TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds REAL,
                    parameters_json TEXT NOT NULL,
                    results_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pattern_id) REFERENCES patterns(id),
                    FOREIGN KEY (strip_family_id) REFERENCES strip_families(id)
                )
            """)
            
            # Indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_name 
                ON patterns(name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_strip_family 
                ON patterns(strip_family_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_joblogs_pattern 
                ON joblogs(pattern_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_joblogs_status 
                ON joblogs(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_joblogs_created 
                ON joblogs(created_at DESC)
            """)
            
            # N11.1: Pattern type index for efficient filtering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_patterns_pattern_type 
                ON patterns(pattern_type)
            """)
            
            # Record schema version
            cursor.execute("""
                INSERT OR IGNORE INTO schema_version (version)
                VALUES (?)
            """, (SCHEMA_VERSION,))
            
            conn.commit()
            logger.info("RMOS database schema initialized")
```

</details>

---

## Testing the Patch

### 1. Delete Existing Database (Fresh Start)

```powershell
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api"
Remove-Item data\rmos.db -ErrorAction SilentlyContinue
```

### 2. Apply the Patch

Make the code changes above in `services/api/app/core/rmos_db.py`

### 3. Restart Server

```powershell
# Stop current server (Ctrl+C)
# Restart
uvicorn app.main:app --reload --port 8000
```

### 4. Verify Schema

```powershell
# Check columns exist
python -c "import sqlite3; conn = sqlite3.connect('data/rmos.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(patterns)'); print([row[1] for row in cursor.fetchall()])"
```

**Expected output:** Should include `'pattern_type'` and `'rosette_geometry'`

### 5. Test Endpoint

```powershell
curl http://localhost:8000/api/rmos/rosette/patterns
```

**Expected:** `{"patterns":[]}`  
**Before patch:** `Internal Server Error`

### 6. Run RMOS Tests

```powershell
.\scripts\Test-RMOS-Sandbox.ps1
```

**Note:** Tests may still have path mismatches (`/api/rosette-patterns` vs `/api/rmos/patterns`), but the 500 errors should be gone.

---

## Alternative: Manual Database Migration

If you don't want to delete the database, manually apply the migration:

```powershell
cd "c:\Users\thepr\Downloads\Luthiers ToolBox\services\api"

sqlite3 data/rmos.db "
ALTER TABLE patterns ADD COLUMN pattern_type TEXT NOT NULL DEFAULT 'generic';
ALTER TABLE patterns ADD COLUMN rosette_geometry TEXT;
CREATE INDEX IF NOT EXISTS idx_patterns_pattern_type ON patterns(pattern_type);
"
```

Then restart the server.

---

## Related Issues

After this patch is applied, there's a **secondary issue** with test paths:

- Tests expect: `/api/rosette-patterns`
- Router provides: `/api/rmos/patterns` and `/api/rmos/rosette`

This is a **test configuration issue**, not a schema issue. Tests need updating to use correct paths.

---

## Verification Checklist

- [ ] Patch applied to `rmos_db.py`
- [ ] Database recreated or migrated
- [ ] Server restarted
- [ ] Schema verified with PRAGMA
- [ ] Endpoint returns 200 instead of 500
- [ ] No "no such column" errors in logs
- [ ] RMOS tests execute (may fail on other issues)

---

**Status:** ⚠️ AWAITING PATCH APPLICATION

Once applied, this will fix the N14 code validation issue and unblock all N11.1+ rosette functionality.
