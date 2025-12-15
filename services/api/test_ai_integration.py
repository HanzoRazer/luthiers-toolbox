"""
AI Core Systems Integration Test

Verifies that all AI constraint, generation, and policy modules
are properly integrated and operational.
"""

import sys
sys.path.insert(0, '.')

def test_constraint_profiles():
    """Test constraint profile resolution."""
    print("=== Testing Constraint Profiles ===")
    from app.rmos.constraint_profiles import resolve_constraints_for_context, list_profile_names
    
    profiles = list_profile_names()
    print(f"  Loaded {len(profiles)} profiles: {profiles}")
    
    # Resolve 'thin_saw' profile
    result = resolve_constraints_for_context('thin_saw')
    print(f"  thin_saw.min_ring_width_mm: {result.min_ring_width_mm}")
    print(f"  thin_saw.max_ring_width_mm: {result.max_ring_width_mm}")
    print(f"  thin_saw.max_rings: {result.max_rings}")
    print(f"  thin_saw.max_total_width_mm: {result.max_total_width_mm}")
    print("  ✓ Constraint profiles OK")
    return result


def test_policy_caps(profile_result):
    """Test global policy enforcement."""
    print("\n=== Testing AI Policy Caps ===")
    from app.rmos.ai_policy import apply_global_policy_to_constraints
    from app.rmos.ai_policy import MAX_SYSTEM_RINGS, MAX_SYSTEM_TOTAL_WIDTH_MM
    
    print(f"  System limits: MAX_RINGS={MAX_SYSTEM_RINGS}, MAX_WIDTH={MAX_SYSTEM_TOTAL_WIDTH_MM}mm")
    
    capped = apply_global_policy_to_constraints(profile_result)
    
    print(f"  After caps: max_rings={capped.max_rings}, max_total_width={capped.max_total_width_mm}mm")
    
    # Verify caps were applied
    assert capped.max_rings <= MAX_SYSTEM_RINGS, "Rings cap not applied"
    assert capped.max_total_width_mm <= MAX_SYSTEM_TOTAL_WIDTH_MM, "Width cap not applied"
    print("  ✓ Policy caps OK")
    return capped


def test_generator(constraints):
    """Test candidate generation."""
    print("\n=== Testing Candidate Generator ===")
    from app.ai_core.structured_generator import generate_constrained_candidate
    
    candidate = generate_constrained_candidate(
        prev_design=None,
        constraints=constraints,
        budget=None,
        attempt_index=0
    )
    
    # Access the Pydantic model fields
    ring_count = candidate.ring_count
    outer_d = candidate.outer_diameter_mm
    inner_d = candidate.inner_diameter_mm
    pattern = candidate.pattern_type
    
    print(f"  Generated candidate with ring_count={ring_count}")
    print(f"  Outer diameter: {outer_d}mm, Inner: {inner_d}mm")
    print(f"  Pattern type: {pattern}")
    
    # Verify constraints respected
    assert ring_count <= constraints.max_rings, "Ring count exceeds max"
    print("  ✓ Generator OK")
    return candidate


def test_logging():
    """Test AI logging infrastructure."""
    print("\n=== Testing AI Logging ===")
    from app.rmos.logging_ai import new_run_id
    from app.rmos.logging_core import log_rmos_event
    
    # Test run ID generation
    run_id = new_run_id()
    assert run_id is not None and len(run_id) > 0, "Run ID not generated"
    print(f"  Generated run_id: {run_id[:8]}...")
    print("  ✓ Run ID generation OK")
    
    # Test basic event logging
    log_rmos_event("test_event", {"message": "AI integration test", "run_id": run_id})
    print("  ✓ Event logging OK")


def test_snapshot():
    """Test generator snapshot module loads correctly."""
    print("\n=== Testing Generator Snapshot Module ===")
    from app.rmos.generator_snapshot import snapshot_generator_behavior, GeneratorSampleStats
    
    # Just verify the module and functions are importable
    print(f"  snapshot_generator_behavior: {snapshot_generator_behavior.__name__}")
    print(f"  GeneratorSampleStats: {GeneratorSampleStats.__name__}")
    print("  ✓ Snapshot module OK (requires RmosContext for full test)")


def main():
    """Run all tests."""
    print("=" * 50)
    print("AI CORE SYSTEMS INTEGRATION TEST")
    print("=" * 50)
    
    try:
        profile_result = test_constraint_profiles()
        capped = test_policy_caps(profile_result)
        test_generator(capped)
        test_logging()
        test_snapshot()
        
        print("\n" + "=" * 50)
        print("✅ ALL AI CORE SYSTEMS OPERATIONAL")
        print("=" * 50)
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
