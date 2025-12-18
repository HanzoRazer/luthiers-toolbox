# Test-PhaseE-CAMPreview.ps1
# Wave 17→18 Phase E: CAM Preview Integration Test Suite
# Tests unified CAM generation + feasibility scoring endpoint

$ErrorActionPreference = 'Stop'

Write-Host "`n=== Testing Wave 17->18 Phase E: CAM Preview Integration ===" -ForegroundColor Cyan
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
    # Test 1: Import CAM preview router
    Write-Host "Test 1: Import CAM preview router" -ForegroundColor Cyan
    $importTest = python -c @"
import sys
try:
    from app.cam.cam_preview_router import (
        router,
        FretSlotPreviewRequest,
        FretSlotPreviewResponse,
        ToolpathSummary,
    )
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
        Write-Host "✓ CAM preview router imports successful" -ForegroundColor Green
    } else {
        Write-Host "✗ Import test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 2: Generate CAM preview for Strat model
    Write-Host "Test 2: Generate CAM preview for Strat 25.5`" model" -ForegroundColor Cyan
    $previewTest = python -c @"
from app.cam.cam_preview_router import preview_fret_slot_cam, FretSlotPreviewRequest

# Build request
request = FretSlotPreviewRequest(
    model_id='strat_25_5',
    fretboard={
        'nut_width_mm': 42.0,
        'heel_width_mm': 56.0,
        'scale_length_mm': 648.0,
        'fret_count': 22,
        'base_radius_mm': 241.3,
        'end_radius_mm': 304.8,
    },
    cam_params={
        'slot_depth_mm': 3.0,
        'slot_width_mm': 0.58,
        'safe_z_mm': 5.0,
        'post_id': 'GRBL',
    },
)

# Generate preview (async function - need to call directly)
import asyncio
response = asyncio.run(preview_fret_slot_cam(request))

toolpath_count = len(response.toolpaths)
feas_score = response.feasibility_score
feas_risk = response.feasibility_risk
is_feas = response.is_feasible
needs_rev = response.needs_review
rec_count = len(response.recommendations)
slot_count = response.statistics['slot_count']

print(f'Toolpaths: {toolpath_count}')
print(f'Feasibility score: {feas_score:.1f}')
print(f'Feasibility risk: {feas_risk}')
print(f'Is feasible: {is_feas}')
print(f'Needs review: {needs_rev}')
print(f'Recommendations: {rec_count}')
print(f'Slot count (stats): {slot_count}')
print(f'DXF preview length: {len(response.dxf_preview)} chars')
print(f'G-code preview length: {len(response.gcode_preview)} chars')

# Validate structure
assert toolpath_count == 22, f'Expected 22 toolpaths, got {toolpath_count}'
assert 0 <= feas_score <= 100, f'Score should be 0-100, got {feas_score}'
assert feas_risk in ('GREEN', 'YELLOW', 'RED'), f'Invalid risk: {feas_risk}'
assert slot_count == 22, f'Expected 22 slots in stats, got {slot_count}'
assert len(response.dxf_preview) > 0, 'DXF preview should not be empty'
assert len(response.gcode_preview) > 0, 'G-code preview should not be empty'

print('SUCCESS: CAM preview generation validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ CAM preview generation successful" -ForegroundColor Green
    } else {
        Write-Host "✗ CAM preview generation test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 3: Validate toolpath details
    Write-Host "Test 3: Validate toolpath summaries" -ForegroundColor Cyan
    $toolpathTest = python -c @"
from app.cam.cam_preview_router import preview_fret_slot_cam, FretSlotPreviewRequest
import asyncio

request = FretSlotPreviewRequest(
    model_id='lp_24_75',
    fretboard={
        'nut_width_mm': 43.0,
        'heel_width_mm': 56.5,
        'scale_length_mm': 628.65,
        'fret_count': 22,
        'base_radius_mm': 304.8,
    },
    cam_params={
        'slot_depth_mm': 3.2,
        'safe_z_mm': 5.0,
        'post_id': 'Mach4',
    },
)

response = asyncio.run(preview_fret_slot_cam(request))

# Check first fret
first_tp = response.toolpaths[0]
twelfth_tp = response.toolpaths[11]
last_tp = response.toolpaths[-1]

print(f'First fret: #{first_tp.fret_number} at {first_tp.position_mm:.2f}mm')
print(f'12th fret: #{twelfth_tp.fret_number} at {twelfth_tp.position_mm:.2f}mm')
print(f'Last fret: #{last_tp.fret_number} at {last_tp.position_mm:.2f}mm')
print(f'Width progression: {first_tp.width_mm:.2f}mm -> {last_tp.width_mm:.2f}mm')

# Validate
assert first_tp.fret_number == 1, 'First should be fret 1'
assert twelfth_tp.fret_number == 12, '12th should be fret 12'
assert last_tp.fret_number == 22, 'Last should be fret 22'
assert 35 < first_tp.position_mm < 37, f'First fret should be ~36mm'
assert 313 < twelfth_tp.position_mm < 315, f'12th fret should be ~314mm (half of 628.65)'
assert first_tp.width_mm < last_tp.width_mm, 'Width should increase'
assert first_tp.slot_depth_mm > 0, 'Slot depth should be positive'

print('SUCCESS: Toolpath summaries validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Toolpath summaries validated" -ForegroundColor Green
    } else {
        Write-Host "✗ Toolpath validation test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 4: Validate feasibility integration
    Write-Host "Test 4: Validate feasibility scoring integration" -ForegroundColor Cyan
    $feasTest = python -c @"
from app.cam.cam_preview_router import preview_fret_slot_cam, FretSlotPreviewRequest
import asyncio

request = FretSlotPreviewRequest(
    model_id='strat_25_5',
    fretboard={
        'nut_width_mm': 42.0,
        'heel_width_mm': 56.0,
        'scale_length_mm': 648.0,
        'fret_count': 22,
    },
)

response = asyncio.run(preview_fret_slot_cam(request))

feas_score = response.feasibility_score
feas_risk = response.feasibility_risk
recs = response.recommendations

print(f'Feasibility score: {feas_score:.1f}')
print(f'Risk level: {feas_risk}')
print(f'Recommendations: {recs}')

# Validate feasibility fields
assert isinstance(feas_score, float), 'Score should be float'
assert feas_risk in ('GREEN', 'YELLOW', 'RED', 'UNKNOWN'), f'Invalid risk: {feas_risk}'
assert isinstance(response.is_feasible, bool), 'is_feasible should be bool'
assert isinstance(response.needs_review, bool), 'needs_review should be bool'
assert len(recs) > 0, 'Should have recommendations'

print('SUCCESS: Feasibility integration validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Feasibility integration validated" -ForegroundColor Green
    } else {
        Write-Host "✗ Feasibility integration test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 5: Validate preview content
    Write-Host "Test 5: Validate DXF and G-code previews" -ForegroundColor Cyan
    $contentTest = python -c @"
from app.cam.cam_preview_router import preview_fret_slot_cam, FretSlotPreviewRequest
import asyncio

request = FretSlotPreviewRequest(
    model_id='strat_25_5',
    fretboard={'nut_width_mm': 42.0, 'heel_width_mm': 56.0, 'scale_length_mm': 648.0, 'fret_count': 22},
)

response = asyncio.run(preview_fret_slot_cam(request))

dxf = response.dxf_preview
gcode = response.gcode_preview

print(f'DXF preview (first 100 chars): {dxf[:100]}')
print(f'G-code preview (first 100 chars): {gcode[:100]}')

# Validate DXF
assert 'SECTION' in dxf or 'DXF' in dxf.upper(), 'DXF should have SECTION keyword'
assert len(dxf) <= 500, 'DXF preview should be truncated to 500 chars'

# Validate G-code
assert 'G21' in gcode or 'Fret' in gcode, 'G-code should have G21 or Fret comment'
assert len(gcode) <= 500, 'G-code preview should be truncated to 500 chars'

print('SUCCESS: Preview content validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Preview content validated" -ForegroundColor Green
    } else {
        Write-Host "✗ Preview content test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 6: Validate statistics
    Write-Host "Test 6: Validate CAM statistics in response" -ForegroundColor Cyan
    $statsTest = python -c @"
from app.cam.cam_preview_router import preview_fret_slot_cam, FretSlotPreviewRequest
import asyncio

request = FretSlotPreviewRequest(
    model_id='lp_24_75',
    fretboard={'nut_width_mm': 43.0, 'heel_width_mm': 56.5, 'scale_length_mm': 628.65, 'fret_count': 22},
)

response = asyncio.run(preview_fret_slot_cam(request))

stats = response.statistics

slot_count = stats.get('slot_count', 0)
cutting_len = stats.get('total_cutting_length_mm', 0)
time_min = stats.get('total_time_min', 0)

print(f'Slot count: {slot_count}')
print(f'Total cutting length: {cutting_len:.2f}mm')
print(f'Estimated time: {time_min:.2f}min')

# Validate
assert slot_count == 22, f'Expected 22 slots, got {slot_count}'
assert cutting_len > 0, 'Cutting length should be positive'
assert time_min > 0, 'Time estimate should be positive'

print('SUCCESS: CAM statistics validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ CAM statistics validated" -ForegroundColor Green
    } else {
        Write-Host "✗ CAM statistics test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "=== Test Summary ===" -ForegroundColor Cyan
    Write-Host "Tests passed: 6" -ForegroundColor Green
    Write-Host "Tests failed: 0" -ForegroundColor Green
    Write-Host ""
    Write-Host "✓ Wave 17->18 Phase E: CAM Preview Integration Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 ALL PHASES COMPLETE! 🎉" -ForegroundColor Magenta
    Write-Host "  ✓ Phase C: Fretboard CAM Operations" -ForegroundColor Green
    Write-Host "  ✓ Phase D: Feasibility Fusion" -ForegroundColor Green
    Write-Host "  ✓ Phase E: CAM Preview Integration" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Start API server: uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host "2. Test unified endpoint:" -ForegroundColor White
    Write-Host "   POST /api/cam/fret_slots/preview" -ForegroundColor White
    Write-Host "3. Implement frontend (Wave 15-16)" -ForegroundColor White
    Write-Host ""

} finally {
    Pop-Location
}
