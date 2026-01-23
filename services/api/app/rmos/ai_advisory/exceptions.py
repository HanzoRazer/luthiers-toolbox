"""
AI Integrator Exception Classes

Maps CLI exit codes to typed Python exceptions.

Exit codes (from ai-integrator CLI spec):
- 0: success
- 1: schema validation error (input or output)
- 2: governance violation
- 3: runtime error
- 4: unsupported job/template
"""

from __future__ import annotations


class AiIntegratorError(RuntimeError):
    """Base exception for ai-integrator errors."""

    exit_code: int | None = None

    def __init__(self, message: str, *, exit_code: int | None = None):
        super().__init__(message)
        self.exit_code = exit_code


class AiIntegratorSchema(AiIntegratorError):
    """Exit code 1: Schema validation error (input or output)."""

    exit_code = 1


class AiIntegratorGovernance(AiIntegratorError):
    """Exit code 2: Governance violation."""

    exit_code = 2


class AiIntegratorRuntime(AiIntegratorError):
    """Exit code 3: Runtime error (includes timeout, binary not found)."""

    exit_code = 3


class AiIntegratorUnsupported(AiIntegratorError):
    """Exit code 4: Unsupported job/template."""

    exit_code = 4


# Exit code to exception mapping
EXIT_CODE_MAP = {
    1: AiIntegratorSchema,
    2: AiIntegratorGovernance,
    3: AiIntegratorRuntime,
    4: AiIntegratorUnsupported,
}


def exception_for_exit_code(code: int, message: str) -> AiIntegratorError:
    """Create the appropriate exception for a given exit code."""
    exc_cls = EXIT_CODE_MAP.get(code, AiIntegratorRuntime)
    return exc_cls(message, exit_code=code)
