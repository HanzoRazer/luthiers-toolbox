# Vision Stack Debt Lock (Micro Patch)

This patch intentionally **locks down legacy vision paths** to prevent further drift.

## What this does

1. Marks legacy modules as **deprecated / slated for removal**
2. Adds a CI guard that **fails builds** if new code imports legacy paths

## Rationale

The canonical vision stack is now:
- app.vision.router
- app.ai.transport.image_client
- RMOS CAS for storage

Legacy modules under:
- app._experimental.ai_graphics

are retained **only for backward compatibility** and must not receive new usage.

## Policy

> No new imports of `app._experimental.ai_graphics.*` are permitted,
> except for explicit re-export shims marked `# DEPRECATED`.
