#!/usr/bin/env python3
"""Corpus-level validation for the MB Sound empirical tonewood dataset.

  python3 scripts/mb_sound_validate_corpus.py
  python3 scripts/mb_sound_validate_corpus.py --write-validation
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORPUS = (
    ROOT
    / "services"
    / "api"
    / "app"
    / "data_registry"
    / "system"
    / "materials"
    / "empirical_tonewood"
    / "mb_sound"
)
SPECIES_SOT = (
    ROOT
    / "services"
    / "api"
    / "app"
    / "data_registry"
    / "system"
    / "materials"
    / "wood_species.json"
)

FORBIDDEN_NORMALIZED = {
    "E_parallel_gpa",
    "E_perpendicular_gpa",
    "stiffness_gpa",
    "youngs_modulus",
    "moe",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _digest_specimens(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.name):
        h.update(path.name.encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _species_ids() -> set[str]:
    doc = _load(SPECIES_SOT)
    block = doc.get("species") or {}
    ids = set(block.keys())
    for v in block.values():
        if isinstance(v, dict) and v.get("id"):
            ids.add(v["id"])
    return ids


def validate(write: bool) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not CORPUS.is_dir():
        print(f"FAIL: corpus missing at {CORPUS}", file=sys.stderr)
        return 2

    specimen_paths = sorted(CORPUS.joinpath("specimens").glob("mb-*.json"))
    specimens = [_load(p) for p in specimen_paths]
    sot = _species_ids()

    ids = [s.get("specimen_id") for s in specimens]
    if len(ids) != len(set(ids)):
        errors.append("duplicate specimen_id values")
    for sid in ids:
        if not sid or not str(sid).startswith("mb-"):
            errors.append(f"bad specimen_id {sid!r}")

    # Catalog IDs restart per MB Sound suite/video; uniqueness is (species_cohort, catalog_id).
    catalog_keys = []
    for s in specimens:
        src = s.get("source") or {}
        cid = src.get("catalog_id")
        aname = src.get("analysis_sample_name")
        cohort = s.get("species_cohort") or s.get("species_id") or ""
        if not cid:
            errors.append(f"{s.get('specimen_id')}: missing source.catalog_id")
        else:
            catalog_keys.append((str(cohort), str(cid)))
        if not aname:
            warnings.append(f"{s.get('specimen_id')}: missing analysis_sample_name")
        if not s.get("species_id") and s.get("species_id") is not None:
            pass
        sid = s.get("species_id")
        if sid and sid not in sot:
            errors.append(f"{s.get('specimen_id')}: species_id {sid!r} not in wood_species.json")
        if not s.get("treatment"):
            warnings.append(f"{s.get('specimen_id')}: missing treatment")

        # layer presence
        for layer in ("source", "normalized", "derived", "validation", "unresolved", "artifacts"):
            if layer not in s:
                errors.append(f"{s.get('specimen_id')}: missing layer {layer}")

        # Laboratory procedural schema (mb_sound_lab_procedure_v1)
        schema = s.get("record_schema")
        if schema != "mb_sound_lab_procedure_v1":
            warnings.append(
                f"{s.get('specimen_id')}: record_schema {schema!r} "
                f"(expected mb_sound_lab_procedure_v1)"
            )
        else:
            for section in (
                "identity",
                "specimen_geometry",
                "measurement_procedure",
                "signal_recording",
                "vendor_surfaces",
                "resonance_modes",
                "batch",
                "field_provenance",
            ):
                if section not in src:
                    errors.append(
                        f"{s.get('specimen_id')}: missing source.{section} "
                        f"(lab_procedure_v1)"
                    )
            surfaces = src.get("vendor_surfaces") or {}
            if "summary_card" not in surfaces or "detailed_analysis" not in surfaces:
                errors.append(
                    f"{s.get('specimen_id')}: vendor_surfaces needs "
                    f"summary_card + detailed_analysis"
                )
            if "signal" not in (s.get("normalized") or {}):
                warnings.append(f"{s.get('specimen_id')}: missing normalized.signal")

        norm = s.get("normalized") or {}
        for bad in FORBIDDEN_NORMALIZED:
            if bad in norm:
                errors.append(f"{s.get('specimen_id')}: forbidden normalized key {bad}")

        # mass / density / volume
        L = norm.get("length_mm")
        W = norm.get("width_mm")
        h = norm.get("thickness_mm")
        mass = norm.get("mass_g")
        dens = norm.get("density_kg_m3")
        if all(v is not None for v in (L, W, h, mass, dens)):
            vol = (float(L) * float(W) * float(h)) * 1e-9
            rho_g = (float(mass) / 1000.0) / vol if vol else None
            if rho_g is not None and abs(rho_g - float(dens)) / float(dens) > 0.08:
                errors.append(
                    f"{s.get('specimen_id')}: density geom {rho_g:.2f} vs stated {dens}"
                )
        else:
            warnings.append(f"{s.get('specimen_id')}: incomplete geometry for mass/density check")

        # Q vs log decrement (δ ≈ π/Q for small damping)
        q = norm.get("q_factor")
        logd = norm.get("log_decrement")
        if q and logd and float(q) > 0:
            expected = math.pi / float(q)
            if abs(expected - float(logd)) / expected > 0.25:
                warnings.append(
                    f"{s.get('specimen_id')}: log_decrement {logd} vs π/Q={expected:.5f} (>25%)"
                )

        # radiation: vendor ≈ c/ρ if E,ρ present
        e = norm.get("modulus_of_elasticity_gpa")
        rad = norm.get("radiation_coefficient_vendor")
        if e and dens and rad:
            c = math.sqrt(float(e) * 1e9 / float(dens))
            schelleng = c / float(dens)
            if abs(schelleng - float(rad)) / float(rad) > 0.05:
                warnings.append(
                    f"{s.get('specimen_id')}: radiation_vendor {rad} vs c/ρ={schelleng:.3f}"
                )

    if len(catalog_keys) != len(set(catalog_keys)):
        errors.append("duplicate (species_cohort, source.catalog_id) pairs")

    by_species = Counter(s.get("species_cohort") or s.get("species_id") for s in specimens)
    by_treatment = Counter(s.get("treatment") for s in specimens)
    digest = _digest_specimens(specimen_paths)

    consistency = {
        "dataset": "mb_sound",
        "specimen_count": len(specimens),
        "unique_specimen_ids": len(set(ids)),
        "counts_by_species_cohort": dict(by_species),
        "counts_by_treatment": dict(by_treatment),
        "dataset_digest_sha256": digest,
        "errors": errors,
        "warnings": warnings,
        "gates": {
            "unique_specimen_ids": len(ids) == len(set(ids)) and len(ids) == len(specimens),
            "unique_catalog_ids_per_cohort": len(catalog_keys) == len(set(catalog_keys)),
            "layer_separation": not any("missing layer" in e for e in errors),
            "no_forbidden_normalized_synonyms": not any("forbidden normalized" in e for e in errors),
            "intake_complete_approx_60": len(specimens) >= 55,
            "production_behavior_unchanged": True,
        },
        "draft_ready_for_merge": False,
        "notes": "draft_ready_for_merge stays false until intake_complete and error-free DO-SIP-013 gates.",
    }

    unresolved = {
        "dataset": "mb_sound",
        "corpus_level": [
            "Full ~60-specimen intake incomplete",
            "Confirm four-species catalog membership vs public MB Sound listing",
            "Radiation coefficient formal definition (Nicoletti vs Schelleng vs Toolbox scale)",
            "E_C_gpa absent on current specimens — blocks orthotropic plate adapters",
        ],
        "per_specimen": {
            s.get("specimen_id"): s.get("unresolved") for s in specimens if s.get("unresolved")
        },
    }

    if write:
        (CORPUS / "validation" / "consistency_results.json").write_text(
            json.dumps(consistency, indent=2) + "\n", encoding="utf-8"
        )
        (CORPUS / "validation" / "unresolved_fields.json").write_text(
            json.dumps(unresolved, indent=2) + "\n", encoding="utf-8"
        )
        schemas = Counter(s.get("record_schema") for s in specimens)
        manifest = {
            "dataset": "mb_sound",
            "dataset_version": "0.5.0-draft",
            "record_schema": "mb_sound_lab_procedure_v1",
            "vendor": "Maderas Barber",
            "authority_status": "non_authoritative_draft_intake",
            "program": "DO-SIP-013",
            "target_specimen_count_approx": 60,
            "target_species_count_approx": 4,
            "specimen_count": len(specimens),
            "specimen_ids": sorted(str(i) for i in ids if i),
            "species_cohorts": sorted(by_species.keys(), key=lambda x: str(x)),
            "treatments": sorted(str(t) for t in by_treatment if t),
            "record_schemas": dict(schemas),
            "dataset_digest_sha256": digest,
            "paths": {
                "specimens": "specimens/",
                "species": "species/",
                "source_artifacts": "source_artifacts/",
                "validation": "validation/",
                "process_docs": "docs/reference/mb-sound/",
            },
            "layer_contract": [
                "source",
                "normalized",
                "derived",
                "validation",
                "unresolved",
                "artifacts",
            ],
            "forbidden_production_effects": [
                "generator_defaults",
                "TonewoodEntry_authority",
                "plate_solver_defaults",
                "wood_species.json_overwrite",
            ],
            "draft_merge_blocked_until": [
                "corpus intake ~complete",
                "consistency_results.errors empty",
                "gates.intake_complete_approx_60 true",
            ],
        }
        (CORPUS / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    print(f"specimens: {len(specimens)}; digest: {digest[:16]}…")
    print(f"by species: {dict(by_species)}; by treatment: {dict(by_treatment)}")
    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print("FAIL")
        return 1
    print("OK (draft intake — merge gates not satisfied until ~60 specimens)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--write-validation",
        action="store_true",
        help="Write manifest.json + validation/*.json",
    )
    args = p.parse_args(argv)
    return validate(write=args.write_validation)


if __name__ == "__main__":
    raise SystemExit(main())
