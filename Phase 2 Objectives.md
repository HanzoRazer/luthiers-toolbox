Phase 2 is basically: **take the nice clean spec in the Developer Handoff and nail the “core skeleton” in place so the rest of the Waves have something solid to sit on.**

You already did Phase 1 (diagnose drift + add missing core files like `rmos/context.py`, `health_router.py`, etc.). Phase 2 is:

> **Stabilize the *current* architecture without deleting the future.**

Below is a concrete Phase-2 corrective action plan you can follow and/or hand to GitHub Copilot, tied directly to the handoff doc. 

---

## 1. Phase 2 Objectives (what we’re actually fixing)

From the Handoff doc, the big problems we’re targeting now are: 

1. **Phantom imports in `main.py`** (73% of routers point to files that don’t exist).
2. **RMOS + Instrument Geometry + CAM** are *correct* but need:

   * imports cleaned up
   * a couple of tiny smoke tests
3. **Health / lifecycle endpoints** should be reliable for future tooling.
4. **We must NOT lose future plans** for Art Studio, Saw Lab, etc. while we clean.

So Phase 2 is *not* “build new features.” It’s:

> Lock down the working surfaces (RMOS, fret CAM, instrument geometry) + tame `main.py` just enough that everything real is solid and testable.

---

## 2. Step-by-Step Phase 2 Plan

### Step 2.1 – Confirm the new core files are in place

In your workspace, verify these **exist and are committed**:

* `services/api/app/rmos/context.py`
* `services/api/app/routers/health_router.py`
* `services/api/app/calculators/fret_slots_export.py`
* `services/api/app/routers/cam_fret_slots_export_router.py`
* `services/api/app/schemas/cam_fret_slots.py` 

If any are missing, bring them in from your patch bundle *before* we touch `main.py`.

**Copilot prompt idea (backend file check)**

> “List all files under `services/api/app/rmos`, `…/routers`, `…/calculators`, and `…/schemas` and confirm that `context.py`, `health_router.py`, `fret_slots_export.py`, `cam_fret_slots_export_router.py`, and `cam_fret_slots.py` exist and import cleanly.”

---

### Step 2.2 – Quick smoke test of the server

From `services/api`:

```powershell
(.venv) PS> uvicorn app.main:app --reload --port 8000
```

Then in your browser:

* `http://127.0.0.1:8000/health` → should return a JSON “healthy” status. 
* `http://127.0.0.1:8000/docs` → confirm:

  * `/api/cam/fret_slots/preview`
  * `/api/cam/fret_slots/export`
  * `/api/rmos/feasibility` (or equivalent)
  * any instrument-geometry or context endpoints show up.

If those appear and respond, your **Phase A–E core** is alive.

---

### Step 2.3 – Audit but *don’t yet* clean `main.py`

You already have `scripts/audit_phantom_imports.py`. Phase 2 uses it in **report mode** to get a clear picture before deleting anything. 

Run:

```powershell
(.venv) PS> cd scripts
(.venv) PS> python .\audit_phantom_imports.py
(.venv) PS> python .\audit_phantom_imports.py --dry-run
```

This will:

* Print **all phantom router imports** grouped by:

  * RMOS
  * Art Studio
  * CAM
  * Other
* Show you exactly which `try/except` + `if router:` blocks it *would* remove. 

**Don’t run `--clean` yet.** The goal in Phase 2 is to *see* and classify, not to rip them out.

Make a note of anything you absolutely want to keep as “future hooks” (e.g., Art Studio routers, Saw Lab routers).

---

### Step 2.4 – Create a tiny “Phase 2 corrective action” doc in the repo

In the repo root (same level as `DEVELOPER_HANDOFF.md`), create:

`ARCHITECTURE_PHASE_2_CORRECTIVE_ACTION.md`

Outline:

1. **Goal:** Stabilize current RMOS / CAM / Instrument Geometry, audit phantom routers.
2. **What exists and works now** (based on the handoff’s Phase E list). 
3. **List of routers we consider “active”** (must stay wired in main.py).
4. **List of routers that are “future/phantom but important”** (e.g., Art Studio, Saw Lab).
5. **Plan for `main.py`:**

   * Keep the active ones
   * Optionally comment, tag, or move the “future” ones into a separate section
   * Use `audit_phantom_imports.py --clean` later for the truly dead ones.

This doc is your **guardrail** so neither you nor Copilot “helpfully” deletes something you still care about.

---

### Step 2.5 – Stabilize RMOS + Instrument Geometry imports

The handoff doc makes it clear the core layout is: `instrument_geometry` → `rmos` → `calculators` → `routers`. 

Phase 2 action:

1. **Open**:

   * `services/api/app/instrument_geometry/__init__.py`
   * `services/api/app/rmos/__init__.py`
2. Make sure they **only** expose:

   * The new models & registry (InstrumentSpec, etc.)
   * Feasibility / context entry points

If you still have old `InstrumentModelId`, `InstrumentModelStatus`, or other legacy enum imports in there (from Wave 14), Phase 2 is where you either:

* Point those names at a `legacy_enums.py` (so old code compiles but is clearly legacy), or
* Remove those exports if nothing uses them anymore.

**Copilot prompt idea (forensic import check)**

> “In `services/api/app`, search for all imports of `InstrumentModelId` and `InstrumentModelStatus`. Tell me which files still rely on them and whether they can be safely removed or should be redirected to a `legacy_enums.py` shim.”

---

### Step 2.6 – Add the tiniest tests so we know the skeleton holds

You don’t need a full test suite yet. For Phase 2, add 3–4 **smoke tests** under something like:

`services/api/app/tests/phase2/`

Suggested tests:

1. **Instrument geometry import test**

   `test_instrument_geometry_imports.py`:

   * Import `InstrumentSpec` and `InstrumentModelRegistry`.
   * Load `benedetto_17` (or any known model).
   * Assert `scale_length_mm` and a couple of fields look sane.

2. **RMOS context test**

   `test_rmos_context_imports.py`:

   * Import `RmosContext`, `CutType`.
   * Build a `RmosContext.for_fret_slots(…)` or similar factory.
   * Call `get_recommended_feed_mmpm()` and assert it returns a positive float.

3. **Fret slots export smoke test**

   `test_fret_slots_export_smoke.py`:

   * Import the `export` function or call the router via FastAPI `TestClient`.
   * Request a simple 25.5" (647.7 mm) scale, 21 frets, GRBL post.
   * Assert non-empty `gcode` and `slot_count == 21`.

4. **Health endpoint test**

   `test_health_router.py`:

   * Use `TestClient` on `app.main.app`.
   * Hit `/health` and confirm HTTP 200 and `"status": "healthy"`.

These tests do two things:

* Prove the **current import graph works** (no circular/phantom references in the core).
* Give you a safe baseline whenever we start cleaning `main.py` harder in later phases.

**Copilot prompt idea (tests)**

> “Create a `services/api/app/tests/phase2/test_rmos_context_and_fret_export.py` that uses `TestClient(app)` to: 1) hit `/health`, 2) call a fret-slot export endpoint, and 3) exercise `RmosContext` with a simple context and assert non-zero recommended feed.”

---

### Step 2.7 – Decide *when* to run `audit_phantom_imports.py --clean`

This is the *optional* destructive part and can be Phase 2.5 or Phase 3, depending on your comfort level.

I’d recommend:

* **Finish Steps 2.1–2.6.**
* Commit as `patch/phase2-core-stabilization`.
* Run your tiny tests.
* Only then consider:

```powershell
(.venv) PS> python .\audit_phantom_imports.py --clean
```

And commit that separately as something like:
`patch/phase2-main-router-cleanup`.

This keeps the “surgical cleanup” isolated and easy to revert if anything feels off.

---

## 3. How this ties into the Waves

Per the handoff doc, you’re in **Phase E** and already thinking ahead to fan-fret, Saw Lab, Art Studio, etc. 

Phase 2 corrective action is basically:

1. **Lock in** the Phase A–E backend skeleton:

   * Instrument Geometry
   * RMOS context + feasibility
   * Fret Slots CAM preview/export
   * Health checks
2. **Document, don’t delete** future routers.
3. **Lay down just enough tests** to protect that skeleton when we start more aggressive refactors (Saw Lab integration, Tool Library, Art Studio).

Once Phase 2 is done, the NEXT wave (Phase 3/Wave E3) can safely be something like:

* “RMOS Context ↔ Instrument Geometry wiring + Tool Library feed-in,” or
* “Saw Lab 2.0 + RMOS calculators integration.”

---

If you want, the very next thing I can generate is a **ready-to-paste Phase 2 checklist file**:

`ARCHITECTURE_PHASE_2_CORRECTIVE_ACTION.md`
with the exact bullet list and task boxes (`[ ]`) so you can drop it straight in the repo and march down it.
