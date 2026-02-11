"""Report printing functions for boundary import checker."""
from __future__ import annotations

from pathlib import Path
from typing import List

from .models import ImportRef, SymbolRef
from .parser import to_relpath_str


def sort_imports(vs: List[ImportRef]) -> List[ImportRef]:
    """Sort import violations for consistent output."""
    return sorted(vs, key=lambda x: (x.fence, str(x.file), x.line, x.module))


def sort_symbols(vs: List[SymbolRef]) -> List[SymbolRef]:
    """Sort symbol violations for consistent output."""
    return sorted(vs, key=lambda x: (x.fence, str(x.file), x.line, x.symbol))


def has_violations(import_violations: List[ImportRef], symbol_violations: List[SymbolRef]) -> bool:
    """Check if there are any violations."""
    return bool(import_violations) or bool(symbol_violations)


def print_report(import_violations: List[ImportRef], symbol_violations: List[SymbolRef]) -> None:
    """Print violation report to stdout."""
    print("\n" + "=" * 60)
    print("BOUNDARY IMPORT VIOLATIONS")
    print("=" * 60 + "\n")

    if import_violations:
        for v in import_violations:
            rel = to_relpath_str(v.file)
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
            rel = to_relpath_str(v.file)
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


def print_baseline_delta(
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
