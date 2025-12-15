# CP-S63 — Saw Blade PDF OCR Extractor

**Status:** ✅ Implementation Ready  
**Priority:** HIGH  
**Dependencies:** pdfplumber>=0.11.0, CP-S50 (Saw Blade Registry)

---

## 🎯 Overview

CP-S63 enables automatic extraction of saw blade specifications from vendor PDFs (Tenryu, Kanefusa, SpeTool, etc.) into the Saw Lab registry. This eliminates manual data entry for 500+ blades across 9 vendor catalogs.

### **Key Features:**
- ✅ Generic PDF table extraction (pdfplumber)
- ✅ Vendor-agnostic header mapping
- ✅ Automatic unit parsing (mm, in, deg)
- ✅ Registry integration (upserts to CP-S50)
- ✅ CLI + optional UI workflow
- ✅ Duplicate detection/update logic

---

## 📁 File Locations

### **Backend:**
```
services/api/app/cam_core/saw_lab/importers/
└── pdf_saw_blade_importer.py
```

### **Scripts (Optional):**
```
services/api/scripts/
└── import_saw_blades_from_pdf.py
```

### **Data Input:**
```
services/api/data/vendor_pdfs/
├── TENRYU_Catalogue_Full_021224.pdf
├── Kanefusa_Saw_Blade_Specifications.pdf
├── SpeTool_Carbide_Spiral_Router_Bit.pdf
├── SpeTool_Tray_Core_Box_Router_Bit.pdf
├── SpeTool_Spoilboard_Surfacing_Bit.pdf
├── SpeTool_2D_3D_Tapered_Router_Bit.pdf
├── SpeTool_V_Groove_Signmaking_Bit.pdf
├── SpeTool_Spiral_Bit_General.pdf
└── Circular_Saw_Blade_Specifications.pdf
```

### **Data Output:**
```
services/api/app/data/cam_core/saw_blades/
├── tenryu_blades.json
├── kanefusa_blades.json
└── spetool_blades.json
```

---

## 🚀 Usage

### **Command-Line Import**

```powershell
# Import Tenryu catalog
cd services/api
python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
  data/vendor_pdfs/TENRYU_Catalogue_Full_021224.pdf `
  --vendor Tenryu

# Import Kanefusa specifications
python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
  data/vendor_pdfs/Kanefusa_Saw_Blade_Specifications.pdf `
  --vendor Kanefusa

# Import SpeTool spiral bits
python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
  data/vendor_pdfs/SpeTool_Carbide_Spiral_Router_Bit.pdf `
  --vendor SpeTool

# Dry-run (JSON output only, no registry upsert)
python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
  data/vendor_pdfs/Kanefusa.pdf `
  --vendor Kanefusa `
  --no-registry > kanefusa_blades.json
```

### **Batch Import (All PDFs)**

```powershell
# PowerShell script to import all 9 PDFs
$pdfs = @(
  @{file="TENRYU_Catalogue_Full_021224.pdf"; vendor="Tenryu"},
  @{file="Kanefusa_Saw_Blade_Specifications.pdf"; vendor="Kanefusa"},
  @{file="SpeTool_Carbide_Spiral_Router_Bit.pdf"; vendor="SpeTool"},
  @{file="SpeTool_Tray_Core_Box_Router_Bit.pdf"; vendor="SpeTool"},
  @{file="SpeTool_Spoilboard_Surfacing_Bit.pdf"; vendor="SpeTool"},
  @{file="SpeTool_2D_3D_Tapered_Router_Bit.pdf"; vendor="SpeTool"},
  @{file="SpeTool_V_Groove_Signmaking_Bit.pdf"; vendor="SpeTool"},
  @{file="SpeTool_Spiral_Bit_General.pdf"; vendor="SpeTool"},
  @{file="Circular_Saw_Blade_Specifications.pdf"; vendor="Generic"}
)

foreach ($pdf in $pdfs) {
  Write-Host "Importing $($pdf.file)..." -ForegroundColor Cyan
  python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
    "data/vendor_pdfs/$($pdf.file)" `
    --vendor $($pdf.vendor)
  Write-Host "✓ Complete" -ForegroundColor Green
}
```

---

## 🔧 How It Works

### **1. Table Extraction**
Uses pdfplumber to find tables on each PDF page:
- Treats row 0 as headers
- Builds `PdfBladeRow` objects with `cells: {header → cell_text}`
- Handles multi-table pages

### **2. Header Mapping**
Maps vendor-specific header names to canonical fields:

| Vendor Headers | Canonical Field |
|----------------|----------------|
| D, dia, diameter | diameter_mm |
| B, kerf, width | kerf_mm |
| B1, plate, body | plate_thickness_mm |
| d2, bore, hole | bore_mm |
| Z, teeth | teeth |
| hook | hook_angle_deg |
| top bevel | top_bevel_angle_deg |
| clearance | clearance_angle_deg |
| application, for | application |
| material | material_family |

### **3. Normalization**
Converts string values to numeric types:
- **Floats:** `"6.5mm"` → `6.5`
- **Ints:** `"48 teeth"` → `48`
- **Units:** Strips units, keeps numeric value
- **Empty cells:** Converts to `None`

### **4. Registry Integration**
Calls `upsert_blades_from_pdf()` from CP-S50 Saw Blade Registry:
- Checks for duplicates by `vendor + model_code`
- Updates existing records if found
- Inserts new records otherwise

---

## 📊 Data Models

### **PdfBladeRow (Raw Extraction)**
```python
class PdfBladeRow(BaseModel):
    vendor: str                    # "Tenryu", "Kanefusa", etc.
    source_pdf: str                # "TENRYU_Catalogue.pdf"
    page_number: int               # 1, 2, 3...
    cells: Dict[str, str]          # {"D": "250", "Kerf": "2.4", ...}
```

### **SawBladeSpec (Normalized)**
```python
class SawBladeSpec(BaseModel):
    vendor: str
    model_code: Optional[str]
    
    # Geometry
    diameter_mm: Optional[float]
    bore_mm: Optional[float]
    teeth: Optional[int]
    kerf_mm: Optional[float]
    plate_thickness_mm: Optional[float]
    
    # Angles
    hook_angle_deg: Optional[float]
    top_bevel_angle_deg: Optional[float]
    clearance_angle_deg: Optional[float]
    tangential_clearance_deg: Optional[float]
    
    # Metadata
    material_family: Optional[str]     # "wood", "melamine", "aluminum"
    application: Optional[str]         # "crosscut", "rip", "scoring"
    
    # Preserve original data for debugging
    raw: Dict[str, Any]
```

---

## 🧪 Testing

### **Unit Tests**
```powershell
# Test header mapping
pytest tests/cam_core/saw_lab/test_pdf_blade_importer.py::test_header_mapping

# Test numeric parsing
pytest tests/cam_core/saw_lab/test_pdf_blade_importer.py::test_numeric_parsing

# Test normalization
pytest tests/cam_core/saw_lab/test_pdf_blade_importer.py::test_normalize_pdf_row
```

### **Integration Tests**
```powershell
# Test each PDF
$pdfs = @(
  "SpeTool_Carbide_Spiral_Router_Bit.pdf",
  "Kanefusa_Saw_Blade_Specifications.pdf",
  "TENRYU_Catalogue_Full_021224.pdf"
)

foreach ($pdf in $pdfs) {
  Write-Host "Testing $pdf..." -ForegroundColor Cyan
  
  $vendor = if ($pdf -like "SpeTool*") { "SpeTool" } 
            elseif ($pdf -like "Kanefusa*") { "Kanefusa" }
            else { "Tenryu" }
  
  python -m app.cam_core.saw_lab.importers.pdf_saw_blade_importer `
    "data/vendor_pdfs/$pdf" `
    --vendor $vendor `
    --no-registry | Out-File "test_output_$vendor.json"
  
  $blades = Get-Content "test_output_$vendor.json" | ConvertFrom-Json
  $count = $blades.Count
  $valid = ($blades | Where-Object { $_.diameter_mm -ne $null }).Count
  
  Write-Host "✓ Extracted $count rows, $valid valid blades" -ForegroundColor Green
}
```

### **Expected Results**

| PDF | Expected Blades | Notes |
|-----|----------------|-------|
| SpeTool Spiral | 40+ | Multiple diameters × materials |
| SpeTool Core Box | 12+ | Bowl bit variations |
| SpeTool V-Groove | 8+ | Signmaking bits |
| Kanefusa Specs | 15+ | Geometry reference table |
| Tenryu Catalog | 180+ | Full product line |
| **Total** | **~500** | All vendors combined |

---

## 🚨 Troubleshooting

### **Issue:** No tables extracted from PDF
**Solution:** PDF may use images instead of text. Check:
```powershell
python -c "
import pdfplumber
with pdfplumber.open('test.pdf') as pdf:
    print(f'Pages: {len(pdf.pages)}')
    print(f'Tables on page 1: {len(pdf.pages[0].extract_tables())}')
    print(f'Text on page 1: {pdf.pages[0].extract_text()[:200]}')
"
```
If text is empty, consider OCR with Tesseract (future bundle).

### **Issue:** Header mapping incorrect
**Solution:** Add vendor-specific mappings in `_header_map()`:
```python
if ch in {"model", "item", "code"}:
    mapped[idx] = "model_code"
```

### **Issue:** Unit parsing fails
**Solution:** Extend `_parse_float()` to handle new unit formats:
```python
# Example: handle "1/4 inch" fractions
if "/" in s:
    numerator, denominator = s.split("/")
    return float(numerator) / float(denominator) * 25.4  # convert to mm
```

### **Issue:** Duplicate blades created
**Solution:** Ensure CP-S50 registry uses unique key:
```python
# In saw_blade_registry.py
def upsert_blades_from_pdf(vendor, blades):
    for blade in blades:
        key = f"{vendor}_{blade['model_code']}"
        # Check if key exists, update or insert
```

---

## 🔗 Integration with Other Bundles

### **CP-S50: Saw Blade Registry**
```python
# CP-S63 calls this after normalization:
from cam_core.saw_lab.saw_blade_registry import upsert_blades_from_pdf

upsert_blades_from_pdf(
    vendor="Tenryu",
    blades=[blade.model_dump() for blade in normalized_specs]
)
```

### **CP-S52: Blade Browser UI**
Imported blades appear automatically in `BladeBrowserPanel.vue`:
```typescript
// Refresh blade list after import
await bladesStore.loadBlades()
```

### **CP-S53/54/55: Saw Operations**
Use imported blades for validation:
```typescript
// In SawContourPanel.vue
const selectedBlade = bladesStore.getBladeById(selectedBladeId)
const minRadius = selectedBlade.diameter_mm / 2 * radiusSafetyFactor
```

---

## 📈 Future Enhancements

### **Image OCR (Tesseract)**
For scanned PDF catalogs:
```python
import pytesseract
from PIL import Image

def extract_text_from_image_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = pytesseract.image_to_string(images[0])
    # Parse text for blade specs
```

### **Machine Learning**
Train model to identify blade parameters without explicit header mapping:
```python
# Future: Use ML to classify columns
from sklearn.ensemble import RandomForestClassifier

def classify_header(header_text: str) -> str:
    # Model predicts: "diameter", "kerf", "teeth", etc.
    pass
```

### **Web UI**
Add "Import PDF" button to blade browser (see CP-S63 Frontend in EXECUTION_PLAN.md).

---

## ✅ Acceptance Criteria

- [ ] pdfplumber extracts tables from all 9 PDFs without crashing
- [ ] Header mapping correctly identifies ≥80% of fields
- [ ] Numeric parsing handles units and converts to floats
- [ ] At least 80% of blade rows successfully normalized
- [ ] Registry integration creates valid SawBladeSpec records
- [ ] CLI prints JSON output with --no-registry flag
- [ ] Duplicate blades update existing records (no duplicates)
- [ ] Batch import script processes all PDFs in <5 minutes
- [ ] Imported blades appear in blade browser UI

---

## 📚 See Also

- [CP-S50: Saw Blade Registry](./CP-S50_Saw_Blade_Registry.md)
- [CP-S51: Tenryu PDF Importer](./CP-S51_Tenryu_Importer.md)
- [CP-S52: Blade Browser UI](./CP-S52_Blade_Browser.md)
- [Execution Plan: Phase 2, Task 2.3](../../EXECUTION_PLAN.md#task-23-create-cp-s63-universal-saw-blade-pdf-ocr)

---

**Status:** ✅ Ready for implementation  
**Estimated Time:** 3 hours (core module) + 2 hours (UI integration)  
**Priority:** HIGH (unlocks 500+ blade catalog)
