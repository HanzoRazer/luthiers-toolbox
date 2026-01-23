#!/usr/bin/env python3
"""
Guitar Vision Engine — Expanded Luthier Vocabulary

Comprehensive vocabulary for guitar image generation with luthier-specific terms.

Covers:
- Body shapes (acoustic, electric, classical, archtop, historical)
- Finishes (French polish, nitro, poly, stains, bursts)
- Tonewoods (tops, backs, necks, fretboards)
- Construction details (bracing, binding, purfling)
- Hardware (tuners, bridges, pickups, tailpieces)
- Neck profiles and scale lengths
- Inlay materials and patterns
- Rosette styles
- Builder/luthier style references

Author: Luthier's ToolBox
Date: December 16, 2025
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Set


# =============================================================================
# ENUMS
# =============================================================================

class GuitarCategory(str, Enum):
    ACOUSTIC = "acoustic"
    ELECTRIC = "electric"
    CLASSICAL = "classical"
    ARCHTOP = "archtop"
    RESONATOR = "resonator"
    BASS = "bass"
    HISTORICAL = "historical"
    TRAVEL = "travel"
    BARITONE = "baritone"
    TWELVE_STRING = "twelve_string"


class FinishType(str, Enum):
    SOLID = "solid"
    BURST = "burst"
    TRANSPARENT = "transparent"
    METALLIC = "metallic"
    FIGURED = "figured"
    NATURAL = "natural"
    SPECIALTY = "specialty"
    RELIC = "relic"


# =============================================================================
# BODY SHAPES — Comprehensive
# =============================================================================

BODY_SHAPES: Dict[str, Dict] = {
    # =========================================================================
    # ACOUSTIC — Steel String
    # =========================================================================
    
    # Dreadnought family
    "dreadnought": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "Martin-style dreadnought acoustic guitar",
        "aliases": ["dread", "D-size"],
        "origin": "Martin D-28",
    },
    "slope shoulder dreadnought": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "slope shoulder dreadnought acoustic guitar with rounded upper bout",
        "aliases": ["slope shoulder", "round shoulder dread"],
        "origin": "Gibson J-45",
    },
    "square shoulder dreadnought": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "square shoulder dreadnought acoustic guitar",
        "aliases": ["square shoulder"],
        "origin": "Martin D-28",
    },
    
    # Orchestra / OM family
    "orchestra model": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "orchestra model OM acoustic guitar",
        "aliases": ["OM", "orchestra"],
        "origin": "Martin OM-28",
    },
    "000": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "triple-O 000 acoustic guitar",
        "aliases": ["triple-o", "triple-oh", "auditorium"],
        "origin": "Martin 000-28",
    },
    "00": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "double-O 00 acoustic guitar",
        "aliases": ["double-o", "double-oh", "grand concert"],
        "origin": "Martin 00-18",
    },
    "0": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "single-O concert acoustic guitar",
        "aliases": ["single-o", "concert"],
        "origin": "Martin 0-18",
    },
    
    # Grand family (Taylor-style)
    "grand auditorium": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "grand auditorium GA acoustic guitar",
        "aliases": ["GA", "taylor GA"],
        "origin": "Taylor 814",
    },
    "grand concert": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "grand concert GC acoustic guitar",
        "aliases": ["GC"],
        "origin": "Taylor 512",
    },
    "grand symphony": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "grand symphony GS acoustic guitar",
        "aliases": ["GS"],
        "origin": "Taylor GS",
    },
    "grand orchestra": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "grand orchestra GO jumbo acoustic guitar",
        "aliases": ["GO"],
        "origin": "Taylor GO",
    },
    "grand pacific": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "grand pacific round shoulder acoustic guitar",
        "aliases": ["GP"],
        "origin": "Taylor GP",
    },
    
    # Jumbo
    "jumbo": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "jumbo body acoustic guitar with large lower bout",
        "aliases": ["super jumbo", "J-200 style"],
        "origin": "Gibson J-200",
    },
    "super jumbo": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "super jumbo acoustic guitar ornate",
        "aliases": ["SJ-200"],
        "origin": "Gibson SJ-200",
    },
    
    # Parlor / Small body
    "parlor": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "parlor acoustic guitar small body vintage",
        "aliases": ["parlour", "size 1", "size 2"],
        "origin": "1890s parlor guitars",
    },
    "terz": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "terz guitar small scale tuned higher",
        "aliases": ["tertz"],
        "origin": "19th century",
    },
    
    # Travel / Mini
    "travel guitar": {
        "category": GuitarCategory.TRAVEL,
        "expanded": "compact travel acoustic guitar",
        "aliases": ["mini guitar", "baby taylor", "little martin"],
        "origin": "Martin LX1",
    },
    "backpacker": {
        "category": GuitarCategory.TRAVEL,
        "expanded": "Martin Backpacker narrow body travel guitar",
        "aliases": [],
        "origin": "Martin Backpacker",
    },
    
    # Specialty acoustic
    "cutaway acoustic": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "acoustic guitar with venetian cutaway",
        "aliases": ["cutaway", "venetian cutaway"],
        "origin": "Various",
    },
    "florentine cutaway": {
        "category": GuitarCategory.ACOUSTIC,
        "expanded": "acoustic guitar with pointed florentine cutaway",
        "aliases": ["sharp cutaway"],
        "origin": "Various",
    },
    "twelve string": {
        "category": GuitarCategory.TWELVE_STRING,
        "expanded": "twelve string acoustic guitar with paired courses",
        "aliases": ["12-string", "12 string"],
        "origin": "Various",
    },
    "baritone acoustic": {
        "category": GuitarCategory.BARITONE,
        "expanded": "baritone acoustic guitar long scale",
        "aliases": [],
        "origin": "Various",
    },
    
    # =========================================================================
    # CLASSICAL / NYLON
    # =========================================================================
    
    "classical": {
        "category": GuitarCategory.CLASSICAL,
        "expanded": "Spanish classical nylon-string guitar",
        "aliases": ["nylon string", "spanish guitar", "concert classical"],
        "origin": "Torres",
    },
    "flamenco": {
        "category": GuitarCategory.CLASSICAL,
        "expanded": "traditional flamenco guitar cypress golpeador",
        "aliases": ["flamenco negra", "flamenco blanca"],
        "origin": "Spain",
    },
    "flamenco negra": {
        "category": GuitarCategory.CLASSICAL,
        "expanded": "flamenco negra guitar rosewood back and sides",
        "aliases": [],
        "origin": "Spain",
    },
    "flamenco blanca": {
        "category": GuitarCategory.CLASSICAL,
        "expanded": "flamenco blanca guitar cypress back and sides bright tone",
        "aliases": [],
        "origin": "Spain",
    },
    "requinto": {
        "category": GuitarCategory.CLASSICAL,
        "expanded": "requinto small scale classical guitar",
        "aliases": [],
        "origin": "Latin America",
    },
    "alto guitar": {
        "category": GuitarCategory.CLASSICAL,
        "expanded": "alto guitar smaller body higher pitch",
        "aliases": [],
        "origin": "Various",
    },
    "romantic guitar": {
        "category": GuitarCategory.HISTORICAL,
        "expanded": "19th century romantic period guitar",
        "aliases": ["early romantic"],
        "origin": "1800s",
    },
    "baroque guitar": {
        "category": GuitarCategory.HISTORICAL,
        "expanded": "five course baroque guitar historical",
        "aliases": [],
        "origin": "1600s",
    },
    "vihuela": {
        "category": GuitarCategory.HISTORICAL,
        "expanded": "renaissance vihuela historical instrument",
        "aliases": [],
        "origin": "Spain 1500s",
    },
    
    # =========================================================================
    # ARCHTOP
    # =========================================================================
    
    "archtop": {
        "category": GuitarCategory.ARCHTOP,
        "expanded": "carved archtop jazz guitar f-holes",
        "aliases": ["jazz box", "jazzbox"],
        "origin": "Gibson L-5",
    },
    "L-5": {
        "category": GuitarCategory.ARCHTOP,
        "expanded": "Gibson L-5 archtop jazz guitar",
        "aliases": ["l5"],
        "origin": "Gibson",
    },
    "super 400": {
        "category": GuitarCategory.ARCHTOP,
        "expanded": "Gibson Super 400 large archtop",
        "aliases": ["super400"],
        "origin": "Gibson",
    },
    "es-175": {
        "category": GuitarCategory.ARCHTOP,
        "expanded": "Gibson ES-175 archtop with florentine cutaway",
        "aliases": ["175"],
        "origin": "Gibson",
    },
    "benedetto": {
        "category": GuitarCategory.ARCHTOP,
        "expanded": "Benedetto style carved archtop",
        "aliases": [],
        "origin": "Robert Benedetto",
    },
    "d'angelico": {
        "category": GuitarCategory.ARCHTOP,
        "expanded": "D'Angelico style archtop art deco",
        "aliases": ["dangelico"],
        "origin": "John D'Angelico",
    },
    "gypsy jazz": {
        "category": GuitarCategory.ARCHTOP,
        "expanded": "Selmer Maccaferri gypsy jazz guitar",
        "aliases": ["manouche", "django style", "selmer", "maccaferri"],
        "origin": "Selmer",
    },
    
    # =========================================================================
    # ELECTRIC — Solid Body
    # =========================================================================
    
    "les paul": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson Les Paul solid body electric guitar carved maple top",
        "aliases": ["lp", "paul"],
        "origin": "Gibson",
    },
    "les paul standard": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson Les Paul Standard flame maple top",
        "aliases": [],
        "origin": "Gibson",
    },
    "les paul custom": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson Les Paul Custom multi-bound ebony fretboard",
        "aliases": ["black beauty"],
        "origin": "Gibson",
    },
    "les paul junior": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson Les Paul Junior single cutaway single P-90",
        "aliases": ["lp jr", "junior"],
        "origin": "Gibson",
    },
    "les paul special": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson Les Paul Special double cutaway",
        "aliases": ["lp special"],
        "origin": "Gibson",
    },
    "sg": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson SG solid guitar double cutaway devil horns",
        "aliases": ["solid guitar"],
        "origin": "Gibson",
    },
    "sg standard": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson SG Standard cherry red",
        "aliases": [],
        "origin": "Gibson",
    },
    "flying v": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson Flying V futuristic angular body",
        "aliases": ["v"],
        "origin": "Gibson",
    },
    "explorer": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson Explorer angular futuristic body",
        "aliases": [],
        "origin": "Gibson",
    },
    "firebird": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson Firebird reverse body through-neck mini-humbuckers",
        "aliases": [],
        "origin": "Gibson",
    },
    "moderne": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson Moderne futuristic rare",
        "aliases": [],
        "origin": "Gibson",
    },
    
    # Fender
    "stratocaster": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Stratocaster contoured double cutaway tremolo",
        "aliases": ["strat"],
        "origin": "Fender",
    },
    "telecaster": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Telecaster slab body single cutaway",
        "aliases": ["tele", "broadcaster", "esquire"],
        "origin": "Fender",
    },
    "telecaster deluxe": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Telecaster Deluxe with humbuckers",
        "aliases": ["tele deluxe"],
        "origin": "Fender",
    },
    "telecaster thinline": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Telecaster Thinline semi-hollow f-hole",
        "aliases": ["thinline"],
        "origin": "Fender",
    },
    "jazzmaster": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Jazzmaster offset waist floating tremolo",
        "aliases": [],
        "origin": "Fender",
    },
    "jaguar": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Jaguar offset short scale rhythm circuit",
        "aliases": ["jag"],
        "origin": "Fender",
    },
    "mustang": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Mustang short scale student",
        "aliases": [],
        "origin": "Fender",
    },
    "duo-sonic": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Duo-Sonic short scale offset",
        "aliases": ["duosonic"],
        "origin": "Fender",
    },
    "musicmaster": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Musicmaster student single pickup",
        "aliases": [],
        "origin": "Fender",
    },
    "lead": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Lead series",
        "aliases": [],
        "origin": "Fender",
    },
    "starcaster": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Starcaster semi-hollow offset",
        "aliases": [],
        "origin": "Fender",
    },
    "coronado": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Fender Coronado thinline semi-hollow",
        "aliases": [],
        "origin": "Fender",
    },
    
    # Semi-hollow / Hollow
    "es-335": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson ES-335 semi-hollow thinline center block",
        "aliases": ["335", "dot"],
        "origin": "Gibson",
    },
    "es-339": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson ES-339 smaller semi-hollow",
        "aliases": ["339"],
        "origin": "Gibson",
    },
    "es-345": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson ES-345 semi-hollow stereo varitone",
        "aliases": ["345"],
        "origin": "Gibson",
    },
    "es-355": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson ES-355 semi-hollow deluxe ebony multi-bound",
        "aliases": ["355"],
        "origin": "Gibson",
    },
    "es-330": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Gibson ES-330 fully hollow thinline P-90",
        "aliases": ["330", "casino style"],
        "origin": "Gibson",
    },
    "casino": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Epiphone Casino fully hollow P-90",
        "aliases": [],
        "origin": "Epiphone",
    },
    "semi-hollow": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "semi-hollow body electric guitar f-holes",
        "aliases": ["thinline", "335-style"],
        "origin": "Various",
    },
    "hollow body": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "fully hollow body electric guitar",
        "aliases": ["hollowbody"],
        "origin": "Various",
    },
    
    # PRS
    "prs custom": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "PRS Custom 24 carved maple top bird inlays",
        "aliases": ["prs", "paul reed smith", "custom 24"],
        "origin": "PRS",
    },
    "prs mccarty": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "PRS McCarty 594 vintage style",
        "aliases": ["mccarty", "594"],
        "origin": "PRS",
    },
    "prs singlecut": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "PRS Singlecut single cutaway",
        "aliases": ["singlecut", "sc"],
        "origin": "PRS",
    },
    "prs hollowbody": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "PRS Hollowbody piezo",
        "aliases": [],
        "origin": "PRS",
    },
    
    # Superstrat / Modern
    "superstrat": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "superstrat hot-rodded pointed headstock floyd rose",
        "aliases": ["super strat", "shred guitar"],
        "origin": "Various",
    },
    "ibanez rg": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Ibanez RG superstrat thin neck wizard floyd rose",
        "aliases": ["rg"],
        "origin": "Ibanez",
    },
    "ibanez jem": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Ibanez JEM monkey grip lion's claw tremolo cavity",
        "aliases": ["jem"],
        "origin": "Ibanez",
    },
    "ibanez s": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Ibanez S series thin body",
        "aliases": ["s series", "sabre"],
        "origin": "Ibanez",
    },
    "jackson soloist": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Jackson Soloist through-neck superstrat",
        "aliases": ["soloist"],
        "origin": "Jackson",
    },
    "jackson dinky": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Jackson Dinky bolt-on superstrat",
        "aliases": ["dinky"],
        "origin": "Jackson",
    },
    "jackson rhoads": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Jackson Rhoads offset V",
        "aliases": ["rhoads", "rr"],
        "origin": "Jackson",
    },
    "jackson kelly": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Jackson Kelly pointed angular",
        "aliases": ["kelly"],
        "origin": "Jackson",
    },
    "jackson king v": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Jackson King V extreme pointed",
        "aliases": ["king v"],
        "origin": "Jackson",
    },
    "esp horizon": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "ESP Horizon superstrat neck-through",
        "aliases": ["horizon"],
        "origin": "ESP",
    },
    "esp eclipse": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "ESP Eclipse single cut",
        "aliases": ["eclipse"],
        "origin": "ESP",
    },
    "charvel san dimas": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Charvel San Dimas superstrat",
        "aliases": ["san dimas"],
        "origin": "Charvel",
    },
    "kramer": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "Kramer pointy headstock superstrat",
        "aliases": ["kramer baretta"],
        "origin": "Kramer",
    },
    
    # Modern / Boutique
    "headless": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "headless guitar steinberger style",
        "aliases": ["steinberger"],
        "origin": "Steinberger",
    },
    "multiscale": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "multiscale fanned fret guitar",
        "aliases": ["fanned fret", "fan fret"],
        "origin": "Various",
    },
    "extended range": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "extended range 7-string or 8-string guitar",
        "aliases": ["7-string", "8-string", "erg"],
        "origin": "Various",
    },
    "modern": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "modern boutique electric guitar",
        "aliases": [],
        "origin": "Various",
    },
    "offset": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "offset waist electric guitar",
        "aliases": [],
        "origin": "Various",
    },
    "t-style": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "T-style single cutaway electric guitar",
        "aliases": ["t style", "tele style"],
        "origin": "Various",
    },
    "s-style": {
        "category": GuitarCategory.ELECTRIC,
        "expanded": "S-style double cutaway contoured electric guitar",
        "aliases": ["s style", "strat style"],
        "origin": "Various",
    },
    
    # =========================================================================
    # RESONATOR
    # =========================================================================
    
    "resonator": {
        "category": GuitarCategory.RESONATOR,
        "expanded": "resonator guitar metal cone",
        "aliases": ["resophonic", "reso"],
        "origin": "National/Dobro",
    },
    "dobro": {
        "category": GuitarCategory.RESONATOR,
        "expanded": "Dobro square neck resonator spider cone",
        "aliases": ["spider cone"],
        "origin": "Dobro",
    },
    "national": {
        "category": GuitarCategory.RESONATOR,
        "expanded": "National metal body resonator",
        "aliases": ["tricone", "single cone"],
        "origin": "National",
    },
    "tricone": {
        "category": GuitarCategory.RESONATOR,
        "expanded": "tricone resonator three cones",
        "aliases": [],
        "origin": "National",
    },
    "biscuit": {
        "category": GuitarCategory.RESONATOR,
        "expanded": "biscuit bridge resonator single cone",
        "aliases": [],
        "origin": "National",
    },
    
    # =========================================================================
    # BASS
    # =========================================================================
    
    "precision bass": {
        "category": GuitarCategory.BASS,
        "expanded": "Fender Precision Bass split-coil pickup",
        "aliases": ["p-bass", "p bass", "precision"],
        "origin": "Fender",
    },
    "jazz bass": {
        "category": GuitarCategory.BASS,
        "expanded": "Fender Jazz Bass offset waist dual single-coil",
        "aliases": ["j-bass", "j bass", "jazz"],
        "origin": "Fender",
    },
    "musicman": {
        "category": GuitarCategory.BASS,
        "expanded": "Music Man StingRay bass humbucker 3+1 tuners",
        "aliases": ["stingray", "mm bass"],
        "origin": "Music Man",
    },
    "thunderbird": {
        "category": GuitarCategory.BASS,
        "expanded": "Gibson Thunderbird reverse body bass",
        "aliases": ["t-bird bass"],
        "origin": "Gibson",
    },
    "eb bass": {
        "category": GuitarCategory.BASS,
        "expanded": "Gibson EB bass violin shape",
        "aliases": ["eb-0", "eb-3", "sg bass"],
        "origin": "Gibson",
    },
    "rickenbacker bass": {
        "category": GuitarCategory.BASS,
        "expanded": "Rickenbacker 4001 bass",
        "aliases": ["ric bass", "4001", "4003"],
        "origin": "Rickenbacker",
    },
    "hofner": {
        "category": GuitarCategory.BASS,
        "expanded": "Hofner violin bass Beatles bass",
        "aliases": ["violin bass", "beatle bass", "500/1"],
        "origin": "Hofner",
    },
    "warwick": {
        "category": GuitarCategory.BASS,
        "expanded": "Warwick curved body bass",
        "aliases": ["thumb bass", "streamer"],
        "origin": "Warwick",
    },
}


# =============================================================================
# FINISHES — Comprehensive
# =============================================================================

FINISHES: Dict[str, Dict] = {
    # =========================================================================
    # SOLID COLORS
    # =========================================================================
    
    # Classic colors
    "black": {"expanded": "gloss black", "type": FinishType.SOLID},
    "white": {"expanded": "olympic white", "type": FinishType.SOLID},
    "arctic white": {"expanded": "arctic white", "type": FinishType.SOLID},
    "vintage white": {"expanded": "vintage white aged cream", "type": FinishType.SOLID},
    "cream": {"expanded": "vintage cream", "type": FinishType.SOLID},
    "ivory": {"expanded": "aged ivory", "type": FinishType.SOLID},
    
    # Reds
    "red": {"expanded": "candy apple red", "type": FinishType.SOLID},
    "candy apple red": {"expanded": "candy apple red metallic", "type": FinishType.METALLIC},
    "fiesta red": {"expanded": "fiesta red", "type": FinishType.SOLID},
    "dakota red": {"expanded": "dakota red", "type": FinishType.SOLID},
    "torino red": {"expanded": "torino red", "type": FinishType.SOLID},
    "cherry": {"expanded": "cherry red", "type": FinishType.SOLID},
    "heritage cherry": {"expanded": "heritage cherry", "type": FinishType.SOLID},
    "wine red": {"expanded": "wine red deep burgundy", "type": FinishType.SOLID},
    "oxblood": {"expanded": "oxblood dark red", "type": FinishType.SOLID},
    
    # Blues
    "blue": {"expanded": "lake placid blue", "type": FinishType.SOLID},
    "lake placid blue": {"expanded": "lake placid blue metallic", "type": FinishType.METALLIC},
    "sonic blue": {"expanded": "sonic blue pastel", "type": FinishType.SOLID},
    "daphne blue": {"expanded": "daphne blue", "type": FinishType.SOLID},
    "ice blue metallic": {"expanded": "ice blue metallic", "type": FinishType.METALLIC},
    "pelham blue": {"expanded": "pelham blue", "type": FinishType.SOLID},
    "navy blue": {"expanded": "navy blue dark", "type": FinishType.SOLID},
    "ocean turquoise": {"expanded": "ocean turquoise", "type": FinishType.SOLID},
    
    # Greens
    "green": {"expanded": "sherwood green", "type": FinishType.SOLID},
    "sherwood green": {"expanded": "sherwood green", "type": FinishType.SOLID},
    "seafoam green": {"expanded": "seafoam green", "type": FinishType.SOLID},
    "surf green": {"expanded": "surf green", "type": FinishType.SOLID},
    "inverness green": {"expanded": "inverness green", "type": FinishType.SOLID},
    "cadillac green": {"expanded": "cadillac green metallic", "type": FinishType.METALLIC},
    "british racing green": {"expanded": "british racing green", "type": FinishType.SOLID},
    "teal": {"expanded": "teal green blue", "type": FinishType.SOLID},
    
    # Yellows / Oranges
    "yellow": {"expanded": "TV yellow", "type": FinishType.SOLID},
    "tv yellow": {"expanded": "TV yellow vintage", "type": FinishType.SOLID},
    "butterscotch": {"expanded": "butterscotch blonde", "type": FinishType.SOLID},
    "blonde": {"expanded": "butterscotch blonde", "type": FinishType.SOLID},
    "orange": {"expanded": "competition orange", "type": FinishType.SOLID},
    "capri orange": {"expanded": "capri orange", "type": FinishType.SOLID},
    "tangerine": {"expanded": "tangerine orange", "type": FinishType.SOLID},
    
    # Other solids
    "purple": {"expanded": "deep purple metallic", "type": FinishType.SOLID},
    "pink": {"expanded": "shell pink", "type": FinishType.SOLID},
    "shell pink": {"expanded": "shell pink vintage", "type": FinishType.SOLID},
    "burgundy mist": {"expanded": "burgundy mist metallic", "type": FinishType.METALLIC},
    "shoreline gold": {"expanded": "shoreline gold metallic", "type": FinishType.METALLIC},
    
    # =========================================================================
    # SUNBURSTS / BURSTS
    # =========================================================================
    
    "sunburst": {"expanded": "three-tone sunburst", "type": FinishType.BURST},
    "3-tone sunburst": {"expanded": "three-tone sunburst black red yellow", "type": FinishType.BURST},
    "2-tone sunburst": {"expanded": "two-tone sunburst brown yellow", "type": FinishType.BURST},
    "tobacco burst": {"expanded": "tobacco sunburst brown", "type": FinishType.BURST},
    "tobacco sunburst": {"expanded": "tobacco sunburst vintage brown", "type": FinishType.BURST},
    "cherry burst": {"expanded": "cherry sunburst red", "type": FinishType.BURST},
    "cherry sunburst": {"expanded": "cherry sunburst vibrant red", "type": FinishType.BURST},
    "honey burst": {"expanded": "honey burst amber gold", "type": FinishType.BURST},
    "honeyburst": {"expanded": "honey burst golden amber", "type": FinishType.BURST},
    "lemon burst": {"expanded": "lemon burst yellow", "type": FinishType.BURST},
    "iced tea": {"expanded": "iced tea burst amber brown", "type": FinishType.BURST},
    "iced tea burst": {"expanded": "iced tea burst warm amber", "type": FinishType.BURST},
    "dark burst": {"expanded": "dark burst faded edges", "type": FinishType.BURST},
    "light burst": {"expanded": "light burst subtle fade", "type": FinishType.BURST},
    "vintage burst": {"expanded": "vintage sunburst aged patina", "type": FinishType.BURST},
    "tea burst": {"expanded": "tea burst brown amber", "type": FinishType.BURST},
    "desert burst": {"expanded": "desert burst tan brown", "type": FinishType.BURST},
    "ocean burst": {"expanded": "ocean burst blue fade", "type": FinishType.BURST},
    "blue burst": {"expanded": "blue burst dark blue fade", "type": FinishType.BURST},
    "purple burst": {"expanded": "purple burst violet fade", "type": FinishType.BURST},
    
    # =========================================================================
    # TRANSPARENT / SEE-THROUGH
    # =========================================================================
    
    "transparent": {"expanded": "transparent stain", "type": FinishType.TRANSPARENT},
    "trans red": {"expanded": "transparent cherry red stain", "type": FinishType.TRANSPARENT},
    "trans blue": {"expanded": "transparent blue stain", "type": FinishType.TRANSPARENT},
    "trans black": {"expanded": "transparent black see-through", "type": FinishType.TRANSPARENT},
    "trans white": {"expanded": "transparent white blonde", "type": FinishType.TRANSPARENT},
    "emerald": {"expanded": "transparent emerald green", "type": FinishType.TRANSPARENT},
    "emerald green": {"expanded": "transparent emerald green stain", "type": FinishType.TRANSPARENT},
    "amber": {"expanded": "transparent amber vintage", "type": FinishType.TRANSPARENT},
    "vintage amber": {"expanded": "vintage amber transparent aged", "type": FinishType.TRANSPARENT},
    "ocean blue": {"expanded": "transparent ocean blue", "type": FinishType.TRANSPARENT},
    "sapphire": {"expanded": "transparent sapphire blue", "type": FinishType.TRANSPARENT},
    "aqua": {"expanded": "transparent aqua blue green", "type": FinishType.TRANSPARENT},
    "violet": {"expanded": "transparent violet purple", "type": FinishType.TRANSPARENT},
    "purple rain": {"expanded": "transparent purple rain violet", "type": FinishType.TRANSPARENT},
    
    # =========================================================================
    # METALLIC / SPARKLE
    # =========================================================================
    
    "gold": {"expanded": "gold top metallic", "type": FinishType.METALLIC},
    "gold top": {"expanded": "gold top Les Paul style", "type": FinishType.METALLIC},
    "goldtop": {"expanded": "gold top vintage", "type": FinishType.METALLIC},
    "silver": {"expanded": "silver metallic", "type": FinishType.METALLIC},
    "silverburst": {"expanded": "silverburst gradient", "type": FinishType.METALLIC},
    "champagne": {"expanded": "champagne sparkle", "type": FinishType.METALLIC},
    "gunmetal": {"expanded": "gunmetal gray metallic", "type": FinishType.METALLIC},
    "charcoal": {"expanded": "charcoal metallic", "type": FinishType.METALLIC},
    "pewter": {"expanded": "pewter gray metallic", "type": FinishType.METALLIC},
    "bronze": {"expanded": "bronze metallic", "type": FinishType.METALLIC},
    "copper": {"expanded": "copper metallic", "type": FinishType.METALLIC},
    
    # Sparkle finishes
    "sparkle": {"expanded": "sparkle finish glitter", "type": FinishType.METALLIC},
    "silver sparkle": {"expanded": "silver sparkle glitter", "type": FinishType.METALLIC},
    "gold sparkle": {"expanded": "gold sparkle glitter", "type": FinishType.METALLIC},
    "blue sparkle": {"expanded": "blue sparkle glitter", "type": FinishType.METALLIC},
    "red sparkle": {"expanded": "red sparkle glitter", "type": FinishType.METALLIC},
    "champagne sparkle": {"expanded": "champagne sparkle vintage", "type": FinishType.METALLIC},
    
    # =========================================================================
    # FIGURED / WOOD GRAIN
    # =========================================================================
    
    "natural": {"expanded": "natural wood finish clear coat", "type": FinishType.NATURAL},
    "clear": {"expanded": "clear gloss natural wood", "type": FinishType.NATURAL},
    "satin natural": {"expanded": "satin natural wood matte", "type": FinishType.NATURAL},
    
    "flame": {"expanded": "flame maple figured top", "type": FinishType.FIGURED},
    "flame maple": {"expanded": "flame maple tiger stripe figure", "type": FinishType.FIGURED},
    "flamed": {"expanded": "flamed figured wood grain", "type": FinishType.FIGURED},
    "quilted": {"expanded": "quilted maple 3D figure", "type": FinishType.FIGURED},
    "quilt": {"expanded": "quilted maple billowy figure", "type": FinishType.FIGURED},
    "quilted maple": {"expanded": "quilted maple dramatic figure", "type": FinishType.FIGURED},
    "birdseye": {"expanded": "birdseye maple figured", "type": FinishType.FIGURED},
    "birdseye maple": {"expanded": "birdseye maple dotted figure", "type": FinishType.FIGURED},
    "figured": {"expanded": "figured maple grain", "type": FinishType.FIGURED},
    "spalted": {"expanded": "spalted maple dark lines", "type": FinishType.FIGURED},
    "spalted maple": {"expanded": "spalted maple fungal figure dark lines", "type": FinishType.FIGURED},
    "burl": {"expanded": "burl wood swirl pattern", "type": FinishType.FIGURED},
    "burl maple": {"expanded": "burl maple dramatic swirl", "type": FinishType.FIGURED},
    "curly": {"expanded": "curly maple figured", "type": FinishType.FIGURED},
    "curly maple": {"expanded": "curly maple wavy figure", "type": FinishType.FIGURED},
    "bookmatched": {"expanded": "bookmatched figured wood symmetrical", "type": FinishType.FIGURED},
    
    # =========================================================================
    # LUTHIER / SPECIALTY FINISHES
    # =========================================================================
    
    # French polish (classical)
    "french polish": {"expanded": "traditional French polish shellac high gloss", "type": FinishType.SPECIALTY},
    "shellac": {"expanded": "hand-rubbed shellac French polish", "type": FinishType.SPECIALTY},
    
    # Nitrocellulose
    "nitro": {"expanded": "nitrocellulose lacquer vintage", "type": FinishType.SPECIALTY},
    "nitrocellulose": {"expanded": "nitrocellulose lacquer thin responsive", "type": FinishType.SPECIALTY},
    "vintage nitro": {"expanded": "vintage nitrocellulose lacquer aged", "type": FinishType.SPECIALTY},
    
    # Poly
    "poly": {"expanded": "polyurethane gloss durable", "type": FinishType.SPECIALTY},
    "polyurethane": {"expanded": "polyurethane modern durable", "type": FinishType.SPECIALTY},
    "polyester": {"expanded": "polyester thick glossy", "type": FinishType.SPECIALTY},
    
    # Other finishes
    "satin": {"expanded": "satin finish matte smooth", "type": FinishType.SPECIALTY},
    "matte": {"expanded": "matte finish flat non-reflective", "type": FinishType.SPECIALTY},
    "semi-gloss": {"expanded": "semi-gloss moderate sheen", "type": FinishType.SPECIALTY},
    "oil": {"expanded": "hand-rubbed oil finish natural", "type": FinishType.SPECIALTY},
    "tung oil": {"expanded": "tung oil penetrating finish", "type": FinishType.SPECIALTY},
    "tru-oil": {"expanded": "Tru-Oil gun stock finish", "type": FinishType.SPECIALTY},
    "wax": {"expanded": "wax finish hand-buffed", "type": FinishType.SPECIALTY},
    
    # =========================================================================
    # RELIC / AGED
    # =========================================================================
    
    "relic": {"expanded": "aged relic finish worn vintage", "type": FinishType.RELIC},
    "heavy relic": {"expanded": "heavy relic severely aged worn", "type": FinishType.RELIC},
    "light relic": {"expanded": "light relic subtle aging", "type": FinishType.RELIC},
    "aged": {"expanded": "vintage aged patina yellowed", "type": FinishType.RELIC},
    "road worn": {"expanded": "road worn relic played-in", "type": FinishType.RELIC},
    "closet classic": {"expanded": "closet classic light aging", "type": FinishType.RELIC},
    "journeyman": {"expanded": "journeyman relic moderate wear", "type": FinishType.RELIC},
    "checking": {"expanded": "finish checking crackling aged nitro", "type": FinishType.RELIC},
    "weather checked": {"expanded": "weather checked lacquer cracks", "type": FinishType.RELIC},
}


# =============================================================================
# TONEWOODS — Comprehensive
# =============================================================================

TONEWOODS: Dict[str, Dict] = {
    # =========================================================================
    # TOPS
    # =========================================================================
    
    # Spruce family
    "spruce": {"usage": "top", "expanded": "solid spruce soundboard"},
    "sitka spruce": {"usage": "top", "expanded": "solid Sitka spruce top bright articulate"},
    "sitka": {"usage": "top", "expanded": "Sitka spruce soundboard"},
    "engelmann spruce": {"usage": "top", "expanded": "solid Engelmann spruce top warm responsive"},
    "engelmann": {"usage": "top", "expanded": "Engelmann spruce sensitive dynamic"},
    "adirondack spruce": {"usage": "top", "expanded": "solid Adirondack red spruce top powerful vintage"},
    "adirondack": {"usage": "top", "expanded": "Adirondack spruce prewar sound"},
    "red spruce": {"usage": "top", "expanded": "Appalachian red spruce vintage tone"},
    "european spruce": {"usage": "top", "expanded": "European Alpine spruce top classical"},
    "alpine spruce": {"usage": "top", "expanded": "Alpine spruce fine grain"},
    "german spruce": {"usage": "top", "expanded": "German spruce classical traditional"},
    "italian spruce": {"usage": "top", "expanded": "Italian spruce val di fiemme"},
    "lutz spruce": {"usage": "top", "expanded": "Lutz spruce hybrid Sitka Engelmann"},
    
    # Cedar
    "cedar": {"usage": "top", "expanded": "solid Western red cedar top warm dark"},
    "western red cedar": {"usage": "top", "expanded": "Western red cedar warm fundamental"},
    "spanish cedar": {"usage": "top", "expanded": "Spanish cedar classical"},
    "port orford cedar": {"usage": "top", "expanded": "Port Orford cedar bright balanced"},
    
    # Other tops
    "redwood": {"usage": "top", "expanded": "solid redwood top warm rich overtones"},
    "sinker redwood": {"usage": "top", "expanded": "sinker redwood reclaimed old growth"},
    "maple top": {"usage": "top", "expanded": "carved maple top electric"},
    "koa top": {"usage": "top", "expanded": "Hawaiian koa top figured"},
    
    # =========================================================================
    # BACK & SIDES
    # =========================================================================
    
    # Rosewood family
    "rosewood": {"usage": "back_sides", "expanded": "solid rosewood back and sides rich complex"},
    "indian rosewood": {"usage": "back_sides", "expanded": "solid East Indian rosewood back and sides"},
    "east indian rosewood": {"usage": "back_sides", "expanded": "East Indian rosewood warm bass rich"},
    "brazilian rosewood": {"usage": "back_sides", "expanded": "solid Brazilian rosewood back and sides rare vintage"},
    "madagascar rosewood": {"usage": "back_sides", "expanded": "Madagascar rosewood complex overtones"},
    "honduran rosewood": {"usage": "back_sides", "expanded": "Honduran rosewood dark rich"},
    "cocobolo": {"usage": "back_sides", "expanded": "solid cocobolo back and sides figured oily"},
    "kingwood": {"usage": "back_sides", "expanded": "kingwood rosewood family violet"},
    
    # Mahogany family
    "mahogany": {"usage": "back_sides", "expanded": "solid mahogany back and sides warm punchy"},
    "honduran mahogany": {"usage": "back_sides", "expanded": "Honduran mahogany warm midrange"},
    "african mahogany": {"usage": "back_sides", "expanded": "African khaya mahogany"},
    "sapele": {"usage": "back_sides", "expanded": "solid sapele back and sides ribbon stripe"},
    "utile": {"usage": "back_sides", "expanded": "utile sipo similar to mahogany"},
    
    # Maple
    "maple": {"usage": "back_sides", "expanded": "solid maple back and sides bright articulate"},
    "hard maple": {"usage": "back_sides", "expanded": "hard rock maple bright sustain"},
    "soft maple": {"usage": "back_sides", "expanded": "soft maple warm"},
    "bigleaf maple": {"usage": "back_sides", "expanded": "Western bigleaf maple figured"},
    "european maple": {"usage": "back_sides", "expanded": "European maple tight grain"},
    
    # Koa
    "koa": {"usage": "back_sides", "expanded": "solid Hawaiian koa back and sides warm bright"},
    "hawaiian koa": {"usage": "back_sides", "expanded": "Hawaiian koa figured premium"},
    "acacia": {"usage": "back_sides", "expanded": "acacia koa relative"},
    "blackwood": {"usage": "back_sides", "expanded": "Australian blackwood similar to koa"},
    "tasmanian blackwood": {"usage": "back_sides", "expanded": "Tasmanian blackwood figured"},
    
    # Walnut
    "walnut": {"usage": "back_sides", "expanded": "solid black walnut back and sides warm balanced"},
    "black walnut": {"usage": "back_sides", "expanded": "American black walnut"},
    "claro walnut": {"usage": "back_sides", "expanded": "claro walnut figured California"},
    "english walnut": {"usage": "back_sides", "expanded": "English walnut European"},
    
    # Other back/sides
    "cypress": {"usage": "back_sides", "expanded": "Mediterranean cypress flamenco bright percussive"},
    "ziricote": {"usage": "back_sides", "expanded": "ziricote spider web figure dark"},
    "ebony": {"usage": "back_sides", "expanded": "solid ebony back and sides rare dark dense"},
    "ovangkol": {"usage": "back_sides", "expanded": "ovangkol African rosewood alternative"},
    "pau ferro": {"usage": "back_sides", "expanded": "pau ferro Bolivian rosewood"},
    "bubinga": {"usage": "back_sides", "expanded": "bubinga African dense figured"},
    "padauk": {"usage": "back_sides", "expanded": "padauk African red bright"},
    "wenge": {"usage": "back_sides", "expanded": "wenge dark striped African"},
    "purpleheart": {"usage": "back_sides", "expanded": "purpleheart amaranth vibrant"},
    "lacewood": {"usage": "back_sides", "expanded": "lacewood leopardwood figured"},
    "bloodwood": {"usage": "back_sides", "expanded": "bloodwood satine vibrant red"},
    "myrtle": {"usage": "back_sides", "expanded": "Oregon myrtle figured Pacific"},
    "granadillo": {"usage": "back_sides", "expanded": "granadillo Mexican rosewood alternative"},
    "monkeypod": {"usage": "back_sides", "expanded": "monkeypod figured tropical"},
    "mango": {"usage": "back_sides", "expanded": "mango wood figured tropical"},
    
    # =========================================================================
    # NECKS
    # =========================================================================
    
    "maple neck": {"usage": "neck", "expanded": "one-piece maple neck bright snappy"},
    "mahogany neck": {"usage": "neck", "expanded": "mahogany neck warm"},
    "roasted maple": {"usage": "neck", "expanded": "roasted torrefied maple neck stable caramel"},
    "roasted maple neck": {"usage": "neck", "expanded": "heat-treated roasted maple neck"},
    "quartersawn maple": {"usage": "neck", "expanded": "quartersawn maple neck stable straight grain"},
    "spanish cedar neck": {"usage": "neck", "expanded": "Spanish cedar classical neck"},
    "walnut neck": {"usage": "neck", "expanded": "walnut neck warm stable"},
    "wenge neck": {"usage": "neck", "expanded": "wenge neck dark stable"},
    "multi-piece neck": {"usage": "neck", "expanded": "laminated multi-piece neck stable"},
    "through-neck": {"usage": "neck", "expanded": "neck-through construction sustain"},
    
    # =========================================================================
    # FRETBOARDS
    # =========================================================================
    
    "rosewood fretboard": {"usage": "fretboard", "expanded": "Indian rosewood fretboard warm"},
    "ebony fretboard": {"usage": "fretboard", "expanded": "ebony fretboard dark fast smooth"},
    "ebony": {"usage": "fretboard", "expanded": "solid ebony fretboard premium"},
    "macassar ebony": {"usage": "fretboard", "expanded": "Macassar ebony striped fretboard"},
    "gaboon ebony": {"usage": "fretboard", "expanded": "Gaboon ebony jet black"},
    "maple fretboard": {"usage": "fretboard", "expanded": "maple fretboard bright snappy"},
    "pau ferro": {"usage": "fretboard", "expanded": "pau ferro fretboard rosewood alternative"},
    "richlite": {"usage": "fretboard", "expanded": "Richlite composite fretboard sustainable"},
    "micarta": {"usage": "fretboard", "expanded": "Micarta phenolic fretboard"},
    "baked maple": {"usage": "fretboard", "expanded": "baked roasted maple fretboard dark"},
    "laurel": {"usage": "fretboard", "expanded": "Indian laurel fretboard"},
    "katalox": {"usage": "fretboard", "expanded": "katalox Mexican ebony fretboard"},
    "ziricote fretboard": {"usage": "fretboard", "expanded": "ziricote fretboard spider web"},
    "cocobolo fretboard": {"usage": "fretboard", "expanded": "cocobolo fretboard figured oily"},
    "snakewood": {"usage": "fretboard", "expanded": "snakewood fretboard rare exotic"},
}


# =============================================================================
# HARDWARE — Comprehensive
# =============================================================================

HARDWARE: Dict[str, Dict] = {
    # =========================================================================
    # HARDWARE FINISHES
    # =========================================================================
    
    "chrome": {"type": "finish", "expanded": "chrome hardware bright silver"},
    "chrome hardware": {"type": "finish", "expanded": "chrome plated hardware"},
    "nickel": {"type": "finish", "expanded": "nickel hardware warm silver"},
    "nickel hardware": {"type": "finish", "expanded": "nickel plated hardware vintage"},
    "aged nickel": {"type": "finish", "expanded": "aged nickel hardware tarnished vintage"},
    "gold hardware": {"type": "finish", "expanded": "gold plated hardware luxury"},
    "gold": {"type": "finish", "expanded": "gold hardware premium"},
    "black hardware": {"type": "finish", "expanded": "black hardware modern"},
    "cosmo black": {"type": "finish", "expanded": "cosmo black hardware Ibanez"},
    "satin chrome": {"type": "finish", "expanded": "satin chrome brushed hardware"},
    "brushed nickel": {"type": "finish", "expanded": "brushed satin nickel hardware"},
    "relic hardware": {"type": "finish", "expanded": "aged relic hardware worn patina"},
    "raw nickel": {"type": "finish", "expanded": "raw nickel hardware unplated"},
    "antique brass": {"type": "finish", "expanded": "antique brass hardware vintage"},
    "smoked chrome": {"type": "finish", "expanded": "smoked chrome dark chrome"},
    
    # =========================================================================
    # TUNERS
    # =========================================================================
    
    "vintage tuners": {"type": "tuner", "expanded": "vintage-style open-back tuning machines"},
    "open-back tuners": {"type": "tuner", "expanded": "open-back vintage tuning machines"},
    "open gear tuners": {"type": "tuner", "expanded": "open gear exposed tuners vintage"},
    "sealed tuners": {"type": "tuner", "expanded": "sealed die-cast tuning machines"},
    "locking tuners": {"type": "tuner", "expanded": "locking tuning machines quick change"},
    "grover": {"type": "tuner", "expanded": "Grover Rotomatic tuners"},
    "grover tuners": {"type": "tuner", "expanded": "Grover tuning machines"},
    "kluson": {"type": "tuner", "expanded": "Kluson vintage tuners single-line"},
    "kluson tuners": {"type": "tuner", "expanded": "Kluson Deluxe vintage style"},
    "gotoh": {"type": "tuner", "expanded": "Gotoh tuning machines precision"},
    "schaller": {"type": "tuner", "expanded": "Schaller tuners German"},
    "sperzel": {"type": "tuner", "expanded": "Sperzel locking tuners trim-lok"},
    "hipshot": {"type": "tuner", "expanded": "Hipshot tuners"},
    "waverly": {"type": "tuner", "expanded": "Waverly tuners acoustic premium"},
    "sloane": {"type": "tuner", "expanded": "Sloane classical tuners"},
    "3+3 tuners": {"type": "tuner", "expanded": "3+3 headstock tuner layout"},
    "6-inline tuners": {"type": "tuner", "expanded": "6-in-line headstock tuner layout"},
    "4+2 tuners": {"type": "tuner", "expanded": "4+2 headstock tuner layout PRS"},
    "keystone tuners": {"type": "tuner", "expanded": "keystone button vintage tuners"},
    "tulip tuners": {"type": "tuner", "expanded": "tulip button tuners Gibson vintage"},
    "butterbean tuners": {"type": "tuner", "expanded": "butterbean button acoustic"},
    
    # =========================================================================
    # BRIDGES — Electric
    # =========================================================================
    
    "tune-o-matic": {"type": "bridge", "expanded": "tune-o-matic bridge adjustable"},
    "tom": {"type": "bridge", "expanded": "tune-o-matic bridge stopbar tailpiece"},
    "abr-1": {"type": "bridge", "expanded": "ABR-1 tune-o-matic vintage"},
    "nashville": {"type": "bridge", "expanded": "Nashville tune-o-matic modern"},
    "wraparound": {"type": "bridge", "expanded": "wraparound bridge tailpiece combo"},
    "lightning bar": {"type": "bridge", "expanded": "lightning bar wraparound"},
    "badass": {"type": "bridge", "expanded": "Badass bridge heavy sustain"},
    
    # Tremolo
    "tremolo": {"type": "bridge", "expanded": "tremolo vibrato bridge"},
    "synchronized tremolo": {"type": "bridge", "expanded": "synchronized tremolo vintage"},
    "vintage tremolo": {"type": "bridge", "expanded": "vintage 6-screw tremolo"},
    "2-point tremolo": {"type": "bridge", "expanded": "2-point pivot tremolo modern"},
    "floyd rose": {"type": "bridge", "expanded": "Floyd Rose locking tremolo double locking"},
    "floyd": {"type": "bridge", "expanded": "Floyd Rose floating tremolo"},
    "original floyd rose": {"type": "bridge", "expanded": "Original Floyd Rose German"},
    "licensed floyd": {"type": "bridge", "expanded": "licensed Floyd Rose tremolo"},
    "edge tremolo": {"type": "bridge", "expanded": "Ibanez Edge tremolo"},
    "lo-pro edge": {"type": "bridge", "expanded": "Ibanez Lo-Pro Edge low profile"},
    "edge zero": {"type": "bridge", "expanded": "Ibanez Edge Zero ZPS"},
    "kahler": {"type": "bridge", "expanded": "Kahler tremolo cam system"},
    "bigsby": {"type": "bridge", "expanded": "Bigsby vibrato tailpiece"},
    "bigsby b5": {"type": "bridge", "expanded": "Bigsby B5 tremolo flatop"},
    "bigsby b7": {"type": "bridge", "expanded": "Bigsby B7 tremolo archtop"},
    "jazzmaster tremolo": {"type": "bridge", "expanded": "Jazzmaster floating tremolo"},
    "jaguar tremolo": {"type": "bridge", "expanded": "Jaguar tremolo mute"},
    "stetsbar": {"type": "bridge", "expanded": "Stetsbar tremolo retrofit"},
    "wilkinson": {"type": "bridge", "expanded": "Wilkinson tremolo"},
    
    # Fixed
    "hardtail": {"type": "bridge", "expanded": "hardtail fixed bridge"},
    "string-through": {"type": "bridge", "expanded": "string-through body hardtail"},
    "top-load": {"type": "bridge", "expanded": "top-load hardtail bridge"},
    "hipshot": {"type": "bridge", "expanded": "Hipshot fixed bridge"},
    
    # =========================================================================
    # BRIDGES — Acoustic
    # =========================================================================
    
    "pinless bridge": {"type": "bridge", "expanded": "pinless acoustic bridge"},
    "pin bridge": {"type": "bridge", "expanded": "traditional pin bridge acoustic"},
    "belly bridge": {"type": "bridge", "expanded": "belly bridge acoustic Martin style"},
    "pyramid bridge": {"type": "bridge", "expanded": "pyramid bridge vintage"},
    "moustache bridge": {"type": "bridge", "expanded": "moustache bridge vintage ornate"},
    "compensated saddle": {"type": "bridge", "expanded": "compensated bone saddle intonated"},
    "bone saddle": {"type": "bridge", "expanded": "bone saddle acoustic"},
    "tusq saddle": {"type": "bridge", "expanded": "Tusq synthetic saddle"},
    "tie block": {"type": "bridge", "expanded": "classical tie block bridge"},
    
    # =========================================================================
    # TAILPIECES
    # =========================================================================
    
    "stopbar": {"type": "tailpiece", "expanded": "stopbar tailpiece"},
    "stop tailpiece": {"type": "tailpiece", "expanded": "stop tailpiece aluminum"},
    "trapeze tailpiece": {"type": "tailpiece", "expanded": "trapeze tailpiece archtop"},
    "frequensator": {"type": "tailpiece", "expanded": "Frequensator split tailpiece"},
    "lyre tailpiece": {"type": "tailpiece", "expanded": "lyre vibrola tailpiece"},
    "maestro vibrola": {"type": "tailpiece", "expanded": "Maestro vibrola tremolo SG"},
    "g tailpiece": {"type": "tailpiece", "expanded": "G tailpiece Gretsch"},
    
    # =========================================================================
    # PICKUPS
    # =========================================================================
    
    # Humbuckers
    "humbucker": {"type": "pickup", "expanded": "dual humbucker pickups"},
    "humbuckers": {"type": "pickup", "expanded": "humbucker pickups warm thick"},
    "paf": {"type": "pickup", "expanded": "PAF patent applied for humbucker vintage"},
    "paf humbucker": {"type": "pickup", "expanded": "PAF style humbucker warm"},
    "burstbucker": {"type": "pickup", "expanded": "Gibson Burstbucker humbucker"},
    "57 classic": {"type": "pickup", "expanded": "Gibson 57 Classic humbucker"},
    "490r 498t": {"type": "pickup", "expanded": "Gibson 490R 498T humbucker set"},
    "dirty fingers": {"type": "pickup", "expanded": "Gibson Dirty Fingers hot humbucker"},
    "seymour duncan": {"type": "pickup", "expanded": "Seymour Duncan humbucker"},
    "jb": {"type": "pickup", "expanded": "Seymour Duncan JB humbucker"},
    "59": {"type": "pickup", "expanded": "Seymour Duncan 59 humbucker PAF"},
    "pearly gates": {"type": "pickup", "expanded": "Seymour Duncan Pearly Gates"},
    "dimarzio": {"type": "pickup", "expanded": "DiMarzio humbucker"},
    "super distortion": {"type": "pickup", "expanded": "DiMarzio Super Distortion hot"},
    "evolution": {"type": "pickup", "expanded": "DiMarzio Evolution Vai"},
    "emg": {"type": "pickup", "expanded": "EMG active humbucker"},
    "emg 81": {"type": "pickup", "expanded": "EMG 81 active hot"},
    "emg 85": {"type": "pickup", "expanded": "EMG 85 active warm"},
    "fishman fluence": {"type": "pickup", "expanded": "Fishman Fluence modern active"},
    "bareknuckle": {"type": "pickup", "expanded": "Bare Knuckle boutique humbucker"},
    "uncovered humbucker": {"type": "pickup", "expanded": "uncovered open coil humbucker"},
    "covered humbucker": {"type": "pickup", "expanded": "nickel covered humbucker"},
    "zebra humbucker": {"type": "pickup", "expanded": "zebra coil humbucker"},
    "mini humbucker": {"type": "pickup", "expanded": "mini humbucker firebird"},
    
    # Single coils
    "single coil": {"type": "pickup", "expanded": "single coil pickups bright clear"},
    "single coils": {"type": "pickup", "expanded": "single coil pickups articulate"},
    "vintage single coil": {"type": "pickup", "expanded": "vintage output single coil"},
    "hot single coil": {"type": "pickup", "expanded": "hot overwound single coil"},
    "texas special": {"type": "pickup", "expanded": "Fender Texas Special single coil"},
    "custom shop": {"type": "pickup", "expanded": "Fender Custom Shop pickups"},
    "fat 50s": {"type": "pickup", "expanded": "Fender Fat 50s single coil"},
    "noiseless": {"type": "pickup", "expanded": "noiseless single coil stacked"},
    
    # P-90
    "p90": {"type": "pickup", "expanded": "P-90 single coil fat warm"},
    "p-90": {"type": "pickup", "expanded": "Gibson P-90 soapbar"},
    "p90s": {"type": "pickup", "expanded": "dual P-90 pickups"},
    "soapbar": {"type": "pickup", "expanded": "soapbar P-90 pickup"},
    "dog ear": {"type": "pickup", "expanded": "dog ear P-90 pickup"},
    
    # Other pickups
    "filtertron": {"type": "pickup", "expanded": "Filtertron pickup Gretsch"},
    "dynasonic": {"type": "pickup", "expanded": "Dynasonic pickup Gretsch"},
    "gold foil": {"type": "pickup", "expanded": "gold foil pickup vintage Japanese"},
    "lipstick": {"type": "pickup", "expanded": "lipstick tube pickup Danelectro"},
    "jazzmaster pickup": {"type": "pickup", "expanded": "wide range Jazzmaster pickup"},
    "wide range": {"type": "pickup", "expanded": "wide range humbucker Fender"},
    "toaster": {"type": "pickup", "expanded": "toaster top pickup Rickenbacker"},
    "charlie christian": {"type": "pickup", "expanded": "Charlie Christian bar pickup"},
    "floating pickup": {"type": "pickup", "expanded": "floating archtop pickup"},
    "piezo": {"type": "pickup", "expanded": "piezo pickup acoustic electric"},
    "undersaddle": {"type": "pickup", "expanded": "undersaddle piezo pickup"},
    "soundhole pickup": {"type": "pickup", "expanded": "magnetic soundhole pickup"},
    
    # Configurations
    "hss": {"type": "pickup", "expanded": "HSS humbucker single single configuration"},
    "hsh": {"type": "pickup", "expanded": "HSH humbucker single humbucker"},
    "ssh": {"type": "pickup", "expanded": "SSH single single humbucker"},
    "hhh": {"type": "pickup", "expanded": "triple humbucker configuration"},
    "sss": {"type": "pickup", "expanded": "triple single coil configuration"},
    "hh": {"type": "pickup", "expanded": "dual humbucker configuration"},
    "pp": {"type": "pickup", "expanded": "dual P-90 configuration"},
    "coil split": {"type": "pickup", "expanded": "coil split humbucker versatile"},
    "coil tap": {"type": "pickup", "expanded": "coil tap variable output"},
    
    # =========================================================================
    # NUTS
    # =========================================================================
    
    "bone nut": {"type": "nut", "expanded": "bone nut traditional sustain"},
    "tusq nut": {"type": "nut", "expanded": "Graph Tech Tusq nut synthetic"},
    "brass nut": {"type": "nut", "expanded": "brass nut bright sustain"},
    "graphite nut": {"type": "nut", "expanded": "graphite nut self-lubricating"},
    "locking nut": {"type": "nut", "expanded": "locking nut Floyd Rose"},
    "roller nut": {"type": "nut", "expanded": "roller nut LSR Fender"},
    "zero fret": {"type": "nut", "expanded": "zero fret consistent action"},
    "earvana": {"type": "nut", "expanded": "Earvana compensated nut intonation"},
    
    # =========================================================================
    # PICKGUARDS
    # =========================================================================
    
    "pickguard": {"type": "pickguard", "expanded": "pickguard scratchplate"},
    "white pickguard": {"type": "pickguard", "expanded": "white single-ply pickguard"},
    "black pickguard": {"type": "pickguard", "expanded": "black pickguard"},
    "tortoise pickguard": {"type": "pickguard", "expanded": "tortoiseshell pickguard"},
    "mint green pickguard": {"type": "pickguard", "expanded": "mint green pickguard vintage"},
    "parchment pickguard": {"type": "pickguard", "expanded": "parchment cream pickguard"},
    "pearloid pickguard": {"type": "pickguard", "expanded": "pearloid pickguard"},
    "gold pickguard": {"type": "pickguard", "expanded": "gold anodized pickguard"},
    "mirror pickguard": {"type": "pickguard", "expanded": "mirror chrome pickguard"},
    "red tortoise": {"type": "pickguard", "expanded": "red tortoise pickguard"},
    "3-ply pickguard": {"type": "pickguard", "expanded": "3-ply pickguard"},
    "no pickguard": {"type": "pickguard", "expanded": "no pickguard clean top"},
    "golpeador": {"type": "pickguard", "expanded": "golpeador tap plate flamenco"},
}


# =============================================================================
# NECK PROFILES
# =============================================================================

NECK_PROFILES: Dict[str, str] = {
    "c profile": "C-shaped neck profile comfortable standard",
    "modern c": "modern C neck profile slim comfortable",
    "vintage c": "vintage C neck profile fuller",
    "soft c": "soft C neck profile rounded",
    "d profile": "D-shaped neck profile flat back",
    "modern d": "modern D neck profile flat fast",
    "v profile": "V-shaped neck profile vintage",
    "soft v": "soft V neck profile subtle",
    "hard v": "hard V neck profile pronounced vintage",
    "u profile": "U-shaped neck profile chunky baseball bat",
    "boat neck": "boat neck thick vintage",
    "baseball bat": "baseball bat neck thick round",
    "wizard": "Ibanez Wizard neck super thin flat fast",
    "super wizard": "Ibanez Super Wizard thinnest",
    "asymmetric": "asymmetric neck profile ergonomic",
    "compound radius": "compound radius fretboard 9.5 to 14",
    "slim taper": "slim taper neck profile Gibson",
    "rounded": "rounded neck profile comfortable",
    "oval": "oval C neck profile",
    "60s slim taper": "1960s slim taper neck Gibson thin",
    "50s rounded": "1950s rounded neck Gibson thick",
}


# =============================================================================
# SCALE LENGTHS
# =============================================================================

SCALE_LENGTHS: Dict[str, str] = {
    "24.75": "24.75 inch Gibson scale length",
    "25.5": "25.5 inch Fender scale length",
    "25": "25 inch PRS scale length",
    "24": "24 inch short scale",
    "22.5": "22.5 inch 3/4 scale student",
    "650mm": "650mm classical scale length",
    "640mm": "640mm shorter classical scale",
    "660mm": "660mm longer classical scale",
    "27": "27 inch baritone scale",
    "28": "28 inch baritone scale extended",
    "30": "30 inch bass short scale",
    "34": "34 inch bass standard scale",
    "35": "35 inch bass extended scale",
    "multiscale": "multiscale fanned fret variable scale",
}


# =============================================================================
# CONSTRUCTION DETAILS
# =============================================================================

BRACING_PATTERNS: Dict[str, str] = {
    "x bracing": "X-bracing acoustic standard Martin",
    "scalloped x bracing": "scalloped X-bracing responsive vintage",
    "forward shifted x": "forward shifted X-bracing modern responsive",
    "v bracing": "V-bracing acoustic vintage ladder",
    "ladder bracing": "ladder bracing parlor vintage",
    "fan bracing": "fan bracing classical Torres",
    "lattice bracing": "lattice bracing classical modern loud",
    "double x": "double X-bracing jumbo Gibson",
    "hybrid bracing": "hybrid X-bracing modern",
    "a-frame": "A-frame bracing Taylor",
    "c-class": "C-Class bracing Taylor",
}

BINDING_STYLES: Dict[str, str] = {
    "binding": "body binding decorative",
    "cream binding": "vintage cream binding",
    "white binding": "white binding clean",
    "black binding": "black binding subtle",
    "ivory binding": "ivory binding vintage",
    "tortoise binding": "tortoiseshell binding",
    "abalone binding": "abalone shell binding premium",
    "herringbone binding": "herringbone purfling binding",
    "multi-ply binding": "multi-ply layered binding deluxe",
    "five-ply binding": "five-ply binding custom",
    "seven-ply binding": "seven-ply binding premium",
    "no binding": "unbound body",
    "neck binding": "bound fretboard edges",
    "headstock binding": "bound headstock",
    "full binding": "fully bound body neck headstock",
}

PURFLING: Dict[str, str] = {
    "purfling": "purfling decorative inlay strip",
    "black white black": "black white black purfling BWB",
    "herringbone purfling": "herringbone purfling Martin style",
    "abalone purfling": "abalone shell purfling",
    "rope purfling": "rope pattern purfling",
    "wood purfling": "contrasting wood purfling",
    "no purfling": "no purfling lines",
}


# =============================================================================
# INLAYS — Comprehensive
# =============================================================================

INLAY_MATERIALS: Dict[str, str] = {
    "mother of pearl": "mother of pearl MOP inlay",
    "mop": "mother of pearl inlay iridescent",
    "abalone": "abalone shell inlay colorful",
    "paua": "paua shell inlay New Zealand",
    "pearloid": "pearloid plastic inlay",
    "clay": "clay dot inlay vintage",
    "acrylic": "acrylic inlay modern",
    "wood": "wood inlay contrasting",
    "brass": "brass inlay metallic",
    "silver": "sterling silver inlay",
    "gold": "gold inlay luxury",
    "stone": "stone inlay turquoise coral",
    "luminlay": "luminescent glow-in-dark inlay",
}

INLAY_PATTERNS: Dict[str, str] = {
    # Fretboard markers
    "dots": "dot inlay markers",
    "small dots": "small dot inlays subtle",
    "large dots": "large dot inlays",
    "offset dots": "offset dot inlays modern",
    "side dots": "side dot markers only clean",
    "no inlays": "unmarked fretboard clean",
    "blocks": "block inlay markers large",
    "small blocks": "small block inlays",
    "trapezoids": "trapezoid inlays Gibson vintage",
    "split blocks": "split block inlays",
    "parallelograms": "parallelogram inlays",
    "shark fin": "shark fin inlays Jackson",
    "sharkfin": "sharkfin inlays pointed",
    "birds": "bird inlays PRS",
    "old school birds": "old school bird inlays PRS vintage",
    "vines": "tree of life vine inlays",
    "tree of life": "tree of life inlay elaborate",
    "dragons": "dragon inlay ornate",
    "crosses": "cross inlay gothic",
    "crowns": "crown inlays ornate",
    "diamonds": "diamond inlays",
    "split diamond": "split diamond headstock inlay",
    "snowflakes": "snowflake inlays Martin",
    "stars": "star inlays",
    "moons": "moon phase inlays",
    "roman numerals": "Roman numeral fret markers",
    "gothic": "gothic style inlays ornate",
    "tribal": "tribal pattern inlays",
    "custom inlays": "custom artistic inlays",
    
    # Position markers
    "12th fret": "12th fret double inlay",
    "double dot": "double dot 12th fret",
}


# =============================================================================
# ROSETTE STYLES — For Acoustics
# =============================================================================

ROSETTE_STYLES: Dict[str, str] = {
    "rosette": "soundhole rosette decoration",
    "abalone rosette": "abalone shell rosette inlay",
    "herringbone rosette": "herringbone purfling rosette",
    "wood rosette": "wood mosaic rosette traditional",
    "mosaic rosette": "Spanish mosaic tile rosette",
    "rope rosette": "rope pattern rosette",
    "simple rosette": "simple concentric ring rosette",
    "multi-ring rosette": "multi-ring rosette decorative",
    "pearl rosette": "mother of pearl rosette",
    "black white rosette": "black white ring rosette",
    "colored rosette": "colored wood rosette",
    "torres rosette": "Torres style mosaic rosette classical",
    "hauser rosette": "Hauser style rosette classical",
    "fleta rosette": "Fleta style rosette classical",
    "romanillos rosette": "Romanillos style rosette classical",
    "no rosette": "no rosette clean modern",
    "sound port": "sound port side monitor hole",
}


# =============================================================================
# LUTHIER / BUILDER STYLES
# =============================================================================

BUILDER_STYLES: Dict[str, str] = {
    # Acoustic
    "martin style": "Martin-style construction American",
    "taylor style": "Taylor-style bolt-on modern",
    "gibson acoustic": "Gibson-style round shoulder acoustic",
    "guild style": "Guild-style acoustic",
    "collings": "Collings-style premium acoustic",
    "santa cruz": "Santa Cruz style boutique",
    "bourgeois": "Bourgeois-style premium",
    "huss dalton": "Huss & Dalton style traditional",
    "lowden": "Lowden-style Irish acoustic",
    "lakewood": "Lakewood-style German",
    "mcpherson": "McPherson-style carbon fiber offset",
    
    # Classical
    "torres": "Torres-style Spanish classical fan bracing",
    "hauser": "Hauser-style German classical",
    "fleta": "Fleta-style Spanish classical",
    "ramirez": "Ramirez-style Spanish classical",
    "romanillos": "Romanillos-style classical",
    "smallman": "Smallman-style lattice braced",
    "humphrey": "Humphrey Millennium classical",
    "friederich": "Friederich-style French classical",
    "kohno": "Kohno-style Japanese classical",
    
    # Archtop
    "gibson archtop": "Gibson-style carved archtop",
    "dangelico": "D'Angelico-style archtop",
    "stromberg": "Stromberg-style large archtop",
    "benedetto style": "Benedetto-style modern archtop",
    "monteleone": "Monteleone-style archtop",
    
    # Electric
    "fender style": "Fender-style bolt-on electric",
    "gibson style": "Gibson-style set-neck electric",
    "prs style": "PRS-style carved top",
    "suhr": "Suhr-style modern boutique",
    "anderson": "Tom Anderson style boutique",
    "tyler": "James Tyler style modern",
    "kiesel": "Kiesel/Carvin style custom",
    "mayones": "Mayones style Polish boutique",
    "strandberg": "Strandberg style ergonomic headless",
}


# =============================================================================
# PHOTOGRAPHY STYLES
# =============================================================================

PHOTOGRAPHY_STYLES: Dict[str, str] = {
    # Studio styles
    "product": "professional product photography studio lighting clean background 8K highly detailed",
    "studio": "professional studio photography softbox lighting gradient background",
    "catalog": "clean catalog photography neutral background even lighting true colors",
    "commercial": "commercial product shot advertising quality",
    "e-commerce": "e-commerce white background product shot",
    
    # Dramatic
    "dramatic": "dramatic side lighting dark background moody atmosphere professional",
    "hero": "hero shot low angle dramatic lighting powerful composition",
    "cinematic": "cinematic lighting film quality dramatic shadows",
    "noir": "noir style dramatic shadows high contrast",
    "chiaroscuro": "chiaroscuro dramatic light dark contrast",
    
    # Lifestyle
    "lifestyle": "lifestyle shot wooden floor natural window light cozy atmosphere",
    "player": "musician playing guitar action shot stage lighting performance",
    "stage": "stage lighting concert atmosphere dramatic",
    "live": "live performance dynamic lighting energy",
    "workshop": "luthier workshop natural light wood shavings tools",
    "studio recording": "recording studio setting microphones professional",
    
    # Natural
    "natural light": "natural window light soft shadows warm",
    "outdoor": "outdoor natural light golden hour",
    "golden hour": "golden hour warm sunset lighting",
    
    # Artistic
    "artistic": "artistic photography creative lighting unique angles fine art",
    "vintage": "vintage photography warm tones film grain nostalgic",
    "film": "film photography grain Kodak Portra aesthetic",
    "fine art": "fine art photography gallery quality artistic",
    "minimalist": "minimalist composition clean simple elegant",
    
    # Technical
    "floating": "floating on pure white background soft shadows commercial",
    "detail": "macro detail shot close-up wood grain hardware",
    "close-up": "close-up detail shot shallow depth of field",
    "360": "360 degree product view all angles",
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_all_body_shapes() -> List[str]:
    """Get all body shape names."""
    return list(BODY_SHAPES.keys())


def get_body_shapes_by_category(category: GuitarCategory) -> List[str]:
    """Get body shapes for a specific category."""
    return [
        name for name, data in BODY_SHAPES.items()
        if data["category"] == category
    ]


def get_all_finishes() -> List[str]:
    """Get all finish names."""
    return list(FINISHES.keys())


def get_finishes_by_type(finish_type: FinishType) -> List[str]:
    """Get finishes of a specific type."""
    return [
        name for name, data in FINISHES.items()
        if data["type"] == finish_type
    ]


def get_all_tonewoods() -> List[str]:
    """Get all tonewood names."""
    return list(TONEWOODS.keys())


def get_tonewoods_by_usage(usage: str) -> List[str]:
    """Get tonewoods for specific usage (top, back_sides, neck, fretboard)."""
    return [
        name for name, data in TONEWOODS.items()
        if data["usage"] == usage
    ]


def expand_term(term: str) -> str:
    """
    Expand a term to its full description.
    Searches all vocabulary categories.
    """
    term_lower = term.lower()
    
    # Check each vocabulary
    if term_lower in BODY_SHAPES:
        return BODY_SHAPES[term_lower]["expanded"]
    if term_lower in FINISHES:
        return FINISHES[term_lower]["expanded"]
    if term_lower in TONEWOODS:
        return TONEWOODS[term_lower]["expanded"]
    if term_lower in HARDWARE:
        return HARDWARE[term_lower]["expanded"]
    if term_lower in INLAY_PATTERNS:
        return INLAY_PATTERNS[term_lower]
    if term_lower in ROSETTE_STYLES:
        return ROSETTE_STYLES[term_lower]
    if term_lower in NECK_PROFILES:
        return NECK_PROFILES[term_lower]
    if term_lower in PHOTOGRAPHY_STYLES:
        return PHOTOGRAPHY_STYLES[term_lower]
    if term_lower in BUILDER_STYLES:
        return BUILDER_STYLES[term_lower]
    if term_lower in BRACING_PATTERNS:
        return BRACING_PATTERNS[term_lower]
    if term_lower in BINDING_STYLES:
        return BINDING_STYLES[term_lower]
    
    return term  # Return unchanged if not found


def get_vocabulary_stats() -> Dict[str, int]:
    """Get counts of all vocabulary categories."""
    return {
        "body_shapes": len(BODY_SHAPES),
        "finishes": len(FINISHES),
        "tonewoods": len(TONEWOODS),
        "hardware": len(HARDWARE),
        "inlay_patterns": len(INLAY_PATTERNS),
        "inlay_materials": len(INLAY_MATERIALS),
        "rosette_styles": len(ROSETTE_STYLES),
        "neck_profiles": len(NECK_PROFILES),
        "scale_lengths": len(SCALE_LENGTHS),
        "bracing_patterns": len(BRACING_PATTERNS),
        "binding_styles": len(BINDING_STYLES),
        "purfling": len(PURFLING),
        "photography_styles": len(PHOTOGRAPHY_STYLES),
        "builder_styles": len(BUILDER_STYLES),
    }


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demo the expanded vocabulary."""
    print("=" * 70)
    print("🎸 EXPANDED LUTHIER VOCABULARY")
    print("=" * 70)
    
    stats = get_vocabulary_stats()
    total = sum(stats.values())
    
    print(f"\n📊 VOCABULARY STATISTICS ({total} total terms)")
    print("-" * 40)
    for category, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"   {category:20} {count:4}")
    
    print(f"\n🎸 BODY SHAPES BY CATEGORY")
    print("-" * 40)
    for cat in GuitarCategory:
        shapes = get_body_shapes_by_category(cat)
        if shapes:
            print(f"   {cat.value:12} {len(shapes):3} shapes")
    
    print(f"\n🎨 FINISHES BY TYPE")
    print("-" * 40)
    for ft in FinishType:
        finishes = get_finishes_by_type(ft)
        print(f"   {ft.value:12} {len(finishes):3} finishes")
    
    print(f"\n🪵 TONEWOODS BY USAGE")
    print("-" * 40)
    for usage in ["top", "back_sides", "neck", "fretboard"]:
        woods = get_tonewoods_by_usage(usage)
        print(f"   {usage:12} {len(woods):3} woods")
    
    print(f"\n🔧 SAMPLE EXPANSIONS")
    print("-" * 40)
    test_terms = [
        "dreadnought", "les paul", "es-335",
        "sunburst", "french polish", "quilted maple",
        "sitka spruce", "brazilian rosewood",
        "paf", "floyd rose", "birds",
        "torres", "x bracing", "herringbone rosette",
    ]
    for term in test_terms:
        expanded = expand_term(term)
        print(f"   {term:20} → {expanded[:40]}...")
    
    print(f"\n" + "=" * 70)
    print("Vocabulary ready for image generation!")
    print("=" * 70)


if __name__ == "__main__":
    demo()

# =============================================================================
# BACKWARD COMPATIBILITY RE-EXPORT
# Import from canonical app.vision.vocabulary for the new minimal API
# =============================================================================
from app.vision.vocabulary import *  # noqa: F401,F403
