# Independent spot-check

**Date:** 2026-10-15. **Census ref:** `d42712e0`. **Result:** 45 rows sampled, 84 content checks PASS,
0 FAIL, 6 not applicable (reference-only rows have no content). The facts once cited for the eight
withdrawn override proposals were also rechecked by hand (below): each fact holds. **The owner ruled on
2026-10-15 that they do not establish lineage**, so those eight rows are `UNRESOLVED`; a true fact is not
a proven descent.

## Why a separate checker

`scripts/investigations/march_2026_census_spot_check.py` re-derives each sampled row by a different route
from the census tool, so a defect shared by the tool and its own tests cannot pass both:

| Census tool | Spot-check |
|---|---|
| `git ls-tree -r <ref>` builds a blob → path map | `git rev-parse <ref>:<path>` for each cited path |
| `git log --all --raw` scan for first appearance | `git log --all --find-object=<blob>` |
| hashes members while walking the bundles | re-reads each member from the bundle, found by name and, for a ZIP, matched to the inventory sha256 |

For a `HEURISTIC_CANDIDATE` row it also confirms the inferred successor exists on the ref with other
content. That shows the successor is there; it does **not** prove descent. Lineage stays heuristic until a
human reads the history, which is why those rows keep that class.

**Negative control.** One `EXTERNAL_ONLY` row in a scratch copy of the ledger was given a blob that is in
history. The checker failed it twice, on the bundle re-read and on `--find-object`, and exited 1. The checker
can therefore fail.

## Selection (deterministic)

Rows are sorted by member sha256, then candidate ID, so a rerun picks the same sample:

- the first five `MECHANICALLY_VERIFIED` rows;
- the first five `HEURISTIC_CANDIDATE` rows;
- every row an override touches (`override_id`), whatever its class;
- every `EXTERNAL_ONLY` row;
- every row behind a recovery-order recommendation in `RECOVERY_RECOMMENDATIONS.md` (MC-060, MC-113,
  MC-R01–R05).

All 52 sources were located on the owner's machine (`<Downloads>`, `<Downloads>/Storage`, and a May
backup folder for the two extracted-folder sources). Hosted CI cannot rerun this; the bundles are not in Git.

```
python -I scripts/investigations/march_2026_census_spot_check.py --repo . --ref d42712e0     --census-dir docs/investigations/march-2026-consolidation-recovery-census     --search "<Downloads>" --search "<Downloads>/Storage" --search "<backup folder>"
```

## Facts cited for the withdrawn proposals, rechecked by hand

"Confirmed" means the cited fact is true. It does not validate the proposed lineage; see `OVERRIDE_REVIEW.md`.

| Override | Claim | Check | Result |
|---|---|---|---|
| `8e436e7b` | the live module was first committed byte-identical to this blob in `21fe1b1f` | the first add of the path is `21fe1b1f` (2026-03-18); `rev-parse 21fe1b1f:<path>` = `8e436e7b` | confirmed |
| `8e436e7b` | since #441 the route refuses before generation | `SAFETY_BLOCKED` in the module on `origin/main` (`703694c1`) | confirmed |
| `721cfa3d` | not the live lineage | the live first-commit blob is `8e436e7b`, not this one | confirmed |
| `blueprint_save_router.py` | `_wired` successor is byte-identical to live `save_router.py` | `rev-parse d42712e0:services/api/app/blueprint/save_router.py` = `1c2dfd58` | confirmed |
| `project_router.py` | `_wired` variant entered Git in `ee31d921` and is the live router | first `--find-object` hit `ee31d921` (2026-03-16), at `services/api/app/projects/router.py` | confirmed |
| `BridgeBreakAnglePanel.vue` | no such path in any ref; no such object | `log --all -- '*BridgeBreakAnglePanel.vue'` = 0 commits; `rev-parse --verify 05d77b7d` fails | confirmed |
| `machines.py` | live `cam/machines.py` descends from `fe1e2f51` | first add of that path is `fe1e2f51` | confirmed |
| `materials_router.py` | live `app.materials.router` is registered at `system_manifest.py:111` | line 111 at `d42712e0` is `module="app.materials.router"` | confirmed (the override remains name + role, as stated) |
| `BACKLOG.md` | archived as blob `50022d74` | `rev-parse d42712e0:docs/archive/photo_vectorizer_patches/BACKLOG.md` = `50022d74` | confirmed |
| `orchestrator.py` | owner ruling 2026-10-14 | not re-derived; the replay evidence is in `docs/investigations/cam-orchestrator-recovery_2026-10-14/` | ruling, cited |

## Discrepancies

None in the sample. Hardening this PR found and corrected two defects outside the sample:

- **The HISTORY_ONLY rule counted archive paths as live.** Seven rows were `LIVE_MODIFIED` without a
  justified live successor. Five had a same name only in an archive; two had several same-named live files.
  The rule was fixed and the rows are now `UNRESOLVED`.
- **Reachability output depended on filesystem order.** Six evidence cells listed UI callers in directory
  order. The walks are now sorted. Every classification was already correct.

## Results

Bundles located: 52 of 52. Ref: d42712e0.

| Candidate | File | Proof class | Selected as | Check | Expected | Actual | Result |
|---|---|---|---|---|---|---|---|
| MC-007 | `uwTable.ts` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | member re-read from bundle | ee736afb | ee736afb | PASS |
| MC-007 | `uwTable.ts` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | log --all --find-object | at least one commit | 46d5ea70, ee31d921 | PASS |
| MC-007 | `uwTable.ts` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | successor packages/client/src/design-utilities/lutherie/string-tension/uwTable.ts on ref | present, other content | present, other content | PASS |
| MC-019 | `result_smart_guitar_concept.png` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 1f51397b | 1f51397b | PASS |
| MC-019 | `result_smart_guitar_concept.png` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-020 | `sg_concept_body.svg` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 63234fbb | 63234fbb | PASS |
| MC-020 | `sg_concept_body.svg` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-021 | `sg_concept_body_cavities.dxf` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 1639bd02 | 1639bd02 | PASS |
| MC-021 | `sg_concept_body_cavities.dxf` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-022 | `jumbo_body.dxf` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 23856078 | 23856078 | PASS |
| MC-022 | `jumbo_body.dxf` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-023 | `jumbo_body.svg` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | ebb14c75 | ebb14c75 | PASS |
| MC-023 | `jumbo_body.svg` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-024 | `result_jumbo_archtop.png` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 20403244 | 20403244 | PASS |
| MC-024 | `result_jumbo_archtop.png` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-025 | `bene_rembg_body.dxf` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | adcbfd17 | adcbfd17 | PASS |
| MC-025 | `bene_rembg_body.dxf` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-026 | `bene_rembg_body.svg` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | d7769856 | d7769856 | PASS |
| MC-026 | `bene_rembg_body.svg` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-027 | `result_benedetto_rembg_potrace.png` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | dbbdc036 | dbbdc036 | PASS |
| MC-027 | `result_benedetto_rembg_potrace.png` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-029 | `dxf-requirements.txt` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 2724f3de | 2724f3de | PASS |
| MC-029 | `dxf-requirements.txt` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-042 | `index.html` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | member re-read from bundle | a5d1c648 | a5d1c648 | PASS |
| MC-042 | `index.html` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | log --all --find-object | no commit | no commit | PASS |
| MC-060 | `headstock_transition_export.py` | UNRESOLVED | every override; recovery order | member re-read from bundle | 8e436e7b | 8e436e7b | PASS |
| MC-060 | `headstock_transition_export.py` | UNRESOLVED | every override; recovery order | log --all --find-object | at least one commit | 21fe1b1f, 3fc19f54, 73a2703d, 8c553069 | PASS |
| MC-062 | `headstock_transition_export.py` | UNRESOLVED | every override | member re-read from bundle | 721cfa3d | 721cfa3d | PASS |
| MC-062 | `headstock_transition_export.py` | UNRESOLVED | every override | log --all --find-object | at least one commit | 73a2703d, 8c553069, bc196138 | PASS |
| MC-094 | `instrument_project.py` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | member re-read from bundle | 0e2cc244 | 0e2cc244 | PASS |
| MC-094 | `instrument_project.py` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | log --all --find-object | at least one commit | a6d664d2, ee31d921 | PASS |
| MC-094 | `instrument_project.py` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | successor services/api/app/schemas/instrument_project.py on ref | present, other content | present, other content | PASS |
| MC-095 | `project_router.py` | UNRESOLVED | every override | member re-read from bundle | 715044cb | 715044cb | PASS |
| MC-095 | `project_router.py` | UNRESOLVED | every override | log --all --find-object | no commit | no commit | PASS |
| MC-099 | `blueprint_save_router.py` | UNRESOLVED | every override | member re-read from bundle | cb905550 | cb905550 | PASS |
| MC-099 | `blueprint_save_router.py` | UNRESOLVED | every override | log --all --find-object | no commit | no commit | PASS |
| MC-100 | `useBlueprintProjectWrite.ts` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | member re-read from bundle | d69f4ac4 | d69f4ac4 | PASS |
| MC-100 | `useBlueprintProjectWrite.ts` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | rev-parse d42712e0:packages/client/src/design-intake/blueprint/useBlueprintProjectWrite.ts | d69f4ac4 | d69f4ac4 | PASS |
| MC-103 | `projects_api.ts` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | member re-read from bundle | a5b08b38 | a5b08b38 | PASS |
| MC-103 | `projects_api.ts` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | rev-parse d42712e0:packages/client/src/api/projects.ts | a5b08b38 | a5b08b38 | PASS |
| MC-104 | `useInstrumentProject.ts` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | member re-read from bundle | eaf3873d | eaf3873d | PASS |
| MC-104 | `useInstrumentProject.ts` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | log --all --find-object | at least one commit | 61807b40, 8d91c4c7, d3035e19, d716d16e | PASS |
| MC-104 | `useInstrumentProject.ts` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | successor packages/client/src/instrument-workspace/shared-state/useInstrumentProject.ts on ref | present, other content | present, other content | PASS |
| MC-108 | `materials_router.py` | UNRESOLVED | every override | member re-read from bundle | e131cf1a | e131cf1a | PASS |
| MC-108 | `materials_router.py` | UNRESOLVED | every override | log --all --find-object | no commit | no commit | PASS |
| MC-113 | `BridgeBreakAnglePanel.vue` | UNRESOLVED | every override; recovery order | member re-read from bundle | 05d77b7d | 05d77b7d | PASS |
| MC-113 | `BridgeBreakAnglePanel.vue` | UNRESOLVED | every override; recovery order | log --all --find-object | no commit | no commit | PASS |
| MC-114 | `StiffnessIndexPanel.vue` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 135418ec | 135418ec | PASS |
| MC-114 | `StiffnessIndexPanel.vue` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-115 | `StringTensionPanel.vue` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | bacff396 | bacff396 | PASS |
| MC-115 | `StringTensionPanel.vue` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-116 | `useTension_fixed.ts` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 9b272b53 | 9b272b53 | PASS |
| MC-116 | `useTension_fixed.ts` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-119 | `useTension.ts` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 19392a22 | 19392a22 | PASS |
| MC-119 | `useTension.ts` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-120 | `archtop_graduation_template.json` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | member re-read from bundle | 249055a7 | 249055a7 | PASS |
| MC-120 | `archtop_graduation_template.json` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | log --all --find-object | at least one commit | 4a72f1de, 73a2703d, 8c553069, bc196138 | PASS |
| MC-120 | `archtop_graduation_template.json` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | successor services/api/app/instrument_geometry/models/archtop/archtop_graduation_template.json on ref | present, other content | present, other content | PASS |
| MC-122 | `BACKLOG.md` | UNRESOLVED | every override | member re-read from bundle | 50022d74 | 50022d74 | PASS |
| MC-122 | `BACKLOG.md` | UNRESOLVED | every override | rev-parse d42712e0:docs/archive/photo_vectorizer_patches/BACKLOG.md | 50022d74 | 50022d74 | PASS |
| MC-132 | `machines.py` | UNRESOLVED | every override | member re-read from bundle | 53c5580f | 53c5580f | PASS |
| MC-132 | `machines.py` | UNRESOLVED | every override | log --all --find-object | at least one commit | 73a2703d, bc196138 | PASS |
| MC-133 | `orchestrator.py` | MANUALLY_ADJUDICATED | every override | member re-read from bundle | 2f10f102 | 2f10f102 | PASS |
| MC-133 | `orchestrator.py` | MANUALLY_ADJUDICATED | every override | log --all --find-object | at least one commit | 73a2703d, bc196138 | PASS |
| MC-143 | `soundhole_calc.py` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | member re-read from bundle | 03af5226 | 03af5226 | PASS |
| MC-143 | `soundhole_calc.py` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | log --all --find-object | at least one commit | 73a2703d, bc196138 | PASS |
| MC-143 | `soundhole_calc.py` | HEURISTIC_CANDIDATE | first five HEURISTIC_CANDIDATE | successor services/api/app/calculators/soundhole_calc.py on ref | present, other content | present, other content | PASS |
| MC-153 | `saddle_compensation_calc.py` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | bce4b536 | bce4b536 | PASS |
| MC-153 | `saddle_compensation_calc.py` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-154 | `saddle_compensation_path_pack.html` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | cf7bf54e | cf7bf54e | PASS |
| MC-154 | `saddle_compensation_path_pack.html` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-155 | `headstock_break_angle_calc.py` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 4d1eb71a | 4d1eb71a | PASS |
| MC-155 | `headstock_break_angle_calc.py` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-156 | `headstock_break_angle_path_pack.html` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 9a25033a | 9a25033a | PASS |
| MC-156 | `headstock_break_angle_path_pack.html` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-166 | `bracing_calc.py` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | member re-read from bundle | b4edce4f | b4edce4f | PASS |
| MC-166 | `bracing_calc.py` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | rev-parse d42712e0:docs/archive/photo_vectorizer_patches/bracing_calc.py | b4edce4f | b4edce4f | PASS |
| MC-180 | `geometry_authority.py` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | member re-read from bundle | 662fd2df | 662fd2df | PASS |
| MC-180 | `geometry_authority.py` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | rev-parse d42712e0:services/photo-vectorizer/geometry_authority.py | 662fd2df | 662fd2df | PASS |
| MC-180 | `geometry_authority.py` | MECHANICALLY_VERIFIED | first five MECHANICALLY_VERIFIED | rev-parse d42712e0:docs/archive/photo_vectorizer_experiment_20260321/geometry_authority.py | 662fd2df | 662fd2df | PASS |
| MC-187 | `side_bending_calc.py` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | cf4e245e | cf4e245e | PASS |
| MC-187 | `side_bending_calc.py` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-188 | `side_bending_calc.py` | MECHANICALLY_VERIFIED | every external-only | member re-read from bundle | 643cb3df | 643cb3df | PASS |
| MC-188 | `side_bending_calc.py` | MECHANICALLY_VERIFIED | every external-only | log --all --find-object | no commit | no commit | PASS |
| MC-R01 | `stores/headstock` | SOURCE_UNAVAILABLE | every override; recovery order | no content to check | reference only | reference only | N/A |
| MC-R02 | `types/headstock` | SOURCE_UNAVAILABLE | every override; recovery order | no content to check | reference only | reference only | N/A |
| MC-R03 | `useHeadstock` | SOURCE_UNAVAILABLE | every override; recovery order | no content to check | reference only | reference only | N/A |
| MC-R04 | `useParametric` | SOURCE_UNAVAILABLE | every override; recovery order | no content to check | reference only | reference only | N/A |
| MC-R05 | `headstockData` | SOURCE_UNAVAILABLE | every override; recovery order | no content to check | reference only | reference only | N/A |
| MC-R06 | `luthiers-toolbox-main (28).7z` | UNRESOLVED | every override | no content to check | reference only | reference only | N/A |

Rows sampled: 45. Checks: N/A 6, PASS 84
