"""MB Sound corpus dependency-pin contract tests (DATA-MIG-002).

Toolbox consumes the MB Sound corpus **by pin, never by copy**. Before DATA-MIG-002
this repository held a complete duplicate of the canonical cohort and was a second
data authority for it. These tests hold the boundary that replaced it:

* the pin identifies exactly one immutable canonical release;
* the verifier fails closed when the pin and the release disagree;
* an unreachable release is reported UNRESOLVED, never as a pass;
* `mb-*` identities are preserved, not re-minted;
* no canonical payload, envelope or workbook is duplicated back into this repository;
* no consumer may silently fall back to a bundled local copy.

The fail-closed tests run fully offline against a synthetic canonical manifest, so
they verify the *verifier*, not the network. Live resolution against the real private
release is a deliberate manual step:

    python scripts/verify_reference_corpus_pin.py

Ported from luthier-acoustics-lab's DATA-REL-001 tests; the semantics are deliberately
identical so both consumers of mb-sound/v1.0.0 verify it the same way.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PIN_DIR = ROOT / "docs" / "reference" / "mb-sound"
PIN_PATH = PIN_DIR / "CORPUS_DEPENDENCY.json"
MIGRATION_RECORD = PIN_DIR / "MIGRATION_DATA-MIG-002.md"


def _load_verifier():
    path = ROOT / "scripts" / "verify_reference_corpus_pin.py"
    spec = importlib.util.spec_from_file_location("verify_reference_corpus_pin", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = _load_verifier()
PIN = json.loads(PIN_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# TC-005 … TC-012 — the pin identifies exactly one release
# --------------------------------------------------------------------------

def test_tc005_canonical_repository_identity():
    assert PIN["canonical_repository"] == "HanzoRazer/luthier-acoustics-data"
    assert PIN["consumer_repository"] == "HanzoRazer/luthiers-toolbox"


def test_tc006_release_identity():
    assert PIN["release_tag"] == "mb-sound/v1.0.0"
    assert PIN["release_tag"] == f"{PIN['corpus_id']}/v{PIN['release_version']}"


def test_tc007_commit_identity():
    """A pin must name an immutable commit, not a branch or a floating ref."""
    sha = PIN["canonical_commit_sha"]
    assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)
    assert PIN["content_commit_sha"] and PIN["content_commit_sha"] != sha


def test_tc008_tc009_digest_identity():
    for key in ("corpus_digest_sha256", "manifest_digest_sha256"):
        digest = PIN[key]
        assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), key
    assert PIN["corpus_digest_sha256"] == (
        "ea77ca6397c2e4b34d92133a59a55f07ff14a8ec3bec7f33e0f59590df653717"
    )
    assert PIN["manifest_digest_sha256"] == (
        "03abe6509ae4e0ad530d85a9d6ff04d43418260380854c72b6b50dc5d2f86689"
    )


def test_tc010_record_count_identity():
    assert PIN["record_count"] == 114
    assert PIN["envelope_count"] == 114


def test_tc011_schema_version_identity():
    assert PIN["schema_version"] == "mb_sound_lab_procedure_v1"
    assert PIN["envelope_schema"] == "luthier-acoustics-data/specimen_envelope/v1"


def test_tc012_source_version_preserved_separately():
    """Custody maturity must never restate source maturity."""
    assert PIN["source_dataset_version"] == "0.5.0-draft"
    assert PIN["release_version"] != PIN["source_dataset_version"]


# --------------------------------------------------------------------------
# D2 — identities are preserved, not re-minted
# --------------------------------------------------------------------------

def test_no_parallel_identifier_namespace_is_minted():
    """`mb-*` identities are consumed as-is; no MBREF-* or Toolbox-local alias."""
    for path in (PIN_PATH, PIN_DIR / "README.md", MIGRATION_RECORD):
        text = path.read_text(encoding="utf-8").upper().replace("MB SOUND", "")
        assert "MBREF" not in text, path.name


def test_pin_declares_it_adds_no_toolbox_evidence():
    assert PIN["evidence_character"]["toolbox_measurements"] == 0
    assert PIN["evidence_character"]["laboratory_measurements"] == 0
    assert PIN["evidence_character"]["tap_tone_pi_measurements"] == 0
    assert PIN["non_claims"], "a pin must state what it does not claim"


def test_provenance_is_external_reference_not_toolbox_authored():
    assert PIN["provenance_class"] == "EXTERNAL_REFERENCE"
    assert PIN["dependency_status"] == "PINNED"


def test_migration_record_preserves_provenance():
    """TC-022 — the custody transfer must remain auditable after deletion."""
    text = MIGRATION_RECORD.read_text(encoding="utf-8")
    assert "Maderas Barber" in text or "MB Sound" in text
    assert PIN["corpus_digest_sha256"] in text, "the proven digest must be recorded"
    assert "df3b3581" in text, "the preservation revision must remain traceable"
    assert text.count("MATCH") >= 145, "the full per-file hash table must be retained"


# --------------------------------------------------------------------------
# TC-013 … TC-016 — fail closed, verified offline against a synthetic release
# --------------------------------------------------------------------------

def _fixture_release(tmp_path: Path, pin: dict) -> tuple[Path, str]:
    """Build a synthetic canonical repo whose manifest agrees with `pin`."""
    manifest = {
        "release_id": pin["release_tag"],
        "release_version": pin["release_version"],
        "cohort_id": pin["corpus_id"],
        "provenance_class": pin["provenance_class"],
        "package": {
            "revision": pin["content_commit_sha"],
            "record_count": pin["record_count"],
            "envelope_count": pin["envelope_count"],
            "dataset_digest_sha256": pin["corpus_digest_sha256"],
            "extension_schema": pin["schema_version"],
            "envelope_schema": pin["envelope_schema"],
        },
        "source_provenance": {"source_dataset_version": pin["source_dataset_version"]},
        "parity_gate": {"passed": True},
    }
    repo = tmp_path / "canonical"
    target = repo / pin["manifest_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(manifest, indent=2).encode()
    target.write_bytes(raw)
    return repo, hashlib.sha256(raw).hexdigest()


def _write_pin(tmp_path: Path, pin: dict) -> Path:
    path = tmp_path / "PIN_CORPUS_DEPENDENCY.json"
    path.write_text(json.dumps(pin, indent=2), encoding="utf-8")
    return path


def test_harness_is_sound_before_asserting_failure(tmp_path):
    """A mutation test proves nothing unless the unmutated case passes."""
    pin = dict(PIN)
    repo, digest = _fixture_release(tmp_path, pin)
    pin["manifest_digest_sha256"] = digest
    assert V.verify(_write_pin(tmp_path, pin), repo) == 0


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("release_tag", "mb-sound/v9.9.9"),        # TC-013 tag drift
        ("corpus_id", "not-mb-sound"),
        ("content_commit_sha", "deadbee"),          # TC-007 commit drift
        ("corpus_digest_sha256", "0" * 64),         # TC-014 digest drift
        ("record_count", 113),                      # TC-015 count drift
        ("envelope_count", 113),
        ("schema_version", "some_other_schema_v9"),
        ("source_dataset_version", "1.0.0"),
        ("provenance_class", "INTERNAL_EXPERIMENTAL"),
    ],
)
def test_verifier_fails_closed_on_any_drift(tmp_path, field, bad_value):
    pin = dict(PIN)
    repo, digest = _fixture_release(tmp_path, pin)
    pin["manifest_digest_sha256"] = digest
    pin[field] = bad_value
    assert V.verify(_write_pin(tmp_path, pin), repo) == 1, f"{field} drift went undetected"


def test_tc014_tampered_release_manifest_is_detected(tmp_path):
    """The manifest digest is what makes tampering with the release record visible."""
    pin = dict(PIN)
    repo, digest = _fixture_release(tmp_path, pin)
    pin["manifest_digest_sha256"] = digest

    manifest_file = repo / pin["manifest_path"]
    doc = json.loads(manifest_file.read_text())
    doc["package"]["record_count"] = 113  # a plausible-looking edit
    manifest_file.write_bytes(json.dumps(doc, indent=2).encode())

    assert V.verify(_write_pin(tmp_path, pin), repo) == 1


def test_tc016_unresolvable_pin_reports_unresolved_not_verified(tmp_path):
    """An unreachable release must never be reported as a pass."""
    pin = dict(PIN)
    pin["canonical_repository"] = "HanzoRazer/does-not-exist-xyz"
    empty = tmp_path / "empty"
    empty.mkdir()
    assert V.verify(_write_pin(tmp_path, pin), empty) == 2


# --------------------------------------------------------------------------
# TC-020 … TC-023 — no second authority may reappear in this repository
# --------------------------------------------------------------------------

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
             "dist", "build", ".mypy_cache", ".ruff_cache"}


def _walk_repo(pattern: str):
    """Repo files matching `pattern`, ignoring vendored and generated trees."""
    for path in ROOT.rglob(pattern):
        if SKIP_DIRS.isdisjoint(path.parts):
            yield path


# A canonical specimen payload is named for its identifier: mb-adt-000001.json,
# mb-rc30-000024.json. Deliberately narrower than "mb-*.json" so that governance
# records and documentation keep their natural names (e.g. the DO-SIP-013 patch
# .cbsp21/patches/mb-sound-panel-corpus-scaffold.json) without tripping the guard.
SPECIMEN_PAYLOAD = re.compile(r"^mb-[a-z0-9]+-\d{6}\.json$")


def test_tc020_no_canonical_specimen_payloads_are_duplicated_here():
    """The decisive test: Toolbox references the corpus, it does not hold it.

    Guards against a future developer re-adding the cohort under any path. A
    handful of synthetic fixtures would be acceptable; a cohort-sized set of
    `mb-*` payloads is a second data authority by definition.
    """
    strays = sorted(str(p.relative_to(ROOT)) for p in _walk_repo("mb-*.json")
                    if SPECIMEN_PAYLOAD.match(p.name))
    assert strays == [], (
        f"{len(strays)} MB Sound payload(s) found in Toolbox. The corpus is canonical "
        f"in luthier-acoustics-data @ mb-sound/v1.0.0 and must be consumed by pin: {strays[:5]}"
    )


def test_tc021_no_canonical_envelope_set_is_duplicated_here():
    """Envelopes are the data repository's custody wrapper. Toolbox holds none."""
    envelopes = sorted(str(p.relative_to(ROOT)) for p in _walk_repo("*.json")
                       if "mb_sound" in str(p).lower() and "envelope" in str(p).lower())
    assert envelopes == [], f"canonical envelopes must not be copied here: {envelopes[:5]}"


def test_tc020_the_retired_corpus_directory_is_gone():
    retired = ROOT / "services" / "api" / "app" / "data_registry" / "system" / "materials" / "empirical_tonewood"
    assert not retired.exists(), (
        "empirical_tonewood/ was removed in DATA-MIG-002; re-creating it restores the "
        "split authority the migration eliminated"
    )


def test_tc021_no_laboratory_workbooks_are_duplicated_here():
    """The four .xlsx source workbooks are canonical; none is held locally."""
    books = sorted(str(p.relative_to(ROOT)) for p in _walk_repo("*Laboratory_Record.xlsx"))
    assert books == [], f"MB Sound workbooks are canonical, not local: {books}"


def test_tc023_no_hidden_local_fallback_exists():
    """D5 — a missing canonical corpus must fail clearly, never degrade silently."""
    verifier = (ROOT / "scripts" / "verify_reference_corpus_pin.py").read_text(encoding="utf-8")
    assert "empirical_tonewood" not in verifier, "the resolver must not know a local corpus path"
    assert "UNRESOLVED" in verifier, "an unreachable release must be named, not swallowed"
    assert PIN["consumption"]["fail_closed"], "the pin must declare fail-closed consumption"


def test_toolbox_specific_provenance_is_retained():
    """TC-022 — removing evidence ownership must not erase Toolbox interpretation."""
    keep = [
        ROOT / "docs" / "calculators" / "acoustics" / "mb_sound_panel_laboratory_records" / "CROSSWALK_TOOLBOX.md",
        ROOT / "docs" / "calculators" / "acoustics" / "nicoletti_mb_sound_acoustic_study_set" / "README.md",
        ROOT / "scripts" / "mb_sound_validate_corpus.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in keep if not p.exists()]
    assert missing == [], f"Toolbox-specific provenance must survive the migration: {missing}"
