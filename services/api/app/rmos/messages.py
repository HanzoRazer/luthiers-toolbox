# services/api/app/rmos/messages.py
"""
RMOS Unified Message Model

Foundation for all warning/error messaging across CAM guards.
Used by fret_cam_guard, saw_cam_guard, and geometry validators.

Wave 5 Implementation (Golden Path Suite)
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


RmosSeverity = Literal["info", "warning", "error", "fatal"]


class RmosMessage(BaseModel):
    """
    Unified message format for RMOS feasibility/guard output.
    
    Attributes:
        code: Machine-readable identifier (e.g., "CHIPLOAD_HIGH", "SLOT_DEPTH_EXCEEDS_TOOL")
        severity: One of "info", "warning", "error", "fatal"
        message: Human-readable description
        context: Structured data (actual values, thresholds, etc.)
        hint: Optional remediation suggestion
    """
    code: str
    severity: RmosSeverity
    message: str
    context: Dict[str, Any] = {}
    hint: Optional[str] = None


def as_message(
    code: str,
    severity: RmosSeverity,
    message: str,
    **context: Any,
) -> RmosMessage:
    """Create an RmosMessage with the given severity."""
    return RmosMessage(code=code, severity=severity, message=message, context=context)


def as_warning(code: str, message: str, **context: Any) -> RmosMessage:
    """Create a warning-level message."""
    return as_message(code=code, severity="warning", message=message, **context)


def as_error(code: str, message: str, **context: Any) -> RmosMessage:
    """Create an error-level message."""
    return as_message(code=code, severity="error", message=message, **context)


def as_info(code: str, message: str, **context: Any) -> RmosMessage:
    """Create an info-level message."""
    return as_message(code=code, severity="info", message=message, **context)


def as_fatal(code: str, message: str, **context: Any) -> RmosMessage:
    """Create a fatal-level message (operation should not proceed)."""
    return as_message(code=code, severity="fatal", message=message, **context)


def collect_messages(*message_lists: List[RmosMessage]) -> List[RmosMessage]:
    """Combine multiple message lists into one, preserving order."""
    result = []
    for msgs in message_lists:
        result.extend(msgs)
    return result


def has_fatal(messages: List[RmosMessage]) -> bool:
    """Check if any message is fatal severity."""
    return any(m.severity == "fatal" for m in messages)


def has_errors(messages: List[RmosMessage]) -> bool:
    """Check if any message is error or fatal severity."""
    return any(m.severity in ("error", "fatal") for m in messages)


def max_severity(messages: List[RmosMessage]) -> Optional[RmosSeverity]:
    """Return the highest severity level in a message list."""
    if not messages:
        return None
    
    severity_order = {"info": 0, "warning": 1, "error": 2, "fatal": 3}
    max_sev = max(messages, key=lambda m: severity_order.get(m.severity, 0))
    return max_sev.severity
