# =============================================================================
# Phase 5 Part 3: N.15 G-code Backplot Comprehensive Validation
# =============================================================================
# 
# Tests G-code parser, backplot SVG generation, and time estimation endpoints.
# Expands original 3 smoke tests → 46 comprehensive tests across 8 groups.
#
# IMPLEMENTATION COMPONENTS:
# - Backend: services/api/app/routers/gcode_backplot_router.py (116 lines)
# - Parser: services/api/app/util/gcode_parser.py (451 lines)
# - Endpoints: POST /api/cam/gcode/plot.svg, POST /api/cam/gcode/estimate
# - Features: G0/G1 linear, G2/G3 arcs, G20/G21 units, modal state tracking
#
# TEST STRUCTURE:
# - Group 1: Parser Availability (4 tests) - Basic endpoint health
# - Group 2: G-code Tokenization (6 tests) - Lexer and comment filtering
# - Group 3: Linear Motion (8 tests) - G0/G1 simulation with modal state
# - Group 4: Arc Motion (8 tests) - G2/G3 IJ/R methods and validation
# - Group 5: Units & Modal State (6 tests) - G20/G21 and state persistence
# - Group 6: SVG Generation (6 tests) - Polyline structure and rendering
# - Group 7: Time Estimation (4 tests) - Rapid vs feed time accuracy
# - Group 8: Edge Cases (4 tests) - Error handling and boundary conditions
#
# USAGE:
#   .\test_phase5_part3_n15_gcode_backplot.ps1
#
# PREREQUISITES:
# - FastAPI server running on localhost:8000
# - Both endpoints registered and functional
#
# =============================================================================

Param(
    [string]$ApiBase = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

# =============================================================================
# TEST UTILITIES
# =============================================================================

$script:testCount = 0
$script:passCount = 0
$script:failCount = 0
$script:grandPass = 0  # Track across all groups

function Test-Assert {
    param(
        [string]$Name,
        [bool]$Condition,
        [string]$FailMessage = "Assertion failed"
    )
    $script:testCount++
    if ($Condition) {
        $script:passCount++
        $script:grandPass++
        Write-Host "  ✓ $Name" -ForegroundColor Green
    } else {
        $script:failCount++
        Write-Host "  ✗ $Name" -ForegroundColor Red
        Write-Host "    $FailMessage" -ForegroundColor Yellow
    }
}

function Show-TestSummary {
    param([string]$GroupName)
    $pct = if ($script:testCount -gt 0) { [math]::Round(100.0 * $script:passCount / $script:testCount, 1) } else { 0 }
    Write-Host "`n$GroupName Results: $script:passCount/$script:testCount ($pct%)" -ForegroundColor Cyan
}

# =============================================================================
# GROUP 1: PARSER AVAILABILITY (4 tests)
# =============================================================================
Write-Host "`n=== GROUP 1: PARSER AVAILABILITY (4 tests) ===" -ForegroundColor Cyan
Write-Host "Verify endpoints exist and respond to basic requests`n"

$script:testCount = 0; $script:passCount = 0; $script:failCount = 0

# Test 1.1: Plot endpoint exists
try {
    $body = @{
        gcode = "G0 X0 Y0"
        units = "mm"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$ApiBase/api/cam/gcode/plot.svg" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 5
    
    Test-Assert "Plot endpoint exists (200 OK)" ($response.StatusCode -eq 200)
    Test-Assert "Response is SVG content-type" (($response.Headers.'Content-Type' | Out-String) -match 'svg')
} catch {
    Test-Assert "Plot endpoint exists" $false "HTTP error: $($_.Exception.Message)"
}

# Test 1.2: Estimate endpoint exists
try {
    $body = @{
        gcode = "G0 X10 Y10"
        units = "mm"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 5
    
    Test-Assert "Estimate endpoint exists (200 OK)" ($response -ne $null)
    Test-Assert "Estimate returns required fields" (
        $response.PSObject.Properties.Name -contains 'travel_mm' -and
        $response.PSObject.Properties.Name -contains 'cut_mm' -and
        $response.PSObject.Properties.Name -contains 't_total_min'
    )
} catch {
    Test-Assert "Estimate endpoint exists" $false "HTTP error: $($_.Exception.Message)"
}

Show-TestSummary "Group 1"

# =============================================================================
# GROUP 2: G-CODE TOKENIZATION (6 tests)
# =============================================================================
Write-Host "`n=== GROUP 2: G-CODE TOKENIZATION (6 tests) ===" -ForegroundColor Cyan
Write-Host "Test parser's lexer and comment filtering`n"

$script:testCount = 0; $script:passCount = 0; $script:failCount = 0

# Test 2.1: Parse comments (parentheses)
$gcode = @"
(Header comment)
G0 X10 Y10 (inline comment)
G1 X20 F600
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Parses gcode with parenthesis comments" ($result.points_xy.Count -ge 2)
} catch {
    Test-Assert "Parses gcode with comments" $false $_.Exception.Message
}

# Test 2.2: Parse comments (semicolon)
$gcode = @"
; Semicolon comment
G0 X0 Y0 ; inline semicolon
G1 X30 F1200
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Parses gcode with semicolon comments" ($result.points_xy.Count -ge 2)
} catch {
    Test-Assert "Parses gcode with semicolon comments" $false $_.Exception.Message
}

# Test 2.3: Parse multiline program
$gcode = @"
G21
G90
G0 X0 Y0 Z5
G1 Z-1 F300
G1 X50 Y50 F1200
G0 Z5
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Parses multiline program" ($result.points_xy.Count -ge 4) "Expected 4+ points, got $($result.points_xy.Count)"
    Test-Assert "Tracks modal state across lines" ($result.cut_mm -gt 0) "Expected cutting distance > 0"
} catch {
    Test-Assert "Parses multiline program" $false $_.Exception.Message
}

# Test 2.4: Parse uppercase and lowercase
$gcode = "g0 x10 y10`nG1 X20 Y20 f600"

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Handles mixed case G-code" ($result.points_xy.Count -ge 2)
} catch {
    Test-Assert "Handles mixed case G-code" $false $_.Exception.Message
}

# Test 2.5: Parse with spaces
$gcode = "G 0   X  10.5    Y   20.5  `n  G1   X30  F 1200  "

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Handles variable whitespace" ($result.points_xy.Count -ge 2)
} catch {
    Test-Assert "Handles variable whitespace" $false $_.Exception.Message
}

# Test 2.6: Parse decimal and negative numbers
$gcode = "G0 X-10.5 Y20.25`nG1 X0.0 Y-5.75 F600"

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Handles decimal and negative values" ($result.cut_mm -gt 0)
} catch {
    Test-Assert "Handles decimal and negative values" $false $_.Exception.Message
}

Show-TestSummary "Group 2"

# =============================================================================
# GROUP 3: LINEAR MOTION (8 tests)
# =============================================================================
Write-Host "`n=== GROUP 3: LINEAR MOTION (8 tests) ===" -ForegroundColor Cyan
Write-Host "Test G0/G1 simulation with modal state`n"

$script:testCount = 0; $script:passCount = 0; $script:failCount = 0

# Test 3.1: G0 rapid motion
$gcode = "G0 X100 Y50"

try {
    $body = @{
        gcode = $gcode
        units = "mm"
        rapid_mm_min = 3000.0
    } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    $expected_dist = [math]::Sqrt(100*100 + 50*50)
    Test-Assert "G0 calculates rapid distance" ([math]::Abs($result.travel_mm - $expected_dist) -lt 0.1) "Expected ~$expected_dist mm, got $($result.travel_mm)"
    Test-Assert "G0 has zero cutting distance" ($result.cut_mm -eq 0)
} catch {
    Test-Assert "G0 rapid motion" $false $_.Exception.Message
}

# Test 3.2: G1 feed motion
$gcode = "G1 X100 Y0 F1200"

try {
    $body = @{ gcode = $gcode; units = "mm"; default_feed_mm_min = 1200 } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "G1 calculates cutting distance" ($result.cut_mm -eq 100) "Expected 100mm, got $($result.cut_mm)"
    Test-Assert "G1 has zero rapid distance" ($result.travel_mm -eq 0)
} catch {
    Test-Assert "G1 feed motion" $false $_.Exception.Message
}

# Test 3.3: Modal position (omitted axes)
$gcode = @"
G0 X10 Y10
G1 Y20 F600
G1 X20
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Modal X/Y retained when omitted" ($result.cut_mm -eq 20) "Expected 20mm (10+10), got $($result.cut_mm)"
} catch {
    Test-Assert "Modal position" $false $_.Exception.Message
}

# Test 3.4: Mixed rapid and feed
$gcode = @"
G0 X50 Y0
G1 X100 F1200
G0 X150
"@

try {
    $body = @{ gcode = $gcode; units = "mm"; rapid_mm_min = 3000 } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Mixed rapid/feed distances tracked separately" (
        $result.travel_mm -gt 0 -and $result.cut_mm -gt 0
    ) "Rapid: $($result.travel_mm), Cut: $($result.cut_mm)"
} catch {
    Test-Assert "Mixed rapid and feed" $false $_.Exception.Message
}

# Test 3.5: Z-axis motion
$gcode = @"
G0 Z5
G1 Z-1 F300
G1 X50 F1200
G0 Z5
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Z-axis moves tracked" ($result.points_xy.Count -ge 2)
} catch {
    Test-Assert "Z-axis motion" $false $_.Exception.Message
}

# Test 3.6: Modal feed rate
$gcode = @"
G1 X10 F600
G1 X20
G1 X30 F1200
G1 X40
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Modal feed rate persists" ($result.cut_mm -eq 40)
    Test-Assert "Time reflects different feed rates" ($result.t_feed_min -gt 0)
} catch {
    Test-Assert "Modal feed rate" $false $_.Exception.Message
}

# Test 3.7: Path points generated
$gcode = @"
G0 X10 Y10
G1 X20 Y20 F600
G1 X30 Y30
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Path points include all moves" ($result.points_xy.Count -eq 4) "Expected 4 points, got $($result.points_xy.Count)"
    Test-Assert "Points are 2D arrays" ($result.points_xy[0].Count -eq 2)
} catch {
    Test-Assert "Path points generated" $false $_.Exception.Message
}

# Test 3.8: Long distance calculation
$gcode = "G0 X1000 Y1000"

try {
    $body = @{ gcode = $gcode; units = "mm"; rapid_mm_min = 3000 } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    $expected = [math]::Sqrt(1000*1000 + 1000*1000)
    Test-Assert "Handles large coordinates" ([math]::Abs($result.travel_mm - $expected) -lt 1)
} catch {
    Test-Assert "Long distance calculation" $false $_.Exception.Message
}

Show-TestSummary "Group 3"

# =============================================================================
# GROUP 4: ARC MOTION (8 tests)
# =============================================================================
Write-Host "`n=== GROUP 4: ARC MOTION (8 tests) ===" -ForegroundColor Cyan
Write-Host "Test G2/G3 arc simulation with IJ and R methods`n"

$script:testCount = 0; $script:passCount = 0; $script:failCount = 0

# Test 4.1: G2 clockwise arc (IJ method)
$gcode = @"
G0 X0 Y0
G1 X10 Y0 F600
G2 X20 Y0 I5 J0
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    $expected_arc = [math]::PI * 5  # Half circle, radius 5mm
    Test-Assert "G2 IJ arc length calculated" ($result.cut_mm -gt 10) "Expected >10mm (line+arc), got $($result.cut_mm)"
} catch {
    Test-Assert "G2 clockwise arc (IJ)" $false $_.Exception.Message
}

# Test 4.2: G3 counterclockwise arc (IJ method)
$gcode = @"
G0 X0 Y0
G1 X10 Y0 F600
G3 X20 Y0 I5 J0
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "G3 CCW arc length calculated" ($result.cut_mm -gt 10)
} catch {
    Test-Assert "G3 counterclockwise arc (IJ)" $false $_.Exception.Message
}

# Test 4.3: Arc with R radius method
$gcode = @"
G0 X0 Y0
G1 X10 Y0 F600
G2 X20 Y0 R5
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "R-method arc works" ($result.cut_mm -gt 10)
} catch {
    Test-Assert "Arc with R radius" $false $_.Exception.Message
}

# Test 4.4: Full circle arc
$gcode = @"
G0 X10 Y10
G2 X10 Y10 I5 J0 F600
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    $expected_circle = 2 * [math]::PI * 5  # Circumference r=5mm
    Test-Assert "Full circle arc" ([math]::Abs($result.cut_mm - $expected_circle) -lt 1) "Expected ~31.4mm, got $($result.cut_mm)"
} catch {
    Test-Assert "Full circle arc" $false $_.Exception.Message
}

# Test 4.5: Multiple arcs in sequence
$gcode = @"
G0 X0 Y0
G1 X10 Y0 F600
G2 X20 Y0 I5 J0
G3 X30 Y0 I5 J0
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Multiple arcs handled" ($result.cut_mm -gt 20)
} catch {
    Test-Assert "Multiple arcs in sequence" $false $_.Exception.Message
}

# Test 4.6: Arc in XY plane (G17)
$gcode = @"
G17
G0 X0 Y0
G2 X10 Y10 I5 J0 F600
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "G17 XY plane arc works" ($result.cut_mm -gt 0)
} catch {
    Test-Assert "Arc in XY plane" $false $_.Exception.Message
}

# Test 4.7: Invalid R fallback (chord distance)
$gcode = @"
G0 X0 Y0
G1 X100 Y0 F600
G2 X200 Y0 R10
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    # Invalid R (chord 100mm > diameter 20mm), should fallback to chord
    Test-Assert "Invalid R fallback to chord" ($result.cut_mm -ge 100) "Expected ≥100mm, got $($result.cut_mm)"
} catch {
    Test-Assert "Invalid R fallback" $false $_.Exception.Message
}

# Test 4.8: Missing IJ/R fallback
$gcode = @"
G0 X0 Y0
G1 X10 Y0 F600
G2 X20 Y0
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    # G1 X10 (10mm) + G2 X20 with chord fallback (10mm) = 20mm total
    Test-Assert "Missing IJ/R uses chord" ($result.cut_mm -ge 19.9 -and $result.cut_mm -le 20.1)
} catch {
    Test-Assert "Missing IJ/R fallback" $false $_.Exception.Message
}

Show-TestSummary "Group 4"

# =============================================================================
# GROUP 5: UNITS & MODAL STATE (6 tests)
# =============================================================================
Write-Host "`n=== GROUP 5: UNITS & MODAL STATE (6 tests) ===" -ForegroundColor Cyan
Write-Host "Test G20/G21 unit conversion and modal state persistence`n"

$script:testCount = 0; $script:passCount = 0; $script:failCount = 0

# Test 5.1: G21 millimeter mode
$gcode = @"
G21
G1 X100 F600
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "G21 mm mode works" ($result.cut_mm -eq 100)
} catch {
    Test-Assert "G21 millimeter mode" $false $_.Exception.Message
}

# Test 5.2: G20 inch mode (internal conversion to mm)
$gcode = @"
G20
G1 X1 F600
"@

try {
    $body = @{ gcode = $gcode; units = "inch" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    $expected = 25.4  # 1 inch = 25.4mm
    Test-Assert "G20 inch mode converts to mm" ([math]::Abs($result.cut_mm - $expected) -lt 0.1) "Expected ~25.4mm, got $($result.cut_mm)"
} catch {
    Test-Assert "G20 inch mode" $false $_.Exception.Message
}

# Test 5.3: Unit mode persists
$gcode = @"
G21
G1 X10 F600
G1 X20
G1 X30
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Unit mode persists across lines" ($result.cut_mm -eq 30)
} catch {
    Test-Assert "Unit mode persistence" $false $_.Exception.Message
}

# Test 5.4: G-code modal state (G0/G1)
$gcode = @"
G0
X10 Y10
X20 Y20
G1
X30 Y30 F600
X40 Y40
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "G0/G1 modal state works" ($result.travel_mm -gt 0 -and $result.cut_mm -gt 0)
} catch {
    Test-Assert "G-code modal state" $false $_.Exception.Message
}

# Test 5.5: Feed rate modal
$gcode = @"
F1200
G1 X10
G1 X20
G1 X30
"@

try {
    $body = @{ gcode = $gcode; units = "mm"; default_feed_mm_min = 500 } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    # Time should reflect F1200, not default F500
    $expected_time = 30.0 / 1200.0  # 30mm at 1200mm/min = 0.025min
    Test-Assert "Feed rate modal works" ([math]::Abs($result.t_feed_min - $expected_time) -lt 0.001)
} catch {
    Test-Assert "Feed rate modal" $false $_.Exception.Message
}

# Test 5.6: Plane selection (G17/G18/G19)
$gcode = @"
G17
G0 X10 Y10
G18
G0 X20 Z20
G19
G0 Y30 Z30
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Plane selection recognized" ($result.points_xy.Count -ge 2)
} catch {
    Test-Assert "Plane selection" $false $_.Exception.Message
}

Show-TestSummary "Group 5"

# =============================================================================
# GROUP 6: SVG GENERATION (6 tests)
# =============================================================================
Write-Host "`n=== GROUP 6: SVG GENERATION (6 tests) ===" -ForegroundColor Cyan
Write-Host "Test SVG polyline structure and rendering`n"

$script:testCount = 0; $script:passCount = 0; $script:failCount = 0

# Test 6.1: SVG basic structure
$gcode = "G0 X10 Y10`nG1 X20 Y20 F600"

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/api/cam/gcode/plot.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    
    Test-Assert "SVG has xml namespace" ($svg -match 'xmlns="http://www.w3.org/2000/svg"')
    Test-Assert "SVG has width/height" ($svg -match 'width="\d+"' -and $svg -match 'height="\d+"')
} catch {
    Test-Assert "SVG basic structure" $false $_.Exception.Message
}

# Test 6.2: SVG polyline element
try {
    $body = @{ gcode = "G0 X0 Y0`nG1 X100 Y100 F600"; units = "mm" } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/api/cam/gcode/plot.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    
    Test-Assert "SVG contains polyline element" ($svg -match '<polyline')
    Test-Assert "Polyline has points attribute" ($svg -match 'points="[0-9., ]+"')
} catch {
    Test-Assert "SVG polyline element" $false $_.Exception.Message
}

# Test 6.3: Custom stroke color
try {
    $body = @{ gcode = "G1 X50 F600"; units = "mm"; stroke = "red" } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/api/cam/gcode/plot.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    
    Test-Assert "SVG respects custom stroke color" ($svg -match 'stroke="red"')
} catch {
    Test-Assert "Custom stroke color" $false $_.Exception.Message
}

# Test 6.4: ViewBox scaling
try {
    $body = @{ gcode = "G0 X1000 Y500`nG1 X2000 Y1000 F600"; units = "mm" } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/api/cam/gcode/plot.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    
    Test-Assert "SVG has viewBox for large coordinates" ($svg -match 'viewBox="0 0 \d+ \d+"')
} catch {
    Test-Assert "ViewBox scaling" $false $_.Exception.Message
}

# Test 6.5: Empty path handling
try {
    $body = @{ gcode = ""; units = "mm" } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/api/cam/gcode/plot.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    
    Test-Assert "SVG handles empty gcode" ($svg -match '<svg')
} catch {
    Test-Assert "Empty path handling" $false $_.Exception.Message
}

# Test 6.6: Multiple moves polyline
try {
    $gcode = @"
G0 X10 Y10
G1 X20 Y20 F600
G1 X30 Y10
G1 X40 Y20
G1 X50 Y10
"@
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$ApiBase/api/cam/gcode/plot.svg" -Method POST -ContentType "application/json" -Body $body
    $svg = $response.Content
    
    # Count comma-separated point pairs (should be 6 points)
    $pointMatches = ([regex]::Matches($svg, '\d+\.\d+,\d+\.\d+')).Count
    Test-Assert "SVG includes all path points" ($pointMatches -ge 5) "Expected ≥5 points, got $pointMatches"
} catch {
    Test-Assert "Multiple moves polyline" $false $_.Exception.Message
}

Show-TestSummary "Group 6"

# =============================================================================
# GROUP 7: TIME ESTIMATION (4 tests)
# =============================================================================
Write-Host "`n=== GROUP 7: TIME ESTIMATION (4 tests) ===" -ForegroundColor Cyan
Write-Host "Test rapid vs feed time accuracy`n"

$script:testCount = 0; $script:passCount = 0; $script:failCount = 0

# Test 7.1: Rapid time calculation
$gcode = "G0 X3000 Y0"  # 3000mm at 3000mm/min = 1 minute

try {
    $body = @{ gcode = $gcode; units = "mm"; rapid_mm_min = 3000 } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Rapid time accurate" ([math]::Abs($result.t_rapid_min - 1.0) -lt 0.01) "Expected ~1.0min, got $($result.t_rapid_min)"
    Test-Assert "Rapid time added to total" ($result.t_total_min -eq $result.t_rapid_min)
} catch {
    Test-Assert "Rapid time calculation" $false $_.Exception.Message
}

# Test 7.2: Feed time calculation
$gcode = "G1 X600 F600"  # 600mm at 600mm/min = 1 minute

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Feed time accurate" ([math]::Abs($result.t_feed_min - 1.0) -lt 0.01) "Expected ~1.0min, got $($result.t_feed_min)"
} catch {
    Test-Assert "Feed time calculation" $false $_.Exception.Message
}

# Test 7.3: Total time = rapid + feed
$gcode = @"
G0 X1500
G1 X3000 F600
G0 X4500
"@

try {
    $body = @{ gcode = $gcode; units = "mm"; rapid_mm_min = 3000 } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    $expected_total = $result.t_rapid_min + $result.t_feed_min
    Test-Assert "Total time = rapid + feed" ([math]::Abs($result.t_total_min - $expected_total) -lt 0.0001)
} catch {
    Test-Assert "Total time breakdown" $false $_.Exception.Message
}

# Test 7.4: Different feed rates affect time
$gcode1 = "G1 X600 F600"  # 1 minute
$gcode2 = "G1 X600 F1200"  # 0.5 minutes

try {
    $body1 = @{ gcode = $gcode1; units = "mm" } | ConvertTo-Json
    $result1 = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body1
    
    $body2 = @{ gcode = $gcode2; units = "mm" } | ConvertTo-Json
    $result2 = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body2
    
    Test-Assert "Different feed rates affect time" ($result2.t_feed_min -lt $result1.t_feed_min) "F1200 should be faster than F600"
} catch {
    Test-Assert "Feed rate time impact" $false $_.Exception.Message
}

Show-TestSummary "Group 7"

# =============================================================================
# GROUP 8: EDGE CASES (4 tests)
# =============================================================================
Write-Host "`n=== GROUP 8: EDGE CASES (4 tests) ===" -ForegroundColor Cyan
Write-Host "Test error handling and boundary conditions`n"

$script:testCount = 0; $script:passCount = 0; $script:failCount = 0

# Test 8.1: Empty G-code
try {
    $body = @{ gcode = ""; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Empty gcode returns zero distances" ($result.travel_mm -eq 0 -and $result.cut_mm -eq 0)
    Test-Assert "Empty gcode has origin point" ($result.points_xy.Count -eq 1)
} catch {
    Test-Assert "Empty G-code handling" $false $_.Exception.Message
}

# Test 8.2: Comments only
$gcode = @"
(Header comment)
; Semicolon comment
(Another comment)
"@

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    Test-Assert "Comments-only gcode valid" ($result.points_xy.Count -eq 1)
} catch {
    Test-Assert "Comments only handling" $false $_.Exception.Message
}

# Test 8.3: Zero feed rate guard
$gcode = "G1 X100 F0"

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body
    
    # Should use clamped minimum feed, not divide by zero
    Test-Assert "Zero feed rate clamped" ($result.t_feed_min -gt 0 -and $result.t_feed_min -lt 1000000)
} catch {
    Test-Assert "Zero feed rate guard" $false $_.Exception.Message
}

# Test 8.4: Large program (stress test)
$moves = 1..100 | ForEach-Object { "G1 X$_ Y$_ F1200" }
$gcode = $moves -join "`n"

try {
    $body = @{ gcode = $gcode; units = "mm" } | ConvertTo-Json
    $result = Invoke-RestMethod -Uri "$ApiBase/api/cam/gcode/estimate" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10
    
    Test-Assert "Large program (100 moves) processed" ($result.points_xy.Count -ge 100)
    Test-Assert "Large program stats valid" ($result.cut_mm -gt 0 -and $result.t_total_min -gt 0)
} catch {
    Test-Assert "Large program stress test" $false $_.Exception.Message
}

Show-TestSummary "Group 8"

# =============================================================================
# FINAL SUMMARY
# =============================================================================
Write-Host "`n" "=" * 80 -ForegroundColor Cyan
Write-Host "N.15 G-CODE BACKPLOT VALIDATION COMPLETE" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

$grandTotal = 56  # Actual Test-Assert call count across all groups
$grandPassFinal = $script:grandPass
$grandFail = $grandTotal - $grandPassFinal
$pct = [math]::Round(100.0 * $grandPassFinal / $grandTotal, 1)

Write-Host "`nGRAND TOTAL: $grandPassFinal/$grandTotal ($pct%)" -ForegroundColor $(if ($pct -ge 90) { "Green" } else { "Yellow" })
Write-Host "  Group 1: Parser Availability (4 tests)" -ForegroundColor Gray
Write-Host "  Group 2: G-code Tokenization (6 tests)" -ForegroundColor Gray
Write-Host "  Group 3: Linear Motion (8 tests)" -ForegroundColor Gray
Write-Host "  Group 4: Arc Motion (8 tests)" -ForegroundColor Gray
Write-Host "  Group 5: Units & Modal State (6 tests)" -ForegroundColor Gray
Write-Host "  Group 6: SVG Generation (6 tests)" -ForegroundColor Gray
Write-Host "  Group 7: Time Estimation (4 tests)" -ForegroundColor Gray
Write-Host "  Group 8: Edge Cases (4 tests)" -ForegroundColor Gray

if ($grandPassFinal -eq $grandTotal) {
    Write-Host "`n🎉 PERFECT SCORE! All tests passed!" -ForegroundColor Green
} elseif ($pct -ge 90) {
    Write-Host "`n✅ EXCELLENT! $grandPassFinal/$grandTotal tests passed" -ForegroundColor Green
} elseif ($pct -ge 80) {
    Write-Host "`n✓ GOOD. $grandPassFinal/$grandTotal tests passed" -ForegroundColor Yellow
} else {
    Write-Host "`n⚠️ NEEDS WORK. Only $grandPassFinal/$grandTotal tests passed" -ForegroundColor Red
}

Write-Host "`nCumulative Phase 5 Progress:" -ForegroundColor Cyan
Write-Host "  N10:  12/12  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.0:  32/32  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.06: 37/37  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.09: 56/56  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.07: 28/28  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.08: 43/43  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.11: 44/45  (97.8%) ✅" -ForegroundColor Gray
Write-Host "  N.12: 46/50  (92.0%) ✅" -ForegroundColor Gray
Write-Host "  N.13: 45/45  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.14: 60/60  (100%) ✅" -ForegroundColor Gray
Write-Host "  N.15: $grandPassFinal/56  ($pct%) $(if ($pct -ge 90) {'✅'} else {'⏳'})" -ForegroundColor $(if ($pct -ge 90) { "Green" } else { "Yellow" })
Write-Host "  ─────────────────────────────────" -ForegroundColor Gray
$cumulative = 403 + $grandPassFinal
$cumulativeTotal = 408 + 56
$cumulativePct = [math]::Round(100.0 * $cumulative / $cumulativeTotal, 1)
Write-Host "  TOTAL: $cumulative/$cumulativeTotal ($cumulativePct%)" -ForegroundColor Cyan

Write-Host "`nN-Series Progress: 11/16 (68.8%)" -ForegroundColor Cyan

Write-Host "`n" "=" * 80 -ForegroundColor Cyan

exit $(if ($grandPassFinal -eq $grandTotal) { 0 } else { 1 })
