"""Human-readable witness report.

The report separates declaration, direct measurement, and derivation.
It repeats the authority boundary and does not add a conclusion.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from app.physical_engineering.build_witness.findings import PackageError
from app.physical_engineering.build_witness.layout import REPORT
from app.physical_engineering.build_witness.package import (
    trusted_derived,
    verify_package,
)
from app.physical_engineering.build_witness.validate import load_package_docs
from app.physical_engineering.build_witness.vocabulary import NON_AUTHORITY_STATEMENT


def render_package(package: Path) -> str:
    package = Path(package)
    verified = verify_package(package)
    if verified["exit_code"] == 4:
        raise PackageError("prohibited authority claim", 4)
    if not verified["integrity_ok"]:
        raise PackageError("the package integrity check did not pass", verified["exit_code"] or 2)
    # Render from the verifier's own strict reading of the records, and from
    # derived observations only after every derived check, including the
    # recomputation. Nothing is re-read leniently, and the seal is not touched.
    docs, _ = load_package_docs(package)
    derived = trusted_derived(package, docs)
    text = render_text(verified, docs, derived)
    destination = package / REPORT
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_bytes(text.encode("utf-8"))
    os.replace(temporary, destination)
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


def render_text(verified: dict, docs: dict, derived: dict | None) -> str:
    build = docs.get("build") or {}
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
    warnings = [item for item in verified.get("findings") or [] if item.get("severity") == "warning"]
    if warnings:
        lines.extend(["", "## Recorded uncertainty", ""])
        lines.extend(f"- {_text(item.get('code'))}: {_text(item.get('message'))}" for item in warnings)
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
    lines.extend(_direct_lines(verified, docs))
    lines.extend(["", "## Derived observations", ""])
    lines.extend(_derived_lines(derived))
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


_CSV_REJECTED = {"csv_malformed", "csv_header", "csv_row_width"}


def _direct_lines(verified: dict, docs: dict) -> list[str]:
    rejected = any(
        item.get("code") in _CSV_REJECTED and str(item.get("message", "")).startswith("MEASUREMENTS.csv")
        for item in verified.get("findings") or []
    )
    if rejected:
        return ["- MEASUREMENTS.csv was rejected by the verifier; none of its rows are shown"]
    lines = []
    for row in docs.get("measurements") or []:
        if not str(row.get("measurement_source") or "").startswith("DIRECT_"):
            continue
        lines.append(
            f"- {_text(row.get('quantity'))}: {_text(row.get('value'))} {_text(row.get('unit'))} "
            f"({_text(row.get('measurement_source'))})"
        )
    return lines or ["- none recorded"]


def _derived_lines(payload: dict | None) -> list[str]:
    if payload is None:
        return ["- not calculated"]
    lines = [
        f"- Algorithm: {_text(payload['algorithm_id'])} {_text(payload['algorithm_version'])}",
        f"- Inputs: {_text(', '.join(item['path'] for item in payload['inputs']))}",
        "- Recomputed from the sealed audio and identical to the stored document",
    ]
    for row in payload["observations"]:
        lines.append(
            f"- {_text(row['quantity'])}: {_text(row['value'])} {_text(row['unit'])} "
            f"from {_text(row['raw_evidence_ref'])}"
        )
    return lines
