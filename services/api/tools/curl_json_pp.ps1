<#
.SYNOPSIS
  JSON pretty-printer for API testing on Windows.
  Can fetch from a URL or read from STDIN pipe.

.DESCRIPTION
  Utility script for formatting JSON responses from the Luthier's Tool Box API.
  Useful for debugging and manual testing of endpoints.

.PARAMETER Url
  Optional URL to fetch JSON from (uses curl.exe)

.EXAMPLES
  # Pretty-print from URL
  .\curl_json_pp.ps1 -Url "http://127.0.0.1:8000/api/cam_gcode/posts_v155"
  
  # Pipe curl output
  curl.exe -s http://127.0.0.1:8000/health | .\curl_json_pp.ps1
  
  # Pipe Invoke-RestMethod output
  Invoke-RestMethod http://127.0.0.1:8000/api/cam_gcode/smoke/posts | ConvertTo-Json -Depth 10
#>

Param(
    [string]$Url,
    [int]$Depth = 10
)

function Format-JsonPretty {
    Param([string]$JsonString)
    
    try {
        $obj = $JsonString | ConvertFrom-Json -ErrorAction Stop
        $obj | ConvertTo-Json -Depth $Depth
    } catch {
        # Fallback to raw output if not valid JSON
        Write-Host "⚠ Input is not valid JSON, displaying raw:" -ForegroundColor Yellow
        $JsonString
    }
}

if ($Url) {
    # Fetch from URL using curl
    Write-Host "==> Fetching: $Url" -ForegroundColor Cyan
    
    $response = & curl.exe -s $Url 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ curl failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
    
    Format-JsonPretty $response | Write-Output
    
} else {
    # Read from STDIN
    if ([Console]::IsInputRedirected) {
        $inputText = [Console]::In.ReadToEnd()
        Format-JsonPretty $inputText | Write-Output
    } else {
        Write-Host "Usage:" -ForegroundColor Cyan
        Write-Host "  .\curl_json_pp.ps1 -Url <url>" -ForegroundColor Gray
        Write-Host "  curl.exe <url> | .\curl_json_pp.ps1" -ForegroundColor Gray
        Write-Host "`nExamples:" -ForegroundColor Cyan
        Write-Host '  .\curl_json_pp.ps1 -Url "http://127.0.0.1:8000/health"' -ForegroundColor Gray
        Write-Host '  curl.exe -s http://127.0.0.1:8000/api/cam_gcode/posts_v155 | .\curl_json_pp.ps1' -ForegroundColor Gray
        exit 1
    }
}
