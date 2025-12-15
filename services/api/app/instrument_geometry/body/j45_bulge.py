"""
Gibson J-45 Body Outline Data
Extracted from ag_45_dxf_040409.dxf
Size: 398.5mm × 504.8mm (15.7" × 19.9")

To integrate into Luthier's ToolBox:
1. Add J45_BODY_OUTLINE to instrument_geometry/body/outlines.py
2. Replace the placeholder rectangle in _BODY_OUTLINES["j_45"]

Note: This is the perimeter outline only. The original DXF contains
additional interior features (bracing patterns, sound hole, etc.)
"""

# 30-point outline with bulge data preserved
# Format: (x_mm, y_mm, start_width, end_width, bulge)
# Bulge values encode arc curvature between points
J45_BODY_OUTLINE_WITH_BULGE = [
    (199.23, 504.82, 0, 0, -0.0078),
    (224.57, 504.43, 0, 0, -0.0688),
    (274.49, 497.03, 0, 0, -0.0767),
    (307.65, 480.07, 0, 0, -0.1677),
    (339.02, 431.09, 0, 0, -0.1247),
    (337.48, 381.92, 0, 0, 0.0922),
    (331.00, 330.06, 0, 0, 0.1290),
    (346.47, 277.86, 0, 0, 0.0),
    (371.80, 227.21, 0, 0, -0.0268),
    (392.28, 176.80, 0, 0, -0.0923),
    (398.47, 127.15, 0, 0, -0.0896),
    (387.59, 77.40, 0, 0, -0.1528),
    (347.52, 28.06, 0, 0, -0.1161),
    (275.12, 2.37, 0, 0, -0.0234),
    (224.60, 0.40, 0, 0, -0.0078),
    (199.23, 0.00, 0, 0, -0.0078),
    (173.87, 0.40, 0, 0, -0.0234),
    (123.34, 2.37, 0, 0, -0.1161),
    (50.95, 28.06, 0, 0, -0.1528),
    (10.88, 77.40, 0, 0, -0.0896),
    (0.00, 127.15, 0, 0, -0.0923),
    (6.19, 176.80, 0, 0, -0.0268),
    (26.67, 227.21, 0, 0, 0.0),
    (52.00, 277.86, 0, 0, 0.1290),
    (67.47, 330.06, 0, 0, 0.0922),
    (60.99, 381.92, 0, 0, -0.1247),
    (59.45, 431.09, 0, 0, -0.1677),
    (90.82, 480.07, 0, 0, -0.0767),
    (123.98, 497.03, 0, 0, -0.0688),
    (173.90, 504.43, 0, 0, -0.0078),
]

# Simple XY outline for outlines.py (no bulge)
# Replace the existing placeholder in _BODY_OUTLINES
J45_BODY_OUTLINE = [
    (199.23, 504.82),
    (224.57, 504.43),
    (274.49, 497.03),
    (307.65, 480.07),
    (339.02, 431.09),
    (337.48, 381.92),
    (331.00, 330.06),
    (346.47, 277.86),
    (371.80, 227.21),
    (392.28, 176.80),
    (398.47, 127.15),
    (387.59, 77.40),
    (347.52, 28.06),
    (275.12, 2.37),
    (224.60, 0.40),
    (199.23, 0.00),
    (173.87, 0.40),
    (123.34, 2.37),
    (50.95, 28.06),
    (10.88, 77.40),
    (0.00, 127.15),
    (6.19, 176.80),
    (26.67, 227.21),
    (52.00, 277.86),
    (67.47, 330.06),
    (60.99, 381.92),
    (59.45, 431.09),
    (90.82, 480.07),
    (123.98, 497.03),
    (173.90, 504.43),
]

# Dimensions
J45_DIMENSIONS = {
    "width_mm": 398.5,
    "length_mm": 504.8,
    "width_inches": 15.69,
    "length_inches": 19.88,
    "lower_bout_width_mm": 398.5,  # Widest point
    "upper_bout_width_mm": 287.0,  # Approximate
    "waist_width_mm": 270.0,       # Approximate
}
