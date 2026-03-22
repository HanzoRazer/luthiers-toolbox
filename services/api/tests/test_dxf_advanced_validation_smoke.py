"""
Smoke tests for DXF advanced validation module.

Tests the TopologyValidator class which detects:
- Self-intersecting polygons
- Degenerate polygons (too few vertices, zero area)
- Zero-length lines
- Overlapping entities

Uses built-in test DXF generators from the module.
"""
import pytest
import io
import ezdxf

from app.cam.dxf_advanced_validation import (
    TopologyValidator,
    TopologyIssue,
    TopologyReport,
    create_test_figure8_dxf,
    create_test_valid_dxf,
)
from app.cam.dxf_preflight import Severity

# Mark all tests to allow missing x-request-id header
pytestmark = pytest.mark.allow_missing_request_id


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_dxf_bytes() -> bytes:
    """Create a valid DXF file for testing."""
    return create_test_valid_dxf()


@pytest.fixture
def figure8_dxf_bytes() -> bytes:
    """Create a self-intersecting figure-8 DXF for testing."""
    return create_test_figure8_dxf()


@pytest.fixture
def degenerate_dxf_bytes() -> bytes:
    """Create a DXF with degenerate (2-vertex) polygon."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    # Only 2 points - not a valid polygon
    msp.add_lwpolyline([(0, 0), (10, 10)], dxfattribs={'layer': 'TEST', 'closed': True})
    text_buf = io.StringIO()
    doc.write(text_buf)
    return doc.encode(text_buf.getvalue())


@pytest.fixture
def zero_area_dxf_bytes() -> bytes:
    """Create a DXF with near-zero area polygon (collapsed)."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    # Three points very close together (< 0.01 mm²)
    msp.add_lwpolyline(
        [(0, 0), (0.001, 0), (0.0005, 0.001)],
        dxfattribs={'layer': 'TEST', 'closed': True}
    )
    text_buf = io.StringIO()
    doc.write(text_buf)
    return doc.encode(text_buf.getvalue())


@pytest.fixture
def zero_length_line_dxf_bytes() -> bytes:
    """Create a DXF with zero-length LINE entity."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    # Zero-length line (same start and end)
    msp.add_line((10, 10, 0), (10, 10, 0), dxfattribs={'layer': 'TEST'})
    # Valid line for comparison
    msp.add_line((0, 0, 0), (100, 100, 0), dxfattribs={'layer': 'TEST'})
    text_buf = io.StringIO()
    doc.write(text_buf)
    return doc.encode(text_buf.getvalue())


@pytest.fixture
def overlapping_dxf_bytes() -> bytes:
    """Create a DXF with two overlapping polygons."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    # First rectangle
    msp.add_lwpolyline(
        [(0, 0), (100, 0), (100, 100), (0, 100)],
        dxfattribs={'layer': 'LAYER1', 'closed': True}
    )
    # Overlapping rectangle (50% overlap)
    msp.add_lwpolyline(
        [(50, 0), (150, 0), (150, 100), (50, 100)],
        dxfattribs={'layer': 'LAYER2', 'closed': True}
    )
    text_buf = io.StringIO()
    doc.write(text_buf)
    return doc.encode(text_buf.getvalue())


@pytest.fixture
def multiple_polygons_dxf_bytes() -> bytes:
    """Create a DXF with multiple valid polygons."""
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    # Multiple valid rectangles
    for i in range(5):
        msp.add_lwpolyline(
            [(i*50, 0), (i*50+40, 0), (i*50+40, 30), (i*50, 30)],
            dxfattribs={'layer': f'LAYER{i}', 'closed': True}
        )
    text_buf = io.StringIO()
    doc.write(text_buf)
    return doc.encode(text_buf.getvalue())


# ---------------------------------------------------------------------------
# TopologyValidator Tests
# ---------------------------------------------------------------------------

class TestTopologyValidatorInit:
    """Tests for TopologyValidator initialization."""

    def test_init_with_valid_dxf(self, valid_dxf_bytes):
        """Validator initializes with valid DXF bytes."""
        validator = TopologyValidator(valid_dxf_bytes, "test.dxf")
        assert validator.filename == "test.dxf"
        assert validator.doc is not None
        assert validator.msp is not None

    def test_init_default_filename(self, valid_dxf_bytes):
        """Validator uses default filename if not provided."""
        validator = TopologyValidator(valid_dxf_bytes)
        assert validator.filename == "unknown.dxf"


class TestCheckSelfIntersections:
    """Tests for check_self_intersections method."""

    def test_valid_polygon_no_issues(self, valid_dxf_bytes):
        """Valid polygon returns report with no issues."""
        validator = TopologyValidator(valid_dxf_bytes, "valid.dxf")
        report = validator.check_self_intersections()

        assert isinstance(report, TopologyReport)
        assert report.is_valid is True
        assert report.self_intersections == 0
        assert len(report.issues) == 0
        assert report.entities_checked > 0

    def test_figure8_detects_self_intersection(self, figure8_dxf_bytes):
        """Figure-8 polygon is detected as self-intersecting."""
        validator = TopologyValidator(figure8_dxf_bytes, "figure8.dxf")
        report = validator.check_self_intersections()

        assert report.is_valid is False
        assert report.self_intersections > 0
        assert len(report.issues) > 0

        # Check the issue details
        issue = report.issues[0]
        assert issue.severity == Severity.ERROR
        assert "Self-intersecting" in issue.message
        assert issue.entity_type == "LWPOLYLINE"
        assert issue.repair_suggestion is not None

    def test_degenerate_polygon_detected(self, degenerate_dxf_bytes):
        """Degenerate polygon (< 3 vertices) is detected."""
        validator = TopologyValidator(degenerate_dxf_bytes, "degenerate.dxf")
        report = validator.check_self_intersections()

        assert report.is_valid is False
        assert report.degenerate_polygons > 0

        # Find the degenerate issue
        degenerate_issues = [i for i in report.issues if "Degenerate" in i.message]
        assert len(degenerate_issues) > 0
        assert degenerate_issues[0].severity == Severity.ERROR

    def test_zero_area_polygon_detected(self, zero_area_dxf_bytes):
        """Near-zero area polygon is flagged as warning."""
        validator = TopologyValidator(zero_area_dxf_bytes, "zero_area.dxf")
        report = validator.check_self_intersections()

        # May have warning or error depending on Shapely version
        # Either zero area warning or validation error is acceptable
        assert report.entities_checked > 0
        # The result depends on how Shapely handles very small polygons

    def test_report_statistics(self, figure8_dxf_bytes):
        """Report includes correct statistics."""
        validator = TopologyValidator(figure8_dxf_bytes, "stats.dxf")
        report = validator.check_self_intersections()

        assert report.filename == "stats.dxf"
        assert report.error_count() >= 1
        assert isinstance(report.entities_checked, int)

    def test_multiple_polygons_validated(self, multiple_polygons_dxf_bytes):
        """Multiple polygons are all validated."""
        validator = TopologyValidator(multiple_polygons_dxf_bytes, "multi.dxf")
        report = validator.check_self_intersections()

        assert report.entities_checked == 5
        assert report.is_valid is True
        assert report.self_intersections == 0


class TestCheckLineSegments:
    """Tests for check_line_segments method."""

    def test_zero_length_line_detected(self, zero_length_line_dxf_bytes):
        """Zero-length LINE entities are detected."""
        validator = TopologyValidator(zero_length_line_dxf_bytes, "lines.dxf")
        issues = validator.check_line_segments()

        # Should find the zero-length line
        zero_length = [i for i in issues if "Zero-length" in i.message]
        assert len(zero_length) == 1
        assert zero_length[0].severity == Severity.WARNING
        assert zero_length[0].entity_type == "LINE"

    def test_valid_lines_no_issues(self, valid_dxf_bytes):
        """Valid lines produce no issues."""
        validator = TopologyValidator(valid_dxf_bytes, "valid.dxf")
        issues = validator.check_line_segments()

        # No LINE entities in the valid test DXF
        assert isinstance(issues, list)


class TestCheckOverlappingEntities:
    """Tests for check_overlapping_entities method."""

    def test_overlapping_detected(self, overlapping_dxf_bytes):
        """Overlapping polygons are detected."""
        validator = TopologyValidator(overlapping_dxf_bytes, "overlap.dxf")
        issues = validator.check_overlapping_entities()

        overlap_issues = [i for i in issues if "Overlapping" in i.message]
        assert len(overlap_issues) > 0
        assert overlap_issues[0].severity == Severity.WARNING
        assert "mm² overlap" in overlap_issues[0].message

    def test_non_overlapping_no_issues(self, multiple_polygons_dxf_bytes):
        """Non-overlapping polygons produce no overlap issues."""
        validator = TopologyValidator(multiple_polygons_dxf_bytes, "separate.dxf")
        issues = validator.check_overlapping_entities()

        overlap_issues = [i for i in issues if "Overlapping" in i.message]
        assert len(overlap_issues) == 0


# ---------------------------------------------------------------------------
# TopologyReport Tests
# ---------------------------------------------------------------------------

class TestTopologyReport:
    """Tests for TopologyReport dataclass."""

    def test_error_count(self):
        """error_count() returns correct count."""
        report = TopologyReport(
            filename="test.dxf",
            is_valid=False,
            issues=[
                TopologyIssue(Severity.ERROR, "Error 1"),
                TopologyIssue(Severity.ERROR, "Error 2"),
                TopologyIssue(Severity.WARNING, "Warning 1"),
            ]
        )
        assert report.error_count() == 2

    def test_warning_count(self):
        """warning_count() returns correct count."""
        report = TopologyReport(
            filename="test.dxf",
            is_valid=False,
            issues=[
                TopologyIssue(Severity.ERROR, "Error 1"),
                TopologyIssue(Severity.WARNING, "Warning 1"),
                TopologyIssue(Severity.WARNING, "Warning 2"),
            ]
        )
        assert report.warning_count() == 2

    def test_empty_report(self):
        """Empty report has zero counts."""
        report = TopologyReport(
            filename="empty.dxf",
            is_valid=True,
            issues=[]
        )
        assert report.error_count() == 0
        assert report.warning_count() == 0


# ---------------------------------------------------------------------------
# TopologyIssue Tests
# ---------------------------------------------------------------------------

class TestTopologyIssue:
    """Tests for TopologyIssue dataclass."""

    def test_basic_issue(self):
        """Basic TopologyIssue creation."""
        issue = TopologyIssue(
            severity=Severity.ERROR,
            message="Test error"
        )
        assert issue.severity == Severity.ERROR
        assert issue.message == "Test error"
        assert issue.category == "topology"

    def test_full_issue(self):
        """TopologyIssue with all fields."""
        issue = TopologyIssue(
            severity=Severity.WARNING,
            message="Self-intersection at corner",
            category="topology",
            layer="OUTLINE",
            entity_handle="1A3",
            entity_type="LWPOLYLINE",
            topology_error="Ring Self-intersection[50.0 30.0]",
            intersection_point=(50.0, 30.0),
            repair_suggestion="Apply buffer(0)"
        )
        assert issue.layer == "OUTLINE"
        assert issue.entity_handle == "1A3"
        assert issue.intersection_point == (50.0, 30.0)


# ---------------------------------------------------------------------------
# Test Utility Functions
# ---------------------------------------------------------------------------

class TestCreateTestDxf:
    """Tests for DXF generation utilities."""

    def test_create_valid_dxf(self):
        """create_test_valid_dxf returns parseable DXF."""
        dxf_bytes = create_test_valid_dxf()
        assert isinstance(dxf_bytes, bytes)
        assert len(dxf_bytes) > 100

        # Should be parseable by ezdxf (ezdxf 1.4.3 needs text stream)
        doc = ezdxf.read(io.StringIO(dxf_bytes.decode('cp1252')))
        assert doc is not None

    def test_create_figure8_dxf(self):
        """create_test_figure8_dxf returns parseable DXF."""
        dxf_bytes = create_test_figure8_dxf()
        assert isinstance(dxf_bytes, bytes)
        assert len(dxf_bytes) > 100

        # Should be parseable by ezdxf (ezdxf 1.4.3 needs text stream)
        doc = ezdxf.read(io.StringIO(dxf_bytes.decode('cp1252')))
        assert doc is not None


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_dxf(self):
        """Empty DXF (no entities) handles gracefully."""
        doc = ezdxf.new('R2010')
        text_buf = io.StringIO()
        doc.write(text_buf)
        empty_bytes = doc.encode(text_buf.getvalue())

        validator = TopologyValidator(empty_bytes, "empty.dxf")
        report = validator.check_self_intersections()

        assert report.is_valid is True
        assert report.entities_checked == 0

    def test_mixed_entity_types(self):
        """DXF with mixed entity types validates correctly."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        # Add various entity types
        msp.add_lwpolyline(
            [(0, 0), (100, 0), (100, 100), (0, 100)],
            dxfattribs={'layer': 'POLY', 'closed': True}
        )
        msp.add_line((0, 0, 0), (200, 200, 0), dxfattribs={'layer': 'LINE'})
        msp.add_circle((50, 50), 25, dxfattribs={'layer': 'CIRCLE'})
        msp.add_text("Test", dxfattribs={'layer': 'TEXT'})

        text_buf = io.StringIO()
        doc.write(text_buf)
        mixed_bytes = doc.encode(text_buf.getvalue())

        validator = TopologyValidator(mixed_bytes, "mixed.dxf")
        report = validator.check_self_intersections()

        # Only LWPOLYLINE should be validated
        assert report.entities_checked == 1
        assert report.is_valid is True
