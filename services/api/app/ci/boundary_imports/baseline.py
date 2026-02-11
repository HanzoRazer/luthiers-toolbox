"""Baseline serialization and loading for boundary import checker."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import ImportRef, SymbolRef
from .parser import to_relpath_str


def import_key(v: ImportRef) -> str:
    """Stable key for import violation (fence|file|line|module|reason)."""
    return f"{v.fence}|{to_relpath_str(v.file)}|{v.line}|{v.module}|{v.reason}"


def symbol_key(v: SymbolRef) -> str:
    """Stable key for symbol violation (fence|file|line|symbol|reason)."""
    return f"{v.fence}|{to_relpath_str(v.file)}|{v.line}|{v.symbol}|{v.reason}"


def serialize(import_violations: List[ImportRef], symbol_violations: List[SymbolRef]) -> dict:
    """Serialize violations to baseline format."""
    return {
        "version": 1,
        "imports": sorted({import_key(v) for v in import_violations}),
        "symbols": sorted({symbol_key(v) for v in symbol_violations}),
    }


def load_baseline(path: Path) -> dict:
    """Load baseline JSON file."""
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or obj.get("version") != 1:
        raise RuntimeError(f"Unsupported baseline format: {path}")
    obj.setdefault("imports", [])
    obj.setdefault("symbols", [])
    return obj
