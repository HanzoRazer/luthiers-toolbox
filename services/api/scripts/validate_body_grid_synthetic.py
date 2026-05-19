"""
Body Grid Synthetic Validation — Downstream Pipeline Test
==========================================================

Tests Body Grid classification using synthetic BodyEvidence,
bypassing Phase 4 dimension extraction.

This validates the downstream classification path:
  BodyEvidence → MorphologyAnalyzer → MorphologyDescriptor

Author: Production Shop
Date: 2026-05-16
Sprint: IBG Corpus Ingestion & Morphology Validation 1B
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# Add app to path
api_root = Path(__file__).parent.parent
sys.path.insert(0, str(api_root))

from app.instrument_geometry.body.ibg.body_grid.body_grid_schema import (
    BodyEvidence,
    Landmark,
    NormalizedPoint,
    EvidenceSource,
)
from app.instrument_geometry.body.ibg.body_grid.morphology_descriptor import (
    MorphologyAnalyzer,
)
from app.instrument_geometry.body.ibg.body_grid.variant_grammar import (
    BodyMorphologyClass,
)


@dataclass
class SyntheticInstrument:
    """Synthetic instrument definition for testing."""
    name: str
    expected_class: BodyMorphologyClass
    body_length_mm: float
    lower_bout_width_mm: float
    upper_bout_width_mm: float
    waist_width_mm: float
    waist_y_norm: float  # 0.0 = butt, 1.0 = neck
    notes: str = ""


# Define synthetic instruments with known dimensions
SYNTHETIC_INSTRUMENTS = [
    SyntheticInstrument(
        name="les_paul_synthetic",
        expected_class=BodyMorphologyClass.ROUNDED_SINGLE_CUT,
        body_length_mm=440.0,
        lower_bout_width_mm=330.0,
        upper_bout_width_mm=280.0,
        waist_width_mm=240.0,
        waist_y_norm=0.40,
        notes="Single cutaway, carved top, pronounced waist",
    ),
    SyntheticInstrument(
        name="sg_synthetic",
        expected_class=BodyMorphologyClass.DOUBLE_CUT,
        body_length_mm=380.0,
        lower_bout_width_mm=320.0,
        upper_bout_width_mm=310.0,
        waist_width_mm=260.0,
        waist_y_norm=0.45,
        notes="Double cutaway, slab body, deep horns",
    ),
    SyntheticInstrument(
        name="stratocaster_synthetic",
        expected_class=BodyMorphologyClass.SLAB_BODY,
        body_length_mm=400.0,
        lower_bout_width_mm=318.0,
        upper_bout_width_mm=260.0,
        waist_width_mm=235.0,
        waist_y_norm=0.42,
        notes="Slab body, contoured, double cutaway",
    ),
    SyntheticInstrument(
        name="dreadnought_synthetic",
        expected_class=BodyMorphologyClass.ROUNDED_ACOUSTIC,
        body_length_mm=505.0,
        lower_bout_width_mm=394.0,
        upper_bout_width_mm=280.0,
        waist_width_mm=280.0,
        waist_y_norm=0.48,
        notes="Figure-8 acoustic, wide lower bout",
    ),
    SyntheticInstrument(
        name="classical_synthetic",
        expected_class=BodyMorphologyClass.ROUNDED_ACOUSTIC,
        body_length_mm=490.0,
        lower_bout_width_mm=360.0,
        upper_bout_width_mm=280.0,
        waist_width_mm=240.0,
        waist_y_norm=0.50,
        notes="Classical proportions, pronounced waist (maps to ROUNDED_ACOUSTIC)",
    ),
    SyntheticInstrument(
        name="explorer_synthetic",
        expected_class=BodyMorphologyClass.ANGULAR_WEDGE,
        body_length_mm=475.0,
        lower_bout_width_mm=460.0,
        upper_bout_width_mm=460.0,
        waist_width_mm=250.0,
        waist_y_norm=0.30,
        notes="Angular, suppressed waist, extreme wings",
    ),
]


def create_body_evidence(instr: SyntheticInstrument) -> BodyEvidence:
    """Create BodyEvidence from synthetic instrument definition."""
    # Create landmarks at key body positions
    landmarks = []
    body_length = instr.body_length_mm

    # Lower bout width at Y=0.15 (near butt)
    landmarks.append(Landmark(
        label="lower_bout_max",
        point=NormalizedPoint(
            x_norm=instr.lower_bout_width_mm / (2 * body_length),
            y_norm=0.15,
        ),
        source=EvidenceSource.SPEC_DEFAULT,
        confidence=0.9,
    ))

    # Left lower bout (mirror)
    landmarks.append(Landmark(
        label="lower_bout_max_left",
        point=NormalizedPoint(
            x_norm=-instr.lower_bout_width_mm / (2 * body_length),
            y_norm=0.15,
        ),
        source=EvidenceSource.SPEC_DEFAULT,
        confidence=0.9,
    ))

    # Waist at waist_y_norm
    landmarks.append(Landmark(
        label="waist_min",
        point=NormalizedPoint(
            x_norm=instr.waist_width_mm / (2 * body_length),
            y_norm=instr.waist_y_norm,
        ),
        source=EvidenceSource.SPEC_DEFAULT,
        confidence=0.9,
    ))

    # Left waist
    landmarks.append(Landmark(
        label="waist_min_left",
        point=NormalizedPoint(
            x_norm=-instr.waist_width_mm / (2 * body_length),
            y_norm=instr.waist_y_norm,
        ),
        source=EvidenceSource.SPEC_DEFAULT,
        confidence=0.9,
    ))

    # Upper bout at Y=0.75
    landmarks.append(Landmark(
        label="upper_bout_max",
        point=NormalizedPoint(
            x_norm=instr.upper_bout_width_mm / (2 * body_length),
            y_norm=0.75,
        ),
        source=EvidenceSource.SPEC_DEFAULT,
        confidence=0.9,
    ))

    # Left upper bout
    landmarks.append(Landmark(
        label="upper_bout_max_left",
        point=NormalizedPoint(
            x_norm=-instr.upper_bout_width_mm / (2 * body_length),
            y_norm=0.75,
        ),
        source=EvidenceSource.SPEC_DEFAULT,
        confidence=0.9,
    ))

    # Butt end
    landmarks.append(Landmark(
        label="butt_center",
        point=NormalizedPoint(x_norm=0.0, y_norm=0.0),
        source=EvidenceSource.SPEC_DEFAULT,
        confidence=0.9,
    ))

    # Neck junction
    landmarks.append(Landmark(
        label="neck_junction",
        point=NormalizedPoint(x_norm=0.0, y_norm=1.0),
        source=EvidenceSource.SPEC_DEFAULT,
        confidence=0.9,
    ))

    return BodyEvidence(
        landmarks=landmarks,
        source_type=EvidenceSource.SPEC_DEFAULT,
        bounding_box_mm=(0, 0, instr.lower_bout_width_mm, body_length),
        centerline_x_mm=instr.lower_bout_width_mm / 2,
    )


def run_synthetic_validation():
    """Run Body Grid classification on synthetic instruments."""
    print("=" * 70)
    print("Body Grid Synthetic Validation — Downstream Pipeline Test")
    print("=" * 70)
    print()
    print(f"Testing {len(SYNTHETIC_INSTRUMENTS)} synthetic instruments")
    print("This validates Body Grid classification when fed known dimensions.")
    print()

    analyzer = MorphologyAnalyzer()

    results = []
    matches = 0

    for instr in SYNTHETIC_INSTRUMENTS:
        print(f"[{instr.name}]")
        print(f"  Expected: {instr.expected_class.value}")

        try:
            evidence = create_body_evidence(instr)
            descriptor = analyzer.analyze(evidence)

            actual_class = descriptor.variant_match.morphology_class
            confidence = descriptor.variant_match.confidence

            match = actual_class == instr.expected_class
            if match:
                matches += 1
                status = "MATCH"
            else:
                status = "MISMATCH"

            print(f"  Actual: {actual_class.value}")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Status: {status}")
            print(f"  Asymmetry: {descriptor.asymmetry.asymmetry_score:.2f}")
            print(f"  Primitives: {len(descriptor.primitives)}")

            results.append({
                "name": instr.name,
                "expected": instr.expected_class.value,
                "actual": actual_class.value,
                "match": match,
                "confidence": confidence,
                "asymmetry_score": descriptor.asymmetry.asymmetry_score,
                "primitive_count": len(descriptor.primitives),
            })

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "name": instr.name,
                "expected": instr.expected_class.value,
                "actual": "ERROR",
                "match": False,
                "error": str(e),
            })

        print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total instruments: {len(SYNTHETIC_INSTRUMENTS)}")
    print(f"Classification matches: {matches}/{len(SYNTHETIC_INSTRUMENTS)} ({matches*100//len(SYNTHETIC_INSTRUMENTS)}%)")
    print()

    # Mismatches
    mismatches = [r for r in results if not r.get("match", False)]
    if mismatches:
        print("Mismatches:")
        for r in mismatches:
            if "error" in r:
                print(f"  - {r['name']}: ERROR - {r['error']}")
            else:
                print(f"  - {r['name']}: expected {r['expected']}, got {r['actual']}")
        print()

    # Observations
    print("Observations for failure taxonomy:")
    for r in results:
        if r.get("match"):
            continue
        if "error" in r:
            print(f"  - {r['name']}: Body Grid analysis error - primitive detection may need tuning")
        elif r.get("confidence", 0) < 0.5:
            print(f"  - {r['name']}: Low confidence ({r.get('confidence', 0):.2f}) suggests ambiguous morphology")
        else:
            print(f"  - {r['name']}: Classification mismatch suggests grammar edge case")

    return results


if __name__ == "__main__":
    results = run_synthetic_validation()
