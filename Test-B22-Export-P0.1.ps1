# Test-B22-Export-P0.1.ps1
# Quick smoke test for B22.12 Diff Report Export (P0.1)

Write-Host "`n=== P0.1: B22.12 Diff Report Export Test ===" -ForegroundColor Cyan
Write-Host "Testing: Backend router + Frontend export button`n" -ForegroundColor Gray

$apiBase = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

# Test 1: Backend endpoint exists
Write-Host "1. Testing POST /export/diff-report endpoint..." -ForegroundColor Yellow
try {
    # Create a test payload with base64-encoded 1x1 PNG
    $testPng = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    $payload = @{
        mode = "overlay"
        layers = @("base", "current")
        screenshotBefore = $testPng
        screenshotAfter = $testPng
        screenshotDiff = $testPng
        beforeLabel = "test-before"
        afterLabel = "test-after"
        diffLabel = "test-diff"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$apiBase/export/diff-report" `
        -Method POST `
        -ContentType "application/json" `
        -Body $payload `
        -UseBasicParsing

    if ($response.StatusCode -eq 200) {
        Write-Host "   ✓ Endpoint responded with 200 OK" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "   ✗ Unexpected status: $($response.StatusCode)" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "   ✗ Request failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 2: Response is a ZIP file
Write-Host "`n2. Testing response content type..." -ForegroundColor Yellow
try {
    $contentType = $response.Headers['Content-Type']
    if ($contentType -eq 'application/zip') {
        Write-Host "   ✓ Content-Type is application/zip" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "   ✗ Wrong Content-Type: $contentType" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "   ✗ Could not verify Content-Type" -ForegroundColor Red
    $testsFailed++
}

# Test 3: Response has Content-Disposition header
Write-Host "`n3. Testing Content-Disposition header..." -ForegroundColor Yellow
try {
    $disposition = $response.Headers['Content-Disposition']
    if ($disposition -like '*attachment*' -and $disposition -like '*diff-report*.zip*') {
        Write-Host "   ✓ Content-Disposition header correct: $disposition" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "   ✗ Wrong Content-Disposition: $disposition" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "   ✗ Content-Disposition header missing" -ForegroundColor Red
    $testsFailed++
}

# Test 4: Save and inspect ZIP contents
Write-Host "`n4. Testing ZIP file contents..." -ForegroundColor Yellow
try {
    $tempZip = Join-Path $env:TEMP "diff-report-test.zip"
    [System.IO.File]::WriteAllBytes($tempZip, $response.Content)
    
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($tempZip)
    
    $expectedFiles = @('test-before.png', 'test-after.png', 'test-diff.png', 'metadata.json')
    $actualFiles = $zip.Entries | ForEach-Object { $_.Name }
    
    $allFound = $true
    foreach ($file in $expectedFiles) {
        if ($actualFiles -contains $file) {
            Write-Host "   ✓ Found: $file" -ForegroundColor Green
        } else {
            Write-Host "   ✗ Missing: $file" -ForegroundColor Red
            $allFound = $false
        }
    }
    
    $zip.Dispose()
    Remove-Item $tempZip -Force
    
    if ($allFound) {
        $testsPassed++
    } else {
        $testsFailed++
    }
} catch {
    Write-Host "   ✗ Failed to inspect ZIP: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 5: Check metadata.json structure
Write-Host "`n5. Testing metadata.json structure..." -ForegroundColor Yellow
try {
    $tempZip = Join-Path $env:TEMP "diff-report-test.zip"
    [System.IO.File]::WriteAllBytes($tempZip, $response.Content)
    
    $zip = [System.IO.Compression.ZipFile]::OpenRead($tempZip)
    $metadataEntry = $zip.Entries | Where-Object { $_.Name -eq 'metadata.json' }
    
    if ($metadataEntry) {
        $stream = $metadataEntry.Open()
        $reader = New-Object System.IO.StreamReader($stream)
        $metadataJson = $reader.ReadToEnd()
        $reader.Close()
        $stream.Close()
        
        $metadata = $metadataJson | ConvertFrom-Json
        
        $requiredFields = @('mode', 'layers', 'beforeLabel', 'afterLabel', 'diffLabel', 'exportedAt')
        $allFieldsPresent = $true
        
        foreach ($field in $requiredFields) {
            if ($metadata.PSObject.Properties.Name -contains $field) {
                Write-Host "   ✓ Field present: $field" -ForegroundColor Green
            } else {
                Write-Host "   ✗ Field missing: $field" -ForegroundColor Red
                $allFieldsPresent = $false
            }
        }
        
        if ($allFieldsPresent) {
            $testsPassed++
        } else {
            $testsFailed++
        }
    } else {
        Write-Host "   ✗ metadata.json not found" -ForegroundColor Red
        $testsFailed++
    }
    
    $zip.Dispose()
    Remove-Item $tempZip -Force
} catch {
    Write-Host "   ✗ Failed to parse metadata: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor Red

if ($testsFailed -eq 0) {
    Write-Host "`n✅ P0.1 Backend Implementation: COMPLETE" -ForegroundColor Green
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "  1. Start client dev server: cd packages\client; npm run dev" -ForegroundColor Gray
    Write-Host "  2. Navigate to Compare Lab" -ForegroundColor Gray
    Write-Host "  3. Load geometry and create diff" -ForegroundColor Gray
    Write-Host "  4. Click '📦 Export Diff Report' button" -ForegroundColor Gray
    Write-Host "  5. Verify ZIP download with 3 PNGs + metadata.json`n" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "`n❌ P0.1 Tests Failed - Check errors above`n" -ForegroundColor Red
    exit 1
}
