# Delete 80%+ duplicate folders
$ErrorActionPreference = "Stop"

$foldersToDelete = @(
    "files (31)",
    "files (34)",
    "files (62)",
    "files (65)",
    "ToolBox_CurveLab_QoL_Patch",
    "ToolBox_CurveLab_DXF_Preflight_Patch",
    "ToolBox_CurveLab_Markdown_Report_Patch",
    "ToolBox_Workspace_Monorepo_Starter_PatchI_J",
    "luthiers_toolbox_vision_engine_bundle (3)",
    "ToolBox_Art_Studio_v16_0",
    "ToolBox_Art_Studio_v16_1_addons",
    "ToolBox_Art_Studio_v16_1_helical",
    "security_patch_dxf",
    "phase_bc_for_repo",
    "temp_patch",
    "Golden Path",
    "Integration_Patch_WiringFinish_v1",
    "Integration_Patch_WiringFinish_v2",
    "Governance_Code_Bundle"
)

Write-Host "Deleting 80%+ duplicate folders..." -ForegroundColor Yellow
$deleted = 0
$skipped = 0

foreach ($folder in $foldersToDelete) {
    if (Test-Path $folder) {
        Remove-Item -Path $folder -Recurse -Force
        Write-Host "  [DELETED] $folder" -ForegroundColor Green
        $deleted++
    } else {
        Write-Host "  [SKIP] $folder (not found)" -ForegroundColor DarkGray
        $skipped++
    }
}

Write-Host ""
Write-Host "Summary: $deleted deleted, $skipped skipped" -ForegroundColor Cyan
