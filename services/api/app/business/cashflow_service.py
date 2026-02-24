"""
Cash Flow Service — Cash flow projections and runway analysis.

Helps luthiers answer: "Can I afford to quit my day job?"
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from calendar import month_name

from .schemas import (
    CashFlowProjection,
    CashFlowMonth,
)


class CashFlowService:
    """
    Cash flow projection calculator.

    Responsibilities:
    - Project monthly cash flows
    - Calculate runway (months of cash)
    - Identify cash crunches
    - Model growth scenarios
    """

    def create_projection(
        self,
        projection_name: str,
        months: int = 12,
        starting_cash: float = 0.0,
        monthly_revenue: float = 0.0,
        monthly_materials: float = 0.0,
        monthly_labor: float = 0.0,
        monthly_overhead: float = 0.0,
        revenue_growth_pct: float = 0.0,
        start_month: int = 1,
        start_year: int = 2026,
    ) -> CashFlowProjection:
        """
        Create a cash flow projection.

        Args:
            projection_name: Name for this projection
            months: Number of months to project
            starting_cash: Cash on hand at start
            monthly_revenue: Expected monthly revenue
            monthly_materials: Monthly materials cost
            monthly_labor: Monthly labor cost (if paying yourself)
            monthly_overhead: Monthly fixed overhead
            revenue_growth_pct: Monthly revenue growth rate
            start_month: Starting month (1-12)
            start_year: Starting year

        Returns:
            Complete CashFlowProjection
        """
        monthly_data: List[CashFlowMonth] = []
        cumulative = starting_cash
        current_revenue = monthly_revenue
        warnings: List[str] = []

        minimum_cash = starting_cash
        minimum_cash_month = 0
        months_to_positive = None
        total_revenue = 0.0
        total_expenses = 0.0

        for i in range(months):
            # Calculate month/year
            month_num = ((start_month - 1 + i) % 12) + 1
            year = start_year + (start_month - 1 + i) // 12
            month_label = f"{month_name[month_num][:3]} {year}"

            # Inflows
            revenue = current_revenue
            total_inflows = revenue

            # Outflows
            materials = monthly_materials * (current_revenue / monthly_revenue) if monthly_revenue > 0 else monthly_materials
            labor = monthly_labor
            overhead = monthly_overhead
            total_outflows = materials + labor + overhead

            # Net
            net_cash_flow = total_inflows - total_outflows
            cumulative += net_cash_flow

            # Track totals
            total_revenue += revenue
            total_expenses += total_outflows

            # Track minimum
            if cumulative < minimum_cash:
                minimum_cash = cumulative
                minimum_cash_month = i + 1

            # Track when we go positive
            if months_to_positive is None and cumulative > 0 and i > 0:
                months_to_positive = i + 1

            monthly_data.append(CashFlowMonth(
                month=i + 1,
                month_label=month_label,
                revenue=round(revenue, 2),
                other_income=0.0,
                total_inflows=round(total_inflows, 2),
                materials=round(materials, 2),
                labor=round(labor, 2),
                overhead=round(overhead, 2),
                other_expenses=0.0,
                total_outflows=round(total_outflows, 2),
                net_cash_flow=round(net_cash_flow, 2),
                cumulative_cash_flow=round(cumulative, 2),
                is_positive=cumulative >= 0,
            ))

            # Apply growth for next month
            current_revenue *= (1 + revenue_growth_pct / 100)

        # Calculate runway
        avg_monthly_burn = total_expenses / months if months > 0 else 0
        runway_months = int(starting_cash / avg_monthly_burn) if avg_monthly_burn > 0 else None

        # Generate warnings
        if minimum_cash < 0:
            warnings.append(
                f"Cash goes negative in month {minimum_cash_month} "
                f"(${minimum_cash:,.0f}). Need additional funding."
            )

        if runway_months and runway_months < 6:
            warnings.append(
                f"Limited runway: only {runway_months} months of cash at current burn rate."
            )

        if total_revenue < total_expenses:
            warnings.append(
                f"Operating at a loss: ${total_expenses - total_revenue:,.0f} "
                f"deficit over {months} months."
            )

        return CashFlowProjection(
            projection_name=projection_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            months=months,
            starting_cash=starting_cash,
            monthly_data=monthly_data,
            total_revenue=round(total_revenue, 2),
            total_expenses=round(total_expenses, 2),
            net_cash_flow=round(total_revenue - total_expenses, 2),
            ending_cash=round(cumulative, 2),
            months_to_positive=months_to_positive,
            runway_months=runway_months,
            minimum_cash_month=minimum_cash_month if minimum_cash < starting_cash else None,
            minimum_cash_amount=round(minimum_cash, 2) if minimum_cash < starting_cash else None,
            warnings=warnings,
        )

    def create_ramp_up_projection(
        self,
        projection_name: str,
        starting_cash: float,
        monthly_overhead: float,
        target_monthly_revenue: float,
        months_to_ramp: int = 6,
        total_months: int = 12,
        cogs_pct: float = 40.0,
        owner_salary: float = 0.0,
    ) -> CashFlowProjection:
        """
        Create a projection with revenue ramp-up period.

        Models starting a business where revenue grows from 0 to target.

        Args:
            projection_name: Name for this projection
            starting_cash: Initial capital
            monthly_overhead: Fixed monthly costs
            target_monthly_revenue: Revenue goal after ramp
            months_to_ramp: Months to reach target revenue
            total_months: Total projection period
            cogs_pct: COGS as percentage of revenue
            owner_salary: Monthly owner draw (optional)

        Returns:
            CashFlowProjection with ramp-up
        """
        monthly_data: List[CashFlowMonth] = []
        cumulative = starting_cash
        warnings: List[str] = []

        minimum_cash = starting_cash
        minimum_cash_month = 0
        months_to_positive = None
        total_revenue = 0.0
        total_expenses = 0.0

        for i in range(total_months):
            month_label = f"Month {i + 1}"

            # Revenue ramp: linear from 0 to target
            if i < months_to_ramp:
                revenue = target_monthly_revenue * (i + 1) / months_to_ramp
            else:
                revenue = target_monthly_revenue

            # Variable costs scale with revenue
            materials = revenue * (cogs_pct / 100)
            labor = owner_salary
            overhead = monthly_overhead

            total_inflows = revenue
            total_outflows = materials + labor + overhead

            net_cash_flow = total_inflows - total_outflows
            cumulative += net_cash_flow

            total_revenue += revenue
            total_expenses += total_outflows

            if cumulative < minimum_cash:
                minimum_cash = cumulative
                minimum_cash_month = i + 1

            if months_to_positive is None and cumulative > 0 and net_cash_flow > 0:
                months_to_positive = i + 1

            monthly_data.append(CashFlowMonth(
                month=i + 1,
                month_label=month_label,
                revenue=round(revenue, 2),
                other_income=0.0,
                total_inflows=round(total_inflows, 2),
                materials=round(materials, 2),
                labor=round(labor, 2),
                overhead=round(overhead, 2),
                other_expenses=0.0,
                total_outflows=round(total_outflows, 2),
                net_cash_flow=round(net_cash_flow, 2),
                cumulative_cash_flow=round(cumulative, 2),
                is_positive=cumulative >= 0,
            ))

        # Warnings
        if minimum_cash < 0:
            funding_gap = abs(minimum_cash)
            warnings.append(
                f"Cash shortfall of ${funding_gap:,.0f} in month {minimum_cash_month}. "
                f"Need ${funding_gap:,.0f} additional starting capital."
            )

        # Calculate required starting capital
        if minimum_cash < 0:
            required_capital = starting_cash + abs(minimum_cash) + (monthly_overhead * 2)  # 2 month buffer
            warnings.append(
                f"Recommended starting capital: ${required_capital:,.0f} "
                f"(current ${starting_cash:,.0f} + gap + 2 month buffer)"
            )

        return CashFlowProjection(
            projection_name=projection_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            months=total_months,
            starting_cash=starting_cash,
            monthly_data=monthly_data,
            total_revenue=round(total_revenue, 2),
            total_expenses=round(total_expenses, 2),
            net_cash_flow=round(total_revenue - total_expenses, 2),
            ending_cash=round(cumulative, 2),
            months_to_positive=months_to_positive,
            runway_months=None,  # Not applicable for ramp-up
            minimum_cash_month=minimum_cash_month if minimum_cash < starting_cash else None,
            minimum_cash_amount=round(minimum_cash, 2) if minimum_cash < starting_cash else None,
            warnings=warnings,
        )

    def calculate_required_capital(
        self,
        monthly_overhead: float,
        months_to_revenue: int,
        target_monthly_revenue: float,
        cogs_pct: float = 40.0,
        buffer_months: int = 3,
    ) -> Dict[str, float]:
        """
        Calculate how much capital is needed to start.

        Args:
            monthly_overhead: Fixed monthly costs
            months_to_revenue: Months before first sale
            target_monthly_revenue: Expected monthly revenue when stable
            cogs_pct: COGS as percentage of revenue
            buffer_months: Emergency reserve months

        Returns:
            Capital requirements breakdown
        """
        # Pre-revenue period
        pre_revenue_burn = monthly_overhead * months_to_revenue

        # Ramp-up period (assume 6 months to reach target, average 50% of target)
        ramp_months = 6
        ramp_avg_revenue = target_monthly_revenue * 0.5
        ramp_avg_cogs = ramp_avg_revenue * (cogs_pct / 100)
        ramp_net_burn = (monthly_overhead + ramp_avg_cogs - ramp_avg_revenue) * ramp_months
        ramp_net_burn = max(0, ramp_net_burn)  # Only if negative

        # Buffer
        buffer_amount = monthly_overhead * buffer_months

        # Working capital (materials in advance)
        working_capital = target_monthly_revenue * (cogs_pct / 100) * 2  # 2 months materials

        total_required = pre_revenue_burn + ramp_net_burn + buffer_amount + working_capital

        return {
            "pre_revenue_burn": round(pre_revenue_burn, 2),
            "ramp_up_shortfall": round(ramp_net_burn, 2),
            "emergency_buffer": round(buffer_amount, 2),
            "working_capital": round(working_capital, 2),
            "total_required": round(total_required, 2),
            "breakdown": {
                "months_before_revenue": months_to_revenue,
                "monthly_overhead": monthly_overhead,
                "buffer_months": buffer_months,
            },
        }
