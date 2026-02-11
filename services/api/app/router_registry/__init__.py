"""Router Registry package — Centralized router loading and health tracking.

Split from router_registry.py (503 lines) into modular components:
- models.py: RouterSpec dataclass
- manifest.py: ROUTER_MANIFEST declarative list
- loader.py: Router loading functions
- health.py: Health reporting functions
"""

from .models import RouterSpec
from .manifest import ROUTER_MANIFEST
from .loader import load_all_routers, get_loaded_routers
from .health import get_router_health

__all__ = [
    "RouterSpec",
    "ROUTER_MANIFEST",
    "load_all_routers",
    "get_loaded_routers",
    "get_router_health",
]
