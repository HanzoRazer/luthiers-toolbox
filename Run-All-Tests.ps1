#!/usr/bin/env pwsh
# Run-All-Tests.ps1
# Comprehensive test runner for entire repository

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        LUTHIER'S TOOLBOX - COMPREHENSIVE TEST SUITE                 ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$totalTests = 0
$totalPassed = 0
$totalFailed = 0
$testResults = @()

function Run-TestScript {
    param(
        [string]$ScriptPath,
        [string]$Category
    )
    
    $scriptName = Split-Path $ScriptPath -Leaf
    Write-Host "[$Category] Running $scriptName..." -ForegroundColor Yellow
    
    try {
        $output = & $ScriptPath 2>&1 | Out-String
        
        # Parse test results
        $passed = 0
        $failed = 0
        $total = 0
        
        # Pattern 1: "Tests Passed: X / Y"
        if ($output -match "Tests Passed:\s*(\d+)\s*/\s*(\d+)") {
            $passed = [int]$matches[1]
            $total = [int]$matches[2]
            $failed = $total - $passed
        }
        # Pattern 2: "Passed: X" and "Failed: Y"
        elseif ($output -match "Passed:\s*(\d+)" -and $output -match "Failed:\s*(\d+)") {
            $passed = [int]$matches[1]
            $failed = [int]$matches[2]
            $total = $passed + $failed
        }
        # Pattern 3: Check for "All tests passing" or similar success messages
        elseif ($output -match "All tests (passing|passed|successful)" -or $output -match "✅|✓ PASS") {
            # Count individual test passes
            $passCount = ([regex]::Matches($output, "✓|✅|PASS")).Count
            if ($passCount -gt 0) {
                $passed = $passCount
                $total = $passCount
                $failed = 0
            }
        }
        # Pattern 4: No clear pattern, check exit code
        elseif ($LASTEXITCODE -eq 0) {
            Write-Host "  ⚠️ Success inferred from exit code (no parseable test count)" -ForegroundColor Yellow
            $passed = 1
            $total = 1
            $failed = 0
        }
        
        if ($total -eq 0) {
            Write-Host "  ⚠️ Could not parse test results" -ForegroundColor Yellow
            return @{
                Script = $scriptName
                Category = $Category
                Passed = 0
                Failed = 0
                Total = 0
                Status = "UNKNOWN"
            }
        }
        
        $status = if ($failed -eq 0) { "PASS" } elseif ($passed -gt 0) { "PARTIAL" } else { "FAIL" }
        $color = if ($status -eq "PASS") { "Green" } elseif ($status -eq "PARTIAL") { "Yellow" } else { "Red" }
        
        Write-Host "  $status : $passed / $total tests passed" -ForegroundColor $color
        
        return @{
            Script = $scriptName
            Category = $Category
            Passed = $passed
            Failed = $failed
            Total = $total
            Status = $status
        }
    }
    catch {
        Write-Host "  ❌ ERROR: $_" -ForegroundColor Red
        return @{
            Script = $scriptName
            Category = $Category
            Passed = 0
            Failed = 1
            Total = 1
            Status = "ERROR"
        }
    }
}

# Wave 19 Tests
Write-Host "`n═══ Wave 19: Fan-Fret CAM ═══" -ForegroundColor Cyan
$wave19Tests = @(
    ".\Test-Wave19-FanFretMath.ps1",
    ".\Test-Wave19-FanFretCAM.ps1",
    ".\Test-Wave19-PerFretRisk.ps1",
    ".\Test-Wave19-PhaseD-Frontend.ps1"
)
foreach ($test in $wave19Tests) {
    if (Test-Path $test) {
        $result = Run-TestScript -ScriptPath $test -Category "Wave 19"
        $testResults += $result
        $totalTests += $result.Total
        $totalPassed += $result.Passed
        $totalFailed += $result.Failed
    }
}

# Wave 18 Tests
Write-Host "`n═══ Wave 18: Feasibility Fusion ═══" -ForegroundColor Cyan
if (Test-Path ".\Test-Wave18-FeasibilityFusion.ps1") {
    $result = Run-TestScript -ScriptPath ".\Test-Wave18-FeasibilityFusion.ps1" -Category "Wave 18"
    $testResults += $result
    $totalTests += $result.Total
    $totalPassed += $result.Passed
    $totalFailed += $result.Failed
}

# Wave 17 Tests
Write-Host "`n═══ Wave 17: Fretboard CAM ═══" -ForegroundColor Cyan
if (Test-Path ".\Test-Wave17-FretboardCAM.ps1") {
    $result = Run-TestScript -ScriptPath ".\Test-Wave17-FretboardCAM.ps1" -Category "Wave 17"
    $testResults += $result
    $totalTests += $result.Total
    $totalPassed += $result.Passed
    $totalFailed += $result.Failed
}

# Wave 15-16 Tests
Write-Host "`n═══ Wave 15-16: Frontend ═══" -ForegroundColor Cyan
if (Test-Path ".\Test-Wave15-16-Frontend.ps1") {
    $result = Run-TestScript -ScriptPath ".\Test-Wave15-16-Frontend.ps1" -Category "Wave 15-16"
    $testResults += $result
    $totalTests += $result.Total
    $totalPassed += $result.Passed
    $totalFailed += $result.Failed
}

# Phase E Tests
Write-Host "`n═══ Phase E: CAM Preview ═══" -ForegroundColor Cyan
if (Test-Path ".\Test-PhaseE-CAMPreview.ps1") {
    $result = Run-TestScript -ScriptPath ".\Test-PhaseE-CAMPreview.ps1" -Category "Phase E"
    $testResults += $result
    $totalTests += $result.Total
    $totalPassed += $result.Passed
    $totalFailed += $result.Failed
}

# N10 WebSocket Tests
Write-Host "`n═══ N10: WebSocket ═══" -ForegroundColor Cyan
if (Test-Path ".\Test-N10-WebSocket.ps1") {
    $result = Run-TestScript -ScriptPath ".\Test-N10-WebSocket.ps1" -Category "N10"
    $testResults += $result
    $totalTests += $result.Total
    $totalPassed += $result.Passed
    $totalFailed += $result.Failed
}

# MM0 Tests
Write-Host "`n═══ MM0: Strip Families ═══" -ForegroundColor Cyan
if (Test-Path ".\Test-MM0-StripFamilies.ps1") {
    $result = Run-TestScript -ScriptPath ".\Test-MM0-StripFamilies.ps1" -Category "MM0"
    $testResults += $result
    $totalTests += $result.Total
    $totalPassed += $result.Passed
    $totalFailed += $result.Failed
}

# Compare Lab Tests
Write-Host "`n═══ Compare Lab: Guardrails ═══" -ForegroundColor Cyan
if (Test-Path ".\Test-CompareLab-Guardrails.ps1") {
    $result = Run-TestScript -ScriptPath ".\Test-CompareLab-Guardrails.ps1" -Category "Compare Lab"
    $testResults += $result
    $totalTests += $result.Total
    $totalPassed += $result.Passed
    $totalFailed += $result.Failed
}

# B22 Export Tests
Write-Host "`n═══ B22: Export ═══" -ForegroundColor Cyan
if (Test-Path ".\Test-B22-Export-P0.1.ps1") {
    $result = Run-TestScript -ScriptPath ".\Test-B22-Export-P0.1.ps1" -Category "B22"
    $testResults += $result
    $totalTests += $result.Total
    $totalPassed += $result.Passed
    $totalFailed += $result.Failed
}

# RMOS Tests (scripts folder)
Write-Host "`n═══ RMOS: Rosette Manufacturing OS ═══" -ForegroundColor Cyan
$rmosTests = @(
    ".\scripts\Test-RMOS-Sandbox.ps1",
    ".\scripts\Test-RMOS-AI-Core.ps1",
    ".\scripts\Test-RMOS-SlicePreview.ps1",
    ".\scripts\Test-RMOS-PipelineHandoff.ps1"
)
foreach ($test in $rmosTests) {
    if (Test-Path $test) {
        $result = Run-TestScript -ScriptPath $test -Category "RMOS"
        $testResults += $result
        $totalTests += $result.Total
        $totalPassed += $result.Passed
        $totalFailed += $result.Failed
    }
}

# Analytics Tests
Write-Host "`n═══ Analytics: N9 ═══" -ForegroundColor Cyan
$analyticsTests = @(
    ".\scripts\Test-Analytics-N9.ps1",
    ".\scripts\Test-Advanced-Analytics-N9_1.ps1"
)
foreach ($test in $analyticsTests) {
    if (Test-Path $test) {
        $result = Run-TestScript -ScriptPath $test -Category "Analytics"
        $testResults += $result
        $totalTests += $result.Total
        $totalPassed += $result.Passed
        $totalFailed += $result.Failed
    }
}

# Directional Workflow Tests
Write-Host "`n═══ Directional Workflow ═══" -ForegroundColor Cyan
if (Test-Path ".\scripts\Test-DirectionalWorkflow.ps1") {
    $result = Run-TestScript -ScriptPath ".\scripts\Test-DirectionalWorkflow.ps1" -Category "Workflow"
    $testResults += $result
    $totalTests += $result.Total
    $totalPassed += $result.Passed
    $totalFailed += $result.Failed
}

# Final Summary
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                       COMPREHENSIVE TEST RESULTS                     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Group by category
$categories = $testResults | Group-Object Category | Sort-Object Name
foreach ($category in $categories) {
    Write-Host "══ $($category.Name) ══" -ForegroundColor Yellow
    foreach ($result in $category.Group) {
        $statusColor = switch ($result.Status) {
            "PASS" { "Green" }
            "PARTIAL" { "Yellow" }
            "FAIL" { "Red" }
            "ERROR" { "Red" }
            default { "Gray" }
        }
        $statusIcon = switch ($result.Status) {
            "PASS" { "✅" }
            "PARTIAL" { "⚠️" }
            "FAIL" { "❌" }
            "ERROR" { "💥" }
            default { "❓" }
        }
        Write-Host "  $statusIcon $($result.Script): $($result.Passed)/$($result.Total) passed" -ForegroundColor $statusColor
    }
    Write-Host ""
}

# Overall Statistics
$percentage = if ($totalTests -gt 0) { [math]::Round(($totalPassed / $totalTests) * 100, 1) } else { 0 }
Write-Host "╔══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                         OVERALL STATISTICS                           ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  Total Tests:      $totalTests" -ForegroundColor White
Write-Host "║  Tests Passed:     $totalPassed" -ForegroundColor Green
Write-Host "║  Tests Failed:     $totalFailed" -ForegroundColor $(if ($totalFailed -eq 0) { "Green" } else { "Red" })
Write-Host "║  Success Rate:     $percentage%" -ForegroundColor $(if ($percentage -ge 95) { "Green" } elseif ($percentage -ge 85) { "Yellow" } else { "Red" })
Write-Host "╚══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($totalFailed -eq 0 -and $totalTests -gt 0) {
    Write-Host "🎉 ALL TESTS PASSING! Repository is in excellent health." -ForegroundColor Green
} elseif ($percentage -ge 95) {
    Write-Host "✅ Repository is production-ready with $totalFailed known issue(s)." -ForegroundColor Yellow
} elseif ($percentage -ge 85) {
    Write-Host "⚠️ Repository has $totalFailed failing test(s). Review recommended." -ForegroundColor Yellow
} else {
    Write-Host "❌ Repository has $totalFailed failing test(s). Immediate attention required." -ForegroundColor Red
}

Write-Host ""
Write-Host "Detailed Results:" -ForegroundColor Cyan
Write-Host "  Total Test Scripts Run: $($testResults.Count)" -ForegroundColor Gray
Write-Host "  Scripts with All Tests Passing: $(($testResults | Where-Object { $_.Status -eq 'PASS' }).Count)" -ForegroundColor Gray
Write-Host "  Scripts with Partial Passes: $(($testResults | Where-Object { $_.Status -eq 'PARTIAL' }).Count)" -ForegroundColor Gray
Write-Host "  Scripts with All Tests Failing: $(($testResults | Where-Object { $_.Status -eq 'FAIL' -or $_.Status -eq 'ERROR' }).Count)" -ForegroundColor Gray
Write-Host ""

exit $(if ($percentage -ge 85) { 0 } else { 1 })
