"""Human-readable witness report.

The report separates declaration, direct measurement, and derivation.
It repeats the authority boundary and does not add a conclusion.
"""

from __future__ import annotations

import json
import os
import re
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


_CONTROL = re.compile(r"[\x00-\x1f\x7f\u2028\u2029]+")


def _text(value: object) -> str:
    """One line of package-supplied text, safe to place inside Markdown.

    Line breaks would let a field start its own heading or list item and
    imitate the report's fixed sections (for example a forged gate line).
    Raw HTML is escaped so it renders as text.
    """
    flat = _CONTROL.sub(" ", str(value))
    return flat.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_text(package: Path, verified: dict) -> str:
    build = json.loads((package / "BUILD-RECORD.json").read_text(encoding="utf-8"))
    lines = [
        "# Build-response witness",
        "",
        NON_AUTHORITY_STATEMENT,
        "",
        f"Witness: {_text(verified.get('witness_id'))}",
        f"Record kind: {_text(build.get('record_kind'))}",
        f"Witness class: {_text(build.get('witness_class'))}",
        "",
        "## States",
        "",
    ]
    lines.extend(f"- {state}" for state in verified["states"])
    lines.extend(["", "## Declarations", ""])
    for key in ("top", "back_side", "neck"):
        material = build.get(key)
        if not isinstance(material, dict):
            material = {}
        lines.append(
            f"- {key}: status {_text(material.get('identity_status'))}; "
            f"trade name {_text(material.get('trade_name'))}; "
            f"botanical name {_text(material.get('botanical_name'))}; "
            f"reason {_text(material.get('unknown_reason'))}"
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
                f"- {_text(row.get('quantity'))}: {_text(row.get('value'))} {_text(row.get('unit'))} "
                f"({_text(row.get('measurement_source'))})"
            )
    return lines or ["- none recorded"]


def _derived_lines(package: Path) -> list[str]:
    path = package / "derived" / "observations.json"
    if not path.is_file():
        return ["- not calculated"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines = [
        f"- Algorithm: {_text(payload.get('algorithm_id'))} {_text(payload.get('algorithm_version'))}",
        f"- Inputs: {_text(', '.join(str(item) for item in payload.get('inputs') or []))}",
    ]
    for row in payload.get("observations") or []:
        lines.append(
            f"- {_text(row.get('quantity'))}: {_text(row.get('value'))} {_text(row.get('unit'))} "
            f"from {_text(row.get('raw_evidence_ref'))}"
        )
    return lines
