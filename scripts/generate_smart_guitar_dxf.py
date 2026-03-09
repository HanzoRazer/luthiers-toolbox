"""
Generate Smart Guitar v1 DXF from mockup analysis.

Creates an approximate body outline based on the visual analysis of the
Smart Guitar mockup images.

Author: The Production Shop
Date: 2026-03-06
"""

import ezdxf
from ezdxf import units
from pathlib import Path
import math


def create_smart_guitar_body():
    """
    Create Smart Guitar body outline.

    Dimensions based on visual analysis:
    - Body Length: 17.5"
    - Body Width (max): 14.5"
    - Lower Bout (V): 12"
    - Scale: 25.5"

    Coordinate system: Center at neck pocket center, Y+ toward bridge
    All dimensions in inches, converted to mm for DXF.
    """

    # Scale factor: inches to mm
    INCH_TO_MM = 25.4

    # Body dimensions in inches
    body_length = 17.5
    body_width = 14.5
    lower_bout_width = 12.0

    # Key reference points (inches, will convert to mm)
    # Origin at approximate center of body

    # Define the outline as a series of points
    # Starting from bottom center, going clockwise

    points_inches = [
        # Bottom V-point (center)
        (0, -8.75),

        # Lower right edge of V
        (5.5, -6.0),

        # Right lower bout curve control
        (6.5, -4.0),

        # Right side waist area
        (5.0, -1.0),

        # Right side upper curve
        (5.5, 1.5),

        # Upper right horn tip
        (7.25, 4.5),

        # Upper right horn inner
        (5.0, 5.5),

        # Neck pocket right
        (2.0, 6.5),

        # Neck pocket area (top of body)
        (0.75, 8.0),

        # Neck pocket left
        (-0.75, 8.0),

        # Upper left - start of upper void
        (-2.0, 6.5),

        # Upper void - inner top
        (-3.5, 5.5),

        # Upper void - inner curve
        (-4.5, 4.0),

        # Upper void - inner bottom
        (-3.5, 2.5),

        # Between voids - narrow section
        (-4.0, 1.0),

        # Lower void - inner top
        (-3.5, -0.5),

        # Lower void - inner curve
        (-5.0, -2.0),

        # Lower void - inner bottom left
        (-4.0, -4.0),

        # Lower void - bottom
        (-3.0, -5.0),

        # Left side of V - lower
        (-5.5, -6.0),

        # Back to bottom V-point
        (0, -8.75),
    ]

    # Convert to mm
    points_mm = [(x * INCH_TO_MM, y * INCH_TO_MM) for x, y in points_inches]

    return points_mm


def create_smart_guitar_dxf(output_path: Path):
    """Create the Smart Guitar DXF file."""

    # Create new DXF document
    doc = ezdxf.new('R2010')
    doc.units = units.MM

    # Get modelspace
    msp = doc.modelspace()

    # Create layers
    doc.layers.add("BODY_OUTLINE", color=7)  # White
    doc.layers.add("CENTERLINE", color=1)     # Red
    doc.layers.add("REFERENCE", color=3)      # Green
    doc.layers.add("ANNOTATIONS", color=5)    # Blue

    # Get body outline points
    body_points = create_smart_guitar_body()

    # Draw body outline as polyline
    msp.add_lwpolyline(
        body_points,
        close=True,
        dxfattribs={"layer": "BODY_OUTLINE", "lineweight": 50}
    )

    # Also draw as spline for smoother curves
    # Convert points for spline fitting
    try:
        from ezdxf.math import BSpline
        # Add a smooth spline version
        msp.add_spline(
            body_points,
            degree=3,
            dxfattribs={"layer": "BODY_OUTLINE", "color": 4}  # Cyan for spline
        )
    except Exception:
        pass  # Spline optional

    # Add centerline
    INCH_TO_MM = 25.4
    msp.add_line(
        (0, -10 * INCH_TO_MM),
        (0, 10 * INCH_TO_MM),
        dxfattribs={"layer": "CENTERLINE", "linetype": "CENTER"}
    )

    # Add reference dimensions
    # Body length
    msp.add_aligned_dim(
        p1=(-8 * INCH_TO_MM, -8.75 * INCH_TO_MM),
        p2=(-8 * INCH_TO_MM, 8 * INCH_TO_MM),
        distance=1 * INCH_TO_MM,
        dxfattribs={"layer": "ANNOTATIONS"}
    ).render()

    # Body width
    msp.add_aligned_dim(
        p1=(-7.25 * INCH_TO_MM, -10 * INCH_TO_MM),
        p2=(7.25 * INCH_TO_MM, -10 * INCH_TO_MM),
        distance=1 * INCH_TO_MM,
        dxfattribs={"layer": "ANNOTATIONS"}
    ).render()

    # Add title block text
    msp.add_text(
        "SMART GUITAR v1.0",
        dxfattribs={
            "layer": "ANNOTATIONS",
            "height": 10,
            "insert": (-150, -280)
        }
    )

    msp.add_text(
        "Body Outline - Preliminary",
        dxfattribs={
            "layer": "ANNOTATIONS",
            "height": 5,
            "insert": (-150, -295)
        }
    )

    msp.add_text(
        "Scale Length: 25.5\" | Body: 17.5\" x 14.5\"",
        dxfattribs={
            "layer": "ANNOTATIONS",
            "height": 4,
            "insert": (-150, -305)
        }
    )

    msp.add_text(
        "The Production Shop - 2026-03-06",
        dxfattribs={
            "layer": "ANNOTATIONS",
            "height": 3,
            "insert": (-150, -315)
        }
    )

    # Add pickup position markers (approximate)
    # Neck pickup
    neck_pu_y = 2.5 * INCH_TO_MM
    msp.add_circle(
        (0, neck_pu_y),
        radius=1.5 * INCH_TO_MM,
        dxfattribs={"layer": "REFERENCE"}
    )

    # Bridge pickup
    bridge_pu_y = -3.5 * INCH_TO_MM
    msp.add_circle(
        (0, bridge_pu_y),
        radius=1.5 * INCH_TO_MM,
        dxfattribs={"layer": "REFERENCE"}
    )

    # Bridge position marker
    bridge_y = -5.5 * INCH_TO_MM
    msp.add_line(
        (-2 * INCH_TO_MM, bridge_y),
        (2 * INCH_TO_MM, bridge_y),
        dxfattribs={"layer": "REFERENCE"}
    )

    # Save file
    doc.saveas(output_path)
    print(f"DXF saved: {output_path}")

    return output_path


def main():
    # Output paths
    output_dir = Path(r"C:\Users\thepr\Downloads\luthiers-toolbox\services\api\app\instrument_geometry\body\dxf\electric")
    output_dir.mkdir(parents=True, exist_ok=True)

    dxf_path = output_dir / "Smart-Guitar-v1_preliminary.dxf"

    create_smart_guitar_dxf(dxf_path)

    print("\nSmart Guitar DXF Generation Complete!")
    print(f"Output: {dxf_path}")
    print("\nNote: This is a preliminary outline based on visual analysis.")
    print("Refine with actual measurements when available.")


if __name__ == "__main__":
    main()
