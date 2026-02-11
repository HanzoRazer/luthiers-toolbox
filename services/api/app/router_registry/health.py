"""Router health reporting functions."""

from typing import Any, Dict

from .manifest import ROUTER_MANIFEST
from .loader import get_loaded_routers, get_router_errors


def get_router_health() -> Dict[str, Any]:
    """Get health summary of all routers.

    Returns:
        Dict with router loading status for health endpoints.
    """
    loaded_routers = get_loaded_routers()
    router_errors = get_router_errors()

    by_category: Dict[str, Dict[str, bool]] = {}
    for spec in ROUTER_MANIFEST:
        cat = spec.category
        if cat not in by_category:
            by_category[cat] = {}
        by_category[cat][spec.module] = loaded_routers.get(spec.module, False)

    return {
        "total": len(ROUTER_MANIFEST),
        "loaded": sum(1 for v in loaded_routers.values() if v),
        "failed": sum(1 for v in loaded_routers.values() if not v),
        "by_category": {
            cat: {
                "loaded": sum(1 for v in routers.values() if v),
                "total": len(routers),
            }
            for cat, routers in by_category.items()
        },
        "errors": router_errors,
    }
