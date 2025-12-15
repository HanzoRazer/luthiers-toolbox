"""
Treble Bleed Circuit Calculator
Migrated from: server/pipelines/wiring/treble_bleed.py
Status: Medium Priority Pipeline

Calculates optimal treble bleed capacitor and resistor values
based on potentiometer value, cable capacitance, and circuit style.

Treble bleed circuits preserve high frequencies when volume is reduced.
"""
from typing import Dict, Any, Optional
import math


# Common capacitor values (in picofarads)
COMMON_CAPS_PF = [100, 150, 220, 330, 470, 680, 1000, 1500, 2200]

# Common resistor values (in ohms)
COMMON_RESISTORS = [100e3, 150e3, 220e3, 330e3, 470e3]


def recommend(
    pot_ohm: int = 500000,
    cable_pf: int = 500,
    style: str = 'parallel'
) -> Dict[str, Any]:
    """
    Recommend treble bleed component values.
    
    Args:
        pot_ohm: Volume pot value in ohms (250k, 500k, 1M)
        cable_pf: Cable capacitance in picofarads (typically 300-1000pF)
        style: Circuit style:
            - 'cap-only': Just a capacitor (simplest, can be harsh)
            - 'parallel': Cap + resistor in parallel (most common)
            - 'series': Cap + resistor in series (warmer, less treble)
    
    Returns:
        Dictionary with:
            - cap_pf: Recommended capacitor value in picofarads
            - cap_nf: Same value in nanofarads
            - resistor_ohm: Recommended resistor (parallel/series only)
            - style: The circuit style
            - cutoff_hz: Approximate high-pass cutoff frequency
            - notes: Usage notes
    """
    # Target cutoff frequency (Hz) - higher for brighter sound
    # Rule of thumb: higher pot values need smaller caps
    base_cutoff = 2000  # 2kHz base cutoff
    
    # Calculate ideal capacitance
    # f = 1 / (2 * pi * R * C)
    # C = 1 / (2 * pi * R * f)
    ideal_cap_f = 1 / (2 * math.pi * pot_ohm * base_cutoff)
    ideal_cap_pf = ideal_cap_f * 1e12
    
    # Find nearest standard capacitor value
    cap_pf = min(COMMON_CAPS_PF, key=lambda c: abs(c - ideal_cap_pf))
    cap_nf = cap_pf / 1000
    
    # Calculate actual cutoff with chosen cap
    actual_cutoff = 1 / (2 * math.pi * pot_ohm * (cap_pf * 1e-12))
    
    # Resistor recommendation (for parallel/series styles)
    resistor_ohm: Optional[float] = None
    notes = []
    
    if style == 'cap-only':
        notes.append("Simplest circuit - may sound harsh at low volumes")
        notes.append("Good for high-gain or already dark pickups")
    
    elif style == 'parallel':
        # Parallel resistor should be close to pot value for smooth taper
        ideal_r = pot_ohm * 0.3  # 30% of pot value is common starting point
        resistor_ohm = min(COMMON_RESISTORS, key=lambda r: abs(r - ideal_r))
        notes.append("Most popular configuration")
        notes.append("Provides smooth volume taper with treble preservation")
        notes.append(f"Resistor bleeds some signal at all positions")
    
    elif style == 'series':
        # Series resistor limits max treble boost
        ideal_r = pot_ohm * 0.5  # 50% of pot value
        resistor_ohm = min(COMMON_RESISTORS, key=lambda r: abs(r - ideal_r))
        notes.append("Warmer sound than parallel or cap-only")
        notes.append("Better for already bright guitars/pickups")
        notes.append("Smoother transition but less treble retention")
    
    else:
        style = 'parallel'  # Default fallback
        resistor_ohm = min(COMMON_RESISTORS, key=lambda r: abs(r - pot_ohm * 0.3))
        notes.append("Unknown style - defaulted to parallel")
    
    # Format resistor for display
    resistor_display = None
    if resistor_ohm:
        if resistor_ohm >= 1e6:
            resistor_display = f"{resistor_ohm/1e6:.1f}M"
        else:
            resistor_display = f"{resistor_ohm/1e3:.0f}k"
    
    return {
        'cap_pf': cap_pf,
        'cap_nf': cap_nf,
        'cap_display': f"{cap_pf}pF" if cap_pf < 1000 else f"{cap_nf:.1f}nF",
        'resistor_ohm': resistor_ohm,
        'resistor_display': resistor_display,
        'style': style,
        'cutoff_hz': round(actual_cutoff),
        'pot_ohm': pot_ohm,
        'cable_pf': cable_pf,
        'notes': notes,
    }


def format_circuit(result: Dict[str, Any]) -> str:
    """Format result as ASCII circuit diagram."""
    style = result['style']
    cap = result['cap_display']
    res = result.get('resistor_display', '')
    
    if style == 'cap-only':
        return f"""
Volume Pot Lug 1 ----||---- Volume Pot Wiper
                    {cap}
"""
    elif style == 'parallel':
        return f"""
                  +--||---+
                  | {cap:^5} |
Pot Lug 1 --------+       +-------- Pot Wiper
                  |       |
                  +--/\\/\\--+
                    {res}
"""
    elif style == 'series':
        return f"""
Pot Lug 1 ----||----/\\/\\---- Pot Wiper
              {cap}   {res}
"""
    return ""


# CLI entry point
if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python treble_bleed.py <pot_kohm> [cable_pf] [style]")
        print("\nStyles: cap-only, parallel, series")
        print("\nExample:")
        print("  python treble_bleed.py 500 500 parallel")
        print("  python treble_bleed.py 250 300 series")
        sys.exit(1)
    
    pot_kohm = int(sys.argv[1])
    pot_ohm = pot_kohm * 1000 if pot_kohm < 1000 else pot_kohm
    cable_pf = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    style = sys.argv[3] if len(sys.argv) > 3 else 'parallel'
    
    result = recommend(pot_ohm, cable_pf, style)
    print(json.dumps(result, indent=2))
    print(format_circuit(result))
