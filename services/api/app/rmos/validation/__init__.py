"""
RMOS v1 Validation Module

Provides:
- 30-scenario validation protocol
- Test harness for batch execution
- Persistent logging of validation results
- API endpoints for validation management
"""
from .harness import (
    load_scenarios,
    evaluate_scenario,
    run_validation,
    ValidationResult,
)
from .store import (
    ValidationRunRecord,
    ValidationSessionRecord,
    write_validation_run,
    write_validation_session,
    get_validation_run,
    get_validation_session,
    list_validation_sessions,
    list_validation_runs,
)
from .router import router

__all__ = [
    # Harness
    "load_scenarios",
    "evaluate_scenario",
    "run_validation",
    "ValidationResult",
    # Store
    "ValidationRunRecord",
    "ValidationSessionRecord",
    "write_validation_run",
    "write_validation_session",
    "get_validation_run",
    "get_validation_session",
    "list_validation_sessions",
    "list_validation_runs",
    # Router
    "router",
]
