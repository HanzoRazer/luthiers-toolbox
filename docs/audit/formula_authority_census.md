# Formula / Calculator Authority Census

**Status:** FROZEN (2026-08-22) — **amended 2026-08-23** (post-freeze; bounded reconciliation passed). Read-only evidence artifact.
The 2026-08-23 amendment adds **§11** (string-course lateral geometry) and one dated correction to the §3 string-spacing row. No prior finding text was rewritten.
**Not a schedule.** This file inventories formula/calculator authority and divergence across
10 sections / 43 findings and closes with a **repository-level disposition matrix** (9 families);
it does not assign priority or create work items. It may later feed a maintenance/scheduling
system, but must not itself decide priority. Remediation prioritization is a separate,
owner-authorized step. The derived, reconciled ordering lives in
[Formula / Calculator Recovery Queue](./formula_recovery_queue.md).

> **Post-freeze amendment rule.** Findings may be changed only through a **dated correction note
> grounded in new evidence**. Any substantive amendment requires a **fresh census↔queue
> reconciliation pass**. Historical classifications should be **preserved rather than silently
> overwritten** where practical.

**Method:** every entry is **re-witnessed against current `main`** (working tree,
2026-08-21) — file paths and line numbers from the April formula catalog
(`docs/audit/math_formula_catalog_2026-04-30.md`) are treated as *claims to verify*,
not facts. No code was corrected. No PRs. No SPRINTS edits.

**Scope so far:** (1) CNC/CAM seed — three grounded findings (§1); (2) full
`lutherie_geometry` — zero-fret/datum chain (§2) + remainder (§3); (3) full
`structural_mechanics` (§4, +BC field); (4) `acoustic_physics` reconciliation (§5,
+CalibrationBasis field); (5) `optimization`/vectorizer heuristics (§6, lifecycle-corrected);
(6) `wood_movement` data authority (§7, +ratified `ValidationBasis`); (7) `temperament_tuning`
authority + datum check (§8); (8) `signal_processing` metric-vs-decision-layer (§9). Remaining
domains toward the full 147 are **deferred to later passes** (checkpoint before each).

---

## Taxonomy (bucket legend)

| Bucket | Meaning |
|--------|---------|
| `SAFETY_DEFECT` | Live, safety-relevant, internally inconsistent or wrong |
| `DATUM_CONFLICT` | Uses a different reference plane / origin than the model intends |
| `DUPLICATE_EQUIVALENT` | ≥2 implementations, **same** math and behavior |
| `DUPLICATE_DIVERGENT` | ≥2 implementations, math agrees but **semantics differ**, or math differs |
| `MODEL_AUTHORITY` | Hard-coded / uncited constant or assumption that ought to be sourced/selectable; unclear owner |
| `EMPIRICAL_UNCITED` | Empirical coefficients without a traceable source |
| `UNTESTED_HIGH_RISK` | High-risk formula with no dedicated tests |
| `STALE_DEAD` | Orphaned / unimported / superseded implementation |
| `CANONICAL_SHIM` | A canonical implementation plus a deliberate back-compat shim |
| `MIGRATED_CAPABILITY_RESIDUE` | Implementation remains in this repo after **authority moved to a separate repository**. A 5th pre-governance archaeology category alongside *stranded implementation · preserved transition-era implementation · preserved/set-aside capability · architectural DNA*. The question is not "which copy is authoritative?" but "is this supposed to be authoritative **here** at all?" **Severity depends on live coupling** (see note) |
| `INCOMPLETE_MIGRATED_IMPLEMENTATION` | Migrated work left partial/unfinished here after authority moved out — distinct from plain dead code |
| `VALID_REUSE` | ≥2 implementations of an **established** relation that are genuinely equivalent (same math, units, boundary conditions) — legitimate reuse, **not** authority debt |
| `VALID_ALTERNATE_MODEL` | ≥2 implementations of the same relation with **different BC / load case**, each **clearly named for a different physical use** — legitimate, **not** debt |
| `UNITS_DEFECT` | The physics/relation is sound; the *implementation* or a *threshold* uses inconsistent units |
| `INSUFFICIENT_EVIDENCE` | Not enough traced yet to classify |

**Note on `SAFETY_DEFECT` / `DUPLICATE_*`:** these describe the *defect or the software situation*, never a verdict that the underlying mathematics is wrong. Read every duplication/defect row together with its **Provenance** (below): a repeated *standard relation* that is equivalent is `VALID_REUSE`, not a conflict.

**Note on `MIGRATED_CAPABILITY_RESIDUE`:** severity turns on **live coupling**, not mere presence. (a) *Inert* residue (no live consumer) = cleanup/archaeology debt. (b) *Live-coupled* residue (a mounted production path still imports/runs the in-repo copy) = the migration is **incomplete at the deploy level** — production executes the old copy while authority nominally moved out. Always record which, and never re-classify migrated residue as current fragmented authority.

**Liveness key:** `LIVE` (imported + reachable from a mounted router) · `LIVE(shim)`
(reached via a deprecated shim) · `DEAD` (0 importers) · `DEPRECATED` (marked, may
still be wired).

---

## Provenance / formula type (classify BEFORE judging duplication)

Every formula is tagged with what *kind* of expression it is. This gates how
duplication and "authority" are interpreted — repeated **established** mathematics is
not architectural debt.

| Provenance | Meaning | How duplication reads |
|-----------|---------|-----------------------|
| `FUNDAMENTAL_PHYSICS` | Elementary physics (circumferential speed, F=ma-level) | repetition ⇒ `VALID_REUSE` unless units/inputs differ |
| `STANDARD_ENGINEERING_RELATION` | Textbook engineering (Euler-Bernoulli, section properties, chip load, Mersenne) | repetition ⇒ `VALID_REUSE` if math/units/BC equivalent |
| `LUTHIERY_DOMAIN_MODEL` | A luthiery modeling *choice* (nut-slot datum, neck-angle target, compensation model) | repetition ⇒ genuine authority/datum question |
| `EMPIRICAL_MODEL` | Fitted/empirical relation from data | authority = the data/source |
| `CALIBRATED_MODEL` | A relation tuned by a repo-chosen constant (PMF, γ, 1.83, relief×0.6) | authority = the calibration provenance |
| `CUSTOM_HEURISTIC` | Repo-specific ad-hoc rule (magic coefficients, scoring weights) | highest scrutiny; often unowned |

## Three lenses (keep separate)

A finding belongs to at most one of these — conflating them is what produces
false positives:

1. **Physics verification** — does the implementation *faithfully represent* the
   established relation (units, boundary conditions, algebra)? (Applies to
   `FUNDAMENTAL_PHYSICS` / `STANDARD_ENGINEERING_RELATION`.)
2. **Model authority** — which *assumptions, datums, constants, and domain
   interpretation* has the repo chosen, and is there a competing choice?
3. **Software authority** — which *implementation* are consumers supposed to call
   (canonical vs shim vs dead vs divergent copy)?

> **Guardrail for all remaining passes.** Do not treat repeated formulas as authority
> conflicts merely because they are repeated. First classify provenance. Authority
> reconciliation is concerned with competing **assumptions, datums, constants,
> boundary conditions, semantics, and downstream behavior** — not legitimate reuse of
> established mathematics. Two modules implementing the same textbook relation with the
> same units and boundary conditions are `VALID_REUSE`, not competing authorities.

### Boundary condition / constraint model (explicit field, added for structural/acoustic)

For structural & acoustic formulas the **BC/constraint** is recorded as its own field —
the structural analog of the datum axis (the thing two faithful implementations of the
same relation can silently disagree on). Values: `cantilever · simply_supported ·
clamped · free · mixed · point_load · distributed_load · plate_edge_condition ·
brace_support_condition · unknown/implicit`.

> **BC guardrail.** Differing boundary conditions are **not** automatically "wrong." A
> clamped plate and a simply-supported plate are both valid if they model *different
> physical situations* (`VALID_ALTERNATE_MODEL`). A finding exists only when the BC is
> **hidden, mislabeled, or ≥2 implementations claim authority over the same use case**.

### CalibrationBasis (acoustic field — separates physics from tuning provenance)

For calibrated constants, record *how the number was arrived at*, distinct from the
(often standard) physics it corrects: `literature-derived · single-point calibration ·
multi-instrument fit · empirical house constant · unknown`. A standard relation
(Helmholtz, orthotropic plate) can be faithful while its correction factor is an
unsourced house constant — two separate verdicts.

### ValidationBasis (ratified standard field, from `wood_movement` onward)

Three concepts stay distinct: **Provenance** = *what kind* of model; **CalibrationBasis**
= *how a numerical constant was fit*; **ValidationBasis** = *what evidence demonstrates
the model / heuristic / threshold / dataset is fit for its claimed use*. Vocabulary:
`TRAINING_VALIDATION_EVIDENCE · EXPERT_CALIBRATION · SINGLE_FIXTURE_TUNING ·
LITERATURE_VALIDATED · CROSS_INSTRUMENT_EMPIRICAL · HISTORICAL_ACCRETION ·
UNKNOWN_ORIGIN · NOT_APPLICABLE`. Use `NOT_APPLICABLE` for `FUNDAMENTAL_PHYSICS` /
elementary geometry — a correct circumference relation needs no repository corpus. When
repository evidence cannot establish validity, the answer is `UNKNOWN_ORIGIN` /
`INSUFFICIENT_EVIDENCE` — **not** a research task to find a replacement value.

---

## The two datum axes traced (per ruling)

These can diverge independently and are recorded separately:

- **Axis A — string-height / fret-plane datum:** traditional nut (string sits *above*
  the fret-crown plane) vs zero-fret (string sits *at* fret-crown height); and whether
  a depth is referenced to the slot-floor, the string-center, or clearance-over-fret.
- **Axis B — scale / reference origin:** nut origin vs zero-fret origin vs a shifted
  effective-scale origin (e.g. per-string compensation setback).

**Operating question:** *does any calculator silently inherit either a zero-fret
height datum (Axis A) or a zero-fret scale-origin datum (Axis B) where a
traditional-nut model is intended, and does that assumption propagate or conflict
downstream?*

**Answer (this pass):**
- **Axis B (scale origin) is CLEAN.** Every calculator in the chain uses **nut origin**
  (fret 0 = nut). The only origin shifts — nut-compensation setback and saddle
  compensation — are **explicit and intentional**, and `nut_compensation_calc` correctly
  zeroes the setback for a zero-fret. No *silent* zero-fret origin inheritance found.
- **Axis A (string height) has exactly one silent zero-fret inheritance:**
  `nut_slot_calc.py` bakes "string center at fret-**crown** height" (a zero-fret height
  datum) into a **traditional-nut** slot-depth calculation (the §17 defect). **It does
  NOT propagate downstream** — `neck_angle` hard-codes `nut_slot_depth=0.5`,
  `setup_cascade` takes slot depth as an input, and `nut_compensation_calc` is
  datum-aware. Instead of a propagating cascade, the **nut-slot-depth quantity is
  fragmented across 3–4 non-communicating authorities**. So the failure mode is
  *authority fragmentation + one contained datum conflict*, not a chain-wide leak.

---

## Section 1 — CNC/CAM (seed; verified live 2026-08-21)

| Quantity | Implementation(s) | Provenance | Lens | Units / defect | Liveness | Bucket |
|----------|-------------------|-----------|------|----------------|----------|--------|
| Saw rim speed | `calculators/cam_cutting_evaluator.py:148 calculate_rim_speed()` | `FUNDAMENTAL_PHYSICS` (circumferential speed — **not in question**) | physics OK; **implementation** | computes **m/min** (`/1000`) but caps at `80.0`, sane only as **m/s** (~60×) | LIVE, `@safety_critical` | **`UNITS_DEFECT`** (safety-relevant) — trips on ~every real blade; drifted from catalog `/60000` |
| Chipload | `cam/vcarve/chipload.py calculate_chipload()` **and** `cam_core/feeds_speeds/chipload_calc.py calc_chipload_mm()` | `STANDARD_ENGINEERING_RELATION` (`feed/(rpm·flutes)`) | **software authority** (the relation itself is `VALID_REUSE`) | mm/tooth; identical math | both LIVE | **`DUPLICATE_DIVERGENT`** — behavior differs: vcarve returns `0.0` on invalid (silent), cam_core raises |
| Tool deflection (beam) | `cam_core/feeds_speeds/deflection_model.py:7 estimate_deflection_mm()` — `F·L³/(3EI)`, `I=π·d⁴/64` | `STANDARD_ENGINEERING_RELATION` (Euler-Bernoulli) — **faithful; units check out (mm)** | **model authority** (the *constant*, not the physics) | `E=90_000 MPa` hard-coded (90 GPa ≠ carbide ~600 / HSS ~200); no material selection | LIVE | `CALIBRATED_MODEL` / **`MODEL_AUTHORITY`** — suspect E, unsourced |
| Tool deflection (rival) | `calculators/cam_cutting_evaluator.py:124 calculate_deflection()` — `(stickout/dia)³·(depth·woc)·0.0001` | `CUSTOM_HEURISTIC` (magic `0.0001`, no material, not a beam eq) | **model + software authority** | not dimensionally a deflection; a scaling proxy | LIVE | **`DUPLICATE_DIVERGENT`** — a *different model* for the same quantity than the beam version; which is authoritative is unresolved |

---

## Section 2 — Zero-fret / datum chain (`lutherie_geometry`)

### Node 1 — Fret position (Axis B: scale origin)

| Quantity | Implementation | Axis B | Formula | Liveness | Bucket |
|----------|---------------|--------|---------|----------|--------|
| Fret distance from nut | `instrument_geometry/neck/fret_math.py compute_fret_positions_mm()` | **nut origin** | `L·(1 − 1/2^(n/12))` | LIVE (12 importers, geometry_calculator_router) — **canonical** | — |
| " | `api_v1/fret_math.py` (POST `/frets/positions`) | nut origin (+ subtracts `nut_width_mm`) | `L·(1 − 2^(−n/12))` | LIVE (own endpoint) | `VALID_REUSE` |
| " | `instrument_geometry/neck_taper/taper_math.py fret_distance()` | nut origin | `L − L/2^(f/12)` | LIVE (4 importers) | `VALID_REUSE` |

**Finding:** three copies of the equal-temperament formula (`STANDARD_ENGINEERING_RELATION` / music math), **all nut-origin, all mathematically equivalent** → `VALID_REUSE`, **not** authority debt. Axis B clean. Consolidation is an optional DRY cleanup, not a correctness or authority issue.

### Node 2 — Neck geometry (taper / width-at-fret)

| Quantity | Implementation | Axis A/B | Liveness | Bucket |
|----------|---------------|----------|----------|--------|
| Neck width at fret | `neck_taper/taper_math.py` (similar-triangles taper) | nut origin; fretboard-plane width; no zero-fret assumption | LIVE (4 importers; no direct router) | `UNTESTED_HIGH_RISK` (catalog: HIGH, no dedicated tests) |

### Node 3 — Nut geometry (slot depth + compensation) — **the hotspot**

| Quantity | Implementation | Axis A (height) | Axis B (origin) | Liveness | Bucket |
|----------|---------------|-----------------|-----------------|----------|--------|
| Nut **slot depth** | `calculators/nut_slot_calc.py compute_nut_slot_depth()` — `r + crown/2 + clearance(0.13)` | **ZERO-FRET height datum** ("string center at crown height") baked into a traditional-nut calc | n/a | **LIVE** (fretwork_router + nut CAM) | **`DATUM_CONFLICT`** (the §17 defect; own gate can never return GREEN) |
| Nut **slot depth** (twin) | `calculators/nut_compensation_physics.py nut_slot_depth()` — `nut_blank_height − crown − clearance` (per-string wound/plain) | traditional; **subtracts** crown (opposite sign); blank-top datum | n/a | **DEAD** (0 importers) | **`STALE_DEAD` + `DUPLICATE_DIVERGENT`** — the *sounder* model, orphaned, contradicts the live one |
| Nut **compensation / setback** | `calculators/nut_compensation_calc.py compute_nut_compensation()` — `setback = (action_at_nut − fret_height)·L/1000` | **datum-aware:** models `traditional \| zero_fret \| compensated` | **explicit per-string origin shift**, zeroed for zero-fret | LIVE (nut_fret_router) — **canonical** | authority (correct reference model) |
| Nut compensation (geom) | `calculators/nut_comp_calc.py` → re-exports `nut_compensation_calc` w/ `DeprecationWarning` | inherits canonical | inherits | LIVE(shim) (4 importers incl. fretwork_router) | `CANONICAL_SHIM` (routers still hit the shim) |

**Finding (Axis A):** three competing string-height models for one quantity (nut slot depth) — live-buggy (`nut_slot_calc`, zero-fret height), dead-sound (`nut_compensation_physics`, traditional), and doc §17 (traditional, fret-plane). The **live one carries the zero-fret inheritance**; the **correct model already exists but is dead.**

### Node 4 — Action (at nut / 12th fret)

| Quantity | Implementation | Axis A/B | Liveness | Bucket |
|----------|---------------|----------|----------|--------|
| Target-action inverse | `instrument_geometry/neck/neck_angle.py solve_for_target_action()` | `relief × 0.6` (uncited parabolic factor); **`nut_slot_depth=0.5` hard-coded**, not consumed from `nut_slot_calc`; nut origin | LIVE (neck_router) | `MODEL_AUTHORITY` + `UNTESTED_HIGH_RISK` |
| Setup cascade | `calculators/setup_cascade.py evaluate_setup()` — `nut_slot_depth → action_at_nut` | takes `nut_slot_depths` as **input** (default `{}`, `action_at_nut=0.5`); imports `neck_angle` | LIVE (build_workflow_router) | authority fragmentation (no single source) |
| Neck relief eval | `instrument_geometry/neck/setup_workflow.py evaluate_relief()` | relief measurement gate | LIVE (setup_router) | — |

**Finding:** the nut-slot-depth / action-at-nut quantity has **no single authority** — *computed* in `nut_slot_calc` (buggy), *hard-coded* `0.5` in `neck_angle`, *input* in `setup_cascade`. `MODEL_AUTHORITY` fragmentation.

### Node 5 — Neck angle

| Quantity | Implementation | Axis A/B | Liveness | Bucket |
|----------|---------------|----------|----------|--------|
| Neck pitch | `instrument_geometry/neck/neck_angle.py compute_neck_angle()` — `θ = arctan((H_saddle+H_bridge−H_fretboard)/L_body)` | fretboard-plane height datum; nut origin; **no zero-fret dependence** (works at 12th/body) | LIVE (neck_router) | `UNTESTED_HIGH_RISK` (catalog: uncited, no tests) |

### Node 6 — Saddle compensation

| Quantity | Implementation | Axis A/B | Liveness | Bucket |
|----------|---------------|----------|----------|--------|
| Per-string comp (design+setup) | `calculators/saddle_compensation.py` — cents↔mm, semi-empirical | nut origin + saddle-end offset | LIVE (saddle_compensation_router) | `EMPIRICAL_UNCITED` (coeffs; has tests) |
| Applied saddle positions | `instrument_geometry/bridge/geometry.py compute_saddle_positions_mm()` — `pos = L + comp` | nut origin; comp moves saddle away from nut | LIVE (geometry_calculator_router) — canonical | — |

**Finding:** two surfaces (estimate vs apply), **consistent nut-origin datum**, not conflicting.

### Node 7 — Bridge geometry

| Quantity | Implementation | Axis A/B | Liveness | Bucket |
|----------|---------------|----------|----------|--------|
| Bridge location / saddle pos / height profile | `instrument_geometry/bridge/geometry.py` (+ `bridge/compensation.py`) | nut origin; `bridge_location = L` | LIVE (geometry_calculator_router) — canonical | bridge-height-profile: `UNTESTED_HIGH_RISK` (catalog) |
| (adjacent) | `calculators/bridge_calc.py`, `calculators/acoustic_bridge_calc.py` | not deep-traced this pass | — | `INSUFFICIENT_EVIDENCE` |

### Node 8 — Break angle (two ends — **not** a conflict)

| Quantity | Implementation | Datum | Liveness | Bucket |
|----------|---------------|-------|----------|--------|
| Break angle over **saddle** | `calculators/bridge_break_angle.py` — `arctan(h/d)` | **explicit:** bridge TOP-SURFACE datum; local pin→saddle origin | LIVE (bridge_presets_router) | clean (explicit datum, tested) |
| Break angle over **nut** | `calculators/headstock_break_angle_calc.py` (GEOMETRY-009) | **explicit:** nut-exit origin `N=(0,0)`, +y downward | LIVE(shim) (imported by shim) — canonical | — |
| " (shim) | `calculators/headstock_break_angle.py` → re-exports `_calc` | inherits | LIVE(shim) (3 importers incl. neck_router) | `CANONICAL_SHIM` (routers hit the shim) |

**Finding:** two break-angle calcs are **different physical ends** (saddle vs nut), both with **explicit, correct datums**. No conflict. (Answers the earlier "headstock-to-nut vs neck-angle" question: no.)

---

## Section 3 — Remaining `lutherie_geometry` (2026-08-21)

Four-axis classification (physics/model class · authority state · impl state ·
evidence), emphasis on **authority** over datum. Datum kept as a field; only primary
where a quantity has one.

| Quantity | Implementation(s) | Model class | Authority state | Impl state | Evidence | Datum/origin |
|----------|-------------------|-------------|-----------------|-----------|----------|--------------|
| Multiscale / perpendicular fret | `neck/fret_math.py:17 perpendicular_distance_for_fret`, `:160 compute_multiscale_fret_positions_mm` | `STANDARD_ENGINEERING_RELATION` (fan-fret extension of equal temperament) | single canonical (same module as Node 1) | LIVE | HIGH; multiscale tests Partial | nut origin, per-string perpendicular fret — **clean** |
| Compound radius | `neck/radius_profiles.py:40 compute_compound_radius_at_fret` (interp by **fret-index/total**) **vs** `body/fretboard_geometry.py:193 compute_compound_radius_at_position` (interp by **position/scale-length**) | `LUTHIERY_DOMAIN_MODEL` (linear radius interp) | **`DUPLICATE_DIVERGENT`** — different interpolation domain; frets aren't evenly spaced, so the two give different radii at the same fret | both LIVE (geometry_calculator_router) | MEDIUM, no tests | the divergence *is* the datum (fret-count vs distance) |
| Radius arc points | `neck/radius_profiles.py:74 compute_radius_arc_points` | `STANDARD_ENGINEERING_RELATION` (circular arc) | single canonical | LIVE | MEDIUM, no tests | local (0,0) — clean |
| Cubic Bézier | `body/parametric.py:43 cubic_bezier` **+ ≥7 other sites** (`generators/bezier_body`, `cam/fhole`, `cam/rosette`, `art_studio/*`, `routers/headstock/dxf_export`) | `FUNDAMENTAL_PHYSICS` / standard curve | **`VALID_REUSE`** — many independent copies of a textbook curve; DRY-only, **not** authority debt (guardrail) | LIVE | MEDIUM, no dedicated tests | n/a (parametric) |
| String spacing (centered / edge-margin) | `spacing.py:47 compute_centered_spacing_mm`, `:88 compute_edge_margin_spacing_mm` | `STANDARD_ENGINEERING_RELATION` (even spacing / margins) | single canonical (no duplicates found) | LIVE (imported; no direct router) | HIGH, no tests | explicit origin conventions (centerline / bass-edge) — **clean, documented** |
| Intonation compensation (saddle/bridge estimate) | `bridge/geometry.py:166 compute_compensation_estimate` (`gauge×30.0` magic) **vs** `saddle_compensation.py:193 estimate_string_compensation_mm` (semi-empirical) | bridge = `CUSTOM_HEURISTIC`; saddle = `EMPIRICAL_MODEL` | **`DUPLICATE_DIVERGENT` / fragmented** — two live estimators, different models (+ nut-comp at the other end, + `alternative_temperaments`) | both LIVE | uncited/heuristic (saddle has tests) | nut origin + saddle offset |
| Cents→mm / straight-saddle fit | `saddle_compensation.py estimate_string_compensation_mm / fit_straight_saddle` | `CALIBRATED_MODEL` (semi-empirical coeffs) | single canonical (saddle) | LIVE (saddle_compensation_router) | calibrated coeffs, has tests | nut origin |

> **CORRECTION — 2026-08-23 (post-freeze amendment).**
>
> The string-spacing row above classifies `instrument_geometry/spacing.py` as
> **"single canonical (no duplicates found)"**. That classification is **superseded by new
> evidence**:
>
> - `app/instrument_geometry/spacing.py` (`compute_centered_spacing_mm`, `compute_edge_margin_spacing_mm`)
> - `app/cam/nut_slot_cam.py::generate_string_positions`
>
> Both are **live** lateral-spacing implementations and they use **different coordinate/origin
> conventions** — `spacing.py` centred spacing declares *negative = bass*, while the nut-CAM
> implementation places *String 1 = high E at low X* (treble at the 0 end) measured from the left
> face of the nut. `spacing.py` has exactly one importer (`app/rmos/context.py`); the nut CAM path
> does **not** consume it and derives positions inline.
>
> The row's other judgements stand: the math is standard, the origin conventions inside
> `spacing.py` itself are explicit and documented, and there are no dedicated tests.
>
> **Original text retained above as historical state.** See **§11** and queue item **17 (`STRING-COURSE-AUTH-001`)**.

**Section 3 finding:** the emphasis shift paid off. Most of the remaining geometry is
**standard math with explicit origins** → `VALID_REUSE` / single-canonical / (several)
`UNTESTED_HIGH_RISK`, **not** authority debt — the provenance guardrail suppressed what
would otherwise have been ~half a dozen false "duplication" findings (esp. Bézier). Two
**genuine** new authority findings emerged, both matching the chain's pattern rather
than the zero-fret hypothesis: **compound radius** (divergent interpolation basis) and
**intonation compensation** (two divergent live estimators). No new datum/scale-origin
leak found in this set.

---

## Section 4 — `structural_mechanics` (2026-08-21)

Operating question: *for each structural quantity, do repeated implementations use the
same relation, the same material assumptions, AND the same boundary/load conditions —
and if not, is the divergence intentional, explicit, and correctly routed?*

| Quantity | Implementation(s) | Model class | BC / load | Authority state | Impl state | Evidence |
|----------|-------------------|-------------|-----------|-----------------|-----------|----------|
| Top deflection | `top_deflection_calc.py:118` — `δ = F·a²·b²/(3·EI·(a+b))` | `STANDARD_ENGINEERING_RELATION` | **simply_supported + point_load** (explicit; code even disambiguates from CNC tool-deflection) | single canonical | LIVE (construction_router) | cited, tested — **clean** |
| Plate EI / 2nd moment | `top_deflection_calc.py:65 compute_plate_EI` (`E_L·w·t³/12`) + `_bracing_physics.py:85 brace_second_moment_mm4` (rect `w·h³/12`, tri `/36`, parabolic `8/175`) | `STANDARD_ENGINEERING_RELATION` (section property) | rectangular/tri/parabolic section | **`VALID_REUSE`** — rect `I` in 2 places; `_bracing_physics` is the richer canonical | LIVE | cited/standard |
| Required EI (inverse) + brace dims | `bracing_calc.py:213 compute_required_EI` (`EI = F·a²·b²/(3·δ·L)`), `:248 compute_brace_dimensions_for_EI` | `STANDARD_ENGINEERING_RELATION` | **simply_supported** — *explicitly the inverse of top_deflection's model; code cross-references `compute_plate_EI`* | single coherent authority (forward↔inverse matched) | LIVE (construction_router) | uncited but internally consistent — **exemplar** |
| Brace section area / camber arc | `_bracing_physics.py:52 / :142` | `STANDARD_ENGINEERING_RELATION` (geometry) | section geometry | single canonical (private helper) | LIVE (via bracing_calc) | standard |
| **Material modulus (MOE / E_L)** | `top_deflection_calc.py:262` presets (**Sitka E_L = 11.0 GPa**) **vs** `_bracing_physics.py:43 MATERIAL_MOE_MPA` (**sitka 9.5 GPa**) **vs** `wood_species.json` (canonical, **unused here**) | `CALIBRATED_MODEL` (material property) | n/a | **`MODEL_AUTHORITY`** — same species, **different modulus** in plate vs brace models that compose into one EI; neither uses the canonical wood data | both LIVE | **inconsistent / unsourced** |
| Saddle force decomposition | `saddle_force_calc.py:72` — `F = T·(sinθ_front + sinθ_behind)` | `STANDARD_ENGINEERING_RELATION` (trig) | **point_load**; θ_front *explicitly* from `bridge_break_angle.py` | single canonical | LIVE (string_tension_router) | uncited but standard, tested |
| Side bending (outer-fiber strain) | `side_bending_calc.py:770` — `strain = t/(2R)` + species targets | `STANDARD_ENGINEERING_RELATION` + `EMPIRICAL_MODEL` | free-bend (strip) | single canonical | LIVE (materials_physics_router) | cited, tested — clean (raises on unknown species, no silent fallback) |
| Lignin glass transition | `side_bending_calc.py:643` — `Tg(MC) ≈ 200 − 8·MC`, bend temp `Tg+30` | `EMPIRICAL_MODEL` (material) | n/a | single canonical | LIVE | **well-cited (Goring 1963), tested — positive exemplar** |
| Fan brace angles | `instrument_geometry/bracing/fan_brace.py:96 get_fan_brace_pattern` (`fan_spread_angle=50°`) | `LUTHIERY_DOMAIN_MODEL` / `CUSTOM_HEURISTIC` | brace_support_condition | single (no competitor) | **DEAD — 0 importers, no router** | uncited, no tests |

**Section 4 finding:** structural_mechanics is the **cleanest domain so far** — the
opposite of the nut cluster. The EI stiffness chain is a *model exemplar*: one BC
(simply-supported), forward (`top_deflection`) and inverse (`bracing_calc`) explicitly
matched and cross-referenced; section properties are `VALID_REUSE`; saddle force
explicitly consumes `bridge_break_angle`; lignin Tg is properly cited. **No hidden or
mislabeled BC** was found — the BC guardrail produced zero false positives, and the new
BC field mostly recorded "explicit & consistent." Two real findings: (a) **MOE material-
constant fragmentation** — Sitka `E_L` is 11.0 GPa in the plate model but 9.5 GPa in the
brace model, and neither uses the canonical `wood_species.json` (`MODEL_AUTHORITY`,
material-assumption axis — exactly the class this pass was watching for); (b) `fan_brace`
is **orphaned dead code** (the third dead-but-domain module, after
`nut_compensation_physics` and now this).

---

## Section 5 — `acoustic_physics` (2026-08-21, RECONCILIATION pass)

Reconciles the formula-catalog acoustic rows with the `LUTHERIE_MATH` drift audit
(M7 / DOC-DRIFT-001), MAINT-DEFER-004, and §1 into one row per authority issue.
Physics is separated from calibration (`CalibrationBasis`), and intentionally different
resonator topologies are recorded as `VALID_ALTERNATE_MODEL`.

| Quantity | Implementation(s) | Physics class | BC / resonator | Calibration (basis) | Authority state | Live / tests |
|----------|-------------------|---------------|----------------|---------------------|-----------------|--------------|
| **Helmholtz air resonance** | `soundhole_calc.py` (canonical) **AND** `soundhole_physics.py` (parallel copy) — *both* define it | `FUNDAMENTAL_PHYSICS` — `f=(c/2π)√(A/(V·L_eff))`, faithful | rigid-wall Helmholtz | — | **`fragmented`** — 2 live modules (calc: 10 importers + router; physics: 5 importers, no router) | LIVE, tested |
| Calibration constants `PMF / GAMMA / K0` | `soundhole_calc.py:93,94,366` **AND** `soundhole_physics.py:33,34,43` — **duplicated, identical values** | corrections to standard physics | — | `K0=1.7` literature-derived (classical flanged end-correction); `GAMMA=0.02`, `PMF=0.92` **multi-instrument fit** (Martin OM/D-28/J-45) | **`DUPLICATE_EQUIVALENT` + `MODEL_AUTHORITY`** — two owners of one calibration → drift risk | LIVE |
| Port neck length / perimeter correction | `soundhole_calc.py compute_port_neck_length` (+ physics copy) | `STANDARD_ENGINEERING_RELATION` (end-correction) | flanged opening | `GAMMA` multi-instrument | canonical (dup in physics) | LIVE, tested |
| Body volume + `L_eff` | `acoustic_body_volume.py:145/:220` **vs** `soundhole_extended.py:145 volume_from_dimensions` | elliptical `EMPIRICAL_MODEL` | — | `VOLUME_FACTOR=1.83` multi-instrument fit | **`DUPLICATE` + `UNITS_DEFECT`** — `acoustic_body_volume` L_eff is dimensionally wrong (**= MAINT-DEFER-004**); a stale second impl | LIVE (legacy) |
| Plate modal frequency | `plate_design/thickness_calculator.py:70` | `STANDARD_ENGINEERING_RELATION` (Hearmon orthotropic plate) | **simply_supported** (η=1.0; →1.2-1.35 in-box) | η / γ transfer, `CALIBRATED` | single canonical | LIVE |
| Rayleigh-Ritz stiffness/mass + eigensolve | `plate_design/rayleigh_ritz.py:297/414` (matrices, `leggauss` quadrature) + **`:613` eigensolver "fallback"** | matrices `STANDARD` & faithful; **fallback path `CUSTOM_HEURISTIC`** | plate BC | — | **`MODEL_AUTHORITY` / unbacked claim** — `# Fallback to scipy if available` but no scipy import; runs `np.diag(K)/np.diag(M)` + `np.eye()` (diagonal approx, discards coupling) = **MAINT-DEFER-010 instance** | LIVE, partial tests |
| Alpha / Beta / Gamma params | `plate_design/alpha_beta.py:171/385/453` | `STANDARD` / `CALIBRATED` plate coefficients | plate | cited_general | single canonical | LIVE, tested |
| Logarithmic spiral (centerline + P:A) | `soundhole/spiral_geometry.py:114/179` | `LUTHIERY_DOMAIN_MODEL` (Williams 2019) | — | cited_specific | single canonical | LIVE, tested — **clean** |
| Two-cavity / coupled resonator | `soundhole_resonator.py:176` (+ coupled eigenfreq) | `STANDARD` (coupled resonators) | **two-cavity** (Selmer/Maccaferri) vs single Helmholtz | — | **`VALID_ALTERNATE_MODEL`** — a *different resonator topology*, not a conflict | LIVE, tested |
| Soundhole stiffness reduction | `soundhole_stiffness.py:120` | `CALIBRATED_MODEL` | soundhole edge | `STIFFNESS_K=0.798` **empirical house constant (basis unknown)** | single | LIVE, partial tests |
| String tension | `string_tension.py:246` | `STANDARD` (Mersenne) | — | — | single canonical (also §19) | LIVE, tested |

**Section 5 finding (reconciliation):** acoustic's headline is a **fragmented soundhole
stack** — `soundhole_calc.py` (router-canonical) and `soundhole_physics.py` (parallel,
5 consumers, no router) both implement Helmholtz *and duplicate the calibration
constants* (currently identical → `DUPLICATE_EQUIVALENT`, but two owners = drift risk).
The catalog vs LUTHERIE_MATH citing different files was a symptom of this split. The
**physics/calibration separation worked cleanly**: Helmholtz / port / modal are faithful
standard physics; the tuning lives in `K0` (literature), `GAMMA`/`PMF`/`1.83`
(multi-instrument fit), and `STIFFNESS_K=0.798` (unknown-basis house constant).
Prior findings reconciled into single rows: **MAINT-DEFER-004** (body-volume `L_eff`
units), **MAINT-DEFER-010** (rayleigh_ritz unbacked scipy fallback — confirmed live).
`VALID_ALTERNATE_MODEL` earned its keep on the **two-cavity resonator** (a different
topology, correctly *not* flagged). No net-new defect class emerged — as expected for a
reconciliation pass.

---

## Section 6 — `optimization` / vectorizer heuristics (2026-08-21)

Operating question here is **not** "does it match known mechanics?" but **"what evidence
justifies these weights/thresholds, and how much authority does the software give
them?"** Consumer-authority (advisory / ranking / **authoritative-gate**) and
validation-basis are captured inline (see checkpoint re: a formal `ValidationBasis`
field).

**AMENDED 2026-08-21, then CORRECTED 2026-08-22 (canonical-pipeline verification).** The
2026-08-21 amendment over-broadened the owner's "moved to a separate repository" note,
labelling the whole body-scoring / vectorizer / Loop-3 stack `MIGRATED_CAPABILITY_RESIDUE`
and calling the export gate "live-coupled migrated residue, incomplete at deploy level."
The hostinger canonical-pipeline check the owner directed **refutes that scope.** Three
converging repo sources fix the boundary precisely:

- **Canonical front-end** — `hostinger/blueprint-reader.html` (canonical IBG intake, served
  at easttrinitybaywoodworks.com) sets `API_BASE = https://luthiers-toolbox-production.up.railway.app`
  and calls **in-repo** endpoints: `/api/blueprint/vectorize/async`, `/api/vectorizer/extract`,
  `/api/blueprint/clean`.
- **Canonical path, named in-repo** — `routers/blueprint/constants.py:78,86`:
  "Canonical production: `POST /api/blueprint/vectorize/async` + `CleanupMode.REFINED`."
- **What actually migrated** — `services/photo-vectorizer/ARCHAEOLOGY_RELOCATION.md`
  (lifecycle `RELOCATED_EXTERNAL`, source commit `f1e11d9`, tag `v0.2.0-semantic-lineage-import`):
  **Tier A archaeology only** — `cognitive_extractor.py`, `cognitive_extraction_engine.py`,
  `body_dimension_reference.json`, `extract_body_grid*.py`, `vectorizer_phase2.py` → the
  `vectorizer-sandbox` repo. It states "**Production path (unchanged):** `/api/blueprint/vectorize/async`
  → `CleanupMode.REFINED` → `edge_to_dxf.py`. **Not** Phase 2 `/vectorize-geometry` or
  cognitive/grid modules." Re-import is blocked by `check_semantic_sandbox_imports.py` (precommit).

So the migration is **real but narrow, and clean/complete**: only Tier A cognitive/grid/phase2
left the repo — they are gone (`PHASE2_AVAILABLE=False`; the relocated endpoints return a
pointer to the canonical path). There is **no live-coupled residue and no "incomplete at deploy
level"** state. The body scorers and export gate were **not** in the relocation manifest — they
remain in-repo, live-mounted, and reached by the canonical front-end. They are therefore
**live canonical in-repo runtime**, reclassified below from residue to `MODEL_AUTHORITY`
(author-chosen weights on live paths, `UNKNOWN_ORIGIN`). The operating question reverts to the
original: **"what evidence justifies these weights/thresholds, and how much authority does the
software give them?"**

| Quantity | Implementation | Class | ValidationBasis | Consumer authority | Authority state |
|----------|---------------|-------|-----------------|--------------------|-----------------|
| Body scoring — locus (a) | `blueprint-import/vectorizer_phase3.py:1891 score_body_candidate` (→ `/api/blueprint/vectorize`) | `CUSTOM_HEURISTIC` | `UNKNOWN_ORIGIN` | ranking | **`MODEL_AUTHORITY` / fragmented (live)** — 1 of 3 live in-repo body-scorers; not in the relocation manifest |
| Body scoring — locus (b) | `services/api/app/services/contour_scoring.py score_contours` (native api; imported by `blueprint_clean.py:45` → `/api/blueprint/clean`) | `CUSTOM_HEURISTIC` | `UNKNOWN_ORIGIN` | selection | **`MODEL_AUTHORITY` / fragmented (live)** — 2 of 3; native-api scorer on the clean path `blueprint-reader.html` calls |
| Body scoring — locus (c) | `photo-vectorizer/contour_plausibility.py:61 body_ownership_score` (→ `/api/vectorizer/extract`) | `CUSTOM_HEURISTIC` (0.50/0.25/0.10/0.15) | `UNKNOWN_ORIGIN` | gates export | **`MODEL_AUTHORITY` / fragmented (live)** — 3 of 3; uncited weights on a live gate |
| Canonical blueprint path | `POST /api/blueprint/vectorize/async` → `CleanupMode.REFINED` → `edge_to_dxf.py` (`constants.py:78,86`, `ARCHAEOLOGY_RELOCATION.md:25`) | — | — | **AUTHORITATIVE — production path** | **`VALID_REUSE` (canonical)** — the named production pipeline, called by `blueprint-reader.html`; *not* residue |
| Ownership/export gate — **layered** | orchestrator `ownership_threshold=0.60` (`services/photo_orchestrator.py:400-401`) over deep `EXPORT_BLOCK_THRESHOLD=0.30` (`photo_vectorizer_v2.py:2777` → `contour_stage.py`); path: **mounted** `photo_vectorizer_router.py` → `PhotoOrchestrator` (native api) → in-repo `services/photo-vectorizer` `PhotoVectorizerV2`; called by front-end `/api/vectorizer/extract` | `CUSTOM_HEURISTIC` | `UNKNOWN_ORIGIN` | **AUTHORITATIVE — blocks export** | **`MODEL_AUTHORITY`** — live canonical in-repo gate; **two uncited thresholds at different layers** (0.60 orchestrator / 0.30 deep). *Not* migrated residue |
| Merge guard epsilon | `contour_stage.py:121 = 0.03` | `CUSTOM_HEURISTIC` | `UNKNOWN_ORIGIN` | merge | live in-repo `MODEL_AUTHORITY` (same live path) |
| Scale calibration / `validate_scale_before_export` | `vectorizer_phase3.py:2336` (2.5× correction) | `CALIBRATED_MODEL` / gate | `SINGLE_FIXTURE_TUNING` (cuatro/Explorer) | corrects/blocks export | **legitimate shipped safety gate** (CLAUDE.md: real, keep) — live in-repo |
| Feedback / correction retraining (Loop 3) | `vectorizer_phase3.py:1216 submit_correction` | — | — | none | **`STALE_DEAD`** — in-repo experimental stub, "no production API; Loop 3 not ratified"; the three-loop *architecture* it belongs to is the sandbox-owned experimental line (CLAUDE.md), but this stub itself is dead in-repo, not migrated |

**Section 6 finding (corrected):** the vectorizer body-scoring + export-gate stack is **live
canonical in-repo runtime**, not migrated residue — reclassified to `MODEL_AUTHORITY`
(author-chosen weights/thresholds, `UNKNOWN_ORIGIN`, on production-reachable paths). The
*only* thing that migrated to `vectorizer-sandbox` is **Tier A archaeology** (cognitive/grid/
`vectorizer_phase2`), and that migration is **clean and complete** — the modules are gone,
the relocated endpoints point to the canonical path, and re-import is precommit-blocked. There
is **no `MIGRATED_CAPABILITY_RESIDUE` and no deploy-level-incomplete state here.** The canonical
production pipeline is confirmed in-repo: `blueprint-reader.html` → Railway api → `/api/blueprint/vectorize/async`
(`REFINED` → `edge_to_dxf.py`) and `/api/vectorizer/extract` (photo-vectorizer). Loop-3
`submit_correction` is `STALE_DEAD` (in-repo dead stub), not `INCOMPLETE_MIGRATED_IMPLEMENTATION`.
`validate_scale_before_export` remains a legitimate shipped safety gate (CLAUDE.md). The still-open
model-authority question stands and is now correctly scoped **to this repo**, and is *broader* than
first stated: **"which contour is the body" is decided by three separate live in-repo scorers** —
`score_body_candidate` (blueprint vectorize), native-api `contour_scoring.score_contours` (blueprint
clean, imported by `blueprint_clean.py:45`), and photo-vectorizer `body_ownership_score` (vectorizer
extract) — all three reached by `blueprint-reader.html`, none with a recorded validation basis
(`UNKNOWN_ORIGIN`). The export decision is likewise **layered**: an orchestrator `ownership_threshold=0.60`
(`photo_orchestrator.py:400`) sits over the deeper `EXPORT_BLOCK_THRESHOLD=0.30` — two uncited thresholds,
not the single 0.30 first recorded. This is live in-repo `MODEL_AUTHORITY` fragmentation to weigh, not an
external-ownership question. **Owner-fact resolved:** the external repo is *not* the canonical
runtime; it holds relocated archaeology only. No re-pointing of `photo_vectorizer_router` is needed.

> *Provenance note:* the 2026-08-21 `MIGRATED_CAPABILITY_RESIDUE`/`INCOMPLETE_MIGRATED_IMPLEMENTATION`
> verdicts in this section were derived from a general owner remark ("moved to a separate repo")
> before the pipeline was witnessed. The verification the owner then directed refuted the scope.
> The `MIGRATED_CAPABILITY_RESIDUE` and `INCOMPLETE_MIGRATED_IMPLEMENTATION` taxonomy buckets (§ Taxonomy)
> remain valid categories — they simply do not apply to §6. This is the grep-absence-vs-positive-trace
> discipline applied to a migration claim: an unwitnessed "it moved" is a claim, not a fact.

---

## Section 7 — `wood_movement` (2026-08-21) — data-authority focus

Central question: **relation authority → property-data authority → species/axis identity
→ consumer authority.** First pass to use `ValidationBasis`. Per ruling: differing
published wood values are **not** automatically `DUPLICATE_DIVERGENT` (properties vary
by specimen / MC / grain / method / source) — a conflict is recorded only when the
software presents incompatible values as **interchangeable authority** without preserving
those distinctions. Where repository evidence can't establish a value's origin, the
verdict is `UNKNOWN_ORIGIN` — not a research task.

| Quantity | Implementation | Provenance | Data / relation authority | ValidationBasis | Consumer | Bucket |
|----------|---------------|-----------|---------------------------|-----------------|----------|--------|
| Dimensional change / MC-from-RH | `wood_movement_calc.py:108 compute_wood_movement` (`ΔW = W₀·ΔMC·S`) | `STANDARD_ENGINEERING_RELATION` (USDA Wood Handbook) | **relation clean**; shrinkage **data from `wood_species.json`** (alias-resolved, raises on unknown) | `LITERATURE_VALIDATED` (relation); data = curated subset | reads canonical dataset — **good discipline** | — (exemplar consumer) |
| Constants `MC_CHANGE_PER_RH=0.30`, `R:T=0.55` | `wood_movement_calc.py:73` | `CALIBRATED_MODEL` | Wood Handbook | `LITERATURE_VALIDATED` | — | minor `MODEL_AUTHORITY` (house rounding) |
| **`wood_species.json` bulk fields** | `data_registry/system/materials/wood_species.json` — 474 density, 474 Janka, 457 MOE | `EMPIRICAL_MODEL` / dataset | **~450+ values UNSOURCED** (only 4 `_density_source`, 4 `_hardness_source`, 4 `_mechanical_source`, ~19 shrinkage); generator `bulk_import_wood_species.py` **deleted** | **`UNKNOWN_ORIGIN` / `HISTORICAL_ACCRETION`** | many | `MODEL_AUTHORITY` — attribution policy only partly honored; provenance severed |
| Janka from density | `bulk_import_wood_species.py:140` `0.00355·ρ^1.85` | `EMPIRICAL_MODEL` (regression) | uncited, **no paper**; **generator file deleted** — outputs frozen in JSON | `UNKNOWN_ORIGIN` | (fed JSON) | **`STALE_DEAD`** (relation gone) + `UNKNOWN_ORIGIN` (outputs persist) |
| Thermal conductivity / specific heat / cutting energy from SG | `bulk_import_wood_species.py:127/133/130` | `EMPIRICAL_MODEL` | uncited; **generator deleted** | `UNKNOWN_ORIGIN` | (fed JSON) | `STALE_DEAD` + `UNKNOWN_ORIGIN` |
| **MOE / E_L (cross-domain)** | `wood_species.json` (457) · `luthier_tonewood_reference.json` (71) · `_bracing_physics` dict (Sitka 9.5) · `top_deflection` presets (Sitka 11.0) | dataset + embedded constants | **≥4 authorities; disagree (Sitka 9.5 vs 11.0)**; two JSONs are *intended* routing (characterization vs acoustic, CLAUDE.md) but share the field name with no basis tag; structural constants bypass **both** | mixed / `UNKNOWN_ORIGIN` (embedded) | 9 calculators embed material constants | **`MODEL_AUTHORITY` / fragmented** (material-property family) — records §4/§15 relationship, not re-opened here |
| Species / axis identity | `wood_movement_calc.py:41 ALIAS_MAP` + `_resolve_species_id` | mapping | single canonical resolver (in wood_movement_calc) | `NOT_APPLICABLE` | — | single — clean (but resolver is local to one calc, not shared) |

**Section 7 finding — material-property authority IS a recurring fragmentation family
(confirmed):** the repository *has* a canonical intent — `wood_species.json`
(characterization) + `luthier_tonewood_reference.json` (acoustic), per CLAUDE.md routing —
and *has* the discipline (`wood_movement_calc` / `side_bending_calc` read the dataset and
raise on unknown). But it is **not universal**: MOE/E_L exists in ≥4 authorities that
disagree; ~450+ dataset values are unsourced with their **generator deleted**
(provenance severed); and **9 calculators embed their own material constants** rather
than reading the datasets. Per the guardrail, this is classified as fragmentation only
because the software treats these as **interchangeable authority without preserving
specimen/MC/method/basis distinctions** — not merely because the numbers differ. The
`wood_movement` *relation* itself is clean, literature-validated, and correctly consumes
the dataset — the issue is **data authority, not the equation**. `ValidationBasis` earned
its keep immediately: it separated the sound relation (`LITERATURE_VALIDATED`) from the
dataset it stands on (`UNKNOWN_ORIGIN`).

---

## Section 8 — `temperament_tuning` (2026-08-22) — authority + datum check

Approached per ruling as a **broad authority-and-datum check**, not an assumed-clean pass:
separating the *mathematical temperament definition* from the *instrument implementation*,
tracing reference pitch, cents↔frequency, ratio→fret-position, and the compensation chain.

**(1) Temperament mathematics — `VALID_REUSE` / `VALID_ALTERNATE_MODEL`, no defect.**
`temperament_ratios.py` holds standard interval tables (Just, Pythagorean, quarter-comma
Meantone, 12-TET) — canonical musical constants. `alternative_temperaments.py` (LIVE, 5
importers + `routers/music/temperament_router.py`) builds on them: `ratio_to_cents =
1200·log2(ratio)`, `compute_n_tet_ratios = 2^(i/n)`, per-system octave extension — all
standard. The N-TET systems (12/19/24/31), the three named non-equal systems, `CUSTOM`, and
Scala `.scl` ingestion (`scala_loader.py`, LIVE via `api_v1/fretboard.py`) are **distinct
recognized temperament systems with explicit identity and consumers** → `VALID_ALTERNATE_MODEL`,
**not** authority debt (per guardrail). One `DUPLICATE_EQUIVALENT`: the octave-extension loop
is copied verbatim in `resolve_temperament_ratios` (l.199-208) and `get_ratio_set` (l.536-545)
— identical math, low-severity DRY smell.

**(2) Reference pitch / pitch standard — clean, explicit where used, absent where not needed.**
The fret/temperament geometry is **purely ratio- and position-based — no absolute Hz, no A4
anywhere in the chain.** A440 appears only in adjacent domains and is **explicit** there:
`soundhole_physics.hz_to_note` (`freq_hz/440.0`, acoustic §5) and `build_sequence.tuning_hz`
(explicit EADGBE `[329.63…82.41]`, tension/build). So reference pitch is *not silently
assumed* in intonation — it is simply not a parameter of ratio-based fret placement.

**(3) Datum check — temperament stays nut-origin; one unrelated API-layer datum defect.**
Ratio→position is nut-origin throughout: `position_from_ratio = L − L/r = L(1 − 1/r)`
(`alternative_temperaments`) and `compute_fret_positions_mm` (`neck/fret_math.py:110`, the
**canonical** authority — 9 importers; `routers/neck/geometry.py:19` literally "Delegates to
canonical …"). **Temperament offsets do NOT introduce a second scale/fret datum** — the earlier
clean result holds once temperament enters. Compensation adjusts *effective string length*
(`compute_compensated_scale_length_mm = scale + saddle_comp − nut_comp`), a **distinct quantity
not fed back into fret spacing** — no datum leak. The one wrinkle is **not** temperament-induced:
`api_v1/fret_math.py` (LIVE standalone router, `api_v1/__init__.py:30`) computes
`distance_from_nut_mm = position − nut_width_mm` (l.120, l.134). The field is named
`nut_width_mm` (a *transverse* width) but described "Nut slot width (subtracted from position)"
and used as a *longitudinal* offset — a **`UNITS_DEFECT` / semantics-datum defect**, latent:
`Field(0.0)` default keeps it inert (matches the 36.37 example), but any real value (43mm nut
width, or even a 0.6mm slot kerf) shifts every fret and drives fret 1 negative. Safe-by-default,
wrong-by-construction.

**(4) Two live fret-position surfaces — `DUPLICATE_DIVERGENT` (software authority).**
`neck/fret_math.py` (canonical, clean, 9 consumers) vs `api_v1/fret_math.py` (separate live
endpoint that inlines its own formula + the nut_width subtraction and does **not** delegate to
the canonical function). Same quantity, two live HTTP authorities, one carrying the latent
datum defect.

**(5) "Compensation" spans different intonation-chain stages — confirmed; mostly staged, not
rival.** The same word names materially different stages, so the hypothesis holds — but liveness
shows they are largely a **pipeline**, not competing authorities:
- `bridge/compensation.py` — **standard lookup tables** (`STANDARD_6_STRING_COMPENSATION`),
  LIVE (via `bridge/geometry.py`, `saddle_compensation_router.py`). `CALIBRATED_MODEL` (published
  per-string setbacks) — the *place-the-saddle* stage.
- `saddle_compensation.py` — **fits a straight saddle line** to per-string comps + action, LIVE
  (`saddle_compensation_router.py`). Different *stage* (geometry fit), not a rival number.
- `nut_compensation_calc.py` — **nut setback** (`nut_setback = f(action, fret_height)`), LIVE
  (3 importers). The *nut-end* stage.
- `neck/fret_math.compute_compensated_scale_length_mm` — the *effective-length combiner*. LIVE.
- `saddle_compensation_calc.py` — **predictive-from-physics** saddle setback (bending stiffness,
  `comp_stretch`). **0 importers → `STALE_DEAD`** — an abandoned *alternate method* for the
  lookup quantity (its own docstring notes the k-factor approach was "rejected"). Not competing
  live authority.
- `nut_compensation_physics.py` — **0 importers → `STALE_DEAD`** (also holds the orphaned
  "sounder" nut-slot-depth model noted in §2).

So the "compensation" fragmentation is primarily a **naming/traceability** issue (predict →
lookup → fit → nut → combine all called "compensation"), plus **two dead alternate estimators**
(`saddle_compensation_calc`, `nut_compensation_physics`) — not a live multi-authority conflict
for one number. This refines the §2/§3 "intonation compensation fragmented" row: the live pieces
are chain *stages*; the genuine debt is the dead physics alternates + the chain-stage naming.

**Section 8 finding:** temperament math is textbook `VALID_REUSE`/`VALID_ALTERNATE_MODEL` with
one trivial `DUPLICATE_EQUIVALENT`; reference pitch is clean; the nut-origin datum survives
temperament. Real findings are **software/units**, not physics: (a) two live fret-position
endpoints (`DUPLICATE_DIVERGENT`), one with a latent `UNITS_DEFECT` (`nut_width_mm` subtracted
from a longitudinal position, default-safe); (b) "compensation" as a chain-stage naming smell
over a real pipeline, with two `STALE_DEAD` alternate estimators. No new taxonomy field required
(existing Provenance · datum · liveness · consumers · software/model-authority sufficed).

---

## Section 9 — `signal_processing` (2026-08-22) — metric vs. decision-layer

Per ruling, kept narrow around one operating question: **does a standard signal-processing /
geometry metric become an authoritative product decision through an uncited threshold, weight,
or gate?** Standard operations (circularity, Hu moments, Hausdorff, 12-TET/cents) are treated as
`VALID_REUSE` unless implementations or consumers materially diverge; the risk is the decision
layer on top. Lifecycle stated first (per the §6 lesson): the vectorizer SP surfaces
(`blueprint-import`, `photo-vectorizer`) are **live in-repo** — none of this code is in the
`vectorizer-sandbox` relocation manifest (only Tier A cognitive/grid/phase2 moved). The heavy
audio DSP is **external** (`tap_tone_pi`, separate repo); the in-repo analyzer is interpretation-only.

**(1) Standard SP/geometry math — `VALID_REUSE`, no defect.**
- **Circularity `4πA/P²`** — identical formula in `photo_vectorizer_v2.py:1573/1882`,
  `march_pipeline_restore.py:197`, and the blueprint classifier feature set. Standard.
- **Hausdorff distance** — `photo-vectorizer/contour_stage.py:75 _hausdorff_distance` (symmetric,
  scipy `directed_hausdorff` with a pure-numpy fallback). Standard; `photo-vectorizer` only (not
  cross-service). A robust modified-Hausdorff is deliberately **preferred for election**
  (`photo_vectorizer_v2.py:3133`, "robust to single outlier points") → `VALID_ALTERNATE_MODEL`
  with a documented rationale.
- **Hu moments** — `vectorizer_phase3.py:247` (feature vector; `blueprint-import` only).
- **12-TET / cents** — `spectrum_service._frequency_to_label` (`1200·log2`, `tolerance_cents=50`
  self-documented "Half a semitone") and `design_advisor.py:355` (`12·log2(f/440)`, explicit A440).
  Standard, and the cents tolerance is a *documented* threshold (natural half-semitone boundary).

**(2) Cross-service duplication — same operation in both surfaces.** The **soundhole classifier
test `80 < dim < 130mm AND circularity > 0.7`** is byte-identical in **three live loci across two
services**: `blueprint-import/vectorizer_phase3.py:701`, `photo-vectorizer/photo_vectorizer_v2.py:1891`,
and `photo-vectorizer/march_pipeline_restore.py:208` (the latter live — imported by
`photo_vectorizer_v2`). Same math **and** same magic numbers → `DUPLICATE_EQUIVALENT`, but the
duplication is of an **uncited decision rule**, so it multiplies the authority-provenance gap
rather than just repeating standard math. (Intra-file wrinkle: `photo_vectorizer_v2` also exposes
`soundhole_circularity_min=0.65` as a configurable default alongside the inline `>0.7` — two
thresholds for one concept.)

**(3) The decision layer — where metrics become authority (`MODEL_AUTHORITY`, `UNKNOWN_ORIGIN`).**
`vectorizer_phase3._rule_*` (l.667-719) is a rule cascade turning standard metrics into
authoritative classifications via **uncited magic-number bands and fixed confidences**:
body_outline `350-650×280-450mm→0.85`, pickup_route `70-110×30-65mm, aspect 1.3-3.0→0.75`,
neck_pocket `→0.80`, control_cavity `→0.70`, soundhole `(…circ>0.7)→0.85`, f_hole
`130-180×30-55mm→0.75`, text `<15mm, aspect>2, circ<0.3→0.70`. The **metrics are `VALID_REUSE`;
the decision layer is the debt** — dimensional bands are plausibly instrument-spec-derived but
uncited, and the confidences (0.70-0.85) are author-assigned with no basis. **ValidationBasis =
`UNKNOWN_ORIGIN`; consumer authority = authoritative** (drives layer/category assignment). Same
family as the §6 body scorers. Adaptive-binarization thresholds in the same class
(`black_ratio>0.3`, `white_ratio>0.95`, `dark_ratio>0.02` → threshold 150/100/0) are likewise
uncited image heuristics gating extraction.

**(4) Coin-candidate scoring (scale calibration) — `MODEL_AUTHORITY`.**
`photo_vectorizer_v2.py:1548-1618` scores the reference coin on sharpness/circularity/size/position
with **uncited weights** (`0.30·circularity + …`) to pick the mm-per-pixel reference — a standard
metric (circularity) folded into an author-weighted decision. `UNKNOWN_ORIGIN`; authoritative
(sets scale). Same shape as the §6 export/body weights.

**(5) Audio SP — interpretation/advisory, honestly scoped (low severity).**
`spectrum_service._interpret_mode` maps uncited frequency bands (80-120 "air/Helmholtz",
150-250 "primary top", 250-400, 400-600, >600) to human-readable text. The bands are uncited and
domain-plausible, **but the consumer is advisory** — it returns interpretation strings, not a gate
or number that drives downstream computation — and the file is explicit about it (three docstrings:
"This is INTERPRETATION"). `ValidationBasis` = `EMPIRICAL`/domain-knowledge, **consumer = advisory**.
This is the well-behaved end of the same pattern: the *same* "standard-metric + uncited band" shape
as the vectorizer classifier, but its low authority makes it not debt. The contrast is the finding:
**authority is set by the consumer tier, not the metric** — captured by ValidationBasis + consumer
authority, no new field needed.

**Section 9 finding:** the SP/geometry *mathematics* is uniformly `VALID_REUSE` (+ one documented
`VALID_ALTERNATE_MODEL`, the robust-Hausdorff election metric). The authority risk is entirely in
the **decision layer**, and the operating question answers **yes for the vectorizer surfaces**
(standard metrics → authoritative classification/scale decisions via uncited thresholds/weights,
`UNKNOWN_ORIGIN`, one soundhole rule `DUPLICATE_EQUIVALENT` across both services) and **no for the
audio surface** (same shape, but advisory-only and self-documented). Lifecycle clean: vectorizer SP
is live in-repo (not relocated); heavy audio DSP is external (`tap_tone_pi`), in-repo analyzer is
interpretation. No new taxonomy dimension required — `ValidationBasis` + consumer-authority
distinguished honest advisory heuristics from authoritative uncited gates exactly as intended.

---

## Section 10 — grouped completion pass: `geometry_2d_3d` · `electronics` · `data_processing` (2026-08-22)

Purpose here is **inventory completion, not further excursion** (per ruling): frozen taxonomy,
no new field, provenance-first, cross-reference existing findings rather than re-finding them.
All three are lower-risk and came back **largely clean** — the standing debt is the finite set
already mapped in §1-§9, which is the point of the census.

### 10a — `geometry_2d_3d`
Concentrated on coordinate frames / datum / units / transform conventions / competing live
geometry ownership (not duplication of standard vector/matrix/curve math).
- **Body Grid coordinate frame — clean, explicit.** `body/ibg/body_grid/grid_normalizer.py`
  transforms raw (pixel/mm) → **centerline-relative normalized** coords via an explicit
  `NormalizationParams` (centerline_x, body_y_min=butt, body_y_max=neck, **`flip_y`** for
  source Y-direction). `body/centerline.py` computes the symmetry axis (SYMMETRIC / ASYMMETRIC /
  OFFSET). This is a **documented, single-authority coordinate system with explicit datum and
  axis-direction handling** → `VALID_REUSE`. It is a *different coordinate space* from the
  fret-math nut-origin (§8) — body-outline grid vs. neck longitudinal — with explicit params, so
  **not** a datum conflict (two spaces, each self-describing).
- **Standard geometry math** (Bézier ≥8 sites, radius-arc, string-spacing, compound radius) is
  already censused: `VALID_REUSE` / single-canonical except **compound radius `DUPLICATE_DIVERGENT`**
  (row 11) — cross-referenced, not re-found.
- **DXF header datum** (`$EXTMIN/$EXTMAX` from geometry, no 1e+20 sentinel) is a governed
  correctness rule (CLAUDE.md / row 1 lineage) — cross-ref, not re-found.
- No new competing live geometry ownership surfaced beyond what §2/§3/§6 already record.

### 10b — `electronics`
Guarded (per ruling) against mistaking ordinary electrical physics for authority debt.
- **Standard electrical relations — `VALID_REUSE`.** `calculators/wiring/impedance_math.py` is
  textbook and self-documented: parallel resistance `1/R=Σ1/Rᵢ`, RC rolloff `f=1/(2πRC)`, pickup
  resonant peak `f=1/(2π√(LC))`. Repetition of these is **not** debt.
- **Embedded component values — documented, standard, low concern.** `treble_bleed.py` carries
  per-style component tables that are **named published designs** (Kinman = cap+series-R, Duncan =
  cap+parallel-R) with concrete values (e.g. `680pF`, `1nF+150K`, `1.2nF‖130K`) — `CALIBRATED_MODEL`
  with **manufacturer/literature provenance**, not `UNKNOWN_ORIGIN`. `impedance_math` defaults
  (`cable_capacitance_pf=500` "typical 15ft cable", `tone_cap_nf=22`) are **documented hardware
  assumptions**, not silent constants. No safety limits apply (passive, low-voltage); **no
  conflicting electrical architectures** found.
- **`pickup_position_calc.py`** uses the same nut-origin fret relation `L − L/2^(n/12)` as a
  building block (cross-ref §8/row 27-28) and places pickups **bridge-origin** relative to
  harmonic nodes — a *correct* second datum for pickups, not a conflict. Reference positions
  (Strat 25.5″, LP 24.75″) are documented standard specs.
- Verdict: `electronics` is a **clean domain** — `VALID_REUSE` physics + documented standard values.

### 10c — `data_processing`
Distinguished mechanical transformation/serialization from interpretive decisions (thresholds,
filtering, confidence, fallback, silent loss).
- **Parsers fail loud — `VALID_REUSE`.** `calculators/scala_loader.py` (`parse_scala_content`,
  `_parse_pitch_line`) **raises `ValueError`** on malformed ratio/cents/integer lines and skips only
  `!` comments — **no silent data loss**, cents↔ratio is standard.
- **Decimation is flagged, not silent — good practice.** `routers/simulation_consolidated_router.py`
  `_decimate_moves_preview` computes stats over the **full** path and decimates only the returned
  *preview*, exposing `moves_decimated: bool` + `preview_stride`. The consumer is told — the
  opposite of silent truncation.
- **Interpretive-decision authority debt is all already censused** (cross-ref, not duplicated):
  vectorizer confidence/threshold assignment → §9 (rows 34-36); rayleigh_ritz "fallback to scipy"
  unbacked claim → §19 (MAINT-DEFER-010); `L_eff` units defect + stale second impl → §20
  (MAINT-DEFER-004); wood dataset severed provenance / unsourced values → §7 (rows 25-26).
- Verdict: `data_processing` mechanics are **clean**; its authority debt is a re-view of
  already-mapped findings, not new territory.

**Section 10 finding:** the three lower-risk domains are **largely `VALID_REUSE` with clean datum,
parser, and data-loss hygiene**; the only authority debt they touch is the finite set already
recorded (§7, §9, §19, §20, and the compound-radius/DXF geometry rows). **No new taxonomy field
required** — the frozen scheme represented every finding. This closes the census surface: the
inventory is a **finite map**, and newly-encountered items resolve to *members of known families*,
not new excursions. Census pass **complete for review**; see the repository-level disposition
matrix below.

---

## Divergence / authority summary

| # | Quantity | Provenance | Bucket | Lens | Live? |
|---|----------|-----------|--------|------|-------|
| 1 | Saw rim speed | `FUNDAMENTAL_PHYSICS` | `UNITS_DEFECT` (safety-relevant) | implementation | LIVE |
| 2 | Nut slot depth | `LUTHIERY_DOMAIN_MODEL` | `DATUM_CONFLICT` + `STALE_DEAD` (sound twin dead) | model/datum | LIVE (buggy) |
| 3 | Nut slot depth / action-at-nut | `LUTHIERY_DOMAIN_MODEL` | `MODEL_AUTHORITY` (fragmented: computed vs `0.5` vs input) | model + software | LIVE |
| 4 | Chipload | `STANDARD_ENGINEERING_RELATION` | `DUPLICATE_DIVERGENT` (relation is `VALID_REUSE`; only invalid-input behavior differs) | software | LIVE |
| 5a | Tool deflection (beam) | `STANDARD_ENGINEERING_RELATION` (faithful) | `CALIBRATED_MODEL` / `MODEL_AUTHORITY` (suspect `E`) | model (constant) | LIVE |
| 5b | Tool deflection (rival) | `CUSTOM_HEURISTIC` | `DUPLICATE_DIVERGENT` (different model vs 5a) | model + software | LIVE |
| 6 | Fret distance (×3) | `STANDARD_ENGINEERING_RELATION` (equal temperament) | **`VALID_REUSE`** — identical math/units/origin; consolidation optional, **not authority debt** | — | LIVE |
| 7 | Nut compensation | `LUTHIERY_DOMAIN_MODEL` | `CANONICAL_SHIM` (deprecated shim still router-wired) | software | LIVE(shim) |
| 8 | Break angle (nut) | `LUTHIERY_DOMAIN_MODEL` | `CANONICAL_SHIM` (deprecated shim still router-wired) | software | LIVE(shim) |
| 9 | Neck angle / taper / bridge-height / string-spacing | `LUTHIERY_DOMAIN_MODEL` | `UNTESTED_HIGH_RISK` | (tests) | LIVE |
| 10 | `relief×0.6`, saddle-comp coeffs, PMF/γ/1.83 | `CALIBRATED_MODEL` | `MODEL_AUTHORITY` (calibration provenance undocumented) | model (constant) | LIVE |
| 11 | Compound radius | `LUTHIERY_DOMAIN_MODEL` | `DUPLICATE_DIVERGENT` (fret-fraction vs distance-fraction interp → different radius at a fret) | model | LIVE |
| 12 | Intonation compensation (saddle/bridge) | `CUSTOM_HEURISTIC` / `EMPIRICAL_MODEL` | `DUPLICATE_DIVERGENT` / fragmented (2 live estimators + nut-end + temperaments) | model + software | LIVE |
| 13 | Bézier (≥8 sites), multiscale fret, radius-arc, string-spacing | `FUNDAMENTAL` / `STANDARD` | `VALID_REUSE` / single-canonical (several `UNTESTED_HIGH_RISK`) — **not** debt | — | LIVE |
| 14 | Top-deflection EI chain (forward + inverse) | `STANDARD_ENGINEERING_RELATION` | `VALID_REUSE` / single coherent authority — same BC (simply-supported), forward↔inverse cross-referenced | — | LIVE |
| 15 | Structural material modulus (Sitka `E_L`) | `CALIBRATED_MODEL` | **`MODEL_AUTHORITY`** — 11.0 GPa (plate) vs 9.5 GPa (brace) vs `wood_species.json` (unused); composed into one EI | model (constant) | LIVE |
| 16 | Fan brace angles | `LUTHIERY_DOMAIN_MODEL` / `CUSTOM_HEURISTIC` | **`STALE_DEAD`** (orphaned; 0 importers) | software | DEAD |
| — | Top deflection, side bending, lignin Tg, saddle force, section props | `STANDARD` / `EMPIRICAL` | `VALID_REUSE` / single-canonical; explicit BCs; **no defect** (lignin Tg is a cited exemplar) | — | LIVE |
| 17 | Soundhole acoustic stack (Helmholtz) | `FUNDAMENTAL_PHYSICS` | **`fragmented`** — `soundhole_calc` (canonical, router) vs `soundhole_physics` (parallel copy, no router); both define it | software + model | LIVE |
| 18 | Acoustic calibration constants (`K0`/`GAMMA`/`PMF`/`1.83`/`STIFFNESS_K`) | `CALIBRATED_MODEL` | `MODEL_AUTHORITY` — mixed CalibrationBasis (K0 literature; γ/PMF/1.83 multi-instrument; **0.798 unknown**); PMF/γ/K0 **duplicated** across calc+physics | model (constant) | LIVE |
| 19 | Rayleigh-Ritz eigensolve fallback | `STANDARD` + `CUSTOM_HEURISTIC` | `MODEL_AUTHORITY` / **unbacked claim** — diagonal approx behind a false "fallback to scipy" (**MAINT-DEFER-010**) | model + software | LIVE |
| 20 | Body volume / `L_eff` | `EMPIRICAL` + `CALIBRATED` | `DUPLICATE` + `UNITS_DEFECT` (**MAINT-DEFER-004**); stale second impl | model | LIVE |
| — | Two-cavity resonator, log-spiral, plate modal, port length, string tension | `STANDARD` / `LUTHIERY_DOMAIN_MODEL` | `VALID_ALTERNATE_MODEL` (two-cavity) / `VALID_REUSE` / single-canonical — **no defect** | — | LIVE |
| 21 | Body-detection scorers — **three live in-repo loci** on three front-end-called endpoints: (a) `blueprint-import/vectorizer_phase3.py:1891 score_body_candidate` (→ `/api/blueprint/vectorize`), (b) `services/api/app/services/contour_scoring.py score_contours` (→ `/api/blueprint/clean`, imported by `blueprint_clean.py:45`), (c) `photo-vectorizer/contour_plausibility.py:61 body_ownership_score` (→ `/api/vectorizer/extract`) | `CUSTOM_HEURISTIC` | `UNKNOWN_ORIGIN` | selection/ranking + gate | **`MODEL_AUTHORITY` / fragmented (live, in-repo)** — three uncited "which contour is the body" impls, all live in-repo, all reached by `blueprint-reader.html`. *Not* migrated residue | model | LIVE |
| 22 | Vectorizer ownership gate — **layered, two uncited thresholds**: orchestrator `ownership_threshold=0.60` (`photo_orchestrator.py:400`) over deep `EXPORT_BLOCK_THRESHOLD=0.30` (`photo_vectorizer_v2.py:2777`) | `CUSTOM_HEURISTIC` | `UNKNOWN_ORIGIN` | **AUTHORITATIVE — gates export** | **`MODEL_AUTHORITY`** — live canonical in-repo gate reached by front-end `/api/vectorizer/extract`; two uncited thresholds at different layers. *Not* residue | software | LIVE |
| 22b | Canonical blueprint path (`/vectorize/async` → REFINED → `edge_to_dxf.py`) | — | **`VALID_REUSE` (canonical)** — named production pipeline; called by `blueprint-reader.html` | — | LIVE |
| 23 | Vectorizer Loop-3 `FeedbackSystem.submit_correction` | — | **`STALE_DEAD`** — in-repo dead experimental stub (no production API; Loop 3 not ratified); three-loop *architecture* is sandbox-owned, this stub is not migrated | software | DEAD |
| — | Scale calibration / `validate_scale_before_export` | `CALIBRATED_MODEL` (gate) | legitimate shipped safety gate; 2.5× correction single-fixture calibrated (`MODEL_AUTHORITY`-lite) | — | LIVE |
| 24 | Wood dimensional change | `STANDARD_ENGINEERING_RELATION` | clean relation + good consumer (reads `wood_species.json`, raises on unknown) — **exemplar** | — | LIVE |
| 25 | Material-property data authority (MOE/density/Janka) | `EMPIRICAL_MODEL` / dataset | **`MODEL_AUTHORITY` / fragmented** — ≥4 MOE authorities disagree; ~450+ dataset values unsourced; **9 calcs embed constants** | model / data | LIVE |
| 26 | Derived-property relations (Janka/thermal/heat/energy from ρ/SG) | `EMPIRICAL_MODEL` | **`STALE_DEAD` + `UNKNOWN_ORIGIN`** — generator `bulk_import_wood_species.py` **deleted**; outputs frozen in JSON | model | DEAD (relation) / values LIVE |
| 27 | Temperament math (ratios, cents, N-TET, just/pyth/meantone, Scala) | `FUNDAMENTAL` (musical) / `STANDARD` | `VALID_REUSE` / `VALID_ALTERNATE_MODEL` — recognized systems, explicit identity + consumers; **not** authority debt. One `DUPLICATE_EQUIVALENT` (octave-extension loop copied) | — | LIVE |
| 28 | Ratio→fret-position datum (temperament) | `STANDARD` | `VALID_REUSE` — **nut-origin holds under temperament**; compensation adjusts effective *string* length, not fret spacing (no second datum) | model/datum | LIVE |
| 29 | Two live fret-position surfaces | `STANDARD` | **`DUPLICATE_DIVERGENT`** — `neck/fret_math` (canonical, 9 consumers) vs `api_v1/fret_math` (standalone endpoint, own inline copy, no delegation) | software | LIVE |
| 30 | `api_v1/fret_math` `distance_from_nut = position − nut_width_mm` | `STANDARD` | **`UNITS_DEFECT`** — transverse `nut_width_mm` subtracted from a longitudinal position; latent (default 0.0 safe; any real value shifts all frets negative) | software/units | LIVE (latent) |
| 31 | "Compensation" across the intonation chain | `CALIBRATED_MODEL` / `EMPIRICAL` | **naming/traceability** — predict→lookup→fit→nut→combine all called "compensation"; live pieces are pipeline *stages*, not rival authorities. Refines §12-row | model + software | LIVE |
| 32 | Saddle/nut predictive-physics estimators | `EMPIRICAL_MODEL` | **`STALE_DEAD`** — `saddle_compensation_calc.py` (0 imp; k-factor "rejected") + `nut_compensation_physics.py` (0 imp; holds orphaned "sounder" nut-slot model) | model | DEAD |
| 33 | SP/geometry metrics (circularity `4πA/P²`, Hu moments, Hausdorff, 12-TET/cents) | `STANDARD` (SP/geometry) | `VALID_REUSE`; robust-Hausdorff election = `VALID_ALTERNATE_MODEL` (documented) | — | LIVE |
| 34 | Soundhole classifier rule (`80-130mm, circ>0.7`) | `STANDARD` metric + heuristic | **`DUPLICATE_EQUIVALENT`** — byte-identical across 3 live loci / 2 services (`vectorizer_phase3`, `photo_vectorizer_v2`, `march_pipeline_restore`); duplicated *uncited decision rule* | software | LIVE |
| 35 | Blueprint contour classifier (`_rule_*` bands + fixed confidences 0.70-0.85) | `STANDARD` metric → decision | **`MODEL_AUTHORITY` / `UNKNOWN_ORIGIN`** — standard metrics become authoritative classification via uncited bands/confidences; authoritative consumer | software/model | LIVE |
| 36 | Coin-candidate scale scoring (weights `0.30·circ+…`) | `CUSTOM_HEURISTIC` | **`MODEL_AUTHORITY` / `UNKNOWN_ORIGIN`** — uncited weights set mm/px scale (same family as §6 body/export weights) | software/model | LIVE |
| 37 | Audio mode interpretation (`_interpret_mode` freq bands; cents match `tol=50`) | `STANDARD` (cents) + `EMPIRICAL` bands | **advisory — not debt** — uncited bands but **consumer=advisory** (returns text, no gate); cents tolerance self-documented. Contrast establishes: authority = consumer tier, not metric | model (advisory) | LIVE |
| 38 | Heavy audio DSP (FFT/peak-extraction) | `STANDARD` (DSP) | **external (`tap_tone_pi`)** — lifecycle `RELOCATED_EXTERNAL`-like; in-repo analyzer consumes pre-computed `ViewerPackV1` spectra | — | external |
| 39 | Body Grid coordinate frame (`grid_normalizer` + `centerline`) | `STANDARD` (geometry) | `VALID_REUSE` — explicit centerline-relative datum, `flip_y`-aware; distinct coord space from fret nut-origin, **not** a conflict | datum | LIVE |
| 40 | Electrical relations (parallel-R, RC rolloff, resonant peak) | `STANDARD_ENGINEERING_RELATION` | `VALID_REUSE` — textbook, self-documented; repetition ≠ debt | — | LIVE |
| 41 | Treble-bleed / pickup-load component values | `CALIBRATED_MODEL` | `VALID_REUSE` — **named published designs** (Kinman/Duncan) + documented hardware defaults (cable 500pF, tone cap 22nF); manufacturer/literature basis, not `UNKNOWN_ORIGIN` | model (constant) | LIVE |
| 42 | `scala_loader` parser | `STANDARD` | `VALID_REUSE` — **fail-loud** (raises on malformed input); no silent data loss | software | LIVE |
| 43 | Simulation move-preview decimation | `STANDARD` | `VALID_REUSE` — **flagged** decimation (`moves_decimated`/`preview_stride`); stats over full path; not silent loss | software | LIVE |
| 44 | **String-course lateral geometry** *(2026-08-23 post-freeze amendment, §11)* | `LUTHIERY_DOMAIN_MODEL` | **`LIVE_AUTHORITY_FRAGMENTATION` / `INCOMPLETE_AUTHORITY`** — shared `spacing.py` abstraction exists but is not canonical (1 importer, bypassed by nut CAM); no equal-edge-gap model; divergent handedness across 5 surfaces | model + software + datum | LIVE |

**Headline for review:**
1. **Axis B (scale origin) is clean** across the whole chain — nut origin everywhere; the only shifts are explicit and zero-fret-aware.
2. **Axis A (string height) has one contained zero-fret inheritance** — `nut_slot_calc` (§17) — and it does **not** propagate; the real problem is that the nut-slot-depth quantity has **no single authority** (live-buggy computer, dead-sound twin, hard-coded `0.5`, input-only consumer).
3. The **two break-angle calcs are not in conflict** (different ends, explicit datums).
4. Deprecated shims (`nut_comp_calc`, `headstock_break_angle`) are still the modules the **routers import** — a wiring smell, not a math defect.
5. **Provenance guards against false positives.** Most repetition here is `VALID_REUSE` of standard relations (fret distance, chip load, the beam-deflection *equation*) — the real findings are the **constants, datums, units, semantics, and ownership** around the equations, not the equations themselves. Only `LUTHIERY_DOMAIN_MODEL` / `CUSTOM_HEURISTIC` repetition (nut-slot datum, the rival deflection heuristic) is genuine authority debt.

## Status / checkpoint

**Mapped so far:** CNC/CAM seed (§1), full `lutherie_geometry` (§2 chain + §3 remainder),
full `structural_mechanics` (§4, +BC field), `acoustic_physics` reconciliation (§5,
+CalibrationBasis), `optimization`/vectorizer heuristics (§6, **lifecycle-corrected
2026-08-22** — see §6), `wood_movement` data authority (§7, `ValidationBasis` **ratified**
and in use), `temperament_tuning` (§8, authority + datum check), `signal_processing` (§9,
metric vs. decision-layer), and the grouped completion pass `geometry_2d_3d` · `electronics` ·
`data_processing` (§10). **CENSUS SURFACE COMPLETE — pass closed for review** (per ruling; the
disposition matrix below is the closing deliverable). No remediation authorized.

**Taxonomy verdict after all domains:** the frozen scheme (Provenance · CalibrationBasis ·
ValidationBasis · BoundaryCondition · datum · liveness · consumers · software/model-authority)
represented **every** finding across 10 sections and 43 rows — **no new dimension was ever
required** after §7. Standing lessons, all reconfirmed by the grouped pass: (a) *liveness ≠
authority* (dead estimators looked like rivals on grep; 0-importer traces made them `STALE_DEAD`);
(b) *classify lifecycle before authority* (compensation "chain" and vectorizer residue both
dissolved into staged pipelines / clean relocations); (c) *authority is set by the consumer tier,
not the metric* (§9 advisory-vs-gate); (d) *provenance guards against false positives* — the great
majority of repetition is `VALID_REUSE` of standard physics/math, not debt. The grouped pass added
**no new authority conflicts** — every debt item resolved to a member of an already-named family.

**Recurring cross-domain landscape (finite inventory taking shape):**
- **Fragmented / duplicated authority** for one quantity: nut-slot depth, chipload,
  tool deflection, compound radius, intonation compensation, soundhole stack.
  (The two body-detection scorers are two live in-repo paths but a single canonical
  capability — `MODEL_AUTHORITY` with uncited weights, not competing fragmented authority.)
- **Uncited weights/thresholds on live production gates** (`MODEL_AUTHORITY`,
  `UNKNOWN_ORIGIN`): body-ownership weights (0.50/0.25/0.10/0.15) and the export
  threshold (0.30) gate a live front-end export path with no recorded validation basis.
- **Dead-but-relevant modules:** `nut_compensation_physics` (dead-but-*better*),
  `fan_brace`, **vectorizer Loop-3 `FeedbackSystem`** (all dead in-repo); **deprecated shims
  still router-wired:** `nut_comp_calc`, `headstock_break_angle`.
- **Constant/material fragmentation** (`MODEL_AUTHORITY`): nut-slot `0.5`, CNC
  `E=90 000`, structural Sitka `E_L` (11.0 vs 9.5), acoustic `PMF/GAMMA/K0` duplicated +
  `STIFFNESS_K=0.798` unsourced.
- **Sound-physics-wrong-input defects:** rim-speed units, `L_eff` units, rayleigh_ritz
  unbacked fallback.
- **Cleanly relocated archaeology (not residue) + live in-repo canonical runtime.**
  Verified 2026-08-22 via the hostinger canonical pipeline: only Tier A vectorizer
  archaeology (cognitive/grid/`vectorizer_phase2`) moved to `vectorizer-sandbox`, and that
  move is complete (modules gone, endpoints repointed, re-import precommit-blocked). The
  body-scoring + export-gate stack is **live canonical in-repo** (`blueprint-reader.html` →
  Railway `/api/blueprint/vectorize/async` REFINED + `/api/vectorizer/extract`) — an
  in-repo `MODEL_AUTHORITY` item (uncited weights 0.50/0.25/0.10/0.15 and threshold 0.30 on
  a live export gate, `UNKNOWN_ORIGIN`), **not** migrated residue. Loop-3 `submit_correction`
  is `STALE_DEAD`. (This corrects a 2026-08-21 over-broadening; see §6 provenance note.)
- **Material-property data authority is its own fragmentation family:** MOE/density/Janka
  spread across `wood_species.json`, `luthier_tonewood_reference.json`, and embedded
  constants in **9 calculators**; ~450+ dataset values unsourced.
- **Severed provenance:** `bulk_import_wood_species.py` (generator of Janka/thermal/etc.)
  deleted while its outputs persist frozen in `wood_species.json` — a "dead generator,
  live data" variant of the dead-code pattern.
- **Good-hygiene exemplars (worth protecting, not fixing):** fail-loud parsers
  (`scala_loader`, `wood_movement` unknown-species raise), flagged (non-silent) decimation
  (`simulation_consolidated_router`), explicit coordinate frames (`grid_normalizer` `flip_y`,
  `centerline`), documented named-design constants (treble-bleed Kinman/Duncan), and the
  self-labeled advisory analyzer (`_interpret_mode`). These show the codebase already contains
  the discipline the debt items lack.
- The **vast majority of repetition is `VALID_REUSE` / `VALID_ALTERNATE_MODEL`**, not debt —
  reconfirmed by the §10 grouped pass, which added no new authority conflict.

## Repository-level disposition matrix (census closing deliverable, 2026-08-22)

The purpose of this matrix is a **finite map, not a task list.** Every census finding is a
*member of a known family*; membership here is a classification, **not** an authorization to
remediate. A finding can touch two families — the **primary** disposition is listed, with the
secondary noted in the disposition column. Row numbers refer to the summary table above.

| Disposition family | Members (row/§ refs) | Disposition note |
|--------------------|----------------------|------------------|
| **VALID / LEAVE ALONE** | Standard/`VALID_REUSE` rows 13, 14, 22b, 24, 27, 28, 33, 39, 40, 41, 42, 43; the `—` alternate-model rows (top-deflection, side-bending, lignin Tg, saddle force, section props, two-cavity resonator, log-spiral, plate modal, port length, string tension); electronics (§10b) | The large majority. Fundamental physics, standard engineering/musical relations, legitimate alternate models, and good-hygiene exemplars. **No action is the correct disposition.** |
| **LIVE AUTHORITY FRAGMENTATION** | 11 (compound radius), 15 (Sitka `E_L` 11.0 vs 9.5), 17 (soundhole stack calc‖physics), 25 (MOE ≥4 authorities), 29 (two fret-position surfaces), 34 (soundhole classifier rule ×3 loci); nut-slot-depth (§2), chipload & tool-deflection (§1/§4); **44 (string-course lateral geometry, §11 — 2026-08-23 amendment)** | Multiple **live** implementations of one quantity/decision. Genuine competition confirmed by consumer/liveness traces. The candidate set for any future "single-authority" decision. |
| **LIVE DEFECT** | 19 (rayleigh_ritz unbacked fallback, MAINT-DEFER-010), 20 (`L_eff` units, MAINT-DEFER-004), 30 (`api_v1/fret_math` `nut_width` units, latent), §1 rim-speed units, §2/§17 nut-slot `+crown/2` (GREEN band unreachable) | Concrete implementation defect on a live path (units/datum/fallback). Bounded and specific. Several already have MAINT-DEFER IDs. |
| **UNVALIDATED AUTHORITY** | 18 (acoustic consts; `0.798` unknown), 21 (body scorers, uncited weights), 22 (export gate, 0.60/0.30 uncited), 35 (blueprint classifier confidences), 36 (coin scale weights), §2 row 10 (saddle-comp/PMF/γ calibration undocumented) | Heuristic/threshold/weight with **consequential consumer authority** (gates export, sets scale, drives classification) but **inadequate `ValidationBasis` (`UNKNOWN_ORIGIN`)**. The "produces product decisions without a basis" family. |
| **DEAD-BUT-RELEVANT** | 32 (`nut_compensation_physics` — the "sounder" nut-slot model; `saddle_compensation_calc` predictive physics) | Orphaned (0 importers) but containing potentially **superior/useful** work. Preserve; do not delete blind. |
| **STALE / SUPERSEDED / MIGRATED** | 16 (fan brace, orphaned), 23 (vectorizer Loop-3 `FeedbackSystem`), 38 (heavy DSP → `tap_tone_pi`), Tier A vectorizer archaeology → `vectorizer-sandbox` (clean relocation), deprecated shims still router-wired (`nut_comp_calc`, `headstock_break_angle`) | Lifecycle explains the apparent duplication. Not competing authority. The §6 correction lives here: the relocation is clean; the runtime is in-repo canonical. |
| **SEVERED PROVENANCE** | 26 (`bulk_import_wood_species.py` deleted, Janka/thermal outputs frozen), 25-partial (~450+ unsourced dataset values) | Live values/artifacts persist but the generator/evidence trail is gone. "Dead generator, live data." |
| **UNTESTED HIGH-RISK** | 13-partial (several `UNTESTED_HIGH_RISK` geometry impls: Bézier ≥8 sites etc.); `validate_scale_before_export` (single-fixture calibrated, important gate) | Live and consequential but without adequate dedicated verification. Risk is *absence of tests*, not a known defect. |
| **INSUFFICIENT EVIDENCE** | `bridge_calc.py` / `acoustic_bridge_calc.py` (deep-trace not done) | Census cannot responsibly adjudicate authority yet. Needs a scoped trace before classification. |

**Reading of the map.** The repository is **mostly sound standard math** with a **finite, bounded**
debt surface: one cluster of *fragmentation* (a handful of quantities with >1 live owner), one
cluster of *unvalidated authority* (uncited weights/thresholds on real gates — the vectorizer stack
and a few acoustic constants), a **small, specific** set of *live defects* (mostly already
MAINT-DEFER-tagged), and a well-explained *lifecycle* tail (dead/migrated/severed). The historical
"shiny objects" — zero-fret, dead-but-better nut model, compound-radius divergence, material-property
fragmentation, soundhole split, vectorizer residue, orphaned feedback work — are **each now a named
member of a family above**, not a standalone emergency. This is the finite landscape the census set
out to produce. **Remediation prioritization is a separate, owner-authorized step** and is explicitly
out of scope here.

## Deferred (not done here — out of census scope)
- Deep-trace `bridge_calc.py` / `acoustic_bridge_calc.py` (currently `INSUFFICIENT_EVIDENCE` — the one unresolved classification).
- Numerical verification of the compound-radius (#11) and compensation (#31/#12) divergences — only if they graduate to a fix decision.
- **Remediation prioritization / dev-order authoring** — a separate, owner-authorized step. The census produces the *map*; it does not schedule the work.

**Census surface status:** the named calculator/formula domains are mapped (§1-§10). The
"147" figure was the raw formula-occurrence count; the census consolidated those into the
**43-row finding inventory + 9-family disposition matrix** above, which is the intended
deliverable. Any later domain not yet named here would slot into the same frozen taxonomy and
disposition families without re-opening them.

---

## Section 11 — POST-FREEZE AMENDMENT (2026-08-23): string-course lateral geometry

> **This section was added after the 2026-08-22 freeze**, under the post-freeze amendment rule
> (dated correction note grounded in new evidence + fresh census↔queue reconciliation). It adds
> **one** finding and **one** dated correction (to the §3 string-spacing row). No prior finding
> text was rewritten. Discovery trigger: a nut-slot spacing review on 2026-08-23.
>
> **Not authorized:** any implementation. This section records and classifies; the reading order
> lives in the queue as item 17 (`STRING-COURSE-AUTH-001`).

### Finding — STRING-COURSE GEOMETRY AUTHORITY — fragmented / missing gauge-aware spacing contract

**This is an authority finding, not a missing feature.** The narrow observation ("gauge-aware
equal-edge spacing is absent from the nut-slot CAM path") is true but is the *symptom*. The finding
is that **ordered string-course lateral geometry has no declared canonical owner**: gauge data,
nut lateral positions, nut E-to-E spread, saddle spread, taper, and CAM slot positions are each
derived independently, by modules that do not agree on string order or on which side of the
centerline is bass.

**Precise statement of the gap** (this supersedes the looser "no shared string-course contract"
framing — a shared abstraction *does* exist):

> A shared spacing abstraction exists (`instrument_geometry/spacing.py`), but it is **not canonical
> across consumers**, **does not implement equal-edge-gap spacing**, and **coexists with a second
> live nut-CAM implementation using a different coordinate convention**.

#### Surfaces traced

| Surface | Role | Emits | Origin / handedness |
|---------|------|-------|---------------------|
| `calculators/nut_slot_calc.py` `STRING_DIAMETERS_MM`, `STANDARD_STRING_SETS` | gauge data + slot **depth** | gauges (in), depth (out) | string order **treble-first** (`e,B,G,D,A,E`) |
| `calculators/nut_compensation_physics.py` `STRING_SETS` (`StringSpec`) | gauge data + compensation physics | gauges incl. **wound flag + pitch** | string order **bass-first** (`Low E … High e`) |
| `instrument_geometry/spacing.py` `compute_centered_spacing_mm` | lateral positions | positions | centerline; **negative = bass** (docstring) |
| `instrument_geometry/spacing.py` `compute_edge_margin_spacing_mm` | lateral positions | positions | **0.0 = bass edge** |
| `cam/nut_slot_cam.py` `generate_string_positions` | lateral positions (**nut CAM**) | positions | 0.0 = left face; **String 1 = high E at low X** (treble at the 0 end) |
| `calculators/acoustic_bridge_calc.py` `compute_string_spacing` | nut + saddle spread, taper | offsets | centerline; **treble side negative** (String 1 = high E at `−e2e/2`) |
| `calculators/bridge_calc.py` `compute_pin_positions`, `string_spacing_mm` presets | saddle/pin positions + preset spans | positions | centerline; **bass at `−half_span`** (Position[0] = low E) |
| `cam/nut_slot_export.py`, `routers/cam/nut_slot_router.py`, `routers/instrument_geometry/nut_fret_router.py` | consumers (DXF / G-code / API) | — | inherit the nut-CAM convention |

#### Evidence — three independent divergences

**(1) Two live lateral-spacing implementations, neither canonical.** `spacing.py` is LIVE but its
only importer is `app/rmos/context.py`. `nut_slot_cam.py` does **not** import it; it computes
`available_width / (num_strings − 1)` inline. Two live owners of one quantity.

**(2) Contradictory handedness for the same representation.** For "offsets from centerline",
`acoustic_bridge_calc` declares **treble negative** while `bridge_calc` and `spacing.py` declare
**bass negative**. These are mutually exclusive readings of an identical output shape.

**(3) Contradictory string ordering in the two gauge registries.** `nut_slot_calc` orders
treble-first; `nut_compensation_physics` orders bass-first. Combined with (2), **an implementer who
plumbs gauges from one module into positions from another silently mirrors the gauge-to-string
assignment** — the thickest string gets the treble slot. This is the concrete failure mode that
makes the prohibition below non-arbitrary, not a stylistic preference.

#### Classification

```text
Quantity:              string-course lateral geometry (ordered string positions at nut and saddle)
Provenance:            LUTHIERY_DOMAIN_MODEL
Lifecycle:             live
Bucket:                LIVE_AUTHORITY_FRAGMENTATION / INCOMPLETE_AUTHORITY
                       (+ DATUM_CONFLICT candidate on handedness — see the bounded P0 note)
Datum:                 edge-clearance semantics UNRESOLVED (see below);
                       handedness/origin divergent across five surfaces
ValidationBasis:       the existing uniform centre-to-centre implementation is FUNCTIONAL and
                       correct for its declared mode; the equal-edge-gap model is ABSENT
Consumer authority:    CAM (nut slot G-code/DXF) + geometry (preview/layout) + export
Software authority:    NONE DECLARED — `spacing.py` looks canonical by name and placement but is
                       consumed by exactly one caller and bypassed by the nut CAM path
```

#### Datum — edge clearance (D4): split verdict, no guessing

`edge_offset_treble_mm` / `edge_offset_bass_mm` are documented only as *"Offset from bass/treble
edge to first/last string."*

- **As implemented: nut edge → string CENTRE.** `generate_slot_toolpath` cuts each slot at a single
  `x_position_mm` centreline; `slot_width_mm` is a separate scalar and never offsets X.
  `test_single_string_position` asserts `positions[0] == 3.5` for `edge_offset_treble_mm=3.5`.
- **As intended: `INSUFFICIENT_EVIDENCE`.** No docstring, schema, or test states whether the
  offset was meant as edge→centre or edge→**outside edge of the outer string**. Because gauge never
  enters the lateral model, the two semantics are indistinguishable in current output — they would
  differ by `gauge/2` per outer string only once gauge is introduced.

Recording both halves is deliberate: the implemented datum is a fact, the intended datum is a
**decision the owner must make before any implementation**, and it cannot be inferred from code
that does not model the distinction.

#### Two spacing models must both be preserved (D3)

```text
UNIFORM_CENTER    equal centre-to-centre  — currently implemented; a VALID explicit mode
EQUAL_EDGE_GAP    equal gap between adjacent string EDGES (gauge-aware) — ABSENT
```

Uniform centre-to-centre is **not** classified as wrong. It is an unlabelled default; the defect is
that the mode is implicit and the alternative is unavailable.

Note also that `compute_edge_margin_spacing_mm` is **edge-margin** (nut edge → outer string), *not*
equal-edge-**gap** (gauge-compensated inter-string gaps). The names are close enough to invite
mistaken reconciliation; they are different quantities, and the presence of the former is not
evidence of the latter.

#### Manual override (`string_positions_x_mm`)

`NutSlotPreviewRequest.string_positions_x_mm` accepts explicit positions that bypass derivation
entirely (validated for count, ordering, and bounds). Recorded as an **escape hatch**, not as
geometry authority: it is a caller-supplied array with no derivation, provenance, or datum
declaration, and its existence is evidence that the derived path was known to be insufficient.

#### Non-finding / prohibited remediation (D2)

> **The gauge table in `nut_slot_calc.py` is evidence that gauge data exists. It does not establish
> that `nut_slot_calc.py` is the canonical string-specification authority.**
>
> **This finding does not authorize copying gauge data from the live nut-slot depth calculator into
> CAM.** Plumbing `STRING_DIAMETERS_MM` / `STANDARD_STRING_SETS` from `nut_slot_calc.py` into
> `nut_slot_cam.py` would deepen authority coupling rather than resolve it — it would make a *depth*
> calculator the de facto owner of *lateral* geometry, and (per evidence (3)) it would do so across
> a string-ordering boundary that no module currently reconciles. Any implementation must first
> identify or create a proper shared authority.

#### Bounded P0 partial trace — string-course representation only

```text
P0 PARTIAL TRACE — string-course representation only
```

The queue's `P0 — investigate before ranking` row (`bridge_calc.py` / `acoustic_bridge_calc.py`,
the census's one `INSUFFICIENT_EVIDENCE` classification) is **NOT discharged, NOT ranked, and NOT
reclassified** by this amendment. Only the *string-spread representation* needed for this finding
was traced:

- `acoustic_bridge_calc.compute_string_spacing` owns **nut + saddle E-to-E spread and the taper
  between them**, emitting uniform centre-to-centre offsets, treble-negative.
- `bridge_calc` owns **per-instrument preset spans** (`string_spacing_mm`, E-to-e at saddle) and
  `compute_pin_positions`, emitting positions bass-negative.

These are **different stages** (acoustic spread/taper analysis vs. bridge pin layout preset), so no
false authority conflict is manufactured between them on the *spacing* quantity. The **handedness
contradiction** between them is recorded here as a `DATUM_CONFLICT` **candidate** and is deliberately
left for the full P0 trace to adjudicate. `bridge_calc` / `acoustic_bridge_calc` remain
`INSUFFICIENT_EVIDENCE` and P0.

#### Relationship to existing findings (no double-counting)

| Existing finding | Relationship |
|------------------|--------------|
| §2 Node 3 / rows 2, 3 — **nut slot DEPTH** authority + datum (queue item 1, P1) | **Distinct quantity.** Item 1 is the *height* axis (slot depth, zero-fret datum inheritance). This finding is the *lateral* axis. They share a nut, a consumer, and one harvest input — not a defect. |
| Row 32 — `nut_compensation_physics` **dead-but-relevant** (queue item 15, P4) | **Shared harvest input.** Its `STRING_SETS` (with wound flag + pitch) is the richer gauge model and is a candidate input for a future string-course authority — the same module already sequenced as item 1's fix source. Recorded as a dependency edge, **not** a merge. |
| §3 string-spacing row — *"single canonical (no duplicates found)"* | **Superseded.** See the dated correction in §3. |
| Row 9 — neck/taper/bridge-height/**string-spacing** `UNTESTED_HIGH_RISK` (queue item 13, P3) | **Different lens.** Row 9's aspect is *absence of tests* on live implementations; this finding's aspect is *absence of a declared owner*. One surface, two lenses — the row-25 aspect-split precedent applies. Not a double-count. |
| Row 31 / §3 — intonation compensation fragmentation | **Adjacent, not overlapping.** Compensation is longitudinal (along the string); this finding is lateral (across the nut/saddle). No shared quantity. |
