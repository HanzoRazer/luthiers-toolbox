# SCAFFOLD-DIST-001 — Result

**Order:** SCAFFOLD-DIST-001 — Scaffolder Self-Test, Sited and Pinned
**Repo:** `luthiers-toolbox`
**Date:** 2026-09-10
**Branch:** `cursor/scaffold-dist-001-53cb`
**Execution environment:** portable — `git`, Python, `pytest`. Tests build their own temp repositories. No owner-environment asset required.

---

## Stage 0 — grounding (before any commit)

Recorded against live `origin/main` at

`c9c60779aa3bab645882adb9754a36997c3e3111`

(2026-09-09, merge of PR #367). The export appendix is not inherited; these facts were re-derived.

| Fact | At live `main` |
|---|---|
| `scripts/scaffold_agents_md.py` | **ABSENT** — D5 applies; scaffolder built to the test contract |
| `scripts/ci/test_scaffold_agents_md.py` | **ABSENT** |
| `AGENTS.md` at repo root | **ABSENT** (and was not written by this order — D8) |
| `.github/PULL_REQUEST_TEMPLATE.md` | exists, **uppercase**. No lowercase sibling. Defects #2/#4 are live here. |
| Governance pytest pin | `core_ci.yml` **line 50** (order's `:46` is stale vs this SHA): `python -m pytest scripts/ci/test_check_contracts_governance.py -v` |
| Workflows searched | **55** `.yml` files under `.github/workflows/` (order appendix said 54) |
| Repo-root `tests/` collected as a directory | **no** — see observation below |

Supplied test source (unmodified, not merged):
`origin/docs/agents-md-scaffold:scripts/ci/test_scaffold_agents_md.py` @ `bd0f5409`.

That branch also carries `AGENTS.md`. It was **not** merged and `AGENTS.md` was **not** copied (D8).

---

## Placement

`scripts/ci/test_scaffold_agents_md.py` is byte-identical to the supplied file (D1).

```
e133b6f638ac581694f155933b08b8bda27c576f25a33879f69a297637e1189d  scripts/ci/test_scaffold_agents_md.py
e133b6f638ac581694f155933b08b8bda27c576f25a33879f69a297637e1189d  supplied file
```

`SCAFFOLDER` resolution, asserted by running, not by reading:

```
Path(__file__).resolve().parents[2] / "scripts" / "scaffold_agents_md.py"
→ /<repo-root>/scripts/scaffold_agents_md.py
exists: True
```

Suite result is the same from repo root and from `scripts/ci/`: **14 passed**.

stdin is closed (`subprocess.DEVNULL`) on every `_run_scaffolder` invocation — the agent-session condition that hid defect #1.

---

## CI pin (D4)

`.github/workflows/core_ci.yml` — the only existing file modified — gained a named step beside the existing by-name pins:

```yaml
      - name: Scaffolder Self-Test (SCAFFOLD-DIST-001)
        run: |
          python -m pytest scripts/ci/test_scaffold_agents_md.py -v
```

No directory glob was added. The by-name convention is followed, not changed.

### Teeth — the pin fails the step when a test fails

Demonstrated locally with the exact CI command. One assertion was temporarily rewritten:

```
assert heading == "# Agent instructions — BROKEN-ON-PURPOSE"
```

Command: `python -m pytest scripts/ci/test_scaffold_agents_md.py -v`

```
FAILED scripts/ci/test_scaffold_agents_md.py::test_heading_uses_remote_name_not_directory_name
1 failed, 13 passed
exit 1
```

The break was **not committed**. After `git checkout --` the test file digest was again

`e133b6f638ac581694f155933b08b8bda27c576f25a33879f69a297637e1189d`

and the suite returned to 14 passed.

A workflow step whose `run:` is that command inherits pytest's non-zero exit. That is the reviewer's one check: the file is named, and a failing assertion turns the step red.

---

## Negative — subject missing is not a skip

With `scripts/scaffold_agents_md.py` renamed, the same heading test **failed** (did not skip):

```
can't open file '.../scripts/scaffold_agents_md.py': [Errno 2] No such file or directory
assert 2 == 0
```

A self-test that silently skipped when its subject was missing would be the hollow guarantee this file exists to avoid. The rename was reverted; nothing committed.

---

## Run outcome — defect by defect

pytest collected **14** items: eight named functions, one of them parametrized across 6 case × location combinations. The order's "ten" count treated the parametrized function as one row plus six combinations; the runner's count is 14. All 14 passed from repo root (0.89s) and from `scripts/ci/` (same assertions).

| # | Test | Defect / contract | Result |
|---|---|---|---|
| 1 | `test_heading_uses_remote_name_not_directory_name` | #3 — heading uses remote name, not worktree directory (`ltb-sprints` → `luthiers-toolbox`) | **PASSED** |
| 2a | `test_existing_template_is_found_in_any_casing_or_location[PULL_REQUEST_TEMPLATE.md-.github]` | #2/#4 — case-folded discovery | **PASSED** |
| 2b | `[PULL_REQUEST_TEMPLATE.md-]` (repo root) | #2/#4 | **PASSED** |
| 2c | `[PULL_REQUEST_TEMPLATE.md-docs]` | #2/#4 | **PASSED** |
| 2d | `[pull_request_template.md-.github]` | #2/#4 | **PASSED** |
| 2e | `[pull_request_template.md-]` (repo root) | #2/#4 | **PASSED** |
| 2f | `[pull_request_template.md-docs]` | #2/#4 | **PASSED** |
| 3 | `test_force_without_yes_refuses_headlessly_and_writes_nothing` | #1 — non-TTY `--force`: non-zero, write nothing, no `EOFError`/`Traceback` | **PASSED** |
| 4 | `test_force_with_yes_overwrites_headlessly` | §6.4 — `--force --yes` overwrites | **PASSED** |
| 5 | `test_undetectable_default_branch_refuses_headlessly` | **poison-pill** — no `origin/HEAD`, no local `main`/`master`: refuse, write nothing; stderr has `could not detect the default branch` and `--default-branch` | **PASSED** |
| 6 | `test_default_branch_override_is_used_throughout` | §6.6 — `--default-branch develop` used throughout; no `origin/main` | **PASSED** |
| 7 | `test_happy_path_writes_both_with_todo_blocks_unfilled` | §6.7 / D5 — writes `AGENTS.md` + `.github/pull_request_template.md`; `<!-- INCIDENTS` and `<!-- VERIFICATION GATES` unfilled; prints `NOT DONE` | **PASSED** |
| 8 | `test_second_run_does_not_clobber` | §6.8 — second run prints `SKIP`, does not clobber a hand edit | **PASSED** |
| 9 | `test_refuses_a_non_git_directory` | §6.9 / D6 — exit code **2**, writes nothing | **PASSED** |

No assertion was changed to obtain a pass (D1). Commit 4 (`fix(scaffold-dist-001): …`) was not required: Stage 0 found the scaffolder absent; commit 3 added it to the test contract; the suite was green.

---

## Scaffolder (D5)

`scripts/scaffold_agents_md.py` was **created** because Stage 0 found it absent. It implements the §6 contract:

1. Heading from the remote repository name, not the directory name.
2. Case-folded PR-template discovery across `.github/`, repo root, and `docs/`.
3. `--force` without `--yes` on non-TTY: refuse before any write.
4. `--force --yes`: overwrite headlessly.
5. Undetectable default branch: refuse before any write.
6. `--default-branch` used throughout the emitted text.
7. Happy path leaves `INCIDENTS` and `VERIFICATION GATES` as unfilled `<!-- … -->` TODO markers.
8. Existing files are skipped (`SKIP`) unless `--force --yes`.
9. Non-git directory: exit 2.

No production path, no service code, no schema. This order did not scaffold this repository.

---

## Diff guard (§9.8 / §9.9)

Against `c9c60779` the branch adds or modifies only:

| Status | Path |
|---|---|
| **M** | `.github/workflows/core_ci.yml` — the only existing file modified |
| **A** | `scripts/ci/test_scaffold_agents_md.py` |
| **A** | `scripts/scaffold_agents_md.py` |
| **A** | `reports/scaffold/scaffold_dist_001/RESULT.md` (this file) |

Nothing under `services/` or `src/`. No `AGENTS.md` written to this or any repository.

---

## Commit sequence (D2)

1. `b9af5349` `test(scaffold-dist-001): site scaffolder self-test in scripts/ci` — test lands; subject still absent
2. `958ef5b4` `ci(scaffold-dist-001): pin scaffolder self-test in core_ci.yml` — guard armed before subject is known good
3. `0b87d3bc` `feat(scaffold-dist-001): add scaffold_agents_md.py to the test contract` — D5, Stage 0 absent
4. *skipped* — no failing assertion against the new scaffolder
5. this file — defect-by-defect result

A regression guard written after the fix proves only that the code matches itself. Commits 1 and 2 precede 3 for that reason.

---

## Repo-wide observation — `tests/` is uncollected as a directory (§9.11)

**Not fixed here.** Recorded so the finding is not assumed.

**Population searched:** all **55** workflow files at `.github/workflows/*.yml` on `c9c60779`.

**Finding:** no workflow runs `pytest tests/` (or `python -m pytest tests/`) as the repo-root `tests/` directory. Every `tests/` reference names an individual file, a named subdirectory, or a path under `services/api/`.

Examples of the by-name pattern (not exhaustive):

- `pytest tests/test_o3d_heal_topology.py` (`mesh-pipeline-ci.yml`)
- `pytest tests/test_replay_smoke.py` (`spine-ci.yml`)
- `python -m pytest tests/test_endpoint_truth_gate.py -q` (`rmos_ci.yml`)
- `python -m pytest tests/test_cost_attribution_mapper_unit.py -v` (`core_ci.yml`)

The closest directory collection is `python -m pytest tests/grounding_agent/ -q` in `grounding_agent.yml` — a **subdirectory**, not repo-root `tests/`.

A self-test placed at repo-root `tests/` would exist and never run. That is the hollow-guarantee shape the scaffolder is hardened against, reproduced as the reason this file is sited in `scripts/ci/` and pinned by name.

---

## Definition of done

| Criterion | Status |
|---|---|
| Stage 0 recorded with base SHA | `c9c60779aa3bab645882adb9754a36997c3e3111`; scaffolder **absent** |
| Test at `scripts/ci/`, byte-identical, runs | digest match; 14 passed from root and from `scripts/ci/` |
| Pinned by name in `core_ci.yml` | `python -m pytest scripts/ci/test_scaffold_agents_md.py -v` |
| Pin demonstrated to fail on a broken assertion | exit 1, 1 failed / 13 passed; revert restored digest |
| Every test recorded, mapped to its defect | table above |
| Where tests failed, scaffolder changed and test did not | no test failure after commit 3; test never modified |
| Exactly one existing file modified | `core_ci.yml` |
| No `AGENTS.md` written | confirmed at root; not tracked |
| `tests/`-uncollected observation with searched population | 55 workflows, recorded above |
