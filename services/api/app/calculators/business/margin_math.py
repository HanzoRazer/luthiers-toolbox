"""
Margin Math Utilities — Target gross margin pricing formulas.

This module provides the canonical pricing math for target gross margin calculations.
All business pricing paths should use these functions to ensure consistency.

Key distinction:
- **Markup**: price = cost * (1 + markup_pct / 100)
- **Target Margin**: price = cost / (1 - target_margin_pct / 100)

Example:
    cost = 1000, target_margin_pct = 30
    price = 1000 / (1 - 0.30) = 1428.57
    actual_margin = (1428.57 - 1000) / 1428.57 = 30.0%

    cost = 1000, markup_pct = 30
    price = 1000 * (1 + 0.30) = 1300.00
    actual_margin = (1300 - 1000) / 1300 = 23.08%
"""
from __future__ import annotations


def validate_target_margin_pct(target_margin_pct: float) -> None:
    """
    Validate target margin percentage is within valid range.

    Args:
        target_margin_pct: Target gross margin as percentage points (e.g., 30.0 = 30%)

    Raises:
        ValueError: If margin is negative or >= 100
    """
    if target_margin_pct < 0:
        raise ValueError("target_margin_pct must be non-negative")
    if target_margin_pct >= 100:
        raise ValueError("target_margin_pct must be less than 100")


def price_from_target_margin(cost: float, target_margin_pct: float) -> float:
    """
    Calculate selling price to achieve a target gross margin.

    Formula: price = cost / (1 - target_margin_pct / 100)

    Args:
        cost: Cost of goods sold (COGS)
        target_margin_pct: Target gross margin as percentage points (e.g., 30.0 = 30%)

    Returns:
        Selling price rounded to 2 decimal places

    Raises:
        ValueError: If cost is negative or margin is invalid

    Example:
        >>> price_from_target_margin(1000, 30.0)
        1428.57
    """
    if cost < 0:
        raise ValueError("cost must be non-negative")
    validate_target_margin_pct(target_margin_pct)
    return round(cost / (1 - target_margin_pct / 100), 2)


def price_from_markup(cost: float, markup_pct: float) -> float:
    """
    Calculate selling price using markup formula.

    Formula: price = cost * (1 + markup_pct / 100)

    This is the LEGACY formula. Use price_from_target_margin for new code.

    Args:
        cost: Cost of goods sold (COGS)
        markup_pct: Markup percentage points (e.g., 30.0 = 30% markup)

    Returns:
        Selling price rounded to 2 decimal places

    Example:
        >>> price_from_markup(1000, 30.0)
        1300.0
    """
    if cost < 0:
        raise ValueError("cost must be non-negative")
    if markup_pct < 0:
        raise ValueError("markup_pct must be non-negative")
    return round(cost * (1 + markup_pct / 100), 2)


def gross_margin_pct(price: float, cost: float) -> float:
    """
    Calculate actual gross margin percentage from price and cost.

    Formula: margin_pct = ((price - cost) / price) * 100

    Args:
        price: Selling price
        cost: Cost of goods sold (COGS)

    Returns:
        Gross margin as percentage points, rounded to 2 decimal places

    Raises:
        ValueError: If price is not positive or cost is negative

    Example:
        >>> gross_margin_pct(1428.57, 1000)
        30.0
        >>> gross_margin_pct(1300.0, 1000)
        23.08
    """
    if price <= 0:
        raise ValueError("price must be positive")
    if cost < 0:
        raise ValueError("cost must be non-negative")
    return round(((price - cost) / price) * 100, 2)


def markup_pct_to_margin_pct(markup_pct: float) -> float:
    """
    Convert markup percentage to equivalent gross margin percentage.

    Formula: margin_pct = (markup_pct / (100 + markup_pct)) * 100

    Args:
        markup_pct: Markup as percentage points (e.g., 30.0 = 30% markup)

    Returns:
        Equivalent gross margin as percentage points

    Raises:
        ValueError: If markup is negative

    Example:
        >>> markup_pct_to_margin_pct(30.0)
        23.08
        >>> markup_pct_to_margin_pct(42.86)
        30.0
    """
    if markup_pct < 0:
        raise ValueError("markup_pct must be non-negative")
    return round((markup_pct / (100 + markup_pct)) * 100, 2)


def margin_pct_to_markup_pct(margin_pct: float) -> float:
    """
    Convert gross margin percentage to equivalent markup percentage.

    Formula: markup_pct = (margin_pct / (100 - margin_pct)) * 100

    Args:
        margin_pct: Gross margin as percentage points (e.g., 30.0 = 30% margin)

    Returns:
        Equivalent markup as percentage points

    Raises:
        ValueError: If margin is negative or >= 100

    Example:
        >>> margin_pct_to_markup_pct(30.0)
        42.86
        >>> margin_pct_to_markup_pct(23.08)
        30.01
    """
    validate_target_margin_pct(margin_pct)
    return round((margin_pct / (100 - margin_pct)) * 100, 2)
