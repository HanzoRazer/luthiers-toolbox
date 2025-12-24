"""
Art Studio CNC Prompt Library

Production-grade prompt system for CNC-oriented image/vector/relief generation.
Integrates with AI Platform (app.ai) for transport, safety, and observability.

Modes:
    - Create: Generate new artifacts from text or rebuild from photos
    - Transform: Convert representations (image → heightmap → STL)
    - Optimize: Apply design lenses (tool-first, failure-first, etc.)
    - Validate: Feasibility gate for RMOS-compatible output

Usage:
    from app.art_studio.prompts import (
        get_prompt,
        get_mode,
        list_modes,
        render_prompt,
        validate_output,
    )

    # Get a prompt by ID
    prompt = get_prompt("cnc_vector_from_text_v1")

    # Render with variables
    rendered = render_prompt("cnc_vector_from_text_v1", subject="fleur-de-lis")

    # Validate output
    result = validate_output("cnc_vector_from_text_v1", svg_content)
"""

from .modes import (
    ArtStudioMode,
    get_mode,
    list_modes,
    get_prompts_for_mode,
    MODE_CREATE,
    MODE_TRANSFORM,
    MODE_OPTIMIZE,
    MODE_VALIDATE,
)

from .validators import (
    validate_output,
    validate_svg,
    validate_heightmap,
    validate_stl,
    ValidationResult,
)

# Lazy load prompt pack to avoid startup overhead
_prompt_pack = None

def _load_prompt_pack():
    """Lazy load the prompt pack JSON."""
    global _prompt_pack
    if _prompt_pack is None:
        import json
        from pathlib import Path
        pack_path = Path(__file__).parent / "cnc_prompt_pack.json"
        with open(pack_path) as f:
            _prompt_pack = json.load(f)
    return _prompt_pack


def get_prompt(prompt_id: str) -> dict:
    """
    Get a prompt definition by ID.

    Args:
        prompt_id: The prompt identifier (e.g., "cnc_vector_from_text_v1")

    Returns:
        Prompt definition dict

    Raises:
        KeyError: If prompt not found
    """
    pack = _load_prompt_pack()
    for prompt in pack["prompts"]:
        if prompt["prompt_id"] == prompt_id:
            return prompt
    raise KeyError(f"Prompt not found: {prompt_id}")


def list_prompts() -> list:
    """List all available prompt IDs."""
    pack = _load_prompt_pack()
    return [p["prompt_id"] for p in pack["prompts"]]


def render_prompt(prompt_id: str, **variables) -> str:
    """
    Render a prompt template with variables.

    Args:
        prompt_id: The prompt identifier
        **variables: Template variables (subject, units, etc.)

    Returns:
        Rendered prompt string
    """
    prompt = get_prompt(prompt_id)
    template = prompt.get("template", "")

    # Apply defaults from inputs
    for inp in prompt.get("inputs", []):
        if inp["name"] not in variables and "default" in inp:
            variables[inp["name"]] = inp["default"]

    # Simple template substitution
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{key}}}", str(value))

    return rendered


def get_system_prompt(prompt_id: str) -> str:
    """Get the system prompt for a given prompt ID."""
    prompt = get_prompt(prompt_id)
    category = prompt.get("category", "")

    # Category-specific system prompts
    if category == "cnc_vector":
        return SYSTEM_PROMPT_VECTOR
    elif category in ("relief_image", "relief_conversion"):
        return SYSTEM_PROMPT_RELIEF
    elif category == "design_lens":
        return SYSTEM_PROMPT_LENS
    else:
        return SYSTEM_PROMPT_DEFAULT


# System prompts by category
SYSTEM_PROMPT_VECTOR = """You are a CNC manufacturing assistant specializing in vector graphics for laser cutting and CNC carving.
You produce clean, manufacturable SVG files with closed paths, consistent line weights, and no gradients.
All output must be suitable for direct import into CAM software (Fusion 360, VCarve, LightBurn)."""

SYSTEM_PROMPT_RELIEF = """You are a CNC manufacturing assistant specializing in bas-relief and height map generation.
You produce grayscale images where brightness maps to Z-depth, suitable for conversion to STL meshes.
White = raised surfaces, Black = recessed surfaces, smooth gradients for slopes."""

SYSTEM_PROMPT_LENS = """You are a design advisor helping reframe CNC projects through manufacturing lenses.
You consider tool constraints, failure modes, material behavior, and machining efficiency.
Your goal is to produce geometry that machines well, not just looks good."""

SYSTEM_PROMPT_DEFAULT = """You are a CNC manufacturing assistant for the Luthier's ToolBox.
You produce manufacturable designs suitable for guitar building and woodworking."""


__all__ = [
    # Prompt functions
    "get_prompt",
    "list_prompts",
    "render_prompt",
    "get_system_prompt",
    # Mode functions
    "ArtStudioMode",
    "get_mode",
    "list_modes",
    "get_prompts_for_mode",
    "MODE_CREATE",
    "MODE_TRANSFORM",
    "MODE_OPTIMIZE",
    "MODE_VALIDATE",
    # Validation
    "validate_output",
    "validate_svg",
    "validate_heightmap",
    "validate_stl",
    "ValidationResult",
]
