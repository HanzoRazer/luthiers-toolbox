# Client Directory Conflict Report

**Date:** December 15, 2025
**Issue Type:** Git Configuration / Directory Structure Conflict
**Severity:** Medium - Blocks frontend file commits

---

## Executive Summary

Two parallel `client/` directories exist in the workspace with conflicting git tracking rules. Files created in `client/src/` are gitignored and cannot be committed, while `packages/client/src/` is tracked. This blocks the implementation of the Run Artifact UI Panel frontend components.

---

## Issue Details

### The Conflict

| Directory | Git Status | Contains |
|-----------|------------|----------|
| `client/src/` | **IGNORED** (line 107 in .gitignore) | Router, API files, components |
| `packages/client/src/` | **TRACKED** | Stores, API files, components |

### Root Cause

Line 107 in `.gitignore`:
```
# ------------------------------------------
# Legacy/Archive Directories (DO NOT TRACK)
# ------------------------------------------
__ARCHIVE__/
Archtop/
Stratocaster/
client/          ← THIS LINE IGNORES ALL OF client/
server/
```

The `client/` directory is classified as "Legacy/Archive" but contains **active development files** including:
- `client/src/router/index.ts` (main router with 400+ lines)
- `client/src/api/*.ts` (13 API client files)
- `client/src/components/` (active Vue components)

### Evidence

**File created but cannot be committed:**
```
Path: client/src/api/rmosRuns.ts
Size: 4200 bytes
Created: Dec 15, 2025 21:38
Git status: IGNORED by .gitignore:107
```

**Git check-ignore output:**
```
.gitignore:107:client/    client/src/api/rmosRuns.ts
```

---

## Directory Comparison

### client/src/ (IGNORED)
```
client/src/
├── api/           (13 files + rmosRuns.ts)
├── App.vue        (22KB - substantial)
├── cam/
├── cnc_production/
├── components/    (active components)
├── composables/
├── labs/
├── main.ts
├── router/        (index.ts - main router)
├── stores/        (empty, created today)
├── style.css
├── types/
├── views/
└── workers/
```

### packages/client/src/ (TRACKED)
```
packages/client/src/
├── api/           (API files - tracked)
├── App.vue        (324 bytes - minimal)
├── cam/
├── cam_core/
├── cnc_production/
├── components/
├── composables/
├── labs/
├── main.ts        (195 bytes - minimal)
├── models/
├── router/
└── stores/        (10+ Pinia stores - tracked)
```

---

## Affected Files

### Currently Blocked (in client/src/)
| File | Status | Action Needed |
|------|--------|---------------|
| `client/src/api/rmosRuns.ts` | Created, cannot commit | Move or unignore |

### Pending Creation (from RUN_ARTIFACT_UI_PANEL.md)
| Document Path | Actual Target | Issue |
|---------------|---------------|-------|
| `packages/client/src/stores/rmosRunsStore.ts` | Unknown | Needs clarification |
| `packages/client/src/components/rmos/RunArtifactPanel.vue` | Unknown | Needs clarification |
| `packages/client/src/components/rmos/RunArtifactRow.vue` | Unknown | Needs clarification |
| `packages/client/src/components/rmos/RunArtifactDetail.vue` | Unknown | Needs clarification |
| `packages/client/src/views/RmosRunsView.vue` | Unknown | Needs clarification |

---

## Resolution Options

### Option A: Unignore client/ (Minimal Change)
**Risk:** Low
**Effort:** 1 line change

```diff
# .gitignore line 107
- client/
+ # client/  ← REMOVED: Now tracked (contains active router)
```

**Pros:**
- Quick fix
- Preserves existing file locations
- Router imports continue working

**Cons:**
- May expose files that were intentionally ignored
- Unclear why it was ignored originally

---

### Option B: Move Files to packages/client/ (Document-Aligned)
**Risk:** Medium
**Effort:** File moves + import updates

```bash
# Move the created file
mv client/src/api/rmosRuns.ts packages/client/src/api/

# Create remaining files in packages/client/src/
```

**Pros:**
- Aligns with markdown document specs
- Uses the tracked directory

**Cons:**
- Need to verify which directory the build system uses
- May break imports in existing components

---

### Option C: Consolidate Directories (Full Resolution)
**Risk:** High
**Effort:** Major refactor

1. Determine which is the "canonical" client
2. Merge unique files from both directories
3. Update all imports
4. Remove duplicate directory
5. Update .gitignore accordingly

**Pros:**
- Eliminates confusion permanently
- Single source of truth

**Cons:**
- Time-consuming
- Risk of breaking builds

---

## Recommended Sandbox Steps

1. **Check build configuration:**
   ```bash
   cat packages/client/vite.config.ts 2>/dev/null
   cat client/vite.config.ts 2>/dev/null
   ```

2. **Check package.json locations:**
   ```bash
   ls -la packages/client/package.json client/package.json 2>/dev/null
   ```

3. **Check which router is used at runtime:**
   - Compare `client/src/router/index.ts` vs `packages/client/src/router/index.ts`

4. **Test Option A in sandbox:**
   ```bash
   git stash
   sed -i 's/^client\//#client\//' .gitignore
   git add client/src/api/rmosRuns.ts
   git status
   git stash pop
   ```

---

## Questions for Resolution

1. **Why was `client/` marked as Legacy/Archive?** Is it actually deprecated?

2. **Which client directory does the build system use?** Check vite.config.ts or package.json scripts.

3. **Are both directories supposed to exist?** Or is one a duplicate/backup?

4. **Should new frontend files go in `client/` or `packages/client/`?**

---

## Files Ready to Commit (Unblocked)

These files are staged and ready:
```
A  AI_SCHEMA_NAMESPACE_REPORT.md
A  BIDIRECTIONAL_WORKFLOW_ANALYSIS_REPORT.md
A  CNC_SAW_LAB_SAFETY_GOVERNANCE.md
A  RUN_ARTIFACT_INDEX_QUERY_API.md
A  RUN_ARTIFACT_PERSISTENCE.md
A  RUN_ARTIFACT_UI_PANEL.md
A  RUN_DIFF_VIEWER.md
A  SAW_LAB_EXECUTIVE_HANDOFF.md
A  SAW_LAB_TEST_REPORT_DEC15.md
A  SERVER_SIDE_FEASIBILITY_ENFORCEMENT.md
A  services/api/app/rmos/policies/__init__.py
A  services/api/app/rmos/runs/__init__.py
A  tests/data/saw_lab_blades.json
```

---

*Report generated for sandbox resolution planning*
