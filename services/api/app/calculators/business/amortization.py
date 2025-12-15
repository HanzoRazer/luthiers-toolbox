"""
Equipment Amortization Calculator

Calculates depreciation and amortization schedules for shop equipment.

MODEL NOTES:
- Straight-line depreciation: Equal annual amounts
- Declining balance: Accelerated early depreciation
- Units of production: Based on actual usage
- Tax implications vary by jurisdiction
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

DepreciationMethod = Literal["straight_line", "declining_balance", "units_of_production"]


@dataclass
class YearlyDepreciation:
    """Depreciation values for a single year."""
    year: int
    depreciation: float
    accumulated: float
    book_value: float


@dataclass
class AmortizationResult:
    """Result from amortization calculation."""
    method: DepreciationMethod
    useful_life_years: int
    salvage_value: float
    annual_depreciation: float  # For straight-line
    schedule: List[YearlyDepreciation]
    notes: str


def calculate_amortization(
    purchase_price: float,
    useful_life_years: int,
    salvage_value: float = 0.0,
    method: DepreciationMethod = "straight_line",
    *,
    declining_rate: float = 2.0,  # For declining balance (2.0 = double declining)
) -> AmortizationResult:
    """
    Calculate equipment depreciation schedule.

    Args:
        purchase_price: Original equipment cost
        useful_life_years: Expected useful life in years
        salvage_value: Expected value at end of life
        method: Depreciation method
        declining_rate: Rate multiplier for declining balance method

    Returns:
        AmortizationResult with depreciation schedule
    """
    if useful_life_years <= 0 or purchase_price <= 0:
        return AmortizationResult(
            method=method,
            useful_life_years=useful_life_years,
            salvage_value=salvage_value,
            annual_depreciation=0.0,
            schedule=[],
            notes="Invalid parameters",
        )

    depreciable_amount = purchase_price - salvage_value
    schedule: List[YearlyDepreciation] = []
    accumulated = 0.0
    book_value = purchase_price

    if method == "straight_line":
        annual = depreciable_amount / useful_life_years

        for year in range(1, useful_life_years + 1):
            depreciation = min(annual, book_value - salvage_value)
            accumulated += depreciation
            book_value -= depreciation

            schedule.append(YearlyDepreciation(
                year=year,
                depreciation=round(depreciation, 2),
                accumulated=round(accumulated, 2),
                book_value=round(book_value, 2),
            ))

        notes = f"Straight-line: ${annual:,.2f}/year for {useful_life_years} years"

    elif method == "declining_balance":
        rate = declining_rate / useful_life_years
        annual = depreciable_amount / useful_life_years  # For reporting

        for year in range(1, useful_life_years + 1):
            # Declining balance depreciation
            depreciation = book_value * rate

            # Don't depreciate below salvage value
            if book_value - depreciation < salvage_value:
                depreciation = book_value - salvage_value

            accumulated += depreciation
            book_value -= depreciation

            schedule.append(YearlyDepreciation(
                year=year,
                depreciation=round(depreciation, 2),
                accumulated=round(accumulated, 2),
                book_value=round(book_value, 2),
            ))

        notes = f"Declining balance ({declining_rate}x): accelerated early depreciation"

    else:  # units_of_production
        # For units of production, we need usage data
        # Return straight-line as placeholder
        annual = depreciable_amount / useful_life_years

        for year in range(1, useful_life_years + 1):
            depreciation = annual
            accumulated += depreciation
            book_value -= depreciation

            schedule.append(YearlyDepreciation(
                year=year,
                depreciation=round(depreciation, 2),
                accumulated=round(accumulated, 2),
                book_value=round(book_value, 2),
            ))

        notes = "Units of production method requires usage tracking (showing straight-line)"
        annual = depreciable_amount / useful_life_years

    return AmortizationResult(
        method=method,
        useful_life_years=useful_life_years,
        salvage_value=salvage_value,
        annual_depreciation=round(annual, 2),
        schedule=schedule,
        notes=notes,
    )


def calculate_remaining_value(
    purchase_price: float,
    purchase_date_year: int,
    current_year: int,
    useful_life_years: int,
    salvage_value: float = 0.0,
    method: DepreciationMethod = "straight_line",
) -> dict:
    """
    Calculate current book value of equipment.

    Args:
        purchase_price: Original cost
        purchase_date_year: Year of purchase
        current_year: Current year
        useful_life_years: Expected useful life
        salvage_value: Expected salvage value
        method: Depreciation method

    Returns:
        Dict with current value information
    """
    years_owned = current_year - purchase_date_year

    if years_owned < 0:
        return {
            "book_value": purchase_price,
            "depreciation_taken": 0.0,
            "years_remaining": useful_life_years,
            "note": "Purchase date is in the future",
        }

    result = calculate_amortization(
        purchase_price=purchase_price,
        useful_life_years=useful_life_years,
        salvage_value=salvage_value,
        method=method,
    )

    if years_owned >= useful_life_years:
        return {
            "book_value": salvage_value,
            "depreciation_taken": purchase_price - salvage_value,
            "years_remaining": 0,
            "fully_depreciated": True,
            "note": "Asset is fully depreciated",
        }

    # Get values at current year
    current_schedule = result.schedule[min(years_owned, len(result.schedule)) - 1] if years_owned > 0 else None

    if current_schedule:
        book_value = current_schedule.book_value
        depreciation_taken = current_schedule.accumulated
    else:
        book_value = purchase_price
        depreciation_taken = 0.0

    return {
        "book_value": book_value,
        "depreciation_taken": depreciation_taken,
        "years_remaining": useful_life_years - years_owned,
        "fully_depreciated": False,
        "note": f"Year {years_owned} of {useful_life_years}",
    }
