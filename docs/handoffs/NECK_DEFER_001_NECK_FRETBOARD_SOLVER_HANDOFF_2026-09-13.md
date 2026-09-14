# NECK-DEFER-001 — Neck & Fretboard Solver: Developer Handoff

**Sprint ID:** NECK-DEFER-001 (registered in `SPRINTS.md` → DEFERRED MAINTENANCE)
**Status:** DEFERRED by owner decision, 2026-09-13. **Not started. No code in this repo.**
**Base checked:** `origin/main` @ `0679dbf6`
**Author:** Claude session `0aefef64`, for Ross (owner)

---

## Executive summary

1. **A working neck & fretboard solver exists outside the repo.** It's a single-file HTML tool, available as a
   private Claude artifact and as an offline portable copy on the owner's machine. It calculates, at **any
   station on the neck**:
   - width
   - fretboard radius: single, compound, or true cone
   - board centre and edge thickness
   - neck depth
   - a parametric back profile

   It also produces a table of every fret, 1:1 printable templates, and DXF cross-sections. A second tab solves
   the Smart Guitar neck/body joint.
2. **Its maths is verified.** The tool carries built-in acceptance tests against hand-computed values (all
   PASS), and its DXF opens cleanly in AutoCAD's engine. Evidence is in §3.
3. **The owner wants it wired into the Luthier's Toolbox** as a general, instrument-agnostic neck tool, not
   only for the Smart Guitar. §5 maps it onto the repo's 6-layer architecture and the governed DXF export lane.
4. **Do not start now.** The files this work would touch are being rewritten by unmerged branches: the Inv-037
   Phase 1 wave (R4a rewrites `routers/neck/*` and the model loader) and the stalled DXF-writer extents fix.
   Starting now guarantees conflicts and rework. §7 has the evidence.
5. **Four owner rulings are needed before any code.** The first matters most (§6):
   - **(a)** the canonical compound-radius definition
   - **(b)** the neck-angle definition
   - **(c)** ownership (Toolbox vs Smart Guitar)
   - **(d)** whether `NeckView.vue` is the canonical neck view
6. **Restore trigger:** R4a merged or abandoned; the extents fix merged; rulings (a), (c) and (d) made; an
   explicit owner GO. On restore, re-verify every anchor in this document against the then-current `main`
   first.

---

## 1. What the solver is for

The CAD designer needs neck **width and thickness** numbers to draw the Smart Guitar neck. The solver derives
them from a small set of design inputs instead of copying stored values, many of which Inv-037 found to be
unsourced. Every input is tagged with its origin: ruled / record (unverified) / assumed / design choice. The
tool computes; it does not assert.

## 2. The model (implementation specification)

Units are mm. Distance `s` is measured from the nut; fret position is `s(n) = L·(1 − 2^(−n/12))`.

| Quantity | Definition |
|---|---|
| Width | Straight edges **anchored at the nut**: `W(s) = W_nut + (W_2 − W_nut)·s / s_2`, where `W_2` is the width at a stated second station. *Anchoring at fret 1 was a defect in the original prototype.* |
| Fretboard radius | `single`: constant. `compound`: `R(s) = R_nut + (R_2 − R_nut)·s / s_R`. `true cone`: `R(s) = R_nut·W(s)/W_nut`. **Which one is canonical is ruling (a).** |
| Edge sag | `sag = R − √(R² − (W/2)²)` |
| Board thickness | Centre thickness varies linearly from the nut to the board end; edge = centre − sag; board left under a fret slot at the edge = edge − slot depth. |
| Neck depth (neck only) | Piecewise **linear** through the owner's points (1st, 12th, optional third). Values beyond the outer points are extrapolated **and flagged**. No smoothing, so no kink at the 12th. |
| Back profile | The sides drop vertically from the board edge by a *side flat*, then a superellipse `|x/a|ⁿ + |y/b|ⁿ = 1` runs to the centre depth, with a separate exponent `n` for the bass and treble sides. |
| Back arc radius | Radius of the circle through both shoulders and the centre: `R_back = (a² + b²)/(2b)`. |
| Depth convention | `neck` = neck only; `total` = neck + board; `with frets` = total + crown. A drawing must state which one it dimensions. |

**Acceptance vectors.** These are hand-computed; any port must reproduce them.

| Case | Expected |
|---|---|
| Width at the 12th (42.86 at the nut → 57.40 at fret 24, L = 647.7) | 52.553 |
| Edge sag at the nut, single R 304.8 | 0.754 |
| Total depth at the 12th (board 5.0 + neck 21.59) | 26.590 |
| Neck depth at fret 7 (20.32 at F1, 21.59 at F12) | 21.111 |
| Compound 254 → 406.4 at fret 24, R at the 12th | 355.600 |
| True cone from 254 at the nut, R at the 12th | 311.445 |
| Back arc radius, a = 25, b = 20 | 25.625 |

The joint tab uses a straight-string model: each string passes through its 1st-fret clearance and its 12th-fret
action, over the radiused crowns. With the ruled joint it gives 13.94 / 12.26 / 26.59 / fret 23.70. See §6(b)
before porting it.

## 3. Verification already done (this session)

- **Built-in acceptance:** neck 7/7 PASS and joint 4/4 PASS, rendered in a headless browser with 0 console
  errors.
- **DXF:** R12, mm (`$INSUNITS 4`, `$MEASUREMENT 1`), extents computed from the geometry, 3 dp, closed
  sections, nothing on layer 0.
  - Opened with AutoCAD's command-line engine (DWG TrueView 2026 `accoreconsole`): 25 entities, 0 errors.
  - The entities were 6 closed section outlines, 6 glue-plane lines, 6 labels, and 7 **PROVENANCE** text lines.
  - The PROVENANCE text carries: class = PREVIEW / DESIGN REFERENCE – not for machining; tool version; date;
    an input fingerprint; the parameters; and the unverified-input status.
- **A real design finding the tool surfaced:** a 5.0 mm board with a 12″ radius and a 3.0 mm slot leaves
  **0.65 mm** under the slot at the board edge by fret 24.

## 4. Where it sits against today's DXF governance

Read on `origin/main` @ `0679dbf6`:

| Governance element | Location | Solver today |
|---|---|---|
| Export classes: PREVIEW / EXPORT / MACHINE OUTPUT | `docs/architecture/CAM_GOVERNED_EXPORT_ARCHITECTURE.md` | Declares itself **PREVIEW / design reference** |
| Export Object (canonical semantics) | `services/api/app/cam/export_object.py` | None |
| Registered translators; only `governed_execution` may produce files | `services/api/app/cam/translators/`, `docs/governance/TRANSLATOR_LAYER_RULES.md` | None. The only DXF translator is `body_outline_dxf_r12/_r2000`. |
| Protected writer chain | `cam/dxf_writer.py` → `util/dxf_compat.py`, enforced by `scripts/check_dxf_compat.py` | Hand-written |
| Save-lifecycle guard | `app/util/dxf_lifecycle_guard.py` (`DxfLifecycleContext`, `assert_dxf_lifecycle_context`); the blueprint lane wraps it as `governed_doc_saveas()`. Plan: `docs/governance/DXF_SAVE_LIFECYCLE_GUARD_PLAN.md` (rollout finished to DO-77). | None |
| Smart Guitar classification | `docs/architecture/DXF_COMPAT_EXEMPTIONS.md` — **EXCLUDED_EXTERNAL_ECOSYSTEM**, "should not drive or contaminate Production Shop governance decisions" | SG-specific, so excluded today |

**The implication.** The neck model itself is instrument-agnostic, which makes it a Production Shop candidate.
Only the Smart Guitar parameter set belongs to the excluded ecosystem. Splitting the two is ruling (c).

## 5. Integration plan (per `docs/governance/ARCHITECTURE_INVARIANTS.md`)

| Layer | Location | Content |
|---|---|---|
| 1 · pure maths | `app/geometry/` | Superellipse, sagitta, polygon area |
| 2 · instrument maths | `app/instrument_geometry/neck/` | Neck station model. **Reuse** `fret_math` (positions) and `neck_taper/taper_math` (same straight-edge width formula; survey-reported, re-verify). **One** radius function (ruling a). |
| 3 · calculators | `app/calculators/` | Station table and checks; the acceptance vectors above as pytest |
| 4 · CAM | `app/cam/` | Export Object (`ExportType.GEOMETRY`) + `translators/dxf/neck_section_translator.py`. It is **registered as `validation_only`**, declares its capabilities, appears in the capability matrix, writes through the protected `DxfWriter`, asserts a `DxfLifecycleContext` at its save boundary (see `blueprint_dxf_export_lifecycle.governed_doc_saveas()` for the pattern), and carries a PROVENANCE layer. |
| 6 · routes | extend `app/routers/neck_router.py` | `/api/neck/stations`, `/api/neck/section`, `/api/neck/sections.dxf`. No maths in routers (Fortran rule). |
| Client | `packages/client/src/views/cam/NeckView.vue` (`/cam/neck`) | Mounted as a **beta panel** (Feature Parity State 3). The existing composables stay canonical until parity is verified (ruling d). |

**Phases.** Each phase is its own PR with a CBSP21 manifest (`.cbsp21/patches/<id>.json`), passes the
governance `check_all.py` precommit and ci tiers, and touches no protected path.

1. **P1:** L1–L3 + pytest acceptance vectors. Additive; no routes.
2. **P2:** routes returning PREVIEW JSON.
3. **P3:** client beta panel.
4. **P4:** Export Object + translator + DXF. **Gated** on the extents fix and on the translator lane accepting
   new translators.
5. **P5:** consolidation of the duplicate radius and profile implementations, **only after parity is
   verified**.
6. **P6:** the joint (string-model) solver, after ruling (b).

## 6. Rulings required before any code, with justification

**(a) Canonical compound-radius definition. Most important; it blocks P1.**
- *Why:* three incompatible definitions are in use. For the same nominal "10″ → 16″" board, fretted to 24 on a
  647.7 scale, the radius at the 12th comes out as:

  | Definition | R at the 12th | Edge sag at the 12th |
  |---|---|---|
  | Linear in distance | **14.00″** | 0.972 mm |
  | Curvature (1/R) linear, as in `luthier_calculator` "true conical" (survey-reported at `luthier_calculator.py:157-175`, unrouted) | **13.33″** | 1.021 mm |
  | Radius ∝ width | **12.26″** | 1.110 mm |

  That is a 0.14 mm spread in edge height. It propagates into fret slot depth, fret levelling, fretboard CAM
  surfacing and binding.
- A survey also reported **eight** compound-radius implementations with different normalisation bases (fret
  index, position/scale, position/fretboard length, 0–1 ratio). Re-verify that count before consolidation.
- One function cannot replace them until one definition is ruled canonical.

**(b) Neck-angle definition. Blocks P6 only.**
- *Why:* the repo's `instrument_geometry/neck/neck_angle.py` aims the fret plane at the **saddle crown**.
- Its reported "required saddle height" echoes its input: `L·tan(atan(h/L)) + fb − bridge` reduces to the
  input saddle height, and `tests/test_neck_angle.py:219` asserts exactly that.
- `calculators/setup_cascade.py:120` passes `saddle_height_mm` into `bridge_height_mm`.
- The solver's string model avoids the aim-point question by computing the actual string path.
- One definition must be ruled canonical before a second joint solver lands.

**(c) Ownership: a general Toolbox neck tool, with Smart Guitar presets kept separate.**
- *Why:* `DXF_COMPAT_EXEMPTIONS.md` excludes Smart Guitar DXF code from Production Shop governance, pending
  repo separation.
- Without this ruling, the tool either stays exempt from DXF governance or pulls the Smart Guitar into Production
  Shop governance. Both outcomes are contrary to that document.

**(d) Confirm `NeckView.vue` is the canonical neck view.**
- *Why:* the Feature Parity Migration Policy (`FEATURE_PARITY_MIGRATION_POLICY.md`) requires the canonical
  implementation to be declared before a beta shell is mounted beside it.
- `NeckView.vue` is the mounted `/cam/neck` route. A survey reported that it computes locally in TypeScript
  composables (`design-utilities/lutherie/neck/*`), with a width formula that differs from `taper_math`. Parity
  must be measured against it, not assumed.

**(e) (timing, owner) When does the translator lane accept new translators?** This gates P4.

## 7. Why deferred: current churn (evidence, 2026-09-13)

| In-flight work | State | Overlap with this plan | Consequence if started now |
|---|---|---|---|
| **Inv-037 R4a** — fail-closed resolution (`fix/p1-r4a-fail-closed-resolution`, 59 files) | Verified, awaiting owner rulings; unmerged | **Direct:** `routers/neck/gcode_router.py`, `routers/neck/schemas.py`, `routers/neck/headstock_transition_export.py`, `instrument_geometry/models/loader.py`, `routers/instrument_geometry/nut_fret_router.py`, 7 calculators | Merge conflicts in the neck router area. R4a also **changes how instrument presets resolve** (unknown id → error), and the solver's presets must be built on that contract. |
| **DXF writer extents fix** (`fix/dxf-writer-extents`) | Pushed; merge blocked | **Direct:** `cam/dxf_writer.py`, the protected writer P4 must use | P4 would build on a writer that still emits the `1e+20` extents placeholder. |
| **PR #370** — CUSTODY-REMED-001 | Open | `instrument_geometry/specs/gibson_explorer.json` | The solver's pre-filled neck depths are **Explorer-derived**; their source record is itself under custody remediation. |
| **Inv-037 Phase 1 wave** (R5-U, R5-L, R6-U, R7A) | Local branches present and unmerged; about 9 owner rulings pending (status of 2026-09-11) | None direct | Review bandwidth, and main is expected to move under every open branch. |
| **G2-MANUFACTURING-SPINE-001** | Active in another Claude session, which asked that its worktree not be written to | None direct (tools/tests/docs) | Parallel-session hazard on a shared machine (78 worktrees). |
| **Neck G-code rapids at cutting depth** (safety; order drafted, held by the owner) | Not yet filed; must merge before or with R7A | Same neck CAM domain (`cam/neck/profile_carving.py:301-302, 360-361`) | A neck-tool PR landing first would widen the review surface of a safety fix. |

**Owner instruction in force:** no new pull requests without an explicit request. This handoff and its
SPRINTS entry are documentation only.

## 8. Guardrails for whoever restores this

- Re-verify every `file:line` above against the current `main`. Several anchors come from surveys, not direct
  reads.
- Do not modify the protected `cam/dxf_writer.py` / `util/dxf_compat.py`. Consume them.
- Do not remove or replace `NeckView.vue` or its composables (feature parity: mount → verify → audit → extract
  → normalize → replace).
- Do not ship Smart Guitar parameter values as generic defaults. Presets come through the resolver (post-R4a),
  and unsourced values are never manufacturing-authoritative (Inv-037 S2-P / S3-D2).
- Keep the DXF output PREVIEW-class until a translator is registered for `governed_execution`.
- Port the acceptance vectors first; they are the contract.
