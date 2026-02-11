"""Router registry models."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class RouterSpec:
    """Specification for a router to load."""

    module: str  # Full module path, e.g., "app.routers.health_router"
    router_attr: str = "router"  # Attribute name in module
    prefix: str = ""  # URL prefix
    tags: List[str] = field(default_factory=list)
    required: bool = False  # If True, failure blocks startup
    enabled: bool = True  # If False, skip loading
    category: str = "misc"  # For grouping in health reports
