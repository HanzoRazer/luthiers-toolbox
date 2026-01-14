# services/api/app/art_studio/services/design_first_workflow_service.py
"""
Design-First Workflow Service (Bundle 32.7.0)

Business logic for design-first workflow sessions.
Handles state transitions and promotion intent generation.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

# Conditional imports
try:
    from app.art_studio.schemas.workflow_design_first import (
        DesignFirstEvent,
        DesignFirstMode,
        DesignFirstSession,
        DesignFirstState,
        PromotionIntent,
    )
    from app.art_studio.stores.design_first_workflow_store import (
        load_session,
        save_session,
    )
except ImportError:
    from art_studio.schemas.workflow_design_first import (
        DesignFirstEvent,
        DesignFirstMode,
        DesignFirstSession,
        DesignFirstState,
        PromotionIntent,
    )
    from art_studio.stores.design_first_workflow_store import (
        load_session,
        save_session,
    )


# Valid state transitions for Design-First workflow
ALLOWED_TRANSITIONS = {
    DesignFirstState.DRAFT: {DesignFirstState.IN_REVIEW},
    DesignFirstState.IN_REVIEW: {
        DesignFirstState.APPROVED,
        DesignFirstState.REJECTED,
        DesignFirstState.DRAFT,
    },
    DesignFirstState.REJECTED: {DesignFirstState.DRAFT},
    DesignFirstState.APPROVED: {DesignFirstState.DRAFT},  # allow reopening design
}


def start_session(
    *,
    mode: DesignFirstMode,
    design,
    feasibility,
) -> DesignFirstSession:
    """Create a new design-first workflow session."""
    sid = uuid4().hex
    sess = DesignFirstSession(
        session_id=sid,
        mode=mode,
        state=DesignFirstState.DRAFT,
        design=design,
        feasibility=feasibility,
        history=[],
    )
    save_session(sess)
    return sess


def get_session(session_id: str) -> DesignFirstSession:
    """Get session by ID. Raises KeyError if not found."""
    sess = load_session(session_id)
    if not sess:
        raise KeyError("design_first_session_not_found")
    return sess


def transition_session(
    *,
    session_id: str,
    to_state: DesignFirstState,
    actor: str,
    note: str | None,
    design=None,
    feasibility=None,
) -> DesignFirstSession:
    """
    Transition session to a new state.
    
    Validates transition is allowed and records event in history.
    """
    sess = get_session(session_id)

    from_state = sess.state
    if from_state == to_state:
        # No-op if already in target state
        return sess

    # Validate transition
    allowed = ALLOWED_TRANSITIONS.get(from_state, set())
    if to_state not in allowed:
        raise ValueError(f"invalid_transition: {from_state.value} -> {to_state.value}")

    # Update design/feasibility if provided
    if design is not None:
        sess.design = design
    if feasibility is not None:
        sess.feasibility = feasibility

    # Record transition
    sess.state = to_state
    sess.history.append(
        DesignFirstEvent(
            actor=actor,
            action="transition",
            from_state=from_state,
            to_state=to_state,
            note=note,
        )
    )
    sess.updated_at = datetime.utcnow()
    save_session(sess)
    return sess


def build_promotion_intent(session_id: str) -> PromotionIntent:
    """
    Build a CAM handoff intent payload.
    
    IMPORTANT: This does NOT execute CAM. It only produces an intent
    payload that downstream CAM/RMOS lanes may consume.
    
    Raises PermissionError if session is not approved.
    """
    sess = get_session(session_id)
    if sess.state != DesignFirstState.APPROVED:
        raise PermissionError("workflow_not_approved")

    return PromotionIntent(
        session_id=sess.session_id,
        mode=sess.mode,
        approved_at=datetime.utcnow(),
        design=sess.design,
        feasibility=sess.feasibility,
    )
