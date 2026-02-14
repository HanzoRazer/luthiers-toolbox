#!/usr/bin/env python3
"""
Generate API Contract from Backend Routers

Extracts all registered endpoints from the FastAPI application
and generates the contracts/api_endpoints.json file.

Usage:
    cd services/api && python ../../scripts/generate_api_contract.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the services/api directory to path
REPO_ROOT = Path(__file__).parent.parent
API_DIR = REPO_ROOT / "services" / "api"
sys.path.insert(0, str(API_DIR))

os.chdir(API_DIR)


def extract_endpoints():
    """Extract all endpoints from the FastAPI app."""
    try:
        from app.main import app
    except ImportError as e:
        print(f"ERROR: Could not import FastAPI app: {e}")
        print("Make sure you're running from the repo root with dependencies installed.")
        sys.exit(1)

    endpoints = {}

    for route in app.routes:
        # Skip internal routes
        if not hasattr(route, 'path'):
            continue

        path = route.path
        methods = list(route.methods - {"HEAD", "OPTIONS"}) if hasattr(route, 'methods') else []

        if not path.startswith("/api"):
            # Include health and metrics but skip others
            if path not in ["/health", "/metrics"]:
                continue

        # Get description from docstring if available
        description = ""
        if hasattr(route, 'endpoint') and route.endpoint.__doc__:
            description = route.endpoint.__doc__.strip().split('\n')[0]

        # Determine category from path
        category = "core"
        if "/cam/" in path:
            category = "cam"
        elif "/rmos/" in path:
            category = "rmos"
        elif "/art/" in path:
            category = "art"
        elif "/blueprint/" in path:
            category = "blueprint"
        elif "/machines" in path or "/posts" in path:
            category = "config"
        elif "/geometry" in path:
            category = "geometry"

        if path not in endpoints:
            endpoints[path] = {
                "methods": sorted(methods),
                "description": description,
                "category": category
            }
        else:
            # Merge methods if path already exists
            existing_methods = set(endpoints[path]["methods"])
            existing_methods.update(methods)
            endpoints[path]["methods"] = sorted(existing_methods)

    return endpoints


def generate_contract(endpoints: dict) -> dict:
    """Generate the contract JSON structure."""
    return {
        "$schema": "./api_endpoints.schema.json",
        "version": "1.0.0",
        "description": "API endpoint contract - auto-generated from FastAPI routes",
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "endpoint_count": len(endpoints),
        "endpoints": dict(sorted(endpoints.items()))
    }


def main():
    print("Extracting endpoints from FastAPI app...")
    endpoints = extract_endpoints()
    print(f"Found {len(endpoints)} endpoints")

    contract = generate_contract(endpoints)

    output_path = REPO_ROOT / "contracts" / "api_endpoints.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2)

    print(f"Generated: {output_path}")

    # Print summary by category
    categories = {}
    for path, info in endpoints.items():
        cat = info.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1

    print("\nEndpoints by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
