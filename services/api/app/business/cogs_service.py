"""
COGS Service — Cost of Goods Sold calculation.

Helps luthiers answer: "What does it actually cost me to build this guitar?"
"""
from typing import List, Optional, Dict
from datetime import datetime, timezone

from .schemas import (
    COGSBreakdown,
    BillOfMaterials,
    LaborEstimate,
    LaborEntry,
    LaborCategory,
    LaborRate,
    OverheadItem,
    InstrumentType,
)


class COGSService:
    """
    Cost of Goods Sold calculator.

    COGS = Direct Materials + Direct Labor + Allocated Overhead

    Responsibilities:
    - Calculate true cost per instrument
    - Allocate overhead properly
    - Track cost trends
    - Identify cost reduction opportunities
    """

    # Default labor estimates by instrument type (hours)
    DEFAULT_LABOR_HOURS: Dict[InstrumentType, Dict[LaborCategory, float]] = {
        InstrumentType.ACOUSTIC_DREADNOUGHT: {
            LaborCategory.DESIGN: 2.0,
            LaborCategory.WOOD_PREP: 8.0,
            LaborCategory.JOINERY: 16.0,
            LaborCategory.CARVING: 12.0,
            LaborCategory.FRETTING: 6.0,
            LaborCategory.FINISHING: 20.0,
            LaborCategory.ASSEMBLY: 8.0,
            LaborCategory.SETUP: 4.0,
            LaborCategory.QA: 2.0,
        },
        InstrumentType.CLASSICAL: {
            LaborCategory.DESIGN: 2.0,
            LaborCategory.WOOD_PREP: 6.0,
            LaborCategory.JOINERY: 14.0,
            LaborCategory.CARVING: 10.0,
            LaborCategory.FRETTING: 5.0,
            LaborCategory.FINISHING: 18.0,
            LaborCategory.ASSEMBLY: 6.0,
            LaborCategory.SETUP: 3.0,
            LaborCategory.QA: 2.0,
        },
        InstrumentType.ELECTRIC_SOLID: {
            LaborCategory.DESIGN: 1.0,
            LaborCategory.WOOD_PREP: 4.0,
            LaborCategory.JOINERY: 6.0,
            LaborCategory.CARVING: 8.0,
            LaborCategory.FRETTING: 5.0,
            LaborCategory.FINISHING: 16.0,
            LaborCategory.ASSEMBLY: 4.0,
            LaborCategory.SETUP: 3.0,
            LaborCategory.QA: 1.0,
        },
    }

    # Default hourly rates by category
    DEFAULT_LABOR_RATES: Dict[LaborCategory, float] = {
        LaborCategory.DESIGN: 50.0,
        LaborCategory.WOOD_PREP: 35.0,
        LaborCategory.JOINERY: 45.0,
        LaborCategory.CARVING: 50.0,
        LaborCategory.FRETTING: 45.0,
        LaborCategory.FINISHING: 40.0,
        LaborCategory.ASSEMBLY: 40.0,
        LaborCategory.SETUP: 50.0,
        LaborCategory.QA: 45.0,
        LaborCategory.ADMIN: 30.0,
    }

    def __init__(
        self,
        labor_rates: Optional[Dict[LaborCategory, float]] = None,
        monthly_overhead: Optional[List[OverheadItem]] = None,
        units_per_month: int = 2,
    ):
        """
        Initialize COGS service.

        Args:
            labor_rates: Custom hourly rates by category
            monthly_overhead: List of monthly overhead costs
            units_per_month: Expected production volume for overhead allocation
        """
        self.labor_rates = labor_rates or self.DEFAULT_LABOR_RATES
        self.monthly_overhead = monthly_overhead or self._default_overhead()
        self.units_per_month = units_per_month

    def _default_overhead(self) -> List[OverheadItem]:
        """Default overhead items for a small shop."""
        return [
            OverheadItem(name="Shop Rent", monthly_cost=800.0, is_fixed=True),
            OverheadItem(name="Utilities", monthly_cost=150.0, is_fixed=True),
            OverheadItem(name="Insurance", monthly_cost=100.0, is_fixed=True),
            OverheadItem(name="Tools & Equipment", monthly_cost=100.0, is_fixed=False),
            OverheadItem(name="Marketing", monthly_cost=50.0, is_fixed=False),
            OverheadItem(name="Software/Subscriptions", monthly_cost=30.0, is_fixed=True),
        ]

    def estimate_labor(
        self,
        instrument_type: InstrumentType,
        custom_hours: Optional[Dict[LaborCategory, float]] = None,
    ) -> LaborEstimate:
        """
        Estimate labor costs for an instrument.

        Args:
            instrument_type: Type of instrument
            custom_hours: Override default hour estimates

        Returns:
            LaborEstimate with breakdown
        """
        hours_template = self.DEFAULT_LABOR_HOURS.get(
            instrument_type,
            self.DEFAULT_LABOR_HOURS[InstrumentType.ACOUSTIC_DREADNOUGHT]
        )

        if custom_hours:
            hours_template = {**hours_template, **custom_hours}

        entries: List[LaborEntry] = []
        hours_by_category: Dict[str, float] = {}
        total_hours = 0.0
        total_cost = 0.0

        for category, hours in hours_template.items():
            rate = self.labor_rates.get(category, 40.0)
            cost = hours * rate

            entries.append(LaborEntry(
                category=category,
                hours=hours,
                hourly_rate=rate,
                total_cost=cost,
            ))

            hours_by_category[category.value] = hours
            total_hours += hours
            total_cost += cost

        return LaborEstimate(
            instrument_type=instrument_type,
            entries=entries,
            total_hours=total_hours,
            total_labor_cost=total_cost,
            hours_by_category=hours_by_category,
        )

    def calculate_overhead_per_unit(self) -> float:
        """Calculate overhead cost per unit based on production volume."""
        total_monthly = sum(item.monthly_cost for item in self.monthly_overhead)
        return total_monthly / max(self.units_per_month, 1)

    def calculate_cogs(
        self,
        bom: BillOfMaterials,
        labor: Optional[LaborEstimate] = None,
        instrument_type: Optional[InstrumentType] = None,
        include_overhead: bool = True,
    ) -> COGSBreakdown:
        """
        Calculate complete Cost of Goods Sold.

        Args:
            bom: Bill of Materials
            labor: Labor estimate (or will be calculated from instrument_type)
            instrument_type: For default labor if not provided
            include_overhead: Whether to include overhead allocation

        Returns:
            Complete COGSBreakdown
        """
        # Get labor estimate
        if labor is None:
            instrument_type = instrument_type or bom.instrument_type
            labor = self.estimate_labor(instrument_type)

        # Direct costs
        materials_cost = bom.total_materials_cost
        labor_cost = labor.total_labor_cost
        direct_costs = materials_cost + labor_cost

        # Overhead allocation
        overhead_per_unit = self.calculate_overhead_per_unit() if include_overhead else 0.0

        # Total COGS
        total_cogs = direct_costs + overhead_per_unit

        # Margin analysis at various price points
        margin_analysis = self._calculate_margin_scenarios(total_cogs)

        return COGSBreakdown(
            instrument_name=bom.instrument_name,
            calculated_at=datetime.now(timezone.utc).isoformat(),
            materials_cost=materials_cost,
            labor_cost=labor_cost,
            direct_costs_total=direct_costs,
            overhead_per_unit=overhead_per_unit,
            overhead_allocation_method="per_unit",
            total_cogs=total_cogs,
            materials_breakdown=bom,
            labor_breakdown=labor,
            margin_analysis=margin_analysis,
        )

    def _calculate_margin_scenarios(
        self,
        cogs: float,
    ) -> List[Dict[str, float]]:
        """Calculate margins at various price points."""
        scenarios = []

        # Standard markup percentages
        for markup_pct in [25, 50, 75, 100, 150, 200]:
            price = cogs * (1 + markup_pct / 100)
            margin = price - cogs
            margin_pct = (margin / price) * 100

            scenarios.append({
                "markup_pct": markup_pct,
                "selling_price": round(price, 2),
                "gross_margin": round(margin, 2),
                "gross_margin_pct": round(margin_pct, 1),
            })

        return scenarios

    def update_labor_rate(
        self,
        category: LaborCategory,
        hourly_rate: float,
    ) -> None:
        """Update the hourly rate for a labor category."""
        self.labor_rates[category] = hourly_rate

    def update_overhead(
        self,
        overhead_items: List[OverheadItem],
        units_per_month: Optional[int] = None,
    ) -> None:
        """Update overhead configuration."""
        self.monthly_overhead = overhead_items
        if units_per_month:
            self.units_per_month = units_per_month

    def get_overhead_summary(self) -> Dict[str, float]:
        """Get summary of overhead costs."""
        fixed = sum(i.monthly_cost for i in self.monthly_overhead if i.is_fixed)
        variable = sum(i.monthly_cost for i in self.monthly_overhead if not i.is_fixed)
        total = fixed + variable

        return {
            "fixed_monthly": fixed,
            "variable_monthly": variable,
            "total_monthly": total,
            "per_unit": total / max(self.units_per_month, 1),
            "units_per_month": self.units_per_month,
        }
