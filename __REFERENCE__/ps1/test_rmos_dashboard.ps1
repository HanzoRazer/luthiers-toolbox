# Quick test for Migration Dashboard API (N8.7)
# Requires FastAPI server running on port 8000

$ErrorActionPreference = 'Stop'

Write-Host "=== Migration Dashboard API Quick Test ===" -ForegroundColor Cyan
Write-Host ""

# Test migration status endpoint
Write-Host "1. Testing GET /api/rmos/stores/migration/status" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/migration/status" -Method GET
    
    Write-Host "  Response structure:" -ForegroundColor Gray
    Write-Host "    success: $($response.success)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "  Migration Status:" -ForegroundColor Green
    Write-Host "    Last migration: $($response.migration_status.last_migration)" -ForegroundColor Gray
    Write-Host "    Database location: $($response.migration_status.database_location)" -ForegroundColor Gray
    Write-Host "    Database size: $($response.migration_status.database_size_mb) MB" -ForegroundColor Gray
    Write-Host "    Schema version: $($response.migration_status.schema_version)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "  Entity Counts:" -ForegroundColor Green
    Write-Host "    Patterns: $($response.entity_counts.patterns)" -ForegroundColor Gray
    Write-Host "    Strip Families: $($response.entity_counts.strip_families)" -ForegroundColor Gray
    Write-Host "    JobLogs: $($response.entity_counts.joblogs)" -ForegroundColor Gray
    Write-Host "    Total: $($response.entity_counts.total)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "  Validation:" -ForegroundColor Green
    Write-Host "    Status: $($response.validation.status)" -ForegroundColor Gray
    Write-Host "    Errors: $($response.validation.errors.Count)" -ForegroundColor Gray
    Write-Host "    Warnings: $($response.validation.warnings.Count)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "  Recent Entities:" -ForegroundColor Green
    Write-Host "    Recent patterns: $($response.recent_entities.patterns.Count)" -ForegroundColor Gray
    Write-Host "    Recent families: $($response.recent_entities.strip_families.Count)" -ForegroundColor Gray
    Write-Host "    Recent joblogs: $($response.recent_entities.joblogs.Count)" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "  ✓ Migration status endpoint working" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to call migration status endpoint" -ForegroundColor Red
    Write-Host "    Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test migration history endpoint
Write-Host "2. Testing GET /api/rmos/stores/migration/history" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/stores/migration/history?limit=5" -Method GET
    
    Write-Host "  Response structure:" -ForegroundColor Gray
    Write-Host "    success: $($response.success)" -ForegroundColor Gray
    Write-Host "    total_migration_dates: $($response.total_migration_dates)" -ForegroundColor Gray
    Write-Host ""
    
    if ($response.history -and $response.history.Count -gt 0) {
        Write-Host "  Migration History (last $($response.history.Count) dates):" -ForegroundColor Green
        foreach ($entry in $response.history) {
            Write-Host "    $($entry.date):" -ForegroundColor Gray
            Write-Host "      Patterns: $($entry.entities.patterns)" -ForegroundColor Gray
            Write-Host "      Strip Families: $($entry.entities.strip_families)" -ForegroundColor Gray
            Write-Host "      JobLogs: $($entry.entities.joblogs)" -ForegroundColor Gray
            Write-Host "      Total: $($entry.total)" -ForegroundColor Gray
            Write-Host ""
        }
    } else {
        Write-Host "  No migration history found (database may be empty)" -ForegroundColor Yellow
    }
    
    Write-Host "  ✓ Migration history endpoint working" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to call migration history endpoint" -ForegroundColor Red
    Write-Host "    Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== All Dashboard API Tests Passed ===" -ForegroundColor Cyan
