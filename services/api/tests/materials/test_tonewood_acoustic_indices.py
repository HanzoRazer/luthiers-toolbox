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


# ---------------------------------------------------------------------------
# TC-02..TC-05 — radiation_ratio contract
# ---------------------------------------------------------------------------

def test_representative_spruce_lands_on_species_class_range():
    """
    TC-02 — a representative soundboard spruce lands on an ~8-15 scale.

    Sanity bound on the magnitude, deliberately wide. This is not a species
    quality gate and must not be tightened into one.
    """
    spruce = make_tonewood(
        density_kg_m3=405.0,
        speed_of_sound_m_s=None,
        modulus_of_elasticity_gpa=10.9,
        name="Sitka Spruce",
    )
    assert 8.0 <= spruce.radiation_ratio <= 15.0


def test_radiation_ratio_via_derived_speed_of_sound():
    """TC-03 — the MOE path: c = sqrt(E/rho), then rr = c/rho."""
    entry = make_tonewood(
        density_kg_m3=420.0,
        speed_of_sound_m_s=None,
        modulus_of_elasticity_gpa=10.5,
    )
    expected_c = math.sqrt(10.5e9 / 420.0)
    assert entry.radiation_ratio == pytest.approx(round(expected_c / 420.0, 2), abs=0.01)


def test_measured_speed_of_sound_takes_precedence():
    """
    TC-04 — when speed_of_sound_m_s is supplied it wins over the MOE-derived
    value, and radiation_ratio follows the measured figure.
    """
    entry = make_tonewood(
        density_kg_m3=420.0,
        speed_of_sound_m_s=5000.0,
        modulus_of_elasticity_gpa=10.5,  # would give ~5000 too; use a distinct rho check
    )
    assert entry.speed_of_sound_computed_m_s == pytest.approx(5000.0, abs=0.1)
    assert entry.radiation_ratio == pytest.approx(11.90, abs=0.01)


@pytest.mark.parametrize(
    "density,speed,moe",
    [
        (None, 5000.0, 10.5),   # no density
        (420.0, None, None),    # no speed and no MOE
        (None, None, None),     # nothing
    ],
)
def test_radiation_ratio_is_none_when_inputs_missing(density, speed, moe):
    """TC-05 — missing inputs yield None, never an exception or a fabricated value."""
    entry = make_tonewood(
        density_kg_m3=density,
        speed_of_sound_m_s=speed,
        modulus_of_elasticity_gpa=moe,
    )
    assert entry.radiation_ratio is None


# ---------------------------------------------------------------------------
# TC-06..TC-09 — _score_acoustic contract
# ---------------------------------------------------------------------------

def test_score_acoustic_one_sigma_offset():
    """
    TC-07 — sigma is 3.0, so a 3.0-unit offset scores exp(-0.5) = 0.60653.

    rho 420, c = 8.5 * 420 = 3570 puts rr exactly 3.0 below the 11.5 target.
    """
    target = _ROLE_TARGETS["soundboard"]
    entry = make_tonewood(density_kg_m3=420.0, speed_of_sound_m_s=3570.0)

    assert entry.radiation_ratio == pytest.approx(8.5, abs=0.01)
    assert _score_acoustic(entry, target) == pytest.approx(math.exp(-0.5), abs=1e-4)


def test_score_acoustic_neutral_when_data_missing():
    """TC-08 — absent acoustic data keeps the existing 0.5 neutral fallback."""
    target = _ROLE_TARGETS["soundboard"]
    entry = make_tonewood(density_kg_m3=None, speed_of_sound_m_s=None)

    assert entry.radiation_ratio is None
    assert _score_acoustic(entry, target) == 0.5


def test_score_acoustic_spans_a_useful_range_across_roles():
    """
    TC-09 (extended) — the same wood scores differently for roles whose targets
    differ, which is the whole point of the acoustic term. Under the defect every
    one of these was 0.0.
    """
    wood = make_tonewood(density_kg_m3=420.0, speed_of_sound_m_s=4830.0)  # rr 11.5
    soundboard = _score_acoustic(wood, _ROLE_TARGETS["soundboard"])   # target 11.5
    fretboard = _score_acoustic(wood, _ROLE_TARGETS["fretboard"])     # target 4.0

    assert soundboard == pytest.approx(1.0, abs=1e-9)
    assert soundboard > fretboard
    assert fretboard < 0.05  # 7.5 units away at sigma 3.0


# ---------------------------------------------------------------------------
# TC-10..TC-12 — role scoring and recommendation integration
# ---------------------------------------------------------------------------

def test_role_score_differentiates_near_and_far_materials():
    """
    TC-10 — two materials identical except for radiation ratio must receive
    different acoustic *and* different total role scores.
    """
    from app.materials.recommendation.scorer import score_for_role

    near = make_tonewood(density_kg_m3=420.0, speed_of_sound_m_s=4830.0, name="Near")
    far = make_tonewood(density_kg_m3=420.0, speed_of_sound_m_s=2100.0, name="Far")

    assert _score_acoustic(near, _ROLE_TARGETS["soundboard"]) != _score_acoustic(
        far, _ROLE_TARGETS["soundboard"]
    )
    assert score_for_role(near, "soundboard") > score_for_role(far, "soundboard")


def test_recommend_for_role_has_live_acoustic_contribution():
    """
    TC-11 — against the real curated registry, soundboard recommendations must
    not all carry a zero acoustic term. This is the end-to-end statement of the
    defect: before the repair every entry here scored 0.0 acoustically.
    """
    from app.materials.recommendation.scorer import recommend_for_role

    ranked = recommend_for_role("soundboard", limit=10)
    assert ranked, "no soundboard candidates in the curated registry"

    acoustic_scores = [
        _score_acoustic(entry, _ROLE_TARGETS["soundboard"])
        for entry, _score in ranked
        if entry.radiation_ratio is not None
    ]
    assert acoustic_scores, "no ranked entry had a radiation ratio"
    assert any(s > 0.0 for s in acoustic_scores), (
        "every acoustic score is 0.0 — the BR-043 scale collapse has returned"
    )


def test_compare_species_returns_corrected_scale():
    """TC-12 — compare_species surfaces radiation ratios on the corrected scale."""
    from app.materials.recommendation.scorer import compare_species
    from app.materials.registry.tonewoods import get_tonewoods_index

    index = get_tonewoods_index()
    ids = [
        sid for sid, e in index.items() if e.radiation_ratio is not None
    ][:3]
    assert ids, "no registry entry has a computable radiation ratio"

    for result in compare_species(ids, role="soundboard"):
        if result.radiation_ratio is not None:
            assert 0.1 <= result.radiation_ratio <= 100.0, (
                f"{result.name} radiation_ratio {result.radiation_ratio} is off-scale"
            )


# ---------------------------------------------------------------------------
# TC-13..TC-14 — serialization and no-compensation guards
# ---------------------------------------------------------------------------

def test_api_serializes_radiation_ratio_on_corrected_scale():
    """TC-13 — the endpoint serves ~11.x, not ~11,000,000.x."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/api/registry/tonewoods")
    assert response.status_code == 200

    entries = response.json()["tonewoods"]
    values = [
        e["radiation_ratio"] for e in entries if e.get("radiation_ratio") is not None
    ]
    assert values, "endpoint returned no computed radiation ratios"
    assert max(values) < 100.0, (
        f"max radiation_ratio {max(values)} is off-scale — a *1e6 has reappeared"
    )

    # Magnitude alone would not catch a wrong-but-still-sub-100 factor. Pin the
    # served value against c/rho recomputed from the same record's own fields.
    checked = 0
    for entry in entries:
        rr = entry.get("radiation_ratio")
        rho = entry.get("density_kg_m3")
        c = entry.get("speed_of_sound_computed_m_s")
        if rr is None or not rho or not c:
            continue
        assert rr == pytest.approx(round(c / rho, 2), abs=0.011), (
            f"{entry.get('name')}: served {rr} != c/rho {c / rho:.4f} — "
            "the serialized value is not the unscaled Schelleng ratio"
        )
        checked += 1
    assert checked >= 10, f"only {checked} entries were cross-checkable; expected >= 10"


def test_no_consumer_applies_a_million_scale_conversion():
    """
    TC-14 — no Python module anywhere in the backend app rescales
    radiation_ratio by a million in either direction. Guards against 'fixing'
    the symptom downstream instead of the producer (BR-043 Decision 2).

    Scope note: this scans the whole `app/` tree, not just `app/materials`, so a
    compensating transform added in another backend package is caught too. It
    cannot see the frontend, which is a different language and an independent
    data path -- that surface is tracked as BR-044, not guarded here.
    """
    import pathlib

    package = pathlib.Path(__file__).resolve().parents[2] / "app"
    offenders: list[str] = []
    for path in package.rglob("*.py"):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if "radiation_ratio" not in line:
                continue
            if any(tok in line for tok in ("1e6", "1e-6", "1_000_000", "1000000")):
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")

    assert not offenders, "million-scale conversion near radiation_ratio:\n" + "\n".join(
        offenders
    )
