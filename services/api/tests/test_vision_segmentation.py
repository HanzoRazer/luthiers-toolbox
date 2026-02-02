"""
Vision Segmentation Tests

Tests for:
1. Geometry utilities (Douglas-Peucker, CCW, normalization)
2. Segmentation service with stub client
3. Router endpoints (smoke tests)
4. DXF/SVG export

DATE: January 2026
"""
import pytest
import math
from fastapi.testclient import TestClient

from app.vision.segmentation_service import (
    GuitarSegmentationService,
    SegmentationResult,
    SegmentationError,
    douglas_peucker,
    perpendicular_distance,
    compute_signed_area,
    ensure_ccw,
    ensure_closed,
    normalize_polygon,
    scale_polygon,
)
from app.ai.transport import set_vision_client
from app.ai.transport.vision_client import StubVisionClient, VisionConfig, VisionProvider


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def stub_vision_client():
    """Create stub vision client with guitar response."""
    client = StubVisionClient()
    client.set_stub_response({
        "body_outline": [
            [100, 50], [150, 80], [180, 150], [190, 250],
            [180, 350], [150, 420], [100, 450], [50, 420],
            [20, 350], [10, 250], [20, 150], [50, 80], [100, 50]
        ],
        "image_width": 200,
        "image_height": 500,
        "confidence": 0.92,
        "guitar_type": "les_paul",
        "notes": "Clear guitar body detected"
    })
    return client


# ---------------------------------------------------------------------------
# Geometry Utilities
# ---------------------------------------------------------------------------

class TestDouglasPeucker:
    """Test Douglas-Peucker polyline simplification."""

    def test_preserves_endpoints(self):
        """Endpoints should always be preserved."""
        points = [(0, 0), (1, 0.001), (2, 0), (3, 0.001), (4, 0)]
        result = douglas_peucker(points, epsilon=0.01)
        assert result[0] == (0, 0)
        assert result[-1] == (4, 0)

    def test_simplifies_collinear_points(self):
        """Collinear points should be reduced to endpoints."""
        points = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        result = douglas_peucker(points, epsilon=0.1)
        assert len(result) == 2
        assert result == [(0, 0), (4, 4)]

    def test_preserves_significant_deviation(self):
        """Points with significant deviation should be preserved."""
        points = [(0, 0), (2, 0), (4, 2), (6, 0), (8, 0)]
        result = douglas_peucker(points, epsilon=0.5)
        assert (4, 2) in result

    def test_handles_short_lists(self):
        """Short lists should be returned as-is."""
        assert douglas_peucker([], epsilon=1.0) == []
        assert douglas_peucker([(0, 0)], epsilon=1.0) == [(0, 0)]
        assert douglas_peucker([(0, 0), (1, 1)], epsilon=1.0) == [(0, 0), (1, 1)]


class TestPerpendicularDistance:
    """Test perpendicular distance calculation."""

    def test_point_on_line(self):
        """Point on line should have zero distance."""
        dist = perpendicular_distance((1, 1), (0, 0), (2, 2))
        assert abs(dist) < 0.001

    def test_perpendicular_offset(self):
        """Point perpendicular to line should have correct distance."""
        dist = perpendicular_distance((1, 1), (0, 0), (2, 0))
        assert abs(dist - 1.0) < 0.001

    def test_degenerate_line(self):
        """Degenerate line (same start/end) should return point distance."""
        dist = perpendicular_distance((3, 4), (0, 0), (0, 0))
        assert abs(dist - 5.0) < 0.001


class TestSignedArea:
    """Test signed area calculation."""

    def test_ccw_positive(self):
        """CCW polygon should have positive area."""
        ccw_square = [(0, 0), (1, 0), (1, 1), (0, 1)]
        area = compute_signed_area(ccw_square)
        assert area > 0

    def test_cw_negative(self):
        """CW polygon should have negative area."""
        cw_square = [(0, 0), (0, 1), (1, 1), (1, 0)]
        area = compute_signed_area(cw_square)
        assert area < 0

    def test_empty_polygon(self):
        """Empty or small polygon should return 0."""
        assert compute_signed_area([]) == 0
        assert compute_signed_area([(0, 0)]) == 0
        assert compute_signed_area([(0, 0), (1, 1)]) == 0


class TestEnsureCCW:
    """Test CCW winding enforcement."""

    def test_already_ccw(self):
        """CCW polygon should be unchanged."""
        ccw = [(0, 0), (1, 0), (1, 1), (0, 1)]
        result = ensure_ccw(ccw)
        assert result == ccw

    def test_reverses_cw(self):
        """CW polygon should be reversed."""
        cw = [(0, 0), (0, 1), (1, 1), (1, 0)]
        result = ensure_ccw(cw)
        expected = [(1, 0), (1, 1), (0, 1), (0, 0)]
        assert result == expected


class TestEnsureClosed:
    """Test polygon closure."""

    def test_already_closed(self):
        """Closed polygon should be unchanged."""
        closed = [(0, 0), (1, 0), (1, 1), (0, 0)]
        result = ensure_closed(closed)
        assert result == closed

    def test_closes_open(self):
        """Open polygon should be closed."""
        open_poly = [(0, 0), (1, 0), (1, 1)]
        result = ensure_closed(open_poly)
        assert len(result) == 4
        assert result[-1] == (0, 0)

    def test_tolerance(self):
        """Near-closed polygon should be recognized as closed."""
        near_closed = [(0, 0), (1, 0), (1, 1), (0.0005, 0.0005)]
        result = ensure_closed(near_closed, tolerance=0.001)
        assert len(result) == 4  # No point added


class TestNormalizePolygon:
    """Test polygon normalization."""

    def test_normalizes_to_0_1(self):
        """Polygon should be normalized to 0-1 range."""
        points = [(0, 0), (100, 0), (100, 200), (0, 200)]
        result = normalize_polygon(points, 100, 200)
        expected = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        for r, e in zip(result, expected):
            assert abs(r[0] - e[0]) < 0.001
            assert abs(r[1] - e[1]) < 0.001


class TestScalePolygon:
    """Test polygon scaling."""

    def test_scales_to_mm(self):
        """Normalized polygon should scale to mm."""
        normalized = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        result = scale_polygon(normalized, 400.0, 600.0, center=False)
        expected = [(0.0, 0.0), (400.0, 0.0), (400.0, 600.0), (0.0, 600.0)]
        for r, e in zip(result, expected):
            assert abs(r[0] - e[0]) < 0.001
            # Y is flipped in scale_polygon with center=True, but we use center=False

    def test_centers_on_origin(self):
        """With center=True, polygon should be centered on origin."""
        normalized = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        result = scale_polygon(normalized, 400.0, 600.0, center=True)
        xs = [p[0] for p in result]
        ys = [p[1] for p in result]
        assert abs(sum(xs) / len(xs)) < 0.001  # Centered X
        # Y is also centered and flipped


# ---------------------------------------------------------------------------
# Segmentation Service
# ---------------------------------------------------------------------------

class TestGuitarSegmentationService:
    """Test GuitarSegmentationService with stub client."""

    def test_segment_with_stub_client(self, stub_vision_client):
        """Service should segment image using stub client."""
        service = GuitarSegmentationService(stub_vision_client)

        # Create minimal valid PNG (1x1 transparent pixel)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        result = service.segment(
            image_bytes=png_bytes,
            target_width_mm=400.0,
            simplify_tolerance_mm=1.0,
        )

        assert isinstance(result, SegmentationResult)
        assert result.confidence == 0.92
        assert result.guitar_type == "les_paul"
        assert result.point_count > 0
        assert len(result.polygon_mm) > 0
        assert result.target_width_mm == 400.0

    def test_segment_returns_error_for_invalid_image(self, stub_vision_client):
        """Service should return error for invalid image."""
        service = GuitarSegmentationService(stub_vision_client)

        result = service.segment(
            image_bytes=b"not an image",
            target_width_mm=400.0,
        )

        assert isinstance(result, SegmentationError)
        assert "Failed to read image" in result.error

    def test_export_to_dxf(self, stub_vision_client):
        """Service should export result to DXF."""
        service = GuitarSegmentationService(stub_vision_client)

        # Create result manually
        result = SegmentationResult(
            polygon_normalized=[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
            polygon_mm=[(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)],
            confidence=0.9,
            guitar_type="les_paul",
            image_width=200,
            image_height=200,
            target_width_mm=100.0,
            target_height_mm=100.0,
            point_count=5,
        )

        dxf_bytes = service.export_to_dxf(result)

        assert b"SECTION" in dxf_bytes
        assert b"ENTITIES" in dxf_bytes
        assert b"POLYLINE" in dxf_bytes
        assert b"GEOMETRY" in dxf_bytes
        assert b"EOF" in dxf_bytes

    def test_export_to_svg(self, stub_vision_client):
        """Service should export result to SVG."""
        service = GuitarSegmentationService(stub_vision_client)

        result = SegmentationResult(
            polygon_normalized=[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
            polygon_mm=[(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)],
            confidence=0.9,
            guitar_type="stratocaster",
            image_width=200,
            image_height=200,
            target_width_mm=100.0,
            target_height_mm=100.0,
            point_count=5,
        )

        svg_content = service.export_to_svg(result)

        assert '<svg' in svg_content
        assert 'polygon' in svg_content
        assert 'stratocaster' in svg_content
        assert '</svg>' in svg_content


# ---------------------------------------------------------------------------
# Router Smoke Tests
# ---------------------------------------------------------------------------

class TestSegmentationEndpoints:
    """Smoke tests for segmentation endpoints."""

    def test_segment_endpoint_exists(self, client):
        """POST /api/vision/segment should exist."""
        # Without a file, we expect 422 (validation error), not 404
        response = client.post("/api/vision/segment")
        assert response.status_code == 422

    def test_segment_rejects_invalid_content_type(self, client):
        """Segment should reject non-image files."""
        response = client.post(
            "/api/vision/segment",
            files={"file": ("test.txt", b"hello world", "text/plain")},
            data={"target_width_mm": "400.0"},
        )
        # Should return error in response body, not 500
        assert response.status_code == 200  # Returns ok=False in body
        data = response.json()
        assert data["ok"] is False
        assert "Unsupported image type" in data["error"]

    def test_photo_to_gcode_endpoint_exists(self, client):
        """POST /api/vision/photo-to-gcode should exist."""
        response = client.post("/api/vision/photo-to-gcode")
        assert response.status_code == 422


class TestSegmentationSchemas:
    """Test segmentation schemas import correctly."""

    def test_segment_request_schema(self):
        """SegmentRequest schema should be valid."""
        from app.vision.schemas import SegmentRequest
        req = SegmentRequest(
            target_width_mm=400.0,
            simplify_tolerance_mm=1.0,
            guitar_category="acoustic",
            output_format="dxf",
        )
        assert req.target_width_mm == 400.0

    def test_segment_response_schema(self):
        """SegmentResponse schema should be valid."""
        from app.vision.schemas import SegmentResponse
        resp = SegmentResponse(
            ok=True,
            polygon=[[0, 0], [100, 0], [100, 100]],
            confidence=0.9,
            guitar_type="les_paul",
            point_count=3,
        )
        assert resp.ok is True
        assert len(resp.polygon) == 3


# ---------------------------------------------------------------------------
# Integration with Stub Client
# ---------------------------------------------------------------------------

class TestVisionClientIntegration:
    """Test vision client setup and teardown."""

    def test_stub_client_can_be_set_globally(self, stub_vision_client):
        """Stub client should be settable for testing."""
        set_vision_client(stub_vision_client)
        from app.ai.transport import get_vision_client
        client = get_vision_client()
        assert client is stub_vision_client
        # Reset
        set_vision_client(None)

    def test_stub_client_tracks_calls(self, stub_vision_client):
        """Stub client should track call count and last prompt."""
        stub_vision_client.analyze(
            image_bytes=b"fake",
            prompt="Test prompt",
        )
        assert stub_vision_client.call_count == 1
        assert stub_vision_client.last_prompt == "Test prompt"
