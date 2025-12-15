#!/usr/bin/env pwsh
<#
.SYNOPSIS
N.0 Smart Post Configurator - User Validation Test Script

.DESCRIPTION
Interactive validation of N.0 integration through API testing.
Tests creating, editing, deleting custom posts and verifying builtin protection.

.NOTES
Phase 5 Part 2: N.0 Smart Post Configurator
Date: January 2025
#>

$ErrorActionPreference = "Continue"
$baseUrl = "http://localhost:8000"

Write-Host "`n=== N.0 Smart Post Configurator - User Validation ===" -ForegroundColor Cyan
Write-Host "Testing API functionality for UI validation`n" -ForegroundColor Gray

# Test counters
$passCount = 0
$failCount = 0

function Test-Step {
    param(
        [string]$Description,
        [scriptblock]$Test
    )
    Write-Host "Testing: $Description" -ForegroundColor Yellow
    try {
        $result = & $Test
        if ($result) {
            Write-Host "  ✓ PASS" -ForegroundColor Green
            $script:passCount++
            return $result
        } else {
            Write-Host "  ✗ FAIL" -ForegroundColor Red
            $script:failCount++
            return $null
        }
    } catch {
        Write-Host "  ✗ ERROR: $_" -ForegroundColor Red
        $script:failCount++
        return $null
    }
}

# Test 1: Verify server is running
Write-Host "`n--- Step 1: Server Health Check ---" -ForegroundColor Cyan
$health = Test-Step "API server is accessible" {
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/" -Method GET -TimeoutSec 5
        return $response.posts -is [array]
    } catch {
        Write-Host "    Server not accessible. Please ensure:" -ForegroundColor Red
        Write-Host "    1. Backend running: cd services/api; python -m uvicorn app.main:app --reload --port 8000" -ForegroundColor Gray
        Write-Host "    2. Frontend running: cd client; npm run dev" -ForegroundColor Gray
        return $false
    }
}

if (-not $health) {
    Write-Host "`n❌ Server not accessible. Exiting." -ForegroundColor Red
    exit 1
}

# Test 2: List builtin posts
Write-Host "`n--- Step 2: Builtin Posts Validation ---" -ForegroundColor Cyan
$posts = Test-Step "List all posts (expect 5 builtins)" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/" -Method GET
    $builtins = $response.posts | Where-Object { $_.builtin -eq $true }
    Write-Host "    Found $($response.posts.Count) total posts, $($builtins.Count) builtin" -ForegroundColor Gray
    return $builtins.Count -eq 5
}

$builtinIds = @("GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO")
foreach ($id in $builtinIds) {
    Test-Step "Get builtin post: $id" {
        $post = Invoke-RestMethod -Uri "$baseUrl/api/posts/$id" -Method GET
        Write-Host "    Name: $($post.name)" -ForegroundColor Gray
        Write-Host "    Header lines: $($post.header.Count)" -ForegroundColor Gray
        Write-Host "    Footer lines: $($post.footer.Count)" -ForegroundColor Gray
        return $post.id -eq $id -and $post.builtin -eq $true
    } | Out-Null
}

# Test 3: Token system validation
Write-Host "`n--- Step 3: Token System Validation ---" -ForegroundColor Cyan
$tokens = Test-Step "List available tokens" {
    $tokenList = Invoke-RestMethod -Uri "$baseUrl/api/posts/tokens/list" -Method GET
    $tokenCount = ($tokenList.PSObject.Properties | Measure-Object).Count
    Write-Host "    Available tokens: $tokenCount" -ForegroundColor Gray
    $tokenList.PSObject.Properties | Select-Object -First 5 | ForEach-Object {
        Write-Host "    - $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
    return $tokenCount -ge 10
}

# Test 4: Create custom post
Write-Host "`n--- Step 4: Create Custom Post ---" -ForegroundColor Cyan
$timestamp = Get-Date -Format "HHmmss"
$testPostId = "TEST_HAAS_$timestamp"

$customPost = @{
    id = $testPostId
    name = "Test Haas VF-2"
    description = "Test custom post created during validation"
    header = @(
        "G90",
        "G21",
        "G17",
        "G54",
        "(Custom header for Haas)",
        "M6 T{{TOOL_NUMBER}}"
    )
    footer = @(
        "M30",
        "(End of program)",
        "(Generated: {{DATE}})"
    )
    metadata = @{
        controller_family = "haas"
        gcode_dialect = "Fanuc"
        supports_arcs = $true
        has_tool_changer = $true
    }
}

$created = Test-Step "Create custom post: $testPostId" {
    $body = $customPost | ConvertTo-Json -Depth 5
    $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/" `
        -Method POST `
        -Body $body `
        -ContentType "application/json"
    Write-Host "    Created at: $($response.created_at)" -ForegroundColor Gray
    return $response.id -eq $testPostId
}

# Test 5: Validate post configuration
Write-Host "`n--- Step 5: Validation System ---" -ForegroundColor Cyan
$validateGood = Test-Step "Validate good configuration (new ID)" {
    $validPost = $customPost.Clone()
    $validPost.id = "VALID_TEST_$timestamp"
    $body = $validPost | ConvertTo-Json -Depth 5
    $result = Invoke-RestMethod -Uri "$baseUrl/api/posts/validate" `
        -Method POST `
        -Body $body `
        -ContentType "application/json"
    Write-Host "    Valid: $($result.valid)" -ForegroundColor Gray
    Write-Host "    Warnings: $($result.warnings.Count)" -ForegroundColor Gray
    Write-Host "    Errors: $($result.errors.Count)" -ForegroundColor Gray
    return $result.valid -eq $true -and $result.errors.Count -eq 0
}

# Test with long line (warning)
$validateWarn = Test-Step "Validate with warning (long line)" {
    $longLinePost = $customPost.Clone()
    $longLinePost.id = "WARN_TEST_$timestamp"
    $longLinePost.header = @("G90", "(" + ("x" * 300) + ")")
    $body = $longLinePost | ConvertTo-Json -Depth 5
    $result = Invoke-RestMethod -Uri "$baseUrl/api/posts/validate" `
        -Method POST `
        -Body $body `
        -ContentType "application/json"
    Write-Host "    Valid: $($result.valid)" -ForegroundColor Gray
    Write-Host "    Warnings: $($result.warnings.Count) (expected: 1)" -ForegroundColor Gray
    if ($result.warnings.Count -gt 0) {
        Write-Host "    Warning message: $($result.warnings[0])" -ForegroundColor Gray
    }
    return $result.valid -eq $true -and $result.warnings.Count -gt 0
}

# Test 6: Update custom post
Write-Host "`n--- Step 6: Update Custom Post ---" -ForegroundColor Cyan
$updated = Test-Step "Update post description" {
    $update = @{
        description = "Updated description - validation test complete"
    }
    $body = $update | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/$testPostId" `
        -Method PUT `
        -Body $body `
        -ContentType "application/json"
    Write-Host "    Updated at: $($response.updated_at)" -ForegroundColor Gray
    return $response.id -eq $testPostId
}

# Verify update
$verifyUpdate = Test-Step "Verify update was applied" {
    $post = Invoke-RestMethod -Uri "$baseUrl/api/posts/$testPostId" -Method GET
    Write-Host "    New description: $($post.description)" -ForegroundColor Gray
    return $post.description -eq "Updated description - validation test complete"
}

# Test 7: Builtin protection
Write-Host "`n--- Step 7: Builtin Protection ---" -ForegroundColor Cyan
$protectDelete = Test-Step "Cannot delete builtin post (GRBL)" {
    try {
        Invoke-RestMethod -Uri "$baseUrl/api/posts/GRBL" -Method DELETE
        return $false  # Should not succeed
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "    Status code: $statusCode (expected: 403)" -ForegroundColor Gray
        Write-Host "    Error message: $($_.ErrorDetails.Message)" -ForegroundColor Gray
        return $statusCode -eq 403
    }
}

$protectUpdate = Test-Step "Cannot update builtin post (Mach4)" {
    try {
        $update = @{ description = "Hacked!" } | ConvertTo-Json
        Invoke-RestMethod -Uri "$baseUrl/api/posts/Mach4" `
            -Method PUT `
            -Body $update `
            -ContentType "application/json"
        return $false  # Should not succeed
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "    Status code: $statusCode (expected: 403)" -ForegroundColor Gray
        return $statusCode -eq 403
    }
}

# Test 8: Reserved prefix validation
Write-Host "`n--- Step 8: ID Validation Rules ---" -ForegroundColor Cyan
$reservedPrefix = Test-Step "Cannot create post with reserved prefix (GRBL_CUSTOM)" {
    try {
        $badPost = @{
            id = "GRBL_CUSTOM"
            name = "Bad Post"
            header = @("G90")
            footer = @("M30")
        } | ConvertTo-Json
        Invoke-RestMethod -Uri "$baseUrl/api/posts/" `
            -Method POST `
            -Body $badPost `
            -ContentType "application/json"
        return $false  # Should not succeed
    } catch {
        $errorMsg = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "    Error: $($errorMsg.detail)" -ForegroundColor Gray
        return $errorMsg.detail -like "*reserved prefix*"
    }
}

# Test 9: Delete custom post (cleanup)
Write-Host "`n--- Step 9: Delete Custom Post ---" -ForegroundColor Cyan
$deleted = Test-Step "Delete test post: $testPostId" {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/$testPostId" -Method DELETE
    Write-Host "    Deleted: $($response.deleted)" -ForegroundColor Gray
    return $response.deleted -eq $true
}

# Verify deletion
$verifyDelete = Test-Step "Verify post is gone" {
    try {
        Invoke-RestMethod -Uri "$baseUrl/api/posts/$testPostId" -Method GET
        return $false  # Should not find it
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "    Status code: $statusCode (expected: 404)" -ForegroundColor Gray
        return $statusCode -eq 404
    }
}

# Test 10: Token expansion (manual verification)
Write-Host "`n--- Step 10: Token Expansion (Info) ---" -ForegroundColor Cyan
Write-Host "Available tokens for header/footer use:" -ForegroundColor Yellow
$tokenList = Invoke-RestMethod -Uri "$baseUrl/api/posts/tokens/list" -Method GET
$tokenList.PSObject.Properties | ForEach-Object {
    Write-Host "  {{$($_.Name)}}" -ForegroundColor Cyan -NoNewline
    Write-Host " - $($_.Value)" -ForegroundColor Gray
}

# Summary
Write-Host "`n=== Validation Summary ===" -ForegroundColor Cyan
Write-Host "Total Tests: $($passCount + $failCount)" -ForegroundColor White
Write-Host "Passed: $passCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })

if ($failCount -eq 0) {
    Write-Host "`n✅ All validation tests passed!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Open browser: http://localhost:5173/cam-dashboard" -ForegroundColor Gray
    Write-Host "2. Click 'Post Processors' card" -ForegroundColor Gray
    Write-Host "3. Test UI: Create, edit, delete custom posts" -ForegroundColor Gray
    Write-Host "4. Verify builtin posts show as read-only" -ForegroundColor Gray
    Write-Host "5. Check token helper in PostEditor modal" -ForegroundColor Gray
} else {
    Write-Host "`n❌ Some tests failed. Review output above." -ForegroundColor Red
}

Write-Host "`n=== End of Validation ===" -ForegroundColor Cyan
