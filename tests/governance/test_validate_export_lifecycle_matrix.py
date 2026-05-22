"""
Tests for export lifecycle classification matrix validator.

Part of Runtime Boundary Follow-Through Sprint, Phase 1D.
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "governance"))

from validate_export_lifecycle_matrix import (
    parse_sections_by_markers,
    parse_sections_by_headings,
    parse_table_rows,
    validate_production_row,
    validate_blocked_row,
    validate_excluded_row,
    validate_matrix,
    LIFECYCLE_STATUS_LABELS,
    REQUIRED_SECTIONS,
    VALID_GUARD_STATUSES,
)


class TestParseSectionsByMarkers:
    """Tests for marker-based section parsing."""

    def test_parses_single_marker(self):
        content = "<!-- SECTION:FOO -->\nSome content here"
        sections, found = parse_sections_by_markers(content)
        assert found is True
        assert "FOO" in sections
        assert "Some content here" in sections["FOO"]

    def test_parses_multiple_markers(self):
        content = """<!-- SECTION:A -->
Content A
<!-- SECTION:B -->
Content B
<!-- SECTION:C -->
Content C"""
        sections, found = parse_sections_by_markers(content)
        assert found is True
        assert len(sections) == 3
        assert "Content A" in sections["A"]
        assert "Content B" in sections["B"]
        assert "Content C" in sections["C"]

    def test_returns_false_when_no_markers(self):
        content = "No markers here\nJust plain text"
        sections, found = parse_sections_by_markers(content)
        assert found is False
        assert sections == {}


class TestParseSectionsByHeadings:
    """Tests for heading-based section parsing (fallback)."""

    def test_parses_section_headings(self):
        content = """## Section 1: Production Runtime Exports
Production content here

## Section 2: Test Fixtures
Test content here"""
        sections = parse_sections_by_headings(content)
        assert "PRODUCTION_RUNTIME_EXPORTS" in sections
        assert "TEST_FIXTURES" in sections

    def test_returns_empty_when_no_headings(self):
        content = "No section headings here"
        sections = parse_sections_by_headings(content)
        assert sections == {}


class TestParseTableRows:
    """Tests for markdown table parsing."""

    def test_parses_simple_table(self):
        content = """
| File | Status | Risk |
|------|--------|------|
| foo.py | COMPAT_ONLY | LOW |
| bar.py | LIFECYCLE_GOVERNED | LOW |
"""
        rows = parse_table_rows(content)
        assert len(rows) == 2
        assert rows[0]["File"] == "foo.py"
        assert rows[0]["Status"] == "COMPAT_ONLY"
        assert rows[1]["File"] == "bar.py"

    def test_handles_backticks_in_cells(self):
        content = """
| File | Lifecycle Status |
|------|------------------|
| `cam/dxf_writer.py` | COMPAT_ONLY |
"""
        rows = parse_table_rows(content)
        assert len(rows) == 1
        assert rows[0]["File"] == "`cam/dxf_writer.py`"

    def test_handles_empty_table(self):
        content = "No table here"
        rows = parse_table_rows(content)
        assert rows == []


class TestValidateProductionRow:
    """Tests for production row validation."""

    def test_valid_row_passes(self):
        row = {
            "File": "foo.py",
            "Export Type": "dxf-create-save",
            "Lifecycle Status": "COMPAT_ONLY",
            "Risk": "LOW",
            "Disposition": "no_action",
            "Guard Status": "GUARD_CANDIDATE",
        }
        errors, warnings = validate_production_row(row, "PRODUCTION_RUNTIME_EXPORTS")
        assert errors == []
        assert warnings == []

    def test_missing_file_fails(self):
        row = {
            "File": "",
            "Lifecycle Status": "COMPAT_ONLY",
            "Risk": "LOW",
            "Disposition": "no_action",
            "Guard Status": "GUARD_CANDIDATE",
        }
        errors, warnings = validate_production_row(row, "PRODUCTION_RUNTIME_EXPORTS")
        assert len(errors) == 1
        assert "missing File" in errors[0]

    def test_missing_lifecycle_status_fails(self):
        row = {
            "File": "foo.py",
            "Risk": "LOW",
            "Disposition": "no_action",
            "Guard Status": "GUARD_CANDIDATE",
        }
        errors, warnings = validate_production_row(row, "PRODUCTION_RUNTIME_EXPORTS")
        assert len(errors) == 1
        assert "missing Lifecycle Status" in errors[0]

    def test_invalid_lifecycle_status_fails(self):
        row = {
            "File": "foo.py",
            "Lifecycle Status": "INVALID_STATUS",
            "Risk": "LOW",
            "Disposition": "no_action",
            "Guard Status": "GUARD_CANDIDATE",
        }
        errors, warnings = validate_production_row(row, "PRODUCTION_RUNTIME_EXPORTS")
        assert len(errors) == 1
        assert "unknown Lifecycle Status" in errors[0]

    def test_missing_guard_status_warns(self):
        row = {
            "File": "foo.py",
            "Export Type": "dxf-create-save",
            "Lifecycle Status": "COMPAT_ONLY",
            "Risk": "LOW",
            "Disposition": "no_action",
        }
        errors, warnings = validate_production_row(row, "PRODUCTION_RUNTIME_EXPORTS")
        assert errors == []
        assert len(warnings) == 1
        assert "missing Guard Status" in warnings[0]

    def test_invalid_guard_status_warns(self):
        row = {
            "File": "foo.py",
            "Export Type": "dxf-create-save",
            "Lifecycle Status": "COMPAT_ONLY",
            "Risk": "LOW",
            "Disposition": "no_action",
            "Guard Status": "INVALID_STATUS",
        }
        errors, warnings = validate_production_row(row, "PRODUCTION_RUNTIME_EXPORTS")
        assert errors == []
        assert len(warnings) == 1
        assert "unknown Guard Status" in warnings[0]

    def test_guard_added_passes(self):
        row = {
            "File": "foo.py",
            "Export Type": "dxf-create-save",
            "Lifecycle Status": "COMPAT_ONLY",
            "Risk": "LOW",
            "Disposition": "guarded_2a",
            "Guard Status": "GUARD_ADDED",
        }
        errors, warnings = validate_production_row(row, "PRODUCTION_RUNTIME_EXPORTS")
        assert errors == []
        assert warnings == []


class TestValidateBlockedRow:
    """Tests for BLOCKED_PROVENANCE row validation."""

    def test_blocked_status_passes(self):
        row = {
            "File": "ibg/solver.py",
            "Lifecycle Status": "BLOCKED_PROVENANCE",
            "Guard Status": "BLOCKED_PROVENANCE",
        }
        errors, warnings = validate_blocked_row(row)
        assert errors == []
        assert warnings == []

    def test_compat_only_allowed(self):
        row = {
            "File": "ibg/solver.py",
            "Lifecycle Status": "COMPAT_ONLY",
            "Guard Status": "BLOCKED_PROVENANCE",
        }
        errors, warnings = validate_blocked_row(row)
        assert errors == []
        assert warnings == []

    def test_lifecycle_governed_fails(self):
        row = {
            "File": "ibg/solver.py",
            "Lifecycle Status": "LIFECYCLE_GOVERNED",
            "Guard Status": "BLOCKED_PROVENANCE",
        }
        errors, warnings = validate_blocked_row(row)
        assert len(errors) == 1
        assert "incorrectly marked as LIFECYCLE_GOVERNED" in errors[0]

    def test_excluded_status_fails(self):
        row = {
            "File": "ibg/solver.py",
            "Lifecycle Status": "TEST_ONLY",
            "Guard Status": "BLOCKED_PROVENANCE",
        }
        errors, warnings = validate_blocked_row(row)
        assert len(errors) == 1
        assert "unexpected status" in errors[0]

    def test_wrong_guard_status_fails(self):
        row = {
            "File": "ibg/solver.py",
            "Lifecycle Status": "BLOCKED_PROVENANCE",
            "Guard Status": "GUARD_CANDIDATE",
        }
        errors, warnings = validate_blocked_row(row)
        assert len(errors) == 1
        assert "should be BLOCKED_PROVENANCE" in errors[0]


class TestValidateExcludedRow:
    """Tests for TEST/R&D row validation."""

    def test_test_only_passes(self):
        row = {
            "File": "tests/test_foo.py",
            "Lifecycle Status": "TEST_ONLY",
            "Guard Status": "NOT_APPLICABLE",
        }
        errors, warnings = validate_excluded_row(row, "TEST_FIXTURES")
        assert errors == []
        assert warnings == []

    def test_rnd_excluded_passes(self):
        row = {
            "File": "photo-vectorizer/foo.py",
            "Lifecycle Status": "R_AND_D_EXCLUDED",
            "Guard Status": "NOT_APPLICABLE",
        }
        errors, warnings = validate_excluded_row(row, "R_AND_D_SANDBOX")
        assert errors == []
        assert warnings == []

    def test_production_status_warns(self):
        row = {
            "File": "tests/test_foo.py",
            "Lifecycle Status": "COMPAT_ONLY",
            "Guard Status": "NOT_APPLICABLE",
        }
        errors, warnings = validate_excluded_row(row, "TEST_FIXTURES")
        assert errors == []
        assert len(warnings) == 1
        assert "should be excluded" in warnings[0]

    def test_wrong_guard_status_warns(self):
        row = {
            "File": "tests/test_foo.py",
            "Lifecycle Status": "TEST_ONLY",
            "Guard Status": "GUARD_CANDIDATE",
        }
        errors, warnings = validate_excluded_row(row, "TEST_FIXTURES")
        assert errors == []
        assert len(warnings) == 1
        assert "should be NOT_APPLICABLE" in warnings[0]


class TestValidateMatrix:
    """Integration tests for full matrix validation."""

    def test_minimal_valid_matrix(self):
        content = """# Export Lifecycle Classification Matrix

### Lifecycle Status Labels

| Label | Meaning |
|-------|---------|
| `LIFECYCLE_GOVERNED` | Full gate |
| `COMPAT_ONLY` | Compat only |
| `DIRECT_SAVE_GAP` | Direct save |
| `BLOCKED_PROVENANCE` | Blocked |
| `TEST_ONLY` | Test only |
| `R_AND_D_EXCLUDED` | R&D |

<!-- SECTION:PRODUCTION_RUNTIME_EXPORTS -->
## Section 1: Production Runtime Exports

| File | Export Type | Lifecycle Status | Risk | Disposition |
|------|-------------|------------------|------|-------------|
| foo.py | dxf-create-save | COMPAT_ONLY | LOW | no_action |

<!-- SECTION:COMPAT_ONLY_EXPORTS -->
## Section 2: Compat-Only Exports

| File | Export Type | Lifecycle Status | Risk | Disposition |
|------|-------------|------------------|------|-------------|
| bar.py | dxf-create-save | COMPAT_ONLY | LOW | no_action |

<!-- SECTION:BLOCKED_PROVENANCE -->
## Section 3: IBG Blocked

| File | Export Type | Lifecycle Status | Risk | Disposition |
|------|-------------|------------------|------|-------------|
| ibg.py | dxf-create-save | BLOCKED_PROVENANCE | BLOCKED | blocked_provenance |

<!-- SECTION:TEST_FIXTURES -->
## Section 4: Test Fixtures

| File | Lifecycle Status |
|------|------------------|
| test.py | TEST_ONLY |

<!-- SECTION:SCRIPTS -->
## Section 5: Scripts

| File | Lifecycle Status |
|------|------------------|
| script.py | R_AND_D_EXCLUDED |

<!-- SECTION:BLUEPRINT_IMPORT -->
## Section 6: Blueprint-Import

| File | Lifecycle Status |
|------|------------------|
| import.py | R_AND_D_EXCLUDED |

<!-- SECTION:R_AND_D_SANDBOX -->
## Section 7: R&D Sandbox

| File | Lifecycle Status |
|------|------------------|
| sandbox.py | R_AND_D_EXCLUDED |
"""
        result = validate_matrix(content)
        assert result.passed is True
        assert len(result.errors) == 0

    def test_missing_sections_fails(self):
        content = """# Matrix
<!-- SECTION:PRODUCTION_RUNTIME_EXPORTS -->
Only one section
"""
        result = validate_matrix(content)
        assert result.passed is False
        assert any("Missing required sections" in e for e in result.errors)

    def test_warns_on_heading_fallback(self):
        content = """# Matrix

### Lifecycle Status Labels

| Label | Meaning |
|-------|---------|
| `LIFECYCLE_GOVERNED` | Full gate |
| `COMPAT_ONLY` | Compat only |
| `DIRECT_SAVE_GAP` | Direct save |
| `BLOCKED_PROVENANCE` | Blocked |
| `TEST_ONLY` | Test only |
| `R_AND_D_EXCLUDED` | R&D |

## Section 1: Production Runtime Exports

| File | Export Type | Lifecycle Status | Risk | Disposition |
|------|-------------|------------------|------|-------------|
| foo.py | dxf-create-save | COMPAT_ONLY | LOW | no_action |

## Section 2: Compat-Only / Lifecycle-Gap Exports

| File | Export Type | Lifecycle Status | Risk | Disposition |
|------|-------------|------------------|------|-------------|

## Section 3: IBG Blocked Provenance Candidates

| File | Export Type | Lifecycle Status | Risk | Disposition |
|------|-------------|------------------|------|-------------|

## Section 4: Test Fixtures

| File | Lifecycle Status |
|------|------------------|

## Section 5: Scripts

| File | Lifecycle Status |
|------|------------------|

## Section 6: Blueprint-Import Surface

| File | Lifecycle Status |
|------|------------------|

## Section 7: R&D Sandbox (Photo-Vectorizer)

| File | Lifecycle Status |
|------|------------------|
"""
        result = validate_matrix(content)
        assert any("fell back to heading-based parsing" in w for w in result.warnings)


class TestLifecycleStatusLabels:
    """Tests for lifecycle status label constants."""

    def test_required_labels_defined(self):
        expected = {
            "LIFECYCLE_GOVERNED",
            "COMPAT_ONLY",
            "DIRECT_SAVE_GAP",
            "BLOCKED_PROVENANCE",
            "TEST_ONLY",
            "R_AND_D_EXCLUDED",
        }
        assert LIFECYCLE_STATUS_LABELS == expected

    def test_required_sections_defined(self):
        assert "PRODUCTION_RUNTIME_EXPORTS" in REQUIRED_SECTIONS
        assert "BLOCKED_PROVENANCE" in REQUIRED_SECTIONS
        assert "TEST_FIXTURES" in REQUIRED_SECTIONS
        assert "R_AND_D_SANDBOX" in REQUIRED_SECTIONS
