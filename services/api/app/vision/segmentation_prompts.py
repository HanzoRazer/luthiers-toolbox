"""
Guitar Segmentation Prompts for Vision AI

Specialized prompts for extracting guitar body outlines from images
using GPT-4o Vision.

DATE: January 2026
"""
from __future__ import annotations

from typing import Dict, Any


# ---------------------------------------------------------------------------
# Core Segmentation Prompt
# ---------------------------------------------------------------------------

GUITAR_BODY_SEGMENTATION_PROMPT = """Analyze this image of a guitar and extract the body outline as a polygon.

TASK: Trace the outer edge of the guitar BODY only (not the neck or headstock).

INSTRUCTIONS:
1. Identify the guitar body shape (the large resonating chamber or solid body)
2. Trace the outer perimeter as a series of (x, y) pixel coordinates
3. Use image coordinates: origin is TOP-LEFT, x increases rightward, y increases downward
4. Provide 60-120 points to capture curves accurately
5. Go CLOCKWISE around the body starting from the top-center
6. The polygon must be closed (last point should be same as first point)
7. Exclude: neck, headstock, tuners, pickups, bridge, strings, controls

RESPOND WITH JSON ONLY:
{
  "body_outline": [[x1, y1], [x2, y2], ...],
  "image_width": <detected image width in pixels>,
  "image_height": <detected image height in pixels>,
  "confidence": <0.0 to 1.0>,
  "guitar_type": "les_paul" | "stratocaster" | "telecaster" | "sg" | "flying_v" | "explorer" | "dreadnought" | "classical" | "jumbo" | "parlor" | "archtop" | "semi_hollow" | "other",
  "notes": "<brief description of what was detected>"
}

If no guitar body is visible or the image is too unclear:
{
  "error": "<description of the issue>",
  "confidence": 0.0
}"""


# ---------------------------------------------------------------------------
# Alternative Prompts for Specific Use Cases
# ---------------------------------------------------------------------------

ACOUSTIC_BODY_PROMPT = """Analyze this image of an ACOUSTIC guitar and extract the body outline.

Focus on the curved soundboard/top outline. Acoustic guitar bodies have:
- Rounded upper bout (shoulders)
- Narrow waist
- Larger lower bout
- Soundhole (ignore this - trace around it)

Return the OUTER EDGE only as pixel coordinates.

{
  "body_outline": [[x1, y1], [x2, y2], ...],
  "image_width": <pixels>,
  "image_height": <pixels>,
  "confidence": <0.0-1.0>,
  "guitar_type": "dreadnought" | "classical" | "jumbo" | "parlor" | "concert" | "auditorium" | "other",
  "notes": "<observations>"
}"""


ELECTRIC_BODY_PROMPT = """Analyze this image of an ELECTRIC guitar and extract the body outline.

Electric guitar bodies have distinctive shapes:
- Les Paul: Rounded single-cutaway
- Stratocaster: Contoured double-cutaway with horns
- Telecaster: Simple single-cutaway slab
- SG: Thin double-cutaway with pointed horns
- Flying V: Angular V-shape
- Explorer: Angular asymmetric

Return the OUTER BODY EDGE only. Exclude neck pocket, control cavities, pickups.

{
  "body_outline": [[x1, y1], [x2, y2], ...],
  "image_width": <pixels>,
  "image_height": <pixels>,
  "confidence": <0.0-1.0>,
  "guitar_type": "les_paul" | "stratocaster" | "telecaster" | "sg" | "flying_v" | "explorer" | "jazzmaster" | "jaguar" | "other",
  "notes": "<observations>"
}"""




OTHER_INSTRUMENT_PROMPT = """Analyze this image of a stringed instrument and extract the body outline as a polygon.

TASK: Trace the outer edge of the instrument BODY only (not the neck, headstock, or fingerboard).

This may be a mandolin, banjo, ukulele, bouzouki, or other stringed instrument - NOT necessarily a guitar.

INSTRUCTIONS:
1. Identify the body shape (the resonating chamber or soundboard)
2. Trace the outer perimeter as a series of (x, y) pixel coordinates
3. Use image coordinates: origin is TOP-LEFT, x increases rightward, y increases downward
4. Provide 40-100 points to capture curves accurately
5. Go CLOCKWISE around the body starting from the top-center
6. The polygon must be closed (last point should be same as first point)
7. Exclude: neck, headstock, tuners, frets, bridge, strings, controls, soundhole

RESPOND WITH JSON ONLY:
{
  "body_outline": [[x1, y1], [x2, y2], ...],
  "image_width": <detected image width in pixels>,
  "image_height": <detected image height in pixels>,
  "confidence": <0.0 to 1.0>,
  "guitar_type": "mandolin" | "banjo" | "ukulele" | "bouzouki" | "lute" | "other",
  "notes": "<brief description of what was detected>"
}

If no instrument body is visible or the image is too unclear:
{
  "error": "<description of the issue>",
  "confidence": 0.0
}"""

# ---------------------------------------------------------------------------
# Blueprint/Technical Drawing Prompt
# ---------------------------------------------------------------------------

BLUEPRINT_BODY_PROMPT = """Analyze this TECHNICAL DRAWING / BLUEPRINT of an electric guitar body.

CRITICAL DISTINCTION - THIS IS A TECHNICAL DRAWING, NOT A PHOTO:
- Technical drawings show the body outline PLUS internal routing cavities
- You must trace ONLY the OUTERMOST perimeter - the external silhouette
- The outermost line is the LARGEST continuous closed curve in the drawing

WHAT TO TRACE (the outer body silhouette):
- The single continuous line forming the guitar body's external shape
- This is typically a thick black line forming the body perimeter
- It should be approximately 340-500mm in one dimension

WHAT TO IGNORE (internal features):
- Pickup routing cavities (rectangular cutouts)
- Control cavity routing (irregular shapes)
- Tremolo/bridge pocket (rectangular or curved cutout)
- Neck pocket (rectangular cutout at top)
- Screw holes (small circles)
- Jack hole (small circle)
- Dimension lines (lines with arrows and measurements)
- Radius callouts (R4, R8, etc.)
- Centerlines (dashed lines)
- Title blocks and text
- Pickguard outlines (if shown separately)

COORDINATES:
- Use image coordinates: origin is TOP-LEFT
- x increases rightward, y increases downward
- Provide 60-100 points for smooth curves
- Go CLOCKWISE starting from top-center (neck pocket area)

RESPOND WITH JSON ONLY:
{
  "body_outline": [[x1, y1], [x2, y2], ...],
  "image_width": <pixels>,
  "image_height": <pixels>,
  "confidence": <0.0-1.0>,
  "guitar_type": "jazzmaster" | "jaguar" | "stratocaster" | "telecaster" | "les_paul" | "sg" | "other",
  "notes": "<what was identified>"
}"""


# ---------------------------------------------------------------------------
# Prompt Selection
# ---------------------------------------------------------------------------

def get_segmentation_prompt(
    guitar_category: str = "auto",
    _detail_level: str = "standard"
) -> str:
    """
    Get the appropriate segmentation prompt.

    Args:
        guitar_category: "acoustic", "electric", "blueprint", "other", or "auto"
        detail_level: "minimal", "standard", or "detailed"

    Returns:
        Prompt string for vision API
    """
    if guitar_category == "acoustic":
        return ACOUSTIC_BODY_PROMPT
    elif guitar_category == "electric":
        return ELECTRIC_BODY_PROMPT
    elif guitar_category == "blueprint":
        return BLUEPRINT_BODY_PROMPT
    elif guitar_category == "other":
        return OTHER_INSTRUMENT_PROMPT
    else:
        return GUITAR_BODY_SEGMENTATION_PROMPT


# ---------------------------------------------------------------------------
# Response Validation
# ---------------------------------------------------------------------------

def validate_segmentation_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize segmentation response.

    Args:
        response: Raw response from vision API

    Returns:
        Validated response dict

    Raises:
        ValueError: If response is invalid
    """
    if "error" in response:
        return response

    required_fields = ["body_outline", "confidence"]
    for field in required_fields:
        if field not in response:
            raise ValueError(f"Missing required field: {field}")

    outline = response["body_outline"]
    if not isinstance(outline, list) or len(outline) < 3:
        raise ValueError(f"body_outline must be a list with at least 3 points, got {len(outline) if isinstance(outline, list) else type(outline)}")

    for i, point in enumerate(outline):
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(f"Point {i} must be [x, y], got {point}")
        try:
            x, y = float(point[0]), float(point[1])
            if x < 0 or y < 0:
                raise ValueError(f"Point {i} has negative coordinates: [{x}, {y}]")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Point {i} has invalid coordinates: {point}") from e

    confidence = response.get("confidence", 0)
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError(f"confidence must be between 0 and 1, got {confidence}")

    return response
