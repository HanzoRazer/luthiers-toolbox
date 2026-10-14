# March 2026 consolidation recovery census

**Status:** evidence only. Bounded to 2026-03-15 through 2026-03-21. **No recovered file gains production
authority through this census.** Nothing was restored, integrated, moved or deleted.
**Base:** `origin/main` @ `d42712e0` (2026-10-13). **Companion:**
[`../cam-orchestrator-recovery_2026-10-14/`](../cam-orchestrator-recovery_2026-10-14/).

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
| Safety-relevant candidates | **3**: one **active** (`/api/headstock/transition/gcode`), two closed (archived orchestrator and machine contract) |
| Requiring immediate preservation | **none** at imminent-loss risk. One HIGH: the five headstock modules exist only in a claude.ai conversation |
| Is a later dedicated recovery program justified? | **Yes, bounded.** See `RECOVERY_RECOMMENDATIONS.md` |

### The first-class test: "marked complete, never reached the usable system"

Each March claim was checked separately for:

- file present;
- import reachable;
- route reachable;
- UI consumer reachable from the client router;
- a test that exercises it.

Results (`MARCH_CLAIM_REACHABILITY.csv`, mechanical; adjudications in `IMPLEMENTATION_RECONCILIATION.md`).
Imports are read syntactically, so dynamic imports are missed (reachability can under-count). The UI-consumer
check is a substring search for URL prefixes, so it can over-count. A `VERIFIED_STRUCTURAL` row is therefore
an upper bound on UI reachability, not proof of it:

| Classification | Count |
|---|---|
| `VERIFIED_STRUCTURAL` (all checks pass; test non-vacuity not assessed) | 26 |
| `PARTIAL_MIGRATION` (usually: backend live, no reachable UI caller) | 15 |
| `STRANDED_IMPLEMENTATION` (present, nothing reaches it) | 6 |
| `FALSE_MIGRATION_CLAIM` (mechanical; 2 of the 3 are plans, adjudicated as not implemented) | 3 |

The Sprint 3 migration claims (April, `CLAIM_VERIFICATION.csv`) show the same shape:

- 10 of the 12 were false when made (04-23 audit);
- today, of the 12: 3 VERIFIED, 7 PARTIAL and 2 STRANDED.

## Files

| File | Content |
|---|---|
| `SOURCE_BUNDLE_INVENTORY.csv` | One row per located source: hash, session, completeness, preservation |
| `BUNDLE_MEMBERS.csv` / `BUNDLE_CENSUS.json` | Every member with content hashes and Git location (raw census output) |
| `RECOVERY_LEDGER.csv` | One row per candidate component, with disposition, reason and follow-up |
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
python -I scripts/investigations/march_2026_claim_reachability.py --root . \
    --claims MARCH_CLAIMS_INPUT.csv --out MARCH_CLAIM_REACHABILITY.csv
```

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
- **Subsystem labels are heuristic** (filename, then output session). Dispositions are not.
- **The 03-30 → 04-05 history is not preserved** (parentless root `8d91c4c7`). Tag `v2.4.0-alpha.1`
  covers up to 03-30.
