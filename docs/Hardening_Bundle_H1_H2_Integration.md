# Hardening Bundle H1 + H2 — Integration Location

**Document Version:** 1.0
**Date:** 2025-12-23
**Status:** Implemented

---

## Overview

### H1 — Snapshot Store Hardening

**Purpose:** Harden the Art Studio snapshot store against security and reliability issues.

| Protection | Threat Mitigated |
|------------|------------------|
| Path traversal validation | `../secrets` or encoded traversal attacks |
| Atomic writes | Partial writes / race corruption |
| Custom SnapshotIdError | Clean error handling in routes |

### H2 — Log Viewer Cursor Pagination

**Purpose:** Scale the RMOS Log Viewer as run volume grows.

| Feature | Benefit |
|---------|---------|
| Cursor-based pagination | Scales better than offset |
| Server-side filters | mode, tool_id, risk_level, status, source |
| Exponential backoff | Reduces server load on errors |
| Soft refresh | Prepend new runs while at top |

---

## H1 Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `services/api/app/art_studio/services/rosette_snapshot_store.py` | MODIFIED | Added SnapshotIdError, validate_snapshot_id(), _safe_snapshot_path(), _atomic_write_text() |
| `services/api/app/art_studio/api/rosette_snapshot_routes.py` | MODIFIED | Catch SnapshotIdError → HTTP 400 |

### H1 Key Components

```python
# rosette_snapshot_store.py

class SnapshotIdError(ValueError):
    """Raised when snapshot_id is invalid or unsafe."""

def validate_snapshot_id(snapshot_id: str) -> str:
    """
    - ASCII alnum + _ -
    - max 64 chars
    - no path separators
    """

def _safe_snapshot_path(snapshot_id: str) -> Path:
    """Path containment check - prevents directory traversal."""

def _atomic_write_text(target_path: Path, text: str) -> None:
    """temp file + fsync + os.replace"""
```

---

## H2 Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `services/api/app/rmos/runs_v2/store.py` | MODIFIED | Added query_recent() with cursor pagination |
| `services/api/app/rmos/api/logs_routes.py` | MODIFIED | Added /recent/v2 endpoint with cursor support |
| `packages/client/src/api/rmosLogsClient.ts` | NEW | Frontend client with cursor + backoff |
| `packages/client/src/components/rmos/RmosLogViewerPanel.vue` | NEW | Enhanced log viewer with H2.1-H2.10 features |

### H2 Key Components

```python
# store.py

def query_recent(
    *,
    limit: int = 50,
    cursor: Optional[str] = None,  # "<created_at_utc>|<run_id>"
    mode: Optional[str] = None,
    tool_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Returns {"items": [...], "next_cursor": "..." | None}"""
```

```typescript
// rmosLogsClient.ts

export async function fetchRecentLogs(params: FetchLogsParams): Promise<RecentLogsResponse>
export async function fetchNextPage(prevResponse, params): Promise<RecentLogsResponse>
export function resetBackoff(): void
export function incrementBackoff(): number
```

---

## API Endpoints

### H1 — Snapshot Routes (existing, hardened)

| Method | Path | Handler |
|--------|------|---------|
| POST | `/api/art/rosette/snapshots/export` | `export_snapshot` |
| POST | `/api/art/rosette/snapshots/import` | `import_snapshot` |
| GET | `/api/art/rosette/snapshots/{snapshot_id}` | `get_snapshot` |
| DELETE | `/api/art/rosette/snapshots/{snapshot_id}` | `remove_snapshot` |
| GET | `/api/art/rosette/snapshots/` | `list_all_snapshots` |

### H2 — Logs Routes (new endpoint)

| Method | Path | Handler |
|--------|------|---------|
| GET | `/api/rmos/logs/recent` | `logs_recent` (legacy offset) |
| GET | `/api/rmos/logs/recent/v2` | `logs_recent_v2` (cursor-based) |
| GET | `/api/rmos/logs/{run_id}` | `logs_get_run` |

---

## H2 Micro Bundles Implemented

| Bundle | Feature | Component |
|--------|---------|-----------|
| H2.1 | Load more button | `RmosLogViewerPanel.vue` |
| H2.2 | Infinite scroll | `onScroll()` near-bottom detection |
| H2.3 | Sentinel row | "Loading older..." / "End of list" |
| H2.4 | Jump to newest | `jumpToNewest()` button |
| H2.5 | New runs badge | Badge with count, pulsing animation |
| H2.6 | Soft refresh | `softRefresh()` prepends at top |
| H2.7 | Soft refresh cap | `overflowCount` with "+N more" row |
| H2.8 | Cap UI setting | Dropdown 10/25/50 |
| H2.9 | Per-filter cap | `getSoftCap(mode, source)` |
| H2.10 | Reset cap button | `resetCapForFilter()` |

---

## Cursor Format

```
<created_at_utc>|<run_id>
```

Example:
```
2025-12-23T10:30:00.000Z|run_abc123def456
```

**Semantics:**
- Newest first ordering
- Cursor represents "last seen" item
- Next page returns items strictly older than cursor

---

## Backoff Policy

| State | Interval |
|-------|----------|
| Initial | 5000ms |
| After error | Previous × 2 |
| Maximum | 30000ms |
| On success | Reset to 5000ms |

---

## Frontend Integration

### Vue Component Usage

```vue
<script setup lang="ts">
import RmosLogViewerPanel from "@/components/rmos/RmosLogViewerPanel.vue";
</script>

<template>
  <RmosLogViewerPanel
    :initial-limit="50"
    @select="handleSelectRun"
  />
</template>
```

### TypeScript Client Usage

```typescript
import {
  fetchRecentLogs,
  fetchNextPage,
  checkForNewerRuns,
} from "@/api/rmosLogsClient";

// Initial fetch
const response = await fetchRecentLogs({
  limit: 50,
  mode: "art_studio",
  risk_level: "RED",
});

// Load more
const nextPage = await fetchNextPage(response, { limit: 50 });

// Check for updates
const { count, newest } = await checkForNewerRuns(
  response.entries[0].created_at_utc
);
```

---

## Error Handling Matrix

### H1 — Snapshot Errors

| Scenario | HTTP Status | Detail |
|----------|-------------|--------|
| Invalid snapshot_id (traversal, bad chars) | 400 | "invalid snapshot_id" |
| snapshot_id too long (>64 chars) | 400 | "snapshot_id too long (max 64)" |
| Snapshot not found | 404 | "Snapshot not found" |

### H2 — Logs Errors

| Scenario | HTTP Status | Detail |
|----------|-------------|--------|
| Invalid cursor format | 200 | Treats as no cursor (returns from start) |
| Run not found | 404 | "Run {run_id} not found" |

---

## Verification Checklist

### H1 Verification

```bash
# Valid flow
POST /api/art/rosette/snapshots/export → 200

# Path traversal → 400
GET /api/art/rosette/snapshots/../secrets → 400
GET /api/art/rosette/snapshots/%2e%2e%2f → 400

# Too long → 400
GET /api/art/rosette/snapshots/aaaa...64+ chars → 400

# Not found → 404
GET /api/art/rosette/snapshots/nonexistent → 404
```

### H2 Verification

```bash
# Cursor pagination
GET /api/rmos/logs/recent/v2?limit=10 → 200 + next_cursor
GET /api/rmos/logs/recent/v2?cursor=... → 200 (next page)

# Filters
GET /api/rmos/logs/recent/v2?mode=art_studio&risk_level=RED → 200

# Frontend
# - Open log viewer
# - Scroll to bottom → triggers infinite scroll
# - Wait for new runs → badge appears
# - Click badge → jumps to top + refreshes
```

---

## Related Documents

- `docs/RMOS_Binding_Bundle_Integration.md` — Art Studio Binding Bundle
- `tests/verification/VERIFICATION_INSTRUCTIONS.md` — Test procedures

---

*End of Document*
