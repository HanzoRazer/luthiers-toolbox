#!/usr/bin/env pwsh
# Test script for Adaptive Feed Override system
# Tests all 3 override modes (comment, inline_f, mcode) plus inherit

Write-Host "=== Testing Adaptive Feed Override System ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$endpoint = "$baseUrl/api/cam/pocket/adaptive/gcode"

# Base request body (simple rectangular pocket)
$baseBody = @{
    loops = @(
        @{ pts = @(@(0,0), @(60,0), @(60,40), @(0,40)) }
    )
    units = "mm"
    tool_d = 6.0
    stepover = 0.45
    stepdown = 1.5
    margin = 0.5
    strategy = "Spiral"
    climb = $true
    feed_xy = 1200
    safe_z = 5
    z_rough = -1.5
    post_id = "GRBL"
    use_trochoids = $false
    jerk_aware = $false
}

# Test 1: Inherit mode (no override)
Write-Host "1. Testing mode: inherit (no override)" -ForegroundColor Yellow
$body1 = $baseBody.Clone()
$body1.adaptive_feed_override = @{ mode = "inherit" }
$json1 = $body1 | ConvertTo-Json -Depth 10

try {
    $response1 = Invoke-WebRequest -Uri $endpoint -Method POST `
        -ContentType "application/json" -Body $json1
    $gcode1 = $response1.Content
    
    Write-Host "  ✓ Request successful" -ForegroundColor Green
    Write-Host "  Length: $($gcode1.Length) bytes" -ForegroundColor Gray
    
    # GRBL default is inline_f, should have scaled F values
    if ($gcode1 -match " F[5-9]\d{2}") {
        Write-Host "  ✓ Inherit mode: using post profile defaults (inline_f)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Warning: Expected inline_f default for GRBL" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Comment mode override
Write-Host "2. Testing mode: comment" -ForegroundColor Yellow
$body2 = $baseBody.Clone()
$body2.adaptive_feed_override = @{ mode = "comment" }
$json2 = $body2 | ConvertTo-Json -Depth 10

try {
    $response2 = Invoke-WebRequest -Uri $endpoint -Method POST `
        -ContentType "application/json" -Body $json2
    $gcode2 = $response2.Content
    
    Write-Host "  ✓ Request successful" -ForegroundColor Green
    
    if ($gcode2 -match "\(FEED_HINT START") {
        Write-Host "  ✓ FEED_HINT START marker found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ FEED_HINT START marker NOT found" -ForegroundColor Red
    }
    
    if ($gcode2 -match "\(FEED_HINT END\)") {
        Write-Host "  ✓ FEED_HINT END marker found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ FEED_HINT END marker NOT found" -ForegroundColor Red
    }
    
    # Save for inspection
    $gcode2 | Out-File -FilePath "test_comment_mode.nc" -Encoding utf8
    Write-Host "  Saved to: test_comment_mode.nc" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: Inline_f mode with custom min feed
Write-Host "3. Testing mode: inline_f (min_f=500)" -ForegroundColor Yellow
$body3 = $baseBody.Clone()
$body3.adaptive_feed_override = @{ 
    mode = "inline_f"
    inline_min_f = 500.0
}
$json3 = $body3 | ConvertTo-Json -Depth 10

try {
    $response3 = Invoke-WebRequest -Uri $endpoint -Method POST `
        -ContentType "application/json" -Body $json3
    $gcode3 = $response3.Content
    
    Write-Host "  ✓ Request successful" -ForegroundColor Green
    
    # Should have scaled F values (not comments)
    if ($gcode3 -match " F[5-9]\d{2}") {
        Write-Host "  ✓ Scaled F values found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Scaled F values NOT found" -ForegroundColor Red
    }
    
    if ($gcode3 -notmatch "\(FEED_HINT") {
        Write-Host "  ✓ No FEED_HINT comments (as expected)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ FEED_HINT comments found (unexpected)" -ForegroundColor Yellow
    }
    
    # Save for inspection
    $gcode3 | Out-File -FilePath "test_inline_f_mode.nc" -Encoding utf8
    Write-Host "  Saved to: test_inline_f_mode.nc" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: M-code mode with custom M-codes
Write-Host "4. Testing mode: mcode (M100 P)" -ForegroundColor Yellow
$body4 = $baseBody.Clone()
$body4.adaptive_feed_override = @{ 
    mode = "mcode"
    mcode_start = "M100 P"
    mcode_end = "M100 P0"
}
$json4 = $body4 | ConvertTo-Json -Depth 10

try {
    $response4 = Invoke-WebRequest -Uri $endpoint -Method POST `
        -ContentType "application/json" -Body $json4
    $gcode4 = $response4.Content
    
    Write-Host "  ✓ Request successful" -ForegroundColor Green
    
    if ($gcode4 -match "M100 P[1-9]") {
        Write-Host "  ✓ Custom M-code start (M100 P) found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Custom M-code start NOT found" -ForegroundColor Red
    }
    
    if ($gcode4 -match "M100 P0") {
        Write-Host "  ✓ Custom M-code end (M100 P0) found" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Custom M-code end NOT found" -ForegroundColor Red
    }
    
    # Save for inspection
    $gcode4 | Out-File -FilePath "test_mcode_mode.nc" -Encoding utf8
    Write-Host "  Saved to: test_mcode_mode.nc" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: Different post processors with overrides
Write-Host "5. Testing override with different posts" -ForegroundColor Yellow

$posts = @("GRBL", "Mach4", "LinuxCNC")
foreach ($post in $posts) {
    Write-Host "  Testing $post with comment override..." -ForegroundColor Cyan
    
    $body5 = $baseBody.Clone()
    $body5.post_id = $post
    $body5.adaptive_feed_override = @{ mode = "comment" }
    $json5 = $body5 | ConvertTo-Json -Depth 10
    
    try {
        $response5 = Invoke-WebRequest -Uri $endpoint -Method POST `
            -ContentType "application/json" -Body $json5
        $gcode5 = $response5.Content
        
        if ($gcode5 -match "\(POST=$post") {
            Write-Host "    ✓ $post metadata found" -ForegroundColor Green
        }
        
        if ($gcode5 -match "\(FEED_HINT START") {
            Write-Host "    ✓ Comment override applied to $post" -ForegroundColor Green
        } else {
            Write-Host "    ✗ Comment override NOT applied to $post" -ForegroundColor Red
        }
    } catch {
        Write-Host "    ✗ $post request failed: $_" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "=== All Tests Completed ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated files:" -ForegroundColor Gray
Write-Host "  - test_comment_mode.nc" -ForegroundColor Gray
Write-Host "  - test_inline_f_mode.nc" -ForegroundColor Gray
Write-Host "  - test_mcode_mode.nc" -ForegroundColor Gray
Write-Host ""
Write-Host "Inspect these files to verify FEED_HINT translation" -ForegroundColor Gray
