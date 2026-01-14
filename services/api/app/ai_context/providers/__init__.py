"""
AI Context Adapter - Providers package
"""

from .run_summary import RunSummaryProvider, run_summary_provider
from .design_intent import DesignIntentProvider, design_intent_provider
from .governance_notes import GovernanceNotesProvider, governance_notes_provider
from .docs_excerpt import DocsExcerptProvider, docs_excerpt_provider
from .ui_state_hint import UIStateHintProvider, ui_state_hint_provider

__all__ = [
    # Classes
    "RunSummaryProvider",
    "DesignIntentProvider",
    "GovernanceNotesProvider",
    "DocsExcerptProvider",
    "UIStateHintProvider",
    # Singleton instances
    "run_summary_provider",
    "design_intent_provider",
    "governance_notes_provider",
    "docs_excerpt_provider",
    "ui_state_hint_provider",
]
