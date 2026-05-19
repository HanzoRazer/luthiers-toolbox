#!/usr/bin/env python3
"""
Governance Utility: List Registered Translators

Lists all translators in the TranslatorRegistry with their capabilities
and execution states. Used for governance auditing and migration tracking.

Usage:
    python scripts/governance/list_translators.py
    python scripts/governance/list_translators.py --governed-only
    python scripts/governance/list_translators.py --target dxf
    python scripts/governance/list_translators.py --json

MRP-4B: Translator Registry Integration
"""
import argparse
import json
import sys
from pathlib import Path

# Add services/api to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.cam.translators import get_translator_registry
from app.cam.translators.base import ExecutionState


def list_translators(
    governed_only: bool = False,
    target: str = None,
    output_json: bool = False,
) -> int:
    """
    List registered translators with their capabilities.

    Args:
        governed_only: Only show governed_execution translators
        target: Filter by target format (dxf, svg, etc.)
        output_json: Output as JSON instead of table

    Returns:
        Exit code (0 = success)
    """
    registry = get_translator_registry()

    if governed_only:
        translator_ids = registry.list_governed()
    else:
        translator_ids = registry.list_all()

    results = []
    for tid in sorted(translator_ids):
        cap = registry.get_capabilities(tid)
        if cap is None:
            continue

        # Filter by target if specified
        if target and cap.target_format.lower() != target.lower():
            continue

        results.append({
            "translator_id": tid,
            "target_format": cap.target_format,
            "format_version": cap.format_version or "N/A",
            "execution_state": cap.execution_state.value,
            "category": cap.category.value,
            "deterministic": cap.deterministic,
            "provenance_supported": cap.provenance_supported,
            "description": cap.description,
        })

    if output_json:
        print(json.dumps({"translators": results, "count": len(results)}, indent=2))
        return 0

    # Table output
    print("\n" + "=" * 80)
    print("TRANSLATOR REGISTRY")
    print("=" * 80)
    print(f"\n{'Translator ID':<35} {'Target':<8} {'Version':<8} {'State':<20}")
    print("-" * 80)

    for r in results:
        state_marker = "[GOV]" if r["execution_state"] == "governed_execution" else "[   ]"
        print(f"{r['translator_id']:<35} {r['target_format']:<8} {r['format_version']:<8} {state_marker} {r['execution_state']}")

    print("-" * 80)
    print(f"Total: {len(results)} translators")

    # Summary by state
    by_state = {}
    for r in results:
        state = r["execution_state"]
        by_state[state] = by_state.get(state, 0) + 1

    print("\nBy Execution State:")
    for state, count in sorted(by_state.items()):
        print(f"  {state}: {count}")

    # Summary by target
    by_target = {}
    for r in results:
        t = r["target_format"]
        by_target[t] = by_target.get(t, 0) + 1

    print("\nBy Target Format:")
    for t, count in sorted(by_target.items()):
        print(f"  {t}: {count}")

    print()
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="List registered translators in the governance registry"
    )
    parser.add_argument(
        "--governed-only", "-g",
        action="store_true",
        help="Only show governed_execution translators"
    )
    parser.add_argument(
        "--target", "-t",
        type=str,
        help="Filter by target format (dxf, svg, etc.)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    try:
        return list_translators(
            governed_only=args.governed_only,
            target=args.target,
            output_json=args.json,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
