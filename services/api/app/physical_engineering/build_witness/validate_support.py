"""Small helpers shared by the witness record checks."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from app.physical_engineering.build_witness.findings import Finding, finding
from app.physical_engineering.build_witness.paths import normalize_relative

DECIMAL_TEXT = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")


def path_exists(package: Path, relative: str) -> bool:
    try:
        path = package / normalize_relative(relative)
    except Exception:
        return False
    return path.is_file() and not path.is_symlink()


def parse_time(value: str, findings: list[Finding]) -> datetime | None:
    try:
        stamped = datetime.fromisoformat(value)
    except ValueError:
        findings.append(finding("malformed", "timestamp", value))
        return None
    if stamped.tzinfo is None or stamped.utcoffset() is None:
        findings.append(finding("malformed", "timestamp", "timestamp needs a timezone"))
        return None
    if stamped.year < 1990 or stamped.year > 2100:
        findings.append(finding("malformed", "timestamp", value))
        return None
    return stamped
