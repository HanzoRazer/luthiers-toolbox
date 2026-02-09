#!/usr/bin/env python3
"""WP-3: Extract module-level convenience functions from store.py -> store_api.py"""

import re

STORE_PATH = "services/api/app/rmos/runs_v2/store.py"
API_PATH = "services/api/app/rmos/runs_v2/store_api.py"

with open(STORE_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

src = "".join(lines)

# Find the marker for module-level convenience functions
marker = "# =============================================================================\n# Module-level convenience functions\n# ============================================================================="
marker_idx = src.find(marker)
if marker_idx < 0:
    print("ERROR: Could not find module-level convenience functions marker")
    exit(1)

# Find line number of marker
marker_line = src[:marker_idx].count("\n")
print(f"Module-level convenience functions start at line {marker_line + 1}")

# Everything from the marker to end of file is the module-level API
api_block = src[marker_idx:]
store_block = src[:marker_idx]

# Build the new store_api.py
api_header = '''"""RMOS Run Store v2 — module-level convenience API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import RunArtifact, AdvisoryInputRef
from .store import RunStoreV2

'''

# We need to patch the api_block:
# 1. Remove the section marker (already have it in header comment)
# 2. _default_store and _get_default_store stay
# 3. All functions stay

# Clean up section markers
api_content = api_block
# Remove the first marker
api_content = api_content.replace(marker, "", 1)

# Remove the H2 Hardening marker
h2_marker = "# =============================================================================\n# H2 Hardening: Cursor-based pagination + server-side filtering\n# ============================================================================="
api_content = api_content.replace(h2_marker, "", 1)

# Strip leading blank lines
api_content = api_content.lstrip("\n")

# Build final store_api.py
api_final = api_header + api_content

# Build the replacement ending for store.py
store_ending = """

# =============================================================================
# Module-level convenience API (re-exported for backward compatibility)
# =============================================================================
# Moved to store_api.py — re-export all public names so existing imports work.

from .store_api import (  # noqa: E402
    create_run_id,
    persist_run,
    store_artifact,
    update_run,
    get_run,
    list_runs_filtered,
    count_runs_filtered,
    rebuild_index,
    attach_advisory,
    delete_run,
    query_runs,
    query_recent,
    _get_default_store,
    _default_store,
    _norm,
    _get_nested,
    _extract_sort_key,
)
"""

# Ensure store_block ends with newline
store_block = store_block.rstrip() + "\n"
store_final = store_block + store_ending

# Write both files
with open(API_PATH, "w", encoding="utf-8") as f:
    f.write(api_final)

with open(STORE_PATH, "w", encoding="utf-8") as f:
    f.write(store_final)

# Count lines
api_lines = api_final.count("\n") + 1
store_lines = store_final.count("\n") + 1
print(f"store_api.py: {api_lines} lines (NEW)")
print(f"store.py: {store_lines} lines (was 1456)")
