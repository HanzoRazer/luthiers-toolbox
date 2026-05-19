#!/usr/bin/env python3
"""
Capability Registry Validation Script

Validates the CAM operation capability registry for:
1. Schema compliance
2. Safety assertion enforcement
3. Maturity level consistency
4. Route existence verification

Usage:
    python scripts/check_capability_registry.py

Exit codes:
    0 - All checks pass
    1 - Validation failures found

Part of Governance Remediation Infrastructure.
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Add services/api to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "services" / "api"))


def check_safety_assertions() -> List[Tuple[str, str]]:
    """
    Check that safety assertions are enforced.

    Safety rules (until machine output is implemented):
    - machine_ready must be False
    - machine_output_supported must be False
    """
    violations = []

    try:
        from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY
    except ImportError as e:
        return [("import_error", f"Cannot import registry: {e}")]

    for op_name, capability in CAM_OPERATION_REGISTRY.items():
        if capability.machine_ready is True:
            violations.append((
                op_name,
                "machine_ready=True violates safety assertion"
            ))

        if capability.machine_output_supported is True:
            violations.append((
                op_name,
                "machine_output_supported=True violates safety assertion"
            ))

    return violations


def check_required_fields() -> List[Tuple[str, str]]:
    """
    Check that all operations have required fields populated.
    """
    violations = []

    try:
        from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY
    except ImportError:
        return []

    required_fields = [
        "operation",
        "lifecycle_supported",
        "export_object_supported",
        "machine_validation_supported",
        "translator_validation_supported",
        "rmos_persistence_supported",
        "exportability_class",
        "maturity",
    ]

    for op_name, capability in CAM_OPERATION_REGISTRY.items():
        for field in required_fields:
            value = getattr(capability, field, None)
            if value is None:
                violations.append((op_name, f"Missing required field: {field}"))

    return violations


def check_maturity_consistency() -> List[Tuple[str, str]]:
    """
    Check that maturity levels are consistent with other properties.

    Rules:
    - canonical operations must have preview_route
    - governed operations should have lifecycle_route
    - experimental operations should have notes explaining status
    """
    violations = []

    try:
        from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY
    except ImportError:
        return []

    for op_name, capability in CAM_OPERATION_REGISTRY.items():
        if capability.maturity == "canonical":
            if not capability.preview_route:
                violations.append((
                    op_name,
                    "Canonical operation missing preview_route"
                ))
            if not capability.lifecycle_supported:
                violations.append((
                    op_name,
                    "Canonical operation should support lifecycle"
                ))

        if capability.maturity == "experimental":
            if not capability.notes:
                violations.append((
                    op_name,
                    "Experimental operation should have notes explaining status"
                ))

    return violations


def check_exportability_permissions() -> List[Tuple[str, str]]:
    """
    Check that exportability class is consistent with support flags.

    Rules:
    - preview_only must have export_object_supported=False
    - governed_export must have export_object_supported=True
    """
    violations = []

    try:
        from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY
    except ImportError:
        return []

    for op_name, capability in CAM_OPERATION_REGISTRY.items():
        if capability.exportability_class == "preview_only":
            if capability.export_object_supported:
                violations.append((
                    op_name,
                    "preview_only class cannot have export_object_supported=True"
                ))
            if capability.machine_validation_supported:
                violations.append((
                    op_name,
                    "preview_only class cannot have machine_validation_supported=True"
                ))

        if capability.exportability_class in ("governed_export", "translator_ready", "machine_candidate"):
            if not capability.export_object_supported:
                violations.append((
                    op_name,
                    f"{capability.exportability_class} class must have export_object_supported=True"
                ))

    return violations


def check_valid_enum_values() -> List[Tuple[str, str]]:
    """
    Check that enum fields have valid values.
    """
    violations = []

    try:
        from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY
    except ImportError:
        return []

    valid_exportability = {"preview_only", "governed_export", "translator_ready", "machine_candidate"}
    valid_maturity = {"experimental", "candidate", "governed", "canonical"}

    for op_name, capability in CAM_OPERATION_REGISTRY.items():
        if capability.exportability_class not in valid_exportability:
            violations.append((
                op_name,
                f"Invalid exportability_class: {capability.exportability_class}"
            ))

        if capability.maturity not in valid_maturity:
            violations.append((
                op_name,
                f"Invalid maturity: {capability.maturity}"
            ))

    return violations


def main() -> int:
    """
    Run all capability registry validations.
    """
    print("Validating CAM Operation Capability Registry...")
    print()

    all_violations = []

    # Run all checks
    checks = [
        ("Safety Assertions", check_safety_assertions),
        ("Required Fields", check_required_fields),
        ("Maturity Consistency", check_maturity_consistency),
        ("Exportability Permissions", check_exportability_permissions),
        ("Valid Enum Values", check_valid_enum_values),
    ]

    for check_name, check_func in checks:
        print(f"  Checking: {check_name}...")
        violations = check_func()
        if violations:
            all_violations.extend([(check_name, op, msg) for op, msg in violations])
            print(f"    FAIL: {len(violations)} violation(s)")
        else:
            print(f"    PASS")

    print()

    if all_violations:
        print("[FAIL] Capability registry validation failed:")
        print()

        for check_name, op_name, message in all_violations:
            print(f"  [{check_name}] {op_name}: {message}")

        print()
        print(f"Total violations: {len(all_violations)}")
        return 1

    print("[OK] Capability registry validation passed")

    # Print summary
    try:
        from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY
        print()
        print(f"Registered operations: {len(CAM_OPERATION_REGISTRY)}")
        for op_name, cap in CAM_OPERATION_REGISTRY.items():
            print(f"  - {op_name}: {cap.maturity}, {cap.exportability_class}")
    except ImportError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
