# DO-101B — Queued: Empirical Registry Discovery

**Status:** QUEUED — immediately behind DO-103 Stage 3  
**Queued:** 2026-08-19  
**Blocked by:** DO-103 Stage 3 freeze (provenance-derived HARDWARE + `grant_readiness` ingestion)  
**Primary owner repo:** `tap_tone_pi`  
**Consumer interest:** `luthiers-toolbox` (material-evidence / anisotropic-model reuse)

---

## 1. Position in sequence

```text
ACTIVE  DO-103 Stage 3   ← must complete / freeze first
QUEUED  DO-101B          ← this order
LATER   DO-103 hardware stages
LATER   ToolBox material-evidence → orthotropic validation → Mesh Pipeline experimental
```

DO-101B is **not** deprioritized for lack of value. It is deferred because Stage 3 is campaign-blocking and because registry schema fields for evidence origin / hardware-vs-simulated provenance should be defined *after* Stage 3 semantics exist.

Authorization source: `docs/handoffs/DO_103_STAGE3_ACTIVE_AUTHORIZATION_2026-08-19.md`.

---

## 2. Intended deliverables (when activated)

```text
empirical registry
→ registry-entry schema
→ `ttp empirical` CLI
→ easier inspection / discovery / reuse
```

Expected eventual registry surface (enriched by Stage 3 outcomes):

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

### Out of scope (still)

- Hardware acquisition campaigns  
- Mesh Pipeline interpretation  
- Orthotropic fitting / ToolBox material UI (later integration phase)  
- Reopening Stage 3 provenance rules except additive consumption of their outputs  

---

## 4. Activation gate

DO-101B may start when Stage 3 reports freeze complete:

1. Provenance-derived HARDWARE classification landed with negative tests  
2. Phase-2 `grant_readiness` ingestion path exists  
3. Active-order handoff marks Stage 3 FROZEN / COMPLETE  

Until then, do not open parallel registry schema work that invents HARDWARE as a free-form enum.

---

*Queued 2026-08-19. Do not promote ahead of DO-103 Stage 3 without a new authorization call.*
