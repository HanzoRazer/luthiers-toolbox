"""G2-MANUFACTURING-SPINE-001 — client consumer tracer (evidence method, not product).

Answers, for each registered manufacturing route: which client source files
reference it, and is each such file reachable from the application entry
(``src/main.ts``) through static or dynamic imports?

This is the *mechanical* half of CONSUMED. A reachable reference is necessary
but not sufficient: D5b also requires that the result is actually used
(rendered / persisted / downloaded). That half is adjudicated by reading each
call site and is recorded separately in the registry evidence.

Deliberate limits, stated so no reader over-trusts the output:

* URL matching is textual, at two strengths. ``exact`` needles are the full
  route path (with and without ``/api``). ``tail`` needles are the route's
  trailing segments, added because clients build URLs from a base variable
  (``${API_BASE_N17}/polygon_offset.nc``) and never spell the full path. A tail
  hit is a *candidate* only and must be adjudicated at the call site.
  A URL assembled from fragments that never appear together
  (``base + op + '/gcode'``) is still not matched. Such cases surface as NO
  reference, which the registry records as UNKNOWN, never as NO.
* Reachability is import reachability. A reachable module is loaded by the app;
  whether a given function in it is ever invoked is a call-site question.
* Components registered globally by name (not imported) are not modelled.

Usage::

    python trace_client_consumers.py <repo_root> <registry.json> <out.json>
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import deque

EXTS = (".ts", ".vue", ".js", ".tsx")
IMPORT_RE = re.compile(
    r"""(?:import|export)\s+(?:[^'"`;]*?\sfrom\s+)?['"]([^'"]+)['"]"""
    r"""|import\(\s*['"]([^'"]+)['"]\s*\)"""
)
SCRIPT_RE = re.compile(r"<script[^>]*>(.*?)</script>", re.S)


def is_test(rel: str) -> bool:
    return "__tests__" in rel or ".spec." in rel or ".test." in rel


def read_source(path: str) -> str:
    text = open(path, encoding="utf-8", errors="replace").read()
    if path.endswith(".vue"):
        return "\n".join(SCRIPT_RE.findall(text))
    return text


def resolve(spec: str, from_file: str, src: str):
    if spec.startswith("@/"):
        base = os.path.join(src, spec[2:])
    elif spec.startswith("."):
        base = os.path.normpath(os.path.join(os.path.dirname(from_file), spec))
    else:
        return None  # bare package import
    cands = [base] + [base + e for e in EXTS] + [os.path.join(base, "index" + e) for e in EXTS]
    for c in cands:
        if os.path.isfile(c):
            return os.path.normpath(c)
    return None


def main() -> int:
    repo, registry_path, out_path = sys.argv[1:4]
    src = os.path.join(repo, "packages", "client", "src")
    files = []
    for root, _dirs, names in os.walk(src):
        for n in names:
            if n.endswith(EXTS):
                p = os.path.normpath(os.path.join(root, n))
                if not is_test(os.path.relpath(p, repo)):
                    files.append(p)

    graph = {}
    raw = {}
    for f in files:
        body = read_source(f)
        raw[f] = open(f, encoding="utf-8", errors="replace").read()
        deps = set()
        for a, b in IMPORT_RE.findall(body):
            r = resolve(a or b, f, src)
            if r:
                deps.add(r)
        graph[f] = deps

    entry = os.path.normpath(os.path.join(src, "main.ts"))
    parent = {entry: None}
    queue = deque([entry])
    while queue:
        cur = queue.popleft()
        for dep in graph.get(cur, ()):
            if dep not in parent:
                parent[dep] = cur
                queue.append(dep)

    def chain(f):
        out = []
        while f is not None:
            out.append(os.path.relpath(f, repo).replace("\\", "/"))
            f = parent.get(f)
        return list(reversed(out))

    registry = json.load(open(registry_path, encoding="utf-8"))
    result = {
        "entry": os.path.relpath(entry, repo).replace("\\", "/"),
        "source_files_scanned": len(files),
        "reachable_from_entry": len(parent),
        "capabilities": [],
    }
    def tail_needles(path: str):
        segs = [s for s in path.split("/") if s]
        out = set()
        if len(segs) >= 2:
            out.add("/" + "/".join(segs[-2:]))
        last = segs[-1] if segs else ""
        # A lone last segment is only distinctive enough when it is not a
        # generic verb like "gcode" or "download".
        if last and ("." in last or "_" in last or len(last) >= 12):
            out.add("/" + last)
        return out

    for cap in registry["capabilities"]:
        needles = {}
        for rt in cap.get("routes") or []:
            p = rt["path"]
            needles[p] = "exact"
            if p.startswith("/api/"):
                needles[p[len("/api"):]] = "exact"
        for rt in cap.get("routes") or []:
            for t in tail_needles(rt["path"]):
                needles.setdefault(t, "tail")
        hits = []
        seen = set()
        for f in files:
            text = raw[f]
            for needle in sorted(needles, key=len, reverse=True):
                for m in re.finditer(re.escape(needle) + r"(?![A-Za-z0-9_])", text):
                    line = text.count("\n", 0, m.start()) + 1
                    key = (f, line)
                    if key in seen:  # a longer needle already claimed this line
                        continue
                    seen.add(key)
                    reachable = f in parent
                    hits.append({
                        "file": os.path.relpath(f, repo).replace("\\", "/"),
                        "line": line,
                        "needle": needle,
                        "match_kind": needles[needle],
                        "reachable_from_entry": reachable,
                        "import_chain": chain(f) if reachable else None,
                    })
        result["capabilities"].append({
            "capability_id": cap["capability_id"],
            "needles": {k: needles[k] for k in sorted(needles)},
            "reference_count": len(hits),
            "reachable_reference_count": sum(h["reachable_from_entry"] for h in hits),
            "references": hits,
        })
    result["reachable_files"] = sorted(
        os.path.relpath(f, repo).replace("\\", "/") for f in parent
    )

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    print(f"scanned={len(files)} reachable={len(parent)} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
