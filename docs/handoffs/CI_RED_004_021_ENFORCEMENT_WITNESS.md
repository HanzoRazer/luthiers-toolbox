# CI-RED-004 / CI-RED-021 Enforcement Witness

Date: 2026-07-05
Status: Witness record
Repo: `HanzoRazer/luthiers-toolbox`

## Summary

CI-RED-004 is closed by enforcement witness.

CI-RED-021 is partially verified but remains open.

## What changed

The existing repository ruleset `May 2 2026` (`15875552`) is now active for the
default branch via `~DEFAULT_BRANCH`.

Active rules observed after the settings change:

```text
deletion
non_fast_forward
pull_request
required_status_checks
```

Required status check:

```text
Fence Checks (Blocking)
```

Pull-request rule:

```text
required_approving_review_count: 0
require_code_owner_review: false
require_last_push_approval: false
required_review_thread_resolution: false
allowed_merge_methods: merge, squash, rebase
```

Bypass actors:

```text
[]
```

## Witnesses

### CODEOWNERS

`gh api repos/HanzoRazer/luthiers-toolbox/codeowners/errors` returned:

```json
{"errors":[]}
```

This verifies that the owner token introduced by #196 resolves.

PR #197 then expanded CODEOWNERS coverage to include:

```text
.github/CODEOWNERS
.github/workflows/architecture_scan.yml
```

PR #197 merged as `38c35cbc`.

### Required Fence

PR #197 was opened after the ruleset became active.

Observed PR state while checks were running:

```text
mergeStateStatus: BLOCKED
```

The exact required check appeared as:

```text
Fence Checks (Blocking)
```

Fence workflow witness:

```text
run: 28748985584
job: 85244687853
result: success
duration: 13s
```

The PR merged only after the required fence reported success.

## Closure Decision

### CI-RED-004

Close CI-RED-004.

Reason:

- the fence code was already green;
- `Fence Checks (Blocking)` now reports on PRs;
- that exact check is required by the active default-branch ruleset;
- the required check was witnessed on PR #197 before merge.

### CI-RED-021

Do not close CI-RED-021 yet.

Move it to partially verified.

Verified:

- active default-branch ruleset exists;
- PRs are required;
- `Fence Checks (Blocking)` is required;
- no ruleset bypass actors are configured;
- CODEOWNERS resolves cleanly;
- the fence workflow and CODEOWNERS file are now covered by CODEOWNERS metadata.

Still open:

- CODEOWNER review is intentionally not required yet;
- the repo currently has only one collaborator, `HanzoRazer`;
- strict CODEOWNER review in that topology can force admin/self-bypass mechanics;
- broader required-check policy beyond the fence is not asserted by this pass.

## Next Human Decision

To fully close CI-RED-021, choose one:

1. Add a second real collaborator/code owner, then require CODEOWNER review.
2. Move the repository to an org/team-backed owner, then require CODEOWNER review.
3. Explicitly accept a documented solo-owner exception, while acknowledging that CI-RED-021 remains less strict than "no routine bypass."

Until that decision lands, CI-RED-021 should remain open.
