"""
Instrument Family Dimension Consistency Test

CI guard that asserts all sources of family dimensions agree.
This test is expected to FAIL when divergences exist - the failures
document the current state and prevent new divergences.

Sources checked:
1. IBG FAMILY_DEFAULTS (body_contour_solver.py) - canonical for IBG families
2. BODY_DIMENSIONS (instrument_specs.py) - photo vectorizer reference
3. body_dimension_reference.json - photo vectorizer JSON copy
4. INSTRUMENT_TEMPLATES (body-outline-editor.html) - frontend templates
5. body_templates.json - data registry templates
6. instrument_model_registry.json - registry body_dimensions_mm

Excluded sources:
- catalog.json - contains DXF bounding boxes, not body landmark dimensions
- bezier_body.py - uses inches, different purpose
- guitars/*.py MODEL_INFO - different schema (body_width_mm vs bouts)

Date: 2026-05-27
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_repo_root() -> Path:
    """Get repository root from test file location."""
    return Path(__file__).parent.parent.parent.parent


def load_family_defaults() -> Dict[str, Dict[str, float]]:
    """Load IBG FAMILY_DEFAULTS from body_contour_solver.py via regex parsing.

    We parse the file directly to avoid importing the full module chain
    which requires ezdxf/numpy and can have import issues in test context.
    """
    path = get_repo_root() / "services" / "api" / "app" / "instrument_geometry" / "body" / "ibg" / "body_contour_solver.py"
    content = path.read_text(encoding="utf-8")

    # Find FAMILY_DEFAULTS dict - it starts at FAMILY_DEFAULTS = { and ends at ^}
    start_marker = "FAMILY_DEFAULTS = {"
    start_idx = content.find(start_marker)
    if start_idx == -1:
        return {}

    # Find matching closing brace
    brace_count = 1
    idx = start_idx + len(start_marker)
    while idx < len(content) and brace_count > 0:
        if content[idx] == '{':
            brace_count += 1
        elif content[idx] == '}':
            brace_count -= 1
        idx += 1

    family_defaults_str = content[start_idx:idx]

    # Parse each family entry - match "family_name": { ... },
    result = {}
    # This pattern finds: "name": { content },
    family_pattern = r'"(\w+)":\s*\{([^}]+(?:#[^\n]*\n[^}]*)*)\}'
    for fmatch in re.finditer(family_pattern, family_defaults_str, re.DOTALL):
        name = fmatch.group(1)
        body = fmatch.group(2)

        def extract_float(key):
            # Match: "key": value, or "key": value.value,
            m = re.search(rf'"{key}":\s*([\d.]+)', body)
            return float(m.group(1)) if m else 0

        result[name] = {
            "lower_bout_mm": extract_float("lower_bout_mm"),
            "upper_bout_mm": extract_float("upper_bout_mm"),
            "waist_mm": extract_float("waist_mm"),
            "body_length_mm": extract_float("body_length_mm"),
            "waist_y_norm": extract_float("waist_y_norm"),
        }

    return result


def load_body_dimensions() -> Dict[str, Dict[str, float]]:
    """Load BODY_DIMENSIONS from instrument_specs.py via regex parsing.

    We parse the file directly to avoid import chain issues in test context.
    """
    path = get_repo_root() / "services" / "api" / "app" / "instrument_geometry" / "instrument_specs.py"
    content = path.read_text(encoding="utf-8")

    result = {}
    # Match BodyDimensions entries like:
    # "stratocaster": BodyDimensions(
    #     body_length_mm=406,
    #     upper_bout_width_mm=311,
    #     ...
    # ),
    pattern = r'"(\w+)":\s*BodyDimensions\(\s*([^)]+)\)'
    for match in re.finditer(pattern, content, re.DOTALL):
        name = match.group(1)
        body = match.group(2)

        def extract_float(key):
            m = re.search(rf'{key}=([\d.]+)', body)
            return float(m.group(1)) if m else 0

        result[name] = {
            "lower_bout_mm": extract_float("lower_bout_width_mm"),
            "upper_bout_mm": extract_float("upper_bout_width_mm"),
            "waist_mm": extract_float("waist_width_mm"),
            "body_length_mm": extract_float("body_length_mm"),
            "waist_y_norm": extract_float("waist_y_norm"),
        }

    return result


def load_body_dimension_reference() -> Dict[str, Dict[str, float]]:
    """Load body_dimension_reference.json from photo-vectorizer."""
    path = get_repo_root() / "services" / "photo-vectorizer" / "body_dimension_reference.json"
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    result = {}
    for name, entry in data.items():
        if name.startswith("_"):
            continue
        result[name] = {
            "lower_bout_mm": entry.get("lower_bout_width_mm", 0),
            "upper_bout_mm": entry.get("upper_bout_width_mm", 0),
            "waist_mm": entry.get("waist_width_mm", 0),
            "body_length_mm": entry.get("body_length_mm", 0),
            "waist_y_norm": entry.get("waist_y_norm", 0),
        }
    return result


def load_instrument_templates() -> Dict[str, Dict[str, float]]:
    """Parse INSTRUMENT_TEMPLATES from body-outline-editor.html."""
    path = get_repo_root() / "hostinger" / "body-outline-editor.html"
    if not path.exists():
        return {}

    content = path.read_text(encoding="utf-8")

    # Find the INSTRUMENT_TEMPLATES block
    pattern = r"const INSTRUMENT_TEMPLATES = \{([^;]+)\};"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return {}

    templates_str = match.group(1)

    result = {}
    # Parse each template
    template_pattern = r"(\w+):\s*\{[^}]*dimensions:\s*\{([^}]+)\}"
    for tmatch in re.finditer(template_pattern, templates_str):
        name = tmatch.group(1)
        dims_str = tmatch.group(2)

        def extract(key):
            m = re.search(rf"{key}:\s*(\d+(?:\.\d+)?)", dims_str)
            return float(m.group(1)) if m else 0

        result[name] = {
            "lower_bout_mm": extract("lowerBout"),
            "upper_bout_mm": extract("upperBout"),
            "waist_mm": extract("waist"),
            "body_length_mm": extract("bodyLength"),
            "waist_y_norm": extract("waistYNorm"),
        }

    return result


def load_body_templates() -> Dict[str, Dict[str, float]]:
    """Load body_templates.json from data_registry."""
    path = get_repo_root() / "services" / "api" / "app" / "data_registry" / "system" / "instruments" / "body_templates.json"
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    result = {}
    for name, entry in data.get("bodies", {}).items():
        dims = entry.get("dimensions", {})
        # Schema varies - acoustic uses bout fields, electric uses length/width
        if "lower_bout_mm" in dims:
            result[name] = {
                "lower_bout_mm": dims.get("lower_bout_mm", 0),
                "upper_bout_mm": dims.get("upper_bout_mm", 0),
                "waist_mm": dims.get("waist_mm", 0),
                "body_length_mm": dims.get("length_mm", 0),
                "waist_y_norm": 0,  # Not present in this source
            }

    return result


def load_registry_dimensions() -> Dict[str, Dict[str, float]]:
    """Load body_dimensions_mm from instrument_model_registry.json."""
    path = get_repo_root() / "services" / "api" / "app" / "instrument_geometry" / "instrument_model_registry.json"
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    result = {}
    for model_id, entry in data.get("models", {}).items():
        dims = entry.get("body_dimensions_mm", {})
        if dims:
            result[model_id] = {
                "lower_bout_mm": dims.get("lower_bout", 0),
                "upper_bout_mm": dims.get("upper_bout", 0),
                "waist_mm": dims.get("waist", 0),
                "body_length_mm": dims.get("body_length", 0),
                "waist_y_norm": 0,  # Not present in this source
            }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Test Classes
# ─────────────────────────────────────────────────────────────────────────────

def load_instrument_specs_ibg() -> Dict[str, Dict[str, float]]:
    """Load INSTRUMENT_SPECS from instrument_body_generator.py via regex parsing.

    This contains per-instrument expected_dimensions, separate from FAMILY_DEFAULTS.
    Structure:
        INSTRUMENT_SPECS = {
            "dreadnought": { ... "expected_dimensions": { ... } },
            "jumbo": { ... "expected_dimensions": { ... } },
        }
    """
    path = get_repo_root() / "services" / "api" / "app" / "instrument_geometry" / "body" / "ibg" / "instrument_body_generator.py"
    content = path.read_text(encoding="utf-8")

    # First find the INSTRUMENT_SPECS block (may have type hint)
    start = content.find("INSTRUMENT_SPECS:")
    if start == -1:
        start = content.find("INSTRUMENT_SPECS = {")
    if start == -1:
        return {}

    # Find the opening brace after INSTRUMENT_SPECS
    brace_start = content.find("{", start)
    if brace_start == -1:
        return {}
    start = brace_start

    # Find the matching closing brace
    brace_count = 1
    idx = start + 1  # Start after the opening brace
    while idx < len(content) and brace_count > 0:
        if content[idx] == '{':
            brace_count += 1
        elif content[idx] == '}':
            brace_count -= 1
        idx += 1

    specs_block = content[start:idx]

    result = {}
    # Find instrument entries: "name": { "family": ..., "constraints": {...}, "expected_dimensions": {...} }
    instruments = ["dreadnought", "cuatro_venezolano", "stratocaster", "jumbo"]

    for inst in instruments:
        # Find this instrument's expected_dimensions - allow nested braces
        pattern = rf'"{inst}":\s*\{{.*?"expected_dimensions":\s*\{{([^}}]+)\}}'
        match = re.search(pattern, specs_block, re.DOTALL)
        if match:
            dims_str = match.group(1)

            def extract_float(key):
                m = re.search(rf'"{key}":\s*([\d.]+)', dims_str)
                return float(m.group(1)) if m else 0

            result[inst] = {
                "lower_bout_mm": extract_float("lower_bout_mm"),
                "upper_bout_mm": extract_float("upper_bout_mm"),
                "waist_mm": extract_float("waist_mm"),
                "body_length_mm": extract_float("body_length_mm"),
            }

    return result


class TestAcousticFlatTopConsistency:
    """Consistency checks for acoustic flat-top families."""

    def test_dreadnought_dimensions_consistent(self):
        """Dreadnought dimensions should match across all sources."""
        family_defaults = load_family_defaults()
        body_dims = load_body_dimensions()
        templates = load_instrument_templates()
        body_templates = load_body_templates()

        canonical = family_defaults["dreadnought"]

        # Check instrument_specs.py
        if "dreadnought" in body_dims:
            assert body_dims["dreadnought"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"instrument_specs.py dreadnought lower_bout {body_dims['dreadnought']['lower_bout_mm']} != canonical {canonical['lower_bout_mm']}"
            assert body_dims["dreadnought"]["upper_bout_mm"] == canonical["upper_bout_mm"], \
                f"instrument_specs.py dreadnought upper_bout diverges"
            assert body_dims["dreadnought"]["waist_mm"] == canonical["waist_mm"], \
                f"instrument_specs.py dreadnought waist diverges"
            assert body_dims["dreadnought"]["body_length_mm"] == canonical["body_length_mm"], \
                f"instrument_specs.py dreadnought body_length diverges"

        # Check body-outline-editor.html
        if "dreadnought" in templates:
            assert templates["dreadnought"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"body-outline-editor.html dreadnought lower_bout {templates['dreadnought']['lower_bout_mm']} != canonical {canonical['lower_bout_mm']}"
            assert templates["dreadnought"]["upper_bout_mm"] == canonical["upper_bout_mm"], \
                f"body-outline-editor.html dreadnought upper_bout diverges"
            assert templates["dreadnought"]["waist_mm"] == canonical["waist_mm"], \
                f"body-outline-editor.html dreadnought waist diverges"
            assert templates["dreadnought"]["body_length_mm"] == canonical["body_length_mm"], \
                f"body-outline-editor.html dreadnought body_length diverges"

        # Check body_templates.json
        if "dreadnought" in body_templates:
            assert body_templates["dreadnought"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"body_templates.json dreadnought lower_bout {body_templates['dreadnought']['lower_bout_mm']} != canonical {canonical['lower_bout_mm']}"

    def test_jumbo_dimensions_consistent(self):
        """Jumbo dimensions should match across all sources."""
        family_defaults = load_family_defaults()
        body_dims = load_body_dimensions()
        templates = load_instrument_templates()
        body_templates = load_body_templates()
        registry = load_registry_dimensions()

        # Canonical source is FAMILY_DEFAULTS in body_contour_solver.py
        assert "jumbo" in family_defaults, \
            "jumbo missing from FAMILY_DEFAULTS in body_contour_solver.py"

        canonical = family_defaults["jumbo"]

        # Check instrument_specs.py
        if "jumbo" in body_dims:
            assert body_dims["jumbo"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"instrument_specs.py jumbo lower_bout {body_dims['jumbo']['lower_bout_mm']} != canonical {canonical['lower_bout_mm']}"
            assert body_dims["jumbo"]["upper_bout_mm"] == canonical["upper_bout_mm"], \
                f"instrument_specs.py jumbo upper_bout {body_dims['jumbo']['upper_bout_mm']} != canonical {canonical['upper_bout_mm']}"
            assert body_dims["jumbo"]["waist_mm"] == canonical["waist_mm"], \
                f"instrument_specs.py jumbo waist {body_dims['jumbo']['waist_mm']} != canonical {canonical['waist_mm']}"
            assert body_dims["jumbo"]["body_length_mm"] == canonical["body_length_mm"], \
                f"instrument_specs.py jumbo body_length {body_dims['jumbo']['body_length_mm']} != canonical {canonical['body_length_mm']}"

        # Check body-outline-editor.html
        if "jumbo" in templates:
            assert templates["jumbo"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"body-outline-editor.html jumbo lower_bout diverges"
            assert templates["jumbo"]["upper_bout_mm"] == canonical["upper_bout_mm"], \
                f"body-outline-editor.html jumbo upper_bout diverges"

        # Check registry jumbo_j200
        if "jumbo_j200" in registry:
            assert registry["jumbo_j200"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"registry jumbo_j200 lower_bout diverges"
            assert registry["jumbo_j200"]["upper_bout_mm"] == canonical["upper_bout_mm"], \
                f"registry jumbo_j200 upper_bout diverges"

        # Check body_templates.json
        if "jumbo" in body_templates:
            assert body_templates["jumbo"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"body_templates.json jumbo lower_bout {body_templates['jumbo']['lower_bout_mm']} != canonical {canonical['lower_bout_mm']}"
            assert body_templates["jumbo"]["upper_bout_mm"] == canonical["upper_bout_mm"], \
                f"body_templates.json jumbo upper_bout {body_templates['jumbo']['upper_bout_mm']} != canonical {canonical['upper_bout_mm']}"
            assert body_templates["jumbo"]["waist_mm"] == canonical["waist_mm"], \
                f"body_templates.json jumbo waist {body_templates['jumbo']['waist_mm']} != canonical {canonical['waist_mm']}"


class TestElectricSolidBodyConsistency:
    """Consistency checks for electric solid-body families."""

    def test_stratocaster_dimensions_consistent(self):
        """Stratocaster dimensions should match across sources that have it."""
        family_defaults = load_family_defaults()
        body_dims = load_body_dimensions()
        templates = load_instrument_templates()

        canonical = family_defaults["stratocaster"]

        # Check instrument_specs.py
        if "stratocaster" in body_dims:
            assert body_dims["stratocaster"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"instrument_specs.py stratocaster lower_bout {body_dims['stratocaster']['lower_bout_mm']} != canonical {canonical['lower_bout_mm']}"
            assert body_dims["stratocaster"]["body_length_mm"] == canonical["body_length_mm"], \
                f"instrument_specs.py stratocaster body_length diverges"

        # Check body-outline-editor.html
        if "stratocaster" in templates:
            assert templates["stratocaster"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"body-outline-editor.html stratocaster lower_bout {templates['stratocaster']['lower_bout_mm']} != canonical {canonical['lower_bout_mm']}"


class TestCuatroDimensionConsistency:
    """Consistency checks for cuatro family."""

    def test_cuatro_venezolano_dimensions_consistent(self):
        """Cuatro venezolano dimensions should match across sources."""
        family_defaults = load_family_defaults()
        body_dims = load_body_dimensions()

        canonical = family_defaults["cuatro_venezolano"]

        # Check instrument_specs.py (uses "cuatro" key)
        if "cuatro" in body_dims:
            assert body_dims["cuatro"]["lower_bout_mm"] == canonical["lower_bout_mm"], \
                f"instrument_specs.py cuatro lower_bout {body_dims['cuatro']['lower_bout_mm']} != canonical {canonical['lower_bout_mm']}"
            assert body_dims["cuatro"]["upper_bout_mm"] == canonical["upper_bout_mm"], \
                f"instrument_specs.py cuatro upper_bout {body_dims['cuatro']['upper_bout_mm']} != canonical {canonical['upper_bout_mm']}"
            assert body_dims["cuatro"]["waist_mm"] == canonical["waist_mm"], \
                f"instrument_specs.py cuatro waist {body_dims['cuatro']['waist_mm']} != canonical {canonical['waist_mm']}"
            assert body_dims["cuatro"]["body_length_mm"] == canonical["body_length_mm"], \
                f"instrument_specs.py cuatro body_length {body_dims['cuatro']['body_length_mm']} != canonical {canonical['body_length_mm']}"


class TestCrossSourceConsistency:
    """Tests that verify body_dimension_reference.json matches instrument_specs.py."""

    def test_body_dimension_reference_matches_instrument_specs(self):
        """body_dimension_reference.json should match instrument_specs.py BODY_DIMENSIONS.

        These are documented as being the same data, so divergence indicates
        one was updated without the other.
        """
        body_dims = load_body_dimensions()
        ref_dims = load_body_dimension_reference()

        common_keys = set(body_dims.keys()) & set(ref_dims.keys())

        for key in common_keys:
            bd = body_dims[key]
            rd = ref_dims[key]

            assert bd["lower_bout_mm"] == rd["lower_bout_mm"], \
                f"{key} lower_bout mismatch: instrument_specs={bd['lower_bout_mm']}, reference={rd['lower_bout_mm']}"
            assert bd["upper_bout_mm"] == rd["upper_bout_mm"], \
                f"{key} upper_bout mismatch"
            assert bd["waist_mm"] == rd["waist_mm"], \
                f"{key} waist mismatch"
            assert bd["body_length_mm"] == rd["body_length_mm"], \
                f"{key} body_length mismatch"


class TestCoverageGaps:
    """Document which categories are missing from FAMILY_DEFAULTS."""

    def test_archtop_families_in_family_defaults(self):
        """FAMILY_DEFAULTS should have archtop entries (currently missing)."""
        family_defaults = load_family_defaults()

        # These should exist but don't
        archtop_families = ["es335", "benedetto_17", "jumbo_archtop", "l5", "super_400"]
        present = [f for f in archtop_families if f in family_defaults]

        assert len(present) > 0, \
            f"No archtop families in FAMILY_DEFAULTS. Missing: {archtop_families}"

    def test_bass_families_in_family_defaults(self):
        """FAMILY_DEFAULTS should have bass entries (currently missing)."""
        family_defaults = load_family_defaults()

        bass_families = ["bass_4string", "jazz_bass", "precision_bass", "short_scale_bass"]
        present = [f for f in bass_families if f in family_defaults]

        assert len(present) > 0, \
            f"No bass families in FAMILY_DEFAULTS. Missing: {bass_families}"

    def test_ukulele_families_in_family_defaults(self):
        """FAMILY_DEFAULTS should have ukulele entries (currently missing)."""
        family_defaults = load_family_defaults()

        ukulele_families = ["soprano", "concert_uke", "tenor_uke", "baritone_uke"]
        present = [f for f in ukulele_families if f in family_defaults]

        assert len(present) > 0, \
            f"No ukulele families in FAMILY_DEFAULTS. Missing: {ukulele_families}"

    def test_electric_families_coverage(self):
        """FAMILY_DEFAULTS should have more than just stratocaster for electrics."""
        family_defaults = load_family_defaults()

        electric_families = ["stratocaster", "les_paul", "telecaster", "sg", "flying_v", "explorer"]
        present = [f for f in electric_families if f in family_defaults]

        assert len(present) >= 3, \
            f"Only {len(present)} electric families in FAMILY_DEFAULTS: {present}. Expected at least 3."
