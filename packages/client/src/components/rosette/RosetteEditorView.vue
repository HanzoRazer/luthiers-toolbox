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
          ref="undoBtnRef"
          class="jump-btn undo-btn"
          :class="{ shake: shakeUndo }"
          type="button"
          :title="undoTitle"
          :disabled="store.historyStack.length === 0"
          @click="() => undo('clicked')"
        >
          Undo
        </button>
        <!-- Bundle 32.4.3.1: Redo button -->
        <button
          ref="redoBtnRef"
          class="jump-btn redo-btn"
          :class="{ shake: shakeRedo }"
          type="button"
          :title="redoTitle"
          :disabled="store.redoStack.length === 0"
          @click="() => redo('clicked')"
        >
          Redo
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

      <!-- Bundle 32.4.2 + 32.4.15: History mini-stack panel with keyboard hint overlay -->
      <div class="historyWrap">
        <HistoryStackPanel
          :highlight-idx-from-top="historyHotkeyFlash"
          @reverted="(idx) => {
            flashHistoryIdx(idx);
            const labels = store.getRecentHistoryLabels(5);
            if (idx < labels.length) {
              toast.push({
                level: 'info',
                message: `Reverted: ${labels[idx]}`,
                detail: 'Source: clicked',
                durationMs: 1800,
              });
            }
          }"
        />

        <!-- Bundle 32.4.15: Keyboard hint overlay -->
        <div v-if="showHistoryHotkeyHint && hasHistory" class="hotkeyHint" role="note">
          <div class="hotkeyHintTitle">Keyboard tip</div>
          <div class="hotkeyHintBody">
            Try <b>1–5</b> to revert history (1 = newest)
          </div>
          <button class="hotkeyHintClose" type="button" @click="hideHint" aria-label="Dismiss">
            ✕
          </button>
        </div>
      </div>

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
import { computed, ref, onMounted, onBeforeUnmount, watch } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useUiToastStore } from "@/stores/uiToastStore";
import PatternLibraryPanel from "./PatternLibraryPanel.vue";
import GeneratorPicker from "./GeneratorPicker.vue";
import RosettePreviewPanel from "./RosettePreviewPanel.vue";
import SnapshotPanel from "./SnapshotPanel.vue";
import FeasibilityBanner from "./FeasibilityBanner.vue";
import ToastHost from "@/components/ui/ToastHost.vue";
import HistoryStackPanel from "./HistoryStackPanel.vue";

const store = useRosetteStore();
const toast = useUiToastStore();

// Bundle 32.4.14: Computed tooltip strings with disabled reasons + hotkeys
const undoTitle = computed(() => {
  const has = !!(store.historyStack && store.historyStack.length);
  return has
    ? "Undo last ring edit (Ctrl/Cmd+Z)"
    : "Nothing to undo yet (Ctrl/Cmd+Z)";
});

const redoTitle = computed(() => {
  const has = !!(store.redoStack && store.redoStack.length);
  return has
    ? "Redo last undone edit (Ctrl/Cmd+Shift+Z)"
    : "Nothing to redo yet (Ctrl/Cmd+Shift+Z)";
});

// Bundle 32.4.13: Button refs + shake state for disabled undo/redo feedback
const undoBtnRef = ref<HTMLButtonElement | null>(null);
const redoBtnRef = ref<HTMLButtonElement | null>(null);

const shakeUndo = ref(false);
const shakeRedo = ref(false);

function triggerShake(which: "undo" | "redo") {
  if (which === "undo") {
    shakeUndo.value = false; // restart animation
    requestAnimationFrame(() => (shakeUndo.value = true));
    window.setTimeout(() => (shakeUndo.value = false), 260);
    undoBtnRef.value?.focus?.();
  } else {
    shakeRedo.value = false;
    requestAnimationFrame(() => (shakeRedo.value = true));
    window.setTimeout(() => (shakeRedo.value = false), 260);
    redoBtnRef.value?.focus?.();
  }
}

// Bundle 32.4.11: Toast helper for undo/redo with source tracking
function toastUndoRedo(kind: "undo" | "redo", source: "keyboard" | "clicked", label?: string) {
  const verb = kind === "undo" ? "Undo" : "Redo";
  toast.push({
    level: "info",
    message: label ? `${verb}: ${label}` : verb,
    detail: `Source: ${source}`,
    durationMs: 1800,
  });
}

// Bundle 32.4.11: Undo wrapper with label-aware toast
// Bundle 32.4.12: No-op suppression (no toast when stack empty)
// Bundle 32.4.13: Shake feedback when unavailable
function undo(source: "keyboard" | "clicked" = "clicked") {
  const stack = store.historyStack ?? [];
  if (!stack.length) {
    triggerShake("undo");
    return;
  }

  const label = String(stack[stack.length - 1]?.label ?? "Edit");

  store.undoLastEdit();
  toastUndoRedo("undo", source, label);
}

// Bundle 32.4.11: Redo wrapper with label-aware toast
// Bundle 32.4.12: No-op suppression (no toast when stack empty)
// Bundle 32.4.13: Shake feedback when unavailable
function redo(source: "keyboard" | "clicked" = "clicked") {
  const stack = store.redoStack ?? [];
  if (!stack.length) {
    triggerShake("redo");
    return;
  }

  const label = String(stack[stack.length - 1]?.label ?? "Edit");

  store.redoLastEdit();
  toastUndoRedo("redo", source, label);
}

// Bundle 32.4.8: Flash state for history hotkey highlight
const historyHotkeyFlash = ref<number | null>(null);
let flashTimer: number | null = null;

function flashHistoryIdx(idx: number) {
  historyHotkeyFlash.value = idx;
  if (flashTimer) window.clearTimeout(flashTimer);
  flashTimer = window.setTimeout(() => {
    historyHotkeyFlash.value = null;
    flashTimer = null;
  }, 750);
}

// Bundle 32.4.15: Keyboard hint overlay state + helpers
const showHistoryHotkeyHint = ref(false);
let hintTimer: number | null = null;

function hideHint() {
  showHistoryHotkeyHint.value = false;
  if (hintTimer) window.clearTimeout(hintTimer);
  hintTimer = null;
}

function scheduleHint() {
  hideHint();
  showHistoryHotkeyHint.value = true;
  hintTimer = window.setTimeout(() => {
    showHistoryHotkeyHint.value = false;
    hintTimer = null;
  }, 6000);
}

// Bundle 32.4.15: Computed for checking if history exists
const hasHistory = computed(() => (store.historyStack?.length ?? 0) > 0);

// Bundle 32.4.15: Show hint when history becomes available
watch(hasHistory, (v) => {
  if (v) scheduleHint();
  else hideHint();
});

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

  // Bundle 32.4.15: Show hint on mount if history already exists
  if (hasHistory.value) scheduleHint();
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeyDown);

  // Bundle 32.4.15: Cleanup hint timer
  if (hintTimer) window.clearTimeout(hintTimer);
  hintTimer = null;
});

// Bundle 32.4.6: Detect if focus is in a typing context (input, textarea, contenteditable)
function isTypingTarget(el: EventTarget | null): boolean {
  const n = el as HTMLElement | null;
  if (!n) return false;

  const tag = (n.tagName || "").toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select") return true;
  if ((n as any).isContentEditable) return true;

  return false;
}

function onKeyDown(e: KeyboardEvent) {
  // Bundle 32.4.15: Suppress hint if user starts typing
  if (showHistoryHotkeyHint.value && isTypingTarget(e.target)) {
    hideHint();
  }

  // Bundle 32.4.6: History hotkeys 1–5 (don't hijack while typing)
  if (!isTypingTarget(e.target)) {
    const k = e.key;
    if (k === "1" || k === "2" || k === "3" || k === "4" || k === "5") {
      const idx = Number(k) - 1; // 0..4 (newest-first)
      const labels = store.getRecentHistoryLabels(5);
      if (idx < labels.length) {
        e.preventDefault();
        store.revertToRecentIndex(idx, 5);
        flashHistoryIdx(idx); // Bundle 32.4.8: trigger row highlight

        toast.push({
          level: "info",
          message: `Reverted: ${labels[idx]}`,
          detail: "Hotkey: 1–5 (1 = newest)",
          durationMs: 2200,
        });
      }
      return;
    }
  }

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

  // Bundle 32.4.0 + 32.4.3 + 32.4.11: Undo/Redo keyboard shortcuts with toast
  const cmd = e.ctrlKey || e.metaKey;
  const isUndo = cmd && !e.shiftKey && (e.key === "z" || e.key === "Z");
  const isRedo = cmd && e.shiftKey && (e.key === "z" || e.key === "Z");
  const redoAlt = cmd && !e.shiftKey && (e.key === "y" || e.key === "Y"); // Win-style

  if (isUndo) {
    e.preventDefault();
    undo("keyboard");
    return;
  }

  if (isRedo || redoAlt) {
    e.preventDefault();
    redo("keyboard");
    return;
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

/* Bundle 32.4.3.1: Redo button styles */
.redo-btn {
  margin-left: 4px;
}
.redo-btn:disabled {
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

/* Bundle 32.4.13: Subtle shake animation for disabled undo/redo */
@keyframes subtleShake {
  0% { transform: translateX(0); }
  25% { transform: translateX(-2px); }
  50% { transform: translateX(2px); }
  75% { transform: translateX(-2px); }
  100% { transform: translateX(0); }
}

.shake {
  animation: subtleShake 220ms ease-in-out;
}

/* Bundle 32.4.15: Keyboard hint overlay styles */
.historyWrap {
  position: relative;
}

.hotkeyHint {
  position: absolute;
  top: 10px;
  right: 10px;
  max-width: 220px;
  border: 1px solid #ececec;
  background: #ffffff;
  border-radius: 12px;
  padding: 10px 12px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
  z-index: 5;
}

.hotkeyHintTitle {
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 4px;
}

.hotkeyHintBody {
  font-size: 12px;
  color: #444;
  line-height: 1.25;
}

.hotkeyHintClose {
  position: absolute;
  top: 6px;
  right: 6px;
  border: 0;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  color: #777;
  padding: 4px;
}
</style>
