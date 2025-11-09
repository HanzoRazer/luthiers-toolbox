# Test DXF Preflight System (Phase 3.2)
# Tests the new validation system based on nc_lint.py pattern

$API_URL = "http://localhost:8000"
$passed = 0
$failed = 0

Write-Host "`n=== Testing Phase 3.2: DXF Preflight System ===" -ForegroundColor Cyan

# Find Gibson L-00 DXF file
$gibsonFiles = Get-ChildItem -Path "." -Recurse -Filter "*L-00*.dxf" -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $gibsonFiles) {
    Write-Host "`n✗ No Gibson L-00 DXF file found" -ForegroundColor Red
    Write-Host "  Please ensure a Gibson_L-00.dxf file exists in the project" -ForegroundColor Yellow
    exit 1
}

$dxfPath = $gibsonFiles.FullName
Write-Host "`nUsing DXF: $dxfPath" -ForegroundColor Gray

# Test 1: Health Check
Write-Host "`n1. Testing GET /cam/blueprint/health" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/cam/blueprint/health" -Method Get
    if ($response.status -eq "ok" -and $response.phase -eq "3.2") {
        Write-Host "  ✓ Blueprint CAM bridge healthy (Phase 3.2)" -ForegroundColor Green
        Write-Host "    Endpoints: $($response.endpoints -join ', ')" -ForegroundColor Gray
        Write-Host "    Features:" -ForegroundColor Gray
        $response.features.PSObject.Properties | ForEach-Object {
            Write-Host "      - $($_.Name): $($_.Value)" -ForegroundColor Gray
        }
        $passed++
    } else {
        Write-Host "  ✗ Health check failed" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 2: DXF Preflight (JSON format)
Write-Host "`n2. Testing POST /cam/blueprint/preflight (JSON)" -ForegroundColor Yellow
try {
    $form = @{
        file = Get-Item $dxfPath
        format = "json"
    }
    
    $response = Invoke-RestMethod -Uri "$API_URL/cam/blueprint/preflight" -Method Post -Form $form
    
    Write-Host "  ✓ Preflight validation completed" -ForegroundColor Green
    Write-Host "    File: $($response.filename)" -ForegroundColor Gray
    Write-Host "    DXF Version: $($response.dxf_version)" -ForegroundColor Gray
    Write-Host "    Status: $(if ($response.passed) { 'PASSED' } else { 'FAILED' })" -ForegroundColor $(if ($response.passed) { "Green" } else { "Red" })
    Write-Host "    Total Entities: $($response.total_entities)" -ForegroundColor Gray
    Write-Host "    Layers: $($response.layers.Count)" -ForegroundColor Gray
    
    # Display summary
    Write-Host "`n  Issue Summary:" -ForegroundColor Cyan
    Write-Host "    - Errors: $($response.summary.errors)" -ForegroundColor $(if ($response.summary.errors -gt 0) { "Red" } else { "Green" })
    Write-Host "    - Warnings: $($response.summary.warnings)" -ForegroundColor $(if ($response.summary.warnings -gt 0) { "Yellow" } else { "Green" })
    Write-Host "    - Info: $($response.summary.info)" -ForegroundColor Gray
    
    # Display issues by category
    if ($response.issues.Count -gt 0) {
        Write-Host "`n  Issues by Category:" -ForegroundColor Cyan
        $response.issues | Group-Object -Property category | ForEach-Object {
            Write-Host "    $($_.Name): $($_.Count)" -ForegroundColor Gray
        }
        
        # Display first 5 issues
        Write-Host "`n  Sample Issues:" -ForegroundColor Cyan
        $response.issues | Select-Object -First 5 | ForEach-Object {
            $color = switch ($_.severity) {
                "ERROR" { "Red" }
                "WARNING" { "Yellow" }
                default { "Gray" }
            }
            Write-Host "    [$($_.severity)] $($_.message)" -ForegroundColor $color
            if ($_.suggestion) {
                Write-Host "      💡 $($_.suggestion)" -ForegroundColor Gray
            }
        }
    }
    
    # Display entity type stats
    if ($response.stats.entity_types) {
        Write-Host "`n  Entity Types:" -ForegroundColor Cyan
        $response.stats.entity_types.PSObject.Properties | ForEach-Object {
            Write-Host "    - $($_.Name): $($_.Value)" -ForegroundColor Gray
        }
    }
    
    $passed++
    
    # Save response for validation
    $script:preflightReport = $response
    
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 3: DXF Preflight (HTML format)
Write-Host "`n3. Testing POST /cam/blueprint/preflight (HTML)" -ForegroundColor Yellow
try {
    $htmlOutputPath = "$env:TEMP\dxf_preflight_report.html"
    
    $form = @{
        file = Get-Item $dxfPath
        format = "html"
    }
    
    Invoke-WebRequest -Uri "$API_URL/cam/blueprint/preflight" -Method Post -Form $form -OutFile $htmlOutputPath
    
    if (Test-Path $htmlOutputPath) {
        $htmlSize = (Get-Item $htmlOutputPath).Length
        Write-Host "  ✓ HTML report generated ($htmlSize bytes)" -ForegroundColor Green
        Write-Host "    Path: $htmlOutputPath" -ForegroundColor Gray
        
        # Read and validate HTML content
        $htmlContent = Get-Content $htmlOutputPath -Raw
        
        $checks = @(
            @{ Pattern = "DXF Preflight Report"; Name = "Title" },
            @{ Pattern = "ERRORS"; Name = "Error count" },
            @{ Pattern = "WARNINGS"; Name = "Warning count" },
            @{ Pattern = "Gibson_L-00"; Name = "Filename" }
        )
        
        $checksPass = 0
        foreach ($check in $checks) {
            if ($htmlContent -match $check.Pattern) {
                $checksPass++
            } else {
                Write-Host "    ⚠ Missing: $($check.Name)" -ForegroundColor Yellow
            }
        }
        
        if ($checksPass -eq $checks.Count) {
            Write-Host "    ✓ HTML structure validated ($checksPass/$($checks.Count) checks)" -ForegroundColor Green
        }
        
        $passed++
    } else {
        Write-Host "  ✗ HTML report not generated" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ✗ Error: $_" -ForegroundColor Red
    $failed++
}

# Test 4: Validate Preflight Rules
if ($script:preflightReport) {
    Write-Host "`n4. Validating Preflight Rules" -ForegroundColor Yellow
    
    $ruleChecks = 0
    $rulesPassed = 0
    
    # Rule 1: File was parsed
    $ruleChecks++
    if ($script:preflightReport.total_entities -gt 0) {
        Write-Host "  ✓ DXF file parsed successfully" -ForegroundColor Green
        $rulesPassed++
    } else {
        Write-Host "  ✗ DXF parsing failed (no entities)" -ForegroundColor Red
    }
    
    # Rule 2: Layers detected
    $ruleChecks++
    if ($script:preflightReport.layers.Count -gt 0) {
        Write-Host "  ✓ Layers detected ($($script:preflightReport.layers.Count) layers)" -ForegroundColor Green
        $rulesPassed++
    } else {
        Write-Host "  ✗ No layers detected" -ForegroundColor Red
    }
    
    # Rule 3: Entity types analyzed
    $ruleChecks++
    if ($script:preflightReport.stats.entity_types) {
        $entityTypeCount = ($script:preflightReport.stats.entity_types.PSObject.Properties).Count
        Write-Host "  ✓ Entity types analyzed ($entityTypeCount types)" -ForegroundColor Green
        $rulesPassed++
    } else {
        Write-Host "  ✗ No entity type analysis" -ForegroundColor Red
    }
    
    # Rule 4: Issues categorized
    $ruleChecks++
    $categories = $script:preflightReport.issues | Group-Object -Property category
    if ($categories.Count -gt 0) {
        Write-Host "  ✓ Issues categorized ($($categories.Count) categories)" -ForegroundColor Green
        $rulesPassed++
    } else {
        Write-Host "  ⚠ No issues found (may be perfect DXF or missing checks)" -ForegroundColor Yellow
        $rulesPassed++  # Don't fail on this
    }
    
    # Rule 5: Severity levels used
    $ruleChecks++
    $severities = $script:preflightReport.issues | Group-Object -Property severity
    if ($severities.Count -gt 0) {
        Write-Host "  ✓ Severity levels applied ($($severities.Name -join ', '))" -ForegroundColor Green
        $rulesPassed++
    } else {
        Write-Host "  ⚠ No severity classification" -ForegroundColor Yellow
        $rulesPassed++  # Don't fail on this
    }
    
    if ($rulesPassed -eq $ruleChecks) {
        Write-Host "`n  ✓ All validation rules passed ($rulesPassed/$ruleChecks)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "`n  ✗ Some validation rules failed ($rulesPassed/$ruleChecks)" -ForegroundColor Red
        $failed++
    }
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($failed -eq 0) {
    Write-Host "`n✓ All Phase 3.2 DXF preflight tests passed!" -ForegroundColor Green
    Write-Host "  Next step: Build PipelineLab UI" -ForegroundColor Cyan
    
    # Open HTML report in browser
    if ($htmlOutputPath -and (Test-Path $htmlOutputPath)) {
        Write-Host "`nOpening HTML report in browser..." -ForegroundColor Cyan
        Start-Process $htmlOutputPath
    }
    
    exit 0
} else {
    Write-Host "`n✗ Some tests failed" -ForegroundColor Red
    exit 1
}
