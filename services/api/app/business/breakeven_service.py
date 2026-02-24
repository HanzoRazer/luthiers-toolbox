"""
Break-Even Service — Break-even analysis and what-if scenarios.

Helps luthiers answer: "How many guitars do I need to sell to cover my costs?"
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from .schemas import (
    BreakEvenAnalysis,
    OverheadItem,
)


class BreakEvenService:
    """
    Break-even analysis calculator.

    Break-even point = Fixed Costs / Contribution Margin per Unit
    Contribution Margin = Selling Price - Variable Cost (COGS)

    Responsibilities:
    - Calculate break-even point
    - Run what-if scenarios
    - Analyze profit at various volumes
    - Identify leverage points
    """

    def calculate_break_even(
        self,
        fixed_costs_monthly: float,
        variable_cost_per_unit: float,
        selling_price_per_unit: float,
        analysis_name: str = "Break-Even Analysis",
    ) -> BreakEvenAnalysis:
        """
        Calculate break-even analysis.

        Args:
            fixed_costs_monthly: Monthly fixed costs (rent, insurance, etc.)
            variable_cost_per_unit: COGS per unit
            selling_price_per_unit: Selling price per unit

        Returns:
            Complete BreakEvenAnalysis
        """
        # Contribution margin
        contribution_margin = selling_price_per_unit - variable_cost_per_unit
        contribution_margin_pct = (
            (contribution_margin / selling_price_per_unit) * 100
            if selling_price_per_unit > 0
            else 0
        )

        # Break-even units
        if contribution_margin <= 0:
            # Cannot break even with negative or zero margin
            break_even_units = float('inf')
            break_even_revenue = float('inf')
        else:
            break_even_units = fixed_costs_monthly / contribution_margin
            break_even_revenue = break_even_units * selling_price_per_unit

        # Generate scenarios
        scenarios = self._generate_scenarios(
            fixed_costs_monthly,
            variable_cost_per_unit,
            selling_price_per_unit,
            contribution_margin,
        )

        return BreakEvenAnalysis(
            analysis_name=analysis_name,
            calculated_at=datetime.now(timezone.utc).isoformat(),
            fixed_costs_monthly=fixed_costs_monthly,
            variable_cost_per_unit=variable_cost_per_unit,
            selling_price_per_unit=selling_price_per_unit,
            contribution_margin=contribution_margin,
            contribution_margin_pct=round(contribution_margin_pct, 1),
            break_even_units=round(break_even_units, 2),
            break_even_revenue=round(break_even_revenue, 2),
            scenarios=scenarios,
        )

    def _generate_scenarios(
        self,
        fixed_costs: float,
        variable_cost: float,
        price: float,
        contribution_margin: float,
    ) -> List[Dict[str, Any]]:
        """Generate what-if scenarios."""
        scenarios = []

        if contribution_margin <= 0:
            return scenarios

        # Volume scenarios
        for units in [1, 2, 3, 4, 5, 6, 8, 10, 12]:
            revenue = units * price
            total_variable = units * variable_cost
            total_costs = fixed_costs + total_variable
            profit = revenue - total_costs
            profit_pct = (profit / revenue * 100) if revenue > 0 else 0

            scenarios.append({
                "scenario_type": "volume",
                "units_per_month": units,
                "monthly_revenue": round(revenue, 2),
                "monthly_costs": round(total_costs, 2),
                "monthly_profit": round(profit, 2),
                "profit_margin_pct": round(profit_pct, 1),
                "is_profitable": profit > 0,
            })

        return scenarios

    def calculate_profit_at_volume(
        self,
        fixed_costs: float,
        variable_cost: float,
        price: float,
        units: int,
    ) -> Dict[str, float]:
        """Calculate profit at a specific volume."""
        revenue = units * price
        total_variable = units * variable_cost
        total_costs = fixed_costs + total_variable
        profit = revenue - total_costs
        profit_pct = (profit / revenue * 100) if revenue > 0 else 0

        return {
            "units": units,
            "revenue": round(revenue, 2),
            "variable_costs": round(total_variable, 2),
            "fixed_costs": round(fixed_costs, 2),
            "total_costs": round(total_costs, 2),
            "profit": round(profit, 2),
            "profit_margin_pct": round(profit_pct, 1),
            "is_profitable": profit > 0,
        }

    def find_target_profit_volume(
        self,
        fixed_costs: float,
        variable_cost: float,
        price: float,
        target_monthly_profit: float,
    ) -> Dict[str, float]:
        """Calculate units needed to achieve target profit."""
        contribution_margin = price - variable_cost

        if contribution_margin <= 0:
            return {
                "achievable": False,
                "reason": "Contribution margin is zero or negative",
            }

        # Units = (Fixed Costs + Target Profit) / Contribution Margin
        required_units = (fixed_costs + target_monthly_profit) / contribution_margin
        required_revenue = required_units * price

        return {
            "achievable": True,
            "target_profit": target_monthly_profit,
            "required_units": round(required_units, 2),
            "required_revenue": round(required_revenue, 2),
            "units_per_week": round(required_units / 4, 2),
        }

    def sensitivity_analysis(
        self,
        base_fixed_costs: float,
        base_variable_cost: float,
        base_price: float,
    ) -> Dict[str, List[Dict]]:
        """
        Run sensitivity analysis on key variables.

        Shows how break-even changes as each variable changes.
        """
        base_cm = base_price - base_variable_cost
        base_be = base_fixed_costs / base_cm if base_cm > 0 else float('inf')

        analysis = {
            "price_sensitivity": [],
            "variable_cost_sensitivity": [],
            "fixed_cost_sensitivity": [],
        }

        # Price sensitivity (-20% to +20%)
        for pct in [-20, -10, -5, 0, 5, 10, 20]:
            new_price = base_price * (1 + pct / 100)
            cm = new_price - base_variable_cost
            be = base_fixed_costs / cm if cm > 0 else float('inf')
            be_change = ((be - base_be) / base_be * 100) if base_be != float('inf') else 0

            analysis["price_sensitivity"].append({
                "change_pct": pct,
                "new_value": round(new_price, 2),
                "break_even_units": round(be, 2) if be != float('inf') else None,
                "break_even_change_pct": round(be_change, 1),
            })

        # Variable cost sensitivity
        for pct in [-20, -10, -5, 0, 5, 10, 20]:
            new_vc = base_variable_cost * (1 + pct / 100)
            cm = base_price - new_vc
            be = base_fixed_costs / cm if cm > 0 else float('inf')
            be_change = ((be - base_be) / base_be * 100) if base_be != float('inf') else 0

            analysis["variable_cost_sensitivity"].append({
                "change_pct": pct,
                "new_value": round(new_vc, 2),
                "break_even_units": round(be, 2) if be != float('inf') else None,
                "break_even_change_pct": round(be_change, 1),
            })

        # Fixed cost sensitivity
        for pct in [-20, -10, -5, 0, 5, 10, 20]:
            new_fc = base_fixed_costs * (1 + pct / 100)
            be = new_fc / base_cm if base_cm > 0 else float('inf')
            be_change = ((be - base_be) / base_be * 100) if base_be != float('inf') else 0

            analysis["fixed_cost_sensitivity"].append({
                "change_pct": pct,
                "new_value": round(new_fc, 2),
                "break_even_units": round(be, 2) if be != float('inf') else None,
                "break_even_change_pct": round(be_change, 1),
            })

        return analysis
