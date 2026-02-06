# Agentic Layer Architecture Mapping

**Version:** 1.0.0
**Last Updated:** 2026-02-06

---

## 1. Overview

This document maps the existing AI infrastructure to the new agentic contracts layer.
The goal is additive integration — new contracts compose with existing modules, not replace them.

---

## 2. Existing AI Infrastructure

### 2.1 Core AI Platform (`app/ai/`)

| Module | Purpose | Agentic Contract Mapping |
|--------|---------|--------------------------|
| `transport/llm_client.py` | LLM API calls (OpenAI/Anthropic/Local) | **Transport only** - no contract needed |
| `transport/image_client.py` | Image generation API | **Transport only** - no contract needed |
| `transport/vision_client.py` | Vision API (image analysis) | `ToolCapabilityV1` → actions: ANALYZE_GEOMETRY |
| `safety/enforcement.py` | Policy enforcement | Informs `SafeDefaults` in capabilities |
| `safety/policy.py` | Safety policies | Informs `SafeDefaults.require_confirmation` |
| `prompts/templates.py` | Prompt templates | Internal - not exposed in contracts |
| `cost/estimate.py` | Cost estimation | `AgentEventV1` → payload includes cost |
| `observability/audit_log.py` | Audit logging | `AgentEventV1` → unified event vocabulary |
| `observability/request_id.py` | Request ID propagation | `AgentEventV1.correlation_id` |

### 2.2 RMOS AI (`app/rmos/ai/`)

| Module | Purpose | Agentic Contract Mapping |
|--------|---------|--------------------------|
| `clients.py` | RMOS-specific LLM clients | Uses `app/ai/transport` |
| `constraints.py` | Output constraints | Informs `ToolCapabilityV1.safe_defaults` |
| `generators.py` | Content generation | `ToolCapabilityV1` → actions: GENERATE_REPORT |
| `structured_generator.py` | Structured output | `ToolCapabilityV1.output_schemas` |
| `coercion.py` | Type coercion | Internal - not exposed |

### 2.3 RMOS AI Advisory (`app/rmos/ai_advisory/`)

| Module | Purpose | Agentic Contract Mapping |
|--------|---------|--------------------------|
| `schemas.py` | AIContextPacketV1, AdvisoryDraftV1 | **Maps to** `AttentionDirectiveV1` |
| `service.py` | Advisory orchestration | Emits `AgentEventV1` events |
| `store.py` | Advisory persistence | N/A (storage layer) |
| `router.py` | API endpoints | Disabled in WP-2 route reduction |
| `runner.py` | Advisory execution | `ToolCapabilityV1` → actions: GENERATE_REPORT |

### 2.4 Experimental AI CAM (`app/_experimental/ai_cam/`)

| Module | Purpose | Agentic Contract Mapping |
|--------|---------|--------------------------|
| `advisor.py` | CAM advice generation | `ToolCapabilityV1` → actions: ANALYZE_TOOLPATH |
| `explain_gcode.py` | G-code explanation | `AttentionDirectiveV1` for highlights |
| `optimize.py` | Toolpath optimization | `ToolCapabilityV1` → actions: TRANSFORM_NORMALIZE |
| `models.py` | CAM AI models | Internal schemas |

---

## 3. Cross-Repo Contract Flow

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   tap_tone_pi    │     │  luthiers-toolbox │     │   Experience     │
│   (Analyzer)     │     │   (RMOS/Agent)    │     │   Shell (UI)     │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         │ ToolCapabilityV1       │                        │
         │ ───────────────────────>                        │
         │                        │                        │
         │                        │ AttentionDirectiveV1   │
         │                        │ ───────────────────────>
         │                        │                        │
         │ AgentEventV1           │ AgentEventV1           │
         │ <══════════════════════════════════════════════>
         │     (unified event vocabulary)                  │
         │                        │                        │
         │                        │ UWSMv1                 │
         │                        │ <─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
         │                        │     (local-only)       │
```

---

## 4. Integration Points

### 4.1 tap_tone_pi → luthiers-toolbox

**Existing Pattern:**
- `TapToneBundleManifestV1` → `ImportPlan` → `import_acoustics_bundle()`

**Agentic Extension:**
- tap_tone_pi publishes `ToolCapabilityV1` (what it can do)
- Agent layer discovers capabilities
- Agent invokes via existing import flow
- Events emitted as `AgentEventV1`

### 4.2 ai-integrator → RMOS

**Existing Pattern:**
- `AIContextPacketV1` → ai-integrator CLI → `AdvisoryDraftV1`

**Agentic Extension:**
- `AIContextPacketV1` maps to evidence refs in `AttentionDirectiveV1`
- `AdvisoryDraftV1` maps to `AttentionDirectiveV1.detail`
- Governance status flows through `AgentEventV1`

### 4.3 RMOS → Experience Shell

**Existing Pattern:**
- RMOS feasibility → UI displays risk badge
- RMOS run artifacts → UI displays in viewer

**Agentic Extension:**
- `AttentionDirectiveV1` replaces ad-hoc notification patterns
- Urgency/confidence enables smart prioritization
- Auto-dismiss rules reduce alert fatigue

---

## 5. Migration Strategy

### Phase 1: Contract Publication (Current)
- [x] Define contracts in `app/agentic/contracts/`
- [ ] tap_tone_pi publishes `ToolCapabilityV1`
- [ ] RMOS emits `AgentEventV1` on key operations

### Phase 2: Attention Layer
- [ ] RMOS advisory generates `AttentionDirectiveV1`
- [ ] UI renders directives (toast, highlight, modal)
- [ ] Dismissal tracking

### Phase 3: UWSM Integration
- [ ] Local-only preference storage
- [ ] Signal collection from user interactions
- [ ] Preference-aware agent behavior

---

## 6. Invariants

1. **Transport Isolation**: AI transport (`app/ai/transport/`) never imports domain modules
2. **Contract-Only Coupling**: Repos only couple via contracts in `app/agentic/contracts/`
3. **Privacy by Default**: UWSM is Layer 0 (local-only), events default to Layer 3
4. **Safe Defaults Explicit**: Every capability declares `SafeDefaults`
5. **Event Vocabulary Unified**: All repos use `EventType` enum, no ad-hoc event strings

---

## 7. File Locations

| Contract | File | Purpose |
|----------|------|---------|
| ToolCapabilityV1 | `app/agentic/contracts/tool_capability.py` | What tools can do |
| AttentionDirectiveV1 | `app/agentic/contracts/analyzer_attention.py` | Directing user attention |
| AgentEventV1 | `app/agentic/contracts/event_emission.py` | Unified event vocabulary |
| UWSMv1 | `app/agentic/contracts/uwsm.py` | User preference model |

---

## 8. Related Documents

| Document | Purpose |
|----------|---------|
| `DEVELOPER_HANDOFF_ROUTE_REDUCTION_PHASE2.md` | WP-2 route reduction context |
| `docs/DEBT_LOCK_VISION.md` | Vision stack debt policy |
| `tap_tone_pi/CBSP21.md` | Analyzer architecture |
