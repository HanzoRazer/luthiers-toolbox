# Agentic Event Integration Snippets

Exact code snippets for wiring M1 Advisory Mode events into existing Vue components.

---

## AudioAnalyzerViewer.vue

### 1. Add import at top of `<script setup>`

```typescript
import { useAgenticEvents } from "@/composables/useAgenticEvents";

const { emitViewRendered, emitArtifactCreated, emitUserAction, emitAnalysisFailed } = useAgenticEvents();
```

### 2. Emit on successful pack load (inside `loadZip()`)

```typescript
async function loadZip(f: File) {
  resetError();
  try {
    pack.value = await loadNormalizedPack(f);

    // --- AGENTIC: Emit artifact created ---
    const hasWolfData = pack.value.files.some(f => f.kind.includes('wolf'));
    const hasOdsData = pack.value.files.some(f => f.kind.includes('ods'));
    if (hasWolfData) {
      emitArtifactCreated('wolf_candidates_v1', 0.75);
    }
    if (hasOdsData) {
      emitArtifactCreated('ods_snapshot_v1', 0.8);
    }
    // Trigger FIRST_SIGNAL for pack loaded
    emitViewRendered('audio_analyzer', pack.value.schema_id);
    // --- END AGENTIC ---

    // ... rest of existing code
  } catch (e: unknown) {
    pack.value = null;
    activePath.value = "";
    err.value = e instanceof Error ? e.message : String(e);

    // --- AGENTIC: Emit failure ---
    emitAnalysisFailed(err.value);
    // --- END AGENTIC ---
  }
}
```

### 3. Emit on peak selection (inside `onPeakSelected()`)

```typescript
function onPeakSelected(payload: any) {
  audioJumpError.value = "";
  const freq_hz = Number(payload?.freq_hz);
  if (!Number.isFinite(freq_hz)) return;

  // --- AGENTIC: Emit user interaction ---
  emitUserAction('peak_selected', { freq_hz, spectrum: activePath.value });
  // --- END AGENTIC ---

  // ... rest of existing code
}
```

---

## DxfToGcodeView.vue (CAM Workflow)

### 1. Add import

```typescript
import { useAgenticEvents } from "@/composables/useAgenticEvents";

const { emitViewRendered, emitAnalysisCompleted, emitParameterChanged, emitDecisionRequired } = useAgenticEvents();
```

### 2. Emit when run completes

```typescript
// After successful CAM run
emitAnalysisCompleted(['gcode_v1', 'toolpath_v1']);
emitViewRendered('cam_result', runId);
```

### 3. Emit when user changes parameters

```typescript
// On parameter slider/input change
function onFeedRateChange(newValue: number) {
  feedRate.value = newValue;
  emitParameterChanged('feed_rate', newValue);
}
```

### 4. Emit when decision is required (e.g., risk override)

```typescript
// When YELLOW/RED risk detected
if (riskLevel === 'YELLOW' || riskLevel === 'RED') {
  emitDecisionRequired('risk_override', ['proceed', 'abort', 'review']);
}
```

---

## ArtStudioRosette.vue (Design Workflow)

### 1. Add import

```typescript
import { useAgenticEvents } from "@/composables/useAgenticEvents";

const { emitViewRendered, emitUserAction, emitUndo } = useAgenticEvents();
```

### 2. Emit on initial render

```typescript
onMounted(() => {
  emitViewRendered('rosette_designer', 'main');
});
```

### 3. Emit on undo

```typescript
function undoChange() {
  // existing undo logic
  historyStack.pop();
  emitUndo('rosette_parameter');
}
```

---

## Global Idle Timer (App.vue or dedicated component)

Add an idle detector to trigger HESITATION moments:

```typescript
// In App.vue or a dedicated IdleDetector.vue
import { onMounted, onUnmounted } from 'vue';
import { useAgenticEvents } from '@/composables/useAgenticEvents';

const { emitIdleTimeout } = useAgenticEvents();

let idleTimer: number | null = null;
const IDLE_THRESHOLD_MS = 8000; // 8 seconds

function resetIdleTimer() {
  if (idleTimer) clearTimeout(idleTimer);
  idleTimer = window.setTimeout(() => {
    emitIdleTimeout(IDLE_THRESHOLD_MS / 1000);
  }, IDLE_THRESHOLD_MS);
}

onMounted(() => {
  ['mousemove', 'keydown', 'click', 'scroll'].forEach(evt => {
    window.addEventListener(evt, resetIdleTimer, { passive: true });
  });
  resetIdleTimer();
});

onUnmounted(() => {
  if (idleTimer) clearTimeout(idleTimer);
  ['mousemove', 'keydown', 'click', 'scroll'].forEach(evt => {
    window.removeEventListener(evt, resetIdleTimer);
  });
});
```

---

## Testing M1 Locally

```bash
# Start with M1 enabled
cd packages/client
VITE_AGENTIC_MODE=M1 npm run dev

# In browser console, manually trigger:
# 1. Import the store
const store = window.__PINIA__.state.value.agenticDirective

# 2. Emit a test event
store.emitEvent('analysis_completed', { artifacts_created: ['wolf_candidates_v1'] })

# 3. Coach Bubble should appear with "Inspect this"
```

---

## Event → Moment → Directive Mapping

| Event Type | Triggers Moment | Directive |
|------------|----------------|-----------|
| `analysis_completed` | FIRST_SIGNAL | "Inspect this" |
| `artifact_created` (confidence ≥ 0.6) | FINDING | "Review this" |
| `idle_timeout` | HESITATION | "Inspect this" |
| `user_feedback` (too_much) | OVERLOAD | "Review this" |
| `user_action` (undo × 3) | OVERLOAD | "Review this" |
| `decision_required` | DECISION_REQUIRED | "Make a choice" |
| `analysis_failed` | ERROR | "Review this" |

---

**End of Snippets**
