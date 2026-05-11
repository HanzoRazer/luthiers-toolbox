"""
DXF Summary Comparator
======================

Basic dimensional and structural DXF comparison.
Extracts summary characteristics and compares against baselines.

MRP-1B: Regression & Behavioral Observability Infrastructure
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


@dataclass
class DXFSummary:
    """
    Summary characteristics of a DXF file for comparison.

    Captures dimensional and structural properties without
    full entity-by-entity comparison.
    """
    # Bounding box
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0

    # Derived dimensions
    width: float = 0.0
    height: float = 0.0

    # Entity counts by type
    entity_counts: Dict[str, int] = field(default_factory=dict)
    total_entities: int = 0

    # Layer information
    layers: List[str] = field(default_factory=list)
    entities_per_layer: Dict[str, int] = field(default_factory=dict)

    # Structural flags
    has_closed_paths: bool = False
    has_open_paths: bool = False

    # Metadata
    dxf_version: str = ""
    units: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "bounding_box": {
                "min_x": self.min_x,
                "min_y": self.min_y,
                "max_x": self.max_x,
                "max_y": self.max_y,
            },
            "dimensions": {
                "width": self.width,
                "height": self.height,
            },
            "entity_counts": self.entity_counts,
            "total_entities": self.total_entities,
            "layers": self.layers,
            "entities_per_layer": self.entities_per_layer,
            "has_closed_paths": self.has_closed_paths,
            "has_open_paths": self.has_open_paths,
            "dxf_version": self.dxf_version,
            "units": self.units,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DXFSummary:
        """Deserialize from dictionary."""
        bbox = data.get("bounding_box", {})
        dims = data.get("dimensions", {})
        return cls(
            min_x=bbox.get("min_x", 0.0),
            min_y=bbox.get("min_y", 0.0),
            max_x=bbox.get("max_x", 0.0),
            max_y=bbox.get("max_y", 0.0),
            width=dims.get("width", 0.0),
            height=dims.get("height", 0.0),
            entity_counts=data.get("entity_counts", {}),
            total_entities=data.get("total_entities", 0),
            layers=data.get("layers", []),
            entities_per_layer=data.get("entities_per_layer", {}),
            has_closed_paths=data.get("has_closed_paths", False),
            has_open_paths=data.get("has_open_paths", False),
            dxf_version=data.get("dxf_version", ""),
            units=data.get("units"),
        )


def extract_dxf_summary(
    dxf_source: str | bytes,
    is_base64: bool = False,
) -> DXFSummary:
    """
    Extract summary characteristics from a DXF file.

    Args:
        dxf_source: Either a file path, raw bytes, or base64-encoded string
        is_base64: If True, treat dxf_source as base64-encoded DXF content

    Returns:
        DXFSummary with extracted characteristics

    Raises:
        ImportError: If ezdxf is not available
        ValueError: If DXF cannot be parsed
    """
    if not EZDXF_AVAILABLE:
        raise ImportError("ezdxf is required for DXF comparison")

    # Handle different input types
    if is_base64 and isinstance(dxf_source, str):
        dxf_bytes = base64.b64decode(dxf_source)
        stream = io.BytesIO(dxf_bytes)
        doc = ezdxf.read(stream)
    elif isinstance(dxf_source, bytes):
        stream = io.BytesIO(dxf_source)
        doc = ezdxf.read(stream)
    else:
        doc = ezdxf.readfile(dxf_source)

    msp = doc.modelspace()

    # Initialize bounds
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    # Count entities
    entity_counts: Dict[str, int] = {}
    entities_per_layer: Dict[str, int] = {}
    total = 0
    has_closed = False
    has_open = False

    for entity in msp:
        # Count by type
        etype = entity.dxftype()
        entity_counts[etype] = entity_counts.get(etype, 0) + 1
        total += 1

        # Count by layer
        layer = entity.dxf.layer
        entities_per_layer[layer] = entities_per_layer.get(layer, 0) + 1

        # Update bounds from entity
        try:
            bbox = entity.bbox()
            if bbox is not None:
                min_x = min(min_x, bbox.extmin.x)
                min_y = min(min_y, bbox.extmin.y)
                max_x = max(max_x, bbox.extmax.x)
                max_y = max(max_y, bbox.extmax.y)
        except Exception:
            pass

        # Check for closed paths
        if etype == "LWPOLYLINE":
            if entity.closed:
                has_closed = True
            else:
                has_open = True
        elif etype == "CIRCLE" or etype == "ELLIPSE":
            has_closed = True
        elif etype == "LINE":
            has_open = True

    # Handle empty DXF
    if min_x == float("inf"):
        min_x = min_y = max_x = max_y = 0.0

    # Get layer names
    layers = sorted(entities_per_layer.keys())

    # Get DXF version
    dxf_version = doc.dxfversion

    return DXFSummary(
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
        width=max_x - min_x,
        height=max_y - min_y,
        entity_counts=entity_counts,
        total_entities=total,
        layers=layers,
        entities_per_layer=entities_per_layer,
        has_closed_paths=has_closed,
        has_open_paths=has_open,
        dxf_version=dxf_version,
    )


@dataclass
class DXFComparisonResult:
    """Result of comparing two DXF summaries."""

    # Dimensional comparison
    width_delta: float = 0.0
    height_delta: float = 0.0
    width_drift_pct: float = 0.0
    height_drift_pct: float = 0.0

    # Positional comparison
    origin_shift: Tuple[float, float] = (0.0, 0.0)

    # Entity comparison
    entity_count_delta: int = 0
    entity_type_changes: Dict[str, int] = field(default_factory=dict)

    # Layer comparison
    layers_added: List[str] = field(default_factory=list)
    layers_removed: List[str] = field(default_factory=list)

    # Structural comparison
    closed_path_change: bool = False
    open_path_change: bool = False

    # Summary
    is_match: bool = True
    drift_detected: bool = False
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "dimensional": {
                "width_delta": self.width_delta,
                "height_delta": self.height_delta,
                "width_drift_pct": self.width_drift_pct,
                "height_drift_pct": self.height_drift_pct,
            },
            "origin_shift": list(self.origin_shift),
            "entity_count_delta": self.entity_count_delta,
            "entity_type_changes": self.entity_type_changes,
            "layers_added": self.layers_added,
            "layers_removed": self.layers_removed,
            "closed_path_change": self.closed_path_change,
            "open_path_change": self.open_path_change,
            "is_match": self.is_match,
            "drift_detected": self.drift_detected,
            "warnings": self.warnings,
        }


def compare_dxf_summaries(
    baseline: DXFSummary,
    current: DXFSummary,
    dimension_tolerance_pct: float = 1.0,
    entity_count_tolerance: int = 0,
) -> DXFComparisonResult:
    """
    Compare two DXF summaries and detect drift.

    Args:
        baseline: The baseline DXF summary
        current: The current DXF summary to compare
        dimension_tolerance_pct: Acceptable dimension drift percentage
        entity_count_tolerance: Acceptable entity count difference

    Returns:
        DXFComparisonResult with comparison details
    """
    result = DXFComparisonResult()
    warnings = []

    # Dimensional comparison
    result.width_delta = current.width - baseline.width
    result.height_delta = current.height - baseline.height

    if baseline.width > 0:
        result.width_drift_pct = abs(result.width_delta) / baseline.width * 100
    if baseline.height > 0:
        result.height_drift_pct = abs(result.height_delta) / baseline.height * 100

    # Origin shift
    result.origin_shift = (
        current.min_x - baseline.min_x,
        current.min_y - baseline.min_y,
    )

    # Entity count comparison
    result.entity_count_delta = current.total_entities - baseline.total_entities

    # Entity type changes
    all_types = set(baseline.entity_counts.keys()) | set(current.entity_counts.keys())
    for etype in all_types:
        base_count = baseline.entity_counts.get(etype, 0)
        curr_count = current.entity_counts.get(etype, 0)
        if base_count != curr_count:
            result.entity_type_changes[etype] = curr_count - base_count

    # Layer comparison
    baseline_layers = set(baseline.layers)
    current_layers = set(current.layers)
    result.layers_added = sorted(current_layers - baseline_layers)
    result.layers_removed = sorted(baseline_layers - current_layers)

    # Structural comparison
    result.closed_path_change = baseline.has_closed_paths != current.has_closed_paths
    result.open_path_change = baseline.has_open_paths != current.has_open_paths

    # Determine if match or drift
    result.is_match = True
    result.drift_detected = False

    # Check dimensional drift
    if result.width_drift_pct > dimension_tolerance_pct:
        result.drift_detected = True
        warnings.append(f"Width drift {result.width_drift_pct:.2f}% exceeds tolerance")
    if result.height_drift_pct > dimension_tolerance_pct:
        result.drift_detected = True
        warnings.append(f"Height drift {result.height_drift_pct:.2f}% exceeds tolerance")

    # Check entity count
    if abs(result.entity_count_delta) > entity_count_tolerance:
        result.drift_detected = True
        warnings.append(f"Entity count changed by {result.entity_count_delta}")

    # Check layer changes
    if result.layers_added or result.layers_removed:
        result.drift_detected = True
        if result.layers_added:
            warnings.append(f"Layers added: {result.layers_added}")
        if result.layers_removed:
            warnings.append(f"Layers removed: {result.layers_removed}")

    # Check structural changes
    if result.closed_path_change:
        result.drift_detected = True
        warnings.append("Closed path presence changed")
    if result.open_path_change:
        result.drift_detected = True
        warnings.append("Open path presence changed")

    if result.drift_detected:
        result.is_match = False

    result.warnings = warnings
    return result
