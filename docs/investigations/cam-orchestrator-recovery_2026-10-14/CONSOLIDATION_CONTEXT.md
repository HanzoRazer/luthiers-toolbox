# Consolidation context (bounded to direct CAM provenance)

The full March 15–21 census is in
[`../march-2026-consolidation-recovery-census/`](../march-2026-consolidation-recovery-census/). This file
covers only what is needed to explain how the orchestrator candidate came to be archived instead of
integrated.

## Verified facts

- **Separate output sessions ran in parallel** during 2026-03-17/18:
  - the claude.ai `ps-vue` suite (headstock + neck + CAM workspace UI, 03-17 03:53–22:42);
  - a CAM-backend session whose output is the 03-18 03:19 bundle;
  - repository commits made through Claude Code and Cursor (`Made-with: Cursor` trailers on
    `34e22a77`, `8c553069`).
- **The live CAM files the candidate targets were all touched that week:**
  - `machines.py` (`fe1e2f51`, `95ef35d5`);
  - the neck generators (`fe1e2f51`, `1d7dbd9e`);
  - `cam_workspace_router.py` (`95ef35d5`, `a1ff8417`).
- **The live orchestrator was not touched in that window.**
- **Parts of the 03-18 03:19 bundle were committed within an hour:** plate physics (`3855579c`, 03:41)
  and `cam_cutting_evaluator.py` (`52ebb632`, 04:11, "From uploaded files").
  - Its `orchestrator.py` and `machines.py` were not committed to a live path.
  - Its `cam_workspace_router.py` was byte-identical to the one already committed at 00:18.
- **The whole bundle was archived on 2026-03-21 (`73a2703d`)**, under the subject
  "chore: archive photo-vectorizer patch history". It was nested inside a different bundle's folder
  (`files - 2026-03-18T011318.450/`), and flattened on 03-24 (`bc196138`).
- **The history from 2026-03-30 to 2026-04-05 is not preserved.** Main starts at a parentless root
  (`8d91c4c7`). The pre-rewrite history survives in tag `v2.4.0-alpha.1`.

## Plausible contextual explanation (inferred)

The candidate edited a file (`orchestrator.py`) and a contract (`machines.py`) that another stream had
just changed in a different direction. Live `machines.py` grew six presets plus a computed-property
contract the same evening. Applying the candidate would have broken the live contract (arm C proves it
cannot run against it). Archiving under an unrelated patch-history commit is consistent with a bulk
"preserve what we did not integrate" sweep, not a per-file decision.

## Unresolved

- Whether anyone evaluated the candidate before it was archived. No record says so.
- Who renamed `BCAM` → `BCAMCNC` in the archive copy, and why. It happened in the unpreserved
  03-30 → 04-05 window.

## Other stranded CAM safety candidates (listed, not investigated)

| Path | Date | Apparent purpose | Recommended review |
|---|---|---|---|
| `docs/archive/photo_vectorizer_patches/machines.py` | 03-18 | Single-preset BCAM contract (safe Z 10, retract 5, M1 pause) | Input to a clearance-authority decision only; not a port candidate |
| `services/api/app/cam/_om_purf_08_additions.py` | 03-17 (`0a3d53b9`) | G38.2 channel-depth probe cycle; a filename prefixed `_` sitting on a live path | Census row; reachability unverified here |

No other stranded CAM file self-describing as a safety fix was found in the bounded window. The census
ledger is the place for any further rows.
