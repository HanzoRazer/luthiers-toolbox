"""
Learning Curve Models — Time reduction through repetition.

The learning curve effect: as you build more of the same design,
each unit takes less time. This is well-documented in manufacturing.

Two main models:
1. Crawford (Unit) Model: Each unit takes a fixed % of the previous
2. Wright (Cumulative Average) Model: Cumulative average decreases

For lutherie, Crawford model is more appropriate because:
- Small batches (1-12 units typically)
- Significant setup time per unit
- Hand work doesn't average as smoothly as assembly lines
"""
import math
from typing import List
from dataclasses import dataclass

from .schemas import LearningCurvePoint, LearningCurveProjection


# =============================================================================
# LEARNING RATE GUIDELINES
# =============================================================================

# Industry-standard learning rates by task type
LEARNING_RATES = {
    "hand_work": 0.90,       # 10% improvement per doubling (carving, shaping)
    "machine_work": 0.80,    # 20% improvement per doubling (routing, sanding)
    "assembly": 0.85,        # 15% improvement (gluing, fitting)
    "finishing": 0.88,       # 12% improvement (spraying, buffing)
    "setup": 0.75,           # 25% improvement (jigs, fixtures)
    "lutherie_blended": 0.85,  # Blended rate for guitar building
}


# =============================================================================
# CRAWFORD (UNIT) MODEL
# =============================================================================

def crawford_unit_time(
    first_unit_hours: float,
    unit_number: int,
    learning_rate: float = 0.85,
) -> float:
    """
    Calculate time for unit N using Crawford model.

    T_n = T_1 * n^b
    where b = log(learning_rate) / log(2)

    Args:
        first_unit_hours: Time for first unit
        unit_number: Which unit (1-indexed)
        learning_rate: Learning rate (0.85 = 15% reduction per doubling)

    Returns:
        Hours for unit N
    """
    if unit_number < 1:
        raise ValueError("Unit number must be >= 1")

    if unit_number == 1:
        return first_unit_hours

    b = math.log(learning_rate) / math.log(2)
    return first_unit_hours * (unit_number ** b)


def crawford_cumulative_time(
    first_unit_hours: float,
    quantity: int,
    learning_rate: float = 0.85,
) -> float:
    """
    Calculate total time for N units using Crawford model.

    Args:
        first_unit_hours: Time for first unit
        quantity: Number of units
        learning_rate: Learning rate

    Returns:
        Total hours for all units
    """
    return sum(
        crawford_unit_time(first_unit_hours, n, learning_rate)
        for n in range(1, quantity + 1)
    )


def crawford_average_time(
    first_unit_hours: float,
    quantity: int,
    learning_rate: float = 0.85,
) -> float:
    """
    Calculate average time per unit for N units.

    Args:
        first_unit_hours: Time for first unit
        quantity: Number of units
        learning_rate: Learning rate

    Returns:
        Average hours per unit
    """
    total = crawford_cumulative_time(first_unit_hours, quantity, learning_rate)
    return total / quantity


# =============================================================================
# WRIGHT (CUMULATIVE AVERAGE) MODEL
# =============================================================================

def wright_cumulative_average(
    first_unit_hours: float,
    unit_number: int,
    learning_rate: float = 0.85,
) -> float:
    """
    Calculate cumulative average time using Wright model.

    Y_n = T_1 * n^b (cumulative average through unit N)

    This model says the AVERAGE of all units through N follows the curve,
    not each individual unit.

    Args:
        first_unit_hours: Time for first unit
        unit_number: Which unit (1-indexed)
        learning_rate: Learning rate

    Returns:
        Cumulative average hours through unit N
    """
    if unit_number < 1:
        raise ValueError("Unit number must be >= 1")

    b = math.log(learning_rate) / math.log(2)
    return first_unit_hours * (unit_number ** b)


def wright_total_time(
    first_unit_hours: float,
    quantity: int,
    learning_rate: float = 0.85,
) -> float:
    """
    Calculate total time for N units using Wright model.

    Total = N * Y_N = N * T_1 * N^b = T_1 * N^(1+b)

    Args:
        first_unit_hours: Time for first unit
        quantity: Number of units
        learning_rate: Learning rate

    Returns:
        Total hours for all units
    """
    b = math.log(learning_rate) / math.log(2)
    return first_unit_hours * (quantity ** (1 + b))


# =============================================================================
# PROJECTION GENERATOR
# =============================================================================

def generate_learning_curve_projection(
    first_unit_hours: float,
    quantity: int,
    learning_rate: float = 0.85,
    hourly_rate: float = 45.0,
    model: str = "crawford",
) -> LearningCurveProjection:
    """
    Generate complete learning curve projection.

    Args:
        first_unit_hours: Time for first unit
        quantity: Number of units to project
        learning_rate: Learning rate
        hourly_rate: Labor rate for cost calculation
        model: "crawford" or "wright"

    Returns:
        LearningCurveProjection with all points
    """
    points: List[LearningCurvePoint] = []
    cumulative_hours = 0.0

    for n in range(1, quantity + 1):
        if model == "crawford":
            hours = crawford_unit_time(first_unit_hours, n, learning_rate)
        else:
            # Wright model: derive unit time from cumulative average
            if n == 1:
                hours = first_unit_hours
            else:
                # Unit time = N * avg(N) - (N-1) * avg(N-1)
                avg_n = wright_cumulative_average(first_unit_hours, n, learning_rate)
                avg_n1 = wright_cumulative_average(first_unit_hours, n - 1, learning_rate)
                hours = n * avg_n - (n - 1) * avg_n1

        cumulative_hours += hours

        points.append(LearningCurvePoint(
            unit_number=n,
            hours_per_unit=round(hours, 2),
            cumulative_hours=round(cumulative_hours, 2),
            cumulative_cost=round(cumulative_hours * hourly_rate, 2),
        ))

    # Calculate efficiency gain vs no learning
    no_learning_hours = first_unit_hours * quantity
    efficiency_gain = ((no_learning_hours - cumulative_hours) / no_learning_hours) * 100

    return LearningCurveProjection(
        first_unit_hours=first_unit_hours,
        learning_rate=learning_rate,
        quantity=quantity,
        points=points,
        average_hours_per_unit=round(cumulative_hours / quantity, 2),
        total_hours=round(cumulative_hours, 2),
        efficiency_gain_pct=round(efficiency_gain, 1),
    )


# =============================================================================
# BATCH SIZE OPTIMIZATION
# =============================================================================

def find_optimal_batch_size(
    first_unit_hours: float,
    target_hours_per_unit: float,
    learning_rate: float = 0.85,
    max_batch: int = 100,
) -> int:
    """
    Find minimum batch size to achieve target hours per unit.

    Args:
        first_unit_hours: Time for first unit
        target_hours_per_unit: Target average hours
        learning_rate: Learning rate
        max_batch: Maximum batch size to consider

    Returns:
        Minimum batch size to achieve target, or max_batch if not achievable
    """
    for n in range(1, max_batch + 1):
        avg = crawford_average_time(first_unit_hours, n, learning_rate)
        if avg <= target_hours_per_unit:
            return n

    return max_batch


def calculate_breakeven_batch_size(
    first_unit_hours: float,
    setup_hours: float,
    learning_rate: float = 0.85,
) -> int:
    """
    Find batch size where learning savings equal setup investment.

    If you spend X hours on jigs/fixtures, how many units until
    the time saved exceeds the setup time?

    Args:
        first_unit_hours: Time for first unit WITHOUT setup investment
        setup_hours: Hours invested in jigs/fixtures
        learning_rate: Learning rate

    Returns:
        Batch size where setup investment pays off
    """
    # With setup, first unit is faster. Model as improved learning.
    # This is a simplification - real setup effects are more complex.

    # For now, find where cumulative savings = setup hours
    cumulative_savings = 0.0
    n = 1

    while cumulative_savings < setup_hours and n < 1000:
        n += 1
        # Time without learning improvement
        naive_time = first_unit_hours
        # Time with learning
        learned_time = crawford_unit_time(first_unit_hours, n, learning_rate)
        cumulative_savings += (naive_time - learned_time)

    return n
