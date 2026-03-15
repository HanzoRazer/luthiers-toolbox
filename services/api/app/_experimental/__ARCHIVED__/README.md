# Archived Experimental Modules

> Archived: 2026-03-15

This directory contains experimental modules that were audited and found to have
**no active imports** in the codebase. They are preserved here for reference but
should NOT be imported.

## Archived Modules

| Module | Reason | Date |
|--------|--------|------|
| `ai_cam/` | No imports found in codebase | 2026-03-15 |
| `ai_cam_router.py` | Not registered in main.py, no imports | 2026-03-15 |
| `joblog_router.py` | Not registered in main.py, no imports | 2026-03-15 |

## Restoration

If you need to restore any of these modules:

1. Move the module back to `_experimental/`
2. Update imports in dependent files
3. Register routers in `main.py` if applicable
4. Remove from this archive

## Deletion Policy

After 2 release cycles with no restoration requests, these modules may be
permanently deleted to reduce codebase size.
