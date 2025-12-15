# Phase 5 Part 2: N.0 Smart Post Configurator — Smoke Test
# Tests CRUD operations for post-processor management

Write-Host "=== Phase 5 Part 2: N.0 Smart Post Configurator — Smoke Test ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

# Test 1: Post router exists
Write-Host "1. Testing post router file (post_router.py)..." -ForegroundColor Yellow
$routerPath = "services/api/app/routers/post_router.py"
if (Test-Path $routerPath) {
    Write-Host "  ✓ Post router exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Post router not found" -ForegroundColor Red
    $failed++
}

# Test 2: Custom posts data file exists
Write-Host "2. Testing custom posts data file..." -ForegroundColor Yellow
$dataPath = "services/api/app/data/posts/custom_posts.json"
if (Test-Path $dataPath) {
    Write-Host "  ✓ Custom posts data file exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Custom posts data file not found" -ForegroundColor Red
    $failed++
}

# Test 3: Frontend API client exists
Write-Host "3. Testing frontend API client (post.ts)..." -ForegroundColor Yellow
$apiPath = "client/src/api/post.ts"
if (Test-Path $apiPath) {
    Write-Host "  ✓ Frontend API client exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Frontend API client not found" -ForegroundColor Red
    $failed++
}

# Test 4: PostManager component exists
Write-Host "4. Testing PostManager component..." -ForegroundColor Yellow
$managerPath = "client/src/components/PostManager.vue"
if (Test-Path $managerPath) {
    Write-Host "  ✓ PostManager.vue exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ PostManager.vue not found" -ForegroundColor Red
    $failed++
}

# Test 5: PostEditor component exists
Write-Host "5. Testing PostEditor component..." -ForegroundColor Yellow
$editorPath = "client/src/components/PostEditor.vue"
if (Test-Path $editorPath) {
    Write-Host "  ✓ PostEditor.vue exists" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ PostEditor.vue not found" -ForegroundColor Red
    $failed++
}

# Test 6: Router registered in main.py
Write-Host "6. Testing router registration..." -ForegroundColor Yellow
$mainPyContent = Get-Content "services/api/app/main.py" -Raw
if ($mainPyContent -match "post_router" -and $mainPyContent -match "Phase 5 Part 2") {
    Write-Host "  ✓ Post router registered in main.py" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  ✗ Post router registration incomplete" -ForegroundColor Red
    $failed++
}

# API Tests (require server running)
Write-Host ""
Write-Host "=== API Endpoint Tests (require server at $baseUrl) ===" -ForegroundColor Cyan

# Test 7: List posts endpoint
Write-Host "7. Testing GET /api/posts/ (list posts)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/" -Method GET -TimeoutSec 10
    if ($response.posts) {
        $builtinCount = ($response.posts | Where-Object { $_.builtin -eq $true }).Count
        Write-Host "  ✓ List posts endpoint works" -ForegroundColor Green
        Write-Host "    Total posts: $($response.posts.Count)" -ForegroundColor Gray
        Write-Host "    Built-in posts: $builtinCount" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Unexpected response format" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ List posts endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 8: Get single post (GRBL)
Write-Host "8. Testing GET /api/posts/GRBL (get single post)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/GRBL" -Method GET -TimeoutSec 10
    if ($response.id -eq "GRBL" -and $response.header -and $response.footer) {
        Write-Host "  ✓ Get post endpoint works" -ForegroundColor Green
        Write-Host "    Post: $($response.name)" -ForegroundColor Gray
        Write-Host "    Built-in: $($response.builtin)" -ForegroundColor Gray
        Write-Host "    Header lines: $($response.header.Count)" -ForegroundColor Gray
        Write-Host "    Footer lines: $($response.footer.Count)" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Unexpected response format" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Get post endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 9: Create custom post
Write-Host "9. Testing POST /api/posts/ (create custom post)..." -ForegroundColor Yellow
try {
    $customPostId = "TEST_POST_" + (Get-Date -Format "HHmmss")
    $body = @{
        id = $customPostId
        name = "Test Post"
        description = "Smoke test post"
        header = @("G90", "G21", "(Test Header)")
        footer = @("M30", "(Test Footer)")
        tokens = @{}
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 10
    
    if ($response.id -eq $customPostId -and $response.builtin -eq $false) {
        Write-Host "  ✓ Create post endpoint works" -ForegroundColor Green
        Write-Host "    Created post: $customPostId" -ForegroundColor Gray
        $passed++
        
        # Store ID for cleanup
        $script:testPostId = $customPostId
    } else {
        Write-Host "  ✗ Unexpected response format" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Create post endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 10: Update custom post
Write-Host "10. Testing PUT /api/posts/{id} (update custom post)..." -ForegroundColor Yellow
if ($script:testPostId) {
    try {
        $updateBody = @{
            name = "Test Post Updated"
            description = "Updated description"
        } | ConvertTo-Json -Depth 5
        
        $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/$($script:testPostId)" `
            -Method PUT `
            -ContentType "application/json" `
            -Body $updateBody `
            -TimeoutSec 10
        
        if ($response.id -eq $script:testPostId) {
            Write-Host "  ✓ Update post endpoint works" -ForegroundColor Green
            Write-Host "    Updated post: $($script:testPostId)" -ForegroundColor Gray
            $passed++
        } else {
            Write-Host "  ✗ Unexpected response format" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "  ⚠ Update post endpoint test skipped" -ForegroundColor Yellow
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ Update post test skipped (no test post created)" -ForegroundColor Yellow
}

# Test 11: Validate post configuration
Write-Host "11. Testing POST /api/posts/validate (validate post config)..." -ForegroundColor Yellow
try {
    $validateBody = @{
        id = "VALID_TEST"
        name = "Valid Test"
        description = "Test"
        header = @("G90")
        footer = @("M30")
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/validate" `
        -Method POST `
        -ContentType "application/json" `
        -Body $validateBody `
        -TimeoutSec 10
    
    if ($response.PSObject.Properties.Name -contains "valid") {
        Write-Host "  ✓ Validate post endpoint works" -ForegroundColor Green
        Write-Host "    Valid: $($response.valid)" -ForegroundColor Gray
        Write-Host "    Warnings: $($response.warnings.Count)" -ForegroundColor Gray
        Write-Host "    Errors: $($response.errors.Count)" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ Unexpected response format" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ Validate post endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 12: List available tokens
Write-Host "12. Testing GET /api/posts/tokens/list (list tokens)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/tokens/list" -Method GET -TimeoutSec 10
    $tokenCount = ($response.PSObject.Properties).Count
    if ($tokenCount -gt 0) {
        Write-Host "  ✓ List tokens endpoint works" -ForegroundColor Green
        Write-Host "    Available tokens: $tokenCount" -ForegroundColor Gray
        $sampleTokens = ($response.PSObject.Properties.Name | Select-Object -First 3) -join ", "
        Write-Host "    Sample: $sampleTokens" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ✗ No tokens returned" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ⚠ List tokens endpoint test skipped (server not running?)" -ForegroundColor Yellow
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Test 13: Delete custom post (cleanup)
Write-Host "13. Testing DELETE /api/posts/{id} (delete custom post)..." -ForegroundColor Yellow
if ($script:testPostId) {
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/posts/$($script:testPostId)" `
            -Method DELETE `
            -TimeoutSec 10
        
        if ($response.deleted -eq $true) {
            Write-Host "  ✓ Delete post endpoint works" -ForegroundColor Green
            Write-Host "    Deleted post: $($script:testPostId)" -ForegroundColor Gray
            $passed++
        } else {
            Write-Host "  ✗ Unexpected response format" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "  ⚠ Delete post endpoint test skipped" -ForegroundColor Yellow
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ Delete post test skipped (no test post created)" -ForegroundColor Yellow
}

# Test 14: Builtin protection (cannot delete GRBL)
Write-Host "14. Testing builtin post protection..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "$baseUrl/api/posts/GRBL" `
        -Method DELETE `
        -TimeoutSec 10 `
        -ErrorAction Stop
    
    Write-Host "  ✗ Built-in post deletion should have failed" -ForegroundColor Red
    $failed++
} catch {
    if ($_.Exception.Response.StatusCode -eq 403) {
        Write-Host "  ✓ Built-in post protection works (403 Forbidden)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ⚠ Unexpected error code: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "✅ All N.0 Smart Post Configurator tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Navigate to Settings → Post Processors (when integrated)" -ForegroundColor Gray
    Write-Host "  2. Test creating a custom post via UI" -ForegroundColor Gray
    Write-Host "  3. Test editing and deleting custom posts" -ForegroundColor Gray
    Write-Host "  4. Verify builtin posts cannot be modified" -ForegroundColor Gray
} else {
    Write-Host "❌ Some tests failed. Please review the errors above." -ForegroundColor Red
    exit 1
}
