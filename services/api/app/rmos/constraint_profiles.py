# services/api/app/rmos/constraint_profiles.py
"""
Constraint Profiles for RMOS AI Generation.

This module provides:
- RosetteGeneratorConstraints dataclass
- YAML profile loading/saving
- Profile validation and lookup
- Integration with ai_policy.py for constraint clamping

Environment Variables:
    RMOS_PROFILE_YAML_PATH: Path to profiles YAML (default: config/rmos_constraint_profiles.yaml)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any

# YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None  # type: ignore
    YAML_AVAILABLE = False


# ======================
# Configuration
# ======================

DEFAULT_PROFILE_PATH = Path("config/rmos_constraint_profiles.yaml")

def get_profile_path() -> Path:
    """Get path to profiles YAML from environment or default."""
    env_path = os.environ.get("RMOS_PROFILE_YAML_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_PROFILE_PATH


# ======================
# Core Dataclass
# ======================

@dataclass
class RosetteGeneratorConstraints:
    """
    Constraints for AI rosette generation.
    
    These define the valid parameter ranges for generated designs.
    Values are clamped by ai_policy.py to system-wide limits.
    """
    # Ring constraints
    min_rings: int = 1
    max_rings: int = 8
    
    # Ring width constraints (mm)
    min_ring_width_mm: float = 0.5
    max_ring_width_mm: float = 4.0
    
    # Total rosette width constraints (mm)
    min_total_width_mm: float = 3.0
    max_total_width_mm: float = 10.0
    
    # Pattern type flags
    allow_mosaic: bool = True
    allow_segmented: bool = True
    
    # Generation hints
    palette_key: Optional[str] = None
    bias_simple: float = 0.5  # 0.0 = complex, 1.0 = simple
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RosetteGeneratorConstraints":
        """Create from dictionary, ignoring unknown fields."""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)
    
    def validate(self) -> List[str]:
        """Validate constraints, return list of errors."""
        errors = []
        
        if self.min_rings < 1:
            errors.append("min_rings must be >= 1")
        if self.max_rings < self.min_rings:
            errors.append("max_rings must be >= min_rings")
        if self.min_ring_width_mm <= 0:
            errors.append("min_ring_width_mm must be > 0")
        if self.max_ring_width_mm < self.min_ring_width_mm:
            errors.append("max_ring_width_mm must be >= min_ring_width_mm")
        if self.min_total_width_mm <= 0:
            errors.append("min_total_width_mm must be > 0")
        if self.max_total_width_mm < self.min_total_width_mm:
            errors.append("max_total_width_mm must be >= min_total_width_mm")
        if not 0.0 <= self.bias_simple <= 1.0:
            errors.append("bias_simple must be between 0.0 and 1.0")
        
        return errors


@dataclass
class ProfileMetadata:
    """Metadata for a constraint profile."""
    tags: List[str] = field(default_factory=list)
    author: str = "user"
    is_system: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    machine_profile_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfileMetadata":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


@dataclass
class ConstraintProfile:
    """Complete constraint profile with metadata."""
    profile_id: str
    name: str
    description: str
    constraints: RosetteGeneratorConstraints
    metadata: ProfileMetadata = field(default_factory=ProfileMetadata)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "constraints": self.constraints.to_dict(),
            "metadata": self.metadata.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, profile_id: str, data: Dict[str, Any]) -> "ConstraintProfile":
        constraints = RosetteGeneratorConstraints.from_dict(data.get("constraints", {}))
        metadata = ProfileMetadata.from_dict(data.get("metadata", {}))
        return cls(
            profile_id=profile_id,
            name=data.get("name", profile_id),
            description=data.get("description", ""),
            constraints=constraints,
            metadata=metadata,
        )


# ======================
# Profile Store
# ======================

class ProfileStore:
    """
    In-memory store for constraint profiles with YAML persistence.
    """
    
    def __init__(self, yaml_path: Optional[Path] = None):
        self._yaml_path = yaml_path or get_profile_path()
        self._profiles: Dict[str, ConstraintProfile] = {}
        self._version: str = "1.0"
        self._loaded = False
    
    def _ensure_loaded(self) -> None:
        """Lazy-load profiles from YAML."""
        if not self._loaded:
            self.load_from_yaml()
            self._loaded = True
    
    def load_from_yaml(self) -> bool:
        """
        Load profiles from YAML file.
        Returns True if loaded successfully.
        """
        if not YAML_AVAILABLE:
            return False
        
        if not self._yaml_path.exists():
            return False
        
        try:
            with open(self._yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data:
                return False
            
            self._version = data.get("version", "1.0")
            profiles_data = data.get("profiles", {})
            
            self._profiles = {}
            for profile_id, profile_data in profiles_data.items():
                try:
                    profile = ConstraintProfile.from_dict(profile_id, profile_data)
                    self._profiles[profile_id] = profile
                except (ValueError, TypeError, KeyError) as e:  # WP-1: narrowed from except Exception
                    continue  # Skip invalid profiles
            
            return True
        except (OSError, ValueError, TypeError, KeyError):  # WP-1: narrowed from except Exception
            return False
    
    def save_to_yaml(self) -> bool:
        """
        Save profiles to YAML file.
        Returns True if saved successfully.
        """
        if not YAML_AVAILABLE:
            return False
        
        try:
            # Ensure directory exists
            self._yaml_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": self._version,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "profiles": {
                    pid: profile.to_dict()
                    for pid, profile in self._profiles.items()
                }
            }
            
            with open(self._yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            
            return True
        except (OSError, ValueError, TypeError):  # WP-1: narrowed from except Exception
            return False
    
    def get(self, profile_id: str) -> Optional[ConstraintProfile]:
        """Get profile by ID."""
        self._ensure_loaded()
        return self._profiles.get(profile_id)
    
    def get_constraints(self, profile_id: str) -> Optional[RosetteGeneratorConstraints]:
        """Get just the constraints for a profile."""
        profile = self.get(profile_id)
        return profile.constraints if profile else None
    
    def list_all(self) -> List[ConstraintProfile]:
        """List all profiles."""
        self._ensure_loaded()
        return list(self._profiles.values())
    
    def list_ids(self) -> List[str]:
        """List all profile IDs."""
        self._ensure_loaded()
        return list(self._profiles.keys())
    
    def list_by_tag(self, tag: str) -> List[ConstraintProfile]:
        """List profiles matching a tag."""
        self._ensure_loaded()
        return [
            p for p in self._profiles.values()
            if tag in p.metadata.tags
        ]
    
    def create(self, profile: ConstraintProfile) -> bool:
        """
        Create a new profile.
        Returns False if profile_id already exists.
        """
        self._ensure_loaded()
        
        if profile.profile_id in self._profiles:
            return False
        
        # Don't allow creating system profiles
        profile.metadata.is_system = False
        profile.metadata.created_at = datetime.now(timezone.utc).isoformat()
        profile.metadata.updated_at = profile.metadata.created_at
        
        self._profiles[profile.profile_id] = profile
        return True
    
    def update(self, profile_id: str, updates: Dict[str, Any]) -> Optional[ConstraintProfile]:
        """
        Update an existing profile.
        Returns updated profile or None if not found or is system profile.
        """
        self._ensure_loaded()
        
        existing = self._profiles.get(profile_id)
        if not existing:
            return None
        
        # Don't allow editing system profiles
        if existing.metadata.is_system:
            return None
        
        # Apply updates
        if "name" in updates:
            existing.name = updates["name"]
        if "description" in updates:
            existing.description = updates["description"]
        if "constraints" in updates:
            existing.constraints = RosetteGeneratorConstraints.from_dict(updates["constraints"])
        if "metadata" in updates:
            meta_updates = updates["metadata"]
            if "tags" in meta_updates:
                existing.metadata.tags = meta_updates["tags"]
        
        existing.metadata.updated_at = datetime.now(timezone.utc).isoformat()
        
        return existing
    
    def delete(self, profile_id: str) -> bool:
        """
        Delete a profile.
        Returns False if not found or is system profile.
        """
        self._ensure_loaded()
        
        existing = self._profiles.get(profile_id)
        if not existing:
            return False
        
        # Don't allow deleting system profiles
        if existing.metadata.is_system:
            return False
        
        del self._profiles[profile_id]
        return True
    
    def exists(self, profile_id: str) -> bool:
        """Check if profile exists."""
        self._ensure_loaded()
        return profile_id in self._profiles


# ======================
# Global Instance
# ======================

_store: Optional[ProfileStore] = None

def get_profile_store() -> ProfileStore:
    """Get or create the global profile store."""
    global _store
    if _store is None:
        _store = ProfileStore()
    return _store


# ======================
# Convenience Functions
# ======================

def default_constraints() -> RosetteGeneratorConstraints:
    """Return default constraint profile."""
    return RosetteGeneratorConstraints()


def get_constraints_by_profile_id(profile_id: str) -> Optional[RosetteGeneratorConstraints]:
    """
    Get constraints for a profile ID.
    Returns None if profile not found.
    """
    store = get_profile_store()
    return store.get_constraints(profile_id)


def list_available_profiles() -> List[str]:
    """List all available profile IDs."""
    store = get_profile_store()
    return store.list_ids()


def constraints_for_beginner() -> RosetteGeneratorConstraints:
    """Beginner-friendly constraints with simpler designs."""
    store = get_profile_store()
    profile = store.get("beginner")
    if profile:
        return profile.constraints
    return RosetteGeneratorConstraints(
        min_rings=1,
        max_rings=4,
        min_ring_width_mm=1.0,
        max_ring_width_mm=3.0,
        min_total_width_mm=4.0,
        max_total_width_mm=8.0,
        allow_mosaic=False,
        allow_segmented=False,
        bias_simple=0.8,
    )


def constraints_for_advanced() -> RosetteGeneratorConstraints:
    """Advanced constraints allowing complex designs."""
    store = get_profile_store()
    profile = store.get("advanced")
    if profile:
        return profile.constraints
    return RosetteGeneratorConstraints(
        min_rings=3,
        max_rings=12,
        min_ring_width_mm=0.5,
        max_ring_width_mm=4.0,
        min_total_width_mm=5.0,
        max_total_width_mm=12.0,
        allow_mosaic=True,
        allow_segmented=True,
        bias_simple=0.2,
    )
