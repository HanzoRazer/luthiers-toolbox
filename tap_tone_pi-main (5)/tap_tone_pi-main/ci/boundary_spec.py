from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
import ast


@dataclass(frozen=True)
class Violation:
    file: str
    lineno: int
    col: int
    imported: str
    message: str


class BoundarySpec:
    """
    Enforces boundary rules by scanning Python files for forbidden import prefixes.

    This is intentionally simple and deterministic:
    - parses AST for 'import x' and 'from x import y'
    - also scans for importlib.import_module("x.y") string literals
    """

    def __init__(
        self,
        *,
        name: str,
        allowed_roots: List[str],
        forbidden_import_prefixes: List[str],
    ) -> None:
        self.name = name
        self.allowed_roots = allowed_roots
        self.forbidden_import_prefixes = forbidden_import_prefixes

    def scan_path(self, root: Path, excludes: Optional[set[str]] = None) -> List[Violation]:
        excludes = excludes or set()
        violations: List[Violation] = []

        for path in root.rglob("*.py"):
            if any(part in excludes for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                # If a file can't be read, treat as a violation so CI doesn't silently pass.
                violations.append(
                    Violation(
                        file=str(path),
                        lineno=1,
                        col=0,
                        imported="(unreadable file)",
                        message="Could not read file (encoding/permissions).",
                    )
                )
                continue

            violations.extend(self._scan_file_text(path, text))

        return violations

    def _scan_file_text(self, path: Path, text: str) -> List[Violation]:
        out: List[Violation] = []

        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as e:
            out.append(
                Violation(
                    file=str(path),
                    lineno=getattr(e, "lineno", 1) or 1,
                    col=getattr(e, "offset", 0) or 0,
                    imported="(syntax error)",
                    message=f"SyntaxError prevents scanning: {e.msg}",
                )
            )
            return out

        # AST imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    v = self._check_import(mod, path, node.lineno, node.col_offset)
                    if v:
                        out.append(v)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod = node.module
                    v = self._check_import(mod, path, node.lineno, node.col_offset)
                    if v:
                        out.append(v)

        # importlib.import_module("x.y") string literal scan (best-effort)
        out.extend(self._scan_importlib_literals(path, tree))

        return out

    def _scan_importlib_literals(self, path: Path, tree: ast.AST) -> List[Violation]:
        out: List[Violation] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            # Match: importlib.import_module("...")
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "import_module"
                and isinstance(func.value, ast.Name)
                and func.value.id == "importlib"
            ):
                continue

            if not node.args:
                continue

            arg0 = node.args[0]
            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                mod = arg0.value
                v = self._check_import(mod, path, node.lineno, node.col_offset)
                if v:
                    v = Violation(
                        file=v.file,
                        lineno=v.lineno,
                        col=v.col,
                        imported=v.imported,
                        message=v.message + " (via importlib.import_module)",
                    )
                    out.append(v)

        return out

    def _check_import(self, module: str, path: Path, lineno: int, col: int) -> Optional[Violation]:
        module = module.strip()
        for forbidden in self.forbidden_import_prefixes:
            if module == forbidden or module.startswith(forbidden + "."):
                return Violation(
                    file=str(path),
                    lineno=lineno,
                    col=col,
                    imported=module,
                    message=f"Forbidden import prefix: '{forbidden}' (boundary: {self.name})",
                )
        return None


def format_banner(spec: BoundarySpec, scan_root: Path) -> str:
    return (
        "\n"
        "──────────────────────────────────────────────────────────────\n"
        f"Boundary Guard FAILED  • preset={spec.name}\n"
        f"Scan root: {scan_root}\n"
        f"Forbidden prefixes: {', '.join(spec.forbidden_import_prefixes)}\n"
        "──────────────────────────────────────────────────────────────\n"
    )


def format_violations(violations: Iterable[Violation]) -> str:
    lines = []
    for v in violations:
        lines.append(f"{v.file}:{v.lineno}:{v.col}  import='{v.imported}'  {v.message}")
    return "\n".join(lines) + "\n"

