#!/usr/bin/env python3
"""Headstock Inlay Art Prompt Module"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class HeadstockStyle(str, Enum):
    """Common headstock shapes."""
    LES_PAUL = "les_paul"           # Gibson open-book
    STRATOCASTER = "stratocaster"   # Fender 6-in-line
    TELECASTER = "telecaster"       # Fender 6-in-line variant
    CLASSICAL = "classical"         # Slotted headstock
    ACOUSTIC = "acoustic"           # Martin-style solid
    PRS = "prs"                     # Paul Reed Smith curved
    EXPLORER = "explorer"           # Gibson angular
    FLYING_V = "flying_v"           # Gibson V-shape
    SG = "sg"                       # Gibson SG style
    JAZZ = "jazz"                   # Archtop style
    CUSTOM = "custom"               # User-defined


class InlayDesign(str, Enum):
    """Common inlay design categories."""
    # Birds
    HUMMINGBIRD = "hummingbird"
    DOVE = "dove"
    EAGLE = "eagle"
    PHOENIX = "phoenix"
    OWL = "owl"
    SWALLOW = "swallow"

    # Floral
    ROSE = "rose"
    VINE = "vine"
    TREE_OF_LIFE = "tree_of_life"
    LOTUS = "lotus"
    CHERRY_BLOSSOM = "cherry_blossom"
    ACANTHUS = "acanthus"

    # Geometric
    DIAMOND = "diamond"
    SPLIT_BLOCK = "split_block"
    CROWN = "crown"
    TORCH = "torch"
    STAR = "star"
    CELTIC_KNOT = "celtic_knot"

    # Other
    DRAGON = "dragon"
    KOI = "koi"
    SKULL = "skull"
    CUSTOM = "custom"


# Wood colors and descriptions for prompts
WOOD_DESCRIPTIONS: Dict[str, str] = {
    # Dark woods (headstock)
    "mahogany": "rich dark mahogany with reddish-brown hues and straight grain",
    "rosewood": "deep chocolate brown rosewood with darker streaks",
    "ebony": "jet black ebony with tight, barely visible grain",
    "walnut": "warm brown walnut with swirling grain patterns",
    "wenge": "dark brown wenge with distinctive black streaks",
    "koa": "golden-brown Hawaiian koa with dramatic figure",
    "ziricote": "dark brown ziricote with striking spider-web grain",

    # Light woods (inlay)
    "maple": "creamy white maple with subtle flame figure",
    "holly": "bright white holly, the whitest of tonewoods",
    "boxwood": "pale yellow boxwood with fine, even texture",
    "spruce": "light tan spruce with gentle grain lines",
    "ash": "light blonde ash with bold grain pattern",

    # Figured woods
    "flame_maple": "highly figured flame maple with intense chatoyance",
    "quilted_maple": "quilted maple with 3D rippling pattern",
    "birdseye_maple": "birdseye maple with distinctive eye spots",
    "spalted_maple": "spalted maple with dramatic black zone lines",

    # Exotic accents
    "abalone": "iridescent abalone shell with blue-green-pink shimmer",
    "mother_of_pearl": "lustrous white mother of pearl with rainbow highlights",
    "paua": "vibrant New Zealand paua shell with intense blue-green",
    "goldleaf": "brilliant gold leaf with metallic luster",
}


# Headstock shape descriptions
HEADSTOCK_SHAPES: Dict[str, str] = {
    "les_paul": """
Classic Gibson Les Paul "open book" headstock shape - the top curves outward
like an open book, with a slight peak at the center. Three tuners on each side,
angled back at 17 degrees. Black "bell" shaped truss rod cover.
""",
    "stratocaster": """
Fender Stratocaster headstock - all six tuners in a line on the treble side.
Distinctive curved shape that's wider at the top, narrowing toward the nut.
Classic Fender transition curve where headstock meets neck.
""",
    "telecaster": """
Fender Telecaster headstock - similar to Stratocaster with 6-in-line tuners,
but with a slightly different curve. More utilitarian, less ornate shape.
""",
    "classical": """
Traditional classical guitar slotted headstock - rectangular shape with two
vertical slots for the tuning machine rollers. Elegant and traditional.
Three tuners visible on each side through the slots.
""",
    "acoustic": """
Martin-style acoustic headstock - solid (not slotted), squared-off shape
with gentle curves. Three tuners per side with open-gear or enclosed tuners.
Often features decorative volute where neck meets headstock.
""",
    "prs": """
Paul Reed Smith headstock - elegant curved shape that flows organically.
Three tuners per side, signature PRS bird inlay or eagle logo.
Refined, modern aesthetic with vintage inspiration.
""",
    "explorer": """
Gibson Explorer headstock - dramatic angular shape that matches the body.
Pointed, aggressive design. Three tuners per side with sharp angles.
""",
    "flying_v": """
Gibson Flying V headstock - V-shaped to complement the body design.
Angular, rock-oriented aesthetic. Chrome hardware typical.
""",
    "sg": """
Gibson SG headstock - similar to Les Paul open-book but often with
slightly different proportions. Associated with rock and metal.
""",
    "jazz": """
Archtop jazz guitar headstock - elegant, often with art deco influences.
May feature ornate inlay work. Typically 3+3 tuner configuration.
Larger size to accommodate longer scale length instruments.
""",
}


# Pre-built inlay design descriptions
INLAY_DESIGNS: Dict[str, str] = {
    "hummingbird": """
A delicate hummingbird in flight, wings spread wide showing individual feathers.
Long slender beak pointing forward, small round eye. Tail feathers flowing behind.
The bird appears to hover, captured mid-wingbeat. Naturalistic proportions.
""",
    "dove": """
A peaceful dove with wings partially spread, olive branch in beak.
Symbol of peace and harmony. Gentle curves, soft appearance.
Feathers rendered with fine detail, serene expression.
""",
    "eagle": """
A majestic eagle with wings fully spread, talons extended.
Powerful, commanding presence. Sharp beak, fierce eye.
Detailed feather work showing primary and secondary feathers.
American bald eagle or golden eagle styling.
""",
    "phoenix": """
A mythical phoenix rising from flames, wings spread triumphantly.
Elaborate tail feathers flowing downward. Fire motif at the base.
Symbol of rebirth and transformation. Ornate, detailed design.
""",
    "rose": """
A classic rose bloom with layered petals, partially open.
Stem with thorns and leaves. Romantic, timeless design.
Can include rosebud accents. Traditional tattoo-style or realistic.
""",
    "vine": """
Flowing vine with curling tendrils and leaves.
Organic, natural movement across the headstock.
May include small flowers or grape clusters.
Art nouveau influence with elegant curves.
""",
    "tree_of_life": """
Elaborate tree design with spreading branches and roots.
Symbolic of growth, knowledge, and connection.
Intricate branch work filling the headstock space.
May include leaves, birds, or fruit in the branches.
""",
    "lotus": """
Sacred lotus flower in bloom, viewed from above or in profile.
Layered petals radiating outward. Eastern spiritual symbolism.
Clean, geometric quality with organic softness.
""",
    "cherry_blossom": """
Japanese cherry blossoms (sakura) on a branch.
Delicate five-petal flowers with visible stamens.
Some petals falling, suggesting transience and beauty.
Branch with subtle texture and smaller buds.
""",
    "dragon": """
Sinuous Eastern dragon with scaled body, four claws.
Flowing whiskers and mane, pearl or orb nearby.
Powerful but graceful, coiling across the headstock.
Detailed scales and fierce expression.
""",
    "celtic_knot": """
Interwoven Celtic knotwork pattern with no beginning or end.
Represents eternity and interconnection.
Precise geometric interlacing. Traditional or modernized style.
May incorporate animal motifs (Celtic dragon, serpent).
""",
    "crown": """
Royal crown design with jewels and filigree.
Gibson-style or ornate medieval styling.
Symbol of quality and prestige.
Metallic accents (gold, silver) if materials allow.
""",
    "split_block": """
Classic split-block inlay pattern - rectangular blocks with
notched centers, running up the headstock.
Traditional Gibson/Epiphone styling.
Clean geometric design, understated elegance.
""",
    "torch": """
Flaming torch held aloft, symbol of enlightenment.
Classical design with realistic flame rendering.
May include hand holding the torch.
Detailed flame with multiple tongues of fire.
""",
    "koi": """
Japanese koi fish swimming upstream, symbolizing perseverance.
Detailed scales, flowing fins and tail.
Water splash or wave motifs around the fish.
Traditional or modern stylized interpretation.
""",
}


def generate_headstock_prompt(
    style: str,
    headstock_wood: str,
    inlay_design: str,
    inlay_material: str,
    tuner_style: str = "chrome vintage",
    additional_details: Optional[str] = None,
    background: str = "dark gradient studio",
    include_strings: bool = True,
) -> str:
    """Generate a detailed prompt for AI headstock image generation."""
    # Get descriptions
    shape_desc = HEADSTOCK_SHAPES.get(style, HEADSTOCK_SHAPES.get("les_paul"))
    wood_desc = WOOD_DESCRIPTIONS.get(headstock_wood, f"{headstock_wood} wood")
    inlay_desc = INLAY_DESIGNS.get(inlay_design, f"{inlay_design} design")
    inlay_mat_desc = WOOD_DESCRIPTIONS.get(inlay_material, f"{inlay_material}")

    prompt = f"""
Professional product photograph of a guitar headstock, studio lighting, photorealistic.

HEADSTOCK SHAPE:
{shape_desc.strip()}

HEADSTOCK WOOD:
The headstock face is made of {wood_desc}.
High-gloss lacquer finish showing the natural wood beauty.
The grain is clearly visible under the finish.

INLAY ARTWORK:
{inlay_desc.strip()}

The inlay is crafted from {inlay_mat_desc}.
The inlay is set perfectly flush with the headstock surface - true luthier craftsmanship.
Fine detail work visible in the inlay, showing master-level artistry.
The contrast between the {headstock_wood} headstock and {inlay_material} inlay is striking.

HARDWARE:
{tuner_style} tuning machines, properly aligned.
Tuner buttons reflecting the studio lights.
Black truss rod cover if applicable to the style.

COMPOSITION:
{background} background.
Camera angle: front view with slight tilt to show depth.
Professional guitar photography lighting - highlights the wood grain and inlay detail.
Sharp focus on the inlay craftsmanship.
{"Guitar strings visible, properly wound around tuning posts." if include_strings else ""}

This is a high-end custom guitar headstock showing exceptional inlay artistry.
The image should look like it belongs in a premium guitar catalog or luthier portfolio.
"""

    if additional_details:
        prompt += f"\nADDITIONAL DETAILS:\n{additional_details}\n"

    return prompt.strip()


def generate_inlay_prompt(
    design: str,
    material: str,
    size_description: str = "approximately 2 inches tall",
    style_notes: Optional[str] = None,
) -> str:
    """Generate a prompt for an isolated inlay design (not installed)."""
    design_desc = INLAY_DESIGNS.get(design, f"{design} design")
    material_desc = WOOD_DESCRIPTIONS.get(material, f"{material}")

    prompt = f"""
Professional product photograph of a guitar headstock inlay piece,
laid flat on a neutral gray background, viewed from directly above.

INLAY DESIGN:
{design_desc.strip()}

MATERIAL:
The inlay is crafted from {material_desc}.
{size_description}.

DETAILS:
- Precision cut edges, laser or CNC quality
- Fine detail work visible
- The piece is flat, thin (approximately 1.5mm thick)
- Ready for installation into a headstock

PHOTOGRAPHY:
- Flat lay, directly overhead camera angle
- Soft, even studio lighting
- No harsh shadows
- Sharp focus on the intricate details
- Clean, professional product photography

This is a finished inlay piece ready for installation, showing the
craftsmanship before it's set into the headstock.
"""

    if style_notes:
        prompt += f"\nSTYLE NOTES:\n{style_notes}\n"

    return prompt.strip()


# Pre-built template combinations
HEADSTOCK_TEMPLATES: Dict[str, Dict] = {
    "gibson_hummingbird": {
        "name": "Gibson Hummingbird Style",
        "style": "les_paul",
        "headstock_wood": "mahogany",
        "inlay_design": "hummingbird",
        "inlay_material": "maple",
        "tuner_style": "chrome vintage Kluson-style",
        "description": "Classic Gibson Hummingbird acoustic inspiration on electric headstock",
    },
    "gibson_dove": {
        "name": "Gibson Dove Style",
        "style": "les_paul",
        "headstock_wood": "mahogany",
        "inlay_design": "dove",
        "inlay_material": "mother_of_pearl",
        "tuner_style": "gold Grover Rotomatics",
        "description": "Gibson Dove acoustic inspiration with pearl inlay",
    },
    "prs_custom_eagle": {
        "name": "PRS Custom Eagle",
        "style": "prs",
        "headstock_wood": "mahogany",
        "inlay_design": "eagle",
        "inlay_material": "abalone",
        "tuner_style": "chrome PRS locking tuners",
        "description": "Paul Reed Smith style with majestic eagle",
    },
    "classical_rose": {
        "name": "Classical Rose",
        "style": "classical",
        "headstock_wood": "rosewood",
        "inlay_design": "rose",
        "inlay_material": "mother_of_pearl",
        "tuner_style": "gold classical tuners with white buttons",
        "description": "Traditional classical guitar with romantic rose inlay",
    },
    "tree_of_life": {
        "name": "Tree of Life",
        "style": "les_paul",
        "headstock_wood": "ebony",
        "inlay_design": "tree_of_life",
        "inlay_material": "abalone",
        "tuner_style": "chrome Grover locking",
        "description": "Elaborate tree of life on dark ebony - ultimate custom piece",
    },
    "japanese_koi": {
        "name": "Japanese Koi",
        "style": "prs",
        "headstock_wood": "koa",
        "inlay_design": "koi",
        "inlay_material": "mother_of_pearl",
        "tuner_style": "gold locking tuners",
        "description": "Hawaiian koa with Japanese koi - Pacific fusion",
    },
    "celtic_warrior": {
        "name": "Celtic Warrior",
        "style": "explorer",
        "headstock_wood": "walnut",
        "inlay_design": "celtic_knot",
        "inlay_material": "maple",
        "tuner_style": "black chrome tuners",
        "description": "Celtic knotwork on angular Explorer - metal aesthetic",
    },
    "dragon_master": {
        "name": "Dragon Master",
        "style": "flying_v",
        "headstock_wood": "ebony",
        "inlay_design": "dragon",
        "inlay_material": "abalone",
        "tuner_style": "black Grover tuners",
        "description": "Eastern dragon on Flying V - ultimate shred guitar",
    },
    "dragon_dreadnought": {
        "name": "Dragon Dreadnought",
        "style": "acoustic",
        "headstock_wood": "ebony",
        "inlay_design": "dragon",
        "inlay_material": "abalone",
        "tuner_style": "gold open-gear butterbean tuners",
        "description": "Eastern dragon on dreadnought acoustic - dramatic showpiece",
        "additional_details": "Sinuous Eastern/Chinese dragon with four claws, flowing whiskers and mane, detailed scales in iridescent abalone. The dragon coils gracefully across the headstock. Martin-style headstock shape with dramatic custom inlay.",
    },
    "acoustic_vine": {
        "name": "Acoustic Vine",
        "style": "acoustic",
        "headstock_wood": "rosewood",
        "inlay_design": "vine",
        "inlay_material": "maple",
        "tuner_style": "chrome open-gear tuners",
        "description": "Martin-style acoustic with flowing vine inlay",
    },
    "jazz_lotus": {
        "name": "Jazz Lotus",
        "style": "jazz",
        "headstock_wood": "ebony",
        "inlay_design": "lotus",
        "inlay_material": "mother_of_pearl",
        "tuner_style": "gold Grover Imperial",
        "description": "Archtop jazz guitar with sacred lotus - spiritual jazz",
    },
}


INLAY_TEMPLATES: Dict[str, Dict] = {
    "pearl_hummingbird": {
        "design": "hummingbird",
        "material": "mother_of_pearl",
        "description": "Classic pearl hummingbird, iridescent wings",
    },
    "abalone_eagle": {
        "design": "eagle",
        "material": "abalone",
        "description": "Majestic eagle in colorful abalone",
    },
    "maple_dove": {
        "design": "dove",
        "material": "flame_maple",
        "description": "Peace dove in figured maple",
    },
    "pearl_tree": {
        "design": "tree_of_life",
        "material": "mother_of_pearl",
        "description": "Elaborate tree of life in lustrous pearl",
    },
    "abalone_dragon": {
        "design": "dragon",
        "material": "abalone",
        "description": "Eastern dragon with iridescent scales",
    },
}


def get_template_prompt(template_name: str) -> str:
    """Generate a prompt from a pre-built template."""
    if template_name not in HEADSTOCK_TEMPLATES:
        available = ", ".join(HEADSTOCK_TEMPLATES.keys())
        raise ValueError(f"Unknown template '{template_name}'. Available: {available}")

    template = HEADSTOCK_TEMPLATES[template_name]

    return generate_headstock_prompt(
        style=template["style"],
        headstock_wood=template["headstock_wood"],
        inlay_design=template["inlay_design"],
        inlay_material=template["inlay_material"],
        tuner_style=template.get("tuner_style", "chrome vintage"),
    )


def list_available_options() -> Dict[str, List[str]]:
    """List all available options for headstock generation."""
    return {
        "headstock_styles": [s.value for s in HeadstockStyle],
        "inlay_designs": [d.value for d in InlayDesign],
        "wood_species": list(WOOD_DESCRIPTIONS.keys()),
        "templates": list(HEADSTOCK_TEMPLATES.keys()),
    }
