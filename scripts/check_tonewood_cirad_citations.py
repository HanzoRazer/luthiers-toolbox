"""Check (and optionally fix) CIRAD density citations in docs/tonewood/*.md.

Any markdown table whose header has a "D12" column and whose row names an
italic binomial present in the CIRAD wood density CSV is compared with the
per-taxon MEAN D12 over all specimens. A header column named exactly "N"
(or containing "specimen") is compared with the specimen count, as is any
"<n> specimens" phrase in the row.

Usage:
    python scripts/check_tonewood_cirad_citations.py            # report, exit 1 on mismatch
    python scripts/check_tonewood_cirad_citations.py --fix      # rewrite cells in place

Tolerance: 0.015 g/cm3 (the docs print two decimals).
"""
from __future__ import annotations

import csv
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "docs/reference/cirad-density/Cirad-wood-density-database.csv"
DOCS = ROOT / "docs/tonewood"
TOL = 0.015
D12_CELL = re.compile(r"^(\**)~?([01]\.\d{1,2})(\**)$")
TAXON = re.compile(r"\*([A-Z][a-z]+ (?:[a-z]+|sp\.?))\*")
SPECIMENS = re.compile(r"\b(\d+) specimens\b")


def load_cirad() -> dict[str, list[float]]:
    db: dict[str, list[float]] = defaultdict(list)
    with CSV.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                db[row["Taxa"].strip()].append(float(row["D12"]))
            except ValueError:
                continue
    return db


def split_row(line: str) -> list[str]:
    return line.strip().strip("|").split("|")


def check_file(path: Path, db, fix: bool) -> list[str]:
    lines = path.read_text(encoding="utf-8").split("\n")
    problems: list[str] = []
    dcol = ncol = None
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            dcol = ncol = None
            continue
        cells = split_row(line)
        stripped = [c.strip() for c in cells]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in stripped if c):
            continue
        low = [c.lower().strip("* ") for c in stripped]
        if any("d12" in c for c in low):
            dcol = next(k for k, c in enumerate(low) if "d12" in c)
            ncol = next((k for k, c in enumerate(low) if c == "n" or "specimen" in c), None)
            continue
        if dcol is None or dcol >= len(cells):
            continue
        tax_m = TAXON.search(line)
        if not tax_m:
            continue
        taxon = tax_m.group(1).rstrip(".")
        if taxon.endswith(" sp"):
            taxon = taxon  # CIRAD writes genus-only rows as "Genus sp"
        dm = D12_CELL.match(stripped[dcol])
        if taxon not in db:
            if dm:
                problems.append(f"{path.name}:{i+1} {taxon}: not in CIRAD density file")
            continue
        vals = db[taxon]
        mean, n = st.mean(vals), len(vals)
        row_bad = False
        if dm and abs(float(dm.group(2)) - mean) > TOL:
            problems.append(f"{path.name}:{i+1} {taxon}: D12 {dm.group(2)} vs CIRAD mean {mean:.2f} (N={n}, max {max(vals):.2f})")
            if fix:
                cells[dcol] = f" {dm.group(1)}{mean:.2f}{dm.group(3)} "
            row_bad = True
        if ncol is not None and ncol < len(cells):
            try:
                cited = int(stripped[ncol].strip("* "))
            except ValueError:
                cited = None
            if cited is not None and cited != n:
                problems.append(f"{path.name}:{i+1} {taxon}: N {cited} vs CIRAD {n}")
                if fix:
                    cells[ncol] = f" {n} "
                row_bad = True
        joined = "|".join(cells)
        for sm in SPECIMENS.finditer(joined):
            if int(sm.group(1)) != n:
                problems.append(f"{path.name}:{i+1} {taxon}: '{sm.group(0)}' vs CIRAD {n}")
                row_bad = True
        if fix and row_bad:
            joined = SPECIMENS.sub(f"{n} specimens" if n != 1 else "1 specimen", joined)
            lead = line[: len(line) - len(line.lstrip())]
            lines[i] = f"{lead}|{joined}|"
    if fix and problems:
        path.write_text("\n".join(lines), encoding="utf-8", newline="")
    return problems


def main() -> int:
    fix = "--fix" in sys.argv
    db = load_cirad()
    allp: list[str] = []
    for p in sorted(DOCS.glob("*.md")):
        allp += check_file(p, db, fix)
    for line in allp:
        print(line)
    print(f"{len(allp)} mismatches{' (fixed)' if fix else ''}")
    return 1 if allp and not fix else 0


if __name__ == "__main__":
    sys.exit(main())
