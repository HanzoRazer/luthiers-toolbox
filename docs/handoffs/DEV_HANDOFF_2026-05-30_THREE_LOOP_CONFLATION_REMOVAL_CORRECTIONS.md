# CORRECTION AGENDA — Three-Loop / AGE Conflation Removal Handoff

**Date:** 2026-05-30
**Author:** Session (Claude), vectorizer-sandbox terminal — cross-repo audit
**Status:** ADVISORY. No canonical code edited; the in-flight main handoff is untouched. This is an additive addendum.
**Corrects:** `DEV_HANDOFF_2026-05-30_THREE_LOOP_CONFLATION_REMOVAL.md` (the "main handoff")
**Scope of authority:** factual corrections + a stub-safety/collision-proofing plan. The conflation-removal **direction is correct and unchanged** — remove the unsourced three-loop/AGE mandate, keep the runtime code, keep Sprint B. Only the factual base and the integration-seam safety need work before execution.

---

## 0. Why this exists

The main handoff's *direction* is sound, but its *verification base* contains one material error that propagates into wrong dispositions, and it does not yet treat the runtime↔vectorizer wiring as what the owner has now declared it to be: **the graduation stub** where the finished sandbox work will plug in. That stub must be (a) safe, (b) collision-proof, and (c) non-interfering with the canonical blueprint→DXF pipeline. This addendum supplies the corrections and the stub-safety plan, all evidence-anchored (verified 2026-05-30).

---

## A. Factual corrections to the main handoff

### A1. "The vectorizer isn't wired into the governed runtime" — FALSE
The main handoff's verification states the blueprint-import vectorizer files are not imported by `services/api/app` and the vectorizer "isn't wired into the governed FastAPI runtime at all." It **is** wired — via *guarded, optional* lazy imports:

| Site | Wiring |
|---|---|
| `services/api/app/routers/blueprint/constants.py:48` | `sys.path.insert(0, BLUEPRINT_SERVICE_PATH)` at **module load** |
| `constants.py:101` | `from vectorizer_phase3 import extract_guitar_blueprint, Phase3Vectorizer` → sets `PHASE3_AVAILABLE` |
| `constants.py` (phase4 block) | `from phase4 import process_blueprint, BlueprintPipeline, PipelineResult` → `PHASE4_AVAILABLE` |
| `constants.py:133` | `from calibration_integration import EnhancedCalibrationPipeline` (wrapped in `create_calibration_pipeline()`) → `CALIBRATION_AVAILABLE` |
| `services/api/app/routers/blueprint/phase3_router.py:80` | `from vectorizer_phase3 import SKLEARN_AVAILABLE, ENHANCEMENTS_AVAILABLE` |
| `services/api/app/services/blueprint_orchestrator.py:219-226` | lazy `sys.path.insert(0, bp_path)` + `from vectorizer_phase3 import Phase3Vectorizer` |

Each is wrapped in `try/except ImportError` that **swallows failure and flips a `*_AVAILABLE` flag to False**. A top-of-file static import scan misses these in-function/guarded imports — which is almost certainly how the "not wired" conclusion was reached. Functionally, when blueprint-import is present, the API **loads and calls the vectorizer.** It is an *optional-but-live* runtime dependency.

### A2. `calibration_integration.py` — KEEP, not DELETE
Main handoff §9 marks it **DELETE from runtime ("never called")**. It **is** called: imported in `constants.py:133` and wrapped in `create_calibration_pipeline()` behind `CALIBRATION_AVAILABLE`. Deleting it flips the flag to False and **silently removes calibration from the API.** Correct disposition: **KEEP.**

### A3. The Phase-4 verify gate is unsafe as written
Main handoff §7 Phase 4 checks "no runtime test or import breaks." Because the seam imports are wrapped in `try/except ImportError`, **deleting a depended-on file produces no import error and no test failure — only silent capability loss** (`*_AVAILABLE` → False). "No import breaks" therefore false-greens. **Replace the gate with a capability assertion:** after any change, assert `PHASE3_AVAILABLE`, `PHASE4_AVAILABLE`, and `CALIBRATION_AVAILABLE` are still `True`.

---

## B. Cross-repo migration corrections (sandbox-side evidence the main handoff lacked)

Several §9 "MIGRATE → sandbox" rows collapse once the sandbox is actually inspected:

| Main handoff §9 claim | Correction (verified) |
|---|---|
| `vectorizer_enhancements.py` may need MIGRATE to sandbox | The 7 richest methods (`_looks_like_humbucker/single_coil/p90/neck_pocket`, `_validate_against_spec`, `_calibrate_from_ocr`, `_measure_contour_dimensions`) are **sandbox-original** — `git log --all -S` shows they **never existed in the parent**, any commit, any path. Nothing migrates *in*; the sandbox is already richer. |
| Sandbox is a fork the runtime might feed | Sandbox `vectorizer_phase3.py` **lacks the scale gate** (`validate_scale_before_export`, `_safe_dxf_save`) that the runtime has and that existed at fork `f1e11d99`. The sandbox copy is ~775 lines **behind** — a stale snapshot, not a migration source. |
| `FeedbackSystem`/`TrainingDataCollector` → DORMANT **or MIGRATE** | Both phase3 copies already contain them; the parent's are annotated DEAD. Nothing to move → **DORMANT** only. |
| `phase4/*` → MIGRATE candidates | `phase4/*` is **byte-identical** across repos (CRLF-only diff). Already mirrored; no action. |
| Manifest tracks provenance | `MIGRATION_MANIFEST.json` records source SHAs for the Tier-A `photo-vectorizer/` modules + `vectorizer_phase2.py`, but **not** `vectorizer_phase3.py`/`vectorizer_enhancements.py`. Provenance gap — log their blob SHAs (or mark "source: dev working copy, unverified"). |

**Net:** nothing needs to migrate runtime→sandbox for the conflation removal. The sandbox-original enhancement methods are a future **graduation candidate (sandbox→production)** through the bridge — *unapproved*, not a migration.

---

## C. Integration-stub safety & collision-proofing  ← the owner's primary concern

**Requirement (owner, 2026-05-30):** the runtime↔vectorizer connection (a) is the stub the finished sandbox work will plug into, (b) must be safe and **collision-proof**, and (c) **must not interfere with the canonical working blueprint→DXF pipeline.**

### C1. Verdict: SAFE TODAY, but by convention — NOT collision-proof

**Why it's safe right now (the canonical pipeline is insulated):**
- The canonical DXF path imports everything **package-qualified** — `from app.util.dxf_compat import ...`, `from ..util.dxf_compat import ...` (bracing_router, inlay_router, inlay_export, inlay_calc, archtop_contour_generator). Qualified imports resolve through the `app` package tree, **immune** to `sys.path` top-level shadowing.
- The canonical DXF generators in `art_studio/`, `cam/`, `calculators/` **do not import the stub at all** (verified: zero bare imports of `vectorizer_phase3`/`phase4`/`calibration_integration` there).
- The stub is **quarantined** to `routers/blueprint/` + `blueprint_orchestrator.py`, behind `*_AVAILABLE` try/except guards.

**Why it is NOT collision-proof (the latent landmine):**
`constants.py:48` runs `sys.path.insert(0, blueprint-import)` at **module load** — placing a directory of **generically-named** modules at the **front** of `sys.path` process-wide, the instant the blueprint router is imported. Four of those names collide with real, *different* canonical modules:

| blueprint-import name | Collides with | Severity |
|---|---|---|
| `dxf_compat.py` | `app/util/dxf_compat.py` — **DIFFERENT (200L vs 176L)** | **High** — wrong-DXF-output if ever resolved bare |
| `analyzer.py` | `app/analyzer/` (package) | High |
| `config/` (package) | extremely common bare-import name | High (latent) |
| `calibration/` (package) | `app/calculators/plate_design/calibration.py` | Medium |

Today nothing does a **bare** `import dxf_compat` / `import config` / `import analyzer`, so no collision fires. That safety is **unenforced convention.** The moment any future code — a canonical addition, a third-party dependency, **or the graduated sandbox plugging into the stub** — does a bare `import config` (or any colliding name), it silently binds blueprint-import's version. With `dxf_compat` divergent, that is a **silent wrong-output bug with no import error.**

### C2. The sequencing hazard (order-dependent, non-deterministic)

There are **six** `sys.path.insert(0, …)` of vectorizer/blueprint/photo-vectorizer dirs, fired at **mixed lifecycle points**:

| Site | When it fires |
|---|---|
| `constants.py:48` | module load (blueprint router import, ~startup) |
| `blueprint_orchestrator.py:224` | **lazy** — first blueprint request |
| `edge_to_dxf_router.py:65` | lazy — first edge-to-dxf request |
| `photo_vectorizer_router.py:103` | lazy — first photo-vectorizer request |
| `blueprint_clean.py:172` | lazy |
| `blueprint_extract.py:192` | lazy |

Because each inserts at **position 0**, the directory that owns the front of `sys.path` **changes during the process lifetime depending on which endpoint was hit first.** A bare `import config` can therefore resolve to *different* places before vs. after the first blueprint/photo request — an order-dependent heisenbug that won't reproduce in a unit test but can surface under live request interleaving. This is the "sequencing order" risk: the seam mutates global import state lazily and repeatedly, at request time.

### C3. Collision-proofing plan (makes the stub graduation-ready; canonical untouched)

**P0 — Convert shadowing to non-shadowing (one-line-each, high impact).**
Change the stub's `sys.path.insert(0, <path>)` → `sys.path.append(<path>)` at: `constants.py:48`, `blueprint_orchestrator.py:224`, `edge_to_dxf_router.py:65`, `photo_vectorizer_router.py:103`, `blueprint_clean.py:172`, `blueprint_extract.py:192`. Append makes blueprint-import the **lowest** priority source — it can only resolve names nothing else provides, so it can **never** shadow a canonical/stdlib/site-packages module. Safe because the stub's *needed* names (`vectorizer_phase3`, `phase4`) are unique and still resolve. This neutralizes the generic-name landmine.

**P0 — Idempotent, single insertion point, deterministic time.**
Replace the six scattered inserts with one idempotent helper (`if path not in sys.path: sys.path.append(path)`) invoked **once at app init**. Removes the request-time re-insertion that mutates the front of `sys.path` mid-process → kills the sequencing heisenbug.

**P1 — Structural fix (the real graduation seam).**
Package blueprint-import as an importable package (e.g. `blueprint_import/`) and switch the seam to qualified imports: `from blueprint_import.vectorizer_phase3 import …`. Eliminates `sys.path` manipulation entirely → collisions become **structurally impossible**. This is the clean target the sandbox should graduate *into*: it publishes a versioned package, the API imports it by qualified name behind the `*_AVAILABLE` flag, and the canonical `app.*` pipeline is provably untouched.

**P1 — Regression guard (CI).**
Add an import-isolation test: after importing the blueprint router, assert the canonical module is what resolves — e.g. `import app.util.dxf_compat as c; assert "blueprint-import" not in c.__file__` — and assert `PHASE3_/PHASE4_/CALIBRATION_AVAILABLE` are all True. CI then catches any future bare-name regression or accidental capability loss.

**P2 — Rename collision-prone generics (belt-and-suspenders, at graduation).**
In the graduated package, rename `config` → `bp_config`, `analyzer` → `bp_analyzer` so even a stray bare import cannot collide.

### C4. The graduation-seam contract (invariant to enforce)

> **Canonical = `app.*` qualified imports only. Stub = quarantined behind `*_AVAILABLE` flags and (after P0/P1) append-path or a qualified package. No bare module name may bridge the two.**

When the sandbox finishes: it publishes into the stub location, the `*_AVAILABLE` flag flips True, and the canonical `art_studio`/`cam`/`calculators` DXF generators keep running unchanged because they only ever import `app.util.*`. The stub *adds* capability behind a flag; it never *replaces* canonical code. Hold this invariant and the connection is collision-proof and non-interfering by construction, not by luck.

---

## D. Paste-ready edits for the main handoff

**§4 (Verification) — replace the "not wired" bullet with:**
> - **The vectorizer IS wired into the governed API — optionally, behind guards.** `constants.py` (lazy `from vectorizer_phase3/phase4/calibration_integration import …` under `try/except`, `*_AVAILABLE` flags, `sys.path.insert(0, blueprint-import)` at module load), `phase3_router.py:80`, and `blueprint_orchestrator.py:226` (lazy load with its own `sys.path.insert`). The canonical `app.*` DXF generators are insulated (qualified imports); the stub is quarantined to `routers/blueprint/` + the orchestrator.

**§7 Phase 4 — replace the verify bullet:**
> - Capability gate (not "no import breaks"): assert `PHASE3_AVAILABLE`, `PHASE4_AVAILABLE`, `CALIBRATION_AVAILABLE` remain `True` after edits (the seam swallows ImportError, so deletions degrade silently).

**§9 row — `calibration_integration.py`:**
> | `calibration_integration.py` | 337 L | yes | **Imported by `constants.py:133`** via `create_calibration_pipeline()` behind `CALIBRATION_AVAILABLE` | **KEEP** (live runtime dependency; NOT "never called") | ☐ |

**§9 row — `FeedbackSystem`/`TrainingDataCollector`:** change disposition to **DORMANT** (both phase3 copies already contain them; nothing to migrate).

**New §9 rows / notes:** `phase4/*` = byte-identical, no action. `vectorizer_enhancements.py` 7 methods = sandbox-original (graduation candidate, not migration). Manifest provenance gap for phase3/enhancements.

**New section to add — "§10 Integration-stub safety":** import §C of this addendum (collision verdict + sequencing hazard + P0/P1/P2 plan + the seam contract).

---

## E. Re-runnable verification (from `luthiers-toolbox/`)

```bash
# Stub wiring is live (not "unwired")
grep -rn "from vectorizer_phase3\|from calibration_integration\|from phase4 import" services/api/app/routers/blueprint services/api/app/services --include="*.py" | grep -v __pycache__

# Canonical DXF generators are insulated (expect empty)
grep -rn "import vectorizer_phase3\|from phase4 import\|from calibration_integration" services/api/app/art_studio services/api/app/cam services/api/app/calculators --include="*.py" | grep -v __pycache__

# Collision surface: blueprint-import names vs same-named app modules
diff -q services/api/app/util/dxf_compat.py services/blueprint-import/dxf_compat.py   # expect: differ

# Every sys.path.insert(0) of a vectorizer/blueprint dir (the sequencing surface)
grep -rn "sys.path.insert" services/api/app --include="*.py" | grep -v __pycache__

# No bare imports of colliding names in canonical app (expect empty = safe-by-convention today)
grep -rn "^\s*import config\b\|^\s*import analyzer\b\|^\s*import dxf_compat\b\|^\s*import calibration\b" services/api/app --include="*.py" | grep -v __pycache__
```

---

## F. Disposition summary

| Item | Status |
|---|---|
| Conflation-removal direction | **Correct — unchanged** |
| "Vectorizer not wired" | **Corrected → wired, optional, guarded** (§A1) |
| `calibration_integration.py` | **DELETE → KEEP** (§A2) |
| Verify gate | **"no import breaks" → assert `*_AVAILABLE`** (§A3) |
| Migration runtime→sandbox | **None needed** (§B) |
| Stub collision-proofing | **Safe-by-convention today; P0/P1 to make it proof** (§C) |
| Sequencing hazard | **Six lazy `insert(0)` → consolidate + `append`** (§C2/C3) |

*No canonical code, the main handoff, or runtime behavior was modified by this addendum.*
