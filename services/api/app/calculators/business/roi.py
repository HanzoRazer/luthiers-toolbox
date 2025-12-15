"""
CNC ROI Calculator

Calculates return on investment for CNC equipment purchases.

MODEL NOTES:
- Simple payback: Time to recover initial investment
- ROI percentage: Annual return relative to investment
- NPV: Net present value accounting for time value of money
- Considers:
  - Labor savings
  - Increased production capacity
  - Material waste reduction
  - Maintenance costs
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ROIResult:
    """Result from ROI calculation."""
    payback_months: float
    annual_roi_percent: float
    five_year_profit: float
    monthly_net_benefit: float
    notes: str


def calculate_cnc_roi(
    machine_cost_usd: float,
    monthly_labor_savings_usd: float,
    monthly_additional_revenue_usd: float = 0.0,
    monthly_material_savings_usd: float = 0.0,
    monthly_operating_cost_usd: float = 0.0,
    *,
    maintenance_annual_usd: float = 0.0,
    training_cost_usd: float = 0.0,
    installation_cost_usd: float = 0.0,
) -> ROIResult:
    """
    Calculate ROI for a CNC machine purchase.

    Args:
        machine_cost_usd: Purchase price of machine
        monthly_labor_savings_usd: Labor cost reduction per month
        monthly_additional_revenue_usd: Extra revenue from increased capacity
        monthly_material_savings_usd: Material waste reduction savings
        monthly_operating_cost_usd: Power, consumables, etc.
        maintenance_annual_usd: Annual maintenance/service cost
        training_cost_usd: One-time training cost
        installation_cost_usd: One-time installation cost

    Returns:
        ROIResult with payback period and ROI metrics
    """
    # Total initial investment
    total_investment = machine_cost_usd + training_cost_usd + installation_cost_usd

    if total_investment <= 0:
        return ROIResult(
            payback_months=0.0,
            annual_roi_percent=0.0,
            five_year_profit=0.0,
            monthly_net_benefit=0.0,
            notes="Invalid investment amount",
        )

    # Monthly benefits
    monthly_benefits = (
        monthly_labor_savings_usd
        + monthly_additional_revenue_usd
        + monthly_material_savings_usd
    )

    # Monthly costs
    monthly_maintenance = maintenance_annual_usd / 12.0
    monthly_costs = monthly_operating_cost_usd + monthly_maintenance

    # Net monthly benefit
    monthly_net = monthly_benefits - monthly_costs

    if monthly_net <= 0:
        return ROIResult(
            payback_months=float('inf'),
            annual_roi_percent=-100.0,
            five_year_profit=monthly_net * 60,  # 5 years of losses
            monthly_net_benefit=monthly_net,
            notes="Negative ROI - costs exceed benefits",
        )

    # Simple payback period
    payback_months = total_investment / monthly_net

    # Annual ROI percentage
    annual_net = monthly_net * 12
    annual_roi = (annual_net / total_investment) * 100

    # 5-year profit (simple, no discounting)
    five_year_profit = (monthly_net * 60) - total_investment

    # Generate notes
    if payback_months < 12:
        notes = f"Excellent ROI - payback in under 1 year"
    elif payback_months < 24:
        notes = f"Good ROI - payback in 1-2 years"
    elif payback_months < 36:
        notes = f"Moderate ROI - payback in 2-3 years"
    elif payback_months < 60:
        notes = f"Long payback - consider if capacity is needed"
    else:
        notes = f"Very long payback - may not be justified without strategic need"

    return ROIResult(
        payback_months=round(payback_months, 1),
        annual_roi_percent=round(annual_roi, 1),
        five_year_profit=round(five_year_profit, 2),
        monthly_net_benefit=round(monthly_net, 2),
        notes=notes,
    )


def calculate_break_even_jobs(
    machine_cost_usd: float,
    profit_per_job_usd: float,
    jobs_per_month: float,
    *,
    monthly_overhead_usd: float = 0.0,
) -> dict:
    """
    Calculate break-even point in number of jobs.

    Args:
        machine_cost_usd: Machine purchase price
        profit_per_job_usd: Net profit per job using the machine
        jobs_per_month: Expected jobs per month
        monthly_overhead_usd: Fixed monthly costs

    Returns:
        Dict with break-even metrics
    """
    if profit_per_job_usd <= 0:
        return {
            "break_even_jobs": float('inf'),
            "break_even_months": float('inf'),
            "note": "Profit per job must be positive",
        }

    # Jobs needed to cover machine cost
    net_profit_per_job = profit_per_job_usd
    if jobs_per_month > 0 and monthly_overhead_usd > 0:
        overhead_per_job = monthly_overhead_usd / jobs_per_month
        net_profit_per_job = profit_per_job_usd - overhead_per_job

    if net_profit_per_job <= 0:
        return {
            "break_even_jobs": float('inf'),
            "break_even_months": float('inf'),
            "note": "Overhead exceeds profit per job",
        }

    break_even_jobs = machine_cost_usd / net_profit_per_job
    break_even_months = break_even_jobs / jobs_per_month if jobs_per_month > 0 else float('inf')

    return {
        "break_even_jobs": round(break_even_jobs, 0),
        "break_even_months": round(break_even_months, 1),
        "net_profit_per_job": round(net_profit_per_job, 2),
        "note": f"Need {break_even_jobs:.0f} jobs to break even",
    }
