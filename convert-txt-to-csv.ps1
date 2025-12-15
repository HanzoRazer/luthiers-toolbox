# Convert TXT to MS-DOS CSV
# Usage: .\convert-txt-to-csv.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Define input/output file mappings
$conversions = @(
    @{
        Input = Join-Path $scriptDir "Two-Moose-Set-CarveCo-V1.2\Two Moose Set-CarveCo-V1.2.txt"
        Output = Join-Path $scriptDir "Two-Moose-Set-CarveCo-V1.2\Two Moose Set-CarveCo-V1.2.csv"
    },
    @{
        Input = Join-Path $scriptDir "Bits-Bits-CarveCo-Complete-V1.2\Bits Bits CarveCo Complete-V1.2.txt"
        Output = Join-Path $scriptDir "Bits-Bits-CarveCo-Complete-V1.2\Bits Bits CarveCo Complete-V1.2.csv"
    },
    @{
        Input = Join-Path $scriptDir "Myers-Woodshop-Set-CarveCo-V1.2\Myers Woodshop Set-CarveCo-V1.2.txt"
        Output = Join-Path $scriptDir "Myers-Woodshop-Set-CarveCo-V1.2\Myers Woodshop Set-CarveCo-V1.2.csv"
    },
    @{
        Input = Join-Path $scriptDir "Amana-Tool-Vectric.tool.txt"
        Output = Join-Path $scriptDir "Amana-Tool-Vectric.tool.csv"
    }
)

foreach ($conversion in $conversions) {
    $inputFile = $conversion.Input
    $outputFile = $conversion.Output
    
    if (Test-Path $inputFile) {
        Write-Host "Converting: $inputFile" -ForegroundColor Green
        
        # Read content and replace tabs with commas
        Get-Content $inputFile -Raw |
            ForEach-Object { $_ -replace '\t', ',' } |
            Out-File $outputFile -Encoding ASCII -NoNewline
        
        Write-Host "  -> Created: $outputFile" -ForegroundColor Cyan
    } else {
        Write-Host "File not found: $inputFile" -ForegroundColor Red
    }
}

Write-Host "`nConversion complete!" -ForegroundColor Green
