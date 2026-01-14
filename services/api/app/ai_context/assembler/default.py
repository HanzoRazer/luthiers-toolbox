"""
AI Context Adapter - Default Assembler

Orchestrates providers, applies redaction, and builds the final envelope.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from ..schemas import (
    AdapterResult,
    AdapterWarning,
    ContextAttachment,
    ContextEnvelope,
    ContextRequest,
    ContextSource,
    RedactionPolicy,
    WarningCode,
    compute_bundle_sha256,
    utc_now_iso,
    STRICT_POLICY,
)
from ..redactor import strict_redactor
from ..providers import (
    run_summary_provider,
    design_intent_provider,
    governance_notes_provider,
    docs_excerpt_provider,
    ui_state_hint_provider,
)


# Schema constants
SCHEMA_ID = "toolbox_ai_context_envelope"
SCHEMA_VERSION = "v1"


class DefaultAssembler:
    """
    Default context assembler.
    
    Orchestrates all registered providers, applies redaction,
    and builds the final context envelope.
    
    Provider execution order:
    1. UI state hint (lightweight, always runs)
    2. Run summary (if run_id in scope)
    3. Design intent (if pattern_id in scope)
    4. Governance notes (always relevant)
    5. Docs excerpt (based on intent keywords)
    """
    
    def __init__(self):
        """Initialize with default providers."""
        # Provider instances in execution order
        self._providers = [
            ui_state_hint_provider,
            run_summary_provider,
            design_intent_provider,
            governance_notes_provider,
            docs_excerpt_provider,
        ]
        
        # Redactor
        self._redactor = strict_redactor
    
    def build(
        self,
        req: ContextRequest,
        policy: Optional[RedactionPolicy] = None,
    ) -> AdapterResult:
        """
        Build a complete context envelope.
        
        Args:
            req: The context request
            policy: Redaction policy (defaults to STRICT_POLICY)
        
        Returns:
            AdapterResult with envelope and warnings
        """
        if policy is None:
            policy = STRICT_POLICY
        
        all_sources: List[ContextSource] = []
        all_attachments: List[ContextAttachment] = []
        all_warnings: List[AdapterWarning] = []
        
        # Run each provider
        for provider in self._providers:
            try:
                sources, attachments, warnings = provider.provide(req, policy)
                all_sources.extend(sources)
                all_attachments.extend(attachments)
                all_warnings.extend(warnings)
            except Exception as e:
                all_warnings.append(AdapterWarning(
                    code=WarningCode.PROVIDER_ERROR,
                    message=f"Provider {provider.__class__.__name__} failed: {e}",
                ))
        
        # Apply redaction
        redacted_sources, redaction_warnings = self._redactor.redact_sources(
            all_sources, policy
        )
        all_warnings.extend(redaction_warnings)
        
        redacted_attachments, attachment_warnings = self._redactor.redact_attachments(
            all_attachments, policy
        )
        all_warnings.extend(attachment_warnings)
        
        # Compute bundle hash
        bundle_sha256 = compute_bundle_sha256(redacted_sources, redacted_attachments)
        
        # Build envelope
        envelope = ContextEnvelope(
            schema_id=SCHEMA_ID,
            schema_version=SCHEMA_VERSION,
            created_at_utc=utc_now_iso(),
            request=req,
            policy=policy,
            sources=tuple(redacted_sources),
            attachments=tuple(redacted_attachments),
            bundle_sha256=bundle_sha256,
        )
        
        return AdapterResult(
            envelope=envelope,
            warnings=tuple(all_warnings),
        )
    
    def build_minimal(
        self,
        req: ContextRequest,
        provider_kinds: Optional[Sequence[str]] = None,
        policy: Optional[RedactionPolicy] = None,
    ) -> AdapterResult:
        """
        Build a minimal context envelope with only specific providers.
        
        Args:
            req: The context request
            provider_kinds: List of source kinds to include (e.g., ["run_summary", "governance_notes"])
            policy: Redaction policy (defaults to STRICT_POLICY)
        
        Returns:
            AdapterResult with envelope and warnings
        """
        if policy is None:
            policy = STRICT_POLICY
        
        if provider_kinds is None:
            # Default minimal set
            provider_kinds = ["ui_state_hint", "governance_notes"]
        
        all_sources: List[ContextSource] = []
        all_attachments: List[ContextAttachment] = []
        all_warnings: List[AdapterWarning] = []
        
        # Run only requested providers
        for provider in self._providers:
            if provider.source_kind.value in provider_kinds:
                try:
                    sources, attachments, warnings = provider.provide(req, policy)
                    all_sources.extend(sources)
                    all_attachments.extend(attachments)
                    all_warnings.extend(warnings)
                except Exception as e:
                    all_warnings.append(AdapterWarning(
                        code=WarningCode.PROVIDER_ERROR,
                        message=f"Provider {provider.__class__.__name__} failed: {e}",
                    ))
        
        # Apply redaction
        redacted_sources, redaction_warnings = self._redactor.redact_sources(
            all_sources, policy
        )
        all_warnings.extend(redaction_warnings)
        
        redacted_attachments, attachment_warnings = self._redactor.redact_attachments(
            all_attachments, policy
        )
        all_warnings.extend(attachment_warnings)
        
        # Compute bundle hash
        bundle_sha256 = compute_bundle_sha256(redacted_sources, redacted_attachments)
        
        # Build envelope
        envelope = ContextEnvelope(
            schema_id=SCHEMA_ID,
            schema_version=SCHEMA_VERSION,
            created_at_utc=utc_now_iso(),
            request=req,
            policy=policy,
            sources=tuple(redacted_sources),
            attachments=tuple(redacted_attachments),
            bundle_sha256=bundle_sha256,
        )
        
        return AdapterResult(
            envelope=envelope,
            warnings=tuple(all_warnings),
        )


# Singleton instance
default_assembler = DefaultAssembler()


# Convenience function
def build_context_envelope(
    request_id: str,
    intent: str,
    actor_kind: str = "human",
    actor_role: str = "builder",
    auth_context: str = "toolbox_session",
    run_id: Optional[str] = None,
    pattern_id: Optional[str] = None,
    session_id: Optional[str] = None,
    project_id: Optional[str] = None,
    redaction_level: str = "strict",
) -> AdapterResult:
    """
    Convenience function to build a context envelope.
    
    This provides a simpler interface for common use cases.
    """
    from ..schemas import Actor, ActorKind, ActorRole, RedactionLevel, Scope
    
    req = ContextRequest(
        request_id=request_id,
        intent=intent,
        actor=Actor(
            kind=ActorKind(actor_kind),
            role=ActorRole(actor_role),
            auth_context=auth_context,
        ),
        scope=Scope(
            run_id=run_id,
            pattern_id=pattern_id,
            session_id=session_id,
            project_id=project_id,
        ),
    )
    
    policy = RedactionPolicy(
        redaction_level=RedactionLevel(redaction_level),
    )
    
    return default_assembler.build(req, policy)
