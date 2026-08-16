"""
Measured-vs-predicted modal residual reporting (MESH-MAT-001).

Does not interpret wood quality. Does not overwrite measured values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from app.governance.confidence_envelope import EpistemicStatus

from .evidence import ModalEvidence
from .predictor import PredictedPlateResponse

MatchStatus = str  # MATCHED | MISMATCHED | NO_MEASUREMENT | NO_PREDICTION


@dataclass(frozen=True)
class ModeResidual:
    predicted_frequency_hz: Optional[float]
    measured_frequency_hz: Optional[float]
    absolute_error_hz: Optional[float]
    relative_error: Optional[float]
    status: MatchStatus
    mode_indices: Optional[Tuple[int, int]] = None
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "predicted_frequency_hz": self.predicted_frequency_hz,
            "measured_frequency_hz": self.measured_frequency_hz,
            "absolute_error_hz": self.absolute_error_hz,
            "relative_error": self.relative_error,
            "status": self.status,
        }
        if self.mode_indices is not None:
            out["mode_indices"] = list(self.mode_indices)
        if self.label is not None:
            out["label"] = self.label
        return out


@dataclass(frozen=True)
class PredictionResidualReport:
    specimen_id: str
    predicted_modes: List[Dict[str, Any]]
    measured_modes: List[Dict[str, Any]]
    residuals: List[Dict[str, Any]]
    epistemic_status: str
    research_only: bool
    tolerance_hz: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_id": "prediction_residual",
            "schema_version": "1.0",
            "specimen_id": self.specimen_id,
            "predicted_modes": self.predicted_modes,
            "measured_modes": self.measured_modes,
            "residuals": self.residuals,
            "tolerance_hz": self.tolerance_hz,
            "epistemic_status": self.epistemic_status,
            "research_only": self.research_only,
        }


def _indices_key(indices: Optional[Sequence[int]]) -> Optional[Tuple[int, int]]:
    if indices is None:
        return None
    return (int(indices[0]), int(indices[1]))


def compare_modal_prediction(
    predicted: PredictedPlateResponse,
    measured: Sequence[ModalEvidence] | Sequence[Mapping[str, Any]],
    *,
    tolerance_hz: float = 1.0,
) -> PredictionResidualReport:
    """
    Compare predicted modes to measured modal evidence.

    Matching prefers mode_indices when present on both sides; otherwise
    pairs by sorted frequency order.
    """
    measured_dicts: List[Dict[str, Any]] = []
    measured_objs: List[Tuple[Optional[Tuple[int, int]], float, Optional[str]]] = []

    for item in measured:
        if isinstance(item, ModalEvidence):
            d = item.to_dict()
            measured_dicts.append(d)
            measured_objs.append((item.mode_indices, item.frequency_hz, item.label))
        else:
            d = dict(item)
            measured_dicts.append(d)
            measured_objs.append(
                (
                    _indices_key(d.get("mode_indices")),
                    float(d["frequency_hz"]),
                    d.get("label"),
                )
            )

    pred_modes = list(predicted.predicted_modes)
    residuals: List[ModeResidual] = []

    used_measured: set[int] = set()

    for pred in pred_modes:
        pred_hz = float(pred["frequency_hz"])
        pred_idx = _indices_key(pred.get("mode_indices"))

        match_i: Optional[int] = None
        if pred_idx is not None:
            for i, (m_idx, _mhz, _lab) in enumerate(measured_objs):
                if i in used_measured:
                    continue
                if m_idx == pred_idx:
                    match_i = i
                    break

        if match_i is None:
            # Fall back to nearest unused measured by frequency.
            best: Optional[Tuple[float, int]] = None
            for i, (_m_idx, mhz, _lab) in enumerate(measured_objs):
                if i in used_measured:
                    continue
                dist = abs(mhz - pred_hz)
                if best is None or dist < best[0]:
                    best = (dist, i)
            if best is not None:
                match_i = best[1]

        if match_i is None:
            residuals.append(
                ModeResidual(
                    predicted_frequency_hz=pred_hz,
                    measured_frequency_hz=None,
                    absolute_error_hz=None,
                    relative_error=None,
                    status="NO_MEASUREMENT",
                    mode_indices=pred_idx,
                )
            )
            continue

        used_measured.add(match_i)
        m_idx, mhz, label = measured_objs[match_i]
        abs_err = pred_hz - mhz
        rel = abs_err / mhz if mhz != 0 else None
        status: MatchStatus = (
            "MATCHED" if abs(abs_err) <= tolerance_hz else "MISMATCHED"
        )
        residuals.append(
            ModeResidual(
                predicted_frequency_hz=pred_hz,
                measured_frequency_hz=mhz,
                absolute_error_hz=abs_err,
                relative_error=rel,
                status=status,
                mode_indices=pred_idx or m_idx,
                label=label,
            )
        )

    # Measured modes with no prediction
    for i, (m_idx, mhz, label) in enumerate(measured_objs):
        if i in used_measured:
            continue
        residuals.append(
            ModeResidual(
                predicted_frequency_hz=None,
                measured_frequency_hz=mhz,
                absolute_error_hz=None,
                relative_error=None,
                status="NO_PREDICTION",
                mode_indices=m_idx,
                label=label,
            )
        )

    return PredictionResidualReport(
        specimen_id=predicted.specimen_id,
        predicted_modes=pred_modes,
        measured_modes=measured_dicts,
        residuals=[r.to_dict() for r in residuals],
        epistemic_status=EpistemicStatus.PREDICTED.value,
        research_only=True,
        tolerance_hz=tolerance_hz,
    )
