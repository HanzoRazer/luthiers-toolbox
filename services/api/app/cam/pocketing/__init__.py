"""
CAM Pocketing Module

Adaptive pocket-clearing via the L.1 adaptive core, exposed through CamIntentV1
(Dev Order 8J). The schema/adapter import without shapely; feasibility (which needs
shapely) is imported behind a guard by the intent router.
"""
from .intent_schema import (
    PocketPointV1,
    PocketIslandV1,
    PocketDesignV1,
    validate_pocket_design,
)
from .intent_adapter import PocketIntentAdaptation, pocket_params_from_intent

__all__ = [
    "PocketPointV1",
    "PocketIslandV1",
    "PocketDesignV1",
    "validate_pocket_design",
    "PocketIntentAdaptation",
    "pocket_params_from_intent",
]
