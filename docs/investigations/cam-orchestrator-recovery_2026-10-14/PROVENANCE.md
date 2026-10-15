# Provenance

## External bundle

| Field | Value |
|---|---|
| Path | `C:\Users\<owner>\Downloads\Storage\files - 2026-03-18T031920.383.zip` (outside Git) |
| Timestamp | name `2026-03-18T03:19:20.383`; file mtime `2026-03-18T03:19:22-05:00` |
| Size | 74,372 bytes |
| SHA-256 | `ee3f5fdb0b29385f1187772829175f20a8c1927c0c04fac9acd68717462b80aa` |
| Copies found | one (Downloads top level and `Storage\` searched) |
| Contents | `BACKLOG.md`, `cam_workspace_router.py`, `machines.py`, `orchestrator.py`, `cam_cutting_evaluator.py`, nine plate-physics files, two graduation JSONs |

The bundle was hashed in place and read without modification. Members were extracted only into the
session scratch directory.

## File identities

| File | Git blob | SHA-256 (bytes as stored) | Lines |
|---|---|---|---|
| Bundle `orchestrator.py` | `2f10f102576f2eac500a155edf15428081e39f95` | `618ebe17…c7fa` | 385 |
| Archived `docs/archive/photo_vectorizer_patches/orchestrator.py` (main) | `a574d92183cb5c39e3aac0aafdea457f04c6311d` | `8f37d10b…e707` | 385 |
| Bundle `machines.py` | `53c5580f0a6cad9ef746b798e21551c9b2e0a899` | `8858ed93…10fc` | 92 |
| Archived `docs/archive/photo_vectorizer_patches/machines.py` (main) | `0946b8330576c78bba6e764a81645d8bfe824a42` | `ce8e3149…a7a0` | 92 |
| Live `services/api/app/cam/neck/orchestrator.py` | `db5904fe4391b905d7c738b672302436fc13409a` | `53880c6f…bbfe` | 279 |
| Live `services/api/app/cam/machines.py` | `0ded91122801adf002935e9253112c4e57afe0a7` | `e39c71d4…116d` | 337 |

### External copy vs repository copy

The two copies are **not byte-identical**, but they are code-identical.

- `git diff --no-index --ignore-cr-at-eol` gives 2 changed lines, both docstring prose:
  `BCAM 2030A` → `BCAMCNC 2030A`.
- The archived path carries the bundle blob `2f10f102` at `bc196138` (2026-03-24) and in tag
  `v2.4.0-alpha.1` (2026-03-30).
- It carries `a574d921` from the parentless root `8d91c4c7` (2026-04-05) onward.
- The rename therefore happened in the **03-30 → 04-05 window, whose history was not preserved**.

`machines.py` follows the same pattern (`53c5580f` → `0946b833`).

**Authority:** the external bundle is the earliest copy. The repo copy is an authentic descendant that
differs only in prose, so the difference is not material.

## Commit chain

| Date | Commit | Event |
|---|---|---|
| 2026-03-15 22:35 | `680e3258` | Live orchestrator created (LP-GAP-03), blob `6cf30d17` |
| 2026-03-17 22:32 | `fe1e2f51` | `cam/machines.py` (live lineage) + PostProcessor wired into `truss_rod_channel.py` |
| 2026-03-17 23:10 | `1d7dbd9e` | PostProcessor wired into `profile_carving.py` and `fret_slots.py` |
| 2026-03-18 00:18 | `95ef35d5` | `cam_workspace_router.py` (+ `/neck/generate-full`) |
| 2026-03-18 03:19 | — | External bundle written (outside Git) |
| 2026-03-18 03:41 | `3855579c` | Bundle's plate-physics files committed (PORT-001) |
| 2026-03-18 04:11 | `52ebb632` | Bundle's `cam_cutting_evaluator.py` committed |
| 2026-03-21 02:14 | `73a2703d` | Bundle archived **nested inside** `docs/archive/photo_vectorizer_patches/files - 2026-03-18T011318.450/files - 2026-03-18T031920.383/`; git records the orchestrator as a 52 % copy of the live file |
| 2026-03-24 23:22 | `bc196138` | Archive flattened → `docs/archive/photo_vectorizer_patches/orchestrator.py` (R100) |
| 2026-03-24 | `8e28ba4b` | Live orchestrator gains `@safety_critical` → blob `db5904fe` (unchanged to today) |
| 2026-03-30 | tag `v2.4.0-alpha.1` | Last preserved pre-rewrite state |
| 2026-04-05 | `8d91c4c7` | Parentless root; archive copies now carry the `BCAMCNC` prose |
| 2026-09-22 | `fc8b322a`, `c731eb94`, `351436f7` → merge `b9b0b929` (#398) | LTB-REMEDIATE-P1: profile-loop rapids converted to feed moves; `neck_pipeline_full` fail-closed |

## Ancestry

- **Live file vs either candidate:** the live orchestrator descends from `680e3258` and never
  incorporated the candidate. Its only change since March is the `@safety_critical` decorator.
- **The candidate itself:** it is a modified copy of the live 03-15 file, consistent with git's 52 %
  copy detection at `73a2703d`. It is not an independent design.
- **Did candidate content reach another path?** No. The candidate-only identifiers
  (`_tool_change_block`, `ToolChangeMode.M1` in the neck pipeline, `self.machine` in `NeckPipeline`)
  appear on `main` only in the archive copy.
- **The candidate `machines.py`:** not adopted. The live `machines.py` descends from `fe1e2f51`. The
  two disagree on BCAM 2030A travel (live 600×900×120 vs candidate 1219.2×609.6×101.6), on safe Z
  (25 vs 10), and on available fields.

## Cause of loss

There is **no namespace-collision record** for this file, so none is claimed. The direct evidence is:

- the candidate was archived (`73a2703d`) under an unrelated photo-vectorizer patch-history commit;
- it was archived nested inside a different bundle's folder;
- the `BACKLOG.md` it shipped with was archived beside it.

Classification: **CONSOLIDATION/MIGRATION ARTIFACT**. The mechanism beyond "archived instead of
integrated" is unresolved.
