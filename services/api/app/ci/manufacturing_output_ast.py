"""Handler AST facts for the manufacturing-output inventory.

Parsing only. Does not call generators or import routers.
"""
from __future__ import annotations

import ast
import inspect
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

_COMMAND = re.compile(r"^[GM]\d+$", re.IGNORECASE)
_FILENAME = re.compile(r"\.(?:nc|tap|ngc|gcode)\b", re.IGNORECASE)
_PROGRAMISH = ("gcode", "toolpath", "nc_program", "postprocess")
_AUTHORITY = {
    "_readiness_gate": "readiness",
    "require_generator_readiness": "readiness",
    "require_manufacturing_output_authority": "manufacturing_output",
    "require_probe_manufacturing_authority": "manufacturing_output",
    "require_manufacturing_authority": "asset",
    "_authorize_retract": "manufacturing_output",
}
_DELEGATES = {
    "generate_neck_gcode",
    "generate_simple_retract_gcode",
    "download_retract_gcode",
}
_CONSTRUCTORS = {"NeckPipeline", "NeckGCodeGenerator", "_create_generator"}
_READINESS_ARG = {"_readiness_gate", "require_generator_readiness"}


def repo_root() -> Path:
    # services/api/app/ci/<file>.py → repository root
    return Path(__file__).resolve().parents[4]


def unwrap(endpoint):
    seen: set[int] = set()
    current = endpoint
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        nxt = getattr(current, "_original_func", None) or getattr(current, "__wrapped__", None)
        if nxt is None:
            break
        current = nxt
    return current


def handler_source(endpoint) -> str:
    target = unwrap(endpoint)
    try:
        return inspect.getsource(target)
    except (OSError, TypeError):
        return ""


def relative_source(endpoint) -> str:
    target = unwrap(endpoint)
    code = getattr(target, "__code__", None)
    if code is None:
        return ""
    path = Path(code.co_filename)
    try:
        return str(path.resolve().relative_to(repo_root())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def handler_id(endpoint) -> str:
    target = unwrap(endpoint)
    module = getattr(target, "__module__", "") or ""
    qual = getattr(target, "__qualname__", "") or getattr(target, "__name__", "")
    return f"{module}.{qual}" if module else qual


def function_node(source: str, name: str | None = None):
    """Parse a handler, including a nested function whose source is indented."""
    try:
        tree = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return None
    found = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if name:
        for node in found:
            if node.name == name:
                return node
    return found[0] if found else None


def _skip_nested(node):
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef))


def iter_calls(fn: ast.AST):
    def visit(node):
        if _skip_nested(node):
            return
        if isinstance(node, ast.Call):
            yield node
        for child in ast.iter_child_nodes(node):
            yield from visit(child)

    for stmt in getattr(fn, "body", []):
        yield from visit(stmt)


def call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def call_owner(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return func.value.id
    return ""


def _placeholder(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return "{" + node.id + "}"
    if isinstance(node, ast.Attribute):
        return "{" + node.attr + "}"
    return "{param}"


def render_expr(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if not isinstance(node, ast.JoinedStr):
        return None
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        elif isinstance(value, ast.FormattedValue):
            parts.append(_placeholder(value.value))
        else:
            parts.append("{param}")
    return "".join(parts)


def authority_key(call: ast.Call, name: str) -> str | None:
    if name in _READINESS_ARG and call.args:
        return render_expr(call.args[0])
    for item in call.keywords:
        if item.arg == "tool_id":
            return render_expr(item.value)
    return None


def alias_map(fn: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(fn):
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            aliases[alias.asname or alias.name] = alias.name
    return aliases


def _programish(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in _PROGRAMISH)


def _is_program_call(name: str, owner: str) -> bool:
    if name in _DELEGATES:
        return False
    if name in _CONSTRUCTORS:
        return True
    if owner == "gcode_lines":
        return True
    if owner == "probe_patterns" and name.startswith("generate_"):
        return True
    if owner.endswith("Generator"):
        return True
    if name.startswith("_build_") and "gcode" in name:
        return True
    if _programish(name) and (name.startswith("generate_") or name.startswith("build_")):
        return True
    return False


def inline_commands(fn: ast.AST) -> bool:
    """G/M constants in this function. Nested functions and the docstring are skipped."""
    body = list(getattr(fn, "body", []))
    if body and _is_docstring(body[0]):
        body = body[1:]

    def visit(node):
        if _skip_nested(node):
            return
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for token in node.value.replace(",", " ").split():
                if _COMMAND.match(token.strip("()")):
                    yield True
        for child in ast.iter_child_nodes(node):
            yield from visit(child)

    for stmt in body:
        if any(visit(stmt)):
            return True
    return False


def _is_docstring(stmt: ast.AST) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


@dataclass
class Facts:
    program: list[tuple[int, str, str]] = field(default_factory=list)
    authority: list[tuple[int, str, str | None]] = field(default_factory=list)
    delegates: list[tuple[int, str]] = field(default_factory=list)
    inline: bool = False

    @property
    def emits(self) -> bool:
        return bool(self.program) or self.inline


def _assigned_program_line(fn: ast.AST) -> int | None:
    """Line where a handler stores a wrapped ``program`` string."""
    def visit(node):
        if _skip_nested(node):
            return
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "program":
                    yield node.lineno
        for child in ast.iter_child_nodes(node):
            yield from visit(child)

    for stmt in getattr(fn, "body", []):
        for lineno in visit(stmt):
            return lineno
    return None


def facts_of(fn: ast.AST | None, source: str) -> Facts:
    facts = Facts()
    if fn is None:
        return facts
    aliases = alias_map(fn)
    for call in iter_calls(fn):
        raw = call_name(call)
        name = aliases.get(raw, raw)
        owner = call_owner(call)
        if name in _AUTHORITY:
            facts.authority.append((call.lineno, _AUTHORITY[name], authority_key(call, name)))
        elif name in _DELEGATES:
            facts.delegates.append((call.lineno, name))
        elif _is_program_call(name, owner):
            facts.program.append((call.lineno, name, owner))
    if "body.gcode" in source and _FILENAME.search(source):
        assigned = _assigned_program_line(fn)
        if assigned is not None:
            facts.program.append((assigned, "postprocess_wrap", ""))
    facts.inline = inline_commands(fn) and "gcode_lines" in source
    return facts
