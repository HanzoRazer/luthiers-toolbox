"""Measured-vs-predicted residual reporting (MESH-MAT-001)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.mesh.materials.evidence import (
    MaterialEvidenceError,
    import_material_evidence,
)
from app.mesh.materials.orthotropic import OrthotropicMaterialState, PlateGeometry
from app.mesh.materials.predictor import PredictedPlateResponse, predict_plate_modes
from app.mesh.materials.residuals import compare_modal_prediction

from ._helpers import fixture, load_json


def test_residual_report_research_only():
    bundle = import_material_evidence(fixture("complete_spruce_evidence.json"))
    state = OrthotropicMaterialState.from_evidence(bundle)
    geom = PlateGeometry(**load_json(
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "materials"
        / "plate_geometry.json"
    ))
    pred = predict_plate_modes(state, geom, n_modes_return=4)
    report = compare_modal_prediction(pred, bundle.modal_evidence, tolerance_hz=50.0)
    d = report.to_dict()
    assert d["schema_id"] == "prediction_residual"
    assert d["epistemic_status"] == "predicted"
    assert d["research_only"] is True
    assert len(d["residuals"]) >= 1
    statuses = {r["status"] for r in d["residuals"]}
    assert statuses <= {"MATCHED", "MISMATCHED", "NO_MEASUREMENT", "NO_PREDICTION"}


def _response(modes):
    """Minimal PredictedPlateResponse standing in for a solver run."""
    return PredictedPlateResponse(
        model_version="test",
        specimen_id="SPEC-1",
        material_state={},
        geometry={},
        boundary_condition={"x": "simply_supported", "y": "simply_supported"},
        assumptions=[],
        predicted_modes=modes,
        epistemic_status="predicted",
        research_only=True,
    )


def test_match_basis_distinguishes_labelled_pairing_from_proximity():
    """
    A residual paired by explicit mode indices and one paired by frequency
    proximity are not equally trustworthy; the report has to say which it did.
    """
    pred = _response(
        [
            {"mode_number": 1, "frequency_hz": 100.0, "mode_indices": [1, 1]},
            {"mode_number": 2, "frequency_hz": 200.0},
        ]
    )
    report = compare_modal_prediction(
        pred,
        [
            {"frequency_hz": 101.0, "mode_indices": [1, 1]},
            {"frequency_hz": 205.0},
        ],
        tolerance_hz=10.0,
    )
    bases = [r.get("match_basis") for r in report.to_dict()["residuals"]]
    assert bases == ["mode_indices", "nearest_frequency"]


def test_index_match_is_not_stolen_by_an_earlier_proximity_guess():
    """
    Mode-index pairing runs as a first pass across ALL predictions.

    Interleaved, the unlabelled 150 Hz prediction is processed first and claims
    the 149 Hz measurement by proximity — even though that measurement is
    explicitly labelled (2,1) and belongs to the second prediction. The labelled
    pairing must win regardless of prediction order.
    """
    pred = _response(
        [
            {"mode_number": 1, "frequency_hz": 150.0},
            {"mode_number": 2, "frequency_hz": 400.0, "mode_indices": [2, 1]},
        ]
    )
    report = compare_modal_prediction(
        pred,
        [
            {"frequency_hz": 149.0, "mode_indices": [2, 1]},
            {"frequency_hz": 152.0},
        ],
        tolerance_hz=5.0,
    )
    residuals = report.to_dict()["residuals"]
    labelled = [r for r in residuals if r.get("match_basis") == "mode_indices"]
    assert len(labelled) == 1
    assert labelled[0]["predicted_frequency_hz"] == 400.0
    assert labelled[0]["measured_frequency_hz"] == 149.0
    # The unlabelled prediction falls back to what remains, not to the (2,1) peak.
    guessed = [r for r in residuals if r.get("match_basis") == "nearest_frequency"]
    assert len(guessed) == 1
    assert guessed[0]["measured_frequency_hz"] == 152.0


def test_unpaired_residuals_carry_no_match_basis():
    report = compare_modal_prediction(_response([{"frequency_hz": 100.0}]), [])
    residuals = report.to_dict()["residuals"]
    assert residuals[0]["status"] == "NO_MEASUREMENT"
    assert "match_basis" not in residuals[0]


def test_negative_tolerance_rejected():
    """A negative tolerance silently marks every pairing MISMATCHED."""
    with pytest.raises(MaterialEvidenceError, match="tolerance_hz"):
        compare_modal_prediction(
            _response([{"frequency_hz": 100.0}]),
            [{"frequency_hz": 100.0}],
            tolerance_hz=-1.0,
        )


def test_malformed_mode_indices_rejected():
    with pytest.raises(MaterialEvidenceError, match="mode_indices"):
        compare_modal_prediction(
            _response([{"frequency_hz": 100.0}]),
            [{"frequency_hz": 100.0, "mode_indices": [1]}],
        )


def test_absolute_error_hz_is_signed_not_magnitude():
    """
    `absolute_error_hz` names the UNIT basis (Hz) against `relative_error`
    (dimensionless) — it is not a magnitude. The sign is load-bearing: it says
    whether the prediction is sharp or flat of the measurement, which is the
    physically interesting direction. Pinned because the name invites an abs()
    "fix" that would destroy that information, and because `relative_error` is
    signed for the same reason.
    """
    from app.mesh.materials.residuals import _paired_residual

    flat = _paired_residual(170.0, (1, 1), ((1, 1), 180.0, None), "mode_indices", 1.0)
    assert flat.absolute_error_hz == pytest.approx(-10.0)
    assert flat.relative_error is not None and flat.relative_error < 0

    sharp = _paired_residual(190.0, (1, 1), ((1, 1), 180.0, None), "mode_indices", 1.0)
    assert sharp.absolute_error_hz == pytest.approx(10.0)
    assert sharp.relative_error is not None and sharp.relative_error > 0

    # status uses magnitude explicitly, so both directions are MISMATCHED here
    assert flat.status == "MISMATCHED" and sharp.status == "MISMATCHED"


def test_boundary_condition_name_error_is_input_validation_not_incompleteness():
    """
    A bad boundary-condition name is a caller mistake, not an incomplete
    material state. IncompleteMaterialStateError subclasses
    MaterialEvidenceError, so this distinction is only observable by asserting
    the narrower type is NOT raised.
    """
    from app.mesh.materials.evidence import MaterialEvidenceError
    from app.mesh.materials.orthotropic import IncompleteMaterialStateError
    from app.mesh.materials.predictor import _parse_bc

    with pytest.raises(MaterialEvidenceError) as exc:
        _parse_bc("hinged_on_tuesdays")
    assert not isinstance(exc.value, IncompleteMaterialStateError)

    # supported names still resolve, including the hyphen spelling
    assert _parse_bc("simply-supported") is _parse_bc("simply_supported")
