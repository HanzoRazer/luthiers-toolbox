# Blueprint Import API Test Script - Phase 1
# Tests /blueprint/analyze and /blueprint/to-svg endpoints

Write-Host "=== Testing Blueprint Import API (Phase 1) ===" -ForegroundColor Cyan
Write-Host ""

$API_BASE = "http://localhost:8000"

# Check if server is running
Write-Host "1. Checking API health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$API_BASE/blueprint/health" -Method Get
    Write-Host "   ✓ Blueprint service status: $($health.status)" -ForegroundColor Green
    Write-Host "   ✓ Phase: $($health.phase)" -ForegroundColor Green
    Write-Host "   ✓ Features: $($health.features -join ', ')" -ForegroundColor Green
} catch {
    Write-Host "   ✗ API not responding. Start server with:" -ForegroundColor Red
    Write-Host "     cd services/api" -ForegroundColor Yellow
    Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "     pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "     `$env:EMERGENT_LLM_KEY = 'your-key-here'" -ForegroundColor Yellow
    Write-Host "     uvicorn app.main:app --reload --port 8000" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "2. Testing /blueprint/analyze endpoint..." -ForegroundColor Yellow

# Check for test blueprint
$testFile = "test_blueprint.pdf"
if (-not (Test-Path $testFile)) {
    Write-Host "   ⚠ No test blueprint found. Please provide a sample PDF/PNG blueprint." -ForegroundColor Yellow
    Write-Host "     Expected file: $testFile" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   You can:" -ForegroundColor Cyan
    Write-Host "   1. Place a blueprint PDF in the root directory as 'test_blueprint.pdf'" -ForegroundColor Cyan
    Write-Host "   2. Or manually test with:" -ForegroundColor Cyan
    Write-Host "      curl -X POST http://localhost:8000/api/blueprint/analyze \\" -ForegroundColor Yellow
    Write-Host "           -F 'file=@your-blueprint.pdf'" -ForegroundColor Yellow
    exit 0
}

try {
    $filePath = (Resolve-Path $testFile).Path
    
    # Create multipart form data
    Add-Type -AssemblyName System.Net.Http
    $httpClient = New-Object System.Net.Http.HttpClient
    $content = New-Object System.Net.Http.MultipartFormDataContent
    
    $fileStream = [System.IO.File]::OpenRead($filePath)
    $fileContent = New-Object System.Net.Http.StreamContent($fileStream)
    $content.Add($fileContent, "file", (Split-Path $filePath -Leaf))
    
    $response = $httpClient.PostAsync("$API_BASE/api/blueprint/analyze", $content).Result
    $result = $response.Content.ReadAsStringAsync().Result | ConvertFrom-Json
    
    $fileStream.Close()
    $httpClient.Dispose()
    
    if ($result.success) {
        Write-Host "   ✓ Analysis successful!" -ForegroundColor Green
        Write-Host "     Filename: $($result.filename)" -ForegroundColor Cyan
        Write-Host "     Scale: $($result.analysis.scale) (confidence: $($result.analysis.scale_confidence))" -ForegroundColor Cyan
        Write-Host "     Dimensions detected: $($result.analysis.dimensions.Count)" -ForegroundColor Cyan
        
        if ($result.analysis.blueprint_type) {
            Write-Host "     Type: $($result.analysis.blueprint_type)" -ForegroundColor Cyan
        }
        
        if ($result.analysis.detected_model) {
            Write-Host "     Model: $($result.analysis.detected_model)" -ForegroundColor Cyan
        }
        
        # Show first 5 dimensions
        if ($result.analysis.dimensions.Count -gt 0) {
            Write-Host ""
            Write-Host "   First 5 dimensions:" -ForegroundColor Yellow
            $result.analysis.dimensions | Select-Object -First 5 | ForEach-Object {
                Write-Host "     - $($_.label): $($_.value) ($($_.type), $($_.confidence))" -ForegroundColor Gray
            }
        }
        
        # Save analysis for SVG export test
        $global:savedAnalysis = $result.analysis
    } else {
        Write-Host "   ✗ Analysis failed: $($result.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "3. Testing /blueprint/to-svg endpoint..." -ForegroundColor Yellow

if ($global:savedAnalysis) {
    try {
        $svgRequest = @{
            analysis_data = $global:savedAnalysis
            format = "svg"
            scale_correction = 1.0
            width_mm = 300
            height_mm = 200
        } | ConvertTo-Json -Depth 10
        
        $svgResponse = Invoke-RestMethod -Uri "$API_BASE/api/blueprint/to-svg" `
                                         -Method Post `
                                         -ContentType "application/json" `
                                         -Body $svgRequest `
                                         -OutFile "test_output.svg"
        
        if (Test-Path "test_output.svg") {
            $svgSize = (Get-Item "test_output.svg").Length
            Write-Host "   ✓ SVG export successful!" -ForegroundColor Green
            Write-Host "     Output: test_output.svg ($svgSize bytes)" -ForegroundColor Cyan
            Write-Host "     Open in browser to view" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "   ✗ SVG export failed: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   ⚠ Skipped (no analysis data)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "4. Testing /blueprint/to-dxf endpoint (should return 501)..." -ForegroundColor Yellow

try {
    $dxfRequest = @{
        analysis_data = @{}
        format = "dxf"
    } | ConvertTo-Json
    
    Invoke-RestMethod -Uri "$API_BASE/api/blueprint/to-dxf" `
                      -Method Post `
                      -ContentType "application/json" `
                      -Body $dxfRequest
    
    Write-Host "   ✗ Expected 501 status but request succeeded" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 501) {
        Write-Host "   ✓ Correctly returns 501 (Not Implemented - Phase 2)" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Unexpected error: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Phase 1 API Tests Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test with real blueprint PDFs from your guitar design library" -ForegroundColor Gray
Write-Host "  2. Verify SVG output quality and dimension accuracy" -ForegroundColor Gray
Write-Host "  3. Proceed to Phase 2: OpenCV vectorization + DXF export" -ForegroundColor Gray
