"""Core check logic for boundary import checker."""
from __future__ import annotations

from typing import List, Tuple

from .fences import (
    check_ai_sandbox_boundary,
    check_artifact_authority,
    check_external_boundary,
    check_rmos_cam_boundary,
    check_saw_lab_encapsulation,
)
from .models import ImportRef, SymbolRef
from .parser import iter_python_files, parse_imports_and_symbols, repo_root_from_cwd


def check_boundaries() -> Tuple[List[ImportRef], List[SymbolRef]]:
    """Run all fence checks and return violations."""
    root = repo_root_from_cwd()
    app_dir = root / "app"

    import_violations: List[ImportRef] = []
    symbol_violations: List[SymbolRef] = []

    for py_file in iter_python_files(app_dir):
        imports, symbols, has_type_checking = parse_imports_and_symbols(py_file)

        # Fence 1: external_boundary
        import_violations.extend(check_external_boundary(py_file, imports))

        # Fence 2: rmos_cam_boundary
        import_violations.extend(check_rmos_cam_boundary(py_file, imports, root))

        # Fence 4: ai_sandbox_boundary
        import_violations.extend(check_ai_sandbox_boundary(py_file, imports))

        # Fence 5: saw_lab_encapsulation
        import_violations.extend(check_saw_lab_encapsulation(py_file, imports))

        # Fence 7: artifact_authority
        symbol_violations.extend(check_artifact_authority(py_file, symbols, root))

    return import_violations, symbol_violations
