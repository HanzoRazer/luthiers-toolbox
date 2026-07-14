# IBG Canonical Repository Proposal Pipeline Contract

> **Status:** RATIFIED (repository owner, 2026-07-12). This document defines the canonical contract
> every future IBG repository-proposal implementation must obey. It is a **contract**, not a feature
> layer — the pipeline it describes owns no new logic; it only composes existing contracts.

## Ratified canonical mission

> The canonical IBG repository proposal pipeline transforms governed engineering evidence into
> deterministic, provenance-bearing review artifacts. It terminates at the human-review boundary. It
> does not commit, push, create pull requests, merge, promote evidence, or exercise repository or
> canonical authority. Existing proposal, review-bundle, and draft-PR contracts remain the owning
> contracts; the pipeline only composes them.

## The canonical stages

```
BodyEvidenceCandidate                       governed engineering evidence (upstream, IBG-owned)
      │  build_proposal_target_binding      PR A — derives evidence-owned fields, fail-closed
      ▼
ProposalTargetBinding
      │  build_repository_change_proposal   PR A — content-addressed rcp- proposal
      ▼
RepositoryChangeProposal
      │  build_review_bundle                PR C — review bundle + draft-PR metadata + provenance
      ▼
RepositoryReviewBundle  ⊃  DraftPullRequestPackage  ⊃  provenance reference
      │
      ▼
   ■ STOP — human-review boundary ■         IBG stops here. No execution, no authority.
```

Each stage is an **existing, owning builder**. The pipeline (`RepositoryProposalPipeline.run`)
invokes them in this order and returns a frozen `RepositoryProposalPipelineResult`. It performs no
validation the builders don't already perform and owns no serialization the bundle doesn't already
own.

## Ownership — who owns what (the pipeline owns none of it)

| Concern | Owning contract | Sprint |
|---|---|---|
| evidence→target derivation | `ProposalTargetBinding` / `build_proposal_target_binding` | PR A |
| the canonical proposal + its id | `RepositoryChangeProposal` | PR A |
| review packaging + draft-PR metadata + provenance embedding | `RepositoryReviewBundle` / `DraftPullRequestPackage` | PR C |
| worktree isolation (if used) | `RepositoryWorktreeSpec` (soft, serialization-only input) | PR B |
| **composition order + terminal boundary** | `RepositoryProposalPipeline` | **PR D (this)** |

The pipeline's only contribution is the **canonical composition order** and the **explicit terminal
marker** (`terminates_at = "human_review"`). It duplicates no contract.

## Invariants (enforced by `test_repository_proposal_pipeline.py`)

1. **Reuses existing contracts** — the result's `proposal`/`review_bundle` are the real PR-A/PR-C
   types, and the bundle embeds the proposal's *own* canonical serialization (no re-modeling). The
   pipeline result equals direct composition.
2. **Preserves provenance** — the provenance reference is carried unchanged; verified full lineage
   flows through only when a governed provenance object is supplied and its hash matches (fail-closed).
3. **Does not upgrade authority** — the candidate is never mutated; `source_authority_state` is
   carried, never promoted.
4. **Terminates at human review** — `terminates_at == "human_review"`; the pipeline exposes exactly
   one operation (`run`) and *no* execute/commit/push/merge/PR method.
5. **No git / filesystem / GitHub / network** — asserted by AST-precise import inspection of the
   module.
6. **Deterministic** — identical inputs yield a byte-identical `to_canonical_dict()`; the result is a
   frozen dataclass.

## What this contract deliberately excludes

No execution, no execution *planning* (that is the descriptive PR-E layer, still upstream of any
real mutation), no git/GitHub, no authority. Repository mutation remains a separate, future,
explicitly human-authorized capability — never reached by composing this pipeline.

## Roadmap position

```
A contracts → B worktree isolation → C review package/draft-PR → D canonical pipeline (this)
   → E execution planning (descriptive) → F human-authorized execution engine (future)
```
