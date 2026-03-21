"""AI Routers Package - The Production Shop

Assistant, recommendations, defect detection, and wood grading endpoints.
"""

from .assistant_router import router as assistant_router
from .defect_detection_router import router as defect_detection_router

__all__ = ["assistant_router", "defect_detection_router"]
