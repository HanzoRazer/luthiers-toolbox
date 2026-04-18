#!/usr/bin/env python3
"""
Instrument Body Generator — Complete Body from Partial Vectorizer Output
=========================================================================

Takes partial vectorizer DXF output + instrument class.
Returns complete parametric body model with:
  - Full outline (closed, clean)
  - Side heights at every point
  - Zone radii for brace fitting
  - Confidence score

Usage:
    gen = InstrumentBodyGenerator(spec_name='dreadnought')
    model = gen.complete_from_dxf('partial_outline.dxf')
    model.save_dxf('completed_outline.dxf')
    model.export_spec_json('completed_spec.json')

Author: Production Shop
Date: 2026-04-16
Sprint: 9 — InstrumentBodyGenerator
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Dict, List, Optional

import tempfile

from body_contour_solver import (
    BodyConstraints,
    BodyContourSolver,
    LandmarkPoint,
    SolvedBodyModel,
    outline_to_dxf,
    FAMILY_DEFAULTS,
)
from constraint_extractor import ConstraintExtractor

# Import consolidator from production path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'api'))
from app.cam.layer_consolidator import LayerConsolidator


# ─── Instrument Library ───────────────────────────────────────────────────────


INSTRUMENT_SPECS: Dict[str, Dict] = {
    "dreadnought": {
        "family": "dreadnought",
        "constraints": {
            "back_radius_mm": 7620.0,     # 25-foot Martin standard
            "butt_depth_mm": 121.0,
            "shoulder_depth_mm": 105.0,
            "top_thickness_mm": 2.8,
            "back_thickness_mm": 2.5,
            "scale_length_mm": 645.0,
        },
        "expected_dimensions": {
            "body_length_mm": 520.0,
            "lower_bout_mm": 381.0,
            "upper_bout_mm": 292.0,
            "waist_mm": 241.0,
        },
    },
    "cuatro_venezolano": {
        "family": "cuatro_venezolano",
        "constraints": {
            "back_radius_mm": 1000.0,     # Estimated for small body
            "butt_depth_mm": 95.0,
            "shoulder_depth_mm": 80.0,
            "top_thickness_mm": 1.9,
            "back_thickness_mm": 2.0,
            "scale_length_mm": 556.5,
        },
        "expected_dimensions": {
            "body_length_mm": 350.0,
            "lower_bout_mm": 250.1,
            "upper_bout_mm": 156.9,
            "waist_mm": 130.0,
        },
    },
    "stratocaster": {
        "family": "stratocaster",
        "constraints": {
            "back_radius_mm": float('inf'),  # Solid body - no arch
            "butt_depth_mm": 44.5,           # 1.75" body thickness
            "shoulder_depth_mm": 44.5,
            "top_thickness_mm": 0.0,
            "back_thickness_mm": 0.0,
            "scale_length_mm": 648.0,        # 25.5"
        },
        "expected_dimensions": {
            "body_length_mm": 406.0,
            "lower_bout_mm": 325.0,
            "upper_bout_mm": 248.0,
            "waist_mm": 245.0,
        },
    },
    "jumbo": {
        "family": "dreadnought",  # Uses dreadnought ratios
        "constraints": {
            "back_radius_mm": 7620.0,
            "butt_depth_mm": 127.0,
            "shoulder_depth_mm": 108.0,
            "top_thickness_mm": 2.8,
            "back_thickness_mm": 2.5,
            "scale_length_mm": 645.0,
        },
        "expected_dimensions": {
            "body_length_mm": 530.0,
            "lower_bout_mm": 432.0,
            "upper_bout_mm": 305.0,
            "waist_mm": 254.0,
        },
    },
}


# ─── Generator Class ──────────────────────────────────────────────────────────


class InstrumentBodyGenerator:
    """
    Generates complete body model from partial vectorizer output.

    Takes partial DXF + instrument spec → complete parametric body.
    """

    def __init__(self, spec_name: str):
        """
        Initialize generator for a specific instrument type.

        Args:
            spec_name: Key from INSTRUMENT_SPECS (e.g., 'dreadnought', 'cuatro_venezolano')

        Raises:
            ValueError: If spec_name is not recognized
        """
        if spec_name not in INSTRUMENT_SPECS:
            available = ", ".join(INSTRUMENT_SPECS.keys())
            raise ValueError(f"Unknown spec: {spec_name}. Available: {available}")

        self.spec_name = spec_name
        self._spec = INSTRUMENT_SPECS[spec_name]
        self.constraints = self._load_constraints()
        self.extractor = ConstraintExtractor()

    def _load_constraints(self) -> BodyConstraints:
        """Load BodyConstraints from instrument spec."""
        c = self._spec["constraints"]
        return BodyConstraints(
            back_radius_mm=c["back_radius_mm"],
            butt_depth_mm=c["butt_depth_mm"],
            shoulder_depth_mm=c["shoulder_depth_mm"],
            top_thickness_mm=c["top_thickness_mm"],
            back_thickness_mm=c["back_thickness_mm"],
            scale_length_mm=c["scale_length_mm"],
        )

    @property
    def family(self) -> str:
        """Return the family for this instrument spec."""
        return self._spec.get("family", "dreadnought")

    @property
    def expected_dimensions(self) -> Dict[str, float]:
        """Return expected dimensions for validation."""
        return self._spec.get("expected_dimensions", {})

    def complete_from_dxf(self, dxf_path: str, consolidate: bool = True) -> SolvedBodyModel:
        """
        Complete a partial DXF outline into a full body model.

        Args:
            dxf_path: Path to partial vectorizer output DXF
            consolidate: If True, consolidate LINE entities to LWPOLYLINE first

        Returns:
            SolvedBodyModel with complete body geometry
        """
        # Step 0: Consolidate raw LINE entities if needed
        working_path = dxf_path
        if consolidate:
            working_path = self._consolidate_if_needed(dxf_path)

        # Step 1: Extract landmarks from DXF
        landmarks = self.extractor.extract_landmarks_from_dxf(working_path)

        # Step 2: Solve complete body
        solver = BodyContourSolver(self.constraints, family=self.family)
        for lm in landmarks:
            solver.add_landmark(lm)

        return solver.solve()

    def _consolidate_if_needed(self, dxf_path: str, threshold: int = 1000) -> str:
        """
        Consolidate DXF if it has many LINE entities.

        Raw vectorizer output can have 300K-600K LINE entities. This consolidates
        them to clean LWPOLYLINE chains for efficient landmark extraction.

        Args:
            dxf_path: Input DXF path
            threshold: Consolidate if LINE count exceeds this (default 1000)

        Returns:
            Path to use (original if already clean, consolidated temp file otherwise)
        """
        import ezdxf

        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # Count LINE entities
        line_count = sum(1 for e in msp if e.dxftype() == "LINE")

        if line_count < threshold:
            return dxf_path  # Already clean, use as-is

        # Consolidate to temp file
        print(f"  Consolidating {line_count:,} LINE entities...")
        consolidator = LayerConsolidator(precision=2, close_tolerance_mm=2.0)

        # Create temp file for consolidated output
        fd, temp_path = tempfile.mkstemp(suffix=".dxf", prefix="ibg_consolidated_")
        os.close(fd)

        result = consolidator.consolidate(dxf_path, temp_path, body_layer_names=["0", "BODY", "BODY_OUTLINE"])
        print(f"  -> {result.output_polylines} polylines")

        return temp_path

    def complete_from_landmarks(self, landmarks: List[LandmarkPoint]) -> SolvedBodyModel:
        """
        Complete body from user-provided landmarks.

        For paid tier with manual landmark override.

        Args:
            landmarks: List of LandmarkPoint from user input

        Returns:
            SolvedBodyModel with complete body geometry
        """
        solver = BodyContourSolver(self.constraints, family=self.family)
        for lm in landmarks:
            solver.add_landmark(lm)

        return solver.solve()

    def generate_from_defaults(self) -> SolvedBodyModel:
        """
        Generate body using only instrument family defaults.

        For cases where no partial DXF or landmarks are available.

        Returns:
            SolvedBodyModel with complete body geometry from defaults
        """
        solver = BodyContourSolver(self.constraints, family=self.family)
        return solver.solve()

    def save_dxf(self, model: SolvedBodyModel, output_path: str) -> str:
        """
        Save solved model to R12 DXF.

        Args:
            model: SolvedBodyModel to export
            output_path: Path for output DXF

        Returns:
            Output file path
        """
        return outline_to_dxf(model, output_path, self.spec_name)

    def export_spec_json(self, model: SolvedBodyModel, output_path: str) -> str:
        """
        Export model as JSON specification.

        Args:
            model: SolvedBodyModel to export
            output_path: Path for output JSON

        Returns:
            Output file path
        """
        spec = {
            "instrument": self.spec_name,
            "family": self.family,
            "dimensions": {
                "body_length_mm": round(model.body_length_mm, 2),
                "lower_bout_width_mm": round(model.lower_bout_width_mm, 2),
                "upper_bout_width_mm": round(model.upper_bout_width_mm, 2),
                "waist_width_mm": round(model.waist_width_mm, 2),
                "waist_y_norm": round(model.waist_y_norm, 3),
            },
            "radii_by_zone_mm": {k: round(v, 2) for k, v in model.radii_by_zone.items()},
            "side_heights_mm": {
                "min": round(min(model.side_heights_mm), 2) if model.side_heights_mm else 0,
                "max": round(max(model.side_heights_mm), 2) if model.side_heights_mm else 0,
            },
            "confidence": round(model.confidence, 3),
            "missing_landmarks": model.missing_landmarks,
            "back_radius_source": model.back_radius_source,
            "outline_point_count": len(model.outline_points),
        }

        with open(output_path, "w") as f:
            json.dump(spec, f, indent=2)

        print(f"Saved: {output_path}")
        return output_path

    def validate_against_expected(self, model: SolvedBodyModel) -> Dict[str, float]:
        """
        Compare solved dimensions against expected spec dimensions.

        Returns:
            Dict of dimension: error_percent pairs
        """
        expected = self.expected_dimensions
        if not expected:
            return {}

        errors = {}
        comparisons = [
            ("body_length_mm", model.body_length_mm, expected.get("body_length_mm")),
            ("lower_bout_mm", model.lower_bout_width_mm, expected.get("lower_bout_mm")),
            ("upper_bout_mm", model.upper_bout_width_mm, expected.get("upper_bout_mm")),
            ("waist_mm", model.waist_width_mm, expected.get("waist_mm")),
        ]

        for name, actual, expected_val in comparisons:
            if expected_val and expected_val > 0:
                error_pct = abs(actual - expected_val) / expected_val * 100
                errors[name] = round(error_pct, 2)

        return errors


# ─── Verification ─────────────────────────────────────────────────────────────


if __name__ == "__main__":
    print("=== Step 6: InstrumentBodyGenerator Verification ===\n")

    # Test 1: Generate from defaults
    print("Test 1: Generate dreadnought from defaults")
    gen = InstrumentBodyGenerator("dreadnought")
    model = gen.generate_from_defaults()

    print(f"  Body length:  {model.body_length_mm:.1f}mm")
    print(f"  Lower bout:   {model.lower_bout_width_mm:.1f}mm")
    print(f"  Waist:        {model.waist_width_mm:.1f}mm")
    print(f"  Confidence:   {model.confidence:.2f}")

    errors = gen.validate_against_expected(model)
    print(f"  Errors: {errors}")

    # Test 2: Complete from partial DXF
    print("\nTest 2: Complete from partial DXF")
    test_dxf = os.path.join(
        os.path.dirname(__file__),
        "results",
        "dreadnought_phase5b_tier0_final.dxf"
    )

    if os.path.exists(test_dxf):
        model2 = gen.complete_from_dxf(test_dxf)

        print(f"  Body length:  {model2.body_length_mm:.1f}mm (expect 520)")
        print(f"  Lower bout:   {model2.lower_bout_width_mm:.1f}mm (expect 381)")
        print(f"  Waist:        {model2.waist_width_mm:.1f}mm (expect 241)")
        print(f"  Confidence:   {model2.confidence:.2f}")

        errors2 = gen.validate_against_expected(model2)
        print(f"  Errors: {errors2}")
    else:
        print(f"  SKIP: Test DXF not found")

    # Test 3: Export outputs
    print("\nTest 3: Export outputs")
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    dxf_out = os.path.join(results_dir, "dreadnought_generated.dxf")
    json_out = os.path.join(results_dir, "dreadnought_generated.json")

    gen.save_dxf(model, dxf_out)
    gen.export_spec_json(model, json_out)

    # Validation
    print("\n=== Validation ===")
    passed = True

    # Body dimensions within 5% of expected
    if errors.get("body_length_mm", 100) > 5:
        print(f"  FAIL: Body length error {errors.get('body_length_mm')}% > 5%")
        passed = False
    if errors.get("lower_bout_mm", 100) > 5:
        print(f"  FAIL: Lower bout error {errors.get('lower_bout_mm')}% > 5%")
        passed = False

    if os.path.exists(dxf_out) and os.path.exists(json_out):
        print(f"  Output files created: OK")
    else:
        print(f"  FAIL: Output files not created")
        passed = False

    if passed:
        print("\n=== Step 6: PASS ===")
    else:
        print("\n=== Step 6: FAIL ===")
