"""
1937 Martin D-28 Specifications for Luthier's ToolBox
Source: John Arnold technical drawings, Serial #65260

All dimensions in inches unless noted.
"""

# Side depth profile (distance from neck -> side depth)
# Raw measurements (excludes top/back/kerfing)
SIDE_PROFILE_RAW_IN = {
    0.0: 3.750,
    3.0: 3.740,
    6.0: 3.895,
    9.0: 4.085,
    10.5: 4.220,  # Waist
    12.0: 4.240,
    15.0: 4.350,
    18.0: 4.455,
    21.0: 4.565,
    24.0: 4.640,
    27.0: 4.670,
    30.4375: 4.720,  # Bottom
}

# With kerfing (~0.25" added)
SIDE_PROFILE_WITH_KERFING_IN = {
    0.0: 4.000,
    3.0: 3.990,
    6.0: 4.145,
    9.0: 4.335,
    10.5: 4.470,
    12.0: 4.490,
    15.0: 4.600,
    18.0: 4.705,
    21.0: 4.815,
    24.0: 4.890,
    27.0: 4.920,
    30.4375: 4.970,
}

# Convert to mm for CNC
def to_mm(profile_dict):
    return {k * 25.4: v * 25.4 for k, v in profile_dict.items()}

SIDE_PROFILE_RAW_MM = to_mm(SIDE_PROFILE_RAW_IN)
SIDE_PROFILE_WITH_KERFING_MM = to_mm(SIDE_PROFILE_WITH_KERFING_IN)

# Back brace dimensions (width, depth in inches)
BACK_BRACES = {
    "BB1": (0.320, 0.450),  # Upper bout
    "BB2": (0.320, 0.450),  # Above waist
    "BB3": (0.735, 0.385),  # Below waist
    "BB4": (0.760, 0.375),  # Lower bout
}

# Top bracing
TOP_BRACE_THICKNESS_IN = 0.095
X_BRACE_PATTERN = "scalloped"

# Overall dimensions (inches)
BODY_LENGTH = 20.0
UPPER_BOUT = 11.5
LOWER_BOUT = 15.625
WAIST = 11.0
SCALE_LENGTH = 25.4
SOUNDHOLE_DIAMETER = 4.0
