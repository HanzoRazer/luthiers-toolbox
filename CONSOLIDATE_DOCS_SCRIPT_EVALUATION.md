# consolidate_docs.ps1 - System Evaluation

**Script:** `consolidate_docs.ps1`
**Lines:** 858
**Purpose:** Organize markdown documentation into canonical hierarchy
**Generated:** December 17, 2025

---

## Executive Summary

This PowerShell script consolidates ~440+ markdown files from scattered locations into a structured documentation hierarchy. It implements a **governance classification system** with three tiers: Canonical (binding), Advisory (guidance), and Archive (historical).

**Overall Assessment:** Well-structured but has several operational risks and edge cases that could cause data loss or incomplete execution.

---

## 1. Architecture / Flow

### Phase Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXECUTION FLOW (8 Phases)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PHASE 1: Create Directory Structure                                       │
│   └── 24 directories created under docs/                                    │
│       ├── canonical/governance/ (7 binding governance docs)                 │
│       ├── advisory/ (5 guidance docs)                                       │
│       ├── quickref/[10 subsystems]/ (operational guides)                    │
│       └── archive/2025-12/[9 categories]/ (historical)                      │
│                                                                             │
│   PHASE 2: Move CANONICAL GOVERNANCE (6 files)                              │
│   └── Binding rules: AI_SANDBOX, CNC_SAW_LAB_SAFETY, GOVERNANCE,            │
│       RMOS_2.0, Tool_Library_Spec, VALUE_ADDED_CODING_POLICY                │
│                                                                             │
│   PHASE 3: Move ADVISORY (5 files)                                          │
│   └── Guidance: AI_SANDBOX_v2.0, OpenAI_Provider, GRAPHICS_INGESTION,       │
│       ROSETTE_DESIGNER, SPECIALTY_MODULES                                   │
│                                                                             │
│   PHASE 4: Move ARCHIVED GOVERNANCE (2 files)                               │
│   └── Historical: LEGACY_ARCHIVE_POLICY, MM_5_ULTRA_FRAGILITY               │
│                                                                             │
│   PHASE 5: Move CANONICAL SPECS (6 files)                                   │
│   └── Architecture: ARCHITECTURE.md, CODING_POLICY, QUICKSTART, etc.        │
│                                                                             │
│   PHASE 6: Move QUICKREF by Subsystem (~73 files)                           │
│   └── art_studio(10), blueprint(3), bridge_lab(1), cam(7),                  │
│       compare_lab(2), curve_lab(2), general(41), instrument(1),             │
│       rmos(4), saw_lab(2)                                                   │
│                                                                             │
│   PHASE 7: Move ARCHIVE Files (~439 files)                                  │
│   └── bundles(28), handoffs(18), integration(27), misc(224),                │
│       patches(41), phases(50), reports(25), sessions(10), waves(16)         │
│                                                                             │
│   PHASE 8: Verification & Statistics                                        │
│   └── Count files in each category and display summary                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Source Locations              Move Operations            Destination
─────────────────────         ────────────────           ───────────────────
Root (*.md)           ────►   Move-Item -Force    ────►  docs/canonical/
docs/*.md             ────►                       ────►  docs/canonical/governance/
docs/subdirs/*.md     ────►                       ────►  docs/advisory/
                                                  ────►  docs/quickref/[subsystem]/
                                                  ────►  docs/archive/2025-12/[category]/
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `-Force` on all Move-Item | Overwrites existing files silently |
| `$ErrorActionPreference = "Stop"` | Halts on first error |
| Individual Test-Path checks | Each file checked before move |
| Hardcoded file lists | No dynamic discovery of files |

---

## 2. Edge Cases Analysis

### Critical Edge Cases

| Edge Case | Current Handling | Risk Level | Impact |
|-----------|------------------|------------|--------|
| File already exists at destination | **Silently overwritten** (`-Force`) | 🔴 HIGH | Data loss |
| File has been renamed since script creation | Marked as `[MISSING]`, continues | 🟡 MEDIUM | Incomplete consolidation |
| File path contains special characters | No escaping | 🟡 MEDIUM | Move fails |
| Working directory is wrong | Uses `Get-Location` | 🔴 HIGH | Moves files to wrong place |
| Partial execution (Ctrl+C) | No rollback mechanism | 🔴 HIGH | Inconsistent state |
| Same file listed multiple times | Last move wins | 🟡 MEDIUM | Silent conflict |
| File is locked by another process | Script stops (`$ErrorActionPreference`) | 🟡 MEDIUM | Partial execution |
| Network drive latency | No retry logic | 🟡 MEDIUM | Timeout/failure |
| Destination directory doesn't exist | Created in Phase 1 | 🟢 LOW | Handled correctly |

### Untested Scenarios

```powershell
# 1. Unicode filenames (e.g., "CNC Saw Lab — Recommended.md")
#    The script uses #U2014 encoding for em-dash, which is brittle

# 2. Very long paths (>260 chars on Windows)
#    docs\archive\2025-12\misc\Some_Very_Long_Filename.md could exceed

# 3. Read-only files
#    Move-Item will fail on read-only source files

# 4. Files modified during execution
#    No file locking mechanism
```

---

## 3. Observability / Testing

### Current Observability

| Feature | Present? | Implementation |
|---------|----------|----------------|
| Progress output | ✅ Yes | Write-Host with colors |
| Phase indicators | ✅ Yes | `[PHASE N]` headers |
| Individual file status | ✅ Yes | `[CANONICAL]`, `[MISSING]`, etc. |
| Final statistics | ✅ Yes | File counts per category |
| Error logging | ❌ No | Errors halt script, no log file |
| Dry-run mode | ❌ No | No `-WhatIf` support |
| Verbose mode | ❌ No | No detailed logging option |
| Execution timestamp | ❌ No | No timestamp in output |
| Rollback log | ❌ No | No record of moves for reversal |

### Testing Gaps

```
❌ No unit tests
❌ No integration tests
❌ No mock filesystem tests
❌ No validation of destination file integrity
❌ No checksum verification after move
❌ No test for idempotency (running twice)
```

### Recommended Test Cases

```powershell
# Test 1: Idempotency
# Run script twice - should produce same result

# Test 2: Missing source files
# Remove a known file and verify [MISSING] output

# Test 3: Pre-existing destination file
# Create file at destination, verify behavior

# Test 4: Permission denied
# Lock a file and verify error handling

# Test 5: Working directory validation
# Run from wrong directory, verify failure

# Test 6: Unicode filenames
# Create file with em-dash, verify move succeeds
```

---

## 4. Operational Risks

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation Status |
|------|------------|--------|-------------------|
| **Data Loss** - `-Force` overwrites files | High | Critical | ❌ Not mitigated |
| **Partial Execution** - Ctrl+C leaves mess | Medium | High | ❌ Not mitigated |
| **Wrong Directory** - Moves wrong files | Medium | Critical | ❌ Not mitigated |
| **Hardcoded Lists** - Stale after new files | High | Medium | ❌ Not mitigated |
| **No Backup** - Original locations lost | High | High | ❌ Not mitigated |
| **Silent Failures** - Some moves fail quietly | Medium | Medium | Partial (Test-Path) |
| **Path Length** - Windows 260 char limit | Low | Medium | ❌ Not mitigated |

### Pre-Run Checklist (REQUIRED)

```
□ Verify current directory is repo root: pwd
□ Create backup: git stash or git commit -m "pre-consolidation"
□ Check git status is clean
□ Verify no files open in editors
□ Review git diff after running
```

### Post-Run Checklist

```
□ Run: git status (check for unexpected changes)
□ Verify key files exist in new locations
□ Check docs/canonical/governance/ has binding files
□ Verify no orphaned empty directories
□ Run: git diff --stat (understand scope of changes)
□ Commit: git add -A && git commit -m "docs: consolidate hierarchy"
```

---

## 5. Graceful Failure Analysis

### Current Failure Modes

```powershell
$ErrorActionPreference = "Stop"  # Line 42
```

**Behavior:** Script halts completely on first error.

| Failure Point | Script Behavior | Recovery |
|---------------|-----------------|----------|
| Directory creation fails | Script stops | Manual cleanup required |
| File move fails (permissions) | Script stops | Partial state, manual fix |
| File move fails (missing) | `[MISSING]` printed, continues | ✅ Graceful |
| Destination exists | **Overwritten silently** | ❌ Data loss possible |
| Invalid path characters | Script stops | Manual fix required |

### What's Missing for Graceful Failure

```powershell
# 1. Transaction support (rollback on failure)
# 2. Pre-flight validation (check all sources exist)
# 3. Backup before move
# 4. Confirmation prompts for destructive operations
# 5. Resume capability after partial failure
# 6. Detailed error log file
```

### Failure Recovery Procedure

If script fails mid-execution:

```powershell
# 1. Check git status to see what moved
git status

# 2. Identify partially moved files
git diff --name-status

# 3. Option A: Complete manually
#    Continue moving files from where script stopped

# 4. Option B: Rollback
git checkout -- .
git clean -fd  # WARNING: removes untracked files

# 5. Option C: Selective restore
git checkout -- path/to/specific/file.md
```

---

## 6. Code Quality Issues

### Identified Issues

| Issue | Location | Severity |
|-------|----------|----------|
| No working directory validation | Line 43 | 🔴 Critical |
| Hardcoded file lists (440+ entries) | Lines 97-803 | 🟡 Medium |
| `-Force` without backup | All Move-Item | 🔴 Critical |
| Unicode path encoding (#U2014) | Multiple | 🟡 Medium |
| No dry-run option | N/A | 🟡 Medium |
| Repeated Test-Path pattern | 700+ times | 🟢 Low (verbose) |
| No timestamp in output | N/A | 🟢 Low |
| Stats counting may miss nested | Lines 824-831 | 🟢 Low |

### Maintenance Burden

```
- Adding a new file requires manual script edit
- Renaming a file requires TWO edits (old path, new path)
- ~440+ individual move commands to maintain
- No automated discovery of new documentation
```

---

## 7. Re-Review Checklist

Use this checklist after any modifications to the script:

### Pre-Modification

```
□ Backup current script version
□ Document intended change
□ Identify affected phases
□ Check for duplicate file entries
```

### Code Changes

```
□ Verify Test-Path uses correct source path
□ Verify Move-Item destination is correct
□ Check for path escaping (spaces, special chars)
□ Ensure phase statistics match actual file counts
□ Verify directory exists in Phase 1 if adding new category
```

### Structural Integrity

```
□ All 8 phases present and in order
□ $ErrorActionPreference = "Stop" is first line
□ Directory creation before file moves
□ Verification phase at end
□ Next steps guidance present
```

### Testing After Changes

```
□ Run on test copy of repository first
□ Verify all [MISSING] entries are expected
□ Check no unexpected [MISSING] entries
□ Verify file counts in final statistics
□ Run git status and review changes
□ Verify git diff shows only expected moves
```

### Edge Case Verification

```
□ Test with file that has space in name
□ Test with file that has em-dash (—) in name
□ Test with very long filename
□ Test running script twice (idempotency)
□ Test from wrong working directory (should fail safely)
```

### Documentation

```
□ Update file counts in script header if changed
□ Update GOVERNANCE HIERARCHY comment if tiers change
□ Add/update USAGE section if workflow changes
□ Document any new environment dependencies
```

---

## 8. Recommended Improvements

### High Priority

```powershell
# 1. Add working directory validation
if (-not (Test-Path ".git")) {
    Write-Host "ERROR: Must run from repository root (no .git found)" -ForegroundColor Red
    exit 1
}

# 2. Add dry-run mode
param(
    [switch]$DryRun,
    [switch]$Force
)

# 3. Add backup before destructive operations
if (-not $Force) {
    Write-Host "Creating backup..." -ForegroundColor Yellow
    git stash push -m "pre-consolidation-backup"
}

# 4. Add confirmation prompt
$confirm = Read-Host "This will move ~440 files. Continue? (y/n)"
if ($confirm -ne 'y') { exit 0 }
```

### Medium Priority

```powershell
# 5. Add logging to file
$logFile = "consolidation_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Start-Transcript -Path $logFile

# 6. Replace -Force with conflict detection
if (Test-Path $destination) {
    Write-Host "  [CONFLICT] $destination already exists" -ForegroundColor Red
    $conflicts++
}

# 7. Add resume capability
$checkpoint = "consolidation_checkpoint.json"
```

### Low Priority

```powershell
# 8. Dynamic file discovery instead of hardcoded lists
$mdFiles = Get-ChildItem -Path . -Filter "*.md" -Recurse

# 9. Add progress bar for long operations
$i = 0
foreach ($file in $files) {
    Write-Progress -Activity "Moving files" -PercentComplete (($i++ / $total) * 100)
}
```

---

## 9. Summary

### Strengths

- ✅ Well-organized phase structure
- ✅ Clear governance tier classification
- ✅ Detailed progress output with colors
- ✅ Final statistics for verification
- ✅ Handles missing files gracefully
- ✅ Creates directory structure first

### Weaknesses

- ❌ No backup mechanism before moves
- ❌ `-Force` can silently destroy data
- ❌ No working directory validation
- ❌ Hardcoded file lists (maintenance burden)
- ❌ No dry-run option
- ❌ No rollback capability
- ❌ No log file for audit trail

### Risk Rating

| Category | Rating |
|----------|--------|
| Data Safety | ⚠️ MEDIUM-HIGH RISK |
| Execution Reliability | ✅ MEDIUM-LOW RISK |
| Maintainability | ⚠️ MEDIUM RISK |
| Observability | ✅ LOW RISK |

### Recommendation

**USE WITH CAUTION.** Always:
1. Commit all changes before running
2. Run `git status` after execution
3. Review changes before committing
4. Keep backup of original file locations

---

*Evaluation generated: December 17, 2025*
*Script version: December 17, 2025*
