# ============================================================================
# TEST SCRIPT: Phase 5 Part 3 - N.12 Tool Tables CRUD Validation
# ============================================================================
# Purpose: Validate existing Tool Tables API implementation (Patch N.12)
# Expected: All tests pass (N.12 already complete, needs validation)
# Endpoints: GET/PUT/DELETE /api/machines/tools/{mid}, GET/POST .csv
# ============================================================================

$baseUrl = "http://localhost:8000"
$api = "$baseUrl/machines/tools"

$totalTests = 0
$passedTests = 0

function Test-Assert {
    param($condition, $testName)
    $script:totalTests++
    if ($condition) {
        Write-Host "  ✓ $testName" -ForegroundColor Green
        $script:passedTests++
    } else {
        Write-Host "  ✗ $testName" -ForegroundColor Red
    }
}

Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       PHASE 5 PART 3 - N.12 TOOL TABLES VALIDATION          ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# SETUP: Create test machine
# ============================================================================
Write-Host "`n=== SETUP: Create Test Machine ===" -ForegroundColor Magenta

# First, ensure machines.json exists by creating test machine via machine profiles
$testMachineJson = '{"machines":[{"id":"test_router_n12","name":"Test Router N12","controller":"GRBL","tools":[]}]}'
$machinesPath = Join-Path $PSScriptRoot "services/api/app/data/machines.json"

try {
    # Create data directory if needed
    $dataDir = Join-Path $PSScriptRoot "services/api/app/data"
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    }
    
    # Create machines.json with test machine
    $testMachineJson | Out-File -FilePath $machinesPath -Encoding UTF8 -Force
    Write-Host "  📦 Created machines.json at $machinesPath" -ForegroundColor Gray
    
    # Set environment variable for API to use this path
    $env:TB_MACHINES_PATH = $machinesPath
    Write-Host "  📦 Set TB_MACHINES_PATH=$machinesPath" -ForegroundColor Gray
} catch {
    Write-Host "  ⚠️  Setup warning: $_" -ForegroundColor Yellow
}

# ============================================================================
# GROUP 1: API Availability & List Tools (4 tests)
# ============================================================================
Write-Host "`n=== GROUP 1: API Availability & List Tools ===" -ForegroundColor Yellow

try {
    $toolsResult = Invoke-RestMethod -Uri "$api/test_router_n12" -Method GET
    Test-Assert ($toolsResult.machine -eq "test_router_n12") "GET /tools/{mid} returns machine ID"
    Test-Assert ($toolsResult.tools -is [array]) "Tools field is array"
    Test-Assert ($toolsResult.tools.Count -eq 0) "New machine has 0 tools initially"
    
    Write-Host "  📊 Machine: $($toolsResult.machine) | Tools: $($toolsResult.tools.Count)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ API request failed: $_" -ForegroundColor Red
    Test-Assert $false "GET /tools/{mid} API available"
    
    # Skip remaining tests if API not available
    Write-Host "`n⚠️  API not available. Ensure server is running and machines.json exists." -ForegroundColor Yellow
    exit 1
}

# Additional availability test
try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/machines/tools" -Method GET -ErrorAction Stop
    Test-Assert $false "Should not have root endpoint"
} catch {
    # Expected to fail (no root endpoint)
    Test-Assert $true "Root endpoint correctly returns error"
}

# ============================================================================
# GROUP 2: Non-Existent Machine (1 test)
# ============================================================================
Write-Host "`n=== GROUP 2: Error Handling - Non-Existent Machine ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$api/machine_that_does_not_exist_xyz" -Method GET -ErrorAction Stop
    Test-Assert $false "Should return 404 for non-existent machine"
} catch {
    $errorCode = $_.Exception.Response.StatusCode.value__
    Test-Assert ($errorCode -eq 404) "Returns 404 for non-existent machine"
}

# ============================================================================
# GROUP 3: Add Tools via PUT (7 tests)
# ============================================================================
Write-Host "`n=== GROUP 3: Add Tools via PUT ===" -ForegroundColor Yellow

$tools = '[
    {
        "t": 1,
        "name": "6mm 2FL End Mill",
        "type": "EM",
        "dia_mm": 6.0,
        "len_mm": 25.0,
        "holder": "ER20",
        "offset_len_mm": 50.0,
        "spindle_rpm": 18000,
        "feed_mm_min": 1200,
        "plunge_mm_min": 400
    },
    {
        "t": 2,
        "name": "3mm Drill",
        "type": "DRILL",
        "dia_mm": 3.0,
        "len_mm": 40.0,
        "holder": "ER20",
        "offset_len_mm": 55.0,
        "spindle_rpm": 12000,
        "feed_mm_min": 600,
        "plunge_mm_min": 300
    },
    {
        "t": 3,
        "name": "6mm Ball Nose",
        "type": "BALL",
        "dia_mm": 6.0,
        "len_mm": 30.0,
        "holder": "ER20",
        "offset_len_mm": 52.0,
        "spindle_rpm": 16000,
        "feed_mm_min": 1000,
        "plunge_mm_min": 350
    }
]'

try {
    $putResult = Invoke-RestMethod -Uri "$api/test_router_n12" -Method PUT `
        -ContentType "application/json" -Body $tools
    Test-Assert ($putResult.ok -eq $true) "PUT /tools/{mid} returns ok=true"
    Test-Assert ($putResult.tools.Count -eq 3) "3 tools added successfully"
    
    # Verify tools were actually added
    $verifyTools = Invoke-RestMethod -Uri "$api/test_router_n12" -Method GET
    Test-Assert ($verifyTools.tools.Count -eq 3) "GET confirms 3 tools exist"
    Test-Assert ($verifyTools.tools[0].t -eq 1) "Tool T1 exists"
    Test-Assert ($verifyTools.tools[0].name -eq "6mm 2FL End Mill") "Tool T1 has correct name"
    Test-Assert ($verifyTools.tools[1].type -eq "DRILL") "Tool T2 is DRILL type"
    Test-Assert ($verifyTools.tools[2].dia_mm -eq 6.0) "Tool T3 has correct diameter"
    
    Write-Host "  📊 Added 3 tools: T1 (6mm EM), T2 (3mm Drill), T3 (6mm Ball)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Add tools failed: $_" -ForegroundColor Red
    Test-Assert $false "PUT /tools/{mid} adds tools"
}

# ============================================================================
# GROUP 4: Update Existing Tool (5 tests)
# ============================================================================
Write-Host "`n=== GROUP 4: Update Existing Tool via PUT ===" -ForegroundColor Yellow

$updateTool = '[
    {
        "t": 2,
        "name": "3mm Drill (Updated)",
        "type": "DRILL",
        "dia_mm": 3.2,
        "len_mm": 42.0,
        "holder": "ER16",
        "offset_len_mm": 56.0,
        "spindle_rpm": 15000,
        "feed_mm_min": 800,
        "plunge_mm_min": 400
    }
]'

try {
    $putResult = Invoke-RestMethod -Uri "$api/test_router_n12" -Method PUT `
        -ContentType "application/json" -Body $updateTool
    Test-Assert ($putResult.ok -eq $true) "Update tool returns ok=true"
    Test-Assert ($putResult.tools.Count -eq 3) "Still 3 tools (no duplication)"
    
    # Verify update was applied
    $verifyTools = Invoke-RestMethod -Uri "$api/test_router_n12" -Method GET
    $updatedTool = $verifyTools.tools | Where-Object { $_.t -eq 2 }
    Test-Assert ($updatedTool.name -eq "3mm Drill (Updated)") "Tool name was updated"
    Test-Assert ($updatedTool.dia_mm -eq 3.2) "Tool diameter was updated"
    Test-Assert ($updatedTool.holder -eq "ER16") "Tool holder was updated"
    
    Write-Host "  📊 Updated T2: dia=$($updatedTool.dia_mm)mm, rpm=$($updatedTool.spindle_rpm)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Update tool failed: $_" -ForegroundColor Red
    Test-Assert $false "PUT /tools/{mid} updates existing tool"
}

# ============================================================================
# GROUP 5: Add New Tool to Existing Table (3 tests)
# ============================================================================
Write-Host "`n=== GROUP 5: Add New Tool to Existing Table ===" -ForegroundColor Yellow

$newTool = '[
    {
        "t": 7,
        "name": "1/4 inch Router Bit",
        "type": "EM",
        "dia_mm": 6.35,
        "len_mm": 20.0,
        "holder": "Collet",
        "offset_len_mm": 45.0,
        "spindle_rpm": 20000,
        "feed_mm_min": 1500,
        "plunge_mm_min": 500
    }
]'

try {
    $putResult = Invoke-RestMethod -Uri "$api/test_router_n12" -Method PUT `
        -ContentType "application/json" -Body $newTool
    Test-Assert ($putResult.ok -eq $true) "Add new tool returns ok=true"
    Test-Assert ($putResult.tools.Count -eq 4) "Now 4 tools (added T7)"
    
    # Verify T7 exists and others unchanged
    $verifyTools = Invoke-RestMethod -Uri "$api/test_router_n12" -Method GET
    $tool7 = $verifyTools.tools | Where-Object { $_.t -eq 7 }
    Test-Assert ($tool7.name -eq "1/4 inch Router Bit") "T7 added successfully"
    
    Write-Host "  📊 Added T7: 1/4 inch Router Bit (6.35mm)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Add new tool failed: $_" -ForegroundColor Red
    Test-Assert $false "PUT /tools/{mid} adds new tool to existing table"
}

# ============================================================================
# GROUP 6: Tool Sorting (2 tests)
# ============================================================================
Write-Host "`n=== GROUP 6: Tool Sorting by T Number ===" -ForegroundColor Yellow

try {
    $tools = Invoke-RestMethod -Uri "$api/test_router_n12" -Method GET
    
    # Tools should be sorted by T number ascending (1, 2, 3, 7)
    $tNumbers = $tools.tools | ForEach-Object { $_.t }
    $expectedOrder = @(1, 2, 3, 7)
    $sortedCorrectly = ($tNumbers[0] -eq 1) -and ($tNumbers[1] -eq 2) -and ($tNumbers[2] -eq 3) -and ($tNumbers[3] -eq 7)
    
    Test-Assert $sortedCorrectly "Tools sorted by T number ascending"
    Test-Assert ($tNumbers.Count -eq 4) "All 4 tools present in sorted list"
    
    Write-Host "  📊 Tool order: T$($tNumbers[0]), T$($tNumbers[1]), T$($tNumbers[2]), T$($tNumbers[3])" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Tool sorting validation failed: $_" -ForegroundColor Red
    Test-Assert $false "Tools are sorted correctly"
}

# ============================================================================
# GROUP 7: Delete Tool (4 tests)
# ============================================================================
Write-Host "`n=== GROUP 7: Delete Tool ===" -ForegroundColor Yellow

try {
    $deleteResult = Invoke-RestMethod -Uri "$api/test_router_n12/7" -Method DELETE
    Test-Assert ($deleteResult.ok -eq $true) "DELETE /tools/{mid}/{tnum} returns ok=true"
    Test-Assert ($deleteResult.tools.Count -eq 3) "Now 3 tools (T7 deleted)"
    
    # Verify T7 is gone
    $verifyTools = Invoke-RestMethod -Uri "$api/test_router_n12" -Method GET
    $tool7 = $verifyTools.tools | Where-Object { $_.t -eq 7 }
    Test-Assert ($null -eq $tool7) "T7 no longer exists"
    Test-Assert ($verifyTools.tools.Count -eq 3) "GET confirms 3 tools remain"
    
    Write-Host "  📊 Deleted T7, remaining: T1, T2, T3" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Delete tool failed: $_" -ForegroundColor Red
    Test-Assert $false "DELETE /tools/{mid}/{tnum} works"
}

# ============================================================================
# GROUP 8: CSV Export (6 tests)
# ============================================================================
Write-Host "`n=== GROUP 8: CSV Export ===" -ForegroundColor Yellow

try {
    $csvResponse = Invoke-WebRequest -Uri "$api/test_router_n12.csv" -Method GET
    Test-Assert ($csvResponse.StatusCode -eq 200) "GET /tools/{mid}.csv returns 200"
    Test-Assert ($csvResponse.Headers.'Content-Type' -like "text/csv*") "Response is CSV"
    
    $csvContent = $csvResponse.Content
    $lines = $csvContent -split "`n" | Where-Object { $_ -ne "" }
    Test-Assert ($lines.Count -ge 4) "CSV has header + 3 tool rows"
    
    # Check header
    $header = $lines[0]
    Test-Assert ($header -match "t,name,type,dia_mm") "CSV header contains expected columns"
    
    # Check data rows
    Test-Assert ($lines[1] -match "^1,") "First row is T1"
    Test-Assert ($lines[2] -match "^2,") "Second row is T2"
    
    Write-Host "  📊 CSV: $($lines.Count-1) tool rows exported" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ CSV export failed: $_" -ForegroundColor Red
    Test-Assert $false "GET /tools/{mid}.csv exports CSV"
}

# ============================================================================
# GROUP 9: CSV Import (8 tests)
# ============================================================================
Write-Host "`n=== GROUP 9: CSV Import ===" -ForegroundColor Yellow

# Create test CSV file
$csvContent = @"
t,name,type,dia_mm,len_mm,holder,offset_len_mm,spindle_rpm,feed_mm_min,plunge_mm_min
4,8mm End Mill,EM,8.0,30.0,ER20,55.0,16000,1400,450
5,5mm Drill,DRILL,5.0,50.0,ER20,60.0,10000,500,250
6,12mm Face Mill,FACE,12.0,15.0,ER32,65.0,12000,2000,800
"@

$csvPath = "test_tools_import.csv"
$csvContent | Out-File -FilePath $csvPath -Encoding UTF8 -Force

try {
    # Import CSV
    $boundary = [System.Guid]::NewGuid().ToString()
    $csvBytes = [System.IO.File]::ReadAllBytes($csvPath)
    
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"tools.csv`"",
        "Content-Type: text/csv",
        "",
        [System.Text.Encoding]::UTF8.GetString($csvBytes),
        "--$boundary--"
    )
    
    $body = $bodyLines -join "`r`n"
    
    $importResult = Invoke-RestMethod -Uri "$api/test_router_n12/import_csv" -Method POST `
        -ContentType "multipart/form-data; boundary=$boundary" -Body $body
    
    Test-Assert ($importResult.ok -eq $true) "POST /import_csv returns ok=true"
    Test-Assert ($importResult.count -eq 3) "Imported 3 tools from CSV"
    Test-Assert ($importResult.skipped -eq 0) "0 rows skipped"
    Test-Assert ($importResult.tools.Count -eq 6) "Now 6 tools total (3 original + 3 imported)"
    
    # Verify imported tools
    $verifyTools = Invoke-RestMethod -Uri "$api/test_router_n12" -Method GET
    $tool4 = $verifyTools.tools | Where-Object { $_.t -eq 4 }
    $tool5 = $verifyTools.tools | Where-Object { $_.t -eq 5 }
    $tool6 = $verifyTools.tools | Where-Object { $_.t -eq 6 }
    
    Test-Assert ($tool4.name -eq "8mm End Mill") "T4 imported correctly"
    Test-Assert ($tool5.dia_mm -eq 5.0) "T5 has correct diameter"
    Test-Assert ($tool6.type -eq "FACE") "T6 has correct type"
    
    Write-Host "  📊 Imported: T4 (8mm EM), T5 (5mm Drill), T6 (12mm Face Mill)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ CSV import failed: $_" -ForegroundColor Red
    Test-Assert $false "POST /import_csv works"
} finally {
    # Cleanup CSV file
    if (Test-Path $csvPath) {
        Remove-Item $csvPath -Force
    }
}

# ============================================================================
# GROUP 10: CSV Import with Invalid Data (3 tests)
# ============================================================================
Write-Host "`n=== GROUP 10: CSV Import Error Handling ===" -ForegroundColor Yellow

# Create CSV with invalid rows (missing required fields)
$invalidCsv = @"
t,name,type,dia_mm,len_mm,holder,offset_len_mm,spindle_rpm,feed_mm_min,plunge_mm_min
10,Valid Tool,EM,10.0,25.0,ER20,50.0,18000,1200,400
,Invalid No T,EM,6.0,20.0,ER20,45.0,16000,1000,350
11,,EM,8.0,30.0,ER20,55.0,14000,1100,375
12,Invalid No Dia,,abc,25.0,ER20,50.0,12000,900,300
"@

$invalidCsvPath = "test_invalid_tools.csv"
$invalidCsv | Out-File -FilePath $invalidCsvPath -Encoding UTF8 -Force

try {
    # Import CSV with invalid rows
    $boundary = [System.Guid]::NewGuid().ToString()
    $csvBytes = [System.IO.File]::ReadAllBytes($invalidCsvPath)
    
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"invalid_tools.csv`"",
        "Content-Type: text/csv",
        "",
        [System.Text.Encoding]::UTF8.GetString($csvBytes),
        "--$boundary--"
    )
    
    $body = $bodyLines -join "`r`n"
    
    $importResult = Invoke-RestMethod -Uri "$api/test_router_n12/import_csv" -Method POST `
        -ContentType "multipart/form-data; boundary=$boundary" -Body $body
    
    Test-Assert ($importResult.ok -eq $true) "Import with invalid rows still returns ok=true"
    Test-Assert ($importResult.count -eq 1) "Only 1 valid tool imported (T10)"
    Test-Assert ($importResult.skipped -ge 3) "At least 3 invalid rows skipped"
    
    Write-Host "  📊 Imported 1 valid, skipped $($importResult.skipped) invalid rows" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ CSV error handling test failed: $_" -ForegroundColor Red
    Test-Assert $false "CSV import handles invalid data gracefully"
} finally {
    # Cleanup CSV file
    if (Test-Path $invalidCsvPath) {
        Remove-Item $invalidCsvPath -Force
    }
}

# ============================================================================
# GROUP 11: Tool Structure Validation (10 tests)
# ============================================================================
Write-Host "`n=== GROUP 11: Tool Structure Validation ===" -ForegroundColor Yellow

try {
    $toolsResult = Invoke-RestMethod -Uri "$api/test_router_n12" -Method GET
    $tool1 = $toolsResult.tools | Where-Object { $_.t -eq 1 }
    
    # Required fields
    Test-Assert ($tool1.t -ne $null) "Tool has 't' field"
    Test-Assert ($tool1.name -ne $null) "Tool has 'name' field"
    Test-Assert ($tool1.type -ne $null) "Tool has 'type' field"
    Test-Assert ($tool1.dia_mm -ne $null) "Tool has 'dia_mm' field"
    Test-Assert ($tool1.len_mm -ne $null) "Tool has 'len_mm' field"
    
    # Optional fields
    Test-Assert ($tool1.holder -ne $null) "Tool has 'holder' field"
    Test-Assert ($tool1.offset_len_mm -ne $null) "Tool has 'offset_len_mm' field"
    Test-Assert ($tool1.spindle_rpm -ne $null) "Tool has 'spindle_rpm' field"
    Test-Assert ($tool1.feed_mm_min -ne $null) "Tool has 'feed_mm_min' field"
    Test-Assert ($tool1.plunge_mm_min -ne $null) "Tool has 'plunge_mm_min' field"
    
    Write-Host "  📊 T1 structure valid: $($tool1.name) ($($tool1.dia_mm)mm $($tool1.type))" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Tool structure validation failed: $_" -ForegroundColor Red
    Test-Assert $false "Tool structure is valid"
}

# ============================================================================
# GROUP 12: Delete Multiple Tools (3 tests)
# ============================================================================
Write-Host "`n=== GROUP 12: Delete Multiple Tools ===" -ForegroundColor Yellow

try {
    # Delete T4, T5, T6
    $delete4 = Invoke-RestMethod -Uri "$api/test_router_n12/4" -Method DELETE
    $delete5 = Invoke-RestMethod -Uri "$api/test_router_n12/5" -Method DELETE
    $delete6 = Invoke-RestMethod -Uri "$api/test_router_n12/6" -Method DELETE
    
    Test-Assert ($delete4.ok -and $delete5.ok -and $delete6.ok) "All deletes return ok=true"
    
    # Verify count
    $verifyTools = Invoke-RestMethod -Uri "$api/test_router_n12" -Method GET
    Test-Assert ($verifyTools.tools.Count -eq 4) "4 tools remain (T1, T2, T3, T10)"
    
    # Verify specific tools remain
    $remainingTs = $verifyTools.tools | ForEach-Object { $_.t }
    $hasT1 = $remainingTs -contains 1
    $hasT2 = $remainingTs -contains 2
    $hasT3 = $remainingTs -contains 3
    $hasT10 = $remainingTs -contains 10
    Test-Assert ($hasT1 -and $hasT2 -and $hasT3 -and $hasT10) "Correct tools remain after deletions"
    
    Write-Host "  📊 Deleted T4, T5, T6. Remaining: T1, T2, T3, T10" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Delete multiple tools failed: $_" -ForegroundColor Red
    Test-Assert $false "Can delete multiple tools"
}

# ============================================================================
# CLEANUP: Delete test machine data
# ============================================================================
Write-Host "`n=== CLEANUP: Remove Test Data ===" -ForegroundColor Magenta

try {
    # Restore machines.json to empty state or original state
    # For safety, just remove our test machine from the JSON
    if (Test-Path $machinesPath) {
        $machines = Get-Content $machinesPath | ConvertFrom-Json
        $machines.machines = @($machines.machines | Where-Object { $_.id -ne "test_router_n12" })
        $machines | ConvertTo-Json -Depth 10 | Out-File -FilePath $machinesPath -Encoding UTF8 -Force
        Write-Host "  🧹 Removed test_router_n12 from machines.json" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠️  Cleanup warning: $_" -ForegroundColor Yellow
}

# ============================================================================
# FINAL RESULTS
# ============================================================================
Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    TEST RESULTS SUMMARY                       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$passRate = [math]::Round(($passedTests / $totalTests) * 100, 1)

Write-Host "Total Tests:  $totalTests" -ForegroundColor White
Write-Host "Passed:       $passedTests" -ForegroundColor Green
Write-Host "Failed:       $($totalTests - $passedTests)" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Red" })
Write-Host "Pass Rate:    $passRate%" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Yellow" })

if ($passedTests -eq $totalTests) {
    Write-Host "`n✅ ALL N.12 TOOL TABLES TESTS PASSED!" -ForegroundColor Green -BackgroundColor Black
    Write-Host "   Tool Tables CRUD with CSV import/export is production-ready." -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Review output above." -ForegroundColor Yellow
}

Write-Host "`n"
