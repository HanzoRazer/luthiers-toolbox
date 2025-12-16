# Run Diff Viewer

## Overview

This bundle adds a **side-by-side comparison tool** for two Run Artifacts, showing:
- Hash differences (feasibility/toolpaths/gcode/opplan)
- Decision differences (risk level/score/reasons)
- Structured JSON diffs for feasibility, decision, and outputs

**Use cases:**
- "Why is this run blocked now?"
- "Did feasibility change or did toolpaths change?"
- "Are we generating different G-code from the same feasibility?"

---

## Prerequisites

This bundle requires:
- **Run Artifact Query API** — `/api/rmos/runs/{run_id}` endpoint
- **Run Artifact UI Panel** — For navigation context

---

## File Structure

```
packages/client/src/
├── utils/
│   └── jsonDiff.ts              # NEW: Stable JSON diff algorithm
├── components/rmos/
│   └── RunDiffViewer.vue        # NEW: Diff UI
├── views/
│   └── RmosRunsDiffView.vue     # NEW: Route wrapper
└── router/
    └── index.ts                 # UPDATED: Add /rmos/runs/diff route
```

---

## Implementation

### 1. JSON Diff Utility

A simple, dependency-free diff algorithm for comparing JSON objects.

**File:** `packages/client/src/utils/jsonDiff.ts`

```typescript
export type DiffOp = "added" | "removed" | "changed";

export interface DiffItem {
  path: string;    // e.g. "feasibility.saw.rim_speed"
  op: DiffOp;
  a?: any;         // Value in artifact A
  b?: any;         // Value in artifact B
}

function isObject(v: any): boolean {
  return v && typeof v === "object" && !Array.isArray(v);
}

function stableKeys(obj: any): string[] {
  return Object.keys(obj).sort();
}

export function diffJson(
  a: any,
  b: any,
  basePath = "",
  out: DiffItem[] = [],
  maxItems = 2000
): DiffItem[] {
  if (out.length >= maxItems) return out;

  // Exact equality (fast path)
  if (a === b) return out;

  // Type differences
  const ta = Array.isArray(a) ? "array" : typeof a;
  const tb = Array.isArray(b) ? "array" : typeof b;

  if (ta !== tb) {
    out.push({ path: basePath || "$", op: "changed", a, b });
    return out;
  }

  // Primitives
  if (!isObject(a) && !Array.isArray(a)) {
    out.push({ path: basePath || "$", op: "changed", a, b });
    return out;
  }

  // Arrays: compare by index
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) {
      out.push({
        path: (basePath || "$") + ".length",
        op: "changed",
        a: a.length,
        b: b.length,
      });
      if (out.length >= maxItems) return out;
    }

    const n = Math.min(a.length, b.length);
    for (let i = 0; i < n; i++) {
      diffJson(a[i], b[i], `${basePath || "$"}[${i}]`, out, maxItems);
      if (out.length >= maxItems) return out;
    }

    // Trailing items in A (removed)
    if (a.length > n) {
      for (let i = n; i < a.length; i++) {
        out.push({ path: `${basePath || "$"}[${i}]`, op: "removed", a: a[i] });
      }
    }

    // Trailing items in B (added)
    if (b.length > n) {
      for (let i = n; i < b.length; i++) {
        out.push({ path: `${basePath || "$"}[${i}]`, op: "added", b: b[i] });
      }
    }

    return out;
  }

  // Objects: compare by key
  const keys = new Set<string>([...stableKeys(a), ...stableKeys(b)]);

  for (const k of Array.from(keys).sort()) {
    const pa = (a as any)[k];
    const pb = (b as any)[k];
    const p = basePath ? `${basePath}.${k}` : k;
    const hasA = Object.prototype.hasOwnProperty.call(a, k);
    const hasB = Object.prototype.hasOwnProperty.call(b, k);

    if (hasA && !hasB) {
      out.push({ path: p, op: "removed", a: pa });
    } else if (!hasA && hasB) {
      out.push({ path: p, op: "added", b: pb });
    } else {
      diffJson(pa, pb, p, out, maxItems);
    }

    if (out.length >= maxItems) return out;
  }

  return out;
}

export function summarizeDiff(items: DiffItem[]) {
  const counts = { added: 0, removed: 0, changed: 0 };
  for (const it of items) {
    counts[it.op]++;
  }
  return counts;
}
```

---

### 2. Diff Viewer Component

**File:** `packages/client/src/components/rmos/RunDiffViewer.vue`

```vue
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { fetchRun } from "@/api/rmosRuns";
import { diffJson, summarizeDiff, DiffItem } from "@/utils/jsonDiff";

const route = useRoute();

const runAId = ref<string>((route.query.a as string) || "");
const runBId = ref<string>((route.query.b as string) || "");
const loading = ref(false);
const a = ref<any>(null);
const b = ref<any>(null);
const diffs = ref<DiffItem[]>([]);

function pickSections(art: any) {
  // Keep diffs meaningful and bounded
  return {
    decision: art?.decision ?? null,
    hashes: art?.hashes ?? null,
    feasibility: art?.feasibility ?? null,
    opplan: art?.outputs?.opplan_json ?? null,
  };
}

const summary = computed(() => summarizeDiff(diffs.value));

const hashSignals = computed(() => {
  const ha = a.value?.hashes || {};
  const hb = b.value?.hashes || {};
  const keys = [
    "feasibility_sha256",
    "toolpaths_sha256",
    "gcode_sha256",
    "opplan_sha256",
  ];
  return keys.map((k) => ({
    key: k,
    a: ha[k] || "---",
    b: hb[k] || "---",
    same: (ha[k] || null) === (hb[k] || null),
  }));
});

async function load() {
  if (!runAId.value || !runBId.value) return;
  loading.value = true;
  
  a.value = await fetchRun(runAId.value);
  b.value = await fetchRun(runBId.value);
  
  const sa = pickSections(a.value);
  const sb = pickSections(b.value);
  diffs.value = diffJson(sa, sb, "");
  
  loading.value = false;
}

onMounted(load);
</script>

<template>
  <div class="run-diff">
    <header class="toolbar">
      <div>
        <label>Run A</label>
        <input v-model="runAId" placeholder="run_id A" />
      </div>
      <div>
        <label>Run B</label>
        <input v-model="runBId" placeholder="run_id B" />
      </div>
      <button @click="load" :disabled="loading || !runAId || !runBId">
        {{ loading ? "Loading..." : "Compare" }}
      </button>
    </header>

    <!-- Overview -->
    <section v-if="a && b" class="overview">
      <h3>Overview</h3>
      <p>
        <strong>A:</strong> {{ a.run_id }} — {{ a.status }} — {{ a.tool_id }}
        <br />
        <strong>B:</strong> {{ b.run_id }} — {{ b.status }} — {{ b.tool_id }}
      </p>
    </section>

    <!-- Hash Comparison -->
    <section v-if="a && b" class="hashes">
      <h3>Hashes</h3>
      <table>
        <thead>
          <tr>
            <th>Key</th>
            <th>A</th>
            <th>B</th>
            <th>Match</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in hashSignals" :key="h.key">
            <td>{{ h.key }}</td>
            <td><code>{{ h.a.slice(0, 12) }}...</code></td>
            <td><code>{{ h.b.slice(0, 12) }}...</code></td>
            <td>{{ h.same ? "✅" : "❌" }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Diff Summary -->
    <section v-if="a && b" class="summary">
      <h3>Diff Summary</h3>
      <p>
        <span class="added">Added: {{ summary.added }}</span> |
        <span class="removed">Removed: {{ summary.removed }}</span> |
        <span class="changed">Changed: {{ summary.changed }}</span>
      </p>
    </section>

    <!-- Diff Items -->
    <section v-if="a && b && diffs.length" class="diffs">
      <h3>Diff Items</h3>
      <table>
        <thead>
          <tr>
            <th>Path</th>
            <th>Op</th>
            <th>A</th>
            <th>B</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(d, i) in diffs" :key="i" :class="d.op">
            <td><code>{{ d.path }}</code></td>
            <td>{{ d.op }}</td>
            <td><pre>{{ JSON.stringify(d.a, null, 2) }}</pre></td>
            <td><pre>{{ JSON.stringify(d.b, null, 2) }}</pre></td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-if="a && b && !diffs.length" class="no-diff">
      <p>✅ No differences found in decision, hashes, feasibility, or opplan.</p>
    </section>
  </div>
</template>

<style scoped>
.run-diff {
  padding: 1rem;
  max-width: 1400px;
}

.toolbar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  align-items: flex-end;
}

.toolbar div {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.toolbar input {
  width: 280px;
  padding: 0.5rem;
  font-family: monospace;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

th, td {
  padding: 0.5rem;
  border: 1px solid #ddd;
  text-align: left;
  vertical-align: top;
}

pre {
  margin: 0;
  font-size: 0.8rem;
  white-space: pre-wrap;
  max-width: 400px;
  overflow-x: auto;
}

code {
  background: #f0f0f0;
  padding: 0.1rem 0.3rem;
  font-size: 0.85rem;
}

.added { color: green; }
.removed { color: red; }
.changed { color: orange; }

tr.added { background: #e6ffe6; }
tr.removed { background: #ffe6e6; }
tr.changed { background: #fff3e6; }

.no-diff {
  padding: 1rem;
  background: #e6ffe6;
  border-radius: 4px;
}
</style>
```

---

### 3. View Wrapper

**File:** `packages/client/src/views/RmosRunsDiffView.vue`

```vue
<template>
  <div class="rmos-runs-diff-view">
    <h1>Run Artifact Diff</h1>
    <RunDiffViewer />
  </div>
</template>

<script setup lang="ts">
import RunDiffViewer from "@/components/rmos/RunDiffViewer.vue";
</script>

<style scoped>
.rmos-runs-diff-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}
</style>
```

---

### 4. Route Configuration

Add to your router:

```typescript
{
  path: "/rmos/runs/diff",
  name: "RmosRunsDiff",
  component: () => import("@/views/RmosRunsDiffView.vue"),
}
```

**Usage:**
```
/rmos/runs/diff?a=<run_id_A>&b=<run_id_B>
```

---

### 5. Optional: "Diff with..." Button

Add to `RunArtifactDetail.vue` for easy access:

```vue
<button
  @click="$router.push({
    name: 'RmosRunsDiff',
    query: { a: artifact.run_id, b: '' }
  })"
>
  Compare with another run...
</button>
```

Or store "last selected run" in the Pinia store and auto-populate B.

---

## User Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DIFF VIEWER WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. From Run List                                                          │
│      └── Select Run A → Click "Compare"                                    │
│          └── Select Run B → View diff                                      │
│                                                                             │
│   2. Direct URL                                                             │
│      └── /rmos/runs/diff?a=abc123&b=def456                                 │
│                                                                             │
│   3. From Blocked Response                                                  │
│      └── "Why blocked?" → Compare with last successful run                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What the Diff Shows

| Section | Purpose |
|---------|---------|
| **Overview** | Quick identity check (run_id, status, tool_id) |
| **Hashes** | Did feasibility/toolpaths/gcode change? (✅/❌) |
| **Diff Summary** | Counts: added, removed, changed |
| **Diff Items** | Path-by-path breakdown of differences |

---

## Example Output

**Hash Comparison:**

| Key | A | B | Match |
|-----|---|---|-------|
| feasibility_sha256 | `abc123...` | `abc123...` | ✅ |
| toolpaths_sha256 | `def456...` | `xyz789...` | ❌ |
| gcode_sha256 | `111aaa...` | `222bbb...` | ❌ |

**Diff Items:**

| Path | Op | A | B |
|------|----|---|---|
| `decision.risk_level` | changed | `"GREEN"` | `"RED"` |
| `decision.score` | changed | `87.5` | `42.0` |
| `feasibility.rim_speed.value` | changed | `3200` | `6500` |

---

## Answering Key Questions

| Question | How to Answer |
|----------|---------------|
| "Why is this run blocked now?" | Diff against last successful run, check `decision.risk_level` |
| "Did feasibility change?" | Check `feasibility_sha256` match |
| "Same feasibility, different G-code?" | `feasibility_sha256` ✅, `gcode_sha256` ❌ |
| "What parameter changed?" | Look at `feasibility.*` diff items |

---

## Design Notes

- **No external dependencies** — Simple recursive diff algorithm
- **Bounded output** — Max 2000 diff items to prevent UI freeze
- **Focused comparison** — Only diffs decision, hashes, feasibility, opplan (not raw G-code text)
- **Bidirectional workflow aligned** — Compare artifacts, not guesses
