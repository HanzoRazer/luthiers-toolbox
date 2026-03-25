#!/usr/bin/env python3
"""
Rosette Image Generation Prompts

Corrected prompts for AI image generation (DALL-E, etc.) that render rosettes
accurately as thin, flat inlays flush with the guitar soundboard - not as
thick 3D rings or bracelets.

A real rosette is:
- Thin veneer (0.5-1.5mm thick)
- Flat, flush with the guitar top surface
- Inlaid into a shallow routed channel around the soundhole
- Delicate marquetry/mosaic work
- Part of the instrument, not a separate object
"""

from typing import Optional


def generate_rosette_prompt(
    pattern_description: str,
    wood_description: str,
    diameter_inches: float = 4.0,
    ring_width_mm: float = 6.0,
    top_wood: str = "spruce",
    style: str = "classical",
    additional_notes: Optional[str] = None,
) -> str:
    """
    Generate a corrected AI image prompt for rosette visualization.

    Shows the rosette as it actually appears: a thin, flat inlay flush
    with the guitar soundboard, not a raised 3D object.

    Args:
        pattern_description: Description of the mosaic/pattern design
        wood_description: Woods used in the rosette (e.g., "ebony and maple")
        diameter_inches: Soundhole diameter in inches
        ring_width_mm: Width of the rosette ring in mm
        top_wood: Guitar top wood species (spruce, cedar, etc.)
        style: Guitar style (classical, acoustic, flamenco)
        additional_notes: Any extra details to include

    Returns:
        Formatted prompt string for AI image generation

    Example:
        >>> prompt = generate_rosette_prompt(
        ...     pattern_description="Black and white checkerboard mosaic tiles",
        ...     wood_description="Black ebony and white holly",
        ...     diameter_inches=4.0,
        ...     style="classical"
        ... )
    """
    top_description = {
        "spruce": "light tan spruce wood with subtle vertical grain lines",
        "cedar": "warm reddish-brown western red cedar with fine grain",
        "redwood": "rich reddish redwood with tight vertical grain",
    }.get(top_wood, f"{top_wood} wood with natural grain")

    prompt = f"""
Photograph looking straight down at a {style} guitar soundhole from directly above.

The guitar top is made of {top_description}.
In the center is a dark circular soundhole (about {diameter_inches} inches diameter).

Surrounding the soundhole is a ROSETTE - a thin decorative ring inlaid FLUSH
into the {top_wood} top. The rosette is NOT raised or 3D - it is perfectly level
with the wood surface, like fine marquetry or wood inlay work.

ROSETTE PATTERN: {pattern_description}

WOODS USED: {wood_description}

CRITICAL DETAILS FOR ACCURACY:
- The rosette is FLAT, flush with the guitar top surface
- It is thin veneer inlay work, approximately 1mm thick
- The mosaic tiles/pieces are tiny, precise, and delicate
- Natural wood grain is visible in each small tile piece
- The rosette ring is about {ring_width_mm}mm wide
- Light reflects evenly across the flat surface - no 3D shadows
- The rosette is PART OF the guitar, not a separate object

CAMERA: Directly overhead, perpendicular to the guitar top
LIGHTING: Soft, even studio lighting showing the fine craftsmanship
STYLE: Professional luthier photography, fine instrument detail shot
"""

    if additional_notes:
        prompt += f"\nADDITIONAL: {additional_notes}\n"

    return prompt.strip()


def generate_isolated_rosette_prompt(
    pattern_description: str,
    wood_description: str,
    diameter_inches: float = 4.0,
    ring_width_mm: float = 6.0,
) -> str:
    """
    Generate prompt for an isolated rosette (not installed in guitar).

    Still shows the rosette as a thin, flat veneer piece - but laying
    on a neutral background rather than installed in an instrument.

    Args:
        pattern_description: Description of the pattern design
        wood_description: Woods used in the rosette
        diameter_inches: Outer diameter in inches
        ring_width_mm: Width of the ring in mm

    Returns:
        Formatted prompt string
    """
    return f"""
Professional product photograph of a guitar rosette, viewed from directly above,
laying flat on a neutral light gray background.

The rosette is a thin, flat decorative ring - a piece of wood veneer marquetry
about {diameter_inches} inches ({diameter_inches * 25.4:.0f}mm) in outer diameter
and approximately {ring_width_mm}mm wide.

IMPORTANT: This is THIN VENEER, only about 1-1.5mm thick. It should look like
a flat decorative disc/ring, NOT a thick 3D bracelet or chunky wooden ring.

PATTERN: {pattern_description}

WOODS: {wood_description}

The piece shows:
- Delicate, precise mosaic/inlay work
- Natural wood grain visible in each tile
- Perfectly flat surface (it's veneer, not carved wood)
- Crisp, clean edges
- The craftsmanship of traditional lutherie

CAMERA: Directly overhead
LIGHTING: Soft, even studio lighting
STYLE: Professional product photography, flat lay, isolated object
The rosette should look like a thin decorative veneer piece, ready to be
inlaid into a guitar top.
""".strip()


# Pre-built prompts for common rosette styles
PROMPT_TEMPLATES = {
    "spanish_mosaic": {
        "pattern": "Traditional Spanish mosaic with small geometric tiles arranged in concentric rings. Black and white alternating diamond or square shapes creating a classic checkerboard effect.",
        "woods": "Black African ebony tiles and white European holly or maple tiles",
    },
    "torres_diamond": {
        "pattern": "Antonio de Torres style diamond/lozenge mosaic. Diagonal arrangement of contrasting tiles creating a repeating diamond pattern around the ring.",
        "woods": "Black ebony and creamy white holly in high contrast",
    },
    "german_rope": {
        "pattern": "Traditional German twisted rope (Seil) pattern with three intertwined strands spiraling around the ring.",
        "woods": "Three colors of dyed wood veneer creating the braided rope effect",
    },
    "herringbone": {
        "pattern": "Herringbone or chevron pattern with diagonal strips arranged in alternating V-shapes around the circumference.",
        "woods": "Contrasting light and dark wood strips (maple and walnut, or similar)",
    },
    "simple_alternating": {
        "pattern": "Simple alternating trapezoidal segments around the ring - one light, one dark, repeating.",
        "woods": "Cherry (warm pinkish-tan) alternating with mahogany (reddish-brown)",
    },
}


def get_template_prompt(
    template_name: str,
    installed: bool = True,
    **kwargs
) -> str:
    """
    Get a pre-built prompt for common rosette styles.

    Args:
        template_name: One of the PROMPT_TEMPLATES keys
        installed: If True, show in guitar; if False, show isolated
        **kwargs: Override default parameters

    Returns:
        Formatted prompt string
    """
    if template_name not in PROMPT_TEMPLATES:
        available = ", ".join(PROMPT_TEMPLATES.keys())
        raise ValueError(f"Unknown template '{template_name}'. Available: {available}")

    template = PROMPT_TEMPLATES[template_name]

    if installed:
        return generate_rosette_prompt(
            pattern_description=template["pattern"],
            wood_description=template["woods"],
            **kwargs
        )
    else:
        return generate_isolated_rosette_prompt(
            pattern_description=template["pattern"],
            wood_description=template["woods"],
            **kwargs
        )
