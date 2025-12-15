"""Saw Lab data contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class SawLabCut:
    id: str
    name: str
    program_id: str
    status: str = "pending"
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SawLabRun:
    id: str
    created_at: datetime
    cuts: List[SawLabCut] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
