from __future__ import annotations

import ast
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


"""
Boundary Import Checker (ToolBox API)
------------------------------------

Purpose:
  Enforce hard architectural boundaries between top-level "components" under app/.

Usage:
  cd services/api
  python -m app.ci.check_boundary_imports

Exit codes:
  0 = ok
  2 = violations found
  3 = configuration / runtime error

Design:
  - Parse Python files with `ast` to avoid false positives.
  - Determine a file's "component" as the first package segment after `app.`
    e.g., app/cam/... => component "cam"
  - Allow:
      * same-component imports
      * imports to "COMMON_ALLOWLIST" modules (shared infrastructure)
      * explicit cross-component edges (EDGE_ALLOWLIST)
  - Block all other cross-component imports.

Note:
  This is intentionally conservative. If a dependency is truly legitimate, add it
  to EDGE_ALLOWLIST (prefer narrow paths) rather than weakening the default rule.
"""


# --- Configuration ---------------------------------------------------------

# Components are inferred dynamically from filesystem, but you can constrain with
# an allowlist if desired (left dynamic to avoid constant updates).

# Modules/packages under app/ that are allowed to be imported from anywhere.
# Keep this tight and "infrastructure-only".
COMMON_ALLOWLIST: Tuple[str, ...] = (
    "app.core",
    "app.config",
    "app.settings",
    "app.logging",
    "app.telemetry",  # scaffolding but safe to read from anywhere
    "app.metrics",
    "app.utils",
    "app.errors",
    "app.schemas",
    "app.types",
    "app.constants",
    "app.security",
    "app.auth",
    "app.db",
    "app.data",  # data access helpers (not domain stores)
    "app.contracts",  # schema/contract layer (Scenario B)
)

# Explicit allowed cross-component import edges.
# Key: (from_component, to_component) -> allowed import prefixes
#
# Example:
#   ("rmos", "cam"): ("app.cam.intent", "app.cam.post", ...)
#
# Rules of thumb:
#  - Prefer allowing a small set of stable "contract" or "service boundary" modules.
#  - Avoid allowing deep internal modules (those are the ones boundaries protect).
EDGE_ALLOWLIST: Dict[Tuple[str, str], Tuple[str, ...]] = {
    # RMOS may need to call CAM in a tightly scoped way (MVP wrapper / planning).
    ("rmos", "cam"): (
        "app.cam",
    ),
    # CAM may record runs/attachments via RMOS runs_v2 (still keep tight).
    ("cam", "rmos"): (
        "app.rmos.runs_v2",
        "app.rmos.feasibility",  # CAM may consume feasibility contracts
    ),
    # Routers are orchestration layer; they often compose domains.
    ("routers", "cam"): ("app.cam",),
    ("routers", "rmos"): ("app.rmos",),
    ("routers", "art_studio"): ("app.art_studio",),
    ("routers", "saw_lab"): ("app.saw_lab",),
    ("routers", "blueprint"): ("app.blueprint",),
    ("routers", "bridge"): ("app.bridge",),

    # Blueprint subsystem is allowed to use CAM bridge and CAM internals.
    ("blueprint", "cam"): ("app.cam",),

    # Bridge router may use CAM export helpers if needed.
    ("bridge", "cam"): ("app.cam",),

    # Saw Lab is a CAM mode; allow it to use CAM primitives.
    ("saw_lab", "cam"): ("app.cam",),
    ("saw_lab", "rmos"): ("app.rmos",),
}

# Components we never treat as "domains" for enforcement (infrastructure or tests).
NON_DOMAIN_COMPONENTS: Set[str] = {
    "ci",
    "__pycache__",
}

# Files to skip (generated, vendored, etc.)
SKIP_FILE_PATTERNS: Tuple[str, ...] = (
    "*/__pycache__/*",
    "*/.venv/*",
    "*/site-packages/*",
)


# --- Data structures -------------------------------------------------------

@dataclass(frozen=True)
class ImportRef:
    file: Path
    line: int
    statement: str
    module: str  # fully qualified import module, e.g. "app.cam.foo"
    from_component: str
    to_component: str


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


def _match_skip(path: Path) -> bool:
    s = str(path).replace("\\", "/")
    for pat in SKIP_FILE_PATTERNS:
        # minimal glob-like check (fast)
        if pat.strip("*") in s:
            return True
    return False


def _discover_components(app_dir: Path) -> Set[str]:
    comps: Set[str] = set()
    for child in app_dir.iterdir():
        if child.is_dir() and (child / "__init__.py").exists():
            comps.add(child.name)
    # also allow treating top-level "routers.py" style modules as component "routers"
    # if there is app/routers/ directory (common in this repo).
    if (app_dir / "routers").is_dir():
        comps.add("routers")
    return {c for c in comps if c not in NON_DOMAIN_COMPONENTS}


def _component_of_file(app_dir: Path, file_path: Path) -> Optional[str]:
    """
    Determine component based on file path relative to app/.
    app/<component>/... => component
    app/<module>.py => component "<module>" is not a directory component; treat as "app_root"
    """
    try:
        rel = file_path.resolve().relative_to(app_dir.resolve())
    except Exception:
        return None
    parts = rel.parts
    if not parts:
        return None
    if len(parts) >= 2 and parts[0] != "__pycache__":
        # component directory
        if (app_dir / parts[0]).is_dir():
            return parts[0]
    # file directly under app/ => "app_root" (treated as infra)
    return "app_root"


def _component_of_module(mod: str) -> Optional[str]:
    """
    For module string like "app.cam.foo", return "cam".
    """
    if not mod.startswith("app."):
        return None
    parts = mod.split(".")
    if len(parts) < 2:
        return None
    return parts[1]


def _is_common_allowed(mod: str) -> bool:
    return any(mod == p or mod.startswith(p + ".") for p in COMMON_ALLOWLIST)


def _is_edge_allowed(from_comp: str, to_comp: str, mod: str) -> bool:
    allowed = EDGE_ALLOWLIST.get((from_comp, to_comp))
    if not allowed:
        return False
    return any(mod == p or mod.startswith(p + ".") for p in allowed)


def _iter_python_files(app_dir: Path) -> Iterable[Path]:
    for p in app_dir.rglob("*.py"):
        if _match_skip(p):
            continue
        yield p


def _parse_imports(py_file: Path) -> List[Tuple[int, str]]:
    """
    Return list of (lineno, module) imports found in file.
    Captures both `import x` and `from x import y`.
    """
    src = py_file.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(src, filename=str(py_file))
    except SyntaxError:
        # Some files may be for older/newer syntax; treat as non-fatal and skip.
        return []

    out: List[Tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    out.append((getattr(node, "lineno", 1), alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Resolve relative imports: from .foo import bar -> app.<component>.foo
                mod = node.module
                if node.level and node.level > 0:
                    # best-effort: keep as relative marker; we'll resolve later per file component
                    mod = ("." * node.level) + mod
                out.append((getattr(node, "lineno", 1), mod))
    return out


def _resolve_relative(module: str, from_component: str) -> Optional[str]:
    """
    Convert relative module strings like ".foo" or "..bar" into absolute "app.<component>...."
    Only resolves within the same component.
    """
    if not module.startswith("."):
        return module
    # Count leading dots
    level = 0
    while level < len(module) and module[level] == ".":
        level += 1
    tail = module[level:]
    # We only support resolving within component; going above component becomes app.*
    if from_component in ("app_root", "", None):
        # cannot reliably resolve relative from app root files
        return None
    if level <= 1:
        return f"app.{from_component}.{tail}" if tail else f"app.{from_component}"
    # level >=2 : treat as app.<tail> (best-effort)
    return f"app.{tail}" if tail else "app"


# --- Core check ------------------------------------------------------------

def check_boundaries() -> List[ImportRef]:
    root = _repo_root_from_cwd()
    app_dir = root / "app"
    components = _discover_components(app_dir)

    violations: List[ImportRef] = []

    for py_file in _iter_python_files(app_dir):
        file_comp = _component_of_file(app_dir, py_file)
        if not file_comp:
            continue
        # app_root is treated as infra: allow it to import anything under app.*
        # (This matches your intentional "shared data layer" patterns).
        if file_comp == "app_root":
            continue

        imports = _parse_imports(py_file)
        for lineno, mod_raw in imports:
            mod = _resolve_relative(mod_raw, file_comp) or mod_raw

            # Only enforce imports within our app package
            if not mod.startswith("app."):
                continue

            to_comp = _component_of_module(mod)
            if not to_comp:
                continue
            if to_comp == file_comp:
                continue

            # Ignore imports to non-domain components (ci, etc.)
            if to_comp in NON_DOMAIN_COMPONENTS:
                continue

            # If to_comp isn't a discovered component, treat it as "app_root"/infra-ish.
            # Example: app/some_module.py imported as app.some_module
            if to_comp not in components:
                continue

            # Allow common infrastructure
            if _is_common_allowed(mod):
                continue

            # Allow explicit edges
            if _is_edge_allowed(file_comp, to_comp, mod):
                continue

            violations.append(
                ImportRef(
                    file=py_file,
                    line=lineno,
                    statement=f"import {mod_raw}",
                    module=mod,
                    from_component=file_comp,
                    to_component=to_comp,
                )
            )

    return violations


def _print_report(violations: List[ImportRef]) -> None:
    print("\nBOUNDARY IMPORT VIOLATIONS\n")
    for v in violations:
        rel = None
        try:
            rel = v.file.resolve().relative_to(_repo_root_from_cwd().resolve())
        except Exception:
            rel = v.file
        print(f"- {rel}:{v.line}")
        print(f"  from: {v.from_component}  ->  to: {v.to_component}")
        print(f"  module: {v.module}")
        print("")

    print("How to fix:")
    print("  - Prefer moving shared logic into app.contracts / app.core / app.utils.")
    print("  - If cross-domain is truly intended, add a narrow allowlist entry in EDGE_ALLOWLIST.")
    print("")


def main() -> int:
    try:
        violations = check_boundaries()
    except Exception as e:
        print(f"Boundary checker error: {e}", file=sys.stderr)
        return 3

    if violations:
        _print_report(violations)
        return 2

    print("Boundary import check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
