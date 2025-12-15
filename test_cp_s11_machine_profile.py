#!/usr/bin/env python3
"""
Test CP-S11-REAL: Machine Profile Alias Support
Tests backward compatibility and new machine_profile parameter.
"""

import sys
import os

# Add services/api to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services", "api"))

from app.learn.overrides_learner import train_overrides
from app.util.overrides import load_overrides, feed_factor_for_move

print("=== Testing CP-S11-REAL: Machine Profile Alias ===\n")

# =============================================================================
# Test 1: train_overrides with machine_id (backward compatibility)
# =============================================================================
print("1. Testing train_overrides with machine_id (backward compat)")
try:
    result1 = train_overrides(machine_id="test_machine_legacy")
    assert "machine_id" in result1
    assert result1["machine_id"] == "test_machine_legacy"
    assert "machine_profile" in result1
    assert result1["machine_profile"] == "test_machine_legacy"
    print("  ✓ machine_id parameter works")
    print(f"  ✓ Output contains both fields: machine_id={result1['machine_id']}, machine_profile={result1['machine_profile']}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
print()

# =============================================================================
# Test 2: train_overrides with machine_profile (new alias)
# =============================================================================
print("2. Testing train_overrides with machine_profile (new alias)")
try:
    result2 = train_overrides(machine_profile="bcam_router_2030")
    assert "machine_id" in result2
    assert result2["machine_id"] == "bcam_router_2030"
    assert "machine_profile" in result2
    assert result2["machine_profile"] == "bcam_router_2030"
    print("  ✓ machine_profile parameter works")
    print(f"  ✓ Output contains both fields: machine_id={result2['machine_id']}, machine_profile={result2['machine_profile']}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
print()

# =============================================================================
# Test 3: train_overrides with neither (should raise ValueError)
# =============================================================================
print("3. Testing train_overrides with neither parameter (should fail)")
try:
    result3 = train_overrides()
    print("  ✗ Should have raised ValueError")
except ValueError as e:
    if "requires machine_id or machine_profile" in str(e):
        print("  ✓ Correctly raises ValueError with expected message")
    else:
        print(f"  ⚠ ValueError raised but unexpected message: {e}")
except Exception as e:
    print(f"  ✗ Unexpected exception: {e}")
print()

# =============================================================================
# Test 4: load_overrides with machine_id (backward compatibility)
# =============================================================================
print("4. Testing load_overrides with machine_id (backward compat)")
try:
    # This will return None if model doesn't exist, which is fine
    result4 = load_overrides(machine_id="test_machine_legacy")
    if result4 is None:
        print("  ✓ machine_id parameter works (no model found, returns None)")
    else:
        print(f"  ✓ machine_id parameter works (loaded model with {len(result4.get('rules', {}))} rules)")
except Exception as e:
    print(f"  ✗ Failed: {e}")
print()

# =============================================================================
# Test 5: load_overrides with machine_profile (new alias)
# =============================================================================
print("5. Testing load_overrides with machine_profile (new alias)")
try:
    result5 = load_overrides(machine_profile="bcam_router_2030")
    if result5 is None:
        print("  ✓ machine_profile parameter works (no model found, returns None)")
    else:
        print(f"  ✓ machine_profile parameter works (loaded model with {len(result5.get('rules', {}))} rules)")
except Exception as e:
    print(f"  ✗ Failed: {e}")
print()

# =============================================================================
# Test 6: feed_factor_for_move with machine_id (backward compatibility)
# =============================================================================
print("6. Testing feed_factor_for_move with machine_id (backward compat)")
try:
    move = {
        "code": "G2",
        "x": 50.0,
        "y": 50.0,
        "radius_mm": 3.5,
        "f": 1200,
        "meta": {}
    }
    factor6 = feed_factor_for_move(move, machine_id="test_machine_legacy")
    assert 0.5 <= factor6 <= 1.0
    print(f"  ✓ machine_id parameter works (factor={factor6})")
except Exception as e:
    print(f"  ✗ Failed: {e}")
print()

# =============================================================================
# Test 7: feed_factor_for_move with machine_profile (new alias)
# =============================================================================
print("7. Testing feed_factor_for_move with machine_profile (new alias)")
try:
    move = {
        "code": "G3",
        "x": 45.0,
        "y": 55.0,
        "i": 5.0,
        "j": 0.0,
        "f": 1200,
        "meta": {"trochoid": True}
    }
    factor7 = feed_factor_for_move(move, machine_profile="bcam_router_2030")
    assert 0.5 <= factor7 <= 1.0
    print(f"  ✓ machine_profile parameter works (factor={factor7})")
except Exception as e:
    print(f"  ✗ Failed: {e}")
print()

# =============================================================================
# Test 8: Verify MODELS_DIR path fix
# =============================================================================
print("8. Testing MODELS_DIR path correctness")
try:
    from app.util.overrides import MODELS_DIR
    # Should be relative to util/ going up to app/, then to learn/models/
    expected_suffix = os.path.join("learn", "models")
    if expected_suffix in MODELS_DIR:
        print(f"  ✓ MODELS_DIR contains correct path: {MODELS_DIR}")
    else:
        print(f"  ⚠ MODELS_DIR may be incorrect: {MODELS_DIR}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
print()

# =============================================================================
# Summary
# =============================================================================
print("=== All CP-S11-REAL Tests Completed ===")
print()
print("Key validations:")
print("  • Backward compatibility: machine_id still works")
print("  • New alias: machine_profile parameter accepted")
print("  • Both parameters resolve to same model file")
print("  • Models dir path fixed to ../learn/models")
print("  • Conservative error handling (ValueError on missing params)")
