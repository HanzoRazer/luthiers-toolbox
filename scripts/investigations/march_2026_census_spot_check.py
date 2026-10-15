#!/usr/bin/env python3
"""Independent spot-check of RECOVERY_LEDGER.csv. Read-only.

Re-derives a deterministic sample of ledger rows by a different route from the
census tool, so a shared bug cannot pass both:

* the member bytes are re-read from the original bundle (located by name under
  ``--search``; a ZIP must also match the inventory sha256) and re-hashed;
* presence on the census ref is checked with ``git rev-parse <ref>:<path>``,
  not ``ls-tree``;
* absence from history is checked with ``git log --all --find-object``, not
  the ``log --raw`` scan the census tool uses;
* a heuristic successor path is checked to exist on the ref with other content,
  and the commits that added or removed the blob are listed for the reader.

Sample (all selections are by sorted sha256, so a rerun picks the same rows):
the first five MECHANICALLY_VERIFIED rows, the first five HEURISTIC_CANDIDATE
rows, every MANUALLY_ADJUDICATED / SOURCE_UNAVAILABLE row, every EXTERNAL_ONLY
row, and the rows behind a recovery-order recommendation.

Prints a Markdown table: candidate, class, check, expected, actual, result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import subprocess
import sys
import zipfile
from pathlib import Path

HIGH_PRIORITY = {"MC-060", "MC-113", "MC-R01", "MC-R02", "MC-R03", "MC-R04", "MC-R05"}


def git(repo: Path, *args: str) -> tuple[int, str]:
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    return run.returncode, run.stdout.decode("utf-8", "replace").strip()


def blob_of(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


class Bundles:
    def __init__(self, inventory: list[dict], roots: list[Path]):
        self.where: dict[str, Path] = {}
        self.note: dict[str, str] = {}
        for row in inventory:
            name, sha = row["filename"], row["sha256"]
            hits = [p for r in roots for p in (r / name,) if p.exists()]
            for p in hits:
                if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() != sha:
                    continue
                self.where[row["source_id"]] = p
                break
            else:
                self.note[row["source_id"]] = "not found" if not hits else "found, sha256 differs"

    def read(self, source_id: str, member: str) -> bytes | None:
        path = self.where.get(source_id)
        if path is None:
            return None
        parts = member.split("!/")
        if path.is_dir():
            data, inner = (path / parts[0]).read_bytes(), parts[1:]
        else:
            data, inner = path.read_bytes(), parts
        for part in inner:
            data = zipfile.ZipFile(io.BytesIO(data)).read(part)
        return data


def checks(row: dict, repo: Path, ref: str, bundles: Bundles) -> list[tuple[str, str, str]]:
    """(check, expected, actual) triples for one ledger row."""
    out = []
    blob = row["content_blob_lf"]
    if blob:
        source = row["source_bundles"].split(";")[0]
        data = bundles.read(source, row["original_path"])
        if data is None:
            out.append(("member re-read from bundle", blob[:8], f"bundle {source} {bundles.note.get(source, '?')}"))
        else:
            out.append(("member re-read from bundle", blob[:8], blob_of(data.replace(b"\r\n", b"\n"))[:8]))
    state = row["census_state"]
    for path in filter(None, row["current_live_path"].split(";") + row["archive_path"].split(";")):
        _, got = git(repo, "rev-parse", f"{ref}:{path}")
        out.append((f"rev-parse {ref[:8]}:{path}", blob[:8], got[:8] or "absent"))
    if state in ("EXTERNAL_ONLY", "HISTORY_ONLY"):
        _, log = git(repo, "log", "--all", "--format=%h", f"--find-object={blob}")
        commits = sorted(set(log.split()))
        expected = "no commit" if state == "EXTERNAL_ONLY" else "at least one commit"
        out.append(("log --all --find-object", expected, ", ".join(commits[:4]) or "no commit"))
    if row["proof_class"] == "HEURISTIC_CANDIDATE" and row["census_state"] == "HISTORY_ONLY":
        successor = row["proof_method"].rsplit(": ", 1)[-1]
        _, got = git(repo, "rev-parse", f"{ref}:{successor}")
        out.append((f"successor {successor} on ref", "present, other content",
                    "absent" if not got or "fatal" in got else ("SAME content" if got == blob else "present, other content")))
    return out


def verdict(check: str, expected: str, actual: str) -> str:
    if check.startswith("successor"):
        return "PASS" if actual == expected else "FAIL"
    if check == "log --all --find-object":
        return "PASS" if (actual == "no commit") == (expected == "no commit") else "FAIL"
    if actual.startswith("bundle "):
        return "NOT CHECKABLE"
    return "PASS" if actual == expected else "FAIL"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--census-dir", type=Path, required=True)
    ap.add_argument("--search", type=Path, action="append", default=[],
                    help="directory holding bundles (repeatable)")
    args = ap.parse_args(argv)
    ledger = list(csv.DictReader((args.census_dir / "RECOVERY_LEDGER.csv").open(encoding="utf-8", newline="")))
    inventory = list(csv.DictReader((args.census_dir / "SOURCE_BUNDLE_INVENTORY.csv").open(encoding="utf-8", newline="")))
    bundles = Bundles(inventory, args.search)
    ref = git(args.repo, "rev-parse", args.ref)[1]

    by_sha = sorted(ledger, key=lambda r: (r["sha256"], r["candidate_id"]))
    sample: dict[str, str] = {}
    for cls in ("MECHANICALLY_VERIFIED", "HEURISTIC_CANDIDATE"):
        for r in [r for r in by_sha if r["proof_class"] == cls][:5]:
            sample.setdefault(r["candidate_id"], f"first five {cls}")
    for r in ledger:
        if r["proof_class"] in ("MANUALLY_ADJUDICATED", "SOURCE_UNAVAILABLE"):
            sample.setdefault(r["candidate_id"], "every override")
        if r["census_state"] == "EXTERNAL_ONLY":
            sample.setdefault(r["candidate_id"], "every external-only")
        if r["candidate_id"] in HIGH_PRIORITY:
            sample[r["candidate_id"]] += "; recovery order"

    print(f"Bundles located: {len(bundles.where)} of {len(inventory)}. Ref: {ref[:8]}.\n")
    print("| Candidate | File | Proof class | Selected as | Check | Expected | Actual | Result |")
    print("|---|---|---|---|---|---|---|---|")
    tally: dict[str, int] = {}
    for r in ledger:
        if r["candidate_id"] not in sample:
            continue
        rows = checks(r, args.repo, ref, bundles) or [("no content to check", "reference only", "reference only")]
        for check, expected, actual in rows:
            result = verdict(check, expected, actual) if check != "no content to check" else "N/A"
            tally[result] = tally.get(result, 0) + 1
            print(f"| {r['candidate_id']} | `{r['filename']}` | {r['proof_class']} | {sample[r['candidate_id']]} "
                  f"| {check} | {expected} | {actual} | {result} |")
    print(f"\nRows sampled: {len(sample)}. Checks: " + ", ".join(f"{k} {v}" for k, v in sorted(tally.items())))
    return 1 if tally.get("FAIL") else 0


if __name__ == "__main__":
    sys.exit(main())
