"""
Processing Tiers Configuration
==============================

Tiered processing system for blueprint vectorization.

Tiers:
- EXPRESS:  <30 sec, basic features, preview/batch
- STANDARD: 1-2 min, daily use with ML
- PREMIUM:  3-5 min, final production with all features
- BATCH:    10-20 min/file, overnight processing

Author: The Production Shop
Version: 4.0.0
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


class ProcessingTier(Enum):
    """Processing tier levels."""
    EXPRESS = "express"      # <30 sec, basic features
    STANDARD = "standard"    # 1-2 min, daily use
    PREMIUM = "premium"      # 3-5 min, final production
    BATCH = "batch"          # 10-20 min, overnight


@dataclass
class TierConfig:
    """Configuration for a processing tier."""
    # Core extraction
    dual_pass: bool = True
    use_ml: bool = True
    detect_primitives: bool = True
    scale_detection: bool = True

    # Phase 4.0 features
    leader_lines: bool = False
    parametric: bool = False

    # Phase 5.0 features
    neural_boost: bool = False

    # Performance limits
    max_contours: int = 2000
    simplify_tolerance: float = 0.2  # mm
    min_area: int = 100  # pixels

    # Multi-page (Phase 4.1)
    extract_all_pages: bool = False

    # Hardware
    gpu_available: bool = False
    batch_size: int = 8

    # OCR
    enable_ocr: bool = True
    ocr_min_confidence: float = 0.3


# Default configurations for each tier
TIER_CONFIGS: Dict[ProcessingTier, TierConfig] = {
    ProcessingTier.EXPRESS: TierConfig(
        dual_pass=False,
        use_ml=False,
        detect_primitives=False,
        scale_detection=False,
        leader_lines=False,
        parametric=False,
        max_contours=500,
        simplify_tolerance=0.5,
        min_area=200,
        enable_ocr=False,
    ),
    ProcessingTier.STANDARD: TierConfig(
        dual_pass=True,
        use_ml=True,
        detect_primitives=True,
        scale_detection=True,
        leader_lines=False,
        parametric=False,
        max_contours=2000,
        simplify_tolerance=0.2,
        min_area=100,
        enable_ocr=True,
    ),
    ProcessingTier.PREMIUM: TierConfig(
        dual_pass=True,
        use_ml=True,
        detect_primitives=True,
        scale_detection=True,
        leader_lines=True,
        parametric=True,
        neural_boost=True,
        max_contours=5000,
        simplify_tolerance=0.1,
        min_area=50,
        enable_ocr=True,
        ocr_min_confidence=0.2,
    ),
    ProcessingTier.BATCH: TierConfig(
        dual_pass=True,
        use_ml=True,
        detect_primitives=True,
        scale_detection=True,
        leader_lines=True,
        parametric=True,
        max_contours=10000,
        simplify_tolerance=0.05,
        min_area=25,
        extract_all_pages=True,
        enable_ocr=True,
        ocr_min_confidence=0.15,
    ),
}


class TieredProcessor:
    """
    Three-layer tier configuration system.

    Priority:
    1. Runtime flag overrides
    2. Config file defaults
    3. Auto-detection fallback

    Usage:
        processor = TieredProcessor(tier='premium')
        config = processor.config

        # Or with config file
        processor = TieredProcessor(
            tier='standard',
            config_path='config/my_settings.json'
        )
    """

    def __init__(
        self,
        tier: Union[str, ProcessingTier] = ProcessingTier.STANDARD,
        config_path: Optional[str] = None,
        auto_detect_hardware: bool = True
    ):
        """
        Initialize tiered processor.

        Args:
            tier: Processing tier (string or enum)
            config_path: Optional path to config file for overrides
            auto_detect_hardware: Auto-detect GPU for premium tier
        """
        # Normalize tier
        if isinstance(tier, str):
            tier = ProcessingTier(tier.lower())
        self.tier = tier

        # Load base config
        self.config = TierConfig(**asdict(TIER_CONFIGS[tier]))

        # Apply config file overrides
        if config_path:
            self._apply_config_file(config_path)

        # Auto-detect hardware
        if auto_detect_hardware and tier in (ProcessingTier.PREMIUM, ProcessingTier.BATCH):
            self._auto_detect_capabilities()

        logger.info(f"Initialized {tier.value} tier processor")

    def _apply_config_file(self, config_path: str):
        """Apply overrides from config file (JSON or YAML)."""
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return

        try:
            with open(path) as f:
                # Determine file format
                if path.suffix.lower() in ('.yaml', '.yml'):
                    if not YAML_AVAILABLE:
                        logger.warning("YAML not available, install PyYAML")
                        return
                    user_config = yaml.safe_load(f)
                else:
                    user_config = json.load(f)

            if not user_config:
                return

            # Check for YAML shop_config format (nested under 'tiers')
            if 'tiers' in user_config:
                tier_overrides = user_config['tiers'].get(self.tier.value, {})
            else:
                # JSON format (direct tier keys)
                tier_overrides = user_config.get(self.tier.value, {})

            # Apply overrides
            for key, value in tier_overrides.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    logger.debug(f"Override: {key} = {value}")

            # Apply OCR settings if present
            if 'ocr' in user_config:
                ocr_config = user_config['ocr']
                if 'enabled' in ocr_config:
                    self.config.enable_ocr = ocr_config['enabled']
                if 'min_confidence' in ocr_config:
                    self.config.ocr_min_confidence = ocr_config['min_confidence']

            # Apply hardware settings if present
            if 'hardware' in user_config:
                hw_config = user_config['hardware']
                if 'batch_size' in hw_config:
                    self.config.batch_size = hw_config['batch_size']

        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")

    def _auto_detect_capabilities(self):
        """Auto-detect hardware capabilities."""
        # Check for GPU
        try:
            import torch
            self.config.gpu_available = torch.cuda.is_available()
            if self.config.gpu_available:
                self.config.batch_size = 32
                logger.info("GPU detected - enabled accelerated processing")
            else:
                self.config.batch_size = 8
        except ImportError:
            self.config.gpu_available = False
            self.config.batch_size = 8

    def get_vectorizer_kwargs(self) -> Dict[str, Any]:
        """
        Get kwargs for Phase3Vectorizer initialization.

        Returns:
            Dictionary of vectorizer parameters
        """
        return {
            'enable_primitives': self.config.detect_primitives,
            'enable_scale_detection': self.config.scale_detection,
            'enable_ocr': self.config.enable_ocr,
            'simplify_tolerance': self.config.simplify_tolerance,
        }

    def get_extract_kwargs(self) -> Dict[str, Any]:
        """
        Get kwargs for vectorizer.extract() call.

        Returns:
            Dictionary of extraction parameters
        """
        return {
            'dual_pass': self.config.dual_pass,
            'use_ml': self.config.use_ml,
            'detect_primitives': self.config.detect_primitives,
        }

    @property
    def supports_leader_lines(self) -> bool:
        """Check if tier supports leader line detection."""
        return self.config.leader_lines

    @property
    def supports_parametric(self) -> bool:
        """Check if tier supports parametric constraints."""
        return self.config.parametric

    @property
    def supports_neural(self) -> bool:
        """Check if tier supports neural recognition."""
        return self.config.neural_boost and self.config.gpu_available

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            'tier': self.tier.value,
            'config': asdict(self.config)
        }

    @classmethod
    def list_tiers(cls) -> Dict[str, str]:
        """List available tiers with descriptions."""
        return {
            'express': '<30 sec - Basic contours, preview/batch',
            'standard': '1-2 min - ML classification, daily use',
            'premium': '3-5 min - All features, final production',
            'batch': '10-20 min - Maximum quality, overnight'
        }


def get_tier_for_task(task_type: str) -> ProcessingTier:
    """
    Recommend a processing tier based on task type.

    Args:
        task_type: Type of task ('preview', 'daily', 'production', 'archive')

    Returns:
        Recommended ProcessingTier
    """
    TASK_MAPPING = {
        'preview': ProcessingTier.EXPRESS,
        'quick': ProcessingTier.EXPRESS,
        'daily': ProcessingTier.STANDARD,
        'normal': ProcessingTier.STANDARD,
        'production': ProcessingTier.PREMIUM,
        'final': ProcessingTier.PREMIUM,
        'archive': ProcessingTier.BATCH,
        'batch': ProcessingTier.BATCH,
    }

    return TASK_MAPPING.get(task_type.lower(), ProcessingTier.STANDARD)
