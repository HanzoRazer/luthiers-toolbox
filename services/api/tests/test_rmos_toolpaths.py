"""
Tests for app.rmos.toolpaths — canonical server-side toolpath generation.

Covers generate_toolpaths_server_side, feasibility contract, mode dispatch,
hashes/meta, and convenience wrappers.
"""
import pytest

from app.rmos.toolpaths import (
    generate_toolpaths_server_side,
    generate_saw_toolpaths,
    generate_rosette_toolpaths,
)


# Minimal feasibility dict required by governance
MIN_FEASIBILITY = {"score": 80, "risk_bucket": "GREEN"}


class TestGenerateToolpathsServerSide:
    """Tests for generate_toolpaths_server_side entry point."""

    def test_requires_feasibility(self):
        """Raises when feasibility is missing (governance contract)."""
        with pytest.raises(ValueError, match="Authoritative feasibility is required"):
            generate_toolpaths_server_side(
                mode="saw",
                design={},
                context={},
                feasibility={},
            )

    def test_requires_feasibility_not_none(self):
        """Raises when feasibility is None (falsy)."""
        with pytest.raises(ValueError, match="feasibility is required"):
            generate_toolpaths_server_side(
                mode="saw",
                design={},
                context={},
                feasibility=None,
            )

    def test_unsupported_mode_raises(self):
        """Raises for unsupported mode."""
        with pytest.raises(ValueError, match="Unsupported mode"):
            generate_toolpaths_server_side(
                mode="unknown_mode",
                design={},
                context={},
                feasibility=MIN_FEASIBILITY,
            )

    def test_saw_mode_returns_expected_keys(self):
        """Saw mode returns toolpaths, gcode_text, opplan, hashes, meta."""
        result = generate_toolpaths_server_side(
            mode="saw",
            design={},
            context={},
            feasibility=MIN_FEASIBILITY,
        )
        assert "toolpaths" in result
        assert "gcode_text" in result
        assert "opplan" in result
        assert "hashes" in result
        assert "meta" in result
        assert result["meta"]["mode"] == "saw"
        assert result["hashes"]["toolpaths_sha256"]
        assert result["hashes"]["opplan_sha256"]

    def test_rosette_mode_returns_expected_keys(self):
        """Rosette mode returns expected structure."""
        result = generate_toolpaths_server_side(
            mode="rosette",
            design={"ring_id": 1},
            context={},
            feasibility=MIN_FEASIBILITY,
        )
        assert result["meta"]["mode"] == "rosette"
        assert "toolpaths" in result
        assert "hashes" in result

    def test_vcarve_mode_returns_expected_keys(self):
        """Vcarve mode returns expected structure (often fallback)."""
        result = generate_toolpaths_server_side(
            mode="vcarve",
            design={},
            context={},
            feasibility=MIN_FEASIBILITY,
        )
        assert result["meta"]["mode"] == "vcarve"
        assert "toolpaths" in result
        assert "gcode_text" in result

    def test_options_default_and_passed(self):
        """Accepts options=None and options dict."""
        result = generate_toolpaths_server_side(
            mode="saw",
            design={},
            context={},
            feasibility=MIN_FEASIBILITY,
            options=None,
        )
        assert result["meta"]["generator_version"] == "1.0.0"

        result2 = generate_toolpaths_server_side(
            mode="saw",
            design={},
            context={},
            feasibility=MIN_FEASIBILITY,
            options={"safe_z_mm": 10.0},
        )
        assert result2["meta"]["generator_version"] == "1.0.0"

    def test_hashes_include_gcode_when_present(self):
        """Hashes include gcode_sha256 when gcode_text is present."""
        result = generate_toolpaths_server_side(
            mode="saw",
            design={},
            context={},
            feasibility=MIN_FEASIBILITY,
        )
        # Saw (real or fallback) always produces gcode_text
        assert "gcode_text" in result
        if result.get("gcode_text"):
            assert result["hashes"]["gcode_sha256"] is not None


class TestConvenienceWrappers:
    """Tests for generate_saw_toolpaths and generate_rosette_toolpaths."""

    def test_generate_saw_toolpaths_calls_server_side(self):
        """generate_saw_toolpaths delegates to server_side with mode=saw."""
        result = generate_saw_toolpaths(
            design={},
            context={},
            feasibility=MIN_FEASIBILITY,
        )
        assert result["meta"]["mode"] == "saw"

    def test_generate_rosette_toolpaths_calls_server_side(self):
        """generate_rosette_toolpaths delegates to server_side with mode=rosette."""
        result = generate_rosette_toolpaths(
            design={"ring_id": 1},
            context={},
            feasibility=MIN_FEASIBILITY,
        )
        assert result["meta"]["mode"] == "rosette"
