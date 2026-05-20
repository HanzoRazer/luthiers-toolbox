# Vectorizer governance audit — ground-truth verification
# Run from repo root: .\scripts\governance\verify_vectorizer_audit.ps1

$ErrorActionPreference = "Continue"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

$Pass = 0
$Fail = 0
$Warn = 0

function Write-Check {
    param([string]$Id, [string]$Status, [string]$Message)
    $symbol = switch ($Status) {
        "PASS" { $script:Pass++; "OK" }
        "FAIL" { $script:Fail++; "FAIL" }
        "WARN" { $script:Warn++; "WARN" }
        default { "?" }
    }
    Write-Host "[$symbol] $Id — $Message"
}

Write-Host ""
Write-Host "=== Vectorizer audit verification ===" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"
Write-Host ""

# --- 1. Cognitive extractor LOC ---
Write-Host "--- 1. Cognitive extractor line counts ---" -ForegroundColor Yellow
$cog1 = Join-Path $RepoRoot "services\photo-vectorizer\cognitive_extractor.py"
$cog2 = Join-Path $RepoRoot "services\photo-vectorizer\cognitive_extraction_engine.py"
foreach ($f in @($cog1, $cog2)) {
    if (Test-Path $f) {
        $n = (Get-Content $f).Count
        Write-Host "  $(Split-Path $f -Leaf): $n lines"
    } else {
        Write-Check "LOC" "FAIL" "Missing $f"
    }
}
$lines1 = if (Test-Path $cog1) { (Get-Content $cog1).Count } else { 0 }
$lines2 = if (Test-Path $cog2) { (Get-Content $cog2).Count } else { 0 }
if ($lines1 -ge 1400 -and $lines2 -ge 1400) {
    Write-Check "1-LOC" "PASS" "Both cognitive files >= 1400 LOC ($lines1, $lines2)"
} else {
    Write-Check "1-LOC" "WARN" "LOC differs from audit (~1455/1492): $lines1, $lines2"
}

# --- 2. Semantic sandbox import gate (cognitive + grid) ---
Write-Host ""
Write-Host "--- 2. Semantic sandbox imports (services/) ---" -ForegroundColor Yellow
$gateScript = Join-Path $RepoRoot "scripts\governance\check_semantic_sandbox_imports.py"
if (-not (Test-Path $gateScript)) {
    Write-Check "2-SANDBOX-GATE" "FAIL" "Missing $gateScript"
} else {
    $gateOut = & python $gateScript 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        Write-Check "2-SANDBOX-GATE" "PASS" "check_semantic_sandbox_imports.py (cognitive_extract*, extract_body_grid*)"
    } else {
        Write-Check "2-SANDBOX-GATE" "FAIL" "check_semantic_sandbox_imports.py failed"
        $gateOut.Trim() -split "`n" | Select-Object -First 12 | ForEach-Object { Write-Host "    $_" }
    }
}

# --- 3. _simple_extraction + UNKNOWN export exclusion ---
Write-Host ""
Write-Host "--- 3. SIMPLE mode + UNKNOWN export ---" -ForegroundColor Yellow
$phase3 = Join-Path $RepoRoot "services\blueprint-import\vectorizer_phase3.py"
if (-not (Test-Path $phase3)) {
    Write-Check "3-SIMPLE" "FAIL" "vectorizer_phase3.py not found"
} else {
    $hasSimple = Select-String -Path $phase3 -Pattern "def _simple_extraction" -Quiet
    $simpleLine = (Select-String -Path $phase3 -Pattern "def _simple_extraction").LineNumber
    $excludesUnknown = Select-String -Path $phase3 -Pattern "ContourCategory\.UNKNOWN" -Context 0,0 |
        Where-Object { $_.Line -match "excluded_categories" -or ($_.Context -eq $null -and $_.Line -match "excluded") }
    $exportBlock = Select-String -Path $phase3 -Pattern "excluded_categories = \[" -Context 0,6
    $exportExcludesUnknown = $false
    foreach ($b in $exportBlock) {
        $block = ($b.Context.PostContext -join "`n") + $b.Line
        if ($block -match "ContourCategory\.UNKNOWN") { $exportExcludesUnknown = $true }
    }
    if (-not $exportExcludesUnknown) {
        $def = Select-String -Path $phase3 -Pattern "if excluded_categories is None:" -Context 0,5
        foreach ($d in $def) {
            if (($d.Context.PostContext -join "`n") -match "UNKNOWN") { $exportExcludesUnknown = $true }
        }
    }
    $simplePutsUnknown = Select-String -Path $phase3 -Pattern "classified = \{ContourCategory\.UNKNOWN" -Quiet
    if ($hasSimple -and $exportExcludesUnknown -and $simplePutsUnknown) {
        Write-Check "3-SIMPLE" "PASS" "_simple_extraction at line $simpleLine; export excludes UNKNOWN; SIMPLE assigns UNKNOWN only — empty DXF risk CONFIRMED"
    } elseif ($hasSimple) {
        Write-Check "3-SIMPLE" "WARN" "_simple_extraction at $simpleLine; verify export/classified manually"
    } else {
        Write-Check "3-SIMPLE" "FAIL" "_simple_extraction not found"
    }
}

# --- 4. calibration_integration usage ---
Write-Host ""
Write-Host "--- 4. calibration_integration / EnhancedCalibrationPipeline ---" -ForegroundColor Yellow
$calHits = @()
Get-ChildItem -Path (Join-Path $RepoRoot "services") -Recurse -Filter "*.py" -ErrorAction SilentlyContinue | ForEach-Object {
    $m = Select-String -Path $_.FullName -Pattern "calibration_integration|EnhancedCalibrationPipeline|create_calibration_pipeline" -ErrorAction SilentlyContinue
    if ($m) {
        $rel = $_.FullName.Substring($RepoRoot.Length + 1)
        foreach ($hit in $m) {
            $calHits += "$rel`:$($hit.LineNumber)"
        }
    }
}
$routerUses = $calHits | Where-Object { $_ -match "calibration_router|phase2_router|constants\.py" }
$orchestratorUses = $calHits | Where-Object { $_ -match "blueprint_orchestrator|vectorize_router" }
if ($routerUses) {
    Write-Check "4-CALIBRATION" "PASS" "PARTIAL: calibration_router/constants/phase2 ($($routerUses.Count) refs); main vectorize orchestrator not wired"
    $routerUses | Select-Object -First 8 | ForEach-Object { Write-Host "    $_" }
} else {
    Write-Check "4-CALIBRATION" "FAIL" "No calibration_router/constants usage found"
}
if ($orchestratorUses) {
    Write-Host "  Main orchestrator/vectorize refs:"
    $orchestratorUses | ForEach-Object { Write-Host "    $_" }
} else {
    Write-Host "  (expected) No hits in blueprint_orchestrator / vectorize_router — MEDIUM debt, not orphan"
}

# --- 5. edge_to_dxf grouping fallback ---
Write-Host ""
Write-Host "--- 5. edge_to_dxf.py grouping fallback (~1294) ---" -ForegroundColor Yellow
$edge = Join-Path $RepoRoot "services\photo-vectorizer\edge_to_dxf.py"
if (Test-Path $edge) {
    $fallback = Select-String -Path $edge -Pattern "_isolate_body_contours|fallback_used|Grouping failed" -Context 2,2
    $hasExcept = Select-String -Path $edge -Pattern "except Exception" -Context 0,4 |
        Where-Object { $_.LineNumber -ge 1285 -and $_.LineNumber -le 1315 }
    if ($fallback) {
        $fbLine = ($fallback | Select-Object -First 1).LineNumber
        $usesException = ($hasExcept.Count -gt 0)
        $hasFallbackFlag = Select-String -Path $edge -Pattern "fallback_used=True" -Quiet
        if ($usesException -and $hasFallbackFlag) {
            Write-Check "5-FALLBACK" "PASS" "Exception path -> _isolate_body_contours near line $fbLine; fallback_used=True (add metrics in prod)"
        } else {
            Write-Check "5-FALLBACK" "WARN" "Fallback present near $fbLine; review logging/metrics"
        }
    } else {
        Write-Check "5-FALLBACK" "FAIL" "Expected fallback block not found"
    }
} else {
    Write-Check "5-FALLBACK" "FAIL" "edge_to_dxf.py not found"
}

# --- 6. TrainingDataCollector instantiated? ---
Write-Host ""
Write-Host "--- 6. TrainingDataCollector instantiation ---" -ForegroundColor Yellow
$tdcDef = Select-String -Path (Join-Path $RepoRoot "services") -Pattern "class TrainingDataCollector" -Recurse -ErrorAction SilentlyContinue
$tdcUse = Select-String -Path (Join-Path $RepoRoot "services") -Pattern "TrainingDataCollector\(" -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Line -notmatch "class TrainingDataCollector" }
if ($tdcUse.Count -eq 0) {
    Write-Check "6-TDC" "PASS" "TrainingDataCollector never instantiated (class only)"
} else {
    Write-Check "6-TDC" "FAIL" "Instantiation found:"
    $tdcUse | ForEach-Object { Write-Host "    $($_.Path):$($_.LineNumber)" }
}

# --- 7. FeedbackSystem record path ---
Write-Host ""
Write-Host "--- 7. FeedbackSystem usage ---" -ForegroundColor Yellow
$fbClass = Select-String -Path $phase3 -Pattern "class FeedbackSystem" -ErrorAction SilentlyContinue
$fbRecord = Select-String -Path (Join-Path $RepoRoot "services") -Pattern "record_classification|submit_correction|FeedbackSystem\(" -Recurse -ErrorAction SilentlyContinue
$recordCount = ($fbRecord | Where-Object { $_.Line -match "record_classification" }).Count
$submitCount = ($fbRecord | Where-Object { $_.Line -match "submit_correction" }).Count
$recCall = ($fbRecord | Where-Object { $_.Line -match "self\.feedback\.record_classification" }).Count
if ($recCall -ge 1 -and $submitCount -eq 0) {
    Write-Check "7-FEEDBACK" "PASS" "PARTIAL: record_classification called ($recCall); submit_correction call sites: 0 (DEAD intake)"
} else {
    Write-Check "7-FEEDBACK" "WARN" "record_classification refs: $recordCount; submit_correction call sites: $submitCount"
}

# --- 8. Dead code file existence ---
Write-Host ""
Write-Host "--- 8. Dead / abandoned files present ---" -ForegroundColor Yellow
$deadFiles = @(
    "services\photo-vectorizer\cognitive_extractor.py",
    "services\photo-vectorizer\cognitive_extraction_engine.py",
    "services\photo-vectorizer\extract_body_grid.py",
    "services\photo-vectorizer\extract_body_grid_v2.py",
    "services\photo-vectorizer\extract_body_grid_v3.py",
    "services\photo-vectorizer\extract_body_grid_v4.py",
    "services\photo-vectorizer\extract_body_grid_v5.py",
    "services\blueprint-import\vectorizer_phase2.py"
)
$found = 0
foreach ($df in $deadFiles) {
    $p = Join-Path $RepoRoot $df
    if (Test-Path $p) { $found++; $loc = (Get-Content $p).Count; Write-Host "  exists: $df ($loc lines)" }
}
Write-Check "8-DEAD" "PASS" "$found / $($deadFiles.Count) flagged files exist on disk"

# --- 9. Direct ezdxf bypass (boundary inventory) ---
Write-Host ""
Write-Host "--- 9. Direct ezdxf.new() bypass ---" -ForegroundColor Yellow
$ezdxfHits = Select-String -Path (Join-Path $RepoRoot "services\api") -Pattern "ezdxf\.new\(" -Recurse -ErrorAction SilentlyContinue
foreach ($h in $ezdxfHits) {
    $rel = $h.Path.Substring($RepoRoot.Length + 1)
    Write-Host "  $rel`:$($h.LineNumber)"
}
if ($ezdxfHits.Count -le 3) {
    Write-Check "9-EZDXF" "PASS" "$($ezdxfHits.Count) direct ezdxf.new() in services/api (expect ~2 per boundary doc)"
} else {
    Write-Check "9-EZDXF" "WARN" "$($ezdxfHits.Count) direct ezdxf.new() calls — review each"
}

# --- Summary ---
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "PASS: $Pass  WARN: $Warn  FAIL: $Fail"
if ($Fail -gt 0) {
    Write-Host "Some checks FAILED — reconcile with governance docs before remediation." -ForegroundColor Red
    exit 1
}
if ($Warn -gt 0) {
    Write-Host "Warnings are expected for nuanced claims (calibration routes, feedback partial)." -ForegroundColor Yellow
}
Write-Host "Verification complete." -ForegroundColor Green
exit 0
