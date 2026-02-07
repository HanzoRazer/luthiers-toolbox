"""
RMOS Strip Family Template Loader (MM-0)

Loads curated mixed-material strip family templates from JSON and
provides utilities to instantiate them as real strip family records.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any

from ..schemas.strip_family import StripFamilyTemplate
from ..stores.rmos_stores import get_rmos_stores


DEFAULT_TEMPLATES_PATH = Path(os.getcwd()) / "data" / "rmos" / "strip_family_templates.json"


def load_templates(path: Path = DEFAULT_TEMPLATES_PATH) -> List[StripFamilyTemplate]:
    """
    Load strip family templates from JSON file.
    
    Returns:
        List of validated StripFamilyTemplate objects
    """
    if not path.exists():
        return []
    
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    
    out: List[StripFamilyTemplate] = []
    for item in raw:
        try:
            out.append(StripFamilyTemplate(**item))
        except (ValueError, TypeError) as e:  # WP-1: narrowed from except Exception
            # Skip malformed entries (log in production)
            print(f"Warning: Skipping invalid template: {e}")
            continue
    
    return out


def apply_template_to_store(template_id: str) -> Dict[str, Any]:
    """
    Find a template by ID and persist it as a real strip_family record.
    
    Args:
        template_id: Template identifier
        
    Returns:
        Created strip family dict
        
    Raises:
        ValueError: If template not found
    """
    templates = load_templates()
    templ = next((t for t in templates if t.id == template_id), None)
    if not templ:
        raise ValueError(f"Strip family template '{template_id}' not found.")

    stores = get_rmos_stores()

    # Check if already exists
    existing = stores.strip_families.get_by_id(template_id)
    if existing:
        return existing

    # Convert Pydantic model to dict and add defaults
    payload = templ.dict()
    payload.setdefault("lane", "experimental")
    payload.setdefault("color_hex", "#999999")
    
    return stores.strip_families.create(payload)
