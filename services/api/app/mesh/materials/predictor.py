"""
Bounded orthotropic plate prediction (MESH-MAT-001).

Wraps ``solve_rayleigh_ritz`` / ``OrthotropicPlate`` with explicit
assumptions. No ``inverse_solver`` imports. No thickness recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.calculators.plate_design.rayleigh_ritz import (
    BoundaryCondition,
    solve_rayleigh_ritz,
)
from app.governance.confidence_envelope import EpistemicStatus

from .orthotropic import (
    IncompleteMaterialStateError,
    OrthotropicMaterialState,
    PlateGeometry,
)

MODEL_VERSION = "mesh-mat-001-rayleigh-ritz-v1"


@dataclass(frozen=True)
class PredictedMode:
    mode_number: int
    frequency_hz: float
    mode_indices: Tuple[int, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_number": self.mode_number,
            "frequency_hz": self.frequency_hz,
            "mode_indices": list(self.mode_indices),
        }


@dataclass(frozen=True)
class PredictedPlateResponse:
    model_version: str
    specimen_id: str
    material_state: Dict[str, Any]
    geometry: Dict[str, Any]
    boundary_condition: Dict[str, str]
    assumptions: List[Dict[str, Any]]
    predicted_modes: List[Dict[str, Any]]
    epistemic_status: str
    research_only: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_id": "material_prediction",
            "schema_version": "1.0",
            "model_version": self.model_version,
            "specimen_id": self.specimen_id,
            "material_state": self.material_state,
            "geometry": self.geometry,
            "boundary_condition": self.boundary_condition,
            "assumptions": self.assumptions,
            "predicted_modes": self.predicted_modes,
            "epistemic_status": self.epistemic_status,
            "research_only": self.research_only,
        }


def _parse_bc(name: str) -> BoundaryCondition:
    key = name.strip().lower().replace("-", "_")
    mapping = {
        "simply_supported": BoundaryCondition.SIMPLY_SUPPORTED,
        "clamped": BoundaryCondition.CLAMPED,
        "free": BoundaryCondition.FREE,
    }
    if key not in mapping:
        raise IncompleteMaterialStateError(f"Unsupported boundary condition {name!r}")
    return mapping[key]


def predict_plate_modes(
    material: OrthotropicMaterialState,
    geometry: PlateGeometry,
    *,
    boundary_condition: str = "simply_supported",
    n_modes_return: int = 6,
    n_modes_x: int = 3,
    n_modes_y: int = 3,
) -> PredictedPlateResponse:
    """
    Predict plate modes using Rayleigh–Ritz orthotropic solver.

    Requires complete material state (including E_C). Fail closed otherwise.
    """
    if not material.is_complete_for_prediction:
        raise IncompleteMaterialStateError(
            "predict_plate_modes requires E_C; missing cross-grain stiffness "
            "cannot be silently assumed"
        )

    bc = _parse_bc(boundary_condition)
    plate = material.to_orthotropic_plate(geometry)
    result = solve_rayleigh_ritz(
        plate,
        n_modes_x=n_modes_x,
        n_modes_y=n_modes_y,
        bc_x=bc,
        bc_y=bc,
        n_modes_return=n_modes_return,
    )

    modes: List[PredictedMode] = []
    for mode in result.modes[:n_modes_return]:
        modes.append(
            PredictedMode(
                mode_number=mode.mode_number,
                frequency_hz=float(mode.frequency_Hz),
                mode_indices=(int(mode.mode_indices[0]), int(mode.mode_indices[1])),
            )
        )

    # Deterministic sort by frequency then mode number.
    modes_sorted = sorted(modes, key=lambda m: (m.frequency_hz, m.mode_number))

    return PredictedPlateResponse(
        model_version=MODEL_VERSION,
        specimen_id=material.specimen_id,
        material_state=material.to_dict(),
        geometry=geometry.to_dict(),
        boundary_condition={"x": bc.value, "y": bc.value},
        assumptions=[a.to_dict() for a in material.assumptions],
        predicted_modes=[m.to_dict() for m in modes_sorted],
        epistemic_status=EpistemicStatus.PREDICTED.value,
        research_only=True,
    )
