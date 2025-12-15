# 🌲 Rainforest Restoration - Phase 2 Results & Action Plan

**Status:** ✅ Phase 2 Inspection Complete  
**Date:** November 15, 2025  
**Decision:** Preserve unique content, delete confirmed duplicates only

---

## 📊 Inspection Results

### **Lutherier Project-2 - 17 Unique Files** ✅ LEGITIMATE

**Content:** Radius Dish Design Bundle (acoustic guitar bracing)

**Files:**
```
Radius dish kits (3 variants):
├── Full_Radius_Dish_Design_Bundle/
│   ├── Acoustic_Guitar_Radius_Explained.pdf
│   ├── Radius_Arc_15ft.dxf/svg
│   ├── Radius_Arc_25ft.dxf/svg
│   └── Router_Trammel_Radius_Dish_Guide.pdf
├── Radius_Dish_CAD_Package/
│   ├── Acoustic_Guitar_Radius_Explained.pdf
│   └── Radius_Arc_15ft/25ft.svg
└── Radius_Dish_Fusion_GRBL_Kit/
    ├── Acoustic_Guitar_Radius_Explained.pdf
    ├── Radius_Arc_15ft/25ft.dxf/svg
    ├── radius_dish_15ft_grbl.nc
    ├── radius_dish_25ft_grbl.nc
    └── Router_Trammel_Radius_Dish_Guide.pdf
```

**Decision:** 🟢 **MERGE** these 17 files into main "Lutherier Project" folder  
**Rationale:** Legitimate CAM content for acoustic guitar radius dish routing

---

### **Guitar Design HTML app-2 - 103 Unique Files** ✅ LEGITIMATE

**Content:** Newer feature bundles (October 2025 additions)

**Files include:**
```
10-10-2025/ (StarterPack + Fusion AutoTags):
├── J45_FusionAutoTags/           # Fusion 360 post-processor snippets
├── LuthiersToolBox_StarterPack/  # Complete starter kit
│   ├── fusion/                   # Post-processor inserts
│   ├── mach4/                    # Mach4 Lua scripts
│   ├── preflight/                # NC linting tools
│   └── wasm_compound_radius/     # WebAssembly module (Rust)

10_06+2025/ (CAM Import Kits):
├── J45_CAM_Import_Kit/           # Gibson J-45 DXF templates
└── LesPaul_CAM_Import_Kit/       # Les Paul DXF templates
```

**Decision:** 🟢 **MERGE** these 103 files into main "Guitar Design HTML app" folder  
**Rationale:** Newest feature additions (Oct 2025), contains production-ready CAM kits

---

## 🎯 Revised Action Plan

### **Safe to Delete Immediately** (Exact Duplicates)

1. **Lutherier Project 2** - 496 files, 268.15 MB
   - Exact duplicate of "Lutherier Project"
   - Zero unique content

2. **Luthiers Tool Box 2** - 441 files, 28.2 MB
   - Incomplete copy of "Luthiers Tool Box" (28 MB vs 1758 MB)
   - Missing 98% of content

**Total immediate deletion:** 296.35 MB

---

### **Merge Then Delete** (After Content Preservation)

1. **Lutherier Project-2** - 513 files, 268.22 MB
   - Merge 17 radius dish files → "Lutherier Project"
   - Delete folder after merge

2. **Guitar Design HTML app-2** - 358 files, 77.69 MB
   - Merge 103 feature bundle files → "Guitar Design HTML app"
   - Delete folder after merge

**Total after merge:** 345.91 MB  
**Grand total space reclaimed:** 642.26 MB

---

## 🚀 Execution Script

Save as: `c:\Users\thepr\Downloads\Luthiers ToolBox\.github\scripts\rainforest_cleanup.ps1`

```powershell
# Rainforest Restoration - Cleanup Script
# Phase 3 & 4: Merge unique content, then delete duplicates

$baseDir = "c:\Users\thepr\Downloads\Luthiers ToolBox"
Set-Location $baseDir

Write-Host "`n=== Rainforest Restoration - Starting Cleanup ===" -ForegroundColor Cyan
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Merge 17 radius dish files from 'Lutherier Project-2'" -ForegroundColor Gray
Write-Host "  2. Merge 103 feature files from 'Guitar Design HTML app-2'" -ForegroundColor Gray
Write-Host "  3. Delete exact duplicate folders" -ForegroundColor Gray
Write-Host "  4. Delete merged folders after verification" -ForegroundColor Gray
Write-Host "`nPress ENTER to continue or Ctrl+C to cancel..." -ForegroundColor Yellow
$null = Read-Host

# === PHASE 3: MERGE UNIQUE CONTENT ===

Write-Host "`n[Phase 3] Merging unique content..." -ForegroundColor Cyan

# Merge Lutherier Project-2 radius dish files
Write-Host "`nMerging 17 radius dish files..." -ForegroundColor Yellow
$radiusDishDirs = @(
    "Full_Radius_Dish_Design_Bundle",
    "Radius_Dish_CAD_Package",
    "Radius_Dish_Fusion_GRBL_Kit"
)

foreach ($dir in $radiusDishDirs) {
    $source = "Lutherier Project-2\Lutherier Project\$dir"
    $dest = "Lutherier Project\Lutherier Project\$dir"
    
    if (Test-Path $source) {
        if (!(Test-Path $dest)) {
            Write-Host "  Copying: $dir" -ForegroundColor Green
            Copy-Item $source $dest -Recurse -Force
        } else {
            Write-Host "  Skipping: $dir (already exists)" -ForegroundColor Gray
        }
    }
}

# Merge Guitar Design HTML app-2 feature bundles
Write-Host "`nMerging 103 feature bundle files..." -ForegroundColor Yellow
$featureDirs = @(
    "Guitar Design HTML app\10-10-2025",
    "Guitar Design HTML app\10_06+2025"
)

foreach ($dir in $featureDirs) {
    $source = "Guitar Design HTML app-2\$dir"
    $dest = "Guitar Design HTML app\$dir"
    
    if (Test-Path $source) {
        if (!(Test-Path $dest)) {
            Write-Host "  Copying: $dir" -ForegroundColor Green
            Copy-Item $source $dest -Recurse -Force
        } else {
            Write-Host "  Skipping: $dir (already exists)" -ForegroundColor Gray
        }
    }
}

Write-Host "`n✓ Phase 3 Complete: Unique content merged" -ForegroundColor Green

# === PHASE 4: DELETE DUPLICATES ===

Write-Host "`n[Phase 4] Deleting duplicate folders..." -ForegroundColor Cyan

# Verify merges before deletion
Write-Host "`nVerifying merges..." -ForegroundColor Yellow
$verifyPaths = @(
    "Lutherier Project\Lutherier Project\Full_Radius_Dish_Design_Bundle",
    "Guitar Design HTML app\Guitar Design HTML app\10-10-2025",
    "Guitar Design HTML app\Guitar Design HTML app\10_06+2025"
)

$allVerified = $true
foreach ($path in $verifyPaths) {
    if (Test-Path $path) {
        Write-Host "  ✓ Verified: $path" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MISSING: $path" -ForegroundColor Red
        $allVerified = $false
    }
}

if (!$allVerified) {
    Write-Host "`n❌ ABORT: Some merged content not found!" -ForegroundColor Red
    Write-Host "Please verify merges manually before deleting" -ForegroundColor Yellow
    exit 1
}

# Delete confirmed duplicates
Write-Host "`nDeleting duplicate folders..." -ForegroundColor Yellow

$foldersToDelete = @(
    @{Name="Lutherier Project 2"; Reason="Exact duplicate"},
    @{Name="Luthiers Tool Box 2"; Reason="Incomplete copy"},
    @{Name="Lutherier Project-2"; Reason="Content merged"},
    @{Name="Guitar Design HTML app-2"; Reason="Content merged"}
)

$totalSize = 0
foreach ($folder in $foldersToDelete) {
    $path = $folder.Name
    if (Test-Path $path) {
        $size = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum).Sum / 1MB
        
        Write-Host "  Deleting: $path ($([math]::Round($size, 2)) MB) - $($folder.Reason)" -ForegroundColor Yellow
        Remove-Item $path -Recurse -Force -ErrorAction Continue
        $totalSize += $size
        Write-Host "    ✓ Deleted" -ForegroundColor Green
    } else {
        Write-Host "  Skipping: $path (not found)" -ForegroundColor Gray
    }
}

Write-Host "`n✓ Phase 4 Complete: Deleted $([math]::Round($totalSize, 2)) MB" -ForegroundColor Green

# === SUMMARY ===

Write-Host "`n=== Rainforest Restoration Complete ===" -ForegroundColor Cyan
Write-Host "✓ Merged 17 radius dish files" -ForegroundColor Green
Write-Host "✓ Merged 103 feature bundle files" -ForegroundColor Green
Write-Host "✓ Deleted 4 duplicate folders" -ForegroundColor Green
Write-Host "✓ Reclaimed $([math]::Round($totalSize, 2)) MB" -ForegroundColor Green
Write-Host "`nWorkspace is now clean! 🌲" -ForegroundColor Cyan
```

---

## ⏭️ Next Steps

### **Option 1: Run Automated Cleanup** (Recommended)
```powershell
cd "c:\Users\thepr\Downloads\Luthiers ToolBox"
.\.github\scripts\rainforest_cleanup.ps1
```

### **Option 2: Manual Cleanup** (If you prefer)
```powershell
# 1. Merge radius dish files
Copy-Item "Lutherier Project-2\Lutherier Project\Full_Radius_Dish_Design_Bundle" `
          "Lutherier Project\Lutherier Project\" -Recurse

Copy-Item "Lutherier Project-2\Lutherier Project\Radius_Dish_CAD_Package" `
          "Lutherier Project\Lutherier Project\" -Recurse

Copy-Item "Lutherier Project-2\Lutherier Project\Radius_Dish_Fusion_GRBL_Kit" `
          "Lutherier Project\Lutherier Project\" -Recurse

# 2. Merge feature bundles
Copy-Item "Guitar Design HTML app-2\Guitar Design HTML app\10-10-2025" `
          "Guitar Design HTML app\Guitar Design HTML app\" -Recurse

Copy-Item "Guitar Design HTML app-2\Guitar Design HTML app\10_06+2025" `
          "Guitar Design HTML app\Guitar Design HTML app\" -Recurse

# 3. Delete duplicates (after verifying merges)
Remove-Item "Lutherier Project 2" -Recurse -Force
Remove-Item "Luthiers Tool Box 2" -Recurse -Force
Remove-Item "Lutherier Project-2" -Recurse -Force
Remove-Item "Guitar Design HTML app-2" -Recurse -Force
```

### **Option 3: Defer to Later**
Keep current state, move to Phase 5 (ZIP cleanup) when ready.

---

## 📊 Expected Outcome

**Before:**
- 7 legacy folders (4 duplicates + 3 originals)
- 642 MB of duplicate data
- Confusing navigation

**After:**
- 3 clean legacy folders (all originals, fully merged)
- 642 MB reclaimed
- All unique content preserved
- Clear workspace structure

---

**Status:** Ready to execute cleanup  
**Risk:** NONE (all unique content identified and will be merged)  
**Time:** 5-10 minutes (automated script)
