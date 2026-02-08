"""Luthier's ToolBox - Hybrid Data Registry"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import hashlib

# WP-3: Configuration, enums, and entitlements extracted to registry_config.py
from .registry_config import (
    Edition as Edition,
    DataTier as DataTier,
    EDITION_ENTITLEMENTS as EDITION_ENTITLEMENTS,
    SyncState as SyncState,
    RegistryConfig as RegistryConfig,
    ValidationError as ValidationError,
    EntitlementError as EntitlementError,
)

# WP-3: Standalone product data accessors extracted to registry_products.py
from .registry_products import RegistryProductsMixin


class Registry(RegistryProductsMixin):
    """Hybrid data registry with three-tier architecture."""
    
    def __init__(self, 
                 edition: Union[str, Edition] = "pro",
                 user_id: Optional[str] = None,
                 base_path: Optional[str] = None,
                 validate: bool = True):
        """Initialize the registry."""
        if isinstance(edition, str):
            edition = Edition(edition.lower())
        
        self.edition = edition
        self.user_id = user_id
        self.validate = validate
        
        # Resolve base path
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(__file__).parent
        
        # Initialize caches
        self._cache: Dict[str, Any] = {}
        self._schemas: Dict[str, dict] = {}
        
        # User data SQLite connection (lazy init)
        self._user_db: Optional[sqlite3.Connection] = None
        self._sync_state = SyncState()
        
        # Load schemas
        self._load_schemas()
    
    # =========================================================================
    # SYSTEM DATA (Read-only, universal)
    # =========================================================================
    
    def get_scale_lengths(self) -> Dict[str, Any]:
        """Get all standard scale lengths (Fender, Gibson, etc.)"""
        return self._load_system_data("references/scale_lengths.json")
    
    def get_scale_length(self, scale_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific scale length by ID"""
        scales = self.get_scale_lengths()
        return scales.get("scales", {}).get(scale_id)
    
    def get_fret_formulas(self) -> Dict[str, Any]:
        """Get fret calculation formulas (12-TET, temperaments)"""
        return self._load_system_data("references/fret_formulas.json")
    
    def get_neck_profiles(self) -> Dict[str, Any]:
        """Get standard neck profiles (C, D, V, asymmetric)"""
        return self._load_system_data("instruments/neck_profiles.json")
    
    def get_body_templates(self) -> Dict[str, Any]:
        """Get standard body templates (Strat, LP, J45, etc.)"""
        return self._load_system_data("instruments/body_templates.json")
    
    def get_body_template(self, body_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific body template by ID"""
        templates = self.get_body_templates()
        return templates.get("bodies", {}).get(body_id)
    
    def get_wood_species(self) -> Dict[str, Any]:
        """Get wood species reference data (no empirical limits)"""
        return self._load_system_data("materials/wood_species.json")
    
    def get_wood(self, species_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific wood species by ID"""
        species = self.get_wood_species()
        return species.get("species", {}).get(species_id)
    
    # =========================================================================
    # EDITION DATA (Read-only, product-specific)
    # =========================================================================
    
    def get_tools(self) -> Dict[str, Any]:
        """Get tool library (Pro/Enterprise only)"""
        self._check_entitlement("edition", "tools")
        return self._load_edition_data("tools/router_bits.json")
    
    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool by ID, checking user overrides first"""
        # Check user tools first
        if self.user_id:
            user_tool = self._get_user_tool(tool_id)
            if user_tool:
                return user_tool
        
        # Fall back to edition tools
        tools = self.get_tools()
        return tools.get("tools", {}).get(tool_id)
    
    def get_machines(self) -> Dict[str, Any]:
        """Get machine profiles (Pro/Enterprise only)"""
        self._check_entitlement("edition", "machines")
        return self._load_edition_data("machines/profiles.json")
    
    def get_machine(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific machine profile by ID"""
        # Check user machines first
        if self.user_id:
            user_machine = self._get_user_machine(machine_id)
            if user_machine:
                return user_machine
        
        machines = self.get_machines()
        return machines.get("machines", {}).get(machine_id)
    
    def get_empirical_limits(self) -> Dict[str, Any]:
        """Get empirical feed/speed limits per wood species (Pro/Enterprise)"""
        self._check_entitlement("edition", "empirical")
        return self._load_edition_data("empirical/wood_limits.json")
    
    def get_empirical_limit(self, species_id: str) -> Optional[Dict[str, Any]]:
        """Get empirical limits for a specific wood species"""
        limits = self.get_empirical_limits()
        return limits.get("limits", {}).get(species_id)
    
    def get_cam_presets(self) -> Dict[str, Any]:
        """Get CAM operation presets (Pro/Enterprise only)"""
        self._check_entitlement("edition", "cam_presets")
        return self._load_edition_data("cam_presets/presets.json")
    
    def get_post_processors(self) -> Dict[str, Any]:
        """Get G-code post processor configs (Pro/Enterprise only)"""
        self._check_entitlement("edition", "posts")
        return self._load_edition_data("posts/processors.json")
    
    # WP-3: Standalone product accessors (ltb-parametric, ltb-neck-designer,
    # ltb-headstock-designer, ltb-bridge-designer, ltb-fingerboard-designer,
    # ltb-cnc-blueprints) extracted to RegistryProductsMixin via registry_products.py

    # =========================================================================
    # COMBINED QUERIES (Merges tiers with precedence)
    # =========================================================================
    
    def get_material_with_limits(self, species_id: str) -> Optional[Dict[str, Any]]:
        """Get wood species data combined with empirical limits."""
        wood = self.get_wood(species_id)
        if not wood:
            return None
        
        result = dict(wood)
        
        # Add empirical limits if entitled
        try:
            limits = self.get_empirical_limit(species_id)
            if limits:
                result["empirical"] = limits
        except EntitlementError:
            # Express edition - no limits available
            pass
        
        return result
    
    def get_tool_for_operation(self, 
                               operation: str, 
                               material: str,
                               preferred_diameter: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Find best tool for an operation considering material and diameter."""
        tools = self.get_tools()
        candidates = []
        
        for tool_id, tool in tools.get("tools", {}).items():
            if operation in tool.get("suitable_for", []):
                score = 0
                
                # Prefer tools rated for this material hardness
                material_data = self.get_wood(material)
                if material_data:
                    tool_hardness = tool.get("max_hardness", 2000)
                    material_janka = material_data.get("janka_hardness", 1000)
                    if tool_hardness >= material_janka:
                        score += 10
                
                # Prefer matching diameter
                if preferred_diameter:
                    tool_dia = tool.get("diameter_mm", 0)
                    if abs(tool_dia - preferred_diameter) < 0.5:
                        score += 5
                
                candidates.append((score, tool_id, tool))
        
        if candidates:
            candidates.sort(key=lambda x: -x[0])
            return candidates[0][2]
        
        return None
    
    # =========================================================================
    # USER DATA (CRUD, cloud-synced)
    # =========================================================================
    
    def save_custom_tool(self, tool: Dict[str, Any]) -> str:
        """Save a user-defined tool to local DB"""
        self._check_entitlement("user", "my_tools")
        return self._save_user_data("my_tools", tool)
    
    def save_custom_machine(self, machine: Dict[str, Any]) -> str:
        """Save a user-defined machine profile to local DB"""
        self._check_entitlement("user", "my_machines")
        return self._save_user_data("my_machines", machine)
    
    def save_custom_profile(self, profile: Dict[str, Any]) -> str:
        """Save a user-defined neck/body profile to local DB"""
        self._check_entitlement("user", "custom_profiles")
        return self._save_user_data("custom_profiles", profile)
    
    def save_project(self, project: Dict[str, Any]) -> str:
        """Save a project to local DB"""
        self._check_entitlement("user", "projects")
        return self._save_user_data("projects", project)
    
    def get_user_tools(self) -> List[Dict[str, Any]]:
        """Get all user-defined tools"""
        self._check_entitlement("user", "my_tools")
        return self._get_user_data("my_tools")
    
    def get_user_machines(self) -> List[Dict[str, Any]]:
        """Get all user-defined machine profiles"""
        self._check_entitlement("user", "my_machines")
        return self._get_user_data("my_machines")
    
    def get_user_profiles(self) -> List[Dict[str, Any]]:
        """Get all user-defined profiles"""
        self._check_entitlement("user", "custom_profiles")
        return self._get_user_data("custom_profiles")
    
    def get_user_projects(self) -> List[Dict[str, Any]]:
        """Get all user projects"""
        self._check_entitlement("user", "projects")
        return self._get_user_data("projects")
    
    # =========================================================================
    # SYNC (Local SQLite ↔ Cloud PostgreSQL)
    # =========================================================================
    
    def enable_cloud_sync(self, endpoint: str, auth_token: str):
        """Enable cloud synchronization for user data"""
        self._sync_state.sync_enabled = True
        # Implementation would connect to cloud endpoint
        # For now, just mark as enabled
    
    def sync_to_cloud(self) -> bool:
        """Push pending local changes to cloud"""
        if not self._sync_state.sync_enabled:
            return False
        
        # Implementation would:
        # 1. Get changes since last sync
        # 2. POST to cloud endpoint
        # 3. Update sync state
        self._sync_state.last_cloud_sync = datetime.now()
        self._sync_state.pending_changes = 0
        return True
    
    def sync_from_cloud(self) -> bool:
        """Pull changes from cloud to local"""
        if not self._sync_state.sync_enabled:
            return False
        
        # Implementation would:
        # 1. GET from cloud endpoint
        # 2. Merge with local data (conflict resolution)
        # 3. Update sync state
        return True
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            "enabled": self._sync_state.sync_enabled,
            "last_local_update": self._sync_state.last_local_update,
            "last_cloud_sync": self._sync_state.last_cloud_sync,
            "pending_changes": self._sync_state.pending_changes
        }
    
    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================
    
    def _load_schemas(self):
        """Load JSON schemas for validation"""
        schema_path = self.base_path / "schemas"
        if schema_path.exists():
            for schema_file in schema_path.glob("*.json"):
                with open(schema_file, encoding="utf-8") as f:
                    self._schemas[schema_file.stem] = json.load(f)
    
    def _load_system_data(self, relative_path: str) -> Dict[str, Any]:
        """Load data from system tier (universal, read-only)"""
        cache_key = f"system:{relative_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        file_path = self.base_path / "system" / relative_path
        data = self._load_json(file_path)
        
        if self.validate:
            self._validate_data(relative_path, data)
        
        self._cache[cache_key] = data
        return data
    
    def _load_edition_data(self, relative_path: str) -> Dict[str, Any]:
        """Load data from edition tier (product-specific, read-only)"""
        cache_key = f"edition:{self.edition.value}:{relative_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try edition-specific first, fall back to pro (which enterprise inherits)
        edition_path = self.base_path / "edition" / self.edition.value / relative_path
        if not edition_path.exists() and self.edition == Edition.ENTERPRISE:
            edition_path = self.base_path / "edition" / "pro" / relative_path
        
        data = self._load_json(edition_path)
        
        if self.validate:
            self._validate_data(relative_path, data)
        
        self._cache[cache_key] = data
        return data
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a JSON file"""
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in {file_path}: {e}")
    
    def _validate_data(self, path: str, data: Dict[str, Any]):
        """Validate data against its schema"""
        # Extract schema name from path (e.g., "tools/router_bits.json" -> "tools")
        schema_name = path.split("/")[0]
        
        if schema_name in self._schemas:
            schema = self._schemas[schema_name]
            # Basic validation - check required fields
            for required in schema.get("required", []):
                if required not in data:
                    raise ValidationError(f"Missing required field '{required}' in {path}")
    
    def _check_entitlement(self, tier: str, category: str):
        """Check if current edition is entitled to access this data"""
        entitlements = EDITION_ENTITLEMENTS.get(self.edition, {})
        allowed = entitlements.get(tier, [])
        
        if category not in allowed:
            raise EntitlementError(
                f"Edition '{self.edition.value}' is not entitled to access '{category}' "
                f"in tier '{tier}'. Upgrade to Pro or Enterprise for this feature."
            )
    
    def _get_user_db(self) -> sqlite3.Connection:
        """Get or create user data SQLite connection"""
        if self._user_db is None:
            if not self.user_id:
                raise ValueError("User ID required for user data operations")
            
            db_path = self.base_path / "user" / f"{self.user_id}.sqlite"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self._user_db = sqlite3.connect(str(db_path))
            self._init_user_db()
        
        return self._user_db
    
    def _init_user_db(self):
        """Initialize user database schema"""
        db = self._user_db
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_at TIMESTAMP
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_category ON user_data(category)")
        db.commit()
    
    def _save_user_data(self, category: str, data: Dict[str, Any]) -> str:
        """Save data to user tier"""
        db = self._get_user_db()
        
        # Generate ID if not present
        data_id = data.get("id") or self._generate_id(data)
        data["id"] = data_id
        
        db.execute("""
            INSERT OR REPLACE INTO user_data (id, category, data, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (data_id, category, json.dumps(data)))
        db.commit()
        
        self._sync_state.last_local_update = datetime.now()
        self._sync_state.pending_changes += 1
        
        return data_id
    
    def _get_user_data(self, category: str) -> List[Dict[str, Any]]:
        """Get all data for a category from user tier"""
        db = self._get_user_db()
        cursor = db.execute(
            "SELECT data FROM user_data WHERE category = ?",
            (category,)
        )
        return [json.loads(row[0]) for row in cursor.fetchall()]
    
    def _get_user_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific user tool by ID"""
        db = self._get_user_db()
        cursor = db.execute(
            "SELECT data FROM user_data WHERE category = 'my_tools' AND id = ?",
            (tool_id,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
    
    def _get_user_machine(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific user machine by ID"""
        db = self._get_user_db()
        cursor = db.execute(
            "SELECT data FROM user_data WHERE category = 'my_machines' AND id = ?",
            (machine_id,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
    
    def _generate_id(self, data: Dict[str, Any]) -> str:
        """Generate a unique ID for data"""
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def clear_cache(self):
        """Clear the data cache"""
        self._cache.clear()
    
    def close(self):
        """Close database connections"""
        if self._user_db:
            self._user_db.close()
            self._user_db = None


# Convenience function for quick access
def get_registry(edition: str = "pro", user_id: Optional[str] = None) -> Registry:
    """Get a registry instance"""
    return Registry(edition=edition, user_id=user_id)
