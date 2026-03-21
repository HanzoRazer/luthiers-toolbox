"""AI Routers Package - The Production Shop

Assistant, recommendations, defect detection, and wood grading endpoints.
"""

from .assistant_router import router as assistant_router

__all__ = ["assistant_router"]
