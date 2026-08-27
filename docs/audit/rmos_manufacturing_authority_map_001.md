# RMOS-AUTHORITY-MAP-001 — Stage 2 Authority Classification

**Status:** STAGE 2 COMPLETE — capability-level classification populated. **No remediation authorized.**  
**Date:** 2026-08-27  
**Base:** `origin/main` at execution (`93df82f3`, after #327).  
**PR:** continues draft #328 (same increment; not a second agent PR).

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
| rosette | **GOVERNED** | MOUNTED | `compute_rosette_feasibility` | authority before gen | NO | Real scorer (not fail-open). After a non-blocking decision, plan currently 400 `TOOLPATH_PLAN_ERROR` (`RosetteGeometry` kwargs). No G-code leaked. Not remediated. MAR-020. |
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

40 passed: MAR-001–024 (Stage 1 integrity/discovery plus Stage 2 semantics).
`--no-cov` because `pytest.ini` has `--cov-fail-under=20` for unrelated modules.

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
