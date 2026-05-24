# Multi-Repository Governance & Convergence Report

**Date:** 2026-05-24 (refreshed with git forensics + DO 77–82 verbatim ingestion)  
**Auditor role:** Senior Systems Architect / Governance Auditor  
**Repositories analyzed:** `luthiers-toolbox`, `tap_tone_pi`, `CAM-Assist-Blueprint`, `vectorizer-sandbox` (reference)  
**Primary handoffs:** `docs/SPRINT_ARCHITECTURE_HANDOFF_2026-05-24.md`, `docs/audit-sources/tap_tone_pi/docs/SPRINT_ARCHITECTURE_HANDOFF.md`, `docs/audit-sources/CAM-Assist-Blueprint/docs/SPRINT_ARCHITECTURE_HANDOFF_2026-05-24.md`, **`docs/handoffs/imports/constitutional_stabilization_do_77_82/`** (Dev Orders 77–82, verbatim)  
**Crosswalk:** [`docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md`](governance/CROSS_REPO_AUTHORITY_CROSSWALK.md)  
**Audit manifest:** [`docs/handoffs/imports/MANIFEST.md`](handoffs/imports/MANIFEST.md)  
**Assumption:** Six parallel sprint tracks executed without a single cross-repo integration charter; git forensics below verified 2026-05-24. Items marked **PENDING / external verification** were not confirmed on disk.

---

## Git forensics snapshot (2026-05-24)

| Repository | Branch | HEAD (short) | Upstream | Ahead | Behind | Latest commit (subject) |
|------------|--------|--------------|----------|-------|--------|-------------------------|
| **luthiers-toolbox** | `main` | `52259793` | `origin/main` | **2** | 0 | docs: rename sprint handoff to timestamped pattern |
| **tap_tone_pi** | `main` | `c910fcc` | `origin/main` | **27** | 0 | docs: add sprint architecture handoff document |
| **CAM-Assist-Blueprint** | `main` | `07e6c04` | `origin/main` | 0 | 0 | Merge PR #11 cam-a11-staged-package-review-queue-index |
| **vectorizer-sandbox** | `master` | `6390c26` | `origin/master` | 0 | 0 | Merge PR #14 research/wave-1n-governance-stratification |

**Working tree notes (PENDING cleanup):**

- **luthiers-toolbox:** Untracked audit artifacts (`MULTI_REPO_*`, `docs/handoffs/imports/`, constitutional folder at repo root), CAM 7U–7W implementation files, acoustics UI panels — not yet committed.
- **tap_tone_pi:** 27 commits **not pushed** — highest reconstruction/collaboration risk.
- **vectorizer-sandbox:** Untracked `docs/SPRINT_ARCHITECTURE_HANDOFF.md` locally.
- **Research spine:** Local `docs/research/` has 2 supporting files only; `origin/research/wave-1a-semantic-memory` exists remotely — **PENDING / external verification** for 1A/1B restore.

---

# 1. Executive Summary

Three repositories are evolving as a **distributed manufacturing-intelligence platform** with unusually strong **constitutional governance** discipline—but **without a shared governance kernel**. Each repo has independently matured:

| Repository | Maturity signal | Primary sprint thrust |
|------------|-----------------|------------------------|
| **luthiers-toolbox** | CI-blocking governance gate, DXF lifecycle matrix, runtime capability federation, CAM review queue (8C–8E), vectorizer sandbox separation, research memory (Waves 1A–1C) | **Runtime + CAM export legitimacy** |
| **tap_tone_pi** | ADR-0010–0012, machine-readable advisory contracts, epistemic taxonomy, export boundary tests, 2,596 tests | **Measurement vs guidance authority** |
| **CAM-Assist-Blueprint** | CAM-A0–A12 non-execution pipeline, JSON Schema authority blocks, 254 tests, portable strategy packages | **Strategy intent packaging (no G-code)** |

**Coherence assessment:** Architecturally, the repos are **philosophically aligned** (human review, non-execution defaults, provenance, fail-closed validation) but **operationally fragmented** (duplicate review-queue abstractions, incompatible authority vocabularies, no shared schema registry). Sprint coordination quality is **high within each repo** and **low across repos**.

**Governance maturity:** **High locally, medium globally.** Each repo can reconstruct its own sprint; none can reconstruct cross-repo contracts without inference.

**Major divergence risks:**

1. **Parallel “review queue” implementations** (CAM-A11/A12, luthiers 8E, IBG Workflow 1A review packages) with no shared IDs or decision semantics.
2. **Confidence / authority vocabulary collision** (`TypedConfidenceV1`, `ConfidenceDeclaration`, `rank_score`, `execution_authority_claim`, `AuthorityState`).
3. **DXF export governance** (luthiers lifecycle guards) vs **vectorizer R&D exclusions** (matrix marks photo-vectorizer as `R_AND_D_EXCLUDED`) vs **IBG BLOCKED_PROVENANCE**—three different export postures in one monorepo spine.
4. **Schema silos**—tap_tone `contracts/schemas/*.json`, CAM `schemas/*.schema.json`, luthiers Pydantic runtime models—no canonical cross-repo ontology.
5. **Accidental fork:** `vectorizer-sandbox` as cognition lab while luthiers-toolbox still documents vectorizer paths in lifecycle matrix as excluded—correct separation, but **reconstruction hazard** if engineers treat sandbox outputs as spine-default.

**Convergence opportunities:** A **shared authority & review vocabulary** (not a monorepo merge) would yield immediate payoff: epistemic status ↔ export lifecycle class ↔ strategy authority block mapping.

**Reconstruction readiness:** **Per-repo: strong (8.5–9.2/10). Cross-repo: moderate (6/10).** Knowledge loss risk concentrates at **integration boundaries** (IBG ↔ CAM ↔ CAM-Assist ↔ acoustic measurement imports).

---

# 2. Sprint Inventory & Classification

## 2.1 Sprint catalog

| ID | Repo | Objective | Systems touched | Governance | Schema | Infra | Architectural implication |
|----|------|-----------|-----------------|------------|--------|-------|---------------------------|
| **DO-008** | tap_tone_pi | Phase 1 demo / synthetic tap | capture pipeline | Low | New demo schemas | — | Measurement instrument baseline |
| **Gov Audit** | tap_tone_pi | Headers, import boundaries, debris cleanup | agent/, core/, ci/ | **High** | — | CI scripts | MEASUREMENT vs DECISION SUPPORT classes |
| **DO-78** | tap_tone_pi | AGE constitutional contract | agentic/contracts, ci language guard | **High** | Additive directive fields | CI | Guidance ≠ evidence |
| **DO-81** | tap_tone_pi | Measurement authority + epistemic taxonomy | docs ADR-0011/12, matrix | **High** | Doctrine-first | Doc tests | Provenance states formalized |
| **PR #17–19** | luthiers-toolbox | Unified governance runner, inventory, **blocking gate** | `scripts/governance/` | **Critical** | governance_inventory JSON | CI tiers | Single policy execution path |
| **PR #24** | luthiers-toolbox | Complexity reduction + safety decorators | CAM inlay/rosette | Medium | — | — | Safer CAM paths |
| **Sandbox migration** | luthiers-toolbox | Tier A → vectorizer-sandbox, PR-1/2/3 | photo-vectorizer, blueprint-import | **High** | — | External repo | Cognition/runtime split |
| **Runtime Boundary 1A–2G** | luthiers-toolbox | DXF lifecycle inventory + guards | routers, cam services | **High** | DxfLifecycleContext | Guards | Export legitimacy layer |
| **MRP-5M–5Y** | luthiers-toolbox | Runtime capability federation | runtime_capabilities/* | **High** | FederatedCapability | Manifest scripts | Capability gate before execution |
| **DO 7Y–7Z, 8A** | luthiers-toolbox | Federation CI, baseline freeze, expansion gate | governance docs | **High** | — | CI | Post-freeze discipline |
| **DO 8C–8E** | luthiers-toolbox | Review UX + CI + **review queue routing** | app/cam/review_* | **High** | Pydantic invariants | REST routers | Human attention routing |
| **Research 1A–1C** | luthiers-toolbox | Semantic memory, trace, artifact quality | docs/research/ | Medium (docs) | research_index.json | — | Institutional memory (non-authoritative) |
| **CAM-A0–A12** | CAM-Assist-Blueprint | Non-execution strategy pipeline | scripts/, schemas/ | **High** | JSON Schema authority blocks | CLI | Portable strategy packages |
| **DO 77** | tap_tone_pi + luthiers | Governance consolidation audit | tap_tone CI/docs; luthiers `TAP_TONE_PI_GOVERNANCE_CONSOLIDATION_AUDIT.md` | **High** | — | — | Structural (tap_tone) + lexical (luthiers) complement |
| **DO 78** | tap_tone_pi | AGE constitutional contract | ADR-0010, AGE_CONTRACT.md | **High** | — | CI | Four orthogonal authority domains |
| **DO 79–80** | tap_tone_pi | Advisory presentation boundary + patches | html_report.py, guidance/engine.py | **High** | — | — | Presentation-layer authority governance |
| **DO 81** | tap_tone_pi | Measurement authority + epistemic taxonomy | ADR-0011/12, epistemic matrix | **High** | Doctrine-first | Analysis memo only | Seven epistemic categories (constitutional) |
| **DO 82** | tap_tone_pi | Constitutional mode transition | CONSTITUTIONAL_CONTINUATION_NOTICE.md | **High** | — | — | Conditional stabilization; escalation triggers |

## 2.2 Sprint dependency map (conceptual)

```text
                    ┌─────────────────────┐
                    │  CAM-A0 Foundation  │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
  CAM-A1..A5            luthiers PR #17-19      tap_tone Gov Audit
  Strategy pack         Governance gate          Instrument headers
         │                     │                     │
         ▼                     ▼                     ▼
  CAM-A6..A12           MRP-5 + DXF guards       DO-78/81 ADRs
  Archive/review        Runtime spine 8C-8E      Epistemic matrix
         │                     │                     │
         └─────────── NO formal cross-repo edges ───┘
                               │
                    (future integration layer)
```

## 2.3 Sprint overlap matrix

| Concern | tap_tone_pi | luthiers-toolbox | CAM-Assist-Blueprint |
|---------|-------------|------------------|----------------------|
| Human review required | Export + UI tests | 8C/8E invariants | `requires_human_review` |
| Non-execution | N/A (measurement) | 8E + capability federation | Core invariant |
| Review queue | — | ReviewQueueItem (8E) | index_staged_packages (A11) |
| Review decision record | — | ReviewDecisionRecord (8E) | record_review_decision (A12) |
| Confidence typing | TypedConfidenceV1 | ConfidenceDeclaration + rank_score | — |
| CI language/authority guards | check_guidance_language | check_all.py governance | validate authority in JSON |
| Provenance | Epistemic status | DxfLifecycleContext, runtime provenance | provenance blocks in manifest |

## 2.4 Governance interaction matrix

| Mechanism | Enforced in CI? | Blocks merge? | Cross-repo shared? |
|-----------|-----------------|---------------|-------------------|
| luthiers `check_all.py` | Yes | Yes (authority chain) | No |
| tap_tone language guard | Partial (non-strict) | Optional | No |
| tap_tone export boundary tests | Yes | Yes | No |
| CAM schema validation | Yes (pytest) | Yes | No |
| DXF lifecycle matrix validator | Yes | Yes | No |
| Research doc structure tests | Yes | Unknown tier | No |

---

# 3. Repository Architecture Comparison

## 3.1 Shared architectural concepts (convergent intent)

| Concept | tap_tone_pi | luthiers-toolbox | CAM-Assist-Blueprint |
|---------|-------------|------------------|----------------------|
| **Human authority** | Measurement instrument; guidance advisory | Review queue routes attention, not decisions | Explicit non-execution |
| **Fail-closed validation** | Schema + export guards | Governance gate + lifecycle guards | Reject invalid packages |
| **Provenance** | Epistemic status taxonomy | Lifecycle + runtime provenance | Manifest provenance |
| **Layered gates** | capture → analysis → export | validation → admission → capability → execution | validate → assemble → stage → decide |
| **Documentation as law** | ADRs + constitutional contract | docs/governance + research memory | docs/strategy_packages |

## 3.2 Duplicated systems (accidental parallel evolution)

| Domain | Instances | Risk |
|--------|-----------|------|
| Review queue | CAM `REVIEW_QUEUE.md`, luthiers `ReviewQueueRegistry`, IBG `review_package.json` | Incompatible operator workflows |
| Review decision | CAM `review_decision_record.schema.json`, luthiers `ReviewDecisionRecord` | Semantic drift on “approve” meaning |
| Authority blocks | 3+ JSON/Pydantic patterns | Integration bugs when linking repos |
| CI governance runners | 3 separate script ecosystems | Duplicated policy logic |
| “Confidence” fields | float + typed + heuristic + rank_score | Silent authority inheritance |

## 3.3 Conflicting abstractions

| Conflict | Description |
|----------|-------------|
| **Measurement vs geometry authority** | tap_tone: “capture integrity ≠ acoustic truth.” luthiers: DXF export may be `COMPAT_ONLY` or `BLOCKED_PROVENANCE`. CAM: strategy never executes. **No mapping table exists.** |
| **Review routing vs review package** | 8E: “routing may not make decisions.” IBG Workflow 1A: emits review package with gate-blocked candidates. **Unclear if CAM-Assist approved strategies feed luthiers queue.** |
| **Advisory vs ranked candidate** | tap_tone forbids guidance in measurement exports. luthiers `rank_score` becomes `confidence_value` on BodyEvidenceCandidate. **Rank ≠ confidence canonization** is documented in research layer but not unified in code vocabulary. |

## 3.4 Incompatible schemas / naming

| Area | tap_tone_pi | luthiers-toolbox | CAM-Assist-Blueprint |
|------|-------------|------------------|----------------------|
| ID format | workflow_id, schema v1 | `rqi-{uuid12}`, namespaced capability IDs | `operation_type:source_spec_id` |
| Version fields | schema file names | manifest hash, deterministic_queue_hash | manifest_version, record_version |
| Authority enum | AuthorityClass, GuidanceScope | AuthorityState, ReviewStatus | authority JSON block booleans |

## 3.5 Reconstruction hazards

| Hazard | Why it hurts |
|--------|--------------|
| **vectorizer-sandbox externalization** | Tier A code + eval live outside main repo; lifecycle matrix still lists R&D paths |
| **Missing handoffs (MRP 5C, 5D, 5I–5L, 5U, 5W)** | luthiers runtime spine gaps |
| **1A/1B research files partial on disk** | Wave 1C cross-links may point to missing docs in some checkouts |
| **8E in-memory registries** | Restart loses queue—documented but easy to miss in ops |
| **13 non-strict language guard findings** | tap_tone authority drift in messages |

---

# 4. Governance Implementation Audit

## 4.1 Schema governance

| Repo | Mechanism | Strength | Gap |
|------|-----------|----------|-----|
| tap_tone_pi | JSON Schema in `contracts/schemas/` | Versioned files, tests | Epistemic status not yet in all export schemas |
| CAM-Assist-Blueprint | JSON Schema + jsonschema CLI | Clear authority blocks | No ADR layer; inline docs only |
| luthiers-toolbox | Pydantic models + governance inventory | Model validators enforce 8E invariants | No single schema export for external consumers |

**Gap:** No **cross-repo schema registry** or shared `$id` namespace.

## 4.2 Commit / branch governance

| Repo | Pattern | Assessment |
|------|---------|------------|
| tap_tone_pi | PR-themed commits (78A–81D), 27 commits ahead of origin | Strong narrative; push debt |
| luthiers-toolbox | PR #17–37, feature branches merged | Mature GitHub flow |
| CAM-Assist-Blueprint | `cam-a<N>-slug` branches | Clean order-per-branch |

**Drift:** tap_tone **27 unpushed commits**—reconstruction risk for collaborators.

## 4.3 Documentation governance

| Repo | Index | Machine-readable |
|------|-------|------------------|
| luthiers-toolbox | `build_governance_inventory.py` | Yes |
| tap_tone_pi | ADR series + matrix | Doc tests |
| CAM-Assist-Blueprint | docs/strategy_packages/* | INDEX.md generators |

**Duplication:** Three documentation constitutions; research layer (`docs/research/`) is **non-authoritative** but essential for vectorizer/IBG—linked via [`RESEARCH_LAYER_GOVERNANCE_ENTRY.md`](governance/RESEARCH_LAYER_GOVERNANCE_ENTRY.md).

## 4.4 Testing governance

| Repo | Tests | Governance-specific |
|------|-------|---------------------|
| tap_tone_pi | 2,596 | constitutional_docs, export boundary, language guard |
| luthiers-toolbox | 223+ API + 72 spine + 138 review UX/queue | regression guard (11), lifecycle (33) |
| CAM-Assist-Blueprint | 254 | per-script pytest |

**Gap:** No cross-repo contract tests (e.g., CAM manifest → luthiers capability import).

## 4.5 CI/CD governance

| Repo | Entry point | Tiers |
|------|-------------|-------|
| luthiers-toolbox | `scripts/governance/check_all.py` | precommit / ci / nightly |
| tap_tone_pi | `ci/check_*.py` + pytest | strict optional |
| CAM-Assist-Blueprint | pytest only | single tier |

## 4.6 Procedural drift

| Drift | Evidence |
|-------|----------|
| Strictness mismatch | tap_tone language guard non-strict vs luthiers blocking gate |
| Research vs governance | luthiers research waves document invariants not encoded in shared types |
| Export posture split | Same monorepo: governed routers vs R_AND_D_EXCLUDED vectorizer vs BLOCKED_PROVENANCE IBG |

---

# 5. Schema Drift & Contract Analysis

## 5.1 Drift hotspots

| Contract | Drift type | Severity |
|----------|------------|----------|
| Review decision semantics | CAM `approve_for_downstream_cam` vs 8E `mark_reviewed` vs IBG gate block | **High** |
| Confidence representation | 4+ representations | **High** |
| Provenance records | Epistemic status vs DxfLifecycleContext vs strategy provenance | **Medium** |
| Package/manifest IDs | Incompatible formats | **Medium** |
| Geometry exports | DXF lifecycle vs strategy JSON (no shared geom schema) | **Low** (domain split) |

## 5.2 Canonical schema recommendations

1. **`shared-authority-v1`** (new spec, not code yet): boolean invariants + enum for `authority_class` aligned to:
   - tap_tone: `MEASUREMENT | DECISION_SUPPORT | …`
   - luthiers: `AuthorityState` + 8E flags
   - CAM: authority block triple

2. **`review-decision-v1`**: unify decision types with explicit **downstream effects** matrix (what each decision may unlock).

3. **`confidence-v1`**: require `domain` + `value` + `source` (tap_tone TypedConfidence pattern) everywhere confidence appears.

4. **`epistemic-status-v1`**: map tap_tone ADR-0012 states to luthiers export lifecycle classes and CAM manifest fields.

## 5.3 Migration sequencing

| Phase | Action |
|-------|--------|
| 1 | ~~Document crosswalk table~~ **Done** — `docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md` (2026-05-24) |
| 2 | Add optional `epistemic_status` to luthiers review UX artifacts (additive) |
| 3 | CAM manifest: optional import of shared authority enum |
| 4 | Deprecate bare `confidence: float` in tap_tone directives (already planned) |

---

# 6. System Dependency & Coupling Analysis

## 6.1 Dependency map (high level)

```text
[Photo/Blueprint Vectorizer] ──► DXF artifacts ──► [IBG Workflow 1A]
        │                                              │
        │ (vectorizer-sandbox R&D)                     ▼
        │                                    BodyEvidenceCandidate
        │                                              │
[CAM Runtime Spine] ◄── capability federation ◄── review queue 8E
        │
        ▼
   DXF exports (guarded) ──► fabrication prep

[CAM-Assist-Blueprint] ── strategy packages ──?──► (integration TBD)

[tap_tone_pi] ── measurement exports ──?──► toolbox import (Predicted / external)
```

## 6.2 Coupling classification

| Link | Type | Notes |
|------|------|-------|
| luthiers CAM ↔ DXF guard | **Intentional** | Core production path |
| luthiers IBG ↔ vectorizer | **Intentional** | Adapter boundary (`artifact_body_evidence_adapter.py`) |
| luthiers ↔ vectorizer-sandbox | **Intentional** | Import gate CI |
| luthiers 8E ↔ CAM-Assist A12 | **Accidental / undefined** | Parallel review decision models |
| luthiers research ↔ governance | **Intentional** | Research non-authoritative |
| tap_tone ↔ luthiers | **Latent** | Toolbox target = Predicted import only |

## 6.3 Dangerous coupling

| Coupling | Failure mode |
|----------|--------------|
| `rank_score` → `confidence_value` on candidates | Operators treat rank as approval |
| Ungoverned vectorizer path if matrix stale | Silent unguarded DXF save |
| CAM “approve_for_downstream_cam” without luthiers gate | False belief of machine authorization |
| Sandbox ML confidence leaking to spine | Constitutional violation (research warns; grep gate partial) |

---

# 7. Reconstruction Readiness Assessment

| Dimension | tap_tone_pi | luthiers-toolbox | CAM-Assist-Blueprint | Cross-repo |
|-----------|-------------|------------------|----------------------|------------|
| **Reconstruction risk** (lower better) | 1.0 / 10 | 1.5 / 10 | 1.0 / 10 | **4.0 / 10** |
| **Governance maturity** | 9 / 10 | 8.5 / 10 | 8 / 10 | **6 / 10** |
| **Architecture stability** | 9 / 10 | 8 / 10 | 9 / 10 | **6.5 / 10** |

**Scores (aggregate):**

| Metric | Score (0–10) |
|--------|----------------|
| Reconstruction readiness (per-repo avg) | **8.8** |
| Cross-repo convergence readiness | **6.0** |
| Governance maturity (global) | **6.5** |
| Architecture stability (global) | **7.0** |

**Knowledge loss hotspots:** Missing luthiers handoffs; unpushed tap_tone commits; research doc fragmentation; undefined CAM→luthiers integration.

---

# 8. Divergence & Collision Detection

| # | Conflict | Risk | Future failure mode | Remediation |
|---|----------|------|---------------------|-------------|
| 1 | Three review queue models | High | Operator runs wrong CLI/API | Publish unified **Review Routing Spec**; adapters per repo |
| 2 | Confidence vocabulary | High | Auto-approval from ML/rank | Mandate TypedConfidence pattern; audit rank_score usage |
| 3 | IBG BLOCKED_PROVENANCE vs guarded CAM exports | High | IBG DXF bypasses lifecycle story | Complete provenance ratification; matrix update |
| 4 | vectorizer R&D excluded vs production paths | Medium | Copy sandbox code to services | Keep import gate; sync research + matrix |
| 5 | 8E in-memory queue | Medium | Lost reviews on deploy | Persist queue or document ephemeral nature in ops runbook |
| 6 | tap_tone language guard non-strict | Medium | Guidance claims truth | Cleanup 13 findings; enable strict CI |
| 7 | CAM / luthiers duplicate “human_review_required” | Low | Doc-only confusion | Crosswalk table |
| 8 | Research waves vs governance freeze | Low | Engineers treat research as law | Keep README authority banner |

---

# 9. Convergence Strategy

## Phase 0 — Stabilize locally (Week 1–2)

- Push tap_tone 27 commits; luthiers keep regression guard green.
- Complete luthiers missing handoffs as OBSERVATION entries.
- Restore full `docs/research/` 1A/1B spine if fragmented in checkout.

## Phase 1 — Vocabulary convergence (Week 2–4, docs-only)

- Create **`CROSS_REPO_AUTHORITY_CROSSWALK.md`** in luthiers-toolbox `docs/governance/` (link from tap_tone + CAM README).
- Map: epistemic status ↔ lifecycle class ↔ CAM authority block ↔ 8E invariants.
- Map review decisions: CAM A12 ↔ luthiers 8E ↔ IBG gate (explicitly **what each does NOT authorize**).

## Phase 2 — Contract boundaries (Month 2)

- Define **`integration-v1`** JSON Schema for:
  - CAM strategy package handoff to luthiers review queue (optional import)
  - tap_tone `viewer_pack_v1` import markers (Predicted / Externally-Sourced)
- No shared code monolith—**schema-only** package or git submodule `platform-contracts/`.

## Phase 3 — CI harmonization (Month 2–3)

- Shared pytest module for authority invariant tests (parameterized per repo).
- luthiers: add manifest drift detection (already noted as follow-up).
- tap_tone: strict language guard in CI.

## Phase 4 — Runtime integration (Month 3+, gated)

- Single **Review Router API** in luthiers that accepts CAM-Assist staged package metadata (read-only index).
- IBG review package fields aligned with 8C artifacts (research Wave 1C guide → desired fields).
- Only after provenance ratification for IBG DXF paths.

## Stabilization milestones

| Milestone | Definition of done |
|-----------|-------------------|
| M1 | Crosswalk doc ratified by owners |
| M2 | All repos CI green on authority invariant tests |
| M3 | CAM→luthiers integration spec (even if not implemented) |
| M4 | IBG provenance unblocked in lifecycle matrix |

---

# 10. Canonical Governance Framework (Draft Constitution)

## 10.1 Repository standards

- Every repo maintains: **README authority statement**, **governance index**, **CI entry script**, **handoff at sprint end**.
- External cognition (sandbox) never default-imported without graduation record.

## 10.2 Schema standards

- All persisted artifacts: `schema_version`, `record_type`, `authority` block, `provenance`.
- Confidence must use **domain + value + source** when representing decision relevance.
- Breaking changes require ADR (tap_tone style) or Dev Order record (luthiers style) or CAM order doc.

## 10.3 Documentation standards

- **Governance** = operational authority; **Research** = memory only; **Handoffs** = sprint narrative.
- Cross-links required when duplicating concepts (1B/1C pattern).

## 10.4 Sprint reporting standards

- Handoff template: executive summary, commit themes, schema delta, reconstruction score, next actions.
- Cross-repo section mandatory when touching integration surfaces.

## 10.5 Architectural review process

- Changes to authority invariants require: governance inventory update + invariant tests + handoff.
- Cross-repo changes require crosswalk update.

## 10.6 Migration / versioning

- Additive-first; deprecations with timeline; no silent authority promotion.

## 10.7 Testing requirements

- Authority tests non-optional for merge.
- Deterministic manifest/index outputs where applicable.

## 10.8 Dependency approval

- New cross-repo dependency requires explicit integration Dev Order.

## 10.9 Commit / branch conventions

- Feature branch per dev order; PR merge to main; handoff on sprint boundary.

---

# 11. Recommended Immediate Actions

| Priority | Action | Repo | Risk addressed |
|----------|--------|------|----------------|
| **P0** | Push tap_tone 27 commits to origin | tap_tone_pi | Reconstruction / collaboration |
| **P0** | Keep luthiers capability regression guard + governance gate green | luthiers-toolbox | Bypass vectors |
| **P0** | Ratify IBG provenance model or document BLOCKED_PROVENANCE timeline | luthiers-toolbox | Export legitimacy gap |
| **P1** | ~~Author `CROSS_REPO_AUTHORITY_CROSSWALK.md`~~ **Done** (2026-05-24); ratify with repo owners | luthiers-toolbox (coord) | Schema/semantic drift |
| **P1** | Restore complete `docs/research/` 1A/1B if missing | luthiers-toolbox | Research reconstruction |
| **P1** | Enable tap_tone language guard `--strict` after 13-fix cleanup | tap_tone_pi | Guidance authority |
| **P2** | CI manifest drift detection | luthiers-toolbox | Capability federation drift |
| **P2** | Document CAM→luthiers integration as **TBD** with explicit non-goals | all | False integration assumptions |
| **P2** | ~~Add governance inventory entry for research layer~~ **Done** (2026-05-24) | luthiers-toolbox | Fragmentation |

---

# 12. Long-Term Architectural Recommendations

1. **`platform-contracts`** repository (schemas + invariant tests only)—consumers: all three repos.
2. **Extract review routing** into shared spec implemented once in luthiers, CLI adapters in CAM-Assist.
3. **Unified provenance service** for DXF + strategy packages + measurement imports (read-only lineage API).
4. **Governance dashboard** aggregating check_all, tap_tone ci scripts, CAM pytest summary.
5. **Domain separation:** tap_tone = acoustic measurement; CAM-Assist = strategy intent; luthiers = geometry/runtime/CAM execution prep; vectorizer-sandbox = cognition R&D.
6. **Research waves** continue as institutional memory—promote findings to governance via explicit Dev Orders only.

---

# 13. Open Questions & Unknowns

| Question | Status |
|----------|--------|
| Content of Dev Orders 77–82 | **Resolved** — ingested verbatim from `docs/handoffs/imports/constitutional_stabilization_do_77_82/` |
| Whether CAM-Assist approved packages feed luthiers 8E today | **PENDING / external verification** — no wire-up found on disk |
| `review_decision_record.schema.json` in CAM-Assist | **Resolved** — on branch `cam-a12-review-decision-record`; merge to `main` **PENDING** |
| vectorizer-sandbox release tags | **PENDING** — `pending tag` in research docs |
| tap_tone 27 unpushed commits | **Verified** ahead count; push **PENDING** |
| Production deployment topology | Inferred dev/CI focus |
| Ownership of cross-repo integration | **Unassigned**—recommended luthiers platform team |
| Research 1A/1B/1C spine on local disk | **Restored** 2026-05-24 (1A/1B from remote; 1C **PENDING** if on separate branch) |
| tap_tone ↔ luthiers Toolbox import path | Predicted/epistemic import only per matrix |

---

# Appendix A — Convergence Readiness Scorecard

| Metric | Score |
|--------|-------|
| **Repositories analyzed** | 3 (+ vectorizer-sandbox referenced) |
| **Sprint tracks analyzed** | 6+ (DO-78/81, Gov audit, luthiers MRP+8C-E, CAM-A0–12, research 1A–1C, sandbox migration) |
| **Governance conflicts identified** | 8 major |
| **Schema drift severity** | **Medium–High** (no shared kernel) |
| **Convergence readiness score** | **6.0 / 10** |
| **Highest risk conflicts** | Review queue duplication; confidence/authority collision; IBG provenance block vs guarded CAM DXF |

---

# Appendix B — Highest-Impact Remediation (Executive)

1. **Do not merge review systems without a crosswalk**—CAM A12, luthiers 8E, and IBG packages are parallel, not equivalent.
2. **Treat rank_score and ML confidence as non-authoritative everywhere**—align with tap_tone TypedConfidence and research invariants.
3. **Close IBG BLOCKED_PROVENANCE** before marketing “governed geometry pipeline” externally.
4. **Coordinate vocabulary before code integration**—schemas first, shared library second.
5. **Maintain sandbox separation**—documented in matrix, research, and import gate must stay aligned.

---

# Appendix C — Audit infrastructure (2026-05-24)

| Asset | Path |
|-------|------|
| Audit manifest | `docs/handoffs/imports/MANIFEST.md` |
| Constitutional DO 77–82 imports | `docs/handoffs/imports/constitutional_stabilization_do_77_82/` |
| Junction: tap_tone_pi | `docs/audit-sources/tap_tone_pi/` |
| Junction: CAM-Assist-Blueprint | `docs/audit-sources/CAM-Assist-Blueprint/` |
| Junction: vectorizer-sandbox | `docs/audit-sources/vectorizer-sandbox/` |
| Authority crosswalk | `docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md` |
| Research layer governance entry | `docs/governance/RESEARCH_LAYER_GOVERNANCE_ENTRY.md` |
| Research wave index | `docs/research/RESEARCH_WAVE_INDEX.md` |

---

*Report generated: 2026-05-24; refreshed with git forensics + DO 77–82 verbatim ingestion*  
*Location: `docs/MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md`*  
*Next review trigger: first cross-repo integration Dev Order, IBG provenance ratification, or tap_tone push to origin*
