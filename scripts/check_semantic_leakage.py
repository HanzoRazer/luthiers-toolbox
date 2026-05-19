#!/usr/bin/env python3
"""
Semantic Leakage Detection Script

Detects patterns that indicate improper coupling between architectural layers.

Anti-patterns detected:
1. DXF semantics in Export Object
2. CAM semantics in Geometry systems
3. Machine semantics in Morphology systems
4. Translator assumptions in upstream systems

Usage:
    python scripts/check_semantic_leakage.py

Exit codes:
    0 - No violations found
    1 - Potential leakage detected (warning only)

Part of Governance Remediation Infrastructure.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Define leakage patterns by architectural layer
LEAKAGE_PATTERNS: Dict[str, Dict] = {
    "export_object": {
        "description": "Export Object must remain DXF-agnostic",
        "forbidden_imports": [
            (r"from\s+.*ezdxf", "Direct ezdxf import in Export Object"),
            (r"import\s+ezdxf", "Direct ezdxf import in Export Object"),
            (r"from\s+.*dxf_compat", "dxf_compat import in Export Object"),
        ],
        "forbidden_patterns": [
            (r"\bdxf_\w+\s*=", "DXF-prefixed field in Export Object"),
            (r"\blwpolyline\b", "LWPOLYLINE reference in Export Object"),
            (r"\bacad_version\b", "AutoCAD version in Export Object"),
            (r"\"dxf_layer\"", "DXF layer field in Export Object"),
        ],
        "paths": [
            "services/api/app/cam/export_object*.py",
            "services/api/app/cam/models/export*.py",
        ],
    },
    "geometry": {
        "description": "Geometry layer must not have CAM semantics",
        "forbidden_imports": [
            (r"from\s+.*\.cam\.\w+\s+import", "CAM import in Geometry layer"),
            (r"from\s+.*toolpath", "Toolpath import in Geometry layer"),
        ],
        "forbidden_patterns": [
            (r"\bfeed_rate\s*[=:]", "feed_rate field in Geometry"),
            (r"\bspindle_rpm\s*[=:]", "spindle_rpm field in Geometry"),
            (r"\btoolpath_type\s*[=:]", "toolpath_type field in Geometry"),
            (r"\bg_code\b", "G-code reference in Geometry"),
            (r"\bstepover\s*[=:]", "stepover (CAM param) in Geometry"),
            (r"\bstepdown\s*[=:]", "stepdown (CAM param) in Geometry"),
        ],
        "paths": [
            "services/api/app/geometry/*.py",
            "services/api/app/instrument_geometry/**/*.py",
        ],
        "exclude": [
            "**/ibg/*.py",  # IBG has separate rules
        ],
    },
    "morphology": {
        "description": "Morphology/IBG must not have translator assumptions",
        "forbidden_imports": [
            (r"from\s+.*translator", "Translator import in Morphology"),
            (r"from\s+.*postprocessor", "Postprocessor import in Morphology"),
            (r"from\s+.*gcode", "G-code import in Morphology"),
        ],
        "forbidden_patterns": [
            (r"def\s+to_dxf", "to_dxf method in Morphology"),
            (r"def\s+to_gcode", "to_gcode method in Morphology"),
            (r"def\s+serialize_to_", "serialize_to_ method in Morphology"),
            (r"DXFEntity", "DXFEntity class reference in Morphology"),
        ],
        "paths": [
            "services/api/app/instrument_geometry/body/ibg/*.py",
            "services/api/app/services/blueprint*.py",
        ],
    },
    "router": {
        "description": "Routers must not contain math (Fortran Rule)",
        "forbidden_imports": [],
        "forbidden_patterns": [
            (r"math\.sin\(", "Trigonometry in router (violates Fortran Rule)"),
            (r"math\.cos\(", "Trigonometry in router (violates Fortran Rule)"),
            (r"math\.sqrt\(", "Math operations in router (violates Fortran Rule)"),
            (r"\*\*\s*2\b", "Power operation in router (violates Fortran Rule)"),
            (r"3\.14159", "Hardcoded pi in router"),
        ],
        "paths": [
            "services/api/app/routers/**/*.py",
        ],
        "exclude": [
            "*_test.py",
            "test_*.py",
        ],
    },
}

# Allowlist for known exceptions (with justification)
ALLOWLIST = {
    # Format: "filepath:line_pattern": "justification"
    "services/api/app/cam/export_object_builder.py:dxf_compat":
        "Export builder may reference dxf_compat for format selection only",
}


def should_check_file(file_path: Path, layer_config: Dict) -> bool:
    """Determine if file should be checked based on layer config."""
    # Check exclusions first
    for exclude_pattern in layer_config.get("exclude", []):
        if file_path.match(exclude_pattern.replace("**", "*")):
            return False
    return True


def is_allowlisted(file_path: str, line: str) -> bool:
    """Check if a violation is in the allowlist."""
    for pattern, _ in ALLOWLIST.items():
        if pattern.split(":")[0] in file_path:
            if pattern.split(":")[1] in line:
                return True
    return False


def check_file_for_leakage(file_path: Path, layer: str) -> List[Tuple[int, str, str]]:
    """
    Check a file for semantic leakage patterns.

    Args:
        file_path: Path to file to check
        layer: Architectural layer name

    Returns:
        List of (line_number, line_text, violation_description) tuples
    """
    violations = []
    config = LEAKAGE_PATTERNS.get(layer, {})

    if not should_check_file(file_path, config):
        return violations

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return violations

    lines = content.split("\n")

    for line_num, line in enumerate(lines, start=1):
        # Skip comments and docstrings (basic detection)
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        # Check if allowlisted
        if is_allowlisted(str(file_path), line):
            continue

        # Check forbidden imports
        for pattern, description in config.get("forbidden_imports", []):
            if re.search(pattern, line, re.IGNORECASE):
                violations.append((line_num, stripped[:80], description))

        # Check forbidden patterns
        for pattern, description in config.get("forbidden_patterns", []):
            if re.search(pattern, line, re.IGNORECASE):
                violations.append((line_num, stripped[:80], description))

    return violations


def find_files_for_layer(repo_root: Path, layer: str) -> List[Path]:
    """Find all files matching layer path patterns."""
    config = LEAKAGE_PATTERNS.get(layer, {})
    files = []

    for glob_pattern in config.get("paths", []):
        # Handle ** glob patterns
        if "**" in glob_pattern:
            base, pattern = glob_pattern.split("**", 1)
            base_path = repo_root / base
            if base_path.exists():
                files.extend(base_path.rglob(pattern.lstrip("/")))
        else:
            files.extend(repo_root.glob(glob_pattern))

    return [f for f in files if f.is_file() and f.suffix == ".py"]


def main() -> int:
    """
    Run semantic leakage detection.

    Returns:
        0 if no violations
        1 if violations found (warning mode - does not block)
    """
    repo_root = Path(__file__).parent.parent
    all_violations = []

    print("Checking for semantic leakage...")
    print()

    for layer, config in LEAKAGE_PATTERNS.items():
        print(f"  Layer: {layer} - {config['description']}")
        files = find_files_for_layer(repo_root, layer)

        for file_path in files:
            violations = check_file_for_leakage(file_path, layer)
            if violations:
                all_violations.append((file_path, layer, violations))

    print()

    if all_violations:
        print("[WARN] Potential semantic leakage detected:")
        print()

        for file_path, layer, violations in all_violations:
            rel_path = file_path.relative_to(repo_root) if file_path.is_relative_to(repo_root) else file_path
            print(f"  File: {rel_path}")
            print(f"  Layer: {layer}")
            for line_num, line_text, reason in violations:
                print(f"    Line {line_num}: {reason}")
                if line_text:
                    print(f"      > {line_text}")
            print()

        print("Review these patterns to ensure architectural boundaries are maintained.")
        print("Add to ALLOWLIST in check_semantic_leakage.py if intentional.")
        print()
        print("Note: This is a warning only. CI will not fail.")
        return 1

    print("[OK] No semantic leakage detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
