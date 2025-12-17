# AI Image Provider Contract

**Document Type:** Canonical Governance Specification
**Version:** 1.0
**Effective Date:** December 16, 2025
**Status:** AUTHORITATIVE

---

## Governance Statement

This document establishes the **canonical contract** for AI image generation providers within the Luthier's ToolBox platform. All implementations MUST conform to the specifications herein. Deviation from this contract is prohibited without formal amendment through the governance review process.

### Governing Principles

1. **Single Source of Truth** — This document is the authoritative reference for AI image provider contracts
2. **One-Way Dependency** — Provider layer imports transport layer; reverse is forbidden
3. **Transport Isolation** — HTTP concerns stay in `llm_client.py`; business logic stays in `providers.py`
4. **Protocol Conformance** — All providers MUST implement the `AiImageProvider` protocol
5. **No Drift Policy** — Implementations must match this contract exactly; no ad-hoc extensions

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Image generation providers | Text/chat completion providers |
| OpenAI DALL-E integration | Local image processing |
| Provider protocol definition | Frontend rendering |
| Transport method signatures | Storage/caching strategies |

---

## Architecture

### Layer Separation (MANDATORY)

```
┌─────────────────────────────────────────────────────────────────┐
│                      PROVIDER LAYER                              │
│            services/api/app/_experimental/ai_graphics/           │
│                      services/providers.py                       │
├─────────────────────────────────────────────────────────────────┤
│  Responsibilities:                                              │
│  • Protocol definition (AiImageProvider)                        │
│  • Provider implementations (OpenAIProvider, StubProvider)      │
│  • Output normalization (→ AiImageResult)                       │
│  • Provider registry (get_provider, set_provider)               │
│  • Input validation                                             │
│  • Error translation to domain exceptions                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ imports (ONE-WAY ONLY)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TRANSPORT LAYER                              │
│            services/api/app/_experimental/ai_graphics/           │
│                     services/llm_client.py                       │
├─────────────────────────────────────────────────────────────────┤
│  Responsibilities:                                              │
│  • HTTP request execution                                       │
│  • Authentication header injection                              │
│  • Retry logic with backoff                                     │
│  • Timeout handling                                             │
│  • Raw response parsing                                         │
│  • Transport exceptions (LLMClientError, etc.)                  │
│                                                                 │
│  PROHIBITED:                                                    │
│  • Domain model imports (AiImageResult, RosetteParamSpec)       │
│  • Provider selection logic                                     │
│  • Business rules or validation                                 │
│  • Imports from providers.py                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Dependency Rule

```
providers.py ──imports──▶ llm_client.py    ✓ ALLOWED
llm_client.py ──imports──▶ providers.py    ✗ FORBIDDEN
```

**Enforcement:** Automated tests scan `llm_client.py` AST for violations.

---

## Contract Specifications

### 1. Result Container

**File:** `providers.py`
**Status:** CANONICAL

```python
from dataclasses import dataclass

@dataclass
class AiImageResult:
    """
    Canonical result container for image generation.

    All image providers MUST return this type.
    """
    image_bytes: bytes          # Raw image data (PNG, JPEG, etc.)
    format: str = "png"         # Image format identifier
    prompt_used: str = ""       # Actual prompt sent to API
    model: str = ""             # Model identifier (e.g., "dall-e-3")
```

**Field Specifications:**

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `image_bytes` | `bytes` | YES | — | Non-empty for successful generation |
| `format` | `str` | NO | `"png"` | One of: `png`, `jpeg`, `webp` |
| `prompt_used` | `str` | NO | `""` | Trimmed, non-null |
| `model` | `str` | NO | `""` | API model identifier |

---

### 2. Provider Protocol

**File:** `providers.py`
**Status:** CANONICAL

```python
from typing import Protocol, Optional, Dict, Any

class AiImageProvider(Protocol):
    """
    Protocol defining the contract for AI image generation providers.

    All provider implementations MUST conform to this interface.
    """

    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of desired image (REQUIRED)
            size: Image dimensions (default: "1024x1024")
            format: Output format (default: "png")
            model: Specific model to use (provider-dependent)
            options: Provider-specific options

        Returns:
            AiImageResult with generated image bytes

        Raises:
            ValueError: If prompt is empty or invalid
            LLMClientError: If API call fails
        """
        ...
```

**Method Signature (IMMUTABLE):**

| Parameter | Type | Required | Default | Notes |
|-----------|------|----------|---------|-------|
| `prompt` | `str` | YES | — | Must be non-empty after trim |
| `size` | `str` | NO | `"1024x1024"` | Provider-specific sizes |
| `format` | `str` | NO | `"png"` | Output image format |
| `model` | `Optional[str]` | NO | `None` | Falls back to provider default |
| `options` | `Optional[Dict]` | NO | `None` | Extension point |

---

### 3. OpenAI Provider Implementation

**File:** `providers.py`
**Status:** CANONICAL

```python
class OpenAIProvider:
    """
    OpenAI-backed provider for image generation (DALL-E).

    GOVERNANCE RULES:
    - This class owns normalization and provider logic
    - llm_client.py owns HTTP transport only
    - One-way dependency: this file imports llm_client, never reverse
    """

    def __init__(self, llm_client: Any):
        """
        Initialize with transport layer client.

        Args:
            llm_client: LLMClient instance for HTTP operations
        """
        self.client = llm_client

    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        """
        Generate image using OpenAI DALL-E API.

        Implementation follows canonical contract.
        """
        # Input validation (provider responsibility)
        prompt_used = (prompt or "").strip()
        if not prompt_used:
            raise ValueError("prompt is required")

        # Delegate to transport layer
        # Contract: generate_image_bytes returns (bytes, metadata_dict)
        bytes_out, meta = self.client.generate_image_bytes(
            prompt=prompt_used,
            size=size,
            format=format,
            model=model,
            options=options or {},
        )

        # Validate transport response
        if not isinstance(bytes_out, (bytes, bytearray)):
            raise RuntimeError(
                "llm_client.generate_image_bytes must return raw bytes as first value"
            )

        # Extract metadata
        used_model = ""
        if isinstance(meta, dict):
            used_model = str(meta.get("model") or "")

        # Normalize to canonical result type
        return AiImageResult(
            image_bytes=bytes(bytes_out),
            format=format,
            prompt_used=prompt_used,
            model=used_model or (model or ""),
        )
```

---

### 4. Transport Layer Method

**File:** `llm_client.py`
**Status:** CANONICAL

```python
def generate_image_bytes(
    self,
    *,
    prompt: str,
    size: str = "1024x1024",
    format: str = "png",
    model: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> tuple[bytes, Dict[str, Any]]:
    """
    Low-level image generation via OpenAI Images API.

    TRANSPORT LAYER CONTRACT:
    - Handles HTTP POST to images/generations endpoint
    - Manages authentication headers
    - Implements retry logic
    - Returns raw bytes + metadata dict

    Args:
        prompt: Image description
        size: Requested dimensions
        format: Response format
        model: Model identifier (dall-e-2, dall-e-3)
        options: Additional API parameters

    Returns:
        Tuple of (image_bytes, metadata_dict)
        metadata_dict contains: {"model": str, "revised_prompt": str, ...}

    Raises:
        LLMAuthError: Invalid API key
        LLMTimeoutError: Request timeout
        LLMRateLimitError: Rate limit exceeded
        LLMClientError: Other API errors
    """
    # Implementation handles HTTP transport only
    ...
```

**Return Contract:**

```python
# MUST return this exact structure:
(
    bytes,              # Raw image bytes (PNG/JPEG/WebP)
    {
        "model": str,           # Model used
        "revised_prompt": str,  # OpenAI's revised prompt (if any)
        # ... other metadata
    }
)
```

---

## Compliance Requirements

### MUST (Mandatory)

| ID | Requirement |
|----|-------------|
| M1 | All image providers MUST implement `AiImageProvider` protocol |
| M2 | All providers MUST return `AiImageResult` dataclass |
| M3 | `llm_client.py` MUST NOT import from `providers.py` |
| M4 | `llm_client.py` MUST NOT reference domain types |
| M5 | Transport methods MUST return raw bytes, not domain objects |
| M6 | Provider methods MUST validate inputs before transport call |

### MUST NOT (Prohibited)

| ID | Prohibition |
|----|-------------|
| P1 | MUST NOT add fields to `AiImageResult` without governance review |
| P2 | MUST NOT change method signatures in protocols |
| P3 | MUST NOT bypass provider layer for direct transport calls |
| P4 | MUST NOT embed business logic in transport layer |

### SHOULD (Recommended)

| ID | Recommendation |
|----|----------------|
| S1 | SHOULD log all API calls with prompt hash (not full prompt) |
| S2 | SHOULD implement circuit breaker for repeated failures |
| S3 | SHOULD cache identical requests within session |

---

## Test Requirements

### Dependency Enforcement Test

```python
def test_llm_client_has_no_provider_imports():
    """llm_client.py MUST NOT import from providers.py"""
    source = LLM_CLIENT_PATH.read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            assert "provider" not in str(node).lower()
```

### Protocol Conformance Test

```python
def test_openai_provider_implements_protocol():
    """OpenAIProvider MUST implement AiImageProvider protocol"""
    assert isinstance(OpenAIProvider(mock_client), AiImageProvider)
```

### Contract Test

```python
def test_generate_image_returns_correct_type():
    """generate_image MUST return AiImageResult"""
    provider = OpenAIProvider(mock_client)
    result = provider.generate_image("test prompt")
    assert isinstance(result, AiImageResult)
    assert isinstance(result.image_bytes, bytes)
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-16 | Claude Opus 4.5 | Initial canonical specification |

---

## Amendment Process

Changes to this contract require:

1. **Proposal** — Written specification of proposed change
2. **Impact Analysis** — Assessment of breaking changes
3. **Review** — Technical review by maintainers
4. **Test Update** — Corresponding test modifications
5. **Approval** — Sign-off from project lead
6. **Version Increment** — Update version and history

---

## References

| Document | Purpose |
|----------|---------|
| `AI_REFACTORING_SESSION_REPORT_DEC16.md` | Session report establishing architecture |
| `test_llm_client_isolation.py` | Dependency enforcement tests |
| `providers.py` | Implementation file |
| `llm_client.py` | Transport layer file |

---

*This document is the authoritative specification for AI image provider contracts.*
*Non-conforming implementations are considered defects.*
