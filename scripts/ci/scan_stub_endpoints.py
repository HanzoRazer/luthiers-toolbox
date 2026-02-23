#!/usr/bin/env python3
"""
Stub Endpoint Scanner

Statically analyzes FastAPI routers to detect stub endpoints.
Stubs are placeholder endpoints that return empty/default responses.

Usage:
    python scripts/scan_stub_endpoints.py --app-root /path/to/app
    python scripts/scan_stub_endpoints.py --app-root /path/to/app --json
    python scripts/scan_stub_endpoints.py --app-root /path/to/app --verbose

Stub Detection Heuristics:
    1. File-level: filename contains "stub" (e.g., stub_routes.py)
    2. Router-level: APIRouter tags contain "stub"
    3. Response-level: returns patterns like:
       - {"ok": True/False, "message": "Stub: ..."}
       - {"items": [], ...}
       - [] (empty list)
       - {"status": "not_implemented"}
    4. Code-level: function body contains "stub" or "not_implemented"
"""

import ast
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict


@dataclass
class StubEndpoint:
    """Information about a detected stub endpoint."""
    file: str
    line: int
    method: str
    path: str
    function_name: str
    indicators: List[str] = field(default_factory=list)
    confidence: str = "medium"  # low, medium, high


@dataclass
class ScanResult:
    """Result of stub endpoint scan."""
    total_endpoints: int = 0
    stub_endpoints: int = 0
    files_scanned: int = 0
    stubs: List[StubEndpoint] = field(default_factory=list)
    by_confidence: Dict[str, int] = field(default_factory=lambda: {"high": 0, "medium": 0, "low": 0})
    by_file: Dict[str, int] = field(default_factory=dict)


# Patterns that indicate stub responses
STUB_RESPONSE_PATTERNS = [
    (r'"message":\s*"[Ss]tub[:\s]', "response contains 'Stub:' message"),
    (r'"status":\s*"not_implemented"', "status: not_implemented"),
    (r'"status":\s*"stub"', "status: stub"),
    (r'return\s*\[\s*\]', "returns empty list"),
    (r'return\s*\{\s*\}', "returns empty dict"),
    (r'return\s*\{\s*"items":\s*\[\s*\]', "returns empty items list"),
    (r'return\s*\{\s*"ok":\s*True,\s*"[^"]+_id":\s*None', "returns ok with null ID"),
    (r'return\s*\{\s*"[^"]+":\s*None\s*\}', "returns single null field"),
    (r'return\s*\{\s*"[^"]+":\s*\[\s*\],\s*"total":\s*0\s*\}', "returns empty list with zero total"),
]

# Code patterns that indicate stub implementation
STUB_CODE_PATTERNS = [
    (r'#\s*[Ss]tub', "comment mentions stub"),
    (r'#\s*[Tt][Oo][Dd][Oo]', "contains TODO comment"),
    (r'#\s*[Nn]ot\s*[Ii]mplemented', "comment: not implemented"),
    (r'raise\s+NotImplementedError', "raises NotImplementedError"),
    (r'pass\s*$', "function body is just 'pass'"),
]


def is_stub_filename(path: Path) -> bool:
    """Check if filename indicates a stub file."""
    name = path.stem.lower()
    return "stub" in name


def extract_router_tags(content: str) -> List[str]:
    """Extract tags from APIRouter() instantiation."""
    tags = []
    # Match tags=["tag1", "tag2"] or tags=('tag1', 'tag2')
    pattern = r'APIRouter\s*\([^)]*tags\s*=\s*[\[\(]([^\]\)]+)[\]\)]'
    match = re.search(pattern, content)
    if match:
        tag_str = match.group(1)
        # Extract quoted strings
        tags = re.findall(r'["\']([^"\']+)["\']', tag_str)
    return tags


def has_stub_tag(tags: List[str]) -> bool:
    """Check if any tag indicates a stub router."""
    return any("stub" in tag.lower() for tag in tags)


def analyze_function_body(func_node: ast.FunctionDef, source_lines: List[str]) -> List[str]:
    """Analyze function body for stub indicators."""
    indicators = []

    # Get function source
    start_line = func_node.lineno - 1
    end_line = func_node.end_lineno if hasattr(func_node, 'end_lineno') else start_line + 20
    func_source = "\n".join(source_lines[start_line:end_line])

    # Check response patterns
    for pattern, description in STUB_RESPONSE_PATTERNS:
        if re.search(pattern, func_source):
            indicators.append(description)

    # Check code patterns
    for pattern, description in STUB_CODE_PATTERNS:
        if re.search(pattern, func_source, re.MULTILINE):
            indicators.append(description)

    # Check docstring for stub mentions
    docstring = ast.get_docstring(func_node)
    if docstring and re.search(r'\b[Ss]tub\b', docstring):
        indicators.append("docstring mentions stub")

    return indicators


def calculate_confidence(indicators: List[str], is_stub_file: bool, has_stub_router_tag: bool) -> str:
    """Calculate confidence level based on indicators."""
    score = 0

    # File-level indicators (strong)
    if is_stub_file:
        score += 3
    if has_stub_router_tag:
        score += 2

    # Response-level indicators
    for ind in indicators:
        if "Stub:" in ind or "not_implemented" in ind:
            score += 3
        elif "empty" in ind or "null" in ind:
            score += 2
        elif "TODO" in ind or "comment" in ind:
            score += 1

    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"


def extract_routes_from_file(file_path: Path, app_root: Path) -> List[StubEndpoint]:
    """Extract route endpoints and detect stubs."""
    stubs = []

    try:
        content = file_path.read_text(encoding="utf-8")
        source_lines = content.split("\n")
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return stubs

    # File-level stub detection
    is_stub_file = is_stub_filename(file_path)

    # Router-level stub detection
    router_tags = extract_router_tags(content)
    has_stub_router_tag = has_stub_tag(router_tags)

    # Extract router prefix
    prefix = ""
    prefix_match = re.search(r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content)
    if prefix_match:
        prefix = prefix_match.group(1)

    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Warning: Syntax error in {file_path}: {e}", file=sys.stderr)
        return stubs

    # Find all decorated functions
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            route_info = parse_route_decorator(decorator)
            if route_info:
                method, path = route_info
                full_path = normalize_path(prefix + path)

                # Analyze function body for stub indicators
                body_indicators = analyze_function_body(node, source_lines)

                # Combine all indicators
                indicators = []
                if is_stub_file:
                    indicators.append("stub filename")
                if has_stub_router_tag:
                    indicators.append("stub router tag")
                indicators.extend(body_indicators)

                # Only report if we found indicators
                if indicators:
                    confidence = calculate_confidence(indicators, is_stub_file, has_stub_router_tag)

                    rel_path = str(file_path.relative_to(app_root.parent)) if app_root.parent in file_path.parents else str(file_path)

                    stubs.append(StubEndpoint(
                        file=rel_path,
                        line=decorator.lineno,
                        method=method,
                        path=full_path,
                        function_name=node.name,
                        indicators=indicators,
                        confidence=confidence,
                    ))

    return stubs


def parse_route_decorator(decorator: ast.expr) -> Optional[tuple]:
    """Parse a route decorator and extract method and path."""
    if isinstance(decorator, ast.Call):
        if isinstance(decorator.func, ast.Attribute):
            attr = decorator.func
            if isinstance(attr.value, ast.Name) and attr.value.id == "router":
                method = attr.attr.upper()
                if method in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
                    # Get the path argument
                    path = ""
                    if decorator.args:
                        arg = decorator.args[0]
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            path = arg.value
                    return (method, path)
    return None


def normalize_path(path: str) -> str:
    """Normalize a path for display."""
    path = path.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    while "//" in path:
        path = path.replace("//", "/")
    return path


def find_router_files(app_root: Path) -> List[Path]:
    """Find all Python files that might contain routers."""
    router_files = []

    for py_file in app_root.rglob("*.py"):
        # Skip test files, __pycache__, etc.
        if "__pycache__" in str(py_file):
            continue
        if py_file.name.startswith("test_"):
            continue

        # Check if file might contain routers
        try:
            content = py_file.read_text(encoding="utf-8")
            if "APIRouter" in content or "@router." in content:
                router_files.append(py_file)
        except Exception:
            continue

    return router_files


def scan_for_stubs(app_root: Path, min_confidence: str = "low") -> ScanResult:
    """Scan an app directory for stub endpoints."""
    result = ScanResult()

    confidence_levels = ["low", "medium", "high"]
    min_level_idx = confidence_levels.index(min_confidence)

    router_files = find_router_files(app_root)
    result.files_scanned = len(router_files)

    for file_path in router_files:
        stubs = extract_routes_from_file(file_path, app_root)

        for stub in stubs:
            result.total_endpoints += 1

            # Filter by confidence
            stub_level_idx = confidence_levels.index(stub.confidence)
            if stub_level_idx >= min_level_idx:
                result.stubs.append(stub)
                result.stub_endpoints += 1
                result.by_confidence[stub.confidence] += 1

                # Track by file
                if stub.file not in result.by_file:
                    result.by_file[stub.file] = 0
                result.by_file[stub.file] += 1

    return result


def print_report(result: ScanResult, verbose: bool = False):
    """Print human-readable report."""
    print("=" * 60)
    print("Stub Endpoint Scanner Report")
    print("=" * 60)
    print()
    print(f"Files scanned: {result.files_scanned}")
    print(f"Stub endpoints found: {result.stub_endpoints}")
    print()

    if result.stub_endpoints == 0:
        print("[PASS] No stub endpoints detected")
        return

    print("By confidence:")
    print(f"  High:   {result.by_confidence['high']}")
    print(f"  Medium: {result.by_confidence['medium']}")
    print(f"  Low:    {result.by_confidence['low']}")
    print()

    # Group by file
    stubs_by_file: Dict[str, List[StubEndpoint]] = defaultdict(list)
    for stub in result.stubs:
        stubs_by_file[stub.file].append(stub)

    print("Stub Endpoints:")
    print("-" * 60)

    for file_path, stubs in sorted(stubs_by_file.items()):
        print(f"\n{file_path} ({len(stubs)} stubs)")
        for stub in sorted(stubs, key=lambda s: s.line):
            conf_marker = {"high": "[H]", "medium": "[M]", "low": "[L]"}[stub.confidence]
            print(f"  {conf_marker} {stub.method:6} {stub.path}")
            print(f"       Line {stub.line}: {stub.function_name}()")
            if verbose:
                for ind in stub.indicators:
                    print(f"         - {ind}")

    print()
    print("=" * 60)
    print("Legend: [H]=High confidence, [M]=Medium, [L]=Low")
    print("=" * 60)


def print_json(result: ScanResult):
    """Print JSON output."""
    output = {
        "summary": {
            "files_scanned": result.files_scanned,
            "stub_endpoints": result.stub_endpoints,
            "by_confidence": result.by_confidence,
        },
        "stubs": [asdict(s) for s in result.stubs],
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Scan FastAPI app for stub endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --app-root ./services/api/app
  %(prog)s --app-root ./app --json
  %(prog)s --app-root ./app --min-confidence high
  %(prog)s --app-root ./app --verbose
        """,
    )
    parser.add_argument(
        "--app-root",
        type=Path,
        required=True,
        help="Root directory of the FastAPI app to scan",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed indicators for each stub",
    )
    parser.add_argument(
        "--min-confidence",
        choices=["low", "medium", "high"],
        default="low",
        help="Minimum confidence level to report (default: low)",
    )

    args = parser.parse_args()

    if not args.app_root.exists():
        print(f"Error: App root does not exist: {args.app_root}", file=sys.stderr)
        sys.exit(1)

    if not args.app_root.is_dir():
        print(f"Error: App root is not a directory: {args.app_root}", file=sys.stderr)
        sys.exit(1)

    result = scan_for_stubs(args.app_root, min_confidence=args.min_confidence)

    if args.json:
        print_json(result)
    else:
        print_report(result, verbose=args.verbose)

    # Exit with code 0 if no stubs, 1 if stubs found
    sys.exit(0 if result.stub_endpoints == 0 else 1)


if __name__ == "__main__":
    main()
