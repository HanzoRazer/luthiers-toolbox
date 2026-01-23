"""
AI Integrator Configuration

Environment variables for CLI invocation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AiIntegratorConfig:
    """Configuration for ai-integrator CLI invocation."""

    # Path to ai-integrator binary (default: assumes installed in PATH)
    bin_path: str = "ai-integrator"

    # Timeout for CLI invocation in seconds
    timeout_sec: int = 60

    # Working directory for temp files
    workdir: Path = Path("/tmp/rmos-ai")

    # Maximum concurrent jobs (for future rate limiting)
    max_concurrent_jobs: int = 2

    @classmethod
    def from_env(cls) -> "AiIntegratorConfig":
        """Load configuration from environment variables."""
        return cls(
            bin_path=os.getenv("AI_INTEGRATOR_BIN", "ai-integrator"),
            timeout_sec=int(os.getenv("AI_INTEGRATOR_TIMEOUT_SEC", "60")),
            workdir=Path(os.getenv("AI_INTEGRATOR_WORKDIR", "/tmp/rmos-ai")),
            max_concurrent_jobs=int(os.getenv("AI_INTEGRATOR_MAX_CONCURRENT", "2")),
        )


# Global singleton (lazy init)
_config: AiIntegratorConfig | None = None


def get_config() -> AiIntegratorConfig:
    """Get the global AI integrator configuration."""
    global _config
    if _config is None:
        _config = AiIntegratorConfig.from_env()
    return _config
