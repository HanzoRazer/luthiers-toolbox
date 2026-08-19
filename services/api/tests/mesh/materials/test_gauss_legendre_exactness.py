"""
Correctness pin for the Gauss-Legendre quadrature used by the plate solver.

`gauss_legendre` no longer calls `np.polynomial.legendre.leggauss`. That routine
performs an ndarray reduction whose default argument is the module-level
sentinel `np._NoValue`; once numpy has been re-imported mid-session the sentinel
stops being the object the C ufunc recognises and the call raises
`TypeError: float() argument must be ... not '_NoValueType'`.

The previous mitigation warmed the cache from conftest "while numpy is still
pristine". Core CI disproved that premise — the warm-up itself raised the
TypeError at conftest-import time (run 32278117183). The rule is now computed by
Golub-Welsch, which touches no reduction sentinel.

These tests pin the rule by its DEFINING property rather than by agreement with
leggauss, so they stay meaningful even if the reference implementation is
unavailable or itself broken.
"""

import numpy as np
import pytest

from app.calculators.plate_design.rayleigh_ritz import gauss_legendre


@pytest.mark.parametrize("n", [2, 3, 4, 8, 16, 32, 64])
def test_rule_integrates_polynomials_up_to_degree_2n_minus_1_exactly(n):
    """
    The defining property of an n-point Gauss-Legendre rule: it integrates every
    polynomial of degree <= 2n-1 over [-1, 1] exactly.
    """
    xi, w = gauss_legendre(n)
    for degree in range(2 * n):
        # exact integral of x**degree over [-1, 1]
        expected = 0.0 if degree % 2 else 2.0 / (degree + 1)
        assert float(np.sum(w * xi**degree)) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("n", [2, 8, 32])
def test_weights_sum_to_interval_measure(n):
    xi, w = gauss_legendre(n)
    assert float(np.sum(w)) == pytest.approx(2.0, abs=1e-12)
    assert np.all(w > 0), "Gauss-Legendre weights are strictly positive"


@pytest.mark.parametrize("n", [2, 8, 32])
def test_nodes_are_sorted_inside_the_open_interval_and_symmetric(n):
    xi, w = gauss_legendre(n)
    assert np.all(np.diff(xi) > 0), "nodes must be ascending"
    assert np.all(np.abs(xi) < 1.0), "nodes lie strictly inside (-1, 1)"
    # the rule is symmetric about 0
    assert xi == pytest.approx(-xi[::-1], abs=1e-12)
    assert w == pytest.approx(w[::-1], abs=1e-12)


def test_returned_arrays_are_shared_and_read_only():
    """Memoized arrays are shared between callers, so mutation must be blocked."""
    xi1, w1 = gauss_legendre(16)
    xi2, w2 = gauss_legendre(16)
    assert xi1 is xi2 and w1 is w2, "expected the lru_cache to return the same objects"
    assert not xi1.flags.writeable and not w1.flags.writeable
    with pytest.raises(ValueError):
        xi1[0] = 0.0


def test_agrees_with_numpy_reference_when_that_reference_is_usable():
    """
    Cross-check against leggauss. Skipped rather than failed if the reference is
    itself broken by the numpy sentinel issue — that is the exact condition this
    module exists to be independent of.
    """
    try:
        ref_xi, ref_w = np.polynomial.legendre.leggauss(32)
    except TypeError as exc:  # pragma: no cover - only under a tainted numpy
        pytest.skip(f"numpy reference unusable in this session: {exc!r}")
    xi, w = gauss_legendre(32)
    assert xi == pytest.approx(ref_xi, abs=1e-13)
    assert w == pytest.approx(ref_w, abs=1e-13)
