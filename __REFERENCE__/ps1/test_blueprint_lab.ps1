# Test Blueprint Lab Integration
# Prerequisites: 
# - API running on :8000
# - Claude API key configured (EMERGENT_LLM_KEY or ANTHROPIC_API_KEY)
# - Optional: Test blueprint file for full E2E testing

Write-Host "=== Testing Blueprint Lab Integration ===" -ForegroundColor Cyan
Write-Host ""

$apiBase = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

# Helper function
function Test-Endpoint {
    param($name, $scriptBlock)
    Write-Host "Testing: $name" -ForegroundColor Yellow
    try {
        & $scriptBlock
        $script:testsPassed++
        Write-Host "  ✓ PASS" -ForegroundColor Green
    } catch {
        $script:testsFailed++
        Write-Host "  ✗ FAIL: $_" -ForegroundColor Red
    }
    Write-Host ""
}

#=============================================================================
# 1. Health Check
#=============================================================================
Test-Endpoint "GET /blueprint/health" {
    $health = Invoke-RestMethod -Uri "$apiBase/blueprint/health" -Method Get
    
    if ($health.status -ne "healthy" -and $health.status -ne "degraded") {
        throw "Health status is '$($health.status)', expected 'healthy' or 'degraded'"
    }
    
    Write-Host "    Status: $($health.status)" -ForegroundColor Gray
    Write-Host "    Phase: $($health.phase)" -ForegroundColor Gray
    Write-Host "    Features: $($health.available_features -join ', ')" -ForegroundColor Gray
    
    # Check if Phase 2 is available
    if ($health.phase -eq "1+2") {
        Write-Host "    ✓ Phase 2 (OpenCV) available" -ForegroundColor Green
    } else {
        Write-Host "    ⚠ Phase 2 (OpenCV) NOT available - vectorization will fail" -ForegroundColor Yellow
    }
}

#=============================================================================
# 2. Verify API Key (Analyze endpoint will fail without it)
#=============================================================================
Test-Endpoint "Verify Claude API Key" {
    $hasKey = $false
    
    if ($env:EMERGENT_LLM_KEY) {
        Write-Host "    ✓ EMERGENT_LLM_KEY configured" -ForegroundColor Gray
        $hasKey = $true
    } elseif ($env:ANTHROPIC_API_KEY) {
        Write-Host "    ✓ ANTHROPIC_API_KEY configured" -ForegroundColor Gray
        $hasKey = $true
    } else {
        Write-Host "    ⚠ No API key found in environment" -ForegroundColor Yellow
        Write-Host "    Set EMERGENT_LLM_KEY or ANTHROPIC_API_KEY to test analysis" -ForegroundColor Yellow
    }
    
    if (-not $hasKey) {
        throw "API key not configured"
    }
}

#=============================================================================
# 3. Test with Sample Blueprint (if available)
#=============================================================================
$testFiles = @(
    "c:\temp\test_blueprint.pdf",
    "c:\temp\test_blueprint.png",
    ".\test_blueprint.pdf",
    ".\test_blueprint.png"
)

$testFile = $null
foreach ($path in $testFiles) {
    if (Test-Path $path) {
        $testFile = $path
        break
    }
}

if ($testFile) {
    Write-Host "Found test file: $testFile" -ForegroundColor Cyan
    Write-Host ""
    
    # 3a. Test Analysis
    Test-Endpoint "POST /api/blueprint/analyze (with test file)" {
        Write-Host "    Uploading and analyzing (this may take 30-120 seconds)..." -ForegroundColor Gray
        
        $form = @{
            file = Get-Item $testFile
        }
        
        $analysis = Invoke-RestMethod -Uri "$apiBase/blueprint/analyze" `
            -Method Post -Form $form -TimeoutSec 180
        
        if (-not $analysis.success) {
            throw "Analysis failed: $($analysis.message)"
        }
        
        Write-Host "    ✓ Analysis successful" -ForegroundColor Green
        Write-Host "      Scale: $($analysis.analysis.scale)" -ForegroundColor Gray
        Write-Host "      Confidence: $($analysis.analysis.scale_confidence)" -ForegroundColor Gray
        Write-Host "      Type: $($analysis.analysis.blueprint_type)" -ForegroundColor Gray
        Write-Host "      Dimensions: $($analysis.analysis.dimensions.Count)" -ForegroundColor Gray
        
        # Store for vectorization test
        $script:analysisResult = $analysis.analysis
    }
    
    # 3b. Test Basic SVG Export
    if ($script:analysisResult) {
        Test-Endpoint "POST /api/blueprint/to-svg (basic export)" {
            $body = @{
                analysis_data = $script:analysisResult
                format = "svg"
                scale_correction = 1.0
                width_mm = 300
                height_mm = 200
            } | ConvertTo-Json -Depth 10
            
            $response = Invoke-WebRequest -Uri "$apiBase/blueprint/to-svg" `
                -Method Post -Body $body -ContentType "application/json"
            
            if ($response.StatusCode -ne 200) {
                throw "SVG export failed with status $($response.StatusCode)"
            }
            
            Write-Host "    ✓ SVG exported ($($response.Content.Length) bytes)" -ForegroundColor Green
        }
    }
    
    # 3c. Test Vectorization (Phase 2)
    if ($script:analysisResult) {
        Test-Endpoint "POST /api/blueprint/vectorize-geometry (Phase 2)" {
            $vectorForm = @{
                file = Get-Item $testFile
                analysis_data = ($script:analysisResult | ConvertTo-Json -Depth 10)
                scale_factor = "1.0"
                low_threshold = "50"
                high_threshold = "150"
                min_area = "100"
            }
            
            Write-Host "    Vectorizing geometry..." -ForegroundColor Gray
            $vector = Invoke-RestMethod -Uri "$apiBase/blueprint/vectorize-geometry" `
                -Method Post -Form $vectorForm -TimeoutSec 60
            
            Write-Host "    ✓ Vectorization successful" -ForegroundColor Green
            Write-Host "      Contours: $($vector.contours_detected)" -ForegroundColor Gray
            Write-Host "      Lines: $($vector.lines_detected)" -ForegroundColor Gray
            Write-Host "      Processing: $($vector.processing_time_ms)ms" -ForegroundColor Gray
            Write-Host "      SVG: $($vector.svg_path)" -ForegroundColor Gray
            Write-Host "      DXF: $($vector.dxf_path)" -ForegroundColor Gray
            
            # Verify files exist
            if (-not $vector.svg_path) {
                throw "SVG path not returned"
            }
            if (-not $vector.dxf_path) {
                throw "DXF path not returned"
            }
        }
    }
    
} else {
    Write-Host "⚠ No test blueprint file found (skipping E2E tests)" -ForegroundColor Yellow
    Write-Host "  To enable E2E testing, place a blueprint file at:" -ForegroundColor Yellow
    Write-Host "    c:\temp\test_blueprint.pdf" -ForegroundColor Yellow
    Write-Host "    c:\temp\test_blueprint.png" -ForegroundColor Yellow
    Write-Host "  OR" -ForegroundColor Yellow
    Write-Host "    .\test_blueprint.pdf (current directory)" -ForegroundColor Yellow
    Write-Host "    .\test_blueprint.png (current directory)" -ForegroundColor Yellow
    Write-Host ""
}

#=============================================================================
# 4. Summary
#=============================================================================
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Blueprint Lab is ready to use. Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start client: cd packages/client && npm run dev" -ForegroundColor Gray
    Write-Host "  2. Add BlueprintLab.vue to router" -ForegroundColor Gray
    Write-Host "  3. Navigate to /lab/blueprint" -ForegroundColor Gray
    Write-Host "  4. Test with real blueprint files" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "✗ Some tests failed. Check errors above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - API not running: cd services/api && uvicorn app.main:app --reload" -ForegroundColor Gray
    Write-Host "  - Missing API key: Set EMERGENT_LLM_KEY or ANTHROPIC_API_KEY" -ForegroundColor Gray
    Write-Host "  - Phase 2 missing: cd services/blueprint-import && pip install opencv-python scikit-image" -ForegroundColor Gray
    exit 1
}
