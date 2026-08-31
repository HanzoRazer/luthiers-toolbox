# `tools/` — repository-owned developer tooling

This directory holds developer/engineering tooling that is **owned by the
repository** and version-controlled normally.

## Custody boundary

`.gitignore` ignores loose content placed *directly* under `tools/` by default,
but explicitly un-ignores the established repository-owned tooling namespaces so
that ordinary source additions are tracked **without needing `git add -f`**:

| Path | Tracked? |
| --- | --- |
| `tools/grounding_agent/**` | Yes — repository-owned package |
| `tools/agent_program/**` | Yes — repository-owned package |
| `tools/codegen/**` | Yes — repository-owned tooling |
| `tools/README.md` | Yes — this document |
| Loose new files directly under `tools/` (e.g. `tools/scratch.py`) | No — ignored by default |
| Generated Python artifacts (`__pycache__/`, `*.pyc`) | No — ignored globally |

Files already tracked at the repository root of `tools/` (for example
`verify_policy.py`, `run_helical_smoke.py`, and the `*.html`/`*.js` utilities)
remain tracked; the ignore-by-default rule only affects *new, untracked* loose
files.

### Adding a new tool

- Adding source inside an authorized namespace above → just `git add` it; it is
  tracked normally.
- Adding a brand-new top-level tooling namespace → create the directory and add
  its `!/tools/<namespace>/` negation to `.gitignore` in the same change, then
  update this table. Prefer a namespace over scattering loose files at the
  `tools/` root.

## Enforcement

The custody boundary is an executable contract, not just prose. It is pinned by
`tests/governance/test_tools_gitignore_boundary.py`, which uses
`git check-ignore` to prove both sides: authorized namespaces are trackable and
loose/generated content stays ignored. Update that test when the boundary
changes.
