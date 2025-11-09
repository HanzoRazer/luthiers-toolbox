"""
Utility functions for safe file naming
"""
import re
from pathlib import Path


def safe_stem(filename: str) -> str:
    """
    Extract a safe stem (filename without extension) from a path or filename
    
    Args:
        filename: Full path or filename
    
    Returns:
        Sanitized filename stem without extension
    """
    # Get stem (filename without extension)
    stem = Path(filename).stem
    
    # Remove any non-alphanumeric characters except underscores and hyphens
    safe = re.sub(r'[^a-zA-Z0-9_-]', '_', stem)
    
    # Remove leading/trailing underscores
    safe = safe.strip('_')
    
    # Limit length
    if len(safe) > 50:
        safe = safe[:50]
    
    # Ensure it's not empty
    if not safe:
        safe = "file"
    
    return safe
