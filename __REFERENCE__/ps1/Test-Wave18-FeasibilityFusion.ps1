# Test-Wave18-FeasibilityFusion.ps1
# Wave 18 Phase D: Feasibility Fusion Test Suite
# Tests unified feasibility scoring across all risk dimensions

$ErrorActionPreference = 'Stop'

Write-Host "`n=== Testing Wave 18 Phase D: Feasibility Fusion ===" -ForegroundColor Cyan
Write-Host ""

# Activate Python environment
$venvPath = "services\api\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
    & $venvPath
} else {
    Write-Host "Warning: Virtual environment not found at $venvPath" -ForegroundColor Yellow
}

# Change to API directory
Push-Location services\api

try {
    # Test 1: Import feasibility fusion modules
    Write-Host "Test 1: Import feasibility fusion modules" -ForegroundColor Cyan
    $importTest = python -c @"
import sys
try:
    from app.rmos.feasibility_fusion import (
        evaluate_feasibility,
        evaluate_feasibility_for_model,
        FeasibilityReport,
        RiskAssessment,
        RiskLevel,
        compute_weighted_score,
        determine_overall_risk,
        generate_recommendations,
    )
    from app.rmos.feasibility_router import router
    print('SUCCESS: All imports successful')
    sys.exit(0)
except ImportError as e:
    print(f'FAIL: Import error: {e}', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'FAIL: {e}', file=sys.stderr)
    sys.exit(1)
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ All feasibility fusion imports successful" -ForegroundColor Green
    } else {
        Write-Host "✗ Import test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 2: Evaluate feasibility for model (basic)
    Write-Host "Test 2: Evaluate feasibility for Strat 25.5`" model" -ForegroundColor Cyan
    $feasibilityTest = python -c @"
from app.rmos.feasibility_fusion import evaluate_feasibility_for_model

design = {
    'tool_diameter_mm': 6.0,
    'feed_rate_mmpm': 1200,
    'spindle_rpm': 18000,
    'depth_of_cut_mm': 3.0,
}

report = evaluate_feasibility_for_model('strat_25_5', design)

score = report.overall_score
risk = report.overall_risk.value
feasible = report.is_feasible()
needs_review = report.needs_review()
assessment_count = len(report.assessments)
rec_count = len(report.recommendations)

print(f'Overall score: {score:.1f}')
print(f'Overall risk: {risk}')
print(f'Is feasible: {feasible}')
print(f'Needs review: {needs_review}')
print(f'Assessments: {assessment_count}')
print(f'Recommendations: {rec_count}')

# Validate structure
assert 0 <= score <= 100, 'Score should be 0-100'
assert risk in ('GREEN', 'YELLOW', 'RED', 'UNKNOWN'), f'Invalid risk: {risk}'
assert assessment_count == 5, f'Should have 5 assessments, got {assessment_count}'
assert rec_count > 0, 'Should have recommendations'

print('SUCCESS: Feasibility evaluation validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Feasibility evaluation successful" -ForegroundColor Green
    } else {
        Write-Host "✗ Feasibility evaluation test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 3: Test risk level aggregation
    Write-Host "Test 3: Risk level aggregation logic" -ForegroundColor Cyan
    $riskTest = python -c @"
from app.rmos.feasibility_fusion import (
    RiskAssessment,
    RiskLevel,
    determine_overall_risk,
)

# Test all GREEN
all_green = [
    RiskAssessment('chipload', 90.0, RiskLevel.GREEN, [], {}),
    RiskAssessment('heat', 85.0, RiskLevel.GREEN, [], {}),
    RiskAssessment('deflection', 88.0, RiskLevel.GREEN, [], {}),
]

overall = determine_overall_risk(all_green)
assert overall == RiskLevel.GREEN, f'All green should be GREEN, got {overall}'
print('All GREEN -> GREEN: PASS')

# Test one YELLOW
one_yellow = all_green + [RiskAssessment('rimspeed', 60.0, RiskLevel.YELLOW, [], {})]
overall = determine_overall_risk(one_yellow)
assert overall == RiskLevel.YELLOW, f'One yellow should be YELLOW, got {overall}'
print('One YELLOW -> YELLOW: PASS')

# Test one RED (worst case)
one_red = one_yellow + [RiskAssessment('bom', 30.0, RiskLevel.RED, [], {})]
overall = determine_overall_risk(one_red)
assert overall == RiskLevel.RED, f'One red should be RED, got {overall}'
print('One RED -> RED: PASS')

print('SUCCESS: Risk aggregation logic validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Risk aggregation logic correct" -ForegroundColor Green
    } else {
        Write-Host "✗ Risk aggregation test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 4: Test weighted scoring
    Write-Host "Test 4: Weighted score computation" -ForegroundColor Cyan
    $weightTest = python -c @"
from app.rmos.feasibility_fusion import (
    RiskAssessment,
    RiskLevel,
    compute_weighted_score,
)

# Weights: chipload 30%, heat 25%, deflection 20%, rimspeed 15%, bom 10%
assessments = [
    RiskAssessment('chipload', 90.0, RiskLevel.GREEN, [], {}),     # 90 * 0.30 = 27
    RiskAssessment('heat', 80.0, RiskLevel.GREEN, [], {}),         # 80 * 0.25 = 20
    RiskAssessment('deflection', 85.0, RiskLevel.GREEN, [], {}),   # 85 * 0.20 = 17
    RiskAssessment('rimspeed', 70.0, RiskLevel.YELLOW, [], {}),    # 70 * 0.15 = 10.5
    RiskAssessment('bom_efficiency', 75.0, RiskLevel.YELLOW, [], {}),  # 75 * 0.10 = 7.5
]

# Expected: 27 + 20 + 17 + 10.5 + 7.5 = 82.0
weighted_score = compute_weighted_score(assessments)
print(f'Weighted score: {weighted_score:.1f}')

assert 81.0 <= weighted_score <= 83.0, f'Expected ~82.0, got {weighted_score:.1f}'

print('SUCCESS: Weighted scoring validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Weighted scoring correct" -ForegroundColor Green
    } else {
        Write-Host "✗ Weighted scoring test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 5: Test recommendation generation
    Write-Host "Test 5: Recommendation generation" -ForegroundColor Cyan
    $recTest = python -c @"
from app.rmos.feasibility_fusion import (
    RiskAssessment,
    RiskLevel,
    generate_recommendations,
)

# Test RED chipload
red_chipload = [
    RiskAssessment('chipload', 20.0, RiskLevel.RED, [], {}),
]
recs = generate_recommendations(red_chipload)
assert len(recs) > 0, 'Should have recommendations for RED'
assert any('Chipload' in r or 'feed' in r for r in recs), 'Should mention chipload'
print(f'RED chipload recommendations: {len(recs)}')

# Test all GREEN
all_green = [
    RiskAssessment('chipload', 90.0, RiskLevel.GREEN, [], {}),
    RiskAssessment('heat', 85.0, RiskLevel.GREEN, [], {}),
]
recs = generate_recommendations(all_green)
assert len(recs) > 0, 'Should have recommendations even for GREEN'
print(f'All GREEN recommendations: {len(recs)}')

print('SUCCESS: Recommendation generation validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Recommendation generation correct" -ForegroundColor Green
    } else {
        Write-Host "✗ Recommendation generation test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 6: Test full integration with RmosContext
    Write-Host "Test 6: Full integration with RmosContext" -ForegroundColor Cyan
    $integrationTest = python -c @"
from app.rmos.feasibility_fusion import evaluate_feasibility
from app.rmos.context import RmosContext

ctx = RmosContext.from_model_id('lp_24_75')

design = {
    'tool_diameter_mm': 3.0,
    'feed_rate_mmpm': 800,
    'spindle_rpm': 24000,
    'depth_of_cut_mm': 2.0,
}

report = evaluate_feasibility(design, ctx)

score = report.overall_score
risk = report.overall_risk.value

print(f'Gibson LP 24.75 context:')
print(f'  Overall score: {score:.1f}')
print(f'  Overall risk: {risk}')
print(f'  Feasible: {report.is_feasible()}')
print(f'  Assessments: {len(report.assessments)}')

# Validate
assert isinstance(report.overall_score, float), 'Score should be float'
assert report.overall_risk in [r for r in __import__('app.rmos.feasibility_fusion', fromlist=['RiskLevel']).RiskLevel], 'Invalid risk'
assert len(report.assessments) == 5, 'Should have 5 assessments'

print('SUCCESS: Full integration validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Full integration successful" -ForegroundColor Green
    } else {
        Write-Host "✗ Integration test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "=== Test Summary ===" -ForegroundColor Cyan
    Write-Host "Tests passed: 6" -ForegroundColor Green
    Write-Host "Tests failed: 0" -ForegroundColor Green
    Write-Host ""
    Write-Host "✓ Wave 18 Phase D: Feasibility Fusion Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Start API server: uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host "2. Test endpoints:" -ForegroundColor White
    Write-Host "   POST /api/rmos/feasibility/evaluate/model/strat_25_5" -ForegroundColor White
    Write-Host "   GET  /api/rmos/feasibility/models" -ForegroundColor White
    Write-Host "3. Implement Phase E: CAM Preview router" -ForegroundColor White
    Write-Host ""

} finally {
    Pop-Location
}
