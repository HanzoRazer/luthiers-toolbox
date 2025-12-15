"""
Phase 28.4: Risk Bucket Detail Service
Phase 28.7: Time-window filtering support

Retrieves individual compare history entries for a specific bucket (lane + preset).
Used by dashboard to show detailed history when user clicks on an aggregated bucket.
"""

from typing import List, Dict, Optional
from . import compare_risk_log


def get_bucket_detail(
    lane: Optional[str] = None, 
    preset: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None
) -> List[Dict]:
    """
    Get all individual entries for a specific bucket (lane + preset combination).
    
    Args:
        lane: Filter by lane (e.g., "rosette", "adaptive"). If None, returns all lanes.
        preset: Filter by preset (e.g., "GRBL", "Mach4"). If None, returns all presets.
        since: ISO timestamp - only include entries >= this time (Phase 28.7)
        until: ISO timestamp - only include entries < this time (Phase 28.7)
    
    Returns:
        List of entry dicts sorted chronologically (oldest first).
        Each entry has: ts, lane, preset, job_id, added_paths, removed_paths, unchanged_paths
    
    Examples:
        >>> get_bucket_detail(lane="rosette", preset="GRBL")
        [
            {
                "ts": "2025-11-12T10:00:00",
                "lane": "rosette",
                "preset": "GRBL",
                "job_id": "rosette_job_0",
                "added_paths": 3,
                "removed_paths": 1,
                "unchanged_paths": 45
            },
            ...
        ]
    """
    data = compare_risk_log._load_log()
    entries = data.get("entries") or []
    
    # Phase 28.7: Filter by time window
    if since or until:
        time_filtered = []
        for entry in entries:
            ts = entry.get("ts", "")
            if since and ts < since:
                continue
            if until and ts >= until:
                continue
            time_filtered.append(entry)
        entries = time_filtered
    
    # Filter by lane and preset
    filtered = []
    for entry in entries:
        # Normalize preset for comparison
        entry_preset = entry.get("preset", "")
        
        # Normalize filter preset
        filter_preset = preset if preset is not None else ""
        
        # Check lane filter
        if lane is not None and entry.get("lane") != lane:
            continue
        
        # Check preset filter
        # If preset is explicitly provided (not None), filter by it
        # If preset is None, don't filter by preset (show all presets)
        if preset is not None and entry_preset != filter_preset:
            continue
        
        filtered.append(entry)
    
    # Sort chronologically (oldest first)
    filtered.sort(key=lambda e: e.get("ts", ""))
    
    return filtered
