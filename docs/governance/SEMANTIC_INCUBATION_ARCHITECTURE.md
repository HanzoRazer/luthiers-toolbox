# Semantic Incubation Architecture

**Date:** 2026-05-20  
**Status:** APPROVED DIRECTION — execution via `VECTORIZER_SANDBOX_MIGRATION_PLAN.md`  
**Authority:** Tier 2 domain governance (VECTOR); complements constitutional runtime (IBG/MRP)

---

## 1. Core principle

```text
sandbox discovers
production ratifies
```

This is **controlled semantic incubation** — not merging unstable sandbox code back into the operational spine.

| Pattern | Status |
|---------|--------|
| Experiments silently mutating production | **Retired** |
| Sandbox capability → evidence → provenance → intake → production | **Required** |
| Bulk restore / copy-paste import from sandbox | **Forbidden** |

---

## 2. Three engineering layers (now separable)

The repository has reached **constitutional stabilization** (canonical routes, runtime authority gates, provenance, deterministic tooling). The stack can split by discipline:

| Layer | Role | Primary home |
|-------|------|--------------|
| **Extraction runtime** | Deterministic evidence generation (contours, scale, DXF bytes) | `luthiers-toolbox` — `refined`, `edge_to_dxf`, orchestrators |
| **Semantic cognition** | Meaning inference, topology, occupancy, multi-agent interpretation | `vectorizer-sandbox` — experimentation without production guarantees |
| **Constitutional runtime** | Authority, provenance, review, intake gates | `luthiers-toolbox` — IBG, governance manifests, `ibg_intake_gate` |

Earlier, all three coexisted in one tree → regressions, archaeology spirals, silent fallbacks, semantic collapse.

---

## 3. Two-repository equilibrium

| Environment | Engineering discipline | Optimizes for |
|-------------|------------------------|---------------|
| **`luthiers-toolbox`** | Semantic **runtime spine** | Determinism, reviewability, provenance, governance constraints, trusted execution |
| **`vectorizer-sandbox`** | Semantic **cognition layer** | Experimentation, heuristics, topology intelligence, morphology reasoning, adaptive extraction |

**Existing repo:** https://github.com/HanzoRazer/vectorizer-sandbox (private)  
**Local clone path:** sibling `../vectorizer-sandbox/` (see `local/README.md`; e.g. `Downloads/vectorizer-sandbox` next to this repo)  
**Do not create** a separate `vectorizer-archaeology` graveyard repo — re-home archaeological lineage **into** the sandbox as `src/semantic/` and `src/archaeology/`.

The sandbox is **not** a code graveyard. It is a **semantic R&D laboratory** that also preserves cognitive/grid historical lineage.

---

## 4. Constitutional graduation bridge

Nothing moves from sandbox to production **directly**. Capabilities graduate only through:

```text
sandbox capability
  → evidence validation (fixtures, golden comparisons, failure taxonomy)
  → provenance wrapping (source SHA, experiment ID, reviewer)
  → deterministic instrumentation (telemetry, bounded outputs, fail-closed)
  → governance review (ADR, lifecycle registry update)
  → intake gate (IBG / Blueprint Reader contract)
  → production adoption (new implementation or flag behind ACTIVE gate)
```

| Graduation artifact | Location |
|---------------------|----------|
| Evidence / benchmarks | `luthiers-toolbox/tests/` + regression corpus |
| Design decision | `luthiers-toolbox/docs/adr/` |
| Lifecycle promotion | `VECTORIZER_COMPONENT_LIFECYCLE.md` |
| Implementation | **New code** in `services/` — not symlink/submodule from sandbox |

**Examples of valid graduation:** Port *idea* of neck-pocket feature calibration after diff review; implement Loop 1 validation gate inspired by `agentic_supervisor` heuristics; ADR for occupancy semantics informed by `extract_body_grid_v3`.

**Invalid graduation:** Replace `vectorizer_phase3.py` in main with sandbox snapshot; import `cognitive_extractor` in `BlueprintOrchestrator`; submodule sandbox into `services/api`.

---

## 5. Cognitive / grid lineage

| Old framing | New framing |
|-------------|-------------|
| ORPHANED → delete | ORPHANED → **re-home** to sandbox semantic ecosystem |
| Failed code | **Unresolved topology research** with harvest value |
| Wire back for quick fix | **Harvest** → ADR → new implementation |

Files: `cognitive_*`, `extract_body_grid_*`, phase archaeology — see migration plan Tier A.

---

## 6. Boundary rules (non-negotiable)

1. **Sandbox may evolve aggressively** — no Blueprint Reader default, no commercial ACTIVE claims without separate gate.
2. **Runtime spine evolves carefully** — PR-2/PR-1/PR-3 remediation precedes any promotion from sandbox.
3. **No production-adjacent coupling** without intake discipline (grep CI, `check_semantic_sandbox_imports.py`).
4. **vector extraction ≠ semantic interpretation** — keep disciplines in separate repos.
5. **Wave 2 `agentic_supervisor`** in sandbox = incubation prototype for Loop 1 / AGE — not production until graduation bridge complete.

---

## 7. Related documents

| Document | Purpose |
|----------|---------|
| `VECTORIZER_SANDBOX_MIGRATION_PLAN.md` | Phased relocation + sandbox repo structure |
| `VECTORIZER_COMPONENT_LIFECYCLE.md` | States, ACTIVE gate, RELOCATED_EXTERNAL |
| `BLUEPRINT_READER_PROTECTION_RULES.md` | LOCKED MVP surface |
| `CLAUDE.md` | Vectorizer three-loop architecture (production goals) |

---

*Semantic incubation preserves research velocity without sacrificing constitutional operational stability.*
