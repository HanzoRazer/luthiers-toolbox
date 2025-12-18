# Delete WiringWorkbench-related folders (already integrated)
$folders = @(
    "WiringWorkbench_Docs_Patch_v1",
    "WiringWorkbench_Enhancements_v1",
    "Luthiers_Tool_Box_Addons_WiringWorkbench_FinishPlanner_v1"
)

foreach ($f in $folders) {
    if (Test-Path $f) {
        Remove-Item $f -Recurse -Force
        Write-Host "[DELETED] $f" -ForegroundColor Green
    } else {
        Write-Host "[SKIP] $f not found" -ForegroundColor DarkGray
    }
}
