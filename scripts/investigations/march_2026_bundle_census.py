#!/usr/bin/env python3
"""Inventory March 2026 Claude output bundles against Git. Read-only evidence tooling.

For every source named on the command line (a ZIP, or a folder), hash the source,
walk its members (descending into nested ZIPs in memory -- nothing is extracted
to disk), and look each member's content up in the repository by Git blob hash:

* on ``--ref`` (e.g. origin/main) at a live path or an archive path, or
* anywhere in history reachable from any ref (first commit recorded), or
* nowhere -- external only.

Both the raw bytes and an LF-normalised copy are hashed, because the repository
stores text with ``eol=lf``. A name-only match (same basename on the ref,
different content) is reported as a hint and never treated as presence.

Usage:
    python scripts/investigations/march_2026_bundle_census.py --repo . --ref origin/main \
        --out-json census.json --out-bundles SOURCE_BUNDLE_INVENTORY.csv \
        --out-members members.csv  SRC_ID=path [SRC_ID=path ...]

No network. Writes only the three named outputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ARCHIVE_PREFIXES = ("docs/archive/", "archive/")
SKIP_SUFFIXES = (".7z",)  # repository snapshots: recorded, not walked


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          check=True).stdout.decode("utf-8", "surrogateescape")


@dataclass
class RepoIndex:
    ref_paths: dict[str, list[str]]          # blob -> paths on ref
    ref_basenames: dict[str, list[str]]      # basename -> paths on ref
    first_seen: dict[str, tuple[str, str, str]]  # blob -> (commit, date, path)

    @classmethod
    def build(cls, repo: Path, ref: str) -> "RepoIndex":
        ref_paths: dict[str, list[str]] = {}
        ref_basenames: dict[str, list[str]] = {}
        for line in git(repo, "ls-tree", "-r", "--full-tree", ref).splitlines():
            meta, path = line.split("\t", 1)
            _, kind, sha = meta.split()
            if kind != "blob":
                continue
            ref_paths.setdefault(sha, []).append(path)
            ref_basenames.setdefault(PurePosixPath(path).name, []).append(path)
        first_seen: dict[str, tuple[str, str, str]] = {}
        commit = date = ""
        log = git(repo, "log", "--all", "--reverse", "--no-renames", "--raw", "--no-abbrev",
                  "--format=C %h %ad", "--date=short")
        for line in log.splitlines():
            if line.startswith("C "):
                _, commit, date = line.split(" ", 2)
            elif line.startswith(":"):
                meta, path = line.split("\t", 1)
                new_sha = meta.split()[3]
                if new_sha.strip("0") and new_sha not in first_seen:
                    first_seen[new_sha] = (commit, date, path)
        return cls(ref_paths, ref_basenames, first_seen)


def walk_zip(data: bytes, prefix: str, nested_out: list):
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = f"{prefix}{info.filename}"
            body = zf.read(info)
            if info.filename.lower().endswith(".zip"):
                nested_out.append(name)
                yield from walk_zip(body, f"{name}!/", nested_out)
            else:
                yield name, body


def walk_source(path: Path, nested_out: list):
    if path.is_dir():
        for p in sorted(path.rglob("*")):
            if p.is_file():
                yield p.relative_to(path).as_posix(), p.read_bytes()
    elif path.suffix.lower() == ".zip":
        yield from walk_zip(path.read_bytes(), "", nested_out)
    else:
        raise SystemExit(f"unsupported source {path}")


def classify(blob_raw: str, blob_lf: str, base: str, idx: RepoIndex) -> dict:
    hit = next((b for b in (blob_lf, blob_raw) if b in idx.ref_paths), None)
    seen = next((b for b in (blob_lf, blob_raw) if b in idx.first_seen), None)
    paths = idx.ref_paths.get(hit, []) if hit else []
    live = [p for p in paths if not p.startswith(ARCHIVE_PREFIXES)]
    archived = [p for p in paths if p.startswith(ARCHIVE_PREFIXES)]
    same_name = [p for p in idx.ref_basenames.get(base, []) if p not in paths]
    if live:
        state = "LIVE_IDENTICAL"
    elif archived:
        state = "ARCHIVE_ONLY"
    elif seen:
        state = "HISTORY_ONLY"
    else:
        state = "EXTERNAL_ONLY"
    first = idx.first_seen.get(seen) if seen else None
    return {
        "state": state,
        "live_paths": live,
        "archive_paths": archived,
        "first_commit": first[0] if first else "",
        "first_date": first[1] if first else "",
        "first_path": first[2] if first else "",
        "name_only_matches_on_ref": same_name,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--out-bundles", type=Path, required=True)
    ap.add_argument("--out-members", type=Path, required=True)
    ap.add_argument("sources", nargs="+", help="SRC_ID=path")
    args = ap.parse_args(argv)

    idx = RepoIndex.build(args.repo, args.ref)
    report = {"schema": "march-2026-bundle-census/1", "ref": args.ref,
              "ref_sha": git(args.repo, "rev-parse", args.ref).strip(), "sources": []}
    member_rows = []
    for spec in args.sources:
        sid, raw_path = spec.split("=", 1)
        path = Path(raw_path)
        if not path.exists():
            print(f"{sid}: missing {path}", file=sys.stderr)
            return 2
        nested: list[str] = []
        src_sha = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
        members = []
        skipped = []
        for name, body in walk_source(path, nested):
            if name.lower().endswith(SKIP_SUFFIXES):
                skipped.append(name)
                continue
            b_raw, b_lf = git_blob(body), git_blob(lf(body))
            info = classify(b_raw, b_lf, PurePosixPath(name).name, idx)
            row = {"source_id": sid, "member": name, "bytes": len(body),
                   "sha256": hashlib.sha256(body).hexdigest(), "blob_raw": b_raw, "blob_lf": b_lf, **info}
            members.append(row)
            member_rows.append(row)
        counts: dict[str, int] = {}
        for m in members:
            counts[m["state"]] = counts.get(m["state"], 0) + 1
        top = sorted({m["member"].split("/")[0].split("!")[0] for m in members})
        report["sources"].append({
            "source_id": sid, "path": path.name, "kind": "folder" if path.is_dir() else "zip",
            "sha256": src_sha, "members": len(members), "nested_archives": nested,
            "skipped_snapshots": skipped, "states": counts, "top_level": top,
        })

    args.out_json.write_text(json.dumps({**report, "members": member_rows}, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8", newline="\n")
    with args.out_members.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["source_id", "member", "bytes", "sha256", "blob_lf", "state", "live_paths",
                    "archive_paths", "first_commit", "first_date", "first_path", "name_only_matches_on_ref"])
        for r in member_rows:
            w.writerow([r["source_id"], r["member"], r["bytes"], r["sha256"], r["blob_lf"], r["state"],
                        ";".join(r["live_paths"]), ";".join(r["archive_paths"]), r["first_commit"],
                        r["first_date"], r["first_path"], ";".join(r["name_only_matches_on_ref"][:3])])
    with args.out_bundles.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["source_id", "path", "kind", "sha256", "members", "nested_archive_count",
                    "live_identical", "archive_only", "history_only", "external_only",
                    "repository_copy_present", "repository_copy_complete", "top_level"])
        for s in report["sources"]:
            c = s["states"]
            ext = c.get("EXTERNAL_ONLY", 0)
            present = s["members"] - ext
            w.writerow([s["source_id"], s["path"], s["kind"], s["sha256"], s["members"],
                        len(s["nested_archives"]), c.get("LIVE_IDENTICAL", 0), c.get("ARCHIVE_ONLY", 0),
                        c.get("HISTORY_ONLY", 0), ext,
                        "yes" if present else "no", "yes" if s["members"] and not ext else "no",
                        ";".join(s["top_level"])[:300]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
