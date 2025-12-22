# AI Platform Layer

This directory contains the **platform layer** for AI capabilities in Luthier's Toolbox. It provides transport, safety, cost estimation, and observability for AI operations, but **does not contain domain-specific logic**.

## Architecture

```
app/ai/                    ← Platform layer (this directory)
├── transport/             → LLM/image client abstractions
├── safety/                → Content policy enforcement
├── cost/                  → Token/request cost estimation
├── observability/         → Audit logging, request IDs
├── prompts/               → Prompt templates (infrastructure only)
└── providers/             → Provider abstractions (OpenAI, etc.)

app/rmos/ai/               ← RMOS domain-specific AI logic
app/art_studio/            ← Art Studio domain-specific AI logic
```

## Core Principles

### 🎨 User Creativity Invariant

**The AI platform should not design a rosette or guitar — it should take prompts at the user's creativity.**

This architectural invariant means:

1. **Domain prompts belong in domain directories**
   - RMOS rosette prompts → `app/rmos/ai/`
   - Art studio prompts → `app/art_studio/`
   - Platform layer → infrastructure only

2. **The platform never injects creative goals**
   - ❌ Bad: Platform layer decides "make a herringbone pattern"
   - ✅ Good: Platform provides transport, domain layer constructs prompt

3. **User creativity flows through domain layers**
   - User intent → Domain-specific prompt construction → Platform transport
   - The platform is **goal-agnostic** — it doesn't know what a rosette is

### Why This Matters

- **Separation of concerns**: Platform handles "how to call AI", domains handle "what to generate"
- **Testability**: Domain prompts can be tested independently of transport
- **Flexibility**: Swap AI providers without touching domain logic
- **User agency**: Creative decisions stay close to user-facing code

## Platform Components

### Transport Layer (`transport/`)

Handles the mechanics of calling LLM and image generation APIs:
- `llm_client.py`: Structured text generation (JSON mode, streaming)
- `image_client.py`: DALL-E and image API clients
- Provider-agnostic abstractions

### Safety Layer (`safety/`)

Enforces content policies across all AI operations:
- `policy.py`: Content safety rules (e.g., no violent imagery)
- `enforcement.py`: Pre-flight and post-generation checks
- Blocks unsafe prompts before they reach providers

### Cost Layer (`cost/`)

Estimates and tracks AI operation costs:
- Token counting (OpenAI, Claude, etc.)
- Image generation pricing
- Budget tracking and alerts

### Observability Layer (`observability/`)

Provides visibility into AI operations:
- `audit_log.py`: Audit trail for AI requests/responses
- `request_id.py`: Correlation IDs for debugging
- Cost tracking and performance metrics

## Usage Pattern

**Domain code** (e.g., `app/rmos/ai/generators.py`):
```python
from app.ai import generate_structured, SafetyPolicy
from app.rmos.ai.constraints import build_rosette_constraints

def generate_rosette_candidate(ctx: RmosContext) -> RosetteParamSpec:
    # Domain-specific prompt construction
    prompt = build_rosette_constraints(ctx)
    
    # Platform handles transport + safety + cost + observability
    result = generate_structured(
        prompt=prompt,
        response_model=RosetteParamSpec,
        safety_policy=SafetyPolicy.STRICT,
    )
    return result
```

**Platform code** (e.g., `app/ai/transport/llm_client.py`):
```python
def generate_structured(prompt: str, response_model: Type[T], ...) -> T:
    # Transport layer - NO domain logic here
    # Just handles: provider selection, retries, safety, cost, logging
    ...
```

## Migration Context

This platform layer was established during the **RMOS AI domain migration** (v1.0-rmos-ai-migration). Prior experimental code mixed platform and domain concerns. The current architecture enforces clean separation:

- **Before**: `app._experimental.ai_core` mixed RMOS prompts with transport
- **After**: `app/ai/*` (platform) + `app/rmos/ai/*` (domain) with clear boundaries

See `RMOS_AI_MIGRATION_COMPLETE.md` for full migration details.

## Adding New Domain AI Features

When adding AI capabilities for a new domain:

1. ✅ **Use platform transport**: Import from `app.ai.transport`
2. ✅ **Build domain prompts in domain dir**: Create `app/<domain>/ai/` if needed
3. ✅ **Apply safety policies**: Use `app.ai.safety` for content checks
4. ❌ **Don't put domain logic in platform**: No rosette/guitar/fret knowledge in `app/ai/`

## Contact

Questions about platform layer architecture? See:
- RMOS domain implementation: `app/rmos/ai/`
- Migration documentation: `RMOS_AI_MIGRATION_COMPLETE.md`
- CI enforcement: `app/ci/ban_experimental_ai_core_imports.py`
