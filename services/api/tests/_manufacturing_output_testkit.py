"""Shared helpers for manufacturing-output proofs.

The route walker is the CI implementation. Production routers must not import
this module, and this module does not call a generator.
"""
from __future__ import annotations

import ast
import json
import re
import textwrap
from dataclasses import dataclass

from app.ci.manufacturing_output_walk import (
    UnresolvedRoute,
    naive_walk,
    normalize_path,
    reconcile,
    walk_live,
)

_COMMAND = re.compile(r"[GM]\d+", re.IGNORECASE)
_LINE_NUMBER = re.compile(r"N\d+", re.IGNORECASE)
_COMMENT = re.compile(r"\([^)]*\)")
PROSE_KEYS = {"reason", "evidence", "detail", "message", "exit_condition"}
PROGRAM_KEYS = {"gcode"}


@dataclass(frozen=True)
class ResolvedRoute:
    method: str
    path: str
    endpoint: object
    response_model: object = None
    include_in_schema: bool = True
    route_name: str = ""


def walk_routes(routes, prefix: str = ""):
    """Resolved routes plus route objects the walker could not classify."""
    live, unresolved = walk_live(routes, prefix)
    resolved = [
        ResolvedRoute(
            route.method,
            route.path,
            route.endpoint,
            route.response_model,
            route.include_in_schema,
            route.route_name,
        )
        for route in live
    ]
    return resolved, unresolved


def find_function(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _first_executable(fn: ast.AST):
    body = list(getattr(fn, "body", []))
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    return body[0] if body else None


def first_statement_gate_key(source: str, fn_name: str) -> str | None:
    """Readiness key if that call is the function's first executable statement.

    A gate later in the body does not count. Docstrings are not executable.
    """
    fn = find_function(ast.parse(textwrap.dedent(source)), fn_name)
    if fn is None:
        return None
    stmt = _first_executable(fn)
    if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
        return None
    call = stmt.value
    func = call.func
    if not isinstance(func, ast.Name) or func.id != "_readiness_gate":
        return None
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Constant):
        return None
    value = call.args[0].value
    return value if isinstance(value, str) else None


def command_token(line: str) -> str | None:
    """First G/M command token on a line. Prose and N-words are not commands."""
    stripped = _COMMENT.sub(" ", line).strip()
    if not stripped or stripped.startswith(";"):
        return None
    for token in stripped.split():
        if _LINE_NUMBER.fullmatch(token):
            continue
        match = _COMMAND.fullmatch(token)
        if match:
            return match.group(0).upper()
        return None
    return None


def records_in_program_text(text: str) -> list[str]:
    return [token for line in text.splitlines() if (token := command_token(line))]


def records_in_json(node, key: str | None = None) -> list[str]:
    """Program records in program-bearing fields. Prose keys are not entered."""
    found: list[str] = []
    if isinstance(node, dict):
        for child_key, child in node.items():
            if child_key in PROSE_KEYS:
                continue
            found.extend(records_in_json(child, child_key))
    elif isinstance(node, list):
        for child in node:
            found.extend(records_in_json(child, key))
    elif isinstance(node, str) and key in PROGRAM_KEYS:
        found.extend(records_in_program_text(node))
    return found


def program_records(content_type: str, body: bytes) -> list[str]:
    if "json" in content_type.lower():
        return records_in_json(json.loads(body.decode()))
    return records_in_program_text(body.decode())


__all__ = [
    "ResolvedRoute",
    "UnresolvedRoute",
    "command_token",
    "find_function",
    "first_statement_gate_key",
    "naive_walk",
    "normalize_path",
    "program_records",
    "reconcile",
    "records_in_json",
    "records_in_program_text",
    "walk_live",
    "walk_routes",
]
