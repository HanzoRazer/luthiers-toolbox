# CarveCo/Vectric Tool Library Parser - PowerShell Version
# Extracts readable tool information from binary .tdb and .tool files

$script:toolTypes = @(
    'tpmDB_VBitTool',
    'tpmDB_BallnoseTool',
    'tpmDB_SlotDrillTool',
    'tpmDB_FlatConicalTool',
    'tpmDB_RadiusedConicalTool',
    'tpmDB_RadiusedSlotDrillTool',
    'tpmDB_RadiusedEngravingTool',
    'mcToolGroupMarker',
    'mcRadiusedEngravingTool',
    'ToolGroup'
)

function Extract-Strings {
    param([byte[]]$Data, [int]$MinLength = 5)
    
    $strings = @()
    $current = ""
    
    foreach ($byte in $Data) {
        # Printable ASCII range (space to ~)
        if ($byte -ge 32 -and $byte -le 126) {
            $current += [char]$byte
        }
        else {
            if ($current.Length -ge $MinLength) {
                $strings += $current
            }
            $current = ""
        }
    }
    
    if ($current.Length -ge $MinLength) {
        $strings += $current
    }
    
    return $strings
}

function Find-ToolMarkers {
    param([byte[]]$Data)
    
    $markers = @()
    
    foreach ($toolType in $script:toolTypes) {
        $searchBytes = [System.Text.Encoding]::ASCII.GetBytes($toolType)
        
        for ($i = 0; $i -lt ($Data.Length - $searchBytes.Length); $i++) {
            $match = $true
            for ($j = 0; $j -lt $searchBytes.Length; $j++) {
                if ($Data[$i + $j] -ne $searchBytes[$j]) {
                    $match = $false
                    break
                }
            }
            
            if ($match) {
                $markers += @{
                    Position = $i
                    Type = $toolType
                }
            }
        }
    }
    
    return $markers | Sort-Object -Property Position
}

function Extract-ToolInfo {
    param([byte[]]$Section)
    
    $strings = Extract-Strings -Data $Section
    
    # Filter out internal markers
    $strings = $strings | Where-Object { 
        $_ -notmatch 'tpmDB_' -and 
        $_ -notmatch 'mcTool' -and 
        $_ -notmatch 'utParameter' -and
        $_.Length -gt 0
    }
    
    $toolName = ""
    $url = ""
    $notes = ""
    
    foreach ($str in $strings) {
        if ($str -match 'http') {
            $url = $str
        }
        elseif ($str.Length -gt $toolName.Length -and 
                ($str -match 'Shank|Bit|Tool|Router|#|mm|Deg|Radius|Dia')) {
            $toolName = $str
        }
    }
    
    return @{
        Name = $toolName
        URL = $url
        Notes = $notes
        Strings = ($strings | Select-Object -First 5)
    }
}

function Parse-ToolFile {
    param([string]$FilePath)
    
    Write-Host "`nParsing: $FilePath" -ForegroundColor Green
    
    if (-not (Test-Path $FilePath)) {
        Write-Host "  File not found!" -ForegroundColor Red
        return @()
    }
    
    $data = [System.IO.File]::ReadAllBytes($FilePath)
    
    # Find all tool markers
    $markers = Find-ToolMarkers -Data $data
    
    if ($markers.Count -eq 0) {
        Write-Host "  No tool markers found!" -ForegroundColor Yellow
        return @()
    }
    
    Write-Host "  Found $($markers.Count) tool markers" -ForegroundColor Cyan
    
    $tools = @()
    
    for ($i = 0; $i -lt $markers.Count; $i++) {
        $startPos = $markers[$i].Position
        $endPos = if ($i + 1 -lt $markers.Count) { $markers[$i + 1].Position } else { $data.Length }
        
        # Skip small sections
        if (($endPos - $startPos) -lt 20) {
            continue
        }
        
        $section = $data[$startPos..($endPos - 1)]
        $toolInfo = Extract-ToolInfo -Section $section
        
        if ($toolInfo.Name) {
            $tools += [PSCustomObject]@{
                Type = $markers[$i].Type
                Name = $toolInfo.Name
                URL = $toolInfo.URL
                Notes = $toolInfo.Notes
                AdditionalInfo = ($toolInfo.Strings -join ' | ')
            }
        }
    }
    
    Write-Host "  Extracted $($tools.Count) tools" -ForegroundColor Cyan
    return $tools
}

function Write-ToolCSV {
    param([array]$Tools, [string]$OutputFile)
    
    if ($Tools.Count -eq 0) {
        Write-Host "  No tools to write" -ForegroundColor Yellow
        return
    }
    
    $Tools | Export-Csv -Path $OutputFile -NoTypeInformation -Encoding UTF8
    Write-Host "  -> Created: $OutputFile" -ForegroundColor Green
}

# Main execution
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$conversions = @(
    @{
        Input = Join-Path $scriptDir "Two-Moose-Set-CarveCo-V1.2\Two Moose Set-CarveCo-V1.2.txt"
        Output = Join-Path $scriptDir "Two-Moose-Set-CarveCo-V1.2\Two Moose Set-CarveCo-V1.2-parsed.csv"
    },
    @{
        Input = Join-Path $scriptDir "Bits-Bits-CarveCo-Complete-V1.2\Bits Bits CarveCo Complete-V1.2.txt"
        Output = Join-Path $scriptDir "Bits-Bits-CarveCo-Complete-V1.2\Bits Bits CarveCo Complete-V1.2-parsed.csv"
    },
    @{
        Input = Join-Path $scriptDir "Myers-Woodshop-Set-CarveCo-V1.2\Myers Woodshop Set-CarveCo-V1.2.txt"
        Output = Join-Path $scriptDir "Myers-Woodshop-Set-CarveCo-V1.2\Myers Woodshop Set-CarveCo-V1.2-parsed.csv"
    },
    @{
        Input = Join-Path $scriptDir "Amana-Tool-Vectric.tool.txt"
        Output = Join-Path $scriptDir "Amana-Tool-Vectric.tool-parsed.csv"
    }
)

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "CarveCo/Vectric Tool Library Parser" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

foreach ($conversion in $conversions) {
    $tools = Parse-ToolFile -FilePath $conversion.Input
    
    if ($tools.Count -gt 0) {
        Write-ToolCSV -Tools $tools -OutputFile $conversion.Output
    }
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "Conversion complete!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
