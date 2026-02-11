"""Data structures for boundary import violations."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportRef:
    """Represents an import violation."""
    file: Path
    line: int
    module: str
    fence: str
    reason: str


@dataclass(frozen=True)
class SymbolRef:
    """Represents a symbol usage violation."""
    file: Path
    line: int
    symbol: str
    fence: str
    reason: str
