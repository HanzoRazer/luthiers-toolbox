#!/usr/bin/env python3
"""Build the CI-RED-016 endpoint consumer map.

The map is an audit artifact, not a deletion list. It records mounted endpoint
surface, first-party string-reference evidence, and broad lane classification so
endpoint consolidation can be planned deliberately.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

SCHEMA = "ci_red_016_endpoint_consumer_map_v1"
VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
DEFAULT_JSON_OUT = Path("metrics/endpoint_consumer_map.json")
DEFAULT_MARKDOWN_OUT = Path("../../docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md")
STATIC_AUDIT_PATH = Path("metrics/endpoint_audit_current.json")

# Mounted API roots recognized as endpoint references. `/exports` is the legacy
# DXF compatibility surface (app.routers.legacy_dxf_exports_router); it is mounted
# without an `/api` prefix, so it must be listed explicitly or its consumers stay
# invisible to the scan (CI-RED-016-C).
ENDPOINT_ROOTS = ("api", "health", "ws", "instrument", "exports")
_ENDPOINT_ROOTS_ALT = "|".join(ENDPOINT_ROOTS)

# Root-relative literal: the path immediately follows the opening quote, e.g.
#   "/api/cam/jobs/123"   `/api/rmos/runs/${runId}`   '/health'   "/exports/polyline_dxf"
ENDPOINT_LITERAL_RE = re.compile(
    rf"""(?P<quote>["'`])(?P<path>/(?:{_ENDPOINT_ROOTS_ALT})[^"'`\s)]*)(?P=quote)"""
)

# Template-base suffix: a static path that follows an interpolated base inside a
# template literal, e.g. `${API_BASE}/exports/polyline_dxf`. Only the static suffix
# is captured; matching stops before any further interpolation (`$`) or the closing
# quote, so a variable base URL still counts as first-party consumer evidence.
#
# CI-RED-016-C deliberately scopes this to the legacy `/exports` surface only. The
# same template-base blind spot exists for `/api` routes, but recognizing those here
# would reclassify ~13 unrelated `/api` endpoints (real, but off-topic) and widen this
# calibration PR beyond the legacy export cluster. Generalizing to all ENDPOINT_ROOTS
# is a tracked follow-up (CI-RED-016 consumer-map improvement), not this slice.
ENDPOINT_TEMPLATE_SUFFIX_RE = re.compile(
    r"""\}(?P<path>/exports[^"'`\s)$]*)"""
)

CONSUMER_ROOTS = (
    Path("../../packages/client/src"),
    Path("tests"),
    Path("scripts"),
    Path("app/ci"),
    Path("../../docs"),
    Path("../../.github/workflows"),
)

# These files document or test the consumer-map scanner itself. New `/exports`
# examples in these files should not become consumer evidence for the legacy
# export cluster; their unmatched examples are also omitted from the unmatched
# literal list to keep the generated artifact observational rather than
# self-referential.
SELF_OBSERVATION_PATHS = frozenset(
    {
        "services/api/scripts/build_endpoint_consumer_map.py",
        "services/api/tests/test_endpoint_consumer_map_builder.py",
        "docs/audit/CI_RED_016_ENDPOINT_CONSUMER_MAP.md",
        "docs/audit/CI_RED_016C_LEGACY_EXPORT_CLUSTER_DISPOSITION.md",
    }
)

TEXT_EXTENSIONS = {
    ".css",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".ts",
    ".tsx",
    ".txt",
    ".yml",
    ".yaml",
}

PROTECTED_CONTEXT_KEYWORDS = (
    "authority",
    "governance",
    "provenance",
    "review",
    "audit",
    "ledger",
    "quarantine",
    "readiness",
    "lifecycle",
    "translation",
)


@dataclass(frozen=True)
class EndpointRecord:
    method: str
    path: str
    operation_id: str
    route_names: tuple[str, ...]
    router_modules: tuple[str, ...]
    router_files: tuple[str, ...]
    tags: tuple[str, ...]
    lane: str
    duplicate_route_count: int = 1

    @property
    def key(self) -> str:
        return f"{self.method} {self.path}"


@dataclass(frozen=True)
class ConsumerEvidence:
    file: str
    consumer_class: str
    evidence: str
    literal: str


@dataclass
class EndpointWithConsumers:
    endpoint: EndpointRecord
    consumers: list[ConsumerEvidence] = field(default_factory=list)

    @property
    def primary_consumer_class(self) -> str:
        if not self.consumers:
            return "no_first_party_consumer_found"
        priority = {
            "frontend_product": 0,
            "frontend_sdk": 1,
            "backend_internal": 2,
            "ci_governance": 3,
            "test_only": 4,
            "docs_only": 5,
            "external_or_unknown": 6,
        }
        return min(
            (consumer.consumer_class for consumer in self.consumers),
            key=lambda value: priority.get(value, 99),
        )

    @property
    def notes(self) -> list[str]:
        if self.primary_consumer_class != "no_first_party_consumer_found":
            return []
        haystack = " ".join(
            [self.endpoint.path, self.endpoint.lane, *self.endpoint.router_modules, *self.endpoint.tags]
        ).lower()
        if any(keyword in haystack for keyword in PROTECTED_CONTEXT_KEYWORDS):
            return [
                "No first-party string consumer was found, but this is a governance/audit/authority lane; absence of a frontend caller is not deletion evidence."
            ]
        return [
            "No first-party string consumer was found by this heuristic scan; this is a review target, not a deletion verdict."
        ]


def repo_root() -> Path:
    return REPO_ROOT


def api_root() -> Path:
    return API_ROOT


def clean_join(prefix: str, path: str) -> str:
    if not prefix:
        out = path
    elif not path:
        out = prefix
    else:
        out = f"{prefix.rstrip('/')}/{path.lstrip('/')}"
    return out or "/"


def route_module_to_file(module: str) -> str:
    if not module:
        return ""
    rel = Path(*module.split(".")).with_suffix(".py")
    candidate = api_root() / rel
    try:
        return candidate.relative_to(repo_root()).as_posix()
    except ValueError:
        return candidate.as_posix()


def route_methods(route: Any) -> list[str]:
    methods = getattr(route, "methods", None) or {"GET"}
    return sorted(method for method in methods if method in VALID_METHODS)


def merged_tags(route: Any, include_tags: Iterable[str]) -> tuple[str, ...]:
    tags: list[str] = []
    for tag in include_tags:
        if tag not in tags:
            tags.append(str(tag))
    for tag in getattr(route, "tags", None) or []:
        if tag not in tags:
            tags.append(str(tag))
    return tuple(tags)


def iter_http_routes_from_app(app: Any) -> Iterable[dict[str, Any]]:
    for app_route in getattr(app, "routes", []):
        if type(app_route).__name__ == "_IncludedRouter":
            context = getattr(app_route, "include_context", None)
            prefix = getattr(context, "prefix", "") if context else ""
            tags = tuple(getattr(context, "tags", None) or ())
            yield from iter_http_routes_from_router(
                getattr(app_route, "original_router", None), prefix=prefix, tags=tags
            )
        else:
            yield from route_to_entries(app_route, prefix="", tags=())


def iter_http_routes_from_router(router: Any, *, prefix: str, tags: tuple[str, ...]) -> Iterable[dict[str, Any]]:
    for route in getattr(router, "routes", []) or []:
        if type(route).__name__ == "_IncludedRouter":
            context = getattr(route, "include_context", None)
            next_prefix = clean_join(prefix, getattr(context, "prefix", "") if context else "")
            next_tags = tags + tuple(getattr(context, "tags", None) or ())
            yield from iter_http_routes_from_router(
                getattr(route, "original_router", None), prefix=next_prefix, tags=next_tags
            )
        else:
            yield from route_to_entries(route, prefix=prefix, tags=tags)


def route_to_entries(route: Any, *, prefix: str, tags: tuple[str, ...]) -> Iterable[dict[str, Any]]:
    methods = route_methods(route)
    if not methods or not hasattr(route, "path"):
        return
    endpoint = getattr(route, "endpoint", None)
    module = getattr(endpoint, "__module__", "") if endpoint else ""
    name = getattr(route, "name", "") or getattr(endpoint, "__name__", "") if endpoint else ""
    full_path = clean_join(prefix, getattr(route, "path", ""))
    route_tags = merged_tags(route, tags)
    for method in methods:
        yield {
            "method": method,
            "path": full_path,
            "route_name": name,
            "router_module": module,
            "router_file": route_module_to_file(module),
            "tags": route_tags,
        }


def operation_lookup_from_openapi(spec: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for path, operations in (spec.get("paths") or {}).items():
        if not isinstance(operations, dict):
            continue
        for method, operation in operations.items():
            upper = method.upper()
            if upper in VALID_METHODS and isinstance(operation, dict):
                lookup[(upper, path)] = operation
    return lookup


def classify_lane(path: str, router_modules: Iterable[str], tags: Iterable[str]) -> str:
    text = " ".join([path, *router_modules, *tags]).lower().replace("_", "-")
    if path in {"/health", "/api/health"} or path.startswith("/api/_meta"):
        return "health_meta"
    if "/api/ai" in path or "app.vision" in text or "analyzer" in text:
        return "ai_advisory"
    if "blueprint" in text or "/api/blueprint" in path:
        return "blueprint_vectorizer"
    if "woodworking" in text or "archtop" in text or "binding" in text or "neck" in text or "headstock" in text:
        return "woodworking_instrument_design"
    if "tooling" in text or "machine" in text or "posts" in text or "probe" in text or "cnc-production" in text:
        return "machine_posts_tooling"
    if "analytics" in text or "registry" in text or "learned-overrides" in text:
        return "analytics_registry"
    if "/api/jobs" in path or "job-queue" in text:
        return "jobs_runtime"
    if "materials" in text:
        return "materials_inventory"
    if "calculator" in text or "music" in text or "temperament" in text or "string-master" in text:
        return "music_calculator"
    if "acoustics" in text or "radius-dish" in text:
        return "acoustics"
    if "/api/compare" in path or "compare" in text:
        return "compare_lab"
    if "/api/saw" in path or "saw-lab" in text:
        return "saw_lab"
    if "geometry-authority" in text or "authority-reference" in text:
        return "authority_reference"
    if any(word in text for word in ("governance", "provenance", "review", "lifecycle", "translator")):
        return "cam_governance"
    if "/api/rmos" in path or "app.rmos" in text:
        return "rmos_runtime"
    if "art-studio" in text or "art-studio" in path or "rosette" in text:
        return "art_studio"
    if "/api/cam" in path or "app.cam" in text or ".cam." in text:
        return "cam_operation"
    if "/instrument" in path or "instrument-geometry" in text or ".instruments." in text:
        return "instrument_geometry"
    if "/api/v1" in path or "/api/projects" in path or "/api/business" in path:
        return "mvp_runtime"
    if any(word in text for word in ("legacy", "migration", "deprecated")):
        return "legacy_migration"
    if any(word in text for word in ("debug", "test", "mock", "dev")):
        return "test_debug_dev"
    return "unknown"


def collect_endpoint_records(app: Any) -> tuple[list[EndpointRecord], dict[str, int]]:
    spec = app.openapi()
    operations = operation_lookup_from_openapi(spec)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for entry in iter_http_routes_from_app(app):
        grouped[(entry["method"], entry["path"])].append(entry)

    records: list[EndpointRecord] = []
    for key in sorted(operations):
        operation = operations[key]
        entries = grouped.get(key, [])
        route_names = tuple(sorted({entry["route_name"] for entry in entries if entry["route_name"]}))
        modules = tuple(sorted({entry["router_module"] for entry in entries if entry["router_module"]}))
        files = tuple(sorted({entry["router_file"] for entry in entries if entry["router_file"]}))
        tags = tuple(sorted({str(tag) for entry in entries for tag in entry["tags"]} | set(operation.get("tags") or [])))
        records.append(
            EndpointRecord(
                method=key[0],
                path=key[1],
                operation_id=str(operation.get("operationId") or ""),
                route_names=route_names,
                router_modules=modules,
                router_files=files,
                tags=tags,
                lane=classify_lane(key[1], modules, tags),
                duplicate_route_count=max(1, len(entries)),
            )
        )

    stats = {
        "openapi_path_count": len(spec.get("paths") or {}),
        "openapi_operation_count": len(operations),
        "route_object_entry_count": sum(len(value) for value in grouped.values()),
        "route_object_unique_endpoint_count": len(grouped),
        "route_object_missing_from_openapi": len(set(grouped) - set(operations)),
        "openapi_missing_from_route_objects": len(set(operations) - set(grouped)),
    }
    return records, stats


def extract_endpoint_literals(text: str) -> list[str]:
    literals = {match.group("path").rstrip(",.;") for match in ENDPOINT_LITERAL_RE.finditer(text)}
    literals |= {match.group("path").rstrip(",.;") for match in ENDPOINT_TEMPLATE_SUFFIX_RE.finditer(text)}
    return sorted(literals)


def classify_consumer_file(path: Path) -> str:
    rel = path.relative_to(repo_root()).as_posix()
    if "/__tests__/" in rel or rel.startswith("services/api/tests/") or rel.endswith("_test.py"):
        return "test_only"
    if rel.startswith("packages/client/src/sdk/endpoints/"):
        return "frontend_sdk"
    if rel.startswith("packages/client/src/"):
        return "frontend_product"
    if rel.startswith("services/api/app/ci/") or rel.startswith("services/api/scripts/") or rel.startswith(".github/"):
        return "ci_governance"
    if rel.startswith("docs/"):
        return "docs_only"
    if rel.startswith("services/api/app/"):
        return "backend_internal"
    return "external_or_unknown"


def is_self_observation_noise(rel_path: str, literal: str) -> bool:
    return rel_path in SELF_OBSERVATION_PATHS and literal.startswith("/exports")


def endpoint_static_prefix(path: str) -> str:
    if "{" not in path:
        return path
    prefix = path.split("{", 1)[0].rstrip("/")
    return prefix if len(prefix) >= 6 else ""


def reference_path(literal: str) -> str:
    return literal.split("?", 1)[0].split("#", 1)[0]


def reference_matches_endpoint(literal: str, endpoint_path: str) -> bool:
    path = reference_path(literal)
    if path == endpoint_path:
        return True
    prefix = endpoint_static_prefix(endpoint_path)
    if not prefix or (path != prefix and not path.startswith(prefix + "/")):
        return False
    if "{" not in endpoint_path and endpoint_path.startswith("/exports/"):
        return False
    return True


def iter_consumer_files() -> Iterable[Path]:
    root = repo_root()
    for rel_root in CONSUMER_ROOTS:
        absolute = (api_root() / rel_root).resolve() if not rel_root.parts[0].startswith("..") else (api_root() / rel_root).resolve()
        if not absolute.exists():
            continue
        for path in absolute.rglob("*"):
            if path.is_file() and path.suffix in TEXT_EXTENSIONS:
                try:
                    path.relative_to(root)
                except ValueError:
                    continue
                yield path


def scan_consumers(records: list[EndpointRecord]) -> tuple[dict[str, list[ConsumerEvidence]], list[dict[str, str]]]:
    evidence_by_key: dict[str, list[ConsumerEvidence]] = {record.key: [] for record in records}
    endpoints_by_path = defaultdict(list)
    for record in records:
        endpoints_by_path[record.path].append(record)

    unmatched_literals: dict[tuple[str, str], str] = {}
    for file_path in sorted(iter_consumer_files(), key=lambda item: item.as_posix()):
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        literals = extract_endpoint_literals(text)
        if not literals:
            continue
        rel = file_path.relative_to(repo_root()).as_posix()
        consumer_class = classify_consumer_file(file_path)
        for literal in literals:
            if is_self_observation_noise(rel, literal):
                continue
            matched = False
            for record in records:
                if reference_matches_endpoint(literal, record.path):
                    evidence_by_key[record.key].append(
                        ConsumerEvidence(
                            file=rel,
                            consumer_class=consumer_class,
                            evidence="string_literal_or_parameter_prefix",
                            literal=literal,
                        )
                    )
                    matched = True
            if not matched and rel not in SELF_OBSERVATION_PATHS:
                unmatched_literals[(rel, literal)] = consumer_class

    for key, items in evidence_by_key.items():
        unique = {(item.file, item.consumer_class, item.evidence, item.literal): item for item in items}
        evidence_by_key[key] = [unique[k] for k in sorted(unique)]

    unmatched = [
        {"file": file, "literal": literal, "consumer_class": consumer_class}
        for (file, literal), consumer_class in sorted(unmatched_literals.items())
    ]
    return evidence_by_key, unmatched


def load_static_audit() -> dict[str, Any]:
    path = api_root() / STATIC_AUDIT_PATH
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(records: list[EndpointRecord], stats: dict[str, int]) -> dict[str, Any]:
    evidence_by_key, unmatched_literals = scan_consumers(records)
    endpoints = [
        EndpointWithConsumers(endpoint=record, consumers=evidence_by_key.get(record.key, []))
        for record in records
    ]
    static_audit = load_static_audit()
    lane_counts = Counter(item.endpoint.lane for item in endpoints)
    consumer_counts = Counter(item.primary_consumer_class for item in endpoints)
    method_counts = Counter(item.endpoint.method for item in endpoints)

    endpoint_dicts = []
    for item in sorted(endpoints, key=lambda value: value.endpoint.key):
        endpoint_dicts.append(
            {
                "key": item.endpoint.key,
                "method": item.endpoint.method,
                "path": item.endpoint.path,
                "operation_id": item.endpoint.operation_id,
                "route_names": list(item.endpoint.route_names),
                "router_modules": list(item.endpoint.router_modules),
                "router_files": list(item.endpoint.router_files),
                "tags": list(item.endpoint.tags),
                "lane": item.endpoint.lane,
                "duplicate_route_count": item.endpoint.duplicate_route_count,
                "primary_consumer_class": item.primary_consumer_class,
                "consumers": [
                    {
                        "file": consumer.file,
                        "consumer_class": consumer.consumer_class,
                        "evidence": consumer.evidence,
                        "literal": consumer.literal,
                    }
                    for consumer in item.consumers
                ],
                "notes": item.notes,
            }
        )

    payload = {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "base_commit": git_commit(),
        "methodology": {
            "source_of_truth": "FastAPI app.routes _IncludedRouter flattening, cross-checked against app.openapi() operations",
            "consumer_scan_roots": [path.as_posix() for path in CONSUMER_ROOTS],
            "self_observation_paths": sorted(SELF_OBSERVATION_PATHS),
            "endpoint_reference_roots": ["/" + root for root in ENDPOINT_ROOTS],
            "consumer_scan_limitations": [
                "String-literal and parameter-prefix matching over the mounted API roots "
                + ", ".join("/" + root for root in ENDPOINT_ROOTS)
                + ". Root-relative literals (\"/exports/polyline_dxf\") are recognized for all "
                "of these roots; template-base suffixes behind an interpolated base "
                "(`${API_BASE}/exports/polyline_dxf`) are recognized for the legacy /exports "
                "surface only (CI-RED-016-C). Generalizing template-base matching to /api routes "
                "is a tracked follow-up. Runtime analytics and generated clients are not inferred.",
                "Scanner implementation files, scanner unit tests, and generated CI-RED-016 audit reports do not count as /exports consumer evidence, and their unmatched literals are omitted to avoid self-referential audit noise.",
                "No first-party consumer found is not a deletion verdict.",
            ],
        },
        "summary": {
            "mounted_endpoint_count": len(endpoint_dicts),
            "lane_counts": dict(sorted(lane_counts.items())),
            "consumer_class_counts": dict(sorted(consumer_counts.items())),
            "method_counts": dict(sorted(method_counts.items())),
            "unmatched_consumer_literal_count": len(unmatched_literals),
            **stats,
        },
        "static_audit": {
            "total": static_audit.get("total"),
            "baseline": static_audit.get("baseline"),
            "delta": static_audit.get("delta"),
            "mounted_vs_static_gap": (
                static_audit.get("total") - len(endpoint_dicts)
                if isinstance(static_audit.get("total"), int)
                else None
            ),
            "note": "Static audit counts decorators; mounted count is generated from the live FastAPI app surface.",
        },
        "endpoints": endpoint_dicts,
        "unmatched_consumer_literals": unmatched_literals,
    }
    return payload


def git_commit() -> str:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root(),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip()


def markdown_table(rows: Iterable[Iterable[Any]], headers: Iterable[str]) -> str:
    header = list(headers)
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    static = payload["static_audit"]
    endpoints = payload["endpoints"]
    no_consumer = [item for item in endpoints if item["primary_consumer_class"] == "no_first_party_consumer_found"]
    protected_no_consumer = [
        item
        for item in no_consumer
        if any("governance/audit/authority" in note for note in item.get("notes", []))
    ]

    lane_rows = sorted(summary["lane_counts"].items(), key=lambda item: (-item[1], item[0]))
    consumer_rows = sorted(summary["consumer_class_counts"].items(), key=lambda item: (-item[1], item[0]))
    no_consumer_by_lane = Counter(item["lane"] for item in no_consumer)
    top_no_consumer = sorted(no_consumer_by_lane.items(), key=lambda item: (-item[1], item[0]))[:20]

    samples = no_consumer[:30]
    sample_rows = [
        [item["method"], item["path"], item["lane"], ", ".join(item["router_modules"][:2])]
        for item in samples
    ]

    return "\n".join(
        [
            "# CI-RED-016 Endpoint Consumer Map",
            "",
            f"Generated: `{payload['generated_at_utc']}`",
            f"Base commit: `{payload['base_commit']}`",
            "",
            "## Purpose",
            "",
            "This document turns CI-RED-016 from a raw route-count concern into a structured consumer map. It does not delete, rename, consolidate, or re-baseline any endpoint.",
            "",
            "## Summary",
            "",
            markdown_table(
                [
                    ["Mounted endpoint operations", summary["mounted_endpoint_count"]],
                    ["OpenAPI operations", summary["openapi_operation_count"]],
                    ["OpenAPI paths", summary["openapi_path_count"]],
                    ["Route-object unique endpoints", summary["route_object_unique_endpoint_count"]],
                    ["Static decorator count", static.get("total")],
                    ["Static baseline", static.get("baseline")],
                    ["Static delta", static.get("delta")],
                    ["Mounted-vs-static gap", static.get("mounted_vs_static_gap")],
                    ["Unmatched consumer literals", summary["unmatched_consumer_literal_count"]],
                ],
                ["Metric", "Value"],
            ),
            "",
            "## Methodology Notes",
            "",
            "- Source of truth is the live mounted FastAPI surface. The utility flattens FastAPI 0.137 `_IncludedRouter` route objects and cross-checks the result against `app.openapi()` operations.",
            "- Static decorator count is retained as debt context only. It can differ from mounted behavior because it does not resolve router inclusion and generated schema behavior.",
            "- Consumer detection is a first-party string-literal and parameter-prefix scan. It is useful triage evidence, not runtime telemetry.",
            "- Scanner implementation files, scanner unit tests, and generated CI-RED-016 audit reports do not count as `/exports` consumer evidence, and their unmatched literals are omitted so examples do not self-register as callers.",
            "- Endpoint references are matched over the mounted API roots `/api`, `/health`, `/ws`, `/instrument`, and `/exports`. Root-relative literals (`\"/exports/polyline_dxf\"`) count as evidence for all of these roots. Template-base suffixes behind an interpolated base (`` `${API_BASE}/exports/polyline_dxf` ``) are recognized for the legacy `/exports` surface only — that compatibility surface was previously invisible to the scan (CI-RED-016-C). Generalizing template-base matching to `/api` routes is a tracked follow-up.",
            "- `no_first_party_consumer_found` is not a deletion verdict. Governance, audit, authority, provenance, and review endpoints are explicitly protected from being interpreted as dead just because they lack a frontend caller.",
            "",
            "## Endpoint Lanes",
            "",
            markdown_table(lane_rows, ["Lane", "Endpoints"]),
            "",
            "## Consumer Classes",
            "",
            markdown_table(consumer_rows, ["Primary consumer class", "Endpoints"]),
            "",
            "## No First-Party Consumer Found By Lane",
            "",
            markdown_table(top_no_consumer, ["Lane", "Endpoints"]),
            "",
            f"Protected governance/audit/authority endpoints in this bucket: `{len(protected_no_consumer)}`.",
            "",
            "## Sample Review Targets",
            "",
            markdown_table(sample_rows, ["Method", "Path", "Lane", "Router modules"]),
            "",
            "## Machine-Readable Artifact",
            "",
            "The full endpoint-level map is committed at `services/api/metrics/endpoint_consumer_map.json`.",
            "",
            "## Recommended Next Step",
            "",
            "Use this map to pick a narrow CI-RED-016-C consolidation candidate. Prioritize endpoints with `no_first_party_consumer_found` only after a human review confirms they are not governance/audit/authority surfaces, not external contract surfaces, and not intentionally retained compatibility endpoints.",
            "",
        ]
    )


def write_payload(payload: dict[str, Any], json_out: Path, markdown_out: Path) -> None:
    json_path = (api_root() / json_out).resolve()
    markdown_path = (api_root() / markdown_out).resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")


def load_app() -> Any:
    from app.main import app

    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_OUT)
    args = parser.parse_args(argv)

    records, stats = collect_endpoint_records(load_app())
    payload = build_payload(records, stats)
    write_payload(payload, args.json_out, args.markdown_out)
    print(f"Wrote {(api_root() / args.json_out).resolve()}")
    print(f"Wrote {(api_root() / args.markdown_out).resolve()}")
    print(f"Mounted endpoint operations: {payload['summary']['mounted_endpoint_count']}")
    print(f"Static decorator count: {payload['static_audit'].get('total')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
