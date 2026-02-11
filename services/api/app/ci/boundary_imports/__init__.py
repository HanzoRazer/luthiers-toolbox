"""
Boundary Import Checker (ToolBox API) — Fence-Aware Edition
------------------------------------------------------------

Purpose:
  Enforce hard architectural boundaries defined in FENCE_REGISTRY.json.
  Implements 5 import-based fences:
    1. external_boundary     - Analyzer internals (tap_tone.*, modes.*)
    2. rmos_cam_boundary     - RMOS <-> CAM isolation
    4. ai_sandbox_boundary   - AI sandbox advisory-only
    5. saw_lab_encapsulation - Saw Lab self-containment
    7. artifact_authority    - RunArtifact construction

Usage:
  cd services/api
  python -m app.ci.boundary_imports
  python -m app.ci.boundary_imports --profile toolbox
  python -m app.ci.boundary_imports --write-baseline app/ci/fence_baseline.json
  python -m app.ci.boundary_imports --baseline app/ci/fence_baseline.json

Exit codes:
  0 = ok
  1 = ok (baseline mode, no new violations)
  2 = violations found
  3 = configuration / runtime error
"""
from __future__ import annotations

from .cli import main
from .core import check_boundaries
from .models import ImportRef, SymbolRef

__all__ = [
    "main",
    "check_boundaries",
    "ImportRef",
    "SymbolRef",
]
