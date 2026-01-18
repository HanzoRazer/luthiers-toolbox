from __future__ import annotations

"""
Art Studio fingerprinting (delegates to shared hardened implementation).

This module provides backwards-compatible exports while delegating
to the hardened shared fingerprint implementation (Bundle 32.8.3).
"""

# Re-export from hardened shared implementation
from app.shared.fingerprint import fingerprint_stable, FINGERPRINT_ALGO
from app.shared.stablejson import stable_dumps

__all__ = [
    "fingerprint_stable",
    "FINGERPRINT_ALGO",
    "stable_dumps",
]
