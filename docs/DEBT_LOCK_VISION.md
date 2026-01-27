# Vision Stack Debt Lock — RESOLVED

**Status:** RESOLVED (January 27, 2026)

The `_experimental/ai_graphics/` folder has been **deleted entirely**.

## What was done

1. Migrated `rosette_rmos_adapter.py` to deterministic stub (no AI import)
2. Removed `teaching_routes` mount from `main.py`
3. Deleted orphan `test_dalle_advisory.py`
4. Cleaned `_experimental` imports from `test_e2e_workflow_integration.py`
5. Deleted `_experimental/ai_graphics/` folder (30 files)
6. Cleaned legacy breadcrumb comments from canonical modules
7. Updated CI guard to zero-baseline mode (no exceptions)

## Canonical vision stack

- `app.vision.router` — Vision domain endpoints
- `app.ai.transport.image_client` — AI provider abstraction
- RMOS CAS for storage

## Defense-in-depth

The CI guard (`ci/guard_no_legacy_vision_imports.sh`) and FENCE_REGISTRY
forbidden import rules remain active to prevent re-introduction.
