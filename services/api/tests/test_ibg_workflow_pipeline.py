"""
Test IBG Workflow Pipeline
==========================

Tests the 7-stage workflow pipeline:
1. preserve_artifacts()
2. recover_topology()
3. isolate_candidates()
4. score_candidates()
5. wrap_candidates()
6. run_intake_gate()
7. emit_review_package()

Success condition: Given canonical DXF/SVG artifacts, produce
provenance-bearing, confidence-declared, gate-blocked
BodyEvidenceCandidate[] and a human-review package.
"""

import tempfile
from pathlib import Path

import pytest

from app.instrument_geometry.body.ibg.workflow import (
    IBGWorkflowPipeline,
    PipelineResult,
    preserve_artifacts,
    ContourCandidate,
    score_candidates,
    ScoredCandidate,
)
from app.instrument_geometry.body.ibg.workflow.topology_recovery import (
    compute_area,
    compute_perimeter,
    compute_bounding_box,
)


# Minimal DXF for testing (R12 format with LWPOLYLINE-like closed body contour)
MINIMAL_DXF = b"""0
SECTION
2
HEADER
9
$ACADVER
1
AC1009
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
8
0
10
0.0
20
0.0
11
200.0
21
0.0
0
LINE
8
0
10
200.0
20
0.0
11
200.0
21
400.0
0
LINE
8
0
10
200.0
20
400.0
11
0.0
21
400.0
0
LINE
8
0
10
0.0
20
400.0
11
0.0
21
0.0
0
ENDSEC
0
EOF
"""


class TestTopologyGeometry:
    """Test geometry computation utilities."""

    def test_compute_area_rectangle(self):
        """Rectangle area should be width * height."""
        points = [(0, 0), (100, 0), (100, 200), (0, 200)]
        area = compute_area(points)
        assert abs(area - 20000.0) < 0.1

    def test_compute_area_triangle(self):
        """Triangle area should be 0.5 * base * height."""
        points = [(0, 0), (100, 0), (50, 100)]
        area = compute_area(points)
        assert abs(area - 5000.0) < 0.1

    def test_compute_perimeter(self):
        """Perimeter of 100x200 rectangle should be 600."""
        points = [(0, 0), (100, 0), (100, 200), (0, 200), (0, 0)]
        perimeter = compute_perimeter(points)
        assert abs(perimeter - 600.0) < 0.1

    def test_compute_bounding_box(self):
        """Bounding box should capture min/max."""
        points = [(10, 20), (150, 50), (80, 300)]
        bbox = compute_bounding_box(points)
        assert bbox == (10, 20, 150, 300)


class TestCandidateScoring:
    """Test candidate scoring logic."""

    def test_score_closed_contour(self):
        """Closed guitar-shaped contour should score well."""
        # Create a guitar-body-like contour
        points = []
        # Lower bout (wider)
        for x in range(0, 180, 10):
            points.append((x, 0))
        # Right side going up
        for y in range(0, 450, 10):
            # Waist narrowing at y=200-250
            if 180 <= y <= 270:
                x_offset = 160 - (y - 180) * 0.3
            else:
                x_offset = 180 - abs(y - 225) * 0.1
            points.append((x_offset, y))
        # Upper bout (slightly narrower)
        for x in range(170, -10, -10):
            points.append((x, 450))
        # Left side going down
        for y in range(450, -10, -10):
            if 180 <= y <= 270:
                x_offset = 20 + (y - 180) * 0.3
            else:
                x_offset = 0 + abs(y - 225) * 0.1
            points.append((x_offset, y))

        contour = ContourCandidate(
            contour_id="test_body",
            points=points,
            is_closed=True,
            area_mm2=compute_area(points),
            perimeter_mm=compute_perimeter(points),
            bounding_box=compute_bounding_box(points),
            gap_distance=0.0,
            source_entities=1,
        )

        result = score_candidates([contour], top_n=1)

        assert len(result.candidates) == 1
        scored = result.candidates[0]
        assert scored.rank == 1
        assert scored.rank_score > 0.5  # Should score reasonably well
        assert scored.signals.closure_quality == 1.0  # Closed contour

    def test_score_open_contour_penalty(self):
        """Open contour should have lower closure_quality."""
        points = [(0, 0), (100, 0), (100, 200), (0, 200)]  # Not closed

        contour = ContourCandidate(
            contour_id="open_test",
            points=points,
            is_closed=False,
            area_mm2=0.0,
            perimeter_mm=compute_perimeter(points),
            bounding_box=compute_bounding_box(points),
            gap_distance=50.0,  # Large gap
            source_entities=4,
        )

        result = score_candidates([contour], top_n=1)
        scored = result.candidates[0]

        assert scored.signals.closure_quality < 0.5
        assert "large_gap" in scored.rejection_flags


class TestArtifactPreservation:
    """Test artifact preservation."""

    def test_preserve_dxf_bytes(self):
        """DXF bytes should be preserved with hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = preserve_artifacts(
                dxf_bytes=MINIMAL_DXF,
                source_filename="test.dxf",
                source_mode="pdf",
                artifact_id="test_001",
                output_dir=Path(tmpdir),
            )

            assert result.success
            assert len(result.artifacts) == 1

            artifact = result.artifacts[0]
            assert artifact.artifact_type == "dxf"
            assert artifact.byte_size == len(MINIMAL_DXF)
            assert len(artifact.artifact_hash) == 64  # SHA-256 hex

            # Verify file exists
            assert Path(artifact.artifact_path).exists()


class TestWorkflowPipeline:
    """Test the complete workflow pipeline."""

    def test_pipeline_with_minimal_dxf(self):
        """Pipeline should process minimal DXF through all stages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch output directories
            import app.instrument_geometry.body.ibg.workflow.artifact_preservation as ap
            import app.instrument_geometry.body.ibg.workflow.review_package as rp

            original_artifacts_dir = ap.WORKFLOW_1A_ARTIFACTS_DIR
            original_packages_dir = rp.REVIEW_PACKAGES_DIR

            ap.WORKFLOW_1A_ARTIFACTS_DIR = Path(tmpdir) / "artifacts"
            rp.REVIEW_PACKAGES_DIR = Path(tmpdir) / "review_packages"

            try:
                pipeline = IBGWorkflowPipeline(
                    top_n_candidates=3,
                    endpoint_tolerance=2.0,
                )

                result = pipeline.run(
                    dxf_bytes=MINIMAL_DXF,
                    source_filename="minimal_body.dxf",
                    source_mode="pdf",
                    pipeline_id="test_pipeline_001",
                )

                # Check pipeline result
                assert isinstance(result, PipelineResult)
                assert result.pipeline_id == "test_pipeline_001"

                # Check stages executed
                stage_names = [s.stage for s in result.stages]
                assert "preserve_artifacts" in stage_names
                assert "recover_topology" in stage_names

                # Check artifacts preserved
                assert len(result.artifacts) >= 1
                assert result.artifacts[0].artifact_type == "dxf"

                # If topology recovery succeeded, check downstream stages
                if result.success:
                    assert len(result.candidates) > 0
                    assert len(result.gate_results) > 0

                    # Check candidates have constitutional properties
                    for candidate in result.candidates:
                        assert candidate.authority_state is not None
                        assert candidate.provenance is not None
                        assert candidate.confidence is not None

                    # Check review package
                    if result.review_package:
                        assert result.review_package.package_id == "test_pipeline_001"
                        assert len(result.review_package.candidate_summaries) > 0

            finally:
                # Restore original paths
                ap.WORKFLOW_1A_ARTIFACTS_DIR = original_artifacts_dir
                rp.REVIEW_PACKAGES_DIR = original_packages_dir

    def test_pipeline_result_to_dict(self):
        """Pipeline result should serialize to dict."""
        result = PipelineResult(
            success=True,
            pipeline_id="test_dict",
            stages=[],
            artifacts=[],
            candidates=[],
            gate_results=[],
        )

        d = result.to_dict()
        assert d["success"] is True
        assert d["pipeline_id"] == "test_dict"
        assert "stage_count" in d
        assert "artifact_count" in d
        assert "candidate_count" in d


class TestIntakeGateEnforcement:
    """Test that IBGIntakeGate enforces constitutional requirements."""

    def test_gate_blocks_without_review(self):
        """Gate should block candidates that require review."""
        from app.instrument_geometry.body.ibg.body_evidence_candidate import (
            BodyEvidenceCandidate,
            create_candidate_from_evidence,
        )
        from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import (
            BodyEvidence,
            EvidenceSource,
        )
        from app.instrument_geometry.body.ibg.ibg_intake_gate import (
            create_default_intake_gate,
            IntakeRejectionReason,
        )

        # Create minimal evidence
        evidence = BodyEvidence(
            outline_points=[(0, 0), (100, 0), (100, 200), (0, 200)],
            contour_segments=[],
            source_type=EvidenceSource.VECTORIZER_DXF,
        )

        # Create candidate (starts in PROPOSED state requiring review)
        candidate = create_candidate_from_evidence(
            evidence=evidence,
            source_artifact="test.dxf",
            extraction_method="test",
        )

        # Gate should block
        gate = create_default_intake_gate()
        result = gate.validate(candidate)

        assert result.is_valid is False
        assert IntakeRejectionReason.REVIEW_REQUIRED in result.rejections


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
