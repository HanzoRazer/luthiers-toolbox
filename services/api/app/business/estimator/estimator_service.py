"""
Engineering Estimator Service — Main estimation engine.

Combines:
- Work breakdown structures
- Complexity factors
- Learning curves
- Material yields

To produce parametric cost estimates.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from .schemas import (
    EstimateRequest,
    EstimateResult,
    ComplexitySelections,
    WBSTask,
    LearningCurveProjection,
    MaterialEstimate,
    RiskFactor,
    QuoteRequest,
    QuoteResult,
    InstrumentType,
    BuilderExperience,
    BindingComplexity,
    FinishType,
)
from .complexity_factors import (
    BODY_FACTORS,
    BINDING_BODY_FACTORS,
    BINDING_NECK_FACTOR,
    BINDING_HEADSTOCK_FACTOR,
    NECK_FACTORS,
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
    get_wbs_total_hours,
    WBSTaskTemplate,
)
from .learning_curve import (
    generate_learning_curve_projection,
    crawford_average_time,
)
from .material_yield import (
    estimate_material_costs,
    get_yield_factor,
)

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
    """

    # Default blended hourly rate (weighted average across task types)
    DEFAULT_HOURLY_RATE = 45.0

    # Confidence thresholds
    CONFIDENCE_HIGH_THRESHOLD = 1.15   # Total multiplier < 1.15 = high confidence
    CONFIDENCE_LOW_THRESHOLD = 1.40    # Total multiplier > 1.40 = low confidence

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

        # 6. Calculate material costs
        material_breakdown = self._estimate_materials(
            request.instrument_type,
            request.complexity,
            request.include_material_waste,
        )
        material_cost_per_unit = sum(m.adjusted_cost for m in material_breakdown)

        # 7. Calculate labor costs
        hourly_rate = request.hourly_rate_override or self.DEFAULT_HOURLY_RATE
        labor_cost_per_unit = avg_hours * hourly_rate

        # 8. Total costs
        total_cost_per_unit = labor_cost_per_unit + material_cost_per_unit
        total_project_cost = total_cost_per_unit * request.quantity

        # 9. Assess confidence and risks
        combined_multiplier = total_complexity * exp_factor
        confidence_level = self._assess_confidence(combined_multiplier, request)
        risk_factors = self._identify_risks(request, combined_multiplier)

        # 10. Calculate estimate range
        range_factor = self._get_range_factor(confidence_level)
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
        range_factor = self._get_range_factor(estimate.confidence_level)
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

    def _estimate_materials(
        self,
        instrument_type: InstrumentType,
        complexity: ComplexitySelections,
        include_waste: bool,
    ) -> List[MaterialEstimate]:
        """Estimate material costs with waste factors."""
        # Get BOM template if available
        try:
            from ..schemas import InstrumentType as BOMInstrumentType
            # Map to BOM instrument type
            bom_type_map = {
                InstrumentType.ACOUSTIC_DREADNOUGHT: "acoustic_dreadnought",
                InstrumentType.CLASSICAL: "classical",
            }
            bom_type = bom_type_map.get(instrument_type)

            if bom_type:
                bom = self.bom_service.create_bom_from_template(
                    instrument_type=bom_type,
                    instrument_name="Estimate",
                )
                items = [
                    {
                        "material_id": item.material_id,
                        "unit_cost": item.unit_cost,
                        "quantity": item.quantity,
                    }
                    for item in bom.items
                ]
                return estimate_material_costs(items, include_waste)
        except Exception:
            pass

        # Fallback: generic estimates by instrument type
        if instrument_type.value.startswith("acoustic"):
            return self._acoustic_material_estimate(include_waste)
        elif "electric" in instrument_type.value or "bass" in instrument_type.value:
            return self._electric_material_estimate(complexity, include_waste)
        else:
            return self._acoustic_material_estimate(include_waste)

    def _acoustic_material_estimate(self, include_waste: bool) -> List[MaterialEstimate]:
        """Generic acoustic guitar material estimate."""
        items = [
            {"material_id": "top_set_premium", "unit_cost": 120, "quantity": 1},
            {"material_id": "back_set_premium", "unit_cost": 180, "quantity": 1},
            {"material_id": "neck_blank_quartersawn", "unit_cost": 80, "quantity": 1},
            {"material_id": "fretboard_ebony", "unit_cost": 45, "quantity": 1},
            {"material_id": "binding_wood", "unit_cost": 25, "quantity": 1},
            {"material_id": "brace_stock_spruce", "unit_cost": 20, "quantity": 1},
            {"material_id": "tuners", "unit_cost": 80, "quantity": 1},
            {"material_id": "fret_wire", "unit_cost": 15, "quantity": 1},
            {"material_id": "finish_lacquer", "unit_cost": 60, "quantity": 1},
            {"material_id": "glue", "unit_cost": 20, "quantity": 1},
        ]
        return estimate_material_costs(items, include_waste)

    def _electric_material_estimate(
        self,
        complexity: ComplexitySelections,
        include_waste: bool,
    ) -> List[MaterialEstimate]:
        """Generic electric guitar material estimate."""
        items = [
            {"material_id": "body_blank", "unit_cost": 100, "quantity": 1},
            {"material_id": "neck_blank_maple", "unit_cost": 70, "quantity": 1},
            {"material_id": "fretboard_rosewood", "unit_cost": 35, "quantity": 1},
            {"material_id": "tuners", "unit_cost": 60, "quantity": 1},
            {"material_id": "bridge", "unit_cost": 50, "quantity": 1},
            {"material_id": "fret_wire", "unit_cost": 15, "quantity": 1},
            {"material_id": "finish_lacquer", "unit_cost": 50, "quantity": 1},
        ]

        # Add pickups based on complexity
        if complexity.pickup_count > 0:
            pickup_cost = 80 * complexity.pickup_count
            items.append({"material_id": "pickups", "unit_cost": pickup_cost, "quantity": 1})
            items.append({"material_id": "electronics", "unit_cost": 40, "quantity": 1})

        return estimate_material_costs(items, include_waste)

    def _assess_confidence(
        self,
        combined_multiplier: float,
        request: EstimateRequest,
    ) -> str:
        """Assess estimate confidence level."""
        # Higher multiplier = more complexity = less confidence
        if combined_multiplier < self.CONFIDENCE_HIGH_THRESHOLD:
            return "high"
        elif combined_multiplier > self.CONFIDENCE_LOW_THRESHOLD:
            return "low"
        else:
            return "medium"

    def _identify_risks(
        self,
        request: EstimateRequest,
        combined_multiplier: float,
    ) -> List[RiskFactor]:
        """Identify risk factors affecting estimate."""
        risks = []

        # Beginner builder risk
        if request.builder_experience == BuilderExperience.BEGINNER:
            risks.append(RiskFactor(
                factor="Beginner Experience",
                impact="high",
                description="First-time builders may take 2-3x longer than estimated",
            ))

        # High complexity risk
        if combined_multiplier > 1.5:
            risks.append(RiskFactor(
                factor="High Complexity",
                impact="medium",
                description="Multiple complex features increase variability",
            ))

        # French polish risk
        if request.complexity.finish == FinishType.SHELLAC_FRENCH_POLISH:
            risks.append(RiskFactor(
                factor="French Polish Finish",
                impact="medium",
                description="French polish is highly skill-dependent; time varies widely",
            ))

        # Custom inlay risk
        from .schemas import FretboardInlay
        if request.complexity.fretboard_inlay == FretboardInlay.CUSTOM:
            risks.append(RiskFactor(
                factor="Custom Inlay",
                impact="medium",
                description="Custom inlay design and execution time varies significantly",
            ))

        # Multi-scale risk
        from .schemas import NeckComplexity
        if NeckComplexity.MULTI_SCALE in request.complexity.neck:
            risks.append(RiskFactor(
                factor="Multi-Scale Frets",
                impact="medium",
                description="Fan fret layout requires precise calculation and execution",
            ))

        # Large batch risk
        if request.quantity > 6:
            risks.append(RiskFactor(
                factor="Large Batch",
                impact="low",
                description="Learning curve projections less certain for batches >6",
            ))

        return risks

    def _get_range_factor(self, confidence_level: str) -> float:
        """Get estimate range factor based on confidence."""
        return {
            "high": 0.10,    # ±10%
            "medium": 0.20,  # ±20%
            "low": 0.35,     # ±35%
        }.get(confidence_level, 0.25)
