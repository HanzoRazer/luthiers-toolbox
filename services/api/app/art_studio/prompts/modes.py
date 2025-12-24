"""
Art Studio Mode System

Classifies prompts into UI modes for the Art Studio interface.
Each mode answers: "What job is Art Studio doing right now?"

Modes:
    - Create: Generate new artifacts (text → vector/relief)
    - Transform: Convert representations (image → heightmap → STL)
    - Optimize: Apply design lenses for better manufacturability
    - Validate: Feasibility gate for RMOS-compatible output
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ModeCategory(str, Enum):
    """Art Studio mode categories."""
    CREATE = "create"
    TRANSFORM = "transform"
    OPTIMIZE = "optimize"
    VALIDATE = "validate"


@dataclass
class ArtStudioMode:
    """
    Definition of an Art Studio mode.

    Attributes:
        mode_id: Unique identifier
        label: Display label for UI
        description: What this mode does
        category: Mode category (create/transform/optimize/validate)
        prompt_ids: List of prompt IDs available in this mode
        icon: Optional icon name for UI
        ui_controls: Optional dict of UI control configurations
    """
    mode_id: str
    label: str
    description: str
    category: ModeCategory
    prompt_ids: List[str]
    icon: Optional[str] = None
    ui_controls: Dict[str, any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "mode_id": self.mode_id,
            "label": self.label,
            "description": self.description,
            "category": self.category.value,
            "prompt_ids": self.prompt_ids,
            "icon": self.icon,
            "ui_controls": self.ui_controls,
        }


# =============================================================================
# MODE DEFINITIONS
# =============================================================================

MODE_CREATE = ArtStudioMode(
    mode_id="create",
    label="Create",
    description="Generate new CNC-ready artifacts from text descriptions or rebuild from reference photos.",
    category=ModeCategory.CREATE,
    prompt_ids=[
        "cnc_vector_from_text_v1",
        "cnc_vector_from_photo_manual_v1",
        "bas_relief_reference_image_v1",
    ],
    icon="plus-circle",
    ui_controls={
        "subject_input": {"type": "text", "required": True, "placeholder": "Describe your design..."},
        "units_select": {"type": "select", "options": ["in", "mm"], "default": "in"},
        "output_format": {"type": "select", "options": ["svg", "png"], "default": "svg"},
    },
)

MODE_TRANSFORM = ArtStudioMode(
    mode_id="transform",
    label="Transform",
    description="Convert between representations: grayscale image → heightmap → STL mesh.",
    category=ModeCategory.TRANSFORM,
    prompt_ids=[
        "heightmap_to_stl_conversion_v1",
    ],
    icon="refresh-cw",
    ui_controls={
        "image_upload": {"type": "file", "accept": "image/*", "required": True},
        "max_relief_height": {"type": "number", "default": 0.25, "min": 0.1, "max": 1.0, "step": 0.05},
        "base_thickness": {"type": "number", "default": 0.125, "min": 0.05, "max": 0.5, "step": 0.025},
    },
)

MODE_OPTIMIZE = ArtStudioMode(
    mode_id="optimize",
    label="Optimize",
    description="Apply design lenses to reframe your design for better manufacturability.",
    category=ModeCategory.OPTIMIZE,
    prompt_ids=[
        "lens_tool_first_v1",
        "lens_failure_first_v1",
        "lens_material_alive_v1",
        "lens_cam_operator_trust_v1",
        "lens_time_compression_v1",
        "lens_reverse_manufacturing_v1",
        "lens_negative_space_product_v1",
        "lens_one_bit_art_v1",
        "lens_legacy_artifact_v1",
    ],
    icon="sliders",
    ui_controls={
        "lens_select": {
            "type": "select",
            "required": True,
            "options": [
                {"value": "lens_tool_first_v1", "label": "Tool-First Design"},
                {"value": "lens_failure_first_v1", "label": "Failure-First Design"},
                {"value": "lens_material_alive_v1", "label": "Grain-Aware Design"},
                {"value": "lens_cam_operator_trust_v1", "label": "CAM Operator Trust"},
                {"value": "lens_time_compression_v1", "label": "Time Compression"},
                {"value": "lens_reverse_manufacturing_v1", "label": "Reverse Manufacturing"},
                {"value": "lens_negative_space_product_v1", "label": "Negative Space"},
                {"value": "lens_one_bit_art_v1", "label": "One-Bit Art"},
                {"value": "lens_legacy_artifact_v1", "label": "Legacy Artifact"},
            ],
        },
        "subject_input": {"type": "text", "required": True},
        "tool_diameter": {"type": "number", "default": 0.125, "min": 0.0625, "max": 0.5},
    },
)

MODE_VALIDATE = ArtStudioMode(
    mode_id="validate",
    label="Validate",
    description="Generate designs that pass automated feasibility checks (RMOS-compatible).",
    category=ModeCategory.VALIDATE,
    prompt_ids=[
        "lens_regulatory_feasibility_gate_v1",
    ],
    icon="check-circle",
    ui_controls={
        "subject_input": {"type": "text", "required": True},
        "output_mode": {"type": "select", "options": ["vector", "relief", "mesh"], "default": "vector"},
        "strict_mode": {"type": "checkbox", "default": True, "label": "Strict validation"},
    },
)

# All modes registry
_MODES: Dict[str, ArtStudioMode] = {
    "create": MODE_CREATE,
    "transform": MODE_TRANSFORM,
    "optimize": MODE_OPTIMIZE,
    "validate": MODE_VALIDATE,
}


# =============================================================================
# PUBLIC API
# =============================================================================

def get_mode(mode_id: str) -> ArtStudioMode:
    """
    Get a mode definition by ID.

    Args:
        mode_id: Mode identifier (create/transform/optimize/validate)

    Returns:
        ArtStudioMode definition

    Raises:
        KeyError: If mode not found
    """
    if mode_id not in _MODES:
        raise KeyError(f"Mode not found: {mode_id}. Available: {list(_MODES.keys())}")
    return _MODES[mode_id]


def list_modes() -> List[Dict]:
    """
    List all available modes for UI rendering.

    Returns:
        List of mode definitions as dicts
    """
    return [mode.to_dict() for mode in _MODES.values()]


def get_prompts_for_mode(mode_id: str) -> List[str]:
    """
    Get prompt IDs available in a mode.

    Args:
        mode_id: Mode identifier

    Returns:
        List of prompt IDs
    """
    mode = get_mode(mode_id)
    return mode.prompt_ids


def get_mode_for_prompt(prompt_id: str) -> Optional[ArtStudioMode]:
    """
    Find which mode contains a given prompt.

    Args:
        prompt_id: Prompt identifier

    Returns:
        ArtStudioMode or None if not found
    """
    for mode in _MODES.values():
        if prompt_id in mode.prompt_ids:
            return mode
    return None


# Lens descriptions for UI tooltips
LENS_DESCRIPTIONS = {
    "lens_tool_first_v1": "Design as if the cutting tool decides the geometry. Avoid sharp corners and fragile features.",
    "lens_failure_first_v1": "Anticipate machining failures and build robustness in. Consider tear-out, chatter, thin bridges.",
    "lens_material_alive_v1": "Design respecting grain direction and material behavior. Luthier thinking.",
    "lens_cam_operator_trust_v1": "Create geometry a CAM operator would immediately trust. Predictable and readable.",
    "lens_time_compression_v1": "Minimize machining time. Every feature must earn its cutting time.",
    "lens_reverse_manufacturing_v1": "Design backwards from the finished part to the sequence of cuts.",
    "lens_negative_space_product_v1": "Focus on removed material (voids) rather than remaining solids.",
    "lens_one_bit_art_v1": "Binary decisions only: cut/don't cut, deep/shallow. No ambiguity.",
    "lens_legacy_artifact_v1": "Self-explaining geometry that communicates intent without documentation.",
    "lens_regulatory_feasibility_gate_v1": "Pass automated feasibility checks. No undercuts, no unsupported islands.",
}


def get_lens_description(prompt_id: str) -> str:
    """Get human-readable description for a lens prompt."""
    return LENS_DESCRIPTIONS.get(prompt_id, "")
