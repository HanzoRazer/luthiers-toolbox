"""Manufacturing-output inventory check. Static route metadata only.

Does not call generators, send programs, or import physical senders.
Production routers must not import this module.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from app.ci.manufacturing_output_classify import (
    BASE_SHA,
    ENUMS,
    HIGH_SIGNAL_MIN,
    HISTORICAL_CANDIDATES,
    HISTORICAL_HANDLERS,
    HISTORICAL_HIGH_SIGNAL,
    ROW_FIELDS,
    classify_route,
)
from app.ci.manufacturing_output_walk import naive_walk, reconcile, walk_live

__all__ = ["BASE_SHA", "build_document", "check_inventory", "main"]


def discover_candidates(routes) -> list[dict]:
    live, unresolved = walk_live(routes)
    if unresolved:
        raise RuntimeError(f"unresolved route objects: {len(unresolved)}")
    rows = []
    for route in live:
        row = classify_route(route)
        if row is not None:
            rows.append(row)
    rows.sort(key=lambda row: (row["method"], row["path"], row["handler"]))
    return rows


def _public(rows: list[dict]) -> list[dict]:
    return [{field: row[field] for field in ROW_FIELDS} for row in rows]


def _reconciliation(candidate_count: int, handler_count: int, high: int) -> str:
    return (
        f"Historical audit baseline is {HISTORICAL_CANDIDATES} broad candidates, "
        f"{HISTORICAL_HANDLERS} handler identities, and {HISTORICAL_HIGH_SIGNAL} "
        f"candidates with at least three signals. This tree recomputes "
        f"{candidate_count} live candidates, {handler_count} handler identities, and "
        f"{high} high-signal rows. The audit scanner is not in the repository. "
        "The difference is the live signal census at the pinned SHA, not a forced "
        "equal to 420. Five optional routers load only when Pillow, OpenCV, and "
        "Markdown are installed; this count includes them. HEAD and OPTIONS aliases "
        "are not separate candidates. A path token alone does not confirm emission."
    )


def build_document(rows: list[dict]) -> dict:
    public = _public(rows)
    high = sum(1 for row in rows if len(row.get("_signals", [])) >= HIGH_SIGNAL_MIN)
    handlers = {row["handler"] for row in public}
    return {
        "base_sha": BASE_SHA,
        "historical_audit": {
            "broad_candidates": HISTORICAL_CANDIDATES,
            "handler_identities": HISTORICAL_HANDLERS,
            "high_signal": HISTORICAL_HIGH_SIGNAL,
        },
        "current": {
            "candidates": len(public),
            "handler_identities": len(handlers),
            "high_signal": high,
        },
        "reconciliation": _reconciliation(len(public), len(handlers), high),
        "rows": public,
    }


def _schema_path() -> Path:
    return Path(__file__).with_name("manufacturing_output_inventory.schema.json")


def _row_problems(index: int, row: dict, seen: set[tuple]) -> list[str]:
    problems: list[str] = []
    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    required = schema["properties"]["rows"]["items"]["required"]
    for field in required:
        if field not in row:
            problems.append(f"row {index} missing {field}")
    for field, allowed in ENUMS.items():
        if field in row and row[field] not in allowed:
            problems.append(f"row {index} bad {field}")
    if row.get("classification") == "CONFIRMED_EMITTER" and not row.get("evidence"):
        problems.append(f"row {index} emitter without evidence")
    if row.get("containment") == "FAIL_CLOSED" and row.get("authority_order") != "before_generation":
        problems.append(f"row {index} fail-closed without a prior authority call")
    if _readiness_key_missing(row):
        problems.append(f"row {index} readiness fail-closed without a key")
    if row.get("classification") == "UNEXAMINED" and re.search(r"\bsafe\b", str(row.get("notes", "")), re.I):
        problems.append(f"row {index} calls UNEXAMINED safe")
    identity = (row.get("method"), row.get("path"), row.get("handler"))
    if identity in seen:
        problems.append(f"duplicate {identity}")
    seen.add(identity)
    return problems


def _readiness_key_missing(row: dict) -> bool:
    return (
        row.get("containment") == "FAIL_CLOSED"
        and row.get("authority_layer") == "readiness"
        and not row.get("authority_key")
    )


def validate_document(document: dict) -> list[str]:
    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    problems: list[str] = []
    for field in schema["required"]:
        if field not in document:
            problems.append(f"missing document field {field}")
    seen: set[tuple] = set()
    for index, row in enumerate(document.get("rows", [])):
        problems.extend(_row_problems(index, row, seen))
    return problems


def _snapshot_problems(document: dict, discovered: list[dict]) -> list[str]:
    fresh = build_document(discovered)
    problems: list[str] = []
    if document.get("base_sha") != BASE_SHA:
        problems.append("base_sha is not the pinned CF-4 merge")
    if document.get("current") != fresh["current"]:
        problems.append(f"current counts drifted: {document.get('current')} != {fresh['current']}")
    if document.get("reconciliation") != fresh["reconciliation"]:
        problems.append("reconciliation text drifted")
    declared = {
        (row["method"], row["path"], row["handler"]): row
        for row in document.get("rows", [])
    }
    found = {(row["method"], row["path"], row["handler"]): row for row in fresh["rows"]}
    for key in sorted(found):
        if key not in declared:
            problems.append(f"missing candidate {key[0]} {key[1]} {key[2]}")
            continue
        for field in ROW_FIELDS:
            if declared[key].get(field) != found[key].get(field):
                problems.append(f"drift {key[0]} {key[1]} {field}")
    for key in sorted(declared):
        if key not in found:
            problems.append(f"stale row {key[0]} {key[1]} {key[2]}")
    return problems


def _readiness_problems(document: dict) -> list[str]:
    from app.cam.generator_readiness import GENERATOR_READINESS

    problems = []
    for row in document.get("rows", []):
        key = row.get("authority_key")
        if row.get("authority_layer") == "readiness" and key and key not in GENERATOR_READINESS:
            problems.append(f"unknown readiness key {key}")
    return problems


def check_inventory(document: dict, routes) -> list[str]:
    discovered = discover_candidates(routes)
    problems = validate_document(document)
    problems.extend(_snapshot_problems(document, discovered))
    problems.extend(_readiness_problems(document))
    return problems


def _count(rows: list[dict], field: str, value: str) -> int:
    return sum(1 for row in rows if row[field] == value)


def _grouped(rows: list[dict], containment: str) -> list[tuple[str, int]]:
    families: dict[str, int] = {}
    for row in rows:
        if row["containment"] != containment:
            continue
        symbol = row["implementation_symbol"] or "unresolved"
        families[symbol] = families.get(symbol, 0) + 1
    return sorted(families.items(), key=lambda item: (-item[1], item[0]))


def _family_block(title: str, pairs: list[tuple[str, int]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not pairs:
        lines.append("- none")
    else:
        lines.extend(f"- `{name}`: {count}" for name, count in pairs)
    lines.append("")
    return lines


def render_markdown(document: dict, live_count: int, openapi_count: int) -> str:
    rows = document["rows"]
    layers: dict[str, int] = {}
    for row in rows:
        layers[row["authority_layer"]] = layers.get(row["authority_layer"], 0) + 1
    layer_lines = [f"- `{name}`: {layers[name]}" for name in sorted(layers)]
    lines = [
        "# Manufacturing output inventory",
        "",
        "Inventory coverage is not manufacturing qualification. `UNEXAMINED` does not mean safe. A listed authority key does not prove that enforcement occurs before generation.",
        "",
        f"Pinned base SHA: `{document['base_sha']}`",
        "",
        f"- OpenAPI paths: {openapi_count}",
        f"- Live route operations: {live_count}",
        f"- Candidates: {len(rows)}",
        f"- Confirmed emitters: {_count(rows, 'classification', 'CONFIRMED_EMITTER')}",
        f"- Delegates: {_count(rows, 'classification', 'CONFIRMED_DELEGATE')}",
        f"- Non-emitting: {_count(rows, 'classification', 'NON_EMITTING')}",
        f"- Unexamined: {_count(rows, 'classification', 'UNEXAMINED')}",
        f"- Fail-closed: {_count(rows, 'containment', 'FAIL_CLOSED')}",
        f"- Permitted by authority: {_count(rows, 'containment', 'PERMITTED_BY_AUTHORITY')}",
        f"- Live-ungoverned: {_count(rows, 'containment', 'LIVE_UNGOVERNED')}",
        f"- Unknown containment: {_count(rows, 'containment', 'UNKNOWN')}",
        f"- Not applicable: {_count(rows, 'containment', 'NOT_APPLICABLE')}",
        "",
        "## Authority layers",
        "",
        *layer_lines,
        "",
    ]
    lines.extend(_family_block("Live-ungoverned families", _grouped(rows, "LIVE_UNGOVERNED")))
    lines.extend(_family_block("Unknown-containment families", _grouped(rows, "UNKNOWN")))
    lines.extend([
        "## Reconciliation",
        "",
        document["reconciliation"],
        "",
        "This inventory is not imported by production routers. It does not qualify a generator or claim the repository is contained.",
        "",
    ])
    return "\n".join(lines)


def _load_app():
    from app.main import app
    return app


def _population_problems(app) -> tuple[list, list[str]]:
    live, unresolved = walk_live(app.routes)
    problems: list[str] = []
    if unresolved:
        problems.append(f"unresolved route objects: {len(unresolved)}")
    if not live or not app.openapi().get("paths"):
        problems.append("empty route population")
    problems.extend(reconcile(live, app.openapi()))
    return live, problems


def _write_outputs(app, live, inventory_path: str | None, report_path: str | None) -> None:
    document = build_document(discover_candidates(app.routes))
    if inventory_path:
        Path(inventory_path).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    if report_path:
        text = render_markdown(document, len(live), len(app.openapi()["paths"]))
        Path(report_path).write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manufacturing output inventory")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write-report")
    parser.add_argument("--write-inventory")
    args = parser.parse_args(argv)
    app = _load_app()
    live, problems = _population_problems(app)
    if problems:
        print("FAIL route population", file=sys.stderr)
        for item in problems[:20]:
            print(item, file=sys.stderr)
        return 1
    if args.write_inventory:
        _write_outputs(app, live, args.write_inventory, args.write_report)
        return 0
    document = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    problems = check_inventory(document, app.routes)
    naive = len(naive_walk(app.routes))
    if naive >= len(live):
        problems.append("naive walker did not truncate")
    if args.write_report:
        text = render_markdown(document, len(live), len(app.openapi()["paths"]))
        Path(args.write_report).write_text(text, encoding="utf-8")
    if problems:
        print(f"FAIL inventory {len(problems)}", file=sys.stderr)
        for item in problems[:40]:
            print(item, file=sys.stderr)
        return 1
    if not args.check and not args.write_report:
        print("nothing to do; pass --check", file=sys.stderr)
        return 1
    print(f"OK candidates={len(document['rows'])} live={len(live)} naive={naive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
