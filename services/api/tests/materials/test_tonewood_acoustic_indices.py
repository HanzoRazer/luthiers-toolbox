"""
BR-043 — Tonewood acoustic index unit repair.

Defect proof. These tests assert the *intended* radiation-ratio scale — the one
already declared by three independent places in this repository:

  1. ``TonewoodEntry.radiation_ratio``'s own docstring
     ("Adirondack spruce ~11.7, Sitka ~11.4");
  2. ``_ROLE_TARGETS`` in the recommendation scorer (soundboard 11.5, bracing
     12.0, back_sides 8.0, fretboard 4.0);
  3. ``materials/router.py`` documentation ("Schelleng c/rho").

The shipped implementation returns ``(c / rho) * 1e6`` instead, which is larger
than every one of those references by six orders of magnitude. Because
``_score_acoustic`` compares the returned value directly against the targets
through a Gaussian with ``sigma = 3.0`` and applies no inverse scaling, every
acoustically-populated species scores 0.0 for every role.

Commit 1 of BR-043 landed these as ``xfail(strict=True)`` so the defect was
proven before production behavior changed. Commit 2 removed the spurious factor
and these markers; the assertions now hold and stand as scale regression guards.

See: docs/remediation/REPOSITORY_DEFECT_REGISTER.md · BR-043
"""

import math

import pytest

from app.materials.recommendation.scorer import _ROLE_TARGETS, _score_acoustic
from app.materials.schemas import TonewoodEntry


def make_tonewood(
    *,
    density_kg_m3: float | None = 420.0,
    speed_of_sound_m_s: float | None = 5000.0,
    modulus_of_elasticity_gpa: float | None = None,
    name: str = "Test Spruce",
) -> TonewoodEntry:
    """Minimal TonewoodEntry for index arithmetic. Only id/name are required."""
    return TonewoodEntry(
        id=name.lower().replace(" ", "_"),
        name=name,
        density_kg_m3=density_kg_m3,
        speed_of_sound_m_s=speed_of_sound_m_s,
        modulus_of_elasticity_gpa=modulus_of_elasticity_gpa,
    )


# ---------------------------------------------------------------------------
# The defect, stated as arithmetic
# ---------------------------------------------------------------------------

def test_radiation_ratio_uses_declared_reference_scale():
    """
    TC-01 — c = 5000 m/s, rho = 420 kg/m3 gives c/rho = 11.90 m^4/(kg*s).

    This is the scale the docstring's own reference species are quoted on and
    the scale ``_ROLE_TARGETS`` compares against.
    """
    entry = make_tonewood(density_kg_m3=420.0, speed_of_sound_m_s=5000.0)
    assert entry.radiation_ratio == pytest.approx(11.90, abs=0.01)


def test_score_acoustic_is_not_collapsed_at_role_target():
    """
    A species sitting exactly on the soundboard target must score ~1.0.

    ``_score_acoustic`` is ``exp(-0.5 * ((rr - target) / 3.0) ** 2)``. With the
    shipped scale the exponent is astronomically negative, so the function
    returns 0.0 for every real wood in every role — acoustic suitability is
    silently dead across the whole recommender.
    """
    target = _ROLE_TARGETS["soundboard"]
    # c/rho == 11.5 exactly: rho 420, c = 11.5 * 420 = 4830 m/s.
    on_target = make_tonewood(density_kg_m3=420.0, speed_of_sound_m_s=4830.0)

    assert on_target.radiation_ratio == pytest.approx(target["radiation_ratio"], abs=0.01)
    assert _score_acoustic(on_target, target) == pytest.approx(1.0, abs=1e-9)


def test_score_acoustic_differentiates_near_from_far():
    """
    Ordering test, not a species-quality claim: a wood nearer the role target
    must outscore one further away. Under the defect both return exactly 0.0,
    so the recommender cannot distinguish them.
    """
    target = _ROLE_TARGETS["soundboard"]
    near = make_tonewood(density_kg_m3=420.0, speed_of_sound_m_s=4830.0, name="Near")
    far = make_tonewood(density_kg_m3=800.0, speed_of_sound_m_s=4000.0, name="Far")

    assert _score_acoustic(near, target) > _score_acoustic(far, target)


# ---------------------------------------------------------------------------
# Characterisation — these pass on the defective code and document why.
# They are retained after the repair as scale regression guards.
# ---------------------------------------------------------------------------

def test_speed_of_sound_is_not_implicated():
    """
    ``speed_of_sound_computed_m_s`` is correct and must not be touched by this
    repair: c = sqrt(E/rho) with E in Pa. Pinning it isolates the defect to the
    radiation-ratio expression alone.
    """
    entry = make_tonewood(
        density_kg_m3=420.0,
        speed_of_sound_m_s=None,
        modulus_of_elasticity_gpa=10.5,
    )
    expected = math.sqrt(10.5e9 / 420.0)
    assert entry.speed_of_sound_computed_m_s == pytest.approx(expected, abs=0.1)


def test_role_targets_are_all_on_the_si_scale():
    """
    Every role target is a single- or double-digit value, i.e. the c/rho scale.
    If this ever fails, the targets moved and BR-043's premise needs re-checking
    before the producer is changed.
    """
    for role, target in _ROLE_TARGETS.items():
        rr = target["radiation_ratio"]
        assert 1.0 <= rr <= 100.0, f"{role} target {rr} is not on the c/rho scale"
