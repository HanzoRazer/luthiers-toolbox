# March 2026 planning index — sources and limits

Companion to `MARCH_PLANNING_INDEX.csv` (59 rows). Evidence only: nothing here changes code, and no
row grants any file production authority.

## What these records prove

A backlog or sprint-board entry proves that the work was **recognized, planned, deferred or claimed**
at a point in time. It does **not** prove the work was implemented, reachable, tested or safe. A section
**removed as complete** proves a *completion claim*, nothing more. The claim-verification pass (file
present → import reachable → route reachable → UI consumer → runtime proven → test non-vacuous) is a
separate step. Where two records disagree, both are kept side by side in the CSV; neither is preferred
for being newer.

`CL-RED` is not used as a source name. It was a July 2026 typo for `CI-RED` (corrected in `b0b2a8ad`),
and `CI-RED` is unrelated to this March work. `SPRINTS.md` did not exist in March (first present in the
2026-04-05 root `8d91c4c7`); it is used only for later dispositions, never for March intent.

## Source 1 — archived March `BACKLOG.md` (authority 1)

| Property | Value |
|---|---|
| Path on `main` | `docs/archive/photo_vectorizer_patches/BACKLOG.md` |
| Git blob | `50022d74bf2807c146aa99bdeb77f7f28daddc7e` |
| SHA-256 | `6b7ca1b5185dd71e24a3ac55836322b55953cf60300503258b8b410e40419787` |
| Size | 44,637 bytes, 1,134 lines |
| External copy | `Downloads/Storage/files - 2026-03-18T031920.383.zip` → `BACKLOG.md`, **byte-identical** (same blob) |
| First commit | `73a2703d` (2026-03-21 02:14, "chore: archive photo-vectorizer patch history"), under a nested bundle path |
| Moved | `bc196138` (2026-03-24, "flatten photo_vectorizer_patches archive"), rename at 100% similarity |
| Reachable from `origin/main` | yes, same blob |

**Structure.** 29 `##` items: PORT-001, ARCH-001/002, WOOD-001, NECK-001, HEADSTOCK-001,
VECTORIZER-001, CAM-SURVEY-001, ROOT-CLEANUP-001, CONSTRUCTION-001…010, GEOMETRY-001…010. Each has
`**Status:**`, `**Priority:**`, usually `**Effort:**` and a "File to create" or copy instruction.
NECK-001, HEADSTOCK-001, VECTORIZER-001 and CAM-SURVEY-001 name source files under
`/mnt/user-data/outputs/` (the claude.ai sandbox) and a Cursor copy step.

**Relation to the committed backlog.** This is the **pre-commit** copy. The first committed
`docs/BACKLOG.md` (`8ef349c9`, 2026-03-18 13:48) equals it minus the ARCH-002 section (16 lines). That
commit applied ARCH-002 and dropped its section. No committed version equals blob `50022d74`.

## Source 1b — committed `docs/BACKLOG.md` history (tag `v2.4.0-alpha.1`)

43 versions from `8ef349c9` (03-18) to `1dff587a` (03-24). The file is **not on `origin/main`**. The
history is reachable only through tag `v2.4.0-alpha.1`. 18 further items appear only here (TEST-001,
CLEANUP-001/002, STUB-001, WIRE-001…003, BACKEND-001/002, ACOUSTIC-001…005, CALC-001, DECOMP-001/002,
PHOTO-003). The CSV gives each item's first-seen commit, its status chain, and the commit that removed
its section.

## Source 2 — `docs/SPRINT_BOARD.md` (authority 2)

| Property | Value |
|---|---|
| Blob at tag `v2.4.0-alpha.1` | `a3b3b57578097dec9cd3013e2c8106282d76f66b` (18,640 bytes) |
| Blob on `origin/main` | **identical** (`a3b3b575`); last touched by the 04-05 root `8d91c4c7` |
| First added | `1f4b9b30` (2026-03-16 18:12). `0dc29a9f` (03-17 14:50) is titled "add SPRINT_BOARD.md" but the file already existed |
| March versions read | `1fdd5d53` (03-18 19:43), `1fea7570` / `222ea78e` (03-19), tag |

The 12 `SB-*` rows are the session-log, "Next Up" and table entries that touch the census subjects. The
board has **no entry** for GEN-6 (acoustic body generator), the PostProcessor wiring, `machines.py`, or the
radius-dish work. For those subjects there is no March planning record, so the census must work from
commits and bundles alone.

## Findings that surfaced while indexing (recorded, not adjudicated)

1. **Removal before implementation (8 items).** CONSTRUCTION-002, -003, -008 and GEOMETRY-002, -005, -006
   were removed by commits that implemented a *different* item, earlier than the commit naming them.
   HEADSTOCK-001 and VECTORIZER-001 were removed by a `chore` commit 26 minutes before the commit naming
   them (see 2). The backlog was being cleared in batches, ahead of the work.
2. **HEADSTOCK-001 / VECTORIZER-001 conflict.** `21fe1b1f` (03-18 19:37) removed both as complete. Its
   HEADSTOCK-001 evidence was `headstock_transition_export.py` + `neck_profile_export.py`, not the specified
   `dxf_export.py`. Six minutes later `1fdd5d53` wrote **"HEADSTOCK-001: dxf_export.py (needs locating)"** and
   **"VECTORIZER-001: photo_vectorizer_router.py integration"** into "Next Up". Both routers then landed in
   `98c0b58d` (20:03). The "Next Up" lines were never reconciled and are still on `main`. The cited
   `neck_profile_export` router was deleted as an orphan the next day (`1fea7570`).
3. **ROOT-CLEANUP-001 cites a commit that does not exist.** The backlog says `e5dae247`, which is not in
   this repository. The removal commit says `3357c793`, which exists.
4. **GEOMETRY-009 self-contradiction.** `4741f084` says "GEOMETRY-009/010 were not present (completed
   separately)", but its diff deletes the GEOMETRY-009 section. No March commit names GEOMETRY-009.
5. **ARCH-001 means two things.** In the backlog it is "connect plate solver to graduation map". The
   SPRINT_BOARD TRACK 10 table uses ARCH-001 for "D'Aquisto graduation data digitized to JSON".
6. **The headstock suite import is recorded only on the board.** The 03-18 log row lists the four headstock
   views going to `views/cam/headstock/`. In the same row it says the backend files were *"flagged for Claude
   Code — not integrated"*. That row came in commit `8c553069`, which is titled "feat(materials): add E_C_gpa
   cross-grain modulus".

## Limitations

- Line numbers are against the stated blobs. CSV `stated_status_in_march` quotes the first status seen,
  verbatim.
- "Commit naming item" means a non-`chore`/`docs` subject that contains the ID. It is a lexical match,
  not proof that the commit implements the item.
- `0d65d043`, `ac56ec6b` and `4600b02f` (cited by the board or backlog) were not resolved in this pass.
- Items outside March 15–21 (DECOMP-*, PHOTO-003, 03-22…24) are indexed because they are in the same
  file history. They are not census subjects.
