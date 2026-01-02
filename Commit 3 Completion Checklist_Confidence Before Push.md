## Commit 3 Completion Checklist (Confidence Before Push)

### 0) Preconditions

* [x] `services/api/app/rmos/policies/safety_policy.py` exists and is the robust implementation (RiskLevel + SafetyDecision + SafetyPolicy).
* [x] `services/api/app/rmos/policies/saw_safety_gate.py` exists and delegates correctly (incl. `risk_bucket → risk_level` normalization).
* [x] `services/api/app/rmos/policies/__init__.py` exports the intended surface (`SafetyPolicy`, `RiskLevel`, `SafetyDecision`, `compute_saw_safety_decision`).

---

### 1) Router Coverage (7 remaining routers)

For each router below, confirm the **OPERATION lane endpoint** contains the server-side gate:

* [x] `cam/routers/toolpath/roughing_router.py`
* [x] `routers/drilling_router.py`
* [x] `cam/routers/drilling/pattern_router.py`
* [x] `cam/routers/toolpath/biarc_router.py`
* [x] `art_studio/relief_router.py`
* [x] `routers/adaptive_router.py`
* [x] `cam/routers/toolpath/helical_router.py`

Also confirm any "download" endpoints delegate to the gated endpoint (no duplicate gate needed):

* [x] Any `/download` endpoint calls the main generator function (like drilling) and does not bypass gating.
  - drilling_router.py: `/drill/gcode/download` calls `generate_drill_gcode(body)` which is the gated endpoint

---

### 2) Gate Semantics (must match reference)

In each gated endpoint:

* [x] Feasibility is **recomputed server-side**:

  * `feasibility = compute_feasibility_internal(tool_id=..., req=..., context=...)`
* [x] Decision derived via policy:

  * `decision = SafetyPolicy.extract_safety_decision(feasibility)`
* [x] Block check uses policy and blocks **RED and UNKNOWN** (UNKNOWN treated as RED):

  * `if SafetyPolicy.should_block(decision.risk_level):`
* [x] Feasibility hash computed:

  * `feas_hash = sha256_of_obj(feasibility)`

---

### 3) BLOCKED Artifact Contract (must be consistent)

When blocked, each endpoint must:

* [x] Create a new `run_id = create_run_id()`
* [x] Persist a `RunArtifact` with:

  * [x] `status="BLOCKED"`
  * [x] `event_type` matches your locked pattern:

    * `*_blocked`
  * [x] `tool_id` matches router's existing tool prefix (e.g., `"drilling_gcode"`)
  * [x] `workflow_mode` matches the router convention (hardcoded or derived)
  * [x] `feasibility=<authoritative feasibility payload>`
  * [x] `request_hash=<sha256_of_obj(feasibility)>`
  * [x] `notes` includes risk level (e.g., `Blocked by safety policy: RED`)
* [x] Call `persist_run(artifact)` exactly once

---

### 4) HTTP 409 Block Response (must be uniform)

On block, response must be:

* [x] `raise HTTPException(status_code=409, detail={...})`
* [x] `detail["error"] == "SAFETY_BLOCKED"`
* [x] `detail` includes:

  * [x] `"run_id": <run_id>`
  * [x] `"decision": decision.to_dict()` (or equivalent dict)
  * [x] `"authoritative_feasibility": feasibility`
  * [x] `"message"` is operation-specific but consistent in meaning

---

### 5) event_type Conventions (locked)

Verify each router uses:

* **OK/ERROR:** `{domain}_{operation}_execution`
* **BLOCKED:** `{domain}_{operation}_blocked`

Specifically confirm (ACTUAL values used):

* [x] roughing: `roughing_gcode_execution` / `roughing_gcode_blocked`
* [x] drilling: `drilling_gcode_execution` / `drilling_gcode_blocked`
* [x] drill pattern: `drill_pattern_gcode_execution` / `drill_pattern_gcode_blocked`
* [x] biarc: `biarc_gcode_execution` / `biarc_gcode_blocked`
* [x] relief: `relief_dxf_export` / `relief_dxf_blocked` (DXF export, not gcode)
* [x] adaptive: `adaptive_plan_execution` / `adaptive_plan_blocked` (plan endpoint, gcode delegates)
* [x] helical: `helical_gcode_execution` / `helical_gcode_blocked`

---

### 6) No Bypass Paths

* [x] No endpoint returns G-code without passing through a feasibility gate.
* [x] Any helper function that generates G-code is only called from a gated endpoint (or itself gates).
  - adaptive: `/gcode`, `/batch_export`, `/plan_from_dxf` all call `plan()` which has the gate

---

### 7) Tests & CI Confidence

Run these commands locally:

* [ ] Policy unit tests:

  ```bash
  cd services/api
  pytest tests/rmos -v
  ```
* [ ] RMOS-targeted tests (quick smoke):

  ```bash
  pytest tests -k "rmos" -q
  ```
* [ ] Optional: full suite sanity (if you normally do this before push):

  ```bash
  pytest -q
  ```

---

### 8) Quick Grep Verification (fast audit)

From repo root:

* [x] Confirm all BLOCKED event types exist:

  ```bash
  rg -n "_gcode_blocked|drill_pattern_blocked|dxf_blocked|plan_blocked" services/api/app
  ```
  **Result:** Found in all 9 routers (7 new + vcarve + rosette)

* [x] Confirm feasibility recompute exists in the 7 routers:

  ```bash
  rg -n "compute_feasibility_internal" services/api/app
  ```
  **Result:** Found in all target routers

* [x] Confirm 409 SAFETY_BLOCKED exists across routers:

  ```bash
  rg -n "status_code=409|SAFETY_BLOCKED" services/api/app
  ```
  **Result:** 18 files with 409, 11 files with SAFETY_BLOCKED (includes all target routers)

---

### 9) Final "Push Readiness" Spot Check

* [x] No unused imports introduced by refactors (`pytest` will usually catch, but scan quickly).
* [x] No duplicated helper functions remain in routers (policy is centralized).
* [x] All new code conforms to OPERATION_EXECUTION_GOVERNANCE (server-side feasibility, BLOCKED artifact, deterministic provenance).

---

### Summary

**All 7 routers patched with Phase 2 feasibility gates:**

| Router | Gate Location | Context Token |
|--------|---------------|---------------|
| roughing_router.py | `/gcode` | `roughing_gcode` |
| drilling_router.py | `/drill/gcode` | `drilling_gcode` |
| pattern_router.py | `/gcode` | `drill_pattern_gcode` |
| biarc_router.py | `/gcode` | `biarc_gcode` |
| relief_router.py | `/export-dxf` | `relief_dxf` |
| adaptive_router.py | `/plan` | `adaptive_plan` |
| helical_router.py | `/helical_entry` | `helical_gcode` |

**Ready for commit pending pytest verification.**
