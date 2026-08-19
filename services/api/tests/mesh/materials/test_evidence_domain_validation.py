"""
Domain-validation regressions for MESH-MAT-001 evidence ingestion.

Every case here was ACCEPTED by the importer before this file existed. They are
grouped by the trap that let each one through, because the traps recur:

  * NaN defeats comparison guards   — `nan <= 0` is False, so a bare positivity
    check passes NaN through.
  * `v != v` catches NaN but not inf — the older idiom misses both infinities.
  * str/bytes are Sequences         — "12" has len 2 and coerces to (1, 2).

NaN/inf are additionally not representable in strict JSON, so accepting them
produces a sidecar that cannot validate against its own contract.
"""

import math

import pytest

from app.mesh.materials.evidence import (
    EvidenceValue,
    MaterialEvidenceError,
    ModalEvidence,
    UncertaintyDescriptor,
    _parse_modal,
)


def _value(prop: str, value: float) -> EvidenceValue:
    return EvidenceValue(
        property=prop,
        value=value,
        unit="Pa" if prop.endswith("_Pa") else "kg/m3",
        epistemic_status="observed",
        source_hash="sha256:test",
    )


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_evidence_value_rejected(bad):
    with pytest.raises(MaterialEvidenceError, match="must be finite"):
        _value("E_L_Pa", bad)


@pytest.mark.parametrize(
    "prop", ["density_kg_m3", "E_L_Pa", "E_C_Pa", "G_LC_Pa"]
)
@pytest.mark.parametrize("bad", [-1.0, 0.0])
def test_non_positive_physical_property_rejected(prop, bad):
    with pytest.raises(MaterialEvidenceError, match="strictly positive"):
        _value(prop, bad)


def test_unrecognised_property_is_not_sign_constrained():
    """
    Positivity is asserted only for the canonicalized physical names. A property
    the importer does not model must not inherit a sign convention it may not
    have (e.g. a temperature coefficient).
    """
    ev = _value("some_signed_coefficient", -3.5)
    assert ev.value == -3.5


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 0.0, -10.0])
def test_modal_frequency_must_be_finite_and_positive(bad):
    with pytest.raises(MaterialEvidenceError, match="frequency_hz"):
        ModalEvidence(frequency_hz=bad)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 0.0, -1.0])
def test_modal_q_factor_must_be_finite_and_positive(bad):
    with pytest.raises(MaterialEvidenceError, match="q_factor"):
        ModalEvidence(frequency_hz=180.0, q_factor=bad)


@pytest.mark.parametrize("field", ["std_dev", "relative"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -0.1])
def test_uncertainty_must_be_finite_and_non_negative(field, bad):
    with pytest.raises(MaterialEvidenceError, match=field):
        UncertaintyDescriptor(**{field: bad})


@pytest.mark.parametrize("bad", ["12", b"12", bytearray(b"12")])
def test_string_like_mode_indices_rejected(bad):
    """
    The trap: "12" is a Sequence of length 2, so a Sequence+len check coerced it
    to (1, 2) and invented a mode pair the artifact never asserted.
    """
    with pytest.raises(MaterialEvidenceError, match=r"\[m, n\] pair"):
        _parse_modal({"frequency_hz": 180.0, "mode_indices": bad})


@pytest.mark.parametrize("bad", [[1], [1, 2, 3], []])
def test_wrong_length_mode_indices_rejected(bad):
    with pytest.raises(MaterialEvidenceError, match=r"\[m, n\] pair"):
        _parse_modal({"frequency_hz": 180.0, "mode_indices": bad})


def test_wellformed_mode_indices_still_accepted():
    assert _parse_modal(
        {"frequency_hz": 180.0, "mode_indices": [1, 2]}
    ).mode_indices == (1, 2)


def test_accepted_evidence_is_strict_json_serializable():
    """
    Anything the importer accepts must survive strict JSON. json.dumps emits
    bare NaN/Infinity by default, which no conforming parser accepts — so a
    non-finite value that slipped through would silently detach the sidecar
    from its schema.
    """
    import json

    ev = _value("E_L_Pa", 1.2e10)
    assert math.isfinite(ev.value)
    json.dumps(ev.to_dict(), allow_nan=False)  # must not raise
