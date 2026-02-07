# services/api/app/rmos/profile_history.py
"""
Profile History Journal for RMOS Constraint Profiles.

This module provides:
- JSONL-based change tracking for constraint profiles
- Audit trail of profile modifications
- Rollback capabilities

Environment Variables:
    RMOS_PROFILE_HISTORY_PATH: Path to history JSONL (default: config/rmos_profile_history.jsonl)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
import uuid


# ======================
# Configuration
# ======================

DEFAULT_HISTORY_PATH = Path("config/rmos_profile_history.jsonl")

def get_history_path() -> Path:
    """Get path to history JSONL from environment or default."""
    env_path = os.environ.get("RMOS_PROFILE_HISTORY_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_HISTORY_PATH


# ======================
# Change Types
# ======================

class ChangeType(str, Enum):
    """Types of profile changes."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ROLLBACK = "rollback"


# ======================
# History Entry
# ======================

@dataclass
class ProfileHistoryEntry:
    """A single entry in the profile history journal."""
    entry_id: str
    timestamp: str
    change_type: ChangeType
    profile_id: str
    user_id: Optional[str]
    
    # For CREATE/UPDATE: the new state
    new_state: Optional[Dict[str, Any]] = None
    
    # For UPDATE/DELETE/ROLLBACK: the previous state
    previous_state: Optional[Dict[str, Any]] = None
    
    # Optional description of the change
    description: Optional[str] = None
    
    # For ROLLBACK: reference to the entry being rolled back to
    rollback_target_entry_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "change_type": self.change_type.value if isinstance(self.change_type, ChangeType) else self.change_type,
            "profile_id": self.profile_id,
            "user_id": self.user_id,
            "new_state": self.new_state,
            "previous_state": self.previous_state,
            "description": self.description,
            "rollback_target_entry_id": self.rollback_target_entry_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProfileHistoryEntry":
        change_type = data.get("change_type", "update")
        if isinstance(change_type, str):
            try:
                change_type = ChangeType(change_type)
            except ValueError:
                change_type = ChangeType.UPDATE
        
        return cls(
            entry_id=data.get("entry_id", ""),
            timestamp=data.get("timestamp", ""),
            change_type=change_type,
            profile_id=data.get("profile_id", ""),
            user_id=data.get("user_id"),
            new_state=data.get("new_state"),
            previous_state=data.get("previous_state"),
            description=data.get("description"),
            rollback_target_entry_id=data.get("rollback_target_entry_id"),
        )
    
    def to_json_line(self) -> str:
        """Convert to JSON line for JSONL file."""
        return json.dumps(self.to_dict(), default=str)


# ======================
# History Store
# ======================

class ProfileHistoryStore:
    """
    JSONL-based history store for profile changes.
    
    Each line in the JSONL file is a ProfileHistoryEntry.
    New entries are appended to the end of the file.
    """
    
    def __init__(self, jsonl_path: Optional[Path] = None):
        self._jsonl_path = jsonl_path or get_history_path()
    
    def _ensure_file(self) -> None:
        """Ensure the history file exists."""
        self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._jsonl_path.exists():
            self._jsonl_path.touch()
    
    def _generate_entry_id(self) -> str:
        """Generate a unique entry ID."""
        return str(uuid.uuid4())[:12]
    
    def append(self, entry: ProfileHistoryEntry) -> bool:
        """
        Append an entry to the history journal.
        Returns True if successful.
        """
        try:
            self._ensure_file()
            with open(self._jsonl_path, "a", encoding="utf-8") as f:
                f.write(entry.to_json_line() + "\n")
            return True
        except OSError:  # WP-1: narrowed from except Exception
            return False
    
    def record_create(
        self,
        profile_id: str,
        new_state: Dict[str, Any],
        user_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[ProfileHistoryEntry]:
        """Record a profile creation."""
        entry = ProfileHistoryEntry(
            entry_id=self._generate_entry_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            change_type=ChangeType.CREATE,
            profile_id=profile_id,
            user_id=user_id,
            new_state=new_state,
            previous_state=None,
            description=description or f"Created profile '{profile_id}'",
        )
        
        if self.append(entry):
            return entry
        return None
    
    def record_update(
        self,
        profile_id: str,
        new_state: Dict[str, Any],
        previous_state: Dict[str, Any],
        user_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[ProfileHistoryEntry]:
        """Record a profile update."""
        entry = ProfileHistoryEntry(
            entry_id=self._generate_entry_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            change_type=ChangeType.UPDATE,
            profile_id=profile_id,
            user_id=user_id,
            new_state=new_state,
            previous_state=previous_state,
            description=description or f"Updated profile '{profile_id}'",
        )
        
        if self.append(entry):
            return entry
        return None
    
    def record_delete(
        self,
        profile_id: str,
        previous_state: Dict[str, Any],
        user_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[ProfileHistoryEntry]:
        """Record a profile deletion."""
        entry = ProfileHistoryEntry(
            entry_id=self._generate_entry_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            change_type=ChangeType.DELETE,
            profile_id=profile_id,
            user_id=user_id,
            new_state=None,
            previous_state=previous_state,
            description=description or f"Deleted profile '{profile_id}'",
        )
        
        if self.append(entry):
            return entry
        return None
    
    def record_rollback(
        self,
        profile_id: str,
        new_state: Dict[str, Any],
        previous_state: Dict[str, Any],
        target_entry_id: str,
        user_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[ProfileHistoryEntry]:
        """Record a rollback to a previous state."""
        entry = ProfileHistoryEntry(
            entry_id=self._generate_entry_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            change_type=ChangeType.ROLLBACK,
            profile_id=profile_id,
            user_id=user_id,
            new_state=new_state,
            previous_state=previous_state,
            description=description or f"Rolled back profile '{profile_id}' to entry {target_entry_id}",
            rollback_target_entry_id=target_entry_id,
        )
        
        if self.append(entry):
            return entry
        return None
    
    def get_history_for_profile(
        self,
        profile_id: str,
        limit: int = 50,
    ) -> List[ProfileHistoryEntry]:
        """
        Get history entries for a specific profile.
        Returns most recent entries first.
        """
        entries = []
        
        try:
            if not self._jsonl_path.exists():
                return entries
            
            with open(self._jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("profile_id") == profile_id:
                            entries.append(ProfileHistoryEntry.from_dict(data))
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent first, limited
            entries.reverse()
            return entries[:limit]
        except OSError:  # WP-1: narrowed from except Exception
            return entries
    
    def get_all_history(
        self,
        limit: int = 100,
        change_type: Optional[ChangeType] = None,
    ) -> List[ProfileHistoryEntry]:
        """
        Get all history entries.
        Returns most recent entries first.
        """
        entries = []
        
        try:
            if not self._jsonl_path.exists():
                return entries
            
            with open(self._jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = ProfileHistoryEntry.from_dict(data)
                        
                        # Filter by change type if specified
                        if change_type and entry.change_type != change_type:
                            continue
                        
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent first, limited
            entries.reverse()
            return entries[:limit]
        except OSError:  # WP-1: narrowed from except Exception
            return entries
    
    def get_entry_by_id(self, entry_id: str) -> Optional[ProfileHistoryEntry]:
        """Get a specific history entry by ID."""
        try:
            if not self._jsonl_path.exists():
                return None
            
            with open(self._jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("entry_id") == entry_id:
                            return ProfileHistoryEntry.from_dict(data)
                    except json.JSONDecodeError:
                        continue
            
            return None
        except OSError:  # WP-1: narrowed from except Exception
            return None
    
    def get_state_at_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the profile state as it was after a specific entry.
        Returns the new_state for CREATE/UPDATE/ROLLBACK, None for DELETE.
        """
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            return None
        
        if entry.change_type == ChangeType.DELETE:
            return None
        
        return entry.new_state


# ======================
# Global Instance
# ======================

_history_store: Optional[ProfileHistoryStore] = None

def get_profile_history_store() -> ProfileHistoryStore:
    """Get or create the global profile history store."""
    global _history_store
    if _history_store is None:
        _history_store = ProfileHistoryStore()
    return _history_store


# ======================
# Convenience Functions
# ======================

def record_profile_change(
    change_type: ChangeType,
    profile_id: str,
    new_state: Optional[Dict[str, Any]] = None,
    previous_state: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[ProfileHistoryEntry]:
    """
    Record a profile change to the history journal.
    Convenience function that routes to the appropriate record method.
    """
    store = get_profile_history_store()
    
    if change_type == ChangeType.CREATE:
        return store.record_create(
            profile_id=profile_id,
            new_state=new_state or {},
            user_id=user_id,
            description=description,
        )
    elif change_type == ChangeType.UPDATE:
        return store.record_update(
            profile_id=profile_id,
            new_state=new_state or {},
            previous_state=previous_state or {},
            user_id=user_id,
            description=description,
        )
    elif change_type == ChangeType.DELETE:
        return store.record_delete(
            profile_id=profile_id,
            previous_state=previous_state or {},
            user_id=user_id,
            description=description,
        )
    
    return None


def get_profile_history(profile_id: str, limit: int = 50) -> List[ProfileHistoryEntry]:
    """Get history for a specific profile."""
    store = get_profile_history_store()
    return store.get_history_for_profile(profile_id, limit)
