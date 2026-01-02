"""
AI Availability Gate
Provides runtime checks for AI subsystem availability.

This module enables the app to boot without AI credentials while gracefully
returning HTTP 503 on AI endpoints when disabled.

INVARIANTS:
- This module must NEVER raise at import time
- All checks happen at runtime (inside request handlers)
- Returns 503 (Service Unavailable) with clear error envelope

Usage in endpoints:
    from app.ai.availability import require_ai_available

    @router.post("/ai-endpoint")
    async def my_ai_endpoint(request: MyRequest):
        require_ai_available(feature="My AI Feature")
        # ... AI logic here
"""
from __future__ import annotations

import os
from fastapi import HTTPException


def is_ai_available(provider: str = "anthropic") -> bool:
    """
    Check if AI subsystem is available for the given provider.
    
    Does NOT raise - use for conditional logic / health checks.
    
    Args:
        provider: "anthropic" | "openai" | "local"
        
    Returns:
        True if the provider's API key is configured
    """
    provider = provider.lower()
    
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        return bool(key)
    
    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "").strip()
        return bool(key)
    
    if provider == "local":
        # Local providers (Ollama etc) just need the URL
        url = os.getenv("OLLAMA_URL", "").strip()
        return bool(url) or True  # Default to localhost
    
    return False


def require_ai_available(
    *,
    feature: str = "AI",
    provider: str = "anthropic",
) -> None:
    """
    Raises HTTP 503 if AI subsystem is not available.
    
    Call this at the top of any endpoint that requires AI functionality.
    
    Args:
        feature: Human-readable feature name for error message
        provider: "anthropic" | "openai" | "local"
        
    Raises:
        HTTPException: 503 with AI_DISABLED error envelope
    """
    if is_ai_available(provider):
        return
    
    # Determine which key is missing
    key_name = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "local": "OLLAMA_URL",
    }.get(provider.lower(), f"{provider.upper()}_API_KEY")
    
    raise HTTPException(
        status_code=503,
        detail={
            "error": "AI_DISABLED",
            "message": f"{feature} is disabled: {key_name} is not set.",
            "provider": provider,
        },
    )


def require_anthropic_available(*, feature: str = "RMOS AI") -> None:
    """
    Convenience wrapper for Anthropic-specific endpoints.
    
    Args:
        feature: Human-readable feature name for error message
        
    Raises:
        HTTPException: 503 with AI_DISABLED error envelope
    """
    require_ai_available(feature=feature, provider="anthropic")


def require_openai_available(*, feature: str = "AI") -> None:
    """
    Convenience wrapper for OpenAI-specific endpoints.
    
    Args:
        feature: Human-readable feature name for error message
        
    Raises:
        HTTPException: 503 with AI_DISABLED error envelope
    """
    require_ai_available(feature=feature, provider="openai")


# ---------------------------------------------------------------------------
# Health check helper
# ---------------------------------------------------------------------------

def get_ai_status() -> dict:
    """
    Get comprehensive AI subsystem status.
    
    Returns:
        Dict with status, available providers, and configuration state
    """
    providers = {
        "anthropic": is_ai_available("anthropic"),
        "openai": is_ai_available("openai"),
        "local": is_ai_available("local"),
    }
    
    any_available = any(providers.values())
    
    return {
        "status": "available" if any_available else "disabled",
        "providers": providers,
        "message": (
            "AI subsystem operational"
            if any_available
            else "No AI providers configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
        ),
    }
