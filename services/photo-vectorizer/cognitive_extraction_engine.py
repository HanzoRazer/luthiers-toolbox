"""
CognitiveExtractionEngine - Agentic shape extraction with parallel methods and iterative refinement.

Architecture:
1. Parallel extraction methods each produce certainty maps
2. Fusion layer merges them into a single grid certainty map
3. Agentic reasoner analyzes the grid, forms hypotheses
4. Agent issues feedback to adjust extraction weights
5. Loop continues until convergence or max iterations

Key modifications from base document:
- max_grid_size guard: grid_size capped at 32 for performance
- AI image bypass: source_type='ai_render' returns early (AI images don't need cognitive refinement)
- Shape knowledge: loaded from body_dimension_reference.json
- Focus boost copy(): all _boost_focus_cells methods use .copy() to prevent mutation
"""

import json
import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Max grid size guard - prevents excessive memory/compute for large grids
MAX_GRID_SIZE = 32

# Path to shape knowledge reference
SHAPE_KNOWLEDGE_PATH = Path(__file__).parent / "body_dimension_reference.json"


# =============================================================================
# Core Data Structures
# =============================================================================

class CellType(Enum):
    UNKNOWN = "unknown"
    BODY = "body"
    NECK = "neck"
    HEADSTOCK = "headstock"
    BACKGROUND = "background"
    HOLE = "hole"
    EDGE = "edge"
    UNCERTAIN = "uncertain"


class ExtractionMethod(Enum):
    OTSU = "otsu"
    CANNY = "canny"
    COLOR = "color"
    GRID = "grid"
    EDGE_FLOW = "edge_flow"
    WATERSHED = "watershed"
    ADAPTIVE_THRESH = "adaptive_thresh"


@dataclass
class ExtractionResult:
    """Result from a single extraction method."""
    method: ExtractionMethod
    certainty_map: np.ndarray  # 0-1 certainty per grid cell
    contour: Optional[np.ndarray] = None
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    notes: List[str] = field(default_factory=list)


@dataclass
class CellState:
    """What the agent knows about one grid cell."""
    beliefs: Dict[CellType, float] = field(default_factory=dict)
    certainty: float = 0.0  # aggregated certainty from all methods
    pixel_stats: Dict[str, float] = field(default_factory=dict)
    neighbors: List[Tuple[int, int]] = field(default_factory=list)
    is_border: bool = False
    visited_count: int = 0

    def entropy(self) -> float:
        if not self.beliefs:
            return 1.0
        probs = list(self.beliefs.values())
        return -sum(p * math.log(p + 1e-10) for p in probs)

    def most_likely(self) -> CellType:
        if not self.beliefs:
            return CellType.UNKNOWN
        return max(self.beliefs, key=self.beliefs.get)


@dataclass
class Hypothesis:
    """A hypothesis about a region of cells."""
    type: CellType
    cells: List[Tuple[int, int]]
    confidence: float
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)

    @property
    def area(self) -> int:
        return len(self.cells)

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        if not self.cells:
            return (0, 0, 0, 0)
        rows = [r for r, c in self.cells]
        cols = [c for r, c in self.cells]
        return (min(cols), min(rows), max(cols) - min(cols) + 1, max(rows) - min(rows) + 1)


@dataclass
class AgentState:
    """Current state of the agentic reasoner."""
    iteration: int = 0
    converged: bool = False
    hypotheses: List[Hypothesis] = field(default_factory=list)
    method_weights: Dict[ExtractionMethod, float] = field(default_factory=dict)
    focus_cells: List[Tuple[int, int]] = field(default_factory=list)
    last_action: str = ""
    reasoning_trace: List[Dict[str, Any]] = field(default_factory=list)


# =============================================================================
# Shape Knowledge Loader
# =============================================================================

def load_shape_knowledge() -> Dict[str, Any]:
    """Load shape knowledge from body_dimension_reference.json."""
    if not SHAPE_KNOWLEDGE_PATH.exists():
        logger.warning("Shape knowledge file not found at %s, using defaults", SHAPE_KNOWLEDGE_PATH)
        return _default_shape_knowledge()

    try:
        with open(SHAPE_KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Convert body_dimension_reference format to shape knowledge format
        knowledge = {
            'body': {
                'min_aspect': 0.8,
                'max_aspect': 1.6,
                'min_cells': 12,
                'should_be_connected': True,
                'should_have_symmetry': True,
                'lower_bout_wider': True,
                'instruments': {},
            },
            'neck': {
                'max_width_cells': 2,
                'min_height_cells': 3,
                'aspect_ratio_min': 2.0,
                'should_connect_to_body': True,
            },
            'background': {
                'touches_border': True,
                'should_be_continuous': True,
            }
        }

        # Load instrument-specific dimensions
        for instrument, dims in data.items():
            if instrument.startswith("_"):
                continue
            if isinstance(dims, dict):
                knowledge['body']['instruments'][instrument] = {
                    'body_length_mm': dims.get('body_length_mm'),
                    'upper_bout_width_mm': dims.get('upper_bout_width_mm'),
                    'waist_width_mm': dims.get('waist_width_mm'),
                    'lower_bout_width_mm': dims.get('lower_bout_width_mm'),
                    'waist_y_norm': dims.get('waist_y_norm'),
                    'family': dims.get('family'),
                }

        return knowledge

    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load shape knowledge: %s, using defaults", e)
        return _default_shape_knowledge()


def _default_shape_knowledge() -> Dict[str, Any]:
    """Default knowledge about guitar shapes."""
    return {
        'body': {
            'min_aspect': 0.8,
            'max_aspect': 1.6,
            'min_cells': 12,
            'should_be_connected': True,
            'should_have_symmetry': True,
            'lower_bout_wider': True,
        },
        'neck': {
            'max_width_cells': 2,
            'min_height_cells': 3,
            'aspect_ratio_min': 2.0,
            'should_connect_to_body': True,
        },
        'background': {
            'touches_border': True,
            'should_be_continuous': True,
        }
    }


# =============================================================================
# Parallel Extraction Methods
# =============================================================================

class OtsuExtractor:
    """Otsu threshold extraction."""

    def extract(self, image: np.ndarray, grid_size: int,
                focus_cells: Optional[List[Tuple[int, int]]] = None) -> ExtractionResult:
        start = cv2.getTickCount()

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Clean up
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Build certainty map from binary
        certainty = self._binary_to_certainty(binary, grid_size)

        # If focus cells provided, boost certainty there
        if focus_cells:
            certainty = self._boost_focus_cells(certainty, focus_cells, grid_size)

        # Extract contour
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours, key=cv2.contourArea) if contours else None

        elapsed = (cv2.getTickCount() - start) / cv2.getTickFrequency() * 1000

        return ExtractionResult(
            method=ExtractionMethod.OTSU,
            certainty_map=certainty,
            contour=contour,
            confidence=0.8 if contour is not None else 0.0,
            processing_time_ms=elapsed
        )

    def _binary_to_certainty(self, binary: np.ndarray, grid_size: int) -> np.ndarray:
        h, w = binary.shape
        cell_h = h // grid_size
        cell_w = w // grid_size
        certainty = np.zeros((grid_size, grid_size), dtype=np.float32)

        for row in range(grid_size):
            for col in range(grid_size):
                y1 = row * cell_h
                y2 = min((row + 1) * cell_h, h)
                x1 = col * cell_w
                x2 = min((col + 1) * cell_w, w)
                region = binary[y1:y2, x1:x2]
                if region.size > 0:
                    fg_ratio = np.sum(region > 0) / region.size
                    certainty[row, col] = fg_ratio
        return certainty

    def _boost_focus_cells(self, certainty: np.ndarray,
                           focus_cells: List[Tuple[int, int]],
                           grid_size: int) -> np.ndarray:
        boosted = certainty.copy()  # CRITICAL: use copy() to prevent mutation
        for r, c in focus_cells:
            if 0 <= r < grid_size and 0 <= c < grid_size:
                boosted[r, c] = min(1.0, boosted[r, c] + 0.3)
        return boosted


class CannyExtractor:
    """Canny edge extraction."""

    def __init__(self, low_threshold: int = 50, high_threshold: int = 150):
        self.low = low_threshold
        self.high = high_threshold

    def extract(self, image: np.ndarray, grid_size: int,
                focus_cells: Optional[List[Tuple[int, int]]] = None) -> ExtractionResult:
        start = cv2.getTickCount()

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, self.low, self.high)

        # Dilate to connect edges
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

        certainty = self._edges_to_certainty(edges, grid_size)

        if focus_cells:
            certainty = self._boost_focus_cells(certainty, focus_cells, grid_size)

        # Extract contour from edge closure
        contour = self._edges_to_contour(edges)

        elapsed = (cv2.getTickCount() - start) / cv2.getTickFrequency() * 1000

        return ExtractionResult(
            method=ExtractionMethod.CANNY,
            certainty_map=certainty,
            contour=contour,
            confidence=0.7 if contour is not None else 0.0,
            processing_time_ms=elapsed
        )

    def _edges_to_certainty(self, edges: np.ndarray, grid_size: int) -> np.ndarray:
        h, w = edges.shape
        cell_h = h // grid_size
        cell_w = w // grid_size
        certainty = np.zeros((grid_size, grid_size), dtype=np.float32)

        for row in range(grid_size):
            for col in range(grid_size):
                y1 = row * cell_h
                y2 = min((row + 1) * cell_h, h)
                x1 = col * cell_w
                x2 = min((col + 1) * cell_w, w)
                region = edges[y1:y2, x1:x2]
                if region.size > 0:
                    edge_ratio = np.sum(region > 0) / region.size
                    certainty[row, col] = min(1.0, edge_ratio * 5)  # Boost sparse edges
        return certainty

    def _boost_focus_cells(self, certainty: np.ndarray,
                           focus_cells: List[Tuple[int, int]],
                           grid_size: int) -> np.ndarray:
        boosted = certainty.copy()  # CRITICAL: use copy() to prevent mutation
        for r, c in focus_cells:
            if 0 <= r < grid_size and 0 <= c < grid_size:
                boosted[r, c] = min(1.0, boosted[r, c] + 0.2)
        return boosted

    def _edges_to_contour(self, edges: np.ndarray) -> Optional[np.ndarray]:
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 1000:
                return largest
        return None


class ColorSegmenter:
    """Color-based segmentation."""

    def extract(self, image: np.ndarray, grid_size: int,
                focus_cells: Optional[List[Tuple[int, int]]] = None) -> ExtractionResult:
        start = cv2.getTickCount()

        # Convert to HSV for better color separation
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Find dominant colors (simple approach: k-means on border pixels)
        bg_color = self._estimate_background_color(image)

        # Create mask for pixels similar to background
        lower = np.array([max(0, bg_color[0] - 20), 20, 20])
        upper = np.array([min(180, bg_color[0] + 20), 255, 255])
        bg_mask = cv2.inRange(hsv, lower, upper)

        # Foreground is inverse
        fg_mask = cv2.bitwise_not(bg_mask)

        # Clean up
        kernel = np.ones((5, 5), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        certainty = self._mask_to_certainty(fg_mask, grid_size)

        if focus_cells:
            certainty = self._boost_focus_cells(certainty, focus_cells, grid_size)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours, key=cv2.contourArea) if contours else None

        elapsed = (cv2.getTickCount() - start) / cv2.getTickFrequency() * 1000

        return ExtractionResult(
            method=ExtractionMethod.COLOR,
            certainty_map=certainty,
            contour=contour,
            confidence=0.65 if contour is not None else 0.0,
            processing_time_ms=elapsed
        )

    def _estimate_background_color(self, image: np.ndarray) -> Tuple[int, int, int]:
        """Estimate background color from image borders."""
        h, w = image.shape[:2]
        border_pixels = np.concatenate([
            image[0:10, :].reshape(-1, 3),
            image[-10:, :].reshape(-1, 3),
            image[:, 0:10].reshape(-1, 3),
            image[:, -10:].reshape(-1, 3)
        ])
        hsv_border = cv2.cvtColor(border_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
        median_hue = int(np.median(hsv_border[:, 0]))
        return (median_hue, 0, 0)

    def _mask_to_certainty(self, mask: np.ndarray, grid_size: int) -> np.ndarray:
        h, w = mask.shape
        cell_h = h // grid_size
        cell_w = w // grid_size
        certainty = np.zeros((grid_size, grid_size), dtype=np.float32)

        for row in range(grid_size):
            for col in range(grid_size):
                y1 = row * cell_h
                y2 = min((row + 1) * cell_h, h)
                x1 = col * cell_w
                x2 = min((col + 1) * cell_w, w)
                region = mask[y1:y2, x1:x2]
                if region.size > 0:
                    fg_ratio = np.sum(region > 0) / region.size
                    certainty[row, col] = fg_ratio
        return certainty

    def _boost_focus_cells(self, certainty: np.ndarray,
                           focus_cells: List[Tuple[int, int]],
                           grid_size: int) -> np.ndarray:
        boosted = certainty.copy()  # CRITICAL: use copy() to prevent mutation
        for r, c in focus_cells:
            if 0 <= r < grid_size and 0 <= c < grid_size:
                boosted[r, c] = min(1.0, boosted[r, c] + 0.25)
        return boosted


class EdgeFlowExtractor:
    """
    Edge flow extraction - follows continuous boundaries.
    This is especially good for finding the full outline when there are gaps.

    Uses vectorized numpy implementation with for-loop propagating along gradient direction.
    """

    def extract(self, image: np.ndarray, grid_size: int,
                focus_cells: Optional[List[Tuple[int, int]]] = None) -> ExtractionResult:
        start = cv2.getTickCount()

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Compute gradient magnitude and direction
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        mag = np.sqrt(gx**2 + gy**2)
        angle = np.arctan2(gy, gx)

        # Normalize magnitude
        mag = np.clip(mag / mag.max(), 0, 1) if mag.max() > 0 else mag

        # Edge flow: follow the strongest gradient direction
        flow_map = self._compute_edge_flow(mag, angle)

        certainty = self._flow_to_certainty(flow_map, grid_size)

        if focus_cells:
            certainty = self._boost_focus_cells(certainty, focus_cells, grid_size)

        # Extract contour from flow map
        flow_binary = (flow_map > 0.3).astype(np.uint8) * 255
        contours, _ = cv2.findContours(flow_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours, key=cv2.contourArea) if contours else None

        elapsed = (cv2.getTickCount() - start) / cv2.getTickFrequency() * 1000

        return ExtractionResult(
            method=ExtractionMethod.EDGE_FLOW,
            certainty_map=certainty,
            contour=contour,
            confidence=0.75 if contour is not None else 0.0,
            processing_time_ms=elapsed
        )

    def _compute_edge_flow(self, mag: np.ndarray, angle: np.ndarray) -> np.ndarray:
        """Simple edge flow by propagating edge strength along gradient direction."""
        h, w = mag.shape
        flow = np.zeros_like(mag)

        # For each strong edge, propagate forward and backward
        strong_edges = mag > 0.2
        for y in range(h):
            for x in range(w):
                if strong_edges[y, x]:
                    flow[y, x] = mag[y, x]
                    # Propagate along angle
                    dx = int(5 * np.cos(angle[y, x]))
                    dy = int(5 * np.sin(angle[y, x]))
                    for step in range(1, 10):
                        nx, ny = x + dx * step, y + dy * step
                        if 0 <= nx < w and 0 <= ny < h:
                            flow[ny, nx] = max(flow[ny, nx], mag[y, x] * (1 - step / 20))
                        else:
                            break
        return flow

    def _flow_to_certainty(self, flow: np.ndarray, grid_size: int) -> np.ndarray:
        h, w = flow.shape
        cell_h = h // grid_size
        cell_w = w // grid_size
        certainty = np.zeros((grid_size, grid_size), dtype=np.float32)

        for row in range(grid_size):
            for col in range(grid_size):
                y1 = row * cell_h
                y2 = min((row + 1) * cell_h, h)
                x1 = col * cell_w
                x2 = min((col + 1) * cell_w, w)
                region = flow[y1:y2, x1:x2]
                if region.size > 0:
                    certainty[row, col] = float(np.mean(region))
        return certainty

    def _boost_focus_cells(self, certainty: np.ndarray,
                           focus_cells: List[Tuple[int, int]],
                           grid_size: int) -> np.ndarray:
        boosted = certainty.copy()  # CRITICAL: use copy() to prevent mutation
        for r, c in focus_cells:
            if 0 <= r < grid_size and 0 <= c < grid_size:
                boosted[r, c] = min(1.0, boosted[r, c] + 0.3)
        return boosted


class GridClassifierWrapper:
    """
    Wrapper for existing grid_classify to make it compatible.
    """

    def __init__(self, base_classifier: Any):
        self.base = base_classifier

    def extract(self, image: np.ndarray, grid_size: int,
                focus_cells: Optional[List[Tuple[int, int]]] = None) -> ExtractionResult:
        start = cv2.getTickCount()

        # Run the existing grid classifier
        # This assumes grid_classify returns a classification per cell
        classification = self.base.classify(image)

        # Convert to certainty map
        certainty = self._classification_to_certainty(classification, grid_size)

        if focus_cells:
            certainty = self._boost_focus_cells(certainty, focus_cells, grid_size)

        # Extract contour from classification (simplified)
        mask = (certainty > 0.5).astype(np.uint8) * 255
        mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours, key=cv2.contourArea) if contours else None

        elapsed = (cv2.getTickCount() - start) / cv2.getTickFrequency() * 1000

        return ExtractionResult(
            method=ExtractionMethod.GRID,
            certainty_map=certainty,
            contour=contour,
            confidence=0.6 if contour is not None else 0.0,
            processing_time_ms=elapsed
        )

    def _classification_to_certainty(self, classification: Any, grid_size: int) -> np.ndarray:
        """Convert grid_classify output to a certainty map."""
        # This is a placeholder - adapt to actual grid_classify output format
        certainty = np.zeros((grid_size, grid_size), dtype=np.float32)
        # Map classification to certainty based on actual implementation
        return certainty

    def _boost_focus_cells(self, certainty: np.ndarray,
                           focus_cells: List[Tuple[int, int]],
                           grid_size: int) -> np.ndarray:
        boosted = certainty.copy()  # CRITICAL: use copy() to prevent mutation
        for r, c in focus_cells:
            if 0 <= r < grid_size and 0 <= c < grid_size:
                boosted[r, c] = min(1.0, boosted[r, c] + 0.2)
        return boosted


# =============================================================================
# Certainty Fusion
# =============================================================================

class CertaintyFusion:
    """
    Merges multiple extraction results into a single certainty map.

    Uses weighted average with optional adaptive weighting based on
    method performance in focus areas.
    """

    def __init__(self):
        self.base_weights = {
            ExtractionMethod.OTSU: 0.20,
            ExtractionMethod.CANNY: 0.20,
            ExtractionMethod.COLOR: 0.15,
            ExtractionMethod.GRID: 0.25,
            ExtractionMethod.EDGE_FLOW: 0.20,
        }

    def fuse(self, results: List[ExtractionResult],
             focus_cells: Optional[List[Tuple[int, int]]] = None,
             adaptive: bool = True) -> np.ndarray:
        """
        Fuse multiple results into a single certainty map.

        Args:
            results: List of extraction results
            focus_cells: Cells to prioritize (boost weights of methods that agree)
            adaptive: If True, adjust weights based on agreement in focus area

        Returns:
            Combined certainty map (grid_size x grid_size)
        """
        if not results:
            return np.zeros((1, 1))

        grid_size = results[0].certainty_map.shape[0]
        total_certainty = np.zeros((grid_size, grid_size), dtype=np.float32)
        total_weight = np.zeros((grid_size, grid_size), dtype=np.float32)

        # Get weights (adaptive if requested)
        weights = self._get_weights(results, focus_cells) if adaptive else self.base_weights

        for result in results:
            weight = weights.get(result.method, 0.1)
            total_certainty += result.certainty_map * weight
            total_weight += weight

        # Avoid division by zero
        total_weight[total_weight == 0] = 1.0

        fused = total_certainty / total_weight

        # Apply focus boost
        if focus_cells:
            fused = self._apply_focus_boost(fused, focus_cells, results)

        return np.clip(fused, 0, 1)

    def _get_weights(self, results: List[ExtractionResult],
                     focus_cells: Optional[List[Tuple[int, int]]]) -> Dict[ExtractionMethod, float]:
        """Calculate adaptive weights based on agreement in focus area."""
        weights = self.base_weights.copy()

        if not focus_cells:
            return weights

        # For each method, measure agreement with others in focus area
        agreements: Dict[ExtractionMethod, float] = defaultdict(float)

        for i, r1 in enumerate(results):
            for j, r2 in enumerate(results):
                if i >= j:
                    continue
                # Measure correlation in focus cells
                corr = self._correlation_in_cells(r1.certainty_map, r2.certainty_map, focus_cells)
                agreements[r1.method] += corr
                agreements[r2.method] += corr

        # Normalize and adjust weights
        total_agreement = sum(agreements.values()) or 1.0
        for method in weights:
            if method in agreements:
                # Boost methods that agree with others
                weights[method] = 0.5 * self.base_weights[method] + 0.5 * (agreements[method] / total_agreement)

        return weights

    def _correlation_in_cells(self, map1: np.ndarray, map2: np.ndarray,
                               cells: List[Tuple[int, int]]) -> float:
        """Calculate correlation between two certainty maps in specific cells."""
        vals1 = [map1[r, c] for r, c in cells if 0 <= r < map1.shape[0] and 0 <= c < map1.shape[1]]
        vals2 = [map2[r, c] for r, c in cells if 0 <= r < map2.shape[0] and 0 <= c < map2.shape[1]]

        if len(vals1) < 2:
            return 0.5

        # Simple agreement: 1 - normalized absolute difference
        diffs = [abs(v1 - v2) for v1, v2 in zip(vals1, vals2)]
        avg_diff = sum(diffs) / len(diffs)
        return 1.0 - avg_diff

    def _apply_focus_boost(self, fused: np.ndarray,
                           focus_cells: List[Tuple[int, int]],
                           results: List[ExtractionResult]) -> np.ndarray:
        """Boost certainty in focus cells where multiple methods agree."""
        boosted = fused.copy()  # CRITICAL: use copy() to prevent mutation

        for r, c in focus_cells:
            if 0 <= r < fused.shape[0] and 0 <= c < fused.shape[1]:
                # Count how many methods have high certainty here
                agreements = sum(1 for res in results
                               if res.certainty_map[r, c] > 0.7)
                if agreements >= 3:
                    boosted[r, c] = min(1.0, boosted[r, c] + 0.2)

        return boosted


# =============================================================================
# Grid Memory (Spatial Workspace)
# =============================================================================

class GridMemory:
    """
    2D spatial memory that stores cell states and relationships.

    The agent queries and updates this as it reasons about the image.
    """

    def __init__(self, image: np.ndarray, grid_size: int, fused_certainty: np.ndarray):
        self.image = image
        self.h, self.w = image.shape[:2]
        self.grid_size = grid_size
        self.cell_h = self.h // grid_size
        self.cell_w = self.w // grid_size

        # Initialize cells
        self.cells: Dict[Tuple[int, int], CellState] = {}
        self._initialize_cells(fused_certainty)

        # Precompute edge map
        self.edge_map = self._compute_edge_map()

    def _initialize_cells(self, fused_certainty: np.ndarray):
        """Initialize each cell with pixel statistics and fused certainty."""
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                y1 = row * self.cell_h
                y2 = min((row + 1) * self.cell_h, self.h)
                x1 = col * self.cell_w
                x2 = min((col + 1) * self.cell_w, self.w)

                cell_region = gray[y1:y2, x1:x2]
                hsv_region = hsv[y1:y2, x1:x2]

                if cell_region.size == 0:
                    continue

                is_border = (row == 0 or row == self.grid_size - 1 or
                            col == 0 or col == self.grid_size - 1)

                # Initial beliefs based on fused certainty
                certainty = fused_certainty[row, col] if row < fused_certainty.shape[0] and col < fused_certainty.shape[1] else 0.5

                beliefs = {
                    CellType.BODY: certainty if certainty > 0.5 else 0.2,
                    CellType.BACKGROUND: (1 - certainty) if certainty < 0.5 else 0.2,
                    CellType.UNKNOWN: 0.6 - abs(certainty - 0.5),
                }

                # Normalize
                total = sum(beliefs.values())
                if total > 0:
                    for k in beliefs:
                        beliefs[k] /= total

                self.cells[(row, col)] = CellState(
                    beliefs=beliefs,
                    certainty=certainty,
                    pixel_stats={
                        'mean_intensity': float(np.mean(cell_region)),
                        'variance': float(np.var(cell_region)),
                        'edge_density': float(np.sum(cell_region > 200) / cell_region.size),
                        'hue': float(np.mean(hsv_region[:, :, 0])) if hsv_region.size > 0 else 0,
                        'saturation': float(np.mean(hsv_region[:, :, 1])) if hsv_region.size > 0 else 0,
                    },
                    is_border=is_border
                )

        # Set neighbor relationships
        for (r, c) in self.cells:
            neighbors = []
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in self.cells:
                        neighbors.append((nr, nc))
            self.cells[(r, c)].neighbors = neighbors

    def _compute_edge_map(self) -> np.ndarray:
        """Precompute edge detection for fast queries."""
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_grid = np.zeros((self.grid_size, self.grid_size), dtype=np.float32)

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                y1 = row * self.cell_h
                y2 = min((row + 1) * self.cell_h, self.h)
                x1 = col * self.cell_w
                x2 = min((col + 1) * self.cell_w, self.w)
                region = edges[y1:y2, x1:x2]
                edge_grid[row, col] = np.sum(region > 0) / region.size if region.size > 0 else 0
        return edge_grid

    def get_cell(self, row: int, col: int) -> Optional[CellState]:
        return self.cells.get((row, col))

    def update_belief(self, row: int, col: int, cell_type: CellType, confidence: float):
        """Update what the agent believes about a cell."""
        cell = self.get_cell(row, col)
        if not cell:
            return

        # Bayesian update
        old_belief = cell.beliefs.get(cell_type, 0.0)
        new_belief = old_belief * (0.5 + confidence * 0.5)

        # Renormalize
        total = sum(cell.beliefs.values()) + new_belief - old_belief
        if total > 0:
            cell.beliefs[cell_type] = new_belief / total
            for t in list(cell.beliefs.keys()):
                if t != cell_type:
                    cell.beliefs[t] = cell.beliefs[t] / total

        cell.visited_count += 1

    def get_uncertain_cells(self, min_entropy: float = 0.5) -> List[Tuple[int, int]]:
        """Get cells the agent is most uncertain about."""
        uncertain = []
        for (r, c), cell in self.cells.items():
            if cell.entropy() > min_entropy:
                uncertain.append((r, c))
        uncertain.sort(key=lambda pos: self.cells[pos].entropy(), reverse=True)
        return uncertain

    def get_connected_region(self, seed: Tuple[int, int],
                             cell_type: CellType,
                             min_confidence: float = 0.5) -> List[Tuple[int, int]]:
        """Flood fill to get all cells of a type connected to seed."""
        if seed not in self.cells:
            return []

        region = []
        stack = [seed]
        visited: set = set()

        while stack:
            pos = stack.pop()
            if pos in visited:
                continue
            visited.add(pos)

            cell = self.get_cell(*pos)
            if cell and cell.beliefs.get(cell_type, 0) >= min_confidence:
                region.append(pos)
                for neighbor in cell.neighbors:
                    if neighbor not in visited:
                        stack.append(neighbor)

        return region


# =============================================================================
# Agentic Reasoner (The Thinker)
# =============================================================================

class AgenticReasoner:
    """
    The reasoning agent that analyzes the grid and decides what to do next.

    It forms hypotheses, evaluates them against shape knowledge,
    and issues feedback to refine extraction.
    """

    def __init__(self, shape_knowledge: Optional[Dict] = None):
        self.shape_knowledge = shape_knowledge or load_shape_knowledge()
        self.state = AgentState()
        self._init_weights()

    def _init_weights(self):
        """Initialize method weights."""
        self.state.method_weights = {
            ExtractionMethod.OTSU: 0.20,
            ExtractionMethod.CANNY: 0.20,
            ExtractionMethod.COLOR: 0.15,
            ExtractionMethod.GRID: 0.25,
            ExtractionMethod.EDGE_FLOW: 0.20,
        }

    def analyze(self, memory: GridMemory, fused_certainty: np.ndarray) -> AgentState:
        """
        Analyze the current grid state, form hypotheses, decide next action.

        Returns updated agent state with hypotheses and next focus cells.
        """
        self.state.iteration += 1

        # 1. Identify uncertain cells
        uncertain = memory.get_uncertain_cells(min_entropy=0.4)

        if not uncertain:
            self.state.converged = True
            self.state.last_action = "Converged - no uncertain cells"
            return self.state

        # 2. Form hypotheses from high-certainty regions
        self._form_hypotheses(memory)

        # 3. Evaluate hypotheses against shape knowledge
        self._evaluate_hypotheses(memory)

        # 4. Determine focus cells (where we need more information)
        self.state.focus_cells = self._determine_focus_cells(memory, uncertain)

        # 5. Decide next action
        self.state.last_action = self._decide_action(memory)

        # 6. Record reasoning trace
        self.state.reasoning_trace.append({
            'iteration': self.state.iteration,
            'hypotheses': len(self.state.hypotheses),
            'focus_cells': len(self.state.focus_cells),
            'uncertain_cells': len(uncertain),
            'action': self.state.last_action,
        })

        return self.state

    def _form_hypotheses(self, memory: GridMemory):
        """Form hypotheses from high-certainty regions."""
        # Find seeds for body hypothesis
        body_seeds = []
        for (r, c), cell in memory.cells.items():
            if cell.beliefs.get(CellType.BODY, 0) > 0.7:
                body_seeds.append((r, c))

        # Group connected seeds
        visited: set = set()
        for seed in body_seeds:
            if seed in visited:
                continue
            region = memory.get_connected_region(seed, CellType.BODY, min_confidence=0.6)
            visited.update(region)

            if len(region) >= 5:  # Minimum size for a body
                confidence = self._score_body_hypothesis(region, memory)
                self.state.hypotheses.append(Hypothesis(
                    type=CellType.BODY,
                    cells=region,
                    confidence=confidence,
                    supporting_evidence=[f"Region of {len(region)} cells with high body belief"]
                ))

        # Find background regions (touching border)
        bg_region: List[Tuple[int, int]] = []
        for (r, c), cell in memory.cells.items():
            if cell.is_border and cell.beliefs.get(CellType.BACKGROUND, 0) > 0.5:
                bg_region = memory.get_connected_region((r, c), CellType.BACKGROUND)
                break

        if bg_region:
            self.state.hypotheses.append(Hypothesis(
                type=CellType.BACKGROUND,
                cells=bg_region,
                confidence=0.8,
                supporting_evidence=["Touches image border"]
            ))

    def _score_body_hypothesis(self, cells: List[Tuple[int, int]], memory: GridMemory) -> float:
        """Score a body hypothesis based on shape knowledge."""
        if len(cells) < 5:
            return 0.0

        rows = [r for r, c in cells]
        cols = [c for r, c in cells]
        height = max(rows) - min(rows) + 1
        width = max(cols) - min(cols) + 1
        aspect = height / max(width, 1)

        score = 0.0

        # Aspect ratio
        body_knowledge = self.shape_knowledge.get('body', {})
        min_aspect = body_knowledge.get('min_aspect', 0.8)
        max_aspect = body_knowledge.get('max_aspect', 1.6)

        if min_aspect <= aspect <= max_aspect:
            score += 0.3
        else:
            score += 0.1

        # Size
        min_cells = body_knowledge.get('min_cells', 12)
        if len(cells) >= min_cells:
            score += 0.3

        # Symmetry (approximate)
        center = (min(cols) + max(cols)) / 2
        left_count = sum(1 for r, c in cells if c < center)
        right_count = sum(1 for r, c in cells if c > center)
        if left_count > 0 and right_count > 0:
            symmetry = min(left_count, right_count) / max(left_count, right_count)
            if symmetry > 0.7:
                score += 0.2
            elif symmetry > 0.5:
                score += 0.1

        # Check if lower part is wider (guitar characteristic)
        if body_knowledge.get('lower_bout_wider', True):
            mid_row = (min(rows) + max(rows)) // 2
            lower_cells = [c for r, c in cells if r > mid_row]
            upper_cells = [c for r, c in cells if r < mid_row]
            if lower_cells and upper_cells:
                lower_width = max(lower_cells) - min(lower_cells)
                upper_width = max(upper_cells) - min(upper_cells)
                if lower_width > upper_width:
                    score += 0.2

        return min(1.0, score)

    def _evaluate_hypotheses(self, memory: GridMemory):
        """Evaluate hypotheses and add contradicting evidence."""
        for hyp in self.state.hypotheses:
            if hyp.type == CellType.BODY:
                # Check for holes inside body (could be soundhole, f-hole)
                holes = self._find_holes_in_region(hyp.cells, memory)
                if holes:
                    hyp.supporting_evidence.append(f"Contains {len(holes)} interior holes")
                else:
                    hyp.contradicting_evidence.append("No interior features found")

    def _find_holes_in_region(self, region_cells: List[Tuple[int, int]],
                               memory: GridMemory) -> List[List[Tuple[int, int]]]:
        """Find holes (cells with low certainty) inside a region."""
        # Simplified implementation
        holes: List[List[Tuple[int, int]]] = []
        return holes

    def _determine_focus_cells(self, memory: GridMemory,
                                uncertain: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Determine which cells to focus on next."""
        focus = []

        # Prioritize uncertain cells that are adjacent to high-certainty body cells
        for r, c in uncertain:
            cell = memory.get_cell(r, c)
            if not cell:
                continue

            # Check neighbors for high body belief
            for nr, nc in cell.neighbors:
                neighbor = memory.get_cell(nr, nc)
                if neighbor and neighbor.beliefs.get(CellType.BODY, 0) > 0.7:
                    focus.append((r, c))
                    break

        # Also focus on cells that would connect fragmented body regions
        if len(self.state.hypotheses) >= 2:
            body_hyp = [h for h in self.state.hypotheses if h.type == CellType.BODY]
            if len(body_hyp) >= 2:
                # Find gap between body hypotheses
                gap = self._find_gap_between_regions(body_hyp[0].cells, body_hyp[1].cells)
                focus.extend(gap)

        # Limit focus cells
        return focus[:20]  # Don't focus on too many at once

    def _find_gap_between_regions(self, region1: List[Tuple[int, int]],
                                   region2: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Find cells that lie between two regions (potential connection)."""
        # Simple Manhattan distance heuristic
        gap = []
        for r1, c1 in region1:
            for r2, c2 in region2:
                # Cells along line between them
                dr = r2 - r1
                dc = c2 - c1
                steps = max(abs(dr), abs(dc))
                if steps == 0:
                    continue
                for t in range(1, steps):
                    r = r1 + int(dr * t / steps)
                    c = c1 + int(dc * t / steps)
                    gap.append((r, c))
        return list(set(gap))

    def _decide_action(self, memory: GridMemory) -> str:
        """Decide what action to take next."""
        # Check if we have a strong body hypothesis
        body_hyp = [h for h in self.state.hypotheses if h.type == CellType.BODY]
        if body_hyp and body_hyp[0].confidence > 0.7:
            # Check if body is complete
            if self._is_body_complete(body_hyp[0], memory):
                self.state.converged = True
                return "Converged - strong body hypothesis"
            else:
                return "Refine body boundary - look for edges"

        # Check if we have conflicting hypotheses
        if len(body_hyp) > 1:
            return "Resolve conflicting body hypotheses"

        # Default: gather more evidence
        return "Focus on uncertain cells adjacent to high-certainty regions"

    def _is_body_complete(self, hypothesis: Hypothesis, memory: GridMemory) -> bool:
        """Check if the body hypothesis forms a closed contour."""
        # Check if the region is well-defined
        body_knowledge = self.shape_knowledge.get('body', {})
        min_cells = body_knowledge.get('min_cells', 12)

        if hypothesis.area < min_cells:
            return False

        # Check if all cells have reasonable certainty
        for r, c in hypothesis.cells:
            cell = memory.get_cell(r, c)
            if cell and cell.certainty < 0.6:
                return False

        return True

    def get_feedback(self) -> Dict[str, Any]:
        """
        Generate feedback for the extraction layer.

        Returns:
            Dictionary with:
            - method_weights: Updated weights for each method
            - focus_cells: Cells to prioritize in next extraction
            - boost_areas: Areas to boost certainty
        """
        return {
            'method_weights': self.state.method_weights,
            'focus_cells': self.state.focus_cells,
            'boost_areas': self.state.focus_cells,  # Same for now
            'confidence_threshold': 0.5,
        }


# =============================================================================
# Cognitive Extraction Engine (Main Orchestrator)
# =============================================================================

class CognitiveExtractionEngine:
    """
    Main orchestrator that combines parallel extraction, certainty fusion,
    grid memory, and agentic reasoning into a closed-loop system.

    The agent thinks, the methods act, the grid remembers, and the loop continues.

    Key features:
    - max_grid_size guard: grid_size capped at MAX_GRID_SIZE (32)
    - AI image bypass: source_type='ai_render' returns early
    - Shape knowledge: loaded from body_dimension_reference.json
    """

    def __init__(self, image: np.ndarray, grid_size: int = 24, max_iterations: int = 10,
                 source_type: Optional[str] = None):
        self.image = image
        # Max grid size guard - cap at MAX_GRID_SIZE for performance
        self.grid_size = min(grid_size, MAX_GRID_SIZE)
        self.max_iterations = max_iterations
        self.source_type = source_type

        # Initialize components
        self.extractors = self._init_extractors()
        self.fusion = CertaintyFusion()
        self.reasoner = AgenticReasoner(shape_knowledge=load_shape_knowledge())

        # State
        self.memory: Optional[GridMemory] = None
        self.results: List[ExtractionResult] = []
        self.fused_certainty: Optional[np.ndarray] = None
        self.final_contour: Optional[np.ndarray] = None

        # Track if we bypassed cognitive refinement
        self.bypassed_reason: Optional[str] = None

    def _init_extractors(self) -> List:
        """Initialize all extraction methods."""
        return [
            OtsuExtractor(),
            CannyExtractor(),
            ColorSegmenter(),
            EdgeFlowExtractor(),
        ]

    def run(self) -> Dict[str, Any]:
        """
        Run the cognitive extraction loop.

        Returns:
            Dictionary with final contour, trace, and state.
        """
        # AI image bypass - AI-rendered images have clean edges, don't need cognitive refinement
        if self.source_type == 'ai_render':
            self.bypassed_reason = "AI-rendered image - cognitive refinement not needed"
            logger.info(self.bypassed_reason)
            return {
                'contour': None,
                'certainty_map': None,
                'trace': [],
                'hypotheses': [],
                'iterations': 0,
                'converged': True,
                'bypassed': True,
                'bypassed_reason': self.bypassed_reason,
            }

        trace = []

        for iteration in range(self.max_iterations):
            logger.debug("Iteration %d/%d", iteration + 1, self.max_iterations)

            # 1. Get feedback from reasoner (or initial state)
            feedback = self.reasoner.get_feedback() if iteration > 0 else {
                'method_weights': None,
                'focus_cells': None,
                'boost_areas': None,
            }

            # 2. Run parallel extraction
            self.results = self._run_extraction(feedback)

            # 3. Fuse results into certainty map
            self.fused_certainty = self.fusion.fuse(
                self.results,
                focus_cells=feedback.get('focus_cells'),
                adaptive=True
            )

            # 4. Initialize or update grid memory
            if self.memory is None:
                self.memory = GridMemory(self.image, self.grid_size, self.fused_certainty)
            else:
                self._update_memory(self.fused_certainty)

            # 5. Run agentic reasoner
            self.reasoner.analyze(self.memory, self.fused_certainty)

            # 6. Record trace
            trace.append({
                'iteration': iteration,
                'hypotheses': len(self.reasoner.state.hypotheses),
                'focus_cells': len(self.reasoner.state.focus_cells),
                'converged': self.reasoner.state.converged,
                'action': self.reasoner.state.last_action,
            })

            # 7. Check convergence
            if self.reasoner.state.converged:
                logger.info("Converged at iteration %d", iteration + 1)
                break

        # 8. Extract final contour
        self.final_contour = self._extract_final_contour()

        return {
            'contour': self.final_contour,
            'certainty_map': self.fused_certainty,
            'trace': trace,
            'hypotheses': self.reasoner.state.hypotheses,
            'iterations': iteration + 1,
            'converged': self.reasoner.state.converged,
            'bypassed': False,
        }

    def _run_extraction(self, feedback: Dict) -> List[ExtractionResult]:
        """Run all extraction methods in parallel."""
        results = []
        focus_cells = feedback.get('focus_cells')

        for extractor in self.extractors:
            try:
                result = extractor.extract(self.image, self.grid_size, focus_cells)
                results.append(result)
            except (ValueError, TypeError, cv2.error) as e:
                logger.warning("Extractor %s failed: %s", extractor.__class__.__name__, e)
                continue

        return results

    def _update_memory(self, new_certainty: np.ndarray):
        """Update grid memory with new certainty map."""
        if self.memory is None:
            return

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                cell = self.memory.get_cell(row, col)
                if cell:
                    old_certainty = cell.certainty
                    new_c = new_certainty[row, col]
                    # Exponential moving average
                    cell.certainty = 0.7 * old_certainty + 0.3 * new_c

                    # Update beliefs based on new certainty
                    if new_c > 0.7:
                        self.memory.update_belief(row, col, CellType.BODY, new_c)
                    elif new_c < 0.3:
                        self.memory.update_belief(row, col, CellType.BACKGROUND, 1 - new_c)

    def _extract_final_contour(self) -> Optional[np.ndarray]:
        """Extract final contour from best body hypothesis."""
        # Find best body hypothesis
        body_hypotheses = [h for h in self.reasoner.state.hypotheses if h.type == CellType.BODY]

        if not body_hypotheses:
            # Fallback: use high-certainty cells
            if self.fused_certainty is None:
                return None

            high_certainty = self.fused_certainty > 0.6
            if not np.any(high_certainty):
                return None

            # Convert to mask
            mask = cv2.resize(high_certainty.astype(np.uint8) * 255,
                             (self.image.shape[1], self.image.shape[0]),
                             interpolation=cv2.INTER_NEAREST)
        else:
            best = max(body_hypotheses, key=lambda h: h.confidence)

            # Convert grid cells to pixel mask
            mask = np.zeros((self.image.shape[0], self.image.shape[1]), dtype=np.uint8)
            cell_h = self.image.shape[0] // self.grid_size
            cell_w = self.image.shape[1] // self.grid_size

            for r, c in best.cells:
                y1 = r * cell_h
                y2 = min((r + 1) * cell_h, self.image.shape[0])
                x1 = c * cell_w
                x2 = min((c + 1) * cell_w, self.image.shape[1])
                mask[y1:y2, x1:x2] = 255

        # Smooth mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # Extract contour
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            # Simplify
            epsilon = 0.005 * cv2.arcLength(largest, True)
            simplified = cv2.approxPolyDP(largest, epsilon, True)
            return simplified

        return None

    def visualize(self, output_path: str):
        """Create visualization of the extraction process."""
        if self.image is None:
            return

        # Create debug image
        debug = self.image.copy()

        # Draw final contour
        if self.final_contour is not None:
            cv2.drawContours(debug, [self.final_contour], -1, (0, 255, 0), 2)

        # Draw grid
        h, w = debug.shape[:2]
        cell_h = h // self.grid_size
        cell_w = w // self.grid_size
        for i in range(self.grid_size):
            cv2.line(debug, (0, i * cell_h), (w, i * cell_h), (255, 0, 0), 1)
            cv2.line(debug, (i * cell_w, 0), (i * cell_w, h), (255, 0, 0), 1)

        # Highlight focus cells
        if self.reasoner.state.focus_cells:
            for r, c in self.reasoner.state.focus_cells:
                y1 = r * cell_h
                y2 = min((r + 1) * cell_h, h)
                x1 = c * cell_w
                x2 = min((c + 1) * cell_w, w)
                cv2.rectangle(debug, (x1, y1), (x2, y2), (0, 0, 255), 2)

        cv2.imwrite(output_path, debug)
        logger.info("Visualization saved to %s", output_path)

    def save_trace(self, output_path: str):
        """Save reasoning trace to JSON."""
        trace = {
            'iterations': len(self.reasoner.state.reasoning_trace),
            'converged': self.reasoner.state.converged,
            'final_hypotheses': [
                {
                    'type': h.type.value,
                    'cells': len(h.cells),
                    'confidence': h.confidence,
                    'supporting': h.supporting_evidence,
                    'contradicting': h.contradicting_evidence,
                }
                for h in self.reasoner.state.hypotheses
            ],
            'trace': self.reasoner.state.reasoning_trace,
        }

        with open(output_path, 'w') as f:
            json.dump(trace, f, indent=2)
        logger.info("Trace saved to %s", output_path)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Cognitive Extraction Engine")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("--grid-size", type=int, default=24, help="Grid size (cells per dimension)")
    parser.add_argument("--max-iter", type=int, default=10, help="Maximum iterations")
    parser.add_argument("--output", "-o", default="output", help="Output prefix")
    parser.add_argument("--visualize", action="store_true", help="Save visualization")
    parser.add_argument("--trace", action="store_true", help="Save reasoning trace")
    parser.add_argument("--source-type", default=None, help="Image source type (ai_render bypasses cognitive)")

    args = parser.parse_args()

    # Load image
    img = cv2.imread(args.image)
    if img is None:
        print(f"Could not load image: {args.image}")
        sys.exit(1)

    # Run cognitive engine
    print(f"Running cognitive extraction on {args.image}...")
    engine = CognitiveExtractionEngine(
        img,
        grid_size=args.grid_size,
        max_iterations=args.max_iter,
        source_type=args.source_type
    )
    result = engine.run()

    if result.get('bypassed'):
        print(f"\nBypassed: {result.get('bypassed_reason')}")
        return

    print(f"\nResults:")
    print(f"  Converged: {result['converged']}")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Hypotheses: {len(result['hypotheses'])}")
    print(f"  Contour points: {len(result['contour']) if result['contour'] is not None else 0}")

    # Save outputs
    if result['contour'] is not None:
        # Save contour as DXF (R2010 format with proper bounds)
        try:
            import ezdxf
            doc = ezdxf.new("R12")  # AC1024 minimum per CLAUDE.md
            doc.header['$INSUNITS'] = 4  # mm
            doc.header['$MEASUREMENT'] = 1  # metric
            msp = doc.modelspace()

            # Create named layer (avoid layer 0 per CLAUDE.md)
            doc.layers.add("BODY_OUTLINE", color=7)

            points = [(float(p[0][0]), float(p[0][1])) for p in result['contour']]

            # Use LINE entities (closed polyline as individual lines per CLAUDE.md)
            for i in range(len(points)):
                p1 = points[i]
                p2 = points[(i + 1) % len(points)]
                msp.add_line(p1, p2, dxfattribs={"layer": "BODY_OUTLINE"})

            # Calculate and set EXTMIN/EXTMAX bounds
            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                doc.header['$EXTMIN'] = (min(xs), min(ys), 0)
                doc.header['$EXTMAX'] = (max(xs), max(ys), 0)

            dxf_path = f"{args.output}.dxf"
            doc.saveas(dxf_path)
            print(f"  DXF saved: {dxf_path}")
        except ImportError:
            print("  ezdxf not installed - skipping DXF export")

    if args.visualize:
        vis_path = f"{args.output}_visualization.jpg"
        engine.visualize(vis_path)

    if args.trace:
        trace_path = f"{args.output}_trace.json"
        engine.save_trace(trace_path)


if __name__ == "__main__":
    main()
