# test_post_presets.py
# Unit test for post_presets module (no server required)

import sys
sys.path.insert(0, './services/api')

from app.utils.post_presets import (
    get_post_preset,
    get_dwell_command,
    list_presets,
    PRESETS
)

def test_presets():
    print("=== Post-Processor Presets Unit Test ===\n")
    
    # Test 1: List all presets
    print("[Test 1] List all presets")
    presets = list_presets()
    print(f"  Available: {', '.join(presets.keys())}")
    assert len(presets) == 4, "Should have 4 presets"
    print("  ✅ PASS\n")
    
    # Test 2: GRBL preset
    print("[Test 2] GRBL preset")
    grbl = get_post_preset("GRBL")
    assert grbl.name == "GRBL"
    assert grbl.use_r_mode == False, "GRBL should use I,J mode"
    assert grbl.dwell_in_seconds == False, "GRBL should use milliseconds"
    print(f"  Name: {grbl.name}")
    print(f"  Arc mode: {'R' if grbl.use_r_mode else 'I,J'}")
    print(f"  Dwell: {'G4 S (seconds)' if grbl.dwell_in_seconds else 'G4 P (ms)'}")
    print("  ✅ PASS\n")
    
    # Test 3: Haas preset (special case)
    print("[Test 3] Haas preset")
    haas = get_post_preset("Haas")
    assert haas.name == "Haas"
    assert haas.use_r_mode == True, "Haas should use R mode"
    assert haas.dwell_in_seconds == True, "Haas should use seconds"
    print(f"  Name: {haas.name}")
    print(f"  Arc mode: {'R' if haas.use_r_mode else 'I,J'}")
    print(f"  Dwell: {'G4 S (seconds)' if haas.dwell_in_seconds else 'G4 P (ms)'}")
    print("  ✅ PASS\n")
    
    # Test 4: Dwell command generation (GRBL)
    print("[Test 4] Dwell command (GRBL, 500ms)")
    dwell_grbl = get_dwell_command(500, grbl)
    assert dwell_grbl == "G4 P500", f"Expected 'G4 P500', got '{dwell_grbl}'"
    print(f"  Output: {dwell_grbl}")
    print("  ✅ PASS\n")
    
    # Test 5: Dwell command generation (Haas, 500ms → 0.5s)
    print("[Test 5] Dwell command (Haas, 500ms → 0.5s)")
    dwell_haas = get_dwell_command(500, haas)
    assert dwell_haas == "G4 S0.5", f"Expected 'G4 S0.5', got '{dwell_haas}'"
    print(f"  Input: 500ms")
    print(f"  Output: {dwell_haas} (converted to seconds)")
    print("  ✅ PASS\n")
    
    # Test 6: Zero dwell
    print("[Test 6] Zero dwell (should return empty string)")
    dwell_zero = get_dwell_command(0, grbl)
    assert dwell_zero == "", f"Expected empty string, got '{dwell_zero}'"
    print(f"  Output: '{dwell_zero}' (empty)")
    print("  ✅ PASS\n")
    
    # Test 7: Default preset (None → GRBL)
    print("[Test 7] Default preset (None → GRBL)")
    default = get_post_preset(None)
    assert default.name == "GRBL", "Default should be GRBL"
    print(f"  Default: {default.name}")
    print("  ✅ PASS\n")
    
    # Test 8: Invalid preset
    print("[Test 8] Invalid preset (should raise ValueError)")
    try:
        invalid = get_post_preset("InvalidPreset")
        print("  ❌ FAIL - Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  Caught expected error: {e}")
        print("  ✅ PASS\n")
    
    # Test 9: All presets have required fields
    print("[Test 9] Validate all preset configurations")
    for name, preset in PRESETS.items():
        assert preset.name == name, f"{name}: name mismatch"
        assert isinstance(preset.use_r_mode, bool), f"{name}: use_r_mode not bool"
        assert isinstance(preset.dwell_in_seconds, bool), f"{name}: dwell_in_seconds not bool"
        print(f"  ✅ {name}: {preset.description}")
    print("  ✅ PASS\n")
    
    print("=== All Tests Passed ===")
    return True

if __name__ == "__main__":
    try:
        success = test_presets()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
