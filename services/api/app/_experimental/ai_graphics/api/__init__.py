"""
AI Graphics API Routes

Provides FastAPI routers for:
- ai_routes: Main AI suggestion endpoints
- session_routes: Session management endpoints
"""

from .ai_routes import router as ai_graphics_router
from .session_routes import router as ai_session_router

__all__ = ["ai_graphics_router", "ai_session_router"]
