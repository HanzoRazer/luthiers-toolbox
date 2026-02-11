"""Fence configuration constants for boundary import checker."""
from __future__ import annotations

from typing import Set, Tuple

# Files to skip (generated, vendored, etc.)
SKIP_FILE_PATTERNS: Tuple[str, ...] = (
    "*/__pycache__/*",
    "*/.venv/*",
    "*/site-packages/*",
)


# --- Fence 1: external_boundary -------------------------------------------
# Cross-repository boundary: ToolBox <-> Analyzer
# DENY: tap_tone.*, modes.*

EXTERNAL_FORBIDDEN_PREFIXES: Tuple[str, ...] = (
    "tap_tone.",
    "tap_tone",
    "modes.",
    "modes",
)


# --- Fence 2: rmos_cam_boundary -------------------------------------------
# Internal domain boundary: RMOS orchestration <-> CAM execution
# Bidirectional isolation with narrow exceptions.

# CAM files MUST NOT import these RMOS modules:
CAM_FORBIDDEN_RMOS_IMPORTS: Tuple[str, ...] = (
    "app.rmos.workflow",
    "app.rmos.runs",
    "app.rmos.feasibility",
)

# RMOS files MUST NOT import these CAM modules:
RMOS_FORBIDDEN_CAM_IMPORTS: Tuple[str, ...] = (
    "app.cam.toolpath",
    "app.cam.post",
)

# Exceptions: these files may cross the boundary
RMOS_CAM_EXCEPTION_FILES: Set[str] = {
    "app/rmos/cam/schemas_intent.py",
    "app/rmos/cam/__init__.py",
}

# CAM is allowed to import CamIntentV1 from RMOS
CAM_ALLOWED_RMOS_IMPORTS: Tuple[str, ...] = (
    "app.rmos.cam.CamIntentV1",
    "app.rmos.cam",
)


# --- Fence 4: ai_sandbox_boundary -----------------------------------------
# AI sandbox isolation: advisory only, no execution authority

AI_SANDBOX_PATHS: Tuple[str, ...] = (
    "app/_experimental",
    "app/ai_sandbox",
)

AI_SANDBOX_FORBIDDEN_IMPORTS: Tuple[str, ...] = (
    "app.rmos.workflow",
    "app.rmos.runs.store",
    "app.rmos.toolpaths",
)


# --- Fence 5: saw_lab_encapsulation ---------------------------------------
# Saw Lab self-containment: reference implementation for OPERATION lane

SAW_LAB_PATHS: Tuple[str, ...] = (
    "app/saw_lab",
)

SAW_LAB_ALLOWED_IMPORTS: Tuple[str, ...] = (
    "app.saw_lab",
    "app.rmos.runs_v2",
    "app.rmos.cam.CamIntentV1",
    "app.rmos.cam",
    "app.rmos.run_artifacts",
    "app.util",
    "app.utils",
    "app.schemas",
    "app.core",
    "app.config",
    "app.settings",
    "app.logging",
    "app.telemetry",
    "app.metrics",
    "app.errors",
    "app.types",
    "app.constants",
    "app.security",
    "app.auth",
    "app.db",
    "app.data",
    "app.contracts",
    # Saw Lab services (legacy location in app.services)
    "app.services",
    "app.saw_lab_run_service",
)


# --- Fence 7: artifact_authority ------------------------------------------
# Run artifact creation restricted to authorized modules

ARTIFACT_AUTHORITY_ALLOWED_FILES: Set[str] = {
    "app/rmos/runs_v2/store.py",
    "app/rmos/runs_v2/schemas.py",
    # CAM routers that create run artifacts
    "app/cam/routers/drilling/pattern_router.py",
    "app/cam/routers/rosette/cam_router.py",
}

# Symbol that requires authority
RUNARTIFACT_SYMBOL = "RunArtifact"
