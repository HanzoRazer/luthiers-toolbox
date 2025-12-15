# MM-3: PDF Design Sheets — Quick Reference

**Status:** ✅ Implemented  
**Date:** November 29, 2025  
**Module:** Rosette Manufacturing OS (RMOS)  
**Depends On:** MM-0 (Strip Families), MM-2 (CAM Profiles)

---

## 🎯 Overview

MM-3 adds **PDF design sheet generation** for mixed-material rosettes, creating shop-ready documentation with:
- Plan summary (segments, arcs, lines)
- Strip family composition (materials + CAM profiles)
- CAM summary (feed range, fragility, lane hints)
- Machine defaults (optional)

**Key Features:**
- ✅ **ReportLab Integration**: Professional PDF generation with tables and formatting
- ✅ **Text Fallback**: Graceful degradation if reportlab unavailable
- ✅ **CLI Tool**: Generate PDFs from JSON files for testing/automation
- ✅ **API Endpoint**: Download design sheets via REST API
- ✅ **CAM Integration**: Auto-includes MM-2 profile summaries

---

## 📁 Architecture

### **Backend Components**
```
services/api/app/
├── core/rosette_design_sheet.py          # PDF generator with reportlab + text fallback
├── tools/rmos_generate_design_sheet.py   # CLI tool for batch generation
└── api/routes/rosette_design_sheet_api.py # GET /rmos/design-sheet/{plan}/{family}
```

### **Dependencies**
- `reportlab>=4.0.0` (added to `services/api/requirements.txt`)
- MM-0: Strip family schemas and stores
- MM-2: CAM profile registry and summarization

---

## 🔌 Core Functions

### **1. Generate Design Sheet**
```python
from app.core.rosette_design_sheet import generate_rosette_design_sheet
from pathlib import Path

plan = {
    "id": "plan_rosette_001",
    "name": "Classical Guitar Rosette",
    "segments": [
        {"type": "arc", "x1": 0, "y1": 0, "x2": 10, "y2": 0, "cx": 5, "cy": 0, "r": 5},
        {"type": "line", "x1": 10, "y1": 0, "x2": 20, "y2": 0}
    ]
}

strip_family = {
    "id": "sf_wood_shell_copper_01",
    "name": "Rosewood + Abalone + Copper",
    "default_width_mm": 3.5,
    "materials": [
        {
            "key": "mat_rosewood",
            "type": "wood",
            "species": "Indian Rosewood",
            "thickness_mm": 1.2,
            "finish": "polished",
            "cam_profile": "wood_standard"
        },
        {
            "key": "mat_abalone",
            "type": "shell",
            "species": "Abalone",
            "thickness_mm": 0.8,
            "finish": "polished",
            "cam_profile": "shell_inlay"
        }
    ]
}

machine_defaults = {
    "spindle_rpm": 18000,
    "feed_rate_mm_min": 1200,
    "plunge_rate_mm_min": 400,
    "stepdown_mm": 0.6
}

output_path = Path("exports/design_sheets/rosette_001.pdf")
pdf_path = generate_rosette_design_sheet(plan, strip_family, machine_defaults, output_path)
print(f"PDF generated: {pdf_path}")
```

---

## 📄 PDF Contents

### **Section 1: Header**
- Title: "Rosette Design Sheet"
- Generation timestamp (UTC)

### **Section 2: Plan Summary**
```
Plan
  Name       : Classical Guitar Rosette
  Plan ID    : plan_rosette_001
  Segments   : 2 (arcs: 1, lines: 1)
```

### **Section 3: Strip Family Info**
```
Strip Family
  ID         : sf_wood_shell_copper_01
  Name       : Rosewood + Abalone + Copper
  Default width: 3.5 mm
  Description: High-end rosette with exotic inlay materials
```

### **Section 4: Materials Table**
```
Materials
Idx  Type      Species           Thk   Finish        CAM profile
───────────────────────────────────────────────────────────────
01  wood      Indian Rosewood   1.2   polished      wood_standard
02  shell     Abalone           0.8   polished      shell_inlay
03  metal     Copper            0.5   polished      metal_inlay
```

### **Section 5: CAM Summary**
```
CAM summary (inferred from materials)
  Profiles        : wood_standard, shell_inlay, metal_inlay
  Feed range      : 250 – 1200 mm/min
  Worst fragility : 0.85
  Lane hint       : experimental
```

### **Section 6: Machine Defaults** (if provided)
```
Machine defaults
  spindle_rpm       : 18000
  feed_rate_mm_min  : 1200
  plunge_rate_mm_min: 400
  stepdown_mm       : 0.6
```

---

## 🛠️ CLI Tool Usage

### **Basic Usage**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1

python -m app.tools.rmos_generate_design_sheet \
    --plan-json data/rmos/plans/my_plan.json \
    --strip-family-json data/rmos/strip_families/my_family.json \
    --out exports/design_sheets/my_sheet.pdf
```

### **With Machine Defaults**
```powershell
python -m app.tools.rmos_generate_design_sheet \
    --plan-json data/rmos/plans/rosette_001.json \
    --strip-family-json data/rmos/strip_families/sf_wood_shell_copper_01.json \
    --machine-defaults-json data/machines/cnc_01_defaults.json \
    --out exports/design_sheets/rosette_001_sheet.pdf
```

### **Example JSON Files**

**plan.json:**
```json
{
  "id": "plan_rosette_001",
  "name": "Classical Guitar Rosette",
  "segments": [
    {"type": "arc", "x1": 0, "y1": 0, "x2": 10, "y2": 0, "cx": 5, "cy": 0, "r": 5},
    {"type": "line", "x1": 10, "y1": 0, "x2": 20, "y2": 0}
  ]
}
```

**strip_family.json:**
```json
{
  "id": "sf_wood_shell_copper_01",
  "name": "Rosewood + Abalone + Copper",
  "default_width_mm": 3.5,
  "materials": [
    {
      "key": "mat_rosewood",
      "type": "wood",
      "species": "Indian Rosewood",
      "thickness_mm": 1.2,
      "cam_profile": "wood_standard"
    }
  ]
}
```

**machine_defaults.json:**
```json
{
  "spindle_rpm": 18000,
  "feed_rate_mm_min": 1200,
  "plunge_rate_mm_min": 400,
  "stepdown_mm": 0.6
}
```

---

## 🌐 API Endpoint

### **GET `/api/rmos/design-sheet/{plan_id}/{strip_family_id}`**

Download a design sheet PDF for a given plan and strip family.

**Request:**
```http
GET /api/rmos/design-sheet/plan_rosette_001/sf_wood_shell_copper_01
```

**Response:**
- **Content-Type:** `application/pdf`
- **Filename:** `designsheet_plan_rosette_001_sf_wood_shell_copper_01.pdf`
- **Body:** PDF binary data

**Status Codes:**
- `200 OK` - PDF generated successfully
- `404 Not Found` - Plan or strip family not found
- `501 Not Implemented` - Plan store not wired yet (see notes below)

**Example cURL:**
```powershell
curl -o my_sheet.pdf http://localhost:8000/api/rmos/design-sheet/plan_001/sf_wood_shell_copper_01
```

**Example Fetch (JavaScript):**
```typescript
const response = await fetch(
  '/api/rmos/design-sheet/plan_rosette_001/sf_wood_shell_copper_01'
)
const blob = await response.blob()
const url = URL.createObjectURL(blob)
const a = document.createElement('a')
a.href = url
a.download = 'rosette_design_sheet.pdf'
a.click()
```

### **⚠️ Plan Store Not Yet Wired**

The API endpoint currently returns `501 Not Implemented` because the plan store is not yet integrated. To enable:

1. Implement plan persistence (similar to strip families)
2. Wire `_get_plan(plan_id)` in `rosette_design_sheet_api.py`:

```python
def _get_plan(plan_id: str) -> Dict[str, Any]:
    stores = get_rmos_stores()
    plan = stores.rosette_plans.get(plan_id)
    if not plan:
        raise KeyError(f"Plan '{plan_id}' not found")
    return plan
```

---

## 🧪 Testing

### **Test PDF Generation (Python)**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1

python -c "
from app.core.rosette_design_sheet import generate_rosette_design_sheet
from pathlib import Path

plan = {'id': 'test_plan', 'name': 'Test Rosette', 'segments': []}
family = {
    'id': 'test_family',
    'name': 'Test Family',
    'materials': [
        {'key': 'm1', 'type': 'wood', 'species': 'Maple', 'thickness_mm': 1.0}
    ]
}

pdf = generate_rosette_design_sheet(plan, family, {}, Path('test_sheet.pdf'))
print(f'PDF created: {pdf}')
"
```

### **Test CLI Tool**
```powershell
# Create test JSON files
echo '{"id":"test_plan","name":"Test Rosette","segments":[]}' > test_plan.json
echo '{"id":"test_family","name":"Test Family","materials":[{"key":"m1","type":"wood","species":"Maple","thickness_mm":1.0}]}' > test_family.json

# Generate PDF
python -m app.tools.rmos_generate_design_sheet \
    --plan-json test_plan.json \
    --strip-family-json test_family.json \
    --out test_output.pdf

# Check output
ls test_output.pdf
```

### **Test API Endpoint** (Once Plan Store Is Wired)
```powershell
# Create strip family first
curl -X POST http://localhost:8000/api/rmos/strip-families/from-template/sf_wood_shell_copper_01

# Get design sheet (will fail with 501 until plan store is ready)
curl -o sheet.pdf http://localhost:8000/api/rmos/design-sheet/plan_001/sf_wood_shell_copper_01_inst_...
```

---

## 📋 Integration Patterns

### **Pattern 1: Export from Pipeline**
```python
# In pipeline handoff or job completion:
from app.core.rosette_design_sheet import generate_rosette_design_sheet
from pathlib import Path

def on_job_complete(job):
    plan = job['plan']
    strip_family = job['strip_family']
    
    pdf_path = Path(f"exports/jobs/{job['id']}/design_sheet.pdf")
    generate_rosette_design_sheet(plan, strip_family, job['machine_defaults'], pdf_path)
    
    job['attachments'].append(str(pdf_path))
```

### **Pattern 2: Batch Generation**
```python
# Generate sheets for all strip families:
from app.services.rmos_stores import get_rmos_stores
from app.core.rosette_design_sheet import generate_rosette_design_sheet
from pathlib import Path

stores = get_rmos_stores()
families = stores.strip_families.all()

for family in families:
    plan = {"id": f"default_plan", "name": "Default Plan", "segments": []}
    out = Path(f"exports/strip_families/{family['id']}_sheet.pdf")
    generate_rosette_design_sheet(plan, family, {}, out)
    print(f"Generated: {out}")
```

### **Pattern 3: Email Attachment**
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

def email_design_sheet(plan, strip_family, recipient_email):
    pdf_path = generate_rosette_design_sheet(plan, strip_family, {}, Path("temp_sheet.pdf"))
    
    msg = MIMEMultipart()
    msg['Subject'] = f"Design Sheet: {strip_family['name']}"
    msg['From'] = "shop@example.com"
    msg['To'] = recipient_email
    
    with open(pdf_path, 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='pdf')
        attachment.add_header('Content-Disposition', 'attachment', filename=pdf_path.name)
        msg.attach(attachment)
    
    # Send via SMTP...
```

---

## 🎨 Customization

### **Text Fallback (No ReportLab)**
If `reportlab` is not installed, the system generates a text file with `.pdf` extension:

```
Rosette Design Sheet (text fallback)
------------------------------------

[Plan]
  Name     : Classical Guitar Rosette
  Plan ID  : plan_rosette_001
  Segments : 2 (arcs: 1, lines: 1)

[Strip Family]
  ID        : sf_wood_shell_copper_01
  Name      : Rosewood + Abalone + Copper
  Width mm  : 3.5

[Materials]
  01  wood      Indian Rosewood   1.2   polished      wood_standard
  02  shell     Abalone           0.8   polished      shell_inlay

[CAM summary]
  Profiles        : wood_standard, shell_inlay
  Feed range      : 250 – 1200 mm/min
  Worst fragility : 0.85
  Lane hint       : experimental
```

### **HTML Export Alternative**
Modify `_build_text_fallback()` to generate HTML instead:

```python
def _build_html_fallback(...):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Design Sheet</title></head>
    <body>
        <h1>Rosette Design Sheet</h1>
        <h2>Plan: {plan_info['name']}</h2>
        <table>
            <tr><th>Material</th><th>Species</th><th>Thickness</th></tr>
            ...
        </table>
    </body>
    </html>
    """
    return html
```

---

## 🐛 Troubleshooting

### **Issue**: `ModuleNotFoundError: No module named 'reportlab'`
**Solution**: 
```powershell
pip install reportlab>=4.0.0
```

### **Issue**: PDF is blank or only has header
**Solution**: Check that `strip_family['materials']` is not empty and materials have required fields (type, species, thickness_mm).

### **Issue**: API returns 501 Not Implemented
**Solution**: This is expected until plan store is wired. Implement `_get_plan()` function in `rosette_design_sheet_api.py`.

### **Issue**: Text fallback generated instead of PDF
**Solution**: Ensure reportlab is installed. If it's installed but still failing, check for import errors in the console.

### **Issue**: Materials table wraps to next page incorrectly
**Solution**: Adjust page break logic in `generate_rosette_design_sheet()` around line `if y < margin + 40`.

---

## ✅ Integration Checklist

**Backend:**
- [x] Create `core/rosette_design_sheet.py` with PDF generator
- [x] Create `tools/rmos_generate_design_sheet.py` CLI tool
- [x] Create `api/routes/rosette_design_sheet_api.py` API endpoint
- [x] Add `reportlab>=4.0.0` to requirements.txt
- [x] Register router in main.py at `/api/rmos/design-sheet`

**Future Work:**
- [ ] Wire plan store persistence
- [ ] Implement `_get_plan()` in API route
- [ ] Add machine profile integration (fetch defaults from M.4)
- [ ] Add QR code with job ID/URL
- [ ] Add shop logo/branding customization

**Testing:**
- [ ] Unit tests for PDF generation
- [ ] CLI tool smoke tests
- [ ] API endpoint integration tests (once plan store is ready)
- [ ] Verify text fallback when reportlab unavailable

---

## 🚀 Next Steps: MM-4

**MM-4: Risk Model Integration** (Future)
- Per-material risk multipliers based on fragility scores
- Failure mode analysis (brittle shell, thin metal delamination)
- Safety margins and tolerance recommendations
- Lane auto-selection based on combined risk score
- Design sheet section showing risk assessment

---

**Status:** ✅ MM-3 Implementation Complete  
**Next Module:** MM-4 (Risk Model Integration)  
**Dependencies:** MM-0 (Strip Families), MM-2 (CAM Profiles), MM-3 (PDF Design Sheets)
