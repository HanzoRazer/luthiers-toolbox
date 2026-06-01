"""
Business Calculators Package

Financial and business calculators for lutherie shop management:

- roi: Return on investment for CNC equipment
- amortization: Equipment depreciation and payback
- machine_throughput: Production capacity modeling
- margin_math: Target gross margin pricing formulas

Usage:
    from app.calculators.business import (
        calculate_cnc_roi,
        calculate_amortization,
        estimate_throughput,
        price_from_target_margin,
        gross_margin_pct,
    )
"""

from .roi import calculate_cnc_roi, ROIResult
from .amortization import calculate_amortization, AmortizationResult
from .machine_throughput import estimate_throughput, ThroughputResult
from .margin_math import (
    price_from_target_margin,
    price_from_markup,
    gross_margin_pct,
    markup_pct_to_margin_pct,
    margin_pct_to_markup_pct,
    validate_target_margin_pct,
)

__all__ = [
    "calculate_cnc_roi",
    "ROIResult",
    "calculate_amortization",
    "AmortizationResult",
    "estimate_throughput",
    "ThroughputResult",
    "price_from_target_margin",
    "price_from_markup",
    "gross_margin_pct",
    "markup_pct_to_margin_pct",
    "margin_pct_to_markup_pct",
    "validate_target_margin_pct",
]
