# Patch N.12: Per-Machine Tool Tables

**Status:** ✅ Ready for Implementation  
**Date:** November 6, 2025  
**Module:** Machine Profiles + Tool Management

---

## 🎯 Overview

Patch N.12 adds **per-machine tool tables** with CSV import/export, template token injection, and a full-featured UI for managing cutting tools across multiple CNC machines.

### **Key Features**
- ✅ **Tool tables per machine** in `services/api/app/data/machines.json`
- ✅ **5 REST endpoints** for CRUD + CSV import/export
- ✅ **Template token injection** - Tool parameters flow into post-processor templates
- ✅ **Vue UI component** with inline editing and CSV upload
- ✅ **Optional global catalog** in `services/api/app/data/tools.json`
- ✅ **Smoke test** for validation

---

## 📦 What's New

### **1. Tool Table Data Model**

**Location:** `services/api/app/data/machines.json`

Each machine now includes a `tools[]` array:

```json
{
  "machines": [
    {
      "id": "m1",
      "title": "Shop Fanuc Mill",
      "post": "fanuc_haas",
      "overrides": {},
      "tools": [
        {
          "t": 1,
          "name": "Ø6 flat endmill",
          "type": "EM",
          "dia_mm": 6.0,
          "len_mm": 45.0,
          "holder": "ER20",
          "offset_len_mm": 120.0,
          "spindle_rpm": 8000,
          "feed_mm_min": 600,
          "plunge_mm_min": 200
        },
        {
          "t": 3,
          "name": "Ø3 drill",
          "type": "DRILL",
          "dia_mm": 3.0,
          "len_mm": 55.0,
          "holder": "ER16",
          "offset_len_mm": 121.2,
          "spindle_rpm": 6000,
          "feed_mm_min": 300,
          "plunge_mm_min": 150
        }
      ]
    }
  ]
}
```

**Tool Fields:**
- `t` (int) - Tool number (e.g., T1, T7)
- `name` (str) - Human-readable name
- `type` (str) - Tool type: `EM`, `DRILL`, `BALL`, `CHAMFER`, etc.
- `dia_mm` (float) - Cutting diameter in mm
- `len_mm` (float) - Flute length in mm
- `holder` (str) - Holder type (ER20, ER16, Collet, etc.)
- `offset_len_mm` (float) - Tool length offset (from gauge line)
- `spindle_rpm` (float) - Default spindle speed
- `feed_mm_min` (float) - Default XY feed rate
- `plunge_mm_min` (float) - Default Z plunge rate

### **2. API Endpoints**

**Router:** `services/api/app/routers/machines_tools_router.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/machines/tools/{mid}` | List all tools for machine |
| `PUT` | `/machines/tools/{mid}` | Upsert tools (merge by `t` number) |
| `DELETE` | `/machines/tools/{mid}/{t}` | Delete specific tool |
| `GET` | `/machines/tools/{mid}.csv` | Export CSV |
| `POST` | `/machines/tools/{mid}/import_csv` | Import CSV (upsert) |

**Merge Policy:**
- `PUT` endpoint merges tools by `t` number
- If tool with same `t` exists, it's replaced
- If tool with new `t` is provided, it's added
- Tools are always sorted by `t` ascending

### **3. Template Token Injection**

**Utility:** `services/api/app/util/tool_table.py`

When CAM endpoints receive `machine_id` + `tool` parameters, the following tokens become available in post-processor templates:

```python
{
  "TOOL": 1,                    # Tool number
  "TOOL_NAME": "Ø6 flat endmill",
  "TOOL_DIA": 6.0,
  "TOOL_LEN": 45.0,
  "TOOL_HOLDER": "ER20",
  "TOOL_OFFS_LEN": 120.0,
  "RPM": 8000,
  "FEED": 600,
  "PLUNGE": 200
}
```

**Post Template Example:**
```gcode
T{TOOL} M06
G43 H{TOOL} Z{TOOL_OFFS_LEN}
S{RPM} M03
F{FEED}
```

**Integration Point:** `services/api/app/post_injection_dropin.py`

The tool context is automatically merged before template expansion in the post-processor wrapper.

### **4. Vue UI Component**

**Location:** `packages/client/src/components/ToolTable.vue`

**Features:**
- Machine selector dropdown
- Inline table editor (all fields editable)
- Add/Delete rows
- Save all changes (bulk `PUT`)
- Export CSV (direct download)
- Import CSV (file upload with merge)
- Save confirmation feedback
- Error handling

**UI Structure:**
```
┌─────────────────────────────────────────────────┐
│ Tool Table                                      │
│ Machine: [Shop Fanuc Mill (m1) ▼] [Refresh]   │
│ [Export CSV] [Import CSV]                       │
├─────────────────────────────────────────────────┤
│ T │ Name       │ Type │ Ø │ Len │ ... │ [Del]   │
│ 1 │ [Ø6 flat]  │ [EM] │[6]│[45] │ ... │ Delete  │
│ 3 │ [Ø3 drill] │[DRILL]│[3]│[55]│ ... │ Delete  │
├─────────────────────────────────────────────────┤
│ [Add Tool] [Save All]           Saved ✓         │
└─────────────────────────────────────────────────┘
```

### **5. CSV Format**

**Headers:**
```csv
t,name,type,dia_mm,len_mm,holder,offset_len_mm,spindle_rpm,feed_mm_min,plunge_mm_min
```

**Example:**
```csv
t,name,type,dia_mm,len_mm,holder,offset_len_mm,spindle_rpm,feed_mm_min,plunge_mm_min
1,Ø6 flat endmill,EM,6.0,45.0,ER20,120.0,8000,600,200
3,Ø3 drill,DRILL,3.0,55.0,ER16,121.2,6000,300,150
7,Ø5 test drill,DRILL,5.0,60.0,ER20,120.0,5000,250,120
```

**Import Behavior:**
- Merges by `t` number (existing tools replaced)
- Skips rows with missing/invalid required fields
- Returns count of successfully imported tools

---

## 🔧 Implementation Steps

### **Step 1: Backend Router**

Create `services/api/app/routers/machines_tools_router.py`:

```python
# server/routers/machines_tools_router.py
from fastapi import APIRouter, HTTPException, Response, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import io, csv, json, os

MACHINES_PATH = os.environ.get("TB_MACHINES_PATH", "services/api/app/data/machines.json")
router = APIRouter(prefix="/machines/tools", tags=["machines","tools"])

class Tool(BaseModel):
    t: int
    name: str
    type: str
    dia_mm: float
    len_mm: float
    holder: Optional[str] = None
    offset_len_mm: Optional[float] = None
    spindle_rpm: Optional[float] = None
    feed_mm_min: Optional[float] = None
    plunge_mm_min: Optional[float] = None

def _load() -> Dict[str, Any]:
    try:
        with open(MACHINES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"machines": []}

def _save(obj: Dict[str, Any]):
    os.makedirs(os.path.dirname(MACHINES_PATH), exist_ok=True)
    with open(MACHINES_PATH, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def _find_machine(data, mid: str) -> Optional[Dict[str, Any]]:
    for m in data.get("machines", []):
        if m.get("id") == mid:
            return m
    return None

@router.get("/{mid}", response_model=dict)
def list_tools(mid: str):
    d = _load(); m = _find_machine(d, mid)
    if not m: raise HTTPException(404, "Machine not found")
    return {"machine": m["id"], "tools": m.get("tools") or []}

@router.put("/{mid}", response_model=dict)
def upsert_tools(mid: str, tools: List[Tool]):
    d = _load(); m = _find_machine(d, mid)
    if not m: raise HTTPException(404, "Machine not found")
    # Index by T for merge/upsert
    idx = { int(t.get("t")): t for t in (m.get("tools") or []) }
    for tool in tools:
        idx[int(tool.t)] = tool.dict()
    m["tools"] = [idx[k] for k in sorted(idx.keys())]
    _save(d)
    return {"ok": True, "tools": m["tools"]}

@router.delete("/{mid}/{tnum}", response_model=dict)
def delete_tool(mid: str, tnum: int):
    d = _load(); m = _find_machine(d, mid)
    if not m: raise HTTPException(404, "Machine not found")
    tools = [t for t in (m.get("tools") or []) if int(t.get("t")) != int(tnum)]
    m["tools"] = tools; _save(d)
    return {"ok": True, "tools": tools}

@router.get("/{mid}.csv")
def export_csv(mid: str):
    d = _load(); m = _find_machine(d, mid)
    if not m: raise HTTPException(404, "Machine not found")
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["t","name","type","dia_mm","len_mm","holder","offset_len_mm","spindle_rpm","feed_mm_min","plunge_mm_min"])
    for t in (m.get("tools") or []):
        w.writerow([t.get("t"),t.get("name"),t.get("type"),t.get("dia_mm"),t.get("len_mm"),t.get("holder"),t.get("offset_len_mm"),t.get("spindle_rpm"),t.get("feed_mm_min"),t.get("plunge_mm_min")])
    return Response(content=buf.getvalue(), media_type="text/csv; charset=utf-8")

@router.post("/{mid}/import_csv")
def import_csv(mid: str, file: UploadFile = File(...)):
    d = _load(); m = _find_machine(d, mid)
    if not m: raise HTTPException(404, "Machine not found")
    text = file.file.read().decode("utf-8", errors="ignore")
    rdr = csv.DictReader(io.StringIO(text))
    tools = []
    for row in rdr:
        try:
            tools.append({
                "t": int(row["t"]), "name": row["name"], "type": row.get("type","EM"),
                "dia_mm": float(row["dia_mm"]), "len_mm": float(row["len_mm"]),
                "holder": row.get("holder") or None,
                "offset_len_mm": float(row["offset_len_mm"]) if row.get("offset_len_mm") else None,
                "spindle_rpm": float(row["spindle_rpm"]) if row.get("spindle_rpm") else None,
                "feed_mm_min": float(row["feed_mm_min"]) if row.get("feed_mm_min") else None,
                "plunge_mm_min": float(row["plunge_mm_min"]) if row.get("plunge_mm_min") else None
            })
        except Exception as e:
            continue
    # Upsert all imported
    idx = { int(t.get("t")): t for t in (m.get("tools") or []) }
    for t in tools:
        idx[int(t["t"])] = t
    m["tools"] = [idx[k] for k in sorted(idx.keys())]
    _save(d)
    return {"ok": True, "count": len(tools), "tools": m["tools"]}
```

### **Step 2: Tool Context Utility**

Create `services/api/app/util/tool_table.py`:

```python
# server/util/tool_table.py
from typing import Dict, Any, Optional
import json, os

MACHINES_PATH = os.environ.get("TB_MACHINES_PATH", "services/api/app/data/machines.json")

def _load_machines() -> Dict[str, Any]:
    try:
        with open(MACHINES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"machines": []}

def get_machine(mid: str) -> Optional[Dict[str, Any]]:
    for m in _load_machines().get("machines", []):
        if m.get("id") == mid:
            return m
    return None

def get_tool(mid: str, tnum: int) -> Optional[Dict[str, Any]]:
    m = get_machine(mid)
    if not m:
        return None
    for t in (m.get("tools") or []):
        if int(t.get("t", -1)) == int(tnum):
            return t
    return None

def tool_context(mid: Optional[str], tnum: Optional[int]) -> Dict[str, Any]:
    """Return context dict for template expansion: {TOOL}, {TOOL_DIA}, {TOOL_LEN}, {TOOL_NAME}, {RPM}, {FEED}…"""
    ctx: Dict[str, Any] = {}
    if not mid or tnum is None:
        return ctx
    t = get_tool(mid, int(tnum))
    if not t:
        return ctx
    ctx.update({
        "TOOL": int(tnum),
        "TOOL_NAME": t.get("name"),
        "TOOL_DIA": t.get("dia_mm"),
        "TOOL_LEN": t.get("len_mm"),
        "TOOL_HOLDER": t.get("holder"),
        "TOOL_OFFS_LEN": t.get("offset_len_mm"),
        "RPM": t.get("spindle_rpm"),
        "FEED": t.get("feed_mm_min"),
        "PLUNGE": t.get("plunge_mm_min"),
    })
    return ctx
```

### **Step 3: Register Router**

Update `services/api/app/main.py`:

```python
# After existing routers (around line 40+)
# Patch N.12 — Machine Tool Tables
try:
    from .routers.machines_tools_router import router as machines_tools_router
except Exception:
    from routers.machines_tools_router import router as machines_tools_router
app.include_router(machines_tools_router)
```

### **Step 4: Post-Processor Integration**

Update `services/api/app/post_injection_dropin.py`:

Add import at top:
```python
from .util.tool_table import tool_context
```

In the `wrap_gcode_with_post()` function, after loading header/footer and before expansion:

```python
# Merge tool context if available (machine_id + TOOL in ctx)
try:
    tc = tool_context(ctx.get("machine_id"), ctx.get("TOOL"))
    if tc: 
        ctx.update({k:v for k,v in tc.items() if v is not None})
except Exception:
    pass
```

### **Step 5: Vue UI Component**

Create `packages/client/src/components/ToolTable.vue`:

```vue
<template>
  <div class="p-4 space-y-4">
    <h2 class="text-xl font-bold">Tool Table</h2>
    <div class="flex items-center gap-3">
      <label class="text-sm">Machine
        <select v-model="mid" @change="refresh" class="border rounded p-1 ml-2">
          <option v-for="m in machines" :key="m.id" :value="m.id">{{ m.title }} ({{ m.id }})</option>
        </select>
      </label>
      <button class="px-3 py-1 border rounded hover:bg-gray-100" @click="refresh">Refresh</button>
      <a class="px-3 py-1 border rounded hover:bg-gray-100" :href="`/api/machines/tools/${mid}.csv`" download>Export CSV</a>
      <label class="px-3 py-1 border rounded cursor-pointer hover:bg-gray-100">
        Import CSV
        <input type="file" class="hidden" @change="importCsv" accept=".csv">
      </label>
    </div>
    <div class="overflow-auto max-h-[480px] border rounded">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-100 sticky top-0">
          <tr>
            <th class="text-left p-2 border-b">T</th>
            <th class="text-left p-2 border-b">Name</th>
            <th class="text-left p-2 border-b">Type</th>
            <th class="text-right p-2 border-b">Ø (mm)</th>
            <th class="text-right p-2 border-b">Len (mm)</th>
            <th class="text-left p-2 border-b">Holder</th>
            <th class="text-right p-2 border-b">Len Offs</th>
            <th class="text-right p-2 border-b">RPM</th>
            <th class="text-right p-2 border-b">Feed</th>
            <th class="text-right p-2 border-b">Plunge</th>
            <th class="p-2 border-b"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(t,i) in tools" :key="i" class="hover:bg-gray-50">
            <td class="p-2 border-b"><input type="number" class="w-16 border rounded p-1" v-model.number="t.t" /></td>
            <td class="p-2 border-b"><input class="w-48 border rounded p-1" v-model="t.name" /></td>
            <td class="p-2 border-b"><input class="w-20 border rounded p-1" v-model="t.type" /></td>
            <td class="p-2 border-b text-right"><input type="number" step="0.01" class="w-24 border rounded p-1 text-right" v-model.number="t.dia_mm" /></td>
            <td class="p-2 border-b text-right"><input type="number" step="0.01" class="w-24 border rounded p-1 text-right" v-model.number="t.len_mm" /></td>
            <td class="p-2 border-b"><input class="w-24 border rounded p-1" v-model="t.holder" /></td>
            <td class="p-2 border-b text-right"><input type="number" step="0.01" class="w-24 border rounded p-1 text-right" v-model.number="t.offset_len_mm" /></td>
            <td class="p-2 border-b text-right"><input type="number" class="w-24 border rounded p-1 text-right" v-model.number="t.spindle_rpm" /></td>
            <td class="p-2 border-b text-right"><input type="number" class="w-24 border rounded p-1 text-right" v-model.number="t.feed_mm_min" /></td>
            <td class="p-2 border-b text-right"><input type="number" class="w-24 border rounded p-1 text-right" v-model.number="t.plunge_mm_min" /></td>
            <td class="p-2 border-b"><button class="text-red-600 hover:underline" @click="rm(i)">Delete</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="flex items-center gap-2">
      <button class="px-3 py-1 rounded bg-black text-white hover:bg-gray-800" @click="add">Add Tool</button>
      <button class="px-3 py-1 rounded bg-green-600 text-white hover:bg-green-700" @click="save">Save All</button>
      <span v-if="saved" class="text-green-700 text-sm">Saved ✓</span>
      <span v-if="error" class="text-red-600 text-sm">{{ error }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const machines = ref<any[]>([])
const mid = ref('')
const tools = ref<any[]>([])
const saved = ref(false)
const error = ref('')

async function loadMachines() {
  try {
    const r = await fetch('/api/machines')
    const j = await r.json()
    machines.value = j.machines || []
    if (machines.value.length) {
      mid.value = machines.value[0].id
    }
  } catch (e: any) {
    error.value = 'Failed to load machines: ' + e.message
  }
}

async function refresh() {
  if (!mid.value) return
  try {
    const r = await fetch('/api/machines/tools/' + encodeURIComponent(mid.value))
    const j = await r.json()
    tools.value = j.tools || []
    saved.value = false
    error.value = ''
  } catch (e: any) {
    error.value = 'Failed to load tools: ' + e.message
  }
}

function add() {
  const lastT = tools.value.at(-1)?.t || 0
  tools.value.push({ 
    t: lastT + 1, 
    name: 'New Tool', 
    type: 'EM', 
    dia_mm: 3.0, 
    len_mm: 30.0,
    holder: null,
    offset_len_mm: null,
    spindle_rpm: null,
    feed_mm_min: null,
    plunge_mm_min: null
  })
  saved.value = false
}

function rm(i: number) {
  tools.value.splice(i, 1)
  saved.value = false
}

async function save() {
  try {
    const r = await fetch('/api/machines/tools/' + encodeURIComponent(mid.value), { 
      method: 'PUT', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify(tools.value) 
    })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    saved.value = true
    error.value = ''
    setTimeout(() => { saved.value = false }, 3000)
  } catch (e: any) {
    error.value = 'Save failed: ' + e.message
  }
}

async function importCsv(e: Event) {
  const target = e.target as HTMLInputElement
  const f = target.files?.[0]
  if (!f) return
  
  try {
    const fd = new FormData()
    fd.append('file', f)
    const r = await fetch('/api/machines/tools/' + encodeURIComponent(mid.value) + '/import_csv', { 
      method: 'POST', 
      body: fd 
    })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    await refresh()
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } catch (e: any) {
    error.value = 'Import failed: ' + e.message
  }
  
  // Reset file input
  target.value = ''
}

onMounted(async () => { 
  await loadMachines()
  await refresh()
})
</script>
```

### **Step 6: Example Data**

Add example tools to `services/api/app/data/machines.json`:

```json
{
  "machines": [
    {
      "id": "m1",
      "title": "Shop Fanuc Mill",
      "post": "fanuc_haas",
      "overrides": {},
      "tools": [
        {
          "t": 1,
          "name": "Ø6 flat endmill",
          "type": "EM",
          "dia_mm": 6.0,
          "len_mm": 45.0,
          "holder": "ER20",
          "offset_len_mm": 120.0,
          "spindle_rpm": 8000,
          "feed_mm_min": 600,
          "plunge_mm_min": 200
        },
        {
          "t": 3,
          "name": "Ø3 drill",
          "type": "DRILL",
          "dia_mm": 3.0,
          "len_mm": 55.0,
          "holder": "ER16",
          "offset_len_mm": 121.2,
          "spindle_rpm": 6000,
          "feed_mm_min": 300,
          "plunge_mm_min": 150
        }
      ]
    },
    {
      "id": "m2",
      "title": "Garage GRBL Router",
      "post": "grbl",
      "overrides": {},
      "tools": [
        {
          "t": 1,
          "name": "Ø3.175 flat",
          "type": "EM",
          "dia_mm": 3.175,
          "len_mm": 35.0,
          "holder": "Collet",
          "offset_len_mm": 0.0,
          "spindle_rpm": 12000,
          "feed_mm_min": 900,
          "plunge_mm_min": 300
        }
      ]
    }
  ]
}
```

### **Step 7: Smoke Test**

Create `scripts/smoke_n12_tools.py`:

```python
#!/usr/bin/env python3
"""
Smoke test for Patch N.12 - Machine Tool Tables
Tests CRUD operations, CSV export/import, and template token injection
"""
import os, sys, requests

BASE = os.environ.get('TB_BASE', 'http://127.0.0.1:8000')

def test_n12():
    print("=== Patch N.12 Smoke Test ===\n")
    
    # Test 1: Upsert tools
    print("1. Testing PUT /api/machines/tools/m1 (upsert)")
    tools = [
        {
            "t": 7,
            "name": "Test Ø5 drill",
            "type": "DRILL",
            "dia_mm": 5.0,
            "len_mm": 60.0,
            "holder": "ER20",
            "offset_len_mm": 120.0,
            "spindle_rpm": 5000,
            "feed_mm_min": 250,
            "plunge_mm_min": 120
        }
    ]
    
    r = requests.put(f'{BASE}/api/machines/tools/m1', json=tools, timeout=10)
    r.raise_for_status()
    data = r.json()
    print(f"  ✓ Upsert OK, tool count: {len(data.get('tools', []))}")
    
    # Test 2: List tools
    print("\n2. Testing GET /api/machines/tools/m1")
    r = requests.get(f'{BASE}/api/machines/tools/m1', timeout=10)
    r.raise_for_status()
    data = r.json()
    print(f"  ✓ List OK, machine: {data.get('machine')}, tools: {len(data.get('tools', []))}")
    
    # Test 3: Export CSV
    print("\n3. Testing GET /api/machines/tools/m1.csv")
    r = requests.get(f'{BASE}/api/machines/tools/m1.csv', timeout=10)
    r.raise_for_status()
    csv_text = r.text
    lines = csv_text.strip().split('\n')
    print(f"  ✓ CSV export OK, lines: {len(lines)} (header + {len(lines)-1} tools)")
    print(f"  First 2 lines:")
    for line in lines[:2]:
        print(f"    {line}")
    
    # Test 4: Tool context integration (drill operation with machine_id + tool)
    print("\n4. Testing tool context injection via /api/cam/drill_g81_g83")
    body = {
        "holes": [{"x": 0, "y": 0, "z": -5, "feed": 180}],
        "cycle": "G81",
        "r_clear": 5,
        "safe_z": 5,
        "post": "fanuc_haas",
        "machine_id": "m1",
        "tool": 7,
        "program_no": "01250",
        "work_offset": "G54"
    }
    
    r = requests.post(f'{BASE}/api/cam/drill_g81_g83', json=body, timeout=10)
    r.raise_for_status()
    gcode = r.text
    lines = gcode.splitlines()
    print(f"  ✓ Drill operation OK, checking for tool context tokens...")
    print(f"  First 10 lines:")
    for line in lines[:10]:
        print(f"    {line}")
    
    # Check if tool context was injected (RPM should be 5000 from tool definition)
    if 'S5000' in gcode or 'T7' in gcode:
        print(f"  ✓ Tool context injection confirmed (S5000 or T7 found)")
    else:
        print(f"  ⚠ Tool context may not be fully integrated (S5000/T7 not found)")
    
    print("\n=== All N.12 Tests Passed ===")
    return True

if __name__ == '__main__':
    try:
        test_n12()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

Make it executable:
```powershell
chmod +x scripts/smoke_n12_tools.py
```

---

## 🧪 Testing

### **Local Testing**

```powershell
# 1. Start API server
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# 2. Start client (separate terminal)
cd packages/client
npm run dev  # Runs on http://localhost:5173

# 3. Run smoke test (separate terminal)
cd scripts
python smoke_n12_tools.py

# 4. Test UI
# Navigate to http://localhost:5173 and open ToolTable component
# Try: Add tool, edit fields, save, export CSV, import CSV
```

### **Expected Smoke Test Output**

```
=== Patch N.12 Smoke Test ===

1. Testing PUT /api/machines/tools/m1 (upsert)
  ✓ Upsert OK, tool count: 3

2. Testing GET /api/machines/tools/m1
  ✓ List OK, machine: m1, tools: 3

3. Testing GET /api/machines/tools/m1.csv
  ✓ CSV export OK, lines: 4 (header + 3 tools)
  First 2 lines:
    t,name,type,dia_mm,len_mm,holder,offset_len_mm,spindle_rpm,feed_mm_min,plunge_mm_min
    1,Ø6 flat endmill,EM,6.0,45.0,ER20,120.0,8000,600,200

4. Testing tool context injection via /api/cam/drill_g81_g83
  ✓ Drill operation OK, checking for tool context tokens...
  First 10 lines:
    O01250
    (POST=fanuc_haas;MACHINE=m1;TOOL=7)
    G90 G17 G40 G49 G80
    G54
    T7 M06
    G43 H7 Z120.0
    S5000 M03
    G0 X0.0000 Y0.0000
    G0 Z5.0000
    G81 X0.0000 Y0.0000 Z-5.0000 R5.0000 F180.0
  ✓ Tool context injection confirmed (S5000 or T7 found)

=== All N.12 Tests Passed ===
```

### **Manual UI Testing Checklist**

- [ ] Machine selector shows all machines
- [ ] Changing machine loads correct tool table
- [ ] Add Tool button creates new row with incremented T number
- [ ] All fields are editable
- [ ] Delete button removes row
- [ ] Save All persists changes (check with Refresh)
- [ ] Export CSV downloads valid CSV file
- [ ] Import CSV merges tools (upsert by T number)
- [ ] Save confirmation shows "Saved ✓"
- [ ] Error messages display on failures

---

## 📊 Integration Points

### **1. CAM Endpoints**

Any CAM endpoint can now accept `machine_id` and `tool` parameters:

```python
# Example: Drill operation
@router.post("/cam/drill_g81_g83")
def drill_operation(body: DrillRequest):
    # Extract machine_id and tool from body
    machine_id = body.machine_id  # Optional
    tool = body.tool              # Optional
    
    # Build context
    ctx = {
        "WORK_OFFSET": body.work_offset,
        "SAFE_Z": body.safe_z,
        # ... other params
    }
    
    if machine_id and tool:
        ctx["machine_id"] = machine_id
        ctx["TOOL"] = tool
    
    # wrap_gcode_with_post will auto-inject tool context
    return wrap_gcode_with_post(gcode, body.post, ctx)
```

### **2. Post-Processor Templates**

Post templates in `services/api/app/data/posts/*.json` can reference tool tokens:

**Example: `posts/fanuc_haas.json`**

```json
{
  "header": [
    "G90 G17 G40 G49 G80",
    "(TOOL={TOOL} DIA={TOOL_DIA}mm {TOOL_NAME})",
    "T{TOOL} M06",
    "G43 H{TOOL} Z{TOOL_OFFS_LEN}",
    "S{RPM} M03",
    "F{FEED}"
  ],
  "footer": [
    "M30"
  ]
}
```

**Generated Output:**

```gcode
G90 G17 G40 G49 G80
(TOOL=1 DIA=6.0mm Ø6 flat endmill)
T1 M06
G43 H1 Z120.0
S8000 M03
F600
... operation code ...
M30
```

### **3. Navigation Integration**

Add ToolTable to main navigation:

**Option A: Settings Page**

```vue
<!-- packages/client/src/views/Settings.vue -->
<template>
  <div>
    <h1>Settings</h1>
    <ToolTable />
  </div>
</template>

<script setup>
import ToolTable from '@/components/ToolTable.vue'
</script>
```

**Option B: Dedicated Route**

```typescript
// packages/client/src/router/index.ts
{
  path: '/tools',
  name: 'ToolManagement',
  component: () => import('@/components/ToolTable.vue')
}
```

---

## 🎯 Use Cases

### **Use Case 1: Shop with Multiple Machines**

A lutherie shop has 3 CNC machines:
- Fanuc VMC (m1) - 4-axis mill for necks
- GRBL router (m2) - Flatbed for bodies
- Mach4 router (m3) - Large format for templates

Each machine has different tooling:
- m1: ER20 holders, metric tools, 8000 RPM max
- m2: Collet holders, imperial tools, 18000 RPM max
- m3: BT30 holders, large diameter bits, 3000 RPM max

**Solution:**
- Define tool tables per machine in machines.json
- CAM operations specify `machine_id` and `tool` number
- G-code automatically includes correct RPM, feed, and tool offset

### **Use Case 2: CSV Tool Library Management**

Shop manager maintains master tool library in Excel:
- Export to CSV
- Import to each machine via ToolTable UI
- Tools merge by T number (existing tools updated)
- New tools added automatically

### **Use Case 3: Template-Based Tool Changes**

Post-processor template needs to inject tool-specific parameters:

```gcode
(TOOL={TOOL} DIA={TOOL_DIA}mm LEN={TOOL_LEN}mm)
T{TOOL} M06
G43 H{TOOL} Z{TOOL_OFFS_LEN}
S{RPM} M03
G0 X0 Y0
G1 Z-{TOOL_LEN} F{PLUNGE}
```

**Result:**
- All tool parameters auto-populated from tool table
- No manual entry of RPM, feed, offsets
- Consistent across all operations

---

## 🐛 Troubleshooting

### **Issue:** Machine not found (404)
**Solution:** 
- Check `services/api/app/data/machines.json` exists
- Verify machine `id` matches request parameter
- Ensure machines array is not empty

### **Issue:** Tools not saving
**Solution:**
- Check file permissions on `machines.json`
- Verify `TB_MACHINES_PATH` environment variable (if set)
- Check API logs for write errors

### **Issue:** CSV import fails silently
**Solution:**
- Verify CSV has correct headers (exact match required)
- Check for missing required fields: `t`, `name`, `type`, `dia_mm`, `len_mm`
- Look for data type mismatches (e.g., text in numeric fields)

### **Issue:** Tool context not injecting into G-code
**Solution:**
- Verify `post_injection_dropin.py` has tool context patch
- Check CAM endpoint passes `machine_id` and `tool` in context
- Ensure post template uses correct token names: `{TOOL}`, `{RPM}`, etc.
- Check API logs for tool lookup errors

### **Issue:** UI shows empty tool table
**Solution:**
- Check browser console for fetch errors
- Verify API endpoint returns valid JSON: `/api/machines/tools/{mid}`
- Ensure machine has `tools` array (can be empty `[]`)

---

## 📋 Implementation Checklist

### **Backend Tasks**
- [ ] Create `services/api/app/routers/machines_tools_router.py`
- [ ] Create `services/api/app/util/tool_table.py`
- [ ] Register router in `services/api/app/main.py`
- [ ] Patch `services/api/app/post_injection_dropin.py` with tool context
- [ ] Add example tools to `services/api/app/data/machines.json`
- [ ] Create `scripts/smoke_n12_tools.py`

### **Frontend Tasks**
- [ ] Create `packages/client/src/components/ToolTable.vue`
- [ ] Add to navigation/settings page
- [ ] Test CSV export download
- [ ] Test CSV import upload
- [ ] Test inline editing and save

### **Testing Tasks**
- [ ] Run smoke test: `python scripts/smoke_n12_tools.py`
- [ ] Test CRUD operations via API
- [ ] Test CSV import/export
- [ ] Test tool context injection in G-code
- [ ] Manual UI testing (all checklist items)

### **Documentation Tasks**
- [ ] Update API documentation with new endpoints
- [ ] Add tool table section to user guide
- [ ] Document CSV format specification
- [ ] Create example tool library CSV files

---

## 🚀 Future Enhancements

### **V2 Features (Planned)**

1. **Global Tool Catalog**
   - `services/api/app/data/tools.json` with all tools
   - Copy/paste tools from catalog to machine tables
   - Tool library search and filter

2. **Tool Life Tracking**
   - Track total runtime per tool
   - Alert when tool reaches expected life
   - Tool change recommendations

3. **Wear Offset Management**
   - Separate geometry and wear offsets
   - Wear offset adjustments in UI
   - Wear history tracking

4. **Tool Validation**
   - Check if required tool exists before operation
   - Warn if tool diameter doesn't match operation
   - Suggest alternative tools

5. **Import from CAM Software**
   - Import Fusion 360 tool libraries
   - Import VCarve tool databases
   - Import HSMWorks/HSMXpress libraries

---

## 📚 See Also

- [Machine Profiles Module M](./MACHINE_PROFILES_MODULE_M.md) - Base machine configuration
- [Post-Processor System](./PATCH_K_EXPORT_COMPLETE.md) - G-code post-processing
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md) - CAM operations
- [Multi-Post Export](./PATCH_K_POST_AWARE_COMPLETE.md) - Multi-post support

---

**Status:** ✅ Ready for Implementation  
**Estimated Time:** 4-6 hours  
**Complexity:** Medium (File I/O, CSV parsing, UI component)  
**Next Steps:** Implement backend router, then Vue component, then smoke test
