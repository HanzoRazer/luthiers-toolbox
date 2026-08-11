# SPRINTS.md Maintenance Discipline

**Established:** 2026-04-23 (Sprint 3 Phase 4)
**Owner:** Engineer executes, Ross triages

---

## Update Rules

### Rule 1: Update at session end
SPRINTS.md must be updated at the end of every session that produces sprint status changes.
Do not batch updates across multiple sessions.

### Rule 2: Commit together
When a sprint completes, mark it completed in the same commit that ships the final code.
This keeps the documentation in sync with the codebase at every commit.

### Rule 3: Immediate status changes
When a sprint is deferred, killed, or superseded, update the entry immediately with:
- New status
- Date of change
- Reason for change
- What replaces it (if superseded)

### Rule 4: last_verified semantics
The `last_verified` field gets bumped when:
- The section's status is intentionally confirmed against reality (audit)
- NOT merely when the section is edited

A typo fix does not bump `last_verified`. A status audit does.

### Rule 6: Deferred maintenance → SPRINTS.md only (added 2026-05-26)

When work is **intentionally held out** of a merge, **deferred** for bandwidth, or **known incomplete** but not scheduled as an active sprint:

1. Add or update an entry in **`SPRINTS.md` → DEFERRED MAINTENANCE** (index row + detail subsection).
2. Assign an ID: `{DOMAIN}-DEFER-{NNN}` (feature) or `MAINT-DEFER-{NNN}` (process/docs/infra).
3. Include: why deferred, restore trigger, `last_verified`.
4. Do **not** rely on orphan docs, PR comments, or chat-only notes as the system of record.

Domain-specific docs may elaborate but must cite the SPRINTS ID.  
**Anti-pattern:** Held out of a PR with no registry entry (see CAM intent routers, `545fccad`).

---

### Rule 7: Governance convergence tail → `GOV-CONVERGE-*` in SPRINTS.md (added 2026-05-28)

May 2026 governance sprint **tail** items register as `GOV-CONVERGE-{NNN}` in **SPRINTS.md** (same parking lot as `CI-RED-*`). Keep entries self-contained; cite audit docs for detail only. Mark **Path:** `MVP` / `EXT` / `HYG`. CI failures → `CI-RED-*`, not GOV-CONVERGE.

---

### Rule 5: Commit hash requirement for completion claims (added 2026-04-26)

**Every completion claim requires three elements:**

1. **Commit hash** that performed the work
2. **File paths** that were touched
3. **Verification method** (test passed, endpoint responds, import check, etc.)

Without all three, the status is **aspirational, not reportorial**.

**Example of valid completion entry:**
```
| File | Status | Verification |
|------|--------|--------------|
| `soundhole/spiral_geometry.py` | ✅ Migrated (9397c055) | imports DxfWriter, 0 ezdxf.new calls |
```

**Example of INVALID completion entry:**
```
| File | Status |
|------|--------|
| `soundhole/spiral_geometry.py` | ✅ Migrated 2026-04-23 |
```

The second form has no commit hash and no verification method. It cannot be trusted.

**Existing entries without commit hashes** should be treated as unverified claims
and flagged for re-verification before any work depends on them.

**Origin:** This rule was added after the 2026-04-26 verification audit found
10/12 DXF migration claims in Sprint 3 were false — status was entered without
work being performed. See docs/audit/sprints_md_verification_2026-04-25.md.

---

### Rule 8: Residual Obligations Check (added 2026-08-10)

> **Rule placement:** new rules append here, at the end of the rule list, in the order they were added.
> Rules 1–7 are historically out of numeric order; do not insert into that sequence — appending keeps
> `git blame` legible and stops a new rule displacing an older one.

**The rule.** A tranche or PR completing does **not** complete its parent program. Before marking any
sprint or program `RESOLVED` / `COMPLETE` **at program level**, every material residual obligation must
already have a durable disposition in `SPRINTS.md` and/or an authoritative residual matrix cited from
the SPRINTS ID.

```text
PR / tranche COMPLETE   ≠   PROGRAM COMPLETE
```

**Checklist.** Inspect each of these for residual language — *deferred, pending, out-of-scope,
owner-action, follow-up, unresolved, blocked, remaining, later*, or equivalent:

- [ ] Dev Order and implementation notes
- [ ] Tests and witnesses (including what was *not* run)
- [ ] PR review threads and closeout documents
- [ ] Findings discovered during the work, including automation PRs opened *by the merge*
- [ ] Each residual mapped to a durable disposition — never left only in prose

**Anti-pattern.** Merging a bounded remediation while residuals live only in prose, review comments,
automation PRs, or chat. Generated PRs are **evidence requiring adjudication**, not one-PR-per-item
implementation authorization.

**Origin.** PR #253 (Tier-1 `COMPLETE`) created Dependabot intake and its merge immediately produced
five version-update PRs, #254–#258. Consolidated in
`docs/ci/DEP_SEC_001_RESIDUAL_DISPOSITION_2026-08-10.md` under `DEP-SEC-001B`.

---

## Timestamps

Every sprint section includes:
```
**Status:** [status]
**last_verified:** YYYY-MM-DD
```

The `last_verified` date indicates when the status was confirmed to match reality,
not when the sprint was created or last edited.

---

## Recurring Audit

### Trigger conditions (either one)
- **Time-based:** Every ~90 days from last audit
- **Size-based:** When SPRINTS.md exceeds 800 lines

### Process
1. **Mechanical audit** — Engineer verifies each sprint's claimed status against repo state
2. **Triage** — Ross reviews audit findings, approves/rejects recommendations
3. **Execute** — Engineer applies approved corrections
4. **Maintenance** — Update `last_verified` timestamps on verified sections

### Deliverables
- Audit report document (e.g., `docs/audit/sprints_audit_YYYY-MM-DD.md`)
- Updated SPRINTS.md with corrections and fresh timestamps

### Reference
First audit completed 2026-04-23 — see `docs/audit/sprints_audit_2026-04-23.md`

---

## CI Enforcement

**Status:** DEFERRED — solo-dev project, not worth implementation cost currently

When the team grows beyond one developer, consider adding:

**Option A — pre-commit hook:**
Warns if code changes touch files named in active sprints without corresponding
SPRINTS.md updates. Advisory only (not blocking), prints suggestion.

**Option B — CI check:**
Runs on PR. Warns if SPRINTS.md hasn't been touched in the last 14 days when the
repo has seen significant commits. Advisory message in PR comment.

Either approach fits. Decision deferred until team size warrants the overhead.

---

## Anti-patterns to avoid

1. **Status inflation** — Marking sprints complete without verifying deliverables exist
2. **Location drift** — Claiming files exist at paths that don't exist
3. **Stale open items** — Leaving resolved items unmarked in task lists
4. **Phantom tech debt** — Marking regressions as fixed without re-verifying
5. **Five-month drift** — Going multiple months without status audit
6. **Undocumented completion** — Marking tasks ✅ without commit hash or verification method (added 2026-04-26)
7. **Untracked deferral** — Holding work out of a merge without a DEFERRED MAINTENANCE entry in SPRINTS.md (added 2026-05-26)
8. **Unresolved residuals in prose** — Marking a program resolved while deferred/pending/out-of-scope/owner-action items remain only in closeout prose, PR comments, or automation PRs without a durable disposition (added 2026-08-10; see Rule 8)

The Sprint 3 audit (2026-04-23) found examples of patterns 1-4.

The Sprint 3 verification audit (2026-04-26) found 10 instances of pattern 6:
completion claims entered without any work being performed. See Rule 5 above
for the commit hash requirement that prevents this pattern.

The recurring audit process exists to prevent pattern 5.
