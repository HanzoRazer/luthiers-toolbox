# Phase B+C Integration Instructions

## What's In This Package

This package contains **only the NEW files** for Phase B+C. Your existing Phase A files (ai_core/, cad/, etc.) are already in your repo.

```
services/api/app/
├── rmos/
│   ├── __init__.py              # REPLACE your existing (updated exports)
│   ├── schemas_ai.py            # NEW - Phase B
│   ├── ai_search.py             # NEW - Phase B  
│   ├── api_ai_routes.py         # NEW - Phase B
│   ├── constraint_profiles.py   # REPLACE stub - Phase C (expanded)
│   ├── profile_history.py       # NEW - Phase C
│   ├── api_constraint_profiles.py # NEW - Phase C
│   └── api_profile_history.py   # NEW - Phase C
└── config/
    └── rmos_constraint_profiles.yaml  # NEW - Phase C (14 profiles)

docs/
└── AI_SYSTEM_REHABILITATION_PLAN_v2.md  # Updated plan
```

## Files You Already Have (DO NOT OVERWRITE)

These files exist in your repo and are NOT included in this package:

```
services/api/app/rmos/
├── logging_ai.py          # Your existing - Phase B integrates with it
├── schemas_logs_ai.py     # Your existing
├── ai_policy.py           # Your existing - Phase B uses it
├── api_contracts.py       # Your existing
├── feasibility_scorer.py  # Your existing
├── api_routes.py          # Your existing
├── feasibility_fusion.py  # Your existing
└── feasibility_router.py  # Your existing
```

---

## Step 1: Copy Files

```powershell
# From your repo root, after extracting the zip:

# Copy new rmos files (will replace __init__.py and constraint_profiles.py)
Copy-Item -Path ".\services\api\app\rmos\*" -Destination ".\services\api\app\rmos\" -Force

# Create config directory if needed and copy
New-Item -ItemType Directory -Path ".\services\api\app\config" -Force
Copy-Item -Path ".\services\api\app\config\*" -Destination ".\services\api\app\config\" -Force

# Copy updated docs
Copy-Item -Path ".\docs\*" -Destination ".\docs\" -Force
```

Or manually copy the folders to merge with your existing structure.

---

## Step 2: Wire Routers in main.py

Add these imports near your other router imports:

```python
# Phase B+C: RMOS AI Routes
from app.rmos.api_ai_routes import router as rmos_ai_router
from app.rmos.api_constraint_profiles import router as rmos_profiles_router
from app.rmos.api_profile_history import router as rmos_history_router
```

Add these router registrations (near your other `app.include_router` calls):

```python
# Phase B+C: RMOS AI Routes
app.include_router(rmos_ai_router, prefix="/api/rmos")
app.include_router(rmos_profiles_router, prefix="/api/rmos")
app.include_router(rmos_history_router, prefix="/api/rmos")
```

---

## Step 3: Verify

```powershell
# Start your dev server
cd services/api
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/api/rmos/ai/health
curl http://localhost:8000/api/rmos/profiles
curl http://localhost:8000/api/rmos/profiles/classical
```

Expected responses:
- `/ai/health` → `{"status":"degraded","components":{...}}`  (degraded until ai_core generators wired)
- `/profiles` → List of 14 preset profiles
- `/profiles/classical` → Classical guitar profile details

---

## Step 4: Commit

```powershell
# Stage all changes
git add services/api/app/rmos/
git add services/api/app/config/
git add services/api/app/main.py
git add docs/

# Commit
git commit -m "feat(rmos): Add AI search loop and profile management (Phase B+C)

Phase B - AI Search Loop:
- schemas_ai.py: Request/response models
- ai_search.py: run_constraint_first_search() loop
- api_ai_routes.py: 5 new endpoints

Phase C - Profile Management:
- constraint_profiles.py: YAML-based ProfileStore
- profile_history.py: JSONL change journal
- api_constraint_profiles.py: Profile CRUD (6 endpoints)
- api_profile_history.py: History/rollback (5 endpoints)
- config/rmos_constraint_profiles.yaml: 14 preset profiles

New endpoints:
- POST /api/rmos/ai/constraint-search
- POST /api/rmos/ai/quick-check
- GET  /api/rmos/ai/health
- GET  /api/rmos/profiles
- POST /api/rmos/profiles/{id}/rollback
- ... and 12 more"

# Push
git push origin feature/client-migration
```

---

## New API Endpoints Summary

### Phase B: AI Search (5 endpoints)
```
POST /api/rmos/ai/constraint-search    # Full search
POST /api/rmos/ai/quick-check          # 5-attempt preview
GET  /api/rmos/ai/status/{code}        # Status descriptions
GET  /api/rmos/ai/workflows            # List workflow modes
GET  /api/rmos/ai/health               # Subsystem health
```

### Phase C: Profiles (7 endpoints)
```
GET    /api/rmos/profiles              # List all
GET    /api/rmos/profiles/ids          # List IDs only
GET    /api/rmos/profiles/tags/{tag}   # Filter by tag
GET    /api/rmos/profiles/{id}         # Get one
POST   /api/rmos/profiles              # Create
PUT    /api/rmos/profiles/{id}         # Update
DELETE /api/rmos/profiles/{id}         # Delete
GET    /api/rmos/profiles/{id}/constraints  # Constraints only
```

### Phase C: History (5 endpoints)
```
GET  /api/rmos/profiles/history              # All history
GET  /api/rmos/profiles/history/types        # Change types
GET  /api/rmos/profiles/history/{entry_id}   # Entry detail
GET  /api/rmos/profiles/{id}/history         # Profile history
POST /api/rmos/profiles/{id}/rollback        # Rollback
```

---

## Troubleshooting

**Import errors?**
- Make sure your existing `logging_ai.py` has `new_run_id`, `log_ai_constraint_attempt`, `log_ai_constraint_run_summary`
- Make sure your existing `ai_policy.py` has `clamp_budget_to_policy`, `validate_request_against_policy`

**YAML not loading?**
- Check `RMOS_PROFILE_YAML_PATH` env var or ensure `config/` is in the right location
- Default path: `config/rmos_constraint_profiles.yaml` (relative to working directory)

**Circular imports?**
- The new files use lazy imports with try/except to prevent this
