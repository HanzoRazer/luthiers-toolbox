# N8.7 Migration System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    RMOS Migration System (N8.7)                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        INPUT SOURCES                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  data/rmos_legacy/                                              │
│  ├── patterns/*.json          (Rosette pattern definitions)     │
│  ├── strip_families/*.json    (Material strip configurations)   │
│  └── joblogs/*.json           (Manufacturing job records)        │
│                                                                  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│               MIGRATION TOOL (rmos_migrate_json_to_sqlite.py)   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Scan directories for JSON files                             │
│  2. Validate required fields per entity type                    │
│  3. Check for duplicate IDs (skip existing)                     │
│  4. Batch insert with transaction rollback on errors            │
│  5. Generate migration statistics                               │
│                                                                  │
│  Options:                                                        │
│  • --dry-run  (validate without writing)                        │
│  • Custom data_dir parameter                                    │
│                                                                  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SQLite DATABASE (rmos.db)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tables:                                                         │
│  ┌────────────────────────────────────────────────────┐        │
│  │ patterns              (id, name, ring_count, ...)  │        │
│  │   ↓ strip_family_id                                │        │
│  ├────────────────────────────────────────────────────┤        │
│  │ strip_families        (id, name, width_mm, ...)    │        │
│  ├────────────────────────────────────────────────────┤        │
│  │ joblogs               (id, job_type, status, ...)  │        │
│  │   ↓ pattern_id, strip_family_id                    │        │
│  ├────────────────────────────────────────────────────┤        │
│  │ schema_version        (version, applied_at)        │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                  │
│  Indexes:                                                        │
│  • idx_patterns_strip_family                                    │
│  • idx_joblogs_pattern                                          │
│  • idx_joblogs_strip_family                                     │
│  • idx_joblogs_status                                           │
│                                                                  │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ├─────────────────────────────────────────────────┐
           │                                                  │
           ▼                                                  ▼
┌──────────────────────────────┐     ┌──────────────────────────────┐
│   AUDIT VALIDATOR            │     │   REPORT GENERATOR           │
│   (rmos_migration_audit.py)  │     │   (rmos_migration_report.py) │
├──────────────────────────────┤     ├──────────────────────────────┤
│                              │     │                              │
│ Validates:                   │     │ Formats:                     │
│ • Schema version             │     │ • JSON (machine-readable)    │
│ • Required tables            │     │ • HTML (visual styling)      │
│ • Indexes                    │     │ • TXT (console-friendly)     │
│ • Data integrity             │     │                              │
│ • Foreign keys               │     │ Includes:                    │
│ • Timestamps                 │     │ • Success rates              │
│ • JSON fields                │     │ • Entity breakdowns          │
│                              │     │ • Error/warning summaries    │
│ Exit: 0=pass, 1=fail         │     │ • Migration timestamps       │
│                              │     │                              │
└──────────────────────────────┘     └──────────────────────────────┘
           │                                      │
           └──────────────┬───────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DASHBOARD API (REST)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GET /api/rmos/stores/migration/status                          │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Returns:                                             │       │
│  │ • Last migration timestamp                           │       │
│  │ • Database info (size, location, schema version)     │       │
│  │ • Entity counts (patterns, families, joblogs)        │       │
│  │ • Recent entities (3 most recent per type)           │       │
│  │ • Validation summary (errors, warnings, status)      │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  GET /api/rmos/stores/migration/history?limit=50                │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Returns:                                             │       │
│  │ • Migration history grouped by date                  │       │
│  │ • Entity counts per migration batch                  │       │
│  │ • Sorted by date (most recent first)                 │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      TESTING & CI/CD                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Local Testing (test_rmos_migration.ps1):                       │
│  1. Create sample JSON                                          │
│  2. Run dry-run migration                                       │
│  3. Run actual migration                                        │
│  4. Verify data via REST API                                    │
│  5. Test duplicate detection                                    │
│  6. Generate reports                                            │
│  7. Run audit validation                                        │
│  8. Test dashboard API                                          │
│  9. Cleanup                                                     │
│                                                                  │
│  GitHub Actions (.github/workflows/rmos_migration.yml):         │
│  • Ubuntu job: Full migration pipeline + verification          │
│  • Windows job: PowerShell syntax validation                   │
│  • Artifacts: Reports (30 days), Database (7 days)             │
│  • Triggers: Push, PR, manual dispatch                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       DATA FLOW SUMMARY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  JSON Files → Migration Tool → SQLite Database                  │
│                                   │                              │
│                                   ├──→ Audit Validator          │
│                                   ├──→ Report Generator         │
│                                   └──→ Dashboard API            │
│                                                                  │
│  All validated by CI/CD pipeline on every push/PR              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Legend:
  →   Data flow
  ↓   Foreign key relationship
  •   Bullet point / feature
```

## Component Interactions

```
User Workflow:
┌──────────┐     ┌───────────────┐     ┌──────────┐     ┌──────────┐
│ Prepare  │────▶│ Run Migration │────▶│ Validate │────▶│ Monitor  │
│ JSON     │     │ (with stats)  │     │ (audit)  │     │ (API)    │
└──────────┘     └───────────────┘     └──────────┘     └──────────┘
                        │
                        ▼
                  ┌───────────┐
                  │ Generate  │
                  │ Reports   │
                  └───────────┘

CI/CD Workflow:
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Push to  │────▶│ Generate │────▶│ Migrate  │────▶│ Validate │
│ GitHub   │     │ Test Data│     │ Data     │     │ + Report │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                           │
                                                           ▼
                                                     ┌──────────┐
                                                     │ Upload   │
                                                     │ Artifacts│
                                                     └──────────┘
```

## Technology Stack

```
┌─────────────────────────────────────────────┐
│ Backend                                      │
├─────────────────────────────────────────────┤
│ • Python 3.11+                              │
│ • FastAPI (REST API)                        │
│ • Pydantic (validation)                     │
│ • SQLite3 (database)                        │
│ • pathlib (file operations)                 │
│ • logging (diagnostics)                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Testing                                      │
├─────────────────────────────────────────────┤
│ • PowerShell (Windows-first scripting)      │
│ • GitHub Actions (CI/CD)                    │
│ • curl/Invoke-RestMethod (API testing)      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Storage                                      │
├─────────────────────────────────────────────┤
│ • SQLite (relational database)              │
│ • JSON (input/output formats)               │
│ • HTML/TXT (reports)                        │
└─────────────────────────────────────────────┘
```

## File Size Distribution

```
Migration Tool:       323 lines  ████████████░░░░░░░░  45%
Report Generator:     340 lines  ████████████░░░░░░░░  47%
Audit Validator:      489 lines  █████████████████░░░  68%
Dashboard API:        172 lines  ██████░░░░░░░░░░░░░░  24%
Test Suites:          377 lines  █████████████░░░░░░░  52%
CI Workflow:          280 lines  ████████░░░░░░░░░░░░  39%
Documentation:        500 lines  █████████████░░░░░░░  69%
```

---

**N8.7 Migration System - Complete Architecture Overview**
