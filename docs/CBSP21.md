# CBSP21: Code Batch Submission Protocol v2.1

**Status:** Active
**Version:** 2.1
**Purpose:** Structured code patch submission with coverage verification

---

## Overview

CBSP21 (Code Batch Submission Protocol v2.1) is an internal governance protocol for managing code patches with:

- **Coverage verification** — Ensures scanned/captured content meets minimum thresholds (default: 95%)
- **Risk assessment** — Tracks risk level per file (low/medium/high)
- **Architecture scanning** — Integrates with architecture scan findings
- **Audit trail** — Structured manifest for patch inputs

---

## Directory Structure

```
luthiers-toolbox/
├── .cbsp21/                    # Configuration
│   ├── patch_input.json        # Current patch manifest
│   ├── patch_input.schema.json # JSON Schema for validation
│   └── patch_input.json.example
├── cbsp21/                     # Data
│   ├── full_source/            # Original source content
│   ├── scanned_source/         # Scanned/captured content
│   └── patch_packets/          # Generated patch packets
└── scripts/cbsp21/             # Scripts
    ├── cbsp21_coverage_check.py
    └── cbsp21_coverage_with_audit.py
```

---

## Patch Input Schema

The `.cbsp21/patch_input.json` manifest follows this schema:

```json
{
  "schema": "cbsp21_patch_input_v1",
  "coverage_min": 0.95,
  "files": [
    {
      "path": "services/api/app/example.py",
      "intent": "Fix edge case in calculation",
      "risk": "low",
      "behavior_change": "Minor output formatting",
      "verification": ["unit_test", "integration_test"]
    }
  ],
  "architecture_scan": {
    "scan_id": "scan_2026-02-28",
    "risk_summary": {
      "critical": 0,
      "high": 0,
      "medium": 2,
      "low": 5
    },
    "acknowledged": true
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Must be `"cbsp21_patch_input_v1"` |
| `files` | array | List of files in the patch |
| `files[].path` | string | Relative path from repo root |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `coverage_min` | number | Minimum coverage (0-1), default 0.95 |
| `files[].intent` | string | Why this file is being changed |
| `files[].risk` | enum | `"low"`, `"medium"`, or `"high"` |
| `files[].behavior_change` | string | What behavior changes |
| `files[].verification` | array | How to verify the change |
| `architecture_scan` | object | Linked architecture scan results |

---

## Per-PR Manifests

New PRs should use a dedicated manifest under:

```text
.cbsp21/patches/<patch-id>.json
```

The legacy `.cbsp21/patch_input.json` path is still honored for older in-flight
work, but new work should not edit that shared file. The CI gates discover all
candidate manifests, then select the one that best covers the current diff:

1. Most changed files covered, excluding `.cbsp21/` internals from the coverage signal.
2. Fewest declared files/prefixes, so the most specific manifest wins.
3. If two manifests are equally plausible, the gate fails and the PR must narrow
   its manifest scope.
4. If the diff has changed files but **zero** candidates cover any of them,
   auto-discovery returns **no applicable manifest** (fail closed with guidance
   to create `.cbsp21/patches/<patch-id>.json`). The gate does **not** attribute
   that failure to an unrelated historical manifest at 0% coverage
   (CBSP21-DIAG-001 / BR-046).
5. An empty changed-file set is a separate no-op case — not “no applicable
   manifest.” Explicit `--manifest` always validates the path you name.

This is selection, not union. A stale manifest on `main` should not make an
unrelated PR pass; when a manifest is selected, it must be one that actually
overlaps the current patch.

### Merged Manifest Cleanup

Per-PR manifests are required while a PR is open, but they are not meant to
accumulate forever on `main`. After a PR merges and its compliance record is
available in the PR itself, a later housekeeping PR may delete that merged PR's
manifest from `.cbsp21/patches/`.

Cleanup rules:

- Never delete the manifest for an open PR.
- Do not delete a merged manifest in the same PR that first introduced it; let it
  serve as that PR's compliance witness through merge.
- Prefer a small cleanup-only PR when several merged manifests have accumulated.
- If a follow-up PR touches the same files as a recently merged PR, make the new
  manifest more specific than the merged one, or include deletion of the
  superseded merged manifest as explicit cleanup.
- Cleanup PRs should not change runtime code. They should touch only stale
  `.cbsp21/patches/*.json` files and any documentation explaining the cleanup.

The purpose is to avoid a slow return of the old shared-manifest footgun: merged
manifests that cover broad paths can collide with follow-up PRs touching the same
files. Specificity tie-breaks are a safeguard, not a substitute for routine
manifest hygiene.

---

## Coverage Check

The coverage check ensures that scanned content represents at least 95% of the original:

```bash
python scripts/cbsp21/cbsp21_coverage_check.py \
  --full-path cbsp21/full_source \
  --scanned-path cbsp21/scanned_source \
  --threshold 0.95
```

**Exit codes:**
- `0` — Coverage requirement satisfied
- `1` — Coverage below threshold (output prohibited)

---

## CI Workflows

The **emitted check context** — not the workflow filename — is what GitHub merge protection targets. On
this repository that protection is implemented through a ruleset rather than classic branch protection
(see [Merge Enforcement](#merge-enforcement)). Get the context wrong and the ruleset silently requires a
check that never reports.

The context is the job's `name:` when the job declares one, and the **job id** otherwise — it is never
the workflow-level `name:`. Two of the four workflows below declare no job-level `name:`, so their
contexts are their job ids, which do **not** resemble their workflow names:

| Workflow | Emitted check context | Context source | Trigger | Draft behaviour | Required for merge? |
|---|---|---|---|---|---|
| `cbsp21_gate.yml` | **`CBSP21 Patch Manifest Gate`** | job `name:` | `pull_request → main`, `workflow_dispatch` | runs (no condition) | **YES — blocking** |
| `cbsp21_patch_input_gate.yml` | `cbsp21-patch-input` | job id | `pull_request: [opened, synchronize, reopened, ready_for_review]` | **skipped** via `if: !draft` | no — observational |
| `cbsp21_coverage_gate.yml` | `cbsp21-coverage` | job id | paths `cbsp21/**`, `scripts/cbsp21/**`; push to `main`/`master` | n/a | no — path-filtered |
| `cbsp21_patch_packet_format.yml` | `cbsp21-patch-format` | job id | paths `cbsp21/patch_packets/**`, `scripts/cbsp21/**` | n/a | no — path-filtered |

The bottom two contexts are **derived from the workflow definitions, not witnessed from a run** — their
path filters match no tracked files, so neither has ever reported. Re-witness before requiring either.

> **Why only one is required.** `CBSP21 Patch Manifest Gate` is the only CBSP21 workflow with neither a
> draft condition nor a path filter, so it is the only one that reports on every PR to `main`. The bottom
> two are path-filtered to directories that are empty (`cbsp21/` and `cbsp21/patch_packets/` hold
> **zero** tracked files; the live manifests are under `.cbsp21/`). **A required check that never reports
> stays pending and blocks merge until the missing-check condition is resolved** — so requiring either of
> those would deadlock every PR that does not touch `scripts/cbsp21/`. `cbsp21-patch-input` is left
> observational until its skipped-check semantics are characterised separately.

---

## Merge Enforcement

**Enforcement mechanism:** repository ruleset **id `15875552`**, whose literal name is `May 2 2026` (a
display name matching its creation date, not the date of this change), `enforcement: active`, targeting
`~DEFAULT_BRANCH`. The required-context update documented here was applied on **2026-08-11**.

Classic branch protection is **not** used on this repository — querying `/branches/main/protection`
returns HTTP 404, which is expected and is not a misconfiguration. Read enforcement state from
`/repos/{owner}/{repo}/rulesets/15875552` or `/repos/{owner}/{repo}/rules/branches/main` instead; the
404 from the classic endpoint is not evidence that `main` is unprotected.

### The contract

```text
READY PR + covered patch     → CBSP21 Patch Manifest Gate SUCCESS → CBSP21 does not block merge
READY PR + uncovered patch   → CBSP21 Patch Manifest Gate FAILURE → MERGE BLOCKED
READY PR + no CBSP21 result  → required check never reports       → MERGE BLOCKED (pending)
```

Required contexts on `main`:

| Context | Responsibility |
|---|---|
| `Fence Checks (Blocking)` | fence architecture |
| **`CBSP21 Patch Manifest Gate`** | CBSP21 admission / coverage |

Adjacent ruleset settings, deliberately **unchanged** by CBSP21 enforcement:
`strict_required_status_checks_policy: false` (branches need not be current with `main`),
`required_approving_review_count: 0`, `bypass_actors: []`.

**`bypass_actors` is empty, so the gate binds administrators too.** There is no bypass flag in
`check_cbsp21_gate.py`, and `cbsp21_gate.yml` sets no `continue-on-error`. A failing gate is not
overridable through the ordinary merge path.

### Draft behaviour

Draft status does **not** suppress `CBSP21 Patch Manifest Gate`: GitHub fires `pull_request` events for
drafts, and neither the workflow nor its job declares a draft-only skip condition.

`cbsp21-patch-input` is skipped on drafts by design. Its workflow lists `ready_for_review` in its
trigger types, so the draft → ready transition re-fires it. That skip is intentional, not enforcement
drift, and it is safe precisely because that context is **not** required.

### Diagnosing a missing or skipped check

| Symptom | Meaning |
|---|---|
| `CBSP21 Patch Manifest Gate` — **fail** | your diff contains files no manifest declares. The log names them. Add or extend `.cbsp21/patches/<patch-id>.json` |
| `CBSP21 Patch Manifest Gate` — **absent / pending** | the workflow did not run. Check the PR targets `main` and the workflow file exists on **your branch** |
| `cbsp21-patch-input` — **skipping** | the PR is a draft. Expected; not a failure. Mark ready for review and it runs |
| `mergeStateStatus: BLOCKED` with all checks green | something other than CBSP21 blocks — inspect the other required context |

### Enforcement witness (CBSP21-GATE-002, 2026-08-11)

Requiring a check is not the same as proving it blocks. Both directions were witnessed on the real PR
path against ruleset `15875552`:

**Negative — an uncovered patch cannot merge.** Disposable PR #264, base `428649c0`, head `65c0982c`,
carrying exactly one file declared by no manifest (`CBSP21_TC16_UNDECLARED_ARTIFACT.md`, +1/-0).
`CBSP21 Patch Manifest Gate` **failed** while `Fence Checks (Blocking)` **passed** and the branch had no
conflicts (`mergeable: MERGEABLE`), so the block is attributable to CBSP21 alone rather than to branch
history or a stale base. `mergeStateStatus: BLOCKED`. A real merge attempt was refused:

```text
HTTP 405 — Repository rule violations found
Required status check "CBSP21 Patch Manifest Gate" is failing.
```

`main` stayed at `428649c0` before and after the attempt. PR closed unmerged; branch deleted, not reused.

**Positive — a covered patch is not blocked.** The CBSP21-GATE-002 patch itself declares its own file
set, passes `CBSP21 Patch Manifest Gate`, and reaches a mergeable state. The sprint eats its own dog
food: the patch that makes the gate blocking is admitted by that same gate.

**Gate-logic witness (prior).** `workflow_dispatch` run `31466755438` on a throwaway branch proved the
gate fails closed and names the uncovered file. That established the script's behaviour; it did **not**
establish merge protection, which is why the PR-path witness above exists.

---

## Related Documentation

- [Architecture Invariants](governance/ARCHITECTURE_INVARIANTS.md)
- [Fence Architecture](governance/FENCE_ARCHITECTURE.md)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.1 | 2026-08 | CBSP21-GATE-002 — `CBSP21 Patch Manifest Gate` made a required context in ruleset `15875552`; merge-enforcement contract, draft behaviour, and blocking witness documented. Documentation only: protocol version stays 2.1, no schema or threshold change |
| 2.1 | 2026-01 | Added architecture_scan integration |
| 2.0 | 2025-12 | Added risk assessment fields |
| 1.0 | 2025-11 | Initial protocol |
