"""Write descriptive observations for a verified build-response capture.

The output, ``derived/observations.json``, is a generated product outside the
evidence seal. It names the manifest digest and the input digests it was
computed from, and the verifier recomputes it before anyone may rely on it.
The evidence seal is not rewritten.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.physical_engineering.build_witness.derivation import observations
from app.physical_engineering.build_witness.findings import PackageError
from app.physical_engineering.build_witness.layout import DERIVED_OBSERVATIONS
from app.physical_engineering.build_witness.package import verify_package
from app.physical_engineering.build_witness.vocabulary import (
    ALLOWED_DERIVATIONS,
    REFUSED_DERIVATIONS,
)


def analyze_package(
    package: Path,
    *,
    compare_reference: bool = False,
    infer_species: bool = False,
    derive: list[str] | None = None,
) -> dict:
    if compare_reference or infer_species:
        raise PackageError("reference comparison and species inference are blocked", 4)
    requested = derive or sorted(ALLOWED_DERIVATIONS)
    for name in requested:
        if name in REFUSED_DERIVATIONS or name not in ALLOWED_DERIVATIONS:
            raise PackageError("derivation is not allowed: " + name, 4)
    verified = verify_package(package)
    if verified["exit_code"] != 0:
        raise PackageError("analysis requires an integrity-verified package", verified["exit_code"])
    payload = observations(Path(package), verified["witness_id"], requested)
    destination = Path(package) / DERIVED_OBSERVATIONS
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, destination)
    return payload
