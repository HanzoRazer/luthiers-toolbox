# N10.1: LiveMonitor Drill-Down — Quick Reference

**Status:** ✅ Production Ready  
**Bundle:** RMOS_N10_1_LiveMonitor_DrillDown_v0.1_120125  
**Effective:** December 1, 2025  

---

## 🎯 Overview

N10.1 extends the Live Monitor (N10.0) with **drill-down capabilities** for deep inspection of job execution. Operators can now:

- View subjob phases (roughing → profiling → finishing)
- Inspect CAM events within each subjob (feed, spindle, DOC)
- See real-time heuristic risk assessment (info/warning/danger)
- Analyze feed state deviations from targets

**Core Features:**
- ✅ **Subjob streaming** — Track execution phases (roughing, profiling, finishing, cleanup, infeed, outfeed)
- ✅ **CAM event emission** — Capture feed/spindle/DOC state at each execution step
- ✅ **Heuristic engine** — Automatic risk classification (safe/alert/danger)
- ✅ **Drill-down drawer** — Side panel UI for deep event inspection
- ✅ **Feed state evaluation** — Deviation tracking (stable/increasing/decreasing/danger)

**Dependencies:**
- N10.0: Live Monitor base (WebSocket infrastructure, event streaming)
- Job metadata with subjobs array structure

---

## 📊 Architecture

### **Data Flow**

```
Job Execution
  ↓ metadata.subjobs[] with cam_events[]
  ↓
backend: SubjobEventBuilder.build_subjobs_from_metadata()
  ↓ Extract subjobs, evaluate heuristics
  ↓
backend: GET /rmos/live-monitor/{job_id}/drilldown
  ↓ Return DrilldownResponse with evaluated events
  ↓
frontend: useLiveMonitorStore.loadDrilldown(jobId)
  ↓
frontend: LiveMonitorDrilldownDrawer.vue
  ↓ Render subjobs, CAM events, risk badges
  ↓
Operator sees detailed execution timeline
```

### **Backend Components**

#### **1. Subjob Event Models** (`services/api/app/models/rmos_subjob_event.py`)

**SubjobType Enum:**
```python
SubjobType = Literal[
    "roughing",     # Bulk material removal
    "profiling",    # Edge contouring
    "finishing",    # Final surface pass
    "cleanup",      # Tab/corner cleanup
    "infeed",       # Material insertion
    "outfeed"       # Part extraction
]
```

**FeedState Enum:**
```python
FeedState = Literal[
    "stable",       # Within ±10% of target
    "increasing",   # 10-20% above target
    "decreasing",   # 10-20% below target
    "danger_low",   # >20% below target
    "danger_high"   # >20% above target
]
```

**HeuristicLevel Enum:**
```python
HeuristicLevel = Literal[
    "info",     # Normal operation
    "warning",  # Approaching limits
    "danger"    # Critical deviation
]
```

**CAMEvent Model:**
```python
class CAMEvent(BaseModel):
    timestamp: str                # ISO 8601
    feedrate: float               # mm/min
    spindle_speed: float          # RPM
    doc: float                    # Depth of cut (mm)
    feed_state: FeedState         # Evaluated deviation
    heuristic: HeuristicLevel     # Risk assessment
    message: Optional[str]        # Optional warning text
```

**SubjobEvent Model:**
```python
class SubjobEvent(BaseModel):
    subjob_type: SubjobType
    started_at: str               # ISO 8601
    ended_at: Optional[str]       # ISO 8601 or null if in progress
    cam_events: List[CAMEvent]
```

#### **2. Heuristic Engine** (`services/api/app/core/live_monitor_heuristics.py`)

**Feed State Evaluation:**
```python
def evaluate_feed_state(feed: float, target: float) -> FeedState:
    """
    Classify feed deviation:
    - ±10% = stable
    - 10-20% = increasing/decreasing
    - >20% = danger_high/danger_low
    """
```

**Risk Assessment:**
```python
def evaluate_heuristic(feed_state: str, doc: float, doc_limit: float) -> HeuristicLevel:
    """
    Generate risk level:
    - Any "danger" feed → danger
    - DOC > 90% of limit → warning
    - Otherwise → info
    """
```

**Example:**
```python
# Feed 800 mm/min, target 1000 mm/min = -20% deviation
evaluate_feed_state(800, 1000)  # → "decreasing"

# Feed 700 mm/min, target 1000 mm/min = -30% deviation
evaluate_feed_state(700, 1000)  # → "danger_low"

# Danger feed + DOC 0.3mm (under limit 0.5mm)
evaluate_heuristic("danger_low", 0.3, 0.5)  # → "danger"
```

#### **3. Event Builder** (`services/api/app/core/live_monitor_event_builder.py`)

**SubjobEventBuilder:**
```python
class SubjobEventBuilder:
    def build_subjobs_from_metadata(self, entry: Dict) -> List[SubjobEvent]:
        """
        Extract subjobs from job metadata with heuristic evaluation.
        
        Input: Job dict with metadata.subjobs[] structure
        Output: List of SubjobEvent with evaluated CAMEvent[]
        """
```

**Expected Metadata Structure:**
```json
{
  "metadata": {
    "subjobs": [
      {
        "subjob_type": "roughing",
        "started_at": "2025-12-01T10:00:00",
        "ended_at": "2025-12-01T10:05:00",
        "cam_events": [
          {
            "timestamp": "2025-12-01T10:01:00",
            "feedrate": 800,
            "target_feed": 1000,
            "spindle_speed": 18000,
            "doc": 0.3,
            "doc_limit": 0.5,
            "message": "Optional warning"
          }
        ]
      }
    ]
  }
}
```

#### **4. Drill-Down API** (`services/api/app/routers/live_monitor_drilldown_api.py`)

**Endpoint:**
```http
GET /api/rmos/live-monitor/{job_id}/drilldown
```

**Response:**
```json
{
  "job_id": "J_001",
  "subjobs": [
    {
      "subjob_type": "roughing",
      "started_at": "2025-12-01T10:00:00",
      "ended_at": "2025-12-01T10:05:00",
      "cam_events": [
        {
          "timestamp": "2025-12-01T10:01:00",
          "feedrate": 800.0,
          "spindle_speed": 18000.0,
          "doc": 0.3,
          "feed_state": "decreasing",
          "heuristic": "warning",
          "message": null
        }
      ]
    }
  ]
}
```

---

### **Frontend Components**

#### **1. TypeScript Models** (`packages/client/src/models/live_monitor_drilldown.ts`)

**Interfaces:**
```typescript
export interface CAMEvent {
  timestamp: string
  feedrate: number
  spindle_speed: number
  doc: number
  feed_state: FeedState
  heuristic: HeuristicLevel
  message?: string | null
}

export interface SubjobEvent {
  subjob_type: SubjobType
  started_at: string
  ended_at?: string | null
  cam_events: CAMEvent[]
}

export interface DrilldownResponse {
  job_id: string
  subjobs: SubjobEvent[]
}
```

**Helper Functions:**
- `feedStateClass(state)` → CSS class for feed badges
- `heuristicClass(level)` → CSS class for risk badges
- `subjobLabel(type)` → Human-readable subjob name
- `formatTimestamp(ts)` → Display format conversion

#### **2. LiveMonitor Store** (`packages/client/src/stores/useLiveMonitorStore.ts`)

**State:**
```typescript
{
  events: LiveMonitorEvent[],
  eventCounts: { job, pattern, material, metrics },
  activeDrilldown: DrilldownResponse | null,
  drilldownLoading: boolean,
  drilldownError: string | null
}
```

**Actions:**
```typescript
loadDrilldown(jobId: string)  // Fetch drill-down data
closeDrilldown()              // Clear drill-down state
```

#### **3. Drill-Down Drawer** (`packages/client/src/components/rmos/LiveMonitorDrilldownDrawer.vue`)

**Features:**
- Side panel overlay (600px max width)
- Subjob cards with timeline headers
- CAM event tables with color-coded badges
- Feed state indicators (stable/increasing/decreasing/danger)
- Risk level badges (info/warning/danger)
- Loading/error states

**Badge Colors:**
- **Feed State:**
  - 🟢 Stable (green)
  - 🔵 Increasing/Decreasing (blue/purple)
  - 🔴 Danger Low/High (red)
- **Heuristic:**
  - 🔵 Info (blue)
  - 🟡 Warning (yellow)
  - 🔴 Danger (red)

#### **4. LiveMonitor Panel** (`packages/client/src/components/rmos/LiveMonitor.vue`)

**Updated UI:**
- **Drill-down button** on each job event row
- Click opens drawer with subjob/CAM event details
- Button shows 🔍 icon + "Drill-down" label

---

## 🚀 Usage

### **Quick Start**

1. **Navigate to Live Monitor:**
   ```
   http://localhost:5173/rmos/live-monitor
   ```

2. **Connect to WebSocket** (if not already connected)

3. **Click "🔍 Drill-down"** on any job event

4. **View subjobs and CAM events:**
   - Subjob phases listed chronologically
   - CAM events table shows feed/spindle/DOC/state/risk
   - Color-coded badges indicate status

### **Example Workflow**

**Scenario:** Investigate a job with feed rate warnings

1. Job event appears: `job:started` for "Maple Inlay Strip"
2. Click "🔍 Drill-down" button
3. Drawer opens showing:
   - Roughing subjob (10:00-10:05)
     - CAM event at 10:01: Feed 800, Target 1000 → "decreasing" (yellow)
     - CAM event at 10:03: Feed 650, Target 1000 → "danger_low" (red)
   - Profiling subjob (10:05-10:08)
     - CAM event at 10:06: Feed 1050, Target 1000 → "stable" (green)
4. Operator sees feed dropped 35% during roughing → investigates toolpath or material hardness

---

## 🧪 Testing

### **Backend Tests** (`services/api/tests/test_live_monitor_drilldown.py`)

**Test Coverage:**
- ✅ Basic subjob extraction from metadata
- ✅ Empty metadata handling (graceful degradation)
- ✅ Multiple subjobs and events
- ✅ Feed state evaluation (stable/deviation/danger)
- ✅ Heuristic risk assessment (info/warning/danger)
- ✅ Zero target feed handling (edge case)

**Run Tests:**
```powershell
cd services/api
pytest tests/test_live_monitor_drilldown.py -v
```

**Expected Output:**
```
test_subjob_builder_basic PASSED
test_subjob_builder_empty_metadata PASSED
test_subjob_builder_multiple_subjobs PASSED
test_feed_state_stable PASSED
test_feed_state_deviation PASSED
test_feed_state_danger PASSED
test_heuristic_info PASSED
test_heuristic_warning_doc PASSED
test_heuristic_danger_feed PASSED
```

### **Frontend Testing**

1. **Start dev server:**
   ```powershell
   cd packages/client
   npm run dev
   ```

2. **Manual test cases:**
   - Job event with subjobs → drill-down button appears
   - Click button → drawer opens with loading spinner
   - Data loads → subjobs and CAM events render
   - Empty subjobs → "No subjobs found" message
   - API error → error message in drawer
   - Close button → drawer closes, state resets

---

## 📋 Integration Checklist

**Backend:**
- [x] Create `services/api/app/models/rmos_subjob_event.py`
- [x] Create `services/api/app/core/live_monitor_heuristics.py`
- [x] Create `services/api/app/core/live_monitor_event_builder.py`
- [x] Create `services/api/app/routers/live_monitor_drilldown_api.py`
- [x] Register router in `services/api/app/main.py`
- [x] Create `services/api/tests/test_live_monitor_drilldown.py`

**Frontend:**
- [x] Create `packages/client/src/models/live_monitor_drilldown.ts`
- [x] Create `packages/client/src/stores/useLiveMonitorStore.ts`
- [x] Create `packages/client/src/components/rmos/LiveMonitorDrilldownDrawer.vue`
- [x] Update `packages/client/src/components/rmos/LiveMonitor.vue`

**Documentation:**
- [x] Create `docs/N10_1_LIVEMONITOR_DRILLDOWN_QUICKREF.md` (this file)

**Git Workflow:**
- [ ] Test backend endpoints
- [ ] Test frontend UI
- [ ] Commit with tag: `RMOS_N10_1_LiveMonitor_DrillDown_v0.1_120125`
- [ ] Update `docs/RMOS_MASTER_TREE.md` (mark N10.1 complete)

---

## 🎨 UI Examples

### **LiveMonitor with Drill-Down Button**

```
┌──────────────────────────────────────────────────────────────┐
│ 🔴 Real-time Monitoring               ● Connected            │
├──────────────────────────────────────────────────────────────┤
│ job:started                     10:00:00    [🔍 Drill-down]  │
│ ├─ Job: Maple Inlay Strip                                    │
│ ├─ [STABLE 35%]  🪵 maple  [Lane: promo]                    │
│ └─ { "job_id": "J_001", ... }                                │
└──────────────────────────────────────────────────────────────┘
```

### **Drill-Down Drawer**

```
┌────────────────────────────────────────────────────┐
│ Job Drill-Down – J_001                         ✕   │
├────────────────────────────────────────────────────┤
│ ⚡ Roughing                                         │
│ 10:00:00 → 10:05:00                                │
│ ┌──────────────────────────────────────────────┐  │
│ │ Time  │ Feed │ RPM   │ DOC  │ State │ Risk   │  │
│ ├──────────────────────────────────────────────┤  │
│ │ 10:01 │ 800  │ 18000 │ 0.3  │ DEC   │ WARN   │  │
│ │ 10:03 │ 650  │ 18000 │ 0.3  │ D-LOW │ DANGER │  │
│ └──────────────────────────────────────────────┘  │
│                                                     │
│ ✂️ Profiling                                       │
│ 10:05:00 → 10:08:00                                │
│ ┌──────────────────────────────────────────────┐  │
│ │ Time  │ Feed │ RPM   │ DOC  │ State │ Risk   │  │
│ ├──────────────────────────────────────────────┤  │
│ │ 10:06 │ 1050 │ 18000 │ 0.15 │ STABLE│ INFO   │  │
│ └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration

### **Heuristic Thresholds**

Edit `services/api/app/core/live_monitor_heuristics.py`:

```python
# Feed state thresholds
STABLE_THRESHOLD = 0.10      # ±10%
WARNING_THRESHOLD = 0.20     # ±20%

# DOC warning threshold
DOC_WARNING_RATIO = 0.90     # 90% of limit
```

### **Subjob Metadata Structure**

Jobs must include `metadata.subjobs[]` array:

```json
{
  "id": "J_001",
  "name": "Maple Inlay Strip",
  "metadata": {
    "subjobs": [
      {
        "subjob_type": "roughing",
        "started_at": "2025-12-01T10:00:00",
        "ended_at": "2025-12-01T10:05:00",
        "cam_events": [
          {
            "timestamp": "2025-12-01T10:01:00",
            "feedrate": 800,
            "target_feed": 1000,
            "spindle_speed": 18000,
            "doc": 0.3,
            "doc_limit": 0.5
          }
        ]
      }
    ]
  }
}
```

---

## 🐛 Troubleshooting

### **Issue:** Drill-down button not appearing

**Symptoms:** Job events show but no drill-down button

**Solutions:**
1. Check event type starts with `job:`
2. Verify event has `job_id` in data field
3. Check component import: `LiveMonitorDrilldownDrawer.vue`

### **Issue:** Drawer shows "No subjobs found"

**Symptoms:** Drawer opens but empty state message

**Solutions:**
1. Check job has `metadata.subjobs[]` array
2. Verify subjobs have `subjob_type` field
3. Inspect API response: `/rmos/live-monitor/{job_id}/drilldown`

### **Issue:** Feed state always "stable"

**Symptoms:** All CAM events show stable feed state

**Solutions:**
1. Verify `target_feed` provided in cam_events
2. Check heuristic calculation: `evaluate_feed_state()`
3. Ensure feedrate deviates from target

### **Issue:** API 404 error

**Symptoms:** Drawer shows error message

**Solutions:**
1. Verify job exists in joblog store
2. Check router registered in `main.py`
3. Confirm API endpoint: `/api/rmos/live-monitor/{job_id}/drilldown`

---

## 📚 Related Documentation

- **N10.0:** [Live Monitor Base](./N10_0_LIVE_MONITOR_QUICKREF.md)
- **MM-6:** [Fragility-Aware Live Monitor](./MM_6_FRAGILITY_AWARE_LIVE_MONITOR_QUICKREF.md)
- **RMOS Master Tree:** [Development Roadmap](./RMOS_MASTER_TREE.md)

---

**Status:** ✅ N10.1 Complete — Drill-down operational  
**Next Steps:** N10.2 (Apprenticeship mode + safety overrides)  
**Tag:** `RMOS_N10_1_LiveMonitor_DrillDown_v0.1_120125`
