# Test Post-Processor Chooser System
# Run this after starting the API server to verify all endpoints work

Write-Host "`n=== Testing Post-Processor Endpoints ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"

# Test 1: List all post-processors
Write-Host "`n1. Testing GET /api/tooling/posts" -ForegroundColor Yellow
try {
    $posts = Invoke-RestMethod -Uri "$baseUrl/tooling/posts" -Method Get
    Write-Host "✓ Found $($posts.Count) post-processors:" -ForegroundColor Green
    $posts | ForEach-Object {
        Write-Host "  - $($_.id): $($_.title) (header: $($_.header.Count) lines, footer: $($_.footer.Count) lines)"
    }
} catch {
    Write-Host "✗ Failed to list posts: $_" -ForegroundColor Red
}

# Test 2: Get individual post-processor
Write-Host "`n2. Testing GET /api/tooling/posts/grbl" -ForegroundColor Yellow
try {
    $grbl = Invoke-RestMethod -Uri "$baseUrl/tooling/posts/grbl" -Method Get
    Write-Host "✓ GRBL config:" -ForegroundColor Green
    Write-Host "  ID: $($grbl.id)"
    Write-Host "  Title: $($grbl.title)"
    Write-Host "  Header: $($grbl.header -join ', ')"
    Write-Host "  Footer: $($grbl.footer -join ', ')"
} catch {
    Write-Host "✗ Failed to get GRBL config: $_" -ForegroundColor Red
}

# Test 3: Export G-code with post-processor
Write-Host "`n3. Testing POST /api/geometry/export_gcode" -ForegroundColor Yellow
try {
    $body = @{
        gcode = "G90`nG0 X10 Y10`nM30"
        units = "mm"
        post_id = "grbl"
    } | ConvertTo-Json

    $result = Invoke-WebRequest -Uri "$baseUrl/geometry/export_gcode" -Method Post -Body $body -ContentType "application/json"
    $nc = $result.Content
    Write-Host "✓ Generated G-code (first 5 lines):" -ForegroundColor Green
    ($nc -split "`n")[0..4] | ForEach-Object { Write-Host "  $_" }
} catch {
    Write-Host "✗ Failed to export G-code: $_" -ForegroundColor Red
}

# Test 4: Multi-post bundle export
Write-Host "`n4. Testing POST /api/geometry/export_bundle_multi" -ForegroundColor Yellow
try {
    $body = @{
        geometry = @{
            units = "mm"
            paths = @(
                @{ type = "line"; x1 = 0; y1 = 0; x2 = 60; y2 = 0 }
            )
        }
        gcode = "G90`nG1 X60 Y0 F1200`nM30"
        post_ids = @("grbl", "mach4", "linuxcnc")
        target_units = "mm"
    } | ConvertTo-Json -Depth 10

    $result = Invoke-WebRequest -Uri "$baseUrl/geometry/export_bundle_multi" -Method Post -Body $body -ContentType "application/json" -OutFile "test_multi_bundle.zip"
    
    if (Test-Path "test_multi_bundle.zip") {
        Write-Host "✓ Multi-post bundle created: test_multi_bundle.zip" -ForegroundColor Green
        
        # List contents
        Add-Type -Assembly System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path "test_multi_bundle.zip"))
        Write-Host "  Contents:" -ForegroundColor Cyan
        $zip.Entries | ForEach-Object { Write-Host "    - $($_.FullName)" }
        $zip.Dispose()
        
        Remove-Item "test_multi_bundle.zip" -Force
    }
} catch {
    Write-Host "✗ Failed to create multi-post bundle: $_" -ForegroundColor Red
}

Write-Host "`n=== All Tests Complete ===" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start the client: cd packages/client && npm run dev"
Write-Host "  2. Open http://localhost:5173 in browser"
Write-Host "  3. Test the PostChooser component (checkboxes should persist in localStorage)"
Write-Host "  4. Click 'Preview' on any post to see the PostPreviewDrawer"
Write-Host "  5. Export multi-post bundle using selected posts`n"
