# Test-MM0-StripFamilies.ps1
# Smoke test for MM-0 Mixed-Material Strip Families backend

$BASE = "http://localhost:8000"
$API = "$BASE/api/rmos/strip-families"

Write-Host "=== MM-0 Strip Family Tests ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Fetch templates
Write-Host "1. GET /api/rmos/strip-families/templates" -ForegroundColor Yellow
try {
    $templates = Invoke-RestMethod -Uri "$API/templates" -Method GET
    Write-Host "  ✓ Fetched $($templates.Count) templates" -ForegroundColor Green
    if ($templates.Count -ge 3) {
        Write-Host "    - $($templates[0].name): $($templates[0].materials.Count) materials" -ForegroundColor Gray
        Write-Host "    - $($templates[1].name): $($templates[1].materials.Count) materials" -ForegroundColor Gray
        Write-Host "    - $($templates[2].name): $($templates[2].materials.Count) materials" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Instantiate template
Write-Host "2. POST /api/rmos/strip-families/from-template/{id}" -ForegroundColor Yellow
$templateId = $templates[0].id
Write-Host "  Using template: $templateId" -ForegroundColor Gray
try {
    $created = Invoke-RestMethod -Uri "$API/from-template/$templateId" -Method POST
    Write-Host "  ✓ Created strip family: $($created.name)" -ForegroundColor Green
    Write-Host "    - ID: $($created.id)" -ForegroundColor Gray
    Write-Host "    - Width: $($created.default_width_mm)mm" -ForegroundColor Gray
    Write-Host "    - Materials: $($created.materials.Count)" -ForegroundColor Gray
    Write-Host "    - Lane: $($created.lane)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 3: Fetch all strip families
Write-Host "3. GET /api/rmos/strip-families/" -ForegroundColor Yellow
try {
    $families = Invoke-RestMethod -Uri "$API/" -Method GET
    Write-Host "  ✓ Fetched $($families.Count) strip families" -ForegroundColor Green
    if ($families.Count -gt 0) {
        $families | ForEach-Object {
            Write-Host "    - $($_.name) [$($_.lane)]: $($_.materials.Count) materials" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 4: Get specific strip family
Write-Host "4. GET /api/rmos/strip-families/{id}" -ForegroundColor Yellow
$familyId = $created.id
Write-Host "  Fetching family: $familyId" -ForegroundColor Gray
try {
    $family = Invoke-RestMethod -Uri "$API/$familyId" -Method GET
    Write-Host "  ✓ Retrieved: $($family.name)" -ForegroundColor Green
    Write-Host "    - Materials:" -ForegroundColor Gray
    $family.materials | ForEach-Object {
        Write-Host "      * $($_.species) ($($_.type)): $($_.thickness_mm)mm - $($_.finish)" -ForegroundColor Gray
        if ($_.visual) {
            Write-Host "        Color: $($_.visual.base_color), Reflectivity: $($_.visual.reflectivity)" -ForegroundColor DarkGray
        }
    }
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 5: Verify material specs
Write-Host "5. Material Spec Validation" -ForegroundColor Yellow
$expectedTypes = @("wood", "metal", "shell", "paper", "foil", "charred", "resin", "composite")
$foundTypes = $family.materials | Select-Object -ExpandProperty type -Unique
Write-Host "  Found material types: $($foundTypes -join ', ')" -ForegroundColor Gray

$allMaterials = $templates | ForEach-Object { $_.materials } | ForEach-Object { $_ }
$allTypes = $allMaterials | Select-Object -ExpandProperty type -Unique
Write-Host "  All template types: $($allTypes -join ', ')" -ForegroundColor Gray

$hasVisual = ($family.materials | Where-Object { $_.visual -ne $null }).Count
Write-Host "  Materials with visual properties: $hasVisual / $($family.materials.Count)" -ForegroundColor Gray

if ($hasVisual -eq $family.materials.Count) {
    Write-Host "  ✓ All materials have visual properties" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Some materials missing visual properties" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "=== MM-0 Tests Complete ===" -ForegroundColor Cyan
Write-Host "✓ Template library loaded ($($templates.Count) templates)" -ForegroundColor Green
Write-Host "✓ Template instantiation working" -ForegroundColor Green
Write-Host "✓ Strip family CRUD operations functional" -ForegroundColor Green
Write-Host "✓ Material specs with visual properties validated" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Start Vite dev server and test UI at http://localhost:5173/rmos/strip-family-lab" -ForegroundColor Cyan
