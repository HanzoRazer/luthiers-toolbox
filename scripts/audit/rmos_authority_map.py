#!/usr/bin/env python3
"""RMOS-AUTHORITY-MAP-001 — one-off manufacturing-output census.

Read-only inventory of mounted machine-artifact routes, grouped by
capability. Report and validate against the inert registry JSON.

This is an ordinary audit script (same shape as the GEN-5 census). It is
not an agent, does not edit the registry, and grants no execution authority.

Usage (from repo root)::

    PYTHONPATH=services/api python scripts/audit/rmos_authority_map.py
    PYTHONPATH=services/api python scripts/audit/rmos_authority_map.py --validate
    PYTHONPATH=services/api python scripts/audit/rmos_authority_map.py --inventory
    PYTHONPATH=services/api python scripts/audit/rmos_authority_map.py --emit-skeleton
    PYTHONPATH=services/api python scripts/audit/rmos_authority_map.py --emit-stage2

``--emit-skeleton`` prints a Stage-1 UNKNOWN registry to stdout.
``--emit-stage2`` prints the Stage-2 overlay applied to that inventory.
Neither flag writes a repository file.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import importlib.util as _importlib_util


def _load_stage2_module():
    sibling = Path(__file__).resolve().parent / "rmos_authority_stage2.py"
    spec = _importlib_util.spec_from_file_location("rmos_authority_stage2", sibling)
    mod = _importlib_util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_STAGE2 = _load_stage2_module()
apply_stage2 = _STAGE2.apply_stage2
infer_surface_kind = _STAGE2.infer_surface_kind
SURFACE_KIND_VOCABULARY = list(_STAGE2.SURFACE_KIND_VOCABULARY)

REPO_MARKERS = (".git", "services/api/app/main.py")
DEFAULT_REGISTRY = "services/api/app/rmos/manufacturing_authority_registry.json"
DEFAULT_SCHEMA = (
    "services/api/app/rmos/schemas/manufacturing_authority_registry.schema.json"
)

SCHEMA_VERSION = "manufacturing_authority_registry_v0.1"
AUDIT_ID = "RMOS-AUTHORITY-MAP-001"

IGNORED_METHODS = {"HEAD", "OPTIONS"}

# Longest-prefix first. Seeded required families from the Dev Order.
SEEDED_PREFIXES: Tuple[Tuple[str, str], ...] = (
    ("/api/cam/pocket/adaptive", "adaptive"),
    ("/api/v1/machines/probe", "probing"),
    ("/api/cam/vcarve/production", "vcarve"),
    ("/api/cam/toolpath/vcarve", "vcarve"),
    ("/api/cam/toolpath/roughing", "roughing"),
    ("/api/cam/toolpath/helical_entry", "helical"),
    ("/api/cam/toolpath/helical", "helical"),
    ("/api/cam/toolpath/biarc", "biarc-contour"),
    ("/api/cam/opt/feeds-speeds", "feeds-speeds"),
    ("/api/cam/polygon_offset_governed", "polygon-offset"),
    ("/api/cam/polygon_offset", "polygon-offset"),
    ("/api/rmos/runs_v2", "operator-pack"),
    ("/api/neck/gcode", "neck-gcode"),
    ("/api/acoustics/radius-dish", "radius-dish"),
    ("/api/art-studio/inlay", "inlay"),
    ("/api/cam/profiling", "profiling"),
    ("/api/cam/drilling", "drilling"),
    ("/api/cam/retract", "retract"),
    ("/api/cam/binding", "binding"),
    ("/api/cam/rosette", "rosette"),
    ("/api/cam/roughing", "roughing"),
    ("/api/cam/vcarve", "vcarve"),
    ("/api/cam/pocketing", "pocketing"),
    ("/api/probe", "probing"),
)

REQUIRED_SEED_IDS: Tuple[str, ...] = (
    "retract",
    "adaptive",
    "drilling",
    "profiling",
    "vcarve",
    "roughing",
    "helical",
    "rosette",
    "probing",
    "binding",
    "inlay",
    "radius-dish",
    "feeds-speeds",
    "biarc-contour",
)

# Path-pattern inclusion for machine-consumable output (census IN rule).
_HINT_TOKENS = (
    "/gcode",
    "gcode/",
    "gcode_",
    ".nc",
    "operator-pack",
    "post_v155",
    "dxf-to-grbl",
    "intent-gcode",
    "gcode_intent",
    "generate-gcode",
    "export-gcode",
    "export_gcode",
    "post-gcode",
    "plan-toolpath",
    "batch_export",
    "export_bundle",
    "helical_entry",
    "feeds-speeds",
    "photo-to-gcode",
    "/v1/dxf/cam/gcode",
    "/v1/machines/probe",
)

# Declared-purpose exclusions (leads from rmos_prod_output_census_001b.md, re-applied).
EXCLUSION_RULES: Tuple[Tuple[str, str], ...] = (
    ("/api/cam/sim/", "consumes G-code or simulates; emits analysis, not a cut"),
    ("/api/cam/gcode/plot", "visualization SVG of existing G-code"),
    ("/api/cam/gcode/estimate", "time/cost estimate; does not emit a machine artifact"),
    ("/api/cam/gcode/simulate", "simulation of existing G-code"),
    ("/api/neck/gcode/styles", "metadata catalog, not emission"),
    ("/api/neck/gcode/profiles", "metadata catalog, not emission"),
    ("/api/neck/gcode/tools", "metadata catalog, not emission"),
    ("/api/blueprint", "vectorization / DXF repair intermediate"),
    ("/api/art-studio/inlay/export-dxf", "design drawing DXF, not machining"),
    ("/api/art-studio/bracing", "design drawing export"),
)

AUTHORITATIVE_DISPOSITIONS = frozenset(
    {
        "GOVERNED",
        "GOVERNED_PROVENANCE_DEFECT",
        "LIVE_UNGOVERNED_OUTPUT",
        "BLOCKED_BY_DESIGN",
        "AUTHORITY_CONTRACT_MISMATCH",
        "POST_MERGE_AUTHORITY_EXPOSURE",
        "RUNTIME_BROKEN",
        "EXPLICITLY_NON_PRODUCTION",
        "ADVISORY_ONLY",
    }
)

DISPOSITION_VOCABULARY = [
    "GOVERNED",
    "GOVERNED_PROVENANCE_DEFECT",
    "LIVE_UNGOVERNED_OUTPUT",
    "BLOCKED_BY_DESIGN",
    "AUTHORITY_CONTRACT_MISMATCH",
    "POST_MERGE_AUTHORITY_EXPOSURE",
    "RUNTIME_BROKEN",
    "EXPLICITLY_NON_PRODUCTION",
    "ADVISORY_ONLY",
    "UNKNOWN",
    "INSUFFICIENT_EVIDENCE",
]

REACHABILITY_VOCABULARY = [
    "SOURCE_PRESENT",
    "MOUNTED",
    "RUNTIME_REACHABLE",
    "RUNTIME_BLOCKED_BY_POLICY",
    "RUNTIME_BROKEN",
    "NO_IN_REPO_CONSUMER",
]

EVIDENCE_CLASS_VOCABULARY = [
    "MOUNTED_ROUTE_TABLE",
    "OPENAPI_PATHS",
    "RUNTIME_REQUEST_WITNESS",
    "STATIC_CODE_TRACE",
    "CLIENT_CALL_SITE",
    "GREP_LEAD",
    "INSUFFICIENT_EVIDENCE",
]

WARNING_TEXT = (
    "PRESENCE IN THIS REGISTRY GRANTS NO EXECUTION AUTHORITY. "
    "This is an audit census of manufacturing-capability reachability. "
    "It does not replace CANONICAL_AUTHORITY_MAP.md, "
    "geometry_authority_registry.py, or ontology_authority_map.py. "
    "Nothing production-facing should import this file."
)

ADJACENT_MAPS = [
    {
        "path": "docs/governance/CANONICAL_AUTHORITY_MAP.md",
        "concern": "semantic ownership — not manufacturing reachability",
    },
    {
        "path": "services/api/app/cam/geometry_authority_registry.py",
        "concern": "7T geometry references; no execution/machine-output authority",
    },
    {
        "path": "services/api/app/cam/ontology_authority_map.py",
        "concern": "7M vocabulary; execution_authorized is always false",
    },
]


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #


def find_repo_root(start: Optional[Path] = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if all((candidate / marker).exists() for marker in REPO_MARKERS):
            return candidate
        # services/api is a marker parent
        if (candidate / "services/api/app/main.py").exists() and (candidate / ".git").exists():
            return candidate
    raise SystemExit("could not locate repository root (missing services/api/app/main.py)")


def _ensure_api_on_path(repo_root: Path) -> None:
    api = str(repo_root / "services/api")
    if api not in sys.path:
        sys.path.insert(0, api)


# --------------------------------------------------------------------------- #
# Mounted-route walk (FastAPI 0.137 _IncludedRouter)
# --------------------------------------------------------------------------- #


def join_paths(prefix: str, path: str) -> str:
    prefix = prefix or ""
    path = path or ""
    if not prefix:
        return path or "/"
    if not path or path == "/":
        return prefix
    return prefix.rstrip("/") + "/" + path.lstrip("/")


def iter_mounted_routes(app: Any, routes: Optional[Sequence[Any]] = None, prefix: str = "") -> Iterable[Dict[str, Any]]:
    """Yield mounted HTTP routes, recursing FastAPI ``_IncludedRouter`` wrappers.

    A naive ``app.routes`` walk sees ~155 top-level entries and under-counts
    because included routers are stored as ``_IncludedRouter``, not flattened
    ``APIRoute`` objects. OpenAPI paths (~1077) are the completeness cross-check.
    """
    if routes is None:
        routes = list(app.routes)
    for route in routes:
        name = type(route).__name__
        if name == "_IncludedRouter":
            ctx = route.include_context
            new_prefix = join_paths(prefix, getattr(ctx, "prefix", "") or "")
            orig = route.original_router
            yield from iter_mounted_routes(app, orig.routes, new_prefix)
            continue
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        nested = getattr(route, "routes", None)
        if methods and path:
            full = join_paths(prefix, path)
            meth = sorted(m for m in methods if m not in IGNORED_METHODS)
            if meth:
                endpoint = getattr(route, "endpoint", None)
                yield {
                    "path": full,
                    "methods": meth,
                    "endpoint": getattr(endpoint, "__name__", None),
                    "module": getattr(endpoint, "__module__", None),
                    "route_type": name,
                }
        if nested:
            extra = path if name == "Mount" else ""
            yield from iter_mounted_routes(app, nested, join_paths(prefix, extra or ""))


def load_app(repo_root: Path) -> Any:
    _ensure_api_on_path(repo_root)
    from app.main import app  # noqa: WPS433 — intentional late import

    return app


def collect_inventory(app: Any) -> Dict[str, Any]:
    mounted = list(iter_mounted_routes(app))
    # Deduplicate identical (path, methods) from double-mounts while keeping count.
    by_key: Dict[Tuple[str, Tuple[str, ...]], Dict[str, Any]] = {}
    duplicate_mounts: List[Dict[str, Any]] = []
    for item in mounted:
        key = (item["path"], tuple(item["methods"]))
        if key in by_key:
            duplicate_mounts.append(item)
            continue
        by_key[key] = item
    unique = list(by_key.values())

    openapi_paths: List[str] = []
    try:
        openapi_paths = sorted((app.openapi() or {}).get("paths", {}).keys())
    except Exception as exc:  # pragma: no cover - OpenAPI is a cross-check
        openapi_paths = []
        openapi_error = str(exc)
    else:
        openapi_error = None

    walked_paths = {r["path"] for r in unique}
    oa_set = set(openapi_paths)

    return {
        "top_level_route_objects": len(app.routes),
        "walked_operations": len(mounted),
        "unique_mounted_operations": len(unique),
        "unique_mounted_paths": len(walked_paths),
        "openapi_paths": len(openapi_paths),
        "openapi_error": openapi_error,
        "in_openapi_not_walked": sorted(oa_set - walked_paths),
        "in_walked_not_openapi": sorted(walked_paths - oa_set),
        "duplicate_mounts": [
            {"path": d["path"], "methods": d["methods"]} for d in duplicate_mounts
        ],
        "routes": unique,
    }


# --------------------------------------------------------------------------- #
# Candidate classification + capability grouping
# --------------------------------------------------------------------------- #


def looks_like_machine_output(path: str) -> bool:
    lowered = path.lower()
    return any(token in lowered for token in _HINT_TOKENS)


def exclusion_reason(path: str) -> Optional[str]:
    lowered = path.lower()
    for prefix, reason in EXCLUSION_RULES:
        if lowered.startswith(prefix) or path.startswith(prefix):
            return reason
    return None


def infer_artifact_types(path: str) -> List[str]:
    lowered = path.lower()
    types: List[str] = []
    if "operator-pack" in lowered:
        types.append("operator_pack")
    if "export_bundle" in lowered:
        types.append("zip_with_gcode")
    if lowered.endswith(".nc") or "_governed.nc" in lowered:
        types.append("nc")
    if "feeds-speeds" in lowered:
        types.append("feeds_speeds_json")
    if "gcode" in lowered or "helical_entry" in lowered or "dxf-to-grbl" in lowered or "post_v155" in lowered:
        if "gcode" not in types:
            types.append("gcode")
    if "plan-toolpath" in lowered:
        types.append("unknown")
    if not types:
        types.append("unknown")
    # unique preserve order
    seen = set()
    out = []
    for t in types:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def route_role(path: str) -> str:
    lowered = path.lower()
    if "intent" in lowered:
        return "intent"
    if "download" in lowered:
        return "download"
    if lowered.endswith("_governed") or "_governed." in lowered or lowered.endswith("_governed.nc"):
        return "alias"
    if lowered.endswith("/gcode") or lowered.endswith("/generate-gcode") or lowered.endswith("/export-gcode"):
        return "primary"
    return "other"


def _prefix_matches(path: str, pfx: str) -> bool:
    return path == pfx or path.startswith(pfx + "/") or path.startswith(pfx + ".")


def assign_capability(path: str) -> Tuple[str, str]:
    """Return (capability_id, grouping_rule). Deterministic; no subjective merge."""
    # Owner ruling 2026-08-27: acoustic binding is manufacturing-intent binding,
    # not guitar-body. Path prefix /api/cam/guitar would otherwise swallow it.
    lowered = path.lower()
    if "/acoustic/" in lowered and "/binding/" in lowered:
        return "binding", "owner_ruling:acoustic_binding_separate"
    matches = [(pfx, cid) for pfx, cid in SEEDED_PREFIXES if _prefix_matches(path, pfx)]
    if matches:
        pfx, cid = max(matches, key=lambda x: len(x[0]))
        return cid, f"seeded_prefix:{pfx}"
    derived = derive_family(path)
    return derived, f"derived_path_family:{derived}"


def derive_family(path: str) -> str:
    action_segments = {
        "gcode",
        "gcode_governed",
        "download",
        "download_governed",
        "generate-gcode",
        "export-gcode",
        "export_gcode",
        "export_gcode_governed",
        "post-gcode",
        "intent-gcode",
        "gcode_intent",
        "batch_export",
        "operator-pack",
        "photo-to-gcode",
        "export_bundle",
        "export_bundle_multi",
        "plan-toolpath",
        "post_v155",
        "posts_v155",
        "dxf-to-grbl",
        "helical_entry",
        "feeds-speeds",
    }
    parts = [p for p in path.split("/") if p]
    while parts and (
        parts[-1] in action_segments
        or parts[-1].endswith(".nc")
        or parts[-1].startswith("{")
    ):
        parts.pop()
    if parts and parts[0] == "api":
        parts = parts[1:]
    parts = [p for p in parts if not p.startswith("{")]
    if not parts:
        return "unclassified"
    # Keep two segments when namespaced (cam/geometry/rmos/saw/v1/neck/...).
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]}-{parts[1]}"


def classify_routes(routes: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = []
    exclusions: List[Dict[str, Any]] = []
    for route in routes:
        path = route["path"]
        if not looks_like_machine_output(path):
            continue
        reason = exclusion_reason(path)
        if reason:
            exclusions.append(
                {
                    "path": path,
                    "methods": route["methods"],
                    "reason": reason,
                }
            )
            continue
        cap_id, grouping = assign_capability(path)
        item = dict(route)
        item["capability_id"] = cap_id
        item["grouping_rule"] = grouping
        item["artifact_types"] = infer_artifact_types(path)
        item["route_role"] = route_role(path)
        candidates.append(item)
    return {"candidates": candidates, "exclusions": exclusions}


def group_capabilities(candidates: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        grouped[item["capability_id"]].append(item)
    return dict(grouped)


def stage1_capability_record(capability_id: str, routes: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    grouping = routes[0]["grouping_rule"] if routes else f"seeded_required:{capability_id}"
    artifact_types: List[str] = []
    for r in routes:
        for t in r.get("artifact_types") or []:
            if t not in artifact_types:
                artifact_types.append(t)
    if not artifact_types:
        artifact_types = ["unknown"]
    family = capability_id
    return {
        "capability_id": capability_id,
        "operation_family": family,
        "grouping_rule": grouping,
        "surface_kind": infer_surface_kind(capability_id),
        "intent_contract": "UNKNOWN",
        "authority": {
            "status": "UNKNOWN",
            "evaluator": None,
            "policy_boundary": None,
        },
        "generation_ordering": "UNKNOWN",
        "input_contract_status": "UNKNOWN",
        "ungated_output_exposure": "UNKNOWN",
        "routes": [
            {
                "path": r["path"],
                "methods": r["methods"],
                "mount_state": "MOUNTED",
                "route_role": r.get("route_role", "other"),
                "historical_or_dead": False,
            }
            for r in sorted(routes, key=lambda x: (x["path"], x["methods"]))
        ],
        "generators": [],
        "persistence": {"status": "UNKNOWN", "mechanism": None},
        "artifact_types": artifact_types,
        "client_consumers": [],
        "reachability": "MOUNTED" if routes else "SOURCE_PRESENT",
        "runtime_evidence": "NOT_OBTAINED_STAGE_1",
        "authority_disposition": "UNKNOWN",
        "evidence": [
            {
                "class": "MOUNTED_ROUTE_TABLE",
                "ref": "app.main:app",
                "note": "Stage 1 inventory only. No authority conclusion.",
            }
        ],
        "evidence_class": "INSUFFICIENT_EVIDENCE",
        "confidence": "LOW",
    }


def build_skeleton(inventory: Dict[str, Any], classified: Dict[str, Any]) -> Dict[str, Any]:
    grouped = group_capabilities(classified["candidates"])
    capabilities = []
    seen = set()
    # Required seeds first, even if empty (taxonomy visibility).
    for seed in REQUIRED_SEED_IDS:
        rec = stage1_capability_record(seed, grouped.get(seed, []))
        capabilities.append(rec)
        seen.add(seed)
    for cap_id in sorted(grouped):
        if cap_id in seen:
            continue
        capabilities.append(stage1_capability_record(cap_id, grouped[cap_id]))
        seen.add(cap_id)
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": AUDIT_ID,
        "stage": "stage_1_checkpoint",
        "warning": WARNING_TEXT,
        "adjacent_authority_maps": ADJACENT_MAPS,
        "surface_kind_vocabulary": SURFACE_KIND_VOCABULARY,
        "reachability_vocabulary": REACHABILITY_VOCABULARY,
        "disposition_vocabulary": DISPOSITION_VOCABULARY,
        "evidence_class_vocabulary": EVIDENCE_CLASS_VOCABULARY,
        "capabilities": capabilities,
        "exclusions": classified["exclusions"],
        "unexplained_emitters": [],
    }


# --------------------------------------------------------------------------- #
# Validation (does not mutate)
# --------------------------------------------------------------------------- #


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def registered_route_keys(registry: Dict[str, Any]) -> Dict[Tuple[str, Tuple[str, ...]], str]:
    out: Dict[Tuple[str, Tuple[str, ...]], str] = {}
    for cap in registry.get("capabilities", []):
        for route in cap.get("routes", []):
            key = (route["path"], tuple(route["methods"]))
            out[key] = cap["capability_id"]
    return out


def candidate_route_keys(classified: Dict[str, Any]) -> Dict[Tuple[str, Tuple[str, ...]], str]:
    out: Dict[Tuple[str, Tuple[str, ...]], str] = {}
    for item in classified["candidates"]:
        key = (item["path"], tuple(item["methods"]))
        out[key] = item["capability_id"]
    return out


def validate_registry(
    registry: Dict[str, Any],
    *,
    inventory: Optional[Dict[str, Any]] = None,
    classified: Optional[Dict[str, Any]] = None,
    schema: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Return a list of validation failures. Empty list means pass."""
    errors: List[str] = []

    if schema is not None:
        try:
            import jsonschema
        except ImportError:  # pragma: no cover
            errors.append("jsonschema is not installed; cannot apply schema")
        else:
            validator = jsonschema.Draft202012Validator(schema)
            for err in validator.iter_errors(registry):
                loc = "/".join(str(p) for p in err.path) or "(root)"
                errors.append(f"schema:{loc}: {err.message}")

    caps = registry.get("capabilities") or []
    ids = [c.get("capability_id") for c in caps]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        errors.append(f"MAR-001 duplicate capability_id(s): {dupes}")

    vocab = set(registry.get("disposition_vocabulary") or DISPOSITION_VOCABULARY)
    for cap in caps:
        disp = cap.get("authority_disposition")
        if disp not in vocab:
            errors.append(
                f"MAR-002 {cap.get('capability_id')}: disposition {disp!r} not in vocabulary"
            )
        if disp in AUTHORITATIVE_DISPOSITIONS:
            evidence = cap.get("evidence") or []
            if not evidence:
                errors.append(
                    f"MAR-003 {cap.get('capability_id')}: authoritative disposition {disp} lacks evidence"
                )
            if disp == "LIVE_UNGOVERNED_OUTPUT" and cap.get("authority", {}).get("status") in (
                "NAMED",
            ):
                # Silent governed marking of an ungoverned disposition.
                errors.append(
                    f"MAR-003 {cap.get('capability_id')}: LIVE_UNGOVERNED_OUTPUT marked with named authority"
                )

        reach = cap.get("reachability")
        runtime_ev = cap.get("runtime_evidence")
        if reach == "RUNTIME_REACHABLE" and runtime_ev in (
            "NOT_OBTAINED_STAGE_1",
            "NOT_OBTAINED_SAFELY",
            None,
        ):
            errors.append(
                f"MAR-023 {cap.get('capability_id')}: SOURCE/MOUNT evidence cannot establish RUNTIME_REACHABLE"
            )
        if reach in {"RUNTIME_BROKEN", "RUNTIME_BLOCKED_BY_POLICY"} and not cap.get("client_consumers"):
            # Empty consumers must not be the reason a route is called dead.
            if runtime_ev in ("NOT_OBTAINED_STAGE_1", "NOT_OBTAINED_SAFELY") and reach != "MOUNTED":
                errors.append(
                    f"MAR-022 {cap.get('capability_id')}: NO_IN_REPO_CONSUMER must not classify reachability as {reach}"
                )

        for route in cap.get("routes") or []:
            if route.get("historical_or_dead") and route.get("mount_state") == "MOUNTED":
                errors.append(
                    f"MAR-005 {cap.get('capability_id')} {route.get('path')}: historical/dead flag on a mounted route"
                )
            if route.get("mount_state") in {"HISTORICAL", "DEAD", "UNMOUNTED"} and not route.get(
                "historical_or_dead"
            ):
                errors.append(
                    f"MAR-005 {cap.get('capability_id')} {route.get('path')}: stale route lacks historical_or_dead"
                )

        kind = cap.get("surface_kind")
        if kind not in set(SURFACE_KIND_VOCABULARY):
            errors.append(
                f"MAR-025 {cap.get('capability_id')}: surface_kind {kind!r} not in vocabulary"
            )
        if kind == "advisory" and disp not in {
            "ADVISORY_ONLY",
            "UNKNOWN",
            "INSUFFICIENT_EVIDENCE",
        }:
            errors.append(
                f"MAR-025 {cap.get('capability_id')}: advisory surface cannot carry manufacturing disposition {disp}"
            )
        if kind == "artifact_retrieval" and disp == "GOVERNED":
            errors.append(
                f"MAR-009 {cap.get('capability_id')}: artifact retrieval cannot be manufacturing GOVERNED"
            )
        if cap.get("persistence", {}).get("status") == "FALSE_PROVENANCE" and disp == "GOVERNED":
            errors.append(
                f"MAR-009 {cap.get('capability_id')}: GREEN/false provenance is not GOVERNED"
            )
        if (
            registry.get("stage") == "stage_2_authority"
            and cap.get("runtime_evidence") == "NOT_OBTAINED_STAGE_1"
        ):
            errors.append(
                f"MAR-023 {cap.get('capability_id')}: Stage 2 cannot retain NOT_OBTAINED_STAGE_1"
            )

    unclassified = registry.get("_stage2_unclassified_capabilities") or []
    if unclassified:
        errors.append(f"MAR-006 Stage 2 overlay missing capabilities: {unclassified}")

    if inventory is not None and classified is not None:
        mounted_keys = {
            (r["path"], tuple(r["methods"])) for r in inventory["routes"]
        }
        reg_keys = registered_route_keys(registry)
        cand_keys = candidate_route_keys(classified)

        for key, cap_id in reg_keys.items():
            path, methods = key
            route_rec = None
            for cap in caps:
                if cap["capability_id"] != cap_id:
                    continue
                for route in cap.get("routes") or []:
                    if route["path"] == path and tuple(route["methods"]) == methods:
                        route_rec = route
                        break
            if route_rec and route_rec.get("historical_or_dead"):
                continue
            if key not in mounted_keys:
                errors.append(
                    f"MAR-004 {cap_id} {path} {list(methods)}: registered mounted route does not resolve"
                )

        for key, cap_id in cand_keys.items():
            if key not in reg_keys:
                path, methods = key
                errors.append(
                    f"MAR-006/MAR-021 unregistered machine-artifact route {path} {list(methods)} (discovered as {cap_id})"
                )

        # Alias grouping: retract-style suffixes must not mint extra capabilities.
        by_family = defaultdict(set)
        for cap in caps:
            for route in cap.get("routes") or []:
                fam, _ = assign_capability(route["path"])
                by_family[fam].add(cap["capability_id"])
        for fam, cap_ids in by_family.items():
            if len(cap_ids) > 1:
                errors.append(
                    f"MAR-008 family {fam} split across capabilities {sorted(cap_ids)}"
                )

    return errors


def checkpoint_summary(
    inventory: Dict[str, Any],
    classified: Dict[str, Any],
    registry: Dict[str, Any],
    errors: Sequence[str],
) -> Dict[str, Any]:
    grouped = group_capabilities(classified["candidates"])
    aliases = []
    for cap in registry.get("capabilities", []):
        routes = cap.get("routes") or []
        if len(routes) > 1:
            aliases.append(
                {
                    "capability_id": cap["capability_id"],
                    "route_count": len(routes),
                    "paths": [r["path"] for r in routes],
                }
            )
    seeded_present = [
        c["capability_id"]
        for c in registry.get("capabilities", [])
        if c["capability_id"] in REQUIRED_SEED_IDS
    ]
    derived = [
        c["capability_id"]
        for c in registry.get("capabilities", [])
        if c["capability_id"] not in REQUIRED_SEED_IDS
    ]
    empty_seeds = [
        c["capability_id"]
        for c in registry.get("capabilities", [])
        if c["capability_id"] in REQUIRED_SEED_IDS and not c.get("routes")
    ]
    return {
        "top_level_route_objects": inventory["top_level_route_objects"],
        "walked_operations": inventory["walked_operations"],
        "unique_mounted_operations": inventory["unique_mounted_operations"],
        "unique_mounted_paths": inventory["unique_mounted_paths"],
        "openapi_paths": inventory["openapi_paths"],
        "machine_output_candidates": len(classified["candidates"]),
        "excluded_hint_matches": len(classified["exclusions"]),
        "capability_count": len(registry.get("capabilities", [])),
        "seeded_capabilities": seeded_present,
        "derived_capabilities": derived,
        "empty_seeded_capabilities": empty_seeds,
        "unexplained_emitters": registry.get("unexplained_emitters") or [],
        "route_aliases": aliases,
        "duplicate_mounts": inventory.get("duplicate_mounts") or [],
        "validation_errors": list(errors),
        "runtime_witnesses_attempted": [],
        "runtime_witnesses_withheld": [
            "all POST machine-artifact endpoints (Stage 1 does not deep-trace)",
            "any endpoint that persists RunArtifact, writes operator files, or mutates durable state",
        ],
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RMOS manufacturing-output census (read-only; not an agent)."
    )
    parser.add_argument("--repo-root", default=None, help="Repository root (auto-detected).")
    parser.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY,
        help="Registry JSON path relative to repo root.",
    )
    parser.add_argument(
        "--schema",
        default=DEFAULT_SCHEMA,
        help="JSON Schema path relative to repo root.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the committed registry against the mounted surface (default with inventory).",
    )
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="Print the checkpoint inventory JSON.",
    )
    parser.add_argument(
        "--emit-skeleton",
        action="store_true",
        help="Print a Stage-1 UNKNOWN skeleton to stdout. Does not write files.",
    )
    parser.add_argument(
        "--emit-stage2",
        action="store_true",
        help="Print the Stage-2 overlay applied to the live inventory. Does not write files.",
    )
    parser.add_argument(
        "--app",
        default=None,
        help=argparse.SUPPRESS,  # tests inject a FastAPI app via load hook, not CLI
    )
    return parser


def _run(
    *,
    repo_root: Path,
    registry_rel: str,
    schema_rel: str,
    do_validate: bool,
    do_inventory: bool,
    emit_skeleton: bool,
    emit_stage2: bool = False,
    app: Any = None,
) -> int:
    if app is None:
        app = load_app(repo_root)
    inventory = collect_inventory(app)
    classified = classify_routes(inventory["routes"])

    if emit_skeleton:
        skeleton = build_skeleton(inventory, classified)
        json.dump(skeleton, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if emit_stage2:
        skeleton = build_skeleton(inventory, classified)
        stage2 = apply_stage2(skeleton)
        stage2.pop("_stage2_unclassified_capabilities", None)
        json.dump(stage2, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    registry_path = repo_root / registry_rel
    schema_path = repo_root / schema_rel
    if not registry_path.is_file():
        print(f"FAIL: registry not found: {registry_path}", file=sys.stderr)
        return 1
    registry = load_json(registry_path)
    schema = load_json(schema_path) if schema_path.is_file() else None

    errors = validate_registry(
        registry, inventory=inventory, classified=classified, schema=schema
    )
    summary = checkpoint_summary(inventory, classified, registry, errors)

    if do_inventory or not do_validate:
        json.dump(summary, sys.stdout, indent=2)
        sys.stdout.write("\n")

    if errors:
        print(f"FAIL: {len(errors)} validation error(s)", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    if do_validate or not do_inventory:
        print("OK: manufacturing authority registry reconciles with mounted surface")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root()
    do_validate = args.validate
    do_inventory = args.inventory
    if not args.emit_skeleton and not args.emit_stage2 and not do_validate and not do_inventory:
        do_validate = True
        do_inventory = True
    return _run(
        repo_root=repo_root,
        registry_rel=args.registry,
        schema_rel=args.schema,
        do_validate=do_validate,
        do_inventory=do_inventory,
        emit_skeleton=args.emit_skeleton,
        emit_stage2=args.emit_stage2,
        app=None,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
