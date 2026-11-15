#!/usr/bin/env python3
"""Check density, Janka, MOE, MOR and shrinkage values in docs/tonewood against FPL GTR-282.

Reads docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv (see its README) and
the markdown tables in docs/tonewood. A cell is checked only when its species maps
to an FPL row in ALIASES and its property is recognised; everything else is
skipped and counted, so "0 mismatches" means "0 among the checked cells", not
"every value in the folder is right".

Table shapes understood:
  A  | Property | <species> | <species> | ...   (one species per column)
  B  | Species  | ... | Density | Janka | ...    (one species per row)
  C  | Property | Value |  under a heading that names one species

FPL-derived values (all at 12% moisture content unless noted):
  density   rho12 = 1000 * G12 * 1.12 (FPL Eq. 4-14). Where FPL gives only basic
            specific gravity (Table 5-5a), G12 = Gb / (1 - S12/100) with
            S12 = S0 * (1 - 12/30) (Eqs. 4-9, 4-11; S0 volumetric, Table 4-4).
  janka     side hardness, N; lbf = N / 4.44822
  moe, mor  as printed (MOE not shear-corrected, FPL footnote c)
  shrinkage green to ovendry, radial / tangential (Tables 4-3, 4-4)

Usage:
  python scripts/check_tonewood_fpl_values.py            # report, exit 1 on mismatch
  python scripts/check_tonewood_fpl_values.py --summary  # counts only
  python scripts/check_tonewood_fpl_values.py --fix      # rewrite mismatched cells (numbers only),
                                                         # then check again; exit 1 if any remain

Exit 1 also when an ALIASES entry names an FPL row that is not in the CSV. Cells that
hold a range ("10.5-12.0") are not compared; they are counted and listed, never dropped
silently.

Checking is strict: for a species mapped to FPL, every recognised cell must equal the
FPL value at display precision (no tolerance), so each such cell can be attributed to
FPL. Specific gravity is checked as G12 (ovendry weight, volume at 12% MC).
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FPL = ROOT / "docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv"
DOCS = ROOT / "docs/tonewood"
SKIP_DOCS = {"README.md", "VERIFICATION_LOG.md", "CITES_STATUS.md"}

# doc name (lower case, markup stripped) -> (mechanical table, species, shrinkage table, species)
# Only unambiguous identities. Left out on purpose: "Meranti", "Red Cedar", "Swamp Ash",
# "Urban Ash", "Hickory/Pecan", "Hard/Soft Maple", "White/Red Oak", and anything whose
# botanical name in the doc differs from FPL's.
US = "5-3a"
ALIASES: dict[str, tuple[str | None, str | None, str | None, str | None]] = {}


def _us(names: list[str], mech: str | None, shrink: str | None = None) -> None:
    for n in names:
        ALIASES[n] = (US if mech else None, mech, "4-3" if (shrink or mech) else None, shrink or mech)


def _imp(names: list[str], mech: str | None, shrink: str | None) -> None:
    for n in names:
        ALIASES[n] = ("5-5a" if mech else None, mech, "4-4" if shrink else None, shrink)


_us(["sitka spruce", "sitka"], "Spruce, Sitka")
_us(["engelmann spruce", "engelmann"], "Spruce, Engelmann")
_us(["adirondack spruce", "adirondack (red) spruce", "red spruce", "adirondack / red spruce"], "Spruce, Red")
_us(["western red cedar", "w. red cedar", "western redcedar"], "Cedar, Western redcedar")
_us(["alaskan yellow cedar", "yellow cedar"], "Cedar, Yellow")
_us(["port orford cedar"], "Cedar, Port-Orford")
_us(["redwood", "redwood (old growth)"], "Redwood, Old-growth", "Redwood, Old growth")
_us(["douglas-fir", "douglas fir"], "Douglas-fir, Coast")
_us(["bald cypress"], "Baldcypress", None)
ALIASES["bald cypress"] = (US, "Baldcypress", None, None)
_us(["hard maple", "sugar maple"], "Maple, Sugar")
_us(["soft maple", "red maple"], "Maple, Red")
_us(["black maple"], "Maple, Black")
_us(["black cherry"], "Cherry, black")
_us(["black walnut", "american black walnut"], "Walnut, black")
_us(["butternut"], "Butternut")
_us(["american sycamore", "am. sycamore"], "Sycamore, American")
_us(["sweetgum"], "Sweetgum")
_us(["black tupelo / blackgum", "black tupelo"], "Tupelo, Black")
_us(["water tupelo"], "Tupelo, Water")
_us(["sassafras"], "Sassafras")
_us(["yellow birch"], "Birch, Yellow")
_us(["sweet birch"], "Birch, Sweet")
_us(["paper birch"], "Birch, Paper")
_us(["american beech"], "Beech, American")
_us(["american chestnut"], "Chestnut, American")
_us(["american elm"], "Elm, American")
_us(["rock elm"], "Elm, Rock")
_us(["red / slippery elm", "slippery elm"], "Elm, Slippery")
_us(["white ash"], "Ash, White")
_us(["green ash"], "Ash, Green")
_us(["blue ash"], "Ash, Blue")
_us(["black ash"], "Ash, Black")
_us(["oregon ash"], "Ash, Oregon")
_us(["northern red oak"], "Oak, red, Northern red")
_us(["southern red oak"], "Oak, red, Southern red")
_us(["cherrybark oak"], "Oak, red, Cherrybark", None)
ALIASES["cherrybark oak"] = (US, "Oak, red, Cherrybark", None, None)
_us(["pin oak"], "Oak, red, Pin")
_us(["willow oak"], "Oak, red, Willow")
_us(["white oak"], "Oak, white, White")
_us(["chestnut oak"], "Oak, white, Chestnut")
_us(["swamp chestnut oak"], "Oak, white, Swamp chestnut", "Oak, white, Swamp, chestnut")
ALIASES["swamp white oak"] = (US, "Oak, white, Swamp white", None, None)
_us(["live oak"], "Oak, white, Live")
_us(["mockernut hickory"], "Hickory, true, Mockernut")
_us(["pignut hickory"], "Hickory, true, Pignut")
_us(["shagbark hickory"], "Hickory, true, Shagbark")
_us(["shellbark hickory"], "Hickory, true, Shellbark")
for n, m in (("bitternut hickory", "Bitternut"), ("nutmeg hickory", "Nutmeg"), ("water hickory", "Water"), ("pecan", "Pecan")):
    ALIASES[n] = (US, f"Hickory, pecan, {m}", "4-3", "Hickory, pecan")
_us(["black locust"], "Locust, black")
_us(["honey locust", "honeylocust"], "Honeylocust")
_us(["hackberry"], "Hackberry")
ALIASES["persimmon"] = (None, None, "4-3", "Persimmon, common")
ALIASES["winged elm"] = (None, None, "4-3", "Elm, Winged")
ALIASES["cedar elm"] = (None, None, "4-3", "Elm, Cedar")
ALIASES["pumpkin ash"] = (None, None, "4-3", "Ash, Pumpkin")
ALIASES["alaska paper birch"] = (None, None, "4-3", "Birch, Alaska paper")

_imp(["honduran mahogany", "mahogany", "swietenia macrophylla"],
     "Mahogany, true (Swietenia macrophylla)", "Mahogany, true (Swietenia macrophylla)")
_imp(["khaya", "african mahogany (khaya)", "african mahogany"],
     "Mahogany, African (Khaya spp.)", "Mahogany, African (Khaya spp.)")
_imp(["sapele", "entandrophragma cylindricum", "sapele / undianuno"],
     "Sapele (Entandrophragma cylindricum)", "Sapele (Entandrophragma cylindricum)")
_imp(["ovangkol", "ovangkol (shedua)", "ovangkol / shedua"],
     "Ovangkol (Guibourtia ehie)", "Ovangkol (Guibourta ehie)")
_imp(["bubinga"], "Bubinga (Guibourtia spp.)", "Bubinga (Guibourtia spp.)")
_imp(["teak"], "Teak (Tectona grandis)", "Teak (Tectona grandis)")
_imp(["okoume"], "Okoume (Aucoumea klaineana)", "Okoume (Aucoumea klaineana)")
_imp(["avodire", "turraeanthus africana"], "Avodire (Turraeanthus africanus)", "Avodire (Turreanthus africanus)")
_imp(["andiroba", "carapa guianensis"], "Andiroba (Carapa guianensis)", "Andiroba (Carapa guianensis)")
_imp(["jarrah"], "Jarrah (Eucalyptus marginata)", "Jarrah (Eucalyptus marginata)")
_imp(["terminalia superba", "limba"], "Limba (Terminalia superba)", "Limba (Terminalia superba)")
_imp(["spanish cedar", "cedrela odorata"], "Spanish-cedar (Cedrela spp.)", "Spanish-cedar (Cedrela spp.)")
_imp(["jatoba"], "Courbaril (Hymenaea courbaril)", "Courbaril (Hymenaea courbaril)")
_imp(["goncalo alves (tigerwood)", "goncalo alves"], "Goncalo alves (Astronium graveolens)", "Goncalo alves (Astronium graveolens)")
_imp(["greenheart"], "Greenheart (Chlorocardium rodiei)", None)
_imp(["bulletwood"], "Bulletwood (Manilkara bidentata)", "Bulletwood (Manilkara bidentata)")
_imp(["lignum vitae"], "Lignumvitae (Guaiacum spp.)", None)
_imp(["brazilian rosewood", "dalbergia nigra"], "Rosewood, Brazilian (Dalbergia nigra)", "Rosewood, Brazilian (Dalbergia nigra)")
_imp(["east indian rosewood", "dalbergia latifolia"], "Rosewood, Indian (Dalbergia latifolia)", "Rosewood, Indian (Dalbergia latifolia)")
_imp(["mora"], "Mora (Mora spp.)", "Mora (Mora spp.)")
_imp(["ipe", "ipe (brazilian walnut)"], "Ipe (Tabebuia spp., lapacho group)", "Ipe (Tabebuia spp.)")
_imp(["mvule / iroko", "iroko"], "Iroko (Chlorophora spp.)", "Iroko (Chlorophora excelsa and C. regia)")
_imp(["cocobolo", "dalbergia retusa"], None, "Cocobolo (Dalbergia retusa)")
_imp(["imbuia"], None, "Imbuia (Phoebe porosa)")
_imp(["merbau"], None, "Merbau (Intsia bijuga and I. palembanica)")

PROPS = [  # (regex on the row/column label, property key); first match wins
    (r"lb/ft|band|scale|rank", None),
    (r"speed of sound|sound speed", "c"),
    (r"impedance", "z"),
    (r"e/ρ|specific modulus", "erho"),
    (r"radiation", "r"),
    (r"specific gravity|^sg$", "sg"),
    (r"^(?!.*band)density", "density"),
    (r"janka.*\(n\)|hardness.*\(n\)", "janka_n"),
    (r"janka|^hardness$|hardness \(lbf\)", "janka_lbf"),
    (r"\bmoe\b|modulus of elasticity|elastic", "moe"),
    (r"\bmor\b|modulus of rupture", "mor"),
    (r"(shrinkage|contraction).*radial|^shrink r$", "radial"),
    (r"(shrinkage|contraction).*tangential|^shrink t$", "tangential"),
]
INPUTS = ("sg", "density", "janka_lbf", "janka_n", "moe", "mor", "radial", "tangential")
DERIVED = ("c", "z", "erho", "r")
DECIMALS = {"sg": 2, "density": 0, "janka_lbf": 0, "janka_n": 0, "moe": 1, "mor": 1, "radial": 1, "tangential": 1,
            "c": 0, "z": 2, "erho": 1, "r": 2}


def load_fpl() -> dict[tuple[str, str], dict[tuple[str, str], float]]:
    raw: dict[tuple[str, str], dict[tuple[str, str], float]] = defaultdict(dict)
    with FPL.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            raw[(r["table"], r["species"])][(r["condition"], r["property"])] = float(r["value"])
    return dict(raw)


def unresolved_aliases(raw: dict[tuple[str, str], dict]) -> list[str]:
    """Every FPL row an alias names must exist exactly, with the values the checker reads."""
    bad = []
    for name, (mt, ms, st, ss) in ALIASES.items():
        if mt and (mt, ms) not in raw:
            bad.append(f"{name!r}: no FPL row {mt} {ms!r}")
        if st:
            row = raw.get((st, ss))
            if row is None:
                bad.append(f"{name!r}: no FPL row {st} {ss!r}")
            elif not {("green_to_ovendry", "shrink_radial_pct"), ("green_to_ovendry", "shrink_tangential_pct")} <= set(row):
                bad.append(f"{name!r}: FPL row {st} {ss!r} lacks radial/tangential shrinkage")
        if not mt and not st:
            bad.append(f"{name!r}: maps to no FPL table")
    return bad


def fpl_values(raw: dict[tuple[str, str], dict[tuple[str, str], float]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for name, (mt, ms, st, ss) in ALIASES.items():
        v: dict[str, float] = {}
        shrink = raw[(st, ss)] if st else {}
        if shrink:
            v["radial"] = shrink[("green_to_ovendry", "shrink_radial_pct")]
            v["tangential"] = shrink[("green_to_ovendry", "shrink_tangential_pct")]
        if mt:
            mech = raw[(mt, ms)]
            g12 = mech.get(("12pct", "sg"))
            if g12 is None and ("green", "sg") in mech and shrink:
                s12 = shrink[("green_to_ovendry", "shrink_volumetric_pct")] * (1 - 12 / 30)
                g12 = mech[("green", "sg")] / (1 - s12 / 100)
            if g12:
                v["sg"] = g12
                v["density"] = 1000 * g12 * 1.12
            if ("12pct", "side_hardness_n") in mech:
                v["janka_n"] = mech[("12pct", "side_hardness_n")]
                v["janka_lbf"] = v["janka_n"] / 4.44822
            if ("12pct", "moe_mpa") in mech:
                v["moe"] = mech[("12pct", "moe_mpa")] / 1000
            if ("12pct", "mor_kpa") in mech:
                v["mor"] = mech[("12pct", "mor_kpa")] / 1000
        out[name] = v
    return out


def norm_name(cell: str) -> str:
    s = re.sub(r"\(\*[^)]*\*\)", "", cell)          # "(*Juglans nigra*)"
    s = re.sub(r"[*†ᵉ‡✅]", "", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    s = re.sub(r"^\d+\.\s*", "", s)
    s = re.sub(r"\s*\((for contrast|old growth)\)\s*❌?$", lambda m: " (old growth)" if "old" in m.group() else "", s).strip(" ❌")
    return s


def prop_of(label: str) -> str | None:
    lab = re.sub(r"[*]", "", label).strip().lower()
    for pat, key in PROPS:
        if re.search(pat, lab):
            return key
    return None


NUMTOK = re.compile(r"~?(?<![\d.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|~?(?<![\d.])\d+(?:\.\d+)?")


def numbers(cell: str) -> list[re.Match]:
    masked = re.sub(r"\[\^[^\]]*\]", lambda m: " " * len(m.group()), cell)  # footnote refs like [^7]
    if re.search(r"\d\s*[–-]\s*\d", masked):   # a range: not checked
        return []
    return list(NUMTOK.finditer(masked))


def is_range(cell: str) -> bool:
    masked = re.sub(r"\[\^[^\]]*\]", " ", cell)
    return bool(re.search(r"\d\s*[–-]\s*\d", masked))


def value_of(cell: str, key: str) -> float | None:
    ms = numbers(cell)
    if not ms:
        return None
    if key == "janka_n" and len(ms) > 1:
        for m in ms:
            if re.match(r"\s*N\b", cell[m.end():]):
                return float(m.group().lstrip("~").replace(",", ""))
    return float(ms[0].group().lstrip("~").replace(",", ""))


def fmt(key: str, val: float, orig: str) -> str:
    d = DECIMALS[key]
    return f"{val:,.{d}f}" if "," in orig else f"{val:.{d}f}"


class Cell:
    def __init__(self, path: Path, line: int, col: int, species: str, key: str | None, text: str):
        self.path, self.line, self.col, self.species, self.key, self.text = path, line, col, species, key, text


def cells_of(path: Path, lines: list[str]) -> list[Cell]:
    out: list[Cell] = []
    i = 0
    heading = ""
    while i < len(lines):
        h = re.match(r"^#{2,4}\s+(.+)$", lines[i])
        if h:
            heading = h.group(1)
        if not (lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1])):
            i += 1
            continue
        hdr = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        j = i + 2
        first = norm_name(hdr[0])
        while j < len(lines) and lines[j].startswith("|"):
            row = [c.strip() for c in lines[j].strip().strip("|").split("|")]
            if first == "property" and len(hdr) == 2 and norm_name(hdr[1]) == "value":
                sp = norm_name(re.sub(r"\(.*?\)|—.*$|:.*$", "", heading))
                if len(row) >= 2:
                    out.append(Cell(path, j, 1, sp, prop_of(row[0]), row[1]))
            elif first == "property":
                key = prop_of(row[0])
                for k, (h, cell) in enumerate(zip(hdr[1:], row[1:]), start=1):
                    out.append(Cell(path, j, k, norm_name(h), key, cell))
            elif first in ("species", "wood", "top wood"):
                for k, (h, cell) in enumerate(zip(hdr[1:], row[1:]), start=1):
                    out.append(Cell(path, j, k, norm_name(row[0]), prop_of(h), cell))
            elif any(norm_name(h) in ("species", "wood", "trade name") for h in hdr[1:]):
                # rank-style tables: "| # | Species | ... |" or "| Rank | Species | ... |"
                sc = next(k for k, h in enumerate(hdr) if norm_name(h) in ("species", "wood", "trade name"))
                if sc < len(row):
                    for k, (h, cell) in enumerate(zip(hdr, row)):
                        if k != sc:
                            out.append(Cell(path, j, k, norm_name(row[sc]), prop_of(h), cell))
            j += 1
        i = j
    return out


def derived(key: str, rho: float, moe: float) -> float:
    c = (moe * 1e9 / rho) ** 0.5
    return {"c": c, "z": rho * c / 1e6, "erho": moe / (rho / 1000), "r": c / rho}[key]


def replace_value(c: Cell, ref: float) -> str:
    text = c.text
    ms = numbers(text)
    if c.key in ("janka_lbf", "janka_n") and len(ms) > 1 and "lbf" in text and re.search(r"\bN\b", text):
        lbf = ref if c.key == "janka_lbf" else ref / 4.44822
        n = lbf * 4.44822
        out = text
        for m in reversed(ms):
            v = n if re.match(r"\s*N\b", text[m.end():]) else lbf
            out = out[: m.start()] + fmt("janka_n", v, m.group()) + out[m.end():]
        text = out
    else:
        m = ms[0]
        text = text[: m.start()] + fmt(c.key, ref, m.group()) + text[m.end():]
    if c.key in ("janka_lbf", "janka_n"):
        text = text.replace(" ᵉ", "").replace("ᵉ", "")
    return text


def run(fpl: dict[str, dict[str, float]], fix: bool):
    results = []  # (doc, line, species, key, doc value, FPL value, ok)
    ranges = []   # (doc, line, species, key, cell text): mapped species, recognised property, a range
    unmapped = 0
    for path in sorted(DOCS.glob("*.md")):
        if path.name in SKIP_DOCS:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        cells = cells_of(path, lines)
        edits: dict[tuple[int, int], str] = {}
        shown: dict[str, dict[str, float]] = defaultdict(dict)  # species -> displayed input after fixes
        for c in cells:
            if c.key is None or c.species not in fpl:
                unmapped += c.key is not None and c.species not in fpl
                continue
            if c.key not in INPUTS:
                continue
            val = value_of(c.text, c.key)
            if val is not None:
                # FPL value where FPL has one (the cell is fixed to it); otherwise the document's own
                shown[c.species].setdefault(c.key, fpl[c.species].get(c.key, val))
        for c in cells:
            if c.key is None or c.species not in fpl:
                continue
            ref_set = fpl[c.species]
            if c.key in INPUTS:
                if c.key not in ref_set:
                    continue
                ref = ref_set[c.key]
            elif c.key in DERIVED:
                rho = shown[c.species].get("density", ref_set.get("density"))
                moe = shown[c.species].get("moe", ref_set.get("moe"))
                if rho is None or moe is None or not ({"density", "moe"} & set(ref_set)):
                    continue
                ref = derived(c.key, rho, moe)
            else:
                continue
            if is_range(c.text):
                lo, hi = sorted(float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*\.?\d*", c.text)[:2])
                ranges.append((path.name, c.line + 1, c.species, c.key, c.text, ref, lo <= ref <= hi))
                continue
            val = value_of(c.text, c.key)
            if val is None:
                continue
            ok = abs(val - ref) <= 0.5 * 10 ** -DECIMALS[c.key] + 1e-9
            results.append((path.name, c.line + 1, c.species, c.key, val, ref, ok))
            if not ok:
                edits[(c.line, c.col)] = replace_value(c, ref)
        if fix and edits:
            for (ln, col), new in edits.items():
                parts = lines[ln].split("|")
                old = parts[col + 1]  # parts[0] is the empty string before the leading pipe
                lead = old[: len(old) - len(old.lstrip())]
                trail = old[len(old.rstrip()):]
                parts[col + 1] = f"{lead}{new}{trail}"
                lines[ln] = "|".join(parts)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return results, ranges, unmapped


def main(argv: list[str]) -> int:
    raw = load_fpl()
    bad_alias = unresolved_aliases(raw)
    if bad_alias:
        for b in bad_alias:
            print("ALIAS", b)
        print(f"{len(bad_alias)} aliases do not resolve to an FPL row; nothing checked")
        return 1
    fpl = fpl_values(raw)
    fix = "--fix" in argv
    if fix:
        results, _, _ = run(fpl, True)
        print(f"--fix rewrote {sum(1 for r in results if not r[6])} cells; checking again")
    results, ranges, unmapped = run(fpl, False)
    bad = [r for r in results if not r[6]]
    if "--summary" not in argv:
        for name, ln, sp, key, val, ref, _ in bad:
            print(f"{name}:{ln} {sp} {key}: doc {val:g} vs FPL {ref:.4g}")
        for name, ln, sp, key, text, ref, inside in ranges:
            where = "inside" if inside else "OUTSIDE"
            print(f"{name}:{ln} {sp} {key}: range {text!r} not compared (FPL {ref:.4g} {where})")
    by_key = defaultdict(lambda: [0, 0])
    for r in results:
        by_key[r[3]][0] += 1
        by_key[r[3]][1] += (not r[6])
    print(f"{len(ALIASES)} aliases resolve; {len(results)} cells checked, {len(bad)} mismatches; "
          f"{len(ranges)} range cells for mapped species not compared "
          f"({sum(1 for r in ranges if not r[6])} exclude the FPL value); "
          f"{unmapped} property cells skipped (species not mapped to FPL)")
    for k, (n, b) in sorted(by_key.items()):
        print(f"  {k}: {n} checked, {b} mismatched")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
