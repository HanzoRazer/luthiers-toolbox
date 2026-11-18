"""Human-readable witness report.

The report separates declaration, direct measurement, and derivation.
It repeats the authority boundary and does not add a conclusion.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.physical_engineering.build_witness.package import PackageError, ingest_package, verify_package
from app.physical_engineering.build_witness.vocabulary import NON_AUTHORITY_STATEMENT


def render_package(package: Path) -> str:
    package = Path(package)
    verified = verify_package(package)
    if verified["exit_code"] == 4:
        raise PackageError("prohibited authority claim", 4)
    if not verified["integrity_ok"]:
        raise PackageError("the package integrity check did not pass", verified["exit_code"] or 2)
    text = render_text(package, verified)
    destination = package / "reports" / "WITNESS-REPORT.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, destination)
    ingest_package(package, replace=True)
    return text


def render_text(package: Path, verified: dict) -> str:
    build = json.loads((package / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    lines = [
        "# Build-response witness",
        "",
        NON_AUTHORITY_STATEMENT,
        "",
        f"Witness: {verified.get('witness_id')}",
        f"Record kind: {build.get('record_kind')}",
        f"Witness class: {build.get('witness_class')}",
        "",
        "## States",
        "",
    ]
    lines.extend(f"- {state}" for state in verified["states"])
    lines.extend(["", "## Declarations", ""])
    for key in ("top", "back_side", "neck"):
        material = build.get(key) or {}
        lines.append(
            f"- {key}: status {material.get('identity_status')}; "
            f"trade name {material.get('trade_name')}; "
            f"botanical name {material.get('botanical_name')}; "
            f"reason {material.get('unknown_reason')}"
        )
    lines.extend(
        [
            "",
            "## Direct measurements",
            "",
            "Direct rows are copied from MEASUREMENTS.csv. Declared build properties are not measurements.",
            "",
        ]
    )
    lines.extend(_direct_lines(package))
    lines.extend(["", "## Derived observations", ""])
    lines.extend(_derived_lines(package))
    lines.extend(
        [
            "",
            "## Gates",
            "",
            "- Material-property validation: pending",
            "- Literature comparison: blocked",
            "- Scientific validation: pending",
            "- Production readiness: closed",
            "- CAM authority: closed",
            "- Machine execution: closed",
            "",
            "Whole-instrument response is not intrinsic wood behavior.",
            "",
        ]
    )
    return "\n".join(lines)


def _direct_lines(package: Path) -> list[str]:
    import csv

    path = package / "MEASUREMENTS.csv"
    lines = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if not str(row.get("measurement_source") or "").startswith("DIRECT_"):
                continue
            lines.append(
                f"- {row.get('quantity')}: {row.get('value')} {row.get('unit')} "
                f"({row.get('measurement_source')})"
            )
    return lines or ["- none recorded"]


def _derived_lines(package: Path) -> list[str]:
    path = package / "derived" / "observations.json"
    if not path.is_file():
        return ["- not calculated"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines = [
        f"- Algorithm: {payload.get('algorithm_id')} {payload.get('algorithm_version')}",
        f"- Inputs: {', '.join(payload.get('inputs') or [])}",
    ]
    for row in payload.get("observations") or []:
        lines.append(f"- {row.get('quantity')}: {row.get('value')} {row.get('unit')} from {row.get('raw_evidence_ref')}")
    return lines
