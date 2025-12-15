<#
.SYNOPSIS
    Developer Mode Firewall Setup
.DESCRIPTION
    Creates firewall rules for the Luthier's Tool Box development stack.
    Opens ports for RMOS, ToolBox API, Saw Lab, and frontend dev servers.
    
    Port allocation:
    - 8000: Main FastAPI (production)
    - 8010: RMOS 2.0 development server
    - 5173: Vite dev server (Vue frontend)
    - 3000: Alternative frontend port
    - 5000: Flask/alternative backend
    - 6543: PostgreSQL (if needed)
    - 8100: Saw Lab secondary API

.PARAMETER Action
    'Enable' to create rules, 'Disable' to remove them, 'Status' to check.

.EXAMPLE
    # Run as Administrator to create firewall rules
    .\Enable-DevFirewall.ps1 -Action Enable

    # Check current status
    .\Enable-DevFirewall.ps1 -Action Status

    # Remove all dev rules
    .\Enable-DevFirewall.ps1 -Action Disable

.NOTES
    Requires Administrator privileges to modify firewall rules.
    Rule group: "Luthiers-ToolBox-Dev"
#>

[CmdletBinding()]
param(
    [ValidateSet("Enable", "Disable", "Status")]
    [string]$Action = "Status"
)

$ErrorActionPreference = "Stop"

# Developer mode port configuration
$DevPorts = @{
    8000  = "FastAPI Main"
    8010  = "RMOS 2.0 Dev"
    5173  = "Vite Frontend"
    3000  = "Alt Frontend"
    5000  = "Flask Backend"
    6543  = "PostgreSQL"
    8100  = "Saw Lab API"
}

$RuleGroupName = "Luthiers-ToolBox-Dev"
$RulePrefix = "LTB-Dev-"

function Test-Administrator {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-DevFirewallRules {
    Get-NetFirewallRule -DisplayName "$RulePrefix*" -ErrorAction SilentlyContinue
}

function Show-Status {
    Write-Host "`n=== Luthier's ToolBox - Developer Firewall Status ===" -ForegroundColor Cyan
    Write-Host "Rule Group: $RuleGroupName`n"

    $existingRules = Get-DevFirewallRules

    if ($existingRules) {
        Write-Host "Configured Rules:" -ForegroundColor Green
        foreach ($port in $DevPorts.Keys | Sort-Object) {
            $ruleName = "$RulePrefix$port"
            $rule = $existingRules | Where-Object { $_.DisplayName -eq $ruleName }
            
            if ($rule) {
                $status = if ($rule.Enabled -eq "True") { "✓ OPEN" } else { "✗ DISABLED" }
                $color = if ($rule.Enabled -eq "True") { "Green" } else { "Yellow" }
            } else {
                $status = "— NOT CONFIGURED"
                $color = "Gray"
            }
            
            Write-Host "  Port $port ($($DevPorts[$port])): " -NoNewline
            Write-Host $status -ForegroundColor $color
        }
    } else {
        Write-Host "No developer firewall rules configured." -ForegroundColor Yellow
        Write-Host "Run with -Action Enable to create rules." -ForegroundColor Gray
    }

    Write-Host ""
}

function Enable-DevFirewall {
    if (-not (Test-Administrator)) {
        Write-Host "ERROR: Administrator privileges required." -ForegroundColor Red
        Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
        return
    }

    Write-Host "`n=== Enabling Developer Firewall Rules ===" -ForegroundColor Cyan
    Write-Host "Rule Group: $RuleGroupName`n"

    $created = 0
    $skipped = 0

    foreach ($port in $DevPorts.Keys | Sort-Object) {
        $ruleName = "$RulePrefix$port"
        $description = "$($DevPorts[$port]) - Luthier's ToolBox Development"

        $existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

        if ($existing) {
            Write-Host "  Port $port : Already exists (skipping)" -ForegroundColor Gray
            $skipped++
        } else {
            try {
                New-NetFirewallRule `
                    -DisplayName $ruleName `
                    -Description $description `
                    -Group $RuleGroupName `
                    -Direction Inbound `
                    -Action Allow `
                    -Protocol TCP `
                    -LocalPort $port `
                    -Profile Private, Domain `
                    -Enabled True | Out-Null

                Write-Host "  Port $port : " -NoNewline
                Write-Host "CREATED ($($DevPorts[$port]))" -ForegroundColor Green
                $created++
            } catch {
                Write-Host "  Port $port : " -NoNewline
                Write-Host "FAILED - $_" -ForegroundColor Red
            }
        }
    }

    Write-Host "`nSummary: $created created, $skipped skipped" -ForegroundColor Cyan
    Write-Host "Developer Mode firewall rules are now active.`n" -ForegroundColor Green
}

function Disable-DevFirewall {
    if (-not (Test-Administrator)) {
        Write-Host "ERROR: Administrator privileges required." -ForegroundColor Red
        Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
        return
    }

    Write-Host "`n=== Disabling Developer Firewall Rules ===" -ForegroundColor Cyan

    $rules = Get-DevFirewallRules
    $removed = 0

    if ($rules) {
        foreach ($rule in $rules) {
            try {
                Remove-NetFirewallRule -DisplayName $rule.DisplayName
                Write-Host "  Removed: $($rule.DisplayName)" -ForegroundColor Yellow
                $removed++
            } catch {
                Write-Host "  Failed to remove: $($rule.DisplayName) - $_" -ForegroundColor Red
            }
        }
        Write-Host "`n$removed rule(s) removed." -ForegroundColor Cyan
    } else {
        Write-Host "No developer firewall rules found to remove." -ForegroundColor Gray
    }

    Write-Host ""
}

# Main execution
switch ($Action) {
    "Enable"  { Enable-DevFirewall }
    "Disable" { Disable-DevFirewall }
    "Status"  { Show-Status }
}
