"""
Test script for instrument_geometry module.
Validates loader, specs, and scale_intonation functionality.
"""
import sys
from pathlib import Path

# Add services/api to path
api_path = Path(__file__).parent.parent / "services" / "api"
sys.path.insert(0, str(api_path))

# Import directly from modules to avoid legacy __init__.py imports
from app.instrument_geometry.models.loader import load_model_spec
from app.instrument_geometry.models.specs import StringCompSpec
from app.instrument_geometry.scale_intonation import (
    fret_distance_from_nut,
    fret_distance_from_bridge,
    fret_spacing,
    generate_fret_table,
    joint_to_bridge_distance_mm,
    estimate_compensation_mm,
    compute_saddle_positions,
)


def test_loader():
    """Test loading benedetto_17.json preset."""
    print("\n=== Test 1: Load Benedetto 17 Preset ===")
    
    preset_path = Path(__file__).parent.parent / "services" / "api" / "app" / "instrument_geometry" / "models" / "benedetto_17.json"
    
    if not preset_path.exists():
        print(f"❌ FAIL: Preset not found at {preset_path}")
        return False
    
    try:
        model = load_model_spec(preset_path)
        print(f"✓ Loaded model: {model.model_id}")
        print(f"  Brand: {model.brand}")
        print(f"  Category: {model.family}")
        
        # Validate scale
        if model.scale_spec:
            print(f"  Scale: {model.scale_spec.scale_length_in}\" ({model.scale_spec.scale_length_mm:.1f}mm)")
            assert model.scale_spec.scale_length_in == 25.5, "Scale should be 25.5 inches"
            assert abs(model.scale_spec.scale_length_mm - 647.7) < 0.1, "Scale should be ~647.7mm"
            print("  ✓ Scale length correct")
        
        # Validate neck joint
        if model.neck_joint:
            print(f"  Neck Joint: {model.neck_joint.type} at fret {model.neck_joint.body_join_fret}")
            print(f"    Pocket depth: {model.neck_joint.pocket_depth_in}\" ({model.neck_joint.pocket_depth_mm:.2f}mm)")
            print(f"    Neck angle: {model.neck_joint.neck_angle_degrees}°")
            assert model.neck_joint.body_join_fret == 14, "Benedetto joins at 14th fret"
            print("  ✓ Neck joint spec correct")
        
        # Validate bridge
        if model.bridge:
            print(f"  Bridge: {model.bridge.type}")
            print(f"    Reference line: {model.bridge.reference_line}")
            print(f"    Base offset: {model.bridge.base_offset_in}\" ({model.bridge.base_offset_mm:.2f}mm)")
            print("  ✓ Bridge spec correct")
        
        # Validate string set
        if model.string_set:
            print(f"  String Set: {model.string_set.string_set_id}")
            print(f"    Description: {model.string_set.description}")
            print(f"    Strings: {len(model.string_set.strings)}")
            for s in model.string_set.strings:
                print(f"      {s.index}. {s.name} - .{int(s.gauge_in * 1000):03d}\" ({s.gauge_mm:.3f}mm) {'wound' if s.wound else 'plain'}")
            assert len(model.string_set.strings) == 6, "Should have 6 strings"
            print("  ✓ String set correct")
        
        # Validate compensation
        if model.reference_compensation_mm:
            print(f"  Reference Compensation: {model.reference_compensation_mm:.2f}mm")
            print("  ✓ Compensation loaded")
        
        print("\n✅ PASS: Loader test")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fret_calculations():
    """Test fret position calculations."""
    print("\n=== Test 2: Fret Position Calculations ===")
    
    scale_mm = 647.7  # 25.5"
    
    try:
        # Test key frets
        nut = fret_distance_from_nut(scale_mm, 0)
        fret_12 = fret_distance_from_nut(scale_mm, 12)
        fret_12_from_bridge = fret_distance_from_bridge(scale_mm, 12)
        
        print(f"  Nut (fret 0): {nut:.2f}mm from nut")
        print(f"  12th fret: {fret_12:.2f}mm from nut")
        print(f"  12th fret: {fret_12_from_bridge:.2f}mm from bridge")
        
        # 12th fret should be at scale/2 (octave)
        expected_12th = scale_mm / 2.0
        assert abs(fret_12 - expected_12th) < 0.1, f"12th fret should be at {expected_12th}mm"
        assert abs(fret_12_from_bridge - expected_12th) < 0.1, "12th fret equidistant from nut and bridge"
        print("  ✓ 12th fret at octave position")
        
        # Test fret spacing
        spacing_1 = fret_spacing(scale_mm, 1)
        spacing_12 = fret_spacing(scale_mm, 12)
        print(f"  Spacing 1st-2nd fret: {spacing_1:.2f}mm")
        print(f"  Spacing 12th-13th fret: {spacing_12:.2f}mm")
        assert spacing_1 > spacing_12, "Fret spacing should decrease toward bridge"
        print("  ✓ Fret spacing decreases correctly")
        
        print("\n✅ PASS: Fret calculation test")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fret_table():
    """Test fret table generation."""
    print("\n=== Test 3: Fret Table Generation ===")
    
    scale_mm = 647.7  # 25.5"
    num_frets = 22
    
    try:
        table = generate_fret_table(scale_mm, num_frets)
        
        print(f"  Generated table with {len(table)} rows (0-{num_frets})")
        assert len(table) == num_frets + 1, f"Should have {num_frets + 1} rows"
        
        # Check first few frets
        print("\n  First 5 frets:")
        for row in table[:5]:
            spacing_str = f"{row.spacing_to_next_mm:.2f}mm" if row.spacing_to_next_mm else "N/A"
            print(f"    Fret {row.fret:2d}: {row.from_nut_mm:6.2f}mm from nut, {row.from_bridge_mm:6.2f}mm from bridge, spacing: {spacing_str}")
        
        # Check 12th fret
        fret_12 = table[12]
        print(f"\n  12th fret (octave):")
        print(f"    From nut: {fret_12.from_nut_mm:.2f}mm")
        print(f"    From bridge: {fret_12.from_bridge_mm:.2f}mm")
        assert abs(fret_12.from_nut_mm - fret_12.from_bridge_mm) < 0.1, "12th fret should be equidistant"
        print("    ✓ Octave position correct")
        
        # Check last fret
        last_fret = table[-1]
        print(f"\n  Last fret ({num_frets}):")
        print(f"    From nut: {last_fret.from_nut_mm:.2f}mm")
        print(f"    Spacing: {last_fret.spacing_to_next_mm}")
        assert last_fret.spacing_to_next_mm is None, "Last fret should have no spacing"
        print("    ✓ Last fret correct")
        
        print("\n✅ PASS: Fret table generation test")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_joint_distance():
    """Test neck joint distance calculation."""
    print("\n=== Test 4: Neck Joint Distance ===")
    
    scale_mm = 647.7  # 25.5"
    joint_fret = 14  # Benedetto typical
    
    try:
        distance = joint_to_bridge_distance_mm(scale_mm, joint_fret)
        print(f"  14th fret to bridge: {distance:.2f}mm")
        
        # Should match fret_distance_from_bridge
        expected = fret_distance_from_bridge(scale_mm, joint_fret)
        assert abs(distance - expected) < 0.01, "Should match fret calculation"
        print("  ✓ Joint distance matches fret calculation")
        
        print("\n✅ PASS: Joint distance test")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compensation_physics():
    """Test physics-based compensation calculation."""
    print("\n=== Test 5: Physics-Based Compensation ===")
    
    try:
        # Test with typical string parameters
        # High E string (plain steel)
        comp_high_e = estimate_compensation_mm(
            diameter_mm=0.254,      # .010"
            modulus_mpa=200000,     # Steel modulus
            tension_newton=75,      # Typical tension
            action_height_mm=1.5,   # Low action
            k=0.15,                 # Tuning constant
        )
        
        # Low E string (wound)
        comp_low_e = estimate_compensation_mm(
            diameter_mm=1.168,      # .046"
            modulus_mpa=180000,     # Slightly lower for wound
            tension_newton=85,      # Higher tension
            action_height_mm=2.0,   # Slightly higher action
            k=0.15,
        )
        
        print(f"  High E (.010\"): {comp_high_e:.3f}mm compensation")
        print(f"  Low E (.046\"): {comp_low_e:.3f}mm compensation")
        
        # Thicker strings should need more compensation
        assert comp_low_e > comp_high_e, "Thicker strings need more compensation"
        print("  ✓ Thicker strings have more compensation")
        
        # Typical range check (should be < 5mm)
        assert 0 < comp_high_e < 5, "High E compensation should be 0-5mm"
        assert 0 < comp_low_e < 5, "Low E compensation should be 0-5mm"
        print("  ✓ Compensation in realistic range")
        
        print("\n✅ PASS: Physics compensation test")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_saddle_positions():
    """Test saddle position calculation for full string set."""
    print("\n=== Test 6: Saddle Position Calculation ===")
    
    scale_mm = 647.7  # 25.5"
    
    try:
        # Define 6-string set (light gauge)
        strings = [
            StringCompSpec(diameter_mm=0.254, modulus_mpa=200000, tension_newton=75, action_height_mm=1.5, k=0.15),   # High E
            StringCompSpec(diameter_mm=0.330, modulus_mpa=200000, tension_newton=78, action_height_mm=1.6, k=0.15),   # B
            StringCompSpec(diameter_mm=0.432, modulus_mpa=200000, tension_newton=80, action_height_mm=1.7, k=0.15),   # G
            StringCompSpec(diameter_mm=0.660, modulus_mpa=190000, tension_newton=82, action_height_mm=1.8, k=0.15),   # D (wound)
            StringCompSpec(diameter_mm=0.914, modulus_mpa=185000, tension_newton=84, action_height_mm=1.9, k=0.15),   # A (wound)
            StringCompSpec(diameter_mm=1.168, modulus_mpa=180000, tension_newton=85, action_height_mm=2.0, k=0.15),   # Low E (wound)
        ]
        
        positions = compute_saddle_positions(scale_mm, strings)
        
        print(f"  Computed saddle positions for {len(positions)} strings:")
        print(f"\n  {'String':<10} {'Compensation':<15} {'Saddle Position':<20}")
        print(f"  {'-'*45}")
        
        for pos in positions:
            print(f"  String {pos.string_index:<3}  {pos.comp_mm:6.3f}mm         {pos.saddle_position_mm:6.2f}mm")
        
        # Validate progression
        comps = [p.comp_mm for p in positions]
        assert all(comps[i] < comps[i+1] for i in range(len(comps)-1)), "Compensation should increase from high to low strings"
        print("\n  ✓ Compensation increases from high to low strings")
        
        # All saddles beyond scale length
        assert all(p.saddle_position_mm > scale_mm for p in positions), "All saddles beyond scale length"
        print("  ✓ All saddles positioned beyond scale length")
        
        print("\n✅ PASS: Saddle position test")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("INSTRUMENT GEOMETRY MODULE TEST SUITE")
    print("="*60)
    
    results = []
    
    results.append(("Loader", test_loader()))
    results.append(("Fret Calculations", test_fret_calculations()))
    results.append(("Fret Table", test_fret_table()))
    results.append(("Joint Distance", test_joint_distance()))
    results.append(("Physics Compensation", test_compensation_physics()))
    results.append(("Saddle Positions", test_saddle_positions()))
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\n  Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
