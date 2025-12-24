# Verification Instructions: Bundle 31.0.27 Patch

## Overview

This document provides step-by-step verification procedures for the two patch requirements:

1. **Backend Locking** - Concurrent snapshot write safety
2. **Frontend Backoff** - Exponential backoff polling

---

## 1. Backend Locking Verification

### Purpose

Verify that concurrent snapshot exports don't create partial/corrupt JSON files.

### Prerequisites

```bash
cd services/api
# Ensure server dependencies are installed
pip install -r requirements.txt
```

### Test A: Automated Concurrency Test

```bash
# Run from project root
cd luthiers-toolbox
python tests/verification/test_snapshot_concurrency.py
```

**Expected Output:**

```
============================================================
SNAPSHOT CONCURRENCY VERIFICATION
============================================================

============================================================
Running 10 concurrent snapshot writes...
============================================================

  [OK]   Index 0: snap_abc123...
  [OK]   Index 1: snap_def456...
  ...
  [OK]   Index 9: snap_xyz789...

============================================================
Results: 10/10 successful
All concurrent writes completed without corruption!
============================================================

============================================================
Testing same-ID write rejection...
============================================================

  [OK] First write succeeded
  [INFO] Second write overwrote (atomic, no corruption)
         Loaded name: Second

============================================================

============================================================
Verifying JSON integrity of all snapshots...
============================================================

  Valid files: 0
  No snapshot files found (OK - empty store)

============================================================

============================================================
ALL VERIFICATIONS PASSED
============================================================
```

### Test B: Manual Concurrent Export via API

```bash
# Terminal 1: Start server
cd services/api
uvicorn app.main:app --reload

# Terminal 2: Run concurrent exports
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/art/rosette/snapshots/export \
    -H "Content-Type: application/json" \
    -d "{\"design\":{\"outer_diameter_mm\":$((100+i)),\"inner_diameter_mm\":20,\"ring_params\":[]},\"name\":\"Concurrent $i\"}" &
done
wait
echo "All requests completed"
```

### Verification Criteria

| Check | Pass Criteria |
|-------|---------------|
| No partial files | `ls data/art_studio/snapshots/` shows only `.json` files, no `.tmp` |
| All valid JSON | `for f in data/art_studio/snapshots/*.json; do python -m json.tool "$f" > /dev/null && echo "OK: $f"; done` |
| No corruption | Each file has `snapshot_id`, `design`, `design_fingerprint` |

### Behavior Without filelock

If `filelock` is not installed, the current implementation still uses atomic writes (`os.replace`), which prevents corruption. The test should still pass.

---

## 2. Frontend Backoff Verification

### Purpose

Verify that the polling client backs off exponentially on failure and resets on success.

### Prerequisites

```bash
# Start the backend server
cd services/api
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Test Method: Browser-Based

1. **Open the test page:**
   ```
   Open in browser: tests/verification/test_frontend_backoff.html
   ```

2. **Start polling:**
   - Click "Start Polling"
   - Observe log shows successful polls every 5 seconds

3. **Simulate backend failure:**
   - Stop the backend server (Ctrl+C in terminal)
   - Watch the log for backoff progression:
     ```
     [12:00:05] ERROR: HTTP 0: Failed to fetch
     [12:00:05] BACKOFF: Next poll in 10000ms (failure #1)
     [12:00:15] ERROR: HTTP 0: Failed to fetch
     [12:00:15] BACKOFF: Next poll in 20000ms (failure #2)
     [12:00:35] ERROR: HTTP 0: Failed to fetch
     [12:00:35] BACKOFF: Next poll in 30000ms (failure #3)
     [12:01:05] ERROR: HTTP 0: Failed to fetch
     [12:01:05] BACKOFF: Next poll in 30000ms (failure #4)  <- Capped at max
     ```

4. **Restore backend:**
   - Restart the server: `uvicorn app.main:app --port 8000`
   - Watch for recovery:
     ```
     [12:01:35] SUCCESS: Got 5 entries (interval reset to 5000ms)
     ```

5. **Verify reset:**
   - Confirm the "Current Interval" stat shows 5000ms
   - Confirm "Consecutive Failures" shows 0

### Expected Backoff Progression

| Failure # | Interval | Cumulative Wait |
|-----------|----------|-----------------|
| 0 (success) | 5000ms | - |
| 1 | 10000ms | 10s |
| 2 | 20000ms | 30s |
| 3+ | 30000ms (max) | 60s+ |

### Verification Criteria

| Check | Pass Criteria |
|-------|---------------|
| Initial interval | 5000ms on start |
| Backoff multiplier | 2x on each failure |
| Max cap | Never exceeds 30000ms |
| Reset on success | Returns to 5000ms after successful poll |
| Failure count | Resets to 0 on success |

---

## 3. Quick Verification Script

Create this script to run both tests:

```bash
#!/bin/bash
# tests/verification/run_all_tests.sh

echo "========================================"
echo "Bundle 31.0.27 Verification Suite"
echo "========================================"
echo ""

# Test 1: Backend concurrency
echo ">>> Running Backend Concurrency Test..."
python tests/verification/test_snapshot_concurrency.py
BACKEND_RESULT=$?

echo ""
echo ">>> Backend test result: $([ $BACKEND_RESULT -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo ""

# Test 2: Frontend (manual)
echo ">>> Frontend Backoff Test: MANUAL"
echo "    Open tests/verification/test_frontend_backoff.html in browser"
echo "    Follow the instructions in the UI"
echo ""

echo "========================================"
echo "Verification Complete"
echo "========================================"
```

---

## 4. Troubleshooting

### Backend Test Fails

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` | Not in correct directory | `cd services/api` before running |
| Permission denied | Data dir not writable | `chmod 755 data/art_studio/snapshots` |
| Corrupt JSON found | Previous failed test | Delete `.tmp` files manually |

### Frontend Test Fails

| Symptom | Cause | Fix |
|---------|-------|-----|
| Immediate errors | Server not running | Start uvicorn |
| CORS errors | Wrong origin | Open HTML via `file://` or serve via HTTP |
| No backoff | Config wrong | Check `DEFAULT_BACKOFF_CONFIG` values |

---

## 5. Sign-Off

| Test | Tester | Date | Result |
|------|--------|------|--------|
| Backend Concurrency | ____________ | ________ | PASS / FAIL |
| Frontend Backoff | ____________ | ________ | PASS / FAIL |
| Overall | ____________ | ________ | APPROVED / REJECTED |

**Notes:**
```
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________
```
