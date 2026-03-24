"""
Integration tests for ai_render_extractor.py

Tests:
1. Smoke test: AIRenderExtractor imports cleanly
2. Spec loading finds smart_guitar_v1.json
3. export_dxf returns True and file exists
"""

import os
import tempfile
from pathlib import Path

import pytest


class TestAIRenderExtractorSmoke:
    """Smoke tests for AIRenderExtractor."""

    def test_import_clean(self):
        """AIRenderExtractor imports without errors."""
        from ai_render_extractor import AIRenderExtractor, ExtractorConfig, ExtractionResult

        # Classes should be importable
        assert AIRenderExtractor is not None
        assert ExtractorConfig is not None
        assert ExtractionResult is not None

    def test_instantiate_default_config(self):
        """AIRenderExtractor instantiates with default config."""
        from ai_render_extractor import AIRenderExtractor

        extractor = AIRenderExtractor()
        assert extractor.config.spec_name == "smart_guitar"
        assert extractor.config.detect_voids is True
        assert extractor.config.overlay_spec_cavities is True

    def test_instantiate_custom_config(self):
        """AIRenderExtractor accepts custom config."""
        from ai_render_extractor import AIRenderExtractor, ExtractorConfig

        config = ExtractorConfig(
            spec_name="test_spec",
            detect_voids=False,
            min_contour_area=500.0,
        )
        extractor = AIRenderExtractor(config)

        assert extractor.config.spec_name == "test_spec"
        assert extractor.config.detect_voids is False
        assert extractor.config.min_contour_area == 500.0


class TestSpecLoading:
    """Tests for instrument spec loading."""

    def test_load_smart_guitar_spec(self):
        """Spec loading finds smart_guitar_v1.json."""
        from ai_render_extractor import AIRenderExtractor, SPEC_DIR

        extractor = AIRenderExtractor()

        # Verify spec directory exists
        assert SPEC_DIR.exists(), f"SPEC_DIR not found: {SPEC_DIR}"

        # Verify smart_guitar_v1.json exists
        spec_path = SPEC_DIR / "smart_guitar_v1.json"
        assert spec_path.exists(), f"smart_guitar_v1.json not found at {spec_path}"

        # Load spec
        result = extractor.load_spec("smart_guitar")
        assert result is True, "Failed to load smart_guitar spec"

        # Verify spec data loaded
        assert extractor._spec_data is not None

    def test_load_nonexistent_spec_returns_false(self):
        """Loading nonexistent spec returns False."""
        from ai_render_extractor import AIRenderExtractor

        extractor = AIRenderExtractor()
        result = extractor.load_spec("nonexistent_spec_xyz")
        assert result is False


class TestDXFExport:
    """Tests for DXF export functionality."""

    def test_export_dxf_returns_true_and_file_exists(self):
        """export_dxf returns True and creates file."""
        from ai_render_extractor import AIRenderExtractor, ExtractionResult

        extractor = AIRenderExtractor()

        # Create mock extraction result with body contour
        result = ExtractionResult(
            body_contour=[
                (0, 0), (100, 0), (100, 200), (50, 250), (0, 200)
            ],
            cutaway_voids=[
                [(20, 50), (40, 50), (40, 80), (20, 80)]
            ],
            spec_cavities={
                "neck_pocket": [(40, 180), (60, 180), (60, 210), (40, 210)]
            },
            image_size=(500, 600),
        )

        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
            output_path = f.name

        try:
            success = extractor.export_dxf(result, output_path)

            # Verify return value
            assert success is True, "export_dxf should return True"

            # Verify file exists
            assert os.path.exists(output_path), f"DXF file not created: {output_path}"

            # Verify file has content
            file_size = os.path.getsize(output_path)
            assert file_size > 0, "DXF file is empty"

        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_export_empty_result(self):
        """export_dxf handles empty result gracefully."""
        from ai_render_extractor import AIRenderExtractor, ExtractionResult

        extractor = AIRenderExtractor()
        result = ExtractionResult()  # Empty result

        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
            output_path = f.name

        try:
            success = extractor.export_dxf(result, output_path)
            # Should still succeed, just with empty DXF
            assert success is True
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestConstants:
    """Tests for module constants."""

    def test_dxf_layers_defined(self):
        """DXF layers are properly defined."""
        from ai_render_extractor import DXF_LAYERS

        assert "BODY_OUTLINE" in DXF_LAYERS
        assert "CUTAWAY_VOID" in DXF_LAYERS
        assert "NECK_POCKET" in DXF_LAYERS
        assert "PICKUP_CAVITY" in DXF_LAYERS

        # Each layer should have a color
        for layer_name, props in DXF_LAYERS.items():
            assert "color" in props, f"Layer {layer_name} missing color"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
