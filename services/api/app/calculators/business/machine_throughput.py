"""
Machine Throughput Calculator

Estimates production capacity and bottlenecks for CNC equipment.

MODEL NOTES:
- Considers:
  - Cycle time per part
  - Setup time between jobs
  - Tool change time
  - Material loading/unloading
  - Machine availability (maintenance, breaks)
- OEE (Overall Equipment Effectiveness) = Availability × Performance × Quality
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ThroughputResult:
    """Result from throughput calculation."""
    parts_per_hour: float
    parts_per_shift: float
    parts_per_week: float
    utilization_percent: float
    bottleneck: str
    notes: str


@dataclass
class JobTiming:
    """Timing breakdown for a job."""
    job_name: str
    cycle_time_min: float
    setup_time_min: float
    parts_per_run: int


def estimate_throughput(
    cycle_time_min: float,
    setup_time_min: float = 0.0,
    parts_per_setup: int = 1,
    *,
    shift_hours: float = 8.0,
    shifts_per_week: int = 5,
    availability_percent: float = 85.0,  # Account for maintenance, breaks
    performance_percent: float = 90.0,   # Actual vs theoretical speed
    quality_percent: float = 98.0,       # Good parts vs total parts
) -> ThroughputResult:
    """
    Estimate machine throughput for a given job.

    Args:
        cycle_time_min: Time to machine one part (minutes)
        setup_time_min: Setup time before running (minutes)
        parts_per_setup: Parts produced per setup
        shift_hours: Hours per shift
        shifts_per_week: Shifts per week
        availability_percent: Machine availability (OEE factor)
        performance_percent: Speed efficiency (OEE factor)
        quality_percent: Quality rate (OEE factor)

    Returns:
        ThroughputResult with throughput estimates
    """
    if cycle_time_min <= 0:
        return ThroughputResult(
            parts_per_hour=0.0,
            parts_per_shift=0.0,
            parts_per_week=0.0,
            utilization_percent=0.0,
            bottleneck="Invalid cycle time",
            notes="Cycle time must be positive",
        )

    # Calculate OEE
    oee = (availability_percent / 100) * (performance_percent / 100) * (quality_percent / 100)

    # Effective time per part including setup amortization
    setup_per_part = setup_time_min / parts_per_setup if parts_per_setup > 0 else setup_time_min
    effective_cycle = cycle_time_min + setup_per_part

    # Theoretical parts per hour
    theoretical_per_hour = 60.0 / effective_cycle

    # Apply OEE for realistic estimate
    actual_per_hour = theoretical_per_hour * oee

    # Scale to shift and week
    shift_minutes = shift_hours * 60
    available_minutes = shift_minutes * (availability_percent / 100)
    parts_per_shift = (available_minutes / effective_cycle) * (performance_percent / 100) * (quality_percent / 100)

    parts_per_week = parts_per_shift * shifts_per_week

    # Determine bottleneck
    if setup_per_part > cycle_time_min:
        bottleneck = "Setup time dominates - batch larger or reduce setups"
    elif availability_percent < 80:
        bottleneck = "Low availability - address maintenance/downtime"
    elif performance_percent < 85:
        bottleneck = "Performance gap - check feeds/speeds optimization"
    elif quality_percent < 95:
        bottleneck = "Quality issues - review process and tooling"
    else:
        bottleneck = "Cycle time is primary constraint"

    # Calculate utilization
    utilization = (effective_cycle * actual_per_hour) / 60 * 100

    notes = f"OEE: {oee*100:.1f}% ({availability_percent:.0f}% × {performance_percent:.0f}% × {quality_percent:.0f}%)"

    return ThroughputResult(
        parts_per_hour=round(actual_per_hour, 1),
        parts_per_shift=round(parts_per_shift, 0),
        parts_per_week=round(parts_per_week, 0),
        utilization_percent=round(utilization, 1),
        bottleneck=bottleneck,
        notes=notes,
    )


def compare_job_mix(
    jobs: List[JobTiming],
    shift_hours: float = 8.0,
    shifts_per_week: int = 5,
) -> dict:
    """
    Analyze a mix of different jobs for capacity planning.

    Args:
        jobs: List of JobTiming specifications
        shift_hours: Hours per shift
        shifts_per_week: Shifts per week

    Returns:
        Dict with capacity analysis
    """
    if not jobs:
        return {"error": "No jobs provided"}

    total_time_per_week_min = shift_hours * 60 * shifts_per_week

    results = []
    total_required_min = 0.0

    for job in jobs:
        # Time needed for this job's batch
        job_time = job.setup_time_min + (job.cycle_time_min * job.parts_per_run)
        total_required_min += job_time

        results.append({
            "job": job.job_name,
            "cycle_min": job.cycle_time_min,
            "setup_min": job.setup_time_min,
            "parts": job.parts_per_run,
            "total_min": round(job_time, 1),
            "percent_of_capacity": round(job_time / total_time_per_week_min * 100, 1),
        })

    capacity_used = (total_required_min / total_time_per_week_min) * 100
    remaining_min = total_time_per_week_min - total_required_min

    return {
        "jobs": results,
        "total_required_min": round(total_required_min, 1),
        "total_available_min": round(total_time_per_week_min, 1),
        "remaining_min": round(remaining_min, 1),
        "capacity_used_percent": round(capacity_used, 1),
        "can_accommodate": capacity_used <= 100,
        "recommendation": (
            "Capacity available for more work"
            if capacity_used < 80
            else "Near capacity - consider overtime or additional equipment"
            if capacity_used < 100
            else "OVER CAPACITY - cannot complete all jobs"
        ),
    }


def estimate_lead_time(
    parts_needed: int,
    cycle_time_min: float,
    setup_time_min: float = 0.0,
    *,
    shift_hours: float = 8.0,
    availability_percent: float = 85.0,
) -> dict:
    """
    Estimate lead time to produce a quantity of parts.

    Args:
        parts_needed: Number of parts to produce
        cycle_time_min: Cycle time per part
        setup_time_min: Initial setup time
        shift_hours: Hours per shift
        availability_percent: Machine availability

    Returns:
        Dict with lead time estimate
    """
    if parts_needed <= 0 or cycle_time_min <= 0:
        return {"error": "Invalid parameters"}

    # Total machining time
    total_machining_min = setup_time_min + (cycle_time_min * parts_needed)

    # Available time per shift
    available_per_shift = shift_hours * 60 * (availability_percent / 100)

    # Shifts needed
    shifts_needed = total_machining_min / available_per_shift
    days_needed = shifts_needed  # Assuming 1 shift per day

    return {
        "parts": parts_needed,
        "total_machining_hours": round(total_machining_min / 60, 1),
        "shifts_needed": round(shifts_needed, 1),
        "days_needed": round(days_needed, 1),
        "weeks_needed": round(days_needed / 5, 1),
        "note": f"Based on {availability_percent}% availability, {shift_hours}hr shifts",
    }
