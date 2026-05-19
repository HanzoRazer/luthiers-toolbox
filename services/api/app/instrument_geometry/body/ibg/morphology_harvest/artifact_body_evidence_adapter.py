"""
Artifact → BodyEvidenceCandidate Adapter
=========================================

Bridges canonical vectorizer artifacts (DXF/SVG) to BodyEvidenceCandidate.

This is the core E-2-E spine component that converts:
- DXF base64 from /api/blueprint/vectorize/async
- SVG content as fallback/review artifact

into BodyEvidenceCandidate for IBG intake with full constitutional metadata:
- ProvenanceRecord (source lineage)
- AuthorityState (advisory_candidate or sandbox_experimental)
- ConfidenceDeclaration (typed confidence)
- ReviewEnforcement (review_required = True)

DEV ORDER 2A: Constitutional Adapter Integration

Author: Production Shop
Date: 2026-05-18
Sprint: IBG Constitutional Adapter Integration
"""

from __future__ import annotations

import base64
import io
import logging
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from uuid import uuid4

import ezdxf

from app.governance import (
    AuthorityState,
    TransformationStage,
    ConfidenceType,
    create_source_provenance,
    create_heuristic_confidence,
)

from ..body_evidence_candidate import (
    BodyEvidenceCandidate,
    create_candidate_from_evidence,
)

from ..ibg_intake_gate import (
    IBGIntakeGate,
    IntakeValidationResult,
    create_default_intake_gate,
)

from ..body_grid.body_grid_schema import (
    BodyEvidence,
    ContourSegment,
    Landmark,
    NormalizedPoint,
    RawCoordinate,
    CoordinateSpace,
    EvidenceSource,
)

logger = logging.getLogger(__name__)


@dataclass
class ArtifactMetadata:
    """Metadata about the source artifact."""
    source_file: str
    source_mode: str  # "pdf" or "photo"
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    entity_count: int = 0
    closed_contours: int = 0
    scale_status: str = "provisional_from_vectorizer_artifact"


@dataclass
class ParsedArtifact:
    """Result of parsing DXF/SVG artifact."""
    outline_points: List[Tuple[float, float]] = field(default_factory=list)
    contour_segments: List[List[Tuple[float, float]]] = field(default_factory=list)
    bounding_box: Optional[Tuple[float, float, float, float]] = None  # min_x, min_y, max_x, max_y
    metadata: Optional[ArtifactMetadata] = None
    svg_content: Optional[str] = None
    dxf_content: Optional[bytes] = None
    parse_errors: List[str] = field(default_factory=list)


class ArtifactBodyEvidenceAdapter:
    """
    Adapter that converts canonical vectorizer artifacts into BodyEvidence.

    Primary path: DXF → BodyEvidence
    Fallback: SVG → BodyEvidence (visual review artifact)

    Usage:
        adapter = ArtifactBodyEvidenceAdapter()

        # From vectorizer response
        result = adapter.from_vectorizer_response(
            dxf_base64="...",
            svg_content="...",
            dimensions={"width_mm": 350, "height_mm": 450},
            source_file="les_paul.pdf",
            source_mode="pdf"
        )

        # Access BodyEvidence
        evidence = result.body_evidence
    """

    def __init__(self):
        self.parse_log: List[str] = []

    def from_vectorizer_response(
        self,
        dxf_base64: Optional[str] = None,
        svg_content: Optional[str] = None,
        dimensions: Optional[Dict[str, float]] = None,
        source_file: str = "unknown",
        source_mode: str = "pdf",
    ) -> "AdapterResult":
        """
        Convert vectorizer response to BodyEvidence.

        Args:
            dxf_base64: Base64-encoded DXF content (preferred)
            svg_content: SVG content (fallback/review)
            dimensions: {"width_mm": float, "height_mm": float}
            source_file: Original source file name
            source_mode: "pdf" or "photo"

        Returns:
            AdapterResult with BodyEvidence and metadata
        """
        self.parse_log = []

        metadata = ArtifactMetadata(
            source_file=source_file,
            source_mode=source_mode,
            width_mm=dimensions.get("width_mm") if dimensions else None,
            height_mm=dimensions.get("height_mm") if dimensions else None,
        )

        parsed = None

        # Prefer DXF path
        if dxf_base64:
            self.parse_log.append("Attempting DXF parse (primary path)")
            parsed = self._parse_dxf_base64(dxf_base64, metadata)

            if parsed.parse_errors:
                self.parse_log.extend(parsed.parse_errors)

        # SVG fallback
        if (not parsed or not parsed.outline_points) and svg_content:
            self.parse_log.append("Falling back to SVG parse")
            parsed = self._parse_svg_content(svg_content, metadata)

        if not parsed:
            return AdapterResult(
                success=False,
                body_evidence=None,
                metadata=metadata,
                errors=["No parseable artifact provided"],
            )

        # Store artifacts
        parsed.svg_content = svg_content
        if dxf_base64:
            parsed.dxf_content = base64.b64decode(dxf_base64)

        # Convert to BodyEvidence
        evidence = self._to_body_evidence(parsed, metadata)

        return AdapterResult(
            success=True,
            body_evidence=evidence,
            parsed_artifact=parsed,
            metadata=metadata,
            errors=parsed.parse_errors if parsed.parse_errors else None,
        )

    def _parse_dxf_base64(
        self,
        dxf_base64: str,
        metadata: ArtifactMetadata,
    ) -> ParsedArtifact:
        """Parse DXF from base64-encoded content."""
        result = ParsedArtifact(metadata=metadata)

        try:
            dxf_bytes = base64.b64decode(dxf_base64)

            # Write to temp file for ezdxf
            with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as f:
                f.write(dxf_bytes)
                temp_path = f.name

            try:
                doc = ezdxf.readfile(temp_path)
                msp = doc.modelspace()

                all_points = []
                contours = []
                entity_count = 0
                closed_count = 0

                for entity in msp:
                    entity_count += 1
                    points = self._entity_to_points(entity)

                    if points:
                        contours.append(points)
                        all_points.extend(points)

                        # Check if closed
                        if len(points) >= 3:
                            first, last = points[0], points[-1]
                            dist = ((first[0] - last[0])**2 + (first[1] - last[1])**2)**0.5
                            if dist < 1.0:  # Within 1mm
                                closed_count += 1

                result.outline_points = all_points
                result.contour_segments = contours

                # Compute bounding box
                if all_points:
                    xs = [p[0] for p in all_points]
                    ys = [p[1] for p in all_points]
                    result.bounding_box = (min(xs), min(ys), max(xs), max(ys))

                metadata.entity_count = entity_count
                metadata.closed_contours = closed_count

                self.parse_log.append(f"DXF parsed: {entity_count} entities, {len(contours)} contours, {closed_count} closed")

            finally:
                Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            result.parse_errors.append(f"DXF parse error: {e}")
            logger.exception("DXF parsing failed")

        return result

    def _entity_to_points(self, entity) -> List[Tuple[float, float]]:
        """Convert DXF entity to list of points."""
        points = []

        try:
            dxf_type = entity.dxftype()

            if dxf_type == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                points = [(start.x, start.y), (end.x, end.y)]

            elif dxf_type == 'LWPOLYLINE':
                points = [(p[0], p[1]) for p in entity.get_points()]
                if entity.closed and points:
                    points.append(points[0])

            elif dxf_type == 'POLYLINE':
                points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                if entity.is_closed and points:
                    points.append(points[0])

            elif dxf_type == 'CIRCLE':
                import math
                cx, cy = entity.dxf.center.x, entity.dxf.center.y
                r = entity.dxf.radius
                # Approximate circle with 64 points
                for i in range(65):
                    angle = 2 * math.pi * i / 64
                    points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

            elif dxf_type == 'ARC':
                import math
                cx, cy = entity.dxf.center.x, entity.dxf.center.y
                r = entity.dxf.radius
                start_angle = math.radians(entity.dxf.start_angle)
                end_angle = math.radians(entity.dxf.end_angle)

                if end_angle < start_angle:
                    end_angle += 2 * math.pi

                # Approximate arc with proportional points
                arc_len = end_angle - start_angle
                num_pts = max(8, int(arc_len / (math.pi / 16)))  # ~16 pts per 180°

                for i in range(num_pts + 1):
                    angle = start_angle + (arc_len * i / num_pts)
                    points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

            elif dxf_type == 'SPLINE':
                # Use control points as approximation
                points = [(p[0], p[1]) for p in entity.control_points]

        except Exception as e:
            logger.debug(f"Entity conversion failed for {entity.dxftype()}: {e}")

        return points

    def _parse_svg_content(
        self,
        svg_content: str,
        metadata: ArtifactMetadata,
    ) -> ParsedArtifact:
        """Parse SVG content for points (fallback path)."""
        result = ParsedArtifact(metadata=metadata)

        try:
            import re

            # Extract path d attribute
            path_match = re.search(r'd="([^"]+)"', svg_content)
            if not path_match:
                result.parse_errors.append("No path found in SVG")
                return result

            path_d = path_match.group(1)
            points = self._parse_svg_path(path_d)

            if points:
                result.outline_points = points
                result.contour_segments = [points]

                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                result.bounding_box = (min(xs), min(ys), max(xs), max(ys))

                self.parse_log.append(f"SVG parsed: {len(points)} points from path")
            else:
                result.parse_errors.append("No points extracted from SVG path")

        except Exception as e:
            result.parse_errors.append(f"SVG parse error: {e}")

        return result

    def _parse_svg_path(self, path_d: str) -> List[Tuple[float, float]]:
        """Parse SVG path d attribute into points."""
        import re

        points = []
        current = [0.0, 0.0]

        # Simple parser for M, L, Z commands
        commands = re.findall(r'([MLZmlz])\s*([-\d.,\s]*)', path_d)

        for cmd, args in commands:
            coords = [float(x) for x in re.findall(r'-?\d+\.?\d*', args)]

            if cmd == 'M':  # Move absolute
                if len(coords) >= 2:
                    current = [coords[0], coords[1]]
                    points.append(tuple(current))

            elif cmd == 'm':  # Move relative
                if len(coords) >= 2:
                    current[0] += coords[0]
                    current[1] += coords[1]
                    points.append(tuple(current))

            elif cmd == 'L':  # Line absolute
                for i in range(0, len(coords), 2):
                    if i + 1 < len(coords):
                        current = [coords[i], coords[i+1]]
                        points.append(tuple(current))

            elif cmd == 'l':  # Line relative
                for i in range(0, len(coords), 2):
                    if i + 1 < len(coords):
                        current[0] += coords[i]
                        current[1] += coords[i+1]
                        points.append(tuple(current))

            elif cmd in ('Z', 'z'):  # Close path
                if points:
                    points.append(points[0])

        return points

    def _to_body_evidence(
        self,
        parsed: ParsedArtifact,
        metadata: ArtifactMetadata,
    ) -> BodyEvidence:
        """Convert ParsedArtifact to BodyEvidence."""

        # Determine body dimensions for normalization
        if parsed.bounding_box:
            min_x, min_y, max_x, max_y = parsed.bounding_box
            body_width = max_x - min_x
            body_height = max_y - min_y
            centerline_x = (min_x + max_x) / 2
        else:
            body_width = metadata.width_mm or 350.0
            body_height = metadata.height_mm or 450.0
            centerline_x = body_width / 2
            min_x, min_y = 0.0, 0.0

        # Normalize points (x relative to centerline, y from 0=butt to 1=neck)
        def normalize_point(x: float, y: float) -> NormalizedPoint:
            x_norm = (x - centerline_x) / (body_width / 2) if body_width > 0 else 0.0
            y_norm = (y - min_y) / body_height if body_height > 0 else 0.0

            return NormalizedPoint(
                x_norm=x_norm,
                y_norm=y_norm,
                raw=RawCoordinate(x=x, y=y, space=CoordinateSpace.RAW_MM),
                confidence=0.7,
            )

        # Convert contour segments
        contour_segments = []
        for segment_points in parsed.contour_segments:
            if len(segment_points) >= 2:
                normalized = [normalize_point(p[0], p[1]) for p in segment_points]

                # Check if closed
                is_closed = False
                if len(segment_points) >= 3:
                    first, last = segment_points[0], segment_points[-1]
                    dist = ((first[0] - last[0])**2 + (first[1] - last[1])**2)**0.5
                    is_closed = dist < 1.0

                contour_segments.append(ContourSegment(
                    points=normalized,
                    is_closed=is_closed,
                    side="unknown",
                    source=EvidenceSource.VECTORIZER_DXF,
                ))

        # Extract landmarks from bounding box
        landmarks = []
        if parsed.bounding_box:
            min_x, min_y, max_x, max_y = parsed.bounding_box

            # Butt center (bottom)
            landmarks.append(Landmark(
                label="butt_center",
                point=normalize_point(centerline_x, min_y),
                source=EvidenceSource.VECTORIZER_DXF,
                confidence=0.6,
            ))

            # Neck center (top)
            landmarks.append(Landmark(
                label="neck_center",
                point=normalize_point(centerline_x, max_y),
                source=EvidenceSource.VECTORIZER_DXF,
                confidence=0.6,
            ))

        # Build source transform
        source_transform = {
            "centerline_x_mm": centerline_x,
            "body_width_mm": body_width,
            "body_height_mm": body_height,
            "min_x_mm": min_x if parsed.bounding_box else 0.0,
            "min_y_mm": min_y if parsed.bounding_box else 0.0,
        }

        return BodyEvidence(
            outline_points=parsed.outline_points,
            contour_segments=contour_segments,
            landmarks=landmarks,
            source_type=EvidenceSource.VECTORIZER_DXF,
            source_transform=source_transform,
            bounding_box_mm=parsed.bounding_box,
            centerline_x_mm=centerline_x,
        )

    def from_vectorizer_response_constitutional(
        self,
        dxf_base64: Optional[str] = None,
        svg_content: Optional[str] = None,
        dimensions: Optional[Dict[str, float]] = None,
        source_file: str = "unknown",
        source_mode: str = "pdf",
    ) -> "ConstitutionalAdapterResult":
        """
        Convert vectorizer response to BodyEvidenceCandidate with constitutional metadata.

        This is the primary entry point for IBG intake. Produces a candidate that:
        - Has full provenance chain
        - Defaults to advisory_candidate (or sandbox_experimental if poor quality)
        - Has review_required = True
        - Has approved_for_ibg_memory = False
        - Is validated against IBGIntakeGate (expected: blocked)

        Args:
            dxf_base64: Base64-encoded DXF content (preferred)
            svg_content: SVG content (fallback/review)
            dimensions: {"width_mm": float, "height_mm": float}
            source_file: Original source file name
            source_mode: "pdf" or "photo"

        Returns:
            ConstitutionalAdapterResult with BodyEvidenceCandidate and gate result
        """
        # First, parse and create BodyEvidence using existing method
        basic_result = self.from_vectorizer_response(
            dxf_base64=dxf_base64,
            svg_content=svg_content,
            dimensions=dimensions,
            source_file=source_file,
            source_mode=source_mode,
        )

        if not basic_result.success or not basic_result.body_evidence:
            return ConstitutionalAdapterResult(
                success=False,
                candidate=None,
                metadata=basic_result.metadata,
                errors=basic_result.errors or ["Failed to create BodyEvidence"],
            )

        # Compute topology integrity from parsing quality
        topology_integrity = self._compute_topology_integrity(
            basic_result.parsed_artifact,
            basic_result.metadata,
        )

        # Create BodyEvidenceCandidate with provenance
        candidate = create_candidate_from_evidence(
            evidence=basic_result.body_evidence,
            source_artifact=source_file,
            extraction_method="artifact_body_evidence_adapter",
            extraction_params={
                "source_mode": source_mode,
                "has_dxf": dxf_base64 is not None,
                "has_svg": svg_content is not None,
                "entity_count": basic_result.metadata.entity_count if basic_result.metadata else 0,
                "closed_contours": basic_result.metadata.closed_contours if basic_result.metadata else 0,
            },
            confidence_value=self._compute_confidence_value(basic_result.parsed_artifact),
            confidence_origin="artifact_body_evidence_adapter",
        )

        # Record topology integrity in provenance
        if candidate.provenance and topology_integrity < 1.0:
            degradation_reason = self._get_degradation_reason(
                basic_result.parsed_artifact,
                basic_result.metadata,
            )
            candidate.provenance.record_topology_degradation(
                topology_integrity,
                degradation_reason,
            )

        # Downgrade to sandbox_experimental if topology is poor
        if topology_integrity < 0.5:
            candidate.authority._current_state = AuthorityState.SANDBOX_EXPERIMENTAL
            if candidate.provenance:
                candidate.provenance.add_transformation(
                    stage=TransformationStage.SEMANTIC_CLASSIFICATION,
                    method="authority_downgrade",
                    params={
                        "reason": "poor_topology_integrity",
                        "integrity_score": topology_integrity,
                    },
                    actor="system:artifact_body_evidence_adapter",
                )

        # Validate against IBGIntakeGate (expect blocked)
        gate = create_default_intake_gate()
        gate_result = gate.validate(candidate)

        return ConstitutionalAdapterResult(
            success=True,
            candidate=candidate,
            gate_result=gate_result,
            parsed_artifact=basic_result.parsed_artifact,
            metadata=basic_result.metadata,
            topology_integrity=topology_integrity,
            errors=basic_result.errors,
        )

    def _compute_topology_integrity(
        self,
        parsed: Optional[ParsedArtifact],
        metadata: Optional[ArtifactMetadata],
    ) -> float:
        """
        Compute topology integrity score from parsing quality.

        Factors:
        - Presence of closed contours (good)
        - Parse errors (bad)
        - Entity count vs closed count ratio
        - Bounding box presence

        Returns:
            Float 0.0-1.0 where 1.0 is perfect topology
        """
        if not parsed:
            return 0.0

        score = 1.0

        # Penalize parse errors
        if parsed.parse_errors:
            score -= 0.2 * len(parsed.parse_errors)

        # Penalize missing bounding box
        if not parsed.bounding_box:
            score -= 0.3

        # Penalize no outline points
        if not parsed.outline_points:
            score -= 0.5

        # Penalize low closed contour ratio
        if metadata and metadata.entity_count > 0:
            closed_ratio = metadata.closed_contours / metadata.entity_count
            if closed_ratio < 0.5:
                score -= 0.2 * (1 - closed_ratio)

        # Penalize few contour segments
        if len(parsed.contour_segments) < 1:
            score -= 0.3

        return max(0.0, min(1.0, score))

    def _compute_confidence_value(
        self,
        parsed: Optional[ParsedArtifact],
    ) -> float:
        """
        Compute confidence value from parsing quality.

        Higher confidence for:
        - More points
        - Closed contours
        - No parse errors
        """
        if not parsed:
            return 0.0

        base = 0.5

        # Boost for points
        if parsed.outline_points:
            point_count = len(parsed.outline_points)
            if point_count > 100:
                base += 0.2
            elif point_count > 20:
                base += 0.1

        # Boost for closed contours
        if parsed.contour_segments:
            closed_count = sum(
                1 for seg in parsed.contour_segments
                if len(seg) >= 3 and self._is_closed_segment(seg)
            )
            if closed_count > 0:
                base += 0.1

        # Penalize parse errors
        if parsed.parse_errors:
            base -= 0.1 * len(parsed.parse_errors)

        return max(0.0, min(1.0, base))

    def _is_closed_segment(self, segment: List[Tuple[float, float]]) -> bool:
        """Check if a segment is closed (first ~= last point)."""
        if len(segment) < 3:
            return False
        first, last = segment[0], segment[-1]
        dist = ((first[0] - last[0])**2 + (first[1] - last[1])**2)**0.5
        return dist < 1.0

    def _get_degradation_reason(
        self,
        parsed: Optional[ParsedArtifact],
        metadata: Optional[ArtifactMetadata],
    ) -> str:
        """Get human-readable reason for topology degradation."""
        reasons = []

        if parsed and parsed.parse_errors:
            reasons.append(f"{len(parsed.parse_errors)} parse errors")

        if not parsed or not parsed.bounding_box:
            reasons.append("missing bounding box")

        if not parsed or not parsed.outline_points:
            reasons.append("no outline points extracted")

        if metadata and metadata.entity_count > 0:
            closed_ratio = metadata.closed_contours / metadata.entity_count
            if closed_ratio < 0.5:
                reasons.append(f"low closed contour ratio ({closed_ratio:.0%})")

        return "; ".join(reasons) if reasons else "unknown degradation"


@dataclass
class AdapterResult:
    """Result of artifact-to-evidence conversion."""
    success: bool
    body_evidence: Optional[BodyEvidence]
    parsed_artifact: Optional[ParsedArtifact] = None
    metadata: Optional[ArtifactMetadata] = None
    errors: Optional[List[str]] = None


@dataclass
class ConstitutionalAdapterResult:
    """
    Result of constitutional artifact-to-candidate conversion.

    Includes:
    - BodyEvidenceCandidate with full provenance
    - IBGIntakeGate validation result
    - Review-ready JSON output
    """
    success: bool
    candidate: Optional[BodyEvidenceCandidate]
    gate_result: Optional[IntakeValidationResult] = None
    parsed_artifact: Optional[ParsedArtifact] = None
    metadata: Optional[ArtifactMetadata] = None
    topology_integrity: float = 1.0
    errors: Optional[List[str]] = None

    def to_review_json(self) -> Dict[str, Any]:
        """
        Generate review-ready JSON output.

        Contains all information needed for human review decision.
        """
        if not self.candidate:
            return {
                "success": False,
                "errors": self.errors or ["No candidate produced"],
            }

        return {
            "candidate_id": self.candidate.candidate_id,
            "source_dxf": self.candidate.provenance.source_artifact if self.candidate.provenance else None,
            "provenance": self.candidate.provenance.to_dict() if self.candidate.provenance else None,
            "authority_state": self.candidate.authority_state.value,
            "confidence_declaration": self.candidate.confidence.to_dict(),
            "topology_integrity": self.topology_integrity,
            "gate_decision": {
                "is_valid": self.gate_result.is_valid if self.gate_result else False,
                "rejections": [r.value for r in self.gate_result.rejections] if self.gate_result else [],
                "gate_results": self.gate_result.gate_results if self.gate_result else {},
            },
            "review_required": self.candidate.review_required,
            "review_notes_placeholder": "",
            "created_at": self.candidate.created_at.isoformat(),
            "metadata": {
                "source_file": self.metadata.source_file if self.metadata else None,
                "source_mode": self.metadata.source_mode if self.metadata else None,
                "entity_count": self.metadata.entity_count if self.metadata else 0,
                "closed_contours": self.metadata.closed_contours if self.metadata else 0,
                "parse_errors": self.errors or [],
            },
        }
