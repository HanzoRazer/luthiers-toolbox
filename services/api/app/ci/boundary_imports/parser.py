"""AST parsing utilities for boundary import checker."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, List, Set, Tuple

from .config import RUNARTIFACT_SYMBOL, SKIP_FILE_PATTERNS


def repo_root_from_cwd() -> Path:
    """
    Expected execution: services/api as cwd, with app/ present.
    If not, we still try to locate an 'app' directory upward.
    """
    cwd = Path.cwd().resolve()
    for p in [cwd] + list(cwd.parents):
        if (p / "app").is_dir():
            return p
    raise RuntimeError("Could not locate services/api root (missing app/). Run from services/api.")


def to_relpath_str(path: Path) -> str:
    """Convert path to stable relative string for baseline keys."""
    root = repo_root_from_cwd()
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def match_skip(path: Path) -> bool:
    """Check if path matches skip patterns."""
    s = str(path).replace("\\", "/")
    for pat in SKIP_FILE_PATTERNS:
        if pat.strip("*") in s:
            return True
    return False


def iter_python_files(app_dir: Path) -> Iterable[Path]:
    """Iterate over Python files in app directory."""
    for p in app_dir.rglob("*.py"):
        if match_skip(p):
            continue
        yield p


def file_matches_path(file_path: Path, patterns: Tuple[str, ...]) -> bool:
    """Check if file path matches any of the given path patterns."""
    s = str(file_path).replace("\\", "/")
    for pat in patterns:
        if pat in s:
            return True
    return False


def normalize_file_key(file_path: Path, root: Path) -> str:
    """Get normalized file key for exception matching."""
    try:
        rel = file_path.resolve().relative_to(root.resolve())
        return str(rel).replace("\\", "/")
    except ValueError:
        return str(file_path).replace("\\", "/")


def is_cam_file(file_path: Path) -> bool:
    """Check if file is in CAM directory."""
    s = str(file_path).replace("\\", "/")
    return "/cam/" in s or "/app/cam" in s


def is_rmos_file(file_path: Path) -> bool:
    """Check if file is in RMOS directory."""
    s = str(file_path).replace("\\", "/")
    return "/rmos/" in s or "/app/rmos" in s


def module_matches_prefix(module: str, prefixes: Tuple[str, ...]) -> bool:
    """Check if module matches any of the given prefixes."""
    for prefix in prefixes:
        if module == prefix or module.startswith(prefix + "."):
            return True
    return False


def parse_imports_and_symbols(py_file: Path) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]], bool]:
    """Parse file and return imports, symbol refs, and TYPE_CHECKING presence."""
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
