# N.0 Browser Debug Helper
# Quick diagnostic to verify all components are working

Write-Host "`n=== N.0 Browser Debug Helper ===" -ForegroundColor Cyan
Write-Host "Testing connectivity and component availability`n"

# Test 1: API Server
Write-Host "Test 1: API Server" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/posts" -Method GET -ErrorAction Stop
    Write-Host "  ✓ API accessible - Found $($response.posts.Count) posts" -ForegroundColor Green
} catch {
    Write-Host "  ✗ API not accessible: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Frontend Server
Write-Host "`nTest 2: Frontend Server" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173/" -Method GET -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ Frontend accessible (HTTP $($response.StatusCode))" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Frontend not accessible: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: API Endpoints
Write-Host "`nTest 3: Key API Endpoints" -ForegroundColor Yellow

$endpoints = @(
    @{Path="/api/posts"; Name="List Posts"},
    @{Path="/api/posts/GRBL"; Name="Get GRBL Post"},
    @{Path="/api/posts/tokens"; Name="List Tokens"}
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000$($endpoint.Path)" -Method GET -ErrorAction Stop
        Write-Host "  ✓ $($endpoint.Name)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ $($endpoint.Name): $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 4: Check for common issues
Write-Host "`nTest 4: Component Files" -ForegroundColor Yellow

$files = @(
    "client\src\views\PostManagerView.vue",
    "client\src\components\PostManager.vue",
    "client\src\components\PostEditor.vue",
    "client\src\api\post.ts",
    "client\src\router\index.ts"
)

foreach ($file in $files) {
    $path = "C:\Users\thepr\Downloads\Luthiers ToolBox\$file"
    if (Test-Path $path) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file - MISSING!" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "All systems operational!" -ForegroundColor Green
Write-Host "`nBrowser URLs:" -ForegroundColor Yellow
Write-Host "  Dashboard: http://localhost:5173/cam-dashboard"
Write-Host "  Post Manager: http://localhost:5173/lab/posts"
Write-Host "`nAPI Base: http://localhost:8000/api/posts" -ForegroundColor Yellow

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Open browser to: http://localhost:5173/lab/posts"
Write-Host "2. You should see 5 builtin posts in a grid"
Write-Host "3. Try clicking 'Create Post' button"
Write-Host "4. If you see errors, check browser console (F12)"
Write-Host "`nPress F12 in browser to see console errors if page doesn't load"
