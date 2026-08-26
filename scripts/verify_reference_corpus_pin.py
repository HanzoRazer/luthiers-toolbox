#!/usr/bin/env python3
"""Resolve and verify this repository's reference-corpus dependency pins.

Toolbox holds no copy of any canonical corpus. It holds pins. This utility proves a
pin still resolves to the canonical release it names, and that the release still
reports the identity, counts and digests the pin was written against.

    python scripts/verify_reference_corpus_pin.py
    python scripts/verify_reference_corpus_pin.py --corpus-repo /path/to/clone

Resolution order:
  1. A local clone, if --corpus-repo is given (offline, no credentials).
  2. The GitHub API via `gh`, required because the canonical repository is private.

It FAILS CLOSED: any mismatch is an error, and an unresolvable pin is reported as
unresolved rather than silently treated as verified.

Exit codes: 0 verified · 1 mismatch · 2 unresolved.

Ported from luthier-acoustics-lab; the verification semantics are deliberately
identical so both consumers of mb-sound/v1.0.0 verify it the same way.

This utility performs no scientific computation. It compares metadata and hashes
only; it never reads, interprets, or recalculates a measurement.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_GLOB = "docs/reference/**/*CORPUS_DEPENDENCY.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fetch_local(repo: Path, rel_path: str) -> bytes | None:
    target = repo / rel_path
    return target.read_bytes() if target.is_file() else None


def _fetch_gh(repository: str, rel_path: str, ref: str) -> bytes | None:
    """Fetch raw manifest bytes so the digest can be checked over exactly what shipped."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repository}/contents/{rel_path}?ref={ref}", "-q", ".content"],
            capture_output=True, text=True, timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return base64.b64decode(result.stdout.strip())
    except Exception:
        return None


def verify(pin_path: Path, corpus_repo: Path | None) -> int:
    pin = _load(pin_path)
    try:
        rel = pin_path.relative_to(ROOT)
    except ValueError:
        # A pin supplied from outside the repository tree (e.g. a test fixture).
        rel = pin_path

    print(f"\n== {rel} ==")
    print(f"   corpus     : {pin['corpus_id']} @ {pin['release_tag']}")
    print(f"   repository : {pin['canonical_repository']}")
    print(f"   commit     : {pin['canonical_commit_sha'][:12]}")
    print(f"   records    : {pin['record_count']}")

    manifest_path = pin["manifest_path"]
    raw: bytes | None = None
    via = ""

    if corpus_repo is not None:
        raw = _fetch_local(corpus_repo, manifest_path)
        if raw is not None:
            via = f"local clone {corpus_repo}"
    if raw is None:
        raw = _fetch_gh(pin["canonical_repository"], manifest_path, pin["release_tag"])
        if raw is not None:
            via = "gh api"

    if raw is None:
        print("   UNRESOLVED — could not reach the canonical release manifest.")
        print("   This is not proof the pin is wrong; it is proof it was not checked.")
        print(f"   Try: --corpus-repo <clone of {pin['canonical_repository']}>")
        return 2

    print(f"   resolved via: {via}")

    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"   MISMATCH — canonical manifest is not valid JSON: {exc}")
        return 1

    actual_manifest_digest = hashlib.sha256(raw).hexdigest()
    pkg = manifest.get("package", {})
    src = manifest.get("source_provenance", {})
    gate = manifest.get("parity_gate", {})

    checks: list[tuple[str, bool, str]] = [
        ("release_tag",
         manifest.get("release_id") == pin["release_tag"],
         f"{manifest.get('release_id')} vs {pin['release_tag']}"),
        ("release_version",
         manifest.get("release_version") == pin["release_version"],
         f"{manifest.get('release_version')} vs {pin['release_version']}"),
        ("corpus_id",
         manifest.get("cohort_id") == pin["corpus_id"],
         f"{manifest.get('cohort_id')} vs {pin['corpus_id']}"),
        ("provenance_class",
         manifest.get("provenance_class") == pin["provenance_class"],
         f"{manifest.get('provenance_class')} vs {pin['provenance_class']}"),
        ("content_commit_sha",
         str(pkg.get("revision", "")).startswith(pin["content_commit_sha"]),
         f"{pkg.get('revision')} vs {pin['content_commit_sha']}"),
        ("record_count",
         pkg.get("record_count") == pin["record_count"],
         f"{pkg.get('record_count')} vs {pin['record_count']}"),
        ("envelope_count",
         pkg.get("envelope_count") == pin["envelope_count"],
         f"{pkg.get('envelope_count')} vs {pin['envelope_count']}"),
        ("corpus_digest_sha256",
         pkg.get("dataset_digest_sha256") == pin["corpus_digest_sha256"],
         f"{str(pkg.get('dataset_digest_sha256'))[:16]}… vs {pin['corpus_digest_sha256'][:16]}…"),
        ("manifest_digest_sha256",
         actual_manifest_digest == pin["manifest_digest_sha256"],
         f"{actual_manifest_digest[:16]}… vs {pin['manifest_digest_sha256'][:16]}…"),
        ("schema_version",
         pkg.get("extension_schema") == pin["schema_version"],
         f"{pkg.get('extension_schema')} vs {pin['schema_version']}"),
        ("envelope_schema",
         pkg.get("envelope_schema") == pin["envelope_schema"],
         f"{pkg.get('envelope_schema')} vs {pin['envelope_schema']}"),
        ("source_dataset_version",
         src.get("source_dataset_version") == pin["source_dataset_version"],
         f"{src.get('source_dataset_version')} vs {pin['source_dataset_version']}"),
        ("parity_gate_passed",
         gate.get("passed") is True,
         str(gate.get("passed"))),
    ]

    print("")
    failed = 0
    for name, ok, detail in checks:
        print(f"   [{'OK ' if ok else 'BAD'}] {name}: {detail}")
        if not ok:
            failed += 1

    if failed:
        print(f"\n   MISMATCH — {failed} check(s) failed. The pin no longer describes the release.")
        return 1

    print(f"\n   VERIFIED — {len(checks)} checks; pin resolves to the canonical release and agrees with it.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus-repo", type=Path, default=None,
                   help="Local clone of the canonical corpus repository (offline verification)")
    args = p.parse_args(argv)

    pins = sorted(ROOT.glob(PIN_GLOB))
    if not pins:
        print("No corpus dependency pins found.")
        return 0

    print(f"Found {len(pins)} corpus dependency pin(s).")
    worst = 0
    for pin_path in pins:
        worst = max(worst, verify(pin_path, args.corpus_repo))
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
