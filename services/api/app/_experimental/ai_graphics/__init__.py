"""
AI Graphics Package

Provides AI-powered graphics and vision capabilities for guitar design.
Lives in advisory sandbox mode only - does NOT touch geometry or CAM execution.

Components:
    - schemas/: AI request/response models
    - services/: LLM client, parameter suggester, providers
    - sessions.py: Session memory for deduplication
    - api/: FastAPI routers (ai_routes, session_routes, vision_routes)
    - prompt_engine.py: Guitar prompt engineering
    - vocabulary.py: UI dropdowns vocabulary
    - image_transport.py: Image generation transport
    - image_providers.py: Multi-provider image generation
    - rosette_generator.py: Rosette-specific generation

Integration:
    - RMOS provides feasibility scoring (via public API)
    - Art Studio provides RosetteParamSpec
    - AI Graphics suggests parameters, RMOS validates them
    - Vision Engine generates guitar images (advisory only)
"""

# Session management
from .sessions import (
    AiSessionState,
    AiSuggestionRecord,
    fingerprint_spec,
    get_session,
    get_or_create_session,
    mark_explored,
    is_explored,
    reset_session,
)

# Prompt engineering (Vision Engine)
try:
    from .prompt_engine import (
        engineer_guitar_prompt,
        parse_guitar_request,
        get_prompt_variations,
        GuitarPrompt,
        ParsedGuitarRequest,
        GuitarCategory,
    )
except ImportError:
    pass

# Vocabulary (Vision Engine UI)
try:
    from .vocabulary import (
        BODY_SHAPES,
        FINISHES,
        WOODS,
        HARDWARE,
        INLAYS,
        PHOTOGRAPHY_STYLES,
        get_vocabulary_for_ui,
    )
except ImportError:
    pass

# Image providers (Vision Engine)
try:
    from .image_providers import (
        GuitarVisionEngine,
        ImageProvider,
        ImageSize,
        ImageQuality,
        ImageGenerationResult,
    )
except ImportError:
    pass

# Vision routes
try:
    from .api.vision_routes import router as vision_router
except ImportError:
    vision_router = None

__all__ = [
    # Session management
    "AiSessionState",
    "AiSuggestionRecord",
    "fingerprint_spec",
    "get_session",
    "get_or_create_session",
    "mark_explored",
    "is_explored",
    "reset_session",
    # Prompt engineering
    "engineer_guitar_prompt",
    "parse_guitar_request",
    "get_prompt_variations",
    "GuitarPrompt",
    "ParsedGuitarRequest",
    "GuitarCategory",
    # Vocabulary
    "BODY_SHAPES",
    "FINISHES",
    "WOODS",
    "HARDWARE",
    "INLAYS",
    "PHOTOGRAPHY_STYLES",
    "get_vocabulary_for_ui",
    # Image providers
    "GuitarVisionEngine",
    "ImageProvider",
    "ImageSize",
    "ImageQuality",
    "ImageGenerationResult",
    # Vision router
    "vision_router",
]
