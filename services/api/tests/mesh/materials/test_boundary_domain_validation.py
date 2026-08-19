"""
Domain-validation regressions for the paths that BYPASS the evidence importer.

`evidence.py` validates values that arrive as EvidenceValue / ModalEvidence.
Three routes reach the solver without passing through it, and each had the same
class of hole:

  * `residuals._normalize_measured` dict path — `freq <= 0` alone, so NaN passed
    (every comparison against NaN is False) and produced a NaN residual reported
    as MISMATCHED rather than an error.
  * `orthotropic._override_assumptions` — caller overrides are recorded as
    assumptions without any domain check, so an unphysical value reached the
    solver wearing an "assumption" label.
  * `orthotropic.PlateGeometry` — `min(...) <= 0` has the same NaN blind spot.

Plus `_indices_key` excluded str/bytes but not bytearray, and
`gauss_legendre` accepted n_quad <= 0.
"""

import pytest

from app.calculators.plate_design.rayleigh_ritz import gauss_legendre
from app.mesh.materials.evidence import MaterialEvidenceError
from app.mesh.materials.orthotropic import PlateGeometry, _override_assumptions
from app.mesh.materials.residuals import _indices_key, _normalize_measured


# --- residuals: the dict path must match the ModalEvidence contract -----------

@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), 0.0, -1.0])
def test_measured_dict_frequency_must_be_finite_and_positive(bad):
    with pytest.raises(MaterialEvidenceError, match="frequency_hz"):
        _normalize_measured([{"frequency_hz": bad}])


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 0.0, -1.0])
def test_measured_dict_q_factor_must_be_finite_and_positive(bad):
    with pytest.raises(MaterialEvidenceError, match="q_factor"):
        _normalize_measured([{"frequency_hz": 180.0, "q_factor": bad}])


def test_valid_measured_dict_still_accepted():
    _dicts, objs = _normalize_measured(
        [{"frequency_hz": 180.0, "q_factor": 40.0, "mode_indices": [1, 1]}]
    )
    assert objs[0][1] == 180.0 and objs[0][0] == (1, 1)


def test_bytearray_mode_indices_rejected_not_read_as_byte_values():
    """
    bytearray(b"12") is a Sequence of length 2 whose elements are 49 and 50 — the
    BYTE values. Unguarded it fabricated mode indices (49, 50) rather than
    failing, which is worse than the str case because the numbers look real.
    """
    with pytest.raises(MaterialEvidenceError, match=r"\[m, n\] pair"):
        _indices_key(bytearray(b"12"))


@pytest.mark.parametrize("bad", ["12", b"12"])
def test_string_like_mode_indices_rejected_in_residuals_too(bad):
    with pytest.raises(MaterialEvidenceError, match=r"\[m, n\] pair"):
        _indices_key(bad)


# --- orthotropic: overrides bypass the evidence layer ------------------------

@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), 0.0, -1e9])
def test_g_lc_override_must_be_finite_and_positive(bad):
    with pytest.raises(MaterialEvidenceError, match="G_LC_Pa"):
        _override_assumptions(bad, None, None)


@pytest.mark.parametrize("name,idx", [("nu_LC", 1), ("nu_CL", 2)])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 2.5, -1.0, 1.0])
def test_poisson_overrides_must_be_finite_and_within_bounds(name, idx, bad):
    args = [None, None, None]
    args[idx] = bad
    with pytest.raises(MaterialEvidenceError, match=name):
        _override_assumptions(*args)


def test_physically_plausible_overrides_still_accepted():
    out = _override_assumptions(7.0e8, 0.37, 0.03)
    assert [a.value for a in out] == [7.0e8, 0.37, 0.03]
    # still recorded as assumptions, not laundered into evidence
    assert {a.name for a in out} == {"G_LC_Pa", "nu_LC", "nu_CL"}


# --- geometry ----------------------------------------------------------------

@pytest.mark.parametrize("field", ["thickness_m", "length_m", "width_m"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 0.0, -0.5])
def test_plate_geometry_dimensions_must_be_finite_and_positive(field, bad):
    kwargs = {"thickness_m": 0.003, "length_m": 0.5, "width_m": 0.2}
    kwargs[field] = bad
    with pytest.raises(MaterialEvidenceError, match=field):
        PlateGeometry(**kwargs)


def test_valid_plate_geometry_still_accepted():
    g = PlateGeometry(thickness_m=0.003, length_m=0.5, width_m=0.2)
    assert g.to_dict()["thickness_m"] == 0.003


# --- quadrature --------------------------------------------------------------

@pytest.mark.parametrize("bad", [0, -1, -32])
def test_gauss_legendre_rejects_non_positive_n_quad(bad):
    """
    np.arange(1, 0) is empty, so n_quad <= 0 built a 0x0 Jacobi matrix and
    returned a degenerate 1-point rule instead of failing — the solver would
    then integrate with a single node and report plausible-looking garbage.
    """
    with pytest.raises(ValueError, match="n_quad"):
        gauss_legendre(bad)


@pytest.mark.parametrize("bad", [2.5, "32", None, True])
def test_gauss_legendre_rejects_non_int_n_quad(bad):
    with pytest.raises((ValueError, TypeError), match="n_quad|unhashable"):
        gauss_legendre(bad)


def test_gauss_legendre_still_accepts_valid_n():
    xi, w = gauss_legendre(32)
    assert xi.shape == (32,) and w.shape == (32,)
