# RMOS JSON to SQLite Migration Test Suite (N8.7)
# Tests migration tool with sample JSON data

$ErrorActionPreference = 'Stop'
$baseDir = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $baseDir "services\api"
$testDataDir = Join-Path $apiDir "test_data\rmos_migration"

Write-Host "=== RMOS Migration Test Suite ===" -ForegroundColor Cyan
Write-Host ""

# Create test data directory
if (Test-Path $testDataDir) {
    Remove-Item -Recurse -Force $testDataDir
}
New-Item -ItemType Directory -Path $testDataDir | Out-Null
New-Item -ItemType Directory -Path (Join-Path $testDataDir "patterns") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $testDataDir "strip_families") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $testDataDir "joblogs") | Out-Null

Write-Host "1. Creating sample JSON files..." -ForegroundColor Yellow

# Sample pattern
$pattern1 = @{
    id = "test-pattern-001"
    name = "Herringbone Rosette"
    ring_count = 3
    geometry = @{
        rings = @(
            @{ radius_mm = 40; segments = 60 },
            @{ radius_mm = 45; segments = 72 },
            @{ radius_mm = 50; segments = 84 }
        )
    }
    strip_family_id = "test-family-001"
    metadata = @{
        complexity = "medium"
        estimated_time_min = 45
    }
} | ConvertTo-Json -Depth 10

$pattern1 | Out-File (Join-Path $testDataDir "patterns\pattern_001.json")

# Sample strip family
$stripFamily1 = @{
    id = "test-family-001"
    name = "Ebony 2mm Standard"
    strip_width_mm = 2.0
    strip_thickness_mm = 0.8
    material_type = "Ebony"
    strips = @(
        @{ id = "strip-001"; length_mm = 400; position = 0 },
        @{ id = "strip-002"; length_mm = 400; position = 1 }
    )
    metadata = @{
        supplier = "Test Supplier"
        batch = "2025-01"
    }
} | ConvertTo-Json -Depth 10

$stripFamily1 | Out-File (Join-Path $testDataDir "strip_families\family_001.json")

# Sample joblog
$joblog1 = @{
    id = "test-job-001"
    job_type = "slice"
    pattern_id = "test-pattern-001"
    strip_family_id = "test-family-001"
    status = "completed"
    start_time = "2025-01-15T10:30:00"
    end_time = "2025-01-15T11:15:00"
    duration_seconds = 2700
    parameters = @{
        blade_angle = 45
        feed_rate = 100
    }
    results = @{
        cuts_made = 180
        waste_percentage = 5.2
    }
} | ConvertTo-Json -Depth 10

$joblog1 | Out-File (Join-Path $testDataDir "joblogs\job_001.json")

Write-Host "  ✓ Created 3 sample JSON files" -ForegroundColor Green
Write-Host ""

# Run migration in dry-run mode
Write-Host "2. Testing dry-run migration..." -ForegroundColor Yellow

Push-Location $apiDir
try {
    $dryRunOutput = python -m app.tools.rmos_migrate_json_to_sqlite --dry-run 2>&1
    $dryRunSuccess = $LASTEXITCODE -eq 0
    
    if ($dryRunSuccess) {
        Write-Host "  ✓ Dry-run completed successfully" -ForegroundColor Green
        Write-Host $dryRunOutput
    } else {
        Write-Host "  ✗ Dry-run failed" -ForegroundColor Red
        Write-Host $dryRunOutput
    }
} finally {
    Pop-Location
}

Write-Host ""

# Run actual migration
Write-Host "3. Running actual migration..." -ForegroundColor Yellow

Push-Location $apiDir
try {
    $migrationOutput = python -m app.tools.rmos_migrate_json_to_sqlite 2>&1
    $migrationSuccess = $LASTEXITCODE -eq 0
    
    if ($migrationSuccess) {
        Write-Host "  ✓ Migration completed successfully" -ForegroundColor Green
        Write-Host $migrationOutput
    } else {
        Write-Host "  ✗ Migration failed" -ForegroundColor Red
        Write-Host $migrationOutput
    }
} finally {
    Pop-Location
}

Write-Host ""

# Verify data in SQLite
Write-Host "4. Verifying migrated data..." -ForegroundColor Yellow

$verifyPattern = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/patterns/test-pattern-001" -Method GET
if ($verifyPattern.name -eq "Herringbone Rosette") {
    Write-Host "  ✓ Pattern migrated correctly" -ForegroundColor Green
} else {
    Write-Host "  ✗ Pattern not found or incorrect" -ForegroundColor Red
}

$verifyFamily = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/strip-families/test-family-001" -Method GET
if ($verifyFamily.name -eq "Ebony 2mm Standard") {
    Write-Host "  ✓ Strip family migrated correctly" -ForegroundColor Green
} else {
    Write-Host "  ✗ Strip family not found or incorrect" -ForegroundColor Red
}

$verifyJob = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/joblogs/test-job-001" -Method GET
if ($verifyJob.job_type -eq "slice") {
    Write-Host "  ✓ JobLog migrated correctly" -ForegroundColor Green
} else {
    Write-Host "  ✗ JobLog not found or incorrect" -ForegroundColor Red
}

Write-Host ""

# Test duplicate detection
Write-Host "5. Testing duplicate detection..." -ForegroundColor Yellow

Push-Location $apiDir
try {
    $duplicateOutput = python -m app.tools.rmos_migrate_json_to_sqlite 2>&1
    $duplicateSuccess = $LASTEXITCODE -eq 0
    
    if ($duplicateSuccess -and $duplicateOutput -match "skipped") {
        Write-Host "  ✓ Duplicate detection working" -ForegroundColor Green
        Write-Host "  (Entities skipped on second run)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Duplicate detection may not be working" -ForegroundColor Red
    }
} finally {
    Pop-Location
}

Write-Host ""

# Test report generation
Write-Host "6. Testing report generation..." -ForegroundColor Yellow

Push-Location $apiDir
try {
    # Create a stats file
    $sampleStats = @{
        patterns = @{ found = 1; migrated = 1; skipped = 0; failed = 0 }
        joblogs = @{ found = 1; migrated = 1; skipped = 0; failed = 0 }
        strip_families = @{ found = 1; migrated = 1; skipped = 0; failed = 0 }
    } | ConvertTo-Json -Depth 10
    
    $statsFile = Join-Path $testDataDir "test_stats.json"
    $sampleStats | Out-File $statsFile
    
    $reportOutput = python -m app.tools.rmos_migration_report $statsFile 2>&1
    
    if (Test-Path "migration_reports") {
        $reportFiles = Get-ChildItem "migration_reports" -Filter "*.html"
        if ($reportFiles.Count -gt 0) {
            Write-Host "  ✓ Reports generated successfully" -ForegroundColor Green
            Write-Host "  Found: $($reportFiles.Count) report files" -ForegroundColor Gray
        } else {
            Write-Host "  ✗ No report files generated" -ForegroundColor Red
        }
    } else {
        Write-Host "  ✗ Report directory not created" -ForegroundColor Red
    }
} finally {
    Pop-Location
}

Write-Host ""

# Test audit tool
Write-Host "7. Testing audit tool..." -ForegroundColor Yellow

Push-Location $apiDir
try {
    $auditOutput = python -m app.tools.rmos_migration_audit 2>&1
    $auditSuccess = $LASTEXITCODE -eq 0
    
    if ($auditSuccess) {
        Write-Host "  ✓ Audit passed successfully" -ForegroundColor Green
        
        # Check for expected output patterns
        if ($auditOutput -match "PASSED") {
            Write-Host "  ✓ Audit report generated" -ForegroundColor Green
        }
        if ($auditOutput -match "Patterns:\s+\d+") {
            Write-Host "  ✓ Entity counts validated" -ForegroundColor Green
        }
        if ($auditOutput -match "Passed:\s+\d+") {
            Write-Host "  ✓ Check statistics reported" -ForegroundColor Green
        }
    } else {
        Write-Host "  ✗ Audit failed" -ForegroundColor Red
        Write-Host $auditOutput
    }
} finally {
    Pop-Location
}

Write-Host ""

# Test migration dashboard API
Write-Host "8. Testing migration dashboard API..." -ForegroundColor Yellow

try {
    $statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/migration/status" -Method GET
    
    if ($statusResponse.success) {
        Write-Host "  ✓ Migration status endpoint accessible" -ForegroundColor Green
        
        # Check response structure
        if ($statusResponse.entity_counts) {
            Write-Host "  ✓ Entity counts present: $($statusResponse.entity_counts.total) total" -ForegroundColor Green
        }
        if ($statusResponse.migration_status) {
            Write-Host "  ✓ Migration status present" -ForegroundColor Green
            Write-Host "    Database size: $($statusResponse.migration_status.database_size_mb) MB" -ForegroundColor Gray
        }
        if ($statusResponse.validation) {
            $valStatus = $statusResponse.validation.status
            if ($valStatus -eq "healthy") {
                Write-Host "  ✓ Validation status: $valStatus" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ Validation status: $valStatus" -ForegroundColor Yellow
            }
        }
        if ($statusResponse.recent_entities) {
            Write-Host "  ✓ Recent entities present" -ForegroundColor Green
        }
    } else {
        Write-Host "  ✗ Status endpoint failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Failed to call status endpoint" -ForegroundColor Red
    Write-Host "    $_" -ForegroundColor Red
}

Write-Host ""

try {
    $historyResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/migration/history?limit=10" -Method GET
    
    if ($historyResponse.success) {
        Write-Host "  ✓ Migration history endpoint accessible" -ForegroundColor Green
        
        if ($historyResponse.history) {
            Write-Host "  ✓ History records present: $($historyResponse.history.Count) dates" -ForegroundColor Green
        }
        if ($historyResponse.total_migration_dates) {
            Write-Host "    Total migration dates: $($historyResponse.total_migration_dates)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ✗ History endpoint failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Failed to call history endpoint" -ForegroundColor Red
    Write-Host "    $_" -ForegroundColor Red
}

Write-Host ""

# Cleanup test data
Write-Host "9. Cleaning up test data..." -ForegroundColor Yellow

try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/joblogs/test-job-001" -Method DELETE | Out-Null
    Write-Host "  ✓ Deleted test joblog" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to delete joblog" -ForegroundColor Red
}

try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/patterns/test-pattern-001" -Method DELETE | Out-Null
    Write-Host "  ✓ Deleted test pattern" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to delete pattern" -ForegroundColor Red
}

try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/strip-families/test-family-001" -Method DELETE | Out-Null
    Write-Host "  ✓ Deleted test strip family" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to delete strip family" -ForegroundColor Red
}

if (Test-Path $testDataDir) {
    Remove-Item -Recurse -Force $testDataDir
    Write-Host "  ✓ Removed test data directory" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Migration Test Suite Complete ===" -ForegroundColor Cyan
