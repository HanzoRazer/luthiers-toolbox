# Run Artifact UI Panel Contract

**Document Type:** Canonical Governance Specification
**Version:** 1.0
**Effective Date:** December 17, 2025
**Status:** AUTHORITATIVE
**Precedence:** PRIMARY - All implementations MUST conform
**Dependency:** RUN_ARTIFACT_INDEX_QUERY_API_CONTRACT_v1.md

---

## Governance Statement

This document establishes the **canonical contract** for the Run Artifact UI Panel within the Luthier's ToolBox client application. All UI implementations for artifact browsing MUST conform to the specifications herein. Deviation from this contract is prohibited without formal amendment through the governance review process.

### Governing Principles

1. **Audit Accessibility** — Every run artifact MUST be viewable and downloadable
2. **Filter Consistency** — UI filters MUST map directly to API query parameters
3. **Deep Linking** — Toolpath responses MUST link to their audit records
4. **Status Visibility** — Run status and risk level MUST be visually distinguished
5. **No State Drift** — UI reads the same artifacts the backend writes

### Subordinate Documents

All implementation documents, component code, and styling guides are subordinate to this contract.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Panel component structure | Backend query implementation |
| Required UI elements | Retention policy UI |
| Status/risk visualization | Artifact creation flows |
| Deep linking requirements | Cross-system federation |

---

## Component Architecture

### Required Components

| Component | Purpose |
|-----------|---------|
| `RunArtifactPanel` | Main container with filters and list |
| `RunArtifactRow` | Table row for single artifact |
| `RunArtifactDetail` | Full artifact inspection view |

### File Structure (Reference)

```
packages/client/src/
+-- api/
|   +-- rmosRuns.ts              # API client
+-- stores/
|   +-- rmosRunsStore.ts         # Pinia state management
+-- components/rmos/
|   +-- RunArtifactPanel.vue     # List + filters
|   +-- RunArtifactDetail.vue    # Inspect one artifact
|   +-- RunArtifactRow.vue       # Table row component
+-- views/
    +-- RmosRunsView.vue         # Route wrapper
```

---

## API Client Contract

### Required Functions

```typescript
// List runs with filters
fetchRuns(params: {
  status?: string;
  mode?: string;
  tool_id_prefix?: string;
  risk_level?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  cursor?: string | null;
}): Promise<RunIndexResponse>

// Fetch single artifact
fetchRun(runId: string): Promise<RunArtifact>

// Trigger download
downloadRun(runId: string): void
```

### RunIndexItem Schema

```typescript
interface RunIndexItem {
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
```

---

## Store Contract

### Required State

```typescript
interface RmosRunsState {
  items: RunIndexItem[];
  nextCursor: string | null;
  loading: boolean;
  selected: RunArtifact | null;
  filters: {
    status: string;
    mode: string;
    tool_id_prefix: string;
    risk_level: string;
  };
}
```

### Required Actions

| Action | Description |
|--------|-------------|
| `loadFirst(limit?)` | Load first page, reset cursor |
| `loadMore(limit?)` | Load next page using cursor |
| `select(runId)` | Fetch and set selected artifact |

---

## UI Requirements

### Filter Controls (MANDATORY)

| Filter | Control Type | Options |
|--------|-------------|---------|
| Status | Select/Dropdown | All, OK, BLOCKED, ERROR |
| Mode | Select/Dropdown | Any Mode, saw, (others as added) |
| Risk Level | Select/Dropdown | Any Risk, GREEN, YELLOW, RED, UNKNOWN |

### Table Columns (MANDATORY)

| Column | Data |
|--------|------|
| Time (UTC) | `created_at_utc` |
| Status | `status` with color coding |
| Mode | `mode` |
| Tool | `tool_id` |
| Risk | `risk_level` with color coding |
| Score | `score` or "---" if null |

### Pagination (MANDATORY)

- "Load more" button when `nextCursor` exists
- Button disabled while loading
- Appends to existing items (not replace)

---

## Visual Styling Requirements

### Status Colors (MANDATORY)

```css
.OK { color: green; }
.BLOCKED { color: red; font-weight: bold; }
.ERROR { color: orange; }
```

### Risk Level Colors (MANDATORY)

```css
.GREEN { color: green; }
.YELLOW { color: #cc9900; }
.RED { color: red; font-weight: bold; }
.UNKNOWN { color: gray; font-style: italic; }
```

### Row Hover

- Rows MUST indicate clickability on hover
- Background change or cursor pointer

---

## Detail View Requirements

### Required Sections

| Section | Content |
|---------|---------|
| Identity | run_id, status, mode, tool_id |
| Decision | Full decision object (formatted JSON) |
| Hashes | All hash values |
| G-code Preview | First 500 chars if available |
| Download Button | Triggers JSON file download |

---

## Deep Linking Requirements

### Toolpath Response Integration

Every toolpath response includes:

```json
{
  "_run_id": "abc123...",
  "_run_artifact_path": "/data/runs/rmos/2025-12-17/abc123.json",
  "_hashes": { ... }
}
```

### Link Requirements

| Scenario | UI Action |
|----------|-----------|
| Success (200) | Show "View Run" link next to result |
| Blocked (409) | Show "View Audit" button in error message |
| Error (500) | Show "View Error" link for debugging |

### Link Format

```
/rmos/runs?run_id={run_id}
```

---

## Route Configuration

### Required Route

```typescript
{
  path: "/rmos/runs",
  name: "RmosRuns",
  component: () => import("@/views/RmosRunsView.vue"),
}
```

---

## User Flow Specification

```
+-----------------------------------------------------------------------------+
|                         OPERATOR WORKFLOW                                    |
+-----------------------------------------------------------------------------+
|                                                                             |
|   1. Generate Toolpaths                                                     |
|      +-- POST /api/rmos/toolpaths                                          |
|          +-- Response includes _run_id                                     |
|                                                                             |
|   2. View Run Artifact (optional)                                           |
|      +-- Click "View Run" link                                             |
|          +-- Opens /rmos/runs?run_id=xxx                                   |
|              +-- Shows full artifact with hashes                           |
|                                                                             |
|   3. Browse All Runs                                                        |
|      +-- Navigate to /rmos/runs                                            |
|          +-- Filter by status, mode, risk level                            |
|              +-- Click row to inspect                                      |
|                  +-- Download JSON for audit                               |
|                                                                             |
|   4. Investigate Blocked Runs                                               |
|      +-- Filter: status=BLOCKED, risk_level=RED                            |
|          +-- Click to see decision details                                 |
|              +-- "Why was this blocked?"                                   |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Compliance Verification

Implementations are compliant when:

- [ ] All required filter controls are present
- [ ] Table displays all mandatory columns
- [ ] Status and risk level have correct color coding
- [ ] Pagination works with "Load more" button
- [ ] Detail view shows all required sections
- [ ] Download button triggers file download
- [ ] Route is accessible at `/rmos/runs`
- [ ] Toolpath responses link to audit trail

---

## Amendment Process

Changes to this contract require:
1. Formal proposal with justification
2. UX review for user impact
3. Version increment
4. Update to all subordinate implementations

---

## Document Control

| Field | Value |
|-------|-------|
| Document ID | GOV-RAUP-001 |
| Classification | Internal - Engineering |
| Owner | RMOS Architecture Team |
| Last Review | December 17, 2025 |
| Next Review | March 17, 2026 |
