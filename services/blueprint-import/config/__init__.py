"""
Blueprint Import Configuration
==============================

Configuration system for tiered processing.

Components:
- ProcessingTier: Enum of available tiers (EXPRESS, STANDARD, PREMIUM, BATCH)
- TierConfig: Dataclass with tier-specific settings
- TieredProcessor: Configuration manager with 3-layer priority

Author: Luthier's Toolbox
Version: 4.0.0
"""

from .processing_tiers import (
    ProcessingTier,
    TierConfig,
    TieredProcessor,
    TIER_CONFIGS,
    get_tier_for_task
)

__all__ = [
    'ProcessingTier',
    'TierConfig',
    'TieredProcessor',
    'TIER_CONFIGS',
    'get_tier_for_task'
]

__version__ = '4.0.0'
