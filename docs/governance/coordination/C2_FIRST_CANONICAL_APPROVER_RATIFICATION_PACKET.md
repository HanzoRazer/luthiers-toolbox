# C2 — First Canonical Approver Ratification Packet (M5)

**Status:** DRAFT — decision packet awaiting owner ratification
**Class:** Governance decision-instance packet (not an implementation document, not a framework)
**Milestone:** M5 — First Canonical Approver Ratification (prep)
**Repo:** `luthiers-toolbox`
**Base:** `origin/main` @ `fc95cfc1` (PR #207 — C2 governance consistency report — merged)
**Governs the anchor:** `AUTHORIZED_CANONICAL_APPROVERS`
(`services/api/app/cam/canonical_geometry_process_policy.py`)
**Decision authority:** Repository owner (a human governance act — not decidable by software)

> **This packet does not name an approver, does not seed the allowlist, and does not
> change runtime behavior.** It prepares the single owner decision required to mint the
> first verified canonical authority, so that decision can be made cleanly and then
> implemented as a separate, isolated commit.

---

## 0. Relationship to the existing framework (read this first)

This packet is a **decision instance**, not a second framework. The general governance
framework already exists and is **not** reopened or duplicated here:

- **Framework (merged, PR #206):** `C2_CANONICAL_APPROVER_RATIFICATION.md` — defines the
  fixed frame (§2), the decision to be answered (§3), the approver **lifecycle**
  (add / revoke / emergency, §4), the ratification checklist (§5), the append-only
  approver register (§6), and audit invariants (§7).
- **This packet (M5):** the concrete, fill-in decision package for the **first** approver.
  It instantiates framework §4.1 step 1 (*Proposal*) and drives framework §5 (*Ratification
  checklist*). Procedures for adding/removing/auditing approvers are **owned by the
  framework** and referenced here, not restated.

Where this packet and the framework could ever disagree, the merged framework and the
runtime anchor are authoritative; this packet is amended to match them.

---

## 1. Purpose

Prepare the owner decision required to seed the **first** canonical approver into
`AUTHORIZED_CANONICAL_APPROVERS`. When (and only when) the owner ratifies the decision in
§5, a **separate** implementation commit (§7) adds the ratified approver id and its tests.
Nothing in this packet grants authority or changes runtime behavior.

**Dependency note (M4 / PR #207).** This packet may proceed as a draft decision artifact
whether or not the M4 consistency report has merged. Final ratification should reference the
latest governance consistency state. *(As of the base commit `fc95cfc1`, the M4 consistency
report is present — that commit is the PR #207 merge — but ratification should re-confirm the
then-current consistency state rather than rely on this note.)*

---

## 2. Current runtime state (verified against code)

Verified read-only from `services/api/app/cam/canonical_geometry_process_policy.py` at base
`fc95cfc1`:

```text
AUTHORIZED_CANONICAL_APPROVERS is empty and fail-closed.
No actor can currently mint verified_governed_process.
```

The anchor entry exists so its shape is reviewable, but its approver id allowlist is
`frozenset()`. Authorization requires **both** an allowed role **and** an explicit approver
id in the allowlist; a role alone is never sufficient, and a `system:` actor is never
authorized. Because the id allowlist is empty, every approval — including one from a
correctly-roled `owner` — resolves to `unverified_pending_governance`.

---

## 3. Ratification target (fixed process frame — verified constants)

These values are **not** decided by this packet; they are the ratified constants the first
approver decision must key on (no forked literals). Verified read-only from the policy module
at base `fc95cfc1`:

| Element | Ratified value | Source (policy module) |
|---|---|---|
| Canonical process id | `body-geometry-canonicalization` | `PROPOSED_CANONICAL_PROCESS_ID` |
| Canonical process version | `v1` | `PROPOSED_CANONICAL_PROCESS_VERSION` |
| Approval rule id | `c2-process-exclusive-canonical-authority-v1` | `PROPOSED_APPROVAL_RULE_ID` |
| Eligible roles | `reviewer`, `owner` | `AUTHORIZED_CANONICAL_APPROVERS[...]["roles"]` |
| Approver id allowlist | **EMPTY** (`frozenset()`) — fail-closed | `AUTHORIZED_CANONICAL_APPROVERS[...]["approvers"]` |
| Verified state (currently unreachable) | `verified_governed_process` | `VERIFIED_GOVERNED_PROCESS` |
| Fail-closed baseline | `unverified_pending_governance` | `UNVERIFIED_PENDING_GOVERNANCE` |

---

## 4. Candidate approver field (TBD — intentionally blank)

Left blank by design. Naming the first approver is the owner's act (§5), not this packet's.

```text
candidate approver id:   TBD
candidate approver role: TBD   (must be one of: reviewer, owner)
```

Recording guidance (from framework §3.1): the approver id must be a stable id keyed to a real
accountable person (e.g. `owner:<name>` or `reviewer:<name>`), **never** a role token alone,
and **never** a `system:` actor.

---

## 5. Required decision (owner completes)

The owner must explicitly ratify the following statement, filling in the two blanks:

```text
Add <approver_id> with role <role> to the canonical approver allowlist for
body-geometry-canonicalization v1 under c2-process-exclusive-canonical-authority-v1.
```

On ratification, complete the framework's ratification checklist
(`C2_CANONICAL_APPROVER_RATIFICATION.md` §5) and record the decision in the framework's
append-only approver register (§6). This packet does not advance any status by itself.

---

## 6. Non-goals

This packet does **not**:

- seed or edit the `AUTHORIZED_CANONICAL_APPROVERS` allowlist;
- name, propose, or imply a first approver;
- grant any canonical authority;
- change any runtime behavior;
- modify GAMS or any geometry-authority mapping;
- merge, or authorize the merge of, any implementation;
- add C3 schema/CI enforcement;
- reopen the ratified process frame (§3) or the framework (PR #206).

---

## 7. Post-ratification implementation (deferred — DO NOT perform here)

After — and only after — §5 is ratified, the seed lands as a **separate** implementation
commit (per framework §4.1 step 3 / §8), containing **only** the anchor change plus tests and
referencing this packet and the ratification decision. It is not performed by this packet and
not performed by any automated agent on its own authority. The change is a single line:

```python
# services/api/app/cam/canonical_geometry_process_policy.py
"approvers": frozenset({"<ratified-approver-id>"})  # was: frozenset()
```

---

## 8. Verification after the future seed (must all pass)

The future implementation commit (§7) is complete only when regression tests confirm:

- an **authorized** approver (ratified id + allowed role) mints `verified_governed_process`
  for the ratified process id / version / rule;
- an **unauthorized** approver (correct role, id **not** on the allowlist) remains
  `unverified_pending_governance`;
- a `system:` actor remains rejected regardless of the allowlist;
- the anchor contains **only** ratified approver id(s) — the runtime allowlist equals the set
  of currently-active approvers in the framework's §6 register (audit invariant);
- the audit trail (commit + register row) references this ratification packet.

---

## 9. Scope discipline of this packet

**This document does NOT** name the first approver, seed or edit
`AUTHORIZED_CANONICAL_APPROVERS`, change any code, grant any authority, or merge anything. It
is a decision packet awaiting a human ratification decision. The remaining work is not about
*building* authority — the mechanism is already built and fail-closed — it is about the owner
*deciding* who first holds it.

---

## 10. Deferred milestone

```text
M6 — First Canonical Approver Seed
```

A separate future PR that requires: an explicit owner-ratified approver id; its role; the
process id / version / rule (§3); the one-line allowlist seed (§7); and runtime verification
(§8) that `verified_governed_process` becomes reachable **only** for that ratified approver.
