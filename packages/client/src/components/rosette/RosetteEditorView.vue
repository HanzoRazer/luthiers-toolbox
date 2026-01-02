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
      </div>
      <GeneratorPicker />
      <FeasibilityBanner />
      <SnapshotPanel />
    </div>
    <RosettePreviewPanel />
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
</style>
