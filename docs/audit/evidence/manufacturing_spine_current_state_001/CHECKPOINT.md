# G2-MANUFACTURING-SPINE-001 — WORK-IN-PROGRESS CHECKPOINT

**Status:** WIP checkpoint, not a deliverable. **No PR. Not reviewed. Do not merge.**
Committed so the work survives a stale session and a reapable worktree.
**Written:** 2026-09-13 · **Base:** `origin/main` @ `0679dbf62d5829207f56618b3fbdbbee433493a0`
**Branch:** `g2-manufacturing-spine-001` · **Worktree:** `C:/tmp/ltb-sprints`

This file is scaffolding. Before the PR it is replaced by
`docs/audit/manufacturing_spine_current_state_001.md` + `.json`; delete it then.

---

## 1. The order, compressed

Evidence / adjudication increment. **Production remediation NOT AUTHORIZED** —
a serious defect is recorded, classified, frozen, and left alone (D6).

Ladder `DECLARED → WIRED → EXERCISED → EFFECTIVE → CONSUMED`, never promoted by
inference. Values `YES / NO / UNKNOWN / NOT_OBTAINED_SAFELY`; absence of
evidence is UNKNOWN, never NO. Identity string exactly
`G2-MANUFACTURING-SPINE-001` everywhere — an earlier `MANUFACTURING-SPINE-001`
(#353, profiling witness) exists, so never shorten it.

Owner rulings (2026-09-10):

| Id | Ruling |
| --- | --- |
| D5a | Repo fixtures + minimal synthetic geometry allowed for EXERCISED/EFFECTIVE, labelled `SYNTHETIC_PROBE`. Never proves CONSUMED. No planted operator artifacts, fake projects, real-machine contexts. |
| D5b | CONSUMED = mounted/reachable client entry → production invocation → implementation → result used/rendered/persisted/downloaded. Static chain suffices; browser witness optional. |
| D7 | `!/tools/manufacturing_spine/` allowlisted — **done** (see §3). |
| D8 | One named `core_ci.yml` step: `Manufacturing Spine Registry Tests (G2-MANUFACTURING-SPINE-001)` → `python -m pytest tests/manufacturing_spine/test_validate_current_state.py -v`. No new workflow. **Not done.** |
| D9 | Evidence lives here, small and selected, no raw log dumps. Lab stays closed. |
| D10 | `docs/agents-md-scaffold` is out of scope. Do not delete or modify it. |
| Env | Stamp mandatory. Source-present / runtime-absent → UNKNOWN, never REMOVED. Capability IDs = `services/api/app/rmos/manufacturing_authority_registry.json`. |

Deliverable: ONE PR "Manufacturing Spine current-state baseline", then STOP for
the owner to choose the next capability. Merge needs its own GO.

---

## 2. Phase status

| Phase | State | Evidence |
| --- | --- | --- |
| 0 Grounding | **DONE** — MATCH / PROCEED, 8/8 claims | `phase0_grounding/` |
| 1 Historical reconciliation | **DONE** | §4 |
| 2 Current census | **DONE** | `phase2_census/census_inventory.json` |
| 3 Maturity: DECLARED + WIRED | **DONE** — 26/26 each | `phase3_wired/` |
| 4 Runtime witnesses | **IN FLIGHT** — v2 run is STALE (harness fixed since) | `phase4_witnesses/witnesses_v2_STALE.json` |
| 5 Consumer tracing | **NOT STARTED** (tracer built and validated) | `method/trace_client_consumers.py` |
| 6 Validator + mutation tests | validator **DONE** (27 tests green); mutation tests **NOT DONE** | `tools/manufacturing_spine/`, `tests/manufacturing_spine/` |
| 7 Regression | **NOT DONE** | — |
| 8 PR | **NOT DONE** | — |

Local test status at checkpoint: `tests/manufacturing_spine` + `tests/governance/test_tools_gitignore_boundary.py` → **43 passed**.

---

## 3. What is committed with this checkpoint

| Path | What |
| --- | --- |
| `.gitignore` | D7: `!/tools/manufacturing_spine/` |
| `tools/README.md` | custody table row for the new namespace (README's own contract) |
| `tests/governance/test_tools_gitignore_boundary.py` | probes for the new namespace; **went red before the `.gitignore` line, green after** |
| `tools/manufacturing_spine/{__init__,validate_current_state}.py` | stdlib-only validator; exit 0 / 1 / 2 |
| `tests/manufacturing_spine/test_validate_current_state.py` | order §9 cases 1–17 + implied rules; **red (import error) before the validator, green after** |
| `method/trace_client_consumers.py` | client import-graph + route-reference tracer (Phase 5 input) |
| `method/run_runtime_witnesses.py` | runtime witness harness (Phase 4) |
| `phase0_grounding/*`, `phase2_census/*`, `phase3_wired/*`, `phase4_witnesses/*` | frozen evidence |

`git check-ignore -v` with controls: `tools/manufacturing_spine/*.py` trackable;
its `__pycache__` still ignored (global rule); `tools/grounding_agent/*` unaffected.

---

## 4. Established facts (re-derived on current main, not inherited)

**Two SHAs, two meanings.** The authority map was *executed against* `93df82f3`;
the registry did **not exist** there. The frozen *registry before-state* is
`9d5d9001` (#328 merge). Diff against `9d5d9001`.

**Environment stamp.** Python 3.11.9, FastAPI 0.137.2 (pin `>=0.137,<0.138`).
The local env does **not** satisfy `services/api/requirements.txt`: 9 missing
(`alembic psycopg2-binary pdfplumber reportlab weasyprint openai requests
sg-spec PyJWT`), `shapely` 2.1.1 vs `==2.1.2`. Bounded, not ignored: router
loader 143 loaded / 0 failed, and the census reconciled every registered route.

**Census** (`rmos_authority_map.py --validate` → OK; `--inventory`):
walked 1155 · unique mounted ops 1141 (frozen 1140) · unique paths 1082 (1081) ·
OpenAPI 1078 (1077) · machine-output candidates **68 (67)** · capabilities 26 ·
unexplained emitters **0** · duplicate mounts 14 (frozen said 15 — **unattributed**).
The +1 candidate is `/api/cam/polygon_offset_n17.nc`, registered by #357.

**Change since frozen (`9d5d9001`)** — 0 ADDED, 0 REMOVED, 0 UNKNOWN:

| Capability | Change | Attribution |
| --- | --- | --- |
| profiling | LIVE_UNGOVERNED_OUTPUT → **GOVERNED** | `7182ac7d` / #329 |
| drilling | contract added; disposition unchanged | `3d4bc7f1`, `632a98b5` / #331 |
| vcarve | registry evidence only; production unchanged (HOLD) | #330 |
| polygon-offset | routes 2→3 (N17), generators + consumers edited | `f0b7d95f` / #357 |
| other 22 | UNCHANGED (registry record, endpoint files, generator files) | — |

Limit: the file-level check covers endpoint + generator files, not deeper
helpers. Runtime witnesses are the backstop.

**WIRED:** 68/68 registered route-ops mount, and 68/68 endpoint symbols resolve
to file:line, using the census's own `_IncludedRouter`-aware walker.

**RMOS witness suites on current main:** 12 files, **220 passed**, 0 failed, 0
skipped (26 min). No regression against any merged remediation claim → stop
condition 6 not triggered. Rosette's `RosetteGeometry.__init__() got an
unexpected keyword argument 'center_x'` is **still live** (RUNTIME_BROKEN persists).

---

## 5. Phase 4 — witness verdicts so far (v2, STALE)

Every witness is `SYNTHETIC_PROBE`. EXERCISED needs a *valid* request; EFFECTIVE
needs an *input-derived* check (a 200 alone proves nothing).

| Capability | Status | EXERCISED | EFFECTIVE | Basis |
| --- | --- | --- | --- | --- |
| retract, roughing, helical, biarc-contour | 409 | YES | NO | policy block on a valid request, no program |
| rosette | 400 | YES | NO | fails after evaluator (`center_x` kwarg) |
| drilling | 200 | YES | YES | canned cycle at the supplied hole |
| profiling | 200 | YES | YES | contour extents match the input rectangle |
| binding, cam-post | 200 | YES | YES | extents match input geometry |
| radius-dish | 200 | YES | YES | spans 300 × 200 = supplied dish |
| probing | 200 | YES | YES | G31 starts at r = d/2 + approach = 30 exactly |
| inlay | 200 | YES | YES | spans match fret positions; minor span = marker − tool (see §7) |
| pocketing | 200 | YES | YES | **94.4%** swept coverage of 100×100 pocket |
| feeds-speeds | 200 | YES | YES | advisory JSON, positive feed/rpm (non-manufacturing) |
| geometry | 200 | YES | YES | supplied moves preserved (transformation) |
| v1-dxf | 200 | YES | NO | body is `; TODO: Full toolpath generation requires CAM engine` |
| cam-guitar, headstock-transition, neck-gcode | 200 | YES | UNKNOWN | valid program; no input-derived check established |
| **vcarve** | 200 | YES | *re-run* | v2 extent collapse was a **harness bug**, fixed, not re-run |
| **adaptive** | 200 | YES | *see §6* | 5.7% coverage |
| **polygon-offset** | 200 | YES | *see §6* | 61.4% coverage |
| **rmos-wrap** | 200 | YES | *see §6* | 16.0% coverage |
| **operator-pack** | 404 | — | UNKNOWN | diagnosis interrupted (§6) |
| vision | — | NOT_OBTAINED_SAFELY | — | external AI service; `openai` not installed |
| saw-batch | 404 (missing id) | UNKNOWN | UNKNOWN | needs multi-step saw-lab artifact; not attempted |

Withheld routes within otherwise-witnessed capabilities: cam-guitar's 4
project/auth routes and probing's 2 `/api/v1/machines/probe/*` routes (need a
real machine) → NOT_OBTAINED_SAFELY for those routes.

---

## 6. Open findings — each needs finishing before it is stated as fact

**F1 — adaptive does not clear its pocket (strong, planner-level).** On the
repo's own `SANE_ADAPTIVE` fixture (100×60 pocket, 6 mm tool) all 148 cutting
moves stay in x 69.7–96.5, y 32.2–56.6: **5.7% swept coverage**. Extents alone
cap coverage at ≤13%, whatever the arithmetic. `/plan` reproduces the same 5.7%
and extents, so the **planner** — not G-code emission — produces it; its own
stats say `area_mm2: 6000` but `length_mm: 110.2` (clearing needs ~2,200 mm),
146/151 moves "tight segments". The existing test asserts only 200 + run id +
hash. Candidate EFFECTIVE = **NO** (one canonical input; other strategies not
surveyed). Not a §13 stop condition; top of the deficit queue.

**F2 — rmos-wrap shows the same signature (16.0%)** on a 60×40 DXF; its G-code
has the adaptive planner's `FEED_HINT` loop pattern. Likely inherits F1.
Confirm the shared engine before stating it.

**F3 — polygon-offset: 61.4% coverage, and a possible 0.6 mm overcut.** First
ring at 2.4 mm from the boundary = stepover × tool (0.4 × 6), not tool radius
(3.0). If the input polygon is *part* geometry, the tool edge cuts 0.6 mm outside
it; if it is a *tool-centre* boundary, it is correct. The route contract does not
say which. **Adjudicate, do not assert.** Also count the rings (61% is low).

**F4 — operator-pack upstream.** An adaptive run → 409 "missing required
attachments: dxf_input, cam_plan, manifest, gcode_output". A rmos-wrap run
(`RUN-DXF-…`) → **404**: the MVP wrap run is apparently not a `runs_v2` run.
Interrupted mid-diagnosis. Next: read `services/api/app/rmos/runs_v2/exports.py`
and `packages/client/src/components/dxf/useDxfToGcode.ts` for the run type that
carries those attachments.

**F5 — cam-guitar.** Another session (Inv-037) reports "acoustic tab passes cut
through the body on main". **Inherited claim — re-derive before using.** It
bears directly on cam-guitar EFFECTIVE (currently UNKNOWN).

---

## 7. Method corrections — disclose in the final report

1. **CRLF false negatives.** File lists written by Windows Python carried `\r`;
   the last path on each line never matched in `git log`. Profiling (a known
   positive) read "0 commits". Fixed with `tr -d '\r'`; the positive now registers.
2. **Wrong generator-only change check.** `generators` names the generation
   module, not the gating route handler; switched to live endpoint files.
3. **Tracer blind spot.** Exact-path matching missed base-variable URLs
   (`${API_BASE_N17}/polygon_offset.nc`); added `tail` needles, marked weaker.
4. **Inlay envelope corrected after run 1** — expected the 6.0 mm marker; the
   tool *centre* spans marker − tool = 2.825 mm. Physics, not fitting; disclose.
5. **Plunge points dropped** in the v2 parser (Z-only G1 at known XY) → false
   V-carve collapse. Fixed; **v3 run pending**.
6. **Env gap bounded, not closed** (§4).

---

## 8. Incidental findings (record, do not fix)

- **Registry `client_consumers` is unreliable.** 3 of 18 claims name paths that
  never existed (`composables/useDxfToGcode.ts` → real `components/dxf/`;
  `views/DxfToGcodeWizard.vue` → real `components/wizards/`), plus #357's
  earlier `views/PolygonOffsetLab.vue`. CONSUMED must come from traced chains.
- **#357's polygon-offset consumer correction names two unreachable files.**
  `views/OffsetLabView.vue` has no importer (orphan); `api/n17_n18.ts` is imported
  only by `components/toolbox/AdaptivePoly.vue`, itself unreachable. The routed
  consumer is `components/toolbox/PolygonOffsetLab.vue` (router line 128).
- **Not collected by any push/PR workflow:** `tests/agent_program/`,
  `tests/governance/` (incl. the tools-custody "executable contract"). The only
  runner reaching them is `api_pytest.yml`, manual-only and deprecated.
  Enumerated per the map's §5 correction, including bare `pytest` runs.
- **Three different "spines":** this Manufacturing Spine; SPINE-002…005 (ADR-002
  project spine, #218/#219/#221/#225 — squash-merged, so branches look unmerged);
  the agentic spine (`spine-ci.yml`). Name them apart in the report.
- **#219 / #221** (project→CAM, RMOS artifacts→project) are prime CONSUMED
  candidates for Phase 5.

---

## 9. Resume here

1. Re-run the harness (v3):
   `py -3.11 docs/audit/evidence/manufacturing_spine_current_state_001/method/run_runtime_witnesses.py "$(pwd)" <out.json>`
   — check vcarve extent returns to 0–20.
2. Finish F1–F4 (F4 first; it was the in-flight call).
3. Phase 5: run `method/trace_client_consumers.py`; adjudicate every reachable
   hit at its call site (entry mounted → invocation → route → result used).
   Only rows at EFFECTIVE=YES can reach CONSUMED.
4. Write `docs/audit/manufacturing_spine_current_state_001.{md,json}`; validate:
   `python -m tools.manufacturing_spine.validate_current_state <json> --identity-registry services/api/app/rmos/manufacturing_authority_registry.json --summary`.
5. Add a test validating the committed JSON; mutation-test the validator.
6. `tools/manufacturing_spine/README.md` (validator ≠ authority; registry ≠
   execution permission; maturity ≠ governance disposition).
7. D8 `core_ci.yml` step; CBSP21 manifest `.cbsp21/patches/g2-manufacturing-spine-001.json`.
8. Phase 7 regression: `tests/grounding_agent`, `tests/agent_program`, RMOS
   authority tests, governance gates.
9. Replace this file with the report; one PR; STOP.
