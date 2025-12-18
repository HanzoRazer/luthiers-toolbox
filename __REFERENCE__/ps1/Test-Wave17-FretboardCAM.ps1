# Test-Wave17-FretboardCAM.ps1
# Wave 17 Phase C: Fretboard CAM Operations Test Suite
# Tests fret_slots_cam.py integration with RMOS context

$ErrorActionPreference = 'Stop'

Write-Host "`n=== Testing Wave 17 Phase C: Fretboard CAM Operations ===" -ForegroundColor Cyan
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
    # Test 1: Import all CAM modules
    Write-Host "Test 1: Import fret_slots_cam module and dependencies" -ForegroundColor Cyan
    $importTest = python -c @"
import sys
try:
    from app.calculators.fret_slots_cam import (
        generate_fret_slot_cam,
        generate_fret_slot_toolpaths,
        compute_radius_blended_depth,
        export_dxf_r12,
        generate_gcode,
        compute_cam_statistics,
        FretSlotToolpath,
        FretSlotCAMOutput,
    )
    from app.instrument_geometry.neck.neck_profiles import FretboardSpec
    from app.instrument_geometry.body.fretboard_geometry import (
        compute_compound_radius_at_position,
    )
    from app.rmos.context import RmosContext
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
        Write-Host "✓ All CAM module imports successful" -ForegroundColor Green
    } else {
        Write-Host "✗ Import test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 2: Generate toolpaths for standard Stratocaster fretboard
    Write-Host "Test 2: Generate fret slot toolpaths (Strat 25.5`" scale)" -ForegroundColor Cyan
    $toolpathTest = python -c @"
from app.calculators.fret_slots_cam import generate_fret_slot_toolpaths
from app.instrument_geometry.neck.neck_profiles import FretboardSpec
from app.rmos.context import RmosContext

# Standard Stratocaster fretboard spec
spec = FretboardSpec(
    nut_width_mm=42.0,      # 1.65\"
    heel_width_mm=56.0,     # ~2.2\"
    scale_length_mm=648.0,  # 25.5\"
    fret_count=22,
    base_radius_mm=241.3,   # 9.5\"
    end_radius_mm=304.8,    # 12\" (compound radius)
)

# Create RMOS context
ctx = RmosContext.from_model_id('strat_25_5')

# Generate toolpaths
toolpaths = generate_fret_slot_toolpaths(spec, ctx, slot_depth_mm=3.0)

print(f'Toolpath count: {len(toolpaths)}')
print(f'First fret position: {toolpaths[0].position_mm:.2f}mm')
print(f'12th fret position: {toolpaths[11].position_mm:.2f}mm')
print(f'Last fret position: {toolpaths[-1].position_mm:.2f}mm')
print(f'First fret width: {toolpaths[0].width_mm:.2f}mm')
print(f'Last fret width: {toolpaths[-1].width_mm:.2f}mm')
print(f'Feed rate: {toolpaths[0].feed_rate_mmpm:.1f} mm/min')
print(f'Plunge rate: {toolpaths[0].plunge_rate_mmpm:.1f} mm/min')

# Validate expectations
assert len(toolpaths) == 22, f'Expected 22 toolpaths, got {len(toolpaths)}'
assert 35 < toolpaths[0].position_mm < 37, f'First fret should be ~36mm'
assert 323 < toolpaths[11].position_mm < 325, f'12th fret should be ~324mm (half scale)'
assert toolpaths[0].width_mm < toolpaths[-1].width_mm, 'Width should increase toward heel'

print('SUCCESS: Toolpath generation validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Fret slot toolpaths generated correctly" -ForegroundColor Green
    } else {
        Write-Host "✗ Toolpath generation test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 3: Test compound radius blending
    Write-Host "Test 3: Compound radius blending (9.5`" → 12`")" -ForegroundColor Cyan
    $radiusTest = python -c @"
from app.instrument_geometry.body.fretboard_geometry import compute_compound_radius_at_position

scale_mm = 648.0  # 25.5\"
base_radius = 241.3  # 9.5\"
end_radius = 304.8   # 12\"

# Test at key positions
nut_radius = compute_compound_radius_at_position(base_radius, end_radius, 0.0, scale_mm)
mid_radius = compute_compound_radius_at_position(base_radius, end_radius, 324.0, scale_mm)
heel_radius = compute_compound_radius_at_position(base_radius, end_radius, 648.0, scale_mm)

print(f'Radius at nut (0mm): {nut_radius:.1f}mm')
print(f'Radius at 12th fret (324mm): {mid_radius:.1f}mm')
print(f'Radius at heel (648mm): {heel_radius:.1f}mm')

# Validate linear blend
assert abs(nut_radius - base_radius) < 0.1, 'Nut should be base radius'
assert abs(heel_radius - end_radius) < 0.1, 'Heel should be end radius'
assert base_radius < mid_radius < end_radius, 'Mid-point should be between base and end'

# Check 12th fret is approximately halfway blend
expected_mid = (base_radius + end_radius) / 2.0
assert abs(mid_radius - expected_mid) < 1.0, f'12th fret should blend ~{expected_mid:.1f}mm'

print('SUCCESS: Compound radius blending validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Compound radius calculations correct" -ForegroundColor Green
    } else {
        Write-Host "✗ Radius blending test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 4: DXF R12 export
    Write-Host "Test 4: DXF R12 export validation" -ForegroundColor Cyan
    $dxfTest = python -c @"
from app.calculators.fret_slots_cam import generate_fret_slot_cam
from app.instrument_geometry.neck.neck_profiles import FretboardSpec
from app.rmos.context import RmosContext

spec = FretboardSpec(42.0, 56.0, 648.0, 22, 241.3, 304.8)
ctx = RmosContext.from_model_id('strat_25_5')

output = generate_fret_slot_cam(spec, ctx)

dxf = output.dxf_content
lines = dxf.split('\n')

# Validate DXF structure
assert 'AC1009' in dxf, 'Should be DXF R12 format'
assert 'FRET_SLOTS' in dxf, 'Should have FRET_SLOTS layer'
assert 'LINE' in dxf, 'Should contain LINE entities'
assert dxf.count('LINE') == 22, f'Should have 22 LINE entities (frets)'

print(f'DXF lines: {len(lines)}')
print(f'DXF format: R12 (AC1009)')
print(f'Layer: FRET_SLOTS')
print(f'Entity count: {dxf.count("LINE")} LINEs')
print('SUCCESS: DXF R12 export validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ DXF R12 export format correct" -ForegroundColor Green
    } else {
        Write-Host "✗ DXF export test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 5: G-code generation
    Write-Host "Test 5: G-code generation with GRBL post" -ForegroundColor Cyan
    $gcodeTest = python -c @"
from app.calculators.fret_slots_cam import generate_fret_slot_cam
from app.instrument_geometry.neck.neck_profiles import FretboardSpec
from app.rmos.context import RmosContext

spec = FretboardSpec(42.0, 56.0, 648.0, 22)
ctx = RmosContext.from_model_id('strat_25_5')

output = generate_fret_slot_cam(spec, ctx, post_id='GRBL')

gcode = output.gcode_content
lines = gcode.split('\n')

# Validate G-code structure
assert 'G21' in gcode, 'Should use metric units (G21)'
assert 'G90' in gcode, 'Should use absolute positioning (G90)'
assert 'POST=GRBL' in gcode, 'Should have GRBL post metadata'
assert gcode.count('G0 X') >= 22, 'Should have rapid moves to each fret'
assert gcode.count('G1 Z') >= 22, 'Should have plunge moves'
assert 'M30' in gcode, 'Should have program end (M30)'

rapid_count = gcode.count('G0')
feed_count = gcode.count('G1')
print(f'G-code lines: {len(lines)}')
print(f'G-code moves: {rapid_count} rapids, {feed_count} feeds')
print(f'Post-processor: GRBL')
print('SUCCESS: G-code generation validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ G-code generation correct" -ForegroundColor Green
    } else {
        Write-Host "✗ G-code generation test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 6: CAM statistics computation
    Write-Host "Test 6: CAM statistics computation" -ForegroundColor Cyan
    $statsTest = python -c @"
from app.calculators.fret_slots_cam import generate_fret_slot_cam
from app.instrument_geometry.neck.neck_profiles import FretboardSpec
from app.rmos.context import RmosContext

spec = FretboardSpec(42.0, 56.0, 648.0, 22)
ctx = RmosContext.from_model_id('strat_25_5')

output = generate_fret_slot_cam(spec, ctx)
stats = output.statistics

slot_count = stats['slot_count']
cutting_length = stats['total_cutting_length_mm']
plunge_depth = stats['total_plunge_depth_mm']
time_min = stats['total_time_min']
avg_feed = stats['avg_feed_mmpm']
cost = stats['estimated_cost_usd']

print(f'Slot count: {slot_count}')
print(f'Total cutting length: {cutting_length:.2f} mm')
print(f'Total plunge depth: {plunge_depth:.2f} mm')
print(f'Estimated time: {time_min:.2f} min')
print(f'Average feed rate: {avg_feed:.1f} mm/min')
print(f'Estimated cost: ${cost:.2f}')

# Validate statistics
assert stats['slot_count'] == 22, 'Should have 22 slots'
assert stats['total_cutting_length_mm'] > 1000, 'Total length should be > 1000mm'
assert stats['total_plunge_depth_mm'] > 60, 'Total plunge should be > 60mm (22 slots × 3mm)'
assert stats['total_time_min'] > 0, 'Should have non-zero time estimate'
assert stats['avg_feed_mmpm'] > 0, 'Should have positive feed rate'

print('SUCCESS: CAM statistics validated')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ CAM statistics computed correctly" -ForegroundColor Green
    } else {
        Write-Host "✗ Statistics test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""

    # Test 7: Full integration test with complete output
    Write-Host "Test 7: Full CAM integration test (all outputs)" -ForegroundColor Cyan
    $integrationTest = python -c @"
from app.calculators.fret_slots_cam import generate_fret_slot_cam, FretSlotCAMOutput
from app.instrument_geometry.neck.neck_profiles import FretboardSpec
from app.rmos.context import RmosContext

# Les Paul spec (Gibson 24.75\" scale)
spec = FretboardSpec(
    nut_width_mm=43.0,
    heel_width_mm=56.5,
    scale_length_mm=628.65,  # 24.75\"
    fret_count=22,
    base_radius_mm=304.8,    # 12\" (constant radius)
)

ctx = RmosContext.from_model_id('lp_24_75')

# Generate complete CAM output
output = generate_fret_slot_cam(
    spec,
    ctx,
    slot_depth_mm=3.2,
    slot_width_mm=0.58,
    safe_z_mm=5.0,
    post_id='Mach4',
)

# Validate output structure
assert isinstance(output, FretSlotCAMOutput), 'Should return FretSlotCAMOutput'
assert len(output.toolpaths) == 22, 'Should have 22 toolpaths'
assert len(output.dxf_content) > 500, 'DXF should have content'
assert len(output.gcode_content) > 500, 'G-code should have content'
assert 'slot_count' in output.statistics, 'Should have statistics'

# Validate post-processor
assert 'POST=Mach4' in output.gcode_content, 'Should use Mach4 post'

print('Output structure validated:')
print(f'  Toolpaths: {len(output.toolpaths)}')
print(f'  DXF size: {len(output.dxf_content)} chars')
print(f'  G-code size: {len(output.gcode_content)} chars')
print(f'  Statistics keys: {list(output.statistics.keys())}')
print('SUCCESS: Full integration test passed')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Full CAM integration successful" -ForegroundColor Green
    } else {
        Write-Host "✗ Integration test failed" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "=== Test Summary ===" -ForegroundColor Cyan
    Write-Host "Tests passed: 7" -ForegroundColor Green
    Write-Host "Tests failed: 0" -ForegroundColor Green
    Write-Host ""
    Write-Host "✓ Wave 17 Phase C: Fretboard CAM Operations Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Run .\Test-Wave18-FeasibilityFusion.ps1 to test Phase D" -ForegroundColor White
    Write-Host "2. Implement Phase D: Feasibility Fusion router" -ForegroundColor White
    Write-Host "3. Implement Phase E: CAM Preview router" -ForegroundColor White
    Write-Host ""

} finally {
    Pop-Location
}
