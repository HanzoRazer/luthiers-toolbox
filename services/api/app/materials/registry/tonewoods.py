# services/api/app/materials/registry/tonewoods.py
"""
Tonewood Registry (MAT-001)

Loads and queries luthier_tonewood_reference.json and wood_species.json.
All data access goes through this module — no other code reads the JSON files.

Provides:
    load_tonewoods()          — all 71 curated entries with computed acoustic indices
    get_tonewood(id)          — single entry by ID
    filter_by_role(role)      — entries suitable for a given instrument role
    filter_by_use(use)        — entries by typical_use tag
    load_wood_species()       — all 473 species with CNC data
    get_wood_species(id)      — single species by ID
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas import TonewoodEntry, WoodSpeciesEntry, MachiningNotes

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data file paths
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent.parent.parent / "data_registry" / "system" / "materials"
_TONEWOOD_FILE = _DATA_DIR / "luthier_tonewood_reference.json"
_SPECIES_FILE = _DATA_DIR / "wood_species.json"


# ---------------------------------------------------------------------------
# Loaders (cached — files are read once per process start)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_tonewoods() -> List[TonewoodEntry]:
    """
    Load all curated tonewood entries (Tier 1 + Tier 2).
    Computes acoustic indices on load via TonewoodEntry @computed_field.
    Cached — called once per process.
    """
    try:
        with open(_TONEWOOD_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("Failed to load tonewood reference: %s", exc)
        return []

    entries: List[TonewoodEntry] = []

    for tier_key in ("tier_1", "tier_2"):
        tier_data = raw.get(tier_key, {})
        # Support both dict (id→record) and list formats
        if isinstance(tier_data, dict):
            records = tier_data.values()
        else:
            records = tier_data

        for record in records:
            try:
                # Flatten machining_notes dict → MachiningNotes model
                mn_raw = record.get("machining_notes")
                machining = MachiningNotes(**mn_raw) if mn_raw else None
                entry = TonewoodEntry(
                    **{k: v for k, v in record.items() if k != "machining_notes"},
                    machining_notes=machining,
                    tier=tier_key,
                )
                entries.append(entry)
            except Exception as exc:  # audited: registry-load-fallback
                logger.warning("Skipped malformed tonewood record %s: %s",
                               record.get("id", "?"), exc)

    logger.info("Loaded %d tonewood entries (%d tier_1, %d tier_2)",
                len(entries),
                sum(1 for e in entries if e.tier == "tier_1"),
                sum(1 for e in entries if e.tier == "tier_2"))
    return entries


@lru_cache(maxsize=1)
def load_wood_species() -> List[WoodSpeciesEntry]:
    """
    Load all 473 species from wood_species.json.
    Flattens nested machining/thermal sub-dicts into WoodSpeciesEntry.
    Cached — called once per process.
    """
    try:
        with open(_SPECIES_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("Failed to load wood species: %s", exc)
        return []

    species_data = raw.get("species", [])
    if isinstance(species_data, dict):
        records = list(species_data.values())
    else:
        records = species_data

    entries: List[WoodSpeciesEntry] = []
    for record in records:
        try:
            physical  = record.get("physical", {})
            thermal   = record.get("thermal", {})
            machining = record.get("machining", {})
            lutherie  = record.get("lutherie", {})
            feed_clamp  = machining.get("feed_clamp", {})
            speed_clamp = machining.get("speed_clamp", {})
            warnings    = machining.get("warnings", {})

            entry = WoodSpeciesEntry(
                id=record["id"],
                name=record.get("name", record["id"]),
                scientific_name=record.get("scientific_name"),
                category=record.get("category"),
                density_kg_m3=physical.get("density_kg_m3"),
                specific_gravity=physical.get("specific_gravity"),
                janka_hardness_lbf=physical.get("janka_hardness_lbf"),
                grain=physical.get("grain"),
                workability=physical.get("workability"),
                specific_cutting_energy_j_per_mm3=thermal.get("specific_cutting_energy_j_per_mm3"),
                hardness_scale=machining.get("hardness_scale"),
                burn_tendency=machining.get("burn_tendency"),
                tearout_tendency=machining.get("tearout_tendency"),
                chipload_multiplier=machining.get("chipload_multiplier"),
                roughing_max_mm_min=feed_clamp.get("roughing_max_mm_min"),
                finishing_max_mm_min=feed_clamp.get("finishing_max_mm_min"),
                max_rpm=speed_clamp.get("max_rpm"),
                tone_character=lutherie.get("tone_character"),
                typical_uses=lutherie.get("typical_uses", []),
                guitar_relevance=record.get("guitar_relevance"),
            )
            entries.append(entry)
        except Exception as exc:  # audited: registry-load-fallback
            logger.warning("Skipped malformed species record %s: %s",
                           record.get("id", "?"), exc)

    logger.info("Loaded %d wood species entries", len(entries))
    return entries


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_tonewood(species_id: str) -> Optional[TonewoodEntry]:
    """Get a single tonewood entry by ID. None if not found."""
    for entry in load_tonewoods():
        if entry.id == species_id:
            return entry
    return None


def get_wood_species(species_id: str) -> Optional[WoodSpeciesEntry]:
    """Get a single wood species entry by ID. None if not found."""
    for entry in load_wood_species():
        if entry.id == species_id:
            return entry
    return None


def filter_by_role(role: str) -> List[TonewoodEntry]:
    """
    Return tonewoods suitable for a given instrument role.
    Role must match a value in typical_uses (e.g. 'soundboard', 'back_sides', 'fretboard').
    """
    return [e for e in load_tonewoods() if role in e.typical_uses]


def filter_by_use(use: str) -> List[TonewoodEntry]:
    """Alias for filter_by_role — same logic, different name."""
    return filter_by_role(use)


def get_tonewoods_index() -> Dict[str, TonewoodEntry]:
    """Return all tonewoods as id→entry dict for O(1) lookups."""
    return {e.id: e for e in load_tonewoods()}
