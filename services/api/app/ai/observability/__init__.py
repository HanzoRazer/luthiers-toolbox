"""
AI Observability Layer - Request Tracking and Audit Logging

Provides request ID propagation and consistent audit logging
for all AI operations.

INVARIANT: Every AI call captures provenance:
- request_id
- provider
- model
- revised_prompt
- cost_estimate
- content hashes
"""

from .request_id import (
    get_request_id,
    set_request_id,
    generate_request_id,
    RequestIdMiddleware,
)

from .audit_log import (
    audit_ai_call,
    AuditEntry,
    get_audit_logger,
)

__all__ = [
    # Request ID
    "get_request_id",
    "set_request_id",
    "generate_request_id",
    "RequestIdMiddleware",
    # Audit
    "audit_ai_call",
    "AuditEntry",
    "get_audit_logger",
]
