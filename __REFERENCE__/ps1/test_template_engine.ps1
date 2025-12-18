#!/usr/bin/env pwsh
# Test script for filename template token engine

Write-Host "=== Filename Template Token Engine Tests ===" -ForegroundColor Cyan
Write-Host ""

$BaseURL = "http://localhost:8000"

# Test 1: Validate simple template
Write-Host "1. Testing POST /api/presets/validate-template (simple)" -ForegroundColor Yellow
$body1 = @{
    template = "{preset}_{date}.nc"
} | ConvertTo-Json

try {
    $resp1 = Invoke-RestMethod -Uri "$BaseURL/api/presets/validate-template" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body1
    
    Write-Host "  ✓ Validation successful:" -ForegroundColor Green
    Write-Host "    Valid: $($resp1.valid)"
    Write-Host "    Tokens: $($resp1.tokens -join ', ')"
    Write-Host "    Unknown: $($resp1.unknown_tokens -join ', ')"
    Write-Host "    Example: $($resp1.example)"
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Validate neck template
Write-Host "2. Testing POST /api/presets/validate-template (neck)" -ForegroundColor Yellow
$body2 = @{
    template = "{preset}__{neck_profile}__{neck_section}__{date}.gcode"
} | ConvertTo-Json

try {
    $resp2 = Invoke-RestMethod -Uri "$BaseURL/api/presets/validate-template" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body2
    
    Write-Host "  ✓ Validation successful:" -ForegroundColor Green
    Write-Host "    Valid: $($resp2.valid)"
    Write-Host "    Tokens: $($resp2.tokens -join ', ')"
    Write-Host "    Example: $($resp2.example)"
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Validate template with unknown token
Write-Host "3. Testing POST /api/presets/validate-template (unknown token)" -ForegroundColor Yellow
$body3 = @{
    template = "{preset}__{unknown}__{post}.nc"
} | ConvertTo-Json

try {
    $resp3 = Invoke-RestMethod -Uri "$BaseURL/api/presets/validate-template" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body3
    
    Write-Host "  ✓ Validation successful:" -ForegroundColor Green
    Write-Host "    Valid: $($resp3.valid)"
    Write-Host "    Tokens: $($resp3.tokens -join ', ')"
    Write-Host "    Unknown: $($resp3.unknown_tokens -join ', ')"
    Write-Host "    Warnings: $($resp3.warnings -join '; ')"
    Write-Host "    Example: $($resp3.example)"
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Resolve filename (simple)
Write-Host "4. Testing POST /api/presets/resolve-filename (simple)" -ForegroundColor Yellow
$body4 = @{
    preset_name = "Strat Pocket"
    post_id = "GRBL"
    extension = "gcode"
} | ConvertTo-Json

try {
    $resp4 = Invoke-RestMethod -Uri "$BaseURL/api/presets/resolve-filename" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body4
    
    Write-Host "  ✓ Resolution successful:" -ForegroundColor Green
    Write-Host "    Filename: $($resp4.filename)"
    Write-Host "    Template: $($resp4.template_used)"
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Resolve filename (neck operation)
Write-Host "5. Testing POST /api/presets/resolve-filename (neck)" -ForegroundColor Yellow
$body5 = @{
    preset_name = "Neck Roughing"
    neck_profile = "Fender Modern C"
    neck_section = "Fret 5"
    post_id = "Mach4"
    extension = "nc"
} | ConvertTo-Json

try {
    $resp5 = Invoke-RestMethod -Uri "$BaseURL/api/presets/resolve-filename" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body5
    
    Write-Host "  ✓ Resolution successful:" -ForegroundColor Green
    Write-Host "    Filename: $($resp5.filename)"
    Write-Host "    Template: $($resp5.template_used)"
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: Resolve filename with custom template
Write-Host "6. Testing POST /api/presets/resolve-filename (custom template)" -ForegroundColor Yellow
$body6 = @{
    template = "{preset}__{machine}__{material}__{timestamp}.gcode"
    preset_name = "Test Adaptive"
    machine_id = "CNC Router 01"
    material = "Maple"
    extension = "gcode"
} | ConvertTo-Json

try {
    $resp6 = Invoke-RestMethod -Uri "$BaseURL/api/presets/resolve-filename" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body6
    
    Write-Host "  ✓ Resolution successful:" -ForegroundColor Green
    Write-Host "    Filename: $($resp6.filename)"
    Write-Host "    Template: $($resp6.template_used)"
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 7: Resolve filename (compare mode)
Write-Host "7. Testing POST /api/presets/resolve-filename (compare mode)" -ForegroundColor Yellow
$body7 = @{
    preset_name = "Rosette Baseline"
    compare_mode = "variant_A"
    post_id = "LinuxCNC"
    extension = "ngc"
} | ConvertTo-Json

try {
    $resp7 = Invoke-RestMethod -Uri "$BaseURL/api/presets/resolve-filename" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body7
    
    Write-Host "  ✓ Resolution successful:" -ForegroundColor Green
    Write-Host "    Filename: $($resp7.filename)"
    Write-Host "    Template: $($resp7.template_used)"
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "=== All Template Engine Tests Completed ===" -ForegroundColor Cyan
