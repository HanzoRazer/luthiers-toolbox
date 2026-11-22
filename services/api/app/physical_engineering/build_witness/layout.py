"""Where each file in a witness package may live.

Two boundaries:

* Evidence: the root records and everything under ``raw/``. Sealed once by
  WITNESS-MANIFEST.json and SHA256SUMS, anchored in the ledger, never
  resealed with different bytes.
* Generated products: exactly ``derived/observations.json`` and
  ``reports/WITNESS-REPORT.md``. They are outside the evidence seal. The
  derived document carries its own binding to the seal and is recomputed
  before it is trusted. The report is output, not evidence.

Any other file is misplaced and is refused.
"""

from __future__ import annotations

from app.physical_engineering.build_witness.paths import MANIFEST_NAME, SUMS_NAME

ROOT_RECORDS = frozenset(
    {
        "BUILD-RECORD.json",
        "TEST-PROTOCOL.json",
        "EQUIPMENT.json",
        "ENVIRONMENT.csv",
        "MEASUREMENTS.csv",
        "READ-ME-FIRST.txt",
    }
)
DERIVED_OBSERVATIONS = "derived/observations.json"
REPORT = "reports/WITNESS-REPORT.md"
GENERATED_FILES = frozenset({DERIVED_OBSERVATIONS, REPORT})
SEAL_FILES = frozenset({MANIFEST_NAME, SUMS_NAME})

AUDIO_DIR = "raw/audio/"
IMAGE_DIR = "raw/images/"
RAW_DIR = "raw/"


def is_sealed_evidence(relative: str) -> bool:
    return relative in ROOT_RECORDS or relative.startswith(RAW_DIR)


def sealed_files(files: list[str]) -> list[str]:
    return [item for item in files if is_sealed_evidence(item)]


def misplaced_files(files: list[str]) -> list[str]:
    """Files that are neither sealed evidence nor a recognized product."""
    return [
        item
        for item in files
        if not is_sealed_evidence(item) and item not in GENERATED_FILES and item not in SEAL_FILES
    ]


def placed(relative: object, directory: str, suffix: str | None = None) -> bool:
    """True if ``relative`` names a file under ``directory`` (and has ``suffix``)."""
    if not isinstance(relative, str) or not relative.startswith(directory):
        return False
    return suffix is None or relative.endswith(suffix)
