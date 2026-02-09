"""
Luthier's ToolBox - Hybrid Data Registry
=========================================

Three-tier data architecture for multi-product SaaS delivery.

Usage:
    from data_registry import Registry, Edition
    
    # Initialize for Pro edition
    reg = Registry(edition="pro", user_id="user_123")
    
    # System data (all editions)
    scale = reg.get_scale_length("fender_25_5")
    wood = reg.get_wood("mahogany_honduran")
    
    # Edition data (Pro/Enterprise only)
    tool = reg.get_tool("flat_6mm_2f")
    machine = reg.get_machine("bcamcnc_2030ca")
    limits = reg.get_empirical_limit("mahogany_honduran")
    
    # Combined query
    material = reg.get_material_with_limits("mahogany_honduran")
    
    # User data (CRUD)
    reg.save_custom_tool({...})
"""

from .registry_config import (
    Edition,
    DataTier,
    ValidationError,
    EntitlementError,
    EDITION_ENTITLEMENTS,
)
from .registry import (
    Registry,
    get_registry,
)

__all__ = [
    'Registry',
    'Edition',
    'DataTier', 
    'ValidationError',
    'EntitlementError',
    'get_registry',
    'EDITION_ENTITLEMENTS'
]

__version__ = "1.0.0"
