"""
AI Audit Logging

Provides structured audit logging for all AI operations.
Captures provenance information required by governance.

INVARIANT: Every AI call captures:
- request_id
- provider
- model
- revised_prompt (if applicable)
- cost_estimate
- content hashes
"""
from __future__ import annotations

import json
import logging
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional, List
from pathlib import Path

from .request_id import get_request_id

logger = logging.getLogger("ai.audit")


@dataclass
class AuditEntry:
    """
    Structured audit entry for an AI operation.

    Captures all provenance information required by governance.
    """
    # Identification
    request_id: str
    timestamp: str
    operation: str  # "llm", "image", "embedding"

    # Provider details
    provider: str
    model: str

    # Input
    prompt_hash: str  # SHA256 of original prompt
    prompt_length: int

    # Output
    response_hash: Optional[str] = None  # SHA256 of response content
    response_length: Optional[int] = None

    # Modifications
    revised_prompt: Optional[str] = None  # If provider modified prompt (DALL-E)
    revised_prompt_hash: Optional[str] = None

    # Cost
    cost_estimate_usd: Optional[float] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None

    # Safety
    safety_level: Optional[str] = None  # "green", "yellow", "red"
    safety_category: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Structured logger for AI operations.

    Writes audit entries to both Python logging and optional file.
    """

    def __init__(
        self,
        log_file: Optional[Path] = None,
        log_level: int = logging.INFO,
    ):
        self.log_file = log_file
        self.log_level = log_level
        self._entries: List[AuditEntry] = []

    def log(self, entry: AuditEntry) -> None:
        """Log an audit entry."""
        self._entries.append(entry)

        # Log to Python logger
        logger.log(
            self.log_level,
            f"AI_AUDIT: {entry.operation} | {entry.provider}/{entry.model} | "
            f"req={entry.request_id} | cost=${entry.cost_estimate_usd or 0:.4f}"
        )

        # Optionally write to file
        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(entry.to_json() + "\n")
            except OSError as e:  # WP-1: narrowed from except Exception
                logger.error(f"Failed to write audit log: {e}")

    def get_entries(
        self,
        request_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Get recent audit entries, optionally filtered by request ID."""
        entries = self._entries
        if request_id:
            entries = [e for e in entries if e.request_id == request_id]
        return entries[-limit:]


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_ai_call(
    operation: str,
    provider: str,
    model: str,
    prompt: str,
    response_content: Optional[str] = None,
    response_bytes: Optional[bytes] = None,
    revised_prompt: Optional[str] = None,
    cost_estimate_usd: Optional[float] = None,
    tokens_input: Optional[int] = None,
    tokens_output: Optional[int] = None,
    safety_level: Optional[str] = None,
    safety_category: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """
    Create and log an audit entry for an AI operation.

    This is the main entry point for audit logging.
    All AI operations should call this after completion.

    Args:
        operation: Type of operation ("llm", "image", "embedding")
        provider: Provider name ("openai", "anthropic", etc.)
        model: Model identifier
        prompt: Original prompt text
        response_content: Text response content (for LLM)
        response_bytes: Binary response (for images)
        revised_prompt: If provider modified the prompt
        cost_estimate_usd: Estimated cost
        tokens_input: Input token count
        tokens_output: Output token count
        safety_level: Safety check result
        safety_category: Content category
        metadata: Additional metadata

    Returns:
        The created AuditEntry
    """
    request_id = get_request_id() or "unknown"

    # Compute hashes
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

    response_hash = None
    response_length = None
    if response_content:
        response_hash = hashlib.sha256(response_content.encode()).hexdigest()[:16]
        response_length = len(response_content)
    elif response_bytes:
        response_hash = hashlib.sha256(response_bytes).hexdigest()[:16]
        response_length = len(response_bytes)

    revised_prompt_hash = None
    if revised_prompt:
        revised_prompt_hash = hashlib.sha256(revised_prompt.encode()).hexdigest()[:16]

    entry = AuditEntry(
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat(),
        operation=operation,
        provider=provider,
        model=model,
        prompt_hash=prompt_hash,
        prompt_length=len(prompt),
        response_hash=response_hash,
        response_length=response_length,
        revised_prompt=revised_prompt,
        revised_prompt_hash=revised_prompt_hash,
        cost_estimate_usd=cost_estimate_usd,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        safety_level=safety_level,
        safety_category=safety_category,
        metadata=metadata or {},
    )

    get_audit_logger().log(entry)
    return entry
