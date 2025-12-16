# Run Artifact UI Panel + Toolpaths Link

## Overview

This bundle adds a **Vue-based UI panel** for browsing, filtering, and inspecting Run Artifacts, plus **deep links** from toolpath responses to their audit records.

**Features:**
- List runs with filters (status, mode, risk level)
- Inspect individual artifacts
- Download artifact JSON
- Link from toolpath responses to audit trail

---

## Prerequisites

This bundle requires:
- **Run Artifact Persistence** — `RunStore`, `RunArtifact` schemas
- **Run Artifact Index + Query API** — `/api/rmos/runs` endpoints

---

## File Structure

```
packages/client/src/
├── api/
│   └── rmosRuns.ts              # NEW: API client
├── stores/
│   └── rmosRunsStore.ts         # NEW: Pinia store
├── components/rmos/
│   ├── RunArtifactPanel.vue     # NEW: List + filters
│   ├── RunArtifactDetail.vue    # NEW: Inspect one artifact
│   └── RunArtifactRow.vue       # NEW: Table row component
└── views/
    └── RmosRunsView.vue         # NEW: Route wrapper
```

---

## Implementation

### 1. API Client

**File:** `packages/client/src/api/rmosRuns.ts`

```typescript
import axios from "axios";

export interface RunIndexItem {
  run_id: string;
  created_at_utc: string;
  status: "OK" | "BLOCKED" | "ERROR";
  mode: string;
  tool_id: string;
  risk_level: string;
  score?: number | null;
  feasibility_sha256: string;
  toolpaths_sha256?: string | null;
  artifact_path: string;
}

export interface RunIndexResponse {
  items: RunIndexItem[];
  next_cursor?: string | null;
}

export async function fetchRuns(params: {
  status?: string;
  mode?: string;
  tool_id_prefix?: string;
  risk_level?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  cursor?: string | null;
}) {
  const res = await axios.get("/api/rmos/runs", { params });
  return res.data as RunIndexResponse;
}

export async function fetchRun(runId: string) {
  const res = await axios.get(`/api/rmos/runs/${runId}`);
  return res.data;
}

export function downloadRun(runId: string) {
  window.open(`/api/rmos/runs/${runId}/download`, "_blank");
}
```

---

### 2. Pinia Store

**File:** `packages/client/src/stores/rmosRunsStore.ts`

```typescript
import { defineStore } from "pinia";
import { fetchRuns, fetchRun, RunIndexItem } from "@/api/rmosRuns";

export const useRmosRunsStore = defineStore("rmosRuns", {
  state: () => ({
    items: [] as RunIndexItem[],
    nextCursor: null as string | null,
    loading: false,
    selected: null as any | null,
    filters: {
      status: "",
      mode: "",
      tool_id_prefix: "",
      risk_level: "",
    },
  }),
  
  actions: {
    async loadFirst(limit = 25) {
      this.loading = true;
      const res = await fetchRuns({
        ...this.cleanFilters(),
        limit,
      });
      this.items = res.items;
      this.nextCursor = res.next_cursor ?? null;
      this.loading = false;
    },
    
    async loadMore(limit = 25) {
      if (!this.nextCursor) return;
      this.loading = true;
      const res = await fetchRuns({
        ...this.cleanFilters(),
        limit,
        cursor: this.nextCursor,
      });
      this.items.push(...res.items);
      this.nextCursor = res.next_cursor ?? null;
      this.loading = false;
    },
    
    async select(runId: string) {
      this.selected = await fetchRun(runId);
    },
    
    cleanFilters() {
      const out: any = {};
      for (const [k, v] of Object.entries(this.filters)) {
        if (v) out[k] = v;
      }
      return out;
    },
  },
});
```

---

### 3. Panel Components

#### Main Panel

**File:** `packages/client/src/components/rmos/RunArtifactPanel.vue`

```vue
<script setup lang="ts">
import { onMounted } from "vue";
import { useRmosRunsStore } from "@/stores/rmosRunsStore";
import RunArtifactRow from "./RunArtifactRow.vue";
import RunArtifactDetail from "./RunArtifactDetail.vue";

const store = useRmosRunsStore();

onMounted(() => {
  store.loadFirst();
});
</script>

<template>
  <div class="rmos-runs">
    <header class="toolbar">
      <select v-model="store.filters.status" @change="store.loadFirst()">
        <option value="">All</option>
        <option value="OK">OK</option>
        <option value="BLOCKED">BLOCKED</option>
        <option value="ERROR">ERROR</option>
      </select>
      
      <select v-model="store.filters.mode" @change="store.loadFirst()">
        <option value="">Any Mode</option>
        <option value="saw">Saw</option>
      </select>
      
      <select v-model="store.filters.risk_level" @change="store.loadFirst()">
        <option value="">Any Risk</option>
        <option value="GREEN">GREEN</option>
        <option value="YELLOW">YELLOW</option>
        <option value="RED">RED</option>
        <option value="UNKNOWN">UNKNOWN</option>
      </select>
    </header>
    
    <table class="runs">
      <thead>
        <tr>
          <th>Time (UTC)</th>
          <th>Status</th>
          <th>Mode</th>
          <th>Tool</th>
          <th>Risk</th>
          <th>Score</th>
        </tr>
      </thead>
      <tbody>
        <RunArtifactRow
          v-for="r in store.items"
          :key="r.run_id"
          :run="r"
          @select="store.select(r.run_id)"
        />
      </tbody>
    </table>
    
    <button v-if="store.nextCursor" @click="store.loadMore()">
      Load more
    </button>
    
    <RunArtifactDetail v-if="store.selected" :artifact="store.selected" />
  </div>
</template>

<style scoped>
.rmos-runs {
  padding: 1rem;
}

.toolbar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.runs {
  width: 100%;
  border-collapse: collapse;
}

.runs th,
.runs td {
  padding: 0.5rem;
  border: 1px solid #ddd;
  text-align: left;
}

.runs tbody tr:hover {
  background: #f5f5f5;
  cursor: pointer;
}
</style>
```

#### Table Row

**File:** `packages/client/src/components/rmos/RunArtifactRow.vue`

```vue
<script setup lang="ts">
defineProps<{ run: any }>();
defineEmits(["select"]);
</script>

<template>
  <tr @click="$emit('select')">
    <td>{{ run.created_at_utc }}</td>
    <td :class="run.status">{{ run.status }}</td>
    <td>{{ run.mode }}</td>
    <td>{{ run.tool_id }}</td>
    <td>{{ run.risk_level }}</td>
    <td>{{ run.score ?? "---" }}</td>
  </tr>
</template>

<style scoped>
.OK {
  color: green;
}
.BLOCKED {
  color: red;
  font-weight: bold;
}
.ERROR {
  color: orange;
}
</style>
```

#### Detail View

**File:** `packages/client/src/components/rmos/RunArtifactDetail.vue`

```vue
<script setup lang="ts">
import { downloadRun } from "@/api/rmosRuns";

defineProps<{ artifact: any }>();
</script>

<template>
  <aside class="run-detail">
    <h3>Run {{ artifact.run_id }}</h3>
    
    <p><strong>Status:</strong> {{ artifact.status }}</p>
    <p><strong>Mode:</strong> {{ artifact.mode }}</p>
    <p><strong>Tool:</strong> {{ artifact.tool_id }}</p>
    
    <section>
      <h4>Decision</h4>
      <pre>{{ JSON.stringify(artifact.decision, null, 2) }}</pre>
    </section>
    
    <section>
      <h4>Hashes</h4>
      <pre>{{ JSON.stringify(artifact.hashes, null, 2) }}</pre>
    </section>
    
    <section v-if="artifact.outputs?.gcode_text">
      <h4>G-code Preview</h4>
      <pre class="gcode">{{ artifact.outputs.gcode_text.slice(0, 500) }}...</pre>
    </section>
    
    <button @click="downloadRun(artifact.run_id)">
      Download JSON
    </button>
  </aside>
</template>

<style scoped>
.run-detail {
  margin-top: 1rem;
  padding: 1rem;
  border: 1px solid #ccc;
  background: #fafafa;
}

pre {
  background: #f0f0f0;
  padding: 0.5rem;
  overflow-x: auto;
  font-size: 0.85rem;
}

.gcode {
  max-height: 200px;
  overflow-y: auto;
}

button {
  margin-top: 1rem;
}
</style>
```

---

### 4. View + Routing

**File:** `packages/client/src/views/RmosRunsView.vue`

```vue
<template>
  <div class="rmos-runs-view">
    <h1>Run Artifacts</h1>
    <RunArtifactPanel />
  </div>
</template>

<script setup lang="ts">
import RunArtifactPanel from "@/components/rmos/RunArtifactPanel.vue";
</script>

<style scoped>
.rmos-runs-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}
</style>
```

#### Add Route

In your router configuration:

```typescript
{
  path: "/rmos/runs",
  name: "RmosRuns",
  component: () => import("@/views/RmosRunsView.vue"),
}
```

---

## Toolpaths Response Link

The toolpath endpoint already returns run metadata:

```json
{
  "_run_id": "abc123...",
  "_run_artifact_path": "/data/runs/rmos/2025-12-15/abc123.json",
  "_hashes": {
    "feasibility_sha256": "...",
    "toolpaths_sha256": "...",
    "gcode_sha256": "..."
  }
}
```

### Client-Side Integration

In any toolpath UI component:

```vue
<template>
  <!-- After successful toolpath generation -->
  <div v-if="response._run_id" class="run-link">
    <router-link :to="`/rmos/runs?run_id=${response._run_id}`">
      View Run Artifact
    </router-link>
  </div>
  
  <!-- On BLOCKED (409) error -->
  <div v-if="error?.run_id" class="error-audit">
    <p>Generation blocked: {{ error.decision.block_reason }}</p>
    <router-link :to="`/rmos/runs?run_id=${error.run_id}`">
      View Audit Trail
    </router-link>
  </div>
</template>
```

### UX Convention

| Scenario | Action |
|----------|--------|
| Success (200) | Show "View Run" link next to result |
| Blocked (409) | Show "View Audit" button in error toast |
| Error (500) | Show "View Error" link for debugging |

---

## User Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OPERATOR WORKFLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. Generate Toolpaths                                                     │
│      └── POST /api/rmos/toolpaths                                          │
│          └── Response includes _run_id                                     │
│                                                                             │
│   2. View Run Artifact (optional)                                           │
│      └── Click "View Run" link                                             │
│          └── Opens /rmos/runs?run_id=xxx                                   │
│              └── Shows full artifact with hashes                           │
│                                                                             │
│   3. Browse All Runs                                                        │
│      └── Navigate to /rmos/runs                                            │
│          └── Filter by status, mode, risk level                            │
│              └── Click row to inspect                                      │
│                  └── Download JSON for audit                               │
│                                                                             │
│   4. Investigate Blocked Runs                                               │
│      └── Filter: status=BLOCKED, risk_level=RED                            │
│          └── Click to see decision details                                 │
│              └── "Why was this blocked?"                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **No state drift** | UI reads same artifacts backend writes |
| **Auditable by design** | Every run inspectable and downloadable |
| **Clone-safe** | File store works in sandbox, monorepo, standalone |
| **Extensible** | Can add diff, compare, approval workflows later |

---

## CSS Classes Reference

For styling status indicators:

```css
/* Status colors */
.OK { color: green; }
.BLOCKED { color: red; font-weight: bold; }
.ERROR { color: orange; }

/* Risk level colors */
.GREEN { color: green; }
.YELLOW { color: #cc9900; }
.RED { color: red; font-weight: bold; }
.UNKNOWN { color: gray; font-style: italic; }
```

---

## Next Recommended Step

**Run Diff Viewer**

Compare two run artifacts by hashes to answer "what changed and why?" in seconds:
- Side-by-side feasibility comparison
- Hash verification
- Delta highlighting
