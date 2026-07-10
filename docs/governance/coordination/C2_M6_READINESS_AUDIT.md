# C2 — M6 Readiness Audit (Pre-Ratification Freeze)

**Class:** Read-only engineering audit artifact (NOT a governance packet, NOT a decision).
**Repo:** `luthiers-toolbox`
**Audit anchor:** `origin/main` @ `d133a054` — every finding below is a point-in-time
observation verified at this SHA on **2026-07-10**, not a standing claim. Re-verify before acting.
**Verdict scope:** factual findings only; this document makes no recommendations and grants no authority.

> **Purpose.** Confirm the merged C2 stack is ready for a future M6 owner-ratification event
> **without** changing any code, runtime, or governance. This is the final engineering audit before
> the first canonical approver could ever be ratified. It names no approver and seeds nothing.

---

## Findings summary (the 7 audit questions)

| # | Question | Finding (as of `d133a054`, 2026-07-10) |
|---|---|---|
| 1 | Is the canonical authority pipeline complete? | **Yes** — ladder M1/M2–M5 merged (§1). |
| 2 | Is every merged governance artifact internally consistent? | **Yes** — constants, cross-links, and runtime agree (§3, §6). |
| 3 | Does runtime still fail closed? | **Yes** — allowlist empty `frozenset()` (§2, §5). |
| 4 | Can verified authority only occur through owner ratification? | **Yes** — only a seeded approver id can flip the state; allowlist is empty (§5, §7). |
| 5 | Are there any dangling references remaining? | **No** — all referenced docs resolve, incl. the `arbitration/` path (§6). |
| 6 | Can any implementation path bypass governance? | **No** — three independent re-checks all route through one fail-closed helper (§5). |
| 7 | Is M6 now purely an owner decision? | **Yes** — not engineering, not documentation, not implementation (§7). |

---

## 1. Governance Ladder

All four milestones observed merged on `origin/main` (immutable merge commits):

```
M1/M2  Canonical Process + Authorization Anchor ... #202  cbde06d9
M3     Canonical Approver Framework ............... #206  c06ecae4
M4     Governance Consistency Audit ............... #207  fc95cfc1
M5     First-Approver Ratification Packet ......... #208  cec253ac
```

Verify: `git log --oneline origin/main | grep -E '#202|#206|#207|#208'`.

---

## 2. Runtime State

`services/api/app/cam/canonical_geometry_process_policy.py:132`:

```python
"approvers": frozenset(),  # EMPTY — fail-closed until owner ratifies
```

- **Empty:** the approver id allowlist is `frozenset()`.
- **Fail-closed:** with no id present, every approval — including a correctly-roled `owner` —
  resolves to `unverified_pending_governance`.
- **Unchanged:** the anchor has not been seeded since it shipped in #202.

Verify: `git grep -n '"approvers": frozenset()' services/api/app/cam/canonical_geometry_process_policy.py`.

---

## 3. Canonical Constants

Recorded from the policy module (no forked literals found elsewhere):

| Constant | Value | Location |
|---|---|---|
| Canonical process id | `body-geometry-canonicalization` | `policy.py:20` |
| Canonical process version | `v1` | `policy.py:21` |
| Approval rule id | `c2-process-exclusive-canonical-authority-v1` | `policy.py:22` |
| Eligible roles | `reviewer`, `owner` | `policy.py:131` |

The anchor (`policy.py:129–134`) and the M5 packet (§3) key on exactly these constants.

Verify: `git grep -n c2-process-exclusive-canonical-authority-v1`.

---

## 4. Authority Boundary

Observed consistent with the GAMS spec (`GAMS_GEOMETRY_AUTHORITY_MAPPING_SPEC.md`) and the
consistency report (#207 §4):

| Source | Role in the authority model |
|---|---|
| Vectorizer | evidence / candidate |
| IBG | evidence / candidate |
| DXF | representation (never authority) |
| CAM | operational consumer |
| Canonical process pipeline | the sole authority |

Code enforces the negative direction: `authority_state_is_representation_derived()`
(`policy.py:72–86`) rejects any authority state inferred from format/route/storage — forbidden
tokens include `dxf, svg, step, stp, route, storage, filename, format, path, representation`.
`APPROVED_CANONICAL_PROCESSES` (`policy.py:40–50`) covers source roles
`evidence, candidate, governed_evidence_candidate, human_reviewed_candidate, existing_canonical`.

---

## 5. Enforcement Boundary

- **Authorization anchor exists** — `AUTHORIZED_CANONICAL_APPROVERS` (`policy.py:128`).
- **Verified path exists** — `VERIFIED_GOVERNED_PROCESS` is an allowed authentication state
  (`policy.py:31–33`).
- **Verified path is unreachable** — the only function that can grant it,
  `is_authorized_canonical_approver()` (`policy.py:138`), requires **both** an allowed role
  **and** an explicit approver id in the (empty) allowlist; a `system:` actor is never authorized.
- **Fail-closed is enforced at three independent points, all routed through that one helper**
  (mint-time and validation-time semantics cannot diverge):
  1. **Mint** — `stamp_canonical_process_authentication()` returns
     `VERIFIED_GOVERNED_PROCESS if authorized else UNVERIFIED_PENDING_GOVERNANCE`
     (`canonical_geometry_process_approval.py:451–459`).
  2. **Model validator** — re-asserts authorization on any record claiming the verified state
     (`canonical_geometry_process_approval.py:248`).
  3. **Reference boundary** — `validate_canonical_process_approval_record()` re-checks
     (`canonical_geometry_process_approval.py:377`), and `GeometryAuthorityReference` rejects a
     directly-constructed/rehydrated reference asserting a verified state it did not legitimately
     inherit (`geometry_authority_reference.py:269`).

**No bypass path was found:** a directly-constructed or rehydrated record/reference cannot assert
verified authority the anchor would not grant. With the allowlist empty, all three points resolve
to `unverified_pending_governance`.

Verify: `git grep -n 'is_authorized_canonical_approver\|VERIFIED_GOVERNED_PROCESS' -- '*.py'`.

---

## 6. Documentation Integrity

Present in `docs/governance/coordination/`: `GAMS_GEOMETRY_AUTHORITY_MAPPING_SPEC.md`,
`C2_CANONICAL_APPROVER_RATIFICATION.md` (framework, #206), `C2_GOVERNANCE_CONSISTENCY_REPORT.md`
(#207), `C2_FIRST_CANONICAL_APPROVER_RATIFICATION_PACKET.md` (#208).

- The M5 packet cross-links the framework, GAMS, #206 and #207 — resolved.
- The consistency report's "Artifacts Reviewed" table lists paths **relative to
  `docs/governance/`**; the one non-obvious entry, `arbitration/C2_GEOMETRY_AUTHORITY_FRAMEWORK.md`,
  **resolves** to `docs/governance/arbitration/C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` (present).
- **No broken or orphan references found** among GAMS / framework / consistency report / M5 packet.

---

## 7. Outstanding Governance

```
Remaining work:

Owner ratification (M6)

Not engineering.
Not documentation.
Not implementation.
```

M6 is the human seed of `AUTHORIZED_CANONICAL_APPROVERS`. Until the repository owner ratifies a
first approver id (a separate, isolated, owner-authorized commit — framework §4.1 / §8, M5 packet
§5/§7), the allowlist stays empty and `verified_governed_process` stays intentionally unreachable.
That is the correct and intended state; it is a reserved governance act, not debt.

---

## Exit condition

Once this audit is merged, the C2 **engineering** program is complete. No further engineering,
documentation, or implementation work is required or authorized. Future work begins only if and
when the repository owner initiates M6 by ratifying the first canonical approver.
