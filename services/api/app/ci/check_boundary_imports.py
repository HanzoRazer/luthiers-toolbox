from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


"""
Boundary Import Checker (ToolBox API) — Fence-Aware Edition
------------------------------------------------------------

Purpose:
  Enforce hard architectural boundaries defined in FENCE_REGISTRY.json.
  Implements 5 import-based fences:
    1. external_boundary     - Analyzer internals (tap_tone.*, modes.*)
    2. rmos_cam_boundary     - RMOS ↔ CAM isolation  
    4. ai_sandbox_boundary   - AI sandbox advisory-only
    5. saw_lab_encapsulation - Saw Lab self-containment
    7. artifact_authority    - RunArtifact construction

Usage:
  cd services/api
  python -m app.ci.check_boundary_imports
  python -m app.ci.check_boundary_imports --profile toolbox
  python -m app.ci.check_boundary_imports --write-baseline app/ci/fence_baseline.json
  python -m app.ci.check_boundary_imports --baseline app/ci/fence_baseline.json

Exit codes:
  0 = ok
  1 = ok (baseline mode, no new violations)
  2 = violations found
  3 = configuration / runtime error

Baseline mode:
  --write-baseline: captures current violations to JSON and exits 0
  --baseline: fails only on NEW violations compared to the baseline
  (This is the recommended posture for brownfield enforcement.)

Design:
  - Parse Python files with `ast` to avoid false positives.
  - Check imports against fence rules from FENCE_REGISTRY.json.
  - Detect forbidden symbol imports (RunArtifact) and constructions.
  - Support TYPE_CHECKING exceptions for type hints.

Note:
  This is intentionally conservative. Exemptions require baseline mode
  or fixing the underlying architecture.
"""


# --- Configuration: Fence Definitions ------------------------------------
# These map to FENCE_REGISTRY.json profiles that use import-based enforcement.
# Pattern-based fences (operation_lane, frontend_sdk, legacy_deprecation) are
# handled by separate checkers.

# Files to skip (generated, vendored, etc.)
SKIP_FILE_PATTERNS: Tuple[str, ...] = (
    "*/__pycache__/*",
    "*/.venv/*",
    "*/site-packages/*",
)


# --- Fence 1: external_boundary -------------------------------------------
# Cross-repository boundary: ToolBox ↔ Analyzer
# DENY: tap_tone.*, modes.*

EXTERNAL_FORBIDDEN_PREFIXES: Tuple[str, ...] = (
    "tap_tone.",
    "tap_tone",
    "modes.",
    "modes",
)


# --- Fence 2: rmos_cam_boundary -------------------------------------------
# Internal domain boundary: RMOS orchestration ↔ CAM execution
# Bidirectional isolation with narrow exceptions.

# CAM files MUST NOT import these RMOS modules:
CAM_FORBIDDEN_RMOS_IMPORTS: Tuple[str, ...] = (
    "app.rmos.workflow",
    "app.rmos.runs",
    "app.rmos.feasibility",
)

# RMOS files MUST NOT import these CAM modules:
RMOS_FORBIDDEN_CAM_IMPORTS: Tuple[str, ...] = (
    "app.cam.toolpath",
    "app.cam.post",
)

# Exceptions: these files may cross the boundary
RMOS_CAM_EXCEPTION_FILES: Set[str] = {
    "app/rmos/cam/schemas_intent.py",
    "app/rmos/cam/__init__.py",
}

# CAM is allowed to import CamIntentV1 from RMOS
CAM_ALLOWED_RMOS_IMPORTS: Tuple[str, ...] = (
    "app.rmos.cam.CamIntentV1",
    "app.rmos.cam",
)


# --- Fence 4: ai_sandbox_boundary -----------------------------------------
# AI sandbox isolation: advisory only, no execution authority

AI_SANDBOX_PATHS: Tuple[str, ...] = (
    "app/_experimental",
    "app/ai_sandbox",
)

AI_SANDBOX_FORBIDDEN_IMPORTS: Tuple[str, ...] = (
    "app.rmos.workflow",
    "app.rmos.runs.store",
    "app.rmos.toolpaths",
)


# --- Fence 5: saw_lab_encapsulation ---------------------------------------
# Saw Lab self-containment: reference implementation for OPERATION lane

SAW_LAB_PATHS: Tuple[str, ...] = (
    "app/saw_lab",
)

SAW_LAB_ALLOWED_IMPORTS: Tuple[str, ...] = (
    "app.saw_lab",
    "app.rmos.runs_v2",
    "app.rmos.cam.CamIntentV1",
    "app.rmos.cam",
    "app.rmos.run_artifacts",
    "app.util",
    "app.utils",
    "app.schemas",
    "app.core",
    "app.config",
    "app.settings",
    "app.logging",
    "app.telemetry",
    "app.metrics",
    "app.errors",
    "app.types",
    "app.constants",
    "app.security",
    "app.auth",
    "app.db",
    "app.data",
    "app.contracts",
    # Saw Lab services (legacy location in app.services)
    "app.services",
    "app.saw_lab_run_service",
)


# --- Fence 7: artifact_authority ------------------------------------------
# Run artifact creation restricted to authorized modules

ARTIFACT_AUTHORITY_ALLOWED_FILES: Set[str] = {
    "app/rmos/runs_v2/store.py",
    "app/rmos/runs_v2/schemas.py",
    # CAM routers that create run artifacts
    "app/cam/routers/drilling/pattern_router.py",
    "app/cam/routers/rosette/cam_router.py",
}

# Symbol that requires authority
RUNARTIFACT_SYMBOL = "RunArtifact"


# --- Data structures -------------------------------------------------------

@dataclass(frozen=True)
class ImportRef:
    file: Path
    line: int
    module: str
    fence: str
    reason: str


@dataclass(frozen=True)
class SymbolRef:
    file: Path
    line: int
    symbol: str
    fence: str
    reason: str


# --- Helpers ---------------------------------------------------------------

def _repo_root_from_cwd() -> Path:
    """
    Expected execution: services/api as cwd, with app/ present.
    If not, we still try to locate an 'app' directory upward.
    """
    cwd = Path.cwd().resolve()
    for p in [cwd] + list(cwd.parents):
        if (p / "app").is_dir():
            return p
    raise RuntimeError("Could not locate services/api root (missing app/). Run from services/api.")


def _to_relpath_str(path: Path) -> str:
    """Convert path to stable relative string for baseline keys."""
    root = _repo_root_from_cwd()
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:  # WP-1: narrowed from except Exception
        return str(path).replace("\\", "/")


def _match_skip(path: Path) -> bool:
    s = str(path).replace("\\", "/")
    for pat in SKIP_FILE_PATTERNS:
        if pat.strip("*") in s:
            return True
    return False


def _iter_python_files(app_dir: Path) -> Iterable[Path]:
    for p in app_dir.rglob("*.py"):
        if _match_skip(p):
            continue
        yield p


def _file_matches_path(file_path: Path, patterns: Tuple[str, ...]) -> bool:
    """Check if file path matches any of the given path patterns."""
    s = str(file_path).replace("\\", "/")
    for pat in patterns:
        if pat in s:
            return True
    return False


def _normalize_file_key(file_path: Path, root: Path) -> str:
    """Get normalized file key for exception matching."""
    try:
        rel = file_path.resolve().relative_to(root.resolve())
        return str(rel).replace("\\", "/")
    except ValueError:  # WP-1: narrowed from except Exception
        return str(file_path).replace("\\", "/")


def _is_cam_file(file_path: Path) -> bool:
    s = str(file_path).replace("\\", "/")
    return "/cam/" in s or "/app/cam" in s


def _is_rmos_file(file_path: Path) -> bool:
    s = str(file_path).replace("\\", "/")
    return "/rmos/" in s or "/app/rmos" in s


def _module_matches_prefix(module: str, prefixes: Tuple[str, ...]) -> bool:
    for prefix in prefixes:
        if module == prefix or module.startswith(prefix + "."):
            return True
    return False


# --- AST Parsing -----------------------------------------------------------

def _parse_imports_and_symbols(py_file: Path) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]], bool]:
    """Parse file and return:"""
    src = py_file.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(src, filename=str(py_file))
    except SyntaxError:
        return [], [], False

    imports: List[Tuple[int, str]] = []
    symbol_refs: List[Tuple[int, str]] = []
    has_type_checking = False
    type_checking_lines: Set[int] = set()

    # First pass: find TYPE_CHECKING blocks
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # Check if this is `if TYPE_CHECKING:`
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                has_type_checking = True
                # Mark all lines in this block as TYPE_CHECKING
                for child in ast.walk(node):
                    if hasattr(child, "lineno"):
                        type_checking_lines.add(child.lineno)

    # Second pass: collect imports and symbol usage
    for node in ast.walk(tree):
        lineno = getattr(node, "lineno", 1)
        in_type_checking = lineno in type_checking_lines

        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.append((lineno, alias.name))
                    # Check for RunArtifact import
                    if RUNARTIFACT_SYMBOL in alias.name and not in_type_checking:
                        symbol_refs.append((lineno, RUNARTIFACT_SYMBOL))

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((lineno, node.module))
                # Check for RunArtifact in from imports
                for alias in node.names:
                    if alias.name == RUNARTIFACT_SYMBOL and not in_type_checking:
                        symbol_refs.append((lineno, RUNARTIFACT_SYMBOL))

        elif isinstance(node, ast.Call):
            # Check for RunArtifact() construction
            func = node.func
            if isinstance(func, ast.Name) and func.id == RUNARTIFACT_SYMBOL:
                symbol_refs.append((lineno, f"{RUNARTIFACT_SYMBOL}()"))
            elif isinstance(func, ast.Attribute) and func.attr == RUNARTIFACT_SYMBOL:
                symbol_refs.append((lineno, f"{RUNARTIFACT_SYMBOL}()"))

    return imports, symbol_refs, has_type_checking


# --- Fence Checks ----------------------------------------------------------

def _check_external_boundary(
    file_path: Path,
    imports: List[Tuple[int, str]],
) -> List[ImportRef]:
    """Fence 1: Block imports from tap_tone.* and modes.*"""
    violations = []
    for lineno, module in imports:
        for prefix in EXTERNAL_FORBIDDEN_PREFIXES:
            if module == prefix or module.startswith(prefix + "."):
                violations.append(ImportRef(
                    file=file_path,
                    line=lineno,
                    module=module,
                    fence="external_boundary",
                    reason="Analyzer internals (tap_tone.*, modes.*) are forbidden in ToolBox.",
                ))
                break
    return violations


def _check_rmos_cam_boundary(
    file_path: Path,
    imports: List[Tuple[int, str]],
    root: Path,
) -> List[ImportRef]:
    """Fence 2: Bidirectional RMOS ↔ CAM isolation."""
    violations = []
    file_key = _normalize_file_key(file_path, root)

    # Check exception files
    if file_key in RMOS_CAM_EXCEPTION_FILES:
        return []

    is_cam = _is_cam_file(file_path)
    is_rmos = _is_rmos_file(file_path)

    for lineno, module in imports:
        # CAM must not import RMOS workflow/runs/feasibility
        if is_cam:
            # Check if it's an allowed exception (CamIntentV1)
            if _module_matches_prefix(module, CAM_ALLOWED_RMOS_IMPORTS):
                continue
            if _module_matches_prefix(module, CAM_FORBIDDEN_RMOS_IMPORTS):
                violations.append(ImportRef(
                    file=file_path,
                    line=lineno,
                    module=module,
                    fence="rmos_cam_boundary",
                    reason="CAM must not import RMOS workflow/runs/feasibility. Only CamIntent envelope allowed.",
                ))

        # RMOS must not import CAM toolpath/post
        if is_rmos:
            if _module_matches_prefix(module, RMOS_FORBIDDEN_CAM_IMPORTS):
                violations.append(ImportRef(
                    file=file_path,
                    line=lineno,
                    module=module,
                    fence="rmos_cam_boundary",
                    reason="RMOS must not import CAM toolpath/post generation. Use CamIntent envelope.",
                ))

    return violations


def _check_ai_sandbox_boundary(
    file_path: Path,
    imports: List[Tuple[int, str]],
) -> List[ImportRef]:
    """Fence 4: AI sandbox must not access execution authority."""
    violations = []

    if not _file_matches_path(file_path, AI_SANDBOX_PATHS):
        return []

    for lineno, module in imports:
        if _module_matches_prefix(module, AI_SANDBOX_FORBIDDEN_IMPORTS):
            violations.append(ImportRef(
                file=file_path,
                line=lineno,
                module=module,
                fence="ai_sandbox_boundary",
                reason="AI sandbox cannot access workflow, runs store, or toolpath generation.",
            ))

    return violations


def _check_saw_lab_encapsulation(
    file_path: Path,
    imports: List[Tuple[int, str]],
) -> List[ImportRef]:
    """Fence 5: Saw Lab must stay self-contained."""
    violations = []

    if not _file_matches_path(file_path, SAW_LAB_PATHS):
        return []

    for lineno, module in imports:
        # Skip non-app imports
        if not module.startswith("app."):
            continue

        # Check if it's an allowed import
        if _module_matches_prefix(module, SAW_LAB_ALLOWED_IMPORTS):
            continue

        violations.append(ImportRef(
            file=file_path,
            line=lineno,
            module=module,
            fence="saw_lab_encapsulation",
            reason="Saw Lab imports must stay within saw_lab, runs_v2, CamIntent envelope, and shared infra.",
        ))

    return violations


def _check_artifact_authority(
    file_path: Path,
    symbol_refs: List[Tuple[int, str]],
    root: Path,
) -> List[SymbolRef]:
    """Fence 7: RunArtifact usage restricted to authorized files."""
    violations = []
    file_key = _normalize_file_key(file_path, root)

    # Authorized files can use RunArtifact freely
    if file_key in ARTIFACT_AUTHORITY_ALLOWED_FILES:
        return []

    for lineno, symbol in symbol_refs:
        if RUNARTIFACT_SYMBOL in symbol:
            if "()" in symbol:
                reason = "Direct RunArtifact() construction is restricted to runs_v2 store/schemas."
            else:
                reason = "Importing RunArtifact is restricted (use dicts or TYPE_CHECKING only)."

            violations.append(SymbolRef(
                file=file_path,
                line=lineno,
                symbol=symbol,
                fence="artifact_authority",
                reason=reason,
            ))

    return violations


# --- Core Check ------------------------------------------------------------

def check_boundaries() -> Tuple[List[ImportRef], List[SymbolRef]]:
    """Run all fence checks and return violations."""
    root = _repo_root_from_cwd()
    app_dir = root / "app"

    import_violations: List[ImportRef] = []
    symbol_violations: List[SymbolRef] = []

    for py_file in _iter_python_files(app_dir):
        imports, symbols, has_type_checking = _parse_imports_and_symbols(py_file)

        # Fence 1: external_boundary
        import_violations.extend(_check_external_boundary(py_file, imports))

        # Fence 2: rmos_cam_boundary
        import_violations.extend(_check_rmos_cam_boundary(py_file, imports, root))

        # Fence 4: ai_sandbox_boundary
        import_violations.extend(_check_ai_sandbox_boundary(py_file, imports))

        # Fence 5: saw_lab_encapsulation
        import_violations.extend(_check_saw_lab_encapsulation(py_file, imports))

        # Fence 7: artifact_authority
        symbol_violations.extend(_check_artifact_authority(py_file, symbols, root))

    return import_violations, symbol_violations


# --- Baseline Support ------------------------------------------------------

def _import_key(v: ImportRef) -> str:
    """Stable key for import violation (fence|file|line|module|reason)."""
    return f"{v.fence}|{_to_relpath_str(v.file)}|{v.line}|{v.module}|{v.reason}"


def _symbol_key(v: SymbolRef) -> str:
    """Stable key for symbol violation (fence|file|line|symbol|reason)."""
    return f"{v.fence}|{_to_relpath_str(v.file)}|{v.line}|{v.symbol}|{v.reason}"


def _serialize(import_violations: List[ImportRef], symbol_violations: List[SymbolRef]) -> dict:
    """Serialize violations to baseline format."""
    return {
        "version": 1,
        "imports": sorted({_import_key(v) for v in import_violations}),
        "symbols": sorted({_symbol_key(v) for v in symbol_violations}),
    }


def _load_baseline(path: Path) -> dict:
    """Load baseline JSON file."""
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or obj.get("version") != 1:
        raise RuntimeError(f"Unsupported baseline format: {path}")
    obj.setdefault("imports", [])
    obj.setdefault("symbols", [])
    return obj


# --- Reporting -------------------------------------------------------------

def _sort_imports(vs: List[ImportRef]) -> List[ImportRef]:
    return sorted(vs, key=lambda x: (x.fence, str(x.file), x.line, x.module))


def _sort_symbols(vs: List[SymbolRef]) -> List[SymbolRef]:
    return sorted(vs, key=lambda x: (x.fence, str(x.file), x.line, x.symbol))


def _has_violations(import_violations: List[ImportRef], symbol_violations: List[SymbolRef]) -> bool:
    return bool(import_violations) or bool(symbol_violations)


def _print_report(import_violations: List[ImportRef], symbol_violations: List[SymbolRef]) -> None:
    print("\n" + "=" * 60)
    print("BOUNDARY IMPORT VIOLATIONS")
    print("=" * 60 + "\n")

    if import_violations:
        for v in import_violations:
            rel = _to_relpath_str(v.file)
            print(f"  {rel}:{v.line}")
            print(f"    fence:  {v.fence}")
            print(f"    module: {v.module}")
            print(f"    reason: {v.reason}")
            print()

    if symbol_violations:
        print("\n" + "=" * 60)
        print("BOUNDARY SYMBOL VIOLATIONS")
        print("=" * 60 + "\n")

        for v in symbol_violations:
            rel = _to_relpath_str(v.file)
            print(f"  {rel}:{v.line}")
            print(f"    fence:  {v.fence}")
            print(f"    symbol: {v.symbol}")
            print(f"    reason: {v.reason}")
            print()

    total = len(import_violations) + len(symbol_violations)
    print("-" * 60)
    print(f"Total violations: {total}")
    print("-" * 60)

    # Summary of enforced fences
    print("\nEnforced fences:")
    print("  1. external_boundary     - Analyzer internals (tap_tone.*, modes.*)")
    print("  2. rmos_cam_boundary     - RMOS <-> CAM isolation")
    print("  4. ai_sandbox_boundary   - AI sandbox advisory-only")
    print("  5. saw_lab_encapsulation - Saw Lab self-containment")
    print("  7. artifact_authority    - RunArtifact construction")
    print("\nNot enforced (pattern-based):")
    print("  3. operation_lane_boundary")
    print("  6. frontend_sdk_boundary")
    print("  8. legacy_deprecation")
    print()


def _print_baseline_delta(
    baseline: dict,
    current: dict,
    *,
    baseline_path: Path,
) -> None:
    """Print delta between baseline and current violations."""
    b_imports = set(baseline.get("imports", []))
    b_symbols = set(baseline.get("symbols", []))
    c_imports = set(current.get("imports", []))
    c_symbols = set(current.get("symbols", []))

    new_imports = sorted(c_imports - b_imports)
    new_symbols = sorted(c_symbols - b_symbols)
    resolved_imports = sorted(b_imports - c_imports)
    resolved_symbols = sorted(b_symbols - c_symbols)

    if new_imports or new_symbols:
        print("\n" + "=" * 60)
        print("NEW FENCE VIOLATIONS (compared to baseline)")
        print("=" * 60 + "\n")

        for s in new_imports[:200]:
            print(f"  - import: {s}")
        if len(new_imports) > 200:
            print(f"  ... ({len(new_imports) - 200} more import violations)")

        for s in new_symbols[:200]:
            print(f"  - symbol: {s}")
        if len(new_symbols) > 200:
            print(f"  ... ({len(new_symbols) - 200} more symbol violations)")
        print()

    # Show resolved summary (progress indicator)
    if resolved_imports or resolved_symbols:
        print("\n" + "-" * 60)
        print("RESOLVED VIOLATIONS (no longer present)")
        print("-" * 60)
        print(f"  imports: {len(resolved_imports)}")
        print(f"  symbols: {len(resolved_symbols)}")
        print()

    print(f"Baseline file: {baseline_path}")
    print()


# --- CLI -------------------------------------------------------------------

def _parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m app.ci.check_boundary_imports",
        description="Fence-aware boundary import checker for ToolBox API",
    )
    p.add_argument(
        "--profile",
        type=str,
        default="toolbox",
        help="Profile name (currently only 'toolbox' is supported).",
    )
    p.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Path to baseline JSON. If provided, fail only on NEW violations vs baseline.",
    )
    p.add_argument(
        "--write-baseline",
        type=str,
        default=None,
        help="Write current violations to baseline JSON and exit 0.",
    )
    return p.parse_args(argv)


def main() -> int:
    try:
        args = _parse_args(sys.argv[1:])
        import_violations, symbol_violations = check_boundaries()
    except Exception as e:  # WP-1: keep broad — top-level CLI catch wraps arg parsing + AST scanning + file I/O
        print(f"Boundary checker error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 3

    import_violations = _sort_imports(import_violations)
    symbol_violations = _sort_symbols(symbol_violations)

    current = _serialize(import_violations, symbol_violations)

    # 1) Write baseline mode (always exit 0)
    if args.write_baseline:
        path = Path(args.write_baseline)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Wrote baseline: {path}")
        print(f"  imports: {len(current['imports'])}")
        print(f"  symbols: {len(current['symbols'])}")
        return 0

    # 2) Baseline compare mode (fail only on NEW)
    if args.baseline:
        bpath = Path(args.baseline)
        if not bpath.exists():
            print(f"Baseline not found: {bpath}", file=sys.stderr)
            print("Tip: generate it with --write-baseline <path>", file=sys.stderr)
            return 3
        try:
            baseline = _load_baseline(bpath)
        except (OSError, json.JSONDecodeError, ValueError) as e:  # WP-1: narrowed from except Exception
            print(f"Failed to read baseline {bpath}: {e}", file=sys.stderr)
            return 3

        b_imports = set(baseline.get("imports", []))
        b_symbols = set(baseline.get("symbols", []))
        c_imports = set(current.get("imports", []))
        c_symbols = set(current.get("symbols", []))

        new_imports = c_imports - b_imports
        new_symbols = c_symbols - b_symbols

        if new_imports or new_symbols:
            _print_baseline_delta(baseline, current, baseline_path=bpath)
            return 2

        # All good: no NEW violations (resolved ones are fine)
        resolved_imports = len(b_imports - c_imports)
        resolved_symbols = len(b_symbols - c_symbols)
        print("Boundary import check: OK (baseline mode)")
        if resolved_imports or resolved_symbols:
            print(f"  resolved since baseline: imports={resolved_imports} symbols={resolved_symbols}")
        return 0

    # 3) Default strict mode (fail on any violation)
    if _has_violations(import_violations, symbol_violations):
        _print_report(import_violations, symbol_violations)
        return 2

    print("Boundary import check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
