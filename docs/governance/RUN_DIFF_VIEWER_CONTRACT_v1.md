# Run Diff Viewer Contract

**Document Type:** Canonical Governance Specification
**Version:** 1.0
**Effective Date:** December 17, 2025
**Status:** AUTHORITATIVE
**Precedence:** PRIMARY - All implementations MUST conform
**Dependency:** RUN_ARTIFACT_UI_PANEL_CONTRACT_v1.md

---

## Governance Statement

This document establishes the **canonical contract** for the Run Diff Viewer within the Luthier's ToolBox client application. All implementations for comparing run artifacts MUST conform to the specifications herein. Deviation from this contract is prohibited without formal amendment through the governance review process.

### Governing Principles

1. **Deterministic Comparison** — Same inputs MUST produce same diff output
2. **Bounded Output** — Diff results MUST be capped to prevent UI freeze
3. **Focused Scope** — Only decision-relevant fields are compared
4. **Hash-First Analysis** — Hash comparison MUST precede detailed diff
5. **Audit Clarity** — Diffs MUST answer "what changed and why?"

### Subordinate Documents

All implementation documents, diff algorithms, and component code are subordinate to this contract.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Diff algorithm specification | Backend diff computation |
| Comparison UI requirements | Artifact creation/modification |
| Hash comparison display | Raw G-code text diffing |
| Route configuration | Multi-artifact comparison (3+) |

---

## Purpose and Use Cases

### Primary Questions Answered

| Question | How Answered |
|----------|--------------|
| "Why is this run blocked now?" | Diff against last successful run |
| "Did feasibility change?" | Check `feasibility_sha256` match |
| "Same feasibility, different G-code?" | Hash match: feas ✅, gcode ❌ |
| "What parameter changed?" | View `feasibility.*` diff items |

---

## Diff Algorithm Specification

### JSON Diff Contract

```typescript
type DiffOp = "added" | "removed" | "changed";

interface DiffItem {
  path: string;    // e.g., "feasibility.saw.rim_speed"
  op: DiffOp;
  a?: any;         // Value in artifact A
  b?: any;         // Value in artifact B
}

function diffJson(
  a: any,
  b: any,
  basePath?: string,
  out?: DiffItem[],
  maxItems?: number  // Default: 2000
): DiffItem[]
```

### Algorithm Requirements

1. **Recursive traversal** — Compare nested objects/arrays
2. **Sorted keys** — Object keys compared in alphabetical order
3. **Array by index** — Arrays compared element-by-element
4. **Type awareness** — Type changes marked as "changed"
5. **Bounded output** — Stop at `maxItems` to prevent freeze

### Comparison Scope

Only these sections are compared:

| Section | Purpose |
|---------|---------|
| `decision` | Safety decision differences |
| `hashes` | Hash value changes |
| `feasibility` | Input parameter changes |
| `outputs.opplan_json` | Operation plan changes |

**Excluded:** `outputs.gcode_text` (too large for useful diff)

---

## Component Architecture

### Required Components

| Component | Purpose |
|-----------|---------|
| `RunDiffViewer` | Main diff display component |
| `jsonDiff.ts` | Diff algorithm utility |

### File Structure (Reference)

```
packages/client/src/
+-- utils/
|   +-- jsonDiff.ts              # Diff algorithm
+-- components/rmos/
|   +-- RunDiffViewer.vue        # Diff UI
+-- views/
    +-- RmosRunsDiffView.vue     # Route wrapper
```

---

## UI Requirements

### Input Controls (MANDATORY)

| Control | Description |
|---------|-------------|
| Run A input | Text field for run_id A |
| Run B input | Text field for run_id B |
| Compare button | Triggers diff computation |

### Display Sections (MANDATORY)

#### 1. Overview Section

| Field | Content |
|-------|---------|
| A Identity | run_id, status, tool_id |
| B Identity | run_id, status, tool_id |

#### 2. Hash Comparison Table

| Column | Content |
|--------|---------|
| Key | Hash field name |
| A | First 12 chars of A's hash |
| B | First 12 chars of B's hash |
| Match | ✅ or ❌ indicator |

Required hash fields:
- `feasibility_sha256`
- `toolpaths_sha256`
- `gcode_sha256`
- `opplan_sha256`

#### 3. Diff Summary

Display counts:
- Added: {count}
- Removed: {count}
- Changed: {count}

#### 4. Diff Items Table

| Column | Content |
|--------|---------|
| Path | JSON path (e.g., `decision.risk_level`) |
| Op | `added`, `removed`, or `changed` |
| A | Value in artifact A (formatted JSON) |
| B | Value in artifact B (formatted JSON) |

---

## Visual Styling Requirements

### Diff Operation Colors (MANDATORY)

```css
.added { color: green; }
.removed { color: red; }
.changed { color: orange; }

tr.added { background: #e6ffe6; }
tr.removed { background: #ffe6e6; }
tr.changed { background: #fff3e6; }
```

### No-Diff State

When no differences found:
- Display success message with ✅
- Green background
- Text: "No differences found in decision, hashes, feasibility, or opplan."

---

## Route Configuration

### Required Route

```typescript
{
  path: "/rmos/runs/diff",
  name: "RmosRunsDiff",
  component: () => import("@/views/RmosRunsDiffView.vue"),
}
```

### URL Format

```
/rmos/runs/diff?a={run_id_A}&b={run_id_B}
```

Query parameters:
- `a` — Run ID for artifact A
- `b` — Run ID for artifact B

---

## User Flow Specification

```
+-----------------------------------------------------------------------------+
|                         DIFF VIEWER WORKFLOW                                 |
+-----------------------------------------------------------------------------+
|                                                                             |
|   1. From Run List                                                          |
|      +-- Select Run A --> Click "Compare"                                   |
|          +-- Select Run B --> View diff                                     |
|                                                                             |
|   2. Direct URL                                                             |
|      +-- /rmos/runs/diff?a=abc123&b=def456                                 |
|                                                                             |
|   3. From Blocked Response                                                  |
|      +-- "Why blocked?" --> Compare with last successful run               |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Integration Requirements

### "Compare with..." Button

The `RunArtifactDetail` component SHOULD include:

```vue
<button @click="navigateToDiff(artifact.run_id)">
  Compare with another run...
</button>
```

Navigation pre-populates run A, allows user to select run B.

---

## Example Output

### Hash Comparison

| Key | A | B | Match |
|-----|---|---|-------|
| feasibility_sha256 | `abc123def4...` | `abc123def4...` | ✅ |
| toolpaths_sha256 | `def456789a...` | `xyz789012b...` | ❌ |
| gcode_sha256 | `111aaa222b...` | `333ccc444d...` | ❌ |
| opplan_sha256 | `---` | `---` | ✅ |

### Diff Items

| Path | Op | A | B |
|------|----|---|---|
| `decision.risk_level` | changed | `"GREEN"` | `"RED"` |
| `decision.score` | changed | `87.5` | `42.0` |
| `feasibility.saw.rim_speed.value` | changed | `3200` | `6500` |
| `feasibility.saw.rim_speed.rating` | changed | `"OK"` | `"DANGER"` |

---

## Compliance Verification

Implementations are compliant when:

- [ ] Run A and Run B inputs are present
- [ ] Compare button triggers diff computation
- [ ] Overview section shows both artifact identities
- [ ] Hash comparison table shows all 4 hash fields
- [ ] Match indicators (✅/❌) are correct
- [ ] Diff summary shows add/remove/change counts
- [ ] Diff items table shows path, op, and values
- [ ] Row colors match diff operation type
- [ ] No-diff state displays success message
- [ ] Route accessible at `/rmos/runs/diff`
- [ ] URL parameters `a` and `b` are parsed on mount

---

## Test Requirements

All implementations MUST include tests proving:

1. **Identical artifacts produce empty diff** — Same run compared to itself
2. **Different artifacts produce diff items** — Changed values detected
3. **Hash match detection works** — ✅/❌ indicators correct
4. **Bounded output** — Large diffs capped at maxItems
5. **Route parameters parsed** — `a` and `b` from URL populate inputs

---

## Amendment Process

Changes to this contract require:
1. Formal proposal with justification
2. Algorithm stability verification
3. Version increment
4. Update to all subordinate implementations

---

## Document Control

| Field | Value |
|-------|-------|
| Document ID | GOV-RDV-001 |
| Classification | Internal - Engineering |
| Owner | RMOS Architecture Team |
| Last Review | December 17, 2025 |
| Next Review | March 17, 2026 |
