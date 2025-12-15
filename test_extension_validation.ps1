# Extension Validation Test Script
# Tests the extension mismatch detection and auto-fix feature

Write-Host "=== Testing Extension Validation Feature ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$apiKey = "test"

# Test 1: Create test preset for export validation
Write-Host "Test 1: Creating test export preset..." -ForegroundColor Yellow
$exportPresetBody = @{
    name = "Test Export Preset"
    description = "Extension validation test preset"
    kind = "export"
    tags = @("extension-test")
    template_data = @{
        filename_template = "{preset}__test__{date}.svg"
        export_format = "svg"
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/presets" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $exportPresetBody
    
    $testPresetId = $response.id
    Write-Host "  ✓ Created test preset: $testPresetId" -ForegroundColor Green
    Write-Host "    Template: $($response.template_data.filename_template)" -ForegroundColor Gray
    Write-Host "    Format: $($response.template_data.export_format)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Failed to create test preset: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Verify localStorage persistence
Write-Host "Test 2: Extension Validation Logic (Manual Browser Test Required)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Open CompareLab in browser and test these scenarios:" -ForegroundColor Cyan
Write-Host ""

Write-Host "  Scenario 1: Template .svg but Format PNG" -ForegroundColor White
Write-Host "    1. Set template: {preset}__{date}.svg" -ForegroundColor Gray
Write-Host "    2. Select format: PNG" -ForegroundColor Gray
Write-Host "    3. Expected: ⚠️ Warning appears with mismatch" -ForegroundColor Yellow
Write-Host "    4. Click 'Fix Template → .png'" -ForegroundColor Gray
Write-Host "    5. Expected: Template changes to .png, warning disappears" -ForegroundColor Green
Write-Host ""

Write-Host "  Scenario 2: Template .png but Format SVG" -ForegroundColor White
Write-Host "    1. Set template: comparison_{timestamp}.png" -ForegroundColor Gray
Write-Host "    2. Select format: SVG" -ForegroundColor Gray
Write-Host "    3. Expected: ⚠️ Warning appears" -ForegroundColor Yellow
Write-Host "    4. Click 'Fix Format → PNG'" -ForegroundColor Gray
Write-Host "    5. Expected: Format changes to PNG, warning disappears" -ForegroundColor Green
Write-Host ""

Write-Host "  Scenario 3: Template .csv but Format SVG" -ForegroundColor White
Write-Host "    1. Set template: metrics_{date}.csv" -ForegroundColor Gray
Write-Host "    2. Select format: SVG" -ForegroundColor Gray
Write-Host "    3. Expected: ⚠️ Warning appears" -ForegroundColor Yellow
Write-Host "    4. Test both fix buttons" -ForegroundColor Gray
Write-Host "    5. Expected: Both fixes work correctly" -ForegroundColor Green
Write-Host ""

Write-Host "  Scenario 4: Template no extension, any format" -ForegroundColor White
Write-Host "    1. Set template: {preset}_comparison" -ForegroundColor Gray
Write-Host "    2. Select any format" -ForegroundColor Gray
Write-Host "    3. Expected: No warning (no extension = OK)" -ForegroundColor Green
Write-Host ""

Write-Host "  Scenario 5: Template matches format" -ForegroundColor White
Write-Host "    1. Set template: output.svg" -ForegroundColor Gray
Write-Host "    2. Select format: SVG" -ForegroundColor Gray
Write-Host "    3. Expected: No warning (match = OK)" -ForegroundColor Green
Write-Host ""

Write-Host "  Scenario 6: Invalid extension with valid format" -ForegroundColor White
Write-Host "    1. Set template: file.dxf" -ForegroundColor Gray
Write-Host "    2. Select format: SVG" -ForegroundColor Gray
Write-Host "    3. Expected: ⚠️ Warning appears (.dxf != svg)" -ForegroundColor Yellow
Write-Host "    4. Fix Template button should change .dxf → .svg" -ForegroundColor Gray
Write-Host "    5. Expected: Warning disappears after fix" -ForegroundColor Green
Write-Host ""

# Test 3: Edge cases
Write-Host "Test 3: Edge Case Validation" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Edge Case 1: Multiple dots in template" -ForegroundColor White
Write-Host "    Template: my.file.name.svg → Should detect .svg" -ForegroundColor Gray
Write-Host ""
Write-Host "  Edge Case 2: Extension in token" -ForegroundColor White
Write-Host "    Template: {preset.svg}__{date} → Should NOT detect extension (inside token)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Edge Case 3: Mixed case extension" -ForegroundColor White
Write-Host "    Template: output.SVG with format svg → Should match (case insensitive)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Edge Case 4: Unsupported extension" -ForegroundColor White
Write-Host "    Template: file.txt with format svg → Should warn" -ForegroundColor Gray
Write-Host ""

# Test 4: localStorage verification
Write-Host "Test 4: localStorage State Persistence" -ForegroundColor Yellow
Write-Host ""
Write-Host "  After making changes in browser:" -ForegroundColor Cyan
Write-Host "    1. Open DevTools → Application → Local Storage" -ForegroundColor Gray
Write-Host "    2. Check key: comparelab.filenameTemplate" -ForegroundColor Gray
Write-Host "    3. Check key: comparelab.exportFormat" -ForegroundColor Gray
Write-Host "    4. Verify values match UI selections" -ForegroundColor Gray
Write-Host "    5. Refresh page (F5)" -ForegroundColor Gray
Write-Host "    6. Expected: Template and format restored from localStorage" -ForegroundColor Green
Write-Host "    7. Expected: Warning re-appears if mismatch still exists" -ForegroundColor Yellow
Write-Host ""

# Test 5: Filename preview validation
Write-Host "Test 5: Filename Preview Correctness" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Verify filename preview updates correctly:" -ForegroundColor Cyan
Write-Host "    1. Set template: test_{date}" -ForegroundColor Gray
Write-Host "    2. Select format: SVG" -ForegroundColor Gray
Write-Host "    3. Preview should show: test_2025-11-28.svg" -ForegroundColor Green
Write-Host "    4. Change format to PNG" -ForegroundColor Gray
Write-Host "    5. Preview should show: test_2025-11-28.png" -ForegroundColor Green
Write-Host "    6. Expected: Extension ALWAYS matches selected format" -ForegroundColor Yellow
Write-Host ""

# Test 6: Export functionality
Write-Host "Test 6: Actual Export with Extension Validation" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Test export works correctly:" -ForegroundColor Cyan
Write-Host "    1. Set template with mismatch: output.svg" -ForegroundColor Gray
Write-Host "    2. Select format: PNG" -ForegroundColor Gray
Write-Host "    3. Fix the warning (either button)" -ForegroundColor Gray
Write-Host "    4. Run comparison" -ForegroundColor Gray
Write-Host "    5. Click 'Export' button" -ForegroundColor Gray
Write-Host "    6. Expected: Downloaded file has correct extension (.png)" -ForegroundColor Green
Write-Host "    7. Expected: File opens correctly in appropriate viewer" -ForegroundColor Green
Write-Host ""

# Cleanup
Write-Host "Cleanup: Removing test preset..." -ForegroundColor Yellow
try {
    $null = Invoke-RestMethod -Uri "$baseUrl/api/presets/$testPresetId" -Method DELETE
    Write-Host "  ✓ Test preset deleted" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Could not delete test preset: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Extension Validation Test Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Backend test preset created successfully" -ForegroundColor Green
Write-Host "📋 Manual browser tests documented above (6 scenarios + 4 edge cases)" -ForegroundColor Yellow
Write-Host "🔍 Verify the following:" -ForegroundColor Cyan
Write-Host "   1. Warning appears when template extension != format" -ForegroundColor White
Write-Host "   2. 'Fix Template' button changes template extension" -ForegroundColor White
Write-Host "   3. 'Fix Format' button changes export format" -ForegroundColor White
Write-Host "   4. Warning disappears after fix applied" -ForegroundColor White
Write-Host "   5. No warning when template has no extension" -ForegroundColor White
Write-Host "   6. No warning when template extension matches format" -ForegroundColor White
Write-Host "   7. localStorage persists template and format changes" -ForegroundColor White
Write-Host "   8. Filename preview always shows correct extension" -ForegroundColor White
Write-Host ""
Write-Host "Next: Open http://localhost:5173/lab/compare and test manually" -ForegroundColor Cyan
Write-Host ""
