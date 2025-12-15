"""Feeds & speeds preset placeholders."""
from __future__ import annotations

from typing import Dict, Any

DEFAULT_FEED_PRESETS: Dict[str, Dict[str, Any]] = {
    "roughing": {"chipload": 0.05, "stepping": 0.4},
    "finishing": {"chipload": 0.02, "stepping": 0.1},
}
