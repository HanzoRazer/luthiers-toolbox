"""
Blueprint Processing Limits
===========================

Configurable guardrails for blueprint vectorization.

Environment variables:
    BLUEPRINT_MAX_UPLOAD_MB: Maximum upload size (default: 20)
    BLUEPRINT_MAX_RASTER_DIM_PX: Max dimension on longest side (default: 4000)
    BLUEPRINT_MAX_MEGAPIXELS: Max total megapixels (default: 12)
    BLUEPRINT_MAX_PDF_DPI: Max PDF render DPI (default: 150)
    BLUEPRINT_MIN_DOWNSCALED_DIM_PX: Minimum dimension after downscale (default: 1200)

Author: Production Shop
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _get_int(name: str, default: int) -> int:
    """Get integer from env var with fallback to default."""
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class BlueprintLimits:
    """
    Immutable configuration for blueprint processing limits.

    All values are loaded from environment at import time.
    """
    max_upload_mb: int = _get_int("BLUEPRINT_MAX_UPLOAD_MB", 20)
    max_raster_dim_px: int = _get_int("BLUEPRINT_MAX_RASTER_DIM_PX", 4000)
    max_megapixels: int = _get_int("BLUEPRINT_MAX_MEGAPIXELS", 12)
    max_pdf_dpi: int = _get_int("BLUEPRINT_MAX_PDF_DPI", 150)
    min_downscaled_dim_px: int = _get_int("BLUEPRINT_MIN_DOWNSCALED_DIM_PX", 1200)

    @property
    def max_upload_bytes(self) -> int:
        """Max upload size in bytes."""
        return self.max_upload_mb * 1024 * 1024


# Singleton instance - values frozen at import time
LIMITS = BlueprintLimits()


class BlueprintGuardrailError(RuntimeError):
    """Raised when blueprint input fails guardrail validation."""
    pass
