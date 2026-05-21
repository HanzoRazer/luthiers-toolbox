#!/usr/bin/env python3
"""
Export Lifecycle Classification Matrix Validator

Validates the structural integrity and consistency of the export lifecycle
classification matrix document.

Usage:
    python scripts/governance/validate_export_lifecycle_matrix.py [--strict]

Options:
    --strict    Promote warnings to failures (exit 1)

Exit codes:
    0 - All checks pass (or warnings only without --strict)
    1 - Structural failures found

Part of Runtime Boundary Follow-Through Sprint, Phase 1D.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).parent.parent.parent
MATRIX_PATH = REPO_ROOT / "docs" / "governance" / "EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md"

REQUIRED_SECTIONS = [
    "PRODUCTION_RUNTIME_EXPORTS",
    "COMPAT_ONLY_EXPORTS",
    "BLOCKED_PROVENANCE",
    "TEST_FIXTURES",
    "SCRIPTS",
    "BLUEPRINT_IMPORT",
    "R_AND_D_SANDBOX",
]

LIFECYCLE_STATUS_LABELS = {
    "LIFECYCLE_GOVERNED",
    "COMPAT_ONLY",
    "DIRECT_SAVE_GAP",
    "BLOCKED_PROVENANCE",
    "TEST_ONLY",
    "R_AND_D_EXCLUDED",
}

PRODUCTION_SECTIONS = {"PRODUCTION_RUNTIME_EXPORTS", "COMPAT_ONLY_EXPORTS"}
BLOCKED_SECTIONS = {"BLOCKED_PROVENANCE"}
EXCLUDED_SECTIONS = {"TEST_FIXTURES", "SCRIPTS", "BLUEPRINT_IMPORT", "R_AND_D_SANDBOX"}

PRODUCTION_REQUIRED_COLUMNS = {
    "File",
    "Export Type",
    "Lifecycle Status",
    "Risk",
    "Disposition",
}


@dataclass
class ValidationResult:
    """Result of matrix validation."""
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)


def parse_sections_by_markers(content: str) -> Tuple[Dict[str, str], bool]:
    """
    Parse sections using HTML markers.

    Returns:
        (dict of section_name -> section_content, found_markers)
    """
    marker_pattern = re.compile(r'<!-- SECTION:(\w+) -->')
    sections: Dict[str, str] = {}

    matches = list(marker_pattern.finditer(content))
    if not matches:
        return {}, False

    for i, match in enumerate(matches):
        section_name = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections[section_name] = content[start:end]

    return sections, True


def parse_sections_by_headings(content: str) -> Dict[str, str]:
    """
    Parse sections using markdown headings (fallback).

    Returns:
        dict of section_name -> section_content
    """
    heading_pattern = re.compile(r'^## Section \d+: (.+)$', re.MULTILINE)
    sections: Dict[str, str] = {}

    section_name_map = {
        "Production Runtime Exports": "PRODUCTION_RUNTIME_EXPORTS",
        "Compat-Only / Lifecycle-Gap Exports": "COMPAT_ONLY_EXPORTS",
        "IBG Blocked Provenance Candidates": "BLOCKED_PROVENANCE",
        "Test Fixtures": "TEST_FIXTURES",
        "Scripts": "SCRIPTS",
        "Blueprint-Import Surface": "BLUEPRINT_IMPORT",
        "R&D Sandbox (Photo-Vectorizer)": "R_AND_D_SANDBOX",
    }

    matches = list(heading_pattern.finditer(content))
    if not matches:
        return {}

    for i, match in enumerate(matches):
        heading_text = match.group(1)
        section_name = section_name_map.get(heading_text, heading_text.upper().replace(" ", "_"))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections[section_name] = content[start:end]

    return sections


def parse_table_rows(section_content: str) -> List[Dict[str, str]]:
    """
    Parse markdown table rows from section content.
    Handles multiple tables within a section (subsection headers create new tables).

    Returns:
        List of dicts with column_name -> cell_value
    """
    lines = section_content.strip().split('\n')
    rows: List[Dict[str, str]] = []

    headers: List[str] = []
    in_table = False
    expecting_separator = False

    for line in lines:
        line = line.strip()

        if line.startswith('#'):
            in_table = False
            headers = []
            expecting_separator = False
            continue

        if not line.startswith('|'):
            if in_table and line == '':
                pass
            elif in_table:
                in_table = False
                headers = []
            continue

        cells = [c.strip() for c in line.split('|')[1:-1]]

        if all(c.replace('-', '').replace(':', '') == '' for c in cells):
            if expecting_separator:
                expecting_separator = False
                in_table = True
            continue

        if not in_table:
            headers = cells
            expecting_separator = True
            continue

        if len(cells) == len(headers) and cells != headers:
            row = {headers[i]: cells[i] for i in range(len(headers))}
            rows.append(row)

    return rows


def validate_production_row(row: Dict[str, str], section_name: str) -> List[str]:
    """Validate a production export row has required columns."""
    errors: List[str] = []

    file_col = row.get("File", "")
    if not file_col:
        errors.append(f"Row missing File column in {section_name}")

    lifecycle_status = row.get("Lifecycle Status", "")
    if not lifecycle_status:
        errors.append(f"Row {file_col} missing Lifecycle Status in {section_name}")
    elif lifecycle_status not in LIFECYCLE_STATUS_LABELS:
        errors.append(f"Row {file_col} has unknown Lifecycle Status '{lifecycle_status}' in {section_name}")

    risk = row.get("Risk", "")
    if not risk:
        errors.append(f"Row {file_col} missing Risk level in {section_name}")

    disposition = row.get("Disposition", "")
    if not disposition:
        errors.append(f"Row {file_col} missing Disposition in {section_name}")

    return errors


def validate_blocked_row(row: Dict[str, str]) -> List[str]:
    """Validate BLOCKED_PROVENANCE row is not marked lifecycle-governed."""
    errors: List[str] = []

    file_col = row.get("File", "")
    lifecycle_status = row.get("Lifecycle Status", "")

    if lifecycle_status == "LIFECYCLE_GOVERNED":
        errors.append(f"BLOCKED_PROVENANCE row {file_col} incorrectly marked as LIFECYCLE_GOVERNED")
    elif lifecycle_status and lifecycle_status not in {"BLOCKED_PROVENANCE", "COMPAT_ONLY", "DIRECT_SAVE_GAP"}:
        errors.append(f"BLOCKED_PROVENANCE row {file_col} has unexpected status '{lifecycle_status}'")

    return errors


def validate_excluded_row(row: Dict[str, str], section_name: str) -> List[str]:
    """Validate TEST/R&D rows are not counted as production gaps."""
    warnings: List[str] = []

    file_col = row.get("File", "")
    lifecycle_status = row.get("Lifecycle Status", "")

    if not file_col:
        return warnings

    if lifecycle_status in {"LIFECYCLE_GOVERNED", "COMPAT_ONLY", "DIRECT_SAVE_GAP"}:
        warnings.append(f"{section_name} row {file_col} has production status '{lifecycle_status}' but should be excluded")

    return warnings


def validate_matrix(content: str) -> ValidationResult:
    """
    Validate the export lifecycle classification matrix.

    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult(passed=True)

    sections, used_markers = parse_sections_by_markers(content)

    if used_markers:
        result.info.append("Parsed sections using HTML markers")
    else:
        sections = parse_sections_by_headings(content)
        if sections:
            result.warnings.append("HTML markers not found; fell back to heading-based parsing")
        else:
            result.errors.append("Could not parse sections (no markers or headings found)")
            result.passed = False
            return result

    missing_sections = set(REQUIRED_SECTIONS) - set(sections.keys())
    if missing_sections:
        result.errors.append(f"Missing required sections: {', '.join(sorted(missing_sections))}")
        result.passed = False

    documented_labels: Set[str] = set()
    legend_match = re.search(r'### Lifecycle Status Labels\s*\n\|[^\n]+\n\|[-|]+\n((?:\|[^\n]+\n)+)', content)
    if legend_match:
        for line in legend_match.group(1).strip().split('\n'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if cells and cells[0].startswith('`'):
                label = cells[0].strip('`')
                documented_labels.add(label)

    missing_labels = LIFECYCLE_STATUS_LABELS - documented_labels
    if missing_labels:
        result.warnings.append(f"Lifecycle Status Labels not documented in legend: {', '.join(sorted(missing_labels))}")

    for section_name in PRODUCTION_SECTIONS:
        if section_name not in sections:
            continue
        rows = parse_table_rows(sections[section_name])
        for row in rows:
            errors = validate_production_row(row, section_name)
            result.errors.extend(errors)
            if errors:
                result.passed = False

    if "BLOCKED_PROVENANCE" in sections:
        rows = parse_table_rows(sections["BLOCKED_PROVENANCE"])
        for row in rows:
            errors = validate_blocked_row(row)
            result.errors.extend(errors)
            if errors:
                result.passed = False

    for section_name in EXCLUDED_SECTIONS:
        if section_name not in sections:
            continue
        rows = parse_table_rows(sections[section_name])
        for row in rows:
            warnings = validate_excluded_row(row, section_name)
            result.warnings.extend(warnings)

    return result


def main() -> int:
    """Validate export lifecycle matrix."""
    parser = argparse.ArgumentParser(
        description="Validate export lifecycle classification matrix"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote warnings to failures (exit 1)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    if not MATRIX_PATH.exists():
        print(f"[FAIL] Matrix file not found: {MATRIX_PATH}")
        return 1

    content = MATRIX_PATH.read_text(encoding="utf-8")
    result = validate_matrix(content)

    if args.verbose:
        for info in result.info:
            print(f"[INFO] {info}")

    for warning in result.warnings:
        print(f"[WARN] {warning}")

    for error in result.errors:
        print(f"[FAIL] {error}")

    if not result.passed:
        print(f"\n[FAIL] Export lifecycle matrix validation failed ({len(result.errors)} error(s))")
        return 1

    if result.warnings and args.strict:
        print(f"\n[FAIL] Export lifecycle matrix validation failed ({len(result.warnings)} warning(s) in strict mode)")
        return 1

    if result.warnings:
        print(f"\n[OK] Export lifecycle matrix validation passed ({len(result.warnings)} warning(s))")
    else:
        print("\n[OK] Export lifecycle matrix validation passed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
