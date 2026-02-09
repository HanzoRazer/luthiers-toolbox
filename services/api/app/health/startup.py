"""Startup validation for safety-critical modules.

This module ensures that safety-critical components load successfully
before the application accepts requests. If any required module fails
to import, the application will refuse to start.

Safety-Critical Modules:
- rmos.feasibility.engine: Risk assessment before G-code generation
- rmos.feasibility.rules: Safety rules that block dangerous operations
- rmos.runs_v2.store: Run artifact persistence (audit trail)
- saw_lab: Saw operation safety checks

The application will:
1. FAIL FAST if any REQUIRED module cannot be imported
2. LOG WARNINGS for OPTIONAL modules that fail
3. Report status via /api/health/modules endpoint
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_log = logging.getLogger(__name__)


@dataclass
class ModuleSpec:
    """Specification for a module to validate at startup."""

    module_path: str
    description: str
    required: bool = True
    loaded: bool = False
    error: Optional[str] = None


# =============================================================================
# SAFETY-CRITICAL MODULES (Required - server won't start without these)
# =============================================================================

SAFETY_CRITICAL_MODULES: List[ModuleSpec] = [
    ModuleSpec(
        module_path="app.rmos.feasibility.engine",
        description="Feasibility analysis engine (risk assessment)",
        required=True,
    ),
    ModuleSpec(
        module_path="app.rmos.feasibility.rules",
        description="Feasibility rules (safety constraints)",
        required=True,
    ),
    ModuleSpec(
        module_path="app.rmos.runs_v2.store",
        description="Run artifact store (audit trail)",
        required=True,
    ),
    ModuleSpec(
        module_path="app.saw_lab.batch_router",
        description="Saw Lab batch operations",
        required=True,
    ),
]

# =============================================================================
# OPTIONAL MODULES (Warnings only - server continues without these)
# =============================================================================

OPTIONAL_MODULES: List[ModuleSpec] = [
    ModuleSpec(
        module_path="app.ai.transport.image_client",
        description="AI image generation client",
        required=False,
    ),
    ModuleSpec(
        module_path="app.cam.routers",
        description="Consolidated CAM router",
        required=False,
    ),
    ModuleSpec(
        module_path="app.compare.routers",
        description="Compare router aggregator",
        required=False,
    ),
]

# Combined list for status reporting
_all_modules: List[ModuleSpec] = SAFETY_CRITICAL_MODULES + OPTIONAL_MODULES


def _try_import(spec: ModuleSpec) -> None:
    """Attempt to import a module and update its status."""
    try:
        importlib.import_module(spec.module_path)
        spec.loaded = True
        spec.error = None
        _log.info("✓ Loaded: %s (%s)", spec.module_path, spec.description)
    except ImportError as e:
        spec.loaded = False
        spec.error = str(e)
        if spec.required:
            _log.error(
                "✗ FAILED (required): %s (%s) - %s",
                spec.module_path,
                spec.description,
                e,
            )
        else:
            _log.warning(
                "⚠ Unavailable (optional): %s (%s) - %s",
                spec.module_path,
                spec.description,
                e,
            )


def validate_startup(strict: bool = True) -> None:
    """Validate that all safety-critical modules can be imported.

    Args:
        strict: If True (default), raise RuntimeError if any required
                module fails to load. If False, only log errors.

    Raises:
        RuntimeError: If strict=True and any required module fails.
    """
    _log.info("=" * 60)
    _log.info("STARTUP VALIDATION: Checking safety-critical modules...")
    _log.info("=" * 60)

    failures: List[ModuleSpec] = []

    # Check required modules first
    for spec in SAFETY_CRITICAL_MODULES:
        _try_import(spec)
        if not spec.loaded:
            failures.append(spec)

    # Then check optional modules
    for spec in OPTIONAL_MODULES:
        _try_import(spec)

    _log.info("-" * 60)

    if failures:
        failure_details = "\n".join(
            f"  - {f.module_path}: {f.error}" for f in failures
        )
        msg = (
            f"STARTUP BLOCKED: {len(failures)} safety-critical module(s) failed to load:\n"
            f"{failure_details}\n\n"
            "The server cannot start without these modules. Fix the import errors above."
        )
        _log.critical(msg)

        if strict:
            raise RuntimeError(msg)
    else:
        _log.info(
            "✓ All %d safety-critical modules loaded successfully.",
            len(SAFETY_CRITICAL_MODULES),
        )

    # Summary of optional modules
    optional_loaded = sum(1 for m in OPTIONAL_MODULES if m.loaded)
    _log.info(
        "  Optional modules: %d/%d available",
        optional_loaded,
        len(OPTIONAL_MODULES),
    )
    _log.info("=" * 60)


def get_module_status() -> Dict[str, dict]:
    """Return the status of all modules for the health endpoint.

    Returns:
        Dict mapping module paths to their status.
    """
    return {
        spec.module_path: {
            "description": spec.description,
            "required": spec.required,
            "loaded": spec.loaded,
            "error": spec.error,
        }
        for spec in _all_modules
    }


def get_startup_summary() -> dict:
    """Return a summary of startup validation for health checks.

    Returns:
        Dict with overall status and module counts.
    """
    required_loaded = sum(1 for m in SAFETY_CRITICAL_MODULES if m.loaded)
    optional_loaded = sum(1 for m in OPTIONAL_MODULES if m.loaded)

    return {
        "safety_critical": {
            "total": len(SAFETY_CRITICAL_MODULES),
            "loaded": required_loaded,
            "ok": required_loaded == len(SAFETY_CRITICAL_MODULES),
        },
        "optional": {
            "total": len(OPTIONAL_MODULES),
            "loaded": optional_loaded,
        },
        "modules": get_module_status(),
    }
