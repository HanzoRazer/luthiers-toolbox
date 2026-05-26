"""Text reinsertion module for faithful blueprint rendering.

Extracts text from blueprint images using EasyOCR, preserving:
- Text content
- Position (insertion point)
- Rotation (computed from 4-point polygon)
- Height (estimated from bounding box)

Then reinserts as DXF TEXT entities on a separate TEXT layer.

Sprint 3: Faithful rendering architecture.
Author: Production Shop
Date: 2026-04-26
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional, Sequence, Any, TYPE_CHECKING

from app.util.dxf_lifecycle_guard import (
    DxfLifecycleContext,
    assert_dxf_lifecycle_context,
)

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)

try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except ImportError:
    _EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not available - text reinsertion disabled")


@dataclass
class ExtractedText:
    """Text element extracted from blueprint with full geometric info."""
    content: str
    confidence: float
    insert_px: Tuple[float, float]  # Bottom-left insertion point (pixels)
    height_px: float  # Estimated text height (pixels)
    rotation_deg: float  # Counter-clockwise rotation (degrees)
    bbox_polygon: List[Tuple[float, float]]  # Original 4-point polygon


def compute_rotation_from_polygon(polygon: Sequence[Tuple[float, float]]) -> float:
    """Compute rotation angle from EasyOCR's 4-point polygon.

    EasyOCR returns corners as: [top-left, top-right, bottom-right, bottom-left]
    Rotation is computed from the baseline (bottom-left to bottom-right).

    Args:
        polygon: 4 corner points [(x,y), ...]

    Returns:
        Rotation angle in degrees, counter-clockwise from horizontal
    """
    if len(polygon) < 4:
        return 0.0

    # Bottom edge: bottom-left to bottom-right
    bl = polygon[3]
    br = polygon[2]

    dx = br[0] - bl[0]
    dy = br[1] - bl[1]

    # atan2 gives angle from positive X axis, counter-clockwise
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)

    # Small angles are likely noise
    if abs(angle_deg) < 0.5:
        return 0.0

    return angle_deg


def estimate_height_from_polygon(polygon: Sequence[Tuple[float, float]]) -> float:
    """Estimate text height from EasyOCR's 4-point polygon.

    Computes average of left and right edge heights to handle rotation.

    Args:
        polygon: 4 corner points [(x,y), ...]

    Returns:
        Estimated text height in pixels
    """
    if len(polygon) < 4:
        return 20.0  # fallback

    tl, tr, br, bl = polygon[:4]

    # Left edge height
    left_h = math.sqrt((tl[0] - bl[0])**2 + (tl[1] - bl[1])**2)
    # Right edge height
    right_h = math.sqrt((tr[0] - br[0])**2 + (tr[1] - br[1])**2)

    return (left_h + right_h) / 2


def get_insertion_point(polygon: Sequence[Tuple[float, float]]) -> Tuple[float, float]:
    """Get text insertion point (bottom-left corner).

    DXF TEXT entities use bottom-left as the insertion point.

    Args:
        polygon: 4 corner points [(x,y), ...]

    Returns:
        (x, y) insertion point in pixels
    """
    if len(polygon) < 4:
        return (0.0, 0.0)

    # Bottom-left corner
    bl = polygon[3]
    return (float(bl[0]), float(bl[1]))


_reader: Optional[easyocr.Reader] = None


def _get_reader() -> Optional[easyocr.Reader]:
    """Lazy-load EasyOCR reader (GPU disabled for compatibility)."""
    global _reader
    if not _EASYOCR_AVAILABLE:
        return None
    if _reader is None:
        logger.info("Initializing EasyOCR reader...")
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader


def extract_text_for_reinsertion(
    image: Any,  # np.ndarray - BGR image
    min_confidence: float = 0.3,
) -> List[ExtractedText]:
    """Extract all text from image with geometry for reinsertion.

    Args:
        image: BGR image (OpenCV format)
        min_confidence: Minimum OCR confidence (0-1)

    Returns:
        List of ExtractedText objects with position, rotation, height
    """
    reader = _get_reader()
    if reader is None:
        logger.warning("EasyOCR unavailable, returning empty text list")
        return []

    # Run OCR
    results = reader.readtext(image)
    logger.info(f"OCR found {len(results)} text regions")

    extracted = []
    for bbox, text, confidence in results:
        if confidence < min_confidence:
            continue

        # Convert bbox to list of tuples
        polygon = [(float(p[0]), float(p[1])) for p in bbox]

        extracted.append(ExtractedText(
            content=text,
            confidence=float(confidence),
            insert_px=get_insertion_point(polygon),
            height_px=estimate_height_from_polygon(polygon),
            rotation_deg=compute_rotation_from_polygon(polygon),
            bbox_polygon=polygon,
        ))

    logger.info(f"Extracted {len(extracted)} text elements (conf >= {min_confidence})")
    return extracted


def convert_text_to_dxf_coords(
    texts: List[ExtractedText],
    image_height_px: float,
    mm_per_px: float,
) -> List[dict]:
    """Convert extracted text from pixel coords to DXF mm coords.

    Applies:
    - Y-flip (image Y=0 at top, DXF Y=0 at bottom)
    - Scale conversion (pixels to mm)

    Args:
        texts: List of ExtractedText from OCR
        image_height_px: Image height in pixels (for Y-flip)
        mm_per_px: Scale factor (mm per pixel)

    Returns:
        List of dicts with: text, insert_mm, height_mm, rotation_deg
    """
    result = []
    for t in texts:
        # Y-flip: DXF y = image_height - image_y
        x_mm = t.insert_px[0] * mm_per_px
        y_mm = (image_height_px - t.insert_px[1]) * mm_per_px
        h_mm = t.height_px * mm_per_px

        result.append({
            "text": t.content,
            "insert_mm": (x_mm, y_mm),
            "height_mm": h_mm,
            "rotation_deg": t.rotation_deg,
            "confidence": t.confidence,
        })

    return result


def add_text_layer_to_dxf(
    writer,  # DxfWriter
    texts: List[dict],
    layer_name: str = "TEXT",
    layer_color: int = 2,  # Yellow
) -> int:
    """Add extracted text to DXF as TEXT entities on dedicated layer.

    Args:
        writer: DxfWriter instance
        texts: List from convert_text_to_dxf_coords()
        layer_name: Layer name for text (default "TEXT")
        layer_color: DXF color code (default 2=yellow)

    Returns:
        Number of text entities added
    """
    from app.cam.dxf_writer import LayerDef

    # Ensure layer exists
    try:
        writer.add_layer(LayerDef(layer_name, layer_color))
    except ValueError:
        pass  # Layer already exists

    count = 0
    for t in texts:
        writer.add_text(
            layer=layer_name,
            text=t["text"],
            insert=t["insert_mm"],
            height=t["height_mm"],
            rotation=t["rotation_deg"],
        )
        count += 1

    logger.info(f"Added {count} text entities to layer '{layer_name}'")
    return count


def append_text_to_existing_dxf(
    dxf_path: str,
    image: Any,  # np.ndarray - BGR image for OCR
    image_height_px: float,
    mm_per_px: float,
    min_confidence: float = 0.3,
    layer_name: str = "TEXT",
    layer_color: int = 2,
) -> int:
    """Extract text from image and append to existing DXF file.

    This is the main integration point for the faithful rendering pipeline.
    Loads an existing DXF, extracts text from the source image, converts
    coordinates, and adds TEXT entities on a dedicated layer.

    Args:
        dxf_path: Path to existing DXF file (will be modified in place)
        image: BGR image (OpenCV format) for OCR
        image_height_px: Image height in pixels (for Y-flip)
        mm_per_px: Scale factor (mm per pixel)
        min_confidence: Minimum OCR confidence (0-1)
        layer_name: Layer name for text entities
        layer_color: DXF color code (default 2=yellow)

    Returns:
        Number of text entities added
    """
    import ezdxf

    # Extract text from image
    texts = extract_text_for_reinsertion(image, min_confidence)
    if not texts:
        logger.info("No text extracted, skipping text reinsertion")
        return 0

    # Convert to DXF coordinates
    dxf_texts = convert_text_to_dxf_coords(texts, image_height_px, mm_per_px)

    # Load existing DXF
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    # Create TEXT layer
    if layer_name not in doc.layers:
        doc.layers.add(layer_name, dxfattribs={"color": layer_color})

    # Add text entities
    count = 0
    for t in dxf_texts:
        msp.add_text(
            t["text"],
            dxfattribs={
                "layer": layer_name,
                "height": round(t["height_mm"], 3),
                "insert": (round(t["insert_mm"][0], 3), round(t["insert_mm"][1], 3)),
                "rotation": round(t["rotation_deg"], 3),
            }
        )
        count += 1

    # Save back to file
    dxf_version = getattr(doc, "dxfversion", "R2010")
    assert_dxf_lifecycle_context(
        DxfLifecycleContext(
            source_module=__name__,
            export_type="dxf-read-modify-save",
            dxf_version=dxf_version,
            lifecycle_status="DIRECT_SAVE_GAP",
            runtime_callable="runtime_service",
            authority_context="pipeline_stage",
            provenance_status="NO",
        )
    )
    doc.saveas(dxf_path)
    logger.info(f"Appended {count} text entities to {dxf_path}")
    return count
