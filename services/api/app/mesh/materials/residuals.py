"""
Measured-vs-predicted modal residual reporting (MESH-MAT-001).

Does not interpret wood quality. Does not overwrite measured values.
"""

from __future__ import annotations

import math

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from app.governance.confidence_envelope import EpistemicStatus

from .evidence import MaterialEvidenceError, ModalEvidence
from .predictor import PredictedPlateResponse

MatchStatus = str  # MATCHED | MISMATCHED | NO_MEASUREMENT | NO_PREDICTION

# How a predicted mode was paired with a measurement.
MATCH_BASIS_INDICES = "mode_indices"
MATCH_BASIS_NEAREST = "nearest_frequency"

# (mode_indices, frequency_hz, label)
_Measured = Tuple[Optional[Tuple[int, int]], float, Optional[str]]


@dataclass(frozen=True)
class ModeResidual:
    predicted_frequency_hz: Optional[float]
    measured_frequency_hz: Optional[float]
    # Signed: predicted - measured, in Hz. See prediction_residual.schema.json.
    absolute_error_hz: Optional[float]
    relative_error: Optional[float]
    status: MatchStatus
    mode_indices: Optional[Tuple[int, int]] = None
    label: Optional[str] = None
    # Absent when there is no pairing at all (NO_MEASUREMENT / NO_PREDICTION).
    match_basis: Optional[str] = None

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
        if self.match_basis is not None:
            out["match_basis"] = self.match_basis
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
    # bytearray must be excluded alongside str/bytes: it is a Sequence of length 2
    # for b"12", and int(bytearray(b"12")[0]) is the BYTE VALUE 49 — so the pair
    # (49, 50) would be fabricated silently. evidence._parse_modal already
    # excludes all three; this is the matching guard.
    if not isinstance(indices, Sequence) or isinstance(
        indices, (str, bytes, bytearray)
    ):
        raise MaterialEvidenceError("mode_indices must be a [m, n] pair")
    if len(indices) != 2:
        raise MaterialEvidenceError(
            f"mode_indices must be a [m, n] pair, got {list(indices)!r}"
        )
    return (int(indices[0]), int(indices[1]))


def _normalize_measured(
    measured: Sequence[ModalEvidence] | Sequence[Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[_Measured]]:
    dicts: List[Dict[str, Any]] = []
    objs: List[_Measured] = []
    for item in measured:
        if isinstance(item, ModalEvidence):
            dicts.append(item.to_dict())
            objs.append((item.mode_indices, item.frequency_hz, item.label))
            continue
        d = dict(item)
        if "frequency_hz" not in d:
            raise MaterialEvidenceError("measured mode requires frequency_hz")
        freq = float(d["frequency_hz"])
        # `freq <= 0` alone lets NaN through — every comparison against NaN is
        # False. ModalEvidence.__post_init__ guards its own path with isfinite;
        # this dict path is the same contract and must agree, or a NaN reaches
        # the residual arithmetic and reports MISMATCHED instead of failing.
        if not math.isfinite(freq) or freq <= 0:
            raise MaterialEvidenceError(
                f"measured frequency_hz must be finite and positive, got {freq!r}"
            )
        q = d.get("q_factor")
        if q is not None:
            q = float(q)
            if not math.isfinite(q) or q <= 0:
                raise MaterialEvidenceError(
                    f"measured q_factor must be finite and positive, got {q!r}"
                )
        dicts.append(d)
        objs.append((_indices_key(d.get("mode_indices")), freq, d.get("label")))
    return dicts, objs


def _match_by_indices(
    predicted: Sequence[Mapping[str, Any]], measured_objs: Sequence[_Measured]
) -> Dict[int, int]:
    """
    First pass: pair every prediction that carries mode_indices with the
    measurement carrying the same indices.

    This runs across *all* predictions before any frequency matching, because a
    labelled pairing is stronger evidence than proximity. Interleaving the two
    would let an earlier prediction's nearest-frequency guess consume a
    measurement that a later prediction names explicitly — the pairing would
    then depend on prediction order rather than on the labels.
    """
    pairs: Dict[int, int] = {}
    claimed: set[int] = set()
    for p_i, pred in enumerate(predicted):
        pred_idx = _indices_key(pred.get("mode_indices"))
        if pred_idx is None:
            continue
        for m_i, (m_idx, _hz, _label) in enumerate(measured_objs):
            if m_i in claimed or m_idx != pred_idx:
                continue
            pairs[p_i] = m_i
            claimed.add(m_i)
            break
    return pairs


def _nearest_unused(
    pred_hz: float, measured_objs: Sequence[_Measured], used: set[int]
) -> Optional[int]:
    best: Optional[Tuple[float, int]] = None
    for m_i, (_m_idx, m_hz, _label) in enumerate(measured_objs):
        if m_i in used:
            continue
        dist = abs(m_hz - pred_hz)
        if best is None or dist < best[0]:
            best = (dist, m_i)
    return None if best is None else best[1]


def _paired_residual(
    pred_hz: float,
    pred_idx: Optional[Tuple[int, int]],
    measurement: _Measured,
    basis: str,
    tolerance_hz: float,
) -> ModeResidual:
    m_idx, m_hz, label = measurement
    # SIGNED, deliberately. "absolute" names the unit basis (Hz) against
    # "relative_error" (dimensionless), not magnitude — the sign carries the
    # physics: negative means the prediction is flat of the measurement.
    # Magnitude is taken explicitly below where it is actually wanted.
    signed_err = pred_hz - m_hz
    return ModeResidual(
        predicted_frequency_hz=pred_hz,
        measured_frequency_hz=m_hz,
        absolute_error_hz=signed_err,
        relative_error=signed_err / m_hz if m_hz != 0 else None,
        status="MATCHED" if abs(signed_err) <= tolerance_hz else "MISMATCHED",
        mode_indices=pred_idx or m_idx,
        label=label,
        match_basis=basis,
    )


def compare_modal_prediction(
    predicted: PredictedPlateResponse,
    measured: Sequence[ModalEvidence] | Sequence[Mapping[str, Any]],
    *,
    tolerance_hz: float = 1.0,
) -> PredictionResidualReport:
    """
    Compare predicted modes to measured modal evidence.

    Matching runs in two passes. First, every prediction carrying
    ``mode_indices`` is paired with the measurement carrying the same indices.
    Only then are the remaining predictions paired with the nearest unused
    measurement by frequency — greedily, in prediction order, which is not
    guaranteed to be the globally closest assignment.

    Each paired residual reports ``match_basis`` so a consumer can tell a
    labelled pairing from a proximity guess.
    """
    if tolerance_hz < 0:
        raise MaterialEvidenceError(
            f"tolerance_hz must be non-negative, got {tolerance_hz!r} "
            "(a negative tolerance marks every pairing MISMATCHED)"
        )

    measured_dicts, measured_objs = _normalize_measured(measured)
    pred_modes = list(predicted.predicted_modes)

    index_pairs = _match_by_indices(pred_modes, measured_objs)
    used_measured: set[int] = set(index_pairs.values())
    residuals: List[ModeResidual] = []

    for p_i, pred in enumerate(pred_modes):
        pred_hz = float(pred["frequency_hz"])
        pred_idx = _indices_key(pred.get("mode_indices"))

        match_i = index_pairs.get(p_i)
        basis = MATCH_BASIS_INDICES
        if match_i is None:
            match_i = _nearest_unused(pred_hz, measured_objs, used_measured)
            basis = MATCH_BASIS_NEAREST

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
        residuals.append(
            _paired_residual(
                pred_hz, pred_idx, measured_objs[match_i], basis, tolerance_hz
            )
        )

    for m_i, (m_idx, m_hz, label) in enumerate(measured_objs):
        if m_i in used_measured:
            continue
        residuals.append(
            ModeResidual(
                predicted_frequency_hz=None,
                measured_frequency_hz=m_hz,
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
