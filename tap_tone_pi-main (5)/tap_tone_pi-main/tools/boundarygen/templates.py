# tools/boundarygen/templates.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from textwrap import dedent
from typing import List


def template_guard_py() -> str:
    # v1 guard, embedded here so generator is self-contained
    return dedent(
        r'''
        #!/usr/bin/env python3
        # ci/check_boundary_imports.py
        """
        Boundary Guard v1.0 — Reusable cross-repo import enforcement.

        Reads boundary_spec.json from repo root and fails CI on violations.
        Detects: import, from-import, importlib.import_module(), __import__()

        Usage:
            python ci/check_boundary_imports.py
        """
        from __future__ import annotations

        import ast
        import fnmatch
        import json
        import pathlib
        import sys
        from dataclasses import dataclass
        from typing import Iterable, List, Optional


        @dataclass(frozen=True)
        class Violation:
            path: str
            line: int
            col: int
            kind: str
            module: str
            detail: str


        def _load_spec(root: pathlib.Path) -> dict:
            p = root / "boundary_spec.json"
            if not p.exists():
                raise FileNotFoundError(f"Missing boundary_spec.json at {p}")
            return json.loads(p.read_text(encoding="utf-8"))


        def _iter_py_files(repo_root: pathlib.Path, scan_roots: List[str]) -> Iterable[pathlib.Path]:
            skip_dirs = {"venv", ".venv", "node_modules", "dist", "build", "__pycache__", ".git", ".pytest_cache", ".mypy_cache"}
            for sr in scan_roots:
                base = (repo_root / sr).resolve()
                if not base.exists():
                    continue
                for p in base.rglob("*.py"):
                    if any(d in p.parts for d in skip_dirs):
                        continue
                    yield p


        def _is_allowed(path: pathlib.Path, allow_globs: List[str], repo_root: pathlib.Path) -> bool:
            rel = path.relative_to(repo_root).as_posix()
            for pat in allow_globs:
                pat = pat[2:] if pat.startswith("./") else pat
                if fnmatch.fnmatch(rel, pat):
                    return True
            return False


        def _matches_forbidden(module: str, forbidden_prefixes: List[str]) -> bool:
            return any(
                module == pref.rstrip(".") or module.startswith(pref)
                for pref in forbidden_prefixes
            )


        def _first_str_arg(node: ast.Call) -> Optional[str]:
            if not node.args:
                return None
            a0 = node.args[0]
            if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                return a0.value
            return None


        def _scan_file(path: pathlib.Path, forbidden_prefixes: List[str]) -> List[Violation]:
            try:
                src = path.read_text(encoding="utf-8")
                tree = ast.parse(src, filename=str(path))
            except (SyntaxError, UnicodeDecodeError):
                return []

            violations: List[Violation] = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name
                        if _matches_forbidden(name, forbidden_prefixes):
                            violations.append(Violation(
                                path=str(path), line=node.lineno, col=node.col_offset,
                                kind="import", module=name, detail="direct import",
                            ))

                elif isinstance(node, ast.ImportFrom) and node.module:
                    if _matches_forbidden(node.module, forbidden_prefixes):
                        violations.append(Violation(
                            path=str(path), line=node.lineno, col=node.col_offset,
                            kind="from-import", module=node.module, detail="from-import",
                        ))

                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                        mod = _first_str_arg(node)
                        if mod and _matches_forbidden(mod, forbidden_prefixes):
                            violations.append(Violation(
                                path=str(path), line=node.lineno, col=node.col_offset,
                                kind="importlib", module=mod, detail="importlib.import_module",
                            ))

                    elif isinstance(node.func, ast.Name) and node.func.id == "__import__":
                        mod = _first_str_arg(node)
                        if mod and _matches_forbidden(mod, forbidden_prefixes):
                            violations.append(Violation(
                                path=str(path), line=node.lineno, col=node.col_offset,
                                kind="__import__", module=mod, detail="dynamic import",
                            ))

            return violations


        def main() -> int:
            repo_root = pathlib.Path(__file__).resolve().parents[1]
            spec = _load_spec(repo_root)

            forbidden_prefixes: List[str] = spec["forbidden_prefixes"]
            scan_roots: List[str] = spec.get("scan_roots", ["."])
            allow_files: List[str] = spec.get("allow_files", [])
            readme_anchor = spec.get("readme_anchor", "README.md#boundary-rules")

            violations: List[Violation] = []

            for path in _iter_py_files(repo_root, scan_roots):
                if _is_allowed(path, allow_files, repo_root):
                    continue
                violations.extend(_scan_file(path, forbidden_prefixes))

            if violations:
                print("❌ Boundary violation: forbidden cross-repo import.")
                print(f"See {readme_anchor}")
                print()
                for v in violations:
                    print(f"{v.path}:{v.line}:{v.col} [{v.kind}] {v.module} ({v.detail})")
                return 1

            print("✅ Boundary check passed")
            return 0


        if __name__ == "__main__":
            sys.exit(main())
        '''
    ).lstrip()


def template_spec_json(
    repo_name: str,
    scan_roots: List[str],
    forbidden_prefixes: List[str],
    allow_files: List[str] | None = None,
    readme_anchor: str = "README.md#boundary-rules",
) -> str:
    payload = {
        "repo_name": repo_name,
        "scan_roots": scan_roots,
        "forbidden_prefixes": forbidden_prefixes,
        "allow_files": allow_files or [],
        "readme_anchor": readme_anchor,
    }
    return json.dumps(payload, indent=2) + "\n"


def template_readme_snippet() -> str:
    return dedent(
        """
        <a id="boundary-rules"></a>
        ## 🔒 Boundary Rules (Enforced by CI)

        This repository enforces a hard architectural boundary.

        ❌ Cross-repo imports are not allowed.  
        ✅ Integration must happen via artifacts, schemas, or HTTP APIs.

        If CI fails with a boundary violation:
        - Do NOT add an exception.
        - Do NOT "just import it".
        - Instead, define or extend a contract between systems.

        See `docs/architecture/BoundarySpec.md` for rationale.
        """
    ).strip() + "\n"


def template_boundaryspec_md(
    repo_name: str,
    counterpart_name: str,
    allowed_roots: List[str],
    forbidden_prefixes: List[str],
    integration_channels: List[str],
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    allowed_list = "\n".join([f"- `{r}`" for r in allowed_roots]) if allowed_roots else "- (none specified)"
    forbidden_list = "\n".join([f"- `{p}`" for p in forbidden_prefixes])
    channel_list = "\n".join([f"- {c}" for c in integration_channels])
    return dedent(
        f"""
        # BoundarySpec — {repo_name} ↔ {counterpart_name}

        Date: {now}  
        Status: Active  
        Enforced by: `ci/check_boundary_imports.py` + `boundary_spec.json`

        ## Purpose

        Prevent "quiet coupling" and long-term drift by forbidding direct Python imports across system boundaries.
        This forces integrations to happen through explicit contracts.

        ## Allowed module roots (this repo)

        The following top-level module roots are considered valid "inside boundary" imports:

        {allowed_list}

        ## Forbidden import prefixes (static guard)

        Any import matching one of these prefixes will fail CI:

        {forbidden_list}

        ## Allowed integration channels (how systems may talk)

        {channel_list}

        ## Rules of engagement

        - The "instrument/analyzer" side emits **facts** (signals, spectra, measurements, manifests).
        - The "toolbox/platform" side emits **interpretations** (recommendations, constraints, advisories, model coupling).
        - Data exchange should be **append-only** where possible (manifests, audit logs).
        - Any new coupling must be introduced as a versioned schema or API contract.

        ## CI failure message

        When CI fails, it should point contributors here:

        - `README.md#boundary-rules`
        - This document: `docs/architecture/BoundarySpec.md`

        ## Change control

        Any change to `boundary_spec.json` requires a PR note explaining:
        - Why the boundary must change
        - What alternative contract could have been used instead
        - Migration plan for existing code
        """
    ).strip() + "\n"
