from types import SimpleNamespace

from contour_election import elect_body_contour_with_ownership


def _candidate(total_score, ownership_score):
    return SimpleNamespace(
        total_score=total_score,
        ownership_score=ownership_score,
        diagnostics={},
    )


def test_elect_body_contour_rejects_high_score_non_owner():
    bad = _candidate(total_score=0.95, ownership_score=0.42)
    good = _candidate(total_score=0.81, ownership_score=0.79)

    winner = elect_body_contour_with_ownership([bad, good], ownership_threshold=0.60)

    assert winner is good
    assert bad.diagnostics["rejected_by_body_ownership_gate"] is True


def test_elect_body_contour_marks_manual_review_when_no_candidate_owns_body():
    a = _candidate(total_score=0.91, ownership_score=0.41)
    b = _candidate(total_score=0.83, ownership_score=0.55)

    winner = elect_body_contour_with_ownership([a, b], ownership_threshold=0.60)

    assert winner is a
    assert winner.diagnostics["manual_review_required"] is True
    assert winner.diagnostics["body_ownership_gate_failed"] is True
