# DO-101B — Queued: Empirical Registry and Discovery

**Status:** QUEUED — immediately behind DO-103 Stage 3  
**Queued:** 2026-08-19  
**Blocked by:** DO-103 Stage 3 freeze (provenance-derived HARDWARE + `grant_readiness` ingestion)  
**Primary owner repo:** `tap_tone_pi`  
**Consumer interest:** `luthiers-toolbox` (material-evidence / orthotropic-model reuse)

---

## 1. Position in sequence

```text
ACTIVE  DO-103 Stage 3   ← must complete / freeze first
QUEUED  DO-101B          ← this queued order
LATER   DO-103 hardware stages
LATER   ToolBox material-evidence → orthotropic validation → Mesh Pipeline experimental
```

DO-101B is **not** deprioritized for lack of value. It is deferred because Stage 3 is
campaign-blocking and should define the provenance semantics that the registry schema will
later encode.

Authorization source: `docs/handoffs/DO_103_STAGE3_ACTIVE_AUTHORIZATION_2026-08-19.md`.  
Sequencing registry: `docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md` §11.

---

## 2. Intended deliverables (when activated)

```text
empirical registry
→ registry-entry schema
→ `ttp empirical` CLI
→ easier inspection / discovery / reuse
```

Expected registry fields once Stage 3 lands:

| Field class | Examples |
|-------------|----------|
| Identity | model id, version |
| Domain | validity domain / applicability bounds |
| Provenance | evidence origin, hardware vs simulated, calibration state |
| Artifacts | supporting measurement / grant_readiness references |

---

## 3. Scope guard (when activated)

### In scope

- Empirical model registry + entry schema  
- `ttp empirical` inspection / discovery CLI  
- Documentation of how to list, show, and reuse registered models  

### Out of scope

- Hardware acquisition campaigns  
- Mesh Pipeline interpretation  
- Orthotropic fitting / ToolBox material UI (later integration phase)  
- Reopening Stage 3 provenance rules except additive consumption of their outputs  

---

## 4. Activation gate

DO-101B may start when Stage 3 reports freeze complete:

1. Provenance-derived HARDWARE classification landed with negative tests  
2. Phase-2 `grant_readiness` ingestion path exists  
3. The active-order handoff marks Stage 3 as FROZEN or COMPLETE  

Until then, do not open parallel registry schema work that invents HARDWARE as a free-form enum.

---

*Queued 2026-08-19. Do not promote this order ahead of DO-103 Stage 3 without a new
authorization call.*
