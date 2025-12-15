# 🚨 CRITICAL: .gitignore Over-Scoping Report

**Date:** December 14, 2025  
**Discovered During:** Orphan File Migration Audit  
**Severity:** **CRITICAL** — Production code being ignored

---

## Executive Summary

The current `.gitignore` contains **unanchored patterns** that are inadvertently blocking vital backend code from being committed. This would cause CI failures and missing functionality in production.

**136 files in `services/api/app/` are currently IGNORED** (not just untracked).

---

## Root Cause

Git's pattern matching treats `data/` as "any folder named data anywhere in the tree", not "the root-level data folder". The patterns need to be **anchored** with a leading `/` to match only root-level directories.

| Current Pattern | Matches | Should Match |
|-----------------|---------|--------------|
| `data/` | ANY `data/` folder | Only `/data/` at root |
| `tools/` | ANY `tools/` folder | Only `/tools/` at root |
| `Calculators/` | ANY `calculators/` (case-insensitive on Windows) | Only `/Calculators/` at root |
| `schemas_logs_ai.py` | ANY file with this name | Only root-level orphan |

---

## Affected Files (CRITICAL)

### calculators/ — ENTIRE PACKAGE IGNORED
```
services/api/app/calculators/__init__.py
services/api/app/calculators/alternative_temperaments.py  ← Precision Fret System!
services/api/app/calculators/bracing_calc.py
services/api/app/calculators/business/                    ← Business calculators
services/api/app/calculators/fret_slots_export.py
services/api/app/calculators/rosette_calc.py
services/api/app/calculators/saw/                         ← Saw calculators
services/api/app/calculators/saw_bridge.py
services/api/app/calculators/suite/
services/api/app/calculators/tool_profiles.py
services/api/app/calculators/wiring/                      ← Wiring calculators
```

### data/ — DATA MODULES IGNORED
```
services/api/app/data/__init__.py
services/api/app/data/cam_core/
services/api/app/data/cnc_production/
services/api/app/data/tool_library.py
services/api/app/data/validate_tool_library.py
```

### tools/ — TOOL DEFINITIONS IGNORED
```
services/api/app/cam_core/tools/
services/api/app/data_registry/system/tools/
services/api/app/tools/
```

### rmos/ — AI LOGGING SCHEMA IGNORED
```
services/api/app/rmos/schemas_logs_ai.py  ← Required by Phase B+C AI search!
```

### Other
```
services/api/app/workflow/mode_preview_routes.py
services/api/app/services/cam_backup_service.py
```

---

## Evidence

```powershell
# Command to verify which rule is blocking calculators:
git check-ignore -v "services/api/app/calculators/__init__.py"
# Output: .gitignore:129:Calculators/     services/api/app/calculators/__init__.py

# Command to verify data/ blocking:
git check-ignore -v "services/api/app/data/__init__.py"
# Output: .gitignore:109:data/    services/api/app/data/__init__.py

# Command to verify tools/ blocking:
git check-ignore -v "services/api/app/tools/"
# Output: .gitignore:112:tools/   services/api/app/tools/

# Command to verify schemas_logs_ai.py blocking:
git check-ignore -v "services/api/app/rmos/schemas_logs_ai.py"
# Output: .gitignore:254:schemas_logs_ai.py       services/api/app/rmos/schemas_logs_ai.py
```

---

## Recommended Fix

### Option A: Anchor Existing Patterns (Minimal Change)

Change these lines in `.gitignore`:

| Line | Current | Fix To |
|------|---------|--------|
| 109 | `data/` | `/data/` |
| 112 | `tools/` | `/tools/` |
| 129 | `Calculators/` | `/Calculators/` |
| 254 | `schemas_logs_ai.py` | `/schemas_logs_ai.py` |

### Option B: Use Negation Patterns (Defensive)

Keep existing patterns but add explicit un-ignore rules:

```gitignore
# Ensure backend code is NEVER ignored
!services/api/app/**
```

### Option C: Restructure .gitignore (Most Robust)

Group all root-level legacy directory ignores under a clearly labeled section with anchored paths:

```gitignore
# ============================================
# ROOT-LEVEL LEGACY DIRECTORIES ONLY
# (Anchored with / to prevent matching nested paths)
# ============================================
/Archtop/
/Calculators/
/Stratocaster/
/client/
/data/
/migrations/
/server/
/templates/
/tools/
```

---

## Impact If Not Fixed

1. **CI will fail** — Missing `calculators/` package breaks imports
2. **Precision Fret System unavailable** — `alternative_temperaments.py` ignored
3. **Phase B+C AI search broken** — `schemas_logs_ai.py` ignored
4. **Calculator endpoints 404** — Business/Saw/Wiring calculators missing
5. **Tool library endpoints broken** — `data/tool_library.py` ignored

---

## Validation Commands (Post-Fix)

```powershell
# After fixing .gitignore, verify nothing in services/api/app is ignored:
git status --ignored --short | Select-String "^!!" | Select-String "services/api/app" | Select-String -NotMatch "__pycache__"

# Expected output: Empty (only __pycache__ should be ignored)

# Verify calculators are now trackable:
git check-ignore -v "services/api/app/calculators/__init__.py"
# Expected: No output (file is not ignored)
```

---

## Decision Required

**Before proceeding with the migration, the .gitignore must be fixed.**

Please confirm which fix approach you prefer:
- [ ] **Option A:** Anchor patterns (minimal change)
- [ ] **Option B:** Add negation pattern (defensive)
- [ ] **Option C:** Restructure section (most robust)

---

**Awaiting developer confirmation before proceeding.**
