# tools/boundarygen/cli.py
from __future__ import annotations

import argparse
import pathlib
import sys

from .templates import (
    template_boundaryspec_md,
    template_guard_py,
    template_readme_snippet,
    template_spec_json,
)


def _apply_preset(args: argparse.Namespace) -> None:
    """
    Presets are convenience defaults. User-provided flags still win.

    - analyzer: forbid importing ToolBox namespaces
    - toolbox: forbid importing Analyzer namespaces
    """
    preset = (args.preset or "").strip().lower()
    if not preset:
        return

    def add_unique(lst: list[str], values: list[str]) -> None:
        s = set(lst)
        for v in values:
            if v not in s:
                lst.append(v)
                s.add(v)

    if preset == "analyzer":
        # Typical Analyzer module roots (can be overridden/extended by flags)
        if not args.allowed_root:
            args.allowed_root = ["tap_tone", "modes", "schemas"]
        if not args.scan_root:
            args.scan_root = ["."]

        # Forbid ToolBox-ish import roots (tighten later to exact roots if desired)
        add_unique(args.forbid, [
            "app.",
            "services.",
            "rmos.",
            "cam.",
            "compare.",
            "art_studio.",
            "workflow.",
        ])

        # Default integration channels for Analyzer → ToolBox
        if not args.channel:
            args.channel = [
                "Artifacts (zip bundles, manifests, hash-addressed attachments)",
                "HTTP APIs (versioned endpoints + typed SDK)",
                "Versioned schemas (JSON/Pydantic, stable envelopes)",
            ]

    elif preset == "toolbox":
        # Typical ToolBox module roots
        if not args.allowed_root:
            args.allowed_root = ["app"]
        if not args.scan_root:
            args.scan_root = ["services/api"]

        # Forbid Analyzer module roots
        add_unique(args.forbid, [
            "tap_tone.",
            "modes.",
            "schemas.",
        ])

        # Default integration channels for ToolBox ↔ Analyzer
        if not args.channel:
            args.channel = [
                "Artifacts (import bundle → runs_v2 attachments + run JSON pointers)",
                "HTTP APIs (frontend-safe SDK surfaces; no direct imports)",
                "Versioned schemas (CamIntentV1, Acoustics bundle manifests, etc.)",
            ]

    else:
        raise SystemExit(f"Unknown preset: {args.preset!r} (expected: analyzer|toolbox)")


def _write(path: pathlib.Path, content: str, *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(content, encoding="utf-8")


def _ensure_readme_snippet(repo_root: pathlib.Path, *, overwrite: bool) -> None:
    readme = repo_root / "README.md"
    snippet = template_readme_snippet()

    if not readme.exists():
        _write(readme, snippet, overwrite=overwrite)
        return

    txt = readme.read_text(encoding="utf-8")
    if "## 🔒 Boundary Rules (Enforced by CI)" in txt:
        return

    # Append at end (simple + safe)
    readme.write_text(txt.rstrip() + "\n\n" + snippet, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="boundarygen",
        description="Generate BoundarySpec + CI import guard scaffolding for a repo.",
    )

    ap.add_argument("--repo-root", default=".", help="Path to repo root (default: .)")
    ap.add_argument("--repo-name", required=True, help="Name of this repo (e.g., tap_tone_pi)")
    ap.add_argument("--counterpart", required=True, help="Other system name (e.g., luthiers-toolbox)")
    ap.add_argument("--preset", choices=["analyzer", "toolbox"], help="Convenience defaults for common repo types")
    ap.add_argument("--scan-root", action="append", default=[], help="Root(s) to scan for .py files (repeatable)")
    ap.add_argument("--forbid", action="append", default=[], help="Forbidden import prefix (repeatable)")
    ap.add_argument("--allowed-root", action="append", default=[], help="Allowed top-level module root (repeatable)")
    ap.add_argument("--channel", action="append", default=[], help="Allowed integration channel bullet (repeatable)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing generated files")

    args = ap.parse_args(argv)
    _apply_preset(args)

    repo_root = pathlib.Path(args.repo_root).resolve()
    scan_roots = args.scan_root or ["."]
    forbidden = args.forbid
    if not forbidden:
        print("ERROR: Provide at least one --forbid prefix", file=sys.stderr)
        return 2

    allowed_roots = args.allowed_root or []
    channels = args.channel or [
        "Artifacts (zip bundles, manifests, hash-addressed attachments)",
        "HTTP APIs (versioned endpoints + typed SDK)",
        "Versioned schemas (JSON/Pydantic, stable envelopes)",
    ]

    # Files
    guard_path = repo_root / "ci" / "check_boundary_imports.py"
    spec_path = repo_root / "boundary_spec.json"
    doc_path = repo_root / "docs" / "architecture" / "BoundarySpec.md"

    # Write
    try:
        _write(guard_path, template_guard_py(), overwrite=args.overwrite)
        _write(
            spec_path,
            template_spec_json(
                repo_name=args.repo_name,
                scan_roots=scan_roots,
                forbidden_prefixes=forbidden,
            ),
            overwrite=args.overwrite,
        )
        _write(
            doc_path,
            template_boundaryspec_md(
                repo_name=args.repo_name,
                counterpart_name=args.counterpart,
                allowed_roots=allowed_roots,
                forbidden_prefixes=forbidden,
                integration_channels=channels,
            ),
            overwrite=args.overwrite,
        )
        _ensure_readme_snippet(repo_root, overwrite=args.overwrite)
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Use --overwrite to replace existing files.", file=sys.stderr)
        return 1

    print("✅ Generated BoundarySpec scaffolding:")
    print(f" - {guard_path.relative_to(repo_root)}")
    print(f" - {spec_path.relative_to(repo_root)}")
    print(f" - {doc_path.relative_to(repo_root)}")
    print()
    print("Add this GitHub Actions step:")
    print("  - name: Enforce boundary rules")
    print("    run: |")
    print("      python ci/check_boundary_imports.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
