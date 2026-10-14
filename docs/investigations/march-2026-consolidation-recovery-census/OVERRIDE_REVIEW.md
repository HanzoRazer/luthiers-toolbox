# Manual override review

`LEDGER_OVERRIDES.json` is the census's main trust boundary. The generated CSVs follow mechanically
from `BUNDLE_CENSUS.json` plus these rulings, so reviewing this page reviews every human judgement in
the ledger. `test_every_manual_override_has_a_review_row` fails if an override has no row here.

**Automatic → ruled** shows what the content-hash rule would have assigned and what the override
assigns. **Changes the answer** is *no* when the override only adds a reason, a safety note or a
follow-up.

How the rule works: a blob found byte-identical live is `LIVE_INTEGRATED`. One found only in archive
paths is `ARCHIVED_COMPLETE`. One that entered Git and later left `main` is `LIVE_MODIFIED` if a
same-named file is live, else `UNRESOLVED`. One never seen in Git is `EXTERNAL_ONLY`.

## Keyed by content (`by_blob`)

A blob key applies to exactly one content.

| Key | Row | Automatic → ruled | Changes the answer | Evidence | Why the rule was not enough |
|---|---|---|---|---|---|
| `8e436e7b` | MC-060 `headstock_transition_export.py` (B15S/B16S/F44, 03-17T155948) | LIVE_MODIFIED → LIVE_MODIFIED | no | The live module was first committed byte-identical to this blob (`21fe1b1f`), registered by `c2c332b8` (`business_manifest.py:50-56`) and modified by `9b7630b9`. The offline replay of the default request gives 21 rapids ending below Z0 with X motion. | The rule cannot know a live route is ungoverned. The override adds the **ACTIVE SAFETY CANDIDATE** label and routes it to HEADSTOCK-TRANSITION-GCODE-SAFETY-001. Recorded only; not fixed here. |
| `721cfa3d` | MC-062 `headstock_transition_export.py` (B17S, 03-17T160517) | LIVE_MODIFIED → SUPERSEDED | **yes** | The live first-commit blob equals `8e436e7b`, not this one (32-line diff). Archived under `archive/experimental/2026-03/`. | The rule infers "live in modified form" from the name alone. Content shows this sibling draft never entered the live tree. Until 2026-10-14 a name-keyed override had wrongly given it MC-060's safety label. The ledger tool now refuses name keys that match two blobs. |

## Keyed by basename (`by_name`)

Each name below maps to exactly one blob in the census. The ledger tool enforces this (exit 2 otherwise).

| Key | Row | Automatic → ruled | Changes the answer | Evidence | Why the rule was not enough |
|---|---|---|---|---|---|
| `orchestrator.py` | MC-133 (blob `2f10f102`, 03-18 bundle) | LIVE_MODIFIED → SUPERSEDED | **yes** | Owner ruling 2026-10-14 after an offline replay: 702 rapids below Z0 with or without it. #398 fixed the defect by another route. It cannot run on the current machine contract and duplicates tool changes. Replay evidence: draft PR #439 (`docs/investigations/cam-orchestrator-recovery_2026-10-14/`, not on `main` while #439 is open). | A same-named live file exists, but it descends from different work. Only the replay shows the candidate never touched the defect. |
| `machines.py` | MC-132 (blob `53c5580f`) | LIVE_MODIFIED → SUPERSEDED | **yes** | Single-preset `BCamMachineSpec` (safe Z 10, retract 5). Live `cam/machines.py` descends from `fe1e2f51` with six presets and a different contract. | The name matches, but the contract does not; the live file is not a modified form of this one. Its clearance values (10 vs 25 mm) go to NECK-CLEARANCE-AUTHORITY-001 as input only. |
| `BridgeBreakAnglePanel.vue` | MC-113 (blob `05d77b7d`) | EXTERNAL_ONLY → RECOVERED_FEATURE_CANDIDATE | **yes** | March task R-2. No path of this name in any Git ref and no such object in the store (both checked 2026-10-14). The backend `calculators/bridge_break_angle.py` is live. | "External only" is true but incomplete. This is planned work that was built and never landed. It still needs an R-2 parity comparison before any restore. |
| `project_router.py` | MC-095 (blob `715044cb`) | EXTERNAL_ONLY → SUPERSEDED | **yes** | The `_wired` variant from nested 03-15T195528 entered Git in `ee31d921` (2026-03-16) and descends to live `app/projects/router.py`. | The rule cannot link an unwired draft to its wired successor under a different name. |
| `blueprint_save_router.py` | MC-099 (blob `cb905550`) | EXTERNAL_ONLY → SUPERSEDED | **yes** | `blueprint_save_router_wired.py` (blob `1c2dfd58`) is byte-identical to live `app/blueprint/save_router.py` (rechecked 2026-10-14). | Same as above: the successor has a different name. |
| `materials_router.py` | MC-108 (blob `e131cf1a`) | EXTERNAL_ONLY → SUPERSEDED | **yes** | Live `app/materials/router.py` is registered (`system_manifest.py:111`). The contents differ. | **Weakest override: inferred from name and role, not content.** It is reasonable, but it is not proven by hash. Treat it as SUPERSEDED (inferred). |
| `BACKLOG.md` | MC-122 (blob `50022d74`) | ARCHIVED_COMPLETE → ARCHIVED_COMPLETE | no | Archived at `docs/archive/photo_vectorizer_patches/BACKLOG.md`. The committed `docs/BACKLOG.md` history is reachable only through tag `v2.4.0-alpha.1`. | Adds only the planning-authority context and the tag dependency (see `PRESERVATION_GAPS.md` P-9). |

## Excluded (`exclude`)

| Pattern | Members | Evidence | Why |
|---|---|---|---|
| `^Kerf Spacing Calculator Bending Wood - Inch` | 68 | A third-party saved web page (site HTML, ad scripts, tracking assets) zipped into `files - 2026-03-20T023112.442 (2).zip` | Not Claude output and not owner material; licence unknown. It is counted in `SOURCE_BUNDLE_INVENTORY.csv` (`excluded_third_party`) but not ledgered, and must never be preserved into this public repository. |

## Reference-only rows (`reference_only`)

These have no content in any source; each row records a reference to something that was never copied out.

| Key | Disposition | Evidence |
|---|---|---|
| `MC-R01` | LOST_REFERENCE_ONLY | `stores/headstock`, imported by the four preserved headstock views and never copied out of the 2026-03-17 claude.ai session (PR #437). |
| `MC-R02` | LOST_REFERENCE_ONLY | `types/headstock`, as MC-R01. |
| `MC-R03` | LOST_REFERENCE_ONLY | `composables/useHeadstock`, as MC-R01. |
| `MC-R04` | LOST_REFERENCE_ONLY | `composables/useParametric`, as MC-R01. |
| `MC-R05` | LOST_REFERENCE_ONLY | `data/headstockData`, as MC-R01. |
| `MC-R06` | UNRESOLVED | A 51,298,423-byte `.7z` repository snapshot inside a 03-21 bundle, recorded but not walked. It cannot cover the unpreserved 03-30→04-05 window because it predates it. |
