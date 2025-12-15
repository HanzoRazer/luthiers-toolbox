# Phase 5 Part 3: N.07 Drilling UI - Test Script
# Tests DrillingLab.vue component functionality

Write-Host "`n=== Testing N.07 Drilling UI Component ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

function Test-ApiEndpoint {
    param($name, $url, $method, $body)
    
    try {
        Write-Host "`nTest: $name" -ForegroundColor Yellow
        
        $headers = @{ "Content-Type" = "application/json" }
        
        if ($method -eq "GET") {
            $response = Invoke-RestMethod -Uri $url -Method $method -Headers $headers
        } else {
            $response = Invoke-RestMethod -Uri $url -Method $method -Headers $headers -Body ($body | ConvertTo-Json -Depth 10)
        }
        
        Write-Host "  ✓ $name passed" -ForegroundColor Green
        $script:testsPassed++
        return $response
    }
    catch {
        Write-Host "  ✗ $name failed: $($_.Exception.Message)" -ForegroundColor Red
        $script:testsFailed++
        return $null
    }
}

# Test 1: Verify drilling endpoints are available
Write-Host "`n--- Test Group 1: API Availability ---" -ForegroundColor Magenta

Test-ApiEndpoint `
    "Get available drilling cycles" `
    "$baseUrl/api/cam/drill/cycles" `
    "GET" `
    $null

Test-ApiEndpoint `
    "Get available post-processors" `
    "$baseUrl/api/cam/drill/posts" `
    "GET" `
    $null

# Test 2: Manual hole pattern (G81 simple drill)
Write-Host "`n--- Test Group 2: Manual Hole Pattern ---" -ForegroundColor Magenta

$manualHoles = @{
    cycle = "G81"
    holes = @(
        @{ x = 10.0; y = 10.0 }
        @{ x = 30.0; y = 10.0 }
        @{ x = 50.0; y = 10.0 }
    )
    depth = -15.0
    retract = 2.0
    feed = 300.0
    safe_z = 10.0
    post_id = "GRBL"
}

$result = Test-ApiEndpoint `
    "Generate G-code for manual 3-hole pattern" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $manualHoles

if ($result) {
    if ($result.stats.holes -eq 3) {
        Write-Host "  ✓ Correct hole count (3)" -ForegroundColor Green
        $script:testsPassed++
    } else {
        Write-Host "  ✗ Wrong hole count: $($result.stats.holes)" -ForegroundColor Red
        $script:testsFailed++
    }
    
    if ($result.gcode -match "G81") {
        Write-Host "  ✓ G81 cycle found in G-code" -ForegroundColor Green
        $script:testsPassed++
    } else {
        Write-Host "  ✗ G81 cycle not found" -ForegroundColor Red
        $script:testsFailed++
    }
}

# Test 3: Linear pattern (6-in-line tuner holes)
Write-Host "`n--- Test Group 3: Linear Pattern (Tuner Holes) ---" -ForegroundColor Magenta

$linearHoles = @()
$startX = 10.0
$spacing = 20.0
for ($i = 0; $i -lt 6; $i++) {
    $linearHoles += @{ x = $startX + ($i * $spacing); y = 10.0 }
}

$linearPattern = @{
    cycle = "G81"
    holes = $linearHoles
    depth = -10.0
    retract = 2.0
    feed = 300.0
    safe_z = 10.0
    post_id = "GRBL"
}

$result = Test-ApiEndpoint `
    "Generate linear 6-hole pattern (tuner holes)" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $linearPattern

if ($result) {
    if ($result.stats.holes -eq 6) {
        Write-Host "  ✓ 6-hole tuner pattern generated" -ForegroundColor Green
        $script:testsPassed++
    }
    
    # Verify spacing (holes should be 20mm apart)
    $firstX = 10.0
    $lastX = 10.0 + (5 * 20.0)
    if ($result.gcode -match "X10\.0" -and $result.gcode -match "X110\.0") {
        Write-Host "  ✓ Correct spacing verified" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Test 4: Circular pattern (bridge pin holes)
Write-Host "`n--- Test Group 4: Circular Pattern (Bridge Pins) ---" -ForegroundColor Magenta

$circularHoles = @()
$centerX = 50.0
$centerY = 50.0
$radius = 30.0
$count = 6

for ($i = 0; $i -lt $count; $i++) {
    $angle = ($i * 360 / $count) * [Math]::PI / 180
    $circularHoles += @{
        x = [Math]::Round($centerX + $radius * [Math]::Cos($angle), 1)
        y = [Math]::Round($centerY + $radius * [Math]::Sin($angle), 1)
    }
}

$circularPattern = @{
    cycle = "G81"
    holes = $circularHoles
    depth = -8.0
    retract = 2.0
    feed = 300.0
    safe_z = 10.0
    post_id = "GRBL"
}

$result = Test-ApiEndpoint `
    "Generate circular 6-hole pattern (bridge pins)" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $circularPattern

if ($result) {
    if ($result.stats.holes -eq 6) {
        Write-Host "  ✓ Circular bridge pin pattern generated" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Test 5: Grid pattern (control cavity mounting)
Write-Host "`n--- Test Group 5: Grid Pattern (Control Cavity) ---" -ForegroundColor Magenta

$gridHoles = @()
$startX = 10.0
$startY = 10.0
$spacingX = 30.0
$spacingY = 40.0
$cols = 2
$rows = 3

for ($row = 0; $row -lt $rows; $row++) {
    for ($col = 0; $col -lt $cols; $col++) {
        $gridHoles += @{
            x = $startX + ($col * $spacingX)
            y = $startY + ($row * $spacingY)
        }
    }
}

$gridPattern = @{
    cycle = "G81"
    holes = $gridHoles
    depth = -5.0
    retract = 2.0
    feed = 300.0
    safe_z = 10.0
    post_id = "GRBL"
}

$result = Test-ApiEndpoint `
    "Generate 2×3 grid pattern (mounting holes)" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $gridPattern

if ($result) {
    if ($result.stats.holes -eq 6) {
        Write-Host "  ✓ Grid pattern (2×3 = 6 holes) generated" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Test 6: CSV import simulation
Write-Host "`n--- Test Group 6: CSV Import ---" -ForegroundColor Magenta

# Simulate CSV import: "x,y" format
$csvData = @"
15.5,20.0
35.5,20.0
55.5,20.0
15.5,40.0
35.5,40.0
55.5,40.0
"@

$csvHoles = @()
$csvData -split "`n" | ForEach-Object {
    $line = $_.Trim()
    if ($line) {
        $parts = $line -split ","
        $csvHoles += @{
            x = [double]$parts[0]
            y = [double]$parts[1]
        }
    }
}

$csvPattern = @{
    cycle = "G81"
    holes = $csvHoles
    depth = -12.0
    retract = 2.0
    feed = 300.0
    safe_z = 10.0
    post_id = "GRBL"
}

$result = Test-ApiEndpoint `
    "Import CSV pattern (6 holes from CSV)" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $csvPattern

if ($result) {
    if ($result.stats.holes -eq 6) {
        Write-Host "  ✓ CSV import pattern generated" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Test 7: G83 peck drilling (deep holes)
Write-Host "`n--- Test Group 7: G83 Peck Drilling ---" -ForegroundColor Magenta

$peckHoles = @{
    cycle = "G83"
    holes = @(
        @{ x = 25.0; y = 25.0 }
        @{ x = 75.0; y = 75.0 }
    )
    depth = -30.0
    retract = 2.0
    feed = 200.0
    safe_z = 10.0
    peck_depth = 5.0
    post_id = "LinuxCNC"
}

$result = Test-ApiEndpoint `
    "Generate G83 peck drill (30mm deep, 5mm peck)" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $peckHoles

if ($result) {
    if ($result.stats.holes -eq 2) {
        Write-Host "  ✓ G83 peck pattern generated" -ForegroundColor Green
        $script:testsPassed++
    }
    
    # For LinuxCNC, should use modal cycles (not expanded)
    if ($result.cycle_mode -eq "modal") {
        Write-Host "  ✓ LinuxCNC uses modal cycles" -ForegroundColor Green
        $script:testsPassed++
    }
    
    # Should have peck_depth parameter
    if ($result.gcode -match "G83") {
        Write-Host "  ✓ G83 cycle found in G-code" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Test 8: G84 tapping (threaded holes)
Write-Host "`n--- Test Group 8: G84 Tapping ---" -ForegroundColor Magenta

$tapHoles = @{
    cycle = "G84"
    holes = @(
        @{ x = 20.0; y = 20.0 }
        @{ x = 40.0; y = 20.0 }
    )
    depth = -15.0
    retract = 2.0
    feed = 150.0
    safe_z = 10.0
    thread_pitch = 1.0
    spindle_rpm = 500.0
    post_id = "Mach4"
}

$result = Test-ApiEndpoint `
    "Generate G84 tapping (M6 thread, 1mm pitch)" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $tapHoles

if ($result) {
    if ($result.stats.holes -eq 2) {
        Write-Host "  ✓ G84 tapping pattern generated" -ForegroundColor Green
        $script:testsPassed++
    }
    
    if ($result.gcode -match "G84") {
        Write-Host "  ✓ G84 tapping cycle found" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Test 9: Multi-post export (GRBL expanded vs LinuxCNC modal)
Write-Host "`n--- Test Group 9: Post-Processor Comparison ---" -ForegroundColor Magenta

$testHoles = @{
    cycle = "G81"
    holes = @(
        @{ x = 10.0; y = 10.0 }
        @{ x = 30.0; y = 10.0 }
    )
    depth = -10.0
    retract = 2.0
    feed = 300.0
    safe_z = 10.0
}

# GRBL (should expand)
$grblPattern = $testHoles.Clone()
$grblPattern.post_id = "GRBL"
$grblResult = Test-ApiEndpoint `
    "GRBL export (expanded cycles)" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $grblPattern

if ($grblResult) {
    if ($grblResult.cycle_mode -eq "expanded") {
        Write-Host "  ✓ GRBL correctly expands cycles" -ForegroundColor Green
        $script:testsPassed++
    }
}

# LinuxCNC (should use modal)
$linuxcncPattern = $testHoles.Clone()
$linuxcncPattern.post_id = "LinuxCNC"
$linuxcncResult = Test-ApiEndpoint `
    "LinuxCNC export (modal cycles)" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $linuxcncPattern

if ($linuxcncResult) {
    if ($linuxcncResult.cycle_mode -eq "modal") {
        Write-Host "  ✓ LinuxCNC correctly uses modal cycles" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Test 10: Download endpoint
Write-Host "`n--- Test Group 10: File Download ---" -ForegroundColor Magenta

$downloadPattern = @{
    cycle = "G81"
    holes = @(
        @{ x = 10.0; y = 10.0 }
        @{ x = 20.0; y = 10.0 }
        @{ x = 30.0; y = 10.0 }
    )
    depth = -15.0
    retract = 2.0
    feed = 300.0
    safe_z = 10.0
    post_id = "GRBL"
}

try {
    Write-Host "`nTest: Download .nc file" -ForegroundColor Yellow
    
    $downloadUrl = "$baseUrl/api/cam/drill/gcode/download"
    $tempFile = [System.IO.Path]::GetTempFileName() + ".nc"
    
    $headers = @{ "Content-Type" = "application/json" }
    $body = $downloadPattern | ConvertTo-Json -Depth 10
    
    Invoke-RestMethod -Uri $downloadUrl -Method POST -Headers $headers -Body $body -OutFile $tempFile
    
    if (Test-Path $tempFile) {
        $fileSize = (Get-Item $tempFile).Length
        if ($fileSize -gt 0) {
            Write-Host "  ✓ Download successful ($fileSize bytes)" -ForegroundColor Green
            $script:testsPassed++
            
            # Verify it's valid G-code
            $content = Get-Content $tempFile -Raw
            if ($content -match "G21" -and $content -match "G90") {
                Write-Host "  ✓ Downloaded file contains valid G-code" -ForegroundColor Green
                $script:testsPassed++
            }
        }
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
}
catch {
    Write-Host "  ✗ Download failed: $($_.Exception.Message)" -ForegroundColor Red
    $script:testsFailed++
}

# Test 11: Error handling (invalid input)
Write-Host "`n--- Test Group 11: Error Handling ---" -ForegroundColor Magenta

# Test missing holes
try {
    Write-Host "`nTest: Reject empty holes array" -ForegroundColor Yellow
    
    $invalidPattern = @{
        cycle = "G81"
        holes = @()
        depth = -10.0
        retract = 2.0
        feed = 300.0
        safe_z = 10.0
        post_id = "GRBL"
    }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/drill/gcode" -Method POST `
        -Headers @{ "Content-Type" = "application/json" } `
        -Body ($invalidPattern | ConvertTo-Json)
    
    Write-Host "  ✗ Should have rejected empty holes" -ForegroundColor Red
    $script:testsFailed++
}
catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "  ✓ Correctly rejected empty holes (400 Bad Request)" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Test G83 without peck_depth
try {
    Write-Host "`nTest: G83 without peck_depth should warn" -ForegroundColor Yellow
    
    $noPeckPattern = @{
        cycle = "G83"
        holes = @( @{ x = 10.0; y = 10.0 } )
        depth = -20.0
        retract = 2.0
        feed = 300.0
        safe_z = 10.0
        post_id = "LinuxCNC"
    }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cam/drill/gcode" -Method POST `
        -Headers @{ "Content-Type" = "application/json" } `
        -Body ($noPeckPattern | ConvertTo-Json)
    
    if ($response.warnings.Count -gt 0) {
        Write-Host "  ✓ Warning issued for missing peck_depth" -ForegroundColor Green
        $script:testsPassed++
    }
}
catch {
    Write-Host "  ✗ Should have allowed G83 with default peck_depth" -ForegroundColor Red
    $script:testsFailed++
}

# Test 12: Performance test (large hole pattern)
Write-Host "`n--- Test Group 12: Performance (100 Holes) ---" -ForegroundColor Magenta

$largePattern = @()
for ($i = 0; $i -lt 100; $i++) {
    $largePattern += @{
        x = [Math]::Round((Get-Random -Minimum 0 -Maximum 100), 1)
        y = [Math]::Round((Get-Random -Minimum 0 -Maximum 100), 1)
    }
}

$largeHoles = @{
    cycle = "G81"
    holes = $largePattern
    depth = -10.0
    retract = 2.0
    feed = 300.0
    safe_z = 10.0
    post_id = "GRBL"
}

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$result = Test-ApiEndpoint `
    "Generate 100-hole pattern (performance test)" `
    "$baseUrl/api/cam/drill/gcode" `
    "POST" `
    $largeHoles
$stopwatch.Stop()

if ($result) {
    $elapsed = $stopwatch.ElapsedMilliseconds
    if ($result.stats.holes -eq 100) {
        Write-Host "  ✓ 100 holes generated in ${elapsed}ms" -ForegroundColor Green
        $script:testsPassed++
    }
    
    if ($elapsed -lt 5000) {
        Write-Host "  ✓ Performance acceptable (< 5 seconds)" -ForegroundColor Green
        $script:testsPassed++
    }
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })

$totalTests = $testsPassed + $testsFailed
$passRate = if ($totalTests -gt 0) { [Math]::Round(($testsPassed / $totalTests) * 100, 1) } else { 0 }
Write-Host "Pass Rate: $passRate% ($testsPassed/$totalTests)" -ForegroundColor Cyan

if ($testsFailed -eq 0) {
    Write-Host "`n✅ ALL N.07 DRILLING UI TESTS PASSED!" -ForegroundColor Green -BackgroundColor Black
    exit 0
} else {
    Write-Host "`n❌ Some tests failed. Review output above." -ForegroundColor Red
    exit 1
}
