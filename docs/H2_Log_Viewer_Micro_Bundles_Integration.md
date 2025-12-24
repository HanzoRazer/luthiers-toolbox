# H2 Log Viewer Micro Bundles — Integration Location

**Document Version:** 1.0
**Date:** 2025-12-23
**Status:** Implemented

---

## Overview

### What It Does

**RMOS Log Viewer Enhancements** — Progressive UX improvements for the run log viewer:

- Cursor-based pagination (scales with run volume)
- Infinite scroll with selection pinning
- Soft refresh with configurable cap
- New runs badge with jump-to-newest
- Per-filter settings persistence

---

## Inputs

| Component | Inputs |
|-----------|--------|
| `query_recent()` | `limit`, `cursor`, `mode`, `tool_id`, `risk_level`, `status`, `source` |
| `/recent/v2` endpoint | Same as above via query params |
| `RmosLogViewerPanel.vue` | `initialLimit` prop |
| `rmosLogsClient.ts` | `FetchLogsParams` object |

---

## Outputs

| Component | Outputs |
|-----------|---------|
| `query_recent()` | `{"items": [...], "next_cursor": "..."}` |
| `/recent/v2` endpoint | `RecentLogsResponseV2` (entries, next_cursor, has_more, filters_applied) |
| `RmosLogViewerPanel.vue` | `@select` event with `RunLogEntry` |

---

## Connection Point

**RMOS Runs v2 Subsystem** — `app/rmos/runs_v2/` + `app/rmos/api/`

---

## Pattern

- [x] **Store → Route → Client → Component** (full stack)
- [x] **Cursor pagination** (not offset)
- [x] **localStorage persistence** (soft cap per filter)

```
Store:     runs_v2/store.py (query_recent)
Route:     api/logs_routes.py (/recent/v2)
Client:    api/rmosLogsClient.ts
Component: components/rmos/RmosLogViewerPanel.vue
```

---

## Dependencies

### Backend — store.py

```python
from .schemas import RunArtifact
# Uses existing list_runs() internally
```

### Backend — logs_routes.py

```python
from ..runs_v2.store import query_recent
from pydantic import BaseModel, Field
```

### Frontend — rmosLogsClient.ts

```typescript
// No external dependencies beyond fetch API
```

### Frontend — RmosLogViewerPanel.vue

```typescript
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import {
  fetchRecentLogs,
  checkForNewerRuns,
  getSoftCap,
  setSoftCap,
  resetSoftCap,
  getBackoffMs,
} from "@/api/rmosLogsClient";
```

---

## Who Calls It

- [x] **HTTP endpoint (frontend)**
- [x] **Vue component (user interaction)**
- [ ] Another Python module
- [ ] Background job

---

## Directory Structure

```
services/api/app/rmos/
├── runs_v2/
│   └── store.py                    ← MODIFIED (added query_recent)
└── api/
    └── logs_routes.py              ← MODIFIED (added /recent/v2)

packages/client/src/
├── api/
│   └── rmosLogsClient.ts           ← NEW
└── components/rmos/
    └── RmosLogViewerPanel.vue      ← NEW
```

---

## Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `runs_v2/store.py` | MODIFIED | Added `query_recent()` with cursor pagination |
| `api/logs_routes.py` | MODIFIED | Added `/recent/v2` endpoint, `RecentLogsResponseV2` |
| `api/rmosLogsClient.ts` | NEW | Frontend client with backoff + cursor support |
| `components/rmos/RmosLogViewerPanel.vue` | NEW | Enhanced log viewer with H2.1-H2.10 |

---

## Micro Bundle Implementation Details

### H2.1 — Load More Button + Selection Pinning

**Purpose:** Cursor-based paging with UI feedback and selection stability.

| Element | Location |
|---------|----------|
| Load more button | Lines 141-147 |
| `loadMore()` function | Lines 320-363 |
| Selection pinning | `data-run-id` attribute + scroll logic |

```vue
<div v-if="hasMore && !loadingMore" class="load-more-row">
  <button class="btn" @click="loadMore">Load More</button>
</div>
```

---

### H2.2 — Infinite Scroll

**Purpose:** Auto-load when scrolling near bottom, pause when typing or viewing details.

| Element | Location |
|---------|----------|
| Scroll handler | Lines 448-464 (`onScroll()`) |
| Pause on typing | Line 66 (`@input="onFilterInput"`) |
| Pause on details | Line 274 (`isPollingPaused = true`) |

```typescript
function onScroll() {
  const nearBottom = scrollHeight - scrollTop - clientHeight < 100;
  if (nearBottom) loadMore();
}
```

---

### H2.3 — Sentinel Row

**Purpose:** Visual indicator at bottom of list.

| State | Display |
|-------|---------|
| Loading | "Loading older..." |
| Has more | "Load more" (clickable) |
| End of list | "End of list" (italic) |

```vue
<tr v-if="hasMore || loadingMore" class="sentinel-row">
  <td colspan="7" class="sentinel-cell">
    <span v-if="loadingMore">Loading older...</span>
    <span v-else-if="hasMore" @click="loadMore">Load more</span>
  </td>
</tr>
```

---

### H2.4 — Jump to Newest

**Purpose:** Quick navigation to top + immediate refresh.

| Element | Location |
|---------|----------|
| Button | Lines 17-25 |
| `jumpToNewest()` | Lines 365-376 |

```typescript
async function jumpToNewest() {
  tableContainerRef.value.scrollTop = 0;
  newRunsCount.value = 0;
  await refresh();
}
```

---

### H2.5 — New Runs Badge

**Purpose:** Notify user of new runs without disrupting current view.

| Element | Location |
|---------|----------|
| Badge button | Lines 9-15 |
| Pulsing animation | CSS lines 548-562 |
| Poll detection | Lines 415-439 |

```vue
<button v-if="newRunsCount > 0" class="badge-btn" @click="jumpToNewest">
  {{ newRunsCount }} new
</button>
```

---

### H2.6 — Soft Refresh

**Purpose:** Prepend new runs at top without losing scroll position.

| Element | Location |
|---------|----------|
| `softRefresh()` | Lines 378-413 |
| Auto-trigger | Lines 406-408 (when at top) |

```typescript
async function softRefresh() {
  const newEntries = response.entries.filter(
    (e) => e.created_at_utc > newestTimestamp.value
  );
  entries.value = [...newEntries, ...entries.value];
}
```

---

### H2.7 — Soft Refresh Cap

**Purpose:** Prevent overwhelming prepend when many new runs arrive.

| Element | Location |
|---------|----------|
| Overflow row | Lines 87-90 |
| Cap logic | Lines 381-385 |

```vue
<div v-if="overflowCount > 0" class="overflow-row" @click="jumpToNewest">
  +{{ overflowCount }} more runs available
</div>
```

---

### H2.8 — Cap UI Setting

**Purpose:** User-configurable soft refresh limit.

| Element | Location |
|---------|----------|
| Dropdown | Lines 69-73 |
| Save watcher | Lines 283-285 |

```vue
<select v-model="softCapValue" class="cap-select">
  <option :value="10">Cap: 10</option>
  <option :value="25">Cap: 25</option>
  <option :value="50">Cap: 50</option>
</select>
```

---

### H2.9 — Per-Filter Cap

**Purpose:** Remember cap setting for each mode/source combination.

| Element | Location |
|---------|----------|
| `getSoftCap()` | rmosLogsClient.ts lines 158-162 |
| `setSoftCap()` | rmosLogsClient.ts lines 167-171 |
| Load on mount | Lines 477-480 |
| Reload on filter change | Lines 484-490 |

**localStorage Key Format:**
```
rmos_logs_soft_cap_{mode}_{source}
```

---

### H2.10 — Reset Cap Button

**Purpose:** Clear custom cap and return to default.

| Element | Location |
|---------|----------|
| Reset button | Lines 75-78 |
| `resetCapForFilter()` | Lines 287-291 |
| `resetSoftCap()` | rmosLogsClient.ts lines 176-180 |

```vue
<button class="btn small" @click="resetCapForFilter">Reset</button>
```

---

## API Endpoints

| Method | Path | Handler | Bundle |
|--------|------|---------|--------|
| GET | `/api/rmos/logs/recent` | `logs_recent` | Legacy (offset) |
| GET | `/api/rmos/logs/recent/v2` | `logs_recent_v2` | H2 (cursor) |
| GET | `/api/rmos/logs/{run_id}` | `logs_get_run` | Details |

---

## Cursor Format

```
<created_at_utc>|<run_id>
```

**Example:**
```
2025-12-23T14:30:00.000000+00:00|run_abc123def456
```

**Semantics:**
- Ordering: newest first
- Cursor points to last returned item
- Next page returns items strictly older than cursor

---

## Backoff Policy

| Condition | Interval |
|-----------|----------|
| Initial | 5,000 ms |
| After error | Previous × 2 |
| Maximum | 30,000 ms |
| On success | Reset to 5,000 ms |

**Client functions:**
```typescript
resetBackoff()      // Call on success
incrementBackoff()  // Call on error
getBackoffMs()      // Get current interval
```

---

## localStorage Keys

| Key Pattern | Purpose |
|-------------|---------|
| `rmos_logs_soft_cap_all_all` | Default cap (no filters) |
| `rmos_logs_soft_cap_art_studio_all` | Cap for mode=art_studio |
| `rmos_logs_soft_cap_all_manual` | Cap for source=manual |
| `rmos_logs_soft_cap_saw_workflow` | Cap for mode=saw, source=workflow |

---

## Component Usage

### Basic Usage

```vue
<script setup lang="ts">
import RmosLogViewerPanel from "@/components/rmos/RmosLogViewerPanel.vue";
</script>

<template>
  <RmosLogViewerPanel :initial-limit="50" />
</template>
```

### With Selection Handler

```vue
<script setup lang="ts">
import RmosLogViewerPanel from "@/components/rmos/RmosLogViewerPanel.vue";
import type { RunLogEntry } from "@/api/rmosLogsClient";

function handleSelect(entry: RunLogEntry) {
  console.log("Selected run:", entry.run_id);
  // Navigate to detail view, show in sidebar, etc.
}
</script>

<template>
  <RmosLogViewerPanel
    :initial-limit="100"
    @select="handleSelect"
  />
</template>
```

---

## Client Usage

### Fetch First Page

```typescript
import { fetchRecentLogs } from "@/api/rmosLogsClient";

const response = await fetchRecentLogs({
  limit: 50,
  mode: "art_studio",
  risk_level: "RED",
});

console.log(response.entries);       // RunLogEntry[]
console.log(response.next_cursor);   // "2025-12-23T...|run_..."
console.log(response.has_more);      // true/false
```

### Fetch Next Page

```typescript
const nextPage = await fetchRecentLogs({
  limit: 50,
  cursor: response.next_cursor,
  mode: "art_studio",
  risk_level: "RED",
});
```

### Check for Newer Runs

```typescript
import { checkForNewerRuns } from "@/api/rmosLogsClient";

const { count, newest } = await checkForNewerRuns(
  "2025-12-23T14:00:00Z",
  { mode: "art_studio" }
);

if (count > 0) {
  console.log(`${count} new runs since last check`);
}
```

---

## Verification Checklist

| Test | Expected |
|------|----------|
| Load initial page | 50 entries, next_cursor present |
| Click "Load More" | Appends next page, selection stays visible |
| Scroll to bottom | Auto-loads next page |
| Type in filter input | Polling pauses |
| Open run details | Polling pauses |
| Wait for new runs | Badge appears with count |
| Click badge | Jumps to top, refreshes |
| At top with new runs | Auto-prepends (up to cap) |
| Many new runs (>cap) | Shows "+N more" row |
| Change cap dropdown | Saves to localStorage |
| Change filter | Loads cap for new filter |
| Click Reset | Clears localStorage, resets to 25 |

---

## Related Documents

- `docs/Hardening_Bundle_H1_H2_Integration.md` — Combined H1+H2 overview
- `docs/RMOS_Binding_Bundle_Integration.md` — Art Studio Binding Bundle
- `tests/verification/VERIFICATION_INSTRUCTIONS.md` — Test procedures

---

*End of Document*
