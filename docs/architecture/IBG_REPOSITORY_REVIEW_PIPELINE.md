# IBG Repository Review Pipeline

> **Scope:** the derived, human-review artifact layer of the IBG repository proposal pipeline
> (IBG-1 PR C). This layer packages a governed proposal for human engineering review. It produces
> **review artifacts only** — no GitHub pull requests, no git execution, no repository mutation, no
> authority. Its output is **advisory**.

## Position in the pipeline

```
observe ──▶ propose ──▶ PACKAGE ──▶ inspect ──▶ approve ──▶ execute
             (PR A)      (PR C)       (PR D)      (PR E)      (PR F)
                          ▲
             worktree isolation (PR B) — soft, serialization-only input here
```

- **PR A (merged):** `RepositoryChangeProposal`, `ProposalTargetBinding`, CBSP21 packet adapter, the
  body-geometry `RepositoryProposalReviewPackage`. The proposal is the **canonical** engineering artifact.
- **PR B (in review):** `RepositoryWorktreeSpec` / builder. PR C consumes only the *spec's metadata*,
  and only as an optional serialization-only input — **PR C does not import PR B.**
- **PR C (this layer):** turns a proposal into a complete, deterministic, human-reviewable package.

## Constitutional boundary

This layer **may** read canonical facts and serialize them. It **may not** commit, push, merge,
execute git, call GitHub, use `gh`, perform network I/O, write repository files as part of package
construction, create worktrees, or grant/promote authority. A review bundle is a *derived* artifact,
never a second canonical proposal contract — it **embeds** canonical serializations rather than
re-modeling constitutional facts into independently editable fields.

## Components

| Module | Produces | Notes |
|---|---|---|
| `review_summary_builder` | ordered `(heading, body)` review sections | fixed section order; duplicate headings rejected; bodies built only from canonical proposal facts |
| `draft_pull_request_package` | `DraftPullRequestPackage` | advisory PR metadata; `branch_name = proposal.proposed_branch`, `target_branch` caller-supplied (default `main`); both ref-validated **without** git via the **shared** `repository_change_proposal.validate_branch_ref` (single source of truth — draft-PR and proposal ref rules cannot drift); never asserts a branch exists |
| `repository_review_bundle` | `RepositoryReviewBundle` | single derived artifact embedding proposal + draft-PR + optional review package + optional workspace metadata + provenance |
| `repository_review_export` | dict / JSON / markdown + stable hash | all rendered from one canonical dict, byte-stable |

## Workspace metadata — the soft PR-B seam

`normalize_workspace_metadata(value)` accepts exactly:

- `None`;
- a `Mapping` of the recognized workspace fields;
- an object exposing `to_canonical_dict()` (e.g. a PR-B `RepositoryWorktreeSpec`).

It **rejects** any other object, non-string keys, and unrecognized fields; **drops** the
environment-specific `worktree_path` from the canonical form (determinism). Canonicalization sorts
mapping **keys** and sorts the set-like `allowed_paths` field, but **preserves the order of every
other sequence** — a list already carries a deterministic order, and reordering one whose position
could be semantic (e.g. an embedded review-package or provenance sequence) would silently corrupt it.

`build_review_bundle` additionally enforces **cross-field consistency**: if the workspace metadata
supplies `proposal_id`, `repository_id`, or `base_revision`, each must match the bundle's proposal —
a contradicting workspace is rejected fail-closed rather than embedded as an inconsistent "canonical"
fact. Fields the workspace omits are not invented against.

This is the only coupling to PR B, and it is serialization-only — no import, no git. After PR B
merges, a compatibility test can confirm a real `RepositoryWorktreeSpec` passes through unchanged.

## Provenance

The bundle **always** preserves the proposal-level provenance *reference*
(`evidence_candidate_id`, `evidence_provenance_hash`, `producing_subsystem`, `source_authority_state`).
Full lineage is embedded **only** when a governed provenance object is explicitly supplied:

- serialized via the existing `ProvenanceRecord.to_dict()`;
- its `compute_provenance_hash()` **must** equal the proposal's `evidence_provenance_hash` — mismatch is rejected;
- lineage is never re-derived or altered, and the authority state is never changed.

Absent a supplied object, the bundle marks `provenance_lineage_embedded = False` — *not embedded*,
which is distinct from *missing* or *invalid*.

## Determinism

Canonical serialization excludes: timestamps, environment paths, current working directory, runtime
object reprs, unordered mappings/sets, network-derived values, and GitHub state. Markdown is rendered
from the same canonical structure as the JSON, so the two never diverge; identical inputs yield
byte-stable output and a stable content hash (`stable_review_hash`, whose bytes are pinned to
UTF-8 / `ensure_ascii=False` so non-Python consumers reproduce the same digest).

Markdown export **sanitizes** interpolated content so an embedded value cannot restructure the
advisory document: single-line slots (title, headings, `- key: value` lines) collapse newlines and
escape backticks; multi-line section bodies escape backticks and line-leading `#` so embedded text
cannot inject code fences or ATX headings. The escape targets never appear in this layer's own body
formatting, so intended layout is preserved verbatim.

## What this layer is NOT

Not a GitHub integration, not a PR creator, not an inspection API (that is PR D), not a UI (PR E),
and not an execution engine (PR F). Repository mutation remains the final, explicitly governed
capability.
