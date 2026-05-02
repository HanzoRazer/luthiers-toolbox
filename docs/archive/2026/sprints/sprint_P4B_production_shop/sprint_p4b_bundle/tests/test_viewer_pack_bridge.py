"""
tests/test_viewer_pack_bridge.py

Tests for Sprint P4-B: viewer_pack_bridge and brace_prescription.

These tests are standalone — they do not depend on viewer_pack_loader,
inverse_solver, or rayleigh_ritz being installed. They test the bridge
and prescription logic in isolation using minimal mock inputs.

Coverage:
  viewer_pack_bridge:
    - Extracts E_L_GPa from bending field (longitudinal orientation)
    - Extracts E_C_GPa from bending field (cross orientation)
    - Falls back to species defaults when no bending data
    - Falls back to species defaults for unknown species
    - Estimates E_C from E_L when only E_L present
    - Converts density g/cm³ to kg/m³ correctly
    - Extracts plate dimensions from metadata
    - Falls back to instrument-type defaults when dimensions absent
    - Defaults thickness to 3.0 mm when missing
    - Extracts modal targets from peaks list
    - Populates notes for all fallback paths
    - bending_measured flag set correctly
    - to_orthotropic_plate_kwargs unit conversion (GPa → Pa, mm → m)
    - BridgeError not raised for valid input (regression)
    - Works with raw dict (no dataclass)

  brace_prescription:
    - prescribe_bracing returns BracePrescription
    - X-brace produces 4 braces
    - Fan-brace produces 5 braces
    - All braces within MIN/MAX height bounds
    - All braces within MIN width bound
    - Manufacturability score 0–100
    - Unimplemented style returns empty prescription with note
    - summary() returns non-empty string
    - Softer wood → taller braces than stiffer wood
"""

from __future__ import annotations

import sys
import os

# Add sprint output dir to path so tests find the bridge and prescription modules
_HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_HERE, ".."))

from app.analyzer.viewer_pack_bridge import (
    PlateInputs,
    BridgeError,
    plate_inputs_from_pack,
    plate_inputs_from_dict,
    _SPECIES_DEFAULTS,
)
from app.calculators.plate_design.brace_prescription import (
    BracePrescription,
    BraceSpec,
    BraceStyle,
    prescribe_bracing,
    _MIN_BRACE_WIDTH_MM,
    _MIN_BRACE_HEIGHT_MM,
    _MAX_BRACE_HEIGHT_MM,
)


# ── Mock objects ──────────────────────────────────────────────────────────────

def _pack(
    species="sitka_spruce",
    E_L=11.2, E_C=0.85, density_g_cm3=0.43,
    orientation="longitudinal",
    length_mm=500.0, width_mm=200.0, thickness_mm=3.2,
    peaks=None,
    include_bending=True,
) -> dict:
    _peaks = peaks if peaks is not None else [{"freq_hz": 203.1}, {"freq_hz": 378.4}]
    return {
        "schema_version": "v1",
        "schema_id": "viewer_pack_v1",
        "source_capdir": "session_001",
        "measurement_only": True,
        "interpretation": "deferred",
        "bending": {
            "E_L_GPa": E_L if orientation == "longitudinal" else None,
            "E_C_GPa": E_C if orientation == "cross" else None,
            "density_g_cm3": density_g_cm3,
            "span_mm": 400.0,
            "method": "3point",
            "source_bundle": "a" * 64,
        } if include_bending else None,
        "meta": {
            "species": species,
            "instrument_type": "steel_string_dreadnought",
            "dimensions_mm": {
                "length": length_mm,
                "width": width_mm,
                "thickness": thickness_mm,
            },
        },
        "peaks": _peaks,
    }


def _mock_solver_result(thickness_mm=3.0, converged=True, rms=2.5):
    class R:
        pass
    r = R()
    r.thickness_mm = thickness_mm
    r.converged = converged
    r.rms_error_Hz = rms
    r.achieved_frequencies_Hz = [200.0, 375.0]
    return r


# ═════════════════════════════════════════════════════════════════════════════
# viewer_pack_bridge
# ═════════════════════════════════════════════════════════════════════════════

class TestViewerPackBridge:

    def test_extracts_E_L_longitudinal(self):
        inputs = plate_inputs_from_dict(_pack(E_L=11.2, orientation="longitudinal"))
        assert abs(inputs.E_L_GPa - 11.2) < 0.001
        assert inputs.bending_measured is True

    def test_extracts_E_C_cross(self):
        inputs = plate_inputs_from_dict(_pack(E_C=0.85, orientation="cross"))
        assert abs(inputs.E_C_GPa - 0.85) < 0.001
        assert inputs.bending_measured is True

    def test_falls_back_to_species_defaults_when_no_bending(self):
        inputs = plate_inputs_from_dict(_pack(include_bending=False))
        defaults = _SPECIES_DEFAULTS["sitka_spruce"]
        assert abs(inputs.E_L_GPa - defaults[0]) < 0.01
        assert inputs.bending_measured is False
        assert any("species default" in n.lower() for n in inputs.notes)

    def test_unknown_species_falls_back_to_sitka(self):
        p = _pack(species="mystery_wood")
        inputs = plate_inputs_from_dict(p)
        assert inputs.species == "sitka_spruce"
        assert any("unknown species" in n.lower() for n in inputs.notes)

    def test_estimates_E_C_from_E_L_when_absent(self):
        p = _pack(E_L=11.2, orientation="longitudinal")
        p["bending"]["E_C_GPa"] = None
        inputs = plate_inputs_from_dict(p)
        # E_C should be estimated from E_L
        assert inputs.E_C_GPa > 0
        assert any("E_C" in n for n in inputs.notes)

    def test_density_converted_g_cm3_to_kg_m3(self):
        inputs = plate_inputs_from_dict(_pack(density_g_cm3=0.43))
        assert abs(inputs.rho_kg_m3 - 430.0) < 1.0

    def test_plate_dimensions_extracted(self):
        inputs = plate_inputs_from_dict(_pack(length_mm=500, width_mm=200, thickness_mm=3.2))
        assert inputs.plate_length_mm == 500.0
        assert inputs.plate_width_mm  == 200.0
        assert inputs.thickness_mm    == 3.2

    def test_instrument_type_defaults_when_dimensions_absent(self):
        p = _pack()
        p["meta"]["dimensions_mm"] = {}
        inputs = plate_inputs_from_dict(p)
        assert inputs.plate_length_mm > 0
        assert inputs.plate_width_mm  > 0
        assert any("default" in n.lower() for n in inputs.notes)

    def test_thickness_defaults_to_3mm_when_missing(self):
        p = _pack()
        p["meta"]["dimensions_mm"]["thickness"] = 0
        inputs = plate_inputs_from_dict(p)
        assert inputs.thickness_mm == 3.0
        assert any("3.0 mm" in n for n in inputs.notes)

    def test_thickness_override(self):
        inputs = plate_inputs_from_dict(_pack(), thickness_override_mm=2.8)
        assert inputs.thickness_mm == 2.8

    def test_modal_targets_extracted(self):
        inputs = plate_inputs_from_dict(_pack(peaks=[{"freq_hz": 203.1}, {"freq_hz": 378.4}]))
        assert len(inputs.target_frequencies) == 2
        labels = [t[0] for t in inputs.target_frequencies]
        freqs  = [t[1] for t in inputs.target_frequencies]
        assert "mode_1" in labels
        assert abs(freqs[0] - 203.1) < 0.01

    def test_no_peaks_adds_note(self):
        p = _pack(peaks=[])
        inputs = plate_inputs_from_dict(p)
        assert inputs.target_frequencies == []
        assert any("peaks" in n.lower() for n in inputs.notes)

    def test_source_session_populated(self):
        inputs = plate_inputs_from_dict(_pack())
        assert inputs.source_session == "session_001"

    def test_to_orthotropic_plate_kwargs_units(self):
        inputs = plate_inputs_from_dict(_pack(E_L=11.2, thickness_mm=3.0, length_mm=500, width_mm=200))
        kwargs = inputs.to_orthotropic_plate_kwargs()
        assert abs(kwargs["E_L"] - 11.2e9) < 1e6     # Pa
        assert abs(kwargs["h"]   - 0.003)  < 1e-6     # m
        assert abs(kwargs["a"]   - 0.500)  < 1e-6     # m
        assert abs(kwargs["b"]   - 0.200)  < 1e-6     # m

    def test_works_with_plain_dict(self):
        """plate_inputs_from_pack must accept a raw dict, not just a dataclass."""
        result = plate_inputs_from_pack(_pack())
        assert isinstance(result, PlateInputs)

    def test_bending_source_sha256_stored(self):
        inputs = plate_inputs_from_dict(_pack())
        assert inputs.bending_source_sha256 == "a" * 64


# ═════════════════════════════════════════════════════════════════════════════
# brace_prescription
# ═════════════════════════════════════════════════════════════════════════════

class TestBracePrescription:

    def _inputs(self, E_L=10.5):
        return plate_inputs_from_dict(
            _pack(E_L=E_L, length_mm=500, width_mm=200, thickness_mm=3.0)
        )

    def test_returns_prescription_object(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="x_brace")
        assert isinstance(result, BracePrescription)

    def test_x_brace_produces_4_braces(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="x_brace")
        assert len(result.braces) == 4

    def test_fan_brace_produces_5_braces(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="fan_brace")
        assert len(result.braces) == 5

    def test_all_braces_above_min_height(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="x_brace")
        for b in result.braces:
            assert b.height_mm >= _MIN_BRACE_HEIGHT_MM, f"{b.label} height too low"

    def test_all_braces_below_max_height(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="x_brace")
        for b in result.braces:
            assert b.height_mm <= _MAX_BRACE_HEIGHT_MM, f"{b.label} height too high"

    def test_all_braces_above_min_width(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="x_brace")
        for b in result.braces:
            assert b.width_mm >= _MIN_BRACE_WIDTH_MM, f"{b.label} width too narrow"

    def test_manufacturability_score_in_range(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="x_brace")
        assert 0 <= result.manufacturability_score <= 100

    def test_converged_stored(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(converged=True), style="x_brace")
        assert result.converged is True

    def test_unimplemented_style_returns_empty_with_note(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="ladder")
        assert result.braces == []
        assert any("not yet implemented" in n for n in result.notes)

    def test_summary_non_empty(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="x_brace")
        assert len(result.summary()) > 50

    def test_softer_wood_gets_taller_braces(self):
        """Softer wood (lower E_L) should produce taller braces than stiffer."""
        soft   = prescribe_bracing(self._inputs(E_L=7.5),  _mock_solver_result(), style="x_brace")
        stiff  = prescribe_bracing(self._inputs(E_L=13.0), _mock_solver_result(), style="x_brace")
        # Primary legs should be taller for softer wood
        soft_h  = next(b.height_mm for b in soft.braces  if "X_leg" in b.label or "leg" in b.label)
        stiff_h = next(b.height_mm for b in stiff.braces if "X_leg" in b.label or "leg" in b.label)
        assert soft_h > stiff_h, f"Softer wood ({soft_h}) should have taller braces than stiffer ({stiff_h})"

    def test_bending_measured_propagated(self):
        inputs = self._inputs()  # bending_measured = True (has bending data)
        result = prescribe_bracing(inputs, _mock_solver_result(), style="x_brace")
        assert result.bending_measured is True

    def test_plate_species_stored(self):
        result = prescribe_bracing(self._inputs(), _mock_solver_result(), style="x_brace")
        assert result.plate_species == "sitka_spruce"
