"""Learned Overrides System - 4-tuple lane-based parameter learning."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Models extracted to learned_overrides_models.py (WP-3)
from .learned_overrides_models import (
    OverrideSource as OverrideSource,
    LaneKey as LaneKey,
    ParameterOverride as ParameterOverride,
    LaneOverrides as LaneOverrides,
    AuditEntry as AuditEntry,
)


# ============================================================================
# Learned Overrides Storage
# ============================================================================

class LearnedOverridesStore:
    """Centralized learned overrides storage and management."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize learned overrides store."""
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent / "data" / "cnc_production" / "learned_overrides.json"
        
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Separate audit log
        self.audit_path = self.storage_path.parent / "learned_overrides_audit.json"
        
        # Initialize storage if not exists
        if not self.storage_path.exists():
            self._save_lanes({})
        
        if not self.audit_path.exists():
            self._save_audit([])
    
    def _make_lane_id(self, lane_key: LaneKey) -> str:
        """Generate unique lane ID from key components."""
        return f"{lane_key.tool_id}|{lane_key.material}|{lane_key.mode}|{lane_key.machine_profile}"
    
    def _load_lanes(self) -> Dict[str, Dict[str, Any]]:
        """Load lanes from JSON storage."""
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                lanes = data.get('lanes', {})
                # Handle legacy format where lanes was a list instead of dict
                if isinstance(lanes, list):
                    return {}
                return lanes
        except (OSError, json.JSONDecodeError) as e:  # WP-1: narrowed from except Exception
            print(f"Error loading learned overrides: {e}")
            return {}
    
    def _save_lanes(self, lanes: Dict[str, Dict[str, Any]]) -> None:
        """Save lanes to JSON storage."""
        data = {
            'lanes': lanes,
            'last_updated': datetime.utcnow().isoformat(),
            'lane_count': len(lanes)
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_audit(self) -> List[Dict[str, Any]]:
        """Load audit entries."""
        if not self.audit_path.exists():
            return []
        
        try:
            with open(self.audit_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('entries', [])
        except (OSError, json.JSONDecodeError):  # WP-1: narrowed from except Exception
            return []
    
    def _save_audit(self, entries: List[Dict[str, Any]]) -> None:
        """Save audit entries."""
        data = {
            'entries': entries,
            'last_updated': datetime.utcnow().isoformat(),
            'entry_count': len(entries)
        }
        
        with open(self.audit_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _add_audit_entry(self, entry: AuditEntry) -> None:
        """Add entry to audit log."""
        entries = self._load_audit()
        entries.append(entry.dict())
        self._save_audit(entries)
    
    # ------------------------------------------------------------------------
    # Lane Management
    # ------------------------------------------------------------------------
    
    def get_lane(self, lane_key: LaneKey) -> Optional[LaneOverrides]:
        """Get overrides for specific lane."""
        lanes = self._load_lanes()
        lane_id = self._make_lane_id(lane_key)
        
        if lane_id not in lanes:
            return None
        
        return LaneOverrides(**lanes[lane_id])
    
    def create_lane(self, lane_key: LaneKey) -> LaneOverrides:
        """Create new lane with default values."""
        lanes = self._load_lanes()
        lane_id = self._make_lane_id(lane_key)
        
        # Create new lane
        lane = LaneOverrides(lane_key=lane_key)
        lanes[lane_id] = lane.dict()
        self._save_lanes(lanes)
        
        return lane
    
    def get_or_create_lane(self, lane_key: LaneKey) -> LaneOverrides:
        """Get existing lane or create if doesn't exist."""
        lane = self.get_lane(lane_key)
        if lane is None:
            lane = self.create_lane(lane_key)
        return lane
    
    def list_lanes(
        self,
        tool_id: Optional[str] = None,
        material: Optional[str] = None,
        mode: Optional[str] = None,
        machine_profile: Optional[str] = None
    ) -> List[LaneOverrides]:
        """List lanes matching filters."""
        lanes = self._load_lanes()
        results = []
        
        for lane_data in lanes.values():
            lane = LaneOverrides(**lane_data)
            
            # Apply filters
            if tool_id and lane.lane_key.tool_id != tool_id:
                continue
            if material and lane.lane_key.material != material:
                continue
            if mode and lane.lane_key.mode != mode:
                continue
            if machine_profile and lane.lane_key.machine_profile != machine_profile:
                continue
            
            results.append(lane)
        
        return results
    
    # ------------------------------------------------------------------------
    # Override Management
    # ------------------------------------------------------------------------
    
    def set_override(
        self,
        lane_key: LaneKey,
        param_name: str,
        value: float,
        source: OverrideSource,
        scale: Optional[float] = None,
        confidence: float = 1.0,
        operator: Optional[str] = None,
        notes: Optional[str] = None,
        reason: Optional[str] = None
    ) -> ParameterOverride:
        """Set parameter override for lane."""
        lanes = self._load_lanes()
        lane_id = self._make_lane_id(lane_key)
        
        # Get or create lane
        if lane_id not in lanes:
            lane = self.create_lane(lane_key)
            lanes = self._load_lanes()
        else:
            lane = LaneOverrides(**lanes[lane_id])
        
        # Get previous override if exists
        prev_override = lane.overrides.get(param_name)
        prev_value = prev_override.value if prev_override else None
        prev_scale = prev_override.scale if prev_override else None
        
        # Create new override
        override = ParameterOverride(
            param_name=param_name,
            value=value,
            scale=scale if scale is not None else 1.0,
            source=source,
            confidence=confidence,
            operator=operator,
            notes=notes
        )
        
        # Update lane
        lane.overrides[param_name] = override
        lane.updated_at = datetime.utcnow().isoformat()
        
        lanes[lane_id] = lane.dict()
        self._save_lanes(lanes)
        
        # Add audit entry
        audit_entry = AuditEntry(
            lane_key=lane_key,
            param_name=param_name,
            source=source,
            prev_value=prev_value,
            new_value=value,
            prev_scale=prev_scale,
            new_scale=override.scale,
            operator=operator,
            reason=reason
        )
        self._add_audit_entry(audit_entry)
        
        return override
    
    def update_lane_scale(
        self,
        lane_key: LaneKey,
        lane_scale: float,
        source: OverrideSource = OverrideSource.AUTO_LEARN,
        operator: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """Update overall lane scale factor."""
        lanes = self._load_lanes()
        lane_id = self._make_lane_id(lane_key)
        
        lane = self.get_or_create_lane(lane_key)
        prev_scale = lane.lane_scale
        
        lane.lane_scale = lane_scale
        lane.updated_at = datetime.utcnow().isoformat()
        
        lanes[lane_id] = lane.dict()
        self._save_lanes(lanes)
        
        # Add audit entry
        audit_entry = AuditEntry(
            lane_key=lane_key,
            param_name="lane_scale",
            source=source,
            prev_value=prev_scale,
            new_value=lane_scale,
            prev_scale=prev_scale,
            new_scale=lane_scale,
            operator=operator,
            reason=reason
        )
        self._add_audit_entry(audit_entry)
    
    def record_run(
        self,
        lane_key: LaneKey,
        success: bool = True
    ) -> None:
        """Record successful run for lane."""
        lanes = self._load_lanes()
        lane_id = self._make_lane_id(lane_key)
        
        lane = self.get_or_create_lane(lane_key)
        
        # Update run stats
        lane.run_count += 1
        if success:
            # Exponential moving average
            alpha = 0.1
            lane.success_rate = (1 - alpha) * lane.success_rate + alpha * 1.0
        else:
            alpha = 0.1
            lane.success_rate = (1 - alpha) * lane.success_rate + alpha * 0.0
        
        lane.last_run = datetime.utcnow().isoformat()
        lane.updated_at = datetime.utcnow().isoformat()
        
        lanes[lane_id] = lane.dict()
        self._save_lanes(lanes)
    
    # ------------------------------------------------------------------------
    # Merge Logic
    # ------------------------------------------------------------------------
    
    def merge_parameters(
        self,
        baseline: Dict[str, float],
        lane_key: LaneKey
    ) -> Dict[str, float]:
        """Merge baseline with learned overrides and lane scale."""
        lane = self.get_lane(lane_key)
        if lane is None:
            # No overrides, return baseline
            return baseline.copy()
        
        merged = baseline.copy()
        
        # Apply individual parameter overrides
        for param_name, override in lane.overrides.items():
            if param_name in merged:
                # Apply override (could be additive or multiplicative based on scale)
                if override.scale != 1.0:
                    # Scale-based: baseline * scale
                    merged[param_name] = baseline[param_name] * override.scale
                else:
                    # Value-based: use override value directly
                    merged[param_name] = override.value
        
        # Apply overall lane scale to all parameters
        if lane.lane_scale != 1.0:
            for param_name in merged:
                merged[param_name] *= lane.lane_scale
        
        return merged
    
    def get_effective_value(
        self,
        param_name: str,
        baseline_value: float,
        lane_key: LaneKey
    ) -> Tuple[float, Dict[str, Any]]:
        """Get effective parameter value with metadata."""
        lane = self.get_lane(lane_key)
        
        if lane is None:
            return baseline_value, {
                'source': 'baseline',
                'has_override': False,
                'lane_scale': 1.0
            }
        
        # Check for override
        override = lane.overrides.get(param_name)
        
        if override:
            # Apply override
            if override.scale != 1.0:
                value = baseline_value * override.scale
            else:
                value = override.value
            
            # Apply lane scale
            value *= lane.lane_scale
            
            return value, {
                'source': override.source,
                'has_override': True,
                'override_value': override.value,
                'override_scale': override.scale,
                'lane_scale': lane.lane_scale,
                'confidence': override.confidence,
                'timestamp': override.timestamp
            }
        else:
            # Just apply lane scale
            value = baseline_value * lane.lane_scale
            
            return value, {
                'source': 'baseline',
                'has_override': False,
                'lane_scale': lane.lane_scale
            }
    
    # ------------------------------------------------------------------------
    # Audit & Statistics
    # ------------------------------------------------------------------------
    
    def get_audit_trail(
        self,
        lane_key: Optional[LaneKey] = None,
        param_name: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Get audit trail entries."""
        entries = self._load_audit()
        results = []
        
        for entry_data in reversed(entries):
            entry = AuditEntry(**entry_data)
            
            # Apply filters
            if lane_key:
                if (entry.lane_key.tool_id != lane_key.tool_id or
                    entry.lane_key.material != lane_key.material or
                    entry.lane_key.mode != lane_key.mode or
                    entry.lane_key.machine_profile != lane_key.machine_profile):
                    continue
            
            if param_name and entry.param_name != param_name:
                continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics."""
        lanes = self._load_lanes()
        audit = self._load_audit()
        
        # Count by source
        sources = {}
        for lane_data in lanes.values():
            lane = LaneOverrides(**lane_data)
            for override in lane.overrides.values():
                sources[override.source] = sources.get(override.source, 0) + 1
        
        # Count by machine
        machines = {}
        for lane_data in lanes.values():
            lane = LaneOverrides(**lane_data)
            machine = lane.lane_key.machine_profile
            machines[machine] = machines.get(machine, 0) + 1
        
        return {
            'total_lanes': len(lanes),
            'total_audit_entries': len(audit),
            'overrides_by_source': sources,
            'lanes_by_machine': machines,
            'last_updated': datetime.utcnow().isoformat()
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_store_instance = None

def get_learned_overrides_store() -> LearnedOverridesStore:
    """Get singleton store instance."""
    global _store_instance
    if _store_instance is None:
        _store_instance = LearnedOverridesStore()
    return _store_instance
