# Pre-Governance Asset Recovery Archaeology

**Scan base:** `origin/main` @ `c8b0b549` · **Posture:** READ-ONLY forensics (classifies, recovers nothing, builds nothing) ·
**Companion to:** [`PRE_GOVERNANCE_SCAN_c8b0b549.md`](PRE_GOVERNANCE_SCAN_c8b0b549.md) (establishes the temporal/branch boundary; this establishes the recovery taxonomy and specimen matrix).

> **Governing principle.** *Age is not the disposition. Reachability is not the disposition. Being merged is not the
> disposition.* The disposition depends on **what engineering value survived** and **whether it is compatible with
> current authority**. A merged transition-era subsystem and an unmerged pre-governance branch can each require the
> same question — *does current architecture still agree with what this work believed it owned?*

> **Consolidation Lab boundary.** CONV-002's source, `DEV_ORDER_CONV-002_TIER_D_STRANDED_BRANCH_DISPOSITION.md`
> (2026-07-27), is held **Lab-side** (not in this repo). Per that order, only **TD-1** is a demonstrable production
> defect (it entered the production register as BR-042); TD-2/TD-3/TD-4 are decision/archival work under Lab
> Investigation 025. This audit **cites CONV-002, does not re-adjudicate it**, and does not treat new specimens as
> members of its TD set. Where evidence exists only Lab-side, the cell reads `EXTERNAL EVIDENCE REQUIRED` — the hole
> is never filled by inference.

---

## Epistemic-state legend (used in every cell)

| State | Meaning |
|---|---|
| **WITNESSED** | Verified directly against `origin/main` / reachable history this pass |
| **PARTIALLY WITNESSED** | Some evidence verified; a named sub-question remains unrun |
| **LEAD** | Plausible from records/memory; not yet verified against code this pass |
| **EXTERNAL EVIDENCE REQUIRED** | Necessary evidence exists only Lab-side or in another repo |
| **NOT YET ARCHAEOLOGICALLY TESTED** | Specimen identified; forensics not run |
| **UNKNOWN** | Identified as a question with no evidence either way |

---

## The four recovery families

- **I. STRANDED IMPLEMENTATION** — real implementation in history that never reached `main` and has no modern authority verdict. Highest recovery risk (may hold both value *and* obsolete authority).
- **II. PRESERVED TRANSITION-ERA IMPLEMENTATION** — reached `main`, but authored while governance was incomplete. Usually nothing to recover from git; what may be missing is the *authority explanation*. A retroactive constitutional witness, not a reconstruction.
- **III. PRESERVED / SET-ASIDE CAPABILITY** — real capability deliberately parked/deferred/superseded without evidence its engineering value was rejected. "Set aside" ≠ "worthless."
- **IV. ARCHITECTURAL DNA** — history that should not be resumed verbatim but carries decomposition/contracts/design knowledge current convergence should not have to rediscover.

---

## I. STRANDED IMPLEMENTATION

### I.1 Retopo / mesh-pipeline — `feature/mesh-pipeline-scaffold` + `feature/adapter-guide` — **WITNESSED (deep)**

| Field | Evidence |
|---|---|
| Branches | `feature/mesh-pipeline-scaffold` (`f6cf2911`) · `feature/adapter-guide` (`b05281d0`) |
| Shared base | **`60610cec`** — both fork from the same point (siblings, not a chain) |
| Ahead of main | 1 commit each |
| Size | mesh-scaffold: 14 files / +893 · adapter-guide: 12 files / +1499 |
| Namespace introduced | **`services/api/app/retopo/`** (`__init__.py`, `miq_adapter.py`, `qrm_adapter.py`, `run.py`; adapter-guide adds `util.py`) |
| Authority artifact touched | `contracts/schema_registry.json` (mesh-scaffold only) |
| Tests | **None** in either branch |
| External dependency | Instant Meshes / QuadRemesher (called via subprocess) — infrastructure-readiness factor |
| Governing decision record | **`docs/adr/ADR-002-mesh-pipeline-coupling.md` — Status: Accepted (2025-12-28)** |

**Current-main equivalents (the decisive nuance — this is a *partial* landing, not a clean strand):**
- **`app/retopo/` code namespace: ABSENT from `main`.** ← the actual stranded remainder.
- **`presets/retopo/` and `examples/retopo/`: PRESENT on `main`, byte-identical to the branches** — they rode in via the ingest-audit commit `f288065b`. The config/data survived; the code did not.
- **`contracts/schema_registry.json`: the branch's version is byte-identical to `main`'s.** This **corrects the boundary scan's earlier flag**: retopo is **not** an authority *conflict* on the registry — the registry already matches. The strand is the implementation, not a competing authority artifact.

**Sibling relationship:** the two branches are overlapping but **not** a superset/subset — mesh-scaffold carries the schema_registry + CI workflow + `validate_schemas.py`; adapter-guide carries `util.py` + `docs/RETOPO_ADAPTERS.md` and more adapter LOC. Any recovery must reconcile the two against each other first.

**Recovery class:** STRANDED IMPLEMENTATION. **Verdict — PROVISIONAL** (pending the deterministic authority check, per the amendment): the leading candidates are **DECLARED_EXTENSION_CANDIDATE** or **NOVEL_VALID** — because **ADR-002 (Accepted) already blesses the coupling layer as a sanctioned extension**, and no current subsystem visibly owns luthier-field-coupled retopology. It is **not** OBSOLETE_AUTHORITY (no decision superseded it) and **not** DUPLICATE (no main equivalent). What is missing is not a decision — it is the *landing* and a check of the ADR-era authority against the post-C0–C2 topology.

**Next archaeology:** (1) reconcile mesh-scaffold vs adapter-guide into one intended surface; (2) confirm no current subsystem silently absorbed field-coupled retopology; (3) run the authority check (deferred) against `authority_chain_registry.json`; (4) confirm the external-tool dependency is acceptable under current infra.

---

## II. PRESERVED TRANSITION-ERA IMPLEMENTATION

### II.1 BOE / IBG — **WITNESSED (deep)**

| Field | Evidence |
|---|---|
| Last pre-baseline commit | **`956533c6` (2026-05-12)** "docs(ibg): IBG-2A BOE integration boundary audit" (+ `70a0d3ee` IBG-2B, same day) — 6 days before baseline |
| Reachability | **On `main`** — `services/api/app/cam/translators/dxf/body_outline_translator.py` + test; full user docs |
| **Post-baseline re-governance (the key finding)** | The transition-era authorship was **followed by extensive constitutional-era governance**: `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md`, `IBG_CONSTITUTIONAL_RUNTIME_1A_COVERAGE_NOTE.md`, `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md`, `IBG_PROVENANCE_RATIFICATION_PACKET.md`, `IBG_BOE_BOUNDARY_MODEL.md`, `BOE_IBG_FAMILY_CONFLATION.md`, `GEOMETRY_AUTHORITY_DECOMPOSITION.md` |

**The retroactive witness is largely already performed.** The exact questions this family raises — *does IBG own what its transition contracts imply? are the BOE↔IBG boundaries represented by current authority? is BLOCKED_PROVENANCE still intentional?* — each have a **dedicated post-baseline governance document** (`IBG_BOE_BOUNDARY_MODEL.md` models the boundary; `BOE_IBG_FAMILY_CONFLATION.md` addresses the family-conflation question directly; the ratification timeline treats BLOCKED_PROVENANCE as an intentional, tracked state).

**Recovery class:** PRESERVED TRANSITION-ERA. **Verdict — PRESERVED + AUTHORITY LARGELY RECONCILED.** This is a valuable *positive* result: not "needs reconstruction," but "reconstruction already happened post-baseline."

**Residual (PARTIALLY WITNESSED):** whether the **BLOCKED_PROVENANCE ratification reached completion** (the *timeline* doc implies an in-progress process). That is a documented, trackable state to confirm — **not** a from-scratch witness. Confirm the ratification packet's terminal state; if ratified, this family closes with `NO REMEDIATION`.

### II.2 CAM translator / governed export (7A–7M, 6A–6I) — **PARTIALLY WITNESSED**

- **Known:** ~22 transition-zone commits, all on `main`; governed by `docs/architecture/CAM_GOVERNED_EXPORT_ARCHITECTURE.md` (Tier-2 domain authority per CLAUDE.md). Translator registry, export lifecycle, capability registry all landed.
- **Unknown (not run):** whether translator/export ownership, governed export paths, and router boundaries as authored under partial governance still match current authority; whether any duplicate export mechanism exists.
- **Elevated scrutiny:** CAM output reaches **physical manufacturing** — ambiguity here warrants more scrutiny than ordinary application duplication. But chronology alone is not a defect.
- **Recovery class:** PRESERVED TRANSITION-ERA. **Verdict — PRESERVE pending boundary spot-check.** **Next archaeology:** authority spot-check of translator vs export ownership and governed-export paths against `authority_chain_registry.json`; scan for duplicate export mechanisms and machine-facing/fence consumers.

### II.3 MRP (morphology / acoustic / CAD) — **PARTIALLY WITNESSED**

- **Known:** dense transition-era body; `docs/governance/MORPHOLOGY_RECONSTRUCTION_PLATFORM.md` is the Tier-2 MRP framework. Descendants span morphology, acoustic, CAD, and the BOE/IBG relationship.
- **Hypothesis (LEAD):** MRP became a **development umbrella** whose responsibilities later separated into multiple authorities — in which case the old MRP architecture is valuable **design provenance**, not a subsystem that should exist today as one production unit.
- **Recovery class:** PRESERVED TRANSITION-ERA. **Verdict — LINEAGE REVIEW.** **Next archaeology:** reconstruct `MRP → {morphology, acoustic, CAD} → BOE/IBG → current descendants`; determine which responsibilities separated and which were dropped.

---

## III. PRESERVED / SET-ASIDE CAPABILITY

### III.1 Photo vectorizer — **PARTIALLY WITNESSED**

- **Known:** present on `main` (`services/photo-vectorizer/`); decision/comparison records exist — `docs/VECTORIZER_MODE_COMPARISON.md`, `docs/PHOTO_VECTORIZER_ARCHITECTURE.md`, `docs/BLUEPRINT_VECTORIZER_ARCHITECTURE.md`. The immediate product path favored the Blueprint vectorizer; photo work was set aside (memory: Blueprint reader is canonical IBG/BEG intake).
- **Unknown (decisive, not yet read):** *why* — technically inferior? merely unnecessary for the immediate workflow? cost? IBG solved outline another way? infra not ready? experimental vs production-grade? These produce **radically different** modern dispositions (`POC_CANDIDATE` vs `RESEARCH_ONLY`).
- **Recovery class:** SET-ASIDE. **Verdict — REASSESS.** **Next archaeology:** read `VECTORIZER_MODE_COMPARISON.md` for the actual set-aside reason; this is a prime **Minimum Monetizable Capability** reassessment candidate.

### III.2 Feedback loops (Loop 1 / 2 / 3) — **PARTIALLY WITNESSED + EXTERNAL EVIDENCE REQUIRED**

The three loops have **different archaeological states** and must not share one verdict:
- **Loop 1 (intra-frame validation):** the runtime scale-validation gate (`validate_scale_before_export`) is **shipped and real** (CLAUDE.md confirms it is NOT part of the experimental loop and should be kept). → *implemented, live.*
- **Loop 2 (cross-image learning):** the strategy-cache loop was **never implemented**; Sprint B segmentation is a separate runtime improvement. → *design DNA, not stranded implementation.*
- **Loop 3 (user-correction retraining):** `FeedbackSystem` and `TrainingDataCollector` **exist but are NEVER CALLED** (CLAUDE.md). → *implemented → orphaned/disabled.*
- **The three-loop + AGE architecture** is **experimental, never approved, sandboxed** into `vectorizer-sandbox` (real embodiment `src/incubation/agentic_supervisor.py`) — **EXTERNAL EVIDENCE REQUIRED** for the sandbox embodiment.
- **Recovery class:** SET-ASIDE (mixed). **Verdict — COMPONENT-LEVEL REVIEW.** **Next archaeology:** per-loop — Loop 1 keep; Loop 2 assess hypothesis before any implementation; Loop 3 determine *why* orphaned (unsafe vs. missing-consumer vs. not-required) before treating as recovery candidate.

---

## IV. ARCHITECTURAL DNA

### IV.1 GEN work (vs emerging GFR) — **LEAD**

- **Known:** `app/generators/` (plural, present on `main`) and `app/art_studio/services/generators/` both exist; GFR (generator framework, catalog-not-registry) is the current architectural direction (memory: GFR-001 rulings; GEN-001 collision findings were BLOCKED/uncommitted).
- **Framing:** the question is **not** "can we finish GEN?" (GFR is the direction) — it is **"what did GEN discover about the generator problem that GFR should not have to rediscover?"** (capability taxonomy, factory/registry concepts, description/serialization models, generator identity, consumer expectations, known authority duplication, failed approaches).
- **Recovery class:** ARCHITECTURAL DNA. **Verdict — EXTRACT-BEFORE-GFR.** **Next archaeology:** produce the `GEN concept → preserved / implementation → superseded / authority → not-restored` mapping *before* GFR becomes authoritative.

### IV.2 Dead parallel origin — `copilot/bridge-luthiery-digital-fabrication` — **WITNESSED (structure) / DNA extraction NOT YET RUN**

- **Known:** 5 unmerged commits (2025-10-31); a **completely different `src/`-layout project** (`pyproject.toml`, `examples/`, `docs/`, `src/`) with **no shared namespace** with current `services/api/app/`. Commit "Implement complete Luthier's Toolbox — CAD/CAM/**Costing**/Tonewood modules" — the **Costing** module is a candidate unique concept (current production may lack a costing subsystem).
- **Recovery class:** ARCHITECTURAL DNA. **Verdict — BOUNDED DNA EXTRACTION, THEN DELETE.** Not a CONV-002 authority conflict (no shared namespace). **Next archaeology:** one bounded extraction pass (unique concepts/algorithms/UI/workflow/schemas/tests/docs — especially Costing); then `DNA EXTRACTED → deletion may proceed`. Do **not** attempt to merge the architecture.

### IV.3 Historical models — **NOT YET ARCHAEOLOGICALLY TESTED**

- **Known:** current models exist (`CANONICAL_PROVENANCE_MODEL.md`, `GEOMETRY_AUTHORITY_DECOMPOSITION.md`). Historical models whose runtime implementations disappeared are **not yet traced**.
- **Recovery class:** ARCHITECTURAL DNA. **Verdict — LINEAGE TRACE.** **Next archaeology:** establish `historical model → later model → current implementation`; the valuable output is often lineage evidence ("subsystem X descends from model Y, responsibility Z was intentionally dropped"), not code.

---

## Recovery matrix

Blank-equivalent cells use explicit epistemic states — incompleteness is recorded, never inferred away.

| Asset | Era | Reachability | Current equivalent | Authority state | Recovery family | Proposed disposition | Confidence |
|---|---|---|---|---|---|---|---|
| mesh-pipeline-scaffold | pre-gov | unmerged (code) / **presets landed** | `app/retopo` **absent**; presets present | ADR-002 **Accepted**; registry **not** in conflict | I. STRANDED | detector required; DECLARED_EXTENSION/NOVEL_VALID (provisional) | **WITNESSED** |
| adapter-guide | pre-gov | unmerged | overlaps mesh-scaffold (sibling) | same as above | I. STRANDED | reconcile the two cuts first | **WITNESSED** |
| BOE / IBG | transition | merged | active | **re-governed post-baseline** | II. PRESERVED-TRANSITION | preserve; confirm ratification terminal state | **WITNESSED** (residual PARTIAL) |
| CAM translator/export | transition | merged | active | Tier-2 governed; spot-check unrun | II. PRESERVED-TRANSITION | preserve pending boundary spot-check | **PARTIALLY WITNESSED** |
| MRP | transition | merged | descendants | umbrella hypothesis | II. PRESERVED-TRANSITION | lineage review | **PARTIALLY WITNESSED** |
| photo vectorizer | pre-gov | preserved | Blueprint preferred | intentionally set aside | III. SET-ASIDE | reassess (MMC candidate) — read reason | **PARTIALLY WITNESSED** |
| feedback loops | pre-gov | mixed (L1 live / L2 none / L3 orphaned) | partial | mixed; arch sandboxed | III. SET-ASIDE | component-level review | **PARTIAL** + **EXTERNAL EVIDENCE REQUIRED** |
| GEN | pre-gov | historical | GFR emerging | superseded direction | IV. DNA | extract before GFR authoritative | **LEAD** |
| copilot bridge | old | unmerged | none (no shared namespace) | parallel origin | IV. DNA | bounded DNA extract (Costing?) → delete | **WITNESSED** (extraction not run) |
| historical models | various | mixed | current models exist | lineage unknown | IV. DNA | lineage trace | **NOT YET TESTED** |

---

## Detector requirements (requirements only — no implementation, no ownership claimed)

This audit **specifies** what a repeatable adjudication instrument must do; it does **not** design or build it, and the build is **not authorized here**.

**R1 — Right question.** The detector must answer: *does a candidate change introduce, revive, duplicate, bypass, or alter an authority-bearing namespace in a way inconsistent with the current declared authority topology?* — **not** the near-useless "does this branch contain a directory main doesn't?"

**R2 — Machine-readable authority inputs (confirmed to exist).** It must read the current authority topology from production sources that already exist: `docs/governance/ontology/authority_chain_registry.json` and `docs/governance/governance_manifest.json` (and any successor the next sprint identifies). **Buildable ≠ authorized in this increment.**

**R3 — Non-duplication (mandatory pre-work).** Before any new tool is created, the next increment MUST inspect `scripts/governance/check_*.py` (the established convention — e.g. `check_routing_truth`, `check_semantic_sandbox_imports`, `check_capability_registry`, `check_sprint_namespace`) **and** `.cbsp21/patches/scan-ac3c96df-detector-sweep.json` (possible prior detector work). If an existing tool already owns part of this responsibility, **extend/consolidate — do not create another authority.**

**R4 — Verdict vocabulary (candidate, to be grounded against existing result conventions):** `NOVEL_VALID`, `DECLARED_EXTENSION`, `DUPLICATE_AUTHORITY`, `PARALLEL_AUTHORITY`, `OBSOLETE_AUTHORITY`, `AUTHORITY_BYPASS`, `NO_AUTHORITY_IMPACT`, `INSUFFICIENT_EVIDENCE`. The last is **essential** — a detector that cannot say *"insufficient evidence"* will manufacture false violations.

**R5 — Determinism + evidence.** Every verdict must be deterministic and accompanied by the evidence that produced it.

**R6 — Fixtures before dogfood.** Synthetic controls first (known-good unrelated namespace → `NO_AUTHORITY_IMPACT`; declared extension → `DECLARED_EXTENSION`; duplicate → `DUPLICATE_AUTHORITY`; two independent registries → `PARALLEL_AUTHORITY`; restored-superseded → `OBSOLETE_AUTHORITY`; ambiguous → `INSUFFICIENT_EVIDENCE`). **Only after** controls are trustworthy, dogfood on `feature/mesh-pipeline-scaffold`.

**R7 — Do not hard-code the retopo verdict.** The first retopo test must prove the detector can analyze it **deterministically**, not that retopo is a violation. Its specific verdict becomes a regression fixture **only after** authority evidence establishes what `retopo` actually represents — otherwise the tool is built to confirm the hypothesis. BOE (merged + current) is the paired control: the detector must evaluate *authority*, not treat BOE's age as suspicious.

---

## Amendment to the archaeological record

> **The inability to deliberately rerun the namespace/authority sanity check is promoted from a scan caveat to an
> independent tooling deficiency. CONV-002 branch findings remain provisional until that deficiency is corrected or an
> equivalent deterministic authority check is identified.**

> **The pre-governance archaeology therefore has two outputs: recovery evidence about historical engineering assets,
> and evidence-backed requirements for a repeatable namespace/authority detector capable of adjudicating those assets
> against current machine-readable authority topology.**

> **The detector requirement is technically actionable: current production contains machine-readable authority
> sources, including `docs/governance/ontology/authority_chain_registry.json` and
> `docs/governance/governance_manifest.json`. Detector implementation and ownership remain outside this audit.**

---

## Downstream use

**This evidence is suitable as an input to a future owner-authorized convergence, maintenance-recovery, GFR, or
production-readiness program. This audit does not create or authorize such a program.** It produces an evidence
baseline, bounded detector requirements, and an explicit next-archaeology step per unresolved specimen — nothing more.

**Guardrail compliance:** read-only. No production code, no branches, no Lab artifacts, and no governance authority
were modified. Deep specimens (retopo, BOE/IBG) are witnessed; all other specimens carry explicit epistemic states and
a named next-archaeology step. Every STRANDED/TIER-D-shaped finding remains **provisional** pending the deferred
authority check.
