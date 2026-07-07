#!/usr/bin/env python3
"""GEN-5-A — Instrument Library Source Census (stdlib-only).

Builds a deterministic census of the five legacy instrument-library sources and a
canonical schema proposal. This is DATA INSPECTION ONLY: it does not import any
``app.*`` runtime module, does not change any source, and does not decide field
winners. Conflicts are reported, not resolved.

Sources inspected (read-only):
  1. guitars/__init__.py       MODEL_SPECS / MODEL_INFOS   (runtime spec factories)
  2. instrument_model_registry.json                        (metadata / assets / CAM)
  3. body_dimension_reference.json                         (vectorizer scale priors)
  4. body_templates.json                                   (body template conventions)
  5. body/catalog.json                                     (body catalog / outline)

Usage:
  python build_instrument_library_census.py --write
  python build_instrument_library_census.py --check
Options:
  --write        regenerate JSON + Markdown artifacts
  --check        exit non-zero if artifacts differ from freshly-computed census
                 (the JSON ``generated_at`` field is ignored for equality)
  --json-out P   override JSON output path (tests)
  --md-out P     override Markdown output path (tests)
  --repo-root P  run against an alternate repo root (tests/fixtures)
  --now ISO      freeze ``generated_at`` (or set env GEN5_CENSUS_NOW)

Stdlib only: json, ast, argparse, os, sys, datetime, pathlib.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- #
# Source layout (relative to repo root)
# --------------------------------------------------------------------------- #
GUITARS_INIT = "services/api/app/instrument_geometry/guitars/__init__.py"
ENUM_FILE = "services/api/app/instrument_geometry/models.py"

JSON_SOURCES = {
    "instrument_model_registry": "services/api/app/instrument_geometry/instrument_model_registry.json",
    "body_dimension_reference": "services/photo-vectorizer/body_dimension_reference.json",
    "body_templates": "services/api/app/data_registry/system/instruments/body_templates.json",
    "body_catalog": "services/api/app/instrument_geometry/body/catalog.json",
}
# Logical order of all five sources for stable reporting.
SOURCE_ORDER = [
    "model_specs",
    "instrument_model_registry",
    "body_dimension_reference",
    "body_templates",
    "body_catalog",
]

DEFAULT_JSON_OUT = "services/api/metrics/gen5_instrument_library_census.json"
DEFAULT_MD_OUT = "docs/audit/GEN5_INSTRUMENT_LIBRARY_SOURCE_CENSUS.md"

# --------------------------------------------------------------------------- #
# Explicit alias map — comparison hygiene ONLY (GEN-5-A dev order).
# Do NOT invent semantic equivalence beyond these groups; uncertain matches are
# reported as candidates, never silently merged.
# --------------------------------------------------------------------------- #
ALIAS_GROUPS = [
    ["j_45", "j45", "gibson_j45"],
    ["es_335", "es335"],
    ["gibson_sg", "sg"],
    ["jumbo_j200", "jumbo"],
    ["explorer", "gibson_explorer"],
    ["cuatro", "cuatro_venezolano", "cuatro_puertorriqueno"],
    ["ukulele", "soprano_ukulele", "concert_ukulele"],
]
# member -> canonical (first entry of its group)
_ALIAS_CANON = {}
for _grp in ALIAS_GROUPS:
    for _member in _grp:
        _ALIAS_CANON[_member] = _grp[0]

# --------------------------------------------------------------------------- #
# Per-source field-role classification (by field presence in an entry).
# --------------------------------------------------------------------------- #
ROLE_FIELDS = {
    "instrument_model_registry": {
        "metadata": ["display_name", "status", "category", "manufacturer",
                     "year_introduced", "fret_count", "string_count", "description"],
        "physical_dimensions": ["scale_length_mm"],
        "assets": ["assets", "spec"],
        "cam_capability": ["cam_capable", "cam_operations"],
    },
    "body_dimension_reference": {
        "physical_dimensions": ["body_length_mm", "upper_bout_width_mm",
                                "waist_width_mm", "lower_bout_width_mm",
                                "waist_y_norm", "depth_mm", "thickness_mm"],
    },
    "body_templates": {
        "body_template": ["type", "features", "neck_pocket", "outline_available", "dimensions"],
        "physical_dimensions": ["scale_length_mm"],
    },
    "body_catalog": {
        "body_catalog": ["dimensions_mm", "points", "source", "name", "category"],
        "assets": ["dxf"],
    },
    # model_specs presence == a runtime spec factory exists.
    "model_specs": {"runtime_spec": ["__present__"]},
}

# Canonical dimension fields compared across sources for CONFLICTS. Only
# same-semantic paths are compared — comparing a bounding-box width against a
# lower-bout width would manufacture false conflicts, so those are left as
# presence-only. Path is a key sequence into the entry dict.
CONFLICT_FIELDS = {
    "scale_length_mm": {
        "instrument_model_registry": ["scale_length_mm"],
        "body_templates": ["scale_length_mm"],
    },
    "body_length_mm": {
        "body_dimension_reference": ["body_length_mm"],
        "body_templates": ["dimensions", "length_mm"],
    },
}

SCHEMA_PROPOSAL = {
    "version": "0.1.0",
    "note": "PROPOSAL ONLY — not used by runtime code. Field-role based; distinguishes "
            "metadata, physical dimensions, body template conventions, body catalog data, "
            "runtime factory availability, assets, and CAM capability. Every field group "
            "carries source_provenance so a later migration can say where each value came from.",
    "families": {
        "<family>": {
            "models": {
                "<model_id>": {
                    "id": "<model_id>",
                    "display_name": "<str>",
                    "variants": {},
                    "metadata": {
                        "manufacturer": None, "category": None, "status": None,
                        "description": None, "year_introduced": None,
                        "string_count": None, "fret_count": None, "scale_length_mm": None,
                    },
                    "physical_dimensions": {
                        "body_length_mm": None, "upper_bout_width_mm": None,
                        "lower_bout_width_mm": None, "waist_width_mm": None,
                        "depth_mm": None, "thickness_mm": None,
                        "vectorizer_scale_priors": {},
                    },
                    "body_template": {"type": None, "features": {}, "neck_pocket": {},
                                      "outline_available": None},
                    "body_catalog": {"dxf": None, "points": None, "source": None,
                                     "dimensions_mm": {}},
                    "runtime_spec": {"factory_exists": False, "factory_ref": None},
                    "assets": [],
                    "cam_capability": {"cam_capable": None, "cam_operations": []},
                    "source_provenance": {
                        "__doc__": "field_group -> {source, source_id, path} recording origin",
                    },
                }
            }
        }
    },
}

META_KEYS = {"_comment", "_fields", "_meta"}  # non-model keys to skip in JSON sources


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise SystemExit(f"GEN5 census: missing source file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"GEN5 census: invalid JSON in {path}: {exc}")


def load_enum_value_map(repo_root: Path) -> dict:
    """AST-parse InstrumentModelId to map ENUM_MEMBER -> string value (no import)."""
    path = repo_root / ENUM_FILE
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, SyntaxError) as exc:
        raise SystemExit(f"GEN5 census: cannot parse enum file {path}: {exc}")
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "InstrumentModelId":
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                        and isinstance(stmt.targets[0], ast.Name) \
                        and isinstance(stmt.value, ast.Constant) \
                        and isinstance(stmt.value.value, str):
                    out[stmt.targets[0].id] = stmt.value.value
    return out


def load_model_specs(repo_root: Path) -> dict:
    """AST-parse guitars/__init__.py for MODEL_SPECS / MODEL_INFOS keys (no import).

    Keys are ``InstrumentModelId.<MEMBER>`` attributes; resolve them to string ids
    via the enum value map. Returns {"model_specs": [ids], "model_infos": [ids]}.
    """
    path = repo_root / GUITARS_INIT
    enum_map = load_enum_value_map(repo_root)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, SyntaxError) as exc:
        raise SystemExit(f"GEN5 census: cannot parse {path}: {exc}")

    def dict_member_ids(var_name: str) -> list:
        ids = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == var_name:
                        for key in node.value.keys:
                            member = None
                            if isinstance(key, ast.Attribute) \
                                    and isinstance(key.value, ast.Name) \
                                    and key.value.id == "InstrumentModelId":
                                member = key.attr
                            elif isinstance(key, ast.Constant) and isinstance(key.value, str):
                                member = key.value
                            if member is None:
                                continue
                            ids.append(enum_map.get(member, member))
        # de-dup preserving first occurrence (the populated assignment wins;
        # the empty fallback dict contributes nothing)
        seen, uniq = set(), []
        for i in ids:
            if i not in seen:
                seen.add(i)
                uniq.append(i)
        return uniq

    return {"model_specs": dict_member_ids("MODEL_SPECS"),
            "model_infos": dict_member_ids("MODEL_INFOS")}


def source_entries(repo_root: Path) -> dict:
    """Return {source: {original_id: entry_or_None}} for all five sources."""
    specs = load_model_specs(repo_root)
    entries = {"model_specs": {mid: None for mid in specs["model_specs"]}}

    reg = _load_json(repo_root / JSON_SOURCES["instrument_model_registry"])
    entries["instrument_model_registry"] = dict(reg.get("models", {}))

    dim = _load_json(repo_root / JSON_SOURCES["body_dimension_reference"])
    entries["body_dimension_reference"] = {
        k: v for k, v in dim.items() if k not in META_KEYS and not k.startswith("_")
    }

    tpl = _load_json(repo_root / JSON_SOURCES["body_templates"])
    entries["body_templates"] = dict(tpl.get("bodies", {}))

    cat = _load_json(repo_root / JSON_SOURCES["body_catalog"])
    entries["body_catalog"] = dict(cat.get("bodies", {}))

    return entries


# --------------------------------------------------------------------------- #
# Normalization / roles / conflicts
# --------------------------------------------------------------------------- #
def normalize_id(raw: str) -> str:
    """Normalize for COMPARISON only. Lowercase, trim, hyphen->underscore, then
    fold known aliases to their group canonical. Original ids are preserved
    elsewhere in the report."""
    base = str(raw).strip().lower().replace("-", "_")
    return _ALIAS_CANON.get(base, base)


def _dig(entry, path):
    cur = entry
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def entry_roles(source: str, entry) -> list:
    """Roles a given entry carries, by field presence."""
    roles = []
    for role, fields in ROLE_FIELDS.get(source, {}).items():
        if fields == ["__present__"]:
            roles.append(role)
        elif isinstance(entry, dict) and any(f in entry for f in fields):
            roles.append(role)
    return sorted(roles)


def _numeric_delta(values):
    nums = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if len(nums) >= 2:
        return round(max(nums) - min(nums), 4)
    return None


def _conflict_key(v):
    """Distinctness key for conflict detection. Numerically-equal ints/floats
    (e.g. 648 vs 648.0) must NOT read as a conflict, so numbers collapse to a
    single float key; bool is kept textual so True never equals 1."""
    if isinstance(v, bool):
        return ("json", json.dumps(v))
    if isinstance(v, (int, float)):
        return ("num", float(v))
    return ("json", json.dumps(v, sort_keys=True))


# --------------------------------------------------------------------------- #
# Census build
# --------------------------------------------------------------------------- #
def build_census(repo_root: Path, now_iso: str) -> dict:
    entries = source_entries(repo_root)

    # normalized_id -> {source: original_id}
    model_source_ids = {}
    for source in SOURCE_ORDER:
        for original_id in entries.get(source, {}):
            norm = normalize_id(original_id)
            model_source_ids.setdefault(norm, {})
            # keep the first-seen original id per (model, source)
            model_source_ids[norm].setdefault(source, original_id)

    all_norms = sorted(model_source_ids)
    all_conflicts = []
    model_index = {}

    for norm in all_norms:
        src_ids = model_source_ids[norm]
        presence = {s: (s in src_ids) for s in SOURCE_ORDER}

        # field roles across sources present
        field_roles = {}
        for source, original_id in sorted(src_ids.items()):
            entry = entries[source].get(original_id)
            for role in entry_roles(source, entry):
                field_roles.setdefault(role, [])
                if source not in field_roles[role]:
                    field_roles[role].append(source)
        field_roles = {r: sorted(v) for r, v in sorted(field_roles.items())}

        # conflicts on explicitly same-semantic fields
        conflicts = []
        for field, source_paths in CONFLICT_FIELDS.items():
            values = {}
            for source, path in source_paths.items():
                if source in src_ids:
                    val = _dig(entries[source].get(src_ids[source]), path)
                    if val is not None:
                        values[source] = val
            distinct = {_conflict_key(v) for v in values.values()}
            if len(values) >= 2 and len(distinct) >= 2:
                rec = {
                    "model": norm,
                    "field": field,
                    "values": {s: values[s] for s in sorted(values)},
                    "delta": _numeric_delta(list(values.values())),
                    "note": "differing values across sources — reported, not resolved",
                }
                conflicts.append(rec)
                all_conflicts.append(rec)

        # alias/uncertainty notes
        notes = []
        raw_forms = sorted(set(src_ids.values()))
        if len(raw_forms) > 1:
            notes.append(f"appears under multiple original ids: {raw_forms} "
                         f"(folded via explicit alias map / normalization)")

        model_index[norm] = {
            "normalized_id": norm,
            "source_ids": {s: src_ids[s] for s in SOURCE_ORDER if s in src_ids},
            "presence": presence,
            "present_in_count": sum(1 for s in SOURCE_ORDER if s in src_ids),
            "field_roles": field_roles,
            "conflicts": conflicts,
            "notes": notes,
        }

    # missing_by_source: ids present somewhere but absent from this source
    missing_by_source = {}
    for source in SOURCE_ORDER:
        missing = [n for n in all_norms if source not in model_source_ids[n]]
        missing_by_source[source] = sorted(missing)

    source_counts = {s: len(entries.get(s, {})) for s in SOURCE_ORDER}

    return {
        "generated_at": now_iso,
        "source_snapshot": {
            s: {"path": (GUITARS_INIT if s == "model_specs" else JSON_SOURCES[s]),
                "count": source_counts[s]}
            for s in SOURCE_ORDER
        },
        "source_counts": source_counts,
        "total_distinct_models": len(all_norms),
        "model_index": model_index,
        "missing_by_source": missing_by_source,
        "conflicts": sorted(all_conflicts, key=lambda r: (r["model"], r["field"])),
        "schema_proposal": SCHEMA_PROPOSAL,
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def _stable_json(census: dict) -> str:
    return json.dumps(census, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_markdown(census: dict) -> str:
    """Deterministic Markdown (no wall-clock — the timestamp lives only in JSON)."""
    L = []
    L.append("# GEN-5-A — Instrument Library Source Census")
    L.append("")
    L.append("_Generated by `services/api/scripts/build_instrument_library_census.py` "
             "(`--write`). Deterministic; regenerate rather than hand-edit._")
    L.append("")
    L.append("> **This census does not decide canonical field winners. It identifies the "
             "source surface that a later GEN-5 migration must preserve or reconcile.** "
             "Conflicts below are findings, not fixes.")
    L.append("")

    # Summary
    L.append("## Summary")
    L.append("")
    L.append(f"- Distinct models (normalized): **{census['total_distinct_models']}**")
    L.append(f"- Conflicts reported (not resolved): **{len(census['conflicts'])}**")
    L.append("- Five legacy sources parsed **without importing any `app.*` runtime module**.")
    L.append("")

    # Source roles
    L.append("## Source roles")
    L.append("")
    roles_desc = {
        "model_specs": "runtime spec factories (`MODEL_SPECS` / `MODEL_INFOS`)",
        "instrument_model_registry": "model metadata, assets, status, CAM capability",
        "body_dimension_reference": "vectorizer scale priors / body dimensions",
        "body_templates": "body template conventions (routable features, neck pocket)",
        "body_catalog": "body catalog / outline metadata (DXF, point counts)",
    }
    L.append("| Source | Role | Path |")
    L.append("|---|---|---|")
    for s in SOURCE_ORDER:
        snap = census["source_snapshot"][s]
        L.append(f"| `{s}` | {roles_desc[s]} | `{snap['path']}` |")
    L.append("")

    # Current counts
    L.append("## Current counts")
    L.append("")
    L.append("| Source | Count |")
    L.append("|---|---|")
    for s in SOURCE_ORDER:
        L.append(f"| `{s}` | {census['source_counts'][s]} |")
    L.append("")

    # Coverage table
    L.append("## Model coverage")
    L.append("")
    header = "| normalized_id | " + " | ".join(SOURCE_ORDER) + " | roles |"
    L.append(header)
    L.append("|" + "---|" * (len(SOURCE_ORDER) + 2))
    for norm in sorted(census["model_index"]):
        mi = census["model_index"][norm]
        cells = []
        for s in SOURCE_ORDER:
            if mi["presence"][s]:
                oid = mi["source_ids"].get(s, "")
                cells.append("✓" if oid == norm else f"✓ `{oid}`")
            else:
                cells.append("·")
        roles = ", ".join(mi["field_roles"].keys())
        L.append(f"| `{norm}` | " + " | ".join(cells) + f" | {roles} |")
    L.append("")

    # Conflicts
    L.append("## Conflicts and mismatches")
    L.append("")
    if census["conflicts"]:
        L.append("| model | field | values (by source) | delta |")
        L.append("|---|---|---|---|")
        for c in census["conflicts"]:
            vals = "; ".join(f"`{s}`={c['values'][s]}" for s in sorted(c["values"]))
            L.append(f"| `{c['model']}` | {c['field']} | {vals} | {c['delta']} |")
    else:
        L.append("_No cross-source conflicts on the explicitly-compared same-semantic fields._")
    L.append("")
    L.append("_Conflict comparison is limited to explicitly same-semantic fields "
             "(`scale_length_mm`, `body_length_mm`) to avoid false positives from "
             "differently-defined dimensions (e.g. bounding-box width vs lower-bout "
             "width). Other dimension fields are single-source and reported as "
             "presence-only._")
    L.append("")

    # Naming / alias
    L.append("## Naming / alias issues")
    L.append("")
    L.append("Explicit alias map used for comparison hygiene only (no semantic "
             "equivalence invented beyond these); uncertain matches stay as candidates:")
    L.append("")
    for grp in ALIAS_GROUPS:
        L.append(f"- {' / '.join('`' + g + '`' for g in grp)}")
    L.append("")
    multi = [n for n in sorted(census["model_index"])
             if census["model_index"][n]["notes"]]
    if multi:
        L.append("Models appearing under multiple original ids:")
        L.append("")
        for n in multi:
            for note in census["model_index"][n]["notes"]:
                L.append(f"- `{n}`: {note}")
        L.append("")

    # Missing
    L.append("## Missing entries (present elsewhere, absent here)")
    L.append("")
    for s in SOURCE_ORDER:
        miss = census["missing_by_source"][s]
        L.append(f"- `{s}` ({len(miss)} missing): "
                 + (", ".join(f"`{m}`" for m in miss) if miss else "_none_"))
    L.append("")

    # Proposed schema
    L.append("## Proposed canonical schema (proposal only — not runtime)")
    L.append("")
    L.append("```json")
    L.append(json.dumps(census["schema_proposal"], indent=2, sort_keys=True))
    L.append("```")
    L.append("")

    # Rollout
    L.append("## Recommended rollout after GEN-5-A")
    L.append("")
    L.append("- **GEN-5-B** — candidate `instrument_library.json` with field-level provenance (no consumers).")
    L.append("- **GEN-5-C** — compatibility loader (`as_model_registry()`, `as_body_dimension_reference()`, `as_body_templates()`, `as_body_catalog()`).")
    L.append("- **GEN-5-D** — migrate consumers one at a time.")
    L.append("- **GEN-5-E** — retire or generate legacy artifacts, only after consumers migrate.")
    L.append("")
    L.append("## Non-disposition statement")
    L.append("")
    L.append("This census does not decide canonical field winners, geometry authority, "
             "or body-outline authority. Current source roles are preserved; every legacy "
             "consumer keeps reading exactly what it reads today. GEN-5 remains open.")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _resolve_now(cli_now):
    val = cli_now or os.environ.get("GEN5_CENSUS_NOW")
    if val:
        return val
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _strip_generated_at(obj):
    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if k != "generated_at"}
    return obj


def _resolve_out(arg, default_rel, repo_root):
    """Resolve an output path against ``repo_root``, not the process CWD.

    Default paths are repo-root-relative; an explicit ``--json-out``/``--md-out``
    override follows the same rule so a relative override (e.g. from a test
    fixture invoked out of another directory) lands beside the defaults instead
    of silently reading/writing under the shell's CWD. Absolute overrides are
    honored as-is."""
    if not arg:
        return repo_root / default_rel
    p = Path(arg)
    return p if p.is_absolute() else (repo_root / p)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="GEN-5-A instrument library source census")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="regenerate artifacts")
    mode.add_argument("--check", action="store_true",
                      help="fail if artifacts are stale (generated_at ignored)")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--md-out", default=None)
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--now", default=None, help="freeze generated_at (or env GEN5_CENSUS_NOW)")
    args = ap.parse_args(argv)

    # repo root: default = two levels up from services/api/scripts/
    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        repo_root = Path(__file__).resolve().parents[3]

    json_out = _resolve_out(args.json_out, DEFAULT_JSON_OUT, repo_root)
    md_out = _resolve_out(args.md_out, DEFAULT_MD_OUT, repo_root)

    census = build_census(repo_root, _resolve_now(args.now))
    json_text = _stable_json(census)
    md_text = render_markdown(census)

    if args.check:
        problems = []
        if not json_out.exists():
            problems.append(f"missing {json_out}")
        else:
            cur = json.loads(json_out.read_text(encoding="utf-8"))
            if _strip_generated_at(cur) != _strip_generated_at(census):
                problems.append(f"{json_out} is stale (regenerate with --write)")
        if not md_out.exists():
            problems.append(f"missing {md_out}")
        elif md_out.read_text(encoding="utf-8") != md_text:
            problems.append(f"{md_out} is stale (regenerate with --write)")
        if problems:
            print("GEN5 census --check FAILED:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print("GEN5 census --check OK: artifacts match sources.")
        return 0

    if args.write:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json_text, encoding="utf-8")
        md_out.write_text(md_text, encoding="utf-8")
        print(f"GEN5 census written:\n  {json_out}\n  {md_out}")
        print(f"  models={census['total_distinct_models']} "
              f"conflicts={len(census['conflicts'])}")
        return 0

    # no mode: print JSON to stdout
    sys.stdout.write(json_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
