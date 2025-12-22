# AI Platform Realignment — Developer Handoff

**Date:** December 22, 2025  
**Commit:** `c96f5e5`  
**Author:** AI Systems Consolidation  
**Status:** ✅ Complete (Phases 1-7)

---

## Executive Summary

The AI Platform Realignment consolidates 4 scattered `import openai` / `import anthropic` occurrences into a single governed layer at `app/ai/`. This document provides everything developers need to integrate with or extend the new infrastructure.

### Hard Invariant (CRITICAL)

```
┌─────────────────────────────────────────────────────────────────┐
│  ONLY app/ai/transport/ may import openai, anthropic, etc.     │
│  Domain code uses get_llm_client() / get_image_client()        │
└─────────────────────────────────────────────────────────────────┘
```

**Violation of this rule will be flagged in code review.**

---

## 1. Architecture Overview

```
app/ai/                           # Canonical AI Platform Layer
├── __init__.py                   # Main exports + architecture diagram
├── transport/                    # SDK wrappers (HTTP layer)
│   ├── __init__.py              # Exports: get_llm_client, get_image_client
│   ├── llm_client.py            # OpenAI, Anthropic, Local, Stub clients
│   └── image_client.py          # DALL-E, SDXL, Stub image clients
├── providers/                    # Provider abstraction (protocols)
│   ├── __init__.py              # Exports: LLMProviderProtocol, ImageProviderProtocol
│   └── base.py                  # Protocol definitions + base classes
├── safety/                       # Content filtering + enforcement
│   ├── __init__.py              # Exports: assert_allowed, SafetyCategory
│   ├── policy.py                # SafetyCategory enum, BLOCKED_TERMS
│   └── enforcement.py           # assert_allowed(), SafetyViolationError
├── prompts/                      # Prompt engineering templates
│   ├── __init__.py              # Exports: prompt builders
│   └── templates.py             # RosettePromptBuilder, CAMAdvisorPromptBuilder
├── cost/                         # Cost estimation
│   ├── __init__.py              # Exports: estimate_llm_cost, estimate_image_cost
│   └── estimate.py              # Pricing dictionaries + estimation functions
└── observability/                # Logging + tracing
    ├── __init__.py              # Exports: audit_ai_call, get_request_id
    ├── request_id.py            # ContextVar for request tracing
    └── audit_log.py             # Structured audit logging

art_studio/svg/                   # Phase 6: Prompt→SVG Pipeline
├── __init__.py                   # Exports: PromptToSvgGenerator
└── generator.py                  # AI-driven design generation
```

---

## 2. Migration Guide

### Before (Scattered Imports)

```python
# ❌ OLD PATTERN - DO NOT USE
import openai
import os

api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ],
    temperature=0.7,
)
result = response.choices[0].message.content
```

### After (Centralized Platform)

```python
# ✅ NEW PATTERN - USE THIS
from app.ai.transport import get_llm_client
from app.ai.safety import assert_allowed, SafetyCategory
from app.ai.observability import audit_ai_call

# 1. Safety check (required for user-facing prompts)
assert_allowed(prompt, category=SafetyCategory.ROSETTE_DESIGN)

# 2. Get client via factory
client = get_llm_client(provider="openai")

# 3. Check configuration
if not client.is_configured:
    raise RuntimeError("OPENAI_API_KEY not set")

# 4. Make request
response = client.request_text(
    prompt=prompt,
    system_prompt="You are a helpful assistant.",
    temperature=0.7,
    max_tokens=1000,
)

# 5. Audit the call
audit_ai_call(
    operation="llm",
    provider="openai",
    model=response.model,
    prompt=prompt,
    response_content=response.content,
)

result = response.content
```

---

## 3. API Reference

### 3.1 Transport Layer (`app.ai.transport`)

#### `get_llm_client(provider: str) -> BaseLLMClient`

Factory function returning configured LLM client.

| Provider | Class | Environment Variable |
|----------|-------|---------------------|
| `"openai"` | `OpenAILLMClient` | `OPENAI_API_KEY` |
| `"anthropic"` | `AnthropicLLMClient` | `ANTHROPIC_API_KEY` |
| `"local"` | `LocalLLMClient` | `LOCAL_LLM_URL` |
| `"stub"` | `StubLLMClient` | None (testing) |

```python
from app.ai.transport import get_llm_client

client = get_llm_client(provider="openai")
print(client.is_configured)  # True if API key set
```

#### `BaseLLMClient.request_text(...)` → `LLMResponse`

```python
response = client.request_text(
    prompt="Design a rosette",           # Required
    system_prompt="You are an expert.",  # Optional
    temperature=0.7,                      # Optional (default: 0.7)
    max_tokens=1000,                      # Optional (default: 1000)
    model=None,                           # Optional (uses env AI_MODEL or default)
)

# LLMResponse attributes:
response.content      # str - The generated text
response.model        # str - Model used (e.g., "gpt-4")
response.usage        # Dict - Token usage info
response.finish_reason # str - "stop", "length", etc.
```

#### `get_image_client(provider: str) -> BaseImageClient`

| Provider | Class | Environment Variable |
|----------|-------|---------------------|
| `"openai"` | `OpenAIImageClient` | `OPENAI_API_KEY` |
| `"sdxl"` | `SDXLImageClient` | `SDXL_API_URL` |
| `"stub"` | `StubImageClient` | None (testing) |

```python
from app.ai.transport import get_image_client

client = get_image_client(provider="openai")
response = client.generate_image(
    prompt="A beautiful guitar rosette",
    size="1024x1024",
    quality="standard",  # or "hd"
)

# ImageResponse attributes:
response.url           # str - Image URL (if URL response)
response.b64_json      # str - Base64 encoded image (if b64 response)
response.revised_prompt # str - DALL-E's revised prompt
response.model         # str - Model used
```

---

### 3.2 Safety Layer (`app.ai.safety`)

#### `SafetyCategory` Enum

```python
from app.ai.safety import SafetyCategory

SafetyCategory.GENERAL           # Default, minimal filtering
SafetyCategory.ROSETTE_DESIGN    # Guitar rosette generation
SafetyCategory.IMAGE_GENERATION  # DALL-E / image prompts
SafetyCategory.CODE_GENERATION   # Code/technical content
SafetyCategory.CAM_ADVISORY      # CAM/machining advice
```

#### `assert_allowed(prompt, category) -> None`

Raises `SafetyViolationError` if prompt fails safety check.

```python
from app.ai.safety import assert_allowed, SafetyCategory, SafetyViolationError

try:
    assert_allowed(user_prompt, category=SafetyCategory.IMAGE_GENERATION)
except SafetyViolationError as e:
    return {"error": f"Prompt rejected: {e}"}
```

#### `check_prompt_safety(prompt, category) -> SafetyResult`

Non-throwing version for soft checks.

```python
from app.ai.safety import check_prompt_safety, SafetyCategory

result = check_prompt_safety(prompt, SafetyCategory.GENERAL)
if not result.is_safe:
    log.warning(f"Safety concern: {result.reason}")
```

---

### 3.3 Observability (`app.ai.observability`)

#### `audit_ai_call(...)`

Structured logging for AI operations.

```python
from app.ai.observability import audit_ai_call

audit_ai_call(
    operation="llm",              # "llm" | "image" | "prompt_to_svg"
    provider="openai",            # Provider name
    model="gpt-4",                # Model used
    prompt="...",                 # Input prompt
    response_content="...",       # Output (optional)
    latency_ms=1234.5,            # Timing (optional)
    error=None,                   # Error message (optional)
)
```

#### Request ID Context

```python
from app.ai.observability import get_request_id, set_request_id, request_id_context

# Manual setting
set_request_id("req-12345")
print(get_request_id())  # "req-12345"

# Context manager (auto-generates ID)
with request_id_context() as req_id:
    # All AI calls in this block share req_id
    client.request_text(...)
```

---

### 3.4 Cost Estimation (`app.ai.cost`)

```python
from app.ai.cost import estimate_llm_cost, estimate_image_cost

# LLM cost (returns USD)
cost = estimate_llm_cost(
    model="gpt-4",
    input_tokens=500,
    output_tokens=200,
)
print(f"Estimated: ${cost:.4f}")

# Image cost
cost = estimate_image_cost(
    model="dall-e-3",
    size="1024x1024",
    quality="hd",
)
print(f"Estimated: ${cost:.4f}")
```

---

### 3.5 Prompt Templates (`app.ai.prompts`)

```python
from app.ai.prompts import RosettePromptBuilder, CAMAdvisorPromptBuilder

# Rosette design prompts
builder = RosettePromptBuilder()
builder.set_diameter(100)
builder.set_style("gothic")
builder.set_constraints({"min_feature_mm": 0.5})

system_prompt = builder.build_system()
user_prompt = builder.build_user("ornate cathedral pattern")

# CAM advisor prompts
cam_builder = CAMAdvisorPromptBuilder()
cam_builder.set_tool("6mm endmill")
cam_builder.set_material("mahogany")
prompt = cam_builder.build()
```

---

### 3.6 Prompt→SVG Pipeline (`app.art_studio.svg`)

```python
from app.art_studio.svg import PromptToSvgGenerator, GenerationResult

# Full pipeline
generator = PromptToSvgGenerator(provider="openai")
result: GenerationResult = generator.generate(
    prompt="Gothic cathedral rosette with 12 petals",
    design_type="rosette",
    constraints={"diameter_mm": 100},
)

if result.success:
    svg_content = result.svg_content  # SVG string
    spec = result.spec                 # Intermediate JSON spec
    print(f"Generated in {result.total_time_ms}ms")
else:
    print(f"Error at {result.error_stage}: {result.error}")

# Convenience functions
from app.art_studio.svg.generator import generate_rosette_from_prompt

result = generate_rosette_from_prompt(
    prompt="Art deco style",
    diameter_mm=80,
    provider="openai",
)
```

---

## 4. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `AI_MODEL` | `gpt-4` | Default LLM model |
| `AI_IMAGE_MODEL` | `dall-e-3` | Default image model |
| `LOCAL_LLM_URL` | `http://localhost:11434` | Ollama/local LLM URL |
| `SDXL_API_URL` | — | Stable Diffusion XL API |
| `AI_AUDIT_ENABLED` | `true` | Enable audit logging |
| `AI_SAFETY_STRICT` | `false` | Strict safety mode |

---

## 5. Testing Patterns

### Unit Tests with Stub Client

```python
import pytest
from app.ai.transport import get_llm_client

def test_rosette_generation():
    # Use stub client for deterministic testing
    client = get_llm_client(provider="stub")
    
    response = client.request_text(
        prompt="Generate rosette",
        system_prompt="You are a luthier.",
    )
    
    assert response.content == "STUB_RESPONSE"
    assert response.model == "stub-model"
```

### Integration Tests

```python
import pytest
from app.ai.transport import get_llm_client

@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)
def test_real_openai_call():
    client = get_llm_client(provider="openai")
    assert client.is_configured
    
    response = client.request_text(
        prompt="Say hello",
        max_tokens=10,
    )
    assert len(response.content) > 0
```

### Mocking AI Calls

```python
from unittest.mock import patch, MagicMock
from app.ai.transport.llm_client import LLMResponse

def test_with_mock():
    mock_response = LLMResponse(
        content='{"rings": []}',
        model="gpt-4",
        usage={"total_tokens": 100},
    )
    
    with patch("app.ai.transport.get_llm_client") as mock_factory:
        mock_client = MagicMock()
        mock_client.request_text.return_value = mock_response
        mock_factory.return_value = mock_client
        
        # Your test code here
        from app.ai.transport import get_llm_client
        client = get_llm_client(provider="openai")
        result = client.request_text(prompt="test")
        
        assert result.content == '{"rings": []}'
```

---

## 6. Files Modified in This Realignment

### New Files (22)

| File | Purpose |
|------|---------|
| `app/ai/__init__.py` | Main exports, architecture docs |
| `app/ai/transport/__init__.py` | Export factory functions |
| `app/ai/transport/llm_client.py` | LLM client implementations |
| `app/ai/transport/image_client.py` | Image client implementations |
| `app/ai/providers/__init__.py` | Export protocols |
| `app/ai/providers/base.py` | Protocol definitions |
| `app/ai/safety/__init__.py` | Export safety functions |
| `app/ai/safety/policy.py` | Safety categories + blocked terms |
| `app/ai/safety/enforcement.py` | Hard-stop enforcement |
| `app/ai/prompts/__init__.py` | Export prompt builders |
| `app/ai/prompts/templates.py` | Domain-specific prompt builders |
| `app/ai/cost/__init__.py` | Export cost functions |
| `app/ai/cost/estimate.py` | Pricing + estimation |
| `app/ai/observability/__init__.py` | Export observability |
| `app/ai/observability/request_id.py` | Request ID context |
| `app/ai/observability/audit_log.py` | Audit logging |
| `app/art_studio/svg/__init__.py` | SVG package exports |
| `app/art_studio/svg/generator.py` | Prompt→SVG pipeline |

### Modified Files (4)

| File | Change |
|------|--------|
| `_experimental/ai_graphics/rosette_generator.py` | Use `app.ai.transport` instead of direct `import openai/anthropic` |
| `_experimental/ai_graphics/services/training_data_generator.py` | Use `app.ai.transport.get_image_client()` |
| `_experimental/ai_graphics/image_transport.py` | Added deprecation notice |
| `_experimental/ai_graphics/image_providers.py` | Added deprecation notice |

### Deprecated Files (Pending Removal)

These files are deprecated and will be removed after migration verification:

- `_experimental/ai_graphics/image_transport.py` → Use `app.ai.transport.image_client`
- `_experimental/ai_graphics/image_providers.py` → Use `app.ai.providers.base`
- `_experimental/ai_graphics/llm_client.py` (if exists) → Use `app.ai.transport.llm_client`

---

## 7. Common Pitfalls

| Issue | Solution |
|-------|----------|
| `ImportError: No module named 'app.ai'` | Ensure working directory is `services/api/` or add to PYTHONPATH |
| `RuntimeError: OPENAI_API_KEY not set` | Check `client.is_configured` before calling |
| `SafetyViolationError` on valid prompt | Check `BLOCKED_TERMS` in `safety/policy.py`, adjust category |
| Audit logs not appearing | Check `AI_AUDIT_ENABLED` env var, verify logging config |
| High latency on first call | SDK lazy-loads, first call includes import time |
| Model mismatch | Check `AI_MODEL` env var, or pass `model=` explicitly |

---

## 8. Extension Points

### Adding a New LLM Provider

1. Create client class in `app/ai/transport/llm_client.py`:

```python
class MyProviderLLMClient(BaseLLMClient):
    """Client for MyProvider API."""
    
    def __init__(self):
        self._api_key = os.environ.get("MYPROVIDER_API_KEY")
    
    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)
    
    def request_text(self, prompt, system_prompt=None, **kwargs) -> LLMResponse:
        import myprovider  # Only import here!
        # ... implementation
```

2. Register in factory function:

```python
def get_llm_client(provider: str = "openai") -> BaseLLMClient:
    if provider == "myprovider":
        return MyProviderLLMClient()
    # ... existing providers
```

3. Add pricing to `app/ai/cost/estimate.py`

### Adding a New Safety Category

1. Add to `SafetyCategory` enum in `safety/policy.py`:

```python
class SafetyCategory(str, Enum):
    # ... existing
    MY_NEW_CATEGORY = "my_new_category"
```

2. Add category-specific rules if needed in `check_prompt_safety()`

---

## 9. Related Documentation

- [RMOS Architecture](../RMOS/README.md) — RMOS AI Search integration
- [Art Studio Workflow](../../services/api/app/art_studio/ART_STUDIO_WORKFLOW_INTEGRATION.md)
- [Experimental Modules Audit](../EXPERIMENTAL_MODULES_AUDIT.md)
- [System Evaluation Summary](../SYSTEM_EVALUATION_EXECUTIVE_SUMMARY.md)

---

## 10. Contact & Support

For questions about the AI Platform:

1. Check this document first
2. Review code in `app/ai/__init__.py` (contains architecture diagram)
3. Run tests: `pytest services/api/app/tests/test_ai_*.py -v`
4. File issue with tag `ai-platform`

---

*Document generated: December 22, 2025*  
*Last commit: c96f5e5*
