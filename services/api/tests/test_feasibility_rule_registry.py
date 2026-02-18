"""Tests for feasibility rule registry consistency."""
import re
import pytest
from app.rmos.feasibility.rule_registry import (
    FEASIBILITY_RULES,
    get_rule,
    get_all_rule_ids,
)


class TestFeasibilityRuleRegistry:
    """Tests for the feasibility rule registry."""

    def test_all_rules_have_required_fields(self):
        """Every rule must have level, summary, description, operator_hint."""
        for rule_id, meta in FEASIBILITY_RULES.items():
            assert meta.get("level") in ("RED", "YELLOW"), f"{rule_id}: invalid level"
            assert len(meta.get("summary", "")) > 0, f"{rule_id}: empty summary"
            assert len(meta.get("description", "")) > 0, f"{rule_id}: empty description"
            assert len(meta.get("operator_hint", "")) > 0, f"{rule_id}: empty operator_hint"

    def test_red_rules_exist(self):
        """At least one RED rule must exist."""
        red_rules = [r for r in FEASIBILITY_RULES.values() if r["level"] == "RED"]
        assert len(red_rules) >= 7, "Expected at least 7 RED rules (F001-F007)"

    def test_yellow_rules_exist(self):
        """At least one YELLOW rule must exist."""
        yellow_rules = [r for r in FEASIBILITY_RULES.values() if r["level"] == "YELLOW"]
        assert len(yellow_rules) >= 4, "Expected at least 4 YELLOW rules (F010-F013)"

    def test_get_rule_returns_none_for_unknown(self):
        """Unknown rule IDs should return None."""
        result = get_rule("UNKNOWN_RULE")
        assert result is None

    def test_get_rule_returns_metadata_for_known(self):
        """Known rule IDs should return metadata dict."""
        result = get_rule("F001")
        assert result is not None
        assert result["level"] == "RED"
        assert "tool" in result["summary"].lower()

    def test_get_all_rule_ids_returns_known_rules(self):
        """get_all_rule_ids should return all registered rules."""
        ids = get_all_rule_ids()
        assert "F001" in ids
        assert "F010" in ids
        assert len(ids) >= 10

    @pytest.mark.parametrize(
        "rule_id,expected_level",
        [
            ("F001", "RED"),
            ("F002", "RED"),
            ("F003", "RED"),
            ("F004", "RED"),
            ("F005", "RED"),
            ("F006", "RED"),
            ("F007", "RED"),
            ("F010", "YELLOW"),
            ("F011", "YELLOW"),
            ("F012", "YELLOW"),
            ("F013", "YELLOW"),
        ],
    )
    def test_specific_rule_levels(self, rule_id: str, expected_level: str):
        """Key rules should have expected levels."""
        meta = get_rule(rule_id)
        assert meta is not None, f"{rule_id} not found"
        assert meta["level"] == expected_level, f"{rule_id} should be {expected_level}"

    def test_all_rules_have_operator_hint(self):
        """Every rule should have an operator hint for usability."""
        for rule_id, meta in FEASIBILITY_RULES.items():
            hint = meta.get("operator_hint", "")
            assert hint, f"{rule_id}: missing operator_hint"
            assert len(hint) > 10, f"{rule_id}: hint too short"

    def test_rule_ids_follow_naming_convention(self):
        """Rule IDs should follow F### pattern."""
        pattern = re.compile(r"^F\d{3}$")
        for rule_id in FEASIBILITY_RULES.keys():
            assert pattern.match(rule_id), f"{rule_id}: doesn't match F### pattern"

    def test_red_rules_are_f00x_series(self):
        """RED rules should be in F00X series (core blocking rules)."""
        for rule_id, meta in FEASIBILITY_RULES.items():
            if meta["level"] == "RED":
                # F00X series for core, F02X for adversarial
                assert rule_id.startswith("F00") or rule_id.startswith("F02"), \
                    f"{rule_id}: RED rule should be F00X or F02X"
