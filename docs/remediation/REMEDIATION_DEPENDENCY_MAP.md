# BR-001 — Remediation Dependency Map

> Relationships among retained items ([adjudication ledger](BACKLOG_ADJUDICATION_LEDGER.md)): blockers,
> prerequisites, shared root causes, same-subsystem clusters, obsolescence, and unsafe-to-parallelize
> pairs. Textual map (no graphical tooling required).

## Blockers / prerequisites

| Item | Depends on / blocked by | Nature |
| ---- | ----------------------- | ------ |
| BR-028 (endpoint sprawl consolidation) | **BR-008** (CI-RED-016B consumer map) | prerequisite — cannot consolidate 1,132 endpoints safely without the consumer map |
| BR-018 (any R2000 DXF change) | **owner fork decision** (sanction vs R12-safe) | blocked-open — "Do NOT execute until fork resolved" |
| BR-014 (SPINE-002/003/004) | **owner merge decision** | blocked — same held-draft pattern as SPINE-005 |
| BR-020 (residual reds #7, #12) | **owner product decisions** (authority lock; zone x-gating) | blocked-open |
| BR-019 (auth/DB stubs) | **owner scope decision** (is a user/auth system in scope?) | blocked-open |
| BR-029 (52 high-risk formulas) | **owner verification plan** | blocked-open (evidence-integrity) |
| BR-007 (CI-RED-020B execution) | verify PR #177 merge-instability resolved | soft prerequisite (reportedly resolved same-day) |
| Confident ranking of test-state items (BR-003, BR-013, BR-020) | **Wave-0 current-red pytest run** | prerequisite — **run 2026-07-20** (21 failed/8155 passed, local toolchain; see [WAVE_0_VERIFICATION.md](WAVE_0_VERIFICATION.md)). CI-stack (3.11) confirmation still recommended. Does **not** gate BR-002A (the current next Dev Order), which is read-only archaeology. |

## Shared root causes

- **BR-001 + BR-004** — both are `store_artifact` kwarg-handling bugs (saw_lab vs rmos endpoint paths).
  Likely one underlying store-layer signature gap. **Fix together / dedup**; confirm the duplicate
  relationship when scoping. BR-002 (`list_runs_filtered` kwarg) is the *same class* of bug (store-layer
  signature vs endpoint call) in the adjacent `rmos/runs_v2` module — natural to fix in one pass.
- **BR-021** (suppressed `client_lint_build` + `vue_decomposition` gates) shares a root with the
  frontend's 400+ TS errors — burning those down is what re-enables both gates.

## Same-subsystem clusters (safe to batch)

| Cluster | Items | Rationale |
| ------- | ----- | --------- |
| **saw_lab / rmos store-layer kwargs** | BR-001, BR-002, BR-004 | **NOT a single isolated pass** (scope-corrected 2026-07-21): BR-002 crosses the central `runs_v2` store + shared `store_filter.matches_index_meta`; sequenced as BR-002A (archaeology) → BR-002B (repair). xfail tests are acceptance for 002B. |
| CI-RED remediation lane | BR-007, BR-008, BR-009, BR-022 | same governance/CI lane; sequence behind consumer map where noted |
| Project-Spine adoption | BR-014 (SPINE-002/003/004) | one owner merge decision covers the cluster |
| CAM translation tail | BR-005 (7D/E/F) | "pending tests+commit" for one authorized feature set |
| DXF / R2000 | BR-018, BR-024 (superseded into BR-018) | gated on the owner fork |

## Obsolescence / already-resolved

- **BR-024** (R2000 `ezdxf.new` regression) — **superseded by BR-018**, not resolved. The specific
  hardcoded `ezdxf.new("R2000")` call the audit cited was refactored into the version-parameterized
  `app/util/dxf_compat.py`, but R2000 remains a supported DXF output (~29 `app/` files, incl. the
  audited `archtop_floating_bridge.py`). Whether R2000 is still emitted / should be sanctioned is the
  open BR-018 fork; grep-absence of the literal string does not settle it.
- **BR-025** (40-failure baseline) — obsoleted by ratchet rebaselining.
- **BR-026** — closed 2026-05-30.

## Unsafe to perform concurrently

- **BR-028** (endpoint consolidation) must not run concurrently with **BR-016** (instrument_geometry
  monolith migration) or **BR-013** (new RMOS route) — all three change the mounted-route surface and
  would race the router-count baseline / endpoint-truth gates. Serialize behind the consumer map.
- **BR-021** gate re-blocking must land *after* the TS-error burndown, not during, or CI goes red.

## Independent / standalone (no blockers)

BR-006 (8J reconstruction — but high data-loss urgency), BR-010 (NECK-A frontend), BR-011 (three-loop
doc removal), BR-015 (rmos strict=True), BR-017 (IBG-224 re-land). These can be scheduled on
consequence alone.

**BR-043** (tonewood radiation-ratio scale) is also standalone, with three ordering notes:

- **No dependency on PR #244.** The MB Sound corpus corroborates the target scale (vendor SRC medians
  12.28–14.00 on the unscaled `c/rho` scale) but is *evidence only* — not runtime authority, not
  imported, not hard-coded by the repair. BR-043 may land before, during or after #244.
- **Should precede** any recommendation-quality evaluation. Scoring the current recommender is
  meaningless while its acoustic term is uniformly 0.0.
- **Should precede** any centralized generator system consuming material rankings, for the same reason.

Its two related findings — `specific_moe` scaling, and the frontend `StiffnessIndexPanel` threshold
mismatch on an independent local data path — are deliberately *not* bundled; see the BR-043 register
entry. The frontend finding is queued as **BR-044**.

**BR-043 → BR-044** (ordering, not blocking):

- BR-043 establishes the canonical backend scale.
- BR-044 must use that adjudicated scale.
- **BR-044 does not block BR-043.** The reverse edge is ordering only.
- **The authority decision is settled** (`740bee94`): correct the local producer to `c/ρ`; do **not**
  delete it in favour of the backend value, which is not transported to this panel.
- **BR-044B does not depend on PR #244.** MB Sound is unrelated to this repair.
- **Backend-value transport is deferred** — a separate additive contract change
  (`ApiTonewoodRecord` + local `TonewoodEntry` + `apiRecordToEntry` + precedence + parity).
- BR-044 **should be completed before frontend material rankings are consumed by the centralized
  generator system**, for the same reason BR-043 should precede recommendation-quality evaluation:
  a degenerate rating that marks every wood "Excellent" carries no signal for a downstream consumer.

**BR-043 → BR-045** (ordering, not blocking). BR-045 is the `specific_moe` cross-surface scale split,
promoted out of BR-043's secondary-index adjudication. BR-043 is **RESOLVED** (merged `a34b6f5d`).
BR-045 is **RESOLVED** (implementation merge `f12f88c2` / PR #247; post-merge witness on `969bdbdc`
via administrative closeout BR-045A). Historical blocker was an owner unit ruling (`c²/10⁶`,
2026-08-04), not engineering capacity.

**BR-044 and BR-045 are siblings, not duplicates** — different metrics (radiation ratio vs specific
MOE), different failure modes (rating collapse vs latent inconsistency), and BR-045 spans both backend
and client while BR-044 is client-local. Neither blocks the other; they may be scoped together only if
an owner rules on a **unit profile for derived acoustic indices as a class**, which would settle both.

**BR-045 closure does not authorize BR-044.** BR-044 is now **CONFIRMED / PROOF COMPLETE /
NOT AUTHORIZED**. Closing it will **not** complete the broader unit-profile program, and
**centralized generators must not consume the defective frontend profile** while it stands. Closing BR-045 also does **not** complete the broader unit-profile
consolidation program for derived acoustic indices.

**Shared root cause — worth recording once.** BR-043, BR-044 and BR-045 are three instances of the same
failure mode: a derived acoustic index whose unit is documented in prose, implemented independently per
surface, and compared against constants written by a third author. Fixing them one at a time works but
does not stop the fourth. The durable fix is a declared unit profile per index, asserted on every
surface that publishes it. That is a candidate Dev Order in its own right and should precede any
centralized generator system consuming material indices.
