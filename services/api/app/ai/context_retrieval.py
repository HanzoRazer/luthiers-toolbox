"""
Context retrieval for LLM assistant queries.

Assembles context packets from:
1. Project data — SQLAlchemy ``Project`` row (``data`` JSONB holds InstrumentProjectData, including ``spec``)
2. Wood species — ``material_db.json`` (CNC reference) and optional ``wood_species.json`` snippets
3. Instrument specifications — ``instrument_model_registry.json`` (family match from user message)

The context packet is truncated to max_tokens to fit within LLM context windows.
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Optional

# Data file paths relative to app directory
APP_DIR = Path(__file__).resolve().parent.parent

MATERIAL_DB_PATH = APP_DIR / "assets" / "material_db.json"
INSTRUMENT_REGISTRY_PATH = APP_DIR / "instrument_geometry" / "instrument_model_registry.json"

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


def _get_project_data(project_id: str, owner_user_id: Optional[str] = None) -> dict[str, Any]:
    """
    Load project metadata and ``data.spec`` from the app database (Project ORM).

    If ``owner_user_id`` is set, only return a row owned by that user (privacy).
    """
    try:
        pid = uuid.UUID(project_id.strip())
    except (ValueError, AttributeError):
        return {}

    try:
        from app.db.session import db_session
        from app.db.models.project import Project
    except ImportError:
        return {}

    try:
        with db_session() as db:
            proj = db.get(Project, pid)
            if proj is None or proj.archived_at is not None:
                return {}
            if owner_user_id is not None and str(proj.owner_id) != owner_user_id:
                return {}

            raw_data = proj.data if isinstance(proj.data, dict) else {}
            spec = raw_data.get("spec") if isinstance(raw_data, dict) else None

            out: dict[str, Any] = {
                "id": str(proj.id),
                "name": proj.name,
                "description": proj.description,
                "instrument_type": proj.instrument_type,
                "spec": spec,
            }
            return out
    except Exception:
        return {}


def _summarize_spec_for_llm(spec: Any) -> list[str]:
    """Flatten InstrumentProjectData.spec (dict) into prompt lines."""
    if not spec or not isinstance(spec, dict):
        return []

    lines: list[str] = []
    # Common InstrumentSpec fields (see schemas/instrument_project.InstrumentSpec)
    for key in (
        "scale_length_mm",
        "fret_count",
        "string_count",
        "nut_width_mm",
        "heel_width_mm",
        "neck_angle_degrees",
        "body_join_fret",
    ):
        if key in spec and spec[key] is not None:
            lines.append(f"- {key}: {spec[key]}")

    nj = spec.get("neck_joint_type")
    if nj is not None:
        lines.append(f"- neck_joint_type: {nj!s}")

    trem = spec.get("tremolo_style")
    if trem is not None:
        lines.append(f"- tremolo_style: {trem!s}")

    return lines[:24]


def _wood_snippets_from_spec(spec: Any) -> list[str]:
    """Pull wood-like hints from material_selection or spec if present."""
    if not spec or not isinstance(spec, dict):
        return []
    found: list[str] = []
    ms = spec.get("material_selection")
    if isinstance(ms, dict):
        for _k, v in ms.items():
            if isinstance(v, str) and len(v) > 2:
                found.append(v.lower())
    return found[:12]


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
    owner_user_id: Optional[str] = None,
    max_tokens: int = 2000,
) -> str:
    """
    Build context packet for LLM assistant from available data sources.

    When ``project_id`` is set, project metadata and ``data.spec`` are loaded from the
    app database via ``_get_project_data`` (SQLAlchemy ``Project`` ORM) — not from
    RMOS SQLite or other offline stores.

    Args:
        message: User's query message
        project_id: Optional UUID of ``Project`` row (loads ``data.spec``)
        owner_user_id: If set, project is only loaded when ``owner_id`` matches
        max_tokens: Maximum tokens for context (rough approximation)

    Returns:
        Formatted context string for LLM prompt
    """
    sections: list[str] = []
    project: dict[str, Any] = {}

    # 1. Project data (Project ORM via _get_project_data)
    if project_id:
        project = _get_project_data(project_id, owner_user_id=owner_user_id)
        if project:
            sections.append("## Project Data")
            sections.append(f"- id: {project.get('id', '')}")
            sections.append(f"- name: {project.get('name', '')}")
            if project.get("description"):
                desc = str(project["description"])[:500]
                sections.append(f"- description: {desc}")
            if project.get("instrument_type"):
                sections.append(f"- instrument_type: {project['instrument_type']}")
            spec = project.get("spec")
            if spec:
                spec_lines = _summarize_spec_for_llm(spec)
                if spec_lines:
                    sections.append("- spec:")
                    sections.extend(spec_lines)

    # 2. Wood species matches (message + woods implied by project spec)
    wood_names = _extract_wood_names(message)
    if project:
        seen: set[str] = set()
        ordered: list[str] = []
        for w in wood_names + _wood_snippets_from_spec(project.get("spec")):
            if w not in seen:
                seen.add(w)
                ordered.append(w)
        wood_names = ordered
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
