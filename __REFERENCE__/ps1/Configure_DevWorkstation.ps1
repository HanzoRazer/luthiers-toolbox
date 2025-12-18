<#
.SYNOPSIS
  Configure a Windows developer workstation for local web/API development.

.DESCRIPTION
  - Verifies the script is running as Administrator.
  - Sets execution policy for the current user to RemoteSigned.
  - Creates inbound firewall rules for common dev ports (TCP).
  - Restricts rules to Private/Domain profiles (not Public).
  - Registers HTTP URL ACLs for ports 8000 and 8100 to avoid "access denied" issues.

.NOTES
  Save as: Configure-DevWorkstation.ps1
  Run from an elevated PowerShell prompt:
      PS> Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
      PS> .\Configure-DevWorkstation.ps1
#>

Write-Host "=== Developer Workstation Configuration Script ===" -ForegroundColor Cyan

# -------------------------------
# 1. Ensure we are running as Administrator
# -------------------------------
$windowsIdentity  = [Security.Principal.WindowsIdentity]::GetCurrent()
$windowsPrincipal = New-Object Security.Principal.WindowsPrincipal($windowsIdentity)
$adminRole        = [Security.Principal.WindowsBuiltInRole]::Administrator

if (-not $windowsPrincipal.IsInRole($adminRole)) {
    Write-Host "[ERROR] This script must be run as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell and choose 'Run as administrator', then re-run this script." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Running with Administrator privileges." -ForegroundColor Green

# -------------------------------
# 2. Set execution policy for current user
# -------------------------------
try {
    $currentPolicy = Get-ExecutionPolicy -Scope CurrentUser -ErrorAction SilentlyContinue
    if ($currentPolicy -ne 'RemoteSigned') {
        Write-Host "[INFO] Setting execution policy for CurrentUser to RemoteSigned..." -ForegroundColor Yellow
        Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
        Write-Host "[OK] Execution policy set to RemoteSigned for CurrentUser." -ForegroundColor Green
    }
    else {
        Write-Host "[OK] Execution policy for CurrentUser is already RemoteSigned." -ForegroundColor Green
    }
}
catch {
    Write-Host "[WARN] Could not set execution policy for CurrentUser: $($_.Exception.Message)" -ForegroundColor Yellow
}

# -------------------------------
# 3. Define common dev ports
#    Adjust this list as needed.
# -------------------------------
$devPorts = @(
    8000,  # Uvicorn / FastAPI
    8100,  # Alternate Uvicorn
    3000,  # Node / React
    4173,  # Vite preview
    5173,  # Vite dev server
    5000,  # Flask / misc
    5432,  # PostgreSQL
    6379   # Redis
)

Write-Host "[INFO] Creating firewall rules for dev ports: $($devPorts -join ', ')" -ForegroundColor Cyan

# Helper: create a firewall rule if it doesn't already exist
function New-DevFirewallRule {
    param(
        [int]$Port
    )

    $ruleName = "DevPort-$Port"

    $existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        Write-Host "[SKIP] Firewall rule '$ruleName' already exists." -ForegroundColor DarkYellow
        return
    }

    try {
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalPort $Port `
            -Profile Domain,Private `
            -Enabled True | Out-Null

        Write-Host "[OK] Created firewall rule '$ruleName' for TCP port $Port (Domain/Private only)." -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Failed to create firewall rule for port $Port: $($_.Exception.Message)" -ForegroundColor Red
    }
}

foreach ($p in $devPorts) {
    New-DevFirewallRule -Port $p
}

# -------------------------------
# 4. Register HTTP URL ACLs to avoid WinError 10013 on ports 8000, 8100
# -------------------------------
Write-Host "[INFO] Registering HTTP URL ACLs for ports 8000 and 8100..." -ForegroundColor Cyan

function Ensure-HttpUrlAcl {
    param(
        [string]$Url
    )

    # Example URL: "http://+:8000/"
    $existing = & netsh http show urlacl url=$Url 2>$null

    if ($LASTEXITCODE -eq 0 -and $existing -match 'Reserved URL') {
        Write-Host "[SKIP] URL ACL already exists for $Url" -ForegroundColor DarkYellow
        return
    }

    # You can change 'Everyone' to a specific user if desired
    $user = "Everyone"

    Write-Host "[INFO] Adding URL ACL for $Url (user: $user)..." -ForegroundColor Yellow
    & netsh http add urlacl url=$Url user=$user

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] URL ACL added for $Url" -ForegroundColor Green
    }
    else {
        Write-Host "[WARN] Failed to add URL ACL for $Url (exit code $LASTEXITCODE)" -ForegroundColor Yellow
    }
}

Ensure-HttpUrlAcl -Url "http://+:8000/"
Ensure-HttpUrlAcl -Url "http://+:8100/"

# -------------------------------
# 5. Show active connection profiles (so you know if you're on Public)
# -------------------------------
Write-Host "`n[INFO] Current network connection profiles:" -ForegroundColor Cyan
Get-NetConnectionProfile | Select-Object Name, InterfaceAlias, NetworkCategory | Format-Table

Write-Host @"
NOTE:
- For trusted home/office networks, ensure NetworkCategory is 'Private' (not 'Public').
  You can change it in Settings → Network & Internet.
- The firewall rules we created only apply to Domain/Private networks.
"@ -ForegroundColor Yellow

# -------------------------------
# 6. Summary
# -------------------------------
Write-Host "`n=== Configuration Complete ===" -ForegroundColor Cyan
Write-Host "What was done:" -ForegroundColor White
Write-Host "  - Verified Administrator privileges." -ForegroundColor White
Write-Host "  - Set execution policy for CurrentUser to RemoteSigned (if needed)." -ForegroundColor White
Write-Host "  - Created inbound firewall rules for dev ports: $($devPorts -join ', ') (Domain/Private only)." -ForegroundColor White
Write-Host "  - Registered HTTP URL ACLs for http://+:8000/ and http://+:8100/ (to avoid access denied errors)." -ForegroundColor White
Write-Host ""
Write-Host "You can now run local dev servers (Uvicorn, Vite, Node, etc.) much more reliably on your Private network." -ForegroundColor Green
