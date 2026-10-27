#!/usr/bin/env python3
"""Validate the SHOP-OPERATING-LOOP-RECOVERY-001 audit package. Read-only except --write-json.

The governing ledger is ``CAPABILITY_LEDGER.csv``. ``CAPABILITY_LEDGER.json`` is
generated from it (``--write-json``) and must agree with it byte for byte.

Rules (each failure is one message; the exit code is 1 when any fire):

  ledger      duplicate candidate_id; blank required field; a value outside the
              classification vocabulary; more than 40 rows, more than 10 per
              track, more than 15 secondary rows, or under 60% LTB rows; a track
              with no row at all (a MISSING row counts)
  live        LIVE_* reachability without a file:line citation
  archive     ARCHIVED_RECOVERABLE without provenance or a 40-hex content digest
  complete    COMPLETE on a concept, document or missing artifact
  basis       disposition_basis under 20 characters
  authority   a non-NONE authority on a CONCEPT_ONLY or MISSING row: a concept
              decides nothing today, so its authority can only come from its name
  canonical   two RETAIN_CANONICAL rows holding the same non-NONE authority on
              the same MVS step (two owners for one decision)
  duplicate   overlap ``duplicate:<id>`` between unequal digests, or
              ``same-name-different-content:<path>@<hex>`` whose hex equals the
              row's own digest
  id-link     a JOB_IDENTITY_MAP.md link marked PROVEN without ``stored:`` and a
              file:line citation
  mvs         a step S1..S9 missing from MVS_GAP_MATRIX.md, a status outside
              AVAILABLE/ADAPT/BUILD/BLOCKED, or AVAILABLE without a ledger row
              disposed RETAIN_CANONICAL
  json        CSV and JSON ledgers disagree
  increment   RECOMMENDATION.md names other than exactly one
              ``RECOMMENDED_INCREMENT:`` line
  scope       evidence.json ``changed_paths`` lists a path outside the audit
              package, this tool, its test, or the PR's CBSP21 manifest

``--verify-digests`` also recomputes every luthiers-toolbox digest with
``git rev-parse <rev>:<path>`` when the object is present (skipped, not failed,
in a shallow clone).

Usage:
    python scripts/investigations/shop_operating_loop_ledger.py --package <dir> [--write-json] [--verify-digests]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = "shop_operating_loop_ledger_v1"
FIELDS = (
    "candidate_id", "capability_track", "repo", "path_or_ref", "artifact_type", "source_revision",
    "content_digest", "provenance", "reachability", "reachability_evidence", "completeness",
    "authority", "current_owner", "overlap_or_successor", "disposition", "disposition_basis",
    "mvs_step", "open_question",
)
TRACKS = ("A_JOB_IDENTITY", "B_ESTIMATE_ACTUAL", "C_KITS", "D_TIME_CAPTURE", "E_GUIDED_WORKFLOW")
REACHABILITY = {"LIVE_ROUTED", "LIVE_LIBRARY", "BUILT_DISCONNECTED", "ARCHIVED_RECOVERABLE",
                "CONCEPT_ONLY", "MISSING"}
COMPLETENESS = {"COMPLETE", "PARTIAL", "STUB", "UNKNOWN", "NOT_APPLICABLE"}
AUTHORITY = {"COMMERCIAL", "DESIGN", "EVIDENCE", "VALIDATION", "CAM", "SHOP_EXECUTION", "NONE"}
DISPOSITION = {"RETAIN_CANONICAL", "RECONNECT", "ADAPT", "REFERENCE_ONLY", "SUPERSEDED",
               "MISSING_BUILD", "OWNER_RULING_REQUIRED"}
MVS_STEPS = tuple(f"S{i}" for i in range(1, 10))
MVS_STATUS = {"AVAILABLE", "ADAPT", "BUILD", "BLOCKED"}
PRIMARY_REPO = "luthiers-toolbox"
SECONDARY_REPOS = {"CNC-Production-Shop", "CAM-Assist-Blueprint", "CAM-Creation-Studio"}
MAX_ROWS, MAX_PER_TRACK, MAX_SECONDARY, MIN_PRIMARY_SHARE = 40, 10, 15, 0.60
PACKAGE_PREFIX = "docs/investigations/shop-operating-loop-recovery_2026-10-26/"
ALLOWED_PATHS = {
    "scripts/investigations/shop_operating_loop_ledger.py",
    "services/api/tests/test_shop_operating_loop_recovery_evidence.py",
    ".cbsp21/patches/shop-operating-loop-recovery-001.json",
}
CONCEPT_TYPES = ("doc:", "missing", "concept", "screenshot", "backlog")

_FILE_LINE = re.compile(r"[\w./-]+\.\w+:\d+")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_SAME_NAME = re.compile(r"same-name-different-content:\S+@([0-9a-f]{40})")
_DUPLICATE = re.compile(r"\bduplicate:(SOL-[A-E]\d{2})\b")
_TABLE_ROW = re.compile(r"^\|(.+)\|\s*$")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"{path.name}: header must be exactly {','.join(FIELDS)}")
        return list(reader)


def build_json(rows: list[dict]) -> str:
    payload = {"schema_version": SCHEMA_VERSION, "row_count": len(rows), "rows": rows}
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _table(text: str) -> list[list[str]]:
    """Body rows of every Markdown table in ``text`` (header and separator rows skipped)."""
    rows: list[list[str]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _TABLE_ROW.match(line.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if nxt.startswith("|") and set(nxt.replace("|", "")) <= set("-: ") and nxt.strip("|"):
            continue  # header row
        rows.append(cells)
    return rows


def validate_rows(rows: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    by_id = {r.get("candidate_id", ""): r for r in rows}
    for r in rows:
        cid = r.get("candidate_id", "") or "<blank>"
        if cid in seen:
            errors.append(f"ledger: duplicate candidate_id {cid}")
        seen.add(cid)
        for f in FIELDS:
            if not (r.get(f) or "").strip():
                errors.append(f"ledger: {cid} blank field {f}")
        for field, vocab in (("capability_track", set(TRACKS)), ("reachability", REACHABILITY),
                             ("completeness", COMPLETENESS), ("authority", AUTHORITY),
                             ("disposition", DISPOSITION), ("mvs_step", set(MVS_STEPS))):
            if r.get(field) and r[field] not in vocab:
                errors.append(f"ledger: {cid} {field}={r[field]!r} outside vocabulary")
        if r.get("repo") not in SECONDARY_REPOS | {PRIMARY_REPO}:
            errors.append(f"ledger: {cid} repo {r.get('repo')!r} outside audit boundary")
        reach, atype = r.get("reachability", ""), r.get("artifact_type", "")
        if reach.startswith("LIVE_") and not _FILE_LINE.search(r.get("reachability_evidence", "")):
            errors.append(f"live: {cid} {reach} has no file:line reachability evidence")
        if reach == "ARCHIVED_RECOVERABLE" and not (
                (r.get("provenance") or "").strip() and _HEX40.match(r.get("content_digest", ""))):
            errors.append(f"archive: {cid} ARCHIVED_RECOVERABLE needs provenance and a 40-hex digest")
        if reach != "MISSING" and not _HEX40.match(r.get("content_digest", "")):
            errors.append(f"ledger: {cid} content_digest must be a 40-hex git object id")
        if r.get("completeness") == "COMPLETE" and (
                reach in {"CONCEPT_ONLY", "MISSING"} or atype.startswith(CONCEPT_TYPES)):
            errors.append(f"complete: {cid} COMPLETE cites only a concept/document")
        if len((r.get("disposition_basis") or "").strip()) < 20:
            errors.append(f"basis: {cid} disposition_basis is not an evidence basis")
        if reach in {"CONCEPT_ONLY", "MISSING"} and r.get("authority") != "NONE":
            errors.append(f"authority: {cid} {reach} row claims {r.get('authority')} authority")
        overlap = r.get("overlap_or_successor", "")
        for other in _DUPLICATE.findall(overlap):
            peer = by_id.get(other)
            if peer is None or peer.get("content_digest") != r.get("content_digest"):
                errors.append(f"duplicate: {cid} called duplicate of {other} without equal content digest")
        for hexd in _SAME_NAME.findall(overlap):
            if hexd == r.get("content_digest"):
                errors.append(f"duplicate: {cid} same-name-different-content but digests are equal")
    canon: dict[tuple[str, str], str] = {}
    for r in rows:
        if r.get("disposition") == "RETAIN_CANONICAL" and r.get("authority", "NONE") != "NONE":
            key = (r.get("authority", ""), r.get("mvs_step", ""))
            if key in canon:
                errors.append(f"canonical: {canon[key]} and {r['candidate_id']} both canonical "
                              f"{key[0]} owners for {key[1]}")
            canon.setdefault(key, r.get("candidate_id", ""))
    if len(rows) > MAX_ROWS:
        errors.append(f"ledger: {len(rows)} rows exceeds the {MAX_ROWS}-row cap")
    for t in TRACKS:
        n = sum(1 for r in rows if r.get("capability_track") == t)
        if n == 0:
            errors.append(f"ledger: track {t} has neither a candidate nor a MISSING row")
        if n > MAX_PER_TRACK:
            errors.append(f"ledger: track {t} has {n} rows (cap {MAX_PER_TRACK})")
    secondary = sum(1 for r in rows if r.get("repo") in SECONDARY_REPOS)
    if secondary > MAX_SECONDARY:
        errors.append(f"ledger: {secondary} secondary rows (cap {MAX_SECONDARY})")
    if rows and sum(1 for r in rows if r.get("repo") == PRIMARY_REPO) / len(rows) < MIN_PRIMARY_SHARE:
        errors.append("ledger: luthiers-toolbox share under 60%")
    return errors


def validate_id_links(text: str) -> list[str]:
    errors: list[str] = []
    for cells in _table(text):
        if len(cells) < 4 or cells[2] not in {"PROVEN", "UNKNOWN", "ABSENT"}:
            continue
        if cells[2] == "PROVEN" and not (cells[3].startswith("stored:") and _FILE_LINE.search(cells[3])):
            errors.append(f"id-link: {cells[0]} -> {cells[1]} PROVEN without a stored field citation")
    return errors


def validate_mvs(text: str, rows: list[dict]) -> list[str]:
    errors: list[str] = []
    by_id = {r["candidate_id"]: r for r in rows}
    found: dict[str, list[str]] = {}
    for cells in _table(text):
        if cells and cells[0] in MVS_STEPS:
            found[cells[0]] = cells
    for step in MVS_STEPS:
        cells = found.get(step)
        if cells is None:
            errors.append(f"mvs: {step} missing from MVS_GAP_MATRIX.md")
            continue
        status = cells[2] if len(cells) > 2 else ""
        if status not in MVS_STATUS:
            errors.append(f"mvs: {step} status {status!r} not AVAILABLE/ADAPT/BUILD/BLOCKED")
        if status == "AVAILABLE":
            owner = by_id.get(cells[3] if len(cells) > 3 else "")
            if owner is None or owner.get("disposition") != "RETAIN_CANONICAL":
                errors.append(f"mvs: {step} AVAILABLE without a RETAIN_CANONICAL owning artifact")
    return errors


def validate_increment(text: str) -> list[str]:
    n = sum(1 for line in text.splitlines() if line.startswith("RECOMMENDED_INCREMENT:"))
    return [] if n == 1 else [f"increment: RECOMMENDATION.md names {n} increments (exactly one required)"]


def validate_scope(evidence: dict) -> list[str]:
    errors: list[str] = []
    for p in evidence.get("changed_paths", []):
        if not (p.startswith(PACKAGE_PREFIX) or p in ALLOWED_PATHS):
            errors.append(f"scope: {p} is outside the evidence-only scope")
    if not evidence.get("changed_paths"):
        errors.append("scope: evidence.json declares no changed_paths")
    return errors


def verify_digests(rows: list[dict], repo_root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    checked = 0
    for r in rows:
        if r["repo"] != PRIMARY_REPO or r["reachability"] == "MISSING":
            continue
        spec = f"{r['source_revision']}:{r['path_or_ref']}"
        proc = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--verify", "-q", spec],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            continue  # object absent (shallow clone): not evidence either way
        checked += 1
        if proc.stdout.strip() != r["content_digest"]:
            errors.append(f"digest: {r['candidate_id']} recorded {r['content_digest']} != {proc.stdout.strip()}")
    return errors, checked


def validate_package(pkg: Path) -> list[str]:
    rows = read_csv(pkg / "CAPABILITY_LEDGER.csv")
    errors = validate_rows(rows)
    json_path = pkg / "CAPABILITY_LEDGER.json"
    if not json_path.exists() or json_path.read_text(encoding="utf-8") != build_json(rows):
        errors.append("json: CAPABILITY_LEDGER.json disagrees with CAPABILITY_LEDGER.csv")
    errors += validate_id_links((pkg / "JOB_IDENTITY_MAP.md").read_text(encoding="utf-8"))
    errors += validate_mvs((pkg / "MVS_GAP_MATRIX.md").read_text(encoding="utf-8"), rows)
    errors += validate_increment((pkg / "RECOMMENDATION.md").read_text(encoding="utf-8"))
    errors += validate_scope(json.loads((pkg / "evidence.json").read_text(encoding="utf-8")))
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--package", required=True, type=Path)
    ap.add_argument("--write-json", action="store_true", help="regenerate CAPABILITY_LEDGER.json from the CSV")
    ap.add_argument("--verify-digests", action="store_true")
    args = ap.parse_args(argv)
    if args.write_json:
        rows = read_csv(args.package / "CAPABILITY_LEDGER.csv")
        with (args.package / "CAPABILITY_LEDGER.json").open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(build_json(rows))
    errors = validate_package(args.package)
    if args.verify_digests:
        digest_errors, checked = verify_digests(read_csv(args.package / "CAPABILITY_LEDGER.csv"),
                                                Path(__file__).resolve().parents[2])
        errors += digest_errors
        print(f"digests verified: {checked}")
    for e in errors:
        print(e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
