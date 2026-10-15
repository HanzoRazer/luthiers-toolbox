# March 2026 consolidation recovery census

**Status:** evidence only. Bounded to 2026-03-15 through 2026-03-21. **No recovered file gains production
authority through this census.** Nothing was restored, integrated, moved or deleted.
**Base:** `origin/main` @ `d42712e0` (2026-10-13). Every path and line citation is pinned there unless it
says otherwise. **Companion:** the CAM orchestrator investigation,
`docs/investigations/cam-orchestrator-recovery_2026-10-14/` (merged in #439). **Since the base:** #441
(`703694c1`) contained the headstock G-code route this census flagged. It now refuses with 409 before
generation; the generator itself is unchanged.

## Review map

Start here. Each conclusion carries a **proof class**, so a reviewer knows what kind of checking it needs:

| Claim | Evidence file | Proof class | Reviewer action |
|---|---|---|---|
| Which bundle members exist and where their content is in Git | `BUNDLE_CENSUS.json`, `BUNDLE_MEMBERS.csv` | Mechanical (content hashes) | Spot-check source hashes; see `SPOT_CHECK.md` |
| Recovery disposition per candidate | `RECOVERY_LEDGER.csv` (`proof_class`, `proof_method`, `automatic_disposition`, `override_id`) | Mixed, labelled per row | Review the `HEURISTIC_CANDIDATE` and `UNRESOLVED` rows |
| Manual corrections | `OVERRIDE_REVIEW.md` (backed by `LEDGER_OVERRIDES.json`) | Human ruling | Approve or reject each row; the **Reviewer** column records it |
| Whether a March "complete" claim reached the usable system | `MARCH_CLAIM_REACHABILITY.csv`, adjudicated in `IMPLEMENTATION_RECONCILIATION.md` | Heuristic, except absent paths | Review the rows whose adjudication differs |
| Independent re-derivation of a deterministic sample | `SPOT_CHECK.md` | Mechanical, by a separate route | Confirm the selection and the negative control |
| Material that no source holds | `PRESERVATION_GAPS.md`, `MC-R01`–`R06` | Evidence of absence | Confirm wording only |

### Proof classes

| Class | Meaning | Rows (ledger) |
|---|---|---|
| `MECHANICALLY_VERIFIED` | A content-hash fact: the blob is on the census ref at a cited path, or in no commit reachable from any ref. For claims: the path is absent. | 143 |
| `HEURISTIC_CANDIDATE` | Inferred from a path or a name, not content. For example: "the first-commit path is still live, so this is its earlier form". Every reachability label other than an absent path is in this class, `VERIFIED_STRUCTURAL` included. | 24 |
| `MANUALLY_ADJUDICATED` | An override in `LEDGER_OVERRIDES.json` decided it; `override_id` names which. | 9 |
| `SOURCE_UNAVAILABLE` | Referenced by preserved code, but no source holds the content. | 5 |
| `UNRESOLVED` | The evidence does not decide it, for example several same-named live files. The tool never guesses. | 13 |

No row reaches `MECHANICALLY_VERIFIED` by a filename or keyword match; `test_ledger_values_and_overrides_are_well_formed`
enforces that.

## Regeneration map

| Output | Inputs | Command | Reproducible in hosted CI? |
|---|---|---|---|
| `BUNDLE_CENSUS.json`, `BUNDLE_MEMBERS.csv` | the 52 March bundles (outside Git; hashes in `SOURCE_BUNDLE_INVENTORY.csv`) + full Git history | `march_2026_bundle_census.py` | **No.** It needs the bundle bytes, which are not committed. This JSON is the authoritative snapshot everything else derives from. |
| `RECOVERY_LEDGER.csv`, `SOURCE_BUNDLE_INVENTORY.csv`, `PLANNING_RECONCILIATION.csv` | `BUNDLE_CENSUS.json` + `LEDGER_OVERRIDES.json` + `MARCH_CLAIM_REACHABILITY.csv` | `march_2026_census_ledger.py` | **Yes, byte-identical.** Checked by `test_the_derived_csvs_regenerate_byte_for_byte`. |
| `MARCH_CLAIM_REACHABILITY.csv` | `MARCH_CLAIMS_INPUT.csv` + the source tree at `d42712e0` | `march_2026_claim_reachability.py --root <git archive d42712e0>` | Yes, byte-identical against that tree (rerun twice 2026-10-15; directory walks are sorted, so filesystem order no longer matters). Not checked in CI, which uses a shallow clone. Run against today's `main` it will differ, because the tree has moved. |
| `SPOT_CHECK.md` results table | the ledger + the 52 bundles + full Git history | `march_2026_census_spot_check.py` | **No.** It needs the bundles. Deterministic sample; exits 1 on any failed check. |
| `MARCH_CLAIMS_INPUT.csv`, `CLAIM_VERIFICATION.csv`, `MARCH_PLANNING_INDEX.csv`, `LEDGER_OVERRIDES.json`, all other `.md` | human-authored from the sources they cite | — | Not generated. These, plus `OVERRIDE_REVIEW.md`, are the review surface. `CLAIM_VERIFICATION.csv` is a human reading of each claim (manually adjudicated); its `VERIFIED` means read and confirmed, not machine-proved. |

Generated files are marked `linguist-generated` in this directory's `.gitattributes`, so GitHub collapses
them in the diff. The human judgement in this census is the overrides; each has a row in
[`OVERRIDE_REVIEW.md`](OVERRIDE_REVIEW.md).

Paths are logical. A bundle is named by its source ID and its timestamped filename, with
`<Downloads>` standing for the owner's local folder. `/mnt/user-data/outputs/` is the generic claude.ai
sandbox output path; it identifies no account.

## Why it was opened

Two independent recoveries found the same shape. In each case, work generated during one week of March
was marked done but never reached the usable system:

- **Headstock suite.** PR #308 shows MERGED, yet it never reached `main`. The views were preserved under
  #437/#438, and five supporting modules were never copied out of the generating session.
- **Neck CAM orchestrator.** A self-described "SAFETY FIX" was archived instead of integrated (companion
  investigation).

The census asks what else from that week shares the shape. It does **not** assume a single technical
cause.

## Four activities this census keeps separate

| Activity | Meaning | Done here? |
|---|---|---|
| **Discovery** | find what existed and where it is now | yes |
| **Preservation** | make an at-risk artefact durable | **no.** Gaps are listed and ranked; nothing is copied in (see `PRESERVATION_GAPS.md`) |
| **Validation** | prove a candidate works or is safe | **no.** Candidates are routed to separate orders |
| **Implementation** | restore, port or fix | **no** |

## Authority order (owner ruling 2026-10-14)

1. Archived March `BACKLOG.md`, blob `50022d74` (`docs/archive/photo_vectorizer_patches/BACKLOG.md`).
2. Contemporaneous `docs/SPRINT_BOARD.md` and the committed `docs/BACKLOG.md` history, via tag
   `v2.4.0-alpha.1`.
3. The original March bundles and nested ZIPs (Downloads, outside Git).
4. Repository commit history and the current runtime.
5. Later `SPRINTS.md`, used **only** for subsequent disposition, never for March intent. It did not exist
   until 2026-04-05; see [`ERRATUM_CL_RED.md`](ERRATUM_CL_RED.md).

## Headline results

| Question | Answer |
|---|---|
| Source bundles located | **52** (41 ZIPs + 11 extracted folders) + **7 nested** ZIPs inside one of them |
| Fully represented in Git (every member's content hash) | **42** |
| Partially represented | **5** |
| Not represented at all | **5** (three 03-16 vectorizer result sets; two 03-19/20 path-pack bundles) |
| Sources holding unique external-only content | **10** |
| Recovery candidates (one per unique content, plus reference-only) | **194** |
| March "complete / integrated" claims checked for reachability | **50** (+12 Sprint 3 migration claims and the BOE endpoint, `CLAIM_VERIFICATION.csv`) |
| Safety-relevant candidates | **3**: one **contained, not fixed** (`/api/headstock/transition/gcode`; ungoverned at the base, refused with 409 since #441), two closed (archived orchestrator and machine contract) |
| Requiring immediate preservation | **none** at imminent-loss risk. One HIGH: the five headstock modules exist only in a claude.ai conversation |
| Is a later dedicated recovery program justified? | **Yes, bounded.** See `RECOVERY_RECOMMENDATIONS.md` |

### The first-class test: "marked complete, never reached the usable system"

Each March claim was checked separately for:

- file present;
- import reachable;
- route reachable;
- UI consumer reachable from the client router;
- a test that exercises it.

Results (`MARCH_CLAIM_REACHABILITY.csv`, machine-computed by heuristic rules; adjudications in
`IMPLEMENTATION_RECONCILIATION.md`). Imports are read syntactically, so dynamic imports are missed (reachability can under-count). The UI-consumer
check is a substring search for URL prefixes, so it can over-count. A `VERIFIED_STRUCTURAL` row is therefore
an upper bound on UI reachability, not proof of it:

| Classification | Count |
|---|---|
| `VERIFIED_STRUCTURAL` (all checks pass; test non-vacuity not assessed) | 26 |
| `PARTIAL_MIGRATION` (usually: backend live, no reachable UI caller) | 15 |
| `STRANDED_IMPLEMENTATION` (present, nothing reaches it) | 6 |
| `FALSE_MIGRATION_CLAIM` (path absent: `MECHANICALLY_VERIFIED`; 2 of the 3 are plans, adjudicated as not implemented) | 3 |

Only the last row is a mechanical fact. The other 47 are `HEURISTIC_CANDIDATE` in the CSV's `proof_class` column.

The Sprint 3 migration claims (April, `CLAIM_VERIFICATION.csv`) show the same shape:

- 10 of the 12 were false when made (04-23 audit);
- today, of the 12: 3 VERIFIED, 7 PARTIAL and 2 STRANDED.

## Files

| File | Content |
|---|---|
| `SOURCE_BUNDLE_INVENTORY.csv` | One row per located source: hash, session, completeness, preservation |
| `BUNDLE_MEMBERS.csv` / `BUNDLE_CENSUS.json` | Every member with content hashes and Git location (raw census output) |
| `RECOVERY_LEDGER.csv` | One row per candidate component, with disposition, reason, follow-up and proof class |
| `OVERRIDE_REVIEW.md` | Every manual ruling: automatic → ruled, evidence, reviewer disposition |
| `SPOT_CHECK.md` | Independent re-derivation of a deterministic sample, with a negative control |
| `LEDGER_OVERRIDES.json` | Every manual disposition and the reason for it, plus the third-party exclusion |
| `MARCH_PLANNING_INDEX.csv` / `.md` | Normalised `BACKLOG.md` + `SPRINT_BOARD.md` items (59) |
| `MARCH_CLAIMS_INPUT.csv` → `MARCH_CLAIM_REACHABILITY.csv` | The reachability test, input and output |
| `PLANNING_RECONCILIATION.csv` | Planning item → bundle → Git → archive → runtime |
| `CLAIM_VERIFICATION.csv` | Sprint 3 (April) migration claims, verified seven ways |
| `R12_R15_CHAIN.md` | The R12/R15 → Sprint 1 → Sprint 3 → headstock → VEC-ANCHOR chain, plus the negative R-12/R-15 search |
| `CONSOLIDATION_TIMELINE.md` | Dated sessions, commits, archives, rewrite; direct vs inferred vs gap |
| `IMPLEMENTATION_RECONCILIATION.md` | Nine questions per subsystem |
| `SUPERSESSION_LEDGER.md` | Later decisions that confirmed, changed or contradicted March dispositions |
| `PRESERVATION_GAPS.md` | Everything still dependent on a non-durable location, ranked |
| `RECOVERY_RECOMMENDATIONS.md` | Grouped findings → separate bounded orders |
| `ERRATUM_CL_RED.md` | CL-RED was a typo; why `SPRINTS.md` is not a March source |

## Reproduce

```
python -I scripts/investigations/march_2026_bundle_census.py --repo . --ref d42712e0 \
    --out-json BUNDLE_CENSUS.json --out-bundles bundles.csv --out-members BUNDLE_MEMBERS.csv \
    B01D="<Downloads>/files - 2026-03-15T003501.238.zip" ...      # source list: SOURCE_BUNDLE_INVENTORY.csv
python -I scripts/investigations/march_2026_census_ledger.py --census BUNDLE_CENSUS.json \
    --overrides LEDGER_OVERRIDES.json --out RECOVERY_LEDGER.csv \
    --out-inventory SOURCE_BUNDLE_INVENTORY.csv \
    --reachability MARCH_CLAIM_REACHABILITY.csv --out-planning PLANNING_RECONCILIATION.csv
git archive d42712e0 services/api/app services/api/tests packages/client/src | tar -x -C <tree>
python -I scripts/investigations/march_2026_claim_reachability.py --root <tree> \
    --claims MARCH_CLAIMS_INPUT.csv --out MARCH_CLAIM_REACHABILITY.csv
python -I scripts/investigations/march_2026_census_spot_check.py --repo . --ref d42712e0 \
    --census-dir . --search "<Downloads>" --search "<Downloads>/Storage"   # see SPOT_CHECK.md
```

Expected output of the ledger step: `{"dispositions": {"ARCHIVED_COMPLETE": 72, "EXTERNAL_ONLY": 21,
"LIVE_INTEGRATED": 51, "LIVE_MODIFIED": 25, "LOST_REFERENCE_ONLY": 5, "RECOVERED_FEATURE_CANDIDATE": 1,
"SUPERSEDED": 6, "UNRESOLVED": 13}, "excluded_members": 68, "rows": 194}`.

ZIPs are read in memory. Nested ZIPs are walked without extraction, and `.7z` repository snapshots are
recorded but not walked.

## Limitations

- **Bundles live outside Git.** Their hashes are recorded here, but their bytes are not preserved by
  this census.
- **Reachability works at router-module granularity.** A UI hit on a sibling endpoint in the same router
  module counts.
- **Client reachability is import-graph based** (from `src/router`). Dynamic string-built imports are
  not followed.
- **Test non-vacuity is not assessed mechanically** (`NOT_ASSESSED`), except where a document says
  otherwise.
- **Subsystem labels are heuristic** (filename, then output session). Dispositions carry their own
  `proof_class`; `LIVE_MODIFIED` from the automatic rule is always `HEURISTIC_CANDIDATE`.
- **The 03-30 → 04-05 history is not preserved** (parentless root `8d91c4c7`). Tag `v2.4.0-alpha.1`
  covers up to 03-30.
