# tap_tone/util/open_url.py
"""Best-effort URL opening in default browser.

Usage:
    from tap_tone.util import try_open_url

    if try_open_url("http://localhost:8000/library"):
        print("Opened!")
    else:
        print("Could not open browser — try manually.")
"""
from __future__ import annotations

import os
import sys
import webbrowser


def try_open_url(url: str) -> bool:
    """
    Best-effort open of a URL in the user's default browser.

    Args:
        url: The URL to open

    Returns:
        True if the open was attempted successfully, False otherwise.

    Notes:
        - Never raises exceptions
        - Returns False in headless Linux environments (no DISPLAY/WAYLAND_DISPLAY)
        - Uses webbrowser.open with new=2 (new tab if possible)
    """
    try:
        # Common CI/headless guard for Linux
        if sys.platform.startswith("linux"):
            if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
                return False

        return bool(webbrowser.open(url, new=2))
    except Exception:
        return False
