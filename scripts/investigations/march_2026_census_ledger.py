#!/usr/bin/env python3
"""Build RECOVERY_LEDGER.csv from the bundle census + explicit overrides. Read-only.

Input: the JSON written by ``march_2026_bundle_census.py`` and an overrides JSON
(``LEDGER_OVERRIDES.json``) committed beside the ledger. One row per unique
content (LF-normalised Git blob), listing every source that carries it.

Automatic disposition (overrides win, and every override records its reason):

  LIVE_IDENTICAL                         -> LIVE_INTEGRATED
  ARCHIVE_ONLY                           -> ARCHIVED_COMPLETE
  HISTORY_ONLY + same name live          -> LIVE_MODIFIED
  HISTORY_ONLY, no same-name live file   -> UNRESOLVED (entered Git, later left main)
  EXTERNAL_ONLY                          -> EXTERNAL_ONLY

Rows whose member path matches an ``exclude`` pattern (third-party saved web
pages) are counted but not ledgered.

Overrides are keyed ``by_blob`` (preferred) or ``by_name`` (basename). A
``by_blob`` entry wins. A ``by_name`` entry whose basename maps to more than one
distinct blob is refused (exit 2), because it would stamp one reason on
different files. ``PLANNING_RECONCILIATION.csv`` still joins claims to sources
by basename; its ``located_source_by_name`` column says so.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path, PurePosixPath

AUTO = {
    "LIVE_IDENTICAL": "LIVE_INTEGRATED",
    "ARCHIVE_ONLY": "ARCHIVED_COMPLETE",
    "EXTERNAL_ONLY": "EXTERNAL_ONLY",
}


def subsystem(name: str) -> str:
    n = name.lower()
    rules = [
        ("headstock", "Headstock Suite"), ("neck", "Neck tooling"), ("cam", "CAM Workspace/backend"),
        ("orchestrator", "Neck orchestrator"), ("machines", "CAM Workspace/backend"),
        ("binding", "Binding/purfling"), ("purf", "Binding/purfling"), ("radius", "Radius dish"),
        ("dish", "Radius dish"), ("brace", "Bracing"), ("bracing", "Bracing"),
        ("plate", "Plate physics"), ("alpha_beta", "Plate physics"), ("rayleigh", "Plate physics"),
        ("calibration", "Plate physics"), ("coupled", "Plate physics"), ("inverse_solver", "Plate physics"),
        ("thickness", "Plate physics"), ("graduation", "Plate physics"), ("vector", "Vectorizer"),
        ("contour", "Vectorizer"), ("landmark", "Vectorizer"), ("body_", "Vectorizer"),
        ("result_", "Vectorizer"), (".dxf", "Vectorizer"), (".svg", "Vectorizer"),
        ("soundhole", "Soundhole"), ("tension", "String tension"), ("stiffness", "Materials"),
        ("tonewood", "Materials"), ("material", "Materials"), ("project", "Project graph"),
        ("blueprint", "Blueprint save"), ("hub", "Instrument hub"), ("bridge", "Bridge lab"),
        ("saddle", "Bridge lab"), ("kerf", "Kerfing"), ("fret", "Fretwork"), ("nut_", "Fretwork"),
        ("side_bending", "Side bending"), ("calculator", "Calculator UI"), ("backlog", "Planning record"),
        ("session_notes", "Planning record"), ("lutherie_math", "Planning record"),
    ]
    for key, label in rules:
        if key in n:
            return label
    return "Other"


#: Output-session label by bundle timestamp prefix (from the bundle file name).
SESSIONS = [
    ("2026-03-15T0", "Calculator UI (03-15 session)"),
    ("2026-03-15T1", "Calculator UI (03-15 session)"),
    ("2026-03-16T14", "Vectorizer (03-16 result sets)"),
    ("2026-03-17T", "ps-vue suite: headstock / neck / CAM UI (03-17)"),
    ("2026-03-18T011318", "Plate physics (03-18)"),
    ("2026-03-18T031920", "CAM Workspace/backend (03-18 03:19)"),
    ("2026-03-19T0", "Soundhole (03-19)"),
    ("2026-03-19T1", "Soundhole / path packs (03-19)"),
    ("2026-03-19T2", "Path packs (03-19)"),
    ("2026-03-20T", "Bracing / radius dish / path packs (03-20)"),
    ("2026-03-21T02", "Vectorizer (03-21)"),
    ("2026-03-21T1", "Side bending (03-21)"),
    ("temp_cam_workspace2", "ps-vue suite: headstock / neck / CAM UI (03-17)"),
]


def session_of(source_path: str) -> str:
    for key, label in SESSIONS:
        if key in source_path:
            return label
    return "Other"


def write_planning(census: dict, reachability: Path, out: Path) -> None:
    """PLANNING_RECONCILIATION.csv: planning item -> bundle -> Git -> archive -> runtime.

    Bundle linkage is by file name (the claimed primary path's basename) and is
    marked as such; Git/live linkage comes from the reachability pass.
    """
    by_name: dict[str, list[dict]] = {}
    for m in census["members"]:
        by_name.setdefault(PurePosixPath(m["member"].split("!/")[-1]).name, []).append(m)
    src_path = {s["source_id"]: s["path"] for s in census["sources"]}
    fields = ["item", "claimed_artifact", "claimed_state", "located_source_by_name", "source_content_states",
              "entered_git", "current_live_path", "archive_path", "external_only_source", "current_status",
              "confidence"]
    with reachability.open(encoding="utf-8", newline="") as fh, out.open("w", encoding="utf-8", newline="") as oh:
        w = csv.DictWriter(oh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in csv.DictReader(fh):
            name = PurePosixPath(r["primary_path"]).name
            hits = by_name.get(name, [])
            archive = sorted({a for h in hits for a in h["archive_paths"]})
            external = sorted({src_path[h["source_id"]] for h in hits if h["state"] == "EXTERNAL_ONLY"})
            w.writerow({
                "item": r["claim_id"], "claimed_artifact": r["primary_path"], "claimed_state": r["claimed_state"],
                "located_source_by_name": ";".join(sorted({src_path[h["source_id"]] for h in hits}))[:240],
                "source_content_states": ";".join(sorted({h["state"] for h in hits})),
                "entered_git": r["claimed_commit"],
                "current_live_path": r["primary_path"] if r["file_present"] == "PASS" else "",
                "archive_path": ";".join(archive)[:240], "external_only_source": ";".join(external)[:240],
                "current_status": r["classification"],
                "confidence": "reachability: mechanical; bundle link: by file name" if hits
                              else "reachability: mechanical; no bundle carries this name",
            })


_STAMP = re.compile(r"(2026-\d\d-\d\dT\d{6}\.\d{3})")


def write_inventory(census: dict, exclude: list, ov: dict, out: Path) -> None:
    """SOURCE_BUNDLE_INVENTORY.csv: one row per located source."""
    members: dict[str, list[dict]] = {}
    for m in census["members"]:
        members.setdefault(m["source_id"], []).append(m)
    fields = ["source_id", "filename", "timestamp", "sha256", "kind", "apparent_originating_session",
              "contained_top_level_paths", "nested_archive_count", "members", "excluded_third_party",
              "live_identical", "archive_only", "history_only", "external_only_unique",
              "repository_copy_present", "repository_copy_complete", "current_preservation_status", "notes"]
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for s in census["sources"]:
            ms = members.get(s["source_id"], [])
            kept = [m for m in ms if not any(p.search(m["member"]) for p in exclude)]
            c: dict[str, int] = {}
            for m in kept:
                c[m["state"]] = c.get(m["state"], 0) + 1
            ext = c.get("EXTERNAL_ONLY", 0)
            stamp = _STAMP.search(s["path"])
            notes = []
            if s["nested_archives"]:
                notes.append(f"nested: {len(s['nested_archives'])} zip(s); repository archive copy omits them")
            if len(ms) != len(kept):
                notes.append(f"{len(ms) - len(kept)} third-party saved-web-page members excluded ({ov.get('exclude_reason', '')[:60]}...)")
            if s["skipped_snapshots"]:
                notes.append("contains repository snapshot archive (not walked): " + ";".join(s["skipped_snapshots"]))
            if s["kind"] == "folder":
                notes.append("extracted folder; duplicates a zip of the same timestamp where one exists")
            w.writerow({
                "source_id": s["source_id"], "filename": s["path"],
                "timestamp": stamp.group(1) if stamp else "",
                "sha256": s["sha256"] or "(folder: per-member hashes in BUNDLE_MEMBERS.csv)",
                "kind": s["kind"], "apparent_originating_session": session_of(s["path"]),
                "contained_top_level_paths": ";".join(s["top_level"])[:240],
                "nested_archive_count": len(s["nested_archives"]), "members": len(kept),
                "excluded_third_party": len(ms) - len(kept),
                "live_identical": c.get("LIVE_IDENTICAL", 0), "archive_only": c.get("ARCHIVE_ONLY", 0),
                "history_only": c.get("HISTORY_ONLY", 0), "external_only_unique": ext,
                "repository_copy_present": "yes" if len(kept) - ext else "no",
                "repository_copy_complete": "yes" if kept and not ext else "no",
                "current_preservation_status": ("Git covers every member" if kept and not ext
                                                else f"{ext} member(s) exist only in this Downloads source"),
                "notes": " | ".join(notes),
            })


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", type=Path, required=True)
    ap.add_argument("--overrides", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-inventory", type=Path, required=True)
    ap.add_argument("--reachability", type=Path, required=True)
    ap.add_argument("--out-planning", type=Path, required=True)
    args = ap.parse_args(argv)
    census = json.loads(args.census.read_text(encoding="utf-8"))
    ov = json.loads(args.overrides.read_text(encoding="utf-8"))
    exclude = [re.compile(p) for p in ov.get("exclude", [])]
    by_blob: dict[str, list[dict]] = {}
    excluded = 0
    for m in census["members"]:
        if any(p.search(m["member"]) for p in exclude):
            excluded += 1
            continue
        by_blob.setdefault(m["blob_lf"], []).append(m)

    # A by_name override stamps every blob sharing that basename. Refuse when a
    # name maps to more than one distinct blob: key that override by_blob instead.
    blobs_by_name: dict[str, set[str]] = {}
    for blob, group in by_blob.items():
        blobs_by_name.setdefault(PurePosixPath(group[0]["member"].split("!/")[-1]).name, set()).add(blob)
    ambiguous = {n: sorted(blobs_by_name[n]) for n in ov["by_name"] if len(blobs_by_name.get(n, ())) > 1}
    if ambiguous:
        print(f"ambiguous by_name overrides (re-key by_blob): {json.dumps(ambiguous)}", file=sys.stderr)
        return 2

    src_path = {s["source_id"]: s["path"] for s in census["sources"]}
    rows = []
    for i, (blob, group) in enumerate(sorted(by_blob.items(), key=lambda kv: (kv[1][0]["source_id"], kv[1][0]["member"])), 1):
        first = group[0]
        name = PurePosixPath(first["member"].split("!/")[-1]).name
        state = first["state"]
        live_same_name = first["name_only_matches_on_ref"]
        if state == "HISTORY_ONLY":
            disp = "LIVE_MODIFIED" if live_same_name else "UNRESOLVED"
        else:
            disp = AUTO[state]
        override = ov["by_blob"].get(blob) or ov["by_name"].get(name)
        reason = ""
        if override:
            disp = override["disposition"]
            reason = override["reason"]
        label = (override or {}).get("subsystem") or subsystem(name)
        if label == "Other":
            nested = first["member"].split("!/")[0] if "!/" in first["member"] else ""
            label = session_of(nested or src_path.get(first["source_id"], ""))
        rows.append({
            "candidate_id": f"MC-{i:03d}",
            "subsystem": label,
            "output_session": session_of(src_path.get(first["source_id"], "")),
            "source_bundles": ";".join(sorted({g["source_id"] for g in group})),
            "original_path": first["member"],
            "filename": name,
            "content_blob_lf": blob,
            "sha256": first["sha256"],
            "census_state": state,
            "first_repository_commit": f'{first["first_commit"][:8]} {first["first_date"]}'.strip(),
            "first_repository_path": first["first_path"],
            "current_live_path": ";".join(first["live_paths"]),
            "archive_path": ";".join(first["archive_paths"]),
            "same_name_on_main_different_content": ";".join(live_same_name[:3]),
            "unique_relative_to_main": "no" if first["live_paths"] else "yes",
            "safety_relevance": (override or {}).get("safety") or "",
            "disposition": disp,
            "disposition_reason": reason or f"automatic from census state {state}",
            "confidence": (override or {}).get("confidence", "content-hash" if state != "HISTORY_ONLY" else "content-hash; current form inferred by name"),
            "follow_up_order": (override or {}).get("follow_up", ""),
        })
    for extra in ov.get("reference_only", []):
        rows.append({k: extra.get(k, "") for k in rows[0]} | {"candidate_id": extra["candidate_id"]})

    with args.out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    write_inventory(census, exclude, ov, args.out_inventory)
    write_planning(census, args.reachability, args.out_planning)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["disposition"]] = counts.get(r["disposition"], 0) + 1
    print(json.dumps({"rows": len(rows), "excluded_members": excluded, "dispositions": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
