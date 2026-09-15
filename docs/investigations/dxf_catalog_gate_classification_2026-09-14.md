# DXF-CATALOG-GATE-001 — declarative catalog gate: classification and records (2026-09-14)

**Status:** landed with this PR. Both DXF catalog gates read one registry,
`services/api/app/ci/dxf_catalog_registry.json`, through `services/api/app/ci/dxf_catalog_policy.py`.
**Scope of enforcement:** manufacturing_authority is recorded and enforced in CI; runtime paths do not yet read it. Quarantine is evidence of known nonconformance, not permission to
manufacture, but today only the CI gates act on it. Known runtime consumer that does not:
`generators/body_generator.py` and `generators/lespaul_body_generator.py` load `LesPaul_CAM_Closed.dxf`
(UNADJUDICATED here) as the Les Paul G-code template, reachable from the CAM routers, without
reading this registry or calling the export gate. Runtime enforcement is a separate order.
**Evidence base:** `docs/investigations/dxf_gate_repair_audit_2026-09-14.md` (rule-by-rule audit of the
Copilot/Cursor repair) and `docs/investigations/dxf_topology_crlf_catalog_rerun_2026-09-14.md`.

## Owner rulings implemented

| Ruling (2026-09-13/14) | Where it lives |
|---|---|
| The Files gate is an export-readiness gate; no blanket warning downgrade | `check_dxf_files.py`: every clause failure fails, unless an explicit record covers exactly that clause |
| Folder + layer define asset class, declared rather than scattered through code | the folder picks the class (`class_rules`); layer roles act within the class contract (`outline_layers`, `reference_layers`, `layer_evidence`) |
| `BODY_POINTS` is reference/measurement data | registry `reference_layers`; the manufacturing view drops it before preflight and topology |
| `WIRING_CHANNEL` open paths are not declared valid until the CAM consumer is traced | not declared; `LesPaul_CAM_Closed.dxf` is `UNADJUDICATED` |
| Stored catalog DXFs are R12 only; R2000 is bucket-① paid-tier vectorizer output | registry `version_policy.approved = ["AC1009"]`; no per-file allowance |
| Quarantine records carry asset, asset_class, failed_contract, observed_evidence, disposition, reason, owner_stream, manufacturing_authority = BLOCKED, exit_condition | registry `quarantine`; `test_quarantine_records_are_complete_and_blocked` |
| Owner stream is DXF Catalog Integrity, not Ross | every record; enforced by test |
| Complexity < 15, no baseline raised | highest new function 12; `check_dxf_files.main` 29 → 11, baseline entry removed |
| Malformed witnesses must still fail | `services/api/tests/test_dxf_catalog_gate.py` |

## How a file is judged

1. The registry classifies the path: `body/dxf/*/*.dxf` = `manufacturing_body`, `reference_dxf/**/*.dxf` =
   `reference` (per-segment globs). An unclassified catalog file **fails**; a path two classes claim is an error.
2. Each clause in the class contract is evaluated (the asset gate evaluates the ezdxf-only clauses; the
   Files gate evaluates all of them). A check that crashes is a failure of that clause.
3. No failures: **PASS**. Failures with no record: **FAIL**. Failures with a record: **QUARANTINED**,
   but only if the failures are exactly the record's declared clauses and the file still hashes to the
   record's `asset_sha256`. An extra failure fails the gate; a declared clause that now passes makes the
   record stale and fails the gate; changed bytes fail the gate; a record for a missing file fails the gate.

## Result on the current catalog (both gates, CI toolchains)

**95 files: 65 PASS, 30 QUARANTINED, 0 FAIL.**

- PASS: the 62 `reference_dxf/cuatro` traces; `Cuatro_Venezolano_body.dxf` and `jazzmaster_body.dxf`
  (closed R12 LINE outlines); `Gibson-Melody-Maker_phase3.dxf` (its `BODY_OUTLINE` LINE chain closes
  and bounds the layer under the corrected LINE-loop semantics).
- QUARANTINED, by disposition:

| Disposition | Count | Assets |
|---|---|---|
| `NONCONFORMING_VERSION` | 15 | stored R2000/R2010 but every geometry clause passes: classical, dreadnought, gibson_l_00, J45_body_outline, J45_body_outline_dense, Jumbo, om_000, soprano_ukulele, flying_v_body_phase3, gibson_explorer_body, JS1000, LesPaul_body, Smart-Guitar-v1_back, Smart-Guitar-v1_front, smart_guitar_back_v6_smoothed |
| `QUARANTINED` | 1 | Stratocaster_body: folded BODY_OUTLINE ring |
| `QUARANTINE_CANDIDATE` | 13 | smart_guitar_front_v6_smoothed (twist); harmony_h44, concert_ukulele, octave_mandolin (open outlines, asset intent pending); orchestra_model_body_view, orchestra_model_clean, Gibson-Melody-Maker_phase3_primitives (appear misclassified by location); flying_v_body, flying_v_full (outline role unadjudicated); carlos_jumbo, mandolin, jaguar, mustang (closed R12 POLYLINE, rejected by the runtime pre-check) |
| `UNADJUDICATED` | 1 | LesPaul_CAM_Closed (WIRING_CHANNEL and CUTOUT roles not demonstrated) |

Every record's exit condition names what would clear it. Most end in "regenerate as R12 through
`dxf_compat`", because no body file may stay stored as R2000.

## How each audited rule was resolved

| Audit rule | Resolution |
|---|---|
| F0 lazy import | on main via #372 |
| A1 closed R12 LINE loops | kept, reimplemented: pruned-graph components, 0.05 mm snap, duplicate edges ignored, ARC/open-SPLINE edges chain too. The closed contour must **bound the outline layer** (≥ 0.9 of its extents in both axes), so a small closed strip cannot stand in for the body (the Flying V case) |
| A1 CIRCLE as a body contour | dropped: CIRCLE never counts |
| A2 R2010 widening | superseded by the R12-only ruling |
| A3 no closed contour → warning | rejected: `closed_outline` is a failing clause |
| F1 numeric version compare | moot: the version clause is an explicit approved list |
| F2/F3 empty / no-geometry hard fail | kept (`nonempty`, `geometry_present`) |
| F4 open LWPOLYLINE → warning | rejected; `BODY_POINTS` exempted by declaration instead |
| F5 closed POLYLINE accepted | **reversed** (see the audit's correction note): the runtime rejects it |
| F6 self-intersection → warning | rejected; chained outlines are now also checked for crossings |
| F7 preflight crash → "skipped" | rejected: a crash is a clause failure (topology too) |
| F8 remaining preflight ERRORs block | kept, now on the manufacturing view |

## Review hardening (registry schema v2)

An external review of #378 raised the items below. Each was checked against the code with an executable
probe before acting; the verdicts are what the probes showed.

| Review item | Probe result | Resolution |
|---|---|---|
| No registry schema validation | **Confirmed**: a record naming an unknown clause was accepted; a missing `outline_coverage_min` surfaced as a `KeyError` mid-evaluation | New `app/ci/dxf_catalog_schema.py`, run at load: required keys/types, clause set == implemented clauses, class/rule/record consistency, dispositions, BLOCKED, owner stream, sha256 format. It rejects a malformed registry with a message listing every problem, and both gates report that as a failure. Schema renamed `dxf_catalog_registry_v2`; any other name is rejected |
| Registry clauses can drift from the implementation | Confirmed possible | `KNOWN_CLAUSES` must equal the registry's `clauses` and the Files gate's implemented checks (test) |
| First-match classification, `*` spans folders | **Confirmed**: `body/dxf/electric/sub/x.dxf` classified as a body | Globs match per path segment (`**` spans folders). A path matched by rules for two classes raises an error, so order never matters |
| Figure-8 / self-touching cycles accepted | **Confirmed, broader than stated**: a pinched figure-8 of LINEs passed `closed_outline` *and* the Files gate's crossing check; a body with a chord also passed | A chained outline must be a simple cycle (every vertex joins exactly two edges). All three real chain outlines in the catalog already are, so no verdict changed |
| Coverage is only a bbox test | Accurate | Kept as the ruled criterion, now named as a bounding-box test in code, messages and the clause text |
| Record matched only by asset | Asset + class were already checked; **real gap**: changed bytes that fail the same clause stayed quarantined | Every record pins `asset_sha256`; changed bytes fail both gates until re-adjudicated |
| Evidence mixes gate output and reviewer notes | Accurate | `observed_evidence` is `{gate, review}`: gate lines are `[clause] message` and must cover exactly `failed_contract` (schema-checked) |
| Path-based dynamic import in the asset gate | Accurate (it also created two copies of the policy module in tests) | Normal package import; `app/__init__.py` and `app/ci/__init__.py` are empty |
| `catalog_root` in the registry is unused | Accurate | Both gates fail if the registry's `catalog_root` is not the root they scan |
| Spline with no defining points makes `_edge` raise | **Not reproduced**: `_edge` returns `None` | No change; covered by a new degenerate-geometry test |
| `_two_core` brittle on collapsed / zero-length edges | **Not reproduced** | No change; covered by a new test |
| Structure the version policy as rules/ranges | Declined | `approved` is already a machine-readable allowlist, separate from its prose `basis`. Ranges would weaken the owner's R12-only ruling |

Found while verifying (not in the review): **a clause that raised crashed the whole gate run.** An outline
layer holding only a degenerate spline hit `min()` on an empty sequence. Both gates now turn a crashing
clause into a failure of that clause for that file, and the empty-extent case has its own message.

The review also asked for tests; added: 13 malformed-registry cases, clause drift, per-segment globs and
ambiguity, pinch/chord/zero-length/degenerate geometry, exact failure messages, a reference asset with
broken outline-like geometry (still PASS), crash isolation in both gates, end-to-end quarantine / extra
failure / healed record / changed bytes / absent class rule through **both** gates, and a real CRLF catalog
file (`smart_guitar_front_v6_smoothed.dxf`) as a fixture. After hardening the catalog result is unchanged:
65 PASS, 30 QUARANTINED, 0 FAIL, with the same 30 assets, clauses and dispositions.

## Second review round (Copilot) and the red CI on `acb7fde6`

**The six red checks** (API Tests ×2, api-verify ×2, Core CI Summary ×2) were one test:
`test_jumbo_dimension_consistency.py::test_no_undeclared_jumbo_dimension_artifacts`. It flags any file that mentions
"jumbo" and contains three of the substrings `530`, `432`, `305`, `254`. Schema v2's `asset_sha256` digests happened
to contain `432`, `305` and `254`; the v1 registry had none. The registry mentions jumbo only in asset paths. Fixed the
way the test prescribes: an `ACKNOWLEDGED_NON_DIMENSION_FILES` entry with that reason, scan filters unchanged.

| Copilot item | Probe result | Resolution |
|---|---|---|
| `_chain_crossings` adds a shapely dependency to a gate meant to run without it | **Rejected**: the Files gate job installs `ezdxf shapely`, and its TopologyValidator already imports shapely at module load. The ezdxf-only asset gate never imports this code | None |
| `_serialize_view` mutates the parsed document | **Confirmed, real latent bug**: with `closed_outline` ordered after preflight in the registry, it crashed on destroyed entities (`'LWPolyline' object has no attribute 'dxf'`) | The view is built from a fresh parse; `ctx.doc` is never mutated. A clause-order test pins it |
| Unknown clauses silently pass | **Confirmed** when handed an unvalidated registry (the loader already rejects them) | Defense in depth: an unimplemented clause fails in both gates. The asset gate still skips the clauses the Files gate owns |
| sha256 computed for every file | **Confirmed**: a missing file raised `FileNotFoundError` and would have crashed the run | Hash only files that have a record; an unreadable recorded file fails its record check instead of crashing. Tested |
| Files outside the catalog reported as "unclassified" | Accurate but imprecise | Its own message: outside the catalog root |
| `passed=True` for QUARANTINED is ambiguous | Accurate; no in-repo consumer reads either gate's JSON | `passed` replaced by `blocks_gate` and `export_ready` (only PASS is export-ready); the Files gate JSON regains summary counts |
| `asset_class` override is reachable from normal use | Accurate | Keyword-only; documented as test-only. The CLIs never pass it |
| CLI entry points not tested end to end | Accurate | Both CLIs run as subprocesses in tests (exit code, report JSON) |
| bbox coverage "is a regression in strictness" | **Rejected**: main's gates had no bounding requirement at all (the old asset gate accepted any closed LWPOLYLINE anywhere). This is strictly stronger, and documented as a bbox test | None |
| Closed POLYLINE accepted by the asset gate vs "export-ready" | **Rejected**: the asset gate evaluates closure only. The POLYLINE bodies fail `preflight_valid` in the Files gate and carry records that declare it | None |
| Degenerate graph cases | Covered last round; added a near-miss that straddles the 0.05 mm snap grid (treated as open, the conservative direction) | Test |
| Schema stops after an earlier stage fails | Intentional; the docstring now says why | Docstring |
| `classify` called twice | Accurate | Computed once |
| Review notes aren't machine-checked | By design (`review` is human findings; `gate` is checked) | None |
| Classification is path-only | Accurate: folders pick the class, and layers act within the class contract | Wording |

Also found: the Files gate workflow's "upload report on failure" step pointed at a file nothing wrote. The gate now
takes `--report FILE`, and the workflow writes the path the upload step already expects.

## What the gate still does not check

These are out of the ruled contract. They are recorded here so a green gate is not read as more than it is:

- **Dimensions.** Nothing compares a body against its instrument spec; the asset gate's old docstring
  claimed it did, and it never did (the docstring is corrected). Observed: `jazzmaster_body.dxf`
  158 × 104 mm (PASS), `jaguar_body.dxf` 20.9 × 25.6 mm and `mustang_body.dxf` 39.7 × 40.8 mm (both
  `$INSUNITS=4`, mm), `mandolin_body.dxf` 200 × 90 mm. The last three are noted in their records.
- **Header units.** 20 of the 25 R2000/R2010 body files declare `$INSUNITS=6` (metres) while their
  coordinates are millimetres (the other 5 declare 4, mm).
- **Half-body closed by a centreline.** A half outline closed by a centreline LINE is a closed contour
  that bounds its own layer, so it passes. Only asset intent or a spec comparison can tell.
- **Title-block borders on an outline layer.** A closed border on `BODY_OUTLINE` would bound the layer;
  no catalog file does this today.
- **What CAM actually consumes.** `preflight_valid` mirrors the runtime pre-check, not every consumer;
  the CAM lanes read closed LWPOLYLINE only, and R12 cannot carry LWPOLYLINE. That is consistent with
  the tier rule (CAM input is the paid-tier vectorizer's R2000 output). The consumers of the catalog
  files themselves (`body/outlines.py`, `catalog.json`) were not traced here, except the Les Paul
  G-code generator named under **Scope of enforcement**.
