# IBG-1 — Repository Proposal Archaeology Inventory

**Class:** Read-only archaeology record (harvest-first inventory that shaped PR A).
**Repo:** `luthiers-toolbox`
**Anchor:** `origin/main` @ `ac5a2d35`, inspected 2026-07-10 (read-only; no mutation, no worktree
during the archaeology pass — read against the object store).
**Purpose:** Record what already exists so IBG-1 harvests and composes existing contracts instead
of inventing parallel abstractions. The original 10-file handoff plan was **discarded** where it
conflicted with the real tree; this document is the delta and the grounded PR-A plan.

---

## 1. Actual IBG package location (vs the handoff's assumption)

| Handoff assumed | Reality (verified) |
|---|---|
| `services/api/app/ibg/` | **Does not exist.** IBG runtime lives at `services/api/app/instrument_geometry/body/ibg/` |
| `services/api/app/routers/ibg_router.py` (modify) | **Does not exist.** IBG has no dedicated router today |
| "Existing Worktree Infrastructure" (dependency) | **Not found** as reusable app code (only a CI-script mention) |
| "Git Integration Layer" (dependency) | **Not found** as an app module |
| create `repository_review_package.py` | A review package **already exists**: `instrument_geometry/body/ibg/workflow/review_package.py` |

**Consequence:** the new capability is homed in a **dedicated package** (§4), not under
`instrument_geometry/body/ibg/` (which owns body-geometry evidence, not general repository
automation) and not under `governance/` (which defines constraints, not operational construction).

## 2. Reusable contracts harvested (NOT reinvented)

- **Constitutional input — `BodyEvidenceCandidate`**
  (`instrument_geometry/body/ibg/body_evidence_candidate.py`): governed dataclass carrying
  `candidate_id`, `authority` (`AuthorityStateContainer` → `authority_state`), **required**
  `provenance: ProvenanceRecord`, `confidence`, `review`. Enforces approved-authority + complete
  lineage before use. This is IBG-1's constitutional input (precedence #1).
- **Provenance + deterministic hash — `ProvenanceRecord`**
  (`governance/provenance_record.py`): `compute_provenance_hash()` (sha256[:16] over
  object_id/object_type/source_artifact/derivation_chain/transformation_stages),
  `has_complete_lineage()`, `get_last_transformation().actor`, `to_dict()`.
- **Review package — `ReviewPackage`** (`instrument_geometry/body/ibg/workflow/review_package.py`):
  `to_dict()`-serializable; IBG-1 **wraps** this, adding only repository-specific facts.
- **CBSP21 patch-packet system** (contract authority): format `cbsp21_patch_input_v1`, enforced by
  `scripts/ci/check_cbsp21_patch_input.py` + `scripts/cbsp21/check_patch_packet_format.py`; live
  examples under `.cbsp21/patches/*.json`. IBG-1 **emits this format via an adapter**, it does not
  fork a competing manifest ontology.

## 3. Genuinely missing (real build targets)

- `RepositoryChangeProposal` — absent.
- `DraftPullRequestPackage` — absent (no `gh`/GitPython PR-creation path exists in app code).
- **Worktree builder** — absent, and no harvest source; must be built greenfield under the full
  safety contract (**deferred to PR B**).

## 4. Decisions locked (owner-ratified for IBG-1)

1. **Patch manifest = CBSP21.** Use the existing `cbsp21_patch_input_v1` format via a thin
   adapter (`build_cbsp21_patch_packet()` / `validate_cbsp21_patch_packet()`, optional
   `CBSP21PatchPacketAdapter`). No competing public manifest type; no forked field names/coverage
   rules. The existing CBSP21 scripts remain contract authority.
2. **Package home = `services/api/app/ibg_repository/`** — dedicated, outside body/ibg and outside
   governance/. It *imports and consumes* the harvested contracts; it does not move or duplicate
   them.
3. **Input adapter = smallest possible `ProposalTargetBinding`** over `BodyEvidenceCandidate`
   (frozen dataclass). Evidence-owned fields are **derived from the candidate** and cannot be
   supplied/overridden by callers; repository-context fields belong to the binding. No new evidence
   ontology; no arbitrary-dict input.
4. **Review reuse** — `RepositoryProposalReviewPackage` is a narrow wrapper adding only
   repository facts (base revision, authorized paths, changed-file summary, CBSP21 packet
   reference/hash, proposed branch metadata, constitutional classification). The underlying IBG
   evidence review stays owned by `ReviewPackage`.

## 5. Constitutional boundaries (binding for all IBG-1 PRs)

IBG-1 moves IBG from observation to **proposal**, never to authority. No proposal may: claim
canonical authority; promote/relabel evidence authority state; change `AUTHORIZED_CANONICAL_APPROVERS`;
commit to `main`; push; create/merge a GitHub PR; mutate a production checkout; expose approver
identities; or bypass canonical process. Worktree creation (PR B) is temp-root-confined,
injected-runner, fail-closed. Draft-PR artifacts (PR C) are metadata only — no `gh`, no network.

## 6. Revised stacked delivery (grounded in the real tree)

- **PR A (this branch) — Contracts + deterministic serialization.** `ibg_repository/` package:
  `ProposalTargetBinding`, `RepositoryChangeProposal`, CBSP21 adapter, `RepositoryProposalReviewPackage`
  wrapper; deterministic JSON + hashing; tests; this archaeology doc as the first commit. No git
  execution, no router, no filesystem mutation, no network.
- **PR B — Isolated worktree builder.** Full safety contract + injected command-runner seam.
- **PR C — Integration boundary.** `DraftPullRequestPackage` (pure metadata) + router/service
  wiring + endpoint tests + architecture doc. No real GitHub mutation.

## 7. Producing-subsystem derivation (reviewable choice)

`ProposalTargetBinding.producing_subsystem` is derived from the candidate's provenance —
specifically the actor of the most recent transformation (`provenance.get_last_transformation().actor`),
which records who produced the current evidence state. This is deterministic and evidence-owned;
flagged here as a deliberate, reviewable derivation rule (not caller-supplied).
