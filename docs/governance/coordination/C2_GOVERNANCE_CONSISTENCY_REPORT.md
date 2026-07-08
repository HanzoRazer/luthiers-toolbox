# C2 Governance Consistency Report (M4)

**Status:** DRAFT — under review. An audited statement of repository state; not ratified.
**Audit basis:** `origin/main` at `c06ecae4` (PR #206 merged 2026-07-08), read-only worktree.
**Scope:** Verify that the C2 canonical-authority implementation faithfully reflects the ratified governance, with no undocumented drift. Consolidation pass — no authority granted, no runtime change, no approver seeded.

**Classification legend:** ✅ Consistent · ⚠ Deferred (by design, not a defect) · ❌ Conflict · ℹ Informational

---

## Milestone Status

| Milestone | Status |
|---|---|
| M1 — Canonical Process Infrastructure | Complete |
| M2 — Authorization Infrastructure (empty, fail-closed anchor) | Complete (PR #202) |
| M3 — Governance Publication (approver ratification framework) | Complete (PR #206) |
| M4 — Governance Consistency Audit | **This report** |
| M5 — First Canonical Approver Ratification | Deferred (owner decision) |

This report is the M4 capstone: it verifies that M1–M3 (implementation + published governance) agree, so that any future governance act — notably M5, seeding the first approver — proceeds from a confirmed-consistent baseline. This document grants no authority and takes no M5 action.

---

## 1. Executive Summary

The C2 governance stack from **PR #202 through PR #206** is **internally consistent**, and the implementation in `services/api/app/cam/` **faithfully reflects** the ratified governance. No governance-vs-governance conflicts and no governance-vs-implementation drift were found.

- The eight-document governance corpus agrees on every audited dimension (authority model, promotion model, fail-closed default, representation-vs-authority, process/pipeline-exclusive authority, deferred items). Later documents **narrow and operationalize** earlier ones rather than contradict them.
- **Geometry-origin remains OPEN.** No document — including the most recent (2026-07-08) — closes it. It is now gated behind a *built, empty, fail-closed* authorization anchor rather than an undesigned gate.
- The runtime honors the governance: the approver allowlist ships **empty and fail-closed**, `verified_governed_process` **cannot be minted**, `unverified_pending_governance` is the only reachable state, and there is **no back door**.
- **One narrative correction (not a repo defect):** a "PR #207" referenced in a draft handoff **does not exist** (latest is #206), and "geometry authority router integration [complete]" is imprecise — a router *surface* exists, but no authority-based *routing/dispatch* layer does. These are handoff-narrative inaccuracies; the repository itself is consistent. Recorded here (§6, ℹ) so the assumption is not institutionalized.

**Overall assessment:** The governance program is ready for the future owner-ratification event **without additional architectural work**. No remediation is required to make governance and implementation agree.

---

## 2. Artifacts Reviewed

### Governance documents (8)
| # | Path | Date | Banner |
|---|------|------|--------|
| 1 | `arbitration/C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` | 2026-05-18 | Decomposition Complete — Awaiting Arbitration |
| 2 | `coordination/C2A_GEOMETRY_AUTHORITY_PACKET.md` | 2026-05-18 | RATIFIED (narrow) |
| 3 | `C2_STATUS_RECONCILIATION_2026-06-23.md` | 2026-06-23 | Authoritative snapshot |
| 4 | `coordination/GAMS_GEOMETRY_AUTHORITY_MAPPING_SPEC.md` | 2026-06-27 | Coordination Spec |
| 5 | `coordination/C2_CANONICAL_APPROVER_RATIFICATION.md` | 2026-07-08 | DRAFT — awaiting owner ratification |
| 6 | `C2C3_AUTHORITY_MODEL_REFINEMENT_DEFERRED.md` | 2026-07-01 | Deferred by design |
| 7 | `CANONICAL_AUTHORITY_MAP.md` | 2026-05-16 | Authoritative |
| 8 | `GEOMETRY_AUTHORITY_DECOMPOSITION.md` | 2026-05-18 | DRAFT for ratification |

### Implementation (`services/api/app/cam/` + routers)
- `canonical_geometry_process_policy.py` — vocabulary, coverage registry, authorization anchor, `is_authorized_canonical_approver`
- `canonical_geometry_process_approval.py` — approval record + authentication decision + invariant validators
- `canonical_geometry_process_approval_event.py` — governed event id derivation
- `geometry_authority_reference.py` / `_factories.py` / `_registry.py` / `_taxonomy.py` / `_validation.py` — reference model (CAM Dev Order 7T)
- `routers/cam/geometry_authority_router.py` — HTTP surface; mounted via `router_registry/manifests/cam_manifest.py:257-259`

---

## 3. Confirmed Consistencies (governance ↔ governance)

| Dimension | Verdict | Evidence |
|---|---|---|
| Authority model | ✅ | Converges on "authority requires explicit governance/human ratification; visibility/consumption/location/format ≠ authority." Framework layers (`1:191`), Map invariants 5/6/7 (`7:194-196`), GAMS two-axis (`4:41`), Approver "the canonical process decides" (`5:29-33`). Doc #5 sharpens to *process-exclusive*; earlier docs are *map/gate-based*. Complementary. |
| Promotion model | ✅ | Governed promotion event / human ratification throughout: `2:709`, `4:130`, `5:79-80`, `7:199`, `8:214`. No doc permits ad-hoc promotion. |
| Fail-closed default | ✅ / ⚠ | Only doc #5 states an explicit *runtime* fail-closed baseline (`5:75-82,143,183`); others are silent or say "non-canonical by default" (`4:127`). #5 realizes what the others implied — silence ≠ conflict. |
| Representation vs authority | ✅ | Unanimous: `1:272`, `4:59-69,184`, `5:106-108`, `7:38,194-196`, `8:75,242`. Strongest agreement in the corpus. |
| Process/pipeline-exclusive authority | ✅ | #5 hardest ("Everything flows through one canonical process," no special vectorizer/IBG/DXF/template/human authority, `5:34-37`); #4 by exclusion (`4:41-43`); #7 map-exclusive (`7:49`); #6 archives a stronger candidate as *non-adopted* (`6:20-27`). Directionally identical. |
| Geometry-origin status | ✅ (all OPEN) | UNRESOLVED (`1:397-398`), OPEN (`2:20`; `3:22,44`), open C2 gate (`4:19-21`), not decided (`6:47,50-52`), Open Questions (`8:279`). No document asserts a closed origin. |
| Deferred items | ✅ / ℹ | Disjoint, mutually-referencing deferrals: IBG federation → C2-C (`2:47,717`); enforcement/schema/CI → C3 (`3:50-51`, `4:280`); two-axis refinement → C2/C3 seam (`6:3`); first approver → owner ratification (`5:22-24`). No two docs defer the same item to incompatible destinations. |

The corpus's own acknowledged tension — stale status banners (`GOVERNANCE_STACK_INDEX` "Not Started" vs. packet banners) — is explicitly reconciled in doc #3 as "different artifacts, not a status conflict" (`3:31-35`), and doc #2 self-corrects its own stale DRAFT banner (`2:20`). **Not a conflict.**

---

## 4. Confirmed Implementation Matches (governance ↔ runtime)

| Governance requirement | Implementation | Verdict |
|---|---|---|
| Authority is process-exclusive; the canonical *process* decides (`5:29-33`) | Authentication is decided once by `is_authorized_canonical_approver` on the approval record; no special vectorizer/IBG/DXF/template/human path exists | ✅ `policy.py:138-196`, `approval.py:451-460` |
| Ships **empty and fail-closed**; nothing mints verified authority (`5:17-19,75-82`) | `AUTHORIZED_CANONICAL_APPROVERS[...]["approvers"] = frozenset()` — empty | ✅ `policy.py:128-135` |
| Only two authentication states; unverified is the fail-safe baseline (`5:77`) | `ALLOWED_AUTHENTICATION_STATES = {unverified_pending_governance, verified_governed_process}` | ✅ `policy.py:30-34` |
| `verified_governed_process` unreachable until owner ratifies (`5:81-82,156`) | Empty allowlist → final `is_authorized_canonical_approver` check fails for every principal → every approval resolves to `unverified_pending_governance` | ✅ `policy.py:190-194`, `approval.py:458-459` |
| Role alone is never sufficient — role **and** explicit approver id required (`5:79-80`) | Gate requires anchor entry + anchored rule + allowed role + approver id in allowlist; all fail-closed | ✅ `policy.py:183-194` |
| Representation/route/format never confers authority (`4:59-69`, `1:272`) | `_FORBIDDEN_SOURCE_AUTHORITY_STATE_TOKENS` includes `route`, `format`, `path`, `representation`, `storage`, `dxf`, `svg`, `step`; `authority_state_is_representation_derived()` rejects them | ✅ `policy.py:53-86` |
| No machine self-authority | `system:` actors hard-blocked before the allowlist is even consulted | ✅ `policy.py:67-69,159-163`; also `approval_event.py:67-92`, `approval.py:206-210` |
| Verified state must be provenance-backed, not hand-set (`5:106-108`) | Multi-layer re-verification: approval model validator (`approval.py:248-266`), `validate_canonical_process_approval_record` (`approval.py:377-393`), reference model backing-metadata requirement (`reference.py:269-287`); reference inherits authentication only via factory (`factories.py:133`) | ✅ |
| Legacy unapproved canonical creation is closed | `/references/canonical` returns HTTP 410 (GOV-CONVERGE-007-A); process-approved path is the only creation route | ✅ `geometry_authority_router.py:248-267,270-307` |
| **No back door** to verified authority | Only `create_canonical_process_approval_record` assigns verified, gated by the empty allowlist; no code mutates/appends the `approvers` frozenset anywhere in `services/api/app` (only a test monkeypatches in-process and separately asserts the shipped anchor is empty, `tests/cam/test_canonical_process_authorization.py:70-75,263-266`) | ✅ |

---

## 5. Confirmed Deferred Items (⚠ — by design, not defects)

1. **First canonical approver id.** The allowlist is intentionally empty; seeding it requires a *separate* repo-owner-ratified commit (`5:22-24,187-190`; `policy.py:121-127`). Not part of any shipped PR.
2. **Mechanical (CI) enforcement of the GAMS invariant.** GAMS "holds by reviewer discipline, not by gate … C3 may later enforce through schema, metadata validation, CI checks" (`4:279-291`). No mechanical gate exists yet — consistent, deferred to C3.
3. **Strict RED for canonical references lacking process-approval metadata.** Currently a transition-state warning, not a hard failure (`geometry_authority_validation.py:216-227,350`; `factories.py:52-60`). Deferred to a later enforcement PR — consistent with #2.
4. **Two-axis → invariance refinement** at the C2/C3 seam — "Deferred by design," requires a dedicated governance discussion, "must not occur opportunistically" (`6:3,36-38`).
5. **Authority-based routing/dispatch layer** — no consumer routes work on `verified` vs `unverified` state today (see §6, ℹ). Absent, not wired — a valid deferral.
6. **Cosmetic:** `PROPOSED_` identifier prefixes are retained though the vocabulary is ratified; dropping them is explicitly optional follow-up (`policy.py:17-19`).

---

## 6. Actual Inconsistencies

**No governance conflicts (❌) and no implementation drift were found.** The items below are informational/narrative, recorded so they are not mistaken for repo state.

- ℹ **"PR #207" does not exist.** A draft handoff described post-#207 state; the latest merged PR on `main` is **#206** (`c06ecae4`, ratification framework doc). There is no #207 and no open PR. Do not carry #207 into governance artifacts.
- ℹ **"Geometry authority router integration [complete]" is imprecise.** A router *surface* **does** exist and is fully wired to the approval/validation machinery: `routers/cam/geometry_authority_router.py` (CAM Dev Order 7T), mounted (`cam_manifest.py:257-259`), with endpoints that create approval records (`:270-307`), validate references (`:397-437`), retire legacy creation to 410 (`:248-267`), and emit a CI summary (`:445-465`). **However, no authority-based *routing/dispatch* layer exists** — nothing consumes `verified_governed_process` vs `unverified_pending_governance` to route work (and nothing could today, since verified is unreachable). The router's own invariants state "No endpoint authorizes execution; No endpoint allows machine output" (`geometry_authority_router.py:12-15`). The PR #205 `registry_router` symbol cleanup is **unrelated** (wood-species/model registries), not authority routing.
- ℹ **Stale status banners across the corpus** are a known, already-reconciled artifact difference (doc #3 `3:31-35`), not a live contradiction. No action beyond awareness.

---

## 7. Recommendations

Per the decision rule, recommendations are limited to contradictions / undocumented implementation / drift. Because none were found, recommendations are minimal and mostly hygiene.

1. **No reconciling changes required.** Governance and implementation agree; do not "fix" the empty allowlist, the warning-not-RED validation, or the missing routing layer — all are ratified/deferred by design.
2. **Narrative hygiene (do, low-cost):** stop numbering handoffs around individual PRs; adopt milestone framing (M1 Canonical Process Infra → M2 Authorization Infra → M3 Governance Publication [done, #206] → M4 Consistency Audit [this doc] → M5 First Approver Ratification [future]). Drop the nonexistent "PR #207" and qualify "router integration" as *surface exists, authority-routing deferred*.
3. **Optional (only if the maintainers want it):** add a one-line pointer from `GOVERNANCE_STACK_INDEX_V1` / the status index to `C2_CANONICAL_APPROVER_RATIFICATION.md` so future readers land on the current fail-closed anchor state. Cosmetic; not required for consistency.
4. **When M5 happens:** the only architectural precondition is met — seeding the first approver id is a one-line, owner-ratified change to `AUTHORIZED_CANONICAL_APPROVERS["approvers"]` in a dedicated commit; no surrounding rework needed.

---

## 8. Overall Assessment

✅ **The governance stack from PR #202 through PR #206 is internally consistent, the implementation matches the governance, no authority is granted prematurely, and the project is ready for the future owner-ratification event without additional architectural work.**

Geometry-origin remains **OPEN by design**, now gated behind a built, empty, fail-closed authorization anchor. The single verified path exists end-to-end and is correctly **unreachable** until a separate owner-ratified approver seed lands. The only inaccuracies surfaced are in *narrative/handoff* framing (a nonexistent PR #207; an over-broad "router integration complete"), not in the repository — captured here so they are corrected rather than institutionalized.

---

*Generated as a read-only consolidation audit. No branch, no commit, no PR. Returned for review before any decision on publication.*
