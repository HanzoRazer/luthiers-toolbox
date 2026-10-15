#!/usr/bin/env python3
"""Reachability checks for "migrated / restored / wired / complete" claims. Read-only.

A claim that a file was integrated is checked five ways, separately, because
each one has failed on its own in this repository's history:

  file_present      the path exists in the tree
  import_reachable  some other application module imports it
  route_reachable   a router module registered in ``router_registry/manifests``
                    reaches it within ``--hops`` import hops (or is it)
  ui_consumer       for a backend file: a client source file contains one of
                    the reaching routers' URL prefixes; for a client file: the
                    client router (``src/router``) reaches it through imports
  test_exercises    a test module imports it (backend) or names its route prefix

``test_non_vacuous`` is never decided here -- it needs a human reading the
assertions -- so the column is always ``NOT_ASSESSED`` from this tool.

Method limits. Labels are mechanical and need human adjudication:
  - imports are a syntactic AST graph (static ``import`` / ``from`` only);
    dynamic imports and string-loaded modules are invisible, so
    import/route reachability can UNDER-count;
  - ``ui_consumer`` is a plain substring search for URL prefixes in client
    text, so it can OVER-count (a prefix in a comment or an unrelated string
    counts as a caller).

Proof class. Only a missing path (``FALSE_MIGRATION_CLAIM``) or a present
non-code artefact (``VERIFIED_PRESENT``) is ``MECHANICALLY_VERIFIED``. Every
other label, ``VERIFIED_STRUCTURAL`` included, rests on the limits above and is
a ``HEURISTIC_CANDIDATE`` until a human adjudicates it.

Directory walks are sorted, so output is byte-stable across filesystems.

Usage:
    python scripts/investigations/march_2026_claim_reachability.py --root . \
        --claims claims.csv --out results.csv
claims.csv columns: claim_id,source,claim_text,claimed_state,claimed_commit,primary_path
"""
from __future__ import annotations

import argparse
import ast
import csv
import re
import sys
from collections import deque
from pathlib import Path

API = Path("services/api")
APP = API / "app"
TESTS = API / "tests"
CLIENT_SRC = Path("packages/client/src")
MANIFESTS = APP / "router_registry" / "manifests"

_SPEC = re.compile(r'module="(app\.[\w.]+)"\s*,\s*prefix="([^"]*)"', re.S)
_DECO = re.compile(r'@router\.(?:get|post|put|patch|delete)\(\s*["\']([^"\']*)["\']')
_ROUTER_PREFIX = re.compile(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']*)["\']')
_CLIENT_IMPORT = re.compile(r"""(?:from\s+|import\s*\(\s*|import\s+)['"]([^'"]+)['"]""")


def module_of(path: Path) -> str:
    rel = path.relative_to(API).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def py_imports(path: Path, module: str) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    pkg = module.rsplit(".", 1)[0] if not path.name == "__init__.py" else module
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                anchor = pkg.split(".")
                anchor = anchor[: len(anchor) - (node.level - 1)] if node.level > 1 else anchor
                base = ".".join(anchor + ([base] if base else []))
            out.add(base)
            out.update(f"{base}.{a.name}" for a in node.names)
    return out


class Index:
    def __init__(self, root: Path):
        self.root = root
        self.py_mods: dict[str, Path] = {}
        self.importers: dict[str, set[str]] = {}
        for p in sorted((root / APP).rglob("*.py")):
            self.py_mods[module_of(p.relative_to(root))] = p
        for mod, p in self.py_mods.items():
            for imp in py_imports(p, mod):
                self.importers.setdefault(imp, set()).add(mod)
        self.routers: dict[str, str] = {}
        for mf in sorted((root / MANIFESTS).glob("*.py")):
            for mod, prefix in _SPEC.findall(mf.read_text(encoding="utf-8")):
                self.routers[mod] = prefix
        self.test_imports: dict[str, set[str]] = {}
        self.test_text: dict[str, str] = {}
        for p in sorted((root / TESTS).rglob("test_*.py")):
            rel = p.relative_to(root).as_posix()
            self.test_text[rel] = p.read_text(encoding="utf-8", errors="replace")
            for imp in py_imports(p, "tests"):
                self.test_imports.setdefault(imp, set()).add(rel)
        self.client_files = [p for p in sorted((root / CLIENT_SRC).rglob("*")) if p.suffix in (".ts", ".vue", ".js")]
        self.client_text = {p: p.read_text(encoding="utf-8", errors="replace") for p in self.client_files}
        self.client_importers: dict[Path, set[Path]] = {}
        for p, text in self.client_text.items():
            for spec in _CLIENT_IMPORT.findall(text):
                target = self._resolve_client(p, spec)
                if target:
                    self.client_importers.setdefault(target, set()).add(p)

    def _resolve_client(self, src: Path, spec: str) -> Path | None:
        if spec.startswith("@/"):
            base = self.root / CLIENT_SRC / spec[2:]
        elif spec.startswith("."):
            base = (src.parent / spec)
        else:
            return None
        base = Path(base)
        for cand in (base, *(base.with_name(base.name + s) for s in (".ts", ".vue", ".js")),
                     base / "index.ts", base / "index.js"):
            if cand.is_file():
                return cand.resolve()
        return None

    # -- backend -------------------------------------------------------------
    def importers_of(self, mod: str) -> set[str]:
        hits = set(self.importers.get(mod, set()))
        # "from pkg import mod" is recorded as pkg.mod -> already covered
        return {h for h in hits if h != mod}

    def reach_set(self, mod: str, hops: int) -> set[str]:
        """``mod`` plus every module that imports it within ``hops``."""
        seen, queue = {mod}, deque([(mod, 0)])
        while queue:
            cur, d = queue.popleft()
            if d == hops:
                continue
            for nxt in self.importers_of(cur):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, d + 1))
        return seen

    def reaching_routers(self, mod: str, hops: int) -> list[str]:
        """Manifest-registered modules in the reach set (a package counts for its members)."""
        reach = self.reach_set(mod, hops)
        return sorted(r for r in self.routers if r in reach or any(m.startswith(r + ".") for m in reach))

    def route_paths(self, mod: str, hops: int) -> list[str]:
        """Full URL paths of every endpoint decorated in a module of the reach set.

        Prefix = the manifest prefix of the registered module (or its package) plus
        any ``APIRouter(prefix=...)`` in the module itself. A bare prefix is never
        used on its own -- ``/api/export`` matches unrelated client code.
        """
        # Only the NEAREST endpoint-defining layer: a package that imports a whole
        # family of routers must not lend every sibling's routes to the target.
        layer: list[tuple[str, str]] = []
        frontier, seen = {mod}, {mod}
        for _ in range(hops + 1):
            for m in sorted(frontier):
                p = self.py_mods.get(m)
                if p is not None:
                    text = p.read_text(encoding="utf-8", errors="replace")
                    if _DECO.search(text):
                        layer.append((m, text))
            if layer:
                break
            frontier = {n for f in frontier for n in self.importers_of(f)} - seen
            seen |= frontier
        paths: set[str] = set()
        for m, text in layer:
            decos = _DECO.findall(text)
            own = _ROUTER_PREFIX.search(text)
            manifest = next((self.routers[r] for r in self.routers if m == r or m.startswith(r + ".")), "")
            prefix = manifest + (own.group(1) if own else "")
            for d in decos:
                full = (prefix + d).split("{", 1)[0].rstrip("/")
                if full.count("/") >= 2 and len(full) >= 8:
                    paths.add(full)
        return sorted(paths)

    # -- client --------------------------------------------------------------
    def client_reached_from_router(self, target: Path, hops: int = 8) -> bool:
        router_dir = (self.root / CLIENT_SRC / "router").resolve()
        seen, queue = {target}, deque([(target, 0)])
        while queue:
            cur, d = queue.popleft()
            if router_dir in cur.parents or cur.name in ("main.ts", "App.vue"):
                return True
            if d == hops:
                continue
            for nxt in self.client_importers.get(cur, set()):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, d + 1))
        return False


def check(idx: Index, rel: str, hops: int) -> dict:
    path = idx.root / rel
    res = {"file_present": "PASS" if path.exists() else "FAIL"}
    if not path.exists():
        return {**res, "import_reachable": "FAIL", "route_reachable": "FAIL", "ui_consumer": "FAIL",
                "test_exercises": "FAIL", "evidence": "path absent from tree"}
    if path.is_dir():
        files = [p for p in sorted(path.rglob("*")) if p.suffix in (".py", ".ts", ".vue")]
        sub = [check(idx, p.relative_to(idx.root).as_posix(), hops) for p in files]
        agg = {k: ("PASS" if any(s[k] == "PASS" for s in sub) else "FAIL")
               for k in ("import_reachable", "route_reachable", "ui_consumer", "test_exercises")}
        return {**res, **agg, "evidence": f"directory: {len(files)} source files, any-member aggregation"}
    if path.suffix == ".py" and rel.startswith(APP.as_posix()):
        mod = module_of(Path(rel))
        importers = sorted(idx.importers_of(mod))
        routers = idx.reaching_routers(mod, hops)
        paths = idx.route_paths(mod, hops) if routers else []
        # Clients often prepend an API base: also accept the path without "/api".
        needles = paths + [u[4:] for u in paths if u.startswith("/api/") and u[4:].count("/") >= 2]
        named = [p for p, t in idx.client_text.items() if any(u in t for u in needles)]
        ui = [p.relative_to(idx.root).as_posix() for p in named if idx.client_reached_from_router(p.resolve())]
        stranded_ui = [p.relative_to(idx.root).as_posix() for p in named
                       if p.relative_to(idx.root).as_posix() not in ui]
        tests = sorted(idx.test_imports.get(mod, set()) |
                       {t for t, txt in idx.test_text.items() if any(u in txt for u in paths)})
        return {**res,
                "import_reachable": "PASS" if importers or mod in idx.routers else "FAIL",
                "route_reachable": "PASS" if routers else "FAIL",
                "ui_consumer": "PASS" if ui else "FAIL",
                "test_exercises": "PASS" if tests else "FAIL",
                "evidence": f"importers={importers[:3]} routers={routers[:2]} paths={paths[:3]} "
                            f"ui={ui[:2]} unreachable_ui={stranded_ui[:2]} tests={tests[:2]}"}
    if path.suffix in (".ts", ".vue", ".js"):
        target = path.resolve()
        importers = sorted(p.relative_to(idx.root).as_posix() for p in idx.client_importers.get(target, set()))
        reached = idx.client_reached_from_router(target)
        return {**res,
                "import_reachable": "PASS" if importers else "FAIL",
                "route_reachable": "PASS" if reached else "FAIL",
                "ui_consumer": "PASS" if reached else "FAIL",
                "test_exercises": "NOT_ASSESSED",
                "evidence": f"client importers={importers[:3]} reached_from_client_router={reached}"}
    return {**res, "import_reachable": "N/A", "route_reachable": "N/A", "ui_consumer": "N/A",
            "test_exercises": "N/A", "evidence": "non-code artefact"}


def classify(r: dict) -> str:
    if r["file_present"] == "FAIL":
        return "FALSE_MIGRATION_CLAIM"
    if r["import_reachable"] == "N/A":
        return "VERIFIED_PRESENT"
    if r["route_reachable"] == "FAIL" and r["import_reachable"] == "FAIL":
        return "STRANDED_IMPLEMENTATION"
    if r["route_reachable"] == "FAIL" or r["ui_consumer"] == "FAIL":
        return "PARTIAL_MIGRATION"
    return "VERIFIED_STRUCTURAL"


def proof(classification: str) -> tuple[str, str]:
    """(proof_class, proof_method) for a classification."""
    if classification == "FALSE_MIGRATION_CLAIM":
        return "MECHANICALLY_VERIFIED", "path absent from the tree"
    if classification == "VERIFIED_PRESENT":
        return "MECHANICALLY_VERIFIED", "path present (non-code artefact)"
    return "HEURISTIC_CANDIDATE", "static import graph + URL-substring UI search"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--claims", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--hops", type=int, default=4)
    args = ap.parse_args(argv)
    idx = Index(args.root.resolve())
    rows = list(csv.DictReader(args.claims.open(encoding="utf-8", newline="")))
    if not rows:
        print("no claims", file=sys.stderr)
        return 2
    fields = ["claim_id", "source", "claim_text", "claimed_state", "claimed_commit", "primary_path",
              "file_present", "import_reachable", "route_reachable", "ui_consumer", "test_exercises",
              "test_non_vacuous", "classification", "proof_class", "proof_method", "evidence"]
    with args.out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for c in rows:
            r = check(idx, c["primary_path"], args.hops)
            label = classify(r)
            proof_class, method = proof(label)
            w.writerow({**{k: c.get(k, "") for k in fields[:6]}, **r, "test_non_vacuous": "NOT_ASSESSED",
                        "classification": label, "proof_class": proof_class, "proof_method": method})
    return 0


if __name__ == "__main__":
    sys.exit(main())
