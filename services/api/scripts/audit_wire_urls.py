#!/usr/bin/env python3
"""
CI-RED-015-D: Wire URL collision audit.

The existing audit_endpoints.py measures decorator paths only, not wire URLs.
A decorator `@router.get("/status")` in a file mounted at `/api/cam/assist`
has wire URL `/api/cam/assist/status`, not `/status`.

This script:
1. Loads manifest entries to get manifest-level prefixes
2. Parses router files to find APIRouter(prefix=...) definitions
3. Extracts decorator paths
4. Computes full wire URLs: manifest_prefix + router_prefix + decorator_path
5. Reports actual wire-URL collisions (which would be real routing bugs)

Output: metrics/wire_url_audit.json
"""
import ast
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
API_ROOT = SCRIPT_DIR.parent
APP_ROOT = API_ROOT / "app"
METRICS_DIR = API_ROOT / "metrics"

# Regexes for decorator extraction
DECORATOR_PATTERN = re.compile(
    r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']*)["\']',
    re.IGNORECASE
)
APIROUTER_PREFIX = re.compile(
    r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']*)["\']',
    re.DOTALL
)


@dataclass
class ManifestEntry:
    module: str
    prefix: str
    router_attr: str = "router"
    category: str = "misc"


@dataclass
class EndpointInfo:
    file: str
    method: str
    decorator_path: str
    router_prefix: str
    manifest_prefix: str
    wire_url: str
    manifest_module: Optional[str] = None


def load_manifest_entries() -> list[ManifestEntry]:
    """Load all RouterSpec entries from manifests."""
    entries = []
    manifest_dir = APP_ROOT / "router_registry" / "manifests"

    for manifest_file in manifest_dir.glob("*_manifest.py"):
        try:
            content = manifest_file.read_text(encoding="utf-8")
            # Extract RouterSpec(...) blocks
            # Simple regex approach since AST parsing of dataclass calls is complex
            spec_pattern = re.compile(
                r'RouterSpec\s*\(\s*'
                r'module\s*=\s*["\']([^"\']+)["\']'
                r'[^)]*?'
                r'(?:prefix\s*=\s*["\']([^"\']*)["\'])?'
                r'[^)]*?'
                r'(?:router_attr\s*=\s*["\']([^"\']*)["\'])?'
                r'[^)]*?'
                r'(?:category\s*=\s*["\']([^"\']*)["\'])?',
                re.DOTALL
            )
            for match in spec_pattern.finditer(content):
                module = match.group(1)
                prefix = match.group(2) or ""
                router_attr = match.group(3) or "router"
                category = match.group(4) or "misc"
                entries.append(ManifestEntry(
                    module=module,
                    prefix=prefix,
                    router_attr=router_attr,
                    category=category,
                ))
        except Exception as e:
            print(f"Warning: Could not parse {manifest_file}: {e}", file=sys.stderr)

    return entries


def module_to_filepath(module: str) -> Optional[Path]:
    """Convert module path to file path."""
    # app.routers.foo -> app/routers/foo.py or app/routers/foo/__init__.py
    parts = module.replace("app.", "").split(".")

    # Try direct file first
    path = APP_ROOT / "/".join(parts[:-1]) / f"{parts[-1]}.py" if len(parts) > 1 else APP_ROOT / f"{parts[0]}.py"
    if path.exists():
        return path

    # Try __init__.py
    path = APP_ROOT / "/".join(parts) / "__init__.py"
    if path.exists():
        return path

    # Try without last component as __init__
    if len(parts) >= 2:
        path = APP_ROOT / "/".join(parts[:-1]) / f"{parts[-1]}.py"
        if path.exists():
            return path

    # Try full path as directory with __init__
    full_path = APP_ROOT / "/".join(parts)
    if full_path.is_dir():
        init_path = full_path / "__init__.py"
        if init_path.exists():
            return init_path

    return None


def extract_router_prefix(content: str) -> str:
    """Extract APIRouter prefix from file content."""
    match = APIROUTER_PREFIX.search(content)
    return match.group(1) if match else ""


def extract_endpoints(filepath: Path, manifest_prefix: str, manifest_module: str) -> list[EndpointInfo]:
    """Extract all endpoints from a router file."""
    endpoints = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return endpoints

    router_prefix = extract_router_prefix(content)
    rel_path = str(filepath.relative_to(APP_ROOT))

    for match in DECORATOR_PATTERN.finditer(content):
        method = match.group(1).upper()
        decorator_path = match.group(2)

        # Compute wire URL
        parts = [manifest_prefix, router_prefix, decorator_path]
        # Normalize: remove empty parts, ensure single slashes
        wire_url = "/".join(p.strip("/") for p in parts if p.strip("/"))
        if not wire_url.startswith("/"):
            wire_url = "/" + wire_url

        endpoints.append(EndpointInfo(
            file=rel_path,
            method=method,
            decorator_path=decorator_path,
            router_prefix=router_prefix,
            manifest_prefix=manifest_prefix,
            wire_url=wire_url,
            manifest_module=manifest_module,
        ))

    return endpoints


def find_unmanifested_routers() -> list[tuple[Path, str]]:
    """Find router files not in manifest (search by @router decorator)."""
    unmanifested = []
    for pyfile in APP_ROOT.rglob("*.py"):
        try:
            content = pyfile.read_text(encoding="utf-8")
        except Exception:
            continue

        if DECORATOR_PATTERN.search(content):
            rel = str(pyfile.relative_to(APP_ROOT))
            unmanifested.append((pyfile, rel))

    return unmanifested


def audit():
    """Run the wire URL collision audit."""
    print("=" * 70)
    print("CI-RED-015-D: Wire URL Collision Audit")
    print("=" * 70)

    # Load manifest
    manifest_entries = load_manifest_entries()
    print(f"\nLoaded {len(manifest_entries)} manifest entries")

    # Build module -> manifest map
    module_to_manifest: dict[str, ManifestEntry] = {}
    for entry in manifest_entries:
        module_to_manifest[entry.module] = entry

    # Extract endpoints from manifested routers
    all_endpoints: list[EndpointInfo] = []
    manifested_files: set[str] = set()

    for entry in manifest_entries:
        filepath = module_to_filepath(entry.module)
        if filepath:
            manifested_files.add(str(filepath.relative_to(APP_ROOT)))
            endpoints = extract_endpoints(filepath, entry.prefix, entry.module)
            all_endpoints.extend(endpoints)

    # Find unmanifested routers
    all_router_files = find_unmanifested_routers()
    unmanifested_count = 0
    unmanifested_endpoints = 0

    for filepath, rel in all_router_files:
        if rel not in manifested_files:
            # Unmanifested router - use empty manifest prefix
            endpoints = extract_endpoints(filepath, "", f"UNMANIFESTED:{rel}")
            all_endpoints.extend(endpoints)
            unmanifested_count += 1
            unmanifested_endpoints += len(endpoints)

    print(f"Manifested router files: {len(manifested_files)}")
    print(f"Unmanifested router files: {unmanifested_count} ({unmanifested_endpoints} endpoints)")
    print(f"Total endpoints: {len(all_endpoints)}")

    # Find wire URL collisions
    wire_url_map: dict[str, list[EndpointInfo]] = defaultdict(list)
    for ep in all_endpoints:
        key = f"{ep.method} {ep.wire_url}"
        wire_url_map[key].append(ep)

    collisions = {k: v for k, v in wire_url_map.items() if len(v) > 1}

    # Find decorator-path "duplicates" that are NOT wire collisions
    decorator_map: dict[str, list[EndpointInfo]] = defaultdict(list)
    for ep in all_endpoints:
        key = f"{ep.method} {ep.decorator_path}"
        decorator_map[key].append(ep)

    decorator_dups = {k: v for k, v in decorator_map.items() if len(v) > 1}

    # Categorize decorator dups: real collision vs false positive
    false_positive_dups = {}
    for key, eps in decorator_dups.items():
        wire_urls = set(ep.wire_url for ep in eps)
        if len(wire_urls) > 1:
            # Different wire URLs = false positive (not a real collision)
            false_positive_dups[key] = eps

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Decorator-path 'duplicates': {len(decorator_dups)}")
    print(f"  - False positives (different wire URLs): {len(false_positive_dups)}")
    print(f"  - Actual wire URL collisions: {len(collisions)}")

    # Report wire URL collisions
    if collisions:
        print("\n" + "-" * 70)
        print("WIRE URL COLLISIONS (potential routing bugs)")
        print("-" * 70)
        for key, eps in sorted(collisions.items(), key=lambda x: -len(x[1])):
            print(f"\n{key}  (x{len(eps)} files)")
            for ep in eps:
                print(f"  - {ep.file}")
                print(f"    manifest: {ep.manifest_module}")
                print(f"    manifest_prefix={ep.manifest_prefix!r} router_prefix={ep.router_prefix!r}")
    else:
        print("\n*** NO WIRE URL COLLISIONS FOUND ***")

    # Report false positives (decorator dups that aren't real collisions)
    print("\n" + "-" * 70)
    print(f"FALSE POSITIVE DECORATOR DUPLICATES ({len(false_positive_dups)} cases)")
    print("These have same decorator path but different wire URLs - NOT collisions")
    print("-" * 70)

    for key, eps in sorted(false_positive_dups.items(), key=lambda x: -len(x[1]))[:15]:
        print(f"\n{key}  (x{len(eps)} files, {len(set(ep.wire_url for ep in eps))} unique wire URLs)")
        for ep in eps[:5]:
            print(f"  - {ep.file}")
            print(f"    wire: {ep.wire_url}")
        if len(eps) > 5:
            print(f"    ... +{len(eps) - 5} more")

    if len(false_positive_dups) > 15:
        print(f"\n... +{len(false_positive_dups) - 15} more false positive cases")

    # Unmanifested routers detail
    print("\n" + "-" * 70)
    print(f"UNMANIFESTED ROUTERS ({unmanifested_count} files)")
    print("Routers with @router decorators but no manifest entry")
    print("-" * 70)

    unmanifested_list = [ep for ep in all_endpoints if ep.manifest_module and ep.manifest_module.startswith("UNMANIFESTED:")]
    by_file = defaultdict(list)
    for ep in unmanifested_list:
        by_file[ep.file].append(ep)

    for f, eps in sorted(by_file.items(), key=lambda x: -len(x[1]))[:20]:
        print(f"  {len(eps):3d}  {f}")
    if len(by_file) > 20:
        print(f"  ... +{len(by_file) - 20} more files")

    # Write full audit output
    METRICS_DIR.mkdir(exist_ok=True)
    out_path = METRICS_DIR / "wire_url_audit.json"

    payload = {
        "summary": {
            "total_endpoints": len(all_endpoints),
            "manifested_files": len(manifested_files),
            "unmanifested_files": unmanifested_count,
            "unmanifested_endpoints": unmanifested_endpoints,
            "decorator_duplicates": len(decorator_dups),
            "false_positive_duplicates": len(false_positive_dups),
            "wire_url_collisions": len(collisions),
        },
        "wire_url_collisions": {
            k: [asdict(ep) for ep in v]
            for k, v in sorted(collisions.items(), key=lambda x: -len(x[1]))
        },
        "false_positive_duplicates": {
            k: [asdict(ep) for ep in v]
            for k, v in sorted(false_positive_dups.items(), key=lambda x: -len(x[1]))
        },
        "unmanifested_routers": {
            f: [asdict(ep) for ep in eps]
            for f, eps in sorted(by_file.items(), key=lambda x: -len(x[1]))
        },
        "all_endpoints": [asdict(ep) for ep in sorted(all_endpoints, key=lambda x: x.wire_url)],
    }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")

    return len(collisions)


if __name__ == "__main__":
    collision_count = audit()
    sys.exit(0 if collision_count == 0 else 1)
