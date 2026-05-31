# DEV HANDOFF — Three-Loop / AGE Conflation Removal

**Date:** 2026-05-30
**Author:** Session (Claude) at Ross's direction
**Status:** READY FOR TEAM REVIEW — execution not yet started (AGE sub-section already corrected; see §6)
**Branch context:** opened alongside `docs/boe-ibg-family-conflation` (same class of work)
**Type:** Documentation conflation removal + sandbox migration triage. **NOT a runtime code rip-out.**

---

## 1. Executive summary

`CLAUDE.md` — the **runtime-spine** project instructions — carries a block titled
**"VECTORIZER ARCHITECTURE DECISION — DO NOT BYPASS / APPROVED DESIGN"** that mandates
building a three-loop feedback architecture plus an "Agentic Guidance Engine (AGE)."

Per Ross (2026-05-30, authoritative):

> The three-loop system was **never implemented** into this repo. It was **experimental**
> and was **never approved for use**. It has been **sandboxed into its own repo**
> (`vectorizer-sandbox`) until further work is done.

So the block is a **conflation**: experimental, unapproved research was written into the
governed runtime's instructions as a standing, non-negotiable mandate, backed by an
**unsourced provenance claim** ("Ross identified the correct solution repeatedly across
multiple sessions"). That claim then propagated, unverified, into **≥6 downstream
governance/handoff/audit documents** — one of them marked ACTIVE GOVERNANCE.

This handoff (a) characterizes the conflation precisely, (b) inventories the blast radius,
(c) gives a phased removal plan, and (d) provides a **migration-triage worksheet** so the
team can decide which (if any) in-repo artifacts should move to the sandbox, stay in the
runtime, or be deleted.

---

## 2. Ground truth (authoritative — do not re-litigate)

| Claim in CLAUDE.md | Reality |
|---|---|
| "APPROVED DESIGN" | **Never approved.** Experimental. |
| "DO NOT BYPASS" / "It must be built" | Not a mandate. It is a candidate at most. |
| The **unified, named** three-loop/AGE architecture (`ValidatedExtractor`/`AdaptiveExtractor`/`VectorizerAGE`/`strategy_cache`) | **Never implemented** in `luthiers-toolbox` (zero occurrences — confirmed). This is the conflation. |
| "Ross identified the correct solution repeatedly across multiple sessions" | **Unsourced provenance** — treat as unverified, not as a decision record. |
| Home of the **architecture/research line** | The **`vectorizer-sandbox`** repo, "until further work is done." |

> **PRECISION (2026-05-30) — "never implemented" applies to the *unified, named* architecture, NOT to all loop-flavored code.** Independent loop-flavored components were built organically in the runtime and **some are LIVE — do not delete or sandbox them**:
> - **`GeometryCoachV2`** (`services/photo-vectorizer/`, + `geometry_authority`, `body_isolation_*`) — **LIVE and reachable via the photo-vectorizer API router/orchestrator**; deleting it degrades a live endpoint path. Retro-labeled "Loop 1 (photo pipeline)" — that's a **retrospective name, not evidence the approved architecture was built** (same shape as Sprint B's "Strategy A in Loop 1").
> - **Scale-validation gate** — shipped (`services/api/app/services/scale_validation.py` + `vectorizer_phase3.py`). Keep.
> - **`FeedbackSystem`/`TrainingDataCollector`** — present in `vectorizer_phase3.py`, **dormant** (`enable_feedback=False`).
>
> So the honest statement: *the named, unified CLAUDE.md architecture was never approved or built; independent loop-flavored components exist at varying maturity (one live, one shipped, one dormant) and are real runtime code, not sandbox work.* See §9b for the photo-vectorizer triage.

---

## 3. The conflation, characterized

Same signature as the BOE/IBG family conflation — a soft idea hardened by repetition:

```
experimental sketch
   → "approved design"            (status inflation, no source)
   → "DO NOT BYPASS / must build" (mandate inflation)
   → cited as fact by N docs      (propagation / hardening)
   → one of them = ACTIVE GOVERNANCE
```

Two distinct defects, both load-bearing:

1. **Status inflation.** Experimental research labeled "APPROVED DESIGN — awaiting
   implementation" with no decision record, PR, or ADR behind it.
2. **Unsourced provenance.** "Ross identified … repeatedly across multiple sessions" is a
   self-referential authority claim living *inside* the instructions it authorizes. Each
   re-read hardens it. (The sibling AGE line — "requested by Ross in multiple sessions" —
   was the same defect and is already corrected; see §6.)

---

## 4. Verification performed (evidence base)

All checked against current code on 2026-05-30:

- **No runtime implementation.** No integrated three-loop architecture exists in
  `services/blueprint-import/`. The CLAUDE.md class names (`VectorizerAGE`,
  `ValidatedExtractor`, `AdaptiveExtractor`, `strategy_cache`) appear in **zero** files in
  *either* repo — the sketch was never built under those names anywhere.
- **The experimental work already lives in the sandbox.** `vectorizer-sandbox`
  (`/c/Users/thepr/Downloads/vectorizer-sandbox`, symlinked at
  `docs/audit-sources/vectorizer-sandbox`) contains `src/incubation/agentic_supervisor.py`
  — "Wave 2: multi-pass, self-correcting pipeline supervision" (7 specialized agents). This
  is the real, more-developed embodiment of the loop/AGE *idea*, on a different design line
  than the CLAUDE.md sketch.
- **`agentic_supervisor.py` is absent from the runtime repo** — the supervisor is cleanly
  sandbox-only already.
- **Two-repo model is real and operating.** Sandbox has `MIGRATION_MANIFEST.json`
  (schema 1.1, blob-SHA-tracked), `GOVERNANCE.md`, `SEMANTIC_INCUBATION.md`, and
  `src/{archaeology,incubation,semantic}/`. Runtime governance already references it via
  `docs/governance/VECTORIZER_SANDBOX_MIGRATION_PLAN.md`,
  `docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md`, and
  `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md` ("two-repository model").
- **The corpus already contradicts itself** on implementation state:
  `docs/handoffs/FEEDBACK_LOOP_SYSTEM_HANDOFF.md:94` annotates another doc as
  "(incorrectly states loops 'never implemented')". Ground truth in §2 resolves this:
  never implemented in the runtime.
- **The tap_tone_pi AGE reference was already retracted** — separate external repo, no
  coupling, dead file path, opposite-kind (advisory) engine. See §6.

---

## 5. Blast radius — every artifact carrying the conflation

### 5a. The trunk (CLAUDE.md — runtime-spine instructions)

The whole block under **`## VECTORIZER ARCHITECTURE DECISION — DO NOT BYPASS`**:

| Locus (by heading/quote) | Defect |
|---|---|
| `### Status: APPROVED DESIGN — awaiting implementation` | Status inflation |
| "Ross identified the correct solution repeatedly across multiple sessions." | Unsourced provenance |
| `## The Approved Architecture: Three Feedback Loops` (Loop 1/2/3 specs) | Experimental presented as owed runtime arch |
| `## Scale Validation — Immediate Requirement` | Mixed: the **scale-validation gate is a real shipped runtime feature** (referenced in the DXF section and present in `vectorizer_phase3.py`) — do **not** delete it; only sever its rhetorical dependence on the loops |
| `## Implementation Priority Order` (items 2–5: Loops + AGE) | Mandate for unapproved work |
| `## Rules for Future Sessions` #4 ("The feedback loop architecture is APPROVED.") | Status inflation |
| `## VECTORIZER SPRINT B — Segmentation-First Extraction` | **Resolved (§8a): NOT loop-dependent.** Reframe to drop "Strategy A in Loop 1"; keep as standalone runtime task |
| AGE sub-section + "tap_tone_pi AGE Reference" | **Already corrected 2026-05-30** (§6) |

### 5b. Downstream docs that inherited the unsourced "approved" claim

| Doc | Line(s) | Inherited claim |
|---|---|---|
| `docs/governance/THREE_LOOP_ARCHITECTURE_REFRAMED.md` | 3, 10 | **ACTIVE GOVERNANCE**; "approved in CLAUDE.md (2026-04-02)" |
| `docs/handoffs/VECTORIZER_GEOMETRY_AUDIT_HANDOFF_2026-05-11.md` | 11, 25, 93, 327, 330 | Quotes the AGE mandate verbatim ×2; "APPROVED DESIGN" |
| `docs/handoffs/VECTOR_1B_LOOP2_PROVENANCE_AUDIT.md` | 13, 143 | "Loop 2 … approved in CLAUDE.md but never built" |
| `docs/handoffs/BLUEPRINT_READER_MVP_BASELINE_2026-05-11.md` | 134, 140 | "CLAUDE.md-approved features were never built" |
| `docs/AI_CONTINUITY_FRAMEWORK.md` | 214, 345, 357 | "Approved design, 0 lines"; "Build or remove from CLAUDE.md" |
| `docs/audits/ARCHITECTURAL_GOVERNANCE_HANDOFF_2026-05-07.md` | 43, 189, 193, 195, 451 | "requested by Ross in multiple sessions"; "APPROVED DESIGN … policy being violated" |
| `docs/handoffs/FEEDBACK_LOOP_SYSTEM_HANDOFF.md` | 94 | Contradiction flag (see §4) |

> `AI_CONTINUITY_FRAMEWORK.md:214` already proposed the correct fork: **"Build or remove
> from CLAUDE.md."** Ground truth picks *remove from runtime / keep in sandbox*.

### 5c. Checked and CLEARED (benign — do not touch)

- `docs/governance/SEMANTIC_PROVENANCE_MODEL.md:173` — lists "this is approved" as an
  *example of a claim needing provenance* (this doc is about the problem).
- `docs/governance/AUTHORITY_METADATA_NORMALIZATION.md:201` — `authority_state is approved`
  is a state-machine field check (code).
- `docs/governance/arbitration/C2_CONTINUITY_PROVENANCE_REVIEW.md:205` — field description.
- `docs/architecture/*` "coordinates approved by BOE" / "architecture is approved" —
  conditional authority-chain rules, not historical claims.
- `docs/governance/approvals/…CHECKPOINT_APPROVAL.md:155` — has a real "APPROVED BY:" signer
  line. This is what good attribution looks like.

---

## 6. Already done this session (2026-05-30)

- **CLAUDE.md AGE sub-section** corrected: added a CONFLATION CORRECTION callout,
  demoted the `VectorizerAGE` sketch to "candidate (standalone, NOT a port of tap_tone_pi)",
  rewrote Rule #3 from "must be built" → "candidate, confirm scope," and marked the
  "tap_tone_pi AGE Reference" section **RETRACTED**.
- **Memory** `feedback-vectorizer-age-conflation` saved + indexed, so future sessions don't
  re-harden the bundle.

The trunk-level three-loop claims (§5a) and the downstream docs (§5b) are **untouched** —
they require the team decisions in §8 before edits.

---

## 7. Removal plan (phased)

> **Guardrail:** This is documentation work + migration triage. The canonical runtime
> vectorizer (`vectorizer_phase3.py`) and the real, shipped **scale-validation gate** must
> keep working. Do not delete runtime code as part of "removing the architecture" — the
> loops were never *in* the runtime code; they were only *in the instructions*.

### Phase 0 — Team decisions (BLOCKING; see §8)
Resolve the open questions before any edit. Record answers in §8's decision log.

### Phase 1 — Reframe the CLAUDE.md trunk
1. Replace `## VECTORIZER ARCHITECTURE DECISION — DO NOT BYPASS` with a neutral pointer:
   the three-loop / AGE / adaptive-extraction line is **experimental, unapproved, and lives
   in `vectorizer-sandbox`**; runtime sessions must not treat it as owed work.
2. Delete the status line "APPROVED DESIGN — awaiting implementation" and the
   "Ross identified … repeatedly across multiple sessions" provenance line.
3. Preserve as runtime fact, decoupled from the loops: the **scale-validation gate** and
   any other already-shipped feature. Move these under a plain "Vectorizer runtime notes"
   heading with no "approved architecture" framing.
4. Remove Priority-Order items 2–5 and Rule #4, or relocate them verbatim into the sandbox
   docs if the sandbox wants them as its backlog.
5. Adjudicate `VECTORIZER SPRINT B` per §8-Q3.

### Phase 2 — Reconcile downstream docs (§5b)
For each: add a dated correction banner pointing to this handoff + ground truth (§2), OR
archive per the 60-day/superseded policy if the doc's sole purpose was the loop mandate.
Priority order:
1. `THREE_LOOP_ARCHITECTURE_REFRAMED.md` — **demote from ACTIVE GOVERNANCE** first (highest
   risk: a live governance doc resting on the unsourced claim).
2. The three audit/baseline handoffs that quote the mandate verbatim.
3. `AI_CONTINUITY_FRAMEWORK.md` — flip "approved design" → "experimental, sandboxed."
4. Resolve the `FEEDBACK_LOOP_SYSTEM_HANDOFF.md:94` contradiction with the §2 ground truth.

### Phase 3 — Migration triage (the part Ross asked for) → §9 worksheet
Decide, per artifact, one of: **KEEP** (legitimate runtime), **MIGRATE** (to sandbox),
**DELETE** (dead/duplicated), or **DORMANT** (leave embedded, mark experimental). Record
any MIGRATE in the sandbox `MIGRATION_MANIFEST.json` (schema 1.1; capture source blob SHA).

### Phase 4 — Verify
- `git grep -nI "APPROVED DESIGN\|DO NOT BYPASS\|three-loop\|three loop\|VectorizerAGE\|requested by Ross\|identified.*repeatedly across"` in `luthiers-toolbox` returns only corrected/retracted/archived hits.
- **Capability-snapshot gate (NOT "no import breaks").** The seam swallows `ImportError` and
  degrades silently, so "no import breaks" false-greens. Snapshot all `*_AVAILABLE` flags
  before and after any edit and require an empty diff:
  ```bash
  # before:
  python -c "from app.routers.blueprint import constants as c; import json; \
    print(json.dumps({k:getattr(c,k) for k in dir(c) if k.endswith('_AVAILABLE')}))" > /tmp/flags_before.json
  # after the edit: same dump → diff must be empty
  ```
  This captures `ANALYZER_AVAILABLE`, `VECTORIZER_AVAILABLE`, `PHASE2_AVAILABLE`,
  `PHASE3_AVAILABLE`, `PHASE4_AVAILABLE`, `CALIBRATION_AVAILABLE` — any silent flip (incl. an
  env-dependent flag a hardcoded assert wouldn't enumerate) shows up. (`VECTORIZER_AVAILABLE`
  and `PHASE2_AVAILABLE` are legitimately `False` — relocated / not-in-Docker — so snapshot,
  don't assert-True.)
- Any MIGRATE entry exists in the sandbox manifest with a SHA.
- Update memory `feedback-vectorizer-age-conflation` to note the trunk + downstream cleanup is done.

> **NOTE — doc-conflation pass completed 2026-05-30.** CLAUDE.md trunk reframed (this section's
> headings/status/provenance + Rule #4 + Sprint B label), retain-with-correction. No runtime
> code touched, no stub file deleted. The runtime↔stub safety / collision-proofing work (P0/P1)
> is deferred to its own reviewed diff — see `_CORRECTIONS.md` §C and the append/analyzer caveat
> recorded in §9 below.

---

## 8. Open questions / decision log (Phase 0 — BLOCKING)

| # | Question | Recommended default | Decision |
|---|---|---|---|
| Q1 | Confirm: three-loop + AGE are **experimental, sandbox-owned**, not runtime backlog? | Yes (per §2) | ☐ |
| Q2 | Reframe trunk **in place** with a correction banner, or **archive** the whole block to `docs/archive/` and leave a 3-line pointer in CLAUDE.md? | Archive block, leave pointer (CLAUDE.md is hot context — keep it lean) | ☐ |
| Q3 | Is `VECTORIZER SPRINT B (Segmentation-First)` loop-dependent (→ sandbox) or an independent runtime extraction task (→ keep)? | **RESOLVED 2026-05-30: NOT loop-dependent → KEEP as runtime task** (see §8a) | ☐ confirm |
| Q4 | Should the removed loop specs be **ported into sandbox docs** as its backlog, or just deleted from runtime (sandbox already has its own design)? | Port verbatim into sandbox, then delete from runtime | ☐ |
| Q5 | Downstream docs: correction-banner vs archive? | Banner for audits/handoffs; demote+banner for the ACTIVE GOVERNANCE doc | ☐ |
| Q6 | Per §9: which artifacts MIGRATE / KEEP / DELETE / DORMANT? | See §9 recommendations | ☐ |

---

## 8a. Q3 resolution — Sprint B is NOT loop-dependent (code-verified 2026-05-30)

**Finding:** The CLAUDE.md "(Strategy A in Loop 1)" label is rhetorical bolt-on, not a real
dependency. Segmentation-first extraction (flood-fill / fg_mask-priority → closed contours
by construction) is a single-pass extraction-method change requiring none of the loop/AGE
machinery.

Evidence (grep, 2026-05-30):
- **Runtime already has the prerequisites:** background removal wired in
  (`vectorizer_phase3.py:2763` `use_rembg=True` → `GuitarPhotoProcessor`), and fg_mask
  *production* in `vectorizer_enhancements.py:250–276` (grabcut + rembg).
- **The consuming step is unimplemented in runtime:** no `extract_body_by_segmentation`,
  no flood-fill body extraction in `vectorizer_phase3.py`. Sprint B is *unbuilt runtime
  work*, not partially-built loop work.
- **Reference implementation is in the sandbox:** `src/archaeology/extract_body_grid_v3.py`
  / `_v4.py` (flood-fill), `src/incubation/agentic_supervisor.py` (consumes `fg_mask`),
  goal tracked in `src/evaluation/adaptive_reconstruction/metrics.md` ("no open endpoints").

**Disposition:** **KEEP Sprint B as a runtime task.** In Phase 1, rewrite its CLAUDE.md
entry to drop "Strategy A in Loop 1" and re-describe it as a standalone segmentation-first
improvement consuming the existing rembg/fg_mask output — independent of the three loops.
Nothing migrates runtime→sandbox for Sprint B; the only optional move is the reverse
(promote the proven flood-fill from sandbox into runtime *if/when* Sprint B is implemented).

**Coupling flag (decide together):** Sprint B's in-runtime prerequisite (`fg_mask`
production) lives in `vectorizer_enhancements.py`, which is itself an undecided §9 triage
row. If that file is migrated/deleted from the runtime, Sprint B loses its prerequisite.
**Resolve Q3 and the `vectorizer_enhancements.py` disposition in the same decision.**

---

## 9. Migration-triage worksheet

In-repo artifacts touched by the loop/AGE narrative. Facts verified 2026-05-30. Disposition
column is a **recommendation**; the team decides (Q6). "In sandbox?" = whether an incubation
fork already exists in `vectorizer-sandbox/src/incubation/`.

| Artifact (in `services/blueprint-import/`) | Size | In sandbox? | Notes from CLAUDE.md | Recommended disposition | Decision |
|---|---|---|---|---|---|
| `vectorizer_phase3.py` | 4182 L | yes (`src/incubation/`) | Canonical runtime; "needs all three loops" | **KEEP** (canonical). Scrub stale "CLAUDE.md architecture requirement" comments referencing the retracted mandate. Keep the scale gate. | ☐ |
| `FeedbackSystem` / `TrainingDataCollector` (classes **inside** `vectorizer_phase3.py`) | — | yes (both phase3 copies already contain them) | "exist but NEVER CALLED" (Loop 3 scaffolding) | **DORMANT** (corrected: both copies already have them → nothing to migrate). Not separately deletable without surgery on the canonical file. | ☐ |
| `vectorizer_enhancements.py` | 1155 L | yes (`src/incubation/`) | "Phase 3.7 features, partially integrated"; **produces the `fg_mask` Sprint B needs (§8a)** | **KEEP if Sprint B is kept** (it's Sprint B's prerequisite). Otherwise MIGRATE/DELETE if duplicated & unused. Decide WITH Q3. | ☐ |
| `calibration_integration.py` | 337 L | yes (`src/incubation/`) | **CORRECTED: it IS called** — `constants.py:133` `from calibration_integration import EnhancedCalibrationPipeline` → `create_calibration_pipeline()` behind `CALIBRATION_AVAILABLE` | **KEEP** (live runtime dependency; the earlier "never called / DELETE" was a false negative — see note below). | ☐ |
| `phase4/pipeline.py` | 271 L | yes (**byte-identical**, CRLF-only diff) | **CORRECTED: wired** via `constants.py:118` `from phase4 import …` → `PHASE4_AVAILABLE` | **KEEP** (wired, optional). Byte-identical across repos → nothing to migrate. | ☐ |
| `phase4/dimension_linker.py` | 348 L | yes (**byte-identical**) | part of the wired `phase4` package | **KEEP** (no action; already mirrored) | ☐ |
| `phase4/__init__.py` + `tests/test_dimension_linker.py` | 49 L / — | yes | phase4 packaging + test | **KEEP** (follows phase4) | ☐ |
| `agentic_supervisor.py` | — | **sandbox-only** (absent in runtime) | the real AGE/loop embodiment | **N/A** — already correctly sandbox-only | ☐ |

> **CORRECTIONS INCORPORATED (2026-05-30, cross-repo audit — see `_CORRECTIONS.md`).** Several
> original §9 dispositions rested on a false-negative spot-check (an import scan that ran from
> the wrong working directory with stderr suppressed, reporting "no imports from
> `services/api/app`"). In fact the vectorizer **is** wired into the governed API — optionally,
> behind `try/except ImportError` + `*_AVAILABLE` flags: `constants.py:101` (phase3), `:118`
> (phase4), `:133` (calibration_integration), `phase3_router.py:80`, `blueprint_orchestrator.py:226`.
> Net corrections: `calibration_integration.py` DELETE→**KEEP**; `phase4/*` MIGRATE→**KEEP**
> (byte-identical); `FeedbackSystem`/`TrainingDataCollector` → **DORMANT**; the 7 rich methods in
> `vectorizer_enhancements.py` are **sandbox-original** (a future sandbox→prod graduation
> candidate, not a runtime→sandbox migration). **Nothing migrates runtime→sandbox** for the
> conflation removal. The canonical `app.*` DXF generators are insulated (qualified imports).
>
> **Stub collision-proofing is its own deferred diff (P0/P1), NOT this pass.** Caveat to record:
> the blanket "`insert(0)`→`append`" P0 is **not** safe at `constants.py:48` — `constants.py:58`
> does a bare `from analyzer import create_analyzer`, and `analyzer` collides with the
> `app/analyzer/` package (which does **not** export `create_analyzer`, verified). Under `append`
> it would resolve `app/analyzer/` first → `ImportError` → `ANALYZER_AVAILABLE` silently False.
> So `constants.py:48` must be de-collided first (P1 package-ify, or explicit-path `importlib`).
> The `vectorizer` site (`:69`) is a red herring (no such module either side — already False by
> design). De-collide per-site, verify-first; do not blanket-sweep.

**Pre-decision checks the engineer should run:**
1. Confirm none of the MIGRATE/DELETE candidates are imported by any runtime entry point.
   **(The original "no imports from `services/api/app`" was a false negative — the imports exist
   in `constants.py`; see the corrections note above. The vectorizer is a live optional
   dependency.)**
2. For each DELETE-from-runtime, confirm the sandbox fork is current (diff against
   `src/incubation/<file>`); if the runtime copy is newer, MIGRATE the delta first and log
   it in `MIGRATION_MANIFEST.json` with the source blob SHA.
3. Verify the `phase4/` package isn't transitively required by a kept runtime path before
   migrating it.

---

## 9b. Migration-triage extension — `services/photo-vectorizer/` (read-only inventory, 2026-05-30)

**Why this exists:** the original §9 scoped only to `blueprint-import/` and missed the photo
pipeline — where the **live `GeometryCoachV2` "Loop 1"** lives. Inventory verified 2026-05-30.

**Headline facts:**
- **Parent-runtime-only.** None of the 31 photo-vectorizer modules exist in `vectorizer-sandbox`.
  Nothing here is a sandbox mirror; nothing migrates in either direction for the conflation removal.
- **API-reachable.** `photo_vectorizer_router.py` (`from photo_vectorizer_v2 import …`) →
  `photo_vectorizer_v2.py:3815` instantiates `GeometryCoachV2`. Deleting any live module degrades
  a **live endpoint path**, not just generators/tests. (Reference/path-injection evidenced;
  exact endpoint→coach line not execution-traced.)
- **Relocation boundary (do not "complete" it):** `cognitive_extractor` + `extract_body_grid*`
  already moved out to sandbox (`src/semantic`, `src/archaeology`). `geometry_coach_v2`,
  `geometry_authority`, `body_isolation_*` **stayed and are live.** Marking this line is the point —
  no one should move the live coach to "finish" the relocation.
- **Collision surface (4th `insert(0)` site, `router:103`, injects `_pv_path`):** of ~31 exposed
  names, **only `replay_summary` collides** with a canonical app module — far smaller than
  blueprint-import's surface. But it's the same `insert(0)` mechanism, so the deferred per-site
  append audit (P0) must cover this site too.

| Class | Modules | Disposition |
|---|---|---|
| **KEEP-live / PROTECT** (imported by the API-reachable `photo_vectorizer_v2` pipeline) | `photo_vectorizer_v2` (entry), `geometry_coach_v2`, `geometry_authority`, `body_isolation_result`, `body_isolation_stage`, `body_model`, `contour_stage`, `grid_classify`, `landmark_extractor`, `light_line_body_extractor`, `march_pipeline_restore`, `material_bom`, `photo_silhouette_extractor` | **KEEP.** Live runtime; deletion degrades a live endpoint. **Not** loop-architecture; do not sandbox. |
| **Standalone / generator / superseded** (not imported by `photo_vectorizer_v2`; presence ≠ dead) | `generate_carlos_jumbo_dxf(_enhanced)`, `calibrate_carlos_jumbo`, `geometry_coach` (v1, superseded by v2), `edge_to_dxf` (per memory: rejected V2 approach — verify), `ai_render_extractor`, `blueprint_view_segmenter`, `contour_election`, `contour_plausibility`, `contour_debug_overlay`, `grouping_telemetry`, `multi_view_reconstructor`, `live_test_run/summary`, `replay_*` | **KEEP pending per-module review.** Inventory is for coverage; safe default is KEEP. Some are used by other live modules or generators. No deletion this effort. |
| **Tests** (~31 `test_*`) | incl. `test_geometry_coach_v2_*`, `test_coaching_convergence`, `test_body_isolation_*` | **KEEP** — they exercise the live coach/retry system. |
| **Relocated → sandbox (GONE)** | `cognitive_extractor`, `extract_body_grid*` | **N/A** — already moved. **Do NOT move more.** |

**Net:** nothing in photo-vectorizer migrates for the conflation removal. The live `GeometryCoachV2`
subsystem is protected runtime code. Its "Loop 1 (photo pipeline)" label (from
`FEEDBACK_LOOP_SYSTEM_HANDOFF`) is a **retrospective name**, not evidence the approved CLAUDE.md
architecture was built — same keep-the-code-question-the-label shape as Sprint B.

---

## 10. Definition of done

- [ ] Q1–Q6 answered and recorded (§8).
- [ ] CLAUDE.md trunk reframed/archived; no "APPROVED DESIGN / DO NOT BYPASS / must be built"
      for the loops; unsourced provenance line gone; scale gate preserved as runtime fact.
- [ ] All §5b downstream docs reconciled; the ACTIVE GOVERNANCE doc demoted.
- [ ] §9 worksheet fully dispositioned; every MIGRATE logged in the sandbox manifest with a SHA.
- [ ] Phase 4 verification grep clean; runtime vectorizer + scale gate still pass.
- [ ] Memory updated to record completion.

---

## 11. References

- Ground truth: Ross, 2026-05-30 (this session).
- Trunk: `CLAUDE.md` § "VECTORIZER ARCHITECTURE DECISION — DO NOT BYPASS".
- Sandbox: `/c/Users/thepr/Downloads/vectorizer-sandbox` (symlink `docs/audit-sources/vectorizer-sandbox`); `MIGRATION_MANIFEST.json`, `src/incubation/agentic_supervisor.py`.
- Two-repo model: `docs/governance/VECTORIZER_SANDBOX_MIGRATION_PLAN.md`, `docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md`, `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md`.
- Prior correction: AGE sub-section + memory `feedback-vectorizer-age-conflation` (2026-05-30).
- Sibling effort: `docs/boe-ibg-family-conflation` branch (same conflation class).

---

## 12. Appendix — P0 stub collision-proofing: six-site verdict (DEFERRED, ready for its own diff)

> **Not part of the doc-conflation pass.** This is the read-only audit output for the future P0
> runtime diff (the `sys.path` collision-proofing). Recorded here so P0 isn't blocked. No runtime
> code has been touched. All facts verified read-only 2026-05-30.

**Append-safety verdict — all six `sys.path.insert(0, …)` sites:**

| # | Site | Inserts | Bare imports it enables | `insert(0)`→`append` verdict |
|---|---|---|---|---|
| 1 | `routers/blueprint/constants.py:48` | blueprint-import | `from analyzer import create_analyzer` | ❌ **UNSAFE** — `analyzer` collides with `app/analyzer/` (no `create_analyzer` there) → silent `ANALYZER_AVAILABLE=False`. De-collide first. |
| 2 | `routers/photo_vectorizer_router.py:103` | photo-vectorizer | `from photo_vectorizer_v2 import …` | ✅ safe (no collisions) |
| 3 | `services/blueprint_orchestrator.py:224` | blueprint-import | `from vectorizer_phase3 import …` | ✅ safe (unique) |
| 4 | `routers/blueprint/edge_to_dxf_router.py:65` | photo-vectorizer | `from edge_to_dxf import …` | ✅ safe |
| 5 | `services/blueprint_clean.py:172` | photo-vectorizer | `from contour_plausibility import …` | ✅ safe |
| 6 | `services/blueprint_extract.py:192` (`_ensure_edge_to_dxf_importable`) | photo-vectorizer | `from edge_to_dxf …`, `from grouping_telemetry …` | ✅ safe |

**Bottom line:** 5 of 6 are append-safe. **Only `constants.py:48` (the `analyzer` site) is
append-unsafe** and must be de-collided first (qualified-package import, or explicit-path
`importlib` load for that one site). The original "blanket `insert(0)`→`append` everywhere"
holds for five sites and breaks one — now pinned per-site.

**Sequencing finding — CORRECTED (read the guards, 2026-05-30):** an earlier draft flagged the
orchestrator's `from edge_to_dxf import` as order-dependent (succeeds only after a photo route
ran). **Not so.** Every `edge_to_dxf` import in `blueprint_orchestrator.py` (lines 344, 594, 645)
is immediately preceded by `_ensure_edge_to_dxf_importable()` (`blueprint_extract.py:183-194`),
which idempotently inserts the photo-vectorizer path on demand (594/645 are additionally
`try/except ImportError`-guarded). The orchestrator **self-provisions** — no cross-module order
dependency for `edge_to_dxf`.

**P0 plan (when scheduled — its own reviewed diff):**
1. Consolidate the six inserts into **one idempotent startup helper** adding both `blueprint-import`
   and `photo-vectorizer` (model: the existing `_ensure_edge_to_dxf_importable` helper). Removes
   request-time `sys.path`-front churn. Correctness payoff for `edge_to_dxf` is already realized by
   the ensure helper; the remaining payoff is hygiene + determinism.
2. Flip to `append` everywhere **except** the `constants.py:48` analyzer resolution — give that a
   qualified/`importlib` fix.
3. Gate with the **snapshot-and-diff `*_AVAILABLE`** check (§7 Phase 4) before/after.
