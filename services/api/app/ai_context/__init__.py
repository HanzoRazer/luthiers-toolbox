"""
AI Context Adapter - Package init

Read-only, redaction-first context adapter for AI consumption.
"""

from .schemas import (
    # Enums
    ActorKind,
    ActorRole,
    AttachmentKind,
    ForbiddenCategory,
    RedactionLevel,
    SourceKind,
    WarningCode,
    # Data structures
    Actor,
    AdapterResult,
    AdapterWarning,
    ContextAttachment,
    ContextEnvelope,
    ContextRequest,
    ContextSource,
    RedactionPolicy,
    Scope,
    STRICT_POLICY,
    # Protocols
    ContextAssembler,
    ContextProvider,
    ContextRedactor,
    # Utilities
    compute_bundle_sha256,
    generate_attachment_id,
    generate_request_id,
    utc_now_iso,
)

__all__ = [
    # Enums
    "ActorKind",
    "ActorRole",
    "AttachmentKind",
    "ForbiddenCategory",
    "RedactionLevel",
    "SourceKind",
    "WarningCode",
    # Data structures
    "Actor",
    "AdapterResult",
    "AdapterWarning",
    "ContextAttachment",
    "ContextEnvelope",
    "ContextRequest",
    "ContextSource",
    "RedactionPolicy",
    "Scope",
    "STRICT_POLICY",
    # Protocols
    "ContextAssembler",
    "ContextProvider",
    "ContextRedactor",
    # Utilities
    "compute_bundle_sha256",
    "generate_attachment_id",
    "generate_request_id",
    "utc_now_iso",
]
