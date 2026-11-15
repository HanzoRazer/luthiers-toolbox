"""Regenerate docs/tonewood/tonewood_catalog_cirad_high_density.md from the
CIRAD wood density CSV using the per-taxon MEAN of every specimen.

The 2026-06-22 version selected taxa by their single heaviest specimen and
printed that maximum as "D12" next to averaged Db/R%. This generator applies
one statistic throughout and prints the range so spread stays visible.

Usage: python gen_cirad_catalog.py <repo_root> <out_md>
"""
import csv
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

THRESHOLD = 0.95
CONTINENT = {
    "Africa": "Africa", "Asia": "Asia", "Australia": "Australia",
    "Carribean": "Caribbean", "Central-America": "Central America",
    "Europe": "Europe", "Indian ocean": "Indian Ocean (incl. Madagascar)",
    "North-America": "North America", "Pacific ocean": "Pacific",
    "South-America": "South America",
}
BLURB = {
    "Leguminosae": "The legume family: rosewoods (*Dalbergia*), Swartzia/Bocoa, cumaru (*Dipteryx*), jatoba (*Hymenaea*).",
    "Sapotaceae": "The bulletwood family. Dense, fine-grained woods traditionally used for tool handles and heavy construction.",
    "Lauraceae": "Aromatic woods including cinnamon relatives.",
    "Myrtaceae": "The eucalyptus family. Australian hardwoods and plantation timber (CIRAD's samples include planted eucalypts outside Australia).",
    "Bignoniaceae": "The ipe/lapacho family. Known for extreme hardness and durability.",
    "Moraceae": "Contains bloodwood (*Brosimum*).",
    "Casuarinaceae": "She-oaks and Australian ironwoods.",
}
DETAIL_MIN = 5  # families with fewer taxa go into the summary table


def fmt(x, nd=2):
    return "—" if x is None else f"{x:.{nd}f}"


def load(csv_path: Path):
    rows = defaultdict(list)
    with csv_path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                d12 = float(r["D12"])
            except ValueError:
                continue
            rows[(r["Taxa"].strip(), r["Family"].strip())].append(r | {"_d12": d12})
    out = []
    for (taxon, fam), rs in rows.items():
        def mean(col):
            vals = []
            for r in rs:
                try:
                    vals.append(float(r[col]))
                except ValueError:
                    pass
            return st.mean(vals) if vals else None
        d = [r["_d12"] for r in rs]
        out.append({
            "taxon": taxon, "family": fam, "n": len(rs),
            "d12": st.mean(d), "dmin": min(d), "dmax": max(d),
            "db": mean("Db"), "r": mean("R"),
            "regions": sorted({CONTINENT.get(r["Continent"], r["Continent"]) for r in rs}),
            "countries": sorted({r["Country"] for r in rs}),
        })
    return out


def main():
    root, out_md = Path(sys.argv[1]), Path(sys.argv[2])
    src = root / "docs/reference/cirad-density/Cirad-wood-density-database.csv"
    taxa = load(src)
    by_max = sum(1 for t in taxa if t["dmax"] >= THRESHOLD)
    sel = sorted((t for t in taxa if t["d12"] >= THRESHOLD), key=lambda t: -t["d12"])
    fams = defaultdict(list)
    for t in sel:
        fams[t["family"]].append(t)
    fam_order = sorted(fams, key=lambda f: (-len(fams[f]), -max(t["d12"] for t in fams[f])))
    region_ct = defaultdict(list)
    for t in sel:
        for reg in t["regions"]:
            region_ct[reg].append(t)
    n_single = sum(1 for t in sel if t["n"] == 1)

    L = []
    w = L.append
    w("# CIRAD High-Density Species Catalog (mean D12 ≥ 0.95 g/cm³)\n")
    w("> **Source:** CIRAD Wood Density Database (Vieilledent et al. 2018), "
      "`docs/reference/cirad-density/Cirad-wood-density-database.csv`")
    w("> **Regenerated:** 2026-11-14 by `scripts/gen_cirad_high_density_catalog.py` (replaces the 2026-06-22 hand-built version)")
    w("> **Related:** `tonewood_comparison_extreme_density_glassy_character.md`, `VERIFICATION_LOG.md`\n")
    w(f"**{len(sel)} taxa across {len(fams)} families** have a **mean** D12 ≥ {THRESHOLD} g/cm³ "
      f"over all their CIRAD specimens ({len(taxa)} taxa in the file).\n")
    w("> **Correction (2026-11-14).** The previous version listed 217 taxa. It selected each taxon by "
      "its *heaviest single specimen* and printed that maximum as D12 beside averaged Db and R%. "
      f"Selecting by maximum gives {by_max} taxa; selecting by mean gives {len(sel)}. Every value "
      "below is now a mean over all specimens, with the min–max range shown. See `VERIFICATION_LOG.md` (C-01).\n")
    w(f"> **Caution.** {n_single} of the {len(sel)} taxa rest on a single specimen. "
      "Genus-only rows (`sp`) pool unidentified specimens and are not species values. "
      "CIRAD gives density and shrinkage only — no stiffness (MOE), so nothing here ranks acoustic quality.\n")
    w("---\n\n## Legend\n")
    w("- **D12** = mean density at 12% moisture content (g/cm³) over N specimens")
    w("- **Range** = lowest–highest specimen D12")
    w("- **Db** = mean basic density (oven-dry mass / green volume), as measured by CIRAD — not converted from D12")
    w("- **R** = mean volumetric shrinkage coefficient (% per % moisture change)")
    w("- **N** = number of CIRAD specimens\n")
    w("---\n\n## Summary by Family\n")
    w("| Family | Taxa | Highest mean D12 | Taxa (top 3 by mean D12) |")
    w("|--------|:----:|:----------------:|--------------------------|")
    for f in fam_order:
        ts = fams[f]
        top = ", ".join(f"*{t['taxon']}*" for t in ts[:3])
        w(f"| **{f}** | {len(ts)} | {ts[0]['d12']:.2f} | {top} |")
    w(f"| **Total** | **{len(sel)}** | | |\n")
    w("---\n\n## Regional Distribution\n")
    w("A taxon sampled on more than one continent is counted in each, so rows can sum to more than the total.\n")
    w("| Region | Taxa | Mean D12 range |")
    w("|--------|:----:|:--------------:|")
    for reg, ts in sorted(region_ct.items(), key=lambda kv: -len(kv[1])):
        lo, hi = min(t["d12"] for t in ts), max(t["d12"] for t in ts)
        w(f"| {reg} | {len(ts)} | {lo:.2f}–{hi:.2f} |")
    w("\n---\n\n# Complete Catalog by Family\n")
    small = []
    for f in fam_order:
        ts = fams[f]
        if len(ts) < DETAIL_MIN:
            small.append(f)
            continue
        w(f"## {f} — {len(ts)} taxa\n")
        if f in BLURB:
            w(BLURB[f] + "\n")
        w("| D12 | Range | Db | R | N | Taxon | Region |")
        w("|:---:|:-----:|:--:|:-:|:-:|-------|--------|")
        for t in ts:
            w(f"| {t['d12']:.2f} | {t['dmin']:.2f}–{t['dmax']:.2f} | {fmt(t['db'])} | {fmt(t['r'])} "
              f"| {t['n']} | *{t['taxon']}* | {', '.join(t['regions'])} |")
        w("\n---\n")
    nsmall = sum(len(fams[f]) for f in small)
    w(f"## Families with fewer than {DETAIL_MIN} taxa ({len(small)} families, {nsmall} taxa)\n")
    w("| Family | D12 | Range | Db | R | N | Taxon | Region |")
    w("|--------|:---:|:-----:|:--:|:-:|:-:|-------|--------|")
    for f in small:
        for t in fams[f]:
            w(f"| {f} | {t['d12']:.2f} | {t['dmin']:.2f}–{t['dmax']:.2f} | {fmt(t['db'])} | {fmt(t['r'])} "
              f"| {t['n']} | *{t['taxon']}* | {', '.join(t['regions'])} |")
    w("\n---\n\n## Best-sampled taxa\n")
    w("Named species (not `sp`) with N ≥ 5, by mean D12. A large N means the mean is less likely to "
      "be one unusual tree; it says nothing about tone.\n")
    w("| Taxon | Family | D12 | Range | N | Countries |")
    w("|-------|--------|:---:|:-----:|:-:|-----------|")
    for t in [t for t in sel if t["n"] >= 5 and not t["taxon"].endswith(" sp")][:20]:
        w(f"| *{t['taxon']}* | {t['family']} | {t['d12']:.2f} | {t['dmin']:.2f}–{t['dmax']:.2f} "
          f"| {t['n']} | {', '.join(t['countries'])} |")
    w("\n---\n\n## References\n")
    w("- Vieilledent G. et al. 2018. Bayesian modeling of wood density. *American Journal of Botany* doi:10.1002/ajb2.1175")
    w("- Data: `docs/reference/cirad-density/Cirad-wood-density-database.csv`")
    w("- Regenerate: `python scripts/gen_cirad_high_density_catalog.py . docs/tonewood/tonewood_catalog_cirad_high_density.md`")
    out_md.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"taxa={len(taxa)} by_max={by_max} by_mean={len(sel)} families={len(fams)} single_specimen={n_single}")


if __name__ == "__main__":
    main()
