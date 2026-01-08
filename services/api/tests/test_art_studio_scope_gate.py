#!/usr/bin/env python3
"""
Unit tests for Art Studio Scope Gate.

These tests verify that the scope gate correctly:
- Detects forbidden patterns (host geometry, machine output, authority)
- Respects inline SCOPE_ALLOW exceptions
- Handles file structure detection
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

import pytest

# Add scripts/ci to path for import
REPO_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "ci"))

from check_art_studio_scope import (
    FORBIDDEN_PATTERNS,
    Finding,
    _detect_frontend_targets,
    _line_has_allow,
    scan_file,
)


class TestForbiddenPatterns:
    """Test that forbidden patterns catch violations correctly."""

    def test_host_geometry_headstock(self):
        """Headstock references should be flagged."""
        line = "const headstockOutline = generateHeadstock();"
        matches = [
            (tag, pat)
            for tag, pat in FORBIDDEN_PATTERNS
            if re.search(pat, line, flags=re.IGNORECASE)
        ]
        assert len(matches) > 0, "headstock should be caught by HOST_GEOMETRY"
        assert any(tag == "HOST_GEOMETRY" for tag, _ in matches)

    def test_host_geometry_bridge(self):
        """Bridge references should be flagged."""
        line = "def compute_bridge_geometry():"
        matches = [
            (tag, pat)
            for tag, pat in FORBIDDEN_PATTERNS
            if re.search(pat, line, flags=re.IGNORECASE)
        ]
        assert len(matches) > 0, "bridge should be caught by HOST_GEOMETRY"

    def test_host_geometry_tuner(self):
        """Tuner references should be flagged."""
        line = "tuner_hole_positions = [...]"
        matches = [
            (tag, pat)
            for tag, pat in FORBIDDEN_PATTERNS
            if re.search(pat, line, flags=re.IGNORECASE)
        ]
        assert len(matches) > 0, "tuner_hole should be caught"

    def test_machine_output_gcode(self):
        """G-code references should be flagged."""
        line = "gcode = generate_gcode(toolpath)"
        matches = [
            (tag, pat)
            for tag, pat in FORBIDDEN_PATTERNS
            if re.search(pat, line, flags=re.IGNORECASE)
        ]
        assert len(matches) > 0, "gcode should be caught by MACHINE_OUTPUT"
        assert any(tag == "MACHINE_OUTPUT" for tag, _ in matches)

    def test_machine_output_toolpath(self):
        """Toolpath references should be flagged."""
        line = "const toolpaths = computeToolpaths();"
        matches = [
            (tag, pat)
            for tag, pat in FORBIDDEN_PATTERNS
            if re.search(pat, line, flags=re.IGNORECASE)
        ]
        assert len(matches) > 0, "toolpaths should be caught by MACHINE_OUTPUT"

    def test_authority_create_run_id(self):
        """create_run_id references should be flagged."""
        line = "run_id = create_run_id()"
        matches = [
            (tag, pat)
            for tag, pat in FORBIDDEN_PATTERNS
            if re.search(pat, line, flags=re.IGNORECASE)
        ]
        assert len(matches) > 0, "create_run_id should be caught by AUTHORITY"
        assert any(tag == "AUTHORITY" for tag, _ in matches)

    def test_authority_bulk_review(self):
        """bulk-review API references should be flagged."""
        line = 'await fetch("/api/rmos/bulk-review", { method: "POST" })'
        matches = [
            (tag, pat)
            for tag, pat in FORBIDDEN_PATTERNS
            if re.search(pat, line, flags=re.IGNORECASE)
        ]
        assert len(matches) > 0, "bulk-review should be caught by AUTHORITY"

    def test_safe_ornament_terms(self):
        """Ornament-related terms should NOT be flagged."""
        safe_lines = [
            "const rosette = new RosetteSpec();",
            "inlay_pattern = InlayPatternSpec(rings=[...])",
            "mosaic_tiles = generate_mosaic()",
            "ring_width = 2.5",
        ]
        for line in safe_lines:
            matches = [
                (tag, pat)
                for tag, pat in FORBIDDEN_PATTERNS
                if re.search(pat, line, flags=re.IGNORECASE)
            ]
            assert len(matches) == 0, f"'{line}' should NOT be flagged"


class TestInlineAllow:
    """Test inline SCOPE_ALLOW mechanism."""

    def test_allow_exact_tag(self):
        """SCOPE_ALLOW: TAG should allow that specific tag."""
        line = "headstock_ref = ...  # SCOPE_ALLOW: HOST_GEOMETRY needed for adapter"
        assert _line_has_allow(line, "HOST_GEOMETRY") is True

    def test_allow_case_insensitive(self):
        """SCOPE_ALLOW should be case-insensitive."""
        line = "gcode = ...  # scope_allow: machine_output for export"
        assert _line_has_allow(line, "MACHINE_OUTPUT") is True

    def test_allow_wrong_tag(self):
        """SCOPE_ALLOW: WRONG_TAG should not allow different tag."""
        line = "headstock = ...  # SCOPE_ALLOW: MACHINE_OUTPUT"
        assert _line_has_allow(line, "HOST_GEOMETRY") is False

    def test_no_allow(self):
        """Lines without SCOPE_ALLOW should not be allowed."""
        line = "headstock = generate_headstock()"
        assert _line_has_allow(line, "HOST_GEOMETRY") is False


class TestScanFile:
    """Test file scanning functionality."""

    def test_scan_clean_file(self):
        """Clean files should produce no findings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            test_file = root / "clean.py"
            test_file.write_text(
                """
# Art Studio rosette generator
def generate_rosette(rings):
    return RosetteParamSpec(rings=rings)
"""
            )
            findings = scan_file(root, test_file)
            assert len(findings) == 0

    def test_scan_violation_file(self):
        """Files with violations should be caught."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            test_file = root / "bad.py"
            test_file.write_text(
                """
# Bad Art Studio file
def generate_headstock():
    gcode = create_toolpath()
    return gcode
"""
            )
            findings = scan_file(root, test_file)
            assert len(findings) >= 2
            tags = {f.tag for f in findings}
            assert "HOST_GEOMETRY" in tags
            assert "MACHINE_OUTPUT" in tags

    def test_scan_with_inline_allow(self):
        """Inline SCOPE_ALLOW should suppress specific violations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            test_file = root / "allowed.py"
            test_file.write_text(
                """
# Placement adapter - legitimately needs host geometry reference
headstock_bounds = get_bounds()  # SCOPE_ALLOW: HOST_GEOMETRY adapter
gcode = create_toolpath()  # No allow - should be caught
"""
            )
            findings = scan_file(root, test_file)
            # headstock should be allowed, gcode should be caught
            tags = [f.tag for f in findings]
            assert "HOST_GEOMETRY" not in tags
            assert "MACHINE_OUTPUT" in tags


class TestFrontendDetection:
    """Test frontend structure detection."""

    def test_detect_monorepo_structure(self):
        """Should detect packages/client/src structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "packages" / "client" / "src").mkdir(parents=True)
            targets = _detect_frontend_targets(root)
            assert any("packages/client/src" in t for t in targets)

    def test_detect_flat_structure(self):
        """Should use default targets for flat structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "client" / "src").mkdir(parents=True)
            targets = _detect_frontend_targets(root)
            assert any("client/src" in t for t in targets)


class TestFindingDataclass:
    """Test Finding dataclass."""

    def test_finding_fields(self):
        """Finding should have all required fields."""
        f = Finding(
            tag="HOST_GEOMETRY",
            relpath="art_studio/bad.py",
            line_no=42,
            line="headstock = ...",
            pattern=r"\bheadstock\b",
        )
        assert f.tag == "HOST_GEOMETRY"
        assert f.relpath == "art_studio/bad.py"
        assert f.line_no == 42
        assert "headstock" in f.line
        assert f.pattern == r"\bheadstock\b"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
