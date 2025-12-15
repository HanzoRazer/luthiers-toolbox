"""
Tests for Business Calculators

Tests ROI, amortization, and machine throughput calculations.
"""
import pytest

from app.calculators.business.roi import (
    calculate_cnc_roi,
    calculate_break_even_jobs,
    ROIResult,
)
from app.calculators.business.amortization import (
    calculate_amortization,
    calculate_remaining_value,
    AmortizationResult,
)
from app.calculators.business.machine_throughput import (
    estimate_throughput,
    compare_job_mix,
    estimate_lead_time,
    ThroughputResult,
    JobTiming,
)


class TestCncRoi:
    """Tests for CNC ROI calculator."""

    def test_basic_roi_calculation(self):
        """Test basic ROI with labor savings."""
        result = calculate_cnc_roi(
            machine_cost_usd=10000,
            monthly_labor_savings_usd=1000,
        )
        
        assert isinstance(result, ROIResult)
        # Payback: $10,000 / $1,000/month = 10 months
        assert abs(result.payback_months - 10) < 0.1
        # Annual ROI: $12,000 / $10,000 = 120%
        assert result.annual_roi_percent > 100

    def test_roi_with_all_factors(self):
        """Test ROI with all cost/benefit factors."""
        result = calculate_cnc_roi(
            machine_cost_usd=15000,
            monthly_labor_savings_usd=800,
            monthly_additional_revenue_usd=500,
            monthly_material_savings_usd=100,
            monthly_operating_cost_usd=150,
            maintenance_annual_usd=600,
            training_cost_usd=1000,
            installation_cost_usd=500,
        )
        
        # Total investment: 15000 + 1000 + 500 = 16500
        # Monthly net: 800 + 500 + 100 - 150 - 50 = 1200
        assert result.payback_months > 0
        assert result.five_year_profit > 0

    def test_negative_roi(self):
        """Test handling of negative ROI scenario."""
        result = calculate_cnc_roi(
            machine_cost_usd=10000,
            monthly_labor_savings_usd=100,
            monthly_operating_cost_usd=200,  # Costs exceed savings
        )
        
        assert result.payback_months == float('inf')
        assert result.annual_roi_percent < 0

    def test_break_even_jobs(self):
        """Test break-even job calculation."""
        result = calculate_break_even_jobs(
            machine_cost_usd=5000,
            profit_per_job_usd=50,
            jobs_per_month=20,
        )
        
        # 5000 / 50 = 100 jobs to break even
        assert result["break_even_jobs"] == 100
        # 100 jobs / 20 per month = 5 months
        assert result["break_even_months"] == 5.0


class TestAmortization:
    """Tests for equipment amortization calculator."""

    def test_straight_line_depreciation(self):
        """Test straight-line depreciation schedule."""
        result = calculate_amortization(
            purchase_price=10000,
            useful_life_years=5,
            salvage_value=1000,
            method="straight_line",
        )
        
        assert isinstance(result, AmortizationResult)
        assert result.method == "straight_line"
        # Annual depreciation: (10000 - 1000) / 5 = 1800
        assert abs(result.annual_depreciation - 1800) < 0.1
        assert len(result.schedule) == 5
        
        # Check final book value equals salvage
        assert abs(result.schedule[-1].book_value - 1000) < 0.1

    def test_declining_balance(self):
        """Test declining balance depreciation."""
        result = calculate_amortization(
            purchase_price=10000,
            useful_life_years=5,
            salvage_value=1000,
            method="declining_balance",
        )
        
        assert result.method == "declining_balance"
        # First year should be highest
        assert result.schedule[0].depreciation > result.schedule[-1].depreciation

    def test_remaining_value(self):
        """Test calculation of remaining book value."""
        result = calculate_remaining_value(
            purchase_price=10000,
            purchase_date_year=2020,
            current_year=2023,
            useful_life_years=5,
            salvage_value=1000,
        )
        
        # After 3 years of 5-year life
        # Depreciation: 3 * 1800 = 5400
        # Book value: 10000 - 5400 = 4600
        assert abs(result["book_value"] - 4600) < 1
        assert result["years_remaining"] == 2


class TestMachineThroughput:
    """Tests for machine throughput calculator."""

    def test_basic_throughput(self):
        """Test basic throughput calculation."""
        result = estimate_throughput(
            cycle_time_min=5.0,  # 5 min per part
            setup_time_min=30.0,  # 30 min setup
            parts_per_setup=10,
        )
        
        assert isinstance(result, ThroughputResult)
        # Effective cycle: 5 + (30/10) = 8 min
        # Theoretical: 60/8 = 7.5 parts/hour
        # With 85% availability, 90% performance, 98% quality
        assert result.parts_per_hour > 0
        assert result.parts_per_shift > 0
        assert result.parts_per_week > 0

    def test_throughput_bottleneck_detection(self):
        """Test bottleneck identification."""
        # Setup-dominated scenario
        result = estimate_throughput(
            cycle_time_min=2.0,
            setup_time_min=60.0,  # Long setup
            parts_per_setup=5,    # Few parts per setup
        )
        
        assert "setup" in result.bottleneck.lower()

    def test_job_mix_comparison(self):
        """Test comparing multiple jobs for capacity."""
        jobs = [
            JobTiming(job_name="Fretboard", cycle_time_min=15, setup_time_min=30, parts_per_run=10),
            JobTiming(job_name="Bridge", cycle_time_min=8, setup_time_min=20, parts_per_run=20),
            JobTiming(job_name="Nut", cycle_time_min=3, setup_time_min=10, parts_per_run=50),
        ]
        
        result = compare_job_mix(jobs)
        
        assert "jobs" in result
        assert len(result["jobs"]) == 3
        assert "capacity_used_percent" in result
        assert "can_accommodate" in result

    def test_lead_time_estimate(self):
        """Test lead time calculation."""
        result = estimate_lead_time(
            parts_needed=100,
            cycle_time_min=10.0,
            setup_time_min=30.0,
        )
        
        # Total time: 30 + (100 * 10) = 1030 min = 17.2 hours
        assert result["total_machining_hours"] > 17
        assert result["days_needed"] > 0
