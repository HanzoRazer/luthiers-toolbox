# API Test Catalogue

> Last tested: 2026-01-17
> Server: http://127.0.0.1:8000
> Total endpoints tested: 45+

---

## 1. Health & Status

### 1.1 Global Health Check
```bash
curl -s http://127.0.0.1:8000/api/health
```
**Expected**: 200, `{"status":"healthy","version":"2.0.0-clean",...}`
**Validates**: API server running, AI providers available, router counts

### 1.2 Saw Lab Health
```bash
curl -s http://127.0.0.1:8000/api/dashboard/saw/health
```
**Expected**: 200, `{"status":"healthy","module":"CP-S61/62 Dashboard + Risk Actions",...}`

---

## 2. RMOS Runs v2

### 2.1 List Runs
```bash
curl -s "http://127.0.0.1:8000/api/rmos/runs?limit=5"
```
**Expected**: 200, array of run summaries with `run_id`, `status`, `mode`, `risk_level`

### 2.2 Query Recent Runs (Detailed)
```bash
curl -s "http://127.0.0.1:8000/api/rmos/runs/query/recent?limit=3"
```
**Expected**: 200, detailed run info including `request_summary`, `feasibility`, `decision`

### 2.3 Get Run by ID
```bash
curl -s "http://127.0.0.1:8000/api/rmos/runs/{run_id}"
```
**Expected**: 200, full run artifact with `hashes`, `outputs`, `advisory_inputs`

### 2.4 Create New Run
```python
import requests
resp = requests.post('http://127.0.0.1:8000/api/rmos/runs', json={
    'mode': 'test_manual',
    'tool_id': 'test_tool',
    'event_type': 'test',
    'status': 'OK',
    'meta': {'test': True, 'source': 'api_test'}
})
# Expected: 200, {"run_id": "run_...", "status": "created", "feasibility_sha256": "..."}
```

### 2.5 List Run Attachments
```bash
curl -s "http://127.0.0.1:8000/api/rmos/runs/{run_id}/attachments"
```
**Expected**: 200, `{"run_id": "...", "count": N, "attachments": [...]}`
**Each attachment has**: `sha256`, `kind`, `mime`, `filename`, `size_bytes`, `download_url`

### 2.6 Get Run Advisories
```bash
curl -s "http://127.0.0.1:8000/api/rmos/runs/{run_id}/advisories"
```
**Expected**: 200, `{"run_id": "...", "count": 0, "advisories": []}`

### 2.7 Get Advisory Variants
```bash
curl -s "http://127.0.0.1:8000/api/rmos/runs/{run_id}/advisory/variants"
```
**Expected**: 200, `{"run_id": "...", "count": 0, "items": []}`

### 2.8 Verify Run Attachments
```bash
curl -s "http://127.0.0.1:8000/api/rmos/runs/{run_id}/attachments/verify"
```
**Expected**: 200 if blobs exist, 404 if blobs not on disk
**Note**: Requires blob store to be populated

---

## 3. RMOS Acoustics (Content-Addressed Storage)

### 3.1 Download Attachment Blob
```bash
curl -s "http://127.0.0.1:8000/api/rmos/acoustics/attachments/{sha256}" -o output.bin
```
**Expected**: 200, binary content
**Validates**: Content-addressed blob retrieval

### 3.2 Get Attachments with Base64 Data
```bash
curl -s "http://127.0.0.1:8000/api/rmos/acoustics/runs/{run_id}/attachments?include_urls=true"
```
**Expected**: 200, attachments with `download_url` and `data_b64` (if under 2MB)

### 3.3 Browse Attachment Meta Index
```bash
curl -s "http://127.0.0.1:8000/api/rmos/acoustics/index/attachment_meta?limit=5"
```
**Expected**: 200
```json
{
  "count": 5,
  "total_in_index": 30,
  "limit": 5,
  "next_cursor": "...",
  "entries": [...]
}
```

### 3.4 Filter Attachments by Kind
```bash
curl -s "http://127.0.0.1:8000/api/rmos/acoustics/index/attachment_meta?kind=gcode_output&limit=3"
```
**Expected**: 200, filtered results by `kind`

### 3.5 Filter Attachments by MIME Prefix
```bash
curl -s "http://127.0.0.1:8000/api/rmos/acoustics/index/attachment_meta?mime_prefix=application/json&limit=5"
```
**Expected**: 200, filtered results

### 3.6 Check Attachment Exists
```bash
curl -s "http://127.0.0.1:8000/api/rmos/acoustics/index/attachment_meta/{sha256}/exists"
```
**Expected**: 200
```json
{
  "sha256": "...",
  "in_index": true,
  "in_store": true,
  "size_bytes": 17197,
  "index_kind": "dxf_input",
  "index_mime": "application/dxf",
  "index_filename": "mvp_rect_with_island.dxf"
}
```

### 3.7 Rebuild Attachment Meta Index
```bash
curl -s -X POST "http://127.0.0.1:8000/api/rmos/acoustics/index/rebuild_attachment_meta"
```
**Expected**: 200
```json
{
  "ok": true,
  "runs_scanned": 42,
  "attachments_indexed": 37,
  "unique_sha256": 30
}
```

### 3.8 Get Attachment Facets
```bash
curl -s "http://127.0.0.1:8000/api/rmos/acoustics/index/attachment_meta/facets"
```
**Expected**: 200, `{"facets": {"kind": {...}, "mime": {...}}, "total_attachments": N}`
**Note**: May return empty if using different index location

---

## 4. Saw Lab - Batch Advisory Flow

### 4.1 Create Batch Spec
```python
import requests
from uuid import uuid4

session_id = str(uuid4())
resp = requests.post('http://127.0.0.1:8000/api/saw/batch/spec', json={
    'session_id': session_id,
    'batch_label': 'test_advisory_batch_001',
    'items': [
        {
            'part_id': 'part_001',
            'material_family': 'hardwood',
            'thickness_mm': 19.0,
            'width_mm': 100.0,
            'length_mm': 500.0
        },
        {
            'part_id': 'part_002',
            'material_family': 'hardwood',
            'thickness_mm': 19.0,
            'width_mm': 150.0,
            'length_mm': 400.0
        }
    ],
    'op_type': 'slice',
    'blade_id': 'BLADE_10IN_60T',
    'machine_profile': 'SAW_LAB_01'
})
# Expected: 200, {"batch_spec_artifact_id": "saw_batch_spec_..."}
```

### 4.2 Create Batch Plan from Spec
```python
resp = requests.post('http://127.0.0.1:8000/api/saw/batch/plan', json={
    'batch_spec_artifact_id': 'saw_batch_spec_...',
    'strategy': 'optimize_feed',
    'blade_id': 'BLADE_10IN_60T',
    'rpm': 3600,
    'feed_mm_min': 1200
})
# Expected: 200
# {
#   "batch_plan_artifact_id": "saw_batch_plan_...",
#   "setups": [{"setup_key": "setup_1", "tool_id": "saw:thin_140", "ops": [...]}],
#   "decision_intel_advisory": null,
#   "tuning_applied": false
# }
```

### 4.3 Approve Batch (Create Decision)
```python
resp = requests.post('http://127.0.0.1:8000/api/saw/batch/approve', json={
    'batch_plan_artifact_id': 'saw_batch_plan_...',
    'batch_spec_artifact_id': 'saw_batch_spec_...',
    'approved_by': 'test_user',
    'reason': 'API test approval - parameters within tolerance',
    'setup_order': ['setup_1'],
    'op_order': ['op_1', 'op_2']
})
# Expected: 200, {"batch_decision_artifact_id": "saw_batch_decision_..."}
```

### 4.4 Get Decisions by Plan
```bash
curl -s "http://127.0.0.1:8000/api/saw/batch/decisions/by-plan?batch_plan_artifact_id={plan_id}"
```
**Expected**: 200, array of decisions linked to plan

### 4.5 Get Decisions by Spec
```bash
curl -s "http://127.0.0.1:8000/api/saw/batch/decisions/by-spec?batch_spec_artifact_id={spec_id}"
```
**Expected**: 200, array of decisions

### 4.6 Get Decision Trends
```bash
curl -s "http://127.0.0.1:8000/api/saw/batch/decisions/trends?batch_decision_artifact_id={decision_id}"
```
**Expected**: 200
```json
{
  "batch_decision_artifact_id": "...",
  "point_count": 0,
  "window": 20,
  "points": [],
  "deltas": {"available": false}
}
```

### 4.7 Get Execution by Decision
```bash
curl -s "http://127.0.0.1:8000/api/saw/batch/execution/by-decision?batch_decision_artifact_id={decision_id}"
```
**Expected**: 200, execution details (null if not executed yet)

### 4.8 Get Toolpaths by Decision
```bash
curl -s "http://127.0.0.1:8000/api/saw/batch/toolpaths/by-decision?batch_decision_artifact_id={decision_id}"
```
**Expected**: 200, toolpath details (null if not generated yet)

---

## 5. Saw Lab - Dashboard & Job Logs

### 5.1 Get Saw Dashboard Runs
```bash
curl -s "http://127.0.0.1:8000/api/dashboard/saw/runs?limit=5"
```
**Expected**: 200
```json
{
  "total_runs": 5,
  "returned_runs": 5,
  "runs": [
    {
      "run_id": "...",
      "op_type": "slice",
      "machine_profile": "SAW_LAB_01",
      "material_family": "hardwood",
      "blade_id": "BLADE_10IN_60T",
      "status": "completed",
      "metrics": {
        "avg_rpm": 3600.0,
        "avg_feed_mm_min": 1200.0,
        "avg_spindle_load_pct": 90.85,
        "avg_vibration_rms": 8.3385
      },
      "risk_score": 0.481375,
      "risk_bucket": {"id": "yellow", "label": "Yellow"}
    }
  ]
}
```

### 5.2 Get Joblog Saw Runs
```bash
curl -s "http://127.0.0.1:8000/api/joblog/saw_runs?limit=3"
```
**Expected**: 200, runs with G-code and metadata

### 5.3 Get Specific Saw Run
```bash
curl -s "http://127.0.0.1:8000/api/joblog/saw_runs/{run_id}"
```
**Expected**: 200, full run details

### 5.4 Get Saw Run Telemetry
```bash
curl -s "http://127.0.0.1:8000/api/joblog/saw_runs/{run_id}/telemetry"
```
**Expected**: 200, telemetry data points

---

## 6. Decision Intelligence (Requires Execution Data)

### 6.1 Get Decision Intel Suggestions
```bash
curl -s "http://127.0.0.1:8000/api/saw/batch/decision-intel/suggestions?batch_execution_artifact_id={exec_id}"
```
**Expected**: 200, list of AI-generated suggestions
**Prereq**: Requires completed batch execution

### 6.2 Approve Decision Intel Suggestion
```python
resp = requests.post('http://127.0.0.1:8000/api/saw/batch/decision-intel/approve', json={
    'suggestion_artifact_id': '...',
    'approved': True,
    'approved_by': 'operator_name'
})
# Expected: 200
```
**Prereq**: Requires suggestion_artifact_id from suggestions endpoint

### 6.3 Get Latest Approved Decision Intel
```bash
curl -s "http://127.0.0.1:8000/api/saw/batch/decision-intel/latest-approved?batch_label={label}&tool_id={tool}&material_id={material}"
```
**Expected**: 200, latest approved suggestion for tool/material combo

---

## 7. Test Data Reference

### Sample Run IDs (from test session)
```
run_4e30cb3ec69940058f6bec47a874c97c  - mvp_dxf_to_grbl, GREEN
run_c77ee86c81074899a839426a1a70761f  - mvp_dxf_to_grbl, GREEN
run_f2cd8e68c5814e9e9cbae8c1269052ac  - test_manual (created via API)
```

### Sample Attachment SHA256
```
e9b55f5f200b7e824269fa8541e4ab47dadc975edbb6a5a3c516296e10ee3242 - dxf_input (17KB)
e6ff9451b8e8d3fb204cd6edba59e6f5d1df9fb844a037121cd92c52b831a62b - gcode_output (30KB)
6427b715d80d6e3d3cbc0e14ecc419a31af79a2d7077214a252934a4c1f59683 - cam_plan (408KB)
```

### Sample Saw Batch Artifacts
```
Spec:     saw_batch_spec_aca661525900
Plan:     saw_batch_plan_135d83e23132
Decision: saw_batch_decision_1dbf646d414d
```

---

## 8. Known Issues & Notes

### 8.1 RMOS Runs v2
| Endpoint | Issue | Notes |
|----------|-------|-------|
| `POST /attach-advisory` | 500 | Requires specific advisory payload format |
| `GET /attachments/verify` | 404 | Returns 404 if blobs not on disk |
| `GET /{run_id}/download` | 404 | Different storage path for ZIP export |
| `GET /facets` | Empty | May use different index location than browse |

### 8.2 Saw Lab
| Endpoint | Issue | Notes |
|----------|-------|-------|
| `POST /toolpaths/from-decision` | 500 | Decision artifact lookup issue |
| `POST /decision-intel/approve` | 422 | Requires suggestion_artifact_id |
| `GET /decision-intel/suggestions` | 422 | Requires batch_execution_artifact_id |
| `POST /slice/preview` | 422 | Needs geometry, tool_id, cut_depth_mm |

---

## 9. Automated Test Script

Save as `test_api_endpoints.py`:

```python
#!/usr/bin/env python3
"""
API Endpoint Test Runner
Run: python test_api_endpoints.py
"""
import requests
import json
from uuid import uuid4

BASE_URL = "http://127.0.0.1:8000"

def test(name, method, path, expected_status, json_body=None, params=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            resp = requests.post(url, json=json_body, timeout=10)

        status = "PASS" if resp.status_code == expected_status else "FAIL"
        print(f"[{status}] {name}: {resp.status_code} (expected {expected_status})")
        return resp.status_code == expected_status, resp
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return False, None

def main():
    results = []

    # Health
    results.append(test("Global Health", "GET", "/api/health", 200))
    results.append(test("Saw Health", "GET", "/api/dashboard/saw/health", 200))

    # RMOS Runs
    results.append(test("List Runs", "GET", "/api/rmos/runs", 200, params={"limit": 5}))
    results.append(test("Query Recent", "GET", "/api/rmos/runs/query/recent", 200, params={"limit": 3}))

    # Create Run
    ok, resp = test("Create Run", "POST", "/api/rmos/runs", 200, json_body={
        "mode": "test_auto",
        "tool_id": "test",
        "event_type": "test",
        "status": "OK"
    })
    results.append((ok, resp))

    if ok and resp:
        run_id = resp.json().get("run_id")
        results.append(test("Get Run", "GET", f"/api/rmos/runs/{run_id}", 200))
        results.append(test("Run Attachments", "GET", f"/api/rmos/runs/{run_id}/attachments", 200))
        results.append(test("Run Advisories", "GET", f"/api/rmos/runs/{run_id}/advisories", 200))

    # Attachment Index
    results.append(test("Browse Attachments", "GET", "/api/rmos/acoustics/index/attachment_meta", 200, params={"limit": 5}))
    results.append(test("Rebuild Index", "POST", "/api/rmos/acoustics/index/rebuild_attachment_meta", 200))

    # Saw Lab Flow
    session_id = str(uuid4())
    ok, resp = test("Create Spec", "POST", "/api/saw/batch/spec", 200, json_body={
        "session_id": session_id,
        "batch_label": f"test_{session_id[:8]}",
        "items": [{"part_id": "p1", "material_family": "hardwood", "thickness_mm": 19.0, "width_mm": 100.0, "length_mm": 500.0}],
        "op_type": "slice",
        "blade_id": "BLADE_10IN_60T",
        "machine_profile": "SAW_LAB_01"
    })
    results.append((ok, resp))

    if ok and resp:
        spec_id = resp.json().get("batch_spec_artifact_id")

        ok2, resp2 = test("Create Plan", "POST", "/api/saw/batch/plan", 200, json_body={
            "batch_spec_artifact_id": spec_id,
            "strategy": "optimize_feed",
            "blade_id": "BLADE_10IN_60T",
            "rpm": 3600,
            "feed_mm_min": 1200
        })
        results.append((ok2, resp2))

        if ok2 and resp2:
            plan_id = resp2.json().get("batch_plan_artifact_id")

            ok3, resp3 = test("Approve Batch", "POST", "/api/saw/batch/approve", 200, json_body={
                "batch_plan_artifact_id": plan_id,
                "batch_spec_artifact_id": spec_id,
                "approved_by": "test_runner",
                "reason": "Automated test",
                "setup_order": ["setup_1"],
                "op_order": ["op_1"]
            })
            results.append((ok3, resp3))

            if ok3 and resp3:
                decision_id = resp3.json().get("batch_decision_artifact_id")
                results.append(test("Decisions by Plan", "GET", "/api/saw/batch/decisions/by-plan", 200, params={"batch_plan_artifact_id": plan_id}))
                results.append(test("Decision Trends", "GET", "/api/saw/batch/decisions/trends", 200, params={"batch_decision_artifact_id": decision_id}))

    # Dashboard
    results.append(test("Saw Runs Dashboard", "GET", "/api/dashboard/saw/runs", 200, params={"limit": 5}))
    results.append(test("Joblog Saw Runs", "GET", "/api/joblog/saw_runs", 200, params={"limit": 3}))

    # Summary
    passed = sum(1 for ok, _ in results if ok)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed ({100*passed//total}%)")

if __name__ == "__main__":
    main()
```

---

## 10. Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-17 | Claude Code | Initial catalogue from manual testing session |

