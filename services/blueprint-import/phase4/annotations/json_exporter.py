"""
Annotation JSON Exporter
========================

Export annotations as JSON for non-CAD tooling, web viewers,
and CI/CD validation pipelines.

Author: Luthier's Toolbox
Version: 4.0.0
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import Annotation
from .dimensions import LinearDimension, RadialDimension

logger = logging.getLogger(__name__)


class AnnotationJSONExporter:
    """
    Export annotations as JSON for non-CAD tooling.

    Output format:
    {
        "version": "1.0",
        "generator": "Phase4.0",
        "timestamp": "2024-01-01T12:00:00",
        "source_file": "blueprint.pdf",
        "dimensions": [
            {
                "type": "linear_dimension",
                "text": "24.625",
                "value": 625.47,
                "unit": "mm",
                "confidence": 0.95,
                "feature_id": "body_outline_0",
                "linear": {
                    "point1": [100, 200],
                    "point2": [200, 200],
                    "measured_length": 625.47
                }
            }
        ],
        "statistics": {
            "total_annotations": 5,
            "by_type": {"linear_dimension": 3, "radial_dimension": 2},
            "average_confidence": 0.87
        }
    }

    Usage:
        exporter = AnnotationJSONExporter()
        exporter.export(annotations, 'output.json', source_file='blueprint.pdf')
    """

    VERSION = "1.0"
    GENERATOR = "Phase4.0"

    def __init__(self, pretty_print: bool = True):
        """
        Initialize JSON exporter.

        Args:
            pretty_print: Format JSON with indentation
        """
        self.pretty_print = pretty_print

    def export(
        self,
        annotations: List[Annotation],
        output_path: str,
        source_file: Optional[str] = None,
        include_statistics: bool = True
    ) -> Dict[str, Any]:
        """
        Export annotations to JSON file.

        Args:
            annotations: List of Annotation objects
            output_path: Output JSON file path
            source_file: Original source file name
            include_statistics: Include summary statistics

        Returns:
            The exported data dictionary
        """
        data = {
            "version": self.VERSION,
            "generator": self.GENERATOR,
            "timestamp": datetime.now().isoformat(),
            "source_file": source_file or "unknown",
            "dimensions": []
        }

        # Export each annotation
        for ann in annotations:
            dim_data = self._annotation_to_dict(ann)
            data["dimensions"].append(dim_data)

        # Add statistics
        if include_statistics:
            data["statistics"] = self._calculate_statistics(annotations)

        # Write file
        with open(output_path, 'w') as f:
            if self.pretty_print:
                json.dump(data, f, indent=2)
            else:
                json.dump(data, f)

        logger.info(f"Exported {len(annotations)} annotations to {output_path}")

        return data

    def _annotation_to_dict(self, ann: Annotation) -> Dict[str, Any]:
        """
        Convert annotation to dictionary representation.

        Args:
            ann: Annotation object

        Returns:
            Dictionary representation
        """
        dim_data = {
            "type": ann.type.value,
            "text": ann.text,
            "value": ann.value,
            "unit": ann.unit,
            "confidence": round(ann.confidence, 4),
            "feature_id": ann.feature_id,
            "source": ann.source.value,
            "position": {
                "text": list(ann.text_position),
                "leaders": [list(p) for p in ann.leader_points]
            }
        }

        # Add type-specific fields
        if isinstance(ann, LinearDimension):
            dim_data["linear"] = {
                "point1": list(ann.point1),
                "point2": list(ann.point2),
                "measured_length": ann.value
            }
        elif isinstance(ann, RadialDimension):
            dim_data["radial"] = {
                "center": list(ann.center),
                "radius": ann.radius,
                "is_diameter": ann.is_diameter,
                "measured_value": ann.value
            }

        # Add source details if hybrid
        if ann.source_details:
            dim_data["source_details"] = ann.source_details

        return dim_data

    def _calculate_statistics(self, annotations: List[Annotation]) -> Dict[str, Any]:
        """
        Calculate summary statistics.

        Args:
            annotations: List of annotations

        Returns:
            Statistics dictionary
        """
        if not annotations:
            return {
                "total_annotations": 0,
                "by_type": {},
                "by_source": {},
                "average_confidence": 0.0
            }

        # Count by type
        by_type = {}
        for ann in annotations:
            type_name = ann.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        # Count by source
        by_source = {}
        for ann in annotations:
            source_name = ann.source.value
            by_source[source_name] = by_source.get(source_name, 0) + 1

        # Average confidence
        avg_confidence = sum(a.confidence for a in annotations) / len(annotations)

        # Confidence distribution
        high_conf = sum(1 for a in annotations if a.confidence >= 0.8)
        medium_conf = sum(1 for a in annotations if 0.5 <= a.confidence < 0.8)
        low_conf = sum(1 for a in annotations if a.confidence < 0.5)

        return {
            "total_annotations": len(annotations),
            "by_type": by_type,
            "by_source": by_source,
            "average_confidence": round(avg_confidence, 4),
            "confidence_distribution": {
                "high": high_conf,
                "medium": medium_conf,
                "low": low_conf
            }
        }

    def export_validation_report(
        self,
        annotations: List[Annotation],
        expected_dimensions: Optional[Dict[str, float]] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export a validation report comparing detected vs expected dimensions.

        Useful for CI/CD pipelines to verify extraction accuracy.

        Args:
            annotations: Detected annotations
            expected_dimensions: Expected dimension values by name/feature_id
            output_path: Optional output path

        Returns:
            Validation report dictionary
        """
        report = {
            "version": self.VERSION,
            "timestamp": datetime.now().isoformat(),
            "total_detected": len(annotations),
            "validations": [],
            "summary": {
                "passed": 0,
                "failed": 0,
                "unmatched": 0
            }
        }

        if expected_dimensions:
            matched_features = set()

            for ann in annotations:
                if ann.feature_id and ann.feature_id in expected_dimensions:
                    expected = expected_dimensions[ann.feature_id]
                    actual = ann.value

                    if actual is not None:
                        diff = abs(actual - expected)
                        diff_pct = (diff / expected) * 100 if expected else 0
                        passed = diff_pct < 5.0  # 5% tolerance

                        report["validations"].append({
                            "feature_id": ann.feature_id,
                            "expected": expected,
                            "actual": actual,
                            "difference": round(diff, 4),
                            "difference_pct": round(diff_pct, 2),
                            "passed": passed,
                            "confidence": ann.confidence
                        })

                        if passed:
                            report["summary"]["passed"] += 1
                        else:
                            report["summary"]["failed"] += 1

                        matched_features.add(ann.feature_id)

            # Check for unmatched expected dimensions
            for feature_id in expected_dimensions:
                if feature_id not in matched_features:
                    report["validations"].append({
                        "feature_id": feature_id,
                        "expected": expected_dimensions[feature_id],
                        "actual": None,
                        "passed": False,
                        "reason": "not_detected"
                    })
                    report["summary"]["unmatched"] += 1

        # Calculate overall pass rate
        total = report["summary"]["passed"] + report["summary"]["failed"] + report["summary"]["unmatched"]
        if total > 0:
            report["summary"]["pass_rate"] = round(report["summary"]["passed"] / total, 4)
        else:
            report["summary"]["pass_rate"] = 1.0

        # Write if path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Validation report saved to {output_path}")

        return report


def load_annotations_from_json(json_path: str) -> List[Annotation]:
    """
    Load annotations from JSON file.

    Useful for testing or re-processing.

    Args:
        json_path: Path to JSON file

    Returns:
        List of Annotation objects
    """
    from .base import AnnotationType, AnnotationSource

    with open(json_path, 'r') as f:
        data = json.load(f)

    annotations = []

    for dim_data in data.get("dimensions", []):
        ann_type = dim_data.get("type", "linear_dimension")

        if ann_type == "linear_dimension":
            linear = dim_data.get("linear", {})
            ann = LinearDimension(
                text=dim_data.get("text", ""),
                value=dim_data.get("value"),
                unit=dim_data.get("unit", "mm"),
                confidence=dim_data.get("confidence", 0.0),
                feature_id=dim_data.get("feature_id"),
                point1=tuple(linear.get("point1", [0, 0])),
                point2=tuple(linear.get("point2", [0, 0])),
                source=AnnotationSource(dim_data.get("source", "ocr"))
            )
        elif ann_type == "radial_dimension":
            radial = dim_data.get("radial", {})
            ann = RadialDimension(
                text=dim_data.get("text", ""),
                value=dim_data.get("value"),
                unit=dim_data.get("unit", "mm"),
                confidence=dim_data.get("confidence", 0.0),
                feature_id=dim_data.get("feature_id"),
                center=tuple(radial.get("center", [0, 0])),
                radius=radial.get("radius"),
                is_diameter=radial.get("is_diameter", False),
                source=AnnotationSource(dim_data.get("source", "ocr"))
            )
        else:
            # Generic annotation
            ann = Annotation(
                type=AnnotationType(ann_type),
                text=dim_data.get("text", ""),
                value=dim_data.get("value"),
                confidence=dim_data.get("confidence", 0.0),
                feature_id=dim_data.get("feature_id"),
                source=AnnotationSource(dim_data.get("source", "ocr"))
            )

        annotations.append(ann)

    logger.info(f"Loaded {len(annotations)} annotations from {json_path}")
    return annotations
