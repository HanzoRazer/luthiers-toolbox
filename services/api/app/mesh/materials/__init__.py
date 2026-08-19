"""
Mesh Pipeline material research namespace.

Specimen-specific evidence and structural interpretation live here.

This package is intentionally separate from ``app.materials`` (curated
tonewood / species reference registry). Mixing those concerns would blur
reference-material authority with specimen evidence.

Constitutional posture (MESH-MAT-001):
- Analyzer / tap_tone_pi emit facts via artifacts; ToolBox interprets.
- No tap_tone runtime imports.
- Outputs are RESEARCH_ONLY; no CAM / manufacturing authority.
"""

from .evidence import (
    EvidenceValue,
    MaterialEvidenceBundle,
    MeasurementReference,
    ModalEvidence,
    UncertaintyDescriptor,
    MaterialEvidenceError,
    import_material_evidence,
)
from .orthotropic import (
    IncompleteMaterialStateError,
    ModelAssumption,
    OrthotropicMaterialState,
    PlateGeometry,
)
from .predictor import (
    PredictedMode,
    PredictedPlateResponse,
    predict_plate_modes,
)
from .residuals import (
    ModeResidual,
    PredictionResidualReport,
    compare_modal_prediction,
)

__all__ = [
    "EvidenceValue",
    "MaterialEvidenceBundle",
    "MeasurementReference",
    "ModalEvidence",
    "UncertaintyDescriptor",
    "MaterialEvidenceError",
    "import_material_evidence",
    "IncompleteMaterialStateError",
    "ModelAssumption",
    "OrthotropicMaterialState",
    "PlateGeometry",
    "PredictedMode",
    "PredictedPlateResponse",
    "predict_plate_modes",
    "ModeResidual",
    "PredictionResidualReport",
    "compare_modal_prediction",
]
