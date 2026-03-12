"""
Miscellaneous Stub Routes

This file previously contained stub endpoints. All stubs have been wired to real
implementations or removed as vestigial.

WIRED to real implementations:
- /ai/advisories/request - See app.rmos.ai_advisory.service.request_advisory

REMOVED (real implementations exist):
- /blueprint/* - See app.routers.blueprint (phase1_router, phase2_router)
- /art/rosette/compare/snapshot - GET was never used (POST exists in rosette_compare_routes)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel


router = APIRouter(tags=["stubs"])


# =============================================================================
# AI Advisory Proxies (delegating to real rmos.ai_advisory service)
# =============================================================================

from ..rmos.ai_advisory import (
    request_advisory as _request_advisory,
    AiIntegratorError,
    AiIntegratorSchema,
    AiIntegratorGovernance,
    AiIntegratorRuntime,
    AiIntegratorUnsupported,
)


@router.post("/ai/advisories/request")
def request_advisory_endpoint(
    payload: Dict[str, Any] = None,
    request: Request = None,
) -> Dict[str, Any]:
    """Request an AI advisory for design decisions (proxy to real service).
    
    This endpoint wraps the RMOS ai_advisory service which:
    1. Validates the AIContextPacket schema
    2. Invokes the ai-integrator CLI
    3. Validates the AdvisoryDraft output
    4. Creates and persists an AdvisoryArtifact
    5. Returns the advisory_id for retrieval
    """
    if payload is None:
        payload = {}
    
    # Extract user_id from request headers if available
    user_id = None
    if request:
        user_id = request.headers.get("X-User-Id") or request.headers.get("X-Operator-Id")
    
    try:
        response = _request_advisory(payload, user_id=user_id)
        return {
            "ok": response.ok,
            "advisory_id": response.advisory_id,
            "status": response.status,
            "message": response.message,
        }
    except AiIntegratorSchema as e:
        # Schema validation failed (input or output)
        return {
            "ok": False,
            "advisory_id": None,
            "status": "error",
            "message": str(e),
            "error_code": "SCHEMA_VALIDATION_ERROR",
        }
    except AiIntegratorGovernance as e:
        # Governance check failed
        return {
            "ok": False,
            "advisory_id": None,
            "status": "error",
            "message": str(e),
            "error_code": "GOVERNANCE_ERROR",
        }
    except AiIntegratorRuntime as e:
        # CLI execution failed
        return {
            "ok": False,
            "advisory_id": None,
            "status": "error",
            "message": str(e),
            "error_code": "RUNTIME_ERROR",
        }
    except AiIntegratorUnsupported as e:
        # Unsupported job/template
        return {
            "ok": False,
            "advisory_id": None,
            "status": "error",
            "message": str(e),
            "error_code": "UNSUPPORTED_ERROR",
        }
    except AiIntegratorError as e:
        # Generic ai-integrator error
        return {
            "ok": False,
            "advisory_id": None,
            "status": "error",
            "message": str(e),
            "error_code": "AI_INTEGRATOR_ERROR",
        }
    except Exception as e:  # WP-2: API endpoint catch-all
        # Unexpected error - log and return generic message
        return {
            "ok": False,
            "advisory_id": None,
            "status": "error",
            "message": f"Unexpected error: {type(e).__name__}",
            "error_code": "INTERNAL_ERROR",
        }
