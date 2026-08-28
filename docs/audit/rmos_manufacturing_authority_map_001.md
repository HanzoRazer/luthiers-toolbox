# RMOS-AUTHORITY-MAP-001 — Stage 2 Authority Classification

**Status:** STAGE 2 COMPLETE — frozen before-state. **No remediation authorized.**  
**Date:** 2026-08-27  
**Base:** `origin/main` at execution (`93df82f3`, after #327).  
**PR:** continues draft #328 (same increment; not a second agent PR).

**Later after-state (do not erase the frozen before-state):**  
RMOS-PROFILING-CONVERGE-001 (2026-08-27) changed **Profiling only** from
`LIVE_UNGOVERNED_OUTPUT` to `GOVERNED`. Historical Stage-2 classifications
in this document remain the before-state. See §7.

RMOS-VCARVE-CONVERGE-001 (2026-08-27) recorded **V-carve HOLD**
(`POST_MERGE_AUTHORITY_EXPOSURE` unchanged). See §8.

RMOS-DRILLING-CONTRACT-001 (2026-08-28) added a truthful drilling
manufacturing contract. Drilling remains `AUTHORITY_CONTRACT_MISMATCH`.
No production gate. See §9.

This is not an agent report. Grounding Agent v0.1 remains the only agent under
trial (`GA-TRIAL-0002`, MATCH / PROCEED). One script, one inert registry, one
report, one PR.

**Presence in the registry grants no execution authority.** Nothing
production-facing imports this file.

This registry does **not** replace:

| Adjacent map | Concern |
| --- | --- |
| `docs/governance/CANONICAL_AUTHORITY_MAP.md` | semantic ownership |
| `services/api/app/cam/geometry_authority_registry.py` | 7T geometry references; no machine-output authority |
| `services/api/app/cam/ontology_authority_map.py` | 7M vocabulary; `execution_authorized = false` |

Owner ruling (2026-08-27): *Stage 1 taxonomy accepted with the semantic
boundary below. Proceed to Stage 2 deep classification, but do not merge
remediation into the same tranche.*

---

## 0. Stage 1 inventory (unchanged counts)

Stage 1 answered “is the capability model itself correct?” Those numbers still
hold. Naive `app.routes` under-counts; the walk recurses `_IncludedRouter`.

| Measure | Count |
| --- | ---: |
| Top-level `app.routes` objects | 155 |
| Walked HTTP operations (incl. duplicate mounts) | 1155 |
| Unique mounted operations | 1140 |
| Unique mounted paths | 1081 |
| OpenAPI paths | 1077 |
| Machine-output candidates | 67 |
| Hint matches excluded by declared purpose | 7 |
| Capabilities | 26 |
| Unexplained emitters | 0 |

Validation: `PYTHONPATH=services/api python3 scripts/audit/rmos_authority_map.py --validate` → OK.

These counts are **environment-dependent and must be read with the stamp
below.** `top_level_route_objects` in particular reflects how the installed
FastAPI stores included routers: 0.137 wraps them as `_IncludedRouter` (155
top-level objects), while an older FastAPI flattens them (~1147). A re-run on a
machine that does not match `services/api/requirements.txt` will not reproduce
this table and should not be treated as contradicting it.

| Stamp | Value |
| --- | --- |
| FastAPI | `>=0.137.0,<0.138.0` (per `services/api/requirements.txt`) |
| Re-run drift observed 2026-08-27 | OpenAPI paths 1077 → 1072, unique mounted paths 1081 → 1076 |

The drift is `main` moving under a frozen snapshot, which is expected and does
not invalidate the classifications: the reconciliation test pins only the 26
registered capabilities' routes, not global counts.

---

## 0a. The mount itself is fail-open (finding added 2026-08-27)

Stage 1 recorded `mount_state: MOUNTED` as a fact. It is not a fact; it is a
**contingent outcome**. `app/cam/routers/aggregator.py` mounts every CAM family
through the same guard:

```python
try:
    from .toolpath import router as toolpath_router
except ImportError:
    toolpath_router = None
...
if toolpath_router:
    cam_router.include_router(toolpath_router, prefix="/toolpath", ...)
```

There are **16 such guards**. A single failed transitive import silently removes
an entire manufacturing-output family — no exception, no log, no gate. This was
not theorised: on 2026-08-27 a missing `defusedxml` (a *declared* requirement,
absent from one developer machine) removed `/api/cam/toolpath/*` in full, taking
four registered routes with it.

**Registry exposure: 9 of 26 capabilities, 16 routes.**

| Capability | Disposition | Routes behind a fail-open guard |
| --- | --- | ---: |
| `pocketing` | GOVERNED | 1 |
| `rosette` | GOVERNED | 2 |
| `vcarve` | POST_MERGE_AUTHORITY_EXPOSURE | 3 |
| `drilling` | AUTHORITY_CONTRACT_MISMATCH | 3 |
| `binding` | LIVE_UNGOVERNED_OUTPUT | 2 |
| `profiling` | LIVE_UNGOVERNED_OUTPUT | 2 |
| `biarc-contour` | BLOCKED_BY_DESIGN | 1 |
| `helical` | BLOCKED_BY_DESIGN | 1 |
| `roughing` | BLOCKED_BY_DESIGN | 1 |

Why it matters to *this* audit specifically, in both directions:

- **Availability.** A capability classified `GOVERNED` can vanish without anyone
  being told. Governance that disappears silently is not governance.
- **Classification integrity.** Three capabilities are classified
  `BLOCKED_BY_DESIGN`. Had that evidence been a 404, it would have been
  indistinguishable from "the router never mounted" — an import failure recorded
  as a design decision. It is not: §4's witnesses assert **409**, which only a
  mounted, governed route can return. The methodology holds, and it holds
  *because* it insisted on a governed status code rather than mere absence.

This is recorded as a finding, not remediated. Removing the guards is an
availability change requiring an owner ruling: today a broken optional
dependency degrades the API, whereas failing closed would refuse to boot.

**Diagnosability, fixed here.** The reconciliation previously reported an
unmounted family as N unrelated `MAR-004 ... does not resolve` lines, which
reads as registry rot rather than a missing router. `MAR-027` now detects that
nothing at all is mounted under the shared prefix and says so once, naming the
import guard as the mechanism.


---

## 1. Taxonomy amendment applied (`surface_kind`)

The registry now distinguishes **manufacturing capability authority** from
artifact layers so postprocessors, wrappers, and retrieval endpoints cannot
inflate the manufacturing count.

| `surface_kind` | Meaning |
| --- | --- |
| `manufacturing_capability` | Generates a machine/operator-consumable artifact under some (or no) manufacturing authority |
| `artifact_transformation` | Transforms an already-produced artifact (post-wrap of supplied G-code, bundles) |
| `artifact_retrieval` | Returns or packages a stored artifact; not a manufacturing generator |
| `advisory` | Parameters/advice that can influence execution without emitting a machine file |

Owner rulings applied:

| Question | Ruling | What we did |
| --- | --- | --- |
| Post vs wrap | Keep separate unless same upstream authority and serialization-only | `cam-post`, `rmos-wrap`, `v1-dxf` remain three capabilities. Rosette plan+post stay one family (shared evaluator). |
| Guitar vs binding | Binding separate | Acoustic `{style}/binding/gcode` moved from `cam-guitar` into `binding` (3 routes). Guitar body/soundhole/electric remain `cam-guitar` (6). |
| Neck surfaces | Split only for a distinct operation/authority contract | Kept `neck-gcode`, `cam-guitar` neck, and `headstock-transition` as three contracts (parametric OP10–40 vs project stub vs blend surfacing). |
| Operator-pack vs retrieval | Retrieval is not manufacturing; pack is a capability only if it constructs a new bundle | `operator-pack` is `artifact_retrieval`. ZIP of existing attachments; not GOVERNED. |
| Feeds-speeds | Keep; advisory unless proven machine-parameter authority | `advisory` / `ADVISORY_ONLY`. JSON 200, no G-code. |
| Saw-batch GETs | Include iff machine-consumable artifacts, not status | Included as `artifact_retrieval`. Three GETs serialize stored moves to G-code. HTTP method ignored. |

Also recorded, not guessed: 15 duplicate mounts remain de-duplicated; adaptive `/plan` is still not a machine-output candidate.

---

## 2. Stage 2 rule

Do not let the registry vocabulary outrun the evidence. A capability is
promoted only after naming evaluator (or none), runtime reachability,
generation ordering, persistence truth, and client/retrieval path.

`UNKNOWN` / `INSUFFICIENT_EVIDENCE` remain valid where a safe witness was
withheld (Stop #5) or inputs would have to be fabricated (Stop #6).

Reading rule (applies to every capability):

```text
GOVERNED
≠
FUNCTIONAL
≠
AVAILABLE
```

`authority_disposition` answers whether manufacturing authority is valid and
consulted. `reachability` answers whether the production path currently emits.
Rosette is the scrutinized case: **GOVERNED** and **RUNTIME_BROKEN**.

---

## 3. Capability classifications

Engine table (`_PRODUCTION_FEASIBILITY_ENGINES`): **saw, rosette, adaptive
only**. Missing engine → `unavailable_feasibility` UNKNOWN →
`SafetyPolicy.should_block`. The historical CAM stub GREEN path is retired.

### Manufacturing capabilities

| ID | Disposition | Reachability | Evaluator | Ordering | Ungated output | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| retract | **BLOCKED_BY_DESIGN** | RUNTIME_BLOCKED_BY_POLICY | none | authority before gen | NO | All 4 routes 409; no G-code. MAR-014. |
| adaptive | **GOVERNED** | RUNTIME_REACHABLE | `compute_adaptive_feasibility` | authority before gen | NO | 200 sane / 409 F004. Persistence matches evaluator. MAR-015. |
| drilling | **AUTHORITY_CONTRACT_MISMATCH** | RUNTIME_REACHABLE | intent-lane only | MIXED | YES | Modal `DrillReq` cannot feed `compute_drilling_feasibility` (`hole_diameter_mm` absent). Modal 200 G81/G83. Do not invent a mapping. MAR-011/016. |
| profiling | **LIVE_UNGOVERNED_OUTPUT** | RUNTIME_REACHABLE | intent-lane only | MIXED | YES | Post-#324 `/gcode` 200 G-code, no RMOS. 422 empty body is not the classifier (MAR-012). Not `POST_MERGE_*` (that name is D9/V-carve). MAR-017. |
| vcarve | **POST_MERGE_AUTHORITY_EXPOSURE** | RUNTIME_REACHABLE | none on production | MIXED | YES | `/production/gcode` 200 without RMOS. Intent 409. MAR-018. |
| roughing | **BLOCKED_BY_DESIGN** | RUNTIME_BLOCKED_BY_POLICY | none | authority before gen | NO | Mode `roughing` has no engine → 409. MAR-019. |
| helical | **BLOCKED_BY_DESIGN** | RUNTIME_BLOCKED_BY_POLICY | none | authority before gen | NO | `helical:gcode` → no engine → 409. MAR-019. |
| biarc-contour | **BLOCKED_BY_DESIGN** | RUNTIME_BLOCKED_BY_POLICY | none | authority before gen | NO | `tool_id='biarc_gcode'` → mode `unknown`. 409. |
| rosette | **GOVERNED** | RUNTIME_BROKEN | `compute_rosette_feasibility` | authority before gen | NO | Real scorer (not fail-open). After a non-blocking decision, plan currently 400 `TOOLPATH_PLAN_ERROR` (`RosetteGeometry` kwargs). No G-code leaked. GOVERNED ≠ functional/available. Not remediated. MAR-020. |
| probing | **LIVE_UNGOVERNED_OUTPUT** | MOUNTED | none | without authority | YES | Draft ungated; governed downloads mint GREEN. Runtime POST withheld (setup probing). |
| binding | **LIVE_UNGOVERNED_OUTPUT** | RUNTIME_REACHABLE | none | without authority | YES | Channel 200 G-code. Includes acoustic binding. |
| inlay | **LIVE_UNGOVERNED_OUTPUT** | MOUNTED | none | without authority | YES | Static; runtime payload not fabricated. |
| radius-dish | **LIVE_UNGOVERNED_OUTPUT** | MOUNTED | none | without authority | YES | Static; client uses public `.nc`, not this API. |
| pocketing | **GOVERNED** | MOUNTED | intent-lane `compute_pocket_feasibility` | authority before gen | NO | Static only; runtime CamIntentV1 not reproduced. Confidence MEDIUM. |
| polygon-offset | **GOVERNED_PROVENANCE_DEFECT** | RUNTIME_REACHABLE | none | without authority | YES | Governed lane 200 NC + `RunDecision(GREEN)` without evaluator. MAR-009. |
| cam-guitar | **LIVE_UNGOVERNED_OUTPUT** | MOUNTED | none | without authority | YES | Auth/project; runtime withheld. Binding removed. |
| cam-post | **LIVE_UNGOVERNED_OUTPUT** | MOUNTED | none | without authority | YES | Independent contour→G-code authority. Runtime payload withheld. |
| rmos-wrap | **GOVERNED_PROVENANCE_DEFECT** | MOUNTED | none | without authority | YES | Hardcoded GREEN. File-upload POST withheld. MAR-009/010. |
| v1-dxf | **EXPLICITLY_NON_PRODUCTION** | MOUNTED | none | without authority | NO | Placeholder `; TODO: Full toolpath…`. |
| vision | **LIVE_UNGOVERNED_OUTPUT** | MOUNTED | none | without authority | YES | Photo pipeline withheld (external/AI). |
| neck-gcode | **LIVE_UNGOVERNED_OUTPUT** | MOUNTED | none | without authority | YES | Distinct from guitar neck / headstock. |
| headstock-transition | **LIVE_UNGOVERNED_OUTPUT** | MOUNTED | none | without authority | YES | Distinct blend-surface operation. |

### Non-manufacturing surfaces

| ID | `surface_kind` | Disposition | Notes |
| --- | --- | --- | --- |
| feeds-speeds | advisory | **ADVISORY_ONLY** | 200 JSON `feed_xy`/`rpm`; not G-code. |
| geometry | artifact_transformation | **LIVE_UNGOVERNED_OUTPUT** | Wraps supplied G-code. Not a manufacturing generator. |
| operator-pack | artifact_retrieval | **INSUFFICIENT_EVIDENCE** | Not GOVERNED. Retrieval of stored blobs; stored-risk gate. Missing run → 404. |
| saw-batch | artifact_retrieval | **LIVE_UNGOVERNED_OUTPUT** | GET serializes stored moves to G-code. Quarantine. Missing id → 404. |

---

## 4. Runtime witnesses (Stage 2)

Ephemeral `RMOS_RUNS_DIR` / `RMOS_ARTIFACT_ROOT` / `ART_STUDIO_DB_PATH`. No
machine-control, no production DB, no operator-file export.

| Attempted | Result |
| --- | --- |
| Retract POST `/gcode` and `/gcode/download` | 409, no G-code |
| Adaptive `/gcode` sane / F004 | 200 + hashes / 409 |
| Drill modal `/gcode` | 200 G81/G83 |
| Profiling `/gcode` empty / contour | 422 / 200 G21 |
| V-carve `/production/gcode` / intent | 200 / 409 |
| Roughing, helical, biarc | 409, no G-code |
| Rosette `plan-toolpath` | 400 TOOLPATH_PLAN_ERROR after evaluator; no G-code |
| Binding channel | 200 G21 |
| Feeds-speeds | 200 JSON |
| Polygon-offset governed | 200 NC, `X-ToolBox-Lane: governed` |
| Operator-pack / saw-batch GET missing id | 404 |

**Withheld (NOT_OBTAINED_SAFELY):** guitar (auth/project), wrap DXF upload,
vision photo/AI, probe G38 programs, inlay/radius-dish/neck/headstock/cam-post
payloads that would require fabricated manufacturing inputs, planting a
saw-batch artifact to download G-code.

---

## 5. Tests

`services/api/tests/rmos/test_manufacturing_authority_registry.py`  
`services/api/tests/rmos/test_manufacturing_authority_discovery.py`  
`services/api/tests/rmos/test_manufacturing_authority_stage2.py`

51 passed: MAR-001–027 (Stage 1 integrity/discovery plus Stage 2 semantics).
`--no-cov` because `pytest.ini` has `--cov-fail-under=20` for unrelated modules.

Added 2026-08-27: `MAR-026` (a blind OpenAPI cross-check must not read as
agreement), `MAR-027` (an unmounted family is reported once, naming the import
guard), a MAR-004 regression proving a single stale route is still reported
individually, and an inertness witness asserting that **no** module under
`services/api/app/` references the registry, the map script, or the Stage 2
overlay. The registry's entire warranty is that it is a record and not a policy
source; nothing previously enforced that.

### These tests were not run by any gate

`services/api/tests/` is **not collected by CI**. The "API Tests" workflow runs
`cd services/api && python -m pytest -q app/tests/` — a different tree. The gap
is repo-scale, not specific to this audit:

| Tree | Test files | Collected by CI |
| --- | ---: | --- |
| `services/api/app/tests/` | 34 | yes |
| `services/api/tests/` | 447 (~8,384 test functions) | **no** |

So every witness in this PR was green locally and unenforced remotely, and
`rmos-ci` passing said nothing about any of it. A **bounded** fix is applied
here: `rmos_ci.yml` now runs these three files explicitly, and unlike the
adjacent steps it is not wrapped in `if [ -f ... ]` — a missing witness fails
the gate rather than skipping quietly.

The wider gap is left open deliberately. Collecting 447 files at once is an
unbounded availability change and belongs to its own order, not to a frozen
audit snapshot.

`--emit-skeleton` still prints Stage-1 UNKNOWN. `--emit-stage2` prints the
overlay to stdout and does not write the registry.

---

## 6. What this still does not authorize

- No CAM, RMOS, feasibility, route, client, persistence, or G-code change.
- No new agent, workflow, or standing mapper service.
- **No cutover.** Discovery does not authorize remediation.
- Rosette `RosetteGeometry` constructor mismatch is recorded, not patched.
- V-carve production exposure is recorded, not gated.
- Drill modal mismatch is preserved, not adapted.

The next manufacturing cutover, if any, should be authorized
**capability-by-capability** against this registry’s *before* state.

Do not launch a generic RMOS remediation tranche from this PR. After #328
merges as the frozen before-state, the owner selects exactly one capability
and writes one bounded Dev Order. Evidence ranking (not a work order):

1. Profiling — reachable ungated G-code; strongest pure authority defect.
2. V-carve production — equally serious exposure; post-#324 history; own ruling.
3. Drilling — contract mismatch; architecture/design before gating.
4. Polygon-offset / rmos-wrap — provenance repair, not immediate emission blocking.
5. Rosette — downstream constructor defect, not authority remediation.

```text
RMOS-AUTHORITY-MAP-001
        ↓
FROZEN BEFORE-STATE
        ↓
OWNER SELECTS ONE CAPABILITY
        ↓
BOUNDED DEV ORDER
        ↓
IMPLEMENT
        ↓
VERIFY AGAINST REGISTRY
        ↓
UPDATE BEFORE → AFTER EVIDENCE
```

---

## 7. After-state — RMOS-PROFILING-CONVERGE-001 (2026-08-27)

This section is an increment on the frozen Stage-2 map. It does **not**
rewrite the historical classification. PR #328 remains the before-state.

```text
Capability: profiling

BEFORE (PR #328 / merge 9d5d9001):
  authority_disposition = LIVE_UNGOVERNED_OUTPUT
  reachability          = RUNTIME_REACHABLE
  POST /api/cam/profiling/gcode → 200 G-code
  RMOS authority boundary absent from the sibling /gcode route

AFTER (RMOS-PROFILING-CONVERGE-001):
  authority_disposition = GOVERNED
  reachability          = RUNTIME_REACHABLE
  POST /api/cam/profiling/gcode → evaluate → SafetyPolicy → ALLOW? generate
  GOVERNED ≠ FUNCTIONAL ≠ AVAILABLE
```

Grounding Agent v0.1: **GA-TRIAL-0003**, `MATCH / PROCEED`. No Grounding
Agent code was changed.

### What changed

Production `POST /api/cam/profiling/gcode` now:

1. maps `ProfileRequest` → the same `ProfileConfig` `ProfileToolpath` runs;
2. builds evaluator inputs from that config (no fabricated defaults;
   finishing fields are the `ProfileConfig` runtime values
   `ProfileToolpath.generate()` actually uses);
3. calls the **existing** `compute_profile_feasibility` through
   `compute_feasibility_internal` / `compute_profiling_feasibility`
   (adapter only — not a second evaluator);
4. passes the result through `SafetyPolicy`;
5. generates G-code only after allow;
6. persists via `validate_and_persist` with the authority decision and
   feasibility identity (not a request hash).

Evaluator vocabulary mapping (not new physics):

| `compute_profile_feasibility` | RMOS `SafetyPolicy` |
| --- | --- |
| not feasible / issues | RED (block) |
| feasible + `low` | GREEN |
| feasible + `medium` or `high` (warnings) | YELLOW (allowed; not rewritten GREEN) |
| missing required inputs | UNKNOWN (block) |
| engine exception | ERROR (block) |

`SafetyPolicy` must not be handed the scorer's `low`/`medium` strings —
those would become UNKNOWN and block valid jobs.

### Witnesses

| Input | After |
| --- | --- |
| Valid default contour | 200 G-code, `X-Risk-Level: GREEN`, `X-Run-ID` |
| Tiny tool + aggressive feed (warnings) | 200 G-code, `X-Risk-Level: YELLOW` |
| `tab_height_mm >= cut_depth_mm` | 409 `SAFETY_BLOCKED`, no G-code, no output hash |
| Empty body | 422 (PR #324 binding preserved) |
| Client-supplied `risk_level` / `decision` | ignored; RED fixture still 409 |
| `POST /api/cam/profiling/preview` | unchanged |

No in-repo production consumer of `/api/cam/profiling/gcode` was found
(`packages/client` calls `/intent-gcode` only). Client code was not
changed.

### What did not change

V-carve, drilling, retract, adaptive, polygon-offset, rmos-wrap, Rosette,
profiling `/preview`, `TabGenerator(contour=...)`, profiling physics, and
the Grounding Agent. Adaptive remains `GOVERNED`. Retract remains
`BLOCKED_BY_DESIGN`. Rosette remains `GOVERNED` + `RUNTIME_BROKEN`.

The `_PRODUCTION_FEASIBILITY_ENGINES` table now includes `profiling`. That
is the sanctioned way to reopen a lane (existing evaluator, registered
mode). It is not a new feasibility physics module.

---

## 8. HOLD — RMOS-VCARVE-CONVERGE-001 (2026-08-27)

This section is an increment on the frozen Stage-2 map. It does **not**
rewrite the historical classification. PR #328 remains the before-state.

```text
Capability: vcarve (production POST /api/cam/vcarve/production/gcode)

BEFORE (PR #328 / merge 9d5d9001):
  authority_disposition = POST_MERGE_AUTHORITY_EXPOSURE
  reachability          = RUNTIME_REACHABLE
  POST /api/cam/vcarve/production/gcode → 200 G-code
  no RMOS authority on the production route
  history: #322 looked live → #324 proved runtime-dead (annotation)
           → #324 restored binding → #328 classified the exposure

HOLD (RMOS-VCARVE-CONVERGE-001):
  AUTHORITY CONTRACT = NOT SATISFIABLE
  no substantive V-carve evaluator
  production behavior unchanged (still 200 ungated G-code)
  do not pretend GOVERNED
```

Grounding Agent v0.1: **GA-TRIAL-0004**, `MATCH / PROCEED`. No Grounding
Agent code was changed.

### Mandatory checkpoint

| Evaluator input | Source | Unit | Semantically identical? |
| --- | --- | --- | --- |
| *(none — no V-carve evaluator exists)* | — | — | — |

```text
AUTHORITY CONTRACT = NOT SATISFIABLE
```

Finding class: **(3) no evaluator exists.** Not (1) a V-carve-capable
scorer, and not (2) a merely adjacent scorer that this order could
reuse. D1 forbids treating profiling, drilling, pocketing, adaptive, or
`FeasibilityInput.tool_d` (flat end mill) as a V-carve authority.

Evidence:

- `_PRODUCTION_FEASIBILITY_ENGINES` = `{saw, rosette, adaptive, profiling}`.
  `resolve_feasibility_engine("vcarve")` is `None`.
- `services/api/app/cam/vcarve/` has toolpath/geometry/chipload/intent
  adapters. There is no `feasibility.py` and no `compute_vcarve_*`.
- CAM feasibility modules that do exist (`profiling`, `drilling`,
  `pocketing`) and the RMOS rule engine (`FeasibilityInput.tool_d`,
  F001/F025) model a straight-diameter cutter. A V-bit is an included
  **angle**, not an endmill diameter (`docs/audit/rmos_prod_audit_001.md`
  already recorded this for the intent lane).
- This order does not create a new evaluator and does not invent physics.

### Why not gate anyway

D3: wiring `unavailable_feasibility` / SafetyPolicy onto production would
turn today's valid 200 G-code into 409 UNKNOWN. That is an availability
change, not an authority correction, and it needs an owner ruling.

Blast radius if gated without an evaluator:

- every syntactically valid `POST /api/cam/vcarve/production/gcode` that
  currently returns 200 machine G-code would 409;
- in-repo client consumers of that production path: **none**
  (`NO_IN_REPO_CONSUMER`); `VCarveView` uses `/api/cam/toolpath/vcarve/gcode`,
  which already 409s;
- intent/toolpath V-carve routes are already fail-closed (not the
  exposure, not changed here).

### What changed in this increment

Tests, audit, registry HOLD evidence, Stage-2 overlay lockstep, and the
RMOS CI collection of the new witness file. The production router, engine
table, Profiling, drilling, retract, adaptive, and client are untouched.

Registry after-state (not a promotion):

```text
authority_disposition = POST_MERGE_AUTHORITY_EXPOSURE   # unchanged
reachability          = RUNTIME_REACHABLE               # unchanged
ungated_output_exposure = YES                           # unchanged
evaluator             = none                            # unchanged
HOLD evidence appended
```

Profiling remains `GOVERNED` / `RUNTIME_REACHABLE` (PR #329 / `c987bfce`).
Retract remains `BLOCKED_BY_DESIGN`. Adaptive remains `GOVERNED`.
Drilling remains `AUTHORITY_CONTRACT_MISMATCH`.

---

## 9. Contract — RMOS-DRILLING-CONTRACT-001 (2026-08-28)

This section is an increment on the frozen Stage-2 map. It does **not**
rewrite the historical classification. PR #328 remains the before-state.
V-carve HOLD in §8 is unchanged.

```text
Capability: drilling (modal POST /api/cam/drilling/gcode)

BEFORE (PR #328):
  authority_disposition = AUTHORITY_CONTRACT_MISMATCH
  reachability          = RUNTIME_REACHABLE
  ungated_output_exposure = YES
  input_contract_status = MISMATCH
  POST /api/cam/drilling/gcode → 200 G81/G83
  no RMOS authority on the modal route
  three HTTP contracts (modal / intent / pattern)

AFTER (RMOS-DRILLING-CONTRACT-001):
  authority_disposition = AUTHORITY_CONTRACT_MISMATCH   # unchanged
  reachability          = RUNTIME_REACHABLE             # unchanged
  ungated_output_exposure = YES                         # unchanged
  input_contract_status = MISMATCH                      # unchanged
  production G81/G83 still 200                          # no gate
  canonical DrillingOperationSpec exists
  canonical → evaluator = TRUTHFUL when spec is complete
  intent → canonical = COMPLETE
  modal → canonical = INCOMPLETE (optional diameter/datum/RPM)
  pattern → canonical = INCOMPLETE (same Z/R gap; resolver queued)
```

Grounding Agent v0.1: **GA-TRIAL-0005**, `MATCH / PROCEED`. No Grounding
Agent code was changed.

### Mandatory checkpoint

```text
DRILLING CONTRACT CHECKPOINT

canonical depth semantic: physical hole depth, mm, positive into material
canonical datum:        work-surface Z in the same absolute frame as target Z;
                        intent proves surface_z_mm = 0 (PeckDrill Z = -depth)
canonical diameter source: first-class hole_diameter_mm (never tool number)
tool identity semantic: Optional[int] tool number; distinct from diameter
feed semantic:          sequence of per-hole feeds; evaluator adapter requires
                        invariant feed (refuse heterogeneous collapse)
RPM semantic:           required for evaluator mapping; not fabricated on modal
peck semantic:          G81 → peck_drilling False; G83 → True; Q = peck_depth_mm
safe-Z semantic:        G0 Z rapid clearance before cycle
retract semantic:       canned-cycle R-plane (modal r_clear / intent retract_z_mm)
units normalization:    canonical always mm; explicit inch→mm * 25.4

modal → canonical:   INCOMPLETE
intent → canonical:  COMPLETE
pattern → canonical: INCOMPLETE
canonical → evaluator: TRUTHFUL
```

### Three-lane matrix

| Semantic | Modal | Intent | Pattern | Evaluator | Resolution |
| --- | --- | --- | --- | --- | --- |
| hole XY | `Hole.x`/`y` | `DrillPointV1.x`/`y` mm | generated from pattern | `hole_count` only | map XY; count=`len(holes)` |
| target Z | `Hole.z` (G90 G-code Z) | derived `−depth` | `DrillParams.z` | not an input | keep as `target_z_mm`; not depth |
| hole depth | missing | `hole_depth_mm` (design default) | missing | required | intent: design default; modal: only if `surface_z` + target Z |
| datum | missing | implied surface Z=0 | missing | implicit | explicit `surface_z_mm`; intent=0 |
| diameter | missing (optional additive) | `hole_diameter_mm` required | missing (optional additive) | required | first-class; never `tool` |
| tool identity | `tool` Optional[int] | — | `tool` Optional[int] | none | keep distinct |
| feed | per-hole `Hole.feed` | singular context (default 100) | singular `DrillParams.feed` | singular | list; adapter requires invariant |
| RPM | optional, post-only | context (default 2000) | optional | required | intent: post-adapter value; modal: omit if missing |
| cycle | G81/G83 | `peck_drilling` bool | G81/G83 | `peck_drilling` | G81=False, G83=True |
| peck depth | `peck_q` (G83 default 1.0) | `peck_depth_mm` required | `peck_q` | required if peck | Q as generated |
| safe Z | `safe_z` default 5 | context default 10 | `safe_z` default 5 | required | actual generator value |
| retract / R | `r_clear` or 5.0 → R word | `retract_z_mm` → R word | `r_clear` or 5.0 | `retract_z_mm` | R-plane, not surface |
| units | string default mm | CamIntentV1 mm | string default mm | mm | explicit normalize |

`r_clear → retract_z_mm` is proven as the canned-cycle **R-plane**, not as
stock-top. Depth is not `R − Z`.

### What became representable

- Physical depth distinct from target Z, with an explicit work-surface datum.
- Diameter as a first-class millimetre field, never a tool number.
- Per-hole feeds that cannot silently collapse to min/max/mean/first.
- G81/G83 as non-peck / peck, with generator-true Q and R defaults.
- Units as an explicit mm canonical with inch×25.4 normalization.
- Intent lane already supplies every evaluator kwarg without fabrication.

### What did not change

No RMOS production gate. Modal `/gcode` still returns 200 G81/G83. No
200→409. Scoring rules in `compute_drilling_feasibility()` are unchanged.
Drilling is **not** GOVERNED. Pattern `tool_id='drill_pattern_gcode'`
resolver defect remains queued. Profiling remains GOVERNED. V-carve remains
HOLD / `POST_MERGE_AUTHORITY_EXPOSURE`. Retract remains `BLOCKED_BY_DESIGN`.
Adaptive remains GOVERNED. Client cleanup is out of scope.

Optional additive `DrillReq` fields (`hole_diameter_mm`, `surface_z_mm`)
are backward-compatible. They are ignored by G-code generation. Existing
`useDrillingOperation.ts` callers keep working. Pattern `DrillParams` is
unchanged in this increment (pre-existing `RunArtifact()` fence sites).

A later, separately authorized `RMOS-DRILLING-CONVERGE-001` may decide
whether this truthful contract is ready to control machine-output authority.

