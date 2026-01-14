"""
AI Context Adapter - Strict Redactor

Implements strict redaction rules for v1:
- Removes anything in forbidden categories
- Strips Smart Guitar / pedagogy data
- Removes write-capable endpoint references
- Downgrades unsafe content to summaries
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Sequence, Set, Tuple

from app.ai_context.schemas import (
    AdapterWarning,
    ContextAttachment,
    ContextSource,
    ForbiddenCategory,
    RedactionPolicy,
    SourceKind,
    WarningCode,
)


# -------------------------
# Field patterns to redact
# -------------------------

# Fields that indicate toolpath/gcode content
TOOLPATH_FIELDS: Set[str] = {
    "toolpath",
    "toolpaths",
    "gcode",
    "g_code",
    "nc_code",
    "ngc",
    "moves",
    "tool_moves",
    "path_data",
    "path_segments",
    "trajectory",
}

# Fields that indicate machine secrets
MACHINE_SECRET_FIELDS: Set[str] = {
    "api_key",
    "api_secret",
    "password",
    "token",
    "secret",
    "credential",
    "credentials",
    "machine_token",
    "auth_token",
    "bearer",
    "private_key",
}

# Fields that indicate player/pedagogy data (Smart Guitar)
PEDAGOGY_FIELDS: Set[str] = {
    "player_id",
    "player_name",
    "lesson_id",
    "lesson_progress",
    "coach_feedback",
    "coaching_notes",
    "practice_session",
    "skill_level",
    "learning_path",
    "student_data",
    "player_stats",
    "player_profile",
}

# Fields that indicate personal data
PERSONAL_DATA_FIELDS: Set[str] = {
    "email",
    "phone",
    "address",
    "ssn",
    "social_security",
    "credit_card",
    "bank_account",
    "full_name",
    "date_of_birth",
    "dob",
    "ip_address",
}

# Patterns that look like action endpoints (POST/PUT/DELETE instructions)
ACTION_PATTERN = re.compile(
    r"(POST|PUT|PATCH|DELETE)\s+/api/",
    re.IGNORECASE,
)


def _get_forbidden_fields(policy: RedactionPolicy) -> Set[str]:
    """Build set of field names to redact based on policy."""
    fields: Set[str] = set()
    
    if policy.is_forbidden(ForbiddenCategory.TOOLPATHS):
        fields.update(TOOLPATH_FIELDS)
    if policy.is_forbidden(ForbiddenCategory.GCODE):
        fields.update(TOOLPATH_FIELDS)  # Same fields
    if policy.is_forbidden(ForbiddenCategory.MACHINE_SECRETS):
        fields.update(MACHINE_SECRET_FIELDS)
    if policy.is_forbidden(ForbiddenCategory.CREDENTIAL_MATERIAL):
        fields.update(MACHINE_SECRET_FIELDS)  # Overlap
    if policy.is_forbidden(ForbiddenCategory.PLAYER_PEDAGOGY):
        fields.update(PEDAGOGY_FIELDS)
    if policy.is_forbidden(ForbiddenCategory.PERSONAL_DATA):
        fields.update(PERSONAL_DATA_FIELDS)
    
    return fields


class StrictRedactor:
    """
    Strict redactor that enforces forbidden_categories.
    
    Redaction rules:
    1. Remove fields matching forbidden patterns
    2. Replace redacted content with "[REDACTED]" marker
    3. Emit warnings for each redaction
    4. Downgrade unsafe content to summaries when possible
    """
    
    def redact_sources(
        self,
        sources: Sequence[ContextSource],
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextSource], List[AdapterWarning]]:
        """
        Redact forbidden content from sources.
        """
        redacted: List[ContextSource] = []
        warnings: List[AdapterWarning] = []
        
        forbidden_fields = _get_forbidden_fields(policy)
        
        for source in sources:
            # Check if entire source should be omitted
            if self._should_omit_source(source, policy):
                warnings.append(AdapterWarning(
                    code=WarningCode.REDACTED_SOURCE,
                    message=f"Source '{source.source_id}' omitted due to forbidden content",
                    source_id=source.source_id,
                ))
                continue
            
            # Redact individual fields
            redacted_payload, field_warnings = self._redact_payload(
                source.payload,
                forbidden_fields,
                source.source_id,
            )
            warnings.extend(field_warnings)
            
            # Check for action patterns in string values
            redacted_payload, action_warnings = self._redact_action_patterns(
                redacted_payload,
                source.source_id,
            )
            warnings.extend(action_warnings)
            
            # Create new source with redacted payload
            redacted.append(ContextSource(
                source_id=source.source_id,
                kind=source.kind,
                content_type=source.content_type,
                payload=redacted_payload,
            ))
        
        return redacted, warnings
    
    def redact_attachments(
        self,
        attachments: Sequence[ContextAttachment],
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextAttachment], List[AdapterWarning]]:
        """
        Redact forbidden attachments.
        """
        allowed: List[ContextAttachment] = []
        warnings: List[AdapterWarning] = []
        
        for attachment in attachments:
            # Check if attachment type is forbidden
            if self._is_attachment_forbidden(attachment, policy):
                warnings.append(AdapterWarning(
                    code=WarningCode.REDACTED_ATTACHMENT,
                    message=f"Attachment '{attachment.attachment_id}' omitted due to policy",
                    source_id=attachment.attachment_id,
                ))
                continue
            
            allowed.append(attachment)
        
        return allowed, warnings
    
    def _should_omit_source(
        self,
        source: ContextSource,
        policy: RedactionPolicy,
    ) -> bool:
        """Check if entire source should be omitted."""
        # Sources that are inherently forbidden in strict mode
        if policy.is_forbidden(ForbiddenCategory.RAW_TELEMETRY):
            if source.kind == SourceKind.TELEMETRY_SUMMARY:
                # Only omit if payload contains raw telemetry
                if "raw_data" in source.payload or "samples" in source.payload:
                    return True
        
        return False
    
    def _redact_payload(
        self,
        payload: Dict[str, Any],
        forbidden_fields: Set[str],
        source_id: str,
    ) -> Tuple[Dict[str, Any], List[AdapterWarning]]:
        """Recursively redact forbidden fields from payload."""
        redacted: Dict[str, Any] = {}
        warnings: List[AdapterWarning] = []
        
        for key, value in payload.items():
            key_lower = key.lower()
            
            # Check if field name matches forbidden patterns
            if key_lower in forbidden_fields or any(f in key_lower for f in forbidden_fields):
                redacted[key] = "[REDACTED]"
                warnings.append(AdapterWarning(
                    code=WarningCode.REDACTED_FIELD,
                    message=f"Field '{key}' redacted",
                    source_id=source_id,
                ))
            elif isinstance(value, dict):
                # Recurse into nested dicts
                nested, nested_warnings = self._redact_payload(
                    value, forbidden_fields, source_id
                )
                redacted[key] = nested
                warnings.extend(nested_warnings)
            elif isinstance(value, list):
                # Handle lists
                redacted[key] = self._redact_list(
                    value, forbidden_fields, source_id, warnings
                )
            else:
                redacted[key] = value
        
        return redacted, warnings
    
    def _redact_list(
        self,
        items: List[Any],
        forbidden_fields: Set[str],
        source_id: str,
        warnings: List[AdapterWarning],
    ) -> List[Any]:
        """Redact items in a list."""
        result: List[Any] = []
        for item in items:
            if isinstance(item, dict):
                redacted_item, item_warnings = self._redact_payload(
                    item, forbidden_fields, source_id
                )
                result.append(redacted_item)
                warnings.extend(item_warnings)
            else:
                result.append(item)
        return result
    
    def _redact_action_patterns(
        self,
        payload: Dict[str, Any],
        source_id: str,
    ) -> Tuple[Dict[str, Any], List[AdapterWarning]]:
        """Remove action instructions from string values."""
        redacted: Dict[str, Any] = {}
        warnings: List[AdapterWarning] = []
        
        for key, value in payload.items():
            if isinstance(value, str) and ACTION_PATTERN.search(value):
                # Replace action instructions with placeholder
                redacted[key] = ACTION_PATTERN.sub("[ACTION_REDACTED]", value)
                warnings.append(AdapterWarning(
                    code=WarningCode.SENSITIVE_CONTENT_OMITTED,
                    message=f"Action instruction removed from '{key}'",
                    source_id=source_id,
                ))
            elif isinstance(value, dict):
                nested, nested_warnings = self._redact_action_patterns(value, source_id)
                redacted[key] = nested
                warnings.extend(nested_warnings)
            else:
                redacted[key] = value
        
        return redacted, warnings
    
    def _is_attachment_forbidden(
        self,
        attachment: ContextAttachment,
        policy: RedactionPolicy,
    ) -> bool:
        """Check if attachment should be filtered out."""
        # NC/G-code files
        if policy.is_forbidden(ForbiddenCategory.GCODE):
            forbidden_mimes = {"application/x-gcode", "text/x-gcode"}
            forbidden_exts = {".nc", ".ngc", ".gcode", ".tap"}
            
            if attachment.mime in forbidden_mimes:
                return True
            if any(attachment.url.lower().endswith(ext) for ext in forbidden_exts):
                return True
        
        return False


# Singleton instance
strict_redactor = StrictRedactor()
