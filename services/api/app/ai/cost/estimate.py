"""
AI Cost Estimation

Provides pre-generation cost estimates for AI API calls.
Pricing data current as of December 2024.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Pricing Data (USD per unit)
# ---------------------------------------------------------------------------

PRICING: Dict[str, Dict[str, float]] = {
    # OpenAI LLM pricing (per 1M tokens)
    "gpt-4": {
        "input": 30.00,   # $30 per 1M input tokens
        "output": 60.00,  # $60 per 1M output tokens
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00,
    },
    "gpt-4o": {
        "input": 2.50,
        "output": 10.00,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
    },

    # Anthropic LLM pricing (per 1M tokens)
    "claude-3-opus": {
        "input": 15.00,
        "output": 75.00,
    },
    "claude-3-sonnet": {
        "input": 3.00,
        "output": 15.00,
    },
    "claude-3-haiku": {
        "input": 0.25,
        "output": 1.25,
    },

    # OpenAI Image pricing (per image)
    "dall-e-3": {
        "1024x1024_standard": 0.040,
        "1024x1024_hd": 0.080,
        "1792x1024_standard": 0.080,
        "1792x1024_hd": 0.120,
        "1024x1792_standard": 0.080,
        "1024x1792_hd": 0.120,
    },
    "dall-e-2": {
        "1024x1024": 0.020,
        "512x512": 0.018,
        "256x256": 0.016,
    },

    # Local/Stub (free)
    "local": {
        "input": 0.0,
        "output": 0.0,
    },
    "stub": {
        "input": 0.0,
        "output": 0.0,
    },
}


@dataclass
class CostEstimate:
    """Cost estimate for an AI operation."""
    model: str
    provider: str
    operation: str  # "llm", "image"
    estimated_cost_usd: float
    details: Dict[str, float]
    currency: str = "USD"

    @property
    def formatted(self) -> str:
        """Return formatted cost string."""
        if self.estimated_cost_usd < 0.01:
            return f"<$0.01 {self.currency}"
        return f"${self.estimated_cost_usd:.4f} {self.currency}"

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "operation": self.operation,
            "estimated_cost_usd": self.estimated_cost_usd,
            "formatted": self.formatted,
            "details": self.details,
        }


def estimate_llm_cost(
    model: str,
    input_tokens: int,
    output_tokens: int = 500,
) -> CostEstimate:
    """
    Estimate cost for an LLM API call.

    Args:
        model: Model identifier (e.g., "gpt-4", "claude-3-sonnet")
        input_tokens: Estimated input token count
        output_tokens: Estimated output token count (default 500)

    Returns:
        CostEstimate with breakdown
    """
    # Normalize model name
    model_key = model.lower()
    for key in PRICING:
        if key in model_key:
            model_key = key
            break

    pricing = PRICING.get(model_key, PRICING.get("gpt-4o-mini", {}))

    input_rate = pricing.get("input", 0.0)
    output_rate = pricing.get("output", 0.0)

    input_cost = (input_tokens / 1_000_000) * input_rate
    output_cost = (output_tokens / 1_000_000) * output_rate
    total_cost = input_cost + output_cost

    provider = "openai" if "gpt" in model_key else "anthropic" if "claude" in model_key else "local"

    return CostEstimate(
        model=model,
        provider=provider,
        operation="llm",
        estimated_cost_usd=total_cost,
        details={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "rate_per_1m_input": input_rate,
            "rate_per_1m_output": output_rate,
        },
    )


def estimate_image_cost(
    model: str = "dall-e-3",
    size: str = "1024x1024",
    quality: str = "standard",
    count: int = 1,
) -> CostEstimate:
    """
    Estimate cost for an image generation API call.

    Args:
        model: Model identifier (e.g., "dall-e-3")
        size: Image size (e.g., "1024x1024")
        quality: Quality level ("standard" or "hd")
        count: Number of images to generate

    Returns:
        CostEstimate with breakdown
    """
    model_key = model.lower().replace("-", "_").replace(" ", "_")
    if "dall" in model_key:
        model_key = "dall-e-3" if "3" in model_key else "dall-e-2"

    pricing = PRICING.get(model_key, {})

    # Build pricing key
    if model_key == "dall-e-3":
        price_key = f"{size}_{quality}"
    else:
        price_key = size

    per_image = pricing.get(price_key, 0.04)  # Default DALL-E 3 standard
    total_cost = per_image * count

    return CostEstimate(
        model=model,
        provider="openai" if "dall" in model.lower() else "local",
        operation="image",
        estimated_cost_usd=total_cost,
        details={
            "size": size,
            "quality": quality,
            "count": count,
            "per_image_usd": per_image,
        },
    )


def estimate_total_cost(
    *estimates: CostEstimate,
) -> CostEstimate:
    """
    Combine multiple cost estimates into a total.

    Args:
        *estimates: Variable number of CostEstimate objects

    Returns:
        Combined CostEstimate
    """
    total = sum(e.estimated_cost_usd for e in estimates)
    details = {
        "breakdown": [e.to_dict() for e in estimates],
        "item_count": len(estimates),
    }

    return CostEstimate(
        model="combined",
        provider="multiple",
        operation="total",
        estimated_cost_usd=total,
        details=details,
    )


def estimate_prompt_tokens(text: str) -> int:
    """
    Rough estimate of token count for a text string.

    Uses the approximation: 1 token ~= 4 characters for English text.
    This is a rough estimate; actual tokenization varies by model.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Rough approximation: ~4 chars per token for English
    return max(1, len(text) // 4)
