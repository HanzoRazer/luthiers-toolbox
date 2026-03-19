"""Tests for voicing_history_calc.py (CONSTRUCTION-009)."""

import pytest

from app.calculators.voicing_history_calc import (
    TapToneMeasurement,
    VoicingSession,
    VoicingReport,
    analyze_voicing_progress,
    predict_final_frequency,
    thickness_for_target_frequency,
    get_target_frequencies,
    list_build_stages,
)


class TestPredictFinalFrequency:
    """Tests for predict_final_frequency function."""

    def test_thinner_plate_lower_frequency(self):
        """Thinning plate should reduce frequency (f ∝ h)."""
        predicted = predict_final_frequency(
            current_thickness_mm=3.0,
            current_frequency_hz=200.0,
            target_thickness_mm=2.5,
        )
        assert predicted < 200.0

    def test_linear_relationship(self):
        """Frequency should scale linearly with thickness."""
        predicted = predict_final_frequency(
            current_thickness_mm=3.0,
            current_frequency_hz=180.0,
            target_thickness_mm=2.7,
        )
        # f_new = f_current * (h_new / h_current) = 180 * (2.7 / 3.0) = 162
        assert abs(predicted - 162.0) < 0.1

    def test_same_thickness_same_frequency(self):
        """No thickness change should give same frequency."""
        predicted = predict_final_frequency(
            current_thickness_mm=3.0,
            current_frequency_hz=180.0,
            target_thickness_mm=3.0,
        )
        assert predicted == 180.0


class TestThicknessForTargetFrequency:
    """Tests for thickness_for_target_frequency function."""

    def test_lower_frequency_needs_thinner_plate(self):
        """Lowering frequency requires thinning."""
        required = thickness_for_target_frequency(
            current_thickness_mm=3.0,
            current_frequency_hz=200.0,
            target_frequency_hz=180.0,
        )
        assert required < 3.0

    def test_inverse_of_predict(self):
        """Should be inverse of predict_final_frequency."""
        required = thickness_for_target_frequency(
            current_thickness_mm=3.0,
            current_frequency_hz=200.0,
            target_frequency_hz=180.0,
        )
        # Verify: predicting frequency at required thickness should give target
        predicted = predict_final_frequency(
            current_thickness_mm=3.0,
            current_frequency_hz=200.0,
            target_thickness_mm=required,
        )
        assert abs(predicted - 180.0) < 0.1


class TestAnalyzeVoicingProgress:
    """Tests for analyze_voicing_progress function."""

    def test_on_target_returns_green(self):
        """Frequency on target should return GREEN gate."""
        session = VoicingSession(
            instrument_id="guitar-001",
            top_species="spruce",
            back_species="rosewood",
            body_style="dreadnought",
            measurements=[
                TapToneMeasurement(
                    stage="rough_thicknessed",
                    thickness_mm=3.0,
                    tap_frequency_hz=180.0,  # Exactly on target for dreadnought
                    timestamp="2024-01-15T10:00:00",
                    notes="top",
                ),
            ],
            target_top_hz=180.0,
            target_back_hz=200.0,
        )
        report = analyze_voicing_progress(session)
        assert report.top_status == "on_target"

    def test_above_target_needs_thinning(self):
        """Frequency above target should indicate work needed."""
        session = VoicingSession(
            instrument_id="guitar-001",
            top_species="spruce",
            back_species="rosewood",
            body_style="dreadnought",
            measurements=[
                TapToneMeasurement(
                    stage="rough_thicknessed",
                    thickness_mm=3.2,
                    tap_frequency_hz=210.0,  # Above target
                    timestamp="2024-01-15T10:00:00",
                    notes="top",
                ),
            ],
            target_top_hz=180.0,
            target_back_hz=200.0,
        )
        report = analyze_voicing_progress(session)
        assert report.top_status == "above_target"
        assert report.top_delta_hz > 0

    def test_below_target_returns_red(self):
        """Frequency below target (over-thinned) should return RED."""
        session = VoicingSession(
            instrument_id="guitar-001",
            top_species="spruce",
            back_species="rosewood",
            body_style="dreadnought",
            measurements=[
                TapToneMeasurement(
                    stage="rough_thicknessed",
                    thickness_mm=2.5,
                    tap_frequency_hz=160.0,  # Below target
                    timestamp="2024-01-15T10:00:00",
                    notes="top",
                ),
            ],
            target_top_hz=180.0,
            target_back_hz=200.0,
        )
        report = analyze_voicing_progress(session)
        assert report.top_status == "below_target"
        assert report.gate == "RED"

    def test_over_thinned_triggers_red(self):
        """Thickness below minimum should trigger RED gate."""
        session = VoicingSession(
            instrument_id="guitar-001",
            top_species="spruce",
            back_species="rosewood",
            body_style="dreadnought",
            measurements=[
                TapToneMeasurement(
                    stage="braced_free_plate",
                    thickness_mm=2.0,  # Below MIN_TOP_THICKNESS_MM (2.2)
                    tap_frequency_hz=150.0,
                    timestamp="2024-01-15T10:00:00",
                    notes="top",
                ),
            ],
            target_top_hz=180.0,
            target_back_hz=200.0,
        )
        report = analyze_voicing_progress(session)
        assert report.top_status == "over_thinned"
        assert report.gate == "RED"


class TestGetTargetFrequencies:
    """Tests for get_target_frequencies function."""

    def test_dreadnought_targets(self):
        """Dreadnought should return correct targets."""
        targets = get_target_frequencies("dreadnought")
        assert targets["top"] == 180
        assert targets["back"] == 200

    def test_om_targets(self):
        """OM/000 should return correct targets."""
        targets = get_target_frequencies("om_000")
        assert targets["top"] == 195
        assert targets["back"] == 215

    def test_unknown_defaults_to_om(self):
        """Unknown body style should default to OM targets."""
        targets = get_target_frequencies("unknown_style")
        assert targets["top"] == 195
        assert targets["back"] == 215


class TestListBuildStages:
    """Tests for list_build_stages function."""

    def test_returns_correct_stages(self):
        """Should return all build stages in order."""
        stages = list_build_stages()
        assert stages == [
            "rough_thicknessed",
            "braced_free_plate",
            "assembled_in_box",
            "strung_up",
        ]

    def test_returns_copy(self):
        """Should return a copy, not the original list."""
        stages1 = list_build_stages()
        stages2 = list_build_stages()
        stages1.append("extra")
        assert len(stages2) == 4  # Original unchanged


class TestVoicingReportToDict:
    """Tests for VoicingReport.to_dict method."""

    def test_to_dict_returns_all_keys(self):
        """to_dict should return all expected keys."""
        report = VoicingReport(
            instrument_id="guitar-001",
            current_stage="rough_thicknessed",
            top_status="above_target",
            back_status="on_target",
            top_frequency_hz=195.5,
            back_frequency_hz=200.0,
            top_delta_hz=15.5,
            back_delta_hz=0.0,
            predicted_top_hz=180.0,
            predicted_back_hz=200.0,
            trend_slope=60.0,
            gate="YELLOW",
            notes=["Minor voicing adjustment needed"],
        )
        d = report.to_dict()
        assert d["instrument_id"] == "guitar-001"
        assert d["current_stage"] == "rough_thicknessed"
        assert d["top_status"] == "above_target"
        assert d["gate"] == "YELLOW"
        assert d["top_frequency_hz"] == 195.5
        assert d["trend_slope"] == 60.0
