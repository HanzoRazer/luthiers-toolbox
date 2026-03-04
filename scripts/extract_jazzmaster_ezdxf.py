#!/usr/bin/env python3
"""
Jazzmaster Body Extraction using ezdxf library

Extracts body outline from PDF using OpenAI Vision API,
then generates a proper R12-compatible DXF using ezdxf.

Real Jazzmaster dimensions: ~340mm wide x ~470mm tall
"""

import os
import sys
import base64
import json
from pathlib import Path

# Add the services/api/app to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "services" / "api" / "app"))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded .env from {env_path}")

from openai import OpenAI
import fitz  # PyMuPDF

# Import the system's ezdxf compat layer
try:
    from util.dxf_compat import create_document, add_polyline, get_version_info
    print("Using system dxf_compat module")
except ImportError:
    # Fallback to direct ezdxf if import fails
    import ezdxf
    def create_document(version='R12', setup=False):
        return ezdxf.new(version)
    def add_polyline(msp, points, layer='0', closed=False, version='R12'):
        # R12 uses LINE segments
        n = len(points)
        end = n if closed else n - 1
        for i in range(end):
            msp.add_line(points[i], points[(i + 1) % n], dxfattribs={'layer': layer})
    print("Using fallback ezdxf directly")


# Real-world Jazzmaster body dimensions (mm)
JAZZMASTER_WIDTH_MM = 340.0
JAZZMASTER_HEIGHT_MM = 470.0


def pdf_page_to_base64(pdf_path: str, page_num: int = 0, dpi: int = 200) -> str:
    """Convert PDF page to base64-encoded PNG."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    png_bytes = pix.tobytes("png")
    doc.close()
    return base64.b64encode(png_bytes).decode('utf-8')


def extract_outline_with_vision(image_base64: str) -> list:
    """Use OpenAI Vision to extract body outline coordinates."""
    client = OpenAI()

    prompt = """You are a CAD data annotation assistant creating training data for CNC routing systems.

TASK: Trace the outer body outline of this guitar body as a closed polygon.

REQUIREMENTS:
1. Return ONLY the outer perimeter/silhouette of the body shape
2. Start at the neck pocket (top center) and trace clockwise
3. Use normalized coordinates where:
   - X: 0.0 = left edge, 1.0 = right edge
   - Y: 0.0 = bottom, 1.0 = top
4. Provide 40-60 points for smooth curves
5. Ignore all internal features (pickups, controls, routing cavities)

OUTPUT FORMAT (JSON only, no other text):
{
  "points": [[x1, y1], [x2, y2], ...],
  "confidence": 0.0-1.0
}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{image_base64}",
                    "detail": "high"
                }}
            ]
        }],
        max_tokens=4000
    )

    content = response.choices[0].message.content.strip()

    # Extract JSON from response
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    return json.loads(content)


def normalize_to_mm(points: list, target_width: float, target_height: float) -> list:
    """
    Convert normalized [0,1] coordinates to millimeters.
    Centers the body at origin (0, 0).
    """
    mm_points = []
    for x_norm, y_norm in points:
        # Scale to target dimensions
        x_mm = x_norm * target_width
        y_mm = y_norm * target_height

        # Center at origin
        x_mm -= target_width / 2
        y_mm -= target_height / 2

        mm_points.append((x_mm, y_mm))

    return mm_points


def create_dxf_with_ezdxf(points: list, output_path: str, version: str = 'R12'):
    """
    Create DXF file using ezdxf library (the system's standard approach).

    Args:
        points: List of (x, y) tuples in mm
        output_path: Output DXF file path
        version: DXF version (R12 for maximum CAM compatibility)
    """
    # Create document using system's compat layer
    doc = create_document(version=version)
    msp = doc.modelspace()

    # Add the body outline as a closed polyline
    # For R12, this will be converted to LINE segments automatically
    add_polyline(msp, points, layer='BODY_OUTLINE', closed=True, version=version)

    # Save the file
    doc.saveas(output_path)

    # Get version info for reporting
    info = get_version_info(version)
    return info


def main():
    # Paths
    pdf_path = r"C:\Users\thepr\Downloads\ltb-express\Lutherier Project\Lutherier Project\Guitar Plans\Fender-Jazzmaster-Body.pdf"
    output_dir = Path(__file__).parent.parent / "services" / "api" / "app" / "instrument_geometry" / "body" / "dxf" / "electric"
    output_path = output_dir / "jazzmaster_body.dxf"

    print(f"Source PDF: {pdf_path}")
    print(f"Output DXF: {output_path}")
    print(f"Target dimensions: {JAZZMASTER_WIDTH_MM}mm x {JAZZMASTER_HEIGHT_MM}mm")
    print()

    # Step 1: Convert PDF to image
    print("Converting PDF to image...")
    image_b64 = pdf_page_to_base64(pdf_path)
    print(f"  Image size: {len(image_b64)} bytes (base64)")

    # Step 2: Extract outline with Vision API
    print("\nExtracting outline with GPT-4o Vision...")
    result = extract_outline_with_vision(image_b64)

    points_norm = result['points']
    confidence = result.get('confidence', 0.0)
    print(f"  Extracted {len(points_norm)} points")
    print(f"  Confidence: {confidence:.0%}")

    # Step 3: Convert to real-world mm coordinates
    print("\nConverting to millimeters...")
    points_mm = normalize_to_mm(points_norm, JAZZMASTER_WIDTH_MM, JAZZMASTER_HEIGHT_MM)

    # Calculate actual bounding box
    xs = [p[0] for p in points_mm]
    ys = [p[1] for p in points_mm]
    actual_width = max(xs) - min(xs)
    actual_height = max(ys) - min(ys)
    print(f"  Actual dimensions: {actual_width:.1f}mm x {actual_height:.1f}mm")

    # Step 4: Create DXF with ezdxf
    print(f"\nCreating DXF with ezdxf (R12 format)...")
    info = create_dxf_with_ezdxf(points_mm, str(output_path), version='R12')
    print(f"  Version: {info['version']} ({info['ac_code']})")
    print(f"  LWPOLYLINE support: {info['supports_lwpolyline']}")
    print(f"  Genesis format: {info['is_genesis']}")

    print(f"\nSaved: {output_path}")
    print(f"Points: {len(points_mm)}, Confidence: {confidence:.0%}")

    # Return data for catalog update
    return {
        'name': 'Fender Jazzmaster',
        'category': 'electric',
        'width_mm': round(actual_width, 1),
        'height_mm': round(actual_height, 1),
        'points': len(points_mm),
        'confidence': confidence
    }


if __name__ == "__main__":
    result = main()
    print(f"\nCatalog data: {json.dumps(result, indent=2)}")
