# CAM Dev Order 8I — Drilling Intent Endpoint Migration

**Created:** 2026-06-08
**Status:** READY — net-new build. Spec complete; execute as the first task of a fresh session on a
confirmed shell. **Rebuild, NOT recover** (forensic finding below).
**Repo:** `luthiers-toolbox`
**Branch (when executed):** off `origin/main`. Stage by explicit path.
**Landing discipline:** **push to a remote branch the moment built+verified** — do NOT let it live only
in a local branch across a session boundary. *This is the order that exists because 8I was already lost
exactly that way.* (See "Why this is a rebuild.")

---

## Why this is a rebuild (forensic finding, 2026-06-08)

8I was built once in a prior session — a terminal printed "8I complete" — but **the work evaporated
because it was never pushed/merged before that session ended.** Object-store search confirms it is
genuinely gone, with nothing to recover:

- `git log --all --oneline --source | rg -i "drill.*intent|8i|DrillingDesignV1"` → **empty**
- `git reflog --all | rg -i "drill|intent"` → only the *older governed-export runtime* (`457100cf` 6G
  "add drilling to governed export lifecycle", `b9517943` 5E "add drilling governed preview") and the
  8G/8H intent commits — **no 8I, nothing dangling**
- `DrillingDesignV1` exists nowhere in the repo

This is the clean opposite of 8H (which *was* stranded on salvage and was recovered, `a9634ab1` →
`6af1eb03`). 8I has no orphan. **It must be rebuilt from scratch.**

**The one piece of good news:** the *runtime it wraps is intact.* `cam/drilling/peck_cycle.py`,
`cam/drilling/patterns.py`, the drilling routers, and `DrillConfig` all still exist. You are not
rebuilding drilling — you are rebuilding the **intent lane** over runtime that's still there.

**The lost-8I chat receipt is a spec, not a source.** The prior session's "8I complete" message
documents what the lost version contained (`DrillingDesignV1` with peck validation, feasibility at
depth:diameter ratio, adapter mapping, ~36 tests). Use it as the *requirements list* below — but
**build the adapter from the REAL `DrillConfig`/`peck_cycle` shapes read in Phase 1, NOT from the
chat's description.** The receipt survived; the goods didn't; don't mistake the receipt for the goods.

---

## Core intent

Migrate drilling into **CamIntentV1** following the **8G (V-Carve)** and **8H (Profile)** patterns,
**without altering proven drilling runtime behavior.** Operational, bounded, parity-first,
non-governance-expanding. No new constitutional work.

---

## Pre-flight (before any edit)

1. **Shell gate (bash):** `echo ok` then `git --version; echo "exit=$?"` → must print `exit=0`.
   (Note: `$LASTEXITCODE` is PowerShell-only and reads empty in bash — use `$?`. This caused
   session-long false "is the shell lying?" tension; it was benign.)
2. **Object-store re-check** (cheap, confirms still-absent): the two searches above.
3. **Branch** off `origin/main`. Explicit-path staging.

---

## Phase 1 — GROUND against the real runtime (read-only; do FIRST)

Read the actual shapes the adapter must map to — do not infer them:
- `cam/drilling/peck_cycle.py` and `cam/drilling/patterns.py` — find the real `DrillConfig`
  (fields, types, defaults) and the peck-cycle entry point.
- Existing routers: `cam/routers/drilling/{drill_modal_router,drill_pattern_router,
  drilling_consolidated_router,drilling_preview_router}.py` — how `DrillConfig` is built and how
  gcode is currently generated (the legacy path to keep parity with).
- **The 8G template on main** (canonical): `cam/vcarve/intent_adapter.py`, `intent_schema.py`,
  `cam/routers/vcarve/intent_router.py`, and the vcarve feasibility. Mirror this structure exactly.
  (8H profiling is the second reference — on branch `feat/cam-intent-8h-profiling-recovery`.)

---

## Required deliverables

### 1. Intent design schema — `cam/drilling/intent_schema.py`
`DrillingDesignV1`. Minimum fields:

| Field | Purpose |
|---|---|
| `operation` | "drilling" |
| `hole_positions` | geometry |
| `hole_depth_mm` | runtime depth |
| `hole_diameter_mm` | **functional feasibility input — not decorative** |
| `peck_drilling` | execution mode |
| `peck_depth_mm` | peck semantics |
| `retract_height_mm` | safe motion |
| `spindle_rpm` | optional runtime hint |
| `feed_rate_mm_min` | optional runtime hint |

### 2. Intent adapter — `cam/drilling/intent_adapter.py`
Bridge `CamIntentV1 → DrillConfig`. **Preserve runtime internals; parity-first mapping; no runtime
rewrite.** Map field-for-field against the *real* `DrillConfig` from Phase 1.

### 3. Intent router — `cam/routers/drilling/intent_router.py`
`POST /api/cam/drilling/intent-gcode`. Pipeline matches 8G:
`normalize → validate → adapt → feasibility → policy gate → toolpath generation → artifact
persistence → structured response`. Must call `normalize_cam_intent_v1` (main's self-extending CI
guard enforces this for every `*/routers/*/intent_router.py`).

### 4. Feasibility — `cam/drilling/feasibility.py`
**Peck rule (mandatory, BLOCKING):**
```
if peck_drilling:
    require  peck_depth_mm > 0  AND  peck_depth_mm < hole_depth_mm
    fail feasibility if  peck_depth_mm >= hole_depth_mm
```
**Diameter rule:** `hole_diameter_mm` drives depth-to-diameter validation + feasibility warnings
(deep-hole ratio). Not metadata — functional.

### 5. Provenance / replay
Return `{request_sha256, feasibility_sha256, gcode_sha256}` — aligns with runtime provenance, replay
lane, deterministic artifact comparison.

### 6. Normalization reporting
Surface coercions, unit normalization, inferred defaults, feasibility warnings. **No silent
normalization.**

### 7. Tests
`tests/test_drilling_intent_adapter.py`, `tests/test_drilling_intent_router.py`,
`tests/test_drilling_feasibility.py`. Mandatory cases: valid peck; `peck_depth_mm >= hole_depth_mm`
blocks; diameter feasibility warning; normalization reporting; legacy parity output; stable hashes;
units normalized visibly.

---

## Explicit non-goals (freeze memo — do NOT drift)

No new governance docs · no CAM-INTENT-2 · no runtime-admission redesign · no capability-registry
unification · no ontology · no schema federation · no legacy-router replacement · no peck-runtime
rewrite · no new abstraction layers.

---

## Verification bar — the FULL 8G parity bar (the one 8H passed), witnessed

Not "36 tests pass" — that's how an unwired lane masquerades as done. ALL of:
1. `app.main` imports clean with the new router.
2. `/api/cam/drilling/intent-gcode` **registered in the live route table**.
3. The three test files collect + pass.
4. **Live integration: `POST /api/cam/drilling/intent-gcode → 200`** with a real payload.
5. CI guard passes (`check_execution_class_compliance.py` → operation-lane compliance).
6. **Legacy parity:** intent path output matches the legacy drilling route for equivalent input.

## Landing (the lesson that created this order)

**Commit AND push the moment the bar is green** — `git push -u origin feat/cam-intent-8i-drilling`.
Push ≠ merge: pushing makes it durable; the codeowner still runs the PR/merge. Do not end the session
with 8I living only in a local branch — that is exactly how the first 8I was lost.

---

## Rollout

1. Phase 1 — inspect `peck_cycle.py`, drilling routers, real `DrillConfig`, 8G template.
2. `DrillingDesignV1` + adapter mapping.
3. `/intent-gcode` + feasibility rules + provenance hashes.
4. Tests.
5. Verify against the full bar (incl. live 200 + legacy parity).
6. **Push immediately.**

## Follow-on

After 8I → **8J Pocketing Intent Migration** (`PocketClearingView`/`/cam/pocket`; generator
`lespaul_gcode/pockets.py`) → parity verification → shared response normalization → migration
stabilization review. No governance expansion unless operations expose a concrete contradiction.

---

## Context pointers

- 8G doc: `docs/handoffs/CAM_8G_VCARVE_INTENT_FIRST_ENDPOINT.md`. 8H doc:
  `docs/handoffs/CAM_8H_PROFILE_INTENT_ENDPOINT.md` (+ recovery: branch
  `feat/cam-intent-8h-profiling-recovery`).
- 8I absence forensics: this doc, "Why this is a rebuild."
- Disciplines: search-the-object-store-first; push-before-session-boundary; verify-before-acting.
