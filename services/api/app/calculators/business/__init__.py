"""
Business Calculators Package

Financial and business calculators for lutherie shop management:

- roi: Return on investment for CNC equipment
- amortization: Equipment depreciation and payback
- machine_throughput: Production capacity modeling

Usage:
    from app.calculators.business import (
        calculate_cnc_roi,
        calculate_amortization,
        estimate_throughput,
    )
"""

from .roi import calculate_cnc_roi, ROIResult
from .amortization import calculate_amortization, AmortizationResult
from .machine_throughput import estimate_throughput, ThroughputResult

__all__ = [
    "calculate_cnc_roi",
    "ROIResult",
    "calculate_amortization",
    "AmortizationResult",
    "estimate_throughput",
    "ThroughputResult",
]
