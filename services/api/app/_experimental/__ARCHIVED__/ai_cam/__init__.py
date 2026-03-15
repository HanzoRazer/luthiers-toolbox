"""
AI-CAM Module (Wave 11)

AI-Assisted CAM Advisor + G-Code Explainer 2.0
"""

from .models import CAMAdvisory, CAMAnalysisResult, GCodeExplanation, GCodeExplainerResult
from .advisor import CAMAdvisor
from .explain_gcode import GCodeExplainer
from .optimize import CAMOptimizer

__all__ = [
    "CAMAdvisory",
    "CAMAnalysisResult",
    "GCodeExplanation",
    "GCodeExplainerResult",
    "CAMAdvisor",
    "GCodeExplainer",
    "CAMOptimizer",
]
