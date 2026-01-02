"""
RMOS Pipeline Feedback Configuration

LANE: OPERATION (infrastructure)
Reference: docs/OPERATION_EXECUTION_GOVERNANCE_v1.md, ADR-003 Phase 5

Feature flag configuration for feedback hooks.
All hooks default to OFF for safety.

Environment Variables:
- {TOOL}_LEARNING_HOOK_ENABLED - Auto-emit learning events from job logs
- {TOOL}_METRICS_ROLLUP_HOOK_ENABLED - Auto-persist metrics rollups
- {TOOL}_APPLY_ACCEPTED_OVERRIDES - Apply learned multipliers to contexts

Example:
    ROUGHING_LEARNING_HOOK_ENABLED=true
    ROUGHING_METRICS_ROLLUP_HOOK_ENABLED=true
    ROUGHING_APPLY_ACCEPTED_OVERRIDES=false
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

# Truthy values for boolean parsing
_TRUTHY = {"1", "true", "yes", "y", "on"}


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    """Parse a boolean from environment variable."""
    if value is None:
        return default
    return value.lower().strip() in _TRUTHY


@dataclass(frozen=True)
class FeedbackConfig:
    """
    Feedback configuration for a tool type.

    All hooks default to OFF for safety. Enable via environment variables.
    """
    tool_type: str

    # Feature flags
    learning_hook_enabled: bool = False
    metrics_rollup_hook_enabled: bool = False
    apply_accepted_overrides: bool = False

    # Paths
    learned_overrides_path: Optional[str] = None

    @classmethod
    def from_env(cls, tool_type: str) -> "FeedbackConfig":
        """
        Load configuration from environment variables.

        Args:
            tool_type: Tool type prefix (e.g., "roughing", "drilling")

        Returns:
            FeedbackConfig with values from environment
        """
        prefix = tool_type.upper()

        learning_enabled = _parse_bool(
            os.getenv(f"{prefix}_LEARNING_HOOK_ENABLED"),
            default=False,
        )
        rollup_enabled = _parse_bool(
            os.getenv(f"{prefix}_METRICS_ROLLUP_HOOK_ENABLED"),
            default=False,
        )
        apply_enabled = _parse_bool(
            os.getenv(f"{prefix}_APPLY_ACCEPTED_OVERRIDES"),
            default=False,
        )

        # Default path for learned overrides
        default_path = f"services/api/data/{tool_type}/learned_overrides.jsonl"
        overrides_path = os.getenv(
            f"{prefix}_LEARNED_OVERRIDES_PATH",
            default_path,
        )

        return cls(
            tool_type=tool_type,
            learning_hook_enabled=learning_enabled,
            metrics_rollup_hook_enabled=rollup_enabled,
            apply_accepted_overrides=apply_enabled,
            learned_overrides_path=overrides_path,
        )


# Cache of configs by tool type
_configs: dict[str, FeedbackConfig] = {}


def get_feedback_config(tool_type: str) -> FeedbackConfig:
    """
    Get feedback configuration for a tool type.

    Caches configuration to avoid repeated env lookups.

    Args:
        tool_type: Tool type prefix (e.g., "roughing", "drilling")

    Returns:
        FeedbackConfig for the tool type
    """
    if tool_type not in _configs:
        _configs[tool_type] = FeedbackConfig.from_env(tool_type)
    return _configs[tool_type]


def clear_config_cache() -> None:
    """Clear the config cache (for testing)."""
    _configs.clear()


def is_learning_hook_enabled(tool_type: str) -> bool:
    """Check if learning hook is enabled for a tool type."""
    return get_feedback_config(tool_type).learning_hook_enabled


def is_metrics_rollup_hook_enabled(tool_type: str) -> bool:
    """Check if metrics rollup hook is enabled for a tool type."""
    return get_feedback_config(tool_type).metrics_rollup_hook_enabled


def is_apply_overrides_enabled(tool_type: str) -> bool:
    """Check if apply overrides is enabled for a tool type."""
    return get_feedback_config(tool_type).apply_accepted_overrides


def get_learned_overrides_path(tool_type: str) -> str:
    """Get the path for learned overrides storage."""
    config = get_feedback_config(tool_type)
    return config.learned_overrides_path or f"services/api/data/{tool_type}/learned_overrides.jsonl"
