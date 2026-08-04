#!/usr/bin/env python3
"""Rebuild docs/calculators/acoustics/cohort_catalog.json and POINT_SEARCH_INDEX.md."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACOUSTICS = ROOT / "docs" / "calculators" / "acoustics"

KNOWN_PREFIX = {
    "P": "Gore Shop Talk #20",
    "H": "Gore Shop Talk #20 heuristics (H01–H10)",
    "W": "Gore wolf mailbag",
    "M": "Gore monopole mobility",
    "S": "Gore Shop Talk #25",
    "R": "Gore responsive objectives",
    "U": "Gore Shop Talk #44",
    "A": "Gore Shop Talk #51",
    "T": "Gore Guitar Analysis (partial) / theory refs",
    "Y": "Somogyi apprentice",
    "ES": "Somogyi primary",
    "N": "Nicoletti family",
    "PM": "Howman Physics Mind",
    "SB": "Shop soundboard species",
    "TB": "Shop top bracing journal",
    "IB": "Jacob I-beam",
    "BK": "Bashkin JM workflow",
    "GL": "Garrett Lee deflection Ep.13",
    "SC": "Schaefer compensated saddle",
    "HM": "Holmberg Gore modeling spreadsheets",
    "MB": "MB Sound / Nicoletti TPC panel laboratory records",
    "G": "Gap IDs (G-R01, G-GL01, …) — see pack GAPS file",
}

PHYSICS_PRIMARY_FORCE = {
    "garrett_lee_soundboard_deflection_ep13",
    "jacob_ibeam_bracing_physics",
}
SHOP_PRIMARY_FORCE = {
    "shop_bashkin_jm_build_workflow",
    "shop_soundboard_species_voicing",
    "shop_top_bracing_history_h_brace",
    "shop_schaefer_compensated_saddle",
    "somogyi_apprentice_build_workflow",
    "nicoletti_mb_kit_interview",
    "nicoletti_mb_sound_acoustic_study_set",
}


def extract_points(text: str) -> list[str]:
    ids = set()
    ids.update(re.findall(r"\*\*Point ID:\*\*\s*([A-Z]{1,3}\d{2,3})", text))
    ids.update(re.findall(r"Point ID[:\*]*\s*([A-Z]{1,3}\d{2,3})", text))
    ids.update(re.findall(r"^\| ([A-Z]{1,3}\d{2,3}) \|", text, re.M))
    # Heuristic rows sometimes use H1–H9 (one digit) — normalize to H0N
    for m in re.findall(r"^\| (H)(\d) \|", text, re.M):
        ids.add(f"{m[0]}0{m[1]}")
    ids.update(
        re.findall(
            r"\b((?:PM|SB|TB|IB|BK|GL|SC|HM|MB|ES|P|H|W|M|S|R|U|A|T|Y|N)\d{2,3})\b",
            text,
        )
    )
    ids.update(re.findall(r"\b(G-[A-Z]{1,3}\d{2,3})\b", text))
    return sorted(ids)


def keywords_from(readme: str, notes_text: str) -> list[str]:
    kws: set[str] = set()
    title = readme.split("\n", 1)[0].lstrip("#").strip()
    for token in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", title):
        kws.add(token.lower())
    for h in re.findall(r"^##+\s+(.+)$", notes_text, re.M)[:40]:
        for token in re.findall(r"[A-Za-z][A-Za-z\-]{4,}", h):
            kws.add(token.lower())
    domain = [
        "deflection",
        "mobility",
        "bracing",
        "soundboard",
        "voicing",
        "frf",
        "chladni",
        "monopole",
        "dipole",
        "intonation",
        "torrefied",
        "lining",
        "nitro",
        "fan",
        "x-brace",
        "i-beam",
        "cube",
        "thickness",
        "tap",
        "wolf",
        "falcate",
        "spruce",
        "cedar",
        "bridge",
        "saddle",
        "scale",
        "dome",
        "radius",
    ]
    blob = (readme + "\n" + notes_text).lower()
    for d in domain:
        if d in blob:
            kws.add(d)
    return sorted(kws)[:60]


def scan() -> dict:
    physics_text = (ACOUSTICS / "PHYSICS_KNOWLEDGE_INDEX.md").read_text()
    shop_text = (ACOUSTICS / "SHOP_BUILDING_KNOWLEDGE_INDEX.md").read_text()
    packs = []
    for p in sorted(ACOUSTICS.iterdir()):
        if not p.is_dir():
            continue
        files = {x.name for x in p.iterdir()}
        readme = (p / "README.md").read_text() if (p / "README.md").exists() else ""
        notes = None
        for n in ("ANNOTATED_LECTURE_NOTES.md", "ANNOTATED_WORKFLOW_NOTES.md"):
            if n in files:
                notes = n
                break
        notes_text = (p / notes).read_text() if notes else ""
        gaps_text = (
            (p / "GAPS_NOT_RECORDED.md").read_text()
            if (p / "GAPS_NOT_RECORDED.md").exists()
            else ""
        )
        point_ids = extract_points(notes_text + "\n" + gaps_text)
        prefixes = sorted(
            {
                (re.match(r"G-", i).group(0).rstrip("-") if i.startswith("G-") else re.match(r"[A-Z]+", i).group(0))
                for i in point_ids
                if re.match(r"[A-Z]", i)
            }
        )
        lane = []
        if f"./{p.name}/" in physics_text or f"`{p.name}/`" in physics_text:
            lane.append("physics")
        if f"./{p.name}/" in shop_text or f"`{p.name}/`" in shop_text:
            lane.append("shop")
        if "PHYSICS_KNOWLEDGE_INDEX" in readme and "physics" not in lane:
            lane.append("physics")
        if "SHOP_BUILDING_KNOWLEDGE_INDEX" in readme and "shop" not in lane:
            lane.append("shop")
        if not lane:
            lane = ["unfiled"]
        if p.name in PHYSICS_PRIMARY_FORCE:
            primary = "physics"
        elif p.name in SHOP_PRIMARY_FORCE or p.name.startswith("shop_"):
            primary = "shop"
        elif "physics" in lane:
            primary = "physics"
        else:
            primary = lane[0]
        req = [
            "README.md",
            "SOURCE_TRANSCRIPT.md",
            "CROSSWALK_TOOLBOX.md",
            "GAPS_NOT_RECORDED.md",
        ]
        missing = [r for r in req if r not in files]
        if not notes:
            missing.append("ANNOTATED_*")
        packs.append(
            {
                "pack_id": p.name,
                "title": readme.split("\n", 1)[0].lstrip("#").strip() if readme else p.name,
                "lane_primary": primary,
                "lane": lane,
                "dual_filed": len(lane) > 1,
                "notes_file": notes,
                "point_prefix": prefixes,
                "point_ids": point_ids,
                "point_count": len(point_ids),
                "has_process_workflow": "PROCESS_WORKFLOW.md" in files,
                "missing_template_files": missing,
                "search_keywords": keywords_from(readme, notes_text),
                "path": f"docs/calculators/acoustics/{p.name}/",
                "status": (
                    "partial"
                    if "PARTIAL" in readme.upper() or "partial" in readme.lower()[:500]
                    else "complete"
                ),
            }
        )
    return {
        "schema": "knowledge_pack_cohort_catalog_v1",
        "updated": date.today().isoformat(),
        "purpose": "Machine catalog so physics/shop cohorts stay annotated, searchable, and off the sandbox floor",
        "governance": "docs/calculators/acoustics/COHORT_GOVERNANCE.md",
        "known_point_prefixes": KNOWN_PREFIX,
        "packs": packs,
        "counts": {
            "packs": len(packs),
            "points": sum(p["point_count"] for p in packs),
            "unfiled": sum(1 for p in packs if "unfiled" in p["lane"]),
            "template_incomplete": sum(1 for p in packs if p["missing_template_files"]),
        },
    }


def write_search_index(catalog: dict) -> None:
    packs = catalog["packs"]
    lines = [
        "# Knowledge pack point search index\n",
        "**Generated from** [`cohort_catalog.json`](./cohort_catalog.json) · "
        "regenerate via `python scripts/knowledge_packs/build_cohort_catalog.py`\n",
        "**Governance:** [`COHORT_GOVERNANCE.md`](./COHORT_GOVERNANCE.md)\n",
        "\nUse this file (or ripgrep over `docs/calculators/acoustics/**/ANNOTATED_*.md`) "
        "to find teaching points by ID or keyword.\n",
        "\n## By point ID prefix\n",
    ]
    by_pref: dict[str, list] = {}
    for p in packs:
        for pref in p["point_prefix"]:
            by_pref.setdefault(pref, []).append(p)
    for pref in sorted(by_pref, key=lambda x: (len(x), x)):
        label = KNOWN_PREFIX.get(pref, "?")
        lines.append(f"\n### `{pref}` — {label}\n")
        for p in by_pref[pref]:
            ids = ", ".join(p["point_ids"][:8])
            more = f' … +{p["point_count"]-8}' if p["point_count"] > 8 else ""
            lines.append(
                f'- [`{p["pack_id"]}`](./{p["pack_id"]}/) ({p["point_count"]}): {ids}{more}\n'
            )
    lines.append("\n## By pack\n")
    lines.append(
        "| Pack | Lane | Points | Prefix | Process WF | Keywords (sample) |\n"
    )
    lines.append("|------|------|--------|--------|------------|-------------------|\n")
    for p in packs:
        kw = ", ".join(p["search_keywords"][:8])
        lanes = "+".join(p["lane"])
        wf = "yes" if p["has_process_workflow"] else ""
        lines.append(
            f'| [{p["pack_id"]}](./{p["pack_id"]}/) | {lanes} | {p["point_count"]} | '
            f'{", ".join(p["point_prefix"])} | {wf} | {kw} |\n'
        )
    lines.append("\n## Keyword → packs\n")
    inv: dict[str, list[str]] = {}
    for p in packs:
        for k in p["search_keywords"]:
            inv.setdefault(k, []).append(p["pack_id"])
    always = {
        "deflection",
        "mobility",
        "bracing",
        "soundboard",
        "voicing",
        "frf",
        "chladni",
        "monopole",
        "wolf",
        "i-beam",
        "lining",
    }
    for k in sorted(inv):
        if len(set(inv[k])) < 2 and k not in always:
            continue
        packs_l = ", ".join(f"`{x}`" for x in sorted(set(inv[k]))[:12])
        lines.append(f"- **{k}**: {packs_l}\n")
    (ACOUSTICS / "POINT_SEARCH_INDEX.md").write_text("".join(lines))


def main() -> int:
    catalog = scan()
    (ACOUSTICS / "cohort_catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
    write_search_index(catalog)
    print(
        f"Wrote catalog: {catalog['counts']['packs']} packs, "
        f"{catalog['counts']['points']} points; "
        f"unfiled={catalog['counts']['unfiled']} "
        f"incomplete={catalog['counts']['template_incomplete']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
