# AI Root Files Cleanup Audit

**Date:** December 16, 2025
**Action:** Archive redundant repo-root AI files

## Summary

11 Python files at the repository root were identified as redundant copies of files that have canonical locations within the `services/api/app/` directory structure. These files were moved to this archive directory pending deletion.

## Files Removed from Root

| Removed File | Canonical Location | Notes |
|--------------|-------------------|-------|
| `ai_core_generator_constraints.py` | `_experimental/ai_core/generator_constraints.py` | AI generation constraints |
| `ai_graphics_schemas.py` | `_experimental/ai_graphics/schemas/ai_schemas.py` | AI graphics schemas |
| `ai_graphics_schemas_ai_schemas.py` | `_experimental/ai_graphics/schemas/ai_schemas.py` | Duplicate schema file |
| `ai_graphics_sessions.py` | `_experimental/ai_graphics/sessions.py` | Session management |
| `ai_rmos_generator_snapshot.py` | `rmos/api_ai_snapshots.py` | Generator snapshots |
| `art_studio_constraint_search.py` | `rmos/services/constraint_search.py` | Constraint search |
| `constraint_profiles_ai.py` | `rmos/constraint_profiles.py` | Constraint profiles |
| `rmos_ai_analytics.py` | `_experimental/analytics/` | AI analytics (merged) |
| `rmos_logging_ai.py` | `rmos/logging_ai.py` | AI logging |
| `routers_ai_cam_router.py` | `_experimental/ai_cam_router.py` | AI CAM router |
| `schemas_logs_ai.py` | `rmos/schemas_logs_ai.py` | Log schemas |

## Verification Steps Performed

1. **Import search:** Confirmed no Python imports reference the repo-root copies
   ```bash
   rg "^(from|import)\s+ai_core_generator|ai_graphics_|ai_rmos_" --type py
   # Result: No matches found
   ```

2. **Canonical equivalents verified:** All 11 files have active equivalents in proper locations

3. **References found only in:**
   - `.gitignore` (listing files to ignore)
   - Documentation files (describing deprecated files)

## Canonical Import Paths

Applications should import from these locations:

```python
# AI Core
from app._experimental.ai_core.generator_constraints import ...

# AI Graphics
from app._experimental.ai_graphics.schemas.ai_schemas import ...
from app._experimental.ai_graphics.sessions import ...

# RMOS AI
from app.rmos.constraint_profiles import ...
from app.rmos.logging_ai import ...
from app.rmos.schemas_logs_ai import ...

# AI CAM
from app._experimental.ai_cam_router import ...
```

## Next Steps

1. **Stage 1 (this commit):** Files moved to archive
2. **Stage 2 (next commit):** Delete this archive directory after tests pass

## Related Documentation

- `ORPHAN_AUDIT_2025-12-14.md` - Previous audit identifying these as orphans
- `AI_SCHEMA_NAMESPACE_REPORT.md` - Schema namespace documentation
- `DEPRECATED_SUBSYSTEMS.md` - Deprecation tracking
