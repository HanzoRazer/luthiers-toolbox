# Baseline — SHOP-OPERATING-LOOP-RECOVERY-001

Recorded 2026-10-26 before any package file was written. Every audit read used
the remote default branch at the SHA below, not a local working branch.

## Repository revisions

| Repo | Audited ref | SHA | Local checkout state (not audited) |
|---|---|---|---|
| luthiers-toolbox | `origin/main` | `02032884c32d871b8a5addc24021763748eae949` (merge of PR #455, `ltb-mvs-evidence-resolver-003`) | Main checkout on `smart-guitar-cavity-geometry-1` at `ffd155e4`, dirty: 3 modified files (`SPRINTS.md`, `docs/ci/SG_SPEC_TOKEN.md`, a workspace file), 13 untracked. None of it was read for this audit. The package was written in a fresh worktree off `origin/main`, branch `docs/shop-operating-loop-recovery-001`. |
| CNC-Production-Shop | `origin/main` | `408f88037707be868ae08ff2a0a25b1149a18932` (merge of PR #19, CNC-JOB-QUOTE-WORKFLOW-001, 2026-10-26) | Local branch `sg-authority-cleanup` at `1dfae412`, 1 dirty path |
| CAM-Assist-Blueprint | `origin/main` | `ccad852d26bc6dd1a3eb03933b7a0a8e89b9928f` | Local branch `cam-a32-indexed-surface-continuity-metrology` at `058abb16`, clean |
| CAM-Creation-Studio | `origin/main` | `374fa5832e571cebb470c5dc2e57f43b71e71226` | `main`, clean |
| luthiers-toolbox-consolidation-lab | `origin/main` | `acda02289785a9736ae972a255b86388306c6c15` | Local branch `agent/investigation-036-cross-repo-deletion-recovery`, 3 dirty paths. No row needed: no LTB question required it (see SOURCE_SCOPE.md). |

Pre-rewrite LTB history is reachable only through tag `v2.4.0-alpha.1`. Three
ledger citations come from it (`9566b9fd`, `aaa0c6f6`, `1f4b9b30`). None of
those commits is an ancestor of `origin/main`.

## Open pull requests that overlap (checked at start)

| Repo | PR | Touches | Overlap verdict |
|---|---|---|---|
| luthiers-toolbox | #456 `cursor/ltb-mvs-validation-policy-004` (open, not draft) | `services/api/app/physical_engineering/*validation_policy*`, its tests, `docs/investigations/ltb-mvs-validation-policy-004/`, `SPRINTS.md` | **Contract-adjacent, not file-overlapping.** It owns the validation-policy contract that MVS step S6 depends on. This audit edits none of its files and does not touch `SPRINTS.md`. It is recorded as the open dependency in SOL-E01. |
| luthiers-toolbox | #457–#461 (dependabot, client deps) | `packages/client` lockfile/manifest | None |
| CNC-Production-Shop, CAM-Assist-Blueprint, CAM-Creation-Studio, consolidation-lab | — | — | No open PRs |

No overlapping PR owns a file this package writes, so the stop condition did
not fire.

## Unavailable sources

- `docs/audit-sources/*` junctions exist only on the local machine. The
  committed tree carries only their README. No LTB document cites them for any
  of the five capabilities, so nothing was lost by not following them.
- Private session transcripts were not used. No claim in this package depends
  on one.
