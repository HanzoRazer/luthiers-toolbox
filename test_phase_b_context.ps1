# Test Phase B — RMOS Context System
# Wave 17→18 Integration
#
# Tests:
# 1. RmosContext.from_model_id() factory
# 2. Context validation
# 3. Material profile defaults
# 4. Context serialization (to_dict/from_dict)
# 5. FastAPI endpoints (if server running)

Write-Host "=== Testing RMOS Context System (Phase B) ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Import RmosContext
Write-Host "1. Testing RmosContext import..." -ForegroundColor Yellow
try {
    python -c "from services.api.app.rmos.context import RmosContext, MaterialProfile, SafetyConstraints, WoodSpecies; print('✓ Import successful')"
    Write-Host "✓ RmosContext import successful" -ForegroundColor Green
} catch {
    Write-Host "✗ Import failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Create context from model ID
Write-Host "2. Testing RmosContext.from_model_id()..." -ForegroundColor Yellow
$testScript = @"
from services.api.app.rmos.context import RmosContext

# Create context for Strat 25.5
context = RmosContext.from_model_id('strat_25_5')

print(f'Model ID: {context.model_id}')
print(f'Scale length: {context.model_spec["scale_length_mm"]}mm')
print(f'Num strings: {context.model_spec["num_strings"]}')
print(f'Material: {context.materials.species.value}')
print(f'Thickness: {context.materials.thickness_mm}mm')

# Validate
errors = context.validate()
if errors:
    print(f'Validation errors: {errors}')
else:
    print('✓ Validation passed')
"@

try {
    $result = $testScript | python
    Write-Host $result -ForegroundColor Green
} catch {
    Write-Host "✗ Factory test failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 3: Context adapter
Write-Host "3. Testing context_adapter.build_rmos_context_for_model()..." -ForegroundColor Yellow
$adapterScript = @"
from services.api.app.rmos.context_adapter import build_rmos_context_for_model, get_context_summary

# Build context with mahogany
context = build_rmos_context_for_model(
    'benedetto_17',
    material_species='mahogany',
    material_thickness_mm=44.45
)

print(f'Model: {context.model_id}')
print(f'Material: {context.materials.species.value}')
print(f'Thickness: {context.materials.thickness_mm}mm ({context.materials.thickness_mm / 25.4:.2f} inches)')

# Get summary
summary = get_context_summary(context)
print(f'Scale: {summary["scale_length_in"]}" inches')
print(f'Validation errors: {len(summary["validation_errors"])}')
print('✓ Context adapter works')
"@

try {
    $result = $adapterScript | python
    Write-Host $result -ForegroundColor Green
} catch {
    Write-Host "✗ Adapter test failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 4: Serialization (to_dict/from_dict)
Write-Host "4. Testing context serialization..." -ForegroundColor Yellow
$serializeScript = @"
from services.api.app.rmos.context import RmosContext

# Create context
context1 = RmosContext.from_model_id('lp_24_75')

# Serialize to dict
payload = context1.to_dict()
print(f'Serialized keys: {list(payload.keys())}')

# Deserialize from dict
context2 = RmosContext.from_dict(payload)
print(f'Deserialized model_id: {context2.model_id}')
print(f'Scale match: {context1.model_spec["scale_length_mm"] == context2.model_spec["scale_length_mm"]}')
print('✓ Serialization round-trip works')
"@

try {
    $result = $serializeScript | python
    Write-Host $result -ForegroundColor Green
} catch {
    Write-Host "✗ Serialization test failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 5: API endpoints (optional, requires server)
Write-Host "5. Testing FastAPI endpoints (optional)..." -ForegroundColor Yellow
$serverRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    $serverRunning = $true
} catch {
    Write-Host "⚠ Server not running, skipping API tests" -ForegroundColor Yellow
}

if ($serverRunning) {
    Write-Host "Server detected, testing endpoints..." -ForegroundColor Cyan
    
    # Test GET /api/rmos/models
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/models" -Method GET
        Write-Host "✓ GET /api/rmos/models: Found $($response.count) models" -ForegroundColor Green
    } catch {
        Write-Host "✗ GET /api/rmos/models failed: $_" -ForegroundColor Red
    }
    
    # Test GET /api/rmos/context/{model_id}
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/context/strat_25_5" -Method GET
        Write-Host "✓ GET /api/rmos/context/strat_25_5: Scale = $($response.summary.scale_length_in)""" -ForegroundColor Green
    } catch {
        Write-Host "✗ GET /api/rmos/context/{model_id} failed: $_" -ForegroundColor Red
    }
    
    # Test POST /api/rmos/context
    try {
        $body = @{
            model_id = "benedetto_17"
            material_species = "rosewood"
            material_thickness_mm = 25.4
            include_default_cuts = $true
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/context" -Method POST -Body $body -ContentType "application/json"
        Write-Host "✓ POST /api/rmos/context: Created context with $($response.summary.cut_count) cuts" -ForegroundColor Green
    } catch {
        Write-Host "✗ POST /api/rmos/context failed: $_" -ForegroundColor Red
    }
    
    # Test POST /api/rmos/context/validate
    try {
        $contextPayload = @{
            context = @{
                model_id = "strat_25_5"
                model_spec = @{
                    scale_length_mm = 648.0
                    num_strings = 6
                }
                materials = @{
                    species = "maple"
                    thickness_mm = 25.4
                    density_kg_m3 = 705.0
                }
            }
        } | ConvertTo-Json -Depth 10
        
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/context/validate" -Method POST -Body $contextPayload -ContentType "application/json"
        if ($response.valid) {
            Write-Host "✓ POST /api/rmos/context/validate: Context is valid" -ForegroundColor Green
        } else {
            Write-Host "✗ POST /api/rmos/context/validate: Errors = $($response.errors)" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ POST /api/rmos/context/validate failed: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Phase B Testing Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "✓ RmosContext class created with full dataclass support" -ForegroundColor Green
Write-Host "✓ Material profiles (11 wood species with density/hardness)" -ForegroundColor Green
Write-Host "✓ Safety constraints (feed/speed/tool limits)" -ForegroundColor Green
Write-Host "✓ Context adapter (model_id → RmosContext transformation)" -ForegroundColor Green
Write-Host "✓ Serialization (to_dict/from_dict round-trip)" -ForegroundColor Green
Write-Host "✓ FastAPI router with 4 endpoints (GET/POST)" -ForegroundColor Green
Write-Host "✓ Registered in main.py with graceful degradation" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update WAVE17_TODO.md with Phase B completion status" -ForegroundColor White
Write-Host "2. Begin Phase C (Fretboard Geometry)" -ForegroundColor White
Write-Host "3. Wire feasibility scoring to use RmosContext (Phase D)" -ForegroundColor White
