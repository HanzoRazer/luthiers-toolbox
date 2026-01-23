#!/usr/bin/env python3
"""
Guitar Vision Engine — Prompt Engineering Layer

Transforms casual user input into optimized image generation prompts.
This is the "brain" that makes any image model produce good guitars.

"green les paul" → Full professional product photography prompt

Author: Luthier's ToolBox
Date: December 16, 2025
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# GUITAR VOCABULARY — The Knowledge Base
# =============================================================================

class GuitarCategory(str, Enum):
    ACOUSTIC = "acoustic"
    ELECTRIC = "electric"
    CLASSICAL = "classical"
    BASS = "bass"
    UNKNOWN = "unknown"


BODY_SHAPES = {
    # Acoustic
    "dreadnought": GuitarCategory.ACOUSTIC,
    "grand auditorium": GuitarCategory.ACOUSTIC,
    "auditorium": GuitarCategory.ACOUSTIC,
    "parlor": GuitarCategory.ACOUSTIC,
    "parlour": GuitarCategory.ACOUSTIC,
    "jumbo": GuitarCategory.ACOUSTIC,
    "concert": GuitarCategory.ACOUSTIC,
    "orchestra model": GuitarCategory.ACOUSTIC,
    "om": GuitarCategory.ACOUSTIC,
    "000": GuitarCategory.ACOUSTIC,
    "triple-o": GuitarCategory.ACOUSTIC,
    "00": GuitarCategory.ACOUSTIC,
    "double-o": GuitarCategory.ACOUSTIC,
    "slope shoulder": GuitarCategory.ACOUSTIC,
    "round shoulder": GuitarCategory.ACOUSTIC,
    "cutaway acoustic": GuitarCategory.ACOUSTIC,
    
    # Electric
    "les paul": GuitarCategory.ELECTRIC,
    "stratocaster": GuitarCategory.ELECTRIC,
    "strat": GuitarCategory.ELECTRIC,
    "telecaster": GuitarCategory.ELECTRIC,
    "tele": GuitarCategory.ELECTRIC,
    "sg": GuitarCategory.ELECTRIC,
    "flying v": GuitarCategory.ELECTRIC,
    "explorer": GuitarCategory.ELECTRIC,
    "firebird": GuitarCategory.ELECTRIC,
    "jazzmaster": GuitarCategory.ELECTRIC,
    "jaguar": GuitarCategory.ELECTRIC,
    "offset": GuitarCategory.ELECTRIC,
    "semi-hollow": GuitarCategory.ELECTRIC,
    "hollow body": GuitarCategory.ELECTRIC,
    "es-335": GuitarCategory.ELECTRIC,
    "335": GuitarCategory.ELECTRIC,
    "es-175": GuitarCategory.ELECTRIC,
    "superstrat": GuitarCategory.ELECTRIC,
    "prs": GuitarCategory.ELECTRIC,
    "paul reed smith": GuitarCategory.ELECTRIC,
    "v-shape": GuitarCategory.ELECTRIC,
    "modern": GuitarCategory.ELECTRIC,
    "shred": GuitarCategory.ELECTRIC,
    "headless": GuitarCategory.ELECTRIC,
    
    # Classical
    "classical": GuitarCategory.CLASSICAL,
    "nylon string": GuitarCategory.CLASSICAL,
    "flamenco": GuitarCategory.CLASSICAL,
    "requinto": GuitarCategory.CLASSICAL,
    "spanish guitar": GuitarCategory.CLASSICAL,
    
    # Bass
    "precision bass": GuitarCategory.BASS,
    "p-bass": GuitarCategory.BASS,
    "jazz bass": GuitarCategory.BASS,
    "j-bass": GuitarCategory.BASS,
    "thunderbird": GuitarCategory.BASS,
    "bass": GuitarCategory.BASS,
}

# Normalize variations
BODY_SHAPE_ALIASES = {
    "strat": "Fender Stratocaster",
    "tele": "Fender Telecaster",
    "lp": "Gibson Les Paul",
    "les paul": "Gibson Les Paul",
    "sg": "Gibson SG",
    "335": "Gibson ES-335 semi-hollow body",
    "es-335": "Gibson ES-335 semi-hollow body",
    "prs": "PRS Custom 24",
    "flying v": "Gibson Flying V",
    "explorer": "Gibson Explorer",
    "jazzmaster": "Fender Jazzmaster offset",
    "jaguar": "Fender Jaguar offset",
    "dreadnought": "Martin-style dreadnought acoustic",
    "grand auditorium": "Taylor-style grand auditorium acoustic",
    "parlor": "vintage parlor acoustic",
    "jumbo": "Gibson-style jumbo acoustic",
    "classical": "Spanish classical nylon-string",
    "flamenco": "traditional flamenco",
    "p-bass": "Fender Precision Bass",
    "j-bass": "Fender Jazz Bass",
}

FINISHES = {
    # Solid colors
    "black": "gloss black",
    "white": "olympic white",
    "cream": "vintage cream",
    "red": "candy apple red",
    "blue": "lake placid blue",
    "green": "sherwood green",
    "yellow": "TV yellow",
    "orange": "competition orange",
    "purple": "deep purple",
    "pink": "shell pink",
    "natural": "natural wood finish",
    "blonde": "butterscotch blonde",
    
    # Bursts
    "sunburst": "three-tone sunburst",
    "tobacco burst": "tobacco sunburst",
    "tobacco sunburst": "tobacco sunburst",
    "cherry burst": "cherry sunburst",
    "cherry sunburst": "cherry sunburst",
    "honey burst": "honey burst",
    "honeyburst": "honey burst",
    "lemon burst": "lemon burst",
    "iced tea": "iced tea burst",
    "heritage cherry": "heritage cherry sunburst",
    
    # Transparent / See-through
    "transparent": "transparent",
    "trans red": "transparent cherry red",
    "trans blue": "transparent blue",
    "emerald": "transparent emerald green",
    "emerald green": "transparent emerald green",
    "amber": "transparent amber",
    "vintage amber": "vintage amber transparent",
    "wine red": "transparent wine red",
    "ocean blue": "transparent ocean blue",
    
    # Metallic
    "gold": "gold top",
    "gold top": "gold top",
    "goldtop": "gold top",
    "silver": "silver metallic",
    "silverburst": "silverburst",
    "champagne": "champagne sparkle",
    "gunmetal": "gunmetal gray metallic",
    
    # Figured wood
    "quilted": "quilted maple top",
    "quilt": "quilted maple top",
    "flame": "flame maple top",
    "flamed": "flame maple top",
    "figured": "figured maple top",
    "spalted": "spalted maple top",
    "burl": "burl maple top",
    "bookmatched": "bookmatched figured wood top",
    
    # Special
    "relic": "aged relic finish",
    "aged": "vintage aged finish",
    "satin": "satin finish",
    "matte": "matte finish",
    "nitro": "nitrocellulose lacquer finish",
}

WOODS = {
    # Tops
    "spruce": "solid Sitka spruce top",
    "sitka": "solid Sitka spruce top",
    "engelmann": "solid Engelmann spruce top",
    "adirondack": "solid Adirondack spruce top",
    "cedar": "solid Western red cedar top",
    "redwood": "solid redwood top",
    "maple top": "carved maple top",
    "koa top": "Hawaiian koa top",
    
    # Back & Sides
    "mahogany": "solid mahogany back and sides",
    "rosewood": "solid East Indian rosewood back and sides",
    "brazilian": "solid Brazilian rosewood back and sides",
    "maple": "solid maple back and sides",
    "koa": "solid Hawaiian koa back and sides",
    "walnut": "solid black walnut back and sides",
    "sapele": "solid sapele back and sides",
    "ovangkol": "solid ovangkol back and sides",
    "cocobolo": "solid cocobolo back and sides",
    
    # Necks
    "maple neck": "one-piece maple neck",
    "mahogany neck": "mahogany neck",
    "roasted maple": "roasted maple neck",
    "quartersawn": "quartersawn maple neck",
    
    # Fretboards
    "rosewood fretboard": "Indian rosewood fretboard",
    "ebony": "ebony fretboard",
    "ebony fretboard": "ebony fretboard",
    "maple fretboard": "maple fretboard",
    "pau ferro": "pau ferro fretboard",
    "richlite": "richlite fretboard",
    "baked maple": "baked maple fretboard",
}

HARDWARE = {
    # Colors
    "chrome": "chrome hardware",
    "gold hardware": "gold hardware",
    "black hardware": "black hardware",
    "nickel": "aged nickel hardware",
    "aged": "aged nickel hardware",
    "relic hardware": "aged relic hardware",
    
    # Tuners
    "vintage tuners": "vintage-style open-back tuners",
    "locking tuners": "locking tuners",
    "grover": "Grover tuners",
    "kluson": "Kluson vintage tuners",
    
    # Bridges
    "tune-o-matic": "tune-o-matic bridge",
    "tom": "tune-o-matic bridge with stopbar tailpiece",
    "wraparound": "wraparound bridge",
    "floyd rose": "Floyd Rose locking tremolo",
    "floyd": "Floyd Rose locking tremolo",
    "bigsby": "Bigsby vibrato tailpiece",
    "hardtail": "hardtail bridge",
    "tremolo": "vintage tremolo bridge",
    "synchronized tremolo": "synchronized tremolo bridge",
    
    # Pickups
    "humbucker": "dual humbucker pickups",
    "humbuckers": "dual humbucker pickups",
    "p90": "P-90 single coil pickups",
    "p-90": "P-90 single coil pickups",
    "single coil": "single coil pickups",
    "hss": "HSS pickup configuration",
    "hsh": "HSH pickup configuration",
    "soapbar": "soapbar P-90 pickups",
    "mini humbucker": "mini humbucker pickups",
    "filtertron": "Filtertron pickups",
    "active": "active pickups",
    "passive": "passive pickups",
}

INLAYS = {
    # Fretboard
    "dots": "mother of pearl dot inlays",
    "dot inlays": "mother of pearl dot inlays",
    "blocks": "pearloid block inlays",
    "block inlays": "pearloid block inlays",
    "trapezoids": "trapezoid inlays",
    "trapezoid": "trapezoid inlays",
    "birds": "PRS bird inlays",
    "bird inlays": "PRS bird inlays",
    "vines": "tree of life vine inlays",
    "vine inlays": "tree of life vine inlays",
    "crown": "crown inlays",
    "shark fin": "shark fin inlays",
    "custom inlays": "custom artistic inlays",
    "no inlays": "unmarked fretboard with side dots only",
    "blank fretboard": "unmarked ebony fretboard",
    
    # Rosette (acoustic)
    "abalone": "abalone shell rosette",
    "abalone rosette": "abalone shell rosette inlay",
    "herringbone": "herringbone purfling and rosette",
    "wood rosette": "wood mosaic rosette",
    "mosaic": "traditional Spanish mosaic rosette",
    "rope": "rope pattern rosette",
    "simple rosette": "simple concentric ring rosette",
    
    # Binding
    "binding": "cream binding",
    "cream binding": "vintage cream binding",
    "black binding": "black binding",
    "abalone binding": "abalone shell binding",
    "no binding": "unbound body",
    "multi-ply": "multi-ply binding",
}

PHOTOGRAPHY_STYLES = {
    "product": "professional product photography, studio lighting, clean background, 8K resolution, highly detailed",
    "dramatic": "dramatic side lighting, dark background, moody atmosphere, professional photography",
    "lifestyle": "lifestyle shot, guitar on wooden floor, natural window light, cozy atmosphere",
    "studio": "professional studio photography, softbox lighting, gradient background",
    "vintage": "vintage photography style, warm tones, film grain, nostalgic lighting",
    "hero": "hero shot, low angle, dramatic lighting, powerful composition",
    "floating": "product floating on pure white background, soft shadows, commercial photography",
    "artistic": "artistic photography, creative lighting, unique angles, fine art style",
    "catalog": "clean catalog photography, neutral background, even lighting, true-to-life colors",
    "player": "musician playing guitar, action shot, stage lighting, live performance feel",
}


# =============================================================================
# PROMPT PARSER — Extract Intent from User Input
# =============================================================================

@dataclass
class ParsedGuitarRequest:
    """Structured representation of user's guitar request."""
    original_input: str
    
    # Detected attributes
    category: GuitarCategory = GuitarCategory.UNKNOWN
    body_shape: Optional[str] = None
    body_shape_expanded: Optional[str] = None
    
    finish: Optional[str] = None
    finish_expanded: Optional[str] = None
    
    woods: List[str] = field(default_factory=list)
    woods_expanded: List[str] = field(default_factory=list)
    
    hardware: List[str] = field(default_factory=list)
    hardware_expanded: List[str] = field(default_factory=list)
    
    inlays: List[str] = field(default_factory=list)
    inlays_expanded: List[str] = field(default_factory=list)
    
    # Photography style
    photo_style: str = "product"
    
    # Unrecognized terms (pass through)
    custom_terms: List[str] = field(default_factory=list)
    
    # Confidence
    confidence: float = 0.0


def parse_guitar_request(user_input: str) -> ParsedGuitarRequest:
    """
    Parse casual user input and extract guitar attributes.
    
    Examples:
        "green les paul" → body_shape="les paul", finish="green"
        "sunburst acoustic with abalone" → category=ACOUSTIC, finish="sunburst", inlays=["abalone"]
    """
    result = ParsedGuitarRequest(original_input=user_input)
    input_lower = user_input.lower()
    matched_terms: Set[str] = set()
    
    # 1. Find body shape (highest priority)
    for shape, category in BODY_SHAPES.items():
        if shape in input_lower:
            result.body_shape = shape
            result.category = category
            result.body_shape_expanded = BODY_SHAPE_ALIASES.get(shape, shape)
            matched_terms.add(shape)
            break
    
    # 2. Find finish
    for finish_key, finish_expanded in FINISHES.items():
        if finish_key in input_lower and finish_key not in matched_terms:
            result.finish = finish_key
            result.finish_expanded = finish_expanded
            matched_terms.add(finish_key)
            break
    
    # 3. Find woods
    for wood_key, wood_expanded in WOODS.items():
        if wood_key in input_lower and wood_key not in matched_terms:
            result.woods.append(wood_key)
            result.woods_expanded.append(wood_expanded)
            matched_terms.add(wood_key)
    
    # 4. Find hardware
    for hw_key, hw_expanded in HARDWARE.items():
        if hw_key in input_lower and hw_key not in matched_terms:
            result.hardware.append(hw_key)
            result.hardware_expanded.append(hw_expanded)
            matched_terms.add(hw_key)
    
    # 5. Find inlays
    for inlay_key, inlay_expanded in INLAYS.items():
        if inlay_key in input_lower and inlay_key not in matched_terms:
            result.inlays.append(inlay_key)
            result.inlays_expanded.append(inlay_expanded)
            matched_terms.add(inlay_key)
    
    # 6. Detect photo style hints
    style_hints = {
        "dramatic": "dramatic",
        "moody": "dramatic",
        "dark": "dramatic",
        "vintage": "vintage",
        "retro": "vintage",
        "lifestyle": "lifestyle",
        "playing": "player",
        "action": "player",
        "floating": "floating",
        "catalog": "catalog",
        "artistic": "artistic",
    }
    for hint, style in style_hints.items():
        if hint in input_lower:
            result.photo_style = style
            matched_terms.add(hint)
            break
    
    # 7. Infer category if not detected
    if result.category == GuitarCategory.UNKNOWN:
        acoustic_hints = ["acoustic", "folk", "fingerstyle", "unplugged", "rosette", "soundhole"]
        electric_hints = ["electric", "amp", "distortion", "shred", "rock", "metal", "pickup"]
        classical_hints = ["classical", "nylon", "spanish", "flamenco"]
        bass_hints = ["bass", "4-string", "5-string", "low end"]
        
        for hint in acoustic_hints:
            if hint in input_lower:
                result.category = GuitarCategory.ACOUSTIC
                break
        for hint in electric_hints:
            if hint in input_lower:
                result.category = GuitarCategory.ELECTRIC
                break
        for hint in classical_hints:
            if hint in input_lower:
                result.category = GuitarCategory.CLASSICAL
                break
        for hint in bass_hints:
            if hint in input_lower:
                result.category = GuitarCategory.BASS
                break
    
    # 8. Extract unmatched terms as custom
    words = re.findall(r'\b\w+\b', input_lower)
    stopwords = {'a', 'an', 'the', 'with', 'and', 'or', 'guitar', 'please', 'make', 'create', 'design', 'show', 'me', 'i', 'want'}
    for word in words:
        if word not in matched_terms and word not in stopwords and len(word) > 2:
            # Check if it's part of a multi-word match
            is_part_of_match = any(word in term for term in matched_terms)
            if not is_part_of_match:
                result.custom_terms.append(word)
    
    # 9. Calculate confidence
    matches = sum([
        1 if result.body_shape else 0,
        1 if result.finish else 0,
        len(result.woods) * 0.5,
        len(result.hardware) * 0.3,
        len(result.inlays) * 0.3,
    ])
    result.confidence = min(1.0, matches / 3.0)  # Normalize to 0-1
    
    return result


# =============================================================================
# PROMPT BUILDER — Construct Optimized Prompts
# =============================================================================

@dataclass
class GuitarPrompt:
    """Generated prompt ready for image models."""
    # Main prompt
    positive_prompt: str
    
    # Negative prompt (things to avoid)
    negative_prompt: str
    
    # Metadata
    parsed_request: ParsedGuitarRequest
    model_hints: Dict[str, Any] = field(default_factory=dict)


def build_guitar_prompt(
    parsed: ParsedGuitarRequest,
    photo_style: Optional[str] = None,
    enhance_quality: bool = True,
    model_target: str = "general",  # "dalle", "sdxl", "midjourney"
) -> GuitarPrompt:
    """
    Build optimized prompt from parsed request.
    
    Args:
        parsed: ParsedGuitarRequest from parser
        photo_style: Override photo style
        enhance_quality: Add quality boosters
        model_target: Optimize for specific model
    
    Returns:
        GuitarPrompt with positive and negative prompts
    """
    parts: List[str] = []
    
    # 1. Photography style prefix
    style = photo_style or parsed.photo_style
    style_text = PHOTOGRAPHY_STYLES.get(style, PHOTOGRAPHY_STYLES["product"])
    parts.append(style_text)
    
    # 2. Main subject
    if parsed.body_shape_expanded:
        parts.append(f"{parsed.body_shape_expanded} guitar")
    elif parsed.category != GuitarCategory.UNKNOWN:
        parts.append(f"{parsed.category.value} guitar")
    else:
        parts.append("guitar")
    
    # 3. Finish
    if parsed.finish_expanded:
        parts.append(parsed.finish_expanded)
    
    # 4. Woods
    for wood in parsed.woods_expanded:
        parts.append(wood)
    
    # 5. Hardware
    for hw in parsed.hardware_expanded:
        parts.append(hw)
    
    # 6. Inlays
    for inlay in parsed.inlays_expanded:
        parts.append(inlay)
    
    # 7. Custom terms (pass through)
    if parsed.custom_terms:
        parts.append(", ".join(parsed.custom_terms))
    
    # 8. Quality enhancers
    if enhance_quality:
        quality_terms = [
            "masterfully crafted",
            "exquisite detail",
            "professional instrument",
        ]
        parts.extend(quality_terms[:2])  # Don't overdo it
    
    # 9. Model-specific optimizations
    if model_target == "dalle":
        # DALL-E likes natural language
        positive = f"A {', '.join(parts)}"
    elif model_target == "sdxl":
        # SD likes comma-separated tags
        positive = ", ".join(parts)
    elif model_target == "midjourney":
        # Midjourney likes specific style tags
        parts.append("--v 6")
        parts.append("--style raw")
        positive = ", ".join(parts)
    else:
        positive = ", ".join(parts)
    
    # 10. Negative prompt
    negative_parts = [
        "blurry",
        "low quality",
        "distorted",
        "wrong proportions",
        "extra strings",
        "missing strings",
        "broken",
        "cartoon",
        "anime",
        "drawing",
        "sketch",
        "watermark",
        "text",
        "signature",
        "deformed frets",
        "wrong number of frets",
        "extra tuners",
        "missing tuners",
        "bad anatomy",
        "poorly drawn",
    ]
    negative = ", ".join(negative_parts)
    
    return GuitarPrompt(
        positive_prompt=positive,
        negative_prompt=negative,
        parsed_request=parsed,
        model_hints={
            "style": style,
            "category": parsed.category.value,
            "confidence": parsed.confidence,
            "model_target": model_target,
        }
    )


# =============================================================================
# HIGH-LEVEL API
# =============================================================================

def engineer_guitar_prompt(
    user_input: str,
    photo_style: Optional[str] = None,
    model_target: str = "general",
) -> GuitarPrompt:
    """
    Main entry point: Transform user input to optimized prompt.
    
    Examples:
        >>> prompt = engineer_guitar_prompt("green les paul gold hardware")
        >>> print(prompt.positive_prompt)
        professional product photography, studio lighting, clean background,
        8K resolution, highly detailed, Gibson Les Paul guitar, transparent
        emerald green, gold hardware, masterfully crafted, exquisite detail
    """
    parsed = parse_guitar_request(user_input)
    return build_guitar_prompt(parsed, photo_style=photo_style, model_target=model_target)


def get_prompt_variations(
    user_input: str,
    count: int = 4,
) -> List[GuitarPrompt]:
    """
    Generate multiple prompt variations for the same request.
    Useful for generating diverse images.
    """
    parsed = parse_guitar_request(user_input)
    
    styles = ["product", "dramatic", "lifestyle", "hero"]
    variations = []
    
    for i in range(min(count, len(styles))):
        prompt = build_guitar_prompt(parsed, photo_style=styles[i])
        variations.append(prompt)
    
    return variations


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demo the prompt engineering layer."""
    print("=" * 70)
    print("GUITAR VISION ENGINE — Prompt Engineering Demo")
    print("=" * 70)
    
    test_inputs = [
        "green les paul",
        "sunburst acoustic with abalone rosette",
        "black telecaster with maple fretboard",
        "emerald green prs with gold hardware birds inlays",
        "vintage dreadnought mahogany herringbone",
        "modern shred guitar floyd rose",
        "classical spanish guitar cedar top",
        "tobacco burst 335 with cream binding",
        "white strat with rosewood fretboard",
    ]
    
    for user_input in test_inputs:
        print(f"\n{'─'*70}")
        print(f"INPUT: \"{user_input}\"")
        print("─" * 70)
        
        prompt = engineer_guitar_prompt(user_input)
        parsed = prompt.parsed_request
        
        print(f"\n📋 PARSED:")
        print(f"   Category: {parsed.category.value}")
        print(f"   Body: {parsed.body_shape} → {parsed.body_shape_expanded}")
        print(f"   Finish: {parsed.finish} → {parsed.finish_expanded}")
        if parsed.woods:
            print(f"   Woods: {parsed.woods}")
        if parsed.hardware:
            print(f"   Hardware: {parsed.hardware}")
        if parsed.inlays:
            print(f"   Inlays: {parsed.inlays}")
        if parsed.custom_terms:
            print(f"   Custom: {parsed.custom_terms}")
        print(f"   Confidence: {parsed.confidence:.1%}")
        
        print(f"\n✅ POSITIVE PROMPT:")
        print(f"   {prompt.positive_prompt[:200]}...")
        
        print(f"\n❌ NEGATIVE PROMPT:")
        print(f"   {prompt.negative_prompt[:100]}...")
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo()

# =============================================================================
# BACKWARD COMPATIBILITY RE-EXPORT
# Import from canonical app.vision.prompt_engine for the new PromptPreview API
# =============================================================================
from app.vision.prompt_engine import *  # noqa: F401,F403
