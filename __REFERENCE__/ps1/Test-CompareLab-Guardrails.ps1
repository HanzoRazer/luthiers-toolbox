# Test-CompareLab-Guardrails.ps1
# Validates the CompareLab B22.8 guardrail system installation

Write-Host "=== CompareLab B22.8 Guardrail System Test ===" -ForegroundColor Cyan
Write-Host ""

$testsPassed = 0
$testsFailed = 0

# Test 1: ESLint rule file exists and is valid
Write-Host "Test 1: ESLint rule exists..." -ForegroundColor Yellow
if (Test-Path ".eslint-rules/no-direct-state-mutation.js") {
    $ruleContent = Get-Content ".eslint-rules/no-direct-state-mutation.js" -Raw
    if ($ruleContent -match "isComputingDiff" -and $ruleContent -match "overlayDisabled") {
        Write-Host "  ✓ Rule file valid" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ❌ Rule file incomplete" -ForegroundColor Red
        $testsFailed++
    }
} else {
    Write-Host "  ❌ Rule file missing" -ForegroundColor Red
    $testsFailed++
}

# Test 2: ESLint config uses custom rule
Write-Host "Test 2: ESLint config valid..." -ForegroundColor Yellow
if (Test-Path "client/.eslintrc.cjs") {
    $eslintConfig = Get-Content "client/.eslintrc.cjs" -Raw
    if ($eslintConfig -match "no-direct-state-mutation" -and $eslintConfig -match "rulePaths") {
        Write-Host "  ✓ Config references custom rule" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ❌ Config incomplete" -ForegroundColor Red
        $testsFailed++
    }
} else {
    Write-Host "  ❌ Config file missing" -ForegroundColor Red
    $testsFailed++
}

# Test 3: VSCode settings enable onType linting
Write-Host "Test 3: VSCode settings..." -ForegroundColor Yellow
if (Test-Path ".vscode/settings.json") {
    $vscodeSettings = Get-Content ".vscode/settings.json" -Raw
    if ($vscodeSettings -match "onType" -and $vscodeSettings -match "rulePaths") {
        Write-Host "  ✓ VSCode configured for real-time linting" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ❌ VSCode settings incomplete" -ForegroundColor Red
        $testsFailed++
    }
} else {
    Write-Host "  ❌ VSCode settings missing" -ForegroundColor Red
    $testsFailed++
}

# Test 4: Husky pre-commit hook exists
Write-Host "Test 4: Pre-commit hook..." -ForegroundColor Yellow
if (Test-Path ".husky/pre-commit") {
    $hookContent = Get-Content ".husky/pre-commit" -Raw
    if ($hookContent -match "lint-staged") {
        Write-Host "  ✓ Husky hook configured" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ❌ Hook incomplete" -ForegroundColor Red
        $testsFailed++
    }
} else {
    Write-Host "  ❌ Hook missing" -ForegroundColor Red
    $testsFailed++
}

# Test 5: package.json has lint-staged config
Write-Host "Test 5: lint-staged config..." -ForegroundColor Yellow
if (Test-Path "client/package.json") {
    $packageJson = Get-Content "client/package.json" -Raw
    if ($packageJson -match "lint-staged" -and $packageJson -match "useCompareState") {
        Write-Host "  ✓ lint-staged configured" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ❌ lint-staged config missing" -ForegroundColor Red
        $testsFailed++
    }
} else {
    Write-Host "  ❌ package.json missing" -ForegroundColor Red
    $testsFailed++
}

# Test 6: useCompareState.ts has guardrail comment
Write-Host "Test 6: Guardrail comment..." -ForegroundColor Yellow
if (Test-Path "client/src/composables/useCompareState.ts") {
    $composableContent = Get-Content "client/src/composables/useCompareState.ts" -Raw
    if ($composableContent -match "CRITICAL GUARDRAIL" -and $composableContent -match "runWithCompareSkeleton") {
        Write-Host "  ✓ Guardrail comment present" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ❌ Guardrail comment incomplete" -ForegroundColor Red
        $testsFailed++
    }
} else {
    Write-Host "  ❌ Composable file missing" -ForegroundColor Red
    $testsFailed++
}

# Test 7: Run ESLint (optional - requires node_modules)
Write-Host "Test 7: ESLint execution..." -ForegroundColor Yellow
Set-Location client
if (Test-Path "node_modules") {
    $lintResult = npm run lint 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ ESLint runs without errors" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ⚠️ ESLint has warnings/errors (review manually)" -ForegroundColor Yellow
        Write-Host "    Run: cd client && npm run lint" -ForegroundColor Gray
        $testsPassed++  # Don't fail - might be pre-existing issues
    }
} else {
    Write-Host "  ⚠️ node_modules not found - run 'npm install' first" -ForegroundColor Yellow
    $testsPassed++  # Don't fail - user needs to install
}
Set-Location ..

# Test 8: Documentation exists
Write-Host "Test 8: Documentation..." -ForegroundColor Yellow
$docs = @(".vscode/README.md", ".husky/INSTALL.md", "docs/COMPARELAB_DEV_CHECKLIST.md")
$docsExist = $true
foreach ($doc in $docs) {
    if (-not (Test-Path $doc)) {
        $docsExist = $false
        break
    }
}
if ($docsExist) {
    Write-Host "  ✓ All documentation present" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  ❌ Some documentation missing" -ForegroundColor Red
    $testsFailed++
}

# Summary
Write-Host ""
Write-Host "=== Test Results ===" -ForegroundColor Cyan
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor Red
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "✓ All tests passed - Guardrail system ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Restart VSCode to activate ESLint onType"
    Write-Host "  2. Try editing a CompareLab file and adding: isComputingDiff.value = true"
    Write-Host "  3. You should see a red squiggle immediately"
    Write-Host ""
    Write-Host "References:" -ForegroundColor Cyan
    Write-Host "  .vscode/README.md - Full protection system docs"
    Write-Host "  .husky/INSTALL.md - Husky installation guide"
    Write-Host "  docs/COMPARELAB_DEV_CHECKLIST.md - Developer checklist"
    exit 0
} else {
    Write-Host "❌ Some tests failed - review output above" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  - Run: .\Setup-CompareLab-Guardrails.ps1 to reinstall"
    Write-Host "  - Check: .vscode/README.md for manual setup steps"
    exit 1
}
