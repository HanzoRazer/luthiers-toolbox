# tests/test_bracing_presets_bridge_smoke.py

"""
Smoke tests for VINE-11: Bracing presets bridge.

Verifies that bracing presets include instrument-specific data
from construction drawings, not just hardcoded generic values.
"""

import pytest


class TestBracingPresetsBridge:
    """Tests for bracing_presets_bridge module."""

    def test_get_instrument_presets_returns_list(self):
        """get_instrument_presets returns a list of presets."""
        from app.art_studio.bracing_presets_bridge import get_instrument_presets

        presets = get_instrument_presets()
        assert isinstance(presets, list)
        assert len(presets) >= 3  # J-45, Dreadnought, Jumbo

    def test_j45_preset_exists(self):
        """Gibson J-45 preset is included."""
        from app.art_studio.bracing_presets_bridge import get_instrument_presets

        presets = get_instrument_presets()
        j45 = next((p for p in presets if "j45" in p.id.lower()), None)
        assert j45 is not None
        assert j45.source == "instrument-spec"

    def test_j45_has_correct_brace_count(self):
        """J-45 has 8 braces (from J45 DIMS.dxf)."""
        from app.art_studio.bracing_presets_bridge import get_instrument_presets

        presets = get_instrument_presets()
        j45 = next((p for p in presets if "j45" in p.id.lower()), None)
        assert len(j45.braces) == 8

    def test_j45_brace_dimensions_match_spec(self):
        """J-45 braces use 6.35mm x 12.70mm cross-section (1/4\" x 1/2\")."""
        from app.art_studio.bracing_presets_bridge import get_instrument_presets

        presets = get_instrument_presets()
        j45 = next((p for p in presets if "j45" in p.id.lower()), None)

        # All braces should have the J-45 cross-section
        for brace in j45.braces:
            assert brace.width_mm == pytest.approx(6.35, abs=0.1)
            assert brace.height_mm == pytest.approx(12.70, abs=0.1)

    def test_dreadnought_preset_exists(self):
        """Dreadnought preset is included."""
        from app.art_studio.bracing_presets_bridge import get_instrument_presets

        presets = get_instrument_presets()
        dread = next((p for p in presets if "dreadnought" in p.id.lower()), None)
        assert dread is not None
        assert dread.source == "instrument-spec"

    def test_jumbo_preset_exists(self):
        """Jumbo J-200 preset is included."""
        from app.art_studio.bracing_presets_bridge import get_instrument_presets

        presets = get_instrument_presets()
        jumbo = next((p for p in presets if "jumbo" in p.id.lower()), None)
        assert jumbo is not None
        assert jumbo.source == "instrument-spec"


class TestBracingPresetsEndpoint:
    """Tests for /art-studio/bracing/presets endpoint."""

    def test_endpoint_returns_mixed_sources(self):
        """Endpoint returns both generic and instrument-spec presets."""
        from app.art_studio.bracing_router import get_bracing_presets

        presets = get_bracing_presets()
        sources = {p.source for p in presets}
        assert "generic" in sources
        assert "instrument-spec" in sources

    def test_endpoint_returns_at_least_six_presets(self):
        """Endpoint returns at least 6 presets (3 generic + 3 instrument)."""
        from app.art_studio.bracing_router import get_bracing_presets

        presets = get_bracing_presets()
        assert len(presets) >= 6

    def test_generic_presets_still_present(self):
        """Original generic presets are still included."""
        from app.art_studio.bracing_router import get_bracing_presets

        presets = get_bracing_presets()
        ids = [p.id for p in presets]
        assert "x-brace-standard" in ids
        assert "ladder-classical" in ids
        assert "scalloped-x" in ids


class TestBracePatternConversion:
    """Tests for BracePattern to BracingPreset conversion."""

    def test_length_calculated_from_endpoints(self):
        """Brace length is calculated from start/end coordinates."""
        from app.art_studio.bracing_presets_bridge import _brace_length_from_endpoints

        # Simple horizontal line: 100mm
        length = _brace_length_from_endpoints((0, 0), (100, 0))
        assert length == pytest.approx(100.0, abs=0.01)

        # Diagonal: sqrt(3^2 + 4^2) = 5
        length = _brace_length_from_endpoints((0, 0), (3, 4))
        assert length == pytest.approx(5.0, abs=0.01)

    def test_scalloped_flag_converted_to_profile_type(self):
        """Scalloped braces get profile_type='scalloped'."""
        from app.art_studio.bracing_presets_bridge import get_instrument_presets

        presets = get_instrument_presets()
        j45 = next((p for p in presets if "j45" in p.id.lower()), None)

        # J-45 has scalloped X-braces
        scalloped_count = sum(1 for b in j45.braces if b.profile_type == "scalloped")
        assert scalloped_count > 0  # At least some braces are scalloped
