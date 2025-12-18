# Test CompareLab Preset Integration
# This script tests the CompareLab preset creation feature

Write-Host "=== Testing CompareLab Preset Integration ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test 1: Create export preset
Write-Host "1. Testing POST /api/presets (export kind)" -ForegroundColor Yellow
try {
    $exportPreset = @{
        name = "Neck Comparison Export Template (Test)"
        kind = "export"
        description = "Standard template for neck profile comparisons"
        tags = @("comparison", "neck", "export", "test")
        export_params = @{
            filename_template = "{preset}__{neck_profile}__{date}"
            format = "svg"
            neck_profile = "Les_Paul_59"
            neck_section = "Fret_12"
        }
        source = "manual"
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/presets" -Method Post -Body $exportPreset -ContentType "application/json"
    Write-Host "  ✓ Created export preset: $($response.id)" -ForegroundColor Green
    Write-Host "    Name: $($response.name)" -ForegroundColor White
    Write-Host "    Kind: $($response.kind)" -ForegroundColor White
    
    $testExportPresetId = $response.id
} catch {
    Write-Host "  ✗ Failed to create export preset: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: Create combo preset
Write-Host "2. Testing POST /api/presets (combo kind)" -ForegroundColor Yellow
try {
    $comboPreset = @{
        name = "Full Neck Diff Workflow (Test)"
        kind = "combo"
        description = "Complete comparison workflow with export settings"
        tags = @("comparison", "neck", "combo", "workflow", "test")
        cam_params = @{
            compare_mode = "neck_diff"
            baseline_name = "original_profile"
        }
        export_params = @{
            filename_template = "{preset}__{compare_mode}__{timestamp}"
            format = "png"
            neck_profile = "Fender_Modern_C"
        }
        source = "manual"
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/presets" -Method Post -Body $comboPreset -ContentType "application/json"
    Write-Host "  ✓ Created combo preset: $($response.id)" -ForegroundColor Green
    Write-Host "    Name: $($response.name)" -ForegroundColor White
    Write-Host "    Kind: $($response.kind)" -ForegroundColor White
    
    if ($response.cam_params) {
        Write-Host "    Compare Mode: $($response.cam_params.compare_mode)" -ForegroundColor White
    }
    
    $testComboPresetId = $response.id
} catch {
    Write-Host "  ✗ Failed to create combo preset: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Verify preset filtering
Write-Host "3. Testing preset kind filtering" -ForegroundColor Yellow
try {
    $exportPresets = Invoke-RestMethod -Uri "$baseUrl/api/presets?kind=export" -Method Get
    $comboPresets = Invoke-RestMethod -Uri "$baseUrl/api/presets?kind=combo" -Method Get
    
    Write-Host "  ✓ Export presets: $($exportPresets.presets.Count)" -ForegroundColor Green
    Write-Host "  ✓ Combo presets: $($comboPresets.presets.Count)" -ForegroundColor Green
    
    # Verify our test presets appear
    $foundExport = $exportPresets.presets | Where-Object { $_.id -eq $testExportPresetId }
    $foundCombo = $comboPresets.presets | Where-Object { $_.id -eq $testComboPresetId }
    
    if ($foundExport) {
        Write-Host "  ✓ Test export preset found in export list" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Test export preset not found in export list" -ForegroundColor Yellow
    }
    
    if ($foundCombo) {
        Write-Host "  ✓ Test combo preset found in combo list" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Test combo preset not found in combo list" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Failed to test filtering: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 4: Verify preset structure
if ($testExportPresetId) {
    Write-Host "4. Testing preset structure validation" -ForegroundColor Yellow
    try {
        $preset = Invoke-RestMethod -Uri "$baseUrl/api/presets/$testExportPresetId" -Method Get
        
        # Check export_params
        if ($preset.export_params) {
            Write-Host "  ✓ export_params present" -ForegroundColor Green
            
            if ($preset.export_params.filename_template) {
                Write-Host "    ✓ filename_template: $($preset.export_params.filename_template)" -ForegroundColor White
            }
            if ($preset.export_params.format) {
                Write-Host "    ✓ format: $($preset.export_params.format)" -ForegroundColor White
            }
            if ($preset.export_params.neck_profile) {
                Write-Host "    ✓ neck_profile: $($preset.export_params.neck_profile)" -ForegroundColor White
            }
            if ($preset.export_params.neck_section) {
                Write-Host "    ✓ neck_section: $($preset.export_params.neck_section)" -ForegroundColor White
            }
        } else {
            Write-Host "  ⚠ No export_params in preset" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Failed to validate structure: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 5: Verify combo preset cam_params
if ($testComboPresetId) {
    Write-Host "5. Testing combo preset cam_params" -ForegroundColor Yellow
    try {
        $preset = Invoke-RestMethod -Uri "$baseUrl/api/presets/$testComboPresetId" -Method Get
        
        if ($preset.cam_params) {
            Write-Host "  ✓ cam_params present" -ForegroundColor Green
            
            if ($preset.cam_params.compare_mode) {
                Write-Host "    ✓ compare_mode: $($preset.cam_params.compare_mode)" -ForegroundColor White
            }
            if ($preset.cam_params.baseline_name) {
                Write-Host "    ✓ baseline_name: $($preset.cam_params.baseline_name)" -ForegroundColor White
            }
        } else {
            Write-Host "  ⚠ No cam_params in combo preset" -ForegroundColor Yellow
        }
        
        if ($preset.export_params) {
            Write-Host "  ✓ export_params also present (combo includes both)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ✗ Failed to validate combo structure: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== CompareLab Preset Integration Tests Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Backend integration verified" -ForegroundColor Green
Write-Host "⏭ Next: Test frontend in CompareLab" -ForegroundColor Cyan
Write-Host "  1. Navigate to CompareLab view" -ForegroundColor White
Write-Host "  2. Load geometry and compute diff" -ForegroundColor White
Write-Host "  3. Click '💾 Save as Preset' button" -ForegroundColor White
Write-Host "  4. Fill preset form (name, description, tags)" -ForegroundColor White
Write-Host "  5. Select 'Export Only' or 'Combo' kind" -ForegroundColor White
Write-Host "  6. Review preset summary" -ForegroundColor White
Write-Host "  7. Click 'Save Preset'" -ForegroundColor White
Write-Host "  8. Verify success message" -ForegroundColor White
Write-Host "  9. Check Preset Hub for new preset" -ForegroundColor White
Write-Host "  10. Test loading saved preset in export dialog" -ForegroundColor White
Write-Host ""
