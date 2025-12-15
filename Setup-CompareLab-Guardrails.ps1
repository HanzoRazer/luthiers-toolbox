# Setup-CompareLab-Guardrails.ps1
# Installs and configures the CompareLab B22.8 4-layer protection system

Write-Host "=== CompareLab B22.8 Guardrail System Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install dependencies
Write-Host "Step 1: Installing Husky + lint-staged..." -ForegroundColor Yellow
Set-Location client
npm install --save-dev husky@^8.0.3 lint-staged@^15.0.2

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ npm install failed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 2: Initialize Husky
Write-Host "Step 2: Initializing Husky..." -ForegroundColor Yellow
npm run prepare

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ npm run prepare failed, trying manual setup..." -ForegroundColor Yellow
    npx husky install
}

Write-Host "✓ Husky initialized" -ForegroundColor Green
Write-Host ""

# Step 3: Verify files exist
Write-Host "Step 3: Verifying installation..." -ForegroundColor Yellow
Set-Location ..

$requiredFiles = @(
    ".eslint-rules/no-direct-state-mutation.js",
    ".eslint-rules/index.js",
    ".vscode/settings.json",
    ".vscode/README.md",
    ".husky/pre-commit",
    ".husky/INSTALL.md",
    "client/.eslintrc.cjs",
    "client/src/composables/useCompareState.ts"
)

$allExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file (missing)" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host ""
    Write-Host "❌ Some required files are missing" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ All files present" -ForegroundColor Green
Write-Host ""

# Step 4: Make pre-commit hook executable (Git Bash compatibility)
Write-Host "Step 4: Configuring Git hooks..." -ForegroundColor Yellow
git config core.hooksPath .husky
Write-Host "✓ Git hooks configured" -ForegroundColor Green
Write-Host ""

# Step 5: Summary
Write-Host "=== Installation Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "4-Layer Protection System Active:" -ForegroundColor Green
Write-Host "  Layer 1: Inline comments in useCompareState.ts"
Write-Host "  Layer 2: ESLint rule (onType in VSCode)"
Write-Host "  Layer 3: Unit tests (40+ tests)"
Write-Host "  Layer 4: Pre-commit hooks (Husky + lint-staged)"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Restart VSCode to activate ESLint onType"
Write-Host "  2. Run test: .\Test-CompareLab-Guardrails.ps1"
Write-Host "  3. See: .vscode/README.md for full documentation"
Write-Host ""
Write-Host "To test manually:" -ForegroundColor Cyan
Write-Host "  cd client"
Write-Host "  npm run lint"
Write-Host "  npm run test -- useCompareState"
