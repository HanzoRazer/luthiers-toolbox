"""
Impedance Math for Guitar Electronics

Calculates impedance-related values for passive guitar circuits.

MODEL NOTES:
- Guitar pickups are essentially inductors with resistance
- Typical single coil: 5-8K DCR, 2-3H inductance
- Typical humbucker: 7-15K DCR, 3-6H inductance
- Volume/tone pots load the pickup, affecting frequency response
- Cable capacitance also affects high-frequency rolloff

Formulas:
- Parallel resistance: 1/R_total = 1/R1 + 1/R2 + ...
- RC rolloff: f_cutoff = 1 / (2 * π * R * C)
- Pickup resonant peak: f_peak = 1 / (2 * π * sqrt(L * C))
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ToneRolloffResult:
    """Result from tone rolloff calculation."""
    cutoff_frequency_hz: float
    rolloff_db_per_octave: float  # Typically -6dB for single RC
    description: str


@dataclass
class PickupLoadResult:
    """Result from pickup loading calculation."""
    total_load_kohm: float
    resonant_peak_hz: Optional[float]
    peak_shift_description: str


def calculate_parallel_resistance(*resistances_kohm: float) -> float:
    """
    Calculate parallel resistance of multiple resistors.

    Args:
        *resistances_kohm: Resistance values in kohms

    Returns:
        Total parallel resistance in kohms
    """
    if not resistances_kohm:
        return 0.0

    # Filter out zeros and infinities
    valid = [r for r in resistances_kohm if r > 0 and r < float('inf')]

    if not valid:
        return 0.0

    if len(valid) == 1:
        return valid[0]

    # 1/R_total = sum(1/R_i)
    reciprocal_sum = sum(1.0 / r for r in valid)
    return 1.0 / reciprocal_sum


def calculate_tone_rolloff(
    pot_value_kohm: float,
    capacitor_nf: float,
    pot_position: float = 0.0,  # 0 = full bass cut, 1 = full treble
) -> ToneRolloffResult:
    """
    Calculate tone control rolloff frequency.

    Args:
        pot_value_kohm: Tone pot value in kohms
        capacitor_nf: Tone cap value in nanofarads
        pot_position: Pot position 0-1 (0 = rolled off, 1 = full up)

    Returns:
        ToneRolloffResult with cutoff frequency
    """
    if pot_value_kohm <= 0 or capacitor_nf <= 0:
        return ToneRolloffResult(
            cutoff_frequency_hz=20000.0,
            rolloff_db_per_octave=0.0,
            description="Invalid parameters",
        )

    # Effective resistance decreases as pot is turned down
    # At position 0, full cap is in circuit
    # At position 1, cap is effectively out of circuit
    effective_pot = pot_value_kohm * max(0.01, 1.0 - pot_position)

    # Convert to base units
    r_ohms = effective_pot * 1000.0
    c_farads = capacitor_nf * 1e-9

    # RC cutoff: f = 1 / (2πRC)
    cutoff = 1.0 / (2.0 * math.pi * r_ohms * c_farads)

    # Describe the result
    if pot_position > 0.95:
        description = "Tone fully up - minimal effect"
    elif cutoff < 1000:
        description = f"Heavy bass cut - {cutoff:.0f}Hz cutoff (dark/muffled)"
    elif cutoff < 3000:
        description = f"Moderate rolloff - {cutoff:.0f}Hz cutoff (warm)"
    else:
        description = f"Light rolloff - {cutoff:.0f}Hz cutoff (slightly darker)"

    return ToneRolloffResult(
        cutoff_frequency_hz=cutoff,
        rolloff_db_per_octave=-6.0,  # Single-pole RC filter
        description=description,
    )


def calculate_pickup_load(
    pickup_dcr_kohm: float,
    pickup_inductance_h: float,
    volume_pot_kohm: float,
    tone_pot_kohm: float,
    cable_capacitance_pf: float = 500.0,  # Typical 15ft cable
    tone_cap_nf: float = 22.0,
    tone_position: float = 1.0,  # Full up by default
) -> PickupLoadResult:
    """
    Calculate how volume/tone pots and cable load a pickup.

    Args:
        pickup_dcr_kohm: Pickup DC resistance in kohms
        pickup_inductance_h: Pickup inductance in Henries
        volume_pot_kohm: Volume pot value
        tone_pot_kohm: Tone pot value
        cable_capacitance_pf: Cable capacitance in picofarads
        tone_cap_nf: Tone capacitor in nanofarads
        tone_position: Tone pot position 0-1

    Returns:
        PickupLoadResult with loading info
    """
    # Total load from pots (parallel)
    pot_load = calculate_parallel_resistance(volume_pot_kohm, tone_pot_kohm)

    # Total capacitance
    # Cable always present, tone cap contributes based on position
    cable_nf = cable_capacitance_pf / 1000.0
    effective_tone_cap = tone_cap_nf * (1.0 - tone_position)  # Full effect when rolled off
    total_cap_nf = cable_nf + effective_tone_cap

    # Calculate resonant peak
    # f = 1 / (2π * sqrt(L * C))
    if pickup_inductance_h > 0 and total_cap_nf > 0:
        l_henries = pickup_inductance_h
        c_farads = total_cap_nf * 1e-9
        resonant_peak = 1.0 / (2.0 * math.pi * math.sqrt(l_henries * c_farads))
    else:
        resonant_peak = None

    # Describe the peak shift
    if resonant_peak is None:
        description = "Cannot calculate resonant peak"
    elif resonant_peak > 8000:
        description = f"Bright setup - peak at {resonant_peak:.0f}Hz"
    elif resonant_peak > 4000:
        description = f"Balanced - peak at {resonant_peak:.0f}Hz"
    elif resonant_peak > 2000:
        description = f"Warm/vintage - peak at {resonant_peak:.0f}Hz"
    else:
        description = f"Dark/muddy - peak at {resonant_peak:.0f}Hz (high capacitance)"

    return PickupLoadResult(
        total_load_kohm=pot_load,
        resonant_peak_hz=resonant_peak,
        peak_shift_description=description,
    )


def suggest_cable_length(
    desired_brightness: float = 0.5,  # 0 = dark, 1 = bright
    pickup_inductance_h: float = 2.5,
) -> dict:
    """
    Suggest maximum cable length for desired tone.

    Args:
        desired_brightness: Brightness preference 0-1
        pickup_inductance_h: Pickup inductance in Henries

    Returns:
        Dict with suggested cable length and capacitance budget
    """
    # Brighter = lower capacitance = shorter cable
    # Typical cable: 30-40 pF per foot

    # Target resonant peak based on brightness
    target_peak_hz = 2500 + (desired_brightness * 6000)  # 2.5kHz to 8.5kHz

    # Solve for C: C = 1 / (4π²f²L)
    c_farads = 1.0 / (4.0 * math.pi**2 * target_peak_hz**2 * pickup_inductance_h)
    c_pf = c_farads * 1e12

    # Assuming 35pF per foot average
    pf_per_foot = 35.0
    max_feet = c_pf / pf_per_foot

    return {
        "max_cable_feet": round(max_feet, 1),
        "max_cable_meters": round(max_feet * 0.3048, 1),
        "capacitance_budget_pf": round(c_pf, 0),
        "target_resonant_peak_hz": round(target_peak_hz, 0),
        "note": f"For {desired_brightness:.0%} brightness with {pickup_inductance_h}H pickup",
    }
