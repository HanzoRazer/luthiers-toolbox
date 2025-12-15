"""
Selmer-Maccaferri D-hole Specifications for Luthier's ToolBox
Source: French luthier plans "Guitare jazz manouche dans le style Maccaferri"

All dimensions in mm unless noted.
Status: TEMPLATE - measurements to be verified/completed
"""

# =============================================================================
# BODY DIMENSIONS
# =============================================================================

BODY_LENGTH = None  # TODO: measure from plans
UPPER_BOUT_WIDTH = None  # TODO
LOWER_BOUT_WIDTH = None  # TODO  
WAIST_WIDTH = None  # TODO
BODY_DEPTH_NECK = None  # TODO
BODY_DEPTH_TAIL = None  # TODO

# D-hole dimensions (the distinctive oval soundhole)
D_HOLE_WIDTH = None  # TODO
D_HOLE_HEIGHT = None  # TODO
D_HOLE_OFFSET_FROM_CENTER = None  # Offset toward bass side

# =============================================================================
# NECK DIMENSIONS
# =============================================================================

SCALE_LENGTH = 670  # Standard Selmer scale (some are 650mm)
NUT_WIDTH = None  # TODO
NECK_WIDTH_12TH_FRET = None  # TODO
HEADSTOCK_LENGTH = 155  # Visible in plans
HEADSTOCK_WIDTH = None  # TODO

# Neck angle and joint
NECK_ANGLE_DEGREES = None  # TODO - appears ~1.5° from plans
DOVETAIL_LENGTH = None  # TODO
HEEL_DEPTH = 8  # Visible in plans

# =============================================================================
# NECK PROFILE (cross-sections at fret positions)
# Format: {fret_number: (width_mm, depth_mm)}
# =============================================================================

NECK_PROFILES = {
    0: (None, None),   # At nut
    1: (None, None),
    5: (None, None),
    7: (None, None),
    9: (None, None),
    12: (None, None),
}

# =============================================================================
# FRET POSITIONS (distance from nut in mm)
# Partial data visible in plans - to be completed
# =============================================================================

FRET_POSITIONS = {
    0: 0,
    1: 35.5,
    2: 63.8,
    3: 101.8,
    4: 135.0,
    5: 165.5,
    6: 193.5,
    7: 212.9,
    8: 236.3,
    9: 253.5,
    10: 270.3,
    11: 304.4,
    12: None,  # TODO - should be scale_length / 2 = 335mm
    13: None,
    14: None,
    15: None,
    16: None,
    17: None,
    18: None,
    19: None,
    20: None,
    21: None,  # Selmer typically has 21 frets
}

# =============================================================================
# BRACING
# =============================================================================

# Top bracing - ladder style with transverse braces
TOP_BRACES = {
    "brace_1": {"position_from_neck": None, "width": None, "height": None},
    "brace_2": {"position_from_neck": None, "width": None, "height": None},
    "brace_3": {"position_from_neck": None, "width": None, "height": None},
    "soundhole_brace": {"width": None, "height": None},
}

# Brace spacing visible in plans
BRACE_SPACING = [90, 90, 50]  # mm between braces (visible in plans)

# Back bracing
BACK_BRACES = {
    # TODO: extract from plans
}

# =============================================================================
# SOUNDBOARD CONSTRUCTION
# =============================================================================

SOUNDBOARD_ARCH_AT_BRIDGE = 8  # "8mm across width at bridge" from plans
SOUNDBOARD_THICKNESS = None  # TODO
SOUNDBOARD_BENT_AT_CENTER = True  # Note: "halves are bent at this point then trimmed and joined"

# =============================================================================
# MATERIALS (from plans)
# =============================================================================

MATERIALS = {
    "soundboard": "Spruce",
    "back": "Laminated Rosewood/Mahogany",
    "sides": "Maple with three dural plates",  # Dural = aluminum alloy reinforcement
    "neck": "Perpendicular to fingerboard",  # Construction note
    "fingerboard": "Ebony",
    "bridge": "Walnut with ebony top (hollowed out)",
    "bridge_construction": "Side pieces glued to soundboard, middle detachable",
}

# =============================================================================
# SIDE PROFILE (depth at distance from neck block)
# Format: {distance_mm: depth_mm}
# =============================================================================

SIDE_PROFILE = {
    0: None,    # At neck block
    50: None,
    100: None,
    150: None,
    200: None,
    250: None,
    300: None,
    350: None,
    400: None,
    450: None,  # At tail block
}

# =============================================================================
# HEADSTOCK
# =============================================================================

HEADSTOCK = {
    "length": 155,
    "width": None,
    "thickness": None,
    "slot_length": None,  # For slotted headstock
    "slot_width": None,
    "angle": None,  # Headstock angle from neck
}

# =============================================================================
# BRIDGE
# =============================================================================

BRIDGE = {
    "length": None,
    "width": None,
    "height": None,
    "saddle_radius": None,  # Flat or radiused
    "mustache_wings": True,  # Distinctive Selmer feature
}

# =============================================================================
# PICKGUARD (if applicable)
# =============================================================================

PICKGUARD = {
    "present": True,  # Selmers typically have pickguard
    "shape": "comma",  # Distinctive shape
    "length": None,
    "width": None,
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_fret_positions(scale_length=670, num_frets=21):
    """
    Calculate fret positions using Rule of 18 (actually 17.817)
    Returns dict of {fret_number: distance_from_nut_mm}
    """
    positions = {0: 0}
    remaining = scale_length
    
    for fret in range(1, num_frets + 1):
        fret_distance = remaining / 17.817
        remaining -= fret_distance
        positions[fret] = round(scale_length - remaining, 2)
    
    return positions


def get_neck_depth_at_fret(fret):
    """
    Interpolate neck depth at any fret position.
    Returns None if profile data not yet populated.
    """
    if not any(v[1] for v in NECK_PROFILES.values() if v[1]):
        return None
    
    # Linear interpolation between known points
    known = [(f, d) for f, (w, d) in NECK_PROFILES.items() if d is not None]
    if len(known) < 2:
        return None
    
    known.sort()
    for i in range(len(known) - 1):
        f1, d1 = known[i]
        f2, d2 = known[i + 1]
        if f1 <= fret <= f2:
            t = (fret - f1) / (f2 - f1)
            return d1 + t * (d2 - d1)
    
    return None


# =============================================================================
# VALIDATION
# =============================================================================

def validate_specs():
    """Check which specifications are still missing."""
    missing = []
    
    # Check main dimensions
    for name in ['BODY_LENGTH', 'UPPER_BOUT_WIDTH', 'LOWER_BOUT_WIDTH', 
                 'WAIST_WIDTH', 'NUT_WIDTH', 'D_HOLE_WIDTH', 'D_HOLE_HEIGHT']:
        if globals().get(name) is None:
            missing.append(name)
    
    # Check fret positions
    missing_frets = [f for f, pos in FRET_POSITIONS.items() if pos is None]
    if missing_frets:
        missing.append(f"FRET_POSITIONS: frets {missing_frets}")
    
    # Check side profile
    missing_depths = [d for d, v in SIDE_PROFILE.items() if v is None]
    if missing_depths:
        missing.append(f"SIDE_PROFILE: positions {missing_depths}")
    
    return missing


def completion_status():
    """Return percentage of specs that are populated."""
    total = 0
    filled = 0
    
    for name in ['BODY_LENGTH', 'UPPER_BOUT_WIDTH', 'LOWER_BOUT_WIDTH',
                 'WAIST_WIDTH', 'BODY_DEPTH_NECK', 'BODY_DEPTH_TAIL',
                 'D_HOLE_WIDTH', 'D_HOLE_HEIGHT', 'NUT_WIDTH',
                 'NECK_WIDTH_12TH_FRET', 'NECK_ANGLE_DEGREES']:
        total += 1
        if globals().get(name) is not None:
            filled += 1
    
    # Frets
    total += len(FRET_POSITIONS)
    filled += sum(1 for v in FRET_POSITIONS.values() if v is not None)
    
    # Side profile  
    total += len(SIDE_PROFILE)
    filled += sum(1 for v in SIDE_PROFILE.values() if v is not None)
    
    return round(filled / total * 100, 1) if total > 0 else 0


if __name__ == "__main__":
    print("Selmer-Maccaferri D-hole Specifications")
    print("=" * 50)
    print(f"Completion: {completion_status()}%")
    print(f"\nMissing specs:")
    for m in validate_specs():
        print(f"  • {m}")
    
    print(f"\nCalculated fret positions (670mm scale):")
    calc = calculate_fret_positions()
    for f in [0, 5, 12, 21]:
        print(f"  Fret {f}: {calc[f]:.1f}mm")
