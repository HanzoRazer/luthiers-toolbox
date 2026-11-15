"""Policy examples must agree with the FPL tables they cite.

CLAUDE.md and docs/process/wood_species_update_template.md show example species records
whose fields carry `FPL_GTR282_table_*` source labels. Every value attributed to FPL is
compared, at the precision it is written with, against the extracted tables in
docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv. A field that carries an FPL
label but cannot be checked fails the test rather than being skipped.

Added after the template example attributed shrinkage 5.0 / 3.1 to Table 4-3, which
has no such row (docs/tonewood/VERIFICATION_LOG.md, C-13).
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv"

# document -> FPL species name of its example record
EXAMPLES = {
    "CLAUDE.md": "Maple, Sugar",
    "docs/process/wood_species_update_template.md": "Maple, Sugar",
}

SHRINK_TABLES = {"4-3", "4-4"}
MECH_TABLES = {"5-3a", "5-4a", "5-5a"}
VALID = {f"FPL_GTR282_table_{t}" for t in SHRINK_TABLES | MECH_TABLES}
DEPRECATED = "FPL_GTR282_table_5-3"
LBF = 4.44822

# value field -> (its source field, table kind, FPL value from the row)
FIELDS = {
    "density_kg_m3": ("_density_source", MECH_TABLES, lambda r: 1000 * r[("12pct", "sg")] * 1.12),
    "specific_gravity": ("_specific_gravity_source", MECH_TABLES, lambda r: r[("12pct", "sg")]),
    "contraction_tangential_pct": ("_shrinkage_tangential_source", SHRINK_TABLES,
                                   lambda r: r[("green_to_ovendry", "shrink_tangential_pct")]),
    "contraction_radial_pct": ("_shrinkage_radial_source", SHRINK_TABLES,
                               lambda r: r[("green_to_ovendry", "shrink_radial_pct")]),
    "modulus_of_elasticity_gpa": ("_mechanical_source", MECH_TABLES, lambda r: r[("12pct", "moe_mpa")] / 1000),
    "modulus_of_rupture_mpa": ("_mechanical_source", MECH_TABLES, lambda r: r[("12pct", "mor_kpa")] / 1000),
    "janka_hardness_n": ("_hardness_source", MECH_TABLES, lambda r: r[("12pct", "side_hardness_n")]),
    "janka_hardness_lbf": ("_hardness_source", MECH_TABLES, lambda r: r[("12pct", "side_hardness_n")] / LBF),
}


def load_fpl() -> dict[tuple[str, str], dict[tuple[str, str], float]]:
    rows: dict[tuple[str, str], dict[tuple[str, str], float]] = defaultdict(dict)
    with CSV.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[(r["table"], r["species"])][(r["condition"], r["property"])] = float(r["value"])
    return dict(rows)


def physical_blocks(text: str) -> list[dict]:
    """Every ```json block holding a "physical" record, values kept as written."""
    out = []
    for body in re.findall(r"```json\n(.*?)```", text.replace("\r\n", "\n"), re.S):
        if '"physical"' not in body:
            continue
        src = body.strip()
        if not src.startswith("{"):
            src = "{" + src + "}"
        data = json.loads(src, parse_float=str, parse_int=str)
        out.append(data["physical"])
    return out


def problems_in(record: dict, species: str, fpl) -> list[str]:
    bad = []
    used_sources = set()
    for field, (src_field, kinds, fpl_value) in FIELDS.items():
        if field not in record:
            continue
        label = record.get(src_field)
        if label is None:
            bad.append(f"{field}: no {src_field}")
            continue
        used_sources.add(src_field)
        if not label.startswith("FPL_GTR282"):
            continue
        if label not in VALID:
            bad.append(f"{field}: {src_field} = {label!r} is not a valid FPL label")
            continue
        table = label.removeprefix("FPL_GTR282_table_")
        if table not in kinds:
            bad.append(f"{field}: {label} is the wrong kind of table for this field")
            continue
        row = fpl.get((table, species))
        if row is None:
            bad.append(f"{field}: no row {species!r} in FPL Table {table}")
            continue
        try:
            ref = fpl_value(row)
        except KeyError as e:
            bad.append(f"{field}: FPL Table {table} {species!r} has no {e.args[0]}")
            continue
        shown = Decimal(record[field])
        if abs(float(shown) - ref) > 0.5 * 10 ** shown.as_tuple().exponent + 1e-9:
            bad.append(f"{field}: {shown} vs FPL Table {table} {ref:.4g}")
    for key, label in record.items():
        if key.endswith("_source") and str(label).startswith("FPL_GTR282") and key not in used_sources:
            bad.append(f"{key} = {label!r} attributes no field this test can check")
    return bad


@pytest.mark.parametrize("doc", sorted(EXAMPLES))
def test_policy_example_values_match_cited_fpl_table(doc):
    blocks = physical_blocks((ROOT / doc).read_text(encoding="utf-8"))
    assert blocks, f"{doc}: no example record found"
    fpl = load_fpl()
    checked = 0
    for rec in blocks:
        assert not problems_in(rec, EXAMPLES[doc], fpl), problems_in(rec, EXAMPLES[doc], fpl)
        checked += sum(1 for f in FIELDS if f in rec and str(rec.get(FIELDS[f][0], "")).startswith("FPL_GTR282"))
    assert checked, f"{doc}: no FPL-attributed value was checked"


@pytest.mark.parametrize("doc", sorted(EXAMPLES))
def test_deprecated_label_only_listed_as_deprecated(doc):
    for line in (ROOT / doc).read_text(encoding="utf-8").splitlines():
        if re.search(re.escape(DEPRECATED) + r"(?![\w-])", line):
            assert "deprecated" in line.lower(), f"{doc}: {line.strip()}"


def test_check_catches_the_original_mislabel():
    """Negative control: the template's former shrinkage values against Table 4-3."""
    rec = {"contraction_tangential_pct": "5.0", "contraction_radial_pct": "3.1",
           "_shrinkage_tangential_source": "FPL_GTR282_table_4-3",
           "_shrinkage_radial_source": "FPL_GTR282_table_4-3"}
    bad = problems_in(rec, "Maple, Sugar", load_fpl())
    assert len(bad) == 2 and all("vs FPL Table 4-3" in b for b in bad), bad


def test_check_rejects_deprecated_and_mismatched_tables():
    fpl = load_fpl()
    rec = {"contraction_radial_pct": "4.8", "_shrinkage_radial_source": DEPRECATED}
    assert "not a valid FPL label" in problems_in(rec, "Maple, Sugar", fpl)[0]
    rec = {"contraction_radial_pct": "4.8", "_shrinkage_radial_source": "FPL_GTR282_table_5-3a"}
    assert "wrong kind of table" in problems_in(rec, "Maple, Sugar", fpl)[0]
