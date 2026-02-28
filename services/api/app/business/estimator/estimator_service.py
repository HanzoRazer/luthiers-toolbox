"""
Engineering Estimator Service — Main estimation engine.

Combines:
- Work breakdown structures
- Complexity factors
- Learning curves
- Material yields

To produce parametric cost estimates.

Decomposed modules:
- risk_assessment.py: Confidence and risk factor evaluation
- material_estimation.py: Material cost calculation
"""
from typing import List, Dict, Any

from .schemas import (
    EstimateRequest,
    EstimateResult,
    ComplexitySelections,
    WBSTask,
    QuoteRequest,
    QuoteResult,
    InstrumentType,
)
from .complexity_factors import (
    BINDING_BODY_FACTORS,
    BINDING_NECK_FACTOR,
    BINDING_HEADSTOCK_FACTOR,
    FRETBOARD_INLAY_FACTORS,
    HEADSTOCK_INLAY_FACTOR,
    FINISH_FACTORS,
    ROSETTE_FACTORS,
    EXPERIENCE_FACTORS,
    calculate_body_complexity,
    calculate_neck_complexity,
    get_electronics_factor,
    get_all_factors_summary,
)
from .work_breakdown import (
    get_wbs_template,
    WBSTaskTemplate,
)
from .learning_curve import generate_learning_curve_projection

# Extracted modules
from .risk_assessment import (
    assess_confidence,
    identify_risks,
    get_range_factor,
)
from .material_estimation import estimate_materials

# Import from parent business module
from ..bom_service import BOMService
from ..cogs_service import COGSService


class EngineeringEstimatorService:
    """
    Parametric cost estimation engine.

    Produces engineering-style estimates based on:
    - Measurable design parameters
    - Historical learning curves
    - Material yield factors

    Risk assessment delegated to: risk_assessment.py
    Material estimation delegated to: material_estimation.py
    """

    # Default blended hourly rate (weighted average across task types)
    DEFAULT_HOURLY_RATE = 45.0

    def __init__(self):
        self.bom_service = BOMService()
        self.cogs_service = COGSService()

    def estimate(self, request: EstimateRequest) -> EstimateResult:
        """
        Generate parametric cost estimate.

        Args:
            request: EstimateRequest with all parameters

        Returns:
            Complete EstimateResult
        """
        notes: List[str] = []
        risk_factors: List[RiskFactor] = []

        # 1. Get base WBS for instrument type
        wbs_template = get_wbs_template(request.instrument_type)
        base_hours = sum(t.base_hours for t in wbs_template)
        notes.append(f"Base WBS: {len(wbs_template)} tasks, {base_hours:.1f} hours")

        # 2. Calculate complexity factors
        factors_applied = self._calculate_all_factors(request.complexity, request.instrument_type)
        total_complexity = self._combine_factors(factors_applied)
        notes.append(f"Complexity multiplier: {total_complexity:.2f}x")

        # 3. Apply experience factor
        exp_factor = EXPERIENCE_FACTORS[request.builder_experience]
        notes.append(f"Experience ({request.builder_experience.value}): {exp_factor:.2f}x")

        # 4. Generate adjusted WBS
        wbs_tasks = self._apply_factors_to_wbs(
            wbs_template,
            factors_applied,
            exp_factor,
            request.hourly_rate_override or self.DEFAULT_HOURLY_RATE,
        )

        first_unit_hours = sum(t.adjusted_hours for t in wbs_tasks)

        # 5. Apply learning curve for quantity > 1
        learning_curve = None
        if request.quantity > 1:
            learning_curve = generate_learning_curve_projection(
                first_unit_hours=first_unit_hours,
                quantity=request.quantity,
                learning_rate=request.learning_rate,
                hourly_rate=request.hourly_rate_override or self.DEFAULT_HOURLY_RATE,
            )
            avg_hours = learning_curve.average_hours_per_unit
            total_hours = learning_curve.total_hours
            notes.append(
                f"Learning curve ({request.learning_rate:.0%}): "
                f"{learning_curve.efficiency_gain_pct:.1f}% time savings"
            )
        else:
            avg_hours = first_unit_hours
            total_hours = first_unit_hours

        # 6. Calculate material costs (delegated to material_estimation module)
        material_breakdown = estimate_materials(
            request.instrument_type,
            request.complexity,
            request.include_material_waste,
            bom_service=self.bom_service,
        )
        material_cost_per_unit = sum(m.adjusted_cost for m in material_breakdown)

        # 7. Calculate labor costs
        hourly_rate = request.hourly_rate_override or self.DEFAULT_HOURLY_RATE
        labor_cost_per_unit = avg_hours * hourly_rate

        # 8. Total costs
        total_cost_per_unit = labor_cost_per_unit + material_cost_per_unit
        total_project_cost = total_cost_per_unit * request.quantity

        # 9. Assess confidence and risks (delegated to risk_assessment module)
        combined_multiplier = total_complexity * exp_factor
        confidence_level = assess_confidence(combined_multiplier, request)
        risk_factors = identify_risks(request, combined_multiplier)

        # 10. Calculate estimate range
        range_factor = get_range_factor(confidence_level)
        estimate_range_low = total_cost_per_unit * (1 - range_factor)
        estimate_range_high = total_cost_per_unit * (1 + range_factor)

        return EstimateResult(
            instrument_type=request.instrument_type.value,
            quantity=request.quantity,
            first_unit_hours=round(first_unit_hours, 2),
            average_hours_per_unit=round(avg_hours, 2),
            total_hours=round(total_hours, 2),
            labor_cost_per_unit=round(labor_cost_per_unit, 2),
            material_cost_per_unit=round(material_cost_per_unit, 2),
            total_cost_per_unit=round(total_cost_per_unit, 2),
            total_project_cost=round(total_project_cost, 2),
            wbs_tasks=wbs_tasks,
            material_breakdown=material_breakdown,
            learning_curve=learning_curve,
            complexity_factors_applied=factors_applied,
            total_complexity_multiplier=round(total_complexity, 3),
            experience_level=request.builder_experience.value,
            experience_multiplier=exp_factor,
            confidence_level=confidence_level,
            risk_factors=risk_factors,
            estimate_range_low=round(estimate_range_low, 2),
            estimate_range_high=round(estimate_range_high, 2),
            notes=notes,
        )

    def generate_quote(self, request: QuoteRequest) -> QuoteResult:
        """
        Generate customer quote from estimate.

        Args:
            request: QuoteRequest with estimate and margin targets

        Returns:
            QuoteResult with pricing
        """
        estimate = request.estimate

        # Base cost from estimate
        base_cost = estimate.total_cost_per_unit * estimate.quantity

        # Calculate markup for target margin
        # margin = (price - cost) / price
        # price = cost / (1 - margin)
        margin_decimal = request.target_margin_pct / 100
        if margin_decimal >= 1:
            margin_decimal = 0.5  # Cap at 50% if invalid

        subtotal = base_cost / (1 - margin_decimal)
        markup = subtotal - base_cost

        # Add design fee if applicable
        design_fee = request.design_fee if request.include_design_fee else 0
        total_price = subtotal + design_fee

        # Calculate actual margin
        gross_margin = total_price - base_cost
        gross_margin_pct = (gross_margin / total_price) * 100 if total_price > 0 else 0

        # Payment terms
        deposit_amount = total_price * (request.deposit_pct / 100)
        balance_due = total_price - deposit_amount

        # Price range based on estimate confidence
        range_factor = get_range_factor(estimate.confidence_level)
        price_range_low = total_price * (1 - range_factor * 0.5)  # Narrower range for price
        price_range_high = total_price * (1 + range_factor * 0.5)

        # Lead time estimate (rough: 1 week per 10 hours of work)
        lead_time_weeks = max(4, int(estimate.total_hours / 10))

        return QuoteResult(
            base_cost=round(base_cost, 2),
            markup=round(markup, 2),
            subtotal=round(subtotal, 2),
            design_fee=round(design_fee, 2),
            total_price=round(total_price, 2),
            gross_margin=round(gross_margin, 2),
            gross_margin_pct=round(gross_margin_pct, 1),
            deposit_amount=round(deposit_amount, 2),
            balance_due=round(balance_due, 2),
            price_range_low=round(price_range_low, 2),
            price_range_high=round(price_range_high, 2),
            lead_time_weeks=lead_time_weeks,
        )

    def get_factors_summary(self) -> Dict[str, Any]:
        """Return all complexity factors for API/UI."""
        return get_all_factors_summary()

    def _calculate_all_factors(
        self,
        complexity: ComplexitySelections,
        instrument_type: InstrumentType,
    ) -> Dict[str, float]:
        """Calculate all applicable complexity factors."""
        factors = {}

        # Body complexity
        body_factor = calculate_body_complexity(complexity.body)
        if body_factor != 1.0:
            factors["body"] = body_factor

        # Binding
        binding_factor = BINDING_BODY_FACTORS[complexity.binding_body]
        if binding_factor > 0:
            factors["binding_body"] = binding_factor
        if complexity.binding_neck:
            factors["binding_neck"] = BINDING_NECK_FACTOR
        if complexity.binding_headstock:
            factors["binding_headstock"] = BINDING_HEADSTOCK_FACTOR

        # Neck
        neck_factor = calculate_neck_complexity(complexity.neck)
        if neck_factor != 1.0:
            factors["neck"] = neck_factor

        # Inlays
        inlay_factor = FRETBOARD_INLAY_FACTORS[complexity.fretboard_inlay]
        if inlay_factor != 1.0:
            factors["fretboard_inlay"] = inlay_factor
        if complexity.headstock_inlay:
            factors["headstock_inlay"] = HEADSTOCK_INLAY_FACTOR

        # Finish
        finish_factor = FINISH_FACTORS[complexity.finish]
        if finish_factor != 1.0:
            factors["finish"] = finish_factor

        # Rosette (acoustic only)
        is_acoustic = instrument_type.value.startswith("acoustic") or instrument_type == InstrumentType.CLASSICAL
        if is_acoustic:
            rosette_factor = ROSETTE_FACTORS[complexity.rosette]
            if rosette_factor > 0:
                factors["rosette"] = rosette_factor

        # Electronics (electric only)
        is_electric = "electric" in instrument_type.value or "bass" in instrument_type.value
        if is_electric and complexity.pickup_count > 0:
            elec_factor = get_electronics_factor(
                complexity.pickup_count,
                complexity.active_electronics,
            )
            if elec_factor != 1.0:
                factors["electronics"] = elec_factor

        return factors

    def _combine_factors(self, factors: Dict[str, float]) -> float:
        """
        Combine multiple factors into single multiplier.

        Uses diminishing returns for multiple high factors.
        """
        if not factors:
            return 1.0

        # Separate by category
        structural = []  # body, neck
        detail = []      # binding, inlay, rosette
        finish_val = 1.0

        for name, value in factors.items():
            if name in ["body", "neck"]:
                structural.append(value)
            elif name == "finish":
                finish_val = value
            else:
                detail.append(value)

        # Structural: multiply directly (fundamental complexity)
        structural_factor = 1.0
        for f in structural:
            structural_factor *= f

        # Detail: diminishing returns
        detail_factor = 1.0
        for f in sorted(detail, reverse=True):
            # First adds full, subsequent add 60%
            if detail_factor == 1.0:
                detail_factor = f
            else:
                detail_factor += (f - 1.0) * 0.6

        # Combine: structural * detail * finish^0.8 (finish scales less)
        combined = structural_factor * detail_factor * (finish_val ** 0.8)

        return round(combined, 3)

    def _apply_factors_to_wbs(
        self,
        template: List[WBSTaskTemplate],
        factors: Dict[str, float],
        experience_factor: float,
        hourly_rate: float,
    ) -> List[WBSTask]:
        """Apply complexity and experience factors to WBS tasks."""
        tasks = []

        for t in template:
            # Determine which factor applies
            multiplier = 1.0

            if t.complexity_group == "body" and "body" in factors:
                multiplier = factors["body"]
            elif t.complexity_group == "neck" and "neck" in factors:
                multiplier = factors["neck"]
            elif t.complexity_group == "binding":
                multiplier = factors.get("binding_body", 1.0)
            elif t.complexity_group == "inlay":
                multiplier = factors.get("fretboard_inlay", 1.0)
            elif t.complexity_group == "finish" and "finish" in factors:
                multiplier = factors["finish"]
            elif t.complexity_group == "rosette":
                multiplier = factors.get("rosette", 1.0)
            elif t.complexity_group == "electronics":
                multiplier = factors.get("electronics", 1.0)

            # Skip tasks with 0 multiplier (e.g., no binding)
            if multiplier == 0:
                continue

            # Apply experience factor
            adjusted_hours = t.base_hours * multiplier * experience_factor
            labor_cost = adjusted_hours * hourly_rate

            tasks.append(WBSTask(
                task_id=t.task_id,
                task_name=t.task_name,
                base_hours=t.base_hours,
                complexity_multiplier=round(multiplier, 3),
                adjusted_hours=round(adjusted_hours, 2),
                labor_cost=round(labor_cost, 2),
            ))

        return tasks

