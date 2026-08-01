#!/usr/bin/env python3
"""Validate MB Sound panel corpus shape, TonewoodEntry name reuse, unit sanity.

  python scripts/mb_sound_validate_corpus.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = (
    ROOT
    / "services"
    / "api"
    / "app"
    / "data_registry"
    / "system"
    / "materials"
    / "panel_acoustic"
    / "mb_sound_panels.json"
)
SPECIES = (
    ROOT
    / "services"
    / "api"
    / "app"
    / "data_registry"
    / "system"
    / "materials"
    / "wood_species.json"
)

# Synonyms that collide with TonewoodEntry / create a parallel namespace
FORBIDDEN_KEYS = {
    "E_parallel_gpa",
    "E_perpendicular_gpa",
    "E_L",
    "E_L_gpa",
    "E_L_GPa",
    "youngs_modulus",
    "moe",
}

TONEWOOD_OVERLAP_KEYS = {
    "density_kg_m3",
    "specific_gravity",
    "modulus_of_elasticity_gpa",
    "E_C_gpa",
    "modulus_of_rupture_mpa",
    "speed_of_sound_m_s",
    "acoustic_impedance",
}


def _warn(msg: str, errors: list[str]) -> None:
    errors.append(msg)
    print(f"WARN: {msg}", file=sys.stderr)


def _scan_forbidden(obj: Any, path: str, errors: list[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else k
            if k in FORBIDDEN_KEYS:
                _warn(f"forbidden synonym key {here!r} — use TonewoodEntry names", errors)
            _scan_forbidden(v, here, errors)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _scan_forbidden(item, f"{path}[{i}]", errors)


def validate_panel(panel: dict[str, Any], species_ids: set[str], errors: list[str]) -> None:
    pid = panel.get("id", "<missing-id>")
    if not panel.get("id"):
        _warn("panel missing id", errors)

    if panel.get("record_kind") != "measured_panel":
        _warn(f"{pid}: record_kind must be 'measured_panel' (got {panel.get('record_kind')!r})", errors)

    sid = panel.get("species_id")
    if sid and sid not in species_ids:
        _warn(f"{pid}: species_id {sid!r} not in wood_species.json", errors)

    # Nested physical/elastic from v0.1 scaffold — reject so we don't keep two shapes
    for legacy in ("physical", "elastic", "geometry", "indices"):
        if legacy in panel:
            _warn(
                f"{pid}: legacy nest {legacy!r} — flatten TonewoodEntry fields; "
                f"panel-only under panel.*",
                errors,
            )

    dens = panel.get("density_kg_m3")
    if dens is not None and not (200 <= float(dens) <= 1400):
        _warn(f"{pid}: density_kg_m3={dens} outside 200–1400 (unit trap?)", errors)

    el = panel.get("modulus_of_elasticity_gpa")
    ec = panel.get("E_C_gpa")
    if el is not None and not (2 <= float(el) <= 30):
        _warn(f"{pid}: modulus_of_elasticity_gpa={el} unusual for GPa", errors)
    if ec is not None and not (0.1 <= float(ec) <= 5):
        _warn(f"{pid}: E_C_gpa={ec} unusual for GPa", errors)

    panel_block = panel.get("panel") or {}
    if el and ec and float(ec) > 0:
        r = float(el) / float(ec)
        stated = panel_block.get("R_anis")
        if stated is not None and abs(r - float(stated)) / r > 0.15:
            _warn(f"{pid}: panel.R_anis {stated} disagrees with MOE/E_C={r:.2f}", errors)

    mass = panel_block.get("mass_g")
    L = panel_block.get("length_mm")
    W = panel_block.get("width_mm")
    h = panel_block.get("thickness_mm")
    if all(v is not None for v in (mass, L, W, h, dens)):
        vol_m3 = (float(L) * float(W) * float(h)) * 1e-9
        if vol_m3 > 0:
            rho_geom = (float(mass) / 1000.0) / vol_m3
            if abs(rho_geom - float(dens)) / float(dens) > 0.08:
                _warn(
                    f"{pid}: density from mass/volume={rho_geom:.1f} vs stated {dens}",
                    errors,
                )

    for mode in panel_block.get("modes") or []:
        f = mode.get("frequency_hz")
        if f is not None and not (10 <= float(f) <= 2000):
            _warn(f"{pid}: mode frequency_hz={f} outside 10–2000", errors)

    _scan_forbidden(panel, "", errors)

    # Soft check: at least one Tonewood overlap key present when row is non-template
    if any(panel.get(k) is not None for k in TONEWOOD_OVERLAP_KEYS):
        pass


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    args = p.parse_args(argv)

    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    panels = corpus.get("panels") or []
    species_doc = json.loads(SPECIES.read_text(encoding="utf-8"))
    species_ids: set[str] = set()
    if isinstance(species_doc, dict):
        block = species_doc.get("species") or {}
        if isinstance(block, dict):
            species_ids = set(block.keys()) | {
                v.get("id") for v in block.values() if isinstance(v, dict) and v.get("id")
            }
    species_ids.discard(None)  # type: ignore[arg-type]

    errors: list[str] = []
    _scan_forbidden(corpus.get("_meta") or {}, "_meta", errors)
    # Allow documenting forbidden names in meta.forbidden_synonyms list values
    errors = [e for e in errors if "forbidden_synonyms" not in e]

    ids: set[str] = set()
    for panel in panels:
        pid = panel.get("id")
        if pid in ids:
            _warn(f"duplicate id {pid!r}", errors)
        if pid:
            ids.add(pid)
        validate_panel(panel, species_ids, errors)

    meta_count = (corpus.get("_meta") or {}).get("panel_count")
    if meta_count is not None and meta_count != len(panels):
        _warn(f"_meta.panel_count={meta_count} != len(panels)={len(panels)}", errors)

    print(f"panels: {len(panels)}; species_ids loaded: {len(species_ids)}")
    if not panels:
        print("OK (empty scaffold)")
        return 0
    if errors:
        print(f"FAIL: {len(errors)} warning(s) treated as validation issues")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
