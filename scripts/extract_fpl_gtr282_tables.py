#!/usr/bin/env python3
"""Extract species tables from FPL GTR-282 (Wood Handbook, 2021) into a long-format CSV.

Source PDFs (public domain, USDA Forest Service, Treesearch):
  Chapter 4 "Moisture Relations and Physical Properties of Wood"  -> 62243.pdf
  Chapter 5 "Mechanical Properties of Wood"                       -> 62244.pdf
  https://research.fs.usda.gov/download/treesearch/62243.pdf
  https://research.fs.usda.gov/download/treesearch/62244.pdf

Tables extracted (metric versions only):
  4-3  shrinkage of domestic woods (radial, tangential, volumetric %; green to ovendry)
  4-4  shrinkage of some imported woods (+ origin)
  5-3a strength properties, woods grown in the United States
  5-4a mechanical properties, Canadian woods imported into the United States
  5-5a mechanical properties, other imported woods (+ sample origin)

Rows are rebuilt from word coordinates, because plain-text extraction drops the
indentation that marks a species as a member of a group ("Spruce" -> "Sitka").
Every row must have exactly the cell count its table defines; anything else is
reported and the script exits 1 rather than guessing.

Usage (needs pdfplumber, which is not a repo dependency):
  python scripts/extract_fpl_gtr282_tables.py <dir with 62243.pdf, 62244.pdf> <out.csv>
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

import pdfplumber

DASHES = ("--", "—", "–", "−−")
NUM = re.compile(r"^(--|—|–|-?\d{1,3}(,\d{3})*(\.\d+)?)$")
COND = {"Green", "12%"}
ORIGIN = {"AF", "AM", "AS"}
SECTIONS = {"Hardwoods", "Softwoods"}
HEADER_WORDS = {"names", "content", "gravity", "(kPa)", "(MPa)", "(N)", "Radial", "Moisture",
                "Specific", "Species", "Tangential", "Volumetric", "Modulus", "botanical",
                "parallel", "perpendicular", "Compression", "Shear", "Static", "bending",
                "rupture", "elasticity", "grain", "Side", "Sample", "Work", "maximum", "load"}

MECH_COLUMNS = {
    "5-3a": ["sg", "mor_kpa", "moe_mpa", "work_kj_m3", "impact_mm", "comp_par_kpa",
             "comp_perp_kpa", "shear_kpa", "tension_perp_kpa", "side_hardness_n"],
    "5-4a": ["sg", "mor_kpa", "moe_mpa", "comp_par_kpa", "comp_perp_kpa", "shear_kpa"],
    "5-5a": ["sg", "mor_kpa", "moe_mpa", "work_kj_m3", "comp_par_kpa", "shear_kpa",
             "side_hardness_n"],
}
SHRINK_COLUMNS = ["shrink_radial_pct", "shrink_tangential_pct", "shrink_volumetric_pct"]
TITLES = {
    "4-3": r"Table 4.3\. Shrinkage values of domestic",
    "4-4": r"Table 4.4\. Shrinkage values of some woods imported",
    "5-3a": r"Table 5.3a\. Strength properties",
    "5-4a": r"Table 5.4a\. Mechanical properties",
    "5-5a": r"Table 5.5a\. Mechanical properties",
}


def lines_of(words: list[dict], tol: float = 2.5) -> list[list[dict]]:
    out: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if out and abs(out[-1][0]["top"] - w["top"]) <= tol:
            out[-1].append(w)
        else:
            out.append([w])
    return [sorted(line, key=lambda w: w["x0"]) for line in out]


class Grouper:
    """Tracks the current group header ("Spruce") across lines, columns and pages."""

    def __init__(self) -> None:
        self.group: str | None = None

    def name(self, text: str, indented: bool) -> str:
        if indented and self.group:
            return f"{self.group}, {text}"
        self.group = None
        return text

    def header(self, text: str) -> None:
        text = re.sub(r"(--|—|–)con\.", "", text).strip()
        if text in SECTIONS:
            self.group = None
        elif HEADER_WORDS & set(text.split()) or not text[:1].isupper():
            return  # a column-header line, not a species group
        elif text and not text.lower().startswith(("table", "species", "shrinkage", "common")):
            self.group = text


def table_pages(pdf, key: str):
    pat = re.compile(TITLES[key])
    for page in pdf.pages:
        text = page.extract_text() or ""
        if not pat.search(text):
            continue
        if key.startswith("5") and "(metric)" not in text.replace("\n", " "):
            continue
        yield page


def body_lines(page, key: str, x_range: tuple[float, float]):
    words = page.extract_words(keep_blank_chars=False, extra_attrs=["size"])
    sizes = sorted(w["size"] for w in words)
    body = sizes[len(sizes) // 2] if sizes else 0
    words = [w for w in words if w["size"] >= 0.85 * body]  # drop footnote superscripts
    title_top = min(
        (w["top"] for w in words if w["text"] == "Table"), default=0
    )
    sel = [w for w in words if x_range[0] <= w["x0"] < x_range[1] and w["top"] > title_top]
    return lines_of(sel)


def extract(pdf_dir: Path) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    problems: list[str] = []
    with pdfplumber.open(pdf_dir / "62243.pdf") as ch4, pdfplumber.open(pdf_dir / "62244.pdf") as ch5:
        for key in ("4-3", "4-4"):
            g = Grouper()
            for page in table_pages(ch4, key):
                mid = page.width / 2
                for x_range in ((0, mid - 4), (mid - 4, page.width)):
                    lines = body_lines(page, key, x_range)
                    starts = [ln[0]["x0"] for ln in lines if any(NUM.match(w["text"]) for w in ln)]
                    base = min(starts) if starts else 0
                    for ln in lines:
                        toks = [w["text"] for w in ln]
                        nums = [i for i, t in enumerate(toks) if NUM.match(t)]
                        if not nums:
                            last = rows[-1]["species"] if rows and rows[-1]["table"] == key else ""
                            if "(" in last and ")" not in last.split("(")[-1]:
                                tail = " ".join(toks)  # wrapped botanical name, e.g. "Iroko (Chlorophora excelsa and" / "C. regia)"
                                for prev in rows[-3:]:
                                    prev["species"] = f"{last} {tail}"
                            else:
                                g.header(" ".join(toks))
                            continue
                        first = nums[0]
                        name = " ".join(toks[:first])
                        cells = toks[first:]
                        origin = ""
                        if key == "4-4" and cells and cells[-1] in ORIGIN:
                            origin = cells.pop()
                        if len(cells) != 3 or not name:
                            if name or len(cells) > 1:
                                problems.append(f"{key} p{page.page_number}: {' '.join(toks)}")
                            continue
                        full = g.name(name, ln[0]["x0"] > base + 4)
                        for col, val in zip(SHRINK_COLUMNS, cells):
                            rows.append(dict(table=key, species=full, condition="green_to_ovendry",
                                             property=col, value=val, origin=origin))
        for key in ("5-3a", "5-4a", "5-5a"):
            g = Grouper()
            cols = MECH_COLUMNS[key]
            current = None
            for page in table_pages(ch5, key):
                lines = body_lines(page, key, (0, page.width))
                starts = [ln[0]["x0"] for ln in lines if any(w["text"] in COND for w in ln)]
                base = min(starts) if starts else 0
                for ln in lines:
                    toks = [w["text"] for w in ln]
                    if "Green" not in toks and "12%" not in toks:
                        if not any(NUM.match(t) for t in toks):
                            if current and current.get("open_paren"):
                                current["species"] += " " + " ".join(toks)
                                current["open_paren"] = "(" in current["species"] and ")" not in current["species"].split("(")[-1]
                            else:
                                g.header(" ".join(toks))
                        continue
                    first_num = next((i for i, t in enumerate(toks) if NUM.match(t)), len(toks))
                    ci = first_num - 1  # the condition sits right before the numbers ("Green" ash: name "Green", cond "Green")
                    if ci < 0 or toks[ci] not in COND:
                        if sum(1 for t in toks if NUM.match(t)) < 3:
                            continue  # footnote prose that mentions "12%"
                        problems.append(f"{key} p{page.page_number}: no condition: {' '.join(toks)}")
                        continue
                    prefix, cond, cells = toks[:ci], toks[ci], toks[ci + 1:]
                    origin = ""
                    if cells and cells[-1] in ORIGIN:
                        origin = cells.pop()
                    if cond == "Green":
                        name = " ".join(prefix)
                        full = g.name(name, ln[0]["x0"] > base + 4)
                        current = {"species": full, "origin": origin,
                                   "open_paren": "(" in full and ")" not in full.split("(")[-1]}
                    elif prefix and current is not None:
                        current["species"] += " " + " ".join(prefix)
                        current["open_paren"] = False
                    if current is None:
                        problems.append(f"{key} p{page.page_number}: orphan row {' '.join(toks)}")
                        continue
                    use = cols
                    if cond == "12%" and len(cells) == len(cols) - 1:
                        use = cols[1:]  # this table prints specific gravity on the green row only
                    if len(cells) != len(use) or not all(NUM.match(c) for c in cells):
                        problems.append(f"{key} p{page.page_number}: {current['species']} {cond}: {' '.join(cells)}")
                        continue
                    current.setdefault("pending", []).append((cond, use, cells))
                    if cond == "12%":
                        for c2, u2, v2 in current.pop("pending"):
                            for col, val in zip(u2, v2):
                                rows.append(dict(table=key, species=current["species"],
                                                 condition="green" if c2 == "Green" else "12pct",
                                                 property=col, value=val, origin=current["origin"]))
    return rows, problems


def main(argv: list[str]) -> int:
    pdf_dir, out = Path(argv[1]), Path(argv[2])
    rows, problems = extract(pdf_dir)
    rows = [r for r in rows if r["value"] not in DASHES]
    for r in rows:
        r["value"] = r["value"].replace(",", "")
        # text-extraction artifacts only (words fused or split by kerning); FPL's own spellings are kept
        r["species"] = re.sub(r"([a-z])spp\.", r" spp.", r["species"]).replace("Hackberr y", "Hackberry")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["table", "species", "condition", "property", "value", "origin"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for name in ("62243.pdf", "62244.pdf"):
        print(f"sha256 {name} {hashlib.sha256((pdf_dir / name).read_bytes()).hexdigest()}")
    species = {(r["table"], r["species"]) for r in rows}
    for key in TITLES:
        print(f"{key}: {sum(1 for t, _ in species if t == key)} species")
    for p in problems:
        print("PROBLEM", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
