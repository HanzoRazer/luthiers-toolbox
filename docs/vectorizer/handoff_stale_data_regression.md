 Developer Handoff: Blueprint Lab / Photo Vectorizer Stale Data Regression

  Timestamp Coverage: 20:34 hrs 03/01/2026 thru 01:57 hrs 04/02/2026

  ---
  Executive Summary

  | Field                               | Value                                                                                                             |
  |-------------------------------------|-------------------------------------------------------------------------------------------------------------------|
  | Feature being implemented           | Blueprint Lab Phase 2 vectorization with cache-busting to prevent stale SVG/DXF results                           |
  | Architectural constraint introduced | HTTP cache headers + query param cache-busting on /api/blueprint/static/{filename}                                |
  | What changed                        | CORS origins extended (5181-5190), backend moved to port 8001, added ?t=${Date.now()} to DXF fetch in sendToCAM() |
  | What broke                          | User still sees stale vectorization results after re-running vectorization                                        |
  | Current user-visible issue          | Blueprint Lab returns same output regardless of new input - stale data persists                                   |
  | Risk level                          | HIGH - Core workflow unusable; users cannot iterate on designs                                                    |

  ---
  Intended Architecture

  | Component                     | Expected Location                                               |
  |-------------------------------|-----------------------------------------------------------------|
  | Photo Vectorizer V2           | Tab 2 in BlueprintLab.vue (lines 100-165)                       |
  | Blueprint Reader (Legacy)     | Tab 1 in BlueprintLab.vue (lines 31-97)                         |
  | Phase 2 Vectorization Backend | services/api/app/routers/blueprint/phase2_router.py             |
  | Static File Serving           | GET /api/blueprint/static/{filename} (phase2_router.py:345-375) |

  Expected Data Flow

  [User uploads image]
      ↓
  POST /api/blueprint/phase2/vectorize
      ↓
  [Vectorizer creates SVG/DXF in tempfile.mkdtemp(prefix="blueprint_phase2_")]
      ↓
  [Files registered in _output_file_registry Dict[str, str]]
      ↓
  [Response returns svg_path, dxf_path]
      ↓
  [Frontend requests GET /api/blueprint/static/{filename}?t={timestamp}]
      ↓
  [FileResponse with Cache-Control: no-cache, no-store, must-revalidate]

  Source of Truth for Rendered Image

  Backend: _output_file_registry (module-level dict in phase2_router.py:43)
  - Key: filename (e.g., vectorized.svg)
  - Value: full path (e.g., /tmp/blueprint_phase2_abc123/vectorized.svg)

  POTENTIAL REGRESSION SOURCE: This registry is NOT cleared between requests. If same filename is generated, old entry is overwritten. But if filenames differ, old entries persist indefinitely.

  ---
  Change Timeline (Chronological)

  | Time           | Event                                                              | Actor     |
  |----------------|--------------------------------------------------------------------|-----------|
  | Prior session  | Added cache headers to phase2_router.py static endpoint            | Developer |
  | Prior session  | Added ?t=${Date.now()} to frontend download functions              | Developer |
  | Prior session  | Fixed Windows path regex in VectorizationResults.vue               | Developer |
  | ~20:34 - 01:00 | ANOMALY WINDOW - Changes unclear                                   | UNKNOWN   |
  | This session   | User reported blank page, Vue Router warning for /blueprint-lab    | User      |
  | This session   | Discovered correct route is /blueprint not /blueprint-lab          | Claude    |
  | This session   | CORS error: frontend on port 5186, backend only allowed up to 5180 | System    |
  | This session   | Extended CORS_ORIGINS to include ports 5181-5190                   | Claude    |
  | This session   | Port 8000 blocked by zombie sockets (14 processes in TIME_WAIT)    | System    |
  | This session   | Switched backend to port 8001                                      | Claude    |
  | This session   | Updated .env.local VITE_API_BASE to http://localhost:8001          | Claude    |
  | This session   | Found missing cache-busting in useBlueprintWorkflow.ts:567         | Claude    |
  | This session   | Fixed: added ?t=${Date.now()} to sendToCAM DXF fetch               | Claude    |
  | This session   | Restarted frontend on port 5188                                    | Claude    |
  | This session   | User reports: "no same results" (stale data persists)              | User      |

  ---
  Current Symptoms (Observed Behavior Only)

  | Symptom                                            | Verified                                                |
  |----------------------------------------------------|---------------------------------------------------------|
  | User uploads new image to Blueprint Lab            | ASSUMED (user report)                                   |
  | Vectorization returns same SVG/DXF as previous run | USER REPORTED                                           |
  | Hard refresh does not resolve                      | UNKNOWN                                                 |
  | Browser localStorage contains adobeCleanFontAdded  | OBSERVED (but confirmed NOT from app - Adobe extension) |
  | Frontend is on port 5188                           | CONFIRMED                                               |
  | Backend is on port 8001, health check passes       | CONFIRMED                                               |
  | CORS headers include port 5188                     | CONFIRMED                                               |

  ---
  Suspected Failure Domains

  | Domain                                                   | Status   | Evidence                                                                       |
  |----------------------------------------------------------|----------|--------------------------------------------------------------------------------|
  | _output_file_registry not cleared on server restart      | LIKELY   | Module-level dict persists in memory; user tested before backend was restarted |
  | Browser HTTP cache ignoring no-cache headers             | LIKELY   | Even with headers, aggressive caching can occur                                |
  | Service Worker intercepting requests                     | UNLIKELY | Searched codebase, no service workers found                                    |
  | Frontend component state persisting stale URLs           | UNKNOWN  | Vue reactive refs may hold old svg_path/dxf_path                               |
  | Vectorizer outputting same filename for different inputs | UNKNOWN  | Need to verify filename generation logic                                       |
  | Calibration cache returning stale data                   | UNKNOWN  | _calibration_cache in calibration_router.py not investigated                   |

  ---
  Files / Modules Touched

  | File                                                                                   | Change                                  | Status          |
  |----------------------------------------------------------------------------------------|-----------------------------------------|-----------------|
  | services/api/app/main.py                                                               | Added CORS origins 5181-5190            | APPLIED         |
  | packages/client/.env.local                                                             | Changed VITE_API_BASE from 8000 to 8001 | APPLIED         |
  | packages/client/src/composables/useBlueprintWorkflow.ts                                | Added ?t=${Date.now()} to line 567      | APPLIED         |
  | services/api/app/routers/blueprint/phase2_router.py                                    | Cache headers (prior session)           | ASSUMED PRESENT |
  | packages/client/src/components/blueprint/phase2-vectorization/VectorizationResults.vue | Cache-busting (prior session)           | ASSUMED PRESENT |

  ---
  API Contract

  Before (Broken State)

  GET /api/blueprint/static/{filename}
  → Returns: Cached file from browser/CDN
  → Headers: UNKNOWN (may have lacked Cache-Control)

  After (Intended)

  GET /api/blueprint/static/{filename}?t={timestamp}
  → Returns: Fresh file from _output_file_registry
  → Headers:
     Cache-Control: no-cache, no-store, must-revalidate
     Pragma: no-cache
     Expires: 0

  ---
  Reproduction Steps

  1. Navigate to http://localhost:5188/blueprint
  2. Select "Photo Vectorizer V2" tab
  3. Upload an image (e.g., guitar photo)
  4. Click "Extract Silhouette"
  5. Note the resulting SVG/DXF
  6. Upload a DIFFERENT image
  7. Click "Extract Silhouette" again
  8. OBSERVE: Same SVG/DXF as step 5 (stale data)

  ---
  Fixes Attempted

  Attempt 1: CORS Extension

  - Hypothesis: CORS blocking requests from high-numbered ports
  - Change: Added ports 5181-5190 to CORS_ORIGINS in main.py
  - Result: CORS errors resolved
  - Status: ✅ Partial (fixed CORS, not stale data)

  Attempt 2: Port Migration

  - Hypothesis: Port 8000 zombie sockets blocking fresh server
  - Change: Started backend on port 8001, updated .env.local
  - Result: Backend accessible, health check passes
  - Status: ✅ Partial (backend works, stale data persists)

  Attempt 3: Cache-Busting in sendToCAM

  - Hypothesis: DXF fetch in sendToCAM() lacked cache-busting
  - Change: Added ?t=${Date.now()} to line 567 of useBlueprintWorkflow.ts
  - Result: Code applied, but stale data still reported
  - Status: ❌ Failed (user reports "same results")

  Attempt 4: Backend Restart

  - Hypothesis: _output_file_registry holding stale paths
  - Change: Attempted to kill Python processes and restart
  - Result: User interrupted before completion
  - Status: ⚠️ INCOMPLETE

  ---
  Tests Run

  | Test                                                      | Outcome                                         |
  |-----------------------------------------------------------|-------------------------------------------------|
  | grep for all /api/blueprint/static/ without cache-busting | All now have ?t=${Date.now()}                   |
  | curl http://localhost:8001/health                         | Returns {"status":"ok","version":"2.0.0-clean"} |
  | grep 5188 in main.py                                      | Port is in CORS list                            |
  | Verify fix in useBlueprintWorkflow.ts:567                 | Confirmed: ?t=${Date.now()} present             |

  ---
  Evidence

  Console Logs

  [vite] connecting...
  [Vue Router warn]: No match found for location with path "/blueprint-lab"
  Resolution: Correct path is /blueprint

  Network Behavior

  - CORS preflight was failing for ports > 5180
  - After CORS fix, requests succeed

  UI Behavior

  - Blank page when navigating to /blueprint-lab (wrong route)
  - Blueprint Lab loads on /blueprint
  - User reports vectorization returns stale results

  Cached/Stale Asset Indicators

  - adobeCleanFontAdded in localStorage: NOT from app (Adobe Creative Cloud extension)
  - sessionStorage.blueprintLab.pendingImage: Cleared immediately after use (line 287)
  - No service workers registered

  ---
  Last Known Good State

  | Field       | Value                                                           |
  |-------------|-----------------------------------------------------------------|
  | When        | UNKNOWN - Prior to anomaly window (before 20:34 hrs 03/01/2026) |
  | What worked | Phase 2 vectorization returned fresh results for each upload    |
  | Evidence    | User implicitly expected it to work, indicating prior success   |

  ---
  Open Questions

  1. Was the backend actually restarted after the cache-busting fix?
    - The _output_file_registry only clears on process restart
    - User interrupted the restart attempt
  2. What filenames does the vectorizer generate?
    - If same filename every time → registry overwrites (should work)
    - If unique filenames → registry grows, old paths invalid
  3. Is the frontend receiving new svg_path/dxf_path from API?
    - Need to check Network tab for POST /api/blueprint/phase2/vectorize response
  4. Are cache headers actually being sent?
    - Need to verify Cache-Control: no-cache appears in response headers
  5. What happened during the 20:34 - 01:00 anomaly window?
    - File modifications?
    - Git commits?
    - Dependency updates?

  ---
  Recommended Next Actions (Priority Ordered)

  1. RESTART BACKEND (Critical)

  cmd.exe /c "taskkill /F /IM python.exe 2>nul"
  # Wait 5 seconds
  cd C:/Users/thepr/Downloads/luthiers-toolbox/services/api
  python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
  Rationale: Clears _output_file_registry which holds stale file paths

  2. HARD REFRESH BROWSER

  - Press Ctrl+Shift+R (or Cmd+Shift+R on Mac)
  - Alternatively: Open DevTools → Network → Check "Disable cache"

  3. VERIFY API RESPONSE

  curl -X POST http://localhost:8001/api/blueprint/phase2/vectorize \
    -F "file=@test_image.png" \
    -v 2>&1 | grep -E "svg_path|dxf_path|Cache-Control"
  Check: Does svg_path change between calls?

  4. CHECK FILENAME GENERATION IN VECTORIZER

  grep -n "svg\|dxf" C:/Users/thepr/Downloads/luthiers-toolbox/services/photo-vectorizer/photo_vectorizer_v2.py | head -20
  Check: Are filenames unique or static?

  5. INSPECT _output_file_registry AT RUNTIME

  Add temporary logging to phase2_router.py:
  logger.info(f"Registry state: {_output_file_registry}")

  6. CHECK GIT HISTORY FOR ANOMALY WINDOW

  git -C "C:/Users/thepr/Downloads/luthiers-toolbox" log --since="2026-03-01 20:34" --until="2026-04-02 01:57" --oneline

  ---
  CONFIDENCE REPORT

  Areas with Solid Evidence

  - ✅ CORS configuration is correct for port 5188
  - ✅ Backend health check passes on port 8001
  - ✅ .env.local points to correct backend port
  - ✅ Cache-busting code exists in useBlueprintWorkflow.ts:567
  - ✅ adobeCleanFontAdded is NOT from this application

  Areas with Missing Data

  - ❓ Whether backend was successfully restarted after fix
  - ❓ Actual HTTP response headers from /api/blueprint/static/
  - ❓ Whether vectorizer generates unique or static filenames
  - ❓ What files were modified during anomaly window
  - ❓ Frontend Network tab showing actual API responses

  Highest Risk of Incorrect Assumptions

  1. "Backend was restarted" - User interrupted the restart; _output_file_registry may still hold stale paths
  2. "Cache headers are being sent" - Not verified via curl -v or DevTools
  3. "Vectorizer generates unique filenames" - Not verified; if static filenames, overwrite should work but race conditions possible

  ---
  IMMEDIATE ACTION REQUIRED: Complete the backend restart that was interrupted. The in-memory _output_file_registry is the most likely source of stale data and only clears on process restart.
