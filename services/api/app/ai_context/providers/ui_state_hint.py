"""
AI Context Adapter - UI State Hint Provider

Provides lightweight hints about the current UI state.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..schemas import (
    AdapterWarning,
    ContextAttachment,
    ContextRequest,
    ContextSource,
    RedactionPolicy,
    SourceKind,
)


class UIStateHintProvider:
    """
    Provides ui_state_hint context describing what the user is looking at.
    
    This is a lightweight provider that creates hints based on the
    request scope and intent. The actual UI state comes from the
    request metadata, not from reading actual UI state.
    """
    
    @property
    def source_kind(self) -> SourceKind:
        return SourceKind.UI_STATE_HINT
    
    def provide(
        self,
        req: ContextRequest,
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextSource], List[ContextAttachment], List[AdapterWarning]]:
        """Provide UI state hint context."""
        sources: List[ContextSource] = []
        attachments: List[ContextAttachment] = []
        warnings: List[AdapterWarning] = []
        
        # Build hint from scope
        hint = self._build_hint(req)
        
        sources.append(ContextSource(
            source_id="ui_state_hint",
            kind=SourceKind.UI_STATE_HINT,
            content_type="application/json",
            payload=hint,
        ))
        
        return sources, attachments, warnings
    
    def _build_hint(self, req: ContextRequest) -> Dict[str, Any]:
        """Build a UI state hint from the request."""
        hint: Dict[str, Any] = {
            "actor_role": req.actor.role.value,
        }
        
        # Infer view context from scope
        scope = req.scope
        
        if scope.run_id:
            hint["likely_view"] = "run_detail"
            hint["context_type"] = "run"
            hint["run_id"] = scope.run_id
        elif scope.pattern_id:
            hint["likely_view"] = "pattern_editor"
            hint["context_type"] = "design"
            hint["pattern_id"] = scope.pattern_id
        elif scope.session_id:
            hint["likely_view"] = "workflow_session"
            hint["context_type"] = "workflow"
            hint["session_id"] = scope.session_id
        elif scope.project_id:
            hint["likely_view"] = "project_overview"
            hint["context_type"] = "project"
            hint["project_id"] = scope.project_id
        else:
            hint["likely_view"] = "dashboard"
            hint["context_type"] = "general"
        
        # Infer user concern from intent
        intent_lower = req.intent.lower()
        
        if any(word in intent_lower for word in ["blocked", "error", "fail", "cannot"]):
            hint["user_concern"] = "blocker"
        elif any(word in intent_lower for word in ["how", "why", "explain", "help"]):
            hint["user_concern"] = "explanation"
        elif any(word in intent_lower for word in ["next", "step", "should", "recommend"]):
            hint["user_concern"] = "guidance"
        else:
            hint["user_concern"] = "general"
        
        return hint


# Singleton instance
ui_state_hint_provider = UIStateHintProvider()
