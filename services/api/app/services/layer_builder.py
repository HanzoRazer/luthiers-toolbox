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
    BODY = "BODY_OUTLINE"
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


# ─── BODY Gap Joining ──────────────────────────────────────────────────────

@dataclass
class GapJoinResult:
    """Result of BODY gap joining pass."""
    joins_attempted: int = 0
    joins_applied: int = 0
    max_gap_mm: float = 0.0
    max_angle_deg: float = 0.0
    joined_segments: List[Tuple[Tuple[float, float], Tuple[float, float]]] = field(
        default_factory=list
    )  # For debug overlay: list of (start_pt, end_pt) in pixels


def _get_endpoint_tangent(
    contour: np.ndarray,
    endpoint_idx: int,
    num_samples: int = 3,
) -> np.ndarray:
    """
    Get tangent direction at a contour endpoint.

    Args:
        contour: Contour points array
        endpoint_idx: 0 for start, -1 for end
        num_samples: Number of points to use for tangent estimation

    Returns:
        Normalized tangent vector pointing outward from contour
    """
    points = contour.reshape(-1, 2)
    n = len(points)

    if n < 2:
        return np.array([1.0, 0.0])

    if endpoint_idx == 0:
        # Start endpoint - tangent points backward (outward)
        end_idx = min(num_samples, n)
        segment = points[:end_idx]
        if len(segment) >= 2:
            tangent = segment[0] - segment[-1]
        else:
            tangent = np.array([1.0, 0.0])
    else:
        # End endpoint - tangent points forward (outward)
        start_idx = max(0, n - num_samples)
        segment = points[start_idx:]
        if len(segment) >= 2:
            tangent = segment[-1] - segment[0]
        else:
            tangent = np.array([1.0, 0.0])

    norm = np.linalg.norm(tangent)
    if norm > 0:
        tangent = tangent / norm

    return tangent


def _get_local_median_segment_length(
    contour: np.ndarray,
    endpoint_idx: int,
    num_segments: int = 5,
) -> float:
    """
    Get median segment length near a contour endpoint.

    Used to reject joins where gap is disproportionate to local scale.
    """
    points = contour.reshape(-1, 2)
    n = len(points)

    if n < 2:
        return float('inf')

    if endpoint_idx == 0:
        # Near start
        end_idx = min(num_segments + 1, n)
        segment_points = points[:end_idx]
    else:
        # Near end
        start_idx = max(0, n - num_segments - 1)
        segment_points = points[start_idx:]

    if len(segment_points) < 2:
        return float('inf')

    # Calculate segment lengths
    lengths = []
    for i in range(len(segment_points) - 1):
        length = np.linalg.norm(segment_points[i + 1] - segment_points[i])
        lengths.append(length)

    if not lengths:
        return float('inf')

    return float(np.median(lengths))


def _is_contour_open(contour: np.ndarray, threshold_px: float = 5.0) -> bool:
    """
    Check if contour is open (endpoints not connected).

    Args:
        contour: Contour points array
        threshold_px: Max distance between endpoints to consider closed

    Returns:
        True if contour is open
    """
    points = contour.reshape(-1, 2)
    if len(points) < 2:
        return False

    start = points[0]
    end = points[-1]
    dist = np.linalg.norm(end - start)

    return dist > threshold_px


def join_body_gaps(
    entities: LayeredEntities,
    max_gap_mm: float = 4.0,
    max_angle_deg: float = 25.0,
    scale_factor_limit: float = 4.0,
) -> Tuple[LayeredEntities, GapJoinResult]:
    """
    Conservative gap joining for BODY layer only.

    Joins contour endpoints that are:
    - Close (within max_gap_mm)
    - Directionally compatible (tangent alignment within max_angle_deg)
    - Not disproportionate to local geometry (gap < 3x local median segment)

    Args:
        entities: LayeredEntities from build_layers()
        max_gap_mm: Maximum gap distance in mm (default 2.0)
        max_angle_deg: Maximum tangent angle difference in degrees (default 25.0)
        scale_factor_limit: Reject if gap > this * local median segment (default 4.0)

    Returns:
        (updated_entities, gap_join_result)
    """
    result = GapJoinResult(
        max_gap_mm=max_gap_mm,
        max_angle_deg=max_angle_deg,
    )

    if not entities.body:
        logger.info("Gap join: No BODY contours to process")
        return entities, result

    mm_per_px = entities.mm_per_px
    if mm_per_px <= 0:
        logger.warning("Gap join: Invalid mm_per_px, skipping")
        return entities, result

    max_gap_px = max_gap_mm / mm_per_px
    max_angle_rad = np.deg2rad(max_angle_deg)

    # Extract open contours from BODY layer
    open_entities = []
    closed_entities = []

    for entity in entities.body:
        if _is_contour_open(entity.contour):
            open_entities.append(entity)
        else:
            closed_entities.append(entity)

    logger.info(f"Gap join: {len(open_entities)} open, {len(closed_entities)} closed BODY contours")

    if len(open_entities) < 2:
        # Nothing to join
        return entities, result

    # Build endpoint list: (entity_idx, endpoint_idx, point, tangent, median_seg_len)
    endpoints = []
    for i, entity in enumerate(open_entities):
        points = entity.contour.reshape(-1, 2)

        # Start endpoint
        start_pt = points[0].astype(float)
        start_tangent = _get_endpoint_tangent(entity.contour, 0)
        start_median = _get_local_median_segment_length(entity.contour, 0)
        endpoints.append((i, 0, start_pt, start_tangent, start_median))

        # End endpoint
        end_pt = points[-1].astype(float)
        end_tangent = _get_endpoint_tangent(entity.contour, -1)
        end_median = _get_local_median_segment_length(entity.contour, -1)
        endpoints.append((i, -1, end_pt, end_tangent, end_median))

    # Track which endpoints have been used
    used_endpoints = set()  # (entity_idx, endpoint_idx)

    # Track joins to apply: list of (entity_i, endpoint_i, entity_j, endpoint_j)
    joins_to_apply = []

    # Find valid join candidates
    for i, (ent_i, ep_i, pt_i, tan_i, med_i) in enumerate(endpoints):
        if (ent_i, ep_i) in used_endpoints:
            continue

        best_match = None
        best_dist = float('inf')

        for j, (ent_j, ep_j, pt_j, tan_j, med_j) in enumerate(endpoints):
            if i == j:
                continue
            if ent_i == ent_j:
                # Same contour - would close it, not join to another
                continue
            if (ent_j, ep_j) in used_endpoints:
                continue

            # Check distance
            dist = np.linalg.norm(pt_j - pt_i)
            if dist > max_gap_px:
                continue

            result.joins_attempted += 1

            # Check tangent alignment
            # Tangents should point toward each other (roughly opposite)
            # So dot product of (tan_i) and (-tan_j) should be positive and close to 1
            alignment = np.dot(tan_i, -tan_j)
            angle = np.arccos(np.clip(alignment, -1.0, 1.0))

            if angle > max_angle_rad:
                continue

            # Check scale factor limit
            gap_mm = dist * mm_per_px
            local_median_mm = min(med_i, med_j) * mm_per_px
            if local_median_mm > 0 and gap_mm > scale_factor_limit * local_median_mm:
                continue

            # Valid candidate
            if dist < best_dist:
                best_dist = dist
                best_match = (ent_j, ep_j, pt_j)

        if best_match is not None:
            ent_j, ep_j, pt_j = best_match
            joins_to_apply.append((ent_i, ep_i, ent_j, ep_j))
            used_endpoints.add((ent_i, ep_i))
            used_endpoints.add((ent_j, ep_j))

            # Record for debug overlay
            result.joined_segments.append((tuple(pt_i), tuple(pt_j)))

    logger.info(f"Gap join: {len(joins_to_apply)} joins to apply")

    if not joins_to_apply:
        return entities, result

    # Apply joins by merging contours
    # Build union-find to track merged groups
    parent = list(range(len(open_entities)))

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for ent_i, ep_i, ent_j, ep_j in joins_to_apply:
        union(ent_i, ent_j)
        result.joins_applied += 1

    # Group entities by their root
    groups: Dict[int, List[int]] = {}
    for i in range(len(open_entities)):
        root = find(i)
        if root not in groups:
            groups[root] = []
        groups[root].append(i)

    # Build merged contours for each group
    merged_entities = []

    for root, members in groups.items():
        if len(members) == 1:
            # No merge, keep original
            merged_entities.append(open_entities[members[0]])
        else:
            # Merge contours in this group
            # Simple approach: concatenate points in order of joins
            # For now, just concatenate all points (can be refined)
            all_points = []
            for idx in members:
                pts = open_entities[idx].contour.reshape(-1, 2)
                all_points.extend(pts.tolist())

            if all_points:
                merged_contour = np.array(all_points, dtype=np.int32).reshape(-1, 1, 2)
                merged_bbox = cv2.boundingRect(merged_contour)
                merged_area = cv2.contourArea(merged_contour)

                merged_entity = LayeredEntity(
                    contour=merged_contour,
                    layer=Layer.BODY,
                    bbox=merged_bbox,
                    area=merged_area,
                    is_closed=not _is_contour_open(merged_contour),
                )
                merged_entities.append(merged_entity)

    # Build new entities with merged BODY layer
    new_entities = LayeredEntities(
        body=merged_entities + closed_entities,
        aux_views=entities.aux_views,
        annotation=entities.annotation,
        title_block=entities.title_block,
        page_frame=entities.page_frame,
        image_size=entities.image_size,
        mm_per_px=entities.mm_per_px,
    )

    logger.info(
        f"Gap join complete: {result.joins_applied} joins applied, "
        f"BODY contours {len(entities.body)} -> {len(new_entities.body)}"
    )

    return new_entities, result


# ─── Scale Correction ───────────────────────────────────────────────────────


def apply_scale_correction(
    entities: LayeredEntities,
    spec_name: str,
) -> Tuple[LayeredEntities, float]:
    """
    Apply scale correction to BODY_OUTLINE layer based on instrument spec.

    Computes scale factor from spec height vs extracted body bounding box height,
    then applies uniformly to BODY_OUTLINE coordinates only.

    Uniform scaling preserves aspect ratio — the shape came from a real instrument,
    so both dimensions should scale together. If source aspect ratio differs from
    spec by >10%, a warning is logged (source may be cropped or angled).

    Args:
        entities: LayeredEntities from build_layers()
        spec_name: Instrument spec name (e.g., "benedetto_17", "dreadnought")

    Returns:
        (corrected_entities, scale_factor)
    """
    import json
    from pathlib import Path

    # Load spec from body_dimension_reference.json
    spec_path = Path(__file__).parent.parent.parent.parent / "photo-vectorizer" / "body_dimension_reference.json"
    if not spec_path.exists():
        # Try alternate path
        spec_path = Path(__file__).parent.parent.parent.parent.parent / "photo-vectorizer" / "body_dimension_reference.json"

    if not spec_path.exists():
        logger.warning(f"body_dimension_reference.json not found, skipping scale correction")
        return entities, 1.0

    with open(spec_path) as f:
        specs = json.load(f)

    if spec_name not in specs:
        logger.warning(f"Spec '{spec_name}' not found, skipping scale correction")
        return entities, 1.0

    spec = specs[spec_name]
    spec_height_mm = spec.get("body_length_mm", 500.0)

    # Get BODY bounding box height
    if not entities.body:
        logger.warning("No BODY entities, skipping scale correction")
        return entities, 1.0

    # Compute combined bounding box of all BODY entities
    all_points = []
    for entity in entities.body:
        pts = entity.contour.reshape(-1, 2)
        all_points.extend(pts.tolist())

    if not all_points:
        return entities, 1.0

    all_points = np.array(all_points)
    min_y, max_y = all_points[:, 1].min(), all_points[:, 1].max()
    raw_height_px = max_y - min_y

    # Convert to mm using current mm_per_px
    raw_height_mm = raw_height_px * entities.mm_per_px

    if raw_height_mm < 1.0:
        logger.warning(f"Raw height too small ({raw_height_mm:.1f}mm), skipping scale correction")
        return entities, 1.0

    # Compute scale factor from height
    scale_factor = spec_height_mm / raw_height_mm

    # Width validation: check aspect ratio against spec
    min_x, max_x = all_points[:, 0].min(), all_points[:, 0].max()
    raw_width_px = max_x - min_x
    raw_width_mm = raw_width_px * entities.mm_per_px
    spec_width_mm = spec.get("lower_bout_width_mm")  # Widest point

    if spec_width_mm:
        spec_aspect = spec_width_mm / spec_height_mm
        raw_aspect = raw_width_mm / raw_height_mm
        aspect_drift = abs(raw_aspect - spec_aspect) / spec_aspect

        if aspect_drift > 0.10:
            logger.warning(
                f"Aspect ratio drift {aspect_drift:.1%}: source W/H={raw_aspect:.3f}, "
                f"spec W/H={spec_aspect:.3f}. Source may be cropped or angled."
            )

    logger.info(
        f"Scale correction: spec={spec_name}, spec_height={spec_height_mm:.1f}mm, "
        f"raw_height={raw_height_mm:.1f}mm, factor={scale_factor:.3f}"
    )

    # Apply scale to BODY entities only
    corrected_body = []
    for entity in entities.body:
        pts = entity.contour.reshape(-1, 2).astype(float)
        # Scale coordinates
        pts *= scale_factor
        corrected_contour = pts.astype(np.int32).reshape(-1, 1, 2)

        # Recompute bbox
        x, y, w, h = cv2.boundingRect(corrected_contour)

        corrected_entity = LayeredEntity(
            contour=corrected_contour,
            layer=entity.layer,
            bbox=(x, y, w, h),
            area=cv2.contourArea(corrected_contour),
            is_closed=entity.is_closed,
        )
        corrected_body.append(corrected_entity)

    # Build corrected entities (only BODY is scaled)
    # NOTE: mm_per_px is NOT scaled because coordinates are already scaled.
    # DXF writer does: coord * mm_per_px. If we scaled both, we'd get scale_factor^2.
    corrected = LayeredEntities(
        body=corrected_body,
        aux_views=entities.aux_views,
        annotation=entities.annotation,
        title_block=entities.title_block,
        page_frame=entities.page_frame,
        image_size=entities.image_size,
        mm_per_px=entities.mm_per_px,  # Keep original - coords are already scaled
    )

    return corrected, scale_factor
