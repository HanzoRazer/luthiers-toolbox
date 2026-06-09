# CAM Dev Order 8J — Pocketing CamIntentV1 Migration (RECONSTRUCT from bytecode)

**Created:** 2026-06-08
**Status:** READY — **UNBLOCKED** (8G+8H+8I all merged to main as of 2026-06-09; 8I = squash
`a9409305`). A **RECONSTRUCTION from recovered bytecode**, not a build-from-spec. Branch off current
main (which has 8G+8H+8I — the correct base for the fourth lane).
**Repo:** `luthiers-toolbox`
**Branch (when executed):** off `origin/main`. Explicit-path staging. **Push the moment built+verified.**
**Source of truth:** `docs/handoffs/RECOVERY_8J_POCKETING_BYTECODE_2026-06-08.md` — the disassembly of
the lost lane's `.pyc`. **That is the spec; this doc summarizes it.**

---

## Why this is a reconstruction (not a build)

8J was built+compiled **2026-05-25** (same session as 8H) but its `.py` source was **never committed
and is lost**. Only orphaned `.pyc` survived in `__pycache__` (Python 3.14). Object-store search
confirmed: `git log --all` for pocketing intent is empty, no dangling commit holds it. The bytecode was
**preserved** (committed+pushed) as the RECOVERY doc above before a `git clean` could erase it.

**The recovered bytecode REFUTES the original speculative 8J spec.** The earlier dev order guessed
`PocketDesignV1` would carry `feed_rate_mm_min`, `spindle_rpm`, `entry_strategy`. **None of those exist
in the built lane.** The real schema (below) is the ground truth. Reconstruct from the bytecode; do
NOT reintroduce the refuted guesses.

---

## Templates: match 8G/8H (NOT "8I")

The original spec said "match the 8I pattern." 8I does not exist yet (it's also a rebuild). The real
templates are **8G (V-Carve, merged on main)** and **8H (Profile, recovered, pushed)**. 8I, when built,
will also follow 8G/8H. Pattern against 8G/8H.

---

## Phase 1 — search-before-building gate (RESULT, 2026-06-08)

Already run. Findings:
- **Pocket RUNTIME exists** (wrap, don't rebuild): `cam/flying_v/pocket_generator.py`,
  `cam/routers/toolpath/roughing_router.py` (roughing == pocket clearing). Confirm the exact runtime
  config class the adapter targets — the RECOVERY adapter disassembly names it (it is NOT
  `DrillConfig`/`PocketRuntimeConfig`; read `cam/pocketing/intent_adapter` in the recovery doc).
- **Intent lane source: LOST**, recovered as bytecode → RECOVERY doc. `cam/pocketing/` and
  `cam/routers/pocketing/` currently contain only `__pycache__/` (orphaned `.pyc`, untracked).
- The frontend `PocketClearingView.vue` is a `setTimeout` scaffold (separate wiring task).

---

## Recovered schema — `PocketDesignV1` (from `intent_schema.pyc`, authoritative)

```python
class PocketPointV1(BaseModel):
    x: float        # "X coordinate in mm"
    y: float        # "Y coordinate in mm"

class PocketIslandV1(BaseModel):
    boundary: List[PocketPointV1]    # "Island boundary as list of points"
    # validator validate_boundary_length: >= 3 points ("Island boundary must have at least 3 points")

class PocketDesignV1(BaseModel):
    boundary: List[PocketPointV1]        # "Pocket boundary as list of points (must form simple polygon)"
    islands: List[PocketIslandV1]        # "Islands (no-cut regions) within the pocket"  <-- NOT in old spec
    pocket_depth_mm: float               # "Total pocket depth in mm"
    tool_diameter_mm: float              # "Tool diameter in mm (L.1 range: 0.5-50mm)"
    stepover_percent: ...                # "Stepover as percentage of tool diameter (30-70%)"
    roughing_only: bool                  # "If True, skip finishing pass"               <-- NOT in old spec
    finish_pass: bool                    # "Whether to include a finishing pass"
    finish_allowance_mm: ...             # "Material left for finishing pass (mm)"       <-- NOT in old spec
    # validate_boundary_length: boundary >= 3 points
    # validate_finish_coherence (model_validator, mode="after"): finishing config coherence

def validate_pocket_design(design_dict: dict) -> PocketDesignV1:
    # raises ValueError("Invalid Pocketing design: ...")
```

**REFUTED guesses (do NOT add):** `feed_rate_mm_min`, `spindle_rpm`, `entry_strategy` — absent from the
built lane. Exact field types/defaults/ranges and the validator bodies: read the disassembly in the
RECOVERY doc.

---

## Deliverables (reconstruct each from its `.pyc` disassembly in the RECOVERY doc)

1. `cam/pocketing/intent_schema.py` — `PocketDesignV1` + `PocketPointV1` + `PocketIslandV1` + validators
   (recovered above; full detail in RECOVERY §`intent_schema`).
2. `cam/pocketing/feasibility.py` — recovered in RECOVERY §`feasibility` (~14KB bytecode, the largest;
   stepover/tool-vs-feature-width/depth-ratio/boundary checks — observational, warn-or-block, no mutate).
3. `cam/pocketing/intent_adapter.py` — `PocketDesignV1 → <runtime config>` (target class named in
   RECOVERY §`intent_adapter`); field mapping + default normalization, no geometry/toolpath generation.
4. `cam/routers/pocketing/intent_router.py` — `POST /api/cam/pocketing/intent-gcode`; OPERATION-lane
   flow `normalize_cam_intent_v1 → validate → adapt → feasibility → policy → toolpath → persist →
   response` with provenance hashes + normalization report. Recovered in RECOVERY §`intent_router`.
5. `cam/pocketing/__init__.py`, `cam/routers/pocketing/__init__.py` — wiring (recovered).
6. Tests: `tests/test_pocketing_intent_{schema,feasibility,adapter,router}.py` — rebuild to the
   recovered behavior (the lost lane's tests were not compiled/recovered; author against recovered code).

---

## Verification bar — full 8G parity (witnessed), NOT "tests pass"

1. `app.main` imports with the router. 2. `/api/cam/pocketing/intent-gcode` registered in live routes.
3. Tests collect + pass. 4. **Live `POST …/intent-gcode → 200`**. 5. CI guard passes (operation-lane).
6. Legacy parity vs the existing pocket/roughing route. Then **push immediately**.

## Non-goals (freeze memo)

No new governance · no CAM-INTENT-2 · no runtime/admission redesign · no registry unification · no
ontology · no schema federation · no legacy-router replacement · no pocket-runtime rewrite.

## Sequence in the bridge

land 8H → rebuild 8I → **reconstruct 8J from RECOVERY bytecode** → parity verification → shared
response normalization → stabilization review. 8J is fourth; it waits behind 8I, with its source
material already preserved and durable.
