"""
AI Platform Layer - Luthier's ToolBox

This is the canonical shared layer for all AI operations.
Domain applications (Vision, AI-CAM, RMOS AI, Art Studio) compose this layer.

HARD INVARIANTS:
1. No domain app may call OpenAI/Anthropic directly - only ai.transport.*
2. No transport layer imports domain modules - one-way dependency
3. Safety enforcement is centralized - all apps use ai.safety.enforcement
4. Every AI call captures provenance - request_id, provider, model, cost
5. Assets stored via one mechanism - attachments/ with sha256 dedupe

Structure:
    ai/
    ├── transport/      # LLM and Image API clients (HTTP layer)
    ├── providers/      # Provider implementations (OpenAI, Anthropic, Local)
    ├── safety/         # Policy enforcement, allow/deny checks
    ├── prompts/        # Prompt templates, vocabulary utilities
    ├── cost/           # Cost estimation before generation
    └── observability/  # Request ID propagation, audit logging

Usage:
    from app.ai.transport import get_llm_client, get_image_client
    from app.ai.safety import assert_allowed
    from app.ai.observability import audit_log
"""

__version__ = "1.0.0"

# Re-export key functions for convenience
from .transport import get_llm_client, get_image_client
from .safety import assert_allowed, check_prompt_safety
from .observability import get_request_id, audit_ai_call

__all__ = [
    # Transport
    "get_llm_client",
    "get_image_client",
    # Safety
    "assert_allowed",
    "check_prompt_safety",
    # Observability
    "get_request_id",
    "audit_ai_call",
]
