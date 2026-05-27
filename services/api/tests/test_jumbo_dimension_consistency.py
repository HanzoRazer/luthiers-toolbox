"""
Jumbo Dimension Consistency Test

Verifies that jumbo body dimensions are consistent across the four
known definition points in the codebase.

This is symptom mitigation — the architectural problem is duplicated
facts that can drift. "Single source of truth for body-family dimensions"
is a future canonicalization item.

Paths checked:
1. IBG FAMILY_DEFAULTS["jumbo"] — body_contour_solver.py (canonical)
2. jumbo_j200.py MODEL_INFO — guitars/jumbo_j200.py
3. Body Outline Editor INSTRUMENT_TEMPLATES.jumbo — hostinger/body-outline-editor.html
4. instrument_model_registry.json jumbo_j200.body_dimensions_mm

NOT checked (out of scope, needs investigation):
- catalog.json "jumbo" — appears to be DXF bounding box, not body dimensions
"""

import json
from pathlib import Path

import pytest


# Canonical jumbo dimensions (from IBG FAMILY_DEFAULTS)
CANONICAL_JUMBO = {
    "lower_bout_mm": 432.0,
    "upper_bout_mm": 305.0,
    "waist_mm": 254.0,
    "body_length_mm": 530.0,
    "waist_y_norm": 0.44,
}


class TestJumboDimensionConsistency:
    """Four-path consistency check for jumbo dimensions."""

    def test_ibg_family_defaults_canonical(self):
        """Path 1: IBG FAMILY_DEFAULTS is the canonical source."""
        from app.instrument_geometry.body.ibg.body_contour_solver import (
            FAMILY_DEFAULTS,
        )

        jumbo = FAMILY_DEFAULTS["jumbo"]

        assert jumbo["lower_bout_mm"] == CANONICAL_JUMBO["lower_bout_mm"]
        assert jumbo["upper_bout_mm"] == CANONICAL_JUMBO["upper_bout_mm"]
        assert jumbo["waist_mm"] == CANONICAL_JUMBO["waist_mm"]
        assert jumbo["body_length_mm"] == CANONICAL_JUMBO["body_length_mm"]
        assert jumbo["waist_y_norm"] == CANONICAL_JUMBO["waist_y_norm"]

    def test_jumbo_j200_model_matches_canonical(self):
        """Path 2: jumbo_j200.py MODEL_INFO matches canonical."""
        from app.instrument_geometry.guitars.jumbo_j200 import MODEL_INFO

        assert MODEL_INFO["lower_bout_mm"] == CANONICAL_JUMBO["lower_bout_mm"]
        assert MODEL_INFO["upper_bout_mm"] == CANONICAL_JUMBO["upper_bout_mm"]
        assert MODEL_INFO["waist_mm"] == CANONICAL_JUMBO["waist_mm"]
        assert MODEL_INFO["body_length_mm"] == CANONICAL_JUMBO["body_length_mm"]
        assert MODEL_INFO["ibg_family"] == "jumbo"

    def test_instrument_registry_matches_canonical(self):
        """Path 3: instrument_model_registry.json matches canonical."""
        registry_path = Path(__file__).parent.parent / "app" / "instrument_geometry" / "instrument_model_registry.json"

        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)

        jumbo = registry["models"]["jumbo_j200"]
        dims = jumbo["body_dimensions_mm"]

        assert jumbo["ibg_family"] == "jumbo"
        assert dims["lower_bout"] == CANONICAL_JUMBO["lower_bout_mm"]
        assert dims["upper_bout"] == CANONICAL_JUMBO["upper_bout_mm"]
        assert dims["waist"] == CANONICAL_JUMBO["waist_mm"]
        assert dims["body_length"] == CANONICAL_JUMBO["body_length_mm"]

    def test_body_outline_editor_matches_canonical(self):
        """Path 4: Body Outline Editor INSTRUMENT_TEMPLATES matches canonical.

        This is a JS file, so we parse it with regex to extract the jumbo dimensions.
        """
        import re

        editor_path = Path(__file__).parent.parent.parent.parent / "hostinger" / "body-outline-editor.html"

        content = editor_path.read_text(encoding="utf-8")

        # Find the jumbo template block
        pattern = r"jumbo:\s*\{[^}]*dimensions:\s*\{([^}]+)\}"
        match = re.search(pattern, content)
        assert match, "Could not find jumbo template in body-outline-editor.html"

        dims_str = match.group(1)

        # Extract individual values
        def extract_value(key):
            m = re.search(rf"{key}:\s*(\d+(?:\.\d+)?)", dims_str)
            return float(m.group(1)) if m else None

        assert extract_value("lowerBout") == CANONICAL_JUMBO["lower_bout_mm"]
        assert extract_value("upperBout") == CANONICAL_JUMBO["upper_bout_mm"]
        assert extract_value("waist") == CANONICAL_JUMBO["waist_mm"]
        assert extract_value("bodyLength") == CANONICAL_JUMBO["body_length_mm"]
        assert extract_value("waistYNorm") == CANONICAL_JUMBO["waist_y_norm"]


class TestCatalogJsonOutOfScope:
    """Document that catalog.json is NOT aligned — needs investigation."""

    @pytest.mark.skip(reason="catalog.json 'jumbo' appears to be DXF bounding box, not body dimensions — needs investigation")
    def test_catalog_json_jumbo_dimensions(self):
        """catalog.json 'jumbo' has width: 474.2, height: 385.1 — does not match canonical.

        This is likely a DXF bounding box from acoustic/Jumbo_body.dxf, not body measurements.
        Requires investigation before alignment.
        """
        pass
