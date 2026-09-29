# BASELINE — post-CF2 consolidation resume (004)

Evidence-only. No production behavior changed by this increment.

## Repository state
- `origin/main` SHA: `5258d4c6754c122fcdad65df2019c9f7c11eaffe` (Merge PR #418).
- PR #418 merged; its head was `ded5f6af4fc5533f42be38e61e7691de0bc32807` (`a344cb0e` Phase B + `17642a94` refusal-persistence test + `ded5f6af` material-canonicalization fix), all ancestors of `origin/main`.
- Branch: `cursor/consolidation-resume-options-004`, cut from `origin/main`; merge base equals `origin/main` (base current).
- Worktree clean at branch creation.

## Open-PR overlap
- 5 open PRs (#413–#417), all Dependabot touching only `packages/client/package.json` + `packages/client/package-lock.json`.
- No open PR overlaps the proposed evidence files under `docs/investigations/consolidation-resume-options_2026-09-29/` or `.cbsp21/patches/consolidation-resume-options-004.json`.

## Manufacturing-output inventory (parsed from committed JSON, not Markdown)
- `python -m app.ci.manufacturing_output_inventory --check` → OK (`candidates=239 live=1157 naive=10`).
- Containment counts: `UNKNOWN=189`, `LIVE_UNGOVERNED=13`, `FAIL_CLOSED=37`. `PERMITTED_BY_AUTHORITY=0` (dead enum by classifier contract).
- Rosette rows:
  - `POST /api/rmos/rosette/export-cnc` → `FAIL_CLOSED` (`authority_key=rosette:export_cnc`).
  - `POST /api/rmos/rosette/design` → `FAIL_CLOSED` (`authority_key=rosette:design`).

## CI / deployment evidence (from the merge authority statement)
- All GitHub workflows passed on #418; Railway backend and client deployments passed.

## Baseline test IDs satisfied
- CRO-001 base SHA `5258d4c6…` ✓
- CRO-002 #418 merged, head `ded5f6af…` ✓
- CRO-003 inventory checker passes unchanged ✓
- CRO-004 both Rosette rows `FAIL_CLOSED` ✓
- CRO-005 live-ungoverned count = 13 ✓
- CRO-006 open-PR overlap completed (no overlap) ✓
