# DO-103 Stage 3 — Active Authorization (Provenance Freeze)

**Status:** ACTIVE — authorized next order  
**Authorized:** 2026-08-19  
**Authorizing call:** Promote DO-103 Stage 3 ahead of DO-101B  
**Program chain:** Tap Tone Pi → Material Evidence → ToolBox Mesh Pipeline → physical validation  
**Primary owner repo:** `tap_tone_pi`  
**Downstream consumer:** `luthiers-toolbox` (contract observer only in Stage 3)  
**Queued immediately behind:** DO-101B (empirical registry / `ttp empirical`)

---

## 1. Authorization decision

> **DO-103 Stage 3 is the next active order. DO-101B remains queued immediately behind it.**

Stage 3 is **time-order sensitive** in a way DO-101B is not. Hardware campaigns must not begin until:

1. Phase-2 `grant_readiness` ingestion exists, and  
2. `HARDWARE` origin cannot be a caller assertion — it must be **derived from measurement provenance**.

DO-101B remains valuable (discoverability / inspection of empirical models) but is infrastructure that becomes *better defined* after provenance semantics are frozen.

---

## 2. Why Stage 3 before DO-101B

| Order | Delivers | Timing character |
|-------|----------|------------------|
| **DO-103 Stage 3** | Trustworthy evidence chain before physical campaign | **Blocking** — must freeze before hardware stages |
| **DO-101B** | Empirical registry schema + `ttp empirical` CLI | Valuable, not campaign-blocking |
| Later DO-103 hardware stages | Shaker / stinger / transducer acquisition | After Stage 3 freeze |
| Later ToolBox integration | Material-evidence consumption → orthotropic validation → Mesh Pipeline experimental phase | After provenance + (optionally) registry |

Target chain Stage 3 must make trustworthy:

```text
physical specimen
    ↓
sensor / fixture / acquisition
    ↓
Tap Tone Pi artifact
    ↓
provenance proves HARDWARE origin   ← Stage 3
    ↓
grant_readiness evidence            ← Stage 3
    ↓
ToolBox consumes artifact
    ↓
material interpretation / model validation
```

Without Stage 3, later claims of the form:

> “This orthotropic material model was validated against physical specimens”

cannot prove the source data left a physical acquisition path rather than a demo/simulator run.

---

## 3. Narrow scope (must not expand)

### In scope

| Work item | Intent |
|-----------|--------|
| Phase-2 `grant_readiness` ingestion | Ingest instrument/measurement data into grant-readiness evidence surfaces |
| Provenance-derived `EvidenceOrigin` / HARDWARE classification | Derive HARDWARE from measurement provenance; reject caller-only labels |
| Negative tests against false HARDWARE claims | Prove demo/simulator/synthetic paths cannot self-assert HARDWARE |
| Freeze gate before physical campaign | Document “Stage 3 frozen → hardware stages may proceed” criteria |

### Explicitly out of scope

- Hardware acquisition (shaker / stinger / transducer) — later DO-103 stages  
- Empirical registry / `ttp empirical` CLI — **DO-101B**  
- Mesh Pipeline interpretation / orthotropic model fitting — later ToolBox integration  
- Broad ToolBox material-evidence UI or CAM coupling  
- Expanding analyzer authority beyond measurement → grant_readiness evidence export

---

## 4. Acceptance criteria (Stage 3 done when…)

1. **Ingestion:** Phase-2 path accepts governed Tap Tone Pi artifacts and emits `grant_readiness` evidence records (or equivalent contract artifact) without Toolbox imports into `tap_tone_pi`.
2. **Derived HARDWARE:** `EvidenceOrigin.HARDWARE` (or equivalent) is computed from provenance fields; API/call sites that pass a free-form HARDWARE flag without supporting provenance **fail closed**.
3. **Negative witnesses:** Tests cover at least:
   - demo/simulator provenance → cannot classify as HARDWARE  
   - missing provenance → cannot classify as HARDWARE  
   - caller-asserted HARDWARE without acquisition chain → rejected  
4. **Freeze note:** A short freeze statement exists naming Stage 3 complete and authorizing later hardware stages of DO-103.
5. **Boundary intact:** `docs/ANALYZER_BOUNDARY_SPEC.md` / tap_tone measurement boundary still hold — Stage 3 does not move interpretation into Tap Tone Pi.

---

## 5. Sequencing after Stage 3

```text
NOW     DO-103 Stage 3   (this order — ACTIVE)
THEN    DO-101B          (queued — empirical registry / schema / ttp empirical)
THEN    DO-103 hardware stages   (when fixtures exist)
THEN    ToolBox material-evidence integration
            ↓
        orthotropic model validation
            ↓
        Mesh Pipeline experimental phase
```

DO-101B should eventually expose richer registry fields once Stage 3 lands:

```text
model | version | validity domain | evidence origin
hardware/simulated provenance | calibration state | supporting artifacts
```

Building that registry *before* provenance semantics are frozen would force a second schema pass.

---

## 6. Cross-repo touchpoints (luthiers-toolbox)

Stage 3 implementation ownership is **tap_tone_pi**. In this repo, Stage 3 authorizes only:

- This active-order record and queue discipline  
- Consumer expectation: ToolBox must treat HARDWARE as provenance-derived when material-evidence integration begins  
- No premature Mesh Pipeline / orthotropic validation work under the guise of Stage 3

Contract reminder (existing law):

> The ONLY interface to tap_tone_pi is `viewer_pack_v1` (see `docs/ANALYZER_BOUNDARY_SPEC.md`).

---

## 7. Related documents

| Doc | Role |
|-----|------|
| `docs/handoffs/DO_101B_QUEUED_EMPIRICAL_REGISTRY_2026-08-19.md` | Immediate next queue entry |
| `docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md` §11 | Sequencing registry |
| `docs/ANALYZER_BOUNDARY_SPEC.md` | Tap Tone ↔ ToolBox boundary |
| `docs/adr/ADR-002-mesh-pipeline-coupling.md` | Downstream Mesh Pipeline coupling (later) |
| Constitutional DO 77–82 imports | Epistemic / advisory boundary posture |

---

*Authorization recorded 2026-08-19. Implementation of Stage 3 code belongs in tap_tone_pi under this scope — do not absorb DO-101B or Mesh Pipeline work into Stage 3.*
