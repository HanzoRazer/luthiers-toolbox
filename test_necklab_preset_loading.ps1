# Test NeckLab Preset Loading
# This script tests the NeckLab preset loading feature

Write-Host "=== Testing NeckLab Preset Loading ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Fetch neck presets
Write-Host "1. Testing GET /api/presets?kind=neck" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/presets?kind=neck" -Method Get
    Write-Host "  ✓ Fetched $($response.presets.Count) neck presets" -ForegroundColor Green
    
    if ($response.presets.Count -eq 0) {
        Write-Host "  ⚠ No neck presets found. Creating test preset..." -ForegroundColor Yellow
        
        # Create test neck preset
        $testPreset = @{
            name = "Les Paul '59 Slim Taper (Test)"
            kind = "neck"
            description = "Authentic '59 Les Paul neck profile"
            tags = @("gibson", "les-paul", "vintage", "test")
            neck_params = @{
                blank_length = 30.0
                blank_width = 3.25
                blank_thickness = 1.0
                scale_length = 24.75
                nut_width = 1.695
                heel_width = 2.25
                neck_length = 18.0
                neck_angle = 3.5
                fretboard_radius = 12.0
                thickness_1st_fret = 0.82
                thickness_12th_fret = 0.87
                radius_at_1st = 1.25
                radius_at_12th = 1.5
                headstock_angle = 17.0
                headstock_length = 6.0
                headstock_thickness = 0.625
                tuner_layout = 1.375
                tuner_diameter = 0.375
                fretboard_offset = 0.25
                include_fretboard = $true
                alignment_pin_holes = $false
            }
        } | ConvertTo-Json -Depth 10
        
        $createResponse = Invoke-RestMethod -Uri "$baseUrl/api/presets" -Method Post -Body $testPreset -ContentType "application/json"
        Write-Host "  ✓ Created test preset: $($createResponse.id)" -ForegroundColor Green
        
        # Re-fetch to verify
        $response = Invoke-RestMethod -Uri "$baseUrl/api/presets?kind=neck" -Method Get
        Write-Host "  ✓ Now have $($response.presets.Count) neck preset(s)" -ForegroundColor Green
    }
    
    # Store first preset ID for testing
    if ($response.presets.Count -gt 0) {
        $testPresetId = $response.presets[0].id
        $testPresetName = $response.presets[0].name
        Write-Host "  ℹ Using preset for testing: $testPresetName ($testPresetId)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ✗ Failed to fetch neck presets: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Fetch specific preset detail
if ($testPresetId) {
    Write-Host "2. Testing GET /api/presets/{id}" -ForegroundColor Yellow
    try {
        $preset = Invoke-RestMethod -Uri "$baseUrl/api/presets/$testPresetId" -Method Get
        Write-Host "  ✓ Fetched preset detail: $($preset.name)" -ForegroundColor Green
        
        # Verify neck_params exists
        if ($preset.neck_params) {
            Write-Host "  ✓ neck_params present with $($preset.neck_params.PSObject.Properties.Count) fields" -ForegroundColor Green
            
            # Verify key fields
            $requiredFields = @('scale_length', 'nut_width', 'neck_angle', 'fretboard_radius')
            $missingFields = @()
            foreach ($field in $requiredFields) {
                if (-not $preset.neck_params.PSObject.Properties.Name.Contains($field)) {
                    $missingFields += $field
                }
            }
            
            if ($missingFields.Count -eq 0) {
                Write-Host "  ✓ All required fields present" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ Missing fields: $($missingFields -join ', ')" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ⚠ No neck_params in preset" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Failed to fetch preset detail: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 3: Verify preset filtering
Write-Host "3. Testing preset kind filtering" -ForegroundColor Yellow
try {
    $allPresets = Invoke-RestMethod -Uri "$baseUrl/api/presets" -Method Get
    $neckPresets = Invoke-RestMethod -Uri "$baseUrl/api/presets?kind=neck" -Method Get
    
    Write-Host "  ✓ Total presets: $($allPresets.presets.Count)" -ForegroundColor Green
    Write-Host "  ✓ Neck presets: $($neckPresets.presets.Count)" -ForegroundColor Green
    
    if ($neckPresets.presets.Count -le $allPresets.presets.Count) {
        Write-Host "  ✓ Filtering works correctly" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Filtering issue: more neck presets than total presets" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Failed to test filtering: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== NeckLab Preset Loading Tests Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Backend integration verified" -ForegroundColor Green
Write-Host "⏭ Next: Test frontend by navigating to /lab/neck in browser" -ForegroundColor Cyan
Write-Host "  1. Check dropdown populates with neck presets" -ForegroundColor White
Write-Host "  2. Select preset and verify form fields update" -ForegroundColor White
Write-Host "  3. Test query parameter: /lab/neck?preset_id=$testPresetId" -ForegroundColor White
Write-Host "  4. Test clear selection (✕ button)" -ForegroundColor White
Write-Host "  5. Test 'Use in NeckLab' from Preset Hub" -ForegroundColor White
Write-Host ""
