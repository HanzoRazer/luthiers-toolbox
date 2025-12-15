# scripts/Setup-DevFirewall.ps1
# Developer Firewall Rules for Luthier's Tool Box Stack
# 
# This script creates firewall rules for all development ports used by:
# - RMOS API (8000, 8010)
# - ToolBox API (8100)
# - Vue Dev Server (5173)
# - Node/Alt servers (3000, 5000)
# - PostgreSQL (6543)
# - Additional dev ports
#
# Run as Administrator to create firewall rules.
# Usage: .\scripts\Setup-DevFirewall.ps1 [-Remove]

param(
    [switch]$Remove,
    [switch]$List,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Developer Mode ports for the full stack
$DEV_PORTS = @(
    @{ Port = 8000;  Name = "RMOS-API";           Desc = "FastAPI RMOS 2.0 main server" },
    @{ Port = 8010;  Name = "RMOS-Alt";           Desc = "RMOS alternate/test instance" },
    @{ Port = 8100;  Name = "ToolBox-API";        Desc = "Luthier's ToolBox API server" },
    @{ Port = 5173;  Name = "Vite-Dev";           Desc = "Vue/Vite development server" },
    @{ Port = 3000;  Name = "Node-Dev";           Desc = "Node.js dev server" },
    @{ Port = 5000;  Name = "Flask-Dev";          Desc = "Flask/Python alt server" },
    @{ Port = 6543;  Name = "PostgreSQL-Dev";     Desc = "PostgreSQL database" },
    @{ Port = 8080;  Name = "Proxy-Dev";          Desc = "Docker proxy / Nginx" },
    @{ Port = 8088;  Name = "Proxy-Alt";          Desc = "Alternate proxy port" }
)

$RULE_GROUP = "LuthierToolBox-DevMode"
$RULE_PREFIX = "LTB-Dev"

function Show-Help {
    Write-Host @"

Luthier's Tool Box - Developer Firewall Setup
==============================================

This script manages Windows Firewall rules for local development.

USAGE:
    .\Setup-DevFirewall.ps1           # Create all dev firewall rules
    .\Setup-DevFirewall.ps1 -Remove   # Remove all dev firewall rules  
    .\Setup-DevFirewall.ps1 -List     # List current dev rules status
    .\Setup-DevFirewall.ps1 -Help     # Show this help message

PORTS CONFIGURED:
"@
    foreach ($p in $DEV_PORTS) {
        Write-Host ("    {0,-5} - {1,-18} {2}" -f $p.Port, $p.Name, $p.Desc)
    }
    Write-Host @"

REQUIREMENTS:
    - Run as Administrator
    - Windows 10/11 or Windows Server

"@
}

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-DevRules {
    Get-NetFirewallRule -DisplayName "$RULE_PREFIX-*" -ErrorAction SilentlyContinue
}

function Show-RuleStatus {
    Write-Host "`n=== Luthier's ToolBox Developer Firewall Rules ===" -ForegroundColor Cyan
    Write-Host ""
    
    $existingRules = Get-DevRules
    
    foreach ($p in $DEV_PORTS) {
        $ruleName = "$RULE_PREFIX-$($p.Name)-$($p.Port)"
        $rule = $existingRules | Where-Object { $_.DisplayName -eq $ruleName }
        
        if ($rule) {
            $status = if ($rule.Enabled -eq "True") { "✓ ENABLED" } else { "○ DISABLED" }
            $color = if ($rule.Enabled -eq "True") { "Green" } else { "Yellow" }
        } else {
            $status = "✗ NOT FOUND"
            $color = "Red"
        }
        
        Write-Host ("{0,-5} {1,-18} [{2}]" -f $p.Port, $p.Name, $status) -ForegroundColor $color
    }
    Write-Host ""
}

function Add-DevFirewallRules {
    Write-Host "`n=== Creating Developer Firewall Rules ===" -ForegroundColor Cyan
    Write-Host "Rule Group: $RULE_GROUP`n"
    
    $created = 0
    $skipped = 0
    
    foreach ($p in $DEV_PORTS) {
        $ruleName = "$RULE_PREFIX-$($p.Name)-$($p.Port)"
        
        # Check if rule already exists
        $existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        
        if ($existing) {
            Write-Host "  [SKIP] $ruleName already exists" -ForegroundColor Yellow
            $skipped++
            continue
        }
        
        try {
            New-NetFirewallRule `
                -DisplayName $ruleName `
                -Description "$($p.Desc) - Luthier's ToolBox Developer Mode" `
                -Direction Inbound `
                -Action Allow `
                -Protocol TCP `
                -LocalPort $p.Port `
                -Group $RULE_GROUP `
                -Profile Domain,Private `
                -Enabled True | Out-Null
            
            Write-Host "  [OK] Created: $ruleName (port $($p.Port))" -ForegroundColor Green
            $created++
        }
        catch {
            Write-Host "  [FAIL] $ruleName - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`nSummary: $created created, $skipped skipped" -ForegroundColor Cyan
}

function Remove-DevFirewallRules {
    Write-Host "`n=== Removing Developer Firewall Rules ===" -ForegroundColor Cyan
    
    $rules = Get-DevRules
    
    if (-not $rules) {
        Write-Host "  No developer rules found to remove." -ForegroundColor Yellow
        return
    }
    
    $removed = 0
    foreach ($rule in $rules) {
        try {
            Remove-NetFirewallRule -DisplayName $rule.DisplayName -ErrorAction Stop
            Write-Host "  [REMOVED] $($rule.DisplayName)" -ForegroundColor Green
            $removed++
        }
        catch {
            Write-Host "  [FAIL] $($rule.DisplayName) - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`nRemoved $removed rules" -ForegroundColor Cyan
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

if ($List) {
    Show-RuleStatus
    exit 0
}

# Check admin privileges for create/remove operations
if (-not (Test-Administrator)) {
    Write-Host "`n[ERROR] This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again.`n" -ForegroundColor Yellow
    exit 1
}

if ($Remove) {
    Remove-DevFirewallRules
} else {
    Add-DevFirewallRules
}

Write-Host "`n=== Current Rule Status ===" -ForegroundColor Cyan
Show-RuleStatus

Write-Host "Done!" -ForegroundColor Green
