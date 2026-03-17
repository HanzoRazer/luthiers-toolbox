"""Router manifest — assembles domain manifests into a single registry."""

from typing import List

from .models import RouterSpec
from .manifests.system_manifest import SYSTEM_ROUTERS
from .manifests.cam_manifest import CAM_ROUTERS
from .manifests.rmos_manifest import RMOS_ROUTERS
from .manifests.art_studio_manifest import ART_STUDIO_ROUTERS
from .manifests.business_manifest import BUSINESS_ROUTERS

# Assemble in fixed order: system, cam, rmos, art_studio, business
ROUTER_REGISTRY: List[RouterSpec] = (
    SYSTEM_ROUTERS
    + CAM_ROUTERS
    + RMOS_ROUTERS
    + ART_STUDIO_ROUTERS
    + BUSINESS_ROUTERS
)

# Keep existing import name for backward compatibility
ROUTER_MANIFEST: List[RouterSpec] = ROUTER_REGISTRY
