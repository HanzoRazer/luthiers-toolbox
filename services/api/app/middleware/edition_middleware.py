"""
Edition Middleware - Luthier's ToolBox
======================================

Provides edition-aware dependency injection for FastAPI endpoints.

Usage in routers:
    from fastapi import Depends
    from ..middleware.edition_middleware import get_edition, require_pro, EditionContext
    
    @router.get("/pro-feature")
    def pro_feature(ctx: EditionContext = Depends(require_pro)):
        # Only Pro/Enterprise users can access this endpoint
        return {"edition": ctx.edition.value}
    
    @router.get("/any-feature")
    def any_feature(ctx: EditionContext = Depends(get_edition)):
        # All editions can access, but behavior may differ
        if ctx.can_access("empirical"):
            return {"data": load_empirical_data()}
        return {"data": None, "upgrade_hint": "Pro required"}

Edition Detection Priority:
    1. X-Edition header (for testing/admin)
    2. Query param ?edition=pro (for testing)
    3. JWT token claim (future: when auth is added)
    4. Environment variable LTB_DEFAULT_EDITION
    5. Default: "pro" (development mode)
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional, List, Set
from enum import Enum

from fastapi import Header, Query, HTTPException, Request


class Edition(Enum):
    """Product editions with tiered capabilities"""
    EXPRESS = "express"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    # Standalone tools (simplified access)
    PARAMETRIC = "parametric"
    NECK_DESIGNER = "neck_designer"
    HEADSTOCK_DESIGNER = "headstock_designer"
    BRIDGE_DESIGNER = "bridge_designer"
    FINGERBOARD_DESIGNER = "fingerboard_designer"
    CNC_BLUEPRINTS = "cnc_blueprints"


# Feature categories each edition can access
EDITION_FEATURES: dict[Edition, Set[str]] = {
    Edition.EXPRESS: {
        "geometry", "scale_lengths", "fret_formulas", "wood_species", 
        "basic_templates", "dxf_export"
    },
    Edition.PRO: {
        "geometry", "scale_lengths", "fret_formulas", "wood_species",
        "basic_templates", "dxf_export",
        # Pro additions
        "empirical_limits", "tools", "machines", "cam_presets", 
        "posts", "adaptive_pocketing", "gcode_export", "simulation"
    },
    Edition.ENTERPRISE: {
        "geometry", "scale_lengths", "fret_formulas", "wood_species",
        "basic_templates", "dxf_export",
        "empirical_limits", "tools", "machines", "cam_presets",
        "posts", "adaptive_pocketing", "gcode_export", "simulation",
        # Enterprise additions
        "fleet", "scheduling", "customers", "orders", "inventory",
        "multi_machine", "production_tracking", "analytics"
    },
    # Standalone tools get specific feature subsets
    Edition.PARAMETRIC: {
        "geometry", "scale_lengths", "fret_formulas", "wood_species",
        "basic_templates", "guitar_templates", "parametric_constraints"
    },
    Edition.NECK_DESIGNER: {
        "geometry", "scale_lengths", "neck_templates", "truss_specs"
    },
    Edition.HEADSTOCK_DESIGNER: {
        "geometry", "headstock_templates", "tuner_layouts"
    },
    Edition.BRIDGE_DESIGNER: {
        "geometry", "scale_lengths", "bridge_templates", "saddle_specs"
    },
    Edition.FINGERBOARD_DESIGNER: {
        "geometry", "scale_lengths", "fret_formulas", "fretboard_templates", "inlay_patterns"
    },
    Edition.CNC_BLUEPRINTS: {
        "geometry", "blueprint_standards", "dimension_tables"
    },
}

# Minimum edition required for premium features
FEATURE_REQUIREMENTS: dict[str, Edition] = {
    "empirical_limits": Edition.PRO,
    "tools": Edition.PRO,
    "machines": Edition.PRO,
    "cam_presets": Edition.PRO,
    "posts": Edition.PRO,
    "adaptive_pocketing": Edition.PRO,
    "gcode_export": Edition.PRO,
    "simulation": Edition.PRO,
    "fleet": Edition.ENTERPRISE,
    "scheduling": Edition.ENTERPRISE,
    "customers": Edition.ENTERPRISE,
    "orders": Edition.ENTERPRISE,
    "inventory": Edition.ENTERPRISE,
    "multi_machine": Edition.ENTERPRISE,
    "production_tracking": Edition.ENTERPRISE,
    "analytics": Edition.ENTERPRISE,
}


@dataclass
class EditionContext:
    """
    Context object carrying edition information through request lifecycle.
    
    Attributes:
        edition: Current user's edition
        features: Set of feature names this edition can access
        user_id: Optional user identifier (for future auth)
        source: How edition was determined (header, query, env, default)
    """
    edition: Edition
    features: Set[str]
    user_id: Optional[str] = None
    source: str = "default"
    
    def can_access(self, feature: str) -> bool:
        """Check if current edition can access a feature"""
        return feature in self.features
    
    def require_feature(self, feature: str) -> None:
        """Raise 403 if edition cannot access feature"""
        if not self.can_access(feature):
            min_edition = FEATURE_REQUIREMENTS.get(feature, Edition.PRO)
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "edition_required",
                    "feature": feature,
                    "current_edition": self.edition.value,
                    "required_edition": min_edition.value,
                    "message": f"Feature '{feature}' requires {min_edition.value.title()} edition or higher",
                    "upgrade_url": "https://luthierstoolbox.com/upgrade"
                }
            )
    
    @property
    def is_express(self) -> bool:
        return self.edition == Edition.EXPRESS
    
    @property
    def is_pro(self) -> bool:
        return self.edition in (Edition.PRO, Edition.ENTERPRISE)
    
    @property
    def is_enterprise(self) -> bool:
        return self.edition == Edition.ENTERPRISE
    
    @property
    def is_standalone(self) -> bool:
        """Check if this is a standalone parametric tool edition"""
        return self.edition in (
            Edition.PARAMETRIC, Edition.NECK_DESIGNER, 
            Edition.HEADSTOCK_DESIGNER, Edition.BRIDGE_DESIGNER,
            Edition.FINGERBOARD_DESIGNER, Edition.CNC_BLUEPRINTS
        )


# Environment configuration
LTB_DEFAULT_EDITION = os.environ.get("LTB_DEFAULT_EDITION", "pro").lower()
LTB_EDITION_OVERRIDE = os.environ.get("LTB_EDITION_OVERRIDE", "true").lower() == "true"


def _parse_edition(value: Optional[str]) -> Optional[Edition]:
    """Parse edition string to enum, returns None if invalid"""
    if not value:
        return None
    try:
        return Edition(value.lower())
    except ValueError:
        return None


async def get_edition(
    request: Request,
    x_edition: Optional[str] = Header(None, alias="X-Edition"),
    edition_param: Optional[str] = Query(None, alias="edition"),
) -> EditionContext:
    """
    FastAPI dependency that resolves the current edition context.
    
    Priority:
        1. X-Edition header (testing/admin)
        2. ?edition= query param (testing)
        3. JWT claim (future)
        4. LTB_DEFAULT_EDITION env var
        5. Default: pro
    
    Usage:
        @router.get("/endpoint")
        def endpoint(ctx: EditionContext = Depends(get_edition)):
            if ctx.can_access("empirical_limits"):
                ...
    """
    edition: Optional[Edition] = None
    source = "default"
    
    # 1. Header override (if allowed)
    if LTB_EDITION_OVERRIDE and x_edition:
        edition = _parse_edition(x_edition)
        if edition:
            source = "header"
    
    # 2. Query param override (if allowed)
    if edition is None and LTB_EDITION_OVERRIDE and edition_param:
        edition = _parse_edition(edition_param)
        if edition:
            source = "query"
    
    # 3. Future: JWT token claim
    # if edition is None:
    #     token = request.state.get("user_token")
    #     if token and token.edition:
    #         edition = _parse_edition(token.edition)
    #         source = "jwt"
    
    # 4. Environment default
    if edition is None:
        edition = _parse_edition(LTB_DEFAULT_EDITION)
        if edition:
            source = "env"
    
    # 5. Fallback to Pro (development friendly)
    if edition is None:
        edition = Edition.PRO
        source = "default"
    
    features = EDITION_FEATURES.get(edition, set())
    
    return EditionContext(
        edition=edition,
        features=features,
        user_id=None,  # Future: from JWT
        source=source
    )


async def require_pro(ctx: EditionContext = None) -> EditionContext:
    """
    Dependency that requires Pro or higher edition.
    
    Usage:
        @router.get("/pro-only")
        def pro_endpoint(ctx: EditionContext = Depends(require_pro)):
            ...
    """
    # This is a factory - we need to get edition first
    from fastapi import Depends
    # Note: This is called as a sub-dependency by FastAPI
    if ctx is None:
        raise HTTPException(
            status_code=500,
            detail="require_pro must be used with Depends(get_edition) context"
        )
    
    if not ctx.is_pro:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "pro_required",
                "current_edition": ctx.edition.value,
                "required_edition": "pro",
                "message": "This endpoint requires Pro edition or higher",
                "upgrade_url": "https://luthierstoolbox.com/upgrade"
            }
        )
    return ctx


async def require_enterprise(ctx: EditionContext = None) -> EditionContext:
    """
    Dependency that requires Enterprise edition.
    
    Usage:
        @router.get("/enterprise-only")
        def enterprise_endpoint(ctx: EditionContext = Depends(require_enterprise)):
            ...
    """
    if ctx is None:
        raise HTTPException(
            status_code=500,
            detail="require_enterprise must be used with Depends(get_edition) context"
        )
    
    if not ctx.is_enterprise:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "enterprise_required",
                "current_edition": ctx.edition.value,
                "required_edition": "enterprise",
                "message": "This endpoint requires Enterprise edition",
                "upgrade_url": "https://luthierstoolbox.com/upgrade"
            }
        )
    return ctx


def require_feature(feature: str):
    """
    Factory for feature-specific dependencies.
    
    Usage:
        @router.get("/adaptive")
        def adaptive(ctx: EditionContext = Depends(require_feature("adaptive_pocketing"))):
            ...
    """
    async def _require(ctx: EditionContext) -> EditionContext:
        ctx.require_feature(feature)
        return ctx
    return _require


# Convenience dependencies for common checks
def get_edition_dep():
    """Get edition without any requirements"""
    return get_edition


# Export for easy importing
__all__ = [
    "Edition",
    "EditionContext", 
    "get_edition",
    "require_pro",
    "require_enterprise",
    "require_feature",
    "EDITION_FEATURES",
    "FEATURE_REQUIREMENTS",
]
