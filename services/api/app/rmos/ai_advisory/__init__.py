"""
RMOS AI Advisory Module — CLI Integration

This module provides the integration seam between RMOS and ai-integrator.
RMOS is the ONLY caller of ai-integrator; ToolBox never calls it directly.

Flow:
1. ToolBox sends AIContextPacket to RMOS
2. RMOS validates, invokes ai-integrator CLI, validates output
3. RMOS persists AdvisoryArtifact and returns advisory_id

See: copilot-instructions.md for architectural boundaries.
"""

from .config import AiIntegratorConfig
from .exceptions import (
    AiIntegratorError,
    AiIntegratorGovernance,
    AiIntegratorRuntime,
    AiIntegratorSchema,
    AiIntegratorUnsupported,
)
from .runner import run_ai_integrator_job
from .service import request_advisory
from .schemas import (
    AIContextPacketV1,
    AdvisoryDraftV1,
    AdvisoryArtifactV1,
    AdvisoryRequestResponse,
)

__all__ = [
    # Config
    "AiIntegratorConfig",
    # Exceptions
    "AiIntegratorError",
    "AiIntegratorGovernance",
    "AiIntegratorRuntime",
    "AiIntegratorSchema",
    "AiIntegratorUnsupported",
    # Core
    "run_ai_integrator_job",
    "request_advisory",
    # Schemas
    "AIContextPacketV1",
    "AdvisoryDraftV1",
    "AdvisoryArtifactV1",
    "AdvisoryRequestResponse",
]
