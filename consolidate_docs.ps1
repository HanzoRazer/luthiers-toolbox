# ============================================================
# LUTHIER'S TOOLBOX - DOCUMENTATION CONSOLIDATION SCRIPT
# ============================================================
# Generated: December 17, 2025
# Purpose: Organize markdown files into canonical hierarchy
# 
# STRUCTURE:
#   docs/canonical/           - Authoritative specs (6 files)
#   docs/canonical/governance - Binding governance (7 files)  <-- OFFICIALLY DESIGNATED
#   docs/advisory/            - Promote when ready (5 files)
#   docs/quickref/[subsystem] - Operational guides
#   docs/archive/2025-12/     - Historical docs
#
# GOVERNANCE HIERARCHY:
#   CANONICAL (binding, enforced in code):
#     - CANONICAL_GOVERNANCE_INDEX.md  <-- Master index
#     - GOVERNANCE.md
#     - AI_SANDBOX_GOVERNANCE.md
#     - CNC_SAW_LAB_SAFETY_GOVERNANCE.md
#     - RMOS_2.0_Specification.md
#     - Tool_Library_Spec.md
#     - VALUE_ADDED_CODING_POLICY.md
#
#   ADVISORY (not yet enforced everywhere):
#     - AI_SANDBOX_GOVERNANCE_v2.0.md  (renamed from v 2.0)
#     - OpenAI_Provider_Contract.md
#     - GLOBAL_GRAPHICS_INGESTION_STANDARD.md
#     - ROSETTE_DESIGNER_REDESIGN_SPEC.md
#     - SPECIALTY_MODULES_QUICKSTART.md
#
#   ARCHIVED (historical only):
#     - MM_5_ULTRA_FRAGILITY_POLICY_QUICKREF.md
#     - LEGACY_ARCHIVE_POLICY.md
#
# USAGE:
#   1. cd to your repo root: cd C:\Users\thepr\Downloads\luthiers-toolbox
#   2. Run: .\consolidate_docs.ps1
#   3. Review changes with: git status
#   4. Commit: git add -A && git commit -m "docs: consolidate documentation hierarchy"
# ============================================================

$ErrorActionPreference = "Stop"
$repoRoot = Get-Location

# ============================================================
# SAFETY: WORKING DIRECTORY VALIDATION
# ============================================================
Write-Host "Validating working directory..." -ForegroundColor Cyan

$requiredMarkers = @(".git", "services", "packages", "docs")
$missingMarkers = @()

foreach ($marker in $requiredMarkers) {
    if (-not (Test-Path $marker)) {
        $missingMarkers += $marker
    }
}

if ($missingMarkers.Count -gt 0) {
    Write-Host ""
    Write-Host "ERROR: Not in repository root!" -ForegroundColor Red
    Write-Host "Missing markers: $($missingMarkers -join ', ')" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run from: C:\Users\thepr\Downloads\luthiers-toolbox" -ForegroundColor Yellow
    Write-Host "  cd C:\Users\thepr\Downloads\luthiers-toolbox" -ForegroundColor Gray
    Write-Host "  .\consolidate_docs.ps1" -ForegroundColor Gray
    exit 1
}

Write-Host "  Working directory validated: $repoRoot" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DOCUMENTATION CONSOLIDATION SCRIPT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# PHASE 1: CREATE DIRECTORY STRUCTURE
# ============================================================
Write-Host "[PHASE 1] Creating directory structure..." -ForegroundColor Yellow

$directories = @(
    "docs\canonical",
    "docs\canonical\governance",
    "docs\advisory",
    "docs\quickref\art_studio",
    "docs\quickref\blueprint",
    "docs\quickref\bridge_lab",
    "docs\quickref\cam",
    "docs\quickref\compare_lab",
    "docs\quickref\curve_lab",
    "docs\quickref\general",
    "docs\quickref\instrument",
    "docs\quickref\rmos",
    "docs\quickref\saw_lab",
    "docs\quickref\calculators",
    "docs\archive\2025-12\governance",
    "docs\archive\2025-12\sessions",
    "docs\archive\2025-12\patches",
    "docs\archive\2025-12\phases",
    "docs\archive\2025-12\waves",
    "docs\archive\2025-12\bundles",
    "docs\archive\2025-12\handoffs",
    "docs\archive\2025-12\reports",
    "docs\archive\2025-12\integration",
    "docs\archive\2025-12\misc"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    }
}
Write-Host ""

# ============================================================
# PHASE 2: CANONICAL GOVERNANCE (7 files) - OFFICIALLY DESIGNATED
# ============================================================
Write-Host "[PHASE 2] Moving CANONICAL GOVERNANCE files (BINDING)..." -ForegroundColor Yellow
Write-Host "  These documents define non-negotiable rules enforced in code." -ForegroundColor Gray


if (Test-Path "docs\AI_SANDBOX_GOVERNANCE.md") {
    Move-Item -Path "docs\AI_SANDBOX_GOVERNANCE.md" -Destination "docs\canonical\governance\AI_SANDBOX_GOVERNANCE.md" -Force
    Write-Host "  [CANONICAL] AI_SANDBOX_GOVERNANCE.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   AI_SANDBOX_GOVERNANCE.md" -ForegroundColor Red
}

if (Test-Path "CNC_SAW_LAB_SAFETY_GOVERNANCE.md") {
    Move-Item -Path "CNC_SAW_LAB_SAFETY_GOVERNANCE.md" -Destination "docs\canonical\governance\CNC_SAW_LAB_SAFETY_GOVERNANCE.md" -Force
    Write-Host "  [CANONICAL] CNC_SAW_LAB_SAFETY_GOVERNANCE.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   CNC_SAW_LAB_SAFETY_GOVERNANCE.md" -ForegroundColor Red
}

if (Test-Path "docs\GOVERNANCE.md") {
    Move-Item -Path "docs\GOVERNANCE.md" -Destination "docs\canonical\governance\GOVERNANCE.md" -Force
    Write-Host "  [CANONICAL] GOVERNANCE.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   GOVERNANCE.md" -ForegroundColor Red
}

if (Test-Path "RMOS_2.0_Specification.md") {
    Move-Item -Path "RMOS_2.0_Specification.md" -Destination "docs\canonical\governance\RMOS_2.0_Specification.md" -Force
    Write-Host "  [CANONICAL] RMOS_2.0_Specification.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   RMOS_2.0_Specification.md" -ForegroundColor Red
}

if (Test-Path "Tool_Library_Spec.md") {
    Move-Item -Path "Tool_Library_Spec.md" -Destination "docs\canonical\governance\Tool_Library_Spec.md" -Force
    Write-Host "  [CANONICAL] Tool_Library_Spec.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   Tool_Library_Spec.md" -ForegroundColor Red
}

if (Test-Path "docs\VALUE_ADDED_CODING_POLICY.md") {
    Move-Item -Path "docs\VALUE_ADDED_CODING_POLICY.md" -Destination "docs\canonical\governance\VALUE_ADDED_CODING_POLICY.md" -Force
    Write-Host "  [CANONICAL] VALUE_ADDED_CODING_POLICY.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   VALUE_ADDED_CODING_POLICY.md" -ForegroundColor Red
}

Write-Host ""

# ============================================================
# PHASE 3: ADVISORY GOVERNANCE (5 files) - NOT YET BINDING
# ============================================================
Write-Host "[PHASE 3] Moving ADVISORY files (promote when ready)..." -ForegroundColor Yellow
Write-Host "  These documents provide guidance but are not yet enforced everywhere." -ForegroundColor Gray


if (Test-Path "AI_SANDBOX_GOVERNANCE_v 2.0.md") {
    Move-Item -Path "AI_SANDBOX_GOVERNANCE_v 2.0.md" -Destination "docs\advisory\AI_SANDBOX_GOVERNANCE_v2.0.md" -Force
    Write-Host "  [ADVISORY]  AI_SANDBOX_GOVERNANCE_v2.0.md (renamed, space removed)" -ForegroundColor Yellow
} else {
    Write-Host "  [MISSING]   AI_SANDBOX_GOVERNANCE_v 2.0.md" -ForegroundColor Red
}

if (Test-Path "GLOBAL_GRAPHICS_INGESTION_STANDARD.md") {
    Move-Item -Path "GLOBAL_GRAPHICS_INGESTION_STANDARD.md" -Destination "docs\advisory\GLOBAL_GRAPHICS_INGESTION_STANDARD.md" -Force
    Write-Host "  [ADVISORY]  GLOBAL_GRAPHICS_INGESTION_STANDARD.md" -ForegroundColor Yellow
} else {
    Write-Host "  [MISSING]   GLOBAL_GRAPHICS_INGESTION_STANDARD.md" -ForegroundColor Red
}

if (Test-Path "OpenAI_Provider_Contract.md") {
    Move-Item -Path "OpenAI_Provider_Contract.md" -Destination "docs\advisory\OpenAI_Provider_Contract.md" -Force
    Write-Host "  [ADVISORY]  OpenAI_Provider_Contract.md" -ForegroundColor Yellow
} else {
    Write-Host "  [MISSING]   OpenAI_Provider_Contract.md" -ForegroundColor Red
}

if (Test-Path "ROSETTE_DESIGNER_REDESIGN_SPEC.md") {
    Move-Item -Path "ROSETTE_DESIGNER_REDESIGN_SPEC.md" -Destination "docs\advisory\ROSETTE_DESIGNER_REDESIGN_SPEC.md" -Force
    Write-Host "  [ADVISORY]  ROSETTE_DESIGNER_REDESIGN_SPEC.md" -ForegroundColor Yellow
} else {
    Write-Host "  [MISSING]   ROSETTE_DESIGNER_REDESIGN_SPEC.md" -ForegroundColor Red
}

if (Test-Path "SPECIALTY_MODULES_QUICKSTART.md") {
    Move-Item -Path "SPECIALTY_MODULES_QUICKSTART.md" -Destination "docs\advisory\SPECIALTY_MODULES_QUICKSTART.md" -Force
    Write-Host "  [ADVISORY]  SPECIALTY_MODULES_QUICKSTART.md" -ForegroundColor Yellow
} else {
    Write-Host "  [MISSING]   SPECIALTY_MODULES_QUICKSTART.md" -ForegroundColor Red
}

Write-Host ""

# ============================================================
# PHASE 4: ARCHIVED GOVERNANCE (2 files) - HISTORICAL ONLY
# ============================================================
Write-Host "[PHASE 4] Moving ARCHIVED GOVERNANCE files (historical only)..." -ForegroundColor Yellow
Write-Host "  These documents are retained for context but must not be treated as current policy." -ForegroundColor Gray


if (Test-Path "LEGACY_ARCHIVE_POLICY.md") {
    Move-Item -Path "LEGACY_ARCHIVE_POLICY.md" -Destination "docs\archive\2025-12\governance\LEGACY_ARCHIVE_POLICY.md" -Force
    Write-Host "  [ARCHIVED]  LEGACY_ARCHIVE_POLICY.md" -ForegroundColor DarkGray
} else {
    Write-Host "  [MISSING]   LEGACY_ARCHIVE_POLICY.md" -ForegroundColor Red
}

if (Test-Path "docs\MM_5_ULTRA_FRAGILITY_POLICY_QUICKREF.md") {
    Move-Item -Path "docs\MM_5_ULTRA_FRAGILITY_POLICY_QUICKREF.md" -Destination "docs\archive\2025-12\governance\MM_5_ULTRA_FRAGILITY_POLICY_QUICKREF.md" -Force
    Write-Host "  [ARCHIVED]  MM_5_ULTRA_FRAGILITY_POLICY_QUICKREF.md" -ForegroundColor DarkGray
} else {
    Write-Host "  [MISSING]   MM_5_ULTRA_FRAGILITY_POLICY_QUICKREF.md" -ForegroundColor Red
}

Write-Host ""

# ============================================================
# PHASE 5: CANONICAL SPECS (6 files)
# ============================================================
Write-Host "[PHASE 5] Moving CANONICAL SPECS..." -ForegroundColor Yellow


if (Test-Path "ARCHITECTURE.md") {
    Move-Item -Path "ARCHITECTURE.md" -Destination "docs\canonical\ARCHITECTURE.md" -Force
    Write-Host "  [SPEC]      ARCHITECTURE.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   ARCHITECTURE.md" -ForegroundColor Red
}

if (Test-Path "ARCHITECTURE_DECISION_NODE_SCOPE.md") {
    Move-Item -Path "ARCHITECTURE_DECISION_NODE_SCOPE.md" -Destination "docs\canonical\ARCHITECTURE_DECISION_NODE_SCOPE.md" -Force
    Write-Host "  [SPEC]      ARCHITECTURE_DECISION_NODE_SCOPE.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   ARCHITECTURE_DECISION_NODE_SCOPE.md" -ForegroundColor Red
}

if (Test-Path "ARCHITECTURE_DRIFT_LESSONS.md") {
    Move-Item -Path "ARCHITECTURE_DRIFT_LESSONS.md" -Destination "docs\canonical\ARCHITECTURE_DRIFT_LESSONS.md" -Force
    Write-Host "  [SPEC]      ARCHITECTURE_DRIFT_LESSONS.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   ARCHITECTURE_DRIFT_LESSONS.md" -ForegroundColor Red
}

if (Test-Path "CODING_POLICY.md") {
    Move-Item -Path "CODING_POLICY.md" -Destination "docs\canonical\CODING_POLICY.md" -Force
    Write-Host "  [SPEC]      CODING_POLICY.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   CODING_POLICY.md" -ForegroundColor Red
}

if (Test-Path "GETTING_STARTED.md") {
    Move-Item -Path "GETTING_STARTED.md" -Destination "docs\canonical\GETTING_STARTED.md" -Force
    Write-Host "  [SPEC]      GETTING_STARTED.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   GETTING_STARTED.md" -ForegroundColor Red
}

if (Test-Path "QUICKSTART.md") {
    Move-Item -Path "QUICKSTART.md" -Destination "docs\canonical\QUICKSTART.md" -Force
    Write-Host "  [SPEC]      QUICKSTART.md" -ForegroundColor Green
} else {
    Write-Host "  [MISSING]   QUICKSTART.md" -ForegroundColor Red
}

Write-Host ""

# ============================================================
# PHASE 6: QUICKREF FILES BY SUBSYSTEM
# ============================================================
Write-Host "[PHASE 6] Moving QUICKREF files by subsystem..." -ForegroundColor Yellow


Write-Host "  [ART_STUDIO] (10 files)" -ForegroundColor Cyan
if (Test-Path "ART_STUDIO_BUNDLE5_QUICKREF.md") { Move-Item -Path "ART_STUDIO_BUNDLE5_QUICKREF.md" -Destination "docs\quickref\art_studio\ART_STUDIO_BUNDLE5_QUICKREF.md" -Force }
if (Test-Path "ART_STUDIO_ENHANCEMENT_ROADMAP.md") { Move-Item -Path "ART_STUDIO_ENHANCEMENT_ROADMAP.md" -Destination "docs\quickref\art_studio\ART_STUDIO_ENHANCEMENT_ROADMAP.md" -Force }
if (Test-Path "ART_STUDIO_QUICKREF.md") { Move-Item -Path "ART_STUDIO_QUICKREF.md" -Destination "docs\quickref\art_studio\ART_STUDIO_QUICKREF.md" -Force }
if (Test-Path "ART_STUDIO_ROADMAP.md") { Move-Item -Path "ART_STUDIO_ROADMAP.md" -Destination "docs\quickref\art_studio\ART_STUDIO_ROADMAP.md" -Force }
if (Test-Path "ART_STUDIO_V15_5_QUICKREF.md") { Move-Item -Path "ART_STUDIO_V15_5_QUICKREF.md" -Destination "docs\quickref\art_studio\ART_STUDIO_V15_5_QUICKREF.md" -Force }
if (Test-Path "ART_STUDIO_V16_0_QUICKREF.md") { Move-Item -Path "ART_STUDIO_V16_0_QUICKREF.md" -Destination "docs\quickref\art_studio\ART_STUDIO_V16_0_QUICKREF.md" -Force }
if (Test-Path "ART_STUDIO_V16_1_QUICKREF.md") { Move-Item -Path "ART_STUDIO_V16_1_QUICKREF.md" -Destination "docs\quickref\art_studio\ART_STUDIO_V16_1_QUICKREF.md" -Force }
if (Test-Path "Art_Studio_Developer Onboarding Guide.md") { Move-Item -Path "Art_Studio_Developer Onboarding Guide.md" -Destination "docs\quickref\art_studio\Art_Studio_Developer Onboarding Guide.md" -Force }
if (Test-Path "ROSETTE_ART_STUDIO_QUICKREF.md") { Move-Item -Path "ROSETTE_ART_STUDIO_QUICKREF.md" -Destination "docs\quickref\art_studio\ROSETTE_ART_STUDIO_QUICKREF.md" -Force }
if (Test-Path "ROSETTE_REDESIGN_QUICKREF.md") { Move-Item -Path "ROSETTE_REDESIGN_QUICKREF.md" -Destination "docs\quickref\art_studio\ROSETTE_REDESIGN_QUICKREF.md" -Force }

Write-Host "  [BLUEPRINT] (3 files)" -ForegroundColor Cyan
if (Test-Path "BLUEPRINT_IMPORT_PHASE2_QUICKREF.md") { Move-Item -Path "BLUEPRINT_IMPORT_PHASE2_QUICKREF.md" -Destination "docs\quickref\blueprint\BLUEPRINT_IMPORT_PHASE2_QUICKREF.md" -Force }
if (Test-Path "BLUEPRINT_LAB_INDEX.md") { Move-Item -Path "BLUEPRINT_LAB_INDEX.md" -Destination "docs\quickref\blueprint\BLUEPRINT_LAB_INDEX.md" -Force }
if (Test-Path "BLUEPRINT_LAB_QUICKREF.md") { Move-Item -Path "BLUEPRINT_LAB_QUICKREF.md" -Destination "docs\quickref\blueprint\BLUEPRINT_LAB_QUICKREF.md" -Force }

Write-Host "  [BRIDGE_LAB] (1 files)" -ForegroundColor Cyan
if (Test-Path "BRIDGE_LAB_QUICKREF.md") { Move-Item -Path "BRIDGE_LAB_QUICKREF.md" -Destination "docs\quickref\bridge_lab\BRIDGE_LAB_QUICKREF.md" -Force }

Write-Host "  [CAM] (7 files)" -ForegroundColor Cyan
if (Test-Path "ADAPTIVE_FEED_OVERRIDE_QUICKREF.md") { Move-Item -Path "ADAPTIVE_FEED_OVERRIDE_QUICKREF.md" -Destination "docs\quickref\cam\ADAPTIVE_FEED_OVERRIDE_QUICKREF.md" -Force }
if (Test-Path "CAM_ESSENTIALS_N0_N10_QUICKREF.md") { Move-Item -Path "CAM_ESSENTIALS_N0_N10_QUICKREF.md" -Destination "docs\quickref\cam\CAM_ESSENTIALS_N0_N10_QUICKREF.md" -Force }
if (Test-Path "CAM_JobInt_Roadmap.md") { Move-Item -Path "CAM_JobInt_Roadmap.md" -Destination "docs\quickref\cam\CAM_JobInt_Roadmap.md" -Force }
if (Test-Path "CAM_PIPELINE_QUICKREF.md") { Move-Item -Path "CAM_PIPELINE_QUICKREF.md" -Destination "docs\quickref\cam\CAM_PIPELINE_QUICKREF.md" -Force }
if (Test-Path "HELICAL_POST_PRESETS_QUICKREF.md") { Move-Item -Path "HELICAL_POST_PRESETS_QUICKREF.md" -Destination "docs\quickref\cam\HELICAL_POST_PRESETS_QUICKREF.md" -Force }
if (Test-Path "HELICAL_V161_PRODUCTION_UPGRADE_PLAN.md") { Move-Item -Path "HELICAL_V161_PRODUCTION_UPGRADE_PLAN.md" -Destination "docs\quickref\cam\HELICAL_V161_PRODUCTION_UPGRADE_PLAN.md" -Force }
if (Test-Path "docs\MM_2_CAM_PROFILES_QUICKREF.md") { Move-Item -Path "docs\MM_2_CAM_PROFILES_QUICKREF.md" -Destination "docs\quickref\cam\MM_2_CAM_PROFILES_QUICKREF.md" -Force }

Write-Host "  [COMPARE_LAB] (2 files)" -ForegroundColor Cyan
if (Test-Path "docs\COMPARE_LAB_B22_TEST_PLAN.md") { Move-Item -Path "docs\COMPARE_LAB_B22_TEST_PLAN.md" -Destination "docs\quickref\compare_lab\COMPARE_LAB_B22_TEST_PLAN.md" -Force }
if (Test-Path "COMPARE_MODE_BUNDLE_ROADMAP.md") { Move-Item -Path "COMPARE_MODE_BUNDLE_ROADMAP.md" -Destination "docs\quickref\compare_lab\COMPARE_MODE_BUNDLE_ROADMAP.md" -Force }

Write-Host "  [CURVE_LAB] (2 files)" -ForegroundColor Cyan
if (Test-Path "CURVELAB_ENHANCEMENT_QUICK_REF.md") { Move-Item -Path "CURVELAB_ENHANCEMENT_QUICK_REF.md" -Destination "docs\quickref\curve_lab\CURVELAB_ENHANCEMENT_QUICK_REF.md" -Force }
if (Test-Path "CURVELAB_FINAL_PATCHES_QUICK_GUIDE.md") { Move-Item -Path "CURVELAB_FINAL_PATCHES_QUICK_GUIDE.md" -Destination "docs\quickref\curve_lab\CURVELAB_FINAL_PATCHES_QUICK_GUIDE.md" -Force }

Write-Host "  [GENERAL] (41 files)" -ForegroundColor Cyan
if (Test-Path "AMENDED WAVE PLAN.md") { Move-Item -Path "AMENDED WAVE PLAN.md" -Destination "docs\quickref\general\AMENDED WAVE PLAN.md" -Force }
if (Test-Path "A_N_BUILD_ROADMAP.md") { Move-Item -Path "A_N_BUILD_ROADMAP.md" -Destination "docs\quickref\general\A_N_BUILD_ROADMAP.md" -Force }
if (Test-Path "BADGE_QUICKREF.md") { Move-Item -Path "BADGE_QUICKREF.md" -Destination "docs\quickref\general\BADGE_QUICKREF.md" -Force }
if (Test-Path "DASHBOARD_ENHANCEMENT_QUICKREF.md") { Move-Item -Path "DASHBOARD_ENHANCEMENT_QUICKREF.md" -Destination "docs\quickref\general\DASHBOARD_ENHANCEMENT_QUICKREF.md" -Force }
if (Test-Path "docs\DATA_REGISTRY_QUICKREF.md") { Move-Item -Path "docs\DATA_REGISTRY_QUICKREF.md" -Destination "docs\quickref\general\DATA_REGISTRY_QUICKREF.md" -Force }
if (Test-Path "DIRECTIONAL_WORKFLOW_2_0_QUICKREF.md") { Move-Item -Path "DIRECTIONAL_WORKFLOW_2_0_QUICKREF.md" -Destination "docs\quickref\general\DIRECTIONAL_WORKFLOW_2_0_QUICKREF.md" -Force }
if (Test-Path "DOCKER_QUICKREF.md") { Move-Item -Path "DOCKER_QUICKREF.md" -Destination "docs\quickref\general\DOCKER_QUICKREF.md" -Force }
if (Test-Path "DOCUMENTATION_INDEX.md") { Move-Item -Path "DOCUMENTATION_INDEX.md" -Destination "docs\quickref\general\DOCUMENTATION_INDEX.md" -Force }
if (Test-Path "EXPRESS_EXTRACTION_GUIDE.md") { Move-Item -Path "EXPRESS_EXTRACTION_GUIDE.md" -Destination "docs\quickref\general\EXPRESS_EXTRACTION_GUIDE.md" -Force }
if (Test-Path "EXTENSION_VALIDATION_QUICKREF.md") { Move-Item -Path "EXTENSION_VALIDATION_QUICKREF.md" -Destination "docs\quickref\general\EXTENSION_VALIDATION_QUICKREF.md" -Force }
if (Test-Path "GITHUB_PAGES_SETUP_GUIDE.md") { Move-Item -Path "GITHUB_PAGES_SETUP_GUIDE.md" -Destination "docs\quickref\general\GITHUB_PAGES_SETUP_GUIDE.md" -Force }
if (Test-Path "LIVE_LEARN_QUICKREF.md") { Move-Item -Path "LIVE_LEARN_QUICKREF.md" -Destination "docs\quickref\general\LIVE_LEARN_QUICKREF.md" -Force }
if (Test-Path "MACHINE_ENVELOPE_QUICKREF.md") { Move-Item -Path "MACHINE_ENVELOPE_QUICKREF.md" -Destination "docs\quickref\general\MACHINE_ENVELOPE_QUICKREF.md" -Force }
if (Test-Path "MACHINE_PROFILES_QUICKREF.md") { Move-Item -Path "MACHINE_PROFILES_QUICKREF.md" -Destination "docs\quickref\general\MACHINE_PROFILES_QUICKREF.md" -Force }
if (Test-Path "MASTER_INDEX.md") { Move-Item -Path "MASTER_INDEX.md" -Destination "docs\quickref\general\MASTER_INDEX.md" -Force }
if (Test-Path "docs\MM_0_MIXED_MATERIAL_QUICKREF.md") { Move-Item -Path "docs\MM_0_MIXED_MATERIAL_QUICKREF.md" -Destination "docs\quickref\general\MM_0_MIXED_MATERIAL_QUICKREF.md" -Force }
if (Test-Path "docs\MM_3_PDF_DESIGN_SHEETS_QUICKREF.md") { Move-Item -Path "docs\MM_3_PDF_DESIGN_SHEETS_QUICKREF.md" -Destination "docs\quickref\general\MM_3_PDF_DESIGN_SHEETS_QUICKREF.md" -Force }
if (Test-Path "docs\MM_4_MATERIAL_AWARE_ANALYTICS_QUICKREF.md") { Move-Item -Path "docs\MM_4_MATERIAL_AWARE_ANALYTICS_QUICKREF.md" -Destination "docs\quickref\general\MM_4_MATERIAL_AWARE_ANALYTICS_QUICKREF.md" -Force }
if (Test-Path "docs\MM_6_FRAGILITY_AWARE_LIVE_MONITOR_QUICKREF.md") { Move-Item -Path "docs\MM_6_FRAGILITY_AWARE_LIVE_MONITOR_QUICKREF.md" -Destination "docs\quickref\general\MM_6_FRAGILITY_AWARE_LIVE_MONITOR_QUICKREF.md" -Force }
if (Test-Path "MODULE_M1_1_QUICKREF.md") { Move-Item -Path "MODULE_M1_1_QUICKREF.md" -Destination "docs\quickref\general\MODULE_M1_1_QUICKREF.md" -Force }
if (Test-Path "MODULE_M3_INDEX.md") { Move-Item -Path "MODULE_M3_INDEX.md" -Destination "docs\quickref\general\MODULE_M3_INDEX.md" -Force }
if (Test-Path "MODULE_M3_QUICKREF.md") { Move-Item -Path "MODULE_M3_QUICKREF.md" -Destination "docs\quickref\general\MODULE_M3_QUICKREF.md" -Force }
if (Test-Path "MONOREPO_QUICKREF.md") { Move-Item -Path "MONOREPO_QUICKREF.md" -Destination "docs\quickref\general\MONOREPO_QUICKREF.md" -Force }
if (Test-Path "MULTI_OP_PIPELINE_PLAN.md") { Move-Item -Path "MULTI_OP_PIPELINE_PLAN.md" -Destination "docs\quickref\general\MULTI_OP_PIPELINE_PLAN.md" -Force }
if (Test-Path "MVP_TO_PRODUCTION_ROADMAP.md") { Move-Item -Path "MVP_TO_PRODUCTION_ROADMAP.md" -Destination "docs\quickref\general\MVP_TO_PRODUCTION_ROADMAP.md" -Force }
if (Test-Path "POST_INJECTION_DROPIN_QUICKREF.md") { Move-Item -Path "POST_INJECTION_DROPIN_QUICKREF.md" -Destination "docs\quickref\general\POST_INJECTION_DROPIN_QUICKREF.md" -Force }
if (Test-Path "POST_INJECTION_HELPERS_QUICKREF.md") { Move-Item -Path "POST_INJECTION_HELPERS_QUICKREF.md" -Destination "docs\quickref\general\POST_INJECTION_HELPERS_QUICKREF.md" -Force }
if (Test-Path "PRODUCTION_QUICKREF.md") { Move-Item -Path "PRODUCTION_QUICKREF.md" -Destination "docs\quickref\general\PRODUCTION_QUICKREF.md" -Force }
if (Test-Path "PRODUCT_SEGMENTATION_INDEX.md") { Move-Item -Path "PRODUCT_SEGMENTATION_INDEX.md" -Destination "docs\quickref\general\PRODUCT_SEGMENTATION_INDEX.md" -Force }
if (Test-Path "docs\PR_GUIDE.md") { Move-Item -Path "docs\PR_GUIDE.md" -Destination "docs\quickref\general\PR_GUIDE.md" -Force }
if (Test-Path "QUICK_REFERENCE.md") { Move-Item -Path "QUICK_REFERENCE.md" -Destination "docs\quickref\general\QUICK_REFERENCE.md" -Force }
if (Test-Path "RUN_ARTIFACT_INDEX_QUERY_API.md") { Move-Item -Path "RUN_ARTIFACT_INDEX_QUERY_API.md" -Destination "docs\quickref\general\RUN_ARTIFACT_INDEX_QUERY_API.md" -Force }
if (Test-Path "SHIELDS_BADGE_QUICKREF.md") { Move-Item -Path "SHIELDS_BADGE_QUICKREF.md" -Destination "docs\quickref\general\SHIELDS_BADGE_QUICKREF.md" -Force }
if (Test-Path "STATE_PERSISTENCE_QUICKREF.md") { Move-Item -Path "STATE_PERSISTENCE_QUICKREF.md" -Destination "docs\quickref\general\STATE_PERSISTENCE_QUICKREF.md" -Force }
if (Test-Path "TEAM_ASSEMBLY_ROADMAP.md") { Move-Item -Path "TEAM_ASSEMBLY_ROADMAP.md" -Destination "docs\quickref\general\TEAM_ASSEMBLY_ROADMAP.md" -Force }
if (Test-Path "TEMPLATE_ENGINE_QUICKREF.md") { Move-Item -Path "TEMPLATE_ENGINE_QUICKREF.md" -Destination "docs\quickref\general\TEMPLATE_ENGINE_QUICKREF.md" -Force }
if (Test-Path "TESTING_QUICK_REFERENCE.md") { Move-Item -Path "TESTING_QUICK_REFERENCE.md" -Destination "docs\quickref\general\TESTING_QUICK_REFERENCE.md" -Force }
if (Test-Path "TEST_COVERAGE_QUICKREF.md") { Move-Item -Path "TEST_COVERAGE_QUICKREF.md" -Destination "docs\quickref\general\TEST_COVERAGE_QUICKREF.md" -Force }
if (Test-Path "Tool_Library_Migration_Plan.md") { Move-Item -Path "Tool_Library_Migration_Plan.md" -Destination "docs\quickref\general\Tool_Library_Migration_Plan.md" -Force }
if (Test-Path "UNIFIED_PIPELINE_QUICKREF.md") { Move-Item -Path "UNIFIED_PIPELINE_QUICKREF.md" -Destination "docs\quickref\general\UNIFIED_PIPELINE_QUICKREF.md" -Force }
if (Test-Path "docs\user_interview_guide.md") { Move-Item -Path "docs\user_interview_guide.md" -Destination "docs\quickref\general\user_interview_guide.md" -Force }

Write-Host "  [INSTRUMENT] (1 files)" -ForegroundColor Cyan
if (Test-Path "docs\Instrument_Geometry_Migration_Plan.md") { Move-Item -Path "docs\Instrument_Geometry_Migration_Plan.md" -Destination "docs\quickref\instrument\Instrument_Geometry_Migration_Plan.md" -Force }

Write-Host "  [RMOS] (4 files)" -ForegroundColor Cyan
if (Test-Path "RMOS Developer Onboarding Guide.md") { Move-Item -Path "RMOS Developer Onboarding Guide.md" -Destination "docs\quickref\rmos\RMOS Developer Onboarding Guide.md" -Force }
if (Test-Path "RMOS_MIGRATION_N8_7_QUICKREF.md") { Move-Item -Path "RMOS_MIGRATION_N8_7_QUICKREF.md" -Destination "docs\quickref\rmos\RMOS_MIGRATION_N8_7_QUICKREF.md" -Force }
if (Test-Path "docs\RMOS_STUDIO_DEVELOPER_GUIDE.md") { Move-Item -Path "docs\RMOS_STUDIO_DEVELOPER_GUIDE.md" -Destination "docs\quickref\rmos\RMOS_STUDIO_DEVELOPER_GUIDE.md" -Force }
if (Test-Path "RMOS_STUDIO_MANUFACTURING_PLANNER.md") { Move-Item -Path "RMOS_STUDIO_MANUFACTURING_PLANNER.md" -Destination "docs\quickref\rmos\RMOS_STUDIO_MANUFACTURING_PLANNER.md" -Force }

Write-Host "  [SAW_LAB] (2 files)" -ForegroundColor Cyan
if (Test-Path "SAW_LAB_2_0_QUICKREF.md") { Move-Item -Path "SAW_LAB_2_0_QUICKREF.md" -Destination "docs\quickref\saw_lab\SAW_LAB_2_0_QUICKREF.md" -Force }
if (Test-Path "Saw_Path_Planner_2_1_Upgrade_Plan.md") { Move-Item -Path "Saw_Path_Planner_2_1_Upgrade_Plan.md" -Destination "docs\quickref\saw_lab\Saw_Path_Planner_2_1_Upgrade_Plan.md" -Force }

Write-Host ""

# ============================================================
# PHASE 7: ARCHIVE FILES (Historical)
# ============================================================
Write-Host "[PHASE 7] Moving ARCHIVE files..." -ForegroundColor Yellow
Write-Host "  (This may take a moment)" -ForegroundColor Gray

if (Test-Path "ACTIONS_1_2_COMPLETE.md") { Move-Item -Path "ACTIONS_1_2_COMPLETE.md" -Destination "docs\archive\2025-12\misc\ACTIONS_1_2_COMPLETE.md" -Force }
if (Test-Path "ADAPTIVE_POCKETING_MODULE_L.md") { Move-Item -Path "ADAPTIVE_POCKETING_MODULE_L.md" -Destination "docs\archive\2025-12\misc\ADAPTIVE_POCKETING_MODULE_L.md" -Force }
if (Test-Path "AGENTS.md") { Move-Item -Path "AGENTS.md" -Destination "docs\archive\2025-12\misc\AGENTS.md" -Force }
if (Test-Path "AI Subsystem_Integration_Handoff_12162025.md") { Move-Item -Path "AI Subsystem_Integration_Handoff_12162025.md" -Destination "docs\archive\2025-12\handoffs\AI Subsystem_Integration_Handoff_12162025.md" -Force }
if (Test-Path "AI_Profile_Tuning_Handoff.md") { Move-Item -Path "AI_Profile_Tuning_Handoff.md" -Destination "docs\archive\2025-12\handoffs\AI_Profile_Tuning_Handoff.md" -Force }
if (Test-Path "AI_REFACTORING_SESSION_REPORT_DEC16.md") { Move-Item -Path "AI_REFACTORING_SESSION_REPORT_DEC16.md" -Destination "docs\archive\2025-12\sessions\AI_REFACTORING_SESSION_REPORT_DEC16.md" -Force }
if (Test-Path "AI_SCHEMA_NAMESPACE_REPORT.md") { Move-Item -Path "AI_SCHEMA_NAMESPACE_REPORT.md" -Destination "docs\archive\2025-12\reports\AI_SCHEMA_NAMESPACE_REPORT.md" -Force }
if (Test-Path "ARCHITECTURAL_EVOLUTION.md") { Move-Item -Path "ARCHITECTURAL_EVOLUTION.md" -Destination "docs\archive\2025-12\misc\ARCHITECTURAL_EVOLUTION.md" -Force }
if (Test-Path "ARCHIVED_DATA_EVALUATION_REPORT.md") { Move-Item -Path "ARCHIVED_DATA_EVALUATION_REPORT.md" -Destination "docs\archive\2025-12\reports\ARCHIVED_DATA_EVALUATION_REPORT.md" -Force }
if (Test-Path "ART_STUDIO_BUNDLE5_BACKEND_COMPLETE.md") { Move-Item -Path "ART_STUDIO_BUNDLE5_BACKEND_COMPLETE.md" -Destination "docs\archive\2025-12\bundles\ART_STUDIO_BUNDLE5_BACKEND_COMPLETE.md" -Force }
if (Test-Path "ART_STUDIO_CHECKPOINT_EVALUATION.md") { Move-Item -Path "ART_STUDIO_CHECKPOINT_EVALUATION.md" -Destination "docs\archive\2025-12\misc\ART_STUDIO_CHECKPOINT_EVALUATION.md" -Force }
if (Test-Path "ART_STUDIO_COMPLETE_VERIFICATION.md") { Move-Item -Path "ART_STUDIO_COMPLETE_VERIFICATION.md" -Destination "docs\archive\2025-12\misc\ART_STUDIO_COMPLETE_VERIFICATION.md" -Force }
if (Test-Path "ART_STUDIO_DEVELOPER_HANDOFF.md") { Move-Item -Path "ART_STUDIO_DEVELOPER_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\ART_STUDIO_DEVELOPER_HANDOFF.md" -Force }
if (Test-Path "ART_STUDIO_DUMP_BUNDLES_ANALYSIS.md") { Move-Item -Path "ART_STUDIO_DUMP_BUNDLES_ANALYSIS.md" -Destination "docs\archive\2025-12\bundles\ART_STUDIO_DUMP_BUNDLES_ANALYSIS.md" -Force }
if (Test-Path "ART_STUDIO_INTEGRATION_V13.md") { Move-Item -Path "ART_STUDIO_INTEGRATION_V13.md" -Destination "docs\archive\2025-12\integration\ART_STUDIO_INTEGRATION_V13.md" -Force }
if (Test-Path "ART_STUDIO_V15_5_INTEGRATION.md") { Move-Item -Path "ART_STUDIO_V15_5_INTEGRATION.md" -Destination "docs\archive\2025-12\integration\ART_STUDIO_V15_5_INTEGRATION.md" -Force }
if (Test-Path "ART_STUDIO_V16_1_HELICAL_INTEGRATION.md") { Move-Item -Path "ART_STUDIO_V16_1_HELICAL_INTEGRATION.md" -Destination "docs\archive\2025-12\integration\ART_STUDIO_V16_1_HELICAL_INTEGRATION.md" -Force }
if (Test-Path "ART_STUDIO_V16_1_INTEGRATION_STATUS.md") { Move-Item -Path "ART_STUDIO_V16_1_INTEGRATION_STATUS.md" -Destination "docs\archive\2025-12\integration\ART_STUDIO_V16_1_INTEGRATION_STATUS.md" -Force }
if (Test-Path "AUDIT_BUILT_VS_CREATED.md") { Move-Item -Path "AUDIT_BUILT_VS_CREATED.md" -Destination "docs\archive\2025-12\misc\AUDIT_BUILT_VS_CREATED.md" -Force }
if (Test-Path "Answer Back for GitHub.md") { Move-Item -Path "Answer Back for GitHub.md" -Destination "docs\archive\2025-12\misc\Answer Back for GitHub.md" -Force }
if (Test-Path "ArtStudio_Bracing_Integration.md") { Move-Item -Path "ArtStudio_Bracing_Integration.md" -Destination "docs\archive\2025-12\integration\ArtStudio_Bracing_Integration.md" -Force }
if (Test-Path "B19_CLONE_AS_PRESET_INTEGRATION.md") { Move-Item -Path "B19_CLONE_AS_PRESET_INTEGRATION.md" -Destination "docs\archive\2025-12\integration\B19_CLONE_AS_PRESET_INTEGRATION.md" -Force }
if (Test-Path "B20_ENHANCED_TOOLTIPS_COMPLETE.md") { Move-Item -Path "B20_ENHANCED_TOOLTIPS_COMPLETE.md" -Destination "docs\archive\2025-12\bundles\B20_ENHANCED_TOOLTIPS_COMPLETE.md" -Force }
if (Test-Path "B21_INTEGRATION_TEST_GUIDE.md") { Move-Item -Path "B21_INTEGRATION_TEST_GUIDE.md" -Destination "docs\archive\2025-12\bundles\B21_INTEGRATION_TEST_GUIDE.md" -Force }
if (Test-Path "B21_MULTI_RUN_COMPARISON_COMPLETE.md") { Move-Item -Path "B21_MULTI_RUN_COMPARISON_COMPLETE.md" -Destination "docs\archive\2025-12\bundles\B21_MULTI_RUN_COMPARISON_COMPLETE.md" -Force }
if (Test-Path "B21_MULTI_RUN_COMPARISON_QUICKREF.md") { Move-Item -Path "B21_MULTI_RUN_COMPARISON_QUICKREF.md" -Destination "docs\archive\2025-12\bundles\B21_MULTI_RUN_COMPARISON_QUICKREF.md" -Force }
if (Test-Path "B21_ROUTE_REGISTRATION_GUIDE.md") { Move-Item -Path "B21_ROUTE_REGISTRATION_GUIDE.md" -Destination "docs\archive\2025-12\bundles\B21_ROUTE_REGISTRATION_GUIDE.md" -Force }
if (Test-Path "docs\B22_10_COMPARE_MODES.md") { Move-Item -Path "docs\B22_10_COMPARE_MODES.md" -Destination "docs\archive\2025-12\bundles\B22_10_COMPARE_MODES.md" -Force }
if (Test-Path "docs\B22_11_LAYER_AWARE_COMPARE.md") { Move-Item -Path "docs\B22_11_LAYER_AWARE_COMPARE.md" -Destination "docs\archive\2025-12\bundles\B22_11_LAYER_AWARE_COMPARE.md" -Force }
if (Test-Path "docs\B22_12_EXPORTABLE_DIFF_REPORTS.md") { Move-Item -Path "docs\B22_12_EXPORTABLE_DIFF_REPORTS.md" -Destination "docs\archive\2025-12\bundles\B22_12_EXPORTABLE_DIFF_REPORTS.md" -Force }
if (Test-Path "docs\B22_13_COMPARE_AUTOMATION_API.md") { Move-Item -Path "docs\B22_13_COMPARE_AUTOMATION_API.md" -Destination "docs\archive\2025-12\bundles\B22_13_COMPARE_AUTOMATION_API.md" -Force }
if (Test-Path "docs\B22_16_GOLDEN_REPORT_FUSION.md") { Move-Item -Path "docs\B22_16_GOLDEN_REPORT_FUSION.md" -Destination "docs\archive\2025-12\bundles\B22_16_GOLDEN_REPORT_FUSION.md" -Force }
if (Test-Path "docs\B22_16_GOLDEN_REPORT_FUSION_QUICKREF.md") { Move-Item -Path "docs\B22_16_GOLDEN_REPORT_FUSION_QUICKREF.md" -Destination "docs\archive\2025-12\bundles\B22_16_GOLDEN_REPORT_FUSION_QUICKREF.md" -Force }
if (Test-Path "docs\B22_8_IMPLEMENTATION_SUMMARY.md") { Move-Item -Path "docs\B22_8_IMPLEMENTATION_SUMMARY.md" -Destination "docs\archive\2025-12\bundles\B22_8_IMPLEMENTATION_SUMMARY.md" -Force }
if (Test-Path "docs\B22_8_SKELETON_INTEGRATION.md") { Move-Item -Path "docs\B22_8_SKELETON_INTEGRATION.md" -Destination "docs\archive\2025-12\bundles\B22_8_SKELETON_INTEGRATION.md" -Force }
if (Test-Path "docs\B22_8_TEST_SETUP.md") { Move-Item -Path "docs\B22_8_TEST_SETUP.md" -Destination "docs\archive\2025-12\bundles\B22_8_TEST_SETUP.md" -Force }
if (Test-Path "docs\B22_9_AUTOSCALE_ZOOM_TO_DIFF.md") { Move-Item -Path "docs\B22_9_AUTOSCALE_ZOOM_TO_DIFF.md" -Destination "docs\archive\2025-12\bundles\B22_9_AUTOSCALE_ZOOM_TO_DIFF.md" -Force }
if (Test-Path "docs\B26_BASELINE_MARKING_COMPLETE.md") { Move-Item -Path "docs\B26_BASELINE_MARKING_COMPLETE.md" -Destination "docs\archive\2025-12\bundles\B26_BASELINE_MARKING_COMPLETE.md" -Force }
if (Test-Path "BATCH3_UPLOAD_RECONCILIATION.md") { Move-Item -Path "BATCH3_UPLOAD_RECONCILIATION.md" -Destination "docs\archive\2025-12\misc\BATCH3_UPLOAD_RECONCILIATION.md" -Force }
if (Test-Path "BATCH_EXPORT_SUBSET_UPGRADE.md") { Move-Item -Path "BATCH_EXPORT_SUBSET_UPGRADE.md" -Destination "docs\archive\2025-12\misc\BATCH_EXPORT_SUBSET_UPGRADE.md" -Force }
if (Test-Path "BIDIRECTIONAL_WORKFLOW_ANALYSIS_REPORT.md") { Move-Item -Path "BIDIRECTIONAL_WORKFLOW_ANALYSIS_REPORT.md" -Destination "docs\archive\2025-12\reports\BIDIRECTIONAL_WORKFLOW_ANALYSIS_REPORT.md" -Force }
if (Test-Path "BLUEPRINT_IMPORT_QUICKSTART.md") { Move-Item -Path "BLUEPRINT_IMPORT_QUICKSTART.md" -Destination "docs\archive\2025-12\misc\BLUEPRINT_IMPORT_QUICKSTART.md" -Force }
if (Test-Path "BLUEPRINT_LAB_WORKFLOW_DIAGRAM.md") { Move-Item -Path "BLUEPRINT_LAB_WORKFLOW_DIAGRAM.md" -Destination "docs\archive\2025-12\misc\BLUEPRINT_LAB_WORKFLOW_DIAGRAM.md" -Force }
if (Test-Path "BLUEPRINT_PHASE2_CAM_INTEGRATION.md") { Move-Item -Path "BLUEPRINT_PHASE2_CAM_INTEGRATION.md" -Destination "docs\archive\2025-12\integration\BLUEPRINT_PHASE2_CAM_INTEGRATION.md" -Force }
if (Test-Path "BLUEPRINT_STANDALONE_EVALUATION.md") { Move-Item -Path "BLUEPRINT_STANDALONE_EVALUATION.md" -Destination "docs\archive\2025-12\misc\BLUEPRINT_STANDALONE_EVALUATION.md" -Force }
if (Test-Path "BLUEPRINT_TECTONIC_SHIFT_ANALYSIS.md") { Move-Item -Path "BLUEPRINT_TECTONIC_SHIFT_ANALYSIS.md" -Destination "docs\archive\2025-12\misc\BLUEPRINT_TECTONIC_SHIFT_ANALYSIS.md" -Force }
if (Test-Path "BLUEPRINT_TO_CAM_INTEGRATION_PLAN.md") { Move-Item -Path "BLUEPRINT_TO_CAM_INTEGRATION_PLAN.md" -Destination "docs\archive\2025-12\integration\BLUEPRINT_TO_CAM_INTEGRATION_PLAN.md" -Force }
if (Test-Path "BUNDLE_10_OPERATOR_REPORT.md") { Move-Item -Path "BUNDLE_10_OPERATOR_REPORT.md" -Destination "docs\archive\2025-12\bundles\BUNDLE_10_OPERATOR_REPORT.md" -Force }
if (Test-Path "BUNDLE_11_OPERATOR_REPORT_PDF.md") { Move-Item -Path "BUNDLE_11_OPERATOR_REPORT_PDF.md" -Destination "docs\archive\2025-12\bundles\BUNDLE_11_OPERATOR_REPORT_PDF.md" -Force }
if (Test-Path "BUNDLE_12_UI_DOWNLOAD_BUTTON.md") { Move-Item -Path "BUNDLE_12_UI_DOWNLOAD_BUTTON.md" -Destination "docs\archive\2025-12\bundles\BUNDLE_12_UI_DOWNLOAD_BUTTON.md" -Force }
if (Test-Path "BUNDLE_13_CNC_HISTORY_ADVANCED_SAFETY.md") { Move-Item -Path "BUNDLE_13_CNC_HISTORY_ADVANCED_SAFETY.md" -Destination "docs\archive\2025-12\bundles\BUNDLE_13_CNC_HISTORY_ADVANCED_SAFETY.md" -Force }
if (Test-Path "BUNDLE_13_COMPLETE_ANALYSIS.md") { Move-Item -Path "BUNDLE_13_COMPLETE_ANALYSIS.md" -Destination "docs\archive\2025-12\bundles\BUNDLE_13_COMPLETE_ANALYSIS.md" -Force }
if (Test-Path "CAD_SOFTWARE_EVALUATION.md") { Move-Item -Path "CAD_SOFTWARE_EVALUATION.md" -Destination "docs\archive\2025-12\misc\CAD_SOFTWARE_EVALUATION.md" -Force }
if (Test-Path "CALCULATORS_DIRECTORY_ANALYSIS.md") { Move-Item -Path "CALCULATORS_DIRECTORY_ANALYSIS.md" -Destination "docs\archive\2025-12\misc\CALCULATORS_DIRECTORY_ANALYSIS.md" -Force }
if (Test-Path "CALCULATOR_NAMESPACE_CONFLICT_ANALYSIS.md") { Move-Item -Path "CALCULATOR_NAMESPACE_CONFLICT_ANALYSIS.md" -Destination "docs\archive\2025-12\misc\CALCULATOR_NAMESPACE_CONFLICT_ANALYSIS.md" -Force }
if (Test-Path "CAM Engine Path A.md") { Move-Item -Path "CAM Engine Path A.md" -Destination "docs\archive\2025-12\misc\CAM Engine Path A.md" -Force }
if (Test-Path "CAM_CAD_DEVELOPER_HANDOFF.md") { Move-Item -Path "CAM_CAD_DEVELOPER_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\CAM_CAD_DEVELOPER_HANDOFF.md" -Force }
if (Test-Path "CAM_Core Wave_11_AI_CAM_Upgrade.md") { Move-Item -Path "CAM_Core Wave_11_AI_CAM_Upgrade.md" -Destination "docs\archive\2025-12\waves\CAM_Core Wave_11_AI_CAM_Upgrade.md" -Force }
if (Test-Path "CAM_DASHBOARD_README.md") { Move-Item -Path "CAM_DASHBOARD_README.md" -Destination "docs\archive\2025-12\misc\CAM_DASHBOARD_README.md" -Force }
if (Test-Path "CAM_ENGINE_ANALYSIS_COMPLETE.md") { Move-Item -Path "CAM_ENGINE_ANALYSIS_COMPLETE.md" -Destination "docs\archive\2025-12\misc\CAM_ENGINE_ANALYSIS_COMPLETE.md" -Force }
if (Test-Path "CAM_ESSENTIALS_N0_N10_INTEGRATION_COMPLETE.md") { Move-Item -Path "CAM_ESSENTIALS_N0_N10_INTEGRATION_COMPLETE.md" -Destination "docs\archive\2025-12\integration\CAM_ESSENTIALS_N0_N10_INTEGRATION_COMPLETE.md" -Force }
if (Test-Path "CAM_ESSENTIALS_N0_N10_STATUS.md") { Move-Item -Path "CAM_ESSENTIALS_N0_N10_STATUS.md" -Destination "docs\archive\2025-12\misc\CAM_ESSENTIALS_N0_N10_STATUS.md" -Force }
if (Test-Path "CAM_ESSENTIALS_V1_0_RELEASE_NOTES.md") { Move-Item -Path "CAM_ESSENTIALS_V1_0_RELEASE_NOTES.md" -Destination "docs\archive\2025-12\misc\CAM_ESSENTIALS_V1_0_RELEASE_NOTES.md" -Force }
if (Test-Path "CAM_EXPORT_BUNDLE_EXECUTIVE_SUMMARY.md") { Move-Item -Path "CAM_EXPORT_BUNDLE_EXECUTIVE_SUMMARY.md" -Destination "docs\archive\2025-12\bundles\CAM_EXPORT_BUNDLE_EXECUTIVE_SUMMARY.md" -Force }
if (Test-Path "CAM_EXPORT_BUNDLE_MANIFEST.md") { Move-Item -Path "CAM_EXPORT_BUNDLE_MANIFEST.md" -Destination "docs\archive\2025-12\bundles\CAM_EXPORT_BUNDLE_MANIFEST.md" -Force }
if (Test-Path "CAM_INTEGRATION_QUICKREF.md") { Move-Item -Path "CAM_INTEGRATION_QUICKREF.md" -Destination "docs\archive\2025-12\integration\CAM_INTEGRATION_QUICKREF.md" -Force }
if (Test-Path "CAM_JOB_SYSTEM_IMPLEMENTATION.md") { Move-Item -Path "CAM_JOB_SYSTEM_IMPLEMENTATION.md" -Destination "docs\archive\2025-12\misc\CAM_JOB_SYSTEM_IMPLEMENTATION.md" -Force }
if (Test-Path "CAM_PIPELINE_FINAL_SUMMARY.md") { Move-Item -Path "CAM_PIPELINE_FINAL_SUMMARY.md" -Destination "docs\archive\2025-12\misc\CAM_PIPELINE_FINAL_SUMMARY.md" -Force }
if (Test-Path "CAM_PIPELINE_INTEGRATION_PHASE1.md") { Move-Item -Path "CAM_PIPELINE_INTEGRATION_PHASE1.md" -Destination "docs\archive\2025-12\integration\CAM_PIPELINE_INTEGRATION_PHASE1.md" -Force }
if (Test-Path "CHECKLIST_V16_COMMUNITY.md") { Move-Item -Path "CHECKLIST_V16_COMMUNITY.md" -Destination "docs\archive\2025-12\misc\CHECKLIST_V16_COMMUNITY.md" -Force }
if (Test-Path "CLIENT_DIRECTORY_CONFLICT_REPORT.md") { Move-Item -Path "CLIENT_DIRECTORY_CONFLICT_REPORT.md" -Destination "docs\archive\2025-12\reports\CLIENT_DIRECTORY_CONFLICT_REPORT.md" -Force }
if (Test-Path "docs\CLONE_PROJECT_DEVELOPER_HANDOFF.md") { Move-Item -Path "docs\CLONE_PROJECT_DEVELOPER_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\CLONE_PROJECT_DEVELOPER_HANDOFF.md" -Force }
if (Test-Path "CNC Saw Lab #U2014 Recommended Repo Strurcture.md") { Move-Item -Path "CNC Saw Lab #U2014 Recommended Repo Strurcture.md" -Destination "docs\archive\2025-12\misc\CNC Saw Lab #U2014 Recommended Repo Strurcture.md" -Force }
if (Test-Path "CNC Saw Lab #U2014 Untracked Files Inventory.md") { Move-Item -Path "CNC Saw Lab #U2014 Untracked Files Inventory.md" -Destination "docs\archive\2025-12\misc\CNC Saw Lab #U2014 Untracked Files Inventory.md" -Force }
if (Test-Path "CNC Saw Lab.md") { Move-Item -Path "CNC Saw Lab.md" -Destination "docs\archive\2025-12\misc\CNC Saw Lab.md" -Force }
if (Test-Path "CNC Saw Lab_Requirements_State Machine Mapping.md") { Move-Item -Path "CNC Saw Lab_Requirements_State Machine Mapping.md" -Destination "docs\archive\2025-12\misc\CNC Saw Lab_Requirements_State Machine Mapping.md" -Force }
if (Test-Path "docs\CNC_PRESET_MANAGER_B20.md") { Move-Item -Path "docs\CNC_PRESET_MANAGER_B20.md" -Destination "docs\archive\2025-12\misc\CNC_PRESET_MANAGER_B20.md" -Force }
if (Test-Path "CNC_SAW_LAB_MISSING_COMPONENTS_VISUAL.md") { Move-Item -Path "CNC_SAW_LAB_MISSING_COMPONENTS_VISUAL.md" -Destination "docs\archive\2025-12\misc\CNC_SAW_LAB_MISSING_COMPONENTS_VISUAL.md" -Force }
if (Test-Path "CNC_SAW_LAB_RECONCILIATION_REPORT.md") { Move-Item -Path "CNC_SAW_LAB_RECONCILIATION_REPORT.md" -Destination "docs\archive\2025-12\reports\CNC_SAW_LAB_RECONCILIATION_REPORT.md" -Force }
if (Test-Path "docs\CNC_Saw_Blade_RFQ.md") { Move-Item -Path "docs\CNC_Saw_Blade_RFQ.md" -Destination "docs\archive\2025-12\misc\CNC_Saw_Blade_RFQ.md" -Force }
if (Test-Path "docs\CNC_Saw_Lab_Conversation.md") { Move-Item -Path "docs\CNC_Saw_Lab_Conversation.md" -Destination "docs\archive\2025-12\misc\CNC_Saw_Lab_Conversation.md" -Force }
if (Test-Path "CNC_Saw_Lab_Handoff.md") { Move-Item -Path "CNC_Saw_Lab_Handoff.md" -Destination "docs\archive\2025-12\handoffs\CNC_Saw_Lab_Handoff.md" -Force }
if (Test-Path "docs\CNC_Saw_Lab_Technical.md") { Move-Item -Path "docs\CNC_Saw_Lab_Technical.md" -Destination "docs\archive\2025-12\misc\CNC_Saw_Lab_Technical.md" -Force }
if (Test-Path "CODE_POLICY_ENFORCEMENT_PLAN.md") { Move-Item -Path "CODE_POLICY_ENFORCEMENT_PLAN.md" -Destination "docs\archive\2025-12\misc\CODE_POLICY_ENFORCEMENT_PLAN.md" -Force }
if (Test-Path "CODE_POLICY_VIOLATIONS_REPORT.md") { Move-Item -Path "CODE_POLICY_VIOLATIONS_REPORT.md" -Destination "docs\archive\2025-12\reports\CODE_POLICY_VIOLATIONS_REPORT.md" -Force }
if (Test-Path "docs\COMPARELAB_B22_8_GUARDRAIL_SYSTEM.md") { Move-Item -Path "docs\COMPARELAB_B22_8_GUARDRAIL_SYSTEM.md" -Destination "docs\archive\2025-12\misc\COMPARELAB_B22_8_GUARDRAIL_SYSTEM.md" -Force }
if (Test-Path "docs\COMPARELAB_B22_ARC_COMPLETE.md") { Move-Item -Path "docs\COMPARELAB_B22_ARC_COMPLETE.md" -Destination "docs\archive\2025-12\misc\COMPARELAB_B22_ARC_COMPLETE.md" -Force }
if (Test-Path "docs\COMPARELAB_BRANCH_WORKFLOW.md") { Move-Item -Path "docs\COMPARELAB_BRANCH_WORKFLOW.md" -Destination "docs\archive\2025-12\misc\COMPARELAB_BRANCH_WORKFLOW.md" -Force }
if (Test-Path "docs\COMPARELAB_DEV_CHECKLIST.md") { Move-Item -Path "docs\COMPARELAB_DEV_CHECKLIST.md" -Destination "docs\archive\2025-12\misc\COMPARELAB_DEV_CHECKLIST.md" -Force }
if (Test-Path "docs\COMPARELAB_GOLDEN_SYSTEM.md") { Move-Item -Path "docs\COMPARELAB_GOLDEN_SYSTEM.md" -Destination "docs\archive\2025-12\misc\COMPARELAB_GOLDEN_SYSTEM.md" -Force }
if (Test-Path "docs\COMPARELAB_GUARDRAILS.md") { Move-Item -Path "docs\COMPARELAB_GUARDRAILS.md" -Destination "docs\archive\2025-12\misc\COMPARELAB_GUARDRAILS.md" -Force }
if (Test-Path "docs\COMPARELAB_REPORTS.md") { Move-Item -Path "docs\COMPARELAB_REPORTS.md" -Destination "docs\archive\2025-12\reports\COMPARELAB_REPORTS.md" -Force }
if (Test-Path "COMPARE_MODE_DEVELOPER_HANDOFF.md") { Move-Item -Path "COMPARE_MODE_DEVELOPER_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\COMPARE_MODE_DEVELOPER_HANDOFF.md" -Force }
if (Test-Path "COMPLETE_CODE_EXTRACTION.md") { Move-Item -Path "COMPLETE_CODE_EXTRACTION.md" -Destination "docs\archive\2025-12\misc\COMPLETE_CODE_EXTRACTION.md" -Force }
if (Test-Path "COMPLETE_TESTING_STRATEGY.md") { Move-Item -Path "COMPLETE_TESTING_STRATEGY.md" -Destination "docs\archive\2025-12\misc\COMPLETE_TESTING_STRATEGY.md" -Force }
if (Test-Path "CONCISE ANALYSIS.md") { Move-Item -Path "CONCISE ANALYSIS.md" -Destination "docs\archive\2025-12\misc\CONCISE ANALYSIS.md" -Force }
if (Test-Path "CONFIDENTIAL_MESH_PIPELINE_PATENT.md") { Move-Item -Path "CONFIDENTIAL_MESH_PIPELINE_PATENT.md" -Destination "docs\archive\2025-12\misc\CONFIDENTIAL_MESH_PIPELINE_PATENT.md" -Force }
if (Test-Path "CONSOLIDATION_PHASE.md") { Move-Item -Path "CONSOLIDATION_PHASE.md" -Destination "docs\archive\2025-12\misc\CONSOLIDATION_PHASE.md" -Force }
if (Test-Path "CONTRIBUTORS.md") { Move-Item -Path "CONTRIBUTORS.md" -Destination "docs\archive\2025-12\misc\CONTRIBUTORS.md" -Force }
if (Test-Path "CP_S50_SAW_BLADE_REGISTRY.md") { Move-Item -Path "CP_S50_SAW_BLADE_REGISTRY.md" -Destination "docs\archive\2025-12\misc\CP_S50_SAW_BLADE_REGISTRY.md" -Force }
if (Test-Path "CP_S51_SAW_BLADE_VALIDATOR.md") { Move-Item -Path "CP_S51_SAW_BLADE_VALIDATOR.md" -Destination "docs\archive\2025-12\misc\CP_S51_SAW_BLADE_VALIDATOR.md" -Force }
if (Test-Path "CP_S53_SAW_OPERATION_PANELS.md") { Move-Item -Path "CP_S53_SAW_OPERATION_PANELS.md" -Destination "docs\archive\2025-12\misc\CP_S53_SAW_OPERATION_PANELS.md" -Force }
if (Test-Path "CURRENT_INIT_PY_CONTENTS.md") { Move-Item -Path "CURRENT_INIT_PY_CONTENTS.md" -Destination "docs\archive\2025-12\misc\CURRENT_INIT_PY_CONTENTS.md" -Force }
if (Test-Path "CURRENT_STATE_REALITY_CHECK.md") { Move-Item -Path "CURRENT_STATE_REALITY_CHECK.md" -Destination "docs\archive\2025-12\misc\CURRENT_STATE_REALITY_CHECK.md" -Force }
if (Test-Path "CURVELAB_FINAL_PATCHES_INTEGRATION.md") { Move-Item -Path "CURVELAB_FINAL_PATCHES_INTEGRATION.md" -Destination "docs\archive\2025-12\integration\CURVELAB_FINAL_PATCHES_INTEGRATION.md" -Force }
if (Test-Path "CURVEMATH_INTEGRATION.md") { Move-Item -Path "CURVEMATH_INTEGRATION.md" -Destination "docs\archive\2025-12\integration\CURVEMATH_INTEGRATION.md" -Force }
if (Test-Path "Calculator_Spine_Overview.md") { Move-Item -Path "Calculator_Spine_Overview.md" -Destination "docs\archive\2025-12\misc\Calculator_Spine_Overview.md" -Force }
if (Test-Path "DASHBOARD_ENHANCEMENT_COMPLETE.md") { Move-Item -Path "DASHBOARD_ENHANCEMENT_COMPLETE.md" -Destination "docs\archive\2025-12\misc\DASHBOARD_ENHANCEMENT_COMPLETE.md" -Force }
if (Test-Path "DATA_REGISTRY_INTEGRATION_PLAN.md") { Move-Item -Path "DATA_REGISTRY_INTEGRATION_PLAN.md" -Destination "docs\archive\2025-12\integration\DATA_REGISTRY_INTEGRATION_PLAN.md" -Force }
if (Test-Path "DATA_REGISTRY_PHASE1_COMPLETE.md") { Move-Item -Path "DATA_REGISTRY_PHASE1_COMPLETE.md" -Destination "docs\archive\2025-12\misc\DATA_REGISTRY_PHASE1_COMPLETE.md" -Force }
if (Test-Path "DATA_REGISTRY_PHASE2_COMPLETE.md") { Move-Item -Path "DATA_REGISTRY_PHASE2_COMPLETE.md" -Destination "docs\archive\2025-12\misc\DATA_REGISTRY_PHASE2_COMPLETE.md" -Force }
if (Test-Path "DEPRECATED_SUBSYSTEMS.md") { Move-Item -Path "DEPRECATED_SUBSYSTEMS.md" -Destination "docs\archive\2025-12\misc\DEPRECATED_SUBSYSTEMS.md" -Force }
if (Test-Path "DEVELOPER_HANDOFF (1).md") { Move-Item -Path "DEVELOPER_HANDOFF (1).md" -Destination "docs\archive\2025-12\handoffs\DEVELOPER_HANDOFF (1).md" -Force }
if (Test-Path "DEVELOPER_HANDOFF.md") { Move-Item -Path "DEVELOPER_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\DEVELOPER_HANDOFF.md" -Force }
if (Test-Path "docs\DEVELOPER_HANDOFF_N16_COMPLETE.md") { Move-Item -Path "docs\DEVELOPER_HANDOFF_N16_COMPLETE.md" -Destination "docs\archive\2025-12\handoffs\DEVELOPER_HANDOFF_N16_COMPLETE.md" -Force }
if (Test-Path "docs\DEVELOPER_ONBOARDING.md") { Move-Item -Path "docs\DEVELOPER_ONBOARDING.md" -Destination "docs\archive\2025-12\misc\DEVELOPER_ONBOARDING.md" -Force }
if (Test-Path "docs\DEVELOPMENT_CHECKPOINT_GUIDE.md") { Move-Item -Path "docs\DEVELOPMENT_CHECKPOINT_GUIDE.md" -Destination "docs\archive\2025-12\misc\DEVELOPMENT_CHECKPOINT_GUIDE.md" -Force }
if (Test-Path "docs\DEVELOPMENT_REVIEW_2025_11_25.md") { Move-Item -Path "docs\DEVELOPMENT_REVIEW_2025_11_25.md" -Destination "docs\archive\2025-12\misc\DEVELOPMENT_REVIEW_2025_11_25.md" -Force }
if (Test-Path "DEV_CHECKLIST_ART_STUDIO_ROSETTE.md") { Move-Item -Path "DEV_CHECKLIST_ART_STUDIO_ROSETTE.md" -Destination "docs\archive\2025-12\misc\DEV_CHECKLIST_ART_STUDIO_ROSETTE.md" -Force }
if (Test-Path "DEV_ONBOARDING_CAM.md") { Move-Item -Path "DEV_ONBOARDING_CAM.md" -Destination "docs\archive\2025-12\misc\DEV_ONBOARDING_CAM.md" -Force }
if (Test-Path "DEV_QUICKSTART.md") { Move-Item -Path "DEV_QUICKSTART.md" -Destination "docs\archive\2025-12\misc\DEV_QUICKSTART.md" -Force }
if (Test-Path "DOCKER_SETUP.md") { Move-Item -Path "DOCKER_SETUP.md" -Destination "docs\archive\2025-12\misc\DOCKER_SETUP.md" -Force }
if (Test-Path "DOCUMENTATION_POLISH_SESSION_SUMMARY.md") { Move-Item -Path "DOCUMENTATION_POLISH_SESSION_SUMMARY.md" -Destination "docs\archive\2025-12\sessions\DOCUMENTATION_POLISH_SESSION_SUMMARY.md" -Force }
if (Test-Path "DXF_ADAPTIVE_INTEGRATION_GUIDE.md") { Move-Item -Path "DXF_ADAPTIVE_INTEGRATION_GUIDE.md" -Destination "docs\archive\2025-12\integration\DXF_ADAPTIVE_INTEGRATION_GUIDE.md" -Force }
if (Test-Path "DXF_SECURITY_PATCH_DEPLOYMENT_COMPLETE.md") { Move-Item -Path "DXF_SECURITY_PATCH_DEPLOYMENT_COMPLETE.md" -Destination "docs\archive\2025-12\misc\DXF_SECURITY_PATCH_DEPLOYMENT_COMPLETE.md" -Force }
if (Test-Path "DXF_SECURITY_PATCH_DEPLOYMENT_SUMMARY.md") { Move-Item -Path "DXF_SECURITY_PATCH_DEPLOYMENT_SUMMARY.md" -Destination "docs\archive\2025-12\misc\DXF_SECURITY_PATCH_DEPLOYMENT_SUMMARY.md" -Force }
if (Test-Path "DXF_SECURITY_PATCH_FINAL_REPORT.md") { Move-Item -Path "DXF_SECURITY_PATCH_FINAL_REPORT.md" -Destination "docs\archive\2025-12\reports\DXF_SECURITY_PATCH_FINAL_REPORT.md" -Force }
if (Test-Path "Developer_Handoff_RMOS_AI_Ops_and_Profile_Tuning.md") { Move-Item -Path "Developer_Handoff_RMOS_AI_Ops_and_Profile_Tuning.md" -Destination "docs\archive\2025-12\handoffs\Developer_Handoff_RMOS_AI_Ops_and_Profile_Tuning.md" -Force }
if (Test-Path "ENERGY_ANALYSIS_VERIFICATION.md") { Move-Item -Path "ENERGY_ANALYSIS_VERIFICATION.md" -Destination "docs\archive\2025-12\misc\ENERGY_ANALYSIS_VERIFICATION.md" -Force }
if (Test-Path "EXECUTION_PLAN.md") { Move-Item -Path "EXECUTION_PLAN.md" -Destination "docs\archive\2025-12\misc\EXECUTION_PLAN.md" -Force }
if (Test-Path "EXPORT_DRAWER_INTEGRATION_PHASE1.md") { Move-Item -Path "EXPORT_DRAWER_INTEGRATION_PHASE1.md" -Destination "docs\archive\2025-12\integration\EXPORT_DRAWER_INTEGRATION_PHASE1.md" -Force }
if (Test-Path "EXTRACT_ARCHIVES_SCRIPT.md") { Move-Item -Path "EXTRACT_ARCHIVES_SCRIPT.md" -Destination "docs\archive\2025-12\misc\EXTRACT_ARCHIVES_SCRIPT.md" -Force }
if (Test-Path "docs\FEATURE_DOCUMENTATION_TRACKER.md") { Move-Item -Path "docs\FEATURE_DOCUMENTATION_TRACKER.md" -Destination "docs\archive\2025-12\misc\FEATURE_DOCUMENTATION_TRACKER.md" -Force }
if (Test-Path "FEATURE_REPORT.md") { Move-Item -Path "FEATURE_REPORT.md" -Destination "docs\archive\2025-12\reports\FEATURE_REPORT.md" -Force }
if (Test-Path "FILE_EXTRACTION_STATUS.md") { Move-Item -Path "FILE_EXTRACTION_STATUS.md" -Destination "docs\archive\2025-12\misc\FILE_EXTRACTION_STATUS.md" -Force }
if (Test-Path "FINAL_EXTRACTION_SUMMARY.md") { Move-Item -Path "FINAL_EXTRACTION_SUMMARY.md" -Destination "docs\archive\2025-12\misc\FINAL_EXTRACTION_SUMMARY.md" -Force }
if (Test-Path "FINAL_INTEGRATION_TEST_CHECKLIST.md") { Move-Item -Path "FINAL_INTEGRATION_TEST_CHECKLIST.md" -Destination "docs\archive\2025-12\integration\FINAL_INTEGRATION_TEST_CHECKLIST.md" -Force }
if (Test-Path "FUNCTIONAL_VERIFICATION_MATRIX.md") { Move-Item -Path "FUNCTIONAL_VERIFICATION_MATRIX.md" -Destination "docs\archive\2025-12\misc\FUNCTIONAL_VERIFICATION_MATRIX.md" -Force }
if (Test-Path "GCODE_GENERATION_SYSTEMS_ANALYSIS.md") { Move-Item -Path "GCODE_GENERATION_SYSTEMS_ANALYSIS.md" -Destination "docs\archive\2025-12\misc\GCODE_GENERATION_SYSTEMS_ANALYSIS.md" -Force }
if (Test-Path "GCODE_READER_ENHANCED.md") { Move-Item -Path "GCODE_READER_ENHANCED.md" -Destination "docs\archive\2025-12\misc\GCODE_READER_ENHANCED.md" -Force }
if (Test-Path "docs\GITHUB_ISSUE_TEMPLATES_QUICKSTART.md") { Move-Item -Path "docs\GITHUB_ISSUE_TEMPLATES_QUICKSTART.md" -Destination "docs\archive\2025-12\misc\GITHUB_ISSUE_TEMPLATES_QUICKSTART.md" -Force }
if (Test-Path "GITHUB_PAGES_DEPLOY.md") { Move-Item -Path "GITHUB_PAGES_DEPLOY.md" -Destination "docs\archive\2025-12\misc\GITHUB_PAGES_DEPLOY.md" -Force }
if (Test-Path "GITHUB_PAGES_SETUP_CHECKLIST.md") { Move-Item -Path "GITHUB_PAGES_SETUP_CHECKLIST.md" -Destination "docs\archive\2025-12\misc\GITHUB_PAGES_SETUP_CHECKLIST.md" -Force }
if (Test-Path "GITHUB_VERIFICATION_CHECKLIST.md") { Move-Item -Path "GITHUB_VERIFICATION_CHECKLIST.md" -Destination "docs\archive\2025-12\misc\GITHUB_VERIFICATION_CHECKLIST.md" -Force }
if (Test-Path "GITHUB_VERIFICATION_GUIDE.md") { Move-Item -Path "GITHUB_VERIFICATION_GUIDE.md" -Destination "docs\archive\2025-12\misc\GITHUB_VERIFICATION_GUIDE.md" -Force }
if (Test-Path "GITIGNORE_CRITICAL_FINDINGS.md") { Move-Item -Path "GITIGNORE_CRITICAL_FINDINGS.md" -Destination "docs\archive\2025-12\misc\GITIGNORE_CRITICAL_FINDINGS.md" -Force }
if (Test-Path "GITIGNORE_FIX_VERIFICATION_REPORT.md") { Move-Item -Path "GITIGNORE_FIX_VERIFICATION_REPORT.md" -Destination "docs\archive\2025-12\reports\GITIGNORE_FIX_VERIFICATION_REPORT.md" -Force }
if (Test-Path "GOLDEN_PATH_DEPLOYMENT_COMPLETE.md") { Move-Item -Path "GOLDEN_PATH_DEPLOYMENT_COMPLETE.md" -Destination "docs\archive\2025-12\misc\GOLDEN_PATH_DEPLOYMENT_COMPLETE.md" -Force }
if (Test-Path "GOLDEN_PATH_DEPLOYMENT_PLAN.md") { Move-Item -Path "GOLDEN_PATH_DEPLOYMENT_PLAN.md" -Destination "docs\archive\2025-12\misc\GOLDEN_PATH_DEPLOYMENT_PLAN.md" -Force }
if (Test-Path "docs\GUITAR_MODEL_INVENTORY_REPORT.md") { Move-Item -Path "docs\GUITAR_MODEL_INVENTORY_REPORT.md" -Destination "docs\archive\2025-12\reports\GUITAR_MODEL_INVENTORY_REPORT.md" -Force }
if (Test-Path "Generate the Saw Lab Commit Script.md") { Move-Item -Path "Generate the Saw Lab Commit Script.md" -Destination "docs\archive\2025-12\misc\Generate the Saw Lab Commit Script.md" -Force }
if (Test-Path "GitHub Issue  Task Checklist.md") { Move-Item -Path "GitHub Issue  Task Checklist.md" -Destination "docs\archive\2025-12\misc\GitHub Issue  Task Checklist.md" -Force }
if (Test-Path "HEALTH_CHECK_IMPLEMENTATION.md") { Move-Item -Path "HEALTH_CHECK_IMPLEMENTATION.md" -Destination "docs\archive\2025-12\misc\HEALTH_CHECK_IMPLEMENTATION.md" -Force }
if (Test-Path "HELICAL_BADGES_SYSTEM_COMPLETE.md") { Move-Item -Path "HELICAL_BADGES_SYSTEM_COMPLETE.md" -Destination "docs\archive\2025-12\misc\HELICAL_BADGES_SYSTEM_COMPLETE.md" -Force }
if (Test-Path "HELICAL_POST_PRESETS.md") { Move-Item -Path "HELICAL_POST_PRESETS.md" -Destination "docs\archive\2025-12\misc\HELICAL_POST_PRESETS.md" -Force }
if (Test-Path "HELICAL_V161_STATUS_ASSESSMENT.md") { Move-Item -Path "HELICAL_V161_STATUS_ASSESSMENT.md" -Destination "docs\archive\2025-12\misc\HELICAL_V161_STATUS_ASSESSMENT.md" -Force }
if (Test-Path "IMPLEMENTATION_CHECKLIST.md") { Move-Item -Path "IMPLEMENTATION_CHECKLIST.md" -Destination "docs\archive\2025-12\misc\IMPLEMENTATION_CHECKLIST.md" -Force }
if (Test-Path "IMPLEMENTATION_COMPLETE.md") { Move-Item -Path "IMPLEMENTATION_COMPLETE.md" -Destination "docs\archive\2025-12\misc\IMPLEMENTATION_COMPLETE.md" -Force }
if (Test-Path "INTEGRATION_AUDIT.md") { Move-Item -Path "INTEGRATION_AUDIT.md" -Destination "docs\archive\2025-12\integration\INTEGRATION_AUDIT.md" -Force }
if (Test-Path "docs\INTEGRATION_GUIDE.md") { Move-Item -Path "docs\INTEGRATION_GUIDE.md" -Destination "docs\archive\2025-12\integration\INTEGRATION_GUIDE.md" -Force }
if (Test-Path "Information To Patch Errors.md") { Move-Item -Path "Information To Patch Errors.md" -Destination "docs\archive\2025-12\misc\Information To Patch Errors.md" -Force }
if (Test-Path "Instrument_Geometry_Wave_15_Instrument_Geometry_Data_Migration.md") { Move-Item -Path "Instrument_Geometry_Wave_15_Instrument_Geometry_Data_Migration.md" -Destination "docs\archive\2025-12\waves\Instrument_Geometry_Wave_15_Instrument_Geometry_Data_Migration.md" -Force }
if (Test-Path "JOB_INTELLIGENCE_BUNDLES_14_15_16_COMPLETE.md") { Move-Item -Path "JOB_INTELLIGENCE_BUNDLES_14_15_16_COMPLETE.md" -Destination "docs\archive\2025-12\bundles\JOB_INTELLIGENCE_BUNDLES_14_15_16_COMPLETE.md" -Force }
if (Test-Path "LEAN_EXTRACTION_STRATEGY.md") { Move-Item -Path "LEAN_EXTRACTION_STRATEGY.md" -Destination "docs\archive\2025-12\misc\LEAN_EXTRACTION_STRATEGY.md" -Force }
if (Test-Path "LONG_FILENAMES_REPORT.md") { Move-Item -Path "LONG_FILENAMES_REPORT.md" -Destination "docs\archive\2025-12\reports\LONG_FILENAMES_REPORT.md" -Force }
if (Test-Path "LPMD_Checklist.md") { Move-Item -Path "LPMD_Checklist.md" -Destination "docs\archive\2025-12\misc\LPMD_Checklist.md" -Force }
if (Test-Path "LPMD_Migration_Report_Template.md") { Move-Item -Path "LPMD_Migration_Report_Template.md" -Destination "docs\archive\2025-12\reports\LPMD_Migration_Report_Template.md" -Force }
if (Test-Path "LTB_CALCULATOR_DEPLOYMENT_SUMMARY.md") { Move-Item -Path "LTB_CALCULATOR_DEPLOYMENT_SUMMARY.md" -Destination "docs\archive\2025-12\misc\LTB_CALCULATOR_DEPLOYMENT_SUMMARY.md" -Force }
if (Test-Path "Legacy_Pipeline_Migration_Directive.md") { Move-Item -Path "Legacy_Pipeline_Migration_Directive.md" -Destination "docs\archive\2025-12\misc\Legacy_Pipeline_Migration_Directive.md" -Force }
if (Test-Path "MACHINE_PROFILES_MODULE_M.md") { Move-Item -Path "MACHINE_PROFILES_MODULE_M.md" -Destination "docs\archive\2025-12\misc\MACHINE_PROFILES_MODULE_M.md" -Force }
if (Test-Path "MAIN_PY_IMPORT_AUDIT_REPORT.md") { Move-Item -Path "MAIN_PY_IMPORT_AUDIT_REPORT.md" -Destination "docs\archive\2025-12\reports\MAIN_PY_IMPORT_AUDIT_REPORT.md" -Force }
if (Test-Path "MAIN_PY_ROUTER_INCLUDES_EXPORT.md") { Move-Item -Path "MAIN_PY_ROUTER_INCLUDES_EXPORT.md" -Destination "docs\archive\2025-12\misc\MAIN_PY_ROUTER_INCLUDES_EXPORT.md" -Force }
if (Test-Path "MAIN_SYSTEM_FILES.md") { Move-Item -Path "MAIN_SYSTEM_FILES.md" -Destination "docs\archive\2025-12\misc\MAIN_SYSTEM_FILES.md" -Force }
if (Test-Path "MARATHON_SESSION_EXECUTIVE_REPORT.md") { Move-Item -Path "MARATHON_SESSION_EXECUTIVE_REPORT.md" -Destination "docs\archive\2025-12\sessions\MARATHON_SESSION_EXECUTIVE_REPORT.md" -Force }
if (Test-Path "MASTER_SEGMENTATION_STRATEGY.md") { Move-Item -Path "MASTER_SEGMENTATION_STRATEGY.md" -Destination "docs\archive\2025-12\misc\MASTER_SEGMENTATION_STRATEGY.md" -Force }
if (Test-Path "MERGE_VERIFICATION_REPORT.md") { Move-Item -Path "MERGE_VERIFICATION_REPORT.md" -Destination "docs\archive\2025-12\reports\MERGE_VERIFICATION_REPORT.md" -Force }
if (Test-Path "MONOREPO_DIAGRAM.md") { Move-Item -Path "MONOREPO_DIAGRAM.md" -Destination "docs\archive\2025-12\misc\MONOREPO_DIAGRAM.md" -Force }
if (Test-Path "MONOREPO_SETUP.md") { Move-Item -Path "MONOREPO_SETUP.md" -Destination "docs\archive\2025-12\misc\MONOREPO_SETUP.md" -Force }
if (Test-Path "N0_UI_VALIDATION_CHECKLIST.md") { Move-Item -Path "N0_UI_VALIDATION_CHECKLIST.md" -Destination "docs\archive\2025-12\misc\N0_UI_VALIDATION_CHECKLIST.md" -Force }
if (Test-Path "docs\N10_0_REALTIME_MONITORING_QUICKREF.md") { Move-Item -Path "docs\N10_0_REALTIME_MONITORING_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N10_0_REALTIME_MONITORING_QUICKREF.md" -Force }
if (Test-Path "docs\N10_1_LIVEMONITOR_DRILLDOWN_QUICKREF.md") { Move-Item -Path "docs\N10_1_LIVEMONITOR_DRILLDOWN_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N10_1_LIVEMONITOR_DRILLDOWN_QUICKREF.md" -Force }
if (Test-Path "docs\N10_2_1_SAFETY_FLOW_INTEGRATION_QUICKREF.md") { Move-Item -Path "docs\N10_2_1_SAFETY_FLOW_INTEGRATION_QUICKREF.md" -Destination "docs\archive\2025-12\integration\N10_2_1_SAFETY_FLOW_INTEGRATION_QUICKREF.md" -Force }
if (Test-Path "docs\N10_2_2_MENTOR_OVERRIDE_PANEL_QUICKREF.md") { Move-Item -Path "docs\N10_2_2_MENTOR_OVERRIDE_PANEL_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N10_2_2_MENTOR_OVERRIDE_PANEL_QUICKREF.md" -Force }
if (Test-Path "docs\N10_2_APPRENTICESHIP_MODE_QUICKREF.md") { Move-Item -Path "docs\N10_2_APPRENTICESHIP_MODE_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N10_2_APPRENTICESHIP_MODE_QUICKREF.md" -Force }
if (Test-Path "docs\N11_1_ROSETTE_SCAFFOLDING_QUICKREF.md") { Move-Item -Path "docs\N11_1_ROSETTE_SCAFFOLDING_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N11_1_ROSETTE_SCAFFOLDING_QUICKREF.md" -Force }
if (Test-Path "docs\N11_2_ROSETTE_GEOMETRY_SCAFFOLDING_QUICKREF.md") { Move-Item -Path "docs\N11_2_ROSETTE_GEOMETRY_SCAFFOLDING_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N11_2_ROSETTE_GEOMETRY_SCAFFOLDING_QUICKREF.md" -Force }
if (Test-Path "N11_ROSETTE_SCAFFOLDING_PLAN.md") { Move-Item -Path "N11_ROSETTE_SCAFFOLDING_PLAN.md" -Destination "docs\archive\2025-12\misc\N11_ROSETTE_SCAFFOLDING_PLAN.md" -Force }
if (Test-Path "docs\N12_0_CORE_MATH_SKELETON_QUICKREF.md") { Move-Item -Path "docs\N12_0_CORE_MATH_SKELETON_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N12_0_CORE_MATH_SKELETON_QUICKREF.md" -Force }
if (Test-Path "docs\N12_1_API_WIRING_QUICKREF.md") { Move-Item -Path "docs\N12_1_API_WIRING_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N12_1_API_WIRING_QUICKREF.md" -Force }
if (Test-Path "N12_ROSETTE_ENGINE_PLAN.md") { Move-Item -Path "N12_ROSETTE_ENGINE_PLAN.md" -Destination "docs\archive\2025-12\misc\N12_ROSETTE_ENGINE_PLAN.md" -Force }
if (Test-Path "N13_ROSETTE_UI_DEEP_INTEGRATION.md") { Move-Item -Path "N13_ROSETTE_UI_DEEP_INTEGRATION.md" -Destination "docs\archive\2025-12\integration\N13_ROSETTE_UI_DEEP_INTEGRATION.md" -Force }
if (Test-Path "N14_RMOS_CNC_PIPELINE.md") { Move-Item -Path "N14_RMOS_CNC_PIPELINE.md" -Destination "docs\archive\2025-12\misc\N14_RMOS_CNC_PIPELINE.md" -Force }
if (Test-Path "N14_VALIDATION_FIX_SUMMARY.md") { Move-Item -Path "N14_VALIDATION_FIX_SUMMARY.md" -Destination "docs\archive\2025-12\misc\N14_VALIDATION_FIX_SUMMARY.md" -Force }
if (Test-Path "N15#U2013N18 Frontend Integration Plan.md") { Move-Item -Path "N15#U2013N18 Frontend Integration Plan.md" -Destination "docs\archive\2025-12\integration\N15#U2013N18 Frontend Integration Plan.md" -Force }
if (Test-Path "N15_N18_IMPLEMENTATION_COMPLETE.md") { Move-Item -Path "N15_N18_IMPLEMENTATION_COMPLETE.md" -Destination "docs\archive\2025-12\misc\N15_N18_IMPLEMENTATION_COMPLETE.md" -Force }
if (Test-Path "N15_N18_SESSION_SUMMARY.md") { Move-Item -Path "N15_N18_SESSION_SUMMARY.md" -Destination "docs\archive\2025-12\sessions\N15_N18_SESSION_SUMMARY.md" -Force }
if (Test-Path "N15_RMOS_PRODUCTION_PIPELINE.md") { Move-Item -Path "N15_RMOS_PRODUCTION_PIPELINE.md" -Destination "docs\archive\2025-12\misc\N15_RMOS_PRODUCTION_PIPELINE.md" -Force }
if (Test-Path "N16_N18_FRONTEND_DEVELOPER_HANDOFF.md") { Move-Item -Path "N16_N18_FRONTEND_DEVELOPER_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\N16_N18_FRONTEND_DEVELOPER_HANDOFF.md" -Force }
if (Test-Path "N18_DEPLOYMENT_CHECKLIST.md") { Move-Item -Path "N18_DEPLOYMENT_CHECKLIST.md" -Destination "docs\archive\2025-12\misc\N18_DEPLOYMENT_CHECKLIST.md" -Force }
if (Test-Path "N18_MISSING_COMPONENTS_ARCHITECTURE.md") { Move-Item -Path "N18_MISSING_COMPONENTS_ARCHITECTURE.md" -Destination "docs\archive\2025-12\misc\N18_MISSING_COMPONENTS_ARCHITECTURE.md" -Force }
if (Test-Path "N18_QUICKREF.md") { Move-Item -Path "N18_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N18_QUICKREF.md" -Force }
if (Test-Path "N18_SPIRAL_POLYCUT_QUICKREF.md") { Move-Item -Path "N18_SPIRAL_POLYCUT_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N18_SPIRAL_POLYCUT_QUICKREF.md" -Force }
if (Test-Path "N18_STATUS_REPORT.md") { Move-Item -Path "N18_STATUS_REPORT.md" -Destination "docs\archive\2025-12\reports\N18_STATUS_REPORT.md" -Force }
if (Test-Path "N8_7_ARCHITECTURE.md") { Move-Item -Path "N8_7_ARCHITECTURE.md" -Destination "docs\archive\2025-12\misc\N8_7_ARCHITECTURE.md" -Force }
if (Test-Path "N8_7_MIGRATION_COMPLETE.md") { Move-Item -Path "N8_7_MIGRATION_COMPLETE.md" -Destination "docs\archive\2025-12\misc\N8_7_MIGRATION_COMPLETE.md" -Force }
if (Test-Path "docs\N9_0_ANALYTICS_COMPLETE.md") { Move-Item -Path "docs\N9_0_ANALYTICS_COMPLETE.md" -Destination "docs\archive\2025-12\misc\N9_0_ANALYTICS_COMPLETE.md" -Force }
if (Test-Path "docs\N9_0_ANALYTICS_QUICKREF.md") { Move-Item -Path "docs\N9_0_ANALYTICS_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N9_0_ANALYTICS_QUICKREF.md" -Force }
if (Test-Path "docs\N9_1_ADVANCED_ANALYTICS_QUICKREF.md") { Move-Item -Path "docs\N9_1_ADVANCED_ANALYTICS_QUICKREF.md" -Destination "docs\archive\2025-12\misc\N9_1_ADVANCED_ANALYTICS_QUICKREF.md" -Force }
if (Test-Path "docs\N9_1_ADVANCED_ANALYTICS_SUMMARY.md") { Move-Item -Path "docs\N9_1_ADVANCED_ANALYTICS_SUMMARY.md" -Destination "docs\archive\2025-12\misc\N9_1_ADVANCED_ANALYTICS_SUMMARY.md" -Force }
if (Test-Path "NECKLAB_PRESET_LOADING_COMPLETE.md") { Move-Item -Path "NECKLAB_PRESET_LOADING_COMPLETE.md" -Destination "docs\archive\2025-12\misc\NECKLAB_PRESET_LOADING_COMPLETE.md" -Force }
if (Test-Path "NECK_CONTEXT_WIRING_COMPLETE.md") { Move-Item -Path "NECK_CONTEXT_WIRING_COMPLETE.md" -Destination "docs\archive\2025-12\misc\NECK_CONTEXT_WIRING_COMPLETE.md" -Force }
if (Test-Path "docs\NECK_PROFILE_BUNDLE_ANALYSIS.md") { Move-Item -Path "docs\NECK_PROFILE_BUNDLE_ANALYSIS.md" -Destination "docs\archive\2025-12\bundles\NECK_PROFILE_BUNDLE_ANALYSIS.md" -Force }
if (Test-Path "docs\NECK_PROFILE_QUICKSTART.md") { Move-Item -Path "docs\NECK_PROFILE_QUICKSTART.md" -Destination "docs\archive\2025-12\misc\NECK_PROFILE_QUICKSTART.md" -Force }
if (Test-Path "NEXT_TASK_DECISION.md") { Move-Item -Path "NEXT_TASK_DECISION.md" -Destination "docs\archive\2025-12\misc\NEXT_TASK_DECISION.md" -Force }
if (Test-Path "OPTION_A_CODE_INVENTORY.md") { Move-Item -Path "OPTION_A_CODE_INVENTORY.md" -Destination "docs\archive\2025-12\misc\OPTION_A_CODE_INVENTORY.md" -Force }
if (Test-Path "OPTION_A_VALIDATION_REPORT.md") { Move-Item -Path "OPTION_A_VALIDATION_REPORT.md" -Destination "docs\archive\2025-12\reports\OPTION_A_VALIDATION_REPORT.md" -Force }
if (Test-Path "docs\OPTION_B_DAY1_SUMMARY.md") { Move-Item -Path "docs\OPTION_B_DAY1_SUMMARY.md" -Destination "docs\archive\2025-12\misc\OPTION_B_DAY1_SUMMARY.md" -Force }
if (Test-Path "ORPHANED_CLIENT_FILES_INVENTORY.md") { Move-Item -Path "ORPHANED_CLIENT_FILES_INVENTORY.md" -Destination "docs\archive\2025-12\misc\ORPHANED_CLIENT_FILES_INVENTORY.md" -Force }
if (Test-Path "ORPHAN_AUDIT_2025-12-14.md") { Move-Item -Path "ORPHAN_AUDIT_2025-12-14.md" -Destination "docs\archive\2025-12\misc\ORPHAN_AUDIT_2025-12-14.md" -Force }
if (Test-Path "Orphaned_Client_Migration_Plan.md") { Move-Item -Path "Orphaned_Client_Migration_Plan.md" -Destination "docs\archive\2025-12\misc\Orphaned_Client_Migration_Plan.md" -Force }
if (Test-Path "P0_1_COMPLETION_CHECKLIST.md") { Move-Item -Path "P0_1_COMPLETION_CHECKLIST.md" -Destination "docs\archive\2025-12\misc\P0_1_COMPLETION_CHECKLIST.md" -Force }
if (Test-Path "P0_1_SHIPPED.md") { Move-Item -Path "P0_1_SHIPPED.md" -Destination "docs\archive\2025-12\misc\P0_1_SHIPPED.md" -Force }
if (Test-Path "P1_4_CAM_ESSENTIALS_PRODUCTION_RELEASE.md") { Move-Item -Path "P1_4_CAM_ESSENTIALS_PRODUCTION_RELEASE.md" -Destination "docs\archive\2025-12\misc\P1_4_CAM_ESSENTIALS_PRODUCTION_RELEASE.md" -Force }
if (Test-Path "P2_1_NECK_GENERATOR_COMPLETE.md") { Move-Item -Path "P2_1_NECK_GENERATOR_COMPLETE.md" -Destination "docs\archive\2025-12\misc\P2_1_NECK_GENERATOR_COMPLETE.md" -Force }
if (Test-Path "PATCHES_A-D_INTEGRATION_GUIDE.md") { Move-Item -Path "PATCHES_A-D_INTEGRATION_GUIDE.md" -Destination "docs\archive\2025-12\patches\PATCHES_A-D_INTEGRATION_GUIDE.md" -Force }
if (Test-Path "PATCHES_A-F_INTEGRATION.md") { Move-Item -Path "PATCHES_A-F_INTEGRATION.md" -Destination "docs\archive\2025-12\patches\PATCHES_A-F_INTEGRATION.md" -Force }
if (Test-Path "PATCHES_G-H0_INTEGRATION.md") { Move-Item -Path "PATCHES_G-H0_INTEGRATION.md" -Destination "docs\archive\2025-12\patches\PATCHES_G-H0_INTEGRATION.md" -Force }
if (Test-Path "PATCHES_G-H0_QUICK_REFERENCE.md") { Move-Item -Path "PATCHES_G-H0_QUICK_REFERENCE.md" -Destination "docs\archive\2025-12\patches\PATCHES_G-H0_QUICK_REFERENCE.md" -Force }
if (Test-Path "PATCHES_I-I1-J_INTEGRATION.md") { Move-Item -Path "PATCHES_I-I1-J_INTEGRATION.md" -Destination "docs\archive\2025-12\patches\PATCHES_I-I1-J_INTEGRATION.md" -Force }
if (Test-Path "PATCHES_I-I1-J_QUICK_REFERENCE.md") { Move-Item -Path "PATCHES_I-I1-J_QUICK_REFERENCE.md" -Destination "docs\archive\2025-12\patches\PATCHES_I-I1-J_QUICK_REFERENCE.md" -Force }
if (Test-Path "PATCHES_I1_2_3_INTEGRATION.md") { Move-Item -Path "PATCHES_I1_2_3_INTEGRATION.md" -Destination "docs\archive\2025-12\patches\PATCHES_I1_2_3_INTEGRATION.md" -Force }
if (Test-Path "PATCHES_I1_2_3_QUICKREF.md") { Move-Item -Path "PATCHES_I1_2_3_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCHES_I1_2_3_QUICKREF.md" -Force }
if (Test-Path "PATCHES_J1-J2_INTEGRATION.md") { Move-Item -Path "PATCHES_J1-J2_INTEGRATION.md" -Destination "docs\archive\2025-12\patches\PATCHES_J1-J2_INTEGRATION.md" -Force }
if (Test-Path "PATCH_K_EXPORT_QUICKREF.md") { Move-Item -Path "PATCH_K_EXPORT_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCH_K_EXPORT_QUICKREF.md" -Force }
if (Test-Path "PATCH_K_POST_AWARE_QUICKREF.md") { Move-Item -Path "PATCH_K_POST_AWARE_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCH_K_POST_AWARE_QUICKREF.md" -Force }
if (Test-Path "PATCH_K_QUICKREF.md") { Move-Item -Path "PATCH_K_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCH_K_QUICKREF.md" -Force }
if (Test-Path "PATCH_L1_COMMANDS.md") { Move-Item -Path "PATCH_L1_COMMANDS.md" -Destination "docs\archive\2025-12\patches\PATCH_L1_COMMANDS.md" -Force }
if (Test-Path "PATCH_L1_QUICKREF.md") { Move-Item -Path "PATCH_L1_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCH_L1_QUICKREF.md" -Force }
if (Test-Path "PATCH_L1_ROBUST_OFFSETTING.md") { Move-Item -Path "PATCH_L1_ROBUST_OFFSETTING.md" -Destination "docs\archive\2025-12\patches\PATCH_L1_ROBUST_OFFSETTING.md" -Force }
if (Test-Path "PATCH_L2_QUICKREF.md") { Move-Item -Path "PATCH_L2_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCH_L2_QUICKREF.md" -Force }
if (Test-Path "PATCH_L2_TRUE_SPIRALIZER.md") { Move-Item -Path "PATCH_L2_TRUE_SPIRALIZER.md" -Destination "docs\archive\2025-12\patches\PATCH_L2_TRUE_SPIRALIZER.md" -Force }
if (Test-Path "PATCH_N01_ROUGHING_POST_MIN.md") { Move-Item -Path "PATCH_N01_ROUGHING_POST_MIN.md" -Destination "docs\archive\2025-12\patches\PATCH_N01_ROUGHING_POST_MIN.md" -Force }
if (Test-Path "PATCH_N03_STANDARDIZATION.md") { Move-Item -Path "PATCH_N03_STANDARDIZATION.md" -Destination "docs\archive\2025-12\patches\PATCH_N03_STANDARDIZATION.md" -Force }
if (Test-Path "PATCH_N04_ROUTER_SNIPPETS.md") { Move-Item -Path "PATCH_N04_ROUTER_SNIPPETS.md" -Destination "docs\archive\2025-12\patches\PATCH_N04_ROUTER_SNIPPETS.md" -Force }
if (Test-Path "PATCH_N05_FANUC_HAAS_INDUSTRIAL.md") { Move-Item -Path "PATCH_N05_FANUC_HAAS_INDUSTRIAL.md" -Destination "docs\archive\2025-12\patches\PATCH_N05_FANUC_HAAS_INDUSTRIAL.md" -Force }
if (Test-Path "PATCH_N06_MODAL_CYCLES.md") { Move-Item -Path "PATCH_N06_MODAL_CYCLES.md" -Destination "docs\archive\2025-12\patches\PATCH_N06_MODAL_CYCLES.md" -Force }
if (Test-Path "PATCH_N07_DRILLING_UI.md") { Move-Item -Path "PATCH_N07_DRILLING_UI.md" -Destination "docs\archive\2025-12\patches\PATCH_N07_DRILLING_UI.md" -Force }
if (Test-Path "PATCH_N08_RETRACT_PATTERNS.md") { Move-Item -Path "PATCH_N08_RETRACT_PATTERNS.md" -Destination "docs\archive\2025-12\patches\PATCH_N08_RETRACT_PATTERNS.md" -Force }
if (Test-Path "PATCH_N09_PROBE_PATTERNS_SVG.md") { Move-Item -Path "PATCH_N09_PROBE_PATTERNS_SVG.md" -Destination "docs\archive\2025-12\patches\PATCH_N09_PROBE_PATTERNS_SVG.md" -Force }
if (Test-Path "PATCH_N0_IMPLEMENTATION_GUIDE.md") { Move-Item -Path "PATCH_N0_IMPLEMENTATION_GUIDE.md" -Destination "docs\archive\2025-12\patches\PATCH_N0_IMPLEMENTATION_GUIDE.md" -Force }
if (Test-Path "PATCH_N0_SMART_POST_SCAFFOLD.md") { Move-Item -Path "PATCH_N0_SMART_POST_SCAFFOLD.md" -Destination "docs\archive\2025-12\patches\PATCH_N0_SMART_POST_SCAFFOLD.md" -Force }
if (Test-Path "PATCH_N10_CAM_ESSENTIALS.md") { Move-Item -Path "PATCH_N10_CAM_ESSENTIALS.md" -Destination "docs\archive\2025-12\patches\PATCH_N10_CAM_ESSENTIALS.md" -Force }
if (Test-Path "PATCH_N11_SCHEMA_FIX.md") { Move-Item -Path "PATCH_N11_SCHEMA_FIX.md" -Destination "docs\archive\2025-12\patches\PATCH_N11_SCHEMA_FIX.md" -Force }
if (Test-Path "PATCH_N12_INDEX.md") { Move-Item -Path "PATCH_N12_INDEX.md" -Destination "docs\archive\2025-12\patches\PATCH_N12_INDEX.md" -Force }
if (Test-Path "PATCH_N12_MACHINE_TOOL_TABLES.md") { Move-Item -Path "PATCH_N12_MACHINE_TOOL_TABLES.md" -Destination "docs\archive\2025-12\patches\PATCH_N12_MACHINE_TOOL_TABLES.md" -Force }
if (Test-Path "PATCH_N12_QUICKREF.md") { Move-Item -Path "PATCH_N12_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCH_N12_QUICKREF.md" -Force }
if (Test-Path "PATCH_N14_INDEX.md") { Move-Item -Path "PATCH_N14_INDEX.md" -Destination "docs\archive\2025-12\patches\PATCH_N14_INDEX.md" -Force }
if (Test-Path "PATCH_N14_QUICKREF.md") { Move-Item -Path "PATCH_N14_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCH_N14_QUICKREF.md" -Force }
if (Test-Path "PATCH_N14_UNIFIED_CAM_SETTINGS.md") { Move-Item -Path "PATCH_N14_UNIFIED_CAM_SETTINGS.md" -Destination "docs\archive\2025-12\patches\PATCH_N14_UNIFIED_CAM_SETTINGS.md" -Force }
if (Test-Path "PATCH_N15_N17_INTEGRATION_PLAN.md") { Move-Item -Path "PATCH_N15_N17_INTEGRATION_PLAN.md" -Destination "docs\archive\2025-12\patches\PATCH_N15_N17_INTEGRATION_PLAN.md" -Force }
if (Test-Path "PATCH_N18_G2G3_LINKERS.md") { Move-Item -Path "PATCH_N18_G2G3_LINKERS.md" -Destination "docs\archive\2025-12\patches\PATCH_N18_G2G3_LINKERS.md" -Force }
if (Test-Path "PATCH_N18_QUICKREF.md") { Move-Item -Path "PATCH_N18_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCH_N18_QUICKREF.md" -Force }
if (Test-Path "PATCH_N_SERIES_ROLLUP.md") { Move-Item -Path "PATCH_N_SERIES_ROLLUP.md" -Destination "docs\archive\2025-12\patches\PATCH_N_SERIES_ROLLUP.md" -Force }
if (Test-Path "PATCH_W_DESIGN_CAM_WORKFLOW.md") { Move-Item -Path "PATCH_W_DESIGN_CAM_WORKFLOW.md" -Destination "docs\archive\2025-12\patches\PATCH_W_DESIGN_CAM_WORKFLOW.md" -Force }
if (Test-Path "PATCH_W_QUICKREF.md") { Move-Item -Path "PATCH_W_QUICKREF.md" -Destination "docs\archive\2025-12\patches\PATCH_W_QUICKREF.md" -Force }
if (Test-Path "PHANTOM_CLEANUP_CONFIRMATION.md") { Move-Item -Path "PHANTOM_CLEANUP_CONFIRMATION.md" -Destination "docs\archive\2025-12\misc\PHANTOM_CLEANUP_CONFIRMATION.md" -Force }
if (Test-Path "PHASE1_DISCOVERY_TIMELINE.md") { Move-Item -Path "PHASE1_DISCOVERY_TIMELINE.md" -Destination "docs\archive\2025-12\phases\PHASE1_DISCOVERY_TIMELINE.md" -Force }
if (Test-Path "PHASE1_EXTRACTION_LOCATION_MISMATCH.md") { Move-Item -Path "PHASE1_EXTRACTION_LOCATION_MISMATCH.md" -Destination "docs\archive\2025-12\phases\PHASE1_EXTRACTION_LOCATION_MISMATCH.md" -Force }
if (Test-Path "PHASE1_EXTRACTION_STATUS.md") { Move-Item -Path "PHASE1_EXTRACTION_STATUS.md" -Destination "docs\archive\2025-12\phases\PHASE1_EXTRACTION_STATUS.md" -Force }
if (Test-Path "PHASE1_NEXT_STEPS.md") { Move-Item -Path "PHASE1_NEXT_STEPS.md" -Destination "docs\archive\2025-12\phases\PHASE1_NEXT_STEPS.md" -Force }
if (Test-Path "PHASE1_PROGRESS_TRACKER.md") { Move-Item -Path "PHASE1_PROGRESS_TRACKER.md" -Destination "docs\archive\2025-12\phases\PHASE1_PROGRESS_TRACKER.md" -Force }
if (Test-Path "PHASE1_QUICK_REFERENCE.md") { Move-Item -Path "PHASE1_QUICK_REFERENCE.md" -Destination "docs\archive\2025-12\phases\PHASE1_QUICK_REFERENCE.md" -Force }
if (Test-Path "PHASE1_SETUP_CHECKLIST.md") { Move-Item -Path "PHASE1_SETUP_CHECKLIST.md" -Destination "docs\archive\2025-12\phases\PHASE1_SETUP_CHECKLIST.md" -Force }
if (Test-Path "PHASE1_TYPESCRIPT_DISCOVERY.md") { Move-Item -Path "PHASE1_TYPESCRIPT_DISCOVERY.md" -Destination "docs\archive\2025-12\phases\PHASE1_TYPESCRIPT_DISCOVERY.md" -Force }
if (Test-Path "PHASE1_VALIDATION_CHECKLIST.md") { Move-Item -Path "PHASE1_VALIDATION_CHECKLIST.md" -Destination "docs\archive\2025-12\phases\PHASE1_VALIDATION_CHECKLIST.md" -Force }
if (Test-Path "PHASE3_2_INTEGRATION_PLAN.md") { Move-Item -Path "PHASE3_2_INTEGRATION_PLAN.md" -Destination "docs\archive\2025-12\phases\PHASE3_2_INTEGRATION_PLAN.md" -Force }
if (Test-Path "PHASE3_2_QUICKREF.md") { Move-Item -Path "PHASE3_2_QUICKREF.md" -Destination "docs\archive\2025-12\phases\PHASE3_2_QUICKREF.md" -Force }
if (Test-Path "PHASE3_2_READY_FOR_TESTING.md") { Move-Item -Path "PHASE3_2_READY_FOR_TESTING.md" -Destination "docs\archive\2025-12\phases\PHASE3_2_READY_FOR_TESTING.md" -Force }
if (Test-Path "PHASE3_3_ADVANCED_VALIDATION_PLAN.md") { Move-Item -Path "PHASE3_3_ADVANCED_VALIDATION_PLAN.md" -Destination "docs\archive\2025-12\phases\PHASE3_3_ADVANCED_VALIDATION_PLAN.md" -Force }
if (Test-Path "PHASE3_3_QUICKSTART.md") { Move-Item -Path "PHASE3_3_QUICKSTART.md" -Destination "docs\archive\2025-12\phases\PHASE3_3_QUICKSTART.md" -Force }
if (Test-Path "PHASE3_INTEGRATION_COMPLETE.md") { Move-Item -Path "PHASE3_INTEGRATION_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE3_INTEGRATION_COMPLETE.md" -Force }
if (Test-Path "PHASE3_REAL_BLUEPRINT_ANALYSIS.md") { Move-Item -Path "PHASE3_REAL_BLUEPRINT_ANALYSIS.md" -Destination "docs\archive\2025-12\phases\PHASE3_REAL_BLUEPRINT_ANALYSIS.md" -Force }
if (Test-Path "PHASE5_PART2_N0_QUICKREF.md") { Move-Item -Path "PHASE5_PART2_N0_QUICKREF.md" -Destination "docs\archive\2025-12\phases\PHASE5_PART2_N0_QUICKREF.md" -Force }
if (Test-Path "PHASE_1_2_PROGRESS_SUMMARY.md") { Move-Item -Path "PHASE_1_2_PROGRESS_SUMMARY.md" -Destination "docs\archive\2025-12\phases\PHASE_1_2_PROGRESS_SUMMARY.md" -Force }
if (Test-Path "PHASE_1_EXECUTION_PLAN.md") { Move-Item -Path "PHASE_1_EXECUTION_PLAN.md" -Destination "docs\archive\2025-12\phases\PHASE_1_EXECUTION_PLAN.md" -Force }
if (Test-Path "PHASE_24_3_24_4_RELIEF_SIM_BRIDGE.md") { Move-Item -Path "PHASE_24_3_24_4_RELIEF_SIM_BRIDGE.md" -Destination "docs\archive\2025-12\phases\PHASE_24_3_24_4_RELIEF_SIM_BRIDGE.md" -Force }
if (Test-Path "PHASE_24_4_QUICKREF.md") { Move-Item -Path "PHASE_24_4_QUICKREF.md" -Destination "docs\archive\2025-12\phases\PHASE_24_4_QUICKREF.md" -Force }
if (Test-Path "PHASE_24_4_RELIEF_SIM_BRIDGE_FRONTEND.md") { Move-Item -Path "PHASE_24_4_RELIEF_SIM_BRIDGE_FRONTEND.md" -Destination "docs\archive\2025-12\phases\PHASE_24_4_RELIEF_SIM_BRIDGE_FRONTEND.md" -Force }
if (Test-Path "PHASE_24_5_MACHINE_ENVELOPE_INTEGRATION.md") { Move-Item -Path "PHASE_24_5_MACHINE_ENVELOPE_INTEGRATION.md" -Destination "docs\archive\2025-12\phases\PHASE_24_5_MACHINE_ENVELOPE_INTEGRATION.md" -Force }
if (Test-Path "PHASE_25_0_QUICKREF.md") { Move-Item -Path "PHASE_25_0_QUICKREF.md" -Destination "docs\archive\2025-12\phases\PHASE_25_0_QUICKREF.md" -Force }
if (Test-Path "PHASE_27_28_INTEGRATION_PLAN.md") { Move-Item -Path "PHASE_27_28_INTEGRATION_PLAN.md" -Destination "docs\archive\2025-12\phases\PHASE_27_28_INTEGRATION_PLAN.md" -Force }
if (Test-Path "PHASE_27_BUNDLE_13_COMPLETION.md") { Move-Item -Path "PHASE_27_BUNDLE_13_COMPLETION.md" -Destination "docs\archive\2025-12\phases\PHASE_27_BUNDLE_13_COMPLETION.md" -Force }
if (Test-Path "PHASE_27_COMPLETE_ANALYSIS.md") { Move-Item -Path "PHASE_27_COMPLETE_ANALYSIS.md" -Destination "docs\archive\2025-12\phases\PHASE_27_COMPLETE_ANALYSIS.md" -Force }
if (Test-Path "PHASE_27_UI_TEST_CHECKLIST.md") { Move-Item -Path "PHASE_27_UI_TEST_CHECKLIST.md" -Destination "docs\archive\2025-12\phases\PHASE_27_UI_TEST_CHECKLIST.md" -Force }
if (Test-Path "PHASE_28_1_INTEGRATION_COMPLETE.md") { Move-Item -Path "PHASE_28_1_INTEGRATION_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_28_1_INTEGRATION_COMPLETE.md" -Force }
if (Test-Path "PHASE_28_2_TIMELINE_COMPLETE.md") { Move-Item -Path "PHASE_28_2_TIMELINE_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_28_2_TIMELINE_COMPLETE.md" -Force }
if (Test-Path "PHASE_2_QUICK_WINS_COMPLETE.md") { Move-Item -Path "PHASE_2_QUICK_WINS_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_2_QUICK_WINS_COMPLETE.md" -Force }
if (Test-Path "PHASE_30_COMPLETION_PATCH.md") { Move-Item -Path "PHASE_30_COMPLETION_PATCH.md" -Destination "docs\archive\2025-12\phases\PHASE_30_COMPLETION_PATCH.md" -Force }
if (Test-Path "PHASE_31_ROSETTE_PARAMETRICS.md") { Move-Item -Path "PHASE_31_ROSETTE_PARAMETRICS.md" -Destination "docs\archive\2025-12\phases\PHASE_31_ROSETTE_PARAMETRICS.md" -Force }
if (Test-Path "PHASE_32_AI_DESIGN_LANE.md") { Move-Item -Path "PHASE_32_AI_DESIGN_LANE.md" -Destination "docs\archive\2025-12\phases\PHASE_32_AI_DESIGN_LANE.md" -Force }
if (Test-Path "PHASE_3_CAM_TYPE_HINTS_COMPLETE.md") { Move-Item -Path "PHASE_3_CAM_TYPE_HINTS_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_3_CAM_TYPE_HINTS_COMPLETE.md" -Force }
if (Test-Path "PHASE_4_BATCH_2_COMPLETE.md") { Move-Item -Path "PHASE_4_BATCH_2_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_4_BATCH_2_COMPLETE.md" -Force }
if (Test-Path "PHASE_4_BATCH_3_COMPLETE.md") { Move-Item -Path "PHASE_4_BATCH_3_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_4_BATCH_3_COMPLETE.md" -Force }
if (Test-Path "PHASE_4_BATCH_3_SUMMARY.md") { Move-Item -Path "PHASE_4_BATCH_3_SUMMARY.md" -Destination "docs\archive\2025-12\phases\PHASE_4_BATCH_3_SUMMARY.md" -Force }
if (Test-Path "PHASE_4_BATCH_4_COMPLETE.md") { Move-Item -Path "PHASE_4_BATCH_4_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_4_BATCH_4_COMPLETE.md" -Force }
if (Test-Path "PHASE_4_BATCH_5_COMPLETE.md") { Move-Item -Path "PHASE_4_BATCH_5_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_4_BATCH_5_COMPLETE.md" -Force }
if (Test-Path "PHASE_4_BATCH_6_COMPLETE.md") { Move-Item -Path "PHASE_4_BATCH_6_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_4_BATCH_6_COMPLETE.md" -Force }
if (Test-Path "PHASE_4_ROUTER_TYPE_HINTS_PROGRESS.md") { Move-Item -Path "PHASE_4_ROUTER_TYPE_HINTS_PROGRESS.md" -Destination "docs\archive\2025-12\phases\PHASE_4_ROUTER_TYPE_HINTS_PROGRESS.md" -Force }
if (Test-Path "PHASE_7_IMPACT_ANALYSIS.md") { Move-Item -Path "PHASE_7_IMPACT_ANALYSIS.md" -Destination "docs\archive\2025-12\phases\PHASE_7_IMPACT_ANALYSIS.md" -Force }
if (Test-Path "PHASE_BC_BUNDLE_EVALUATION.md") { Move-Item -Path "PHASE_BC_BUNDLE_EVALUATION.md" -Destination "docs\archive\2025-12\phases\PHASE_BC_BUNDLE_EVALUATION.md" -Force }
if (Test-Path "PHASE_B_SUMMARY.md") { Move-Item -Path "PHASE_B_SUMMARY.md" -Destination "docs\archive\2025-12\phases\PHASE_B_SUMMARY.md" -Force }
if (Test-Path "PHASE_D_E_DECISIONS.md") { Move-Item -Path "PHASE_D_E_DECISIONS.md" -Destination "docs\archive\2025-12\phases\PHASE_D_E_DECISIONS.md" -Force }
if (Test-Path "PHASE_E_IMPLEMENTATION_COMPLETE.md") { Move-Item -Path "PHASE_E_IMPLEMENTATION_COMPLETE.md" -Destination "docs\archive\2025-12\phases\PHASE_E_IMPLEMENTATION_COMPLETE.md" -Force }
if (Test-Path "PIPELINE_DEVELOPMENT_STRATEGY.md") { Move-Item -Path "PIPELINE_DEVELOPMENT_STRATEGY.md" -Destination "docs\archive\2025-12\misc\PIPELINE_DEVELOPMENT_STRATEGY.md" -Force }
if (Test-Path "POST_CHOOSER_SYSTEM.md") { Move-Item -Path "POST_CHOOSER_SYSTEM.md" -Destination "docs\archive\2025-12\misc\POST_CHOOSER_SYSTEM.md" -Force }
if (Test-Path "PRIORITY_1_COMPLETE_STATUS.md") { Move-Item -Path "PRIORITY_1_COMPLETE_STATUS.md" -Destination "docs\archive\2025-12\misc\PRIORITY_1_COMPLETE_STATUS.md" -Force }
if (Test-Path "PRODUCTION_ARCHITECTURE.md") { Move-Item -Path "PRODUCTION_ARCHITECTURE.md" -Destination "docs\archive\2025-12\misc\PRODUCTION_ARCHITECTURE.md" -Force }
if (Test-Path "PRODUCTION_DEPLOYMENT.md") { Move-Item -Path "PRODUCTION_DEPLOYMENT.md" -Destination "docs\archive\2025-12\misc\PRODUCTION_DEPLOYMENT.md" -Force }
if (Test-Path "PRODUCT_REPO_SETUP.md") { Move-Item -Path "PRODUCT_REPO_SETUP.md" -Destination "docs\archive\2025-12\misc\PRODUCT_REPO_SETUP.md" -Force }
if (Test-Path "PROFILE_N17_SANDBOX_PACKAGE.md") { Move-Item -Path "PROFILE_N17_SANDBOX_PACKAGE.md" -Destination "docs\archive\2025-12\misc\PROFILE_N17_SANDBOX_PACKAGE.md" -Force }
if (Test-Path "docs\PROJECTS_ON_HOLD_INVENTORY.md") { Move-Item -Path "docs\PROJECTS_ON_HOLD_INVENTORY.md" -Destination "docs\archive\2025-12\misc\PROJECTS_ON_HOLD_INVENTORY.md" -Force }
if (Test-Path "PROJECT_COMPLETE_SUMMARY.md") { Move-Item -Path "PROJECT_COMPLETE_SUMMARY.md" -Destination "docs\archive\2025-12\misc\PROJECT_COMPLETE_SUMMARY.md" -Force }
if (Test-Path "Phase 2 Objectives.md") { Move-Item -Path "Phase 2 Objectives.md" -Destination "docs\archive\2025-12\phases\Phase 2 Objectives.md" -Force }
if (Test-Path "Phased Migration of Orphaned Files.md") { Move-Item -Path "Phased Migration of Orphaned Files.md" -Destination "docs\archive\2025-12\phases\Phased Migration of Orphaned Files.md" -Force }
if (Test-Path "Pre-Wave Verification Results.md") { Move-Item -Path "Pre-Wave Verification Results.md" -Destination "docs\archive\2025-12\waves\Pre-Wave Verification Results.md" -Force }
if (Test-Path "Product _ervice_Manual_Drat.md") { Move-Item -Path "Product _ervice_Manual_Drat.md" -Destination "docs\archive\2025-12\misc\Product _ervice_Manual_Drat.md" -Force }
if (Test-Path "Question Concerning the CAM Engine.md") { Move-Item -Path "Question Concerning the CAM Engine.md" -Destination "docs\archive\2025-12\misc\Question Concerning the CAM Engine.md" -Force }
if (Test-Path "Questions Before Execution.md") { Move-Item -Path "Questions Before Execution.md" -Destination "docs\archive\2025-12\misc\Questions Before Execution.md" -Force }
if (Test-Path "Questions_for_Developer_Review.md") { Move-Item -Path "Questions_for_Developer_Review.md" -Destination "docs\archive\2025-12\misc\Questions_for_Developer_Review.md" -Force }
if (Test-Path "docs\README_CAM_SETTINGS_BACKUP.md") { Move-Item -Path "docs\README_CAM_SETTINGS_BACKUP.md" -Destination "docs\archive\2025-12\misc\README_CAM_SETTINGS_BACKUP.md" -Force }
if (Test-Path "README_PHASE1.md") { Move-Item -Path "README_PHASE1.md" -Destination "docs\archive\2025-12\misc\README_PHASE1.md" -Force }
if (Test-Path "README_PUBLIC_GITHUB.md") { Move-Item -Path "README_PUBLIC_GITHUB.md" -Destination "docs\archive\2025-12\misc\README_PUBLIC_GITHUB.md" -Force }
if (Test-Path "RECOVERED_SCRIPTS_INTEGRATION_PLAN.md") { Move-Item -Path "RECOVERED_SCRIPTS_INTEGRATION_PLAN.md" -Destination "docs\archive\2025-12\integration\RECOVERED_SCRIPTS_INTEGRATION_PLAN.md" -Force }
if (Test-Path "REFORESTATION_PLAN.md") { Move-Item -Path "REFORESTATION_PLAN.md" -Destination "docs\archive\2025-12\misc\REFORESTATION_PLAN.md" -Force }
if (Test-Path "REPOSITORY_ERROR_ANALYSIS.md") { Move-Item -Path "REPOSITORY_ERROR_ANALYSIS.md" -Destination "docs\archive\2025-12\misc\REPOSITORY_ERROR_ANALYSIS.md" -Force }
if (Test-Path "REPO_AUDIT_REPORT.md") { Move-Item -Path "REPO_AUDIT_REPORT.md" -Destination "docs\archive\2025-12\reports\REPO_AUDIT_REPORT.md" -Force }
if (Test-Path "REPO_LAYOUT.md") { Move-Item -Path "REPO_LAYOUT.md" -Destination "docs\archive\2025-12\misc\REPO_LAYOUT.md" -Force }
if (Test-Path "REPO_STATUS_REPORT_2025-12-14.md") { Move-Item -Path "REPO_STATUS_REPORT_2025-12-14.md" -Destination "docs\archive\2025-12\reports\REPO_STATUS_REPORT_2025-12-14.md" -Force }
if (Test-Path "REPO_STRUCTURE_SUMMARY.md") { Move-Item -Path "REPO_STRUCTURE_SUMMARY.md" -Destination "docs\archive\2025-12\misc\REPO_STRUCTURE_SUMMARY.md" -Force }
if (Test-Path "RMOS 2.0 #U2014 Rosette Manufacturing Operating System.md") { Move-Item -Path "RMOS 2.0 #U2014 Rosette Manufacturing Operating System.md" -Destination "docs\archive\2025-12\misc\RMOS 2.0 #U2014 Rosette Manufacturing Operating System.md" -Force }
if (Test-Path "RMOS_2_0_IMPLEMENTATION_QUICKREF.md") { Move-Item -Path "RMOS_2_0_IMPLEMENTATION_QUICKREF.md" -Destination "docs\archive\2025-12\misc\RMOS_2_0_IMPLEMENTATION_QUICKREF.md" -Force }
if (Test-Path "RMOS_AI_Profile_Tuning_Handoff.md") { Move-Item -Path "RMOS_AI_Profile_Tuning_Handoff.md" -Destination "docs\archive\2025-12\handoffs\RMOS_AI_Profile_Tuning_Handoff.md" -Force }
if (Test-Path "RMOS_Developer_Onboarding.md") { Move-Item -Path "RMOS_Developer_Onboarding.md" -Destination "docs\archive\2025-12\misc\RMOS_Developer_Onboarding.md" -Force }
if (Test-Path "RMOS_Directional_Workflow_2_0.md") { Move-Item -Path "RMOS_Directional_Workflow_2_0.md" -Destination "docs\archive\2025-12\misc\RMOS_Directional_Workflow_2_0.md" -Force }
if (Test-Path "RMOS_MASTER_DEVELOPMENT_TRACKER.md") { Move-Item -Path "RMOS_MASTER_DEVELOPMENT_TRACKER.md" -Destination "docs\archive\2025-12\misc\RMOS_MASTER_DEVELOPMENT_TRACKER.md" -Force }
if (Test-Path "docs\RMOS_MASTER_TREE.md") { Move-Item -Path "docs\RMOS_MASTER_TREE.md" -Destination "docs\archive\2025-12\misc\RMOS_MASTER_TREE.md" -Force }
if (Test-Path "docs\RMOS_N8_N10_ARCHITECTURE.md") { Move-Item -Path "docs\RMOS_N8_N10_ARCHITECTURE.md" -Destination "docs\archive\2025-12\misc\RMOS_N8_N10_ARCHITECTURE.md" -Force }
if (Test-Path "docs\RMOS_Onboarding.md") { Move-Item -Path "docs\RMOS_Onboarding.md" -Destination "docs\archive\2025-12\misc\RMOS_Onboarding.md" -Force }
if (Test-Path "docs\RMOS_PatchN_Consolidated.md") { Move-Item -Path "docs\RMOS_PatchN_Consolidated.md" -Destination "docs\archive\2025-12\misc\RMOS_PatchN_Consolidated.md" -Force }
if (Test-Path "RMOS_RUNS_INIT_EXPORT.md") { Move-Item -Path "RMOS_RUNS_INIT_EXPORT.md" -Destination "docs\archive\2025-12\misc\RMOS_RUNS_INIT_EXPORT.md" -Force }
if (Test-Path "RMOS_STUDIO.md") { Move-Item -Path "RMOS_STUDIO.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO.md" -Force }
if (Test-Path "RMOS_STUDIO_ALGORITHMS.md") { Move-Item -Path "RMOS_STUDIO_ALGORITHMS.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO_ALGORITHMS.md" -Force }
if (Test-Path "RMOS_STUDIO_API.md") { Move-Item -Path "RMOS_STUDIO_API.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO_API.md" -Force }
if (Test-Path "RMOS_STUDIO_DATA_STRUCTURES.md") { Move-Item -Path "RMOS_STUDIO_DATA_STRUCTURES.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO_DATA_STRUCTURES.md" -Force }
if (Test-Path "RMOS_STUDIO_FAQ.md") { Move-Item -Path "RMOS_STUDIO_FAQ.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO_FAQ.md" -Force }
if (Test-Path "RMOS_STUDIO_SAW_PIPELINE.md") { Move-Item -Path "RMOS_STUDIO_SAW_PIPELINE.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO_SAW_PIPELINE.md" -Force }
if (Test-Path "RMOS_STUDIO_SYSTEM_ARCHITECTURE.md") { Move-Item -Path "RMOS_STUDIO_SYSTEM_ARCHITECTURE.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO_SYSTEM_ARCHITECTURE.md" -Force }
if (Test-Path "RMOS_STUDIO_TUTORIALS.md") { Move-Item -Path "RMOS_STUDIO_TUTORIALS.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO_TUTORIALS.md" -Force }
if (Test-Path "RMOS_STUDIO_UI_LAYOUT.md") { Move-Item -Path "RMOS_STUDIO_UI_LAYOUT.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO_UI_LAYOUT.md" -Force }
if (Test-Path "RMOS_STUDIO_WORKFLOW.md") { Move-Item -Path "RMOS_STUDIO_WORKFLOW.md" -Destination "docs\archive\2025-12\misc\RMOS_STUDIO_WORKFLOW.md" -Force }
if (Test-Path "ROSETTE_ART_STUDIO_INTEGRATION.md") { Move-Item -Path "ROSETTE_ART_STUDIO_INTEGRATION.md" -Destination "docs\archive\2025-12\integration\ROSETTE_ART_STUDIO_INTEGRATION.md" -Force }
if (Test-Path "ROSETTE_PATTERN_GENERATOR_DEPLOYMENT.md") { Move-Item -Path "ROSETTE_PATTERN_GENERATOR_DEPLOYMENT.md" -Destination "docs\archive\2025-12\misc\ROSETTE_PATTERN_GENERATOR_DEPLOYMENT.md" -Force }
if (Test-Path "ROSETTE_PHOTO_IMPORT_DEPLOYMENT.md") { Move-Item -Path "ROSETTE_PHOTO_IMPORT_DEPLOYMENT.md" -Destination "docs\archive\2025-12\misc\ROSETTE_PHOTO_IMPORT_DEPLOYMENT.md" -Force }
if (Test-Path "ROSETTE_REALITY_CHECK.md") { Move-Item -Path "ROSETTE_REALITY_CHECK.md" -Destination "docs\archive\2025-12\misc\ROSETTE_REALITY_CHECK.md" -Force }
if (Test-Path "ROSETTE_ROUTER_TEST_BUNDLE_SUMMARY.md") { Move-Item -Path "ROSETTE_ROUTER_TEST_BUNDLE_SUMMARY.md" -Destination "docs\archive\2025-12\bundles\ROSETTE_ROUTER_TEST_BUNDLE_SUMMARY.md" -Force }
if (Test-Path "RUN_ARTIFACT_PERSISTENCE.md") { Move-Item -Path "RUN_ARTIFACT_PERSISTENCE.md" -Destination "docs\archive\2025-12\misc\RUN_ARTIFACT_PERSISTENCE.md" -Force }
if (Test-Path "RUN_ARTIFACT_UI_DELTA_PATCH.md") { Move-Item -Path "RUN_ARTIFACT_UI_DELTA_PATCH.md" -Destination "docs\archive\2025-12\misc\RUN_ARTIFACT_UI_DELTA_PATCH.md" -Force }
if (Test-Path "RUN_ARTIFACT_UI_PANEL.md") { Move-Item -Path "RUN_ARTIFACT_UI_PANEL.md" -Destination "docs\archive\2025-12\misc\RUN_ARTIFACT_UI_PANEL.md" -Force }
if (Test-Path "RUN_DIFF_VIEWER.md") { Move-Item -Path "RUN_DIFF_VIEWER.md" -Destination "docs\archive\2025-12\misc\RUN_DIFF_VIEWER.md" -Force }
if (Test-Path "Re-audit_B19= B21_the Export Preset stack.md") { Move-Item -Path "Re-audit_B19= B21_the Export Preset stack.md" -Destination "docs\archive\2025-12\misc\Re-audit_B19= B21_the Export Preset stack.md" -Force }
if (Test-Path "Repo directory trees _Express_Pro_Enterprise.md") { Move-Item -Path "Repo directory trees _Express_Pro_Enterprise.md" -Destination "docs\archive\2025-12\misc\Repo directory trees _Express_Pro_Enterprise.md" -Force }
if (Test-Path "Rosette_Template_Lab_Overview.md") { Move-Item -Path "Rosette_Template_Lab_Overview.md" -Destination "docs\archive\2025-12\misc\Rosette_Template_Lab_Overview.md" -Force }
if (Test-Path "SAW_LAB_EXECUTIVE_HANDOFF.md") { Move-Item -Path "SAW_LAB_EXECUTIVE_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\SAW_LAB_EXECUTIVE_HANDOFF.md" -Force }
if (Test-Path "SAW_LAB_TEST_REPORT_DEC15.md") { Move-Item -Path "SAW_LAB_TEST_REPORT_DEC15.md" -Destination "docs\archive\2025-12\reports\SAW_LAB_TEST_REPORT_DEC15.md" -Force }
if (Test-Path "SAW_LAB_UNTRACKED_FILES_INVENTORY.md") { Move-Item -Path "SAW_LAB_UNTRACKED_FILES_INVENTORY.md" -Destination "docs\archive\2025-12\misc\SAW_LAB_UNTRACKED_FILES_INVENTORY.md" -Force }
if (Test-Path "SECURITY_PATCH_DXF_EVALUATION_REPORT.md") { Move-Item -Path "SECURITY_PATCH_DXF_EVALUATION_REPORT.md" -Destination "docs\archive\2025-12\reports\SECURITY_PATCH_DXF_EVALUATION_REPORT.md" -Force }
if (Test-Path "SERVER_SIDE_FEASIBILITY_ENFORCEMENT.md") { Move-Item -Path "SERVER_SIDE_FEASIBILITY_ENFORCEMENT.md" -Destination "docs\archive\2025-12\misc\SERVER_SIDE_FEASIBILITY_ENFORCEMENT.md" -Force }
if (Test-Path "SESSION_5_SUMMARY.md") { Move-Item -Path "SESSION_5_SUMMARY.md" -Destination "docs\archive\2025-12\sessions\SESSION_5_SUMMARY.md" -Force }
if (Test-Path "SESSION_EXECUTIVE_SUMMARY_DEC17_2025.md") { Move-Item -Path "SESSION_EXECUTIVE_SUMMARY_DEC17_2025.md" -Destination "docs\archive\2025-12\sessions\SESSION_EXECUTIVE_SUMMARY_DEC17_2025.md" -Force }
if (Test-Path "SESSION_EXECUTIVE_SUMMARY_DEC17_2025_BUNDLE31.md") { Move-Item -Path "SESSION_EXECUTIVE_SUMMARY_DEC17_2025_BUNDLE31.md" -Destination "docs\archive\2025-12\sessions\SESSION_EXECUTIVE_SUMMARY_DEC17_2025_BUNDLE31.md" -Force }
if (Test-Path "SESSION_EXECUTIVE_SUMMARY_DEC17_2025_GOVERNANCE_BUNDLE.md") { Move-Item -Path "SESSION_EXECUTIVE_SUMMARY_DEC17_2025_GOVERNANCE_BUNDLE.md" -Destination "docs\archive\2025-12\sessions\SESSION_EXECUTIVE_SUMMARY_DEC17_2025_GOVERNANCE_BUNDLE.md" -Force }
if (Test-Path "SHIELDS_BADGE_SYSTEM.md") { Move-Item -Path "SHIELDS_BADGE_SYSTEM.md" -Destination "docs\archive\2025-12\misc\SHIELDS_BADGE_SYSTEM.md" -Force }
if (Test-Path "SIZE_REGRESSION_CHECK.md") { Move-Item -Path "SIZE_REGRESSION_CHECK.md" -Destination "docs\archive\2025-12\misc\SIZE_REGRESSION_CHECK.md" -Force }
if (Test-Path "STRING_SPACING_CALCULATOR_STATUS.md") { Move-Item -Path "STRING_SPACING_CALCULATOR_STATUS.md" -Destination "docs\archive\2025-12\misc\STRING_SPACING_CALCULATOR_STATUS.md" -Force }
if (Test-Path "STRUCTURAL_TREE_CODE_LIST.md") { Move-Item -Path "STRUCTURAL_TREE_CODE_LIST.md" -Destination "docs\archive\2025-12\misc\STRUCTURAL_TREE_CODE_LIST.md" -Force }
if (Test-Path "SUBSYSTEM_PROMOTION_CHECKLIST.md") { Move-Item -Path "SUBSYSTEM_PROMOTION_CHECKLIST.md" -Destination "docs\archive\2025-12\misc\SUBSYSTEM_PROMOTION_CHECKLIST.md" -Force }
if (Test-Path "SVG_VIEWER_README.md") { Move-Item -Path "SVG_VIEWER_README.md" -Destination "docs\archive\2025-12\misc\SVG_VIEWER_README.md" -Force }
if (Test-Path "SYSTEM_ARCHITECTURE.md") { Move-Item -Path "SYSTEM_ARCHITECTURE.md" -Destination "docs\archive\2025-12\misc\SYSTEM_ARCHITECTURE.md" -Force }
if (Test-Path "Saw Blade Import Playbook.md") { Move-Item -Path "Saw Blade Import Playbook.md" -Destination "docs\archive\2025-12\misc\Saw Blade Import Playbook.md" -Force }
if (Test-Path "Saw Lab 2.0 #U2013 Architecture Overview.md") { Move-Item -Path "Saw Lab 2.0 #U2013 Architecture Overview.md" -Destination "docs\archive\2025-12\misc\Saw Lab 2.0 #U2013 Architecture Overview.md" -Force }
if (Test-Path "Saw Lab 2.0 Code Skeleton.md") { Move-Item -Path "Saw Lab 2.0 Code Skeleton.md" -Destination "docs\archive\2025-12\misc\Saw Lab 2.0 Code Skeleton.md" -Force }
if (Test-Path "SawLab_2_0_Test_Hierarchy.md") { Move-Item -Path "SawLab_2_0_Test_Hierarchy.md" -Destination "docs\archive\2025-12\misc\SawLab_2_0_Test_Hierarchy.md" -Force }
if (Test-Path "SawLab_Saw_Physics_Debugger.md") { Move-Item -Path "SawLab_Saw_Physics_Debugger.md" -Destination "docs\archive\2025-12\misc\SawLab_Saw_Physics_Debugger.md" -Force }
if (Test-Path "Saw_Lab_2_0_Integration_Plan.md") { Move-Item -Path "Saw_Lab_2_0_Integration_Plan.md" -Destination "docs\archive\2025-12\integration\Saw_Lab_2_0_Integration_Plan.md" -Force }
if (Test-Path "Segmentation_Checklist.md") { Move-Item -Path "Segmentation_Checklist.md" -Destination "docs\archive\2025-12\misc\Segmentation_Checklist.md" -Force }
if (Test-Path "TECHNICAL_HANDOFF.md") { Move-Item -Path "TECHNICAL_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\TECHNICAL_HANDOFF.md" -Force }
if (Test-Path "TEST_COVERAGE_KNOWN_ISSUES.md") { Move-Item -Path "TEST_COVERAGE_KNOWN_ISSUES.md" -Destination "docs\archive\2025-12\misc\TEST_COVERAGE_KNOWN_ISSUES.md" -Force }
if (Test-Path "TEST_COVERAGE_NEXT_STEPS.md") { Move-Item -Path "TEST_COVERAGE_NEXT_STEPS.md" -Destination "docs\archive\2025-12\misc\TEST_COVERAGE_NEXT_STEPS.md" -Force }
if (Test-Path "TEST_COVERAGE_PROGRESS.md") { Move-Item -Path "TEST_COVERAGE_PROGRESS.md" -Destination "docs\archive\2025-12\misc\TEST_COVERAGE_PROGRESS.md" -Force }
if (Test-Path "TEST_COVERAGE_SESSION_RESULTS.md") { Move-Item -Path "TEST_COVERAGE_SESSION_RESULTS.md" -Destination "docs\archive\2025-12\sessions\TEST_COVERAGE_SESSION_RESULTS.md" -Force }
if (Test-Path "docs\TEST_SESSION_REPORT_2025_11_25.md") { Move-Item -Path "docs\TEST_SESSION_REPORT_2025_11_25.md" -Destination "docs\archive\2025-12\sessions\TEST_SESSION_REPORT_2025_11_25.md" -Force }
if (Test-Path "TEST_STATUS_REPORT.md") { Move-Item -Path "TEST_STATUS_REPORT.md" -Destination "docs\archive\2025-12\reports\TEST_STATUS_REPORT.md" -Force }
if (Test-Path "THERMAL_REPORT_CSV_LINKS_PATCH.md") { Move-Item -Path "THERMAL_REPORT_CSV_LINKS_PATCH.md" -Destination "docs\archive\2025-12\reports\THERMAL_REPORT_CSV_LINKS_PATCH.md" -Force }
if (Test-Path "THERMAL_REPORT_PATCH.md") { Move-Item -Path "THERMAL_REPORT_PATCH.md" -Destination "docs\archive\2025-12\reports\THERMAL_REPORT_PATCH.md" -Force }
if (Test-Path "TOOLBOX_CAM_ARCHITECTURE_v1.md") { Move-Item -Path "TOOLBOX_CAM_ARCHITECTURE_v1.md" -Destination "docs\archive\2025-12\misc\TOOLBOX_CAM_ARCHITECTURE_v1.md" -Force }
if (Test-Path "TOOLBOX_CAM_DEVELOPER_HANDOFF.md") { Move-Item -Path "TOOLBOX_CAM_DEVELOPER_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\TOOLBOX_CAM_DEVELOPER_HANDOFF.md" -Force }
if (Test-Path "The_ Game_Changer_Insight_Bi-Directional_Work_FLow.md") { Move-Item -Path "The_ Game_Changer_Insight_Bi-Directional_Work_FLow.md" -Destination "docs\archive\2025-12\misc\The_ Game_Changer_Insight_Bi-Directional_Work_FLow.md" -Force }
if (Test-Path "ToolBox_CAM_CAD_Developer_Handoff.md") { Move-Item -Path "ToolBox_CAM_CAD_Developer_Handoff.md" -Destination "docs\archive\2025-12\handoffs\ToolBox_CAM_CAD_Developer_Handoff.md" -Force }
if (Test-Path "Tool_Library_Audit_Checklist.md") { Move-Item -Path "Tool_Library_Audit_Checklist.md" -Destination "docs\archive\2025-12\misc\Tool_Library_Audit_Checklist.md" -Force }
if (Test-Path "docs\UI_NAVIGATION_AUDIT.md") { Move-Item -Path "docs\UI_NAVIGATION_AUDIT.md" -Destination "docs\archive\2025-12\misc\UI_NAVIGATION_AUDIT.md" -Force }
if (Test-Path "UNIFIED_PRESET_INTEGRATION_STATUS.md") { Move-Item -Path "UNIFIED_PRESET_INTEGRATION_STATUS.md" -Destination "docs\archive\2025-12\integration\UNIFIED_PRESET_INTEGRATION_STATUS.md" -Force }
if (Test-Path "UNIFIED_PRESET_SYSTEM_PHASE1_COMPLETE.md") { Move-Item -Path "UNIFIED_PRESET_SYSTEM_PHASE1_COMPLETE.md" -Destination "docs\archive\2025-12\misc\UNIFIED_PRESET_SYSTEM_PHASE1_COMPLETE.md" -Force }
if (Test-Path "UNIT_CONVERSION_VALIDATION_COMPLETE.md") { Move-Item -Path "UNIT_CONVERSION_VALIDATION_COMPLETE.md" -Destination "docs\archive\2025-12\misc\UNIT_CONVERSION_VALIDATION_COMPLETE.md" -Force }
if (Test-Path "UNIVERSAL_GALLERY_README.md") { Move-Item -Path "UNIVERSAL_GALLERY_README.md" -Destination "docs\archive\2025-12\misc\UNIVERSAL_GALLERY_README.md" -Force }
if (Test-Path "UNRESOLVED_TASKS_INVENTORY.md") { Move-Item -Path "UNRESOLVED_TASKS_INVENTORY.md" -Destination "docs\archive\2025-12\misc\UNRESOLVED_TASKS_INVENTORY.md" -Force }
if (Test-Path "UX_NAVIGATION_REDESIGN_TASK.md") { Move-Item -Path "UX_NAVIGATION_REDESIGN_TASK.md" -Destination "docs\archive\2025-12\misc\UX_NAVIGATION_REDESIGN_TASK.md" -Force }
if (Test-Path "VCARVE_ADDON_DEVELOPER_HANDOFF.md") { Move-Item -Path "VCARVE_ADDON_DEVELOPER_HANDOFF.md" -Destination "docs\archive\2025-12\handoffs\VCARVE_ADDON_DEVELOPER_HANDOFF.md" -Force }
if (Test-Path "VERIFICATION_SMOKE_TEST_RESULTS.md") { Move-Item -Path "VERIFICATION_SMOKE_TEST_RESULTS.md" -Destination "docs\archive\2025-12\misc\VERIFICATION_SMOKE_TEST_RESULTS.md" -Force }
if (Test-Path "docs\VISION_ENGINE_COMPLIANCE_ANALYSIS.md") { Move-Item -Path "docs\VISION_ENGINE_COMPLIANCE_ANALYSIS.md" -Destination "docs\archive\2025-12\misc\VISION_ENGINE_COMPLIANCE_ANALYSIS.md" -Force }
if (Test-Path "WAVE15_18_COMPLETE_SUMMARY.md") { Move-Item -Path "WAVE15_18_COMPLETE_SUMMARY.md" -Destination "docs\archive\2025-12\waves\WAVE15_18_COMPLETE_SUMMARY.md" -Force }
if (Test-Path "WAVE16_PHASE_D_GAP_ANALYSIS.md") { Move-Item -Path "WAVE16_PHASE_D_GAP_ANALYSIS.md" -Destination "docs\archive\2025-12\phases\WAVE16_PHASE_D_GAP_ANALYSIS.md" -Force }
if (Test-Path "WAVE17_18_IMPLEMENTATION_PLAN.md") { Move-Item -Path "WAVE17_18_IMPLEMENTATION_PLAN.md" -Destination "docs\archive\2025-12\waves\WAVE17_18_IMPLEMENTATION_PLAN.md" -Force }
if (Test-Path "WAVE17_18_INTEGRATION_AUTHORITY.md") { Move-Item -Path "WAVE17_18_INTEGRATION_AUTHORITY.md" -Destination "docs\archive\2025-12\waves\WAVE17_18_INTEGRATION_AUTHORITY.md" -Force }
if (Test-Path "WAVE17_18_QUESTIONS_ANSWERED.md") { Move-Item -Path "WAVE17_18_QUESTIONS_ANSWERED.md" -Destination "docs\archive\2025-12\waves\WAVE17_18_QUESTIONS_ANSWERED.md" -Force }
if (Test-Path "WAVE17_TODO.md") { Move-Item -Path "WAVE17_TODO.md" -Destination "docs\archive\2025-12\waves\WAVE17_TODO.md" -Force }
if (Test-Path "WAVE19_COMPLETE_SUMMARY.md") { Move-Item -Path "WAVE19_COMPLETE_SUMMARY.md" -Destination "docs\archive\2025-12\waves\WAVE19_COMPLETE_SUMMARY.md" -Force }
if (Test-Path "WAVE19_FAN_FRET_CAM_IMPLEMENTATION.md") { Move-Item -Path "WAVE19_FAN_FRET_CAM_IMPLEMENTATION.md" -Destination "docs\archive\2025-12\waves\WAVE19_FAN_FRET_CAM_IMPLEMENTATION.md" -Force }
if (Test-Path "WAVE19_FOUNDATION_IMPLEMENTATION.md") { Move-Item -Path "WAVE19_FOUNDATION_IMPLEMENTATION.md" -Destination "docs\archive\2025-12\waves\WAVE19_FOUNDATION_IMPLEMENTATION.md" -Force }
if (Test-Path "WAVE19_QUICKREF.md") { Move-Item -Path "WAVE19_QUICKREF.md" -Destination "docs\archive\2025-12\waves\WAVE19_QUICKREF.md" -Force }
if (Test-Path "WAVE_1_6_DEVELOPER_HANDOFF.md") { Move-Item -Path "WAVE_1_6_DEVELOPER_HANDOFF.md" -Destination "docs\archive\2025-12\waves\WAVE_1_6_DEVELOPER_HANDOFF.md" -Force }
if (Test-Path "WAVE_E1_CAM_SECTION_ANALYSIS.md") { Move-Item -Path "WAVE_E1_CAM_SECTION_ANALYSIS.md" -Destination "docs\archive\2025-12\waves\WAVE_E1_CAM_SECTION_ANALYSIS.md" -Force }
if (Test-Path "WAVE_E1_COMPLETE_SUMMARY.md") { Move-Item -Path "WAVE_E1_COMPLETE_SUMMARY.md" -Destination "docs\archive\2025-12\waves\WAVE_E1_COMPLETE_SUMMARY.md" -Force }
if (Test-Path "WIRING_WORKBENCH_INTEGRATION.md") { Move-Item -Path "WIRING_WORKBENCH_INTEGRATION.md" -Destination "docs\archive\2025-12\integration\WIRING_WORKBENCH_INTEGRATION.md" -Force }
if (Test-Path "WORKSPACE_ANALYSIS.md") { Move-Item -Path "WORKSPACE_ANALYSIS.md" -Destination "docs\archive\2025-12\misc\WORKSPACE_ANALYSIS.md" -Force }
if (Test-Path "WORKSPACE_HEALTH_REPORT.md") { Move-Item -Path "WORKSPACE_HEALTH_REPORT.md" -Destination "docs\archive\2025-12\reports\WORKSPACE_HEALTH_REPORT.md" -Force }
if (Test-Path "Wave_12_AI_CAM_UI.md") { Move-Item -Path "Wave_12_AI_CAM_UI.md" -Destination "docs\archive\2025-12\waves\Wave_12_AI_CAM_UI.md" -Force }
if (Test-Path "Yes #U2014 proceed only in packagesclien.md") { Move-Item -Path "Yes #U2014 proceed only in packagesclien.md" -Destination "docs\archive\2025-12\misc\Yes #U2014 proceed only in packagesclien.md" -Force }
if (Test-Path "instrument_Neck_Taper_DXF_Export.md") { Move-Item -Path "instrument_Neck_Taper_DXF_Export.md" -Destination "docs\archive\2025-12\misc\instrument_Neck_Taper_DXF_Export.md" -Force }
if (Test-Path "rmos_runs_schemas.md") { Move-Item -Path "rmos_runs_schemas.md" -Destination "docs\archive\2025-12\misc\rmos_runs_schemas.md" -Force }


Write-Host "  Archive complete:" -ForegroundColor Green
Write-Host "    bundles: 28 files" -ForegroundColor Gray
Write-Host "    handoffs: 18 files" -ForegroundColor Gray
Write-Host "    integration: 27 files" -ForegroundColor Gray
Write-Host "    misc: 224 files" -ForegroundColor Gray
Write-Host "    patches: 41 files" -ForegroundColor Gray
Write-Host "    phases: 50 files" -ForegroundColor Gray
Write-Host "    reports: 25 files" -ForegroundColor Gray
Write-Host "    sessions: 10 files" -ForegroundColor Gray
Write-Host "    waves: 16 files" -ForegroundColor Gray

Write-Host ""

# ============================================================
# PHASE 8: CLEANUP & VERIFICATION
# ============================================================
Write-Host "[PHASE 8] Verification..." -ForegroundColor Yellow

$stats = @{
    "canonical" = (Get-ChildItem -Path "docs\canonical" -Filter "*.md" -ErrorAction SilentlyContinue).Count
    "canonical_governance" = (Get-ChildItem -Path "docs\canonical\governance" -Filter "*.md" -ErrorAction SilentlyContinue).Count
    "advisory" = (Get-ChildItem -Path "docs\advisory" -Filter "*.md" -ErrorAction SilentlyContinue).Count
    "quickref" = (Get-ChildItem -Path "docs\quickref" -Recurse -Filter "*.md" -ErrorAction SilentlyContinue).Count
    "archive" = (Get-ChildItem -Path "docs\archive" -Recurse -Filter "*.md" -ErrorAction SilentlyContinue).Count
    "root" = (Get-ChildItem -Path "." -Filter "*.md" -ErrorAction SilentlyContinue).Count
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CONSOLIDATION COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "GOVERNANCE DESIGNATION:" -ForegroundColor White
Write-Host "  docs/canonical/governance/  - $($stats.canonical_governance) BINDING documents" -ForegroundColor Green
Write-Host "  docs/advisory/              - $($stats.advisory) ADVISORY documents" -ForegroundColor Yellow
Write-Host ""
Write-Host "Final counts:" -ForegroundColor White
Write-Host "  Root:                  $($stats.root) files" -ForegroundColor Gray
Write-Host "  docs/canonical/:       $($stats.canonical) files" -ForegroundColor Green
Write-Host "  docs/canonical/gov/:   $($stats.canonical_governance) files" -ForegroundColor Green
Write-Host "  docs/advisory/:        $($stats.advisory) files" -ForegroundColor Yellow
Write-Host "  docs/quickref/:        $($stats.quickref) files" -ForegroundColor Green
Write-Host "  docs/archive/:         $($stats.archive) files" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Review: git status" -ForegroundColor Gray
Write-Host "  2. Commit: git add -A && git commit -m 'docs: consolidate documentation hierarchy'" -ForegroundColor Gray
Write-Host "  3. Manual: Remove DEVELOPER_HANDOFF_ROADMAP.md (wrong project - EMO Options Bot)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Governance is now officially designated. See CANONICAL_GOVERNANCE_INDEX.md for details." -ForegroundColor Cyan
Write-Host ""

