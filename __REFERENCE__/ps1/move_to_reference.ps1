# Move reference folders to __REFERENCE__/
$ErrorActionPreference = "Stop"

# Create __REFERENCE__ if it doesn't exist
if (-not (Test-Path "__REFERENCE__")) {
    New-Item -ItemType Directory -Path "__REFERENCE__" | Out-Null
    Write-Host "Created __REFERENCE__/" -ForegroundColor Cyan
}

$foldersToMove = @(
    # Instrument projects
    "Luthiers Tool Box",
    "Guitar Design HTML app",
    "Archtop",
    "Stratocaster",
    "Lutherier Project",
    "OM Project",
    "Soprano Ukuele",

    # External tools
    "vibe-blueprintanalyzer-main",

    # Art Studio legacy
    "ToolBox_Art_Studio-repo",

    # Script archives
    "ToolBox_All_Scripts_Consolidated",
    "ToolBox_All_Scripts_Consolidated (2)",
    "ToolBox_All_Scripts_Consolidated_20251104_082246",
    "ToolBox_All_Scripts_Consolidated_extracted",
    "ToolBox_All_Scripts_Consolidated_v2",
    "ToolBox_All_Scripts_Consolidated_v4",
    "ToolBox_All_Scripts_Consolidated_v6",
    "ToolBox_All_Scripts_Consolidated_v7",
    "ToolBox_Scripts_Recovered",
    "ToolBox_Scripts_Recovered_2",
    "ToolBox_Scripts_Recovered_2_extracted",

    # Patch folders
    "ToolBox_CurveMath_Patch_v1",
    "ToolBox_CurveMath_Patch_v2_DXF_and_Tests",
    "ToolBox_DXF_JSON_Comment_Patch",
    "ToolBox_Monorepo_Patch_I1_2_3",
    "ToolBox_PatchA_Server_ExportHistory",
    "ToolBox_PatchB_CI",
    "ToolBox_PatchC_Client_QoL",
    "ToolBox_PatchD_SVG_Layers_Tolerance_Preview",
    "ToolBox_PatchE_DXFLayers_SVG_CI",
    "ToolBox_PatchF2_CAM_Roughing_Embedded_Preflight",
    "ToolBox_PatchG_Units_LeadIn_TabsEditor",
    "ToolBox_PatchH0_CAM_Neutral_Export",
    "ToolBox_PatchH_Adaptive_Pocketing",
    "ToolBox_PatchI1_Sim_Animated_Playback",
    "ToolBox_PatchI1_Sim_Animated_Playback (1)",
    "ToolBox_PatchI_Simulation_Validation",
    "ToolBox_PatchJ1_Post_Injection",
    "ToolBox_PatchJ2_Post_All",
    "ToolBox_PatchJ_Tool_Library_Post_Profiles",
    "ToolBox_PatchJ_Tool_Library_Post_Profiles (1)",
    "ToolBox_Patch_I1_2_Arcs_TimeScrub",
    "ToolBox_Patch_I1_2_Arcs_TimeScrub_FULL",
    "ToolBox_Patch_I1_3_Worker_Render",
    "ToolBox_Patch_I1_3_Worker_Render_FULL",
    "ToolBox_Patch_N01_roughing_post_min",
    "ToolBox_Patch_N03_standard",
    "ToolBox_Patch_N04c_helpers",
    "ToolBox_Patch_N04_router_snippet",
    "ToolBox_Patch_N05_fanuc_haas",
    "ToolBox_Patch_N06_post_modal_cycles",
    "ToolBox_Patch_N07_cycles_ui_drill",
    "ToolBox_Patch_N08_retract_tools_patterns",
    "ToolBox_Patch_N09_probe_patterns_svg",
    "ToolBox_Patch_N0_followup",
    "ToolBox_Patch_N0_SmartPost_Scaffold",
    "ToolBox_Patch_N10_CAM_Essentials",
    "ToolBox_Patch_N12_machine_tool_tables",
    "ToolBox_Patch_N14_unified_route_adaptive_preview_post_editor",
    "ToolBox_Patch_N15_gcode_backplot_time",
    "ToolBox_Patch_N16_adaptive_spiral_trochoid_bench",
    "ToolBox_Patch_N17_polyclip_arc_link_min_engagement",
    "ToolBox_Patch_N_CAMEssentials_Rollup",
    "ToolBox_Patch_N_Rollup",
    "ToolBox_PathDoctor_LongPaths",

    # Tool databases
    "Bits-Bits-CarveCo-Complete-V1.2",
    "Carveco Tool Database table-230307",
    "Fusion360 Tool Database",
    "Myers-Woodshop-Set-CarveCo-V1.2",
    "SainSmart Bit Table 3018",
    "SainSmart Bits GWizard(V3.0)",
    "Two-Moose-Set-CarveCo-V1.2",
    "MUST-Be-UNZIPPED-IDC-Woodcraft-Carveco-Tool-Database",

    # Misc
    "Feature_N17_Polygon_Offset_Arc (1)",
    "Feature_v16_1_Helical_Ramping",
    "CAM_Roadmap_AlphaNightingale",
    "Calculators",
    "README_Community_Patch",
    "README_Community_Patch_Additions",
    "phantom_cleanup_patch",
    "assets_staging",
    "ltb-express",
    "Altitude vs Modal frequencies__files",
    "Luthiers_ToolBox_Smart_Guitar_DAW_Bundle_v1.0",
    "temp_extract_37",
    "temp_extract_38"
)

$moved = 0
$skipped = 0

foreach ($folder in $foldersToMove) {
    if (Test-Path $folder) {
        Move-Item -Path $folder -Destination "__REFERENCE__\" -Force
        Write-Host "[MOVED] $folder" -ForegroundColor Green
        $moved++
    } else {
        Write-Host "[SKIP] $folder (not found)" -ForegroundColor DarkGray
        $skipped++
    }
}

Write-Host ""
Write-Host "Summary: $moved moved, $skipped skipped" -ForegroundColor Cyan
