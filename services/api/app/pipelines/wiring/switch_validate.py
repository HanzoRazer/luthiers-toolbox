"""
Pickup Switch Combination Validator
Migrated from: server/pipelines/wiring/switch_validate.py
Status: Medium Priority Pipeline

Validates pickup combinations against switch hardware capabilities:
- 3-way switch: max 3 positions
- 5-way switch: max 5 positions
- Superswitch: up to 10 positions (5 positions × 2 poles)

Prevents impossible wiring configurations.
"""
from typing import List, Dict, Any


# Hardware position limits
HARDWARE_LIMITS = {
    '3-way': 3,
    '5-way': 5,
    'superswitch': 10,
    'freeway': 6,
    'rotary-6': 6,
    'rotary-12': 12,
}


def validate(hardware: str, combos: List[str]) -> Dict[str, Any]:
    """
    Validate pickup combinations against switch hardware.
    
    Args:
        hardware: Switch type ('3-way', '5-way', 'superswitch', etc.)
        combos: List of pickup combination names (e.g., ['Neck', 'Neck+Middle', 'Bridge'])
    
    Returns:
        Dictionary with:
            - valid: bool - True if all combos fit on hardware
            - hardware: str - The switch type
            - max_positions: int - Maximum positions for this hardware
            - combo_count: int - Number of requested combinations
            - message: str - Human-readable status
            - excess: int - How many combos exceed capacity (0 if valid)
    """
    hardware_lower = hardware.lower().replace(' ', '-')
    max_positions = HARDWARE_LIMITS.get(hardware_lower, 5)  # Default to 5-way
    
    combo_count = len(combos)
    excess = max(0, combo_count - max_positions)
    valid = combo_count <= max_positions
    
    if valid:
        message = f"✓ {combo_count} combinations fit on {hardware} ({max_positions} positions available)"
    else:
        message = f"✗ {combo_count} combinations exceed {hardware} capacity ({max_positions} positions). Remove {excess} combo(s)."
    
    return {
        'valid': valid,
        'hardware': hardware,
        'max_positions': max_positions,
        'combo_count': combo_count,
        'message': message,
        'excess': excess,
        'combos': combos,
    }


def suggest_hardware(combos: List[str]) -> List[str]:
    """
    Suggest compatible switch hardware for given combinations.
    
    Args:
        combos: List of pickup combination names
    
    Returns:
        List of compatible hardware types
    """
    combo_count = len(combos)
    compatible = []
    
    for hw, max_pos in sorted(HARDWARE_LIMITS.items(), key=lambda x: x[1]):
        if combo_count <= max_pos:
            compatible.append(hw)
    
    return compatible


# CLI entry point
if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 3:
        print("Usage: python switch_validate.py <hardware> <combo1> [combo2] ...")
        print("\nHardware types: 3-way, 5-way, superswitch, freeway, rotary-6, rotary-12")
        print("\nExample:")
        print("  python switch_validate.py 3-way Neck Middle Bridge")
        print("  python switch_validate.py 5-way Neck Neck+Mid Mid Mid+Bridge Bridge")
        sys.exit(1)
    
    hardware = sys.argv[1]
    combos = sys.argv[2:]
    
    result = validate(hardware, combos)
    print(json.dumps(result, indent=2))
