# Runs + Advisories/Explanations Design Note

**Status:** Canonical (implementation-aligned)
**Audience:** Core devs, maintainers, reviewers
**Purpose:** Explain why the "suggest-and-attach" architecture is stable and extensible.

---

## Problem We're Solving

We want RMOS to attach "advisories" and "explanations" to a Run in a way that is:

- safe (does not bypass governance)
- auditable (immutable records)
- scalable (handles large payloads)
- flexible (supports multiple AI providers, or no AI at all)
- future-proof (sync now, async later without schema churn)

---

## Key Design Choice

### Runs store references; attachments store payloads.

A RunArtifact stores only:
- small inline preview fields (optional)
- append-only references to external assets (advisory_inputs)
- provenance (request_id, engine_id/version, etc.)

The canonical advisory/explanation payload is stored as a **content-addressed attachment** (sha256).

This makes payload storage:
- immutable by default
- cheap to dedupe
- easy to verify
- safe to diff and audit

---

## Why This Is Future-Proof

### 1) It prevents coupling core workflow to AI internals
Runs are workflow truth (what happened).
AI is advisory (how we might describe or explain it).

By storing AI output as an attachment:
- we can change providers/models/prompts without breaking Run schema
- we can attach manual explanations even with no AI
- we preserve governance boundaries: AI never becomes execution authority

### 2) It supports "sync now" and "async later" without rework
The API can return:
- `READY` for synchronous generation
- `PENDING` for asynchronous jobs later

The run only needs:
- `explanation_status`
- `advisory_inputs[]` referencing the eventual payload

Async is just a new producer for the same stored asset.

### 3) It scales to large payloads safely
LLM explanations can be long.
Keeping them out of the Run JSON prevents:
- bloated run records
- heavy diff payloads
- accidental UI performance regressions

The UI can fetch attachments on-demand.

### 4) It makes audit and reverse lookup trivial
Each advisory asset stores `run_id` and `request_id`.
Each run stores the advisory sha256.

This supports:
- "show me all advisories for this run"
- "show me which run produced this advisory"
- "diff run A vs run B and include advisory lineage"
without inventing a separate indexing subsystem prematurely.

### 5) It preserves determinism where it matters
The run and its gating/feasibility are deterministic and enforced.
Advisories are:
- optional
- non-authoritative
- traceable

That is the correct safety posture.

---

## The Orchestrator Endpoint

### `POST /api/runs/{run_id}/suggest-and-attach`

Responsibilities:
1. load run
2. optionally generate explanation (sync MVP)
3. store canonical payload as attachment (sha256)
4. append an AdvisoryInputRef to the run
5. set small preview fields (optional)

Non-responsibilities:
- no feasibility decisions
- no toolpath authority
- no client-trust of safety outcomes

The router orchestrates; engines compute; attachments persist.

---

## Extension Points

Planned extensions that do NOT require schema rewrite:
- async explanation jobs
- multiple explanation styles (operator/executive/debug)
- provider metadata and replay support
- advisory indexing and dashboards
- richer payload formats (sections, citations, token usage)

---

## Final Rule

> Runs are authoritative history.
> Advisories/explanations are optional, attachable assets.

This boundary is what makes the system robust.
