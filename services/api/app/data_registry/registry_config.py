"""
Registry configuration: Edition enum, entitlements, data tiers, and support classes.

Extracted from registry.py during WP-3 decomposition.
"""
from __future__ import annotations

import json
import os
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class Edition(Enum):
    # Core Editions (Tiered)
    EXPRESS = "express"           # $49 - Entry-level, geometry only
    PRO = "pro"                   # $299-399 - Professional CAM
    ENTERPRISE = "enterprise"     # $899-1299 - Multi-CNC, customers, inventory
    
    # Standalone Parametric Tools (Etsy/Gumroad)
    PARAMETRIC = "parametric"               # $39-59 - Guitar builder CAD
    NECK_DESIGNER = "neck_designer"         # $29-79 - Neck profile creator
    HEADSTOCK_DESIGNER = "headstock_designer"  # $14-29 - Headstock layout
    BRIDGE_DESIGNER = "bridge_designer"     # $14-19 - Bridge geometry (or free)
    FINGERBOARD_DESIGNER = "fingerboard_designer"  # $19-29 - Fretboard calculator
    
    # Industry Crossover
    CNC_BLUEPRINTS = "cnc_blueprints"       # $29-49 - Housing industry blueprint reader


class DataTier(Enum):
    SYSTEM = "system"       # Read-only, shipped with product
    EDITION = "edition"     # Read-only, product-specific
    USER = "user"           # CRUD, cloud-synced


# Product entitlements - which data categories each edition can access
EDITION_ENTITLEMENTS = {
    # =========================================================================
    # CORE EDITIONS (Tiered)
    # =========================================================================
    Edition.EXPRESS: {
        "system": ["instruments", "materials", "references"],
        "edition": [],  # Express gets no edition-specific data (honeypot strategy)
        "user": ["custom_profiles", "custom_templates", "projects"]
    },
    Edition.PRO: {
        "system": ["instruments", "materials", "references"],
        "edition": ["tools", "machines", "empirical", "cam_presets", "posts"],
        "user": ["custom_profiles", "custom_templates", "my_tools", "my_machines", "projects"]
    },
    Edition.ENTERPRISE: {
        "system": ["instruments", "materials", "references"],
        "edition": ["tools", "machines", "empirical", "cam_presets", "posts", "fleet", "scheduling"],
        "user": ["custom_profiles", "custom_templates", "my_tools", "my_machines", "projects", 
                 "customers", "orders", "inventory"]
    },
    
    # =========================================================================
    # STANDALONE PARAMETRIC TOOLS (Etsy/Gumroad - No CAM features)
    # =========================================================================
    Edition.PARAMETRIC: {
        # Full guitar CAD - needs all geometry, no CAM
        "system": ["instruments", "materials", "references"],
        "edition": ["guitar_templates", "parametric_constraints"],
        "user": ["custom_profiles", "custom_templates", "projects"]
    },
    Edition.NECK_DESIGNER: {
        # Neck profiles, taper, truss rod - subset of instruments
        "system": ["instruments", "references"],  # neck_profiles, scale_lengths
        "edition": ["neck_templates", "truss_specs"],
        "user": ["custom_profiles", "projects"]
    },
    Edition.HEADSTOCK_DESIGNER: {
        # Headstock shapes, tuner layouts
        "system": ["instruments", "references"],
        "edition": ["headstock_templates", "tuner_layouts"],
        "user": ["custom_templates", "projects"]
    },
    Edition.BRIDGE_DESIGNER: {
        # Bridge geometry, string spacing, saddle compensation
        "system": ["instruments", "references"],  # scale_lengths, compensation
        "edition": ["bridge_templates", "saddle_specs"],
        "user": ["custom_templates", "projects"]
    },
    Edition.FINGERBOARD_DESIGNER: {
        # Fret positions, radius, inlay layouts
        "system": ["instruments", "references"],  # fret_formulas, scale_lengths
        "edition": ["fretboard_templates", "inlay_patterns"],
        "user": ["custom_templates", "projects"]
    },
    
    # =========================================================================
    # INDUSTRY CROSSOVER
    # =========================================================================
    Edition.CNC_BLUEPRINTS: {
        # Housing industry blueprint reader - completely different domain
        "system": ["references"],  # Generic measurement/dimension data
        "edition": ["blueprint_standards", "dimension_tables", "construction_codes"],
        "user": ["imported_blueprints", "projects"]
    }
}


@dataclass
class SyncState:
    """Tracks local vs cloud sync status for user data"""
    last_local_update: Optional[datetime] = None
    last_cloud_sync: Optional[datetime] = None
    pending_changes: int = 0
    sync_enabled: bool = False


@dataclass
class RegistryConfig:
    """Configuration for registry initialization"""
    edition: Edition = Edition.PRO
    user_id: Optional[str] = None
    base_path: Optional[Path] = None
    user_db_path: Optional[Path] = None
    cloud_sync_enabled: bool = False
    cloud_endpoint: Optional[str] = None
    validate_on_load: bool = True


class ValidationError(Exception):
    """Raised when data fails schema validation"""
    pass


class EntitlementError(Exception):
    """Raised when accessing data outside product entitlements"""
    pass
