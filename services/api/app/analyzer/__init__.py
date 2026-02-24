"""
Analyzer Module — Acoustic Interpretation Layer

ARCHITECTURAL BOUNDARY:
    This module INTERPRETS measurement data. It does NOT measure.

    tap_tone_pi asks:  "What frequencies are present?"
    This module asks:  "What does that mean for this build?"

ALLOWED IMPORTS:
    - app.core.*           (shared types, math)
    - app.calculators.*    (domain calculations)

FORBIDDEN IMPORTS:
    - app.cam.*            (CAM has no business here)
    - app.rmos.*           (RMOS consumes us, we don't consume it)
    - app.saw_lab.*        (production, not analysis)
    - tap_tone_pi.*        (HARD BOUNDARY - we consume viewer_pack only)

INPUT CONTRACT:
    viewer_pack_v1.json from tap_tone_pi

OUTPUT:
    Interpretation, visualization data, design recommendations

See: docs/ANALYZER_BOUNDARY_SPEC.md
"""

from .viewer_pack_loader import load_viewer_pack, ViewerPack
from .spectrum_service import SpectrumService
from .modal_visualizer import ModalVisualizerService
from .design_advisor import DesignAdvisorService

__all__ = [
    "load_viewer_pack",
    "ViewerPack",
    "SpectrumService",
    "ModalVisualizerService",
    "DesignAdvisorService",
]
