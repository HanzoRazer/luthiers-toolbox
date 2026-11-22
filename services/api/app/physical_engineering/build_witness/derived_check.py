"""The derived-observation boundary.

``derived/observations.json`` is written after the evidence is sealed, so the
evidence seal cannot vouch for it. It is trusted only when all of these hold:

1. The evidence itself verifies (no other non-warning finding).
2. It is UTF-8 JSON that satisfies ``pem_derived_observations_v1``.
3. It names this witness and session, and the digest of the current
   WITNESS-MANIFEST.json.
4. Its inputs are exactly the protocol's trial and background recordings,
   each listed in the sealed manifest with the same length and digest.
5. Every row cites only those inputs.
6. Recomputing it from the sealed audio gives an identical document.

Step 6 is what shows the numbers were not edited; steps 1-5 make the failure
specific. Any failure is an ``integrity`` finding (exit 2).
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

from app.physical_engineering.build_witness.derivation import observations
from app.physical_engineering.build_witness.findings import (
    Finding,
    PackageError,
    finding,
)
from app.physical_engineering.build_witness.layout import DERIVED_OBSERVATIONS
from app.physical_engineering.build_witness.paths import MANIFEST_NAME, sha256_file
from app.physical_engineering.build_witness.schema_check import DERIVED, schema_findings


class DerivedInvalid(Exception):
    pass


def check_derived(package: Path, docs: dict, listed: dict[str, dict], evidence_ok: bool) -> tuple[dict | None, list[Finding]]:
    """The validated derived document (or None if absent) and any findings."""
    if not (package / DERIVED_OBSERVATIONS).is_file():
        return None, []
    try:
        if not evidence_ok:
            raise DerivedInvalid("derived observations cannot be trusted because the evidence does not verify")
        payload = _read(package)
        _bind(package, payload, docs, listed)
        _recompute(package, payload)
    except DerivedInvalid as exc:
        return None, [finding("integrity", "derived_invalid", f"{DERIVED_OBSERVATIONS}: {exc}")]
    return payload, []


def _read(package: Path) -> dict:
    try:
        payload = json.loads((package / DERIVED_OBSERVATIONS).read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise DerivedInvalid("not UTF-8") from exc
    except (json.JSONDecodeError, RecursionError) as exc:
        raise DerivedInvalid("not JSON") from exc
    if not isinstance(payload, dict):
        raise DerivedInvalid("not a JSON object")
    problems = schema_findings(DERIVED, payload, DERIVED_OBSERVATIONS)
    if problems:
        raise DerivedInvalid(problems[0].message)
    return payload


def _bind(package: Path, payload: dict, docs: dict, listed: dict[str, dict]) -> None:
    build, protocol = docs.get("build") or {}, docs.get("protocol") or {}
    if payload["witness_id"] != build.get("witness_id") or payload["session_id"] != build.get("session_id"):
        raise DerivedInvalid("names a different witness or session")
    if payload["evidence_manifest_sha256"] != sha256_file(package / MANIFEST_NAME):
        raise DerivedInvalid("was computed from a different evidence seal")
    trials = protocol.get("trials") if isinstance(protocol.get("trials"), list) else []
    expected = [trial.get("file") for trial in trials if isinstance(trial, dict)] + [protocol.get("background_file")]
    paths = [item["path"] for item in payload["inputs"]]
    if paths != expected:
        raise DerivedInvalid("inputs are not the protocol's recordings")
    for item in payload["inputs"]:
        entry = listed.get(item["path"])
        if entry is None or entry.get("sha256") != item["sha256"] or entry.get("byte_length") != item["byte_length"]:
            raise DerivedInvalid("input is not sealed with this length and digest: " + item["path"])
    allowed = set(paths)
    for row in payload["observations"]:
        cited = {row["raw_evidence_ref"], *row["derived_from"]}
        if not cited <= allowed:
            raise DerivedInvalid("an observation cites evidence that is not an input: " + ", ".join(sorted(cited - allowed)))


def _recompute(package: Path, payload: dict) -> None:
    try:
        fresh = observations(package, payload["witness_id"], payload["derivations"])
    except (PackageError, OSError, ValueError, KeyError, EOFError, wave.Error) as exc:
        raise DerivedInvalid("could not be recomputed: " + str(exc)) from exc
    if fresh != payload:
        raise DerivedInvalid("values do not match a recomputation from the sealed audio")
