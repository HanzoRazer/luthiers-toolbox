#!/usr/bin/env python3
"""
Trace Live Path - Blueprint Vectorizer Endpoint Mapper

CLI tool to verify the exact production code path for blueprint endpoints.
Use this BEFORE implementing any fix to confirm you're targeting the right function.

Usage:
    python scripts/trace_live_path.py
    python scripts/trace_live_path.py --endpoint /api/blueprint/vectorize/async
    python scripts/trace_live_path.py --mode refined
    python scripts/trace_live_path.py --mode layered_dual_pass

Output:
    Prints the router -> orchestrator -> cleaner/writer chain for the given config.

Author: Production Shop
"""

import argparse
import sys
from pathlib import Path

# Add services/api to path for imports
API_ROOT = Path(__file__).parent.parent / "services" / "api"
sys.path.insert(0, str(API_ROOT))


# --- Mode Dispatch Table ---

MODE_DISPATCH = {
    "refined": {
        "function": "_clean_blueprint_refined()",
        "file": "services/api/app/services/blueprint_clean.py",
        "pipeline": "extract_blueprint_to_dxf -> clean_blueprint_dxf",
        "writer": "unified_dxf_cleaner.write_selected_chains",
        "features": {
            "outline_reconstructor": False,
            "gap_joining": False,
            "layer_classification": False,
            "pass_b_annotation": False,
            "annotations_in_output": False,
        },
    },
    "baseline": {
        "function": "_clean_blueprint_baseline()",
        "file": "services/api/app/services/blueprint_clean.py",
        "pipeline": "extract_blueprint_to_dxf -> clean_blueprint_dxf",
        "writer": "unified_dxf_cleaner.write_selected_chains",
        "features": {
            "outline_reconstructor": False,
            "gap_joining": False,
            "layer_classification": False,
            "pass_b_annotation": False,
            "annotations_in_output": False,
        },
    },
    "restored_baseline": {
        "function": "_clean_blueprint_restored_baseline()",
        "file": "services/api/app/services/blueprint_clean.py",
        "pipeline": "extract_blueprint_to_dxf -> clean_blueprint_dxf",
        "writer": "unified_dxf_cleaner.write_selected_chains",
        "features": {
            "outline_reconstructor": "GATED (env ENABLE_OUTLINE_RECONSTRUCTION=1)",
            "gap_joining": False,
            "layer_classification": False,
            "pass_b_annotation": False,
            "annotations_in_output": False,
        },
    },
    "layered_dual_pass": {
        "function": "orchestrator dual-pass path (lines 300-382)",
        "file": "services/api/app/services/blueprint_orchestrator.py",
        "pipeline": "extract_entities_simple + extract_annotations -> build_layers -> join_body_gaps",
        "writer": "write_layered_dxf",
        "default_preset": "geometry_only",
        "features": {
            "outline_reconstructor": False,
            "gap_joining": True,
            "layer_classification": True,
            "pass_b_annotation": True,
            "annotations_in_output": "ONLY with export_preset=reference_full (default: NO)",
        },
    },
}

ENDPOINT_INFO = {
    "/api/blueprint/vectorize/async": {
        "router": "services/api/app/routers/blueprint_async_router.py",
        "handler": "vectorize_blueprint_async()",
        "default_mode": "layered_dual_pass",  # Frontend sends this explicitly
        "backend_fallback": "refined",  # Form default if mode not sent
        "form_field": 'mode: str = Form("refined")',
    },
    "/api/blueprint/vectorize": {
        "router": "services/api/app/routers/blueprint/vectorize_router.py",
        "handler": "vectorize_blueprint()",
        "default_mode": "layered_dual_pass",  # Frontend sends this explicitly
        "backend_fallback": "refined",  # Form default if mode not sent
        "form_field": 'mode: str = Form("refined")',
    },
}


def print_separator(char="-", width=70):
    print(char * width)


def print_header(title):
    print()
    print_separator("=")
    print(f"  {title}")
    print_separator("=")


def trace_endpoint(endpoint: str):
    """Print the full trace for an endpoint."""
    info = ENDPOINT_INFO.get(endpoint)
    if not info:
        print(f"Unknown endpoint: {endpoint}")
        print(f"Known endpoints: {list(ENDPOINT_INFO.keys())}")
        return

    print_header(f"Endpoint: {endpoint}")
    print(f"  Router:        {info['router']}")
    print(f"  Handler:       {info['handler']}")
    print(f"  Default mode:  {info['default_mode']}")
    print(f"  Form field:    {info['form_field']}")


def trace_mode(mode: str):
    """Print the full trace for a mode."""
    dispatch = MODE_DISPATCH.get(mode)
    if not dispatch:
        print(f"Unknown mode: {mode}")
        print(f"Known modes: {list(MODE_DISPATCH.keys())}")
        return

    print_header(f"Mode: {mode}")
    print(f"  Function:  {dispatch['function']}")
    print(f"  File:      {dispatch['file']}")
    print(f"  Pipeline:  {dispatch['pipeline']}")
    print(f"  Writer:    {dispatch['writer']}")
    if dispatch.get("default_preset"):
        print(f"  Preset:    {dispatch['default_preset']} (default)")
    print()
    print("  Features:")
    for feature, status in dispatch["features"].items():
        status_str = status if isinstance(status, str) else ("YES" if status else "NO")
        print(f"    {feature}: {status_str}")


def trace_production_default():
    """Print the current production default path."""
    print_header("PRODUCTION DEFAULT PATH (promoted 2026-04-15)")
    print()
    print("  Frontend:    hostinger/blueprint-reader.html")
    print("  Endpoint:    /api/blueprint/vectorize/async")
    print("  Mode sent:   'layered_dual_pass'")
    print("  Preset:      geometry_only (BODY layer only)")
    print()
    trace_mode("layered_dual_pass")
    print()
    print_separator()
    print("  NOTE: Production now uses orchestrator dual-pass path.")
    print("        Fixes go in blueprint_orchestrator.py lines 270-382.")
    print_separator()


def trace_rollback_path():
    """Print the rollback path (former production default)."""
    print_header("ROLLBACK PATH (refined)")
    print()
    print("  Former production default. Use for fallback testing.")
    print("  To rollback: ?blueprint_mode=refined in URL")
    print()
    trace_mode("refined")
    print()
    print_separator()
    print("  ANNOTATION NOTE:")
    print("    Pass B annotation extraction RUNS in layered_dual_pass.")
    print("    BUT default export_preset=geometry_only EXCLUDES annotations.")
    print("    To include annotations: use export_preset=reference_full")
    print_separator()


def main():
    parser = argparse.ArgumentParser(
        description="Trace the live code path for blueprint vectorizer endpoints"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        help="Endpoint to trace (e.g., /api/blueprint/vectorize/async)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=list(MODE_DISPATCH.keys()),
        help="Mode to trace",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all endpoints and modes",
    )

    args = parser.parse_args()

    if args.all:
        for endpoint in ENDPOINT_INFO:
            trace_endpoint(endpoint)
        for mode in MODE_DISPATCH:
            trace_mode(mode)
    elif args.endpoint:
        trace_endpoint(args.endpoint)
        # Also show the default mode for this endpoint
        info = ENDPOINT_INFO.get(args.endpoint)
        if info:
            trace_mode(info["default_mode"])
    elif args.mode:
        trace_mode(args.mode)
    else:
        # Default: show production path and rollback
        trace_production_default()
        print()
        trace_rollback_path()


if __name__ == "__main__":
    main()
