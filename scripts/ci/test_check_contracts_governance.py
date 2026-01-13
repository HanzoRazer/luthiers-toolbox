#!/usr/bin/env python3
"""
Unit tests for check_contracts_governance.py

Run with: python -m pytest scripts/ci/test_check_contracts_governance.py -v
"""

import re
import pytest


def stem_mentioned(text: str, stem: str) -> bool:
    """
    Token-safe match: avoid partial matches like cam_policy in cam_policy_extended.
    Copied from check_contracts_governance.py for isolated testing.
    """
    pat = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(stem)}(?![A-Za-z0-9_])")
    return pat.search(text) is not None


class TestStemMentioned:
    """Test cases for the stem_mentioned regex matcher."""

    # --- SHOULD MATCH (True) ---

    def test_exact_match(self):
        """Exact stem on its own line."""
        assert stem_mentioned("cam_policy", "cam_policy") is True

    def test_stem_in_markdown_bullet(self):
        """Stem in a markdown bullet point."""
        assert stem_mentioned("- cam_policy: updated constraints", "cam_policy") is True

    def test_stem_in_backticks(self):
        """Stem wrapped in markdown backticks."""
        assert stem_mentioned("Updated `cam_policy` schema", "cam_policy") is True

    def test_stem_at_line_start(self):
        """Stem at the beginning of a line."""
        assert stem_mentioned("cam_policy was modified", "cam_policy") is True

    def test_stem_at_line_end(self):
        """Stem at the end of a line."""
        assert stem_mentioned("Modified the cam_policy", "cam_policy") is True

    def test_stem_with_colon(self):
        """Stem followed by colon (common in changelogs)."""
        assert stem_mentioned("cam_policy: tightened rules", "cam_policy") is True

    def test_stem_in_parentheses(self):
        """Stem inside parentheses."""
        assert stem_mentioned("Updated schema (cam_policy)", "cam_policy") is True

    def test_stem_with_comma(self):
        """Stem followed by comma."""
        assert stem_mentioned("cam_policy, qa_core updated", "cam_policy") is True

    def test_stem_multiline_found(self):
        """Stem found in multiline text."""
        text = """## 2026-01-13
- Updated cam_policy constraints
- Fixed qa_core validation
"""
        assert stem_mentioned(text, "cam_policy") is True

    def test_stem_v1_suffix(self):
        """Stem with _v1 suffix (common pattern)."""
        assert stem_mentioned("viewer_pack_v1 updated", "viewer_pack_v1") is True

    def test_stem_in_quotes(self):
        """Stem in double quotes."""
        assert stem_mentioned('Updated "cam_policy" schema', "cam_policy") is True

    # --- SHOULD NOT MATCH (False) ---

    def test_partial_match_extended(self):
        """cam_policy should NOT match cam_policy_extended."""
        assert stem_mentioned("cam_policy_extended was added", "cam_policy") is False

    def test_partial_match_prefix(self):
        """cam_policy should NOT match new_cam_policy."""
        assert stem_mentioned("new_cam_policy was added", "cam_policy") is False

    def test_partial_match_v2(self):
        """cam_policy_v1 should NOT match cam_policy_v1_experimental."""
        assert stem_mentioned("cam_policy_v1_experimental", "cam_policy_v1") is False

    def test_case_sensitive_upper(self):
        """Case sensitivity: CAM_POLICY should not match cam_policy."""
        assert stem_mentioned("CAM_POLICY updated", "cam_policy") is False

    def test_case_sensitive_mixed(self):
        """Case sensitivity: Cam_Policy should not match cam_policy."""
        assert stem_mentioned("Cam_Policy updated", "cam_policy") is False

    def test_stem_not_present(self):
        """Stem simply not in text."""
        assert stem_mentioned("Updated qa_core schema", "cam_policy") is False

    def test_empty_text(self):
        """Empty text should not match."""
        assert stem_mentioned("", "cam_policy") is False

    def test_partial_in_word(self):
        """Stem embedded in larger identifier."""
        assert stem_mentioned("my_cam_policy_thing", "cam_policy") is False

    def test_numeric_suffix_boundary(self):
        """cam_policy should NOT match cam_policy2."""
        assert stem_mentioned("cam_policy2 added", "cam_policy") is False

    def test_numeric_prefix_boundary(self):
        """cam_policy should NOT match 2cam_policy."""
        assert stem_mentioned("2cam_policy added", "cam_policy") is False

    # --- EDGE CASES ---

    def test_stem_with_hyphen_adjacent(self):
        """Hyphen is not a word character, so stem-something should match stem."""
        # Hyphen is NOT in [A-Za-z0-9_], so "cam_policy-extra" has cam_policy at boundary
        assert stem_mentioned("cam_policy-notes", "cam_policy") is True

    def test_stem_with_dot_adjacent(self):
        """Dot is not a word character."""
        assert stem_mentioned("cam_policy.schema.json", "cam_policy") is True

    def test_multiple_stems_in_text(self):
        """Multiple different stems, check each."""
        text = "Updated cam_policy and qa_core"
        assert stem_mentioned(text, "cam_policy") is True
        assert stem_mentioned(text, "qa_core") is True
        assert stem_mentioned(text, "viewer_pack_v1") is False

    def test_regex_special_chars_in_stem(self):
        """Stem with characters that need regex escaping (hypothetical)."""
        # re.escape handles this - testing with a realistic stem
        assert stem_mentioned("schema.v1 updated", "schema.v1") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
