#!/usr/bin/env python3
"""
API Contract Validator

Validates that frontend API calls match backend endpoint definitions.
Catches frontend-backend drift before deployment.

Usage:
    python scripts/validate_api_contracts.py
    python scripts/validate_api_contracts.py --strict  # Fail on warnings too
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Set, Dict, List, Tuple

# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent
CONTRACTS_FILE = REPO_ROOT / "contracts" / "api_endpoints.json"
FRONTEND_DIR = REPO_ROOT / "packages" / "client" / "src"
BACKEND_DIR = REPO_ROOT / "services" / "api" / "app"


def load_contract() -> Dict:
    """Load the API contract file."""
    if not CONTRACTS_FILE.exists():
        print(f"ERROR: Contract file not found: {CONTRACTS_FILE}")
        sys.exit(1)

    with open(CONTRACTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_frontend_api_calls(directory: Path) -> Set[str]:
    """
    Scan frontend code for fetch('/api/...') calls.
    Returns set of API paths found.
    """
    api_calls = set()

    # Patterns to match API calls
    patterns = [
        r"fetch\(['\"`](/api/[^'\"`\s\)]+)",  # fetch('/api/...')
        r"fetch\(['\"`]\$\{[^}]+\}(/api/[^'\"`\s\)]+)",  # fetch(`${base}/api/...`)
        r"\.get\(['\"`](/api/[^'\"`\s\)]+)",  # axios.get('/api/...')
        r"\.post\(['\"`](/api/[^'\"`\s\)]+)",  # axios.post('/api/...')
        r"\.put\(['\"`](/api/[^'\"`\s\)]+)",
        r"\.delete\(['\"`](/api/[^'\"`\s\)]+)",
    ]

    for ext in ["*.vue", "*.ts", "*.js"]:
        for file_path in directory.rglob(ext):
            try:
                content = file_path.read_text(encoding="utf-8")
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Normalize: remove query params, trailing slashes inconsistency
                        path = match.split("?")[0].split("#")[0]
                        api_calls.add(path)
            except (OSError, UnicodeDecodeError):
                continue

    return api_calls


def normalize_path(path: str) -> str:
    """Normalize API path for comparison (handle path params)."""
    # Replace specific IDs with {param} placeholder
    # /api/posts/GRBL -> /api/posts/{id}
    # /api/machines/123 -> /api/machines/{id}
    normalized = re.sub(r"/[a-zA-Z0-9_-]{8,}$", "/{id}", path)
    normalized = re.sub(r"/[0-9]+$", "/{id}", normalized)
    return normalized


def path_matches_endpoint(call_path: str, endpoint_path: str) -> bool:
    """Check if a frontend call path matches an endpoint definition."""
    # Exact match
    if call_path == endpoint_path:
        return True

    # Normalize trailing slashes
    if call_path.rstrip("/") == endpoint_path.rstrip("/"):
        return True

    # Check parameterized match
    # /api/posts/GRBL should match /api/posts/{post_id}
    call_parts = call_path.strip("/").split("/")
    endpoint_parts = endpoint_path.strip("/").split("/")

    if len(call_parts) != len(endpoint_parts):
        return False

    for call_part, endpoint_part in zip(call_parts, endpoint_parts):
        if endpoint_part.startswith("{") and endpoint_part.endswith("}"):
            continue  # Parameter placeholder matches anything
        if call_part != endpoint_part:
            return False

    return True


def find_matching_endpoint(call_path: str, endpoints: Dict) -> str | None:
    """Find which endpoint definition matches a frontend call."""
    for endpoint_path in endpoints:
        if path_matches_endpoint(call_path, endpoint_path):
            return endpoint_path
    return None


def validate(strict: bool = False) -> Tuple[int, int, int]:
    """
    Run validation and return (errors, warnings, ok_count).
    """
    contract = load_contract()
    endpoints = contract.get("endpoints", {})

    print("=" * 60)
    print("API Contract Validation")
    print("=" * 60)
    print(f"Contract: {CONTRACTS_FILE}")
    print(f"Frontend: {FRONTEND_DIR}")
    print(f"Endpoints defined: {len(endpoints)}")
    print()

    # Extract frontend API calls
    print("Scanning frontend for API calls...")
    frontend_calls = extract_frontend_api_calls(FRONTEND_DIR)
    print(f"Found {len(frontend_calls)} unique API calls")
    print()

    errors = []
    warnings = []
    matched = []

    for call_path in sorted(frontend_calls):
        endpoint = find_matching_endpoint(call_path, endpoints)
        if endpoint:
            matched.append((call_path, endpoint))
        else:
            # Check if it's a common pattern that might be intentionally missing
            if "/api/_" in call_path:  # Internal endpoints like /api/_analytics
                warnings.append(f"Internal endpoint not in contract: {call_path}")
            else:
                errors.append(f"No matching endpoint for: {call_path}")

    # Report results
    print("-" * 60)
    print("MATCHED (frontend call -> endpoint)")
    print("-" * 60)
    for call_path, endpoint in matched:
        if call_path == endpoint:
            print(f"  OK  {call_path}")
        else:
            print(f"  OK  {call_path} -> {endpoint}")
    print()

    if warnings:
        print("-" * 60)
        print(f"WARNINGS ({len(warnings)})")
        print("-" * 60)
        for w in warnings:
            print(f"  WARN  {w}")
        print()

    if errors:
        print("-" * 60)
        print(f"ERRORS ({len(errors)})")
        print("-" * 60)
        for e in errors:
            print(f"  ERR   {e}")
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Matched:  {len(matched)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Errors:   {len(errors)}")
    print()

    if errors:
        print("FAILED: Frontend calls endpoints not defined in contract.")
        print("Fix: Add missing endpoints to contracts/api_endpoints.json")
        print("     OR fix frontend to use correct endpoint paths")
        return (len(errors), len(warnings), len(matched))

    if warnings and strict:
        print("FAILED (strict mode): Warnings treated as errors.")
        return (len(warnings), 0, len(matched))

    print("PASSED: All frontend API calls have matching endpoint definitions.")
    return (0, len(warnings), len(matched))


def write_baseline(frontend_calls: Set[str], output_path: Path):
    """Write current frontend calls as baseline (known state)."""
    baseline = {
        "description": "Baseline of frontend API calls - violations against these are known",
        "generated": str(Path(__file__).name),
        "calls": sorted(frontend_calls)
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2)
    print(f"Wrote baseline: {output_path}")


def load_baseline(baseline_path: Path) -> Set[str]:
    """Load baseline of known frontend calls."""
    if not baseline_path.exists():
        return set()
    with open(baseline_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return set(data.get("calls", []))


def main():
    parser = argparse.ArgumentParser(description="Validate API contracts")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    parser.add_argument("--write-baseline", action="store_true",
                        help="Write current frontend calls as baseline")
    parser.add_argument("--baseline", type=Path,
                        help="Only fail on NEW violations not in baseline")
    args = parser.parse_args()

    # Handle baseline writing
    if args.write_baseline:
        frontend_calls = extract_frontend_api_calls(FRONTEND_DIR)
        baseline_path = REPO_ROOT / "contracts" / "api_calls_baseline.json"
        write_baseline(frontend_calls, baseline_path)
        sys.exit(0)

    errors, warnings, matched = validate(strict=args.strict)

    # If using baseline mode, only count NEW violations
    if args.baseline and errors > 0:
        baseline_calls = load_baseline(args.baseline)
        frontend_calls = extract_frontend_api_calls(FRONTEND_DIR)
        contract = load_contract()
        endpoints = contract.get("endpoints", {})

        new_violations = []
        for call in frontend_calls:
            if call not in baseline_calls:  # New call not in baseline
                if not find_matching_endpoint(call, endpoints):
                    new_violations.append(call)

        if new_violations:
            print(f"\nNEW violations (not in baseline): {len(new_violations)}")
            for v in new_violations:
                print(f"  NEW  {v}")
            errors = len(new_violations)
        else:
            print(f"\nNo NEW violations (existing violations in baseline are ignored)")
            errors = 0

    if args.json:
        print(json.dumps({
            "errors": errors,
            "warnings": warnings,
            "matched": matched,
            "passed": errors == 0 and (not args.strict or warnings == 0)
        }))

    sys.exit(1 if errors > 0 or (args.strict and warnings > 0) else 0)


if __name__ == "__main__":
    main()
