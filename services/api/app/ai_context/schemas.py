"""
AI Context Adapter Interface v1

Read-only, redaction-first context adapter for AI consumption.
This module defines the core data structures and protocols for the adapter boundary.

Design goals:
- Read-only: no mutation, no "actions"
- Deterministic: same inputs → same snapshot structure
- Redaction-first: secrets and user-private data stripped by default
- Composable: multiple context sources can be merged

See: contracts/AI_CONTEXT_ADAPTER_INTERFACE_v1.json
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple


# -------------------------
# Enums
# -------------------------

class ActorKind(str, Enum):
    HUMAN = "human"
    SYSTEM = "system"
    AUTOMATED = "automated"


class ActorRole(str, Enum):
    BUILDER = "builder"
    OPERATOR = "operator"
    ADMIN = "admin"
    VIEWER = "viewer"


class RedactionLevel(str, Enum):
    STRICT = "strict"
    BALANCED = "balanced"


class SourceKind(str, Enum):
    """v1 vocabulary for context source types."""
    RUN_SUMMARY = "run_summary"
    DESIGN_INTENT = "design_intent"
    GOVERNANCE_NOTES = "governance_notes"
    DOCS_EXCERPT = "docs_excerpt"
    UI_STATE_HINT = "ui_state_hint"
    TELEMETRY_SUMMARY = "telemetry_summary"
    CALC_STATUS = "calc_status"


class AttachmentKind(str, Enum):
    IMAGE = "image"
    FILE = "file"
    PREVIEW = "preview"


class ForbiddenCategory(str, Enum):
    """Categories that MUST be redacted in strict mode."""
    TOOLPATHS = "toolpaths"
    GCODE = "gcode"
    MACHINE_SECRETS = "machine_secrets"
    CREDENTIAL_MATERIAL = "credential_material"
    PLAYER_PEDAGOGY = "player_pedagogy"
    PERSONAL_DATA = "personal_data"
    PROPRIETARY_ALGORITHMS = "proprietary_algorithms"
    RAW_TELEMETRY = "raw_telemetry"


# -------------------------
# Core data structures
# -------------------------

@dataclass(frozen=True)
class Actor:
    """Actor who initiated the context request."""
    kind: ActorKind
    role: ActorRole
    auth_context: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "kind": self.kind.value,
            "role": self.role.value,
            "auth_context": self.auth_context,
        }


@dataclass(frozen=True)
class Scope:
    """Scope of the context request."""
    project_id: Optional[str] = None
    run_id: Optional[str] = None
    pattern_id: Optional[str] = None
    session_id: Optional[str] = None
    artifact_id: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        return {k: v for k, v in {
            "project_id": self.project_id,
            "run_id": self.run_id,
            "pattern_id": self.pattern_id,
            "session_id": self.session_id,
            "artifact_id": self.artifact_id,
        }.items() if v is not None}


@dataclass(frozen=True)
class ContextRequest:
    """A request for context from the AI system."""
    request_id: str
    intent: str
    scope: Scope
    actor: Actor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "actor": self.actor.to_dict(),
            "intent": self.intent,
            "scope": self.scope.to_dict(),
        }


@dataclass(frozen=True)
class RedactionPolicy:
    """Policy controlling what content must be redacted."""
    mode: str = "read_only"  # v1 only supports read_only
    redaction_level: RedactionLevel = RedactionLevel.STRICT
    forbidden_categories: Tuple[ForbiddenCategory, ...] = field(default_factory=lambda: (
        ForbiddenCategory.TOOLPATHS,
        ForbiddenCategory.GCODE,
        ForbiddenCategory.MACHINE_SECRETS,
        ForbiddenCategory.CREDENTIAL_MATERIAL,
        ForbiddenCategory.PLAYER_PEDAGOGY,
        ForbiddenCategory.PERSONAL_DATA,
    ))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "redaction_level": self.redaction_level.value,
            "forbidden_categories": [c.value for c in self.forbidden_categories],
        }

    def is_forbidden(self, category: ForbiddenCategory) -> bool:
        return category in self.forbidden_categories


# Default strict policy
STRICT_POLICY = RedactionPolicy()


@dataclass(frozen=True)
class ContextSource:
    """A single source of context (already sanitized)."""
    source_id: str
    kind: SourceKind
    content_type: str
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "kind": self.kind.value,
            "content_type": self.content_type,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class ContextAttachment:
    """A binary attachment referenced by URL (read-only)."""
    attachment_id: str
    kind: AttachmentKind
    mime: str
    sha256: str
    url: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attachment_id": self.attachment_id,
            "kind": self.kind.value,
            "mime": self.mime,
            "sha256": self.sha256,
            "url": self.url,
        }


@dataclass(frozen=True)
class AdapterWarning:
    """Warning generated during context assembly or redaction."""
    code: str
    message: str
    source_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.source_id:
            result["source_id"] = self.source_id
        return result


@dataclass(frozen=True)
class ContextEnvelope:
    """The complete context envelope for AI consumption."""
    schema_id: str
    schema_version: str
    created_at_utc: str
    request: ContextRequest
    policy: RedactionPolicy
    sources: Tuple[ContextSource, ...]
    attachments: Tuple[ContextAttachment, ...]
    bundle_sha256: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "created_at_utc": self.created_at_utc,
            "request": self.request.to_dict(),
            "policy": self.policy.to_dict(),
            "context": {
                "sources": [s.to_dict() for s in self.sources],
                "attachments": [a.to_dict() for a in self.attachments],
            },
            "integrity": {
                "bundle_sha256": self.bundle_sha256,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


@dataclass(frozen=True)
class AdapterResult:
    """Result of context assembly."""
    envelope: ContextEnvelope
    warnings: Tuple[AdapterWarning, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope": self.envelope.to_dict(),
            "warnings": [w.to_dict() for w in self.warnings],
        }


# -------------------------
# Adapter interfaces (Protocols)
# -------------------------

class ContextProvider(Protocol):
    """
    A ContextProvider pulls a single slice of read-only context from ToolBox
    (or from local cached docs), and returns it already sanitized.
    """

    @property
    def source_kind(self) -> SourceKind:
        """The kind of source this provider produces."""
        ...

    def provide(
        self,
        req: ContextRequest,
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextSource], List[ContextAttachment], List[AdapterWarning]]:
        """
        Provide context sources and attachments.
        
        Returns:
            Tuple of (sources, attachments, warnings)
        """
        ...


class ContextRedactor(Protocol):
    """
    Redaction is explicit and testable.
    Implementations must enforce forbidden_categories.
    """

    def redact_sources(
        self,
        sources: Sequence[ContextSource],
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextSource], List[AdapterWarning]]:
        """
        Redact forbidden content from sources.
        
        Returns:
            Tuple of (redacted_sources, warnings)
        """
        ...

    def redact_attachments(
        self,
        attachments: Sequence[ContextAttachment],
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextAttachment], List[AdapterWarning]]:
        """
        Redact forbidden attachments.
        
        Returns:
            Tuple of (allowed_attachments, warnings)
        """
        ...


class ContextAssembler(Protocol):
    """
    The assembler orchestrates providers, applies redaction, and builds the final envelope.
    """

    def build(
        self,
        req: ContextRequest,
        policy: RedactionPolicy,
    ) -> AdapterResult:
        """
        Build a complete context envelope.
        
        Returns:
            AdapterResult containing the envelope and any warnings
        """
        ...


# -------------------------
# Utility functions
# -------------------------

def compute_bundle_sha256(
    sources: Sequence[ContextSource],
    attachments: Sequence[ContextAttachment],
) -> str:
    """
    Compute SHA256 hash of the canonical JSON representation of sources + attachments.
    This provides integrity verification for the context bundle.
    """
    canonical = {
        "sources": [s.to_dict() for s in sources],
        "attachments": [a.to_dict() for a in attachments],
    }
    # Sort keys for deterministic output
    json_str = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_request_id() -> str:
    """Generate a unique context request ID."""
    import uuid
    return f"ctxreq_{uuid.uuid4().hex[:12]}"


def generate_attachment_id() -> str:
    """Generate a unique attachment ID."""
    import uuid
    return f"att_{uuid.uuid4().hex[:12]}"


# -------------------------
# Warning codes
# -------------------------

class WarningCode:
    """Standard warning codes for adapter operations."""
    # Redaction warnings
    REDACTED_FIELD = "REDACTED_FIELD"
    REDACTED_SOURCE = "REDACTED_SOURCE"
    REDACTED_ATTACHMENT = "REDACTED_ATTACHMENT"
    
    # Provider warnings
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    SCOPE_NOT_FOUND = "SCOPE_NOT_FOUND"
    
    # Content warnings
    CONTENT_TRUNCATED = "CONTENT_TRUNCATED"
    CONTENT_DOWNGRADED = "CONTENT_DOWNGRADED"
    SENSITIVE_CONTENT_OMITTED = "SENSITIVE_CONTENT_OMITTED"
