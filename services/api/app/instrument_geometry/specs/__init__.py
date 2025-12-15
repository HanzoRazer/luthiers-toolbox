"""
Instrument Specs Package

Contains detailed specifications for specific instrument models,
including dimensions, bracing patterns, and construction data.

Specs are available as JSON files for data consumption and
Python modules for programmatic access.
"""

from pathlib import Path

# Specs directory path
SPECS_DIR = Path(__file__).parent

def get_spec_path(model_id: str) -> Path:
    """Get the path to a spec JSON file."""
    return SPECS_DIR / f"{model_id}.json"

def list_available_specs() -> list:
    """List all available spec files."""
    return [f.stem for f in SPECS_DIR.glob("*.json")]

__all__ = ["SPECS_DIR", "get_spec_path", "list_available_specs"]
