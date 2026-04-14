"""
Layer Builder for Dual-Pass Extraction
=======================================

Assigns entities from Pass A (structural) and Pass B (annotation)
to semantic layers for controlled export.

Layers:
- BODY: Primary instrument outline (largest central structural cluster)
- AUX_VIEWS: Secondary structural clusters (side views, sections)
- ANNOTATION: Text, dimensions, labels from Pass B
- TITLE_BLOCK: Dense annotation cluster near bottom/right
- PAGE_FRAME: Page border geometry (preserved, not deleted)

Phase 4: Simple, stable classification rules. No ML, no OCR.

Author: Production Shop
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ─── Layer Definitions ──────────────────────────────────────────────────────

class Layer(str, Enum):
    """Semantic layer for blueprint entities."""
    BODY = "BODY"
    AUX_VIEWS = "AUX_VIEWS"
    ANNOTATION = "ANNOTATION"
    TITLE_BLOCK = "TITLE_BLOCK"
    PAGE_FRAME = "PAGE_FRAME"


# Layer colors for overlay (BGR format)
LAYER_COLORS = {
    Layer.BODY: (0, 255, 0),        # Green
    Layer.AUX_VIEWS: (255, 0, 0),   # Blue
    Layer.ANNOTATION: (0, 165, 255), # Orange
    Layer.TITLE_BLOCK: (255, 0, 255), # Purple/Magenta
    Layer.PAGE_FRAME: (0, 0, 255),  # Red
}


# ─── Export Presets ─────────────────────────────────────────────────────────

class ExportPreset(str, Enum):
    """Export preset controlling which layers to include."""
    GEOMETRY_ONLY = "geometry_only"        # BODY only
    GEOMETRY_PLUS_AUX = "geometry_plus_aux"  # BODY + AUX_VIEWS
    REFERENCE_FULL = "reference_full"      # All layers


PRESET_LAYERS = {
    ExportPreset.GEOMETRY_ONLY: {Layer.BODY},
    ExportPreset.GEOMETRY_PLUS_AUX: {Layer.BODY, Layer.AUX_VIEWS},
    ExportPreset.REFERENCE_FULL: {Layer.BODY, Layer.AUX_VIEWS, Layer.ANNOTATION,
                                   Layer.TITLE_BLOCK, Layer.PAGE_FRAME},
}


# ─── Data Models ────────────────────────────────────────────────────────────

@dataclass
class LayeredEntity:
    """Single entity with layer assignment."""
    contour: np.ndarray
    layer: Layer
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    area: float
    is_closed: bool = True


@dataclass
class LayeredEntities:
    """Entities organized by layer."""
    body: List[LayeredEntity] = field(default_factory=list)
    aux_views: List[LayeredEntity] = field(default_factory=list)
    annotation: List[LayeredEntity] = field(default_factory=list)
    title_block: List[LayeredEntity] = field(default_factory=list)
    page_frame: List[LayeredEntity] = field(default_factory=list)

    # Metadata
    image_size: Tuple[int, int] = (0, 0)
    mm_per_px: float = 0.0

    def get_layer(self, layer: Layer) -> List[LayeredEntity]:
        """Get entities for a specific layer."""
        return {
            Layer.BODY: self.body,
            Layer.AUX_VIEWS: self.aux_views,
            Layer.ANNOTATION: self.annotation,
            Layer.TITLE_BLOCK: self.title_block,
            Layer.PAGE_FRAME: self.page_frame,
        }[layer]

    def get_contours_for_preset(self, preset: ExportPreset) -> List[np.ndarray]:
        """Get all contours included in an export preset."""
        layers = PRESET_LAYERS[preset]
        contours = []
        for layer in layers:
            contours.extend([e.contour for e in self.get_layer(layer)])
        return contours

    def get_entities_for_preset(self, preset: ExportPreset) -> List[LayeredEntity]:
        """Get all entities included in an export preset."""
        layers = PRESET_LAYERS[preset]
        entities = []
        for layer in layers:
            entities.extend(self.get_layer(layer))
        return entities

    def counts(self) -> Dict[str, int]:
        """Return entity counts by layer."""
        return {
            "body": len(self.body),
            "aux_views": len(self.aux_views),
            "annotation": len(self.annotation),
            "title_block": len(self.title_block),
            "page_frame": len(self.page_frame),
            "total": (len(self.body) + len(self.aux_views) +
                     len(self.annotation) + len(self.title_block) +
                     len(self.page_frame)),
        }


# ─── Acceptance Grading ────────────────────────────────────────────────────

class AcceptanceGrade(str, Enum):
    """Grade indicating quality level of layered extraction."""
    STARTER = "starter"              # Minimal usable output
    USABLE = "usable"                # Good for reference work
    PRODUCTION_READY = "production_ready"  # Ready for CAM/fabrication


@dataclass
class LayeredAcceptance:
    """Result of evaluating layered extraction quality."""
    ok: bool                         # True if extraction is usable
    grade: AcceptanceGrade           # Quality grade
    reasons: List[str] = field(default_factory=list)  # Explanation
    body_count: int = 0
    body_area_ratio: float = 0.0     # BODY area / total structural area
    page_frame_dominance: float = 0.0  # PAGE_FRAME area / total area


def evaluate_layered_acceptance(
    entities: LayeredEntities,
) -> LayeredAcceptance:
    """
    Evaluate whether layered extraction produced usable output.

    Criteria:
    - Usable BODY system present (>= 1 contour with reasonable area)
    - BODY not trivial compared to useful geometry (BODY + AUX_VIEWS)
    - Page frames excluded from useful structural calculation (they're borders)

    Grades:
    - PRODUCTION_READY: BODY >= 10 contours, BODY area > 40% of useful
    - USABLE: BODY >= 3 contours, BODY area > 20% of useful
    - STARTER: BODY >= 1 contour with any meaningful area

    Returns:
        LayeredAcceptance with grade and explanation
    """
    counts = entities.counts()
    reasons = []

    # Calculate areas
    body_area = sum(e.area for e in entities.body)
    aux_area = sum(e.area for e in entities.aux_views)
    frame_area = sum(e.area for e in entities.page_frame)

    # Useful structural area excludes PAGE_FRAME (which are just borders)
    # PAGE_FRAME contours have large enclosed areas but are not actual geometry
    useful_area = body_area + aux_area
    total_structural = useful_area + frame_area

    # Body ratio against useful structural area (not including page frames)
    body_area_ratio = body_area / useful_area if useful_area > 0 else 0.0
    # Frame dominance as info metric (not used for rejection)
    frame_dominance = frame_area / total_structural if total_structural > 0 else 0.0

    # Check for usable BODY system
    if counts["body"] == 0:
        reasons.append("No BODY contours found")
        return LayeredAcceptance(
            ok=False,
            grade=AcceptanceGrade.STARTER,
            reasons=reasons,
            body_count=0,
            body_area_ratio=0.0,
            page_frame_dominance=frame_dominance,
        )

    # Check if BODY is trivially small compared to useful area
    if useful_area > 0 and body_area_ratio < 0.05 and counts["body"] < 3:
        reasons.append(f"BODY system too small: {counts['body']} contours, {body_area_ratio:.0%} of useful area")
        return LayeredAcceptance(
            ok=False,
            grade=AcceptanceGrade.STARTER,
            reasons=reasons,
            body_count=counts["body"],
            body_area_ratio=body_area_ratio,
            page_frame_dominance=frame_dominance,
        )

    # Grade based on BODY richness relative to useful structural area
    if counts["body"] >= 10 and body_area_ratio > 0.40:
        grade = AcceptanceGrade.PRODUCTION_READY
        reasons.append(f"BODY system: {counts['body']} contours, {body_area_ratio:.0%} of useful area")
    elif counts["body"] >= 3 and body_area_ratio > 0.20:
        grade = AcceptanceGrade.USABLE
        reasons.append(f"BODY system: {counts['body']} contours, {body_area_ratio:.0%} of useful area")
    else:
        grade = AcceptanceGrade.STARTER
        reasons.append(f"Minimal BODY system: {counts['body']} contours, {body_area_ratio:.0%} of useful area")

    # All grades with adequate BODY are considered ok
    return LayeredAcceptance(
        ok=True,
        grade=grade,
        reasons=reasons,
        body_count=counts["body"],
        body_area_ratio=body_area_ratio,
        page_frame_dominance=frame_dominance,
    )


# ─── Classification Helpers ─────────────────────────────────────────────────

def _is_page_frame(
    bbox: Tuple[int, int, int, int],
    image_size: Tuple[int, int],
    contour_area: Optional[float] = None,
    margin_ratio: float = 0.02,
) -> bool:
    """
    Check if contour is a page frame/border.

    Known-good heuristic from earlier successful work:
    - Touches >= 3 edges, OR
    - Touches >= 2 edges AND area_ratio > 0.70, OR
    - Bbox spans >95% width AND >95% height

    Do NOT classify by sheer size alone - that misclassifies
    the main structural region on dense blueprints.
    """
    x, y, w, h = bbox
    img_w, img_h = image_size

    margin_x = img_w * margin_ratio
    margin_y = img_h * margin_ratio

    # Count edge contacts
    near_left = x < margin_x
    near_right = (x + w) > (img_w - margin_x)
    near_top = y < margin_y
    near_bottom = (y + h) > (img_h - margin_y)
    edge_contacts = sum([near_left, near_right, near_top, near_bottom])

    # Calculate area ratio if contour_area provided
    image_area = img_w * img_h
    area_ratio = contour_area / image_area if contour_area and image_area > 0 else 0.0

    # Bbox coverage ratios
    bbox_width_ratio = w / img_w
    bbox_height_ratio = h / img_h

    # Rule 1: Touches 3+ edges
    if edge_contacts >= 3:
        return True

    # Rule 2: Touches 2+ edges AND area > 70%
    if edge_contacts >= 2 and area_ratio > 0.70:
        return True

    # Rule 3: Bbox spans >95% in both dimensions (extra confirmation)
    if bbox_width_ratio > 0.95 and bbox_height_ratio > 0.95:
        return True

    return False


def _is_title_block_region(
    bbox: Tuple[int, int, int, int],
    image_size: Tuple[int, int],
) -> bool:
    """
    Check if bbox is in typical title block region (bottom-right quadrant).
    """
    x, y, w, h = bbox
    img_w, img_h = image_size

    center_x = x + w / 2
    center_y = y + h / 2

    # Title block typically in bottom 30% and right 40%
    in_bottom = center_y > (img_h * 0.7)
    in_right = center_x > (img_w * 0.6)

    return in_bottom and in_right


def _is_body_support(
    data: Dict[str, Any],
    body_region: Tuple[int, int, int, int],
    image_size: Tuple[int, int],
    body_core_area: float,
    min_overlap_ratio: float = 0.5,
) -> bool:
    """
    Check if a contour should be promoted from AUX_VIEWS to BODY.

    BODY_SUPPORT criteria:
    - Significantly overlaps with or is inside the BODY region
    - Not a detached secondary view (check position relative to body)
    - Structurally plausible for same instrument elevation

    Args:
        data: Contour data dict with bbox, area, center, centrality
        body_region: Expanded BODY bbox (x, y, w, h)
        image_size: (width, height) of image
        body_core_area: Area of the original body core (not expanded region)
        min_overlap_ratio: Minimum overlap with body region to qualify

    Returns:
        True if contour should be promoted to BODY
    """
    cx, cy, cw, ch = data["bbox"]
    bx, by, bw, bh = body_region
    img_w, img_h = image_size

    # Calculate overlap between contour bbox and body region
    overlap_x = max(0, min(cx + cw, bx + bw) - max(cx, bx))
    overlap_y = max(0, min(cy + ch, by + bh) - max(cy, by))
    overlap_area = overlap_x * overlap_y

    contour_area_bbox = cw * ch
    if contour_area_bbox <= 0:
        return False

    overlap_ratio = overlap_area / contour_area_bbox

    # Must have significant overlap with body region
    if overlap_ratio < min_overlap_ratio:
        return False

    # Reject if in title block region (bottom-right)
    center_x, center_y = data["center"]
    if center_y > (img_h * 0.75) and center_x > (img_w * 0.65):
        return False

    # Reject very small contours (likely noise or annotation)
    # Use body_core_area (original, not expanded) for consistent threshold
    if data["area"] < body_core_area * 0.001:
        return False

    # Accept: overlaps body region, not in title block, reasonable size
    return True


def _classify_structural_cluster(
    contour: np.ndarray,
    bbox: Tuple[int, int, int, int],
    area: float,
    image_size: Tuple[int, int],
    is_largest: bool,
    centrality_score: float,
) -> Layer:
    """
    Classify a structural contour from Pass A.

    BODY: Largest, central, curved
    AUX_VIEWS: Other structural clusters
    PAGE_FRAME: Edge-hugging rectangles
    """
    # Check for page frame first (pass area for 70% rule)
    if _is_page_frame(bbox, image_size, contour_area=area):
        return Layer.PAGE_FRAME

    # Largest central contour is body
    if is_largest and centrality_score > 0.3:
        return Layer.BODY

    # Everything else from Pass A is aux views
    return Layer.AUX_VIEWS


def _classify_annotation(
    bbox: Tuple[int, int, int, int],
    area: float,
    image_size: Tuple[int, int],
    annotation_count_in_region: int,
) -> Layer:
    """
    Classify an annotation entity from Pass B.

    TITLE_BLOCK: Dense cluster in bottom-right
    ANNOTATION: Everything else from Pass B
    """
    if _is_title_block_region(bbox, image_size) and annotation_count_in_region > 10:
        return Layer.TITLE_BLOCK

    return Layer.ANNOTATION


# ─── Main Builder ───────────────────────────────────────────────────────────

def build_layers(
    structural_contours: List[np.ndarray],
    annotation_contours: List[np.ndarray],
    image_size: Tuple[int, int],
    mm_per_px: float = 1.0,
) -> LayeredEntities:
    """
    Build layered entity structure from Pass A and Pass B contours.

    Args:
        structural_contours: Contours from Pass A (body, views)
        annotation_contours: Contours from Pass B (text, dimensions)
        image_size: (width, height) in pixels
        mm_per_px: Scale factor for mm conversion

    Returns:
        LayeredEntities with classified contours
    """
    result = LayeredEntities(image_size=image_size, mm_per_px=mm_per_px)

    img_w, img_h = image_size
    img_center = (img_w / 2, img_h / 2)

    # ─── Process structural contours (Pass A) ───────────────────────────

    if structural_contours:
        # Calculate areas, centrality, and check page frame for each
        structural_data = []
        for contour in structural_contours:
            area = cv2.contourArea(contour)
            bbox = cv2.boundingRect(contour)
            x, y, w, h = bbox
            center = (x + w/2, y + h/2)

            # Centrality: distance from image center (normalized)
            dist = np.sqrt((center[0] - img_center[0])**2 +
                          (center[1] - img_center[1])**2)
            max_dist = np.sqrt(img_center[0]**2 + img_center[1]**2)
            centrality = 1.0 - (dist / max_dist) if max_dist > 0 else 0.0

            # Pre-check page frame status
            is_frame = _is_page_frame(bbox, image_size, contour_area=area)

            structural_data.append({
                "contour": contour,
                "area": area,
                "bbox": bbox,
                "center": center,
                "centrality": centrality,
                "is_frame": is_frame,
            })

        # ─── BODY SYSTEM: Find core + support contours ───────────────────

        # Step 1: Find BODY_CORE (largest non-frame central contour)
        non_frame_data = [d for d in structural_data if not d["is_frame"]]
        body_core = None
        body_core_bbox = None

        if non_frame_data:
            central_non_frames = [d for d in non_frame_data if d["centrality"] > 0.3]
            if central_non_frames:
                body_core = max(central_non_frames, key=lambda d: d["area"])
            else:
                body_core = max(non_frame_data, key=lambda d: d["area"])

            if body_core:
                body_core_bbox = body_core["bbox"]

        # Step 2: Define BODY region with margin for BODY_SUPPORT detection
        # Using 25% margin to capture same-view structural contours
        body_region = None
        body_core_area = 0.0
        if body_core_bbox:
            bx, by, bw, bh = body_core_bbox
            body_core_area = bw * bh  # Original core area for size threshold
            margin_x = int(bw * 0.25)
            margin_y = int(bh * 0.25)
            body_region = (
                max(0, bx - margin_x),
                max(0, by - margin_y),
                bw + 2 * margin_x,
                bh + 2 * margin_y,
            )

        # Step 3: Classify each structural contour
        for data in structural_data:
            if data["is_frame"]:
                layer = Layer.PAGE_FRAME
            elif body_core and data is body_core:
                layer = Layer.BODY
            elif body_region and _is_body_support(data, body_region, image_size, body_core_area):
                layer = Layer.BODY
            else:
                layer = Layer.AUX_VIEWS

            entity = LayeredEntity(
                contour=data["contour"],
                layer=layer,
                bbox=data["bbox"],
                area=data["area"],
                is_closed=True,
            )

            result.get_layer(layer).append(entity)

    # ─── Process annotation contours (Pass B) ───────────────────────────

    if annotation_contours:
        # First pass: count annotations in title block region
        title_region_count = 0
        for contour in annotation_contours:
            bbox = cv2.boundingRect(contour)
            if _is_title_block_region(bbox, image_size):
                title_region_count += 1

        # Second pass: classify
        for contour in annotation_contours:
            area = cv2.contourArea(contour)
            bbox = cv2.boundingRect(contour)

            layer = _classify_annotation(
                bbox=bbox,
                area=area,
                image_size=image_size,
                annotation_count_in_region=title_region_count,
            )

            entity = LayeredEntity(
                contour=contour,
                layer=layer,
                bbox=bbox,
                area=area,
                is_closed=True,
            )

            result.get_layer(layer).append(entity)

    # Log summary
    counts = result.counts()
    logger.info(
        f"Layer assignment complete: "
        f"BODY={counts['body']}, AUX_VIEWS={counts['aux_views']}, "
        f"ANNOTATION={counts['annotation']}, TITLE_BLOCK={counts['title_block']}, "
        f"PAGE_FRAME={counts['page_frame']}"
    )

    return result
