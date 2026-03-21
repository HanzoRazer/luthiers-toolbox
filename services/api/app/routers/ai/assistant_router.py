"""Assistant Router (Session D-1) — Luthier's Book Compendium

Backend for AssistantView.vue with lutherie-grounded system prompt.
D-2 (build_context_packet) and D-3 (get_lutherie_prompt) are wired on the chat path.

Endpoints:
    POST /api/ai/assistant/chat   — Send message, get AI response
    GET  /api/ai/assistant/history — Retrieve conversation history

Uses in-memory storage (dict keyed by session_id). SQLite persistence TBD.

Session D-1 / D-2 / D-3: Every chat request wires ``build_context_packet`` (D-2) and
``get_lutherie_prompt`` (D-3) with the assistant route (D-1) so each reply is grounded
with optional project context and the lutherie system prompt.
"""

# Chat pipeline (high level):
#   D-3 get_lutherie_prompt — system prompt / compendium grounding
#   D-2 build_context_packet — optional project + materials context
#   LLM — request_text with assembled user prompt + system prompt

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...auth.deps import get_optional_principal
from ...auth.principal import Principal
from ...ai.transport.llm_client import get_llm_client, LLMClientError
from ...ai.context_retrieval import build_context_packet
from ...ai.lutherie_system_prompt import get_lutherie_prompt

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ai/assistant",
    tags=["AI Assistant", "Compendium"],
)


# =============================================================================
# IN-MEMORY CONVERSATION STORAGE
# =============================================================================

# session_id -> List[{role, content, timestamp}]
_conversation_store: Dict[str, List[Dict[str, Any]]] = {}


def _get_session_history(session_id: str) -> List[Dict[str, Any]]:
    """Get or create conversation history for a session."""
    if session_id not in _conversation_store:
        _conversation_store[session_id] = []
    return _conversation_store[session_id]


def _add_message(session_id: str, role: str, content: str) -> Dict[str, Any]:
    """Add a message to the conversation history."""
    history = _get_session_history(session_id)
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    history.append(message)
    return message


# System prompt loaded from app.ai.lutherie_system_prompt (D-3)
# Context retrieval loaded from app.ai.context_retrieval (D-2)


# =============================================================================
# SCHEMAS
# =============================================================================


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    session_id: str = Field(..., description="Session identifier for conversation continuity")
    project_id: Optional[str] = Field(
        None,
        description="When set, project context is assembled via build_context_packet for the chat prompt.",
    )


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    session_id: str
    project_id: Optional[str] = Field(
        None,
        description="Echo of request project_id when provided (debugging).",
    )


class HistoryMessage(BaseModel):
    """Single message in conversation history."""
    role: str
    content: str
    timestamp: str


class HistoryResponse(BaseModel):
    """Response from history endpoint."""
    session_id: str
    messages: List[HistoryMessage]
    count: int


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    principal: Optional[Principal] = Depends(get_optional_principal),
) -> ChatResponse:
    """
    Send a message to the luthier assistant.

    D-3 lutherie system prompt + D-2 context retrieval on every chat request.
    Project context is assembled via ``build_context_packet`` when ``project_id`` is set;
    authentication is required for project-scoped context and project rows are limited to the owner.
    """
    session_id = request.session_id
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if request.project_id:
        logger.info(
            "Assistant chat D-4: project_id=%r (build_context_packet + get_lutherie_prompt)",
            request.project_id,
        )

    if request.project_id and not principal:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to attach project context (project_id).",
        )

    owner_user_id: Optional[str] = str(principal.user_id) if principal else None

    # Add user message to history
    _add_message(session_id, "user", user_message)

    # Build conversation context from history (last 10 messages)
    history = _get_session_history(session_id)
    recent_history = history[-10:]  # Keep context window manageable

    # Format conversation for LLM
    conversation_context = ""
    for msg in recent_history[:-1]:  # Exclude current message (already in prompt)
        role_label = "User" if msg["role"] == "user" else "Assistant"
        conversation_context += f"{role_label}: {msg['content']}\n\n"

    # Build full prompt
    if conversation_context:
        full_prompt = f"Previous conversation:\n{conversation_context}\nUser: {user_message}"
    else:
        full_prompt = user_message

    # D-2: context packet (project.data.spec, materials, instrument registry)
    context_packet = build_context_packet(
        message=user_message,
        project_id=request.project_id,
        owner_user_id=owner_user_id,
    )
    if context_packet:
        full_prompt = f"--- Context ---\n{context_packet}\n--- End Context ---\n\n{full_prompt}"

    # D-3 system prompt + optional project acknowledgement hint
    system_prompt = get_lutherie_prompt()
    if context_packet and "## Project Data" in context_packet:
        system_prompt += (
            "\n\n## Active project (session)\n"
            "The user has an active Production Shop project in Context. Open with a brief "
            "acknowledgement (instrument type, scale, notable woods) when relevant — then answer."
        )

    try:
        # Use Anthropic by default for better reasoning
        client = get_llm_client("anthropic")

        if not client.is_configured:
            # Fallback to OpenAI if Anthropic not configured
            client = get_llm_client("openai")

        if not client.is_configured:
            raise HTTPException(
                status_code=503,
                detail="AI service not configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
            )

        response = client.request_text(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2048,
        )

        assistant_response = response.content.strip()

        # Add assistant response to history
        _add_message(session_id, "assistant", assistant_response)

        logger.info(
            f"Assistant chat: session={session_id[:8]}..., "
            f"tokens={response.total_tokens}, model={response.model}, "
            f"proj={request.project_id[:8] if request.project_id else 'none'}"
        )

        return ChatResponse(
            response=assistant_response,
            session_id=session_id,
            project_id=request.project_id,
        )

    except LLMClientError as e:
        logger.error(f"LLM client error: {e}")
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    session_id: str = Query(..., description="Session identifier"),
    limit: int = Query(20, ge=1, le=100, description="Maximum messages to return"),
) -> HistoryResponse:
    """
    Retrieve conversation history for a session.

    Returns the most recent messages up to the specified limit.
    """
    history = _get_session_history(session_id)
    recent = history[-limit:] if len(history) > limit else history

    messages = [
        HistoryMessage(
            role=msg["role"],
            content=msg["content"],
            timestamp=msg["timestamp"],
        )
        for msg in recent
    ]

    return HistoryResponse(
        session_id=session_id,
        messages=messages,
        count=len(messages),
    )


@router.delete("/history")
async def clear_history(
    session_id: str = Query(..., description="Session identifier"),
) -> Dict[str, Any]:
    """
    Clear conversation history for a session.

    Returns the number of messages cleared.
    """
    history = _get_session_history(session_id)
    count = len(history)
    history.clear()

    return {
        "ok": True,
        "session_id": session_id,
        "messages_cleared": count,
    }


@router.get("/status")
async def assistant_status() -> Dict[str, Any]:
    """
    Get assistant service status.

    Checks if AI providers are configured and accessible.
    """
    anthropic_configured = False
    openai_configured = False

    try:
        anthropic_client = get_llm_client("anthropic")
        anthropic_configured = anthropic_client.is_configured
    except Exception:
        pass

    try:
        openai_client = get_llm_client("openai")
        openai_configured = openai_client.is_configured
    except Exception:
        pass

    return {
        "ok": anthropic_configured or openai_configured,
        "providers": {
            "anthropic": {"configured": anthropic_configured},
            "openai": {"configured": openai_configured},
        },
        "active_sessions": len(_conversation_store),
        "system_prompt_length": len(get_lutherie_prompt()),
    }


__all__ = ["router"]
