#!/usr/bin/env python3
"""Build RECOVERY_LEDGER.csv from the bundle census + explicit overrides. Read-only.

Input: the JSON written by ``march_2026_bundle_census.py`` and an overrides JSON
(``LEDGER_OVERRIDES.json``) committed beside the ledger. One row per unique
content (LF-normalised Git blob), listing every source that carries it.

Automatic disposition (overrides win, and every override records its reason):

  LIVE_IDENTICAL                         -> LIVE_INTEGRATED
  ARCHIVE_ONLY                           -> ARCHIVED_COMPLETE
  HISTORY_ONLY (entered Git, later left the ref), by same-name live files:
    the first-commit path is one of them -> LIVE_MODIFIED (path lineage)
    exactly one, first path gone         -> LIVE_MODIFIED (name only)
    two or more                          -> UNRESOLVED (ambiguous; never guessed)
    none (same name archived, or absent) -> UNRESOLVED
  EXTERNAL_ONLY                          -> EXTERNAL_ONLY

Every row also carries a proof class, so a reader can tell observation from
inference from ruling:

  MECHANICALLY_VERIFIED  content-hash presence/absence against Git
  HEURISTIC_CANDIDATE    inferred from a path or a name, not from content
  MANUALLY_ADJUDICATED   an override decided it (``override_id`` names which)
  SOURCE_UNAVAILABLE     referenced, but no content survives in any source
  UNRESOLVED             the evidence does not decide it

``automatic_disposition`` keeps what the rule alone gave, so an override's
effect stays visible.

Rows whose member path matches an ``exclude`` pattern (third-party saved web
pages) are counted but not ledgered.

Overrides are keyed ``by_blob`` (preferred) or ``by_name`` (basename). A
``by_blob`` entry wins. The overrides file is refused (exit 2, nothing written)
when it repeats a key, gives a disposition outside the allowed set or a reason
under 20 characters, names a blob or basename the census does not contain, or
keys ``by_name`` on a basename that maps to more than one distinct blob (that
would stamp one reason on different files). ``PLANNING_RECONCILIATION.csv`` still joins claims to sources
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
ALLOWED_DISPOSITIONS = {
    "LIVE_INTEGRATED", "LIVE_MODIFIED", "PARTIALLY_INTEGRATED", "ARCHIVED_COMPLETE",
    "ARCHIVED_INCOMPLETE", "EXTERNAL_ONLY", "LOST_REFERENCE_ONLY", "SUPERSEDED",
    "RECOVERED_FEATURE_CANDIDATE", "RECOVERED_SAFETY_FIX_CANDIDATE", "DUPLICATE", "UNRESOLVED",
}
ARCHIVE_PREFIXES = ("docs/archive/", "archive/")


class OverrideError(ValueError):
    pass


def _no_duplicate_keys(pairs: list) -> dict:
    seen: dict = {}
    for key, value in pairs:
        if key in seen:
            raise OverrideError(f"duplicate key {key!r}")
        seen[key] = value
    return seen


def basename(member: dict) -> str:
    return PurePosixPath(member["member"].split("!/")[-1]).name


def parse_overrides(path: Path) -> dict:
    """Parse the overrides file, refusing invalid JSON and repeated keys."""
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise OverrideError(f"not valid JSON: {exc}") from exc


def check_overrides(ov: dict, by_blob: dict[str, list[dict]]) -> None:
    """Check the overrides against the census they will be applied to."""
    names: dict[str, set[str]] = {}
    for blob, group in by_blob.items():
        names.setdefault(basename(group[0]), set()).add(blob)
    problems = []
    for kind in ("by_name", "by_blob"):
        for key, o in ov.get(kind, {}).items():
            if o.get("disposition") not in ALLOWED_DISPOSITIONS:
                problems.append(f"{kind}[{key}]: disposition {o.get('disposition')!r} not allowed")
            if len(o.get("reason", "")) < 20:
                problems.append(f"{kind}[{key}]: reason missing or under 20 characters")
            known = names.get(key, set()) if kind == "by_name" else ({key} if key in by_blob else set())
            if not known:
                problems.append(f"{kind}[{key}]: matches nothing in the census (stale override)")
            elif len(known) > 1:
                problems.append(f"{kind}[{key}]: ambiguous, matches {len(known)} blobs "
                                f"{sorted(known)} (re-key by_blob)")
    ids = [r.get("candidate_id", "") for r in ov.get("reference_only", [])]
    for rid in sorted({i for i in ids if ids.count(i) > 1 or not re.fullmatch(r"MC-R\d\d", i)}):
        problems.append(f"reference_only[{rid}]: duplicate or not of the form MC-Rnn")
    for r in ov.get("reference_only", []):
        if r.get("disposition") not in ALLOWED_DISPOSITIONS:
            problems.append(f"reference_only[{r.get('candidate_id')}]: disposition not allowed")
    if problems:
        raise OverrideError("; ".join(problems))


def automatic(member: dict) -> tuple[str, str, str]:
    """(disposition, proof_class, proof_method) from the content-hash state alone."""
    state = member["state"]
    if state in ("LIVE_IDENTICAL", "ARCHIVE_ONLY"):
        where = (member["live_paths"] or member["archive_paths"])[0]
        return AUTO[state], "MECHANICALLY_VERIFIED", f"content blob on the census ref at {where}"
    if state == "EXTERNAL_ONLY":
        return AUTO[state], "MECHANICALLY_VERIFIED", "content blob in no commit reachable from any ref"
    same = member["name_only_matches_on_ref"]
    live = [p for p in same if not p.startswith(ARCHIVE_PREFIXES)]
    if member["first_path"] in live:
        return ("LIVE_MODIFIED", "HEURISTIC_CANDIDATE",
                f"first-commit path still live with other content: {member['first_path']}")
    if len(live) == 1:
        return "LIVE_MODIFIED", "HEURISTIC_CANDIDATE", f"only same-name live file: {live[0]}"
    if live:
        return "UNRESOLVED", "UNRESOLVED", f"ambiguous: {len(live)} same-name live files, first path gone"
    if same:
        return "UNRESOLVED", "UNRESOLVED", "same name survives only in archive paths, with other content"
    return "UNRESOLVED", "UNRESOLVED", "entered Git and left it; no same-name file on the ref"


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
        by_name.setdefault(basename(m), []).append(m)
    src_path = {s["source_id"]: s["path"] for s in census["sources"]}
    fields = ["item", "claimed_artifact", "claimed_state", "located_source_by_name", "source_content_states",
              "entered_git", "current_live_path", "archive_path", "external_only_source", "current_status",
              "confidence", "proof_class"]
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
                "confidence": "reachability: heuristic; bundle link: by file name" if hits
                              else "reachability: heuristic; no bundle carries this name",
                "proof_class": r["proof_class"],
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
    try:
        ov = parse_overrides(args.overrides)
        exclude = [re.compile(p) for p in ov.get("exclude", [])]
        by_blob: dict[str, list[dict]] = {}
        excluded = 0
        for m in census["members"]:
            if any(p.search(m["member"]) for p in exclude):
                excluded += 1
                continue
            by_blob.setdefault(m["blob_lf"], []).append(m)
        check_overrides(ov, by_blob)
    except OverrideError as exc:
        print(f"overrides refused: {exc}", file=sys.stderr)
        return 2

    src_path = {s["source_id"]: s["path"] for s in census["sources"]}
    rows = []
    for i, (blob, group) in enumerate(sorted(by_blob.items(), key=lambda kv: (kv[1][0]["source_id"], kv[1][0]["member"])), 1):
        first = group[0]
        name = basename(first)
        state = first["state"]
        auto_disp, proof_class, method = automatic(first)
        disp, reason, override_id = auto_disp, "", ""
        override = ov["by_blob"].get(blob)
        if override:
            override_id = f"by_blob:{blob[:8]}"
        elif name in ov["by_name"]:
            override, override_id = ov["by_name"][name], f"by_name:{name}"
        if override:
            disp, reason, proof_class = override["disposition"], override["reason"], "MANUALLY_ADJUDICATED"
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
            "same_name_on_main_different_content": ";".join(first["name_only_matches_on_ref"][:3]),
            "unique_relative_to_main": "no" if first["live_paths"] else "yes",
            "safety_relevance": (override or {}).get("safety") or "",
            "disposition": disp,
            "disposition_reason": reason or f"automatic from census state {state}",
            "confidence": (override or {}).get("confidence", "content-hash" if state != "HISTORY_ONLY" else "content-hash; current form inferred by path or name"),
            "follow_up_order": (override or {}).get("follow_up", ""),
            "proof_class": proof_class,
            "proof_method": method,
            "automatic_disposition": auto_disp,
            "override_id": override_id,
        })
    for extra in ov.get("reference_only", []):
        unresolved = extra["disposition"] == "UNRESOLVED"
        rows.append({k: extra.get(k, "") for k in rows[0]} | {
            "candidate_id": extra["candidate_id"],
            "proof_class": "UNRESOLVED" if unresolved else "SOURCE_UNAVAILABLE",
            "proof_method": "recorded, not walked" if unresolved else "import references to content no source holds",
            "override_id": f"reference_only:{extra['candidate_id']}",
        })

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
