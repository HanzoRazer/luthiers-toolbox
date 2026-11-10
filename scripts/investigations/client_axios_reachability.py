#!/usr/bin/env python3
"""Evidence-only reachability scan for client Axios imports.

The scan reports facts. It does not decide deletion, migration, or preservation.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_EXTENSIONS = (".ts", ".tsx", ".vue", ".js", ".mjs", ".cjs")
_IMPORT_FROM = re.compile(
    r"""^[ \t]*import\s+(?P<body>[\s\S]*?)\s+from\s+['\"](?P<spec>[^'\"]+)['\"]\s*;?\s*$""",
    re.M,
)
_IMPORT_SIDE = re.compile(r"""^[ \t]*import\s+['\"](?P<spec>[^'\"]+)['\"]\s*;?\s*$""", re.M)
_EXPORT_FROM = re.compile(
    r"""^[ \t]*export\s+(?P<kind>type\s+)?(?P<body>\{[\s\S]*?\}|\*(?:\s+as\s+\w+)?)"""
    r"""\s+from\s+['\"](?P<spec>[^'\"]+)['\"]\s*;?\s*$""",
    re.M,
)
_LINE_COMMENT = re.compile(r"""(?m)//.*?$""")
_BLOCK_COMMENT = re.compile(r"""/\*.*?\*/""", re.S)
_REQUIRE_AXIOS = re.compile(r"""(?m)^[ \t]*(?:const|let|var)\s+\w+\s*=\s*require\(\s*['\"]axios['\"]\s*\)""")
_LOCAL_VALUE = re.compile(
    r"^[ \t]*export\s+(?:declare\s+)?(?:async\s+)?(?:function\*?|class|const|let|var|enum)\s+(\w+)",
    re.M,
)
_LOCAL_DEFAULT = re.compile(r"^[ \t]*export\s+default\b", re.M)
_LOCAL_BRACE = re.compile(r"^[ \t]*export\s+\{([^}]+)\}\s*;?\s*$", re.M)
_SCRIPT_SETUP = re.compile(r"<script\b[^>]*\bsetup\b", re.I)


@dataclass
class Edge:
    specifier: str
    names: frozenset[str] | None
    type_only: bool
    namespace: bool
    dynamic: bool
    resolved: str | None = None
    outside_src: bool = False


@dataclass
class Module:
    path: str
    imports: list[Edge] = field(default_factory=list)
    local_exports: set[str] = field(default_factory=set)
    has_default: bool = False
    # original specifier, resolved path, public->source map or None for export *, type_only
    reexports: list[tuple[str, str | None, dict[str, str] | None, bool]] = field(default_factory=list)


def _strip_comments(text: str) -> str:
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", text))


def _script_text(path: Path, text: str) -> str:
    if path.suffix != ".vue":
        return text
    parts = re.findall(r"<script\b[^>]*>(.*?)</script>", text, flags=re.S | re.I)
    return "\n".join(parts)


def _join_statements(text: str) -> str:
    lines: list[str] = []
    buf: list[str] = []
    depth = 0
    for line in text.splitlines():
        buf.append(line)
        depth += line.count("{") + line.count("(") - line.count("}") - line.count(")")
        if depth <= 0:
            lines.append(" ".join(part.strip() for part in buf))
            buf = []
            depth = 0
    if buf:
        lines.append(" ".join(part.strip() for part in buf))
    return "\n".join(lines)


def _import_names(body: str) -> tuple[frozenset[str] | None, bool, bool]:
    body = body.strip()
    if body.startswith("type "):
        names, _type_only, namespace = _import_names(body[5:])
        return names, True, namespace
    if body.startswith("*"):
        return None, False, True
    type_only = True
    names: set[str] = set()
    default, _, named = body.partition("{") if "{" in body else (body, "", "")
    if named:
        named = named.rsplit("}", 1)[0]
    default = default.replace(",", " ").strip()
    if default:
        names.add("default")
        type_only = False
    for piece in named.split(","):
        piece = piece.strip()
        if not piece:
            continue
        is_type = piece.startswith("type ")
        piece = piece[5:].strip() if is_type else piece
        original = piece.split(" as ")[0].strip()
        if original:
            names.add(original)
        type_only = type_only and is_type
    return frozenset(names), type_only and "default" not in names, False


def _export_map(body: str) -> dict[str, str] | None:
    body = body.strip()
    if body.startswith("*"):
        return None
    mapping: dict[str, str] = {}
    for piece in body.strip()[1:-1].split(","):
        piece = piece.strip()
        if not piece:
            continue
        if piece.startswith("type "):
            piece = piece[5:].strip()
        source, _, alias = piece.partition(" as ")
        source = source.strip()
        public = alias.strip() or source
        if public:
            mapping[public] = source or public
    return mapping


def _dynamic_specs(text: str) -> list[str]:
    specs: list[str] = []
    quote = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "'\"`":
            quote = ch
            i += 1
            continue
        if text.startswith("import(", i):
            j = i + len("import(")
            while j < len(text) and text[j].isspace():
                j += 1
            if j < len(text) and text[j] in "'\"":
                end = text.find(text[j], j + 1)
                if end != -1:
                    specs.append(text[j + 1:end])
            i = j
            continue
        i += 1
    return specs


def _local_export_names(joined: str) -> set[str]:
    names = {match.group(1) for match in _LOCAL_VALUE.finditer(joined)}
    for match in _LOCAL_BRACE.finditer(joined):
        for piece in match.group(1).split(","):
            piece = piece.strip()
            if not piece or piece.startswith("type "):
                continue
            public = piece.split(" as ")[-1].strip()
            if public:
                names.add(public)
    return names


def parse_module(path: Path, src: Path) -> Module:
    raw = path.read_text(encoding="utf-8")
    script = _strip_comments(_script_text(path, raw))
    joined = _join_statements(script)
    module = Module(path=path.relative_to(src).as_posix())
    module.local_exports = _local_export_names(joined)
    module.has_default = _LOCAL_DEFAULT.search(joined) is not None or (
        path.suffix == ".vue" and _SCRIPT_SETUP.search(raw) is not None
    )
    for match in _IMPORT_FROM.finditer(joined):
        names, type_only, namespace = _import_names(match.group("body"))
        module.imports.append(Edge(match.group("spec"), names, type_only, namespace, False))
    for match in _IMPORT_SIDE.finditer(joined):
        module.imports.append(Edge(match.group("spec"), None, False, False, False))
    for match in _EXPORT_FROM.finditer(joined):
        module.reexports.append((match.group("spec"), match.group("spec"), _export_map(match.group("body")), bool(match.group("kind"))))
    for spec in _dynamic_specs(script):
        module.imports.append(Edge(spec, None, False, False, True))
    return module


def _candidate(base: Path) -> Path | None:
    if base.is_file():
        return base
    options = [Path(str(base) + ext) for ext in _EXTENSIONS]
    options.extend(base / f"index{ext}" for ext in _EXTENSIONS)
    for option in options:
        if option.is_file():
            return option
    return None


def resolve_specifier(importer: Path, specifier: str, src: Path) -> Path | None:
    spec = specifier.split("?", 1)[0]
    if spec.startswith("@/"):
        return _candidate(src / spec[2:])
    if spec.startswith("."):
        return _candidate((importer.parent / spec).resolve())
    return None


def _is_local(spec: str) -> bool:
    return spec.startswith((".", "@/"))


def _rel_or_outside(resolved: Path | None, src: Path) -> tuple[str | None, bool]:
    if resolved is None:
        return None, False
    try:
        return resolved.relative_to(src).as_posix(), False
    except ValueError:
        return None, True


def load_modules(src: Path) -> dict[str, Module]:
    modules: dict[str, Module] = {}
    for pattern in ("*.ts", "*.tsx", "*.vue", "*.js"):
        for path in src.rglob(pattern):
            if "node_modules" in path.parts:
                continue
            module = parse_module(path, src)
            modules[module.path] = module
    for module in modules.values():
        importer = src / module.path
        for edge in module.imports:
            resolved = resolve_specifier(importer, edge.specifier, src)
            edge.resolved, edge.outside_src = _rel_or_outside(resolved, src)
        resolved_reexports: list[tuple[str, str | None, dict[str, str] | None, bool]] = []
        for spec, _placeholder, mapping, type_only in module.reexports:
            resolved = resolve_specifier(importer, spec, src)
            rel, _outside = _rel_or_outside(resolved, src)
            resolved_reexports.append((spec, rel, mapping, type_only))
        module.reexports = resolved_reexports
    return modules


def imports_axios(path: Path, src: Path) -> bool:
    module = parse_module(path, src)
    if any(edge.specifier == "axios" for edge in module.imports):
        return True
    script = _strip_comments(_script_text(path, path.read_text(encoding="utf-8")))
    return _REQUIRE_AXIOS.search(script) is not None


def axios_importers(src: Path) -> list[str]:
    found: list[str] = []
    for pattern in ("*.ts", "*.tsx", "*.vue", "*.js"):
        for path in src.rglob(pattern):
            if "node_modules" in path.parts:
                continue
            if imports_axios(path, src):
                found.append(path.relative_to(src).as_posix())
    return sorted(found)


def export_providers(
    modules: dict[str, Module],
    path: str,
    name: str,
    seen: frozenset[str],
) -> list[str]:
    if path in seen or path not in modules:
        return []
    module = modules[path]
    next_seen = seen | {path}
    found: list[str] = []
    if (name == "default" and module.has_default) or name in module.local_exports:
        found.append(path)
    for _spec, resolved, mapping, type_only in module.reexports:
        if type_only or resolved is None:
            continue
        if mapping is None:
            if name == "default":
                continue
            found.extend(export_providers(modules, resolved, name, next_seen))
        elif name in mapping:
            found.extend(export_providers(modules, resolved, mapping[name], next_seen))
    return sorted(set(found))


def _walk(
    modules: dict[str, Module],
    entries: list[str],
    *,
    binding: bool,
) -> tuple[set[str], list[dict[str, str]]]:
    reached: set[str] = set()
    ambiguous: list[dict[str, str]] = []
    seen: set[tuple[str, tuple[str, ...] | None]] = set()
    stack: list[tuple[str, frozenset[str] | None]] = [(entry, None) for entry in entries if entry in modules]

    def push(path: str | None, names: frozenset[str] | None) -> None:
        if path is None:
            return
        key = (path, None if names is None else tuple(sorted(names)))
        if key in seen:
            return
        stack.append((path, names))

    while stack:
        path, names = stack.pop()
        key = (path, None if names is None else tuple(sorted(names)))
        if key in seen or path not in modules:
            continue
        seen.add(key)
        reached.add(path)
        module = modules[path]
        local_or_unknown = names is None
        if names is not None:
            for demanded in sorted(names):
                providers = [item for item in export_providers(modules, path, demanded, frozenset()) if item != path]
                if len(providers) > 1:
                    ambiguous.append({
                        "from": path,
                        "name": demanded,
                        "providers": ",".join(providers),
                    })
                if providers:
                    for provider in providers:
                        push(provider, frozenset({demanded}))
                else:
                    local_or_unknown = True
        if local_or_unknown or not binding:
            for edge in module.imports:
                if edge.type_only:
                    continue
                push(edge.resolved, None if edge.namespace or edge.names is None else edge.names)
        if (not binding) or names is None:
            for _spec, resolved, _mapping, type_only in module.reexports:
                if not type_only:
                    push(resolved, None)
    ambiguous.sort(key=lambda item: (item["from"], item["name"], item["providers"]))
    return reached, ambiguous


def unresolved_imports(modules: dict[str, Module]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for module in modules.values():
        importer_specs = [(edge.specifier, edge.resolved) for edge in module.imports]
        importer_specs.extend((spec, resolved) for spec, resolved, _mapping, _type_only in module.reexports)
        outside = {edge.specifier for edge in module.imports if edge.outside_src}
        for specifier, resolved in importer_specs:
            if specifier and _is_local(specifier) and resolved is None and specifier not in outside:
                found.append({"from": module.path, "specifier": specifier})
    deduped = {(item["from"], item["specifier"]): item for item in found}
    return [deduped[key] for key in sorted(deduped)]


def ambiguous_aliases(modules: dict[str, Module]) -> list[dict[str, str]]:
    found = [
        {"from": module.path, "specifier": edge.specifier}
        for module in modules.values()
        for edge in module.imports
        if edge.namespace and _is_local(edge.specifier)
    ]
    found.sort(key=lambda item: (item["from"], item["specifier"]))
    return found


def analyze(src: Path, entries: list[str]) -> dict[str, object]:
    modules = load_modules(src)
    importers = axios_importers(src)
    binding, binding_ambiguous = _walk(modules, entries, binding=True)
    evaluated, _evaluated_ambiguous = _walk(modules, entries, binding=False)
    rows = [
        {
            "binding_reachable": rel in binding,
            "evaluated_reachable": rel in evaluated,
            "path": rel,
        }
        for rel in importers
    ]
    return {
        "ambiguous_aliases": ambiguous_aliases(modules),
        "ambiguous_exports": binding_ambiguous,
        "axios_importers": importers,
        "entries": sorted(entries),
        "importers": rows,
        "unresolved_imports": unresolved_imports(modules),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report client Axios import reachability.")
    parser.add_argument("--src", type=Path, required=True)
    parser.add_argument("--entry", action="append", default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args(argv)
    src = args.src.resolve()
    payload = analyze(src, args.entry or ["main.ts", "App.vue", "router/index.ts"])
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["path", "binding_reachable", "evaluated_reachable"])
            writer.writeheader()
            for row in payload["importers"]:
                assert isinstance(row, dict)
                writer.writerow(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
