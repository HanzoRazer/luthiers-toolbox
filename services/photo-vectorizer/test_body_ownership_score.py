from contour_plausibility import body_ownership_score


def test_body_ownership_score_rewards_complete_low_neck_body():
    score = body_ownership_score(
        completeness=0.90,
        border_contact=0.05,
        vertical_coverage=0.88,
        neck_inclusion=0.05,
    )
    assert score > 0.80


def test_body_ownership_score_penalizes_neck_heavy_partial_shape():
    score = body_ownership_score(
        completeness=0.52,
        border_contact=0.12,
        vertical_coverage=0.42,
        neck_inclusion=0.46,
    )
    assert score < 0.60


def test_body_ownership_score_penalizes_border_hugging_fragment():
    score = body_ownership_score(
        completeness=0.60,
        border_contact=0.55,
        vertical_coverage=0.51,
        neck_inclusion=0.08,
    )
    assert score < 0.60
