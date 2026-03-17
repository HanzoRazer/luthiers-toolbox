from body_isolation_stage import BodyIsolationParams, RETRY_PROFILES


def test_body_region_expansion_profile_exists_in_retry_profiles():
    assert "body_region_expansion" in RETRY_PROFILES
    profile = RETRY_PROFILES["body_region_expansion"]
    assert profile["bbox_expand_ratio"] > 0.0
    assert profile["allow_vertical_growth"] is True
    assert profile["allow_lower_bout_growth"] is True


def test_body_isolation_params_has_expansion_fields():
    params = BodyIsolationParams(
        profile="body_region_expansion",
        bbox_expand_ratio=0.10,
        allow_vertical_growth=True,
        allow_lower_bout_growth=True,
    )
    assert params.bbox_expand_ratio == 0.10
    assert params.allow_vertical_growth is True
    assert params.allow_lower_bout_growth is True
