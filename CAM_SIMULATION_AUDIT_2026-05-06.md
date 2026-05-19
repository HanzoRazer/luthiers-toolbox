# CAM Animated Simulation — Audit of "Production-Ready" Claim

**Audit date:** 2026-05-06
**Auditor:** Claude (verification pass)
**Source document audited:** `CAM Animated Simulation — Build Status` (dated 2026-05-06)
**Repo state:** `luthiers-toolbox-main__37__7z` (extracted)
**Scope:** Verify claims in the build status document against actual repo contents
**Method:** Read-only — file inspection, grep, test collection, attempted test execution

---

## Executive Summary

The build status document claims the CAM simulation system is "substantially complete" and "production-ready" with "no immediate work required." Verification against the actual repo finds that several claims are accurate, several are misleading or wrong, and one finding is significant enough to warrant correction:

**The 8 tests marked xfail are not "edge cases deferred." They are documented production bugs in the `/api/cam/sim/metrics` endpoint — one of three production endpoints the doc lists as a feature.**

A more honest characterization is "working core infrastructure with known unfixed bugs and architectural debt." That status is normal for working software but is materially different from what the document states.

---

## Findings by Severity

### Critical — Production bug reframed as edge case

**Doc claim:** "67 passed, 8 xfailed. The 8 xfailed are expected failures (edge cases deferred)."

**Repo evidence:** `services/api/tests/test_simulation_endpoint_smoke.py` lines 26-30:

```python
metrics_production_bug = pytest.mark.xfail(
    reason="Production bug: router/schema mismatch in metrics endpoint",
    raises=(AttributeError, TypeError, PydanticValidationError, Exception),
    strict=False
)
```

This decorator is applied to 8 test functions at lines 65, 294, 301, 308, 316, 327, 335, 345. Every xfail in the file points to the same documented production bug.

**Why this matters:** The metrics endpoint is one of three endpoints the document lists as a feature. The fact that 8 tests are explicitly labeled as failing because of a router/schema mismatch is not "edge cases deferred" — it is a known broken endpoint protected behind an xfail marker so CI stays green. This is the same failure mode the data integrity work surfaced: documentation that reframes problems as features.

**Recommended action:** Either fix the metrics endpoint or remove it from the API surface. Letting an endpoint sit as xfail-protected indefinitely creates the kind of latent bug that hurts customer-facing reliability.

---

### High — "Views Using This System" claims are largely false

**Doc claim:** Lists four views as using the CAM simulation system:
- `ToolpathSimulatorView.vue`
- `CamWorkspaceView.vue`
- `DxfToGcodeWizard.vue`
- `BridgeLabView.vue`

**Repo evidence:** All four files exist in the repo, but none of them import or use `ToolpathPlayer` or `ToolpathCanvas`:

```
ToolpathSimulatorView.vue: ToolpathPlayer=0, ToolpathCanvas=0
CamWorkspaceView.vue:       ToolpathPlayer=0, ToolpathCanvas=0
DxfToGcodeWizard.vue:       ToolpathPlayer=0, ToolpathCanvas=0
BridgeLabView.vue:          ToolpathPlayer=0, ToolpathCanvas=0
```

`ToolpathSimulatorView.vue` is a stub with local state (`gcodeFile`, `gcodeText`, `viewMode`, `simulationSpeed`) and a docstring claiming to call `POST /api/cam/simulate/preview` and `POST /api/cam/simulate/analyze`. Neither endpoint exists in the codebase.

**Actual production usage of `ToolpathPlayer`:**
- `packages/client/src/views/DxfToGcodeView.vue` (one view, routed)
- `packages/client/src/components/cam/ToolpathCompare.vue` (one component, used internally)

**Why this matters:** The document claims four integrations; reality is one routed view and one component. This is the kind of confident-sounding catalog entry that doesn't survive verification — same shape as the unverified citation work in the data integrity audits.

**Recommended action:** Either wire the claimed views to the actual player, or remove the integration claim from the documentation. The current state is documentation pointing at scaffolding.

---

### High — Dead duplicate router survives in production tree

**Doc claim:** Single consolidated router at `simulation_consolidated_router.py`.

**Repo evidence:** Two files with this name exist:

| Location | LOC | Endpoints | Status |
|----------|-----|-----------|--------|
| `services/api/app/routers/simulation_consolidated_router.py` | 325 | `/gcode`, `/upload`, `/metrics`, `/simulate_gcode` (legacy) | LIVE — registered via manifest |
| `services/api/app/cam/routers/simulation/simulation_consolidated_router.py` | 142 | `/simulate_gcode`, `/upload` | DEAD — not wired |

The dead router in `app/cam/routers/simulation/` is referenced only in the docstring of the live router (which acknowledges the duplication). The cam aggregator that would include it has the import commented out:

```python
# services/api/app/cam/routers/aggregator.py
#     from .simulation import router as simulation_router
```

**Why this matters:** This is the api/ vs api_v1/ resolution problem flagged in the broader codebase scan, surviving in current code. If anyone (engineer, agent, future Claude) adds an endpoint to the wrong file, it silently fails to ship.

**Recommended action:** Delete the dead version with a commit that explains why, or commit to consolidating the cam-aggregator structure and remove the live one. Either direction resolves the ambiguity.

---

### Medium — LOC counts undercount the most complex components

**Doc claim (frontend table):**
| File | Doc LOC | Actual LOC | Discrepancy |
|------|---------|------------|-------------|
| `ToolpathPlayer.vue` | ~300 | 393 | +31% (acceptable) |
| `ToolpathCanvas.vue` | ~400 | 798 | +99% (2x off) |
| `ToolpathCanvas3D.vue` | ~350 | 997 | +185% (3x off) |
| `useToolpathPlayerStore.ts` | ~400 | 526 | +31% (acceptable) |
| `toolpath-player/*` (subcomponents) | "12 files" | 35 files | +191% (3x off) |

**Repo evidence:**

```
393 packages/client/src/components/cam/ToolpathPlayer.vue
798 packages/client/src/components/cam/ToolpathCanvas.vue
997 packages/client/src/components/cam/ToolpathCanvas3D.vue
526 packages/client/src/stores/useToolpathPlayerStore.ts
```

Subcomponent count via `ls packages/client/src/components/cam/toolpath-player/ | wc -l`: 35 files (mix of `.vue` components and `.ts` composables/utilities).

**Why this matters:** The most acoustically expensive components — the 2D and 3D canvas renderers — are 2-3x more complex than the doc suggests. ToolpathCanvas3D at 997 lines is substantial and warrants its own architectural scrutiny. 35 subcomponents in one feature folder may indicate organic growth rather than designed organization. The undercounting hides where the real complexity (and risk) lives.

**Recommended action:** Re-examine ToolpathCanvas3D.vue specifically to confirm whether 997 lines is necessary or whether it has accumulated complexity that could be decomposed. Audit the 35-file subcomponent folder to confirm each file earns its place.

---

### Medium — Test count claim is unverifiable

**Doc claim:** "67 passed, 8 xfailed. Coverage: 21.99%"

**Repo evidence:**
- No test report file found containing these numbers (searched `*.md`, `*.txt`, `*.json`)
- `pytest --collect-only` on the four primary CAM test files yields **79 tests collected**
- Running unit-level tests (`test_gcode_simulate.py`, `test_simulation_gate.py`, `test_cam_gcode_fixes.py`) yields **43 passing tests** in this audit environment
- `test_simulation_endpoint_smoke.py` requires full app context to execute and could not be run in this audit environment (28 collection errors, 8 xfail)

**Why this matters:** The specific "67 passed" number cannot be reproduced or located. It may be accurate from a prior run, but there is no artifact backing it up. Documents should cite test reports they can point to, not recall numbers from memory.

**Recommended action:** Either run the tests and capture the report at the time of writing, or remove the specific count and replace with "tests pass; see `services/api/tests/test_*.py`" or similar.

---

### Low — Phase claims (P1-P6) match source code

**Doc claim:** Six enhancement phases (P1-P6) covering memory management, caching, M-code HUD, collision detection, Three.js 3D, and multi-tool support.

**Repo evidence:** The phase markers appear in `ToolpathPlayer.vue`:

```
3:  * ToolpathPlayer — P1-P5 Full Integration
12: * P1: Memory management, progress indicator, G-code validation
13: * P2: Caching (sessionStorage), LOD (in canvas)
14: * P3: M-code HUD, tool viz (in canvas), time estimates
15: * P4: Collision detection, optimization suggestions, stock simulation
16: * P5: 3D Three.js visualization with orbit controls
57:  // P4 props
63:  // P5 props
```

Note: source declares "P1-P5", doc declares "P1-P6". P6 ("Multi-tool color coding") may have been added after the docstring was written, or may be aspirational.

**Specific feature verifications:**

| Phase | Feature | Verification |
|-------|---------|--------------|
| P1 | 75k/100k segment thresholds | `MAX_SEGMENTS = 100_000`, `WARNING_THRESHOLD = 75_000` confirmed at `useToolpathPlayerStore.ts:21-22` |
| P2 | FNV-1a sessionStorage caching | `function fnv1a(str: string)` confirmed at `useToolpathPlayerStore.ts:94`, sessionStorage usage at lines 257-275 |
| P5 | Three.js usage | 79 references to `three`/`THREE`/`OrbitControls` in `ToolpathCanvas3D.vue` |

**Why this matters:** Phase claims are largely accurate. Minor inconsistency between source ("P1-P5") and doc ("P1-P6") is worth resolving but not significant.

**Recommended action:** Either update the source docstring to include P6, or remove P6 from the doc if it was aspirational.

---

### Low — Backend simulator is genuinely solid

**Doc claim:** State machine simulator with modal state tracking, arc interpolation, multi-tool support.

**Repo evidence:**
- `services/api/app/util/gcode/simulator.py`: 375 lines, exists and is referenced by the live router
- `services/api/app/util/gcode/lexer.py`: 62 lines, tokenizer
- `services/api/app/util/gcode/geometry.py`: arc center/length calculations
- 28 test functions in `test_gcode_simulate.py` covering simulation behavior
- Tests pass when run

**Why this matters:** The core simulation logic is real working code with real test coverage. This is the strongest part of the system and the doc's claim about it holds up.

**Recommended action:** None. The simulator is production-quality.

---

## Summary of Doc Claims vs Reality

| Claim | Status | Notes |
|-------|--------|-------|
| 67 tests pass, 8 xfailed | Unverifiable / misleading | Cannot reproduce; xfails are production bugs not edge cases |
| Production-ready | Misleading | Has known unfixed bug in metrics endpoint |
| No immediate work required | False | Metrics bug needs attention; dead router needs cleanup |
| State machine simulator | True | Real working code with test coverage |
| Three.js 3D rendering | True | 79 THREE references confirmed |
| Memory management thresholds | True | 75k/100k constants confirmed |
| FNV-1a sessionStorage caching | True | Implementation confirmed |
| 4 production views integrated | False | Only 1 view + 1 component actually use the player |
| 12 subcomponents | False | 35 files in subcomponent folder |
| Single consolidated router | False | Dead duplicate exists in cam/routers/simulation/ |
| LOC ~300/400/350/400 | Mixed | Two main canvas files are 2-3x larger than claimed |
| P1-P6 phases | Mostly true | Source says P1-P5; P6 may be aspirational or added later |

---

## What "Production-Ready" Actually Means Here

A more honest characterization:

The CAM simulation system has real working infrastructure for G-code parsing, state machine simulation, and 2D/3D visualization. The simulator's unit tests pass when runnable. Two of three production endpoints (`/sim/gcode`, `/sim/upload`) function correctly. The third endpoint (`/sim/metrics`) has a documented production bug that has been worked around with xfail markers rather than fixed. One production view actually uses the player; the others claimed in the doc are scaffolding. There are 35 subcomponents organizing 3,293 lines of frontend code that may or may not be cleanly architected. A duplicate dead-code router exists alongside the live one.

That is a system in working condition with known unfixed bugs and architectural debt — which is normal for working software, but is materially different from "production-ready with no immediate work required."

---

## Recommended Next Actions (Priority Order)

1. **Fix or remove the `/api/cam/sim/metrics` endpoint.** The xfail-protected production bug is the single most concrete issue surfaced by this audit. Options:
   - Fix the router/schema mismatch and remove the xfail markers
   - Remove the endpoint from the API surface and from documentation
   - Document the bug explicitly with a tracked issue and timeline

2. **Resolve the duplicate router.** Delete `services/api/app/cam/routers/simulation/simulation_consolidated_router.py` with a commit explaining the consolidation, or wire the cam-aggregator structure and remove the version under `app/routers/`. Pick a direction.

3. **Correct the "Views Using This System" claim.** Either wire the four claimed views to the actual `ToolpathPlayer`, or update the documentation to reflect that only `DxfToGcodeView.vue` and `ToolpathCompare.vue` actually integrate the player.

4. **Re-examine `ToolpathCanvas3D.vue`** (997 lines) and the 35-file subcomponent folder. Determine whether the complexity is necessary or whether decomposition would improve maintainability.

5. **Update LOC counts and phase numbering in the documentation** to match the source code. Minor but worth doing.

6. **Run the test suite at the time of any future "production-ready" claim** and capture the report alongside the claim. Specific numbers cited without an artifact undermine trust in the rest of the document.

---

## Methodological Note

This audit verified file existence, line counts, import relationships, route registrations, and test markers via direct repo inspection. It did not verify behavioral correctness of the simulator's output, the 2D/3D rendering quality, or end-to-end functionality from the browser. A behavioral audit would require running the application and exercising the simulation endpoints with representative G-code, which is out of scope here.

The audit is read-only. No code changes were made.

---

## Appendix — Verification Commands

For reproducibility, the key verification commands used:

```bash
# Confirm router files
find services/api/app -name "simulation*router*.py"

# Confirm wiring
grep -rn "include_router.*simulat\|prefix.*simulat" services/api/app

# Verify views don't use ToolpathPlayer
for v in ToolpathSimulatorView CamWorkspaceView DxfToGcodeWizard BridgeLabView; do
  grep -c "ToolpathPlayer\|ToolpathCanvas" packages/client/**/*"$v".vue
done

# Verify the xfail reason
grep -B 1 -A 8 "metrics_production_bug = pytest" services/api/tests/test_simulation_endpoint_smoke.py

# LOC counts
wc -l packages/client/src/components/cam/ToolpathPlayer.vue \
      packages/client/src/components/cam/ToolpathCanvas.vue \
      packages/client/src/components/cam/ToolpathCanvas3D.vue \
      packages/client/src/stores/useToolpathPlayerStore.ts

# Subcomponent count
ls packages/client/src/components/cam/toolpath-player/ | wc -l

# Test collection (bypassing coverage addopts)
python3 -m pytest tests/test_gcode_simulate.py tests/test_simulation_gate.py \
  tests/test_cam_gcode_fixes.py --collect-only -o addopts=""
```
