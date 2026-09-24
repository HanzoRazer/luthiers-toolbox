"""Static classification of manufacturing-output candidates.

Source and route metadata only. This module does not call generators,
send programs, or import physical senders.
"""
from __future__ import annotations

import ast
import inspect
import re
import textwrap

from app.ci.manufacturing_output_ast import (
    Facts,
    authentication_posture,
    facts_of,
    function_node,
    handler_id,
    handler_source,
    relative_source,
    unwrap,
)


BASE_SHA = "1ebc49610b1690ef7d761ab598758c5db8d6193c"
HISTORICAL_CANDIDATES = 420
HISTORICAL_HANDLERS = 126
HISTORICAL_HIGH_SIGNAL = 56
HIGH_SIGNAL_MIN = 3

PATH_TOKENS = (
    "gcode", "toolpath", "/generate", "/download", ".nc", ".tap", ".ngc",
    "program", "export", "postprocess",
)
_FILENAME = re.compile(r"\.(?:nc|tap|ngc|gcode)\b", re.IGNORECASE)
RUNTIME_PROVED = frozenset({
    ("POST", "/api/cam-workspace/neck/generate-full"),
    ("POST", "/api/cam-workspace/neck/generate/{op}"),
    ("POST", "/api/neck/gcode/generate"),
    ("POST", "/api/neck/gcode/download"),
    ("POST", "/api/cam/guitar/{model_id}/neck/gcode"),
    ("POST", "/api/cam/guitar/flying_v/body/gcode"),
    ("POST", "/api/cam/guitar/flying_v/toolpath/control_cavity"),
    ("POST", "/api/cam/guitar/flying_v/toolpath/neck_pocket"),
    ("POST", "/api/cam/guitar/flying_v/toolpath/pickup"),
    ("POST", "/api/cam/guitar/stratocaster/body/gcode"),
    ("POST", "/api/cam/guitar/les_paul/body/gcode"),
    ("POST", "/api/cam/guitar/acoustic/{style}/body/gcode"),
    ("POST", "/api/cam/guitar/acoustic/{style}/soundhole/gcode"),
    ("POST", "/api/cam/guitar/acoustic/{style}/binding/gcode"),
    ("POST", "/api/cam/polygon_offset_governed.nc"),
    ("POST", "/api/geometry/export_gcode_governed"),
    ("POST", "/api/probe/boss/gcode/download_governed"),
    ("POST", "/api/probe/corner/gcode/download_governed"),
    ("POST", "/api/probe/pocket/gcode/download_governed"),
    ("POST", "/api/probe/surface_z/gcode/download_governed"),
    ("POST", "/api/probe/vise_square/gcode/download_governed"),
    ("POST", "/api/cam/retract/gcode"),
    ("POST", "/api/cam/retract/gcode/download"),
})
ROW_FIELDS = (
    "method", "path", "route_name", "handler", "source_file", "response_carrier",
    "classification", "implementation_kind", "implementation_symbol", "delegates_to",
    "authentication", "authority_layer", "authority_key", "authority_order",
    "containment", "proof_status", "evidence", "notes",
)
ENUMS = {
    "classification": {"CONFIRMED_EMITTER", "CONFIRMED_DELEGATE", "NON_EMITTING", "UNEXAMINED"},
    "implementation_kind": {"class", "function", "inline", "delegate", "postprocessor", "unknown"},
    "authentication": {"none", "optional", "required", "unknown"},
    "authority_layer": {"readiness", "manufacturing_output", "asset", "other", "none", "unknown"},
    "authority_order": {"before_generation", "after_generation", "none", "unknown"},
    "containment": {"FAIL_CLOSED", "PERMITTED_BY_AUTHORITY", "LIVE_UNGOVERNED", "UNKNOWN", "NOT_APPLICABLE"},
    "proof_status": {"RUNTIME_PROVED", "SOURCE_PROVED", "MECHANICALLY_DISCOVERED", "UNEXAMINED"},
    "response_carrier": {"json_field", "attachment", "stream", "websocket", "none", "unknown"},
}


def _lookup(endpoint, name: str):
    module = inspect.getmodule(unwrap(endpoint))
    if module is None:
        return None
    value = getattr(module, name, None)
    if inspect.isfunction(value) or inspect.iscoroutinefunction(value):
        return value
    return None


def _authentication_dependency(endpoint, name: str):
    """Resolve one handler-visible dependency to its function AST."""
    dependency = _lookup(endpoint, name)
    if dependency is None:
        return None
    source = handler_source(dependency)
    dependency_name = getattr(unwrap(dependency), "__name__", None)
    return function_node(source, dependency_name)


def _resolve_import(module: str | None, level: int, current: str) -> str:
    if not level:
        return module or ""
    package = current.rsplit(".", 1)[0]
    parts = package.split(".")
    keep = len(parts) - (level - 1)
    base = ".".join(parts[:keep]) if keep > 0 else ""
    if module and base:
        return f"{base}.{module}"
    return module or base


def _module_text(endpoint, name: str) -> str:
    helper = _lookup(endpoint, name)
    if helper is None:
        return ""
    module = inspect.getmodule(helper)
    if module is None:
        return handler_source(helper)
    try:
        return inspect.getsource(module)
    except (OSError, TypeError):
        return handler_source(helper)


def _imported(source: str, imported_name: str, current_module: str) -> str | None:
    node = _parse_module(source)
    if node is None:
        return None
    for item in ast.walk(node):
        if not isinstance(item, ast.ImportFrom):
            continue
        for alias in item.names:
            if (alias.asname or alias.name) != imported_name and alias.name != imported_name:
                continue
            resolved = _resolve_import(item.module, item.level, current_module)
            return f"{resolved}.{alias.name}" if resolved else alias.name
    return None


def _parse_module(source: str):
    try:
        return ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return None


def _class_in_text(source: str, current_module: str) -> str | None:
    node = _parse_module(source)
    if node is None:
        return None
    for item in ast.walk(node):
        if not isinstance(item, ast.Call):
            continue
        func = item.func
        class_name = ""
        if isinstance(func, ast.Name) and func.id.endswith("Generator"):
            class_name = func.id
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id.endswith("Generator"):
                class_name = func.value.id
        if not class_name:
            continue
        imported = _imported(source, class_name, current_module)
        return imported or class_name
    return None


def _qualify_call(endpoint, name: str, owner: str, source: str) -> tuple[str, str]:
    current = getattr(unwrap(endpoint), "__module__", "") or ""
    if name == "NeckPipeline":
        return "class", "app.cam.neck.orchestrator.NeckPipeline"
    if name == "NeckGCodeGenerator":
        return "class", "app.generators.neck_headstock_generator.NeckGCodeGenerator"
    if owner.endswith("Generator"):
        imported = _imported(source, owner, current)
        return "class", imported or owner
    if owner == "probe_patterns":
        imported = _imported(source, owner, current)
        base = imported or "app.cam.probe_patterns"
        return "function", f"{base}.{name}"
    if owner == "gcode_lines" or name == "inline":
        return "inline", "inline"
    if "postprocess" in name.lower():
        return "postprocessor", _qualify_function(endpoint, name)
    if "cam.flying_v" in source:
        return "function", "app.cam.flying_v.pocket_generator"
    if name == "_create_generator":
        found = _class_in_text(_module_text(endpoint, name), current)
        if found:
            return "class", found
    return "function", _qualify_function(endpoint, name)


def _qualify_function(endpoint, name: str) -> str:
    helper = _lookup(endpoint, name)
    if helper is None:
        return name
    module = getattr(helper, "__module__", "") or ""
    return f"{module}.{name}" if module else name


def implementation_of(endpoint, facts: Facts, source: str) -> tuple[str, str | None]:
    if facts.inline and not facts.program:
        return "inline", "inline"
    for _lineno, name, owner in facts.program:
        if name == "postprocess_wrap":
            return "postprocessor", handler_id(endpoint)
        if owner == "gcode_lines":
            return "inline", "inline"
        return _qualify_call(endpoint, name, owner, source)
    if "cam.flying_v" in source and facts.program:
        return "function", "app.cam.flying_v.pocket_generator"
    if facts.inline:
        return "inline", "inline"
    return "unknown", None


def authority_order(facts: Facts) -> str:
    if not facts.authority:
        return "none"
    points = [lineno for lineno, _name, _owner in facts.program]
    points.extend(lineno for lineno, _name in facts.delegates)
    if facts.inline:
        points.append(_first_inline_line(facts))
    if not points:
        return "before_generation"
    if min(item[0] for item in facts.authority) < min(points):
        return "before_generation"
    return "after_generation"


def delegation_edge(facts: Facts) -> tuple[int, str] | None:
    """Return the first caller-local delegate edge without crossing scopes."""
    return facts.delegates[0] if facts.delegates else None


def composed_authority_order(caller: Facts, callee: Facts) -> str:
    """Order authority across a caller -> callee edge without comparing lines.

    Caller line numbers are compared only with the caller's delegate call. Callee
    line numbers are compared only with callee generation. Either scope may
    independently establish a pre-generation authority decision.
    """
    edge = delegation_edge(caller)
    caller_order = "none"
    if caller.authority and edge is not None:
        caller_order = (
            "before_generation"
            if min(item[0] for item in caller.authority) < edge[0]
            else "after_generation"
        )
    callee_order = authority_order(callee)
    if "before_generation" in {caller_order, callee_order}:
        return "before_generation"
    if "after_generation" in {caller_order, callee_order}:
        return "after_generation"
    return "none"


def _first_inline_line(facts: Facts) -> int:
    return min((lineno for lineno, _name, owner in facts.program if owner == "gcode_lines"), default=10**9)


def _model_fields(model) -> str:
    fields = getattr(model, "model_fields", None)
    if not fields:
        return ""
    return " ".join(fields)


def signal_set(route, source: str, fn) -> set[str]:
    signals: set[str] = set()
    if any(token in route.path.lower() for token in PATH_TOKENS):
        signals.add("path_token")
    if any(token in _model_fields(route.response_model).lower() for token in ("gcode", "program", "toolpath")):
        signals.add("response_model")
    lowered = source.lower()
    if "streamingresponse" in lowered or "fileresponse" in lowered:
        signals.add("stream")
    if "content-disposition" in lowered or "attachment" in lowered:
        signals.add("attachment")
    if "text/x-gcode" in lowered or "application/x-gcode" in lowered:
        signals.add("media_type")
    if _FILENAME.search(source):
        signals.add("program_filename")
    facts = facts_of(fn, source)
    if facts.emits:
        signals.add("generator")
    if facts.delegates:
        signals.add("delegation")
    return signals


def response_carrier(route, source: str) -> str:
    if route.method == "WEBSOCKET":
        return "websocket"
    lowered = source.lower()
    if "streamingresponse" in lowered:
        return "stream"
    if "content-disposition" in lowered or "attachment" in lowered or "fileresponse" in lowered:
        return "attachment"
    if any(token in _model_fields(route.response_model).lower() for token in ("gcode", "program", "toolpath")):
        return "json_field"
    return "none"


def _containment(order: str, has_authority: bool, key: str | None) -> str:
    if order == "before_generation" and has_authority and key:
        return "FAIL_CLOSED"
    if order == "after_generation":
        return "LIVE_UNGOVERNED"
    if has_authority:
        return "UNKNOWN"
    return "LIVE_UNGOVERNED"


def _proof(classified: bool, high: bool, proved: bool, signals: set[str]) -> str:
    if classified and proved:
        return "RUNTIME_PROVED"
    if classified:
        return "SOURCE_PROVED"
    if high or not signals:
        return "UNEXAMINED"
    return "MECHANICALLY_DISCOVERED"


def _note(classification: str, order: str) -> str:
    if classification == "UNEXAMINED":
        return "UNEXAMINED is not a safety claim. Source review did not prove emission."
    if order == "after_generation":
        return "Authority appears after generation, so this row is not fail-closed."
    return "Inventory classification is not manufacturing qualification."


def _apply_delegate(endpoint, facts: Facts, source: str):
    """One-level callee. Retract aliases inherit the handler they call."""
    if not facts.delegates or facts.emits:
        return facts, implementation_of(endpoint, facts, source), None, None
    _lineno, name = facts.delegates[0]
    callee = _lookup(endpoint, name)
    if callee is None:
        return facts, ("delegate", None), None, None
    callee_source = handler_source(callee)
    callee_fn = function_node(callee_source, getattr(callee, "__name__", None))
    callee_facts = facts_of(callee_fn, callee_source)
    kind, symbol = implementation_of(callee, callee_facts, callee_source)
    if not callee_facts.emits:
        return facts, (kind, symbol), None, None
    order = composed_authority_order(facts, callee_facts)
    caller_edge = delegation_edge(facts)
    caller_before = bool(
        facts.authority
        and caller_edge
        and min(item[0] for item in facts.authority) < caller_edge[0]
    )
    effective_authority = facts.authority if caller_before else callee_facts.authority
    if not effective_authority and facts.authority:
        effective_authority = facts.authority
    return callee_facts, ("delegate", symbol), order, effective_authority


def _delegate_name(facts: Facts) -> str | None:
    if facts.delegates and not facts.emits:
        return facts.delegates[0][1]
    return None


def _positive_verdict(kind: str, order: str, has_authority: bool, key, high: bool, proved: bool, signals: set[str]):
    classification = "CONFIRMED_DELEGATE" if kind == "delegate" else "CONFIRMED_EMITTER"
    containment = _containment(order, has_authority, key)
    proof = _proof(True, high, proved, signals)
    return classification, containment, proof, order, kind


def _unexamined_verdict(facts: Facts, has_authority: bool, layer: str, key, high: bool, signals: set[str]):
    proof = _proof(False, high, False, signals)
    if not has_authority:
        return "UNEXAMINED", "UNKNOWN", proof, "unknown", "unknown", None
    return "UNEXAMINED", "UNKNOWN", proof, authority_order(facts), layer, key


def _verdict(
    route,
    facts: Facts,
    used: Facts,
    kind: str,
    signals: set[str],
    order_override: str | None = None,
    authority_override: list[tuple[int, str, str | None]] | None = None,
):
    delegate_name = _delegate_name(facts)
    classified = bool(used.emits)
    if delegate_name and classified:
        kind = "delegate"
    authority = authority_override if authority_override is not None else used.authority
    has_authority = bool(authority)
    layer = authority[0][1] if has_authority else "none"
    key = authority[0][2] if has_authority else None
    high = len(signals) >= HIGH_SIGNAL_MIN
    proved = (route.method, route.path) in RUNTIME_PROVED
    if classified:
        order = order_override or authority_order(used)
        classification, containment, proof, order, kind = _positive_verdict(
            kind, order, has_authority, key, high, proved, signals,
        )
    else:
        classification, containment, proof, order, layer, key = _unexamined_verdict(
            facts, has_authority, layer, key, high, signals,
        )
    return {
        "delegate_name": delegate_name,
        "classified": classified,
        "kind": kind,
        "layer": layer,
        "key": key,
        "order": order,
        "classification": classification,
        "containment": containment,
        "proof": proof,
    }


def _evidence(endpoint, proof: str) -> str:
    evidence = relative_source(endpoint) or "source unavailable"
    if proof == "RUNTIME_PROVED":
        return f"{evidence}; prior containment tests"
    return evidence


def classify_route(route) -> dict | None:
    source = handler_source(route.endpoint)
    name = getattr(unwrap(route.endpoint), "__name__", None)
    fn = function_node(source, name)
    signals = signal_set(route, source, fn)
    if not signals:
        return None
    facts = facts_of(fn, source)
    used, (kind, symbol), order_override, authority_override = _apply_delegate(
        route.endpoint, facts, source,
    )
    verdict = _verdict(
        route,
        facts,
        used,
        kind,
        signals,
        order_override,
        authority_override,
    )
    classified = verdict["classified"]
    return {
        "method": route.method,
        "path": route.path,
        "route_name": route.route_name,
        "handler": handler_id(route.endpoint),
        "source_file": relative_source(route.endpoint),
        "response_carrier": response_carrier(route, source),
        "classification": verdict["classification"],
        "implementation_kind": verdict["kind"] if classified else "unknown",
        "implementation_symbol": symbol if classified else None,
        "delegates_to": verdict["delegate_name"],
        "authentication": authentication_posture(
            fn,
            lambda dependency: _authentication_dependency(route.endpoint, dependency),
        ),
        "authority_layer": verdict["layer"],
        "authority_key": verdict["key"],
        "authority_order": verdict["order"],
        "containment": verdict["containment"],
        "proof_status": verdict["proof"],
        "evidence": _evidence(route.endpoint, verdict["proof"]),
        "notes": _note(verdict["classification"], verdict["order"]),
        "_signals": sorted(signals),
    }
