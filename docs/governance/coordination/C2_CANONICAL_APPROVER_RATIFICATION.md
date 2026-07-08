# C2 — Canonical Approver Ratification

**Status:** DRAFT — awaiting owner ratification decision
**Class:** Governance ratification record (not an implementation document)
**Repo:** `luthiers-toolbox`
**Anchor under governance:** `AUTHORIZED_CANONICAL_APPROVERS`
(`services/api/app/cam/canonical_geometry_process_policy.py`)
**Decision required:** Who is the first authorized canonical approver?
**Decision authority:** Repository owner (a human governance act — not decidable by software)

---

## 0. Purpose

The canonical authorization anchor is implemented and merged. It ships **empty and
fail-closed**: the mechanism to grant verified canonical authority exists, but **no
authority has been granted**. This record governs the one remaining constitutional
decision — *who may authorize the canonical process* — and specifies how approvers
are added, removed, and audited.

This document does **not** name an approver. Naming the first approver is a separate
owner-ratified decision (§5) and, if approved, a separate code commit (§8). Nothing in
this draft grants authority or changes runtime behavior.

---

## 1. Constitutional boundary being governed

The architecture answers *"who decides canonical geometry?"* precisely:

> **The canonical process decides.**
> The authorization anchor determines **who may authorize that process** — not who
> may create geometry.

Everything flows through one canonical process. There is deliberately **no** special
vectorizer authority, IBG authority, DXF authority, template authority, or human
"because I said so" authority. This record governs authorization of the *process*,
consistent with the metrology discipline: **approve the process, not the metric.**

Authority stack (established by PR #202):

```
Evidence
    │
    ▼
Canonical Process
    │
    ▼
Governed Approval Record
    │
    ▼
Authorization Anchor        ◄── governed by THIS record
    │
    ▼
Canonical Reference
    │
    ▼
Operational Consumers
```

---

## 2. What is already ratified (the fixed frame)

These are locked by the merged anchor and are **not** reopened by this record. An
approver decision must key on exactly these constants (no forked literals):

| Element | Ratified value |
|---|---|
| Canonical process id | `body-geometry-canonicalization` |
| Canonical process version | `v1` |
| Approval rule id | `c2-process-exclusive-canonical-authority-v1` |
| Allowed approver roles | `reviewer`, `owner` |
| Approver id allowlist | **EMPTY** (`frozenset()`) — fail-closed |
| Verified authentication state | `verified_governed_process` (currently unreachable) |
| Fail-closed baseline | `unverified_pending_governance` |

**Authorization requires BOTH** an allowed role **AND** an explicit approver id present
in the allowlist. Role alone is never sufficient. A `system:` actor is never authorized.
Because the id allowlist is empty, every approval — including one from a correctly-roled
`owner` — currently resolves to `unverified_pending_governance` (runtime-verified).

---

## 3. The decision this record ratifies

Ratification must answer the following. Until each is answered by the owner, the
allowlist stays empty.

### 3.1 Who may approve canonical geometry?
> **TBD — awaiting owner ratification.** (Approver identity intentionally left blank in
> this draft. Recorded as a stable approver id, e.g. `owner:<name>` or `reviewer:<name>`,
> keyed to a real accountable person, never a role token alone and never a `system:` actor.)

### 3.2 Under what role?
The approver's role must be one of the ratified roles: `reviewer` or `owner`. The role
is recorded alongside the id; the anchor checks both.

### 3.3 Under what conditions?
An approver may mint `verified_governed_process` **only** for the ratified process id,
version, and approval rule in §2, and only through the single authorization decision made
on the approval record at creation (never re-decided downstream). Conditions that any
ratified approver is bound by:

- Approval attaches to a **governed approval record**, not to raw geometry.
- The authentication decision is made once, on the record, and inherited by the reference.
- Approval does not confer authority to create geometry — only to authorize the process.
- Approval outside the ratified process/version/rule is void (fails closed).

---

## 4. Approver lifecycle procedures

These procedures are the working governance process. They are enforceable as written.

### 4.1 Adding an approver
1. **Proposal.** A named proposer records the candidate approver id, role, and rationale
   as an amendment to §3.1 / §6 of this record (or a superseding record).
2. **Owner ratification.** The repository owner explicitly approves the addition. This is a
   human act; it cannot be delegated to software, CI, or an automated agent, and an approver
   may not self-authorize.
3. **Implementation commit.** A **separate** commit adds the ratified approver id to
   `AUTHORIZED_CANONICAL_APPROVERS["approvers"]` for the ratified key (§8). The commit
   references this record and the ratification decision. It contains **only** the anchor
   change plus tests; it does not bundle unrelated work.
4. **Verification.** Tests confirm the newly-authorized approver mints
   `verified_governed_process` for the ratified process/version/rule, and that all other
   approvers/roles still fail closed.

### 4.2 Removing (revoking) an approver
1. **Trigger.** Role change, loss of accountability, compromise, or owner decision.
2. **Owner ratification.** The owner records the revocation and reason in §6.
3. **Implementation commit.** A separate commit removes the approver id from the allowlist.
   Removal is **fail-safe by construction**: an id absent from the allowlist immediately
   reverts every future approval by that id to `unverified_pending_governance`.
4. **Reference re-assessment.** Any existing canonical references that were verified by the
   revoked approver are flagged for governance review. Removal does not silently rewrite
   history; it prevents future minting and surfaces prior verifications for re-adjudication.

### 4.3 Emergency fail-closed
If the anchor's integrity is in doubt, reverting the allowlist to **empty** restores the
behaviour-preserving baseline (all approvals `unverified_pending_governance`) with no other
code change. Empty is always a safe state.

---

## 5. Ratification checklist (owner completes)

- [ ] First approver id decided and recorded in §3.1 / §6
- [ ] Role confirmed as `reviewer` or `owner`
- [ ] Conditions in §3.3 acknowledged
- [ ] Add/remove/audit procedures (§4, §7) accepted
- [ ] Separate implementation commit authorized (§8)
- [ ] This record status advanced from DRAFT → RATIFIED

Until every box is checked, the allowlist remains empty and no verified authority exists.

---

## 6. Approver register (append-only)

The authoritative human-readable record of authorization decisions. Empty until ratified.

| Date | Approver id | Role | Action (add/revoke) | Ratified by (owner) | Reason / reference |
|---|---|---|---|---|---|
| — | *(TBD — none authorized)* | — | — | — | Anchor ships empty / fail-closed |

---

## 7. Audit

- **Source of truth (register):** this §6 table — the human governance record.
- **Source of truth (runtime):** `AUTHORIZED_CANONICAL_APPROVERS` in
  `canonical_geometry_process_policy.py`.
- **Invariant:** the runtime allowlist MUST equal the set of currently-active approvers in
  §6. Any divergence is a governance defect.
- **Change traceability:** every add/revoke is (a) a row in §6 and (b) a discrete commit
  touching only the anchor, each referencing this record. `git log` over the policy file
  is the immutable audit trail.
- **Periodic review:** on each C2 governance review, reconcile §6 against the runtime
  allowlist and confirm no approver is a role token or `system:` actor.
- **Fail-closed guarantee:** because authority requires an explicit id, an audit gap or a
  lost entry degrades to *no verified authority*, never to *silent verified authority*.

---

## 8. Implementation change (deferred — not part of this draft)

Once §5 is ratified, the implementation is a single, isolated change — **not performed by
this record and not performed by any automated agent on its own authority**:

```python
# services/api/app/cam/canonical_geometry_process_policy.py
AUTHORIZED_CANONICAL_APPROVERS = {
    (PROPOSED_CANONICAL_PROCESS_ID, PROPOSED_CANONICAL_PROCESS_VERSION): {
        PROPOSED_APPROVAL_RULE_ID: {
            "roles": frozenset({"reviewer", "owner"}),
            "approvers": frozenset({ ... }),  # ← ratified approver id(s), owner-authorized
        },
    },
}
```

Everything else — the anchor, the second authentication state, single-point decision,
centralized validation, fail-closed semantics, regression coverage — is already built.

---

## 9. Milestone record (corrected)

PR #202 — canonical process authorization anchor — merged to `main`.

| Item | Value |
|---|---|
| Merge commit (squash) | `cbde06d9` |
| Final green tree (pre-squash) | `bbfbf297` |
| Anchor implementation commit | `345b3243` |
| Test suite @ anchor commit (`345b3243`) | **177 passing** |
| Test suite @ merged remediation tree (`bbfbf297` → `cbde06d9`) | **183 passing** |
| Authority granted | **None** (anchor empty / fail-closed) |
| Runtime behavior change | **None** (behaviour-preserving) |

Delivered by PR #202: canonical authorization anchor; second authentication state
(`verified_governed_process`); single-point authorization decided on the approval record
and inherited by the reference; fail-closed empty allowlist; id + role authorization
semantics; centralized authentication validation; no behavior change to existing canonical
references; regression coverage as above.

---

## 10. Scope discipline of this record

**This document does NOT:**
- name the first approver,
- seed or edit `AUTHORIZED_CANONICAL_APPROVERS`,
- change any code,
- grant any authority,
- open a PR or commit anything.

It is a governance framework awaiting a human ratification decision. The remaining work is
not about *building* authority — it is about *governing* it.
