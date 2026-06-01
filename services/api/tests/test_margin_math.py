"""
Tests for margin math utilities.

Verifies the correct implementation of target gross margin pricing.

Key invariant:
    cost = 1000, target_margin_pct = 30.0
    correct price = 1428.57
    incorrect markup result = 1300.00 (this is what we're fixing)
"""
import pytest

from app.calculators.business.margin_math import (
    price_from_target_margin,
    price_from_markup,
    gross_margin_pct,
    markup_pct_to_margin_pct,
    margin_pct_to_markup_pct,
    validate_target_margin_pct,
)


class TestPriceFromTargetMargin:
    """Tests for target margin pricing formula."""

    def test_price_from_target_margin_not_markup(self):
        """
        Core invariant: 30% target margin on $1000 = $1428.57, NOT $1300.

        This is the primary defect this sprint fixes.
        """
        assert price_from_target_margin(1000, 30.0) == 1428.57

    def test_price_from_target_margin_50_percent(self):
        """50% margin on $1000 = $2000."""
        assert price_from_target_margin(1000, 50.0) == 2000.0

    def test_price_from_target_margin_zero(self):
        """0% margin returns cost."""
        assert price_from_target_margin(1000, 0.0) == 1000.0

    def test_price_from_target_margin_small(self):
        """10% margin on $1000 = $1111.11."""
        assert price_from_target_margin(1000, 10.0) == 1111.11

    def test_rejects_negative_cost(self):
        """Negative cost should raise ValueError."""
        with pytest.raises(ValueError, match="cost must be non-negative"):
            price_from_target_margin(-100, 30.0)

    def test_rejects_negative_margin(self):
        """Negative margin should raise ValueError."""
        with pytest.raises(ValueError, match="target_margin_pct must be non-negative"):
            price_from_target_margin(1000, -10.0)

    def test_rejects_margin_at_100(self):
        """Margin at 100% would require infinite price."""
        with pytest.raises(ValueError, match="target_margin_pct must be less than 100"):
            price_from_target_margin(1000, 100.0)

    def test_rejects_margin_above_100(self):
        """Margin above 100% is mathematically impossible."""
        with pytest.raises(ValueError, match="target_margin_pct must be less than 100"):
            price_from_target_margin(1000, 150.0)


class TestPriceFromMarkup:
    """Tests for legacy markup formula (preserved for compatibility)."""

    def test_price_from_markup_30_percent(self):
        """30% markup on $1000 = $1300 (the legacy behavior)."""
        assert price_from_markup(1000, 30.0) == 1300.0

    def test_price_from_markup_100_percent(self):
        """100% markup doubles the price."""
        assert price_from_markup(1000, 100.0) == 2000.0

    def test_price_from_markup_zero(self):
        """0% markup returns cost."""
        assert price_from_markup(1000, 0.0) == 1000.0


class TestGrossMarginPct:
    """Tests for calculating actual gross margin from price and cost."""

    def test_gross_margin_pct_from_target_margin_price(self):
        """Price from 30% target margin should yield 30% actual margin."""
        assert gross_margin_pct(1428.57, 1000) == 30.0

    def test_gross_margin_pct_from_markup_price(self):
        """Price from 30% markup only yields 23.08% actual margin."""
        assert gross_margin_pct(1300.0, 1000) == 23.08

    def test_gross_margin_pct_50_percent(self):
        """$2000 price on $1000 cost = 50% margin."""
        assert gross_margin_pct(2000.0, 1000) == 50.0

    def test_rejects_zero_price(self):
        """Zero price should raise ValueError."""
        with pytest.raises(ValueError, match="price must be positive"):
            gross_margin_pct(0, 1000)

    def test_rejects_negative_price(self):
        """Negative price should raise ValueError."""
        with pytest.raises(ValueError, match="price must be positive"):
            gross_margin_pct(-100, 1000)


class TestMarkupToMarginConversion:
    """Tests for converting between markup and margin percentages."""

    def test_markup_pct_to_margin_pct_30(self):
        """30% markup = 23.08% margin."""
        assert markup_pct_to_margin_pct(30.0) == 23.08

    def test_markup_pct_to_margin_pct_100(self):
        """100% markup = 50% margin."""
        assert markup_pct_to_margin_pct(100.0) == 50.0

    def test_margin_pct_to_markup_pct_30(self):
        """30% margin requires 42.86% markup."""
        assert margin_pct_to_markup_pct(30.0) == 42.86

    def test_margin_pct_to_markup_pct_50(self):
        """50% margin requires 100% markup."""
        assert margin_pct_to_markup_pct(50.0) == 100.0

    def test_roundtrip_conversion(self):
        """Converting margin->markup->margin should return close to original."""
        original_margin = 30.0
        markup = margin_pct_to_markup_pct(original_margin)
        back_to_margin = markup_pct_to_margin_pct(markup)
        assert abs(back_to_margin - original_margin) < 0.1


class TestPricingInvariants:
    """End-to-end tests verifying pricing invariants."""

    def test_target_margin_achieves_stated_margin(self):
        """
        If I request 30% target margin, the resulting price should
        actually yield 30% gross margin when I calculate it.
        """
        cost = 1000
        target = 30.0
        price = price_from_target_margin(cost, target)
        actual = gross_margin_pct(price, cost)
        assert actual == target

    def test_markup_does_not_achieve_same_margin(self):
        """
        30% markup does NOT yield 30% margin.
        This is the core distinction this sprint addresses.
        """
        cost = 1000
        markup = 30.0
        price = price_from_markup(cost, markup)
        actual = gross_margin_pct(price, cost)
        assert actual != markup
        assert actual == 23.08

    def test_equivalent_markup_for_target_margin(self):
        """
        To achieve 30% margin, you need ~42.86% markup.
        """
        cost = 1000
        target_margin = 30.0

        # Calculate what markup would be needed
        required_markup = margin_pct_to_markup_pct(target_margin)
        assert required_markup == 42.86

        # Verify that markup achieves the target margin
        price_via_markup = price_from_markup(cost, required_markup)
        price_via_margin = price_from_target_margin(cost, target_margin)

        # Should be very close (within rounding)
        assert abs(price_via_markup - price_via_margin) < 1.0
