<template>
  <div class="wrap">
    <PatternLibraryPanel />
    <div class="mid">
      <div class="toolbar" v-if="store.problematicRingIndices.length > 0">
        <button
          class="jump-btn"
          type="button"
          title="Jump to previous problematic ring ([)"
          @click="jumpPrev"
        >
          Prev
        </button>
        <button
          class="jump-btn"
          type="button"
          title="Jump to next problematic ring (])"
          @click="jumpNext"
        >
          Next
        </button>
        <span class="problem-count">{{ store.problematicRingIndices.length }} problems</span>
        <button
          class="jump-btn"
          type="button"
          :title="store.jumpSeverity === 'RED_ONLY'
            ? 'Jump filter: RED only (click to include YELLOW)'
            : 'Jump filter: RED + YELLOW (click for RED only)'"
          @click="store.toggleJumpSeverity()"
        >
          {{ store.jumpSeverity === "RED_ONLY" ? "RED only" : "RED+YELLOW" }}
        </button>
        <div
          class="jump-hud"
          :class="{ pulse: hudPulse }"
          v-if="store.totalRingCount > 0"
        >
          <span class="pill">
            {{ store.jumpSeverity === "RED_ONLY" ? "Filter: RED only" : "Filter: RED+YELLOW" }}
          </span>
          <span class="pill">
            RED rings: {{ store.redRingCount }} / {{ store.totalRingCount }}
          </span>
          <span class="pill" v-if="store.jumpRingPosition.total > 0">
            Focus: {{ store.jumpRingPosition.pos || "—" }} / {{ store.jumpRingPosition.total }}
          </span>
          <!-- Bundle 32.3.8: HUD help tooltip -->
          <span class="hud-help" tabindex="0" aria-label="Jump hotkeys help">
            ?
            <span class="hud-tooltip" role="tooltip">
              <div class="tt-title">Jump hotkeys</div>
              <div class="tt-row"><kbd>[</kbd> Prev problem</div>
              <div class="tt-row"><kbd>]</kbd> Next problem</div>
              <div class="tt-row"><kbd>w</kbd> Jump to worst</div>
              <div class="tt-row"><kbd>Shift</kbd> + <kbd>R</kbd> Toggle filter</div>
            </span>
          </span>
        </div>
        <!-- Bundle 32.4.0: Undo button -->
        <button
          class="jump-btn undo-btn"
          type="button"
          title="Undo last edit (Ctrl+Z)"
          :disabled="store.historyStack.length === 0"
          @click="store.undoLastEdit()"
        >
          Undo
        </button>
      </div>

      <!-- Bundle 32.4.0: Ring Nudge Section -->
      <div class="ring-nudge-section" v-if="store.currentParams?.ring_params?.length">
        <div class="nudge-title">Ring Widths</div>
        <div
          class="ring-row"
          v-for="(ring, idx) in store.currentParams.ring_params"
          :key="idx"
          :data-ring-index="idx"
          :class="{ focused: store.focusedRingIndex === idx }"
        >
          <span class="ring-label">Ring {{ idx + 1 }}</span>
          <span class="ring-width">{{ Number(ring.width_mm || 0).toFixed(2) }} mm</span>
          <div class="ring-actions">
            <button
              class="mini"
              type="button"
              title="Shrink width by 0.10 mm"
              :disabled="store.isRedBlocked"
              @click="store.nudgeRingWidth(idx, -0.1)"
            >−0.10</button>
            <button
              class="mini"
              type="button"
              title="Grow width by 0.10 mm"
              :disabled="store.isRedBlocked"
              @click="store.nudgeRingWidth(idx, 0.1)"
            >+0.10</button>
            <button
              class="mini dist"
              type="button"
              title="Shrink width, distribute to neighbors"
              :disabled="store.isRedBlocked"
              @click="store.nudgeRingWidthDistribute(idx, -0.1)"
            >−0.10↔</button>
            <button
              class="mini dist"
              type="button"
              title="Grow width, distribute to neighbors"
              :disabled="store.isRedBlocked"
              @click="store.nudgeRingWidthDistribute(idx, 0.1)"
            >+0.10↔</button>
          </div>
        </div>
      </div>

      <!-- Bundle 32.4.2: History mini-stack panel -->
      <HistoryStackPanel />

      <GeneratorPicker />
      <FeasibilityBanner />
      <SnapshotPanel />
    </div>
    <RosettePreviewPanel />
    <!-- Bundle 32.4.1: Toast host for inline notifications -->
    <ToastHost />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";
import PatternLibraryPanel from "./PatternLibraryPanel.vue";
import GeneratorPicker from "./GeneratorPicker.vue";
import RosettePreviewPanel from "./RosettePreviewPanel.vue";
import SnapshotPanel from "./SnapshotPanel.vue";
import FeasibilityBanner from "./FeasibilityBanner.vue";
import ToastHost from "@/components/ui/ToastHost.vue";
import HistoryStackPanel from "./HistoryStackPanel.vue";

const store = useRosetteStore();

// Bundle 32.3.7: HUD pulse on filter toggle
const hudPulse = ref(false);

watch(
  () => store.jumpSeverity,
  () => {
    hudPulse.value = true;
    window.setTimeout(() => (hudPulse.value = false), 260);
  }
);

onMounted(async () => {
  await store.loadPatterns();
  await store.loadGenerators();
  await store.loadRecentSnapshots();
  await store.refreshPreviewAndFeasibility();

  // Keyboard shortcut: ] = jump to next problematic ring (Bundle 32.3.3)
  window.addEventListener("keydown", onKeyDown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeyDown);
});

function onKeyDown(e: KeyboardEvent) {
  // ] key -> jump to next problematic ring
  if (e.key === "]" && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    store.jumpToNextProblemRing();
  }

  // [ key -> jump to previous problematic ring (Bundle 32.3.4)
  if (e.key === "[" && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    store.jumpToPreviousProblemRing();
  }

  // Shift+R toggles severity filter (Bundle 32.3.5)
  if ((e.key === "R" || e.key === "r") && e.shiftKey && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    store.toggleJumpSeverity();
  }

  // w → jump to worst problematic ring (Bundle 32.3.7)
  if ((e.key === "w" || e.key === "W") && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    store.jumpToWorstProblemRing();
  }

  // Bundle 32.4.0: Ctrl+Z / Cmd+Z → undo last edit
  if (e.key === "z" && (e.ctrlKey || e.metaKey) && !e.shiftKey) {
    e.preventDefault();
    store.undoLastEdit();
  }
}

function jumpNext() {
  store.jumpToNextProblemRing();
}

function jumpPrev() {
  store.jumpToPreviousProblemRing();
}

// Auto refresh: debounce on any param change
watch(
  () => store.currentParams,
  () => {
    store.requestAutoRefresh();
  },
  { deep: true }
);
</script>

<style scoped>
.wrap {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  padding: 12px;
}
.mid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
}
.jump-btn {
  font-size: 11px;
  font-weight: 700;
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid #f3bcbc;
  background: #fdeaea;
  color: #a00;
  cursor: pointer;
}
.jump-btn:hover {
  background: #fbd5d5;
}
.problem-count {
  font-size: 11px;
  font-weight: 600;
  color: #a00;
}
.jump-hud {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 8px;
  flex-wrap: wrap;
}
.pill {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 999px;
  border: 1px solid #e6e6e6;
  background: #fafafa;
  color: #444;
}
.jump-hud.pulse {
  animation: hudPulse 260ms ease-out;
}

/* Bundle 32.3.8: HUD help tooltip styles */
.hud-help {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  border: 1px solid #e6e6e6;
  background: #fff;
  color: #555;
  font-size: 12px;
  font-weight: 900;
  cursor: help;
  user-select: none;
}
.hud-tooltip {
  position: absolute;
  right: 0;
  top: 24px;
  min-width: 170px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #e6e6e6;
  background: #fff;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  font-size: 11px;
  color: #333;
  z-index: 20;
  display: none;
}
.hud-help:hover .hud-tooltip,
.hud-help:focus .hud-tooltip,
.hud-help:focus-within .hud-tooltip {
  display: block;
}
.tt-title {
  font-weight: 800;
  margin-bottom: 6px;
  color: #111;
}
.tt-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 0;
}
kbd {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 10px;
  padding: 2px 6px;
  border: 1px solid #ddd;
  border-bottom-width: 2px;
  border-radius: 6px;
  background: #fafafa;
  color: #222;
}

@keyframes hudPulse {
  0% {
    transform: scale(1);
    filter: brightness(1);
  }
  45% {
    transform: scale(1.02);
    filter: brightness(1.06);
  }
  100% {
    transform: scale(1);
    filter: brightness(1);
  }
}
@media (max-width: 1100px) {
  .wrap {
    grid-template-columns: 1fr;
  }
}

/* Bundle 32.4.0: Undo button styles */
.undo-btn {
  margin-left: auto;
}
.undo-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Bundle 32.4.0: Ring nudge section styles */
.ring-nudge-section {
  background: #fafafa;
  border: 1px solid #e6e6e6;
  border-radius: 10px;
  padding: 10px 12px;
  max-height: 240px;
  overflow-y: auto;
}
.nudge-title {
  font-size: 11px;
  font-weight: 800;
  color: #333;
  margin-bottom: 8px;
}
.ring-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border-radius: 6px;
  margin-bottom: 4px;
}
.ring-row.focused {
  background: #fff3cd;
  border: 1px solid #ffc107;
}
.ring-label {
  font-size: 11px;
  font-weight: 600;
  color: #555;
  min-width: 50px;
}
.ring-width {
  font-size: 11px;
  font-weight: 700;
  color: #222;
  min-width: 55px;
  text-align: right;
}
.ring-actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
}
.ring-actions .mini {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 6px;
  border-radius: 6px;
  border: 1px solid #ccc;
  background: #fff;
  color: #333;
  cursor: pointer;
}
.ring-actions .mini:hover:not(:disabled) {
  background: #e8e8e8;
}
.ring-actions .mini:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.ring-actions .mini.dist {
  border-color: #a8d4f0;
  background: #e8f4fc;
  color: #0066aa;
}
.ring-actions .mini.dist:hover:not(:disabled) {
  background: #cce8f7;
}
</style>
