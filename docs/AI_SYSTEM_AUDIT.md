# AI System Audit

**Version:** 1.0.0
**Date:** 2026-01-13
**Status:** ~65-70% Production-Ready

---

## Executive Summary

The luthiers-toolbox AI system is a **multi-layered platform** with approximately **26,878 lines of AI-related backend code**. The architecture features a canonical AI platform layer with multi-provider support, graceful degradation, and domain-specific integrations for Blueprint Reader, RMOS search, and experimental AI Graphics. Core infrastructure is production-ready; domain integrations are at various stages of completion.

---

## 1. Architecture Overview

### Multi-Layer Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    Canonical AI Platform                         │
│  ├── Transport Layer    - Multi-provider LLM + Image clients    │
│  ├── Cost Estimation    - Token pricing tables                  │
│  ├── Safety Policy      - Content filtering framework           │
│  ├── Observability      - Audit logging, request tracing        │
│  └── Availability Gate  - Graceful 503 degradation              │
├─────────────────────────────────────────────────────────────────┤
│                    Domain Integrations                           │
│  ├── Blueprint Reader   - Claude Sonnet 4 vision analysis       │
│  ├── RMOS AI Search     - Constraint-first design generation    │
│  ├── AI Graphics        - Rosette suggestions (experimental)    │
│  └── G-code Explainer   - CNC program analysis (stub)           │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Provider Abstraction** | Only `app/ai/transport/` imports external AI SDKs |
| **Graceful Degradation** | Server boots without API keys; AI endpoints return 503 |
| **Domain Isolation** | Each domain uses factory functions, not direct imports |
| **Safety First** | Content filtering policy enforced at transport layer |
| **Observability** | Structured audit logging with request tracing |

---

## 2. Backend Structure

### Directory Layout

```
services/api/app/
├── ai/                                   # Canonical AI Platform (2,924 lines)
│   ├── __init__.py                       ✅ 45 lines - Module exports
│   ├── availability.py                   ✅ 147 lines - Runtime availability gate
│   ├── README.md                         ✅ 150 lines - Architecture docs
│   ├── transport/
│   │   ├── llm_client.py                 ✅ 521 lines - Multi-provider LLM
│   │   ├── image_client.py               ✅ 540 lines - Multi-provider image
│   │   └── __init__.py                   ✅ 30 lines
│   ├── cost/
│   │   ├── estimate.py                   ✅ 215 lines - Token pricing
│   │   └── __init__.py                   ✅ 50 lines
│   ├── safety/
│   │   ├── policy.py                     ✅ 230 lines - Content filtering
│   │   ├── enforcement.py                ✅ 120 lines - Violation detection
│   │   └── __init__.py                   ✅ 40 lines
│   ├── observability/
│   │   ├── audit_log.py                  ✅ 250 lines - AI call logging
│   │   ├── request_id.py                 ✅ 125 lines - Request tracing
│   │   └── __init__.py                   ✅ 35 lines
│   ├── prompts/
│   │   ├── templates.py                  ✅ 320 lines - Prompt engineering
│   │   └── __init__.py                   ✅ 45 lines
│   └── providers/
│       ├── base.py                       ✅ 180 lines - Provider protocols
│       └── __init__.py                   ✅ 40 lines
│
├── rmos/                                 # RMOS AI Integration (2,080+ lines)
│   ├── ai_search.py                      ✅ 375 lines - Constraint search loop
│   ├── ai_policy.py                      ✅ 131 lines - Global constraints
│   ├── api_ai_routes.py                  ✅ 283 lines - AI endpoints
│   ├── api_ai_snapshots.py               ✅ 141 lines - Snapshot persistence
│   ├── schemas_ai.py                     ✅ 400+ lines - AI request/response
│   ├── schemas_logs_ai.py                ✅ 250+ lines - Logging schemas
│   ├── logging_ai.py                     ✅ 300+ lines - AI event logging
│   └── ai/constraints.py                 ✅ 200+ lines - Constraint validation
│
├── _experimental/ai_graphics/            # AI Graphics (6,647+ lines)
│   ├── __init__.py                       ⚠️ 116 lines
│   ├── api/
│   │   ├── ai_routes.py                  ⚠️ 56 lines - Suggest endpoint
│   │   └── teaching_routes.py            ⚠️ 150+ lines
│   ├── schemas/
│   │   ├── ai_schemas.py                 ⚠️ 400+ lines
│   │   └── advisory_schemas.py           ⚠️ 49 lines
│   ├── services/
│   │   ├── llm_client.py                 ⚠️ 372 lines - Legacy client
│   │   ├── ai_parameter_suggester.py     ⚠️ 254 lines - Main entrypoint
│   │   └── training_data_generator.py    ⚠️ 280+ lines
│   ├── sessions.py                       ⚠️ 200+ lines
│   ├── image_transport.py                ⚠️ 480 lines
│   ├── image_providers.py                ⚠️ 650+ lines
│   ├── rosette_generator.py              ⚠️ 610+ lines
│   ├── prompt_engine.py                  ⚠️ 730 lines
│   └── vocabulary.py                     ⚠️ 2,300+ lines
│
├── _experimental/ai_cam/                 # AI CAM (327 lines)
│   └── explain_gcode.py                  ⚠️ 100 lines - Basic parsing
│
├── pipelines/gcode_explainer/            # G-code Explainer (115 lines)
│   └── explain_gcode_ai.py               ⚠️ 115 lines - Non-LLM parsing
│
└── routers/
    ├── blueprint_router.py               ✅ 1,315 lines - Blueprint AI endpoints
    └── ai_cam_router.py                  ⚠️ 227 lines - CAM AI (optional)

services/blueprint-import/                # Blueprint Reader (1,177 lines)
├── analyzer.py                           ✅ 221 lines - Claude Sonnet 4
├── vectorizer.py                         ✅ 280 lines - OpenCV Phase 2
├── vectorizer_phase2.py                  ✅ 450 lines - Advanced vectorization
├── dxf_compat.py                         ✅ 200 lines - DXF R12 export
└── requirements.txt                      ✅ 16 lines
```

**Total Backend AI Code: ~26,878 lines**

---

## 3. Component Status

### Tier 1: Production-Ready

| Component | Lines | Status | Features |
|-----------|-------|--------|----------|
| **Canonical AI Platform** | 2,924 | ✅ 95% | Multi-provider transport, safety, cost, observability |
| **Blueprint Reader Phase 1** | 1,177 | ✅ 100% | Claude Sonnet 4 vision, PDF→PNG, dimension extraction |
| **Blueprint Reader Phase 2** | 730 | ✅ 100% | OpenCV vectorization, DXF R12 export |
| **RMOS AI Search** | 2,080+ | ✅ 90% | Constraint-first design, feasibility scoring |
| **Availability Gate** | 147 | ✅ 100% | Graceful 503 degradation |

### Tier 2: Experimental/Partial

| Component | Lines | Status | Gap |
|-----------|-------|--------|-----|
| **AI Graphics** | 6,647+ | ⚠️ 50% | Works API-side, no Vue UI integration |
| **Cost Tracking** | 215 | ⚠️ 60% | Estimation exists, not persisted |
| **Token Audit** | 250 | ⚠️ 50% | Framework exists, not wired |

### Tier 3: Stub/Early Stage

| Component | Lines | Status | Gap |
|-----------|-------|--------|-----|
| **G-code Explainer** | 115 | ❌ 20% | Parsing only, no LLM |
| **AI CAM Router** | 227 | ⚠️ 10% | Optional import, early stage |
| **AI Core (Locked)** | 250+ | ❌ 0% | Import banned by CI |

---

## 4. Canonical AI Platform Layer

### Transport Layer

**LLM Client:** `ai/transport/llm_client.py` (521 lines)

```python
class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"

@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7

@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens
    model: str
    finish_reason: str
```

**Image Client:** `ai/transport/image_client.py` (540 lines)

```python
class ImageProvider(str, Enum):
    DALLE = "dalle"
    SDXL = "sdxl"
    STUB = "stub"

@dataclass
class ImageGenerationRequest:
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    n: int = 1

@dataclass
class ImageGenerationResponse:
    images: List[str]  # Base64 or URLs
    revised_prompt: Optional[str]
```

### Availability Gate

**File:** `ai/availability.py` (147 lines)

```python
def is_ai_available(provider: str = "anthropic") -> bool:
    """Check if AI provider is configured and available."""
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        return bool(key)
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "").strip()
        return bool(key)
    return False

def require_ai_available(provider: str = "anthropic"):
    """FastAPI dependency that returns 503 if AI unavailable."""
    if not is_ai_available(provider):
        raise HTTPException(
            status_code=503,
            detail={"error": "AI_DISABLED", "message": f"{provider} API key not set"}
        )
```

### Cost Estimation

**File:** `ai/cost/estimate.py` (215 lines)

| Model | Input (per 1K) | Output (per 1K) |
|-------|----------------|-----------------|
| claude-3-sonnet | $0.003 | $0.015 |
| claude-3-opus | $0.015 | $0.075 |
| gpt-4-turbo | $0.01 | $0.03 |
| gpt-4o | $0.005 | $0.015 |
| dall-e-3 | $0.04/image | - |

### Safety Policy

**File:** `ai/safety/policy.py` (230 lines)

```python
class SafetyCategory(str, Enum):
    HARMFUL = "harmful"
    ILLEGAL = "illegal"
    SEXUAL = "sexual"
    VIOLENT = "violent"
    DECEPTIVE = "deceptive"

@dataclass
class SafetyPolicy:
    blocked_categories: List[SafetyCategory]
    warning_categories: List[SafetyCategory]
    max_prompt_length: int = 32000
    max_response_length: int = 16000
```

### Observability

**Audit Log:** `ai/observability/audit_log.py` (250 lines)

```python
def audit_ai_call(
    operation: str,          # "llm" | "image" | "vision"
    provider: str,           # "anthropic" | "openai"
    model: str,
    prompt: str,
    response_content: str,
    tokens_used: int = 0,
    cost_usd: float = 0.0,
) -> None:
    """Log AI call for audit trail."""
```

---

## 5. Domain Integrations

### 5.1 Blueprint Reader AI (Phase 1)

**Location:** `services/blueprint-import/analyzer.py` (221 lines)

**Claude Model:** `claude-sonnet-4-20250514`

**Features:**
- PDF to PNG conversion at 300 DPI
- Multi-page PDF support
- Dimension extraction via Claude vision
- Scale detection (1:1, 1/4" = 1', etc.)
- Blueprint type classification (guitar, architectural, mechanical)

**Request Flow:**
```
PDF/Image Upload → pdf2image conversion → Claude Vision API →
    Structured JSON response → AnalysisResponse
```

**Response Schema:**
```python
{
    "scale": "1:1",
    "scale_confidence": "high",
    "dimensions": [
        {
            "label": "body_width",
            "value": "12.5 inches",
            "type": "detected",
            "confidence": "high"
        }
    ],
    "blueprint_type": "guitar",
    "detected_model": "Les Paul",
    "notes": "Classical guitar body outline..."
}
```

### 5.2 RMOS AI Search

**Location:** `rmos/ai_search.py` (375 lines)

**Purpose:** Constraint-first design generation with feasibility scoring

**Search Loop:**
```
User Constraints → LLM Candidate Generation → RMOS Feasibility Scoring →
    Risk Bucketing (GREEN/YELLOW/RED) → Refinement Loop → Best Candidate
```

**Request Schema:**
```python
class AiSearchRequest:
    workflow_mode: str = "constraint_first"
    context: Dict  # tool_id, material_id, machine_id
    search_budget: SearchBudget  # max_attempts, time_limit, min_score
```

**Response Schema:**
```python
class AiSearchResponse:
    status: str  # success, best_effort, exhausted, timeout
    best_candidate: DesignCandidate  # rosette_spec, feasibility, ai_score
    summary: SearchSummary  # total_attempts, green_found, elapsed_seconds
```

### 5.3 AI Graphics (Experimental)

**Location:** `_experimental/ai_graphics/` (6,647+ lines)

**Purpose:** LLM-powered rosette design suggestions

**Components:**
- `ai_parameter_suggester.py` - Main entrypoint
- `prompt_engine.py` - Guitar-specific prompt engineering
- `rosette_generator.py` - Rosette-specific image generation
- `vocabulary.py` - 2,300+ lines of UI vocabulary dropdowns

**Status:** Works via API, no Vue UI integration

### 5.4 G-code Explainer (Stub)

**Location:** `pipelines/gcode_explainer/explain_gcode_ai.py` (115 lines)

**Status:** Basic G-code parsing only, no LLM integration

---

## 6. API Endpoints

### Production Endpoints

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/blueprint/analyze` | POST | ✅ | Claude vision dimension extraction |
| `/api/rmos/ai/constraint-search` | POST | ✅ | LLM-guided design generation |
| `/api/rmos/ai/quick-check` | POST | ✅ | Fast feasibility check |
| `/api/rmos/ai/health` | GET | ✅ | AI availability status |
| `/api/blueprint/vectorize-geometry` | POST | ✅ | OpenCV vectorization (non-AI) |

### Experimental Endpoints

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/api/ai/graphics/suggest` | POST | ⚠️ | Rosette suggestions (no UI) |
| `/api/ai/graphics/health` | GET | ⚠️ | AI Graphics health |
| `/api/gcode/explain` | POST | ❌ | Stub - parsing only |

### Graceful Degradation

All AI endpoints return HTTP 503 when API keys are missing:

```json
{
    "error": "AI_DISABLED",
    "message": "ANTHROPIC_API_KEY not set"
}
```

---

## 7. Provider Configuration

### Supported Providers

| Provider | Env Variable | Required | Primary Use |
|----------|-------------|----------|-------------|
| **Anthropic (Claude)** | `ANTHROPIC_API_KEY` | ✅ Yes | Blueprint analysis, RMOS search |
| **Emergent LLM** | `EMERGENT_LLM_KEY` | Optional | Alternate Blueprint analyzer |
| **OpenAI** | `OPENAI_API_KEY` | No | Image generation (DALL-E) |
| **Ollama** | `OLLAMA_URL` | No | Local LLM fallback |

### Environment Setup

```bash
# Required for AI features
ANTHROPIC_API_KEY=sk-ant-v0-...

# Optional
OPENAI_API_KEY=sk-proj-...
OLLAMA_URL=http://localhost:11434/api
EMERGENT_LLM_KEY=...
```

### Installation

```bash
# Base server (works without AI)
pip install -r services/api/requirements.txt

# With AI features
pip install -r services/api/requirements-ai.txt
# Then set: ANTHROPIC_API_KEY
```

---

## 8. Test Coverage

### Test Files

| Test File | Lines | Status | Coverage |
|-----------|-------|--------|----------|
| `test_ai_disabled.py` | 186 | ✅ | Availability gate (503 behavior) |
| `test_blueprint_ai_disabled.py` | 100 | ✅ | Blueprint AI disabled |
| `test_blueprint_ai_disabled.py` (routers) | 38 | ✅ | Additional Blueprint tests |
| `test_rmos_ai_factory_pattern.py` | 150 | ✅ | RMOS AI factory |
| `test_compare_risk_bucket_detail.py` | 145 | ✅ | Risk bucket comparison |
| `test_llm_client_isolation.py` | - | ⚠️ | LLM client isolation |

**Total Test Code: ~843+ lines**

### Coverage Analysis

| Category | Status | Notes |
|----------|--------|-------|
| Availability gate | ✅ Good | 503 degradation tested |
| Blueprint AI disabled | ✅ Good | Graceful fallback tested |
| RMOS AI factory | ✅ Good | Factory pattern tested |
| Provider-specific tests | ⚠️ Weak | No actual API call tests |
| End-to-end flows | ❌ Missing | No integration tests |
| Cost estimation | ⚠️ Weak | Edge cases untested |

---

## 9. Frontend Components

### Vue Components

| Component | Lines | Status | Purpose |
|-----------|-------|--------|---------|
| `GCodeExplainer.vue` | 17 | ⚠️ Stub | "Implementation in progress" |
| `ArtJobDetail.vue` | 63 | ⚠️ Partial | Art job with AI status |

### Frontend Status

- **Blueprint Reader UI:** No dedicated Vue component - form submission only
- **RMOS AI UI:** No dedicated Vue component - API-first design
- **AI Graphics UI:** Directory exists at `packages/client/src/features/ai_images/`
- **Overall:** Most AI features are **API-only** with minimal frontend

---

## 10. Cost & Token Tracking

### Current Implementation

**Cost Estimation:** `ai/cost/estimate.py` (215 lines)
- Token pricing tables for major models
- Cost calculation per request
- ✅ Functions implemented
- ❌ NOT integrated into request/response tracking
- ❌ NO persistent cost logging

**Token Usage:** Captured in `LLMResponse.usage`
```python
@dataclass
class LLMResponse:
    usage: Dict[str, int]  # {"prompt_tokens": X, "completion_tokens": Y}
```

**Audit Logging:** `ai/observability/audit_log.py` (250 lines)
- ✅ Audit functions defined
- ⚠️ NOT wired into main API calls
- ❌ No persistent storage
- ❌ No dashboard

### Missing Features

- Persistent token usage tracking
- Cost accumulation per user/session
- Budget enforcement
- Usage dashboards

---

## 11. Identified Gaps

### Gap 1: AI Graphics Vue Integration

**Issue:** AI Graphics works API-side but has no Vue UI
**Impact:** Users can't access rosette suggestions via frontend
**Effort:** 16 hours
**Priority:** HIGH

### Gap 2: Cost/Token Tracking Persistence

**Issue:** Estimation exists but not persisted or wired
**Impact:** No visibility into AI costs
**Effort:** 9 hours
**Priority:** MEDIUM

### Gap 3: Provider-Specific Tests

**Issue:** No tests for actual Anthropic/OpenAI API calls
**Impact:** Provider behavior changes could break silently
**Effort:** 10 hours
**Priority:** MEDIUM

### Gap 4: G-code Explainer LLM Integration

**Issue:** Only parsing, no LLM analysis
**Impact:** Feature is non-functional
**Effort:** 8 hours
**Priority:** LOW

### Gap 5: Cost/Token Dashboard

**Issue:** No UI for viewing AI usage
**Impact:** No operational visibility
**Effort:** 12 hours
**Priority:** LOW

### Gap 6: RMOS Refinement Loop

**Issue:** Refinement loop partially implemented
**Impact:** Suboptimal design candidates
**Effort:** 6 hours
**Priority:** MEDIUM

### Gap 7: Budget Enforcement

**Issue:** No per-user or per-session budget limits
**Impact:** Potential runaway costs
**Effort:** 4 hours
**Priority:** LOW

---

## 12. Path to Full Completion

### Phase 1: Core Completion (~35 hours)

| Task | Hours | Priority |
|------|-------|----------|
| AI Graphics Vue integration | 16h | HIGH |
| Wire cost tracking to all AI calls | 4h | MEDIUM |
| Token audit logging integration | 5h | MEDIUM |
| RMOS refinement loop completion | 6h | MEDIUM |
| Budget enforcement basics | 4h | LOW |

### Phase 2: Testing & Polish (~30 hours)

| Task | Hours | Priority |
|------|-------|----------|
| Provider-specific unit tests | 10h | MEDIUM |
| G-code explainer LLM integration | 8h | LOW |
| Cost/token dashboard | 12h | LOW |

**Total: ~65 hours to full completion**

---

## 13. Summary

**The AI System is 65-70% production-ready with excellent core infrastructure.**

### What Works

- ✅ Canonical AI Platform with multi-provider abstraction
- ✅ Graceful 503 degradation without API keys
- ✅ Blueprint Reader Phase 1 (Claude Sonnet 4 vision)
- ✅ Blueprint Reader Phase 2 (OpenCV vectorization)
- ✅ RMOS AI constraint-first search with feasibility scoring
- ✅ Safety policy and content filtering framework
- ✅ Cost estimation functions
- ✅ Audit logging framework

### What's Missing

- ⚠️ AI Graphics Vue UI integration
- ⚠️ Cost/token tracking persistence
- ⚠️ Provider-specific tests
- ❌ G-code explainer LLM integration
- ❌ Cost/token dashboard
- ❌ Budget enforcement

### Comparison to Other Systems

| Aspect | AI System | Saw Lab | Blueprint | Art Studio | RMOS | CAM |
|--------|-----------|---------|-----------|------------|------|-----|
| Core Algorithms | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| API Endpoints | ⚠️ 80% | ✅ 95% | ✅ 93% | ✅ 90% | ✅ 95% | ⚠️ 65% |
| Frontend UI | ⚠️ 30% | ⚠️ 70% | ✅ 90% | ✅ 85% | ✅ Complete | ⚠️ 60% |
| Test Coverage | ⚠️ 70% | ✅ Excellent | ⚠️ Partial | ✅ Good | ⚠️ 20% | ⚠️ Gaps |
| Hours to MVP | ~65h | ~75h | ~24h | ~30h | ~48h | ~50h |

**The AI System provides the foundation for intelligent features across the platform. Core infrastructure is solid; remaining work focuses on UI integration and operational visibility.**

---

*Document generated as part of luthiers-toolbox system audit.*
