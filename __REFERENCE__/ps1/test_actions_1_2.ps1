# Test Actions 1 & 2 — Wave 17→18 Integration
# Verifies scale_intonation.py shim and calculator API wrappers

Write-Host "=== Testing Wave 17→18 Integration - Actions 1 & 2 ===" -ForegroundColor Cyan
Write-Host ""

$testsPassed = 0
$testsFailed = 0

# ---------------------------------------------------------------------------
# Test 1: scale_intonation.py compatibility shim
# ---------------------------------------------------------------------------
Write-Host "Test 1: scale_intonation.py import compatibility" -ForegroundColor Yellow

$test1Script = @"
import sys
sys.path.insert(0, 'services/api/app')

# Test new shim imports
from instrument_geometry.scale_intonation import (
    compute_fret_positions_mm,
    compute_fret_spacing_mm,
    SEMITONE_RATIO,
)

# Test with Fender 25.5" scale (648mm)
positions = compute_fret_positions_mm(648.0, 22)
print(f'✓ Computed {len(positions)} fret positions')
print(f'✓ 12th fret at {positions[11]:.2f}mm (should be ~324mm)')

# Verify 12th fret is at half scale length
if abs(positions[11] - 324.0) < 1.0:
    print('✓ 12th fret position correct')
else:
    print(f'✗ 12th fret position incorrect: {positions[11]:.2f}mm')
    sys.exit(1)

# Test spacing calculation
spacing = compute_fret_spacing_mm(648.0, 22)
print(f'✓ Computed {len(spacing)} fret spacings')

# Test constant
print(f'✓ SEMITONE_RATIO = {SEMITONE_RATIO:.6f}')

print('✓ scale_intonation.py shim working correctly')
"@

try {
    $result = $test1Script | python 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $result -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "✗ Test 1 failed:" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "✗ Test 1 failed: $_" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# ---------------------------------------------------------------------------
# Test 2: Calculator API wrappers (imports only)
# ---------------------------------------------------------------------------
Write-Host "Test 2: Calculator API wrapper imports" -ForegroundColor Yellow

$test2Script = @"
import sys
sys.path.insert(0, 'services/api/app')

# Test new calculator wrapper imports
from calculators.service import (
    compute_chipload_risk,
    compute_heat_risk,
    compute_deflection_risk,
    compute_rimspeed_risk,
    compute_bom_efficiency,
)

print('✓ compute_chipload_risk imported')
print('✓ compute_heat_risk imported')
print('✓ compute_deflection_risk imported')
print('✓ compute_rimspeed_risk imported')
print('✓ compute_bom_efficiency imported')

# Verify they are callable
assert callable(compute_chipload_risk), 'compute_chipload_risk not callable'
assert callable(compute_heat_risk), 'compute_heat_risk not callable'
assert callable(compute_deflection_risk), 'compute_deflection_risk not callable'
assert callable(compute_rimspeed_risk), 'compute_rimspeed_risk not callable'
assert callable(compute_bom_efficiency), 'compute_bom_efficiency not callable'

print('✓ All calculator wrappers are callable')
print('✓ Calculator API wrappers working correctly')
"@

try {
    $result = $test2Script | python 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $result -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "✗ Test 2 failed:" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "✗ Test 2 failed: $_" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# ---------------------------------------------------------------------------
# Test 3: Calculator wrappers with RmosContext (integration test)
# ---------------------------------------------------------------------------
Write-Host "Test 3: Calculator wrappers with RmosContext" -ForegroundColor Yellow

$test3Script = @"
import sys
sys.path.insert(0, 'services/api/app')

from calculators.service import compute_bom_efficiency
from rmos.context import RmosContext

# Create a simple context
ctx = RmosContext.from_model_id('strat_25_5')

# Test BOM efficiency calculator (returns conservative score)
request = {
    'design': {'design_type': 'fret_slotting'},
    'context': ctx
}

result = compute_bom_efficiency(request)

print(f'✓ BOM efficiency score: {result["score"]}')
print(f'✓ Risk level: {result["risk"]}')
print(f'✓ Warnings: {len(result["warnings"])} warning(s)')

# Verify expected structure
assert 'score' in result, 'Missing score'
assert 'risk' in result, 'Missing risk'
assert 'warnings' in result, 'Missing warnings'
assert 'details' in result, 'Missing details'

print('✓ Calculator wrapper integration with RmosContext working')
"@

try {
    $result = $test3Script | python 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $result -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "✗ Test 3 failed:" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "✗ Test 3 failed: $_" -ForegroundColor Red
    $testsFailed++
}

Write-Host ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Tests passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests failed: $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "✓ All Actions 1 & 2 implementations verified!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Run .\test_phase_b_context.ps1 to verify Phase B" -ForegroundColor White
    Write-Host "2. Begin Phase C (Fretboard CAM operations)" -ForegroundColor White
    Write-Host "3. Review WAVE17_18_IMPLEMENTATION_PLAN.md for details" -ForegroundColor White
    exit 0
} else {
    Write-Host "✗ Some tests failed. Review errors above." -ForegroundColor Red
    exit 1
}
