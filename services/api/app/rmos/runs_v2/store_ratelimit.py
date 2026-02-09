"""Delete rate limiting for RMOS Run Artifact Store.

H3.6.2 in-process rate limiter for delete operations.
Extracted from ``store.py`` (WP-3).
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from typing import Dict, List

# In-process rate limiter: {rate_limit_key: [timestamps]}
_DELETE_RATE_LIMIT: Dict[str, List[float]] = defaultdict(list)
_DELETE_RATE_LIMIT_LOCK = threading.Lock()

# Default: 10 deletes per minute per actor
DELETE_RATE_LIMIT_MAX = int(os.getenv("RMOS_DELETE_RATE_LIMIT_MAX", "10"))
DELETE_RATE_LIMIT_WINDOW_SEC = int(os.getenv("RMOS_DELETE_RATE_LIMIT_WINDOW", "60"))


class DeleteRateLimitError(Exception):
    """Raised when delete rate limit is exceeded."""

    def __init__(self, key: str, limit: int, window: int):
        self.key = key
        self.limit = limit
        self.window = window
        super().__init__(f"Rate limit exceeded for '{key}': max {limit} deletes per {window}s")


def check_delete_rate_limit(key: str) -> None:
    """Check if a delete operation is allowed under rate limiting.

    Raises ``DeleteRateLimitError`` if limit exceeded.
    """
    if DELETE_RATE_LIMIT_MAX <= 0:
        return  # Rate limiting disabled

    now = time.time()
    cutoff = now - DELETE_RATE_LIMIT_WINDOW_SEC

    with _DELETE_RATE_LIMIT_LOCK:
        # Prune old entries
        _DELETE_RATE_LIMIT[key] = [t for t in _DELETE_RATE_LIMIT[key] if t > cutoff]

        if len(_DELETE_RATE_LIMIT[key]) >= DELETE_RATE_LIMIT_MAX:
            raise DeleteRateLimitError(key, DELETE_RATE_LIMIT_MAX, DELETE_RATE_LIMIT_WINDOW_SEC)

        # Record this attempt
        _DELETE_RATE_LIMIT[key].append(now)
