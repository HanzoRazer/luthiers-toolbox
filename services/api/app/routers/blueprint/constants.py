"""
Blueprint Router Constants
==========================

Shared validation constants and configuration for blueprint processing.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Set

logger = logging.getLogger(__name__)

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

# Maximum file upload size in bytes (20 MB for blueprint images/PDFs)
MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024

# Allowed file extensions for blueprint upload
ALLOWED_EXTENSIONS: Set[str] = {'.pdf', '.png', '.jpg', '.jpeg'}

# Phase 2 image formats (OpenCV compatible)
PHASE2_EXTENSIONS: Set[str] = {'.png', '.jpg', '.jpeg'}

# Default SVG canvas dimensions (mm)
DEFAULT_SVG_WIDTH_MM: float = 300.0
DEFAULT_SVG_HEIGHT_MM: float = 200.0

# Phase 2 edge detection defaults
DEFAULT_EDGE_THRESHOLD_LOW: int = 50
DEFAULT_EDGE_THRESHOLD_HIGH: int = 150
DEFAULT_MIN_CONTOUR_AREA: float = 100.0

# Scale correction bounds (prevent extreme scaling)
MIN_SCALE_FACTOR: float = 0.1
MAX_SCALE_FACTOR: float = 10.0

# =============================================================================
# SERVICE PATH CONFIGURATION
# =============================================================================

# Add blueprint-import service to path
BLUEPRINT_SERVICE_PATH = Path(__file__).parent.parent.parent.parent.parent / "blueprint-import"
sys.path.insert(0, str(BLUEPRINT_SERVICE_PATH))

# =============================================================================
# PHASE 1 ANALYZER (AI-POWERED)
# =============================================================================

ANALYZER_AVAILABLE = True
ANALYZER_IMPORT_ERROR: Optional[str] = None

try:
    from analyzer import create_analyzer
except (ImportError, OSError) as e:
    ANALYZER_AVAILABLE = False
    ANALYZER_IMPORT_ERROR = f"{type(e).__name__}: {e}"
    create_analyzer = None  # type: ignore

# Phase 1 SVG Vectorizer - Optional (not in Docker image)
VECTORIZER_AVAILABLE = False
create_vectorizer = None  # type: ignore

try:
    from vectorizer import create_vectorizer
    VECTORIZER_AVAILABLE = True
except ImportError:
    pass

# =============================================================================
# PHASE 2 VECTORIZER (OPENCV-POWERED)
# =============================================================================

PHASE2_AVAILABLE = False
create_phase2_vectorizer = None  # type: ignore

try:
    from vectorizer_phase2 import create_phase2_vectorizer
    PHASE2_AVAILABLE = True
except ImportError:
    pass
