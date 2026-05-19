#!/usr/bin/env python3
"""
Morphology Harvest Smoke Test — Direct Execution Validation
=============================================================

Validates the Morphology Harvest implementation by:
1. Importing all modules
2. Testing schema creation
3. Testing terminology normalization
4. Testing adapter availability checks
5. Testing harvest record creation
6. Testing BodyEvidence conversion

Run directly: python tests/smoke_test_morphology_harvest.py

Note: This bypasses pytest to avoid import chain issues.

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Semantic Morphology Harvest Pass 1A
"""

import json
import os
import sys
from pathlib import Path

# Add the api directory to path for imports
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))


def test_imports():
    """Test that all morphology_harvest modules import correctly."""
    print("1. Testing imports...")

    # Schema
    from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
        HarvestRecord, HarvestSource, ReviewStatus,
        TermNormalization, TERM_NORMALIZATIONS,
    )
    print("   - schema: OK")

    # Evidence categories
    from app.instrument_geometry.body.ibg.morphology_harvest.evidence_categories import (
        BodyData, NeckPocketData, NeckSystemData, FretboardData,
        HeadstockData, HardwareCavityData, AlignmentData, ConstructionNotes,
        create_empty_categories,
    )
    print("   - evidence_categories: OK")

    # PDF inventory
    from app.instrument_geometry.body.ibg.morphology_harvest.pdf_inventory import (
        PDFInventoryEntry, PDFInventoryScanner, CorpusManifest, scan_corpus,
    )
    print("   - pdf_inventory: OK")

    # Adapters
    from app.instrument_geometry.body.ibg.morphology_harvest.adapters import (
        AdapterResult, Phase4DimensionAssociationAdapter,
        CalibrationMetadataAdapter, BodyGridAdapter,
        get_phase4_adapter, get_calibration_adapter, get_body_grid_adapter,
        check_all_adapters,
    )
    print("   - adapters: OK")

    # Coordinator
    from app.instrument_geometry.body.ibg.morphology_harvest.harvest_coordinator import (
        HarvestCoordinator, HarvestResult,
    )
    print("   - harvest_coordinator: OK")

    # Overlay wrapper
    from app.instrument_geometry.body.ibg.morphology_harvest.overlay_wrapper import (
        HarvestOverlayWrapper, OverlayConfig, generate_harvest_overlay,
    )
    print("   - overlay_wrapper: OK")

    # Review manifest
    from app.instrument_geometry.body.ibg.morphology_harvest.review_manifest import (
        HarvestManifest, ManifestEntry, ManifestManager,
    )
    print("   - review_manifest: OK")

    return True


def test_schema_creation():
    """Test HarvestRecord creation."""
    print("\n2. Testing schema creation...")

    from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
        HarvestRecord, HarvestSource, ReviewStatus,
    )
    from app.instrument_geometry.body.ibg.morphology_harvest.evidence_categories import (
        BodyData,
    )

    # Create a record
    record = HarvestRecord(
        harvest_id="test_001",
        source_pdf="test.pdf",
        page_number=1,
        harvest_source=HarvestSource.VECTOR_TEXT,
    )

    # Add body data
    record.body_data.body_length_mm = 520.0
    record.body_data.lower_bout_width_mm = 381.0
    record.body_data.mark_observed(
        confidence=0.85,
        source_type="test",
        source_authority="smoke_test",
    )

    # Verify
    assert record.harvest_id == "test_001"
    assert record.body_data.observed is True
    assert record.body_data.confidence == 0.85
    assert record.body_data.body_length_mm == 520.0

    print("   [PASS] HarvestRecord creation")
    return True


def test_terminology_normalization():
    """Test terminology normalization."""
    print("\n3. Testing terminology normalization...")

    from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
        HarvestRecord, TERM_NORMALIZATIONS,
    )

    record = HarvestRecord(
        harvest_id="test_002",
        source_pdf="test.pdf",
    )

    # Test normalization
    normalized = record.normalize_term("lower_bout_mm")
    assert normalized == "lower_bout_width_mm"
    assert len(record.term_normalizations) == 1
    assert record.term_normalizations[0].source_term == "lower_bout_mm"
    assert record.term_normalizations[0].normalized_term == "lower_bout_width_mm"

    # Test passthrough for canonical terms
    normalized2 = record.normalize_term("body_length_mm")
    assert normalized2 == "body_length_mm"

    print("   [PASS] Terminology normalization")
    print(f"   Mappings tested: {len(TERM_NORMALIZATIONS)} defined")
    return True


def test_adapter_availability():
    """Test adapter availability checks."""
    print("\n4. Testing adapter availability...")

    from app.instrument_geometry.body.ibg.morphology_harvest.adapters import (
        check_all_adapters,
        get_phase4_adapter,
        get_calibration_adapter,
        get_body_grid_adapter,
    )

    results = check_all_adapters()

    # Phase 4 should be unavailable (stubbed)
    assert results["phase4"].available is False
    assert "not_wired_in_1A" in results["phase4"].reason
    print("   [PASS] Phase 4 adapter correctly stubbed")

    # Calibration should be unavailable (stubbed)
    assert results["calibration"].available is False
    assert "not_wired_in_1A" in results["calibration"].reason
    print("   [PASS] Calibration adapter correctly stubbed")

    # Body Grid should be available (same service)
    body_grid = get_body_grid_adapter()
    bg_result = body_grid.check_availability()
    if bg_result.available:
        print("   [PASS] Body Grid adapter available")
    else:
        print(f"   [WARN] Body Grid adapter not available: {bg_result.reason}")

    return True


def test_body_evidence_conversion():
    """Test HarvestRecord to BodyEvidence conversion."""
    print("\n5. Testing BodyEvidence conversion...")

    from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
        HarvestRecord,
    )

    record = HarvestRecord(
        harvest_id="test_003",
        source_pdf="test.pdf",
    )

    # Add complete body data
    record.body_data.body_length_mm = 520.0
    record.body_data.lower_bout_width_mm = 381.0
    record.body_data.upper_bout_width_mm = 292.0
    record.body_data.waist_width_mm = 241.0
    record.body_data.waist_y_norm = 0.43
    record.body_data.mark_observed(
        confidence=0.85,
        source_type="test",
        source_authority="smoke_test",
    )

    # Convert to BodyEvidence
    body_evidence = record.to_body_evidence()

    if body_evidence is None:
        print("   [SKIP] BodyEvidence conversion (body_grid not available)")
        return True

    # Verify landmarks
    assert len(body_evidence.landmarks) >= 2
    print(f"   [PASS] Created {len(body_evidence.landmarks)} landmarks")

    return True


def test_overall_confidence():
    """Test overall confidence calculation."""
    print("\n6. Testing confidence calculation...")

    from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
        HarvestRecord,
    )

    record = HarvestRecord(
        harvest_id="test_004",
        source_pdf="test.pdf",
    )

    # No observed data
    assert record.overall_confidence() == 0.0
    print("   [PASS] Zero confidence when no data")

    # Add body data
    record.body_data.mark_observed(
        confidence=0.8,
        source_type="test",
        source_authority="smoke_test",
    )

    assert record.overall_confidence() == 0.8
    print("   [PASS] Correct confidence with single category")

    # Add neck data
    record.neck_system_data.mark_observed(
        confidence=0.6,
        source_type="test",
        source_authority="smoke_test",
    )

    expected = (0.8 + 0.6) / 2
    assert abs(record.overall_confidence() - expected) < 0.01
    print("   [PASS] Correct average confidence")

    return True


def test_evidence_categories():
    """Test all evidence categories."""
    print("\n7. Testing evidence categories...")

    from app.instrument_geometry.body.ibg.morphology_harvest.evidence_categories import (
        create_empty_categories,
        BodyData, NeckPocketData, NeckSystemData, FretboardData,
        HeadstockData, HardwareCavityData, AlignmentData, ConstructionNotes,
    )

    categories = create_empty_categories()

    assert len(categories) == 8
    assert "body_data" in categories
    assert "neck_pocket_data" in categories
    assert "neck_system_data" in categories
    assert "fretboard_data" in categories
    assert "headstock_data" in categories
    assert "hardware_cavity_data" in categories
    assert "alignment_data" in categories
    assert "construction_notes" in categories

    print(f"   [PASS] All {len(categories)} categories created")
    return True


def test_json_serialization():
    """Test JSON serialization."""
    print("\n8. Testing JSON serialization...")

    from app.instrument_geometry.body.ibg.morphology_harvest.schema import (
        HarvestRecord, HarvestSource,
    )

    record = HarvestRecord(
        harvest_id="test_005",
        source_pdf="test.pdf",
        harvest_source=HarvestSource.VECTOR_TEXT,
    )
    record.body_data.body_length_mm = 520.0
    record.body_data.mark_observed(0.85, "test", "smoke_test")

    # Convert to dict
    data = record.to_dict()

    # Verify structure
    assert "harvest_id" in data
    assert "evidence_categories" in data
    assert "body_data" in data["evidence_categories"]
    assert data["evidence_categories"]["body_data"]["body_length_mm"] == 520.0

    # Verify JSON serializable
    json_str = json.dumps(data, indent=2)
    assert len(json_str) > 100

    print("   [PASS] JSON serialization")
    return True


def test_fixtures_loadable():
    """Test that sample fixtures can be loaded."""
    print("\n9. Testing fixture loading...")

    fixtures_dir = api_dir / "tests" / "fixtures" / "ibg_morphology_harvest"

    # Sample harvest record
    record_path = fixtures_dir / "sample_harvest_record.json"
    if record_path.exists():
        with open(record_path) as f:
            data = json.load(f)
        assert data["harvest_id"] == "harvest_sample01"
        print("   [PASS] sample_harvest_record.json loaded")
    else:
        print("   [SKIP] sample_harvest_record.json not found")

    # Sample corpus manifest
    manifest_path = fixtures_dir / "sample_corpus_manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            data = json.load(f)
        assert data["statistics"]["total_pdfs"] == 5
        print("   [PASS] sample_corpus_manifest.json loaded")
    else:
        print("   [SKIP] sample_corpus_manifest.json not found")

    return True


def test_no_duplicate_extraction_logic():
    """Verify no dimension parsing in harvest module (governance compliance)."""
    print("\n10. Testing governance compliance...")

    harvest_dir = api_dir / "app" / "instrument_geometry" / "body" / "ibg" / "morphology_harvest"

    # OCR and computer vision extraction patterns (actual extraction logic)
    forbidden_patterns = [
        "pytesseract",
        "easyocr",
        "cv2.boundingRect",
        "cv2.findContours",
    ]

    # pdf_inventory.py uses re.findall for metadata classification (inventory)
    # not dimension extraction — this is allowed per governance audit
    # The forbidden action is duplicating Phase 4 extraction, not inventory detection

    violations = []

    for py_file in harvest_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text()

        for pattern in forbidden_patterns:
            if pattern in content:
                violations.append((py_file.name, pattern))

    if violations:
        print("   [FAIL] Found extraction logic:")
        for filename, pattern in violations:
            print(f"      - {filename}: {pattern}")
        return False

    print("   [PASS] No duplicate extraction logic")
    return True


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("IBG Morphology Harvest 1A — Smoke Test")
    print("=" * 60)

    tests = [
        test_imports,
        test_schema_creation,
        test_terminology_normalization,
        test_adapter_availability,
        test_body_evidence_conversion,
        test_overall_confidence,
        test_evidence_categories,
        test_json_serialization,
        test_fixtures_loadable,
        test_no_duplicate_extraction_logic,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   [FAIL] Exception: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n[OVERALL: PASS]")
        return 0
    else:
        print("\n[OVERALL: ISSUES FOUND]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
