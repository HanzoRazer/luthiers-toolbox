"""
Context retrieval for LLM assistant queries.

Assembles context packets from:
1. Project data (rmos.sqlite3 projects table)
2. Wood species database (material_db.json)
3. Instrument specifications (instrument_model_registry.json)

The context packet is truncated to max_tokens to fit within LLM context windows.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

# Data file paths relative to app directory
APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR.parent / "data"

MATERIAL_DB_PATH = APP_DIR / "assets" / "material_db.json"
INSTRUMENT_REGISTRY_PATH = APP_DIR / "instrument_geometry" / "instrument_model_registry.json"
RMOS_DB_PATH = DATA_DIR / "rmos.sqlite3"

# Instrument family aliases for matching
INSTRUMENT_ALIASES: dict[str, list[str]] = {
    "dreadnought": ["dreadnought", "d-28", "d28", "martin d"],
    "stratocaster": ["stratocaster", "strat", "fender strat"],
    "les_paul": ["les paul", "lespaul", "les-paul", "lp", "gibson les paul"],
    "telecaster": ["telecaster", "tele", "fender tele"],
    "jazz_bass": ["jazz bass", "j-bass", "jbass"],
    "es_335": ["es-335", "es335", "335", "semi-hollow"],
    "flying_v": ["flying v", "flying-v", "v-shape"],
    "explorer": ["explorer", "gibson explorer"],
    "classical": ["classical", "nylon string", "spanish guitar"],
    "om_000": ["om", "000", "orchestra model"],
    "archtop": ["archtop", "arch-top", "jazz box"],
    "ukulele": ["ukulele", "uke"],
    "smart_guitar": ["smart guitar", "smartguitar", "iot guitar"],
}


def _load_json(path: Path) -> Any:
    """Load JSON file, return empty dict/list on failure."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _get_project_data(project_id: str) -> dict[str, Any]:
    """Load project data from rmos.sqlite3 projects table."""
    if not RMOS_DB_PATH.exists():
        return {}

    try:
        conn = sqlite3.connect(str(RMOS_DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM projects WHERE id = ? OR project_id = ? LIMIT 1",
            (project_id, project_id),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
    except sqlite3.Error:
        pass

    return {}


def _search_materials(query: str) -> list[dict[str, Any]]:
    """Search materials by name in material_db.json."""
    materials = _load_json(MATERIAL_DB_PATH)
    if not isinstance(materials, list):
        return []

    query_lower = query.lower()
    matches = []

    for mat in materials:
        title = mat.get("title", "").lower()
        mat_id = mat.get("id", "").lower()

        if query_lower in title or query_lower in mat_id:
            matches.append(mat)

    return matches[:5]  # Limit to top 5


def _match_instrument_family(message: str) -> Optional[str]:
    """Match instrument family mentioned in message."""
    message_lower = message.lower()

    for family_id, aliases in INSTRUMENT_ALIASES.items():
        for alias in aliases:
            if alias in message_lower:
                return family_id

    return None


def _get_instrument_spec(family_id: str) -> dict[str, Any]:
    """Load instrument spec from registry."""
    registry = _load_json(INSTRUMENT_REGISTRY_PATH)
    models = registry.get("models", {})
    return models.get(family_id, {})


def _extract_wood_names(message: str) -> list[str]:
    """Extract potential wood names from message."""
    # Common wood species in lutherie
    wood_keywords = [
        "maple", "mahogany", "rosewood", "ebony", "spruce", "cedar",
        "walnut", "ash", "alder", "basswood", "koa", "cocobolo",
        "padauk", "purpleheart", "wenge", "bubinga", "sapele",
        "oak", "cherry", "poplar", "birch", "mdf", "plywood"
    ]

    found = []
    message_lower = message.lower()

    for wood in wood_keywords:
        if wood in message_lower:
            found.append(wood)

    return found


def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Rough truncation to approximate token limit (4 chars ≈ 1 token)."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def build_context_packet(
    message: str,
    project_id: Optional[str] = None,
    max_tokens: int = 2000,
) -> str:
    """
    Build context packet for LLM assistant from available data sources.

    Args:
        message: User's query message
        project_id: Optional project ID to load from rmos.sqlite3
        max_tokens: Maximum tokens for context (rough approximation)

    Returns:
        Formatted context string for LLM prompt
    """
    sections: list[str] = []

    # 1. Project data if project_id provided
    if project_id:
        project = _get_project_data(project_id)
        if project:
            sections.append("## Project Data")
            # Extract key fields
            for key in ["name", "description", "instrument_type", "scale_length_mm",
                        "body_wood", "neck_wood", "fretboard_wood", "status"]:
                if key in project and project[key]:
                    sections.append(f"- {key}: {project[key]}")

    # 2. Wood species matches
    wood_names = _extract_wood_names(message)
    if wood_names:
        all_matches = []
        for wood_name in wood_names:
            matches = _search_materials(wood_name)
            all_matches.extend(matches)

        if all_matches:
            sections.append("\n## Materials")
            seen = set()
            for mat in all_matches:
                mat_id = mat.get("id", "")
                if mat_id not in seen:
                    seen.add(mat_id)
                    title = mat.get("title", mat_id)
                    sce = mat.get("sce_j_per_mm3", "N/A")
                    sections.append(f"- {title}: specific cutting energy = {sce} J/mm³")

    # 3. Instrument spec if family mentioned
    family = _match_instrument_family(message)
    if family:
        spec = _get_instrument_spec(family)
        if spec:
            sections.append(f"\n## Instrument: {spec.get('display_name', family)}")
            sections.append(f"- Category: {spec.get('category', 'N/A')}")
            sections.append(f"- Scale length: {spec.get('scale_length_mm', 'N/A')} mm")
            sections.append(f"- Frets: {spec.get('fret_count', 'N/A')}")
            sections.append(f"- Strings: {spec.get('string_count', 'N/A')}")
            sections.append(f"- Status: {spec.get('status', 'N/A')}")

            if spec.get("cam_capable"):
                ops = spec.get("cam_operations", [])
                sections.append(f"- CAM operations: {', '.join(ops)}")

            if spec.get("description"):
                sections.append(f"- Description: {spec['description'][:200]}...")

    # Combine and truncate
    if not sections:
        return ""

    context = "\n".join(sections)
    return _truncate_to_tokens(context, max_tokens)
