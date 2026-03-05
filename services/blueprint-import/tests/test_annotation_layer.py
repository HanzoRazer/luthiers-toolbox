"""
Tests for Annotation Layer Architecture
=======================================

Tests for Phase 4.0 annotation separation functionality.

Author: Luthier's Toolbox
Version: 4.0.0
"""

import pytest
import json
import tempfile
from pathlib import Path

# Import annotation classes
from phase4.annotations import (
    Annotation,
    AnnotationType,
    AnnotationSource,
    LinearDimension,
    RadialDimension,
    AnnotationAwareExporter,
    AnnotationJSONExporter,
    check_dxf_compatibility
)


class TestLinearDimension:
    """Tests for LinearDimension class."""

    def test_linear_dimension_creation(self):
        """Test basic linear dimension creation."""
        dim = LinearDimension(
            text="24.625",
            value=625.47,
            point1=(100, 200),
            point2=(200, 200),
            confidence=0.95,
            feature_id="body_outline_0"
        )

        assert dim.type == AnnotationType.LINEAR_DIMENSION
        assert dim.text == "24.625"
        assert dim.value == 625.47
        assert dim.point1 == (100, 200)
        assert dim.point2 == (200, 200)
        assert dim.confidence == 0.95

    def test_linear_dimension_auto_value_calculation(self):
        """Test automatic value calculation from points."""
        dim = LinearDimension(
            text="100",
            point1=(0, 0),
            point2=(100, 0)
        )

        # Value should be calculated as distance between points
        assert dim.value == 100.0

    def test_linear_dimension_to_dict(self):
        """Test dictionary export."""
        dim = LinearDimension(
            text="50",
            value=50.0,
            point1=(0, 0),
            point2=(50, 0),
            feature_id="pickup_route_1"
        )

        d = dim.to_dict()

        assert d['type'] == 'linear_dimension'
        assert d['text'] == '50'
        assert d['value'] == 50.0
        assert 'linear' in d
        assert d['linear']['point1'] == (0, 0)
        assert d['linear']['point2'] == (50, 0)


class TestRadialDimension:
    """Tests for RadialDimension class."""

    def test_radial_dimension_radius(self):
        """Test radial dimension for radius."""
        dim = RadialDimension(
            text="R25",
            radius=25.0,
            center=(100, 100),
            is_diameter=False,
            confidence=0.88
        )

        assert dim.type == AnnotationType.RADIAL_DIMENSION
        assert dim.radius == 25.0
        assert dim.is_diameter is False
        assert dim.value == 25.0  # Same as radius

    def test_radial_dimension_diameter(self):
        """Test radial dimension for diameter."""
        dim = RadialDimension(
            text="D50",
            radius=25.0,
            center=(100, 100),
            is_diameter=True
        )

        assert dim.is_diameter is True
        assert dim.value == 50.0  # Diameter = 2 * radius

    def test_radial_dimension_to_dict(self):
        """Test dictionary export."""
        dim = RadialDimension(
            text="R10",
            radius=10.0,
            center=(50, 50),
            is_diameter=False
        )

        d = dim.to_dict()

        assert d['type'] == 'radial_dimension'
        assert 'radial' in d
        assert d['radial']['center'] == (50, 50)
        assert d['radial']['radius'] == 10.0
        assert d['radial']['is_diameter'] is False


class TestAnnotationSource:
    """Tests for annotation source tracking."""

    def test_source_types(self):
        """Test all source types are available."""
        sources = [
            AnnotationSource.OCR,
            AnnotationSource.ARROW,
            AnnotationSource.WITNESS,
            AnnotationSource.INFERRED,
            AnnotationSource.TEMPLATE,
            AnnotationSource.MANUAL,
            AnnotationSource.HYBRID
        ]

        assert len(sources) == 7

    def test_hybrid_source_details(self):
        """Test hybrid source with details."""
        dim = LinearDimension(
            text="100",
            point1=(0, 0),
            point2=(100, 0),
            source=AnnotationSource.HYBRID,
            confidence=0.92
        )

        # Should auto-populate source_details
        assert 'combined_confidence' in dim.source_details


class TestDXFCompatibility:
    """Tests for DXF version compatibility."""

    def test_r12_warning(self):
        """Test R12 compatibility warning."""
        dim = LinearDimension(text="100", point1=(0, 0), point2=(100, 0))

        # R12 should return False (not fully compatible)
        result = check_dxf_compatibility([dim], 'R12')
        assert result is False

    def test_r2000_compatible(self):
        """Test R2000+ is compatible."""
        dim = LinearDimension(text="100", point1=(0, 0), point2=(100, 0))

        result = check_dxf_compatibility([dim], 'R2000')
        assert result is True

    def test_empty_annotations_compatible(self):
        """Test empty annotations list is always compatible."""
        result = check_dxf_compatibility([], 'R12')
        assert result is True


class TestJSONExporter:
    """Tests for JSON sidecar export."""

    def test_json_export(self):
        """Test basic JSON export."""
        annotations = [
            LinearDimension(
                text="24.625",
                value=625.47,
                point1=(100, 200),
                point2=(200, 200),
                confidence=0.95,
                feature_id="body_outline_0"
            ),
            RadialDimension(
                text="R50",
                radius=50.0,
                center=(300, 300),
                confidence=0.88
            )
        ]

        exporter = AnnotationJSONExporter()

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            data = exporter.export(
                annotations,
                output_path,
                source_file='test_blueprint.pdf'
            )

            assert data['version'] == '1.0'
            assert data['source_file'] == 'test_blueprint.pdf'
            assert len(data['dimensions']) == 2
            assert 'statistics' in data
            assert data['statistics']['total_annotations'] == 2

            # Verify file was written
            with open(output_path, 'r') as f:
                loaded = json.load(f)
                assert loaded['version'] == '1.0'

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_json_statistics(self):
        """Test statistics calculation."""
        annotations = [
            LinearDimension(text="100", point1=(0, 0), point2=(100, 0), confidence=0.9),
            LinearDimension(text="200", point1=(0, 0), point2=(200, 0), confidence=0.8),
            RadialDimension(text="R50", radius=50, center=(0, 0), confidence=0.7),
        ]

        exporter = AnnotationJSONExporter()

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            data = exporter.export(annotations, output_path)

            stats = data['statistics']
            assert stats['total_annotations'] == 3
            assert stats['by_type']['linear_dimension'] == 2
            assert stats['by_type']['radial_dimension'] == 1
            assert 0.79 < stats['average_confidence'] < 0.81

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_validation_report(self):
        """Test validation report generation."""
        annotations = [
            LinearDimension(
                text="100",
                value=100.0,
                point1=(0, 0),
                point2=(100, 0),
                feature_id="test_feature",
                confidence=0.95
            )
        ]

        expected = {
            "test_feature": 100.0  # Exact match expected
        }

        exporter = AnnotationJSONExporter()
        report = exporter.export_validation_report(annotations, expected)

        assert report['summary']['passed'] == 1
        assert report['summary']['failed'] == 0
        assert report['summary']['pass_rate'] == 1.0


class TestAnnotationAwareExporter:
    """Tests for DXF export with annotation separation."""

    def test_exporter_initialization(self):
        """Test exporter can be initialized."""
        try:
            exporter = AnnotationAwareExporter()
            assert exporter.annotation_layer == "DIMENSIONS"
        except ImportError:
            pytest.skip("ezdxf not available")

    def test_layer_properties(self):
        """Test layer property retrieval."""
        try:
            exporter = AnnotationAwareExporter()

            props = exporter._get_layer_properties('DIMENSIONS')
            assert props['color'] == 2  # Yellow
            assert 'lineweight' in props

            props = exporter._get_layer_properties('BODY_OUTLINE')
            assert props['color'] == 1  # Red

        except ImportError:
            pytest.skip("ezdxf not available")

    def test_confidence_threshold(self):
        """Test confidence threshold filtering."""
        try:
            exporter = AnnotationAwareExporter(confidence_threshold=0.8)
            assert exporter.confidence_threshold == 0.8
        except ImportError:
            pytest.skip("ezdxf not available")


class TestFeatureIDMapping:
    """Tests for feature ID to handle mapping."""

    def test_resolve_handle(self):
        """Test handle resolution."""
        dim = LinearDimension(
            text="100",
            point1=(0, 0),
            point2=(100, 0),
            feature_id="body_outline_0"
        )

        id_to_handle = {
            "body_outline_0": "ABC123",
            "pickup_route_1": "DEF456"
        }

        handle = dim.resolve_handle(id_to_handle)
        assert handle == "ABC123"
        assert dim.associated_geometry == "ABC123"

    def test_resolve_handle_missing(self):
        """Test handle resolution for missing ID."""
        dim = LinearDimension(
            text="100",
            point1=(0, 0),
            point2=(100, 0),
            feature_id="unknown_feature"
        )

        id_to_handle = {
            "body_outline_0": "ABC123"
        }

        handle = dim.resolve_handle(id_to_handle)
        assert handle is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
