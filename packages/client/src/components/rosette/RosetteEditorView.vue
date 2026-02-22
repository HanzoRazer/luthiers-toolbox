<template>
  <div :class="styles.wrap">
    <PatternLibraryPanel />
    <div :class="styles.mid">
      <div
        v-if="store.problematicRingIndices.length > 0"
        :class="styles.toolbar"
      >
        <button
          :class="styles.jumpBtn"
          type="button"
          title="Jump to previous problematic ring ([)"
          @click="jumpPrev"
        >
          Prev
        </button>
        <button
          :class="styles.jumpBtn"
          type="button"
          title="Jump to next problematic ring (])"
          @click="jumpNext"
        >
          Next
        </button>
        <span :class="styles.problemCount">{{ store.problematicRingIndices.length }} problems</span>
        <button
          :class="styles.jumpBtn"
          type="button"
          :title="store.jumpSeverity === 'RED_ONLY'
            ? 'Jump filter: RED only (click to include YELLOW)'
            : 'Jump filter: RED + YELLOW (click for RED only)'"
          @click="store.toggleJumpSeverity()"
        >
          {{ store.jumpSeverity === "RED_ONLY" ? "RED only" : "RED+YELLOW" }}
        </button>
        <div
          v-if="store.totalRingCount > 0"
          :class="[styles.jumpHud, { [styles.jumpHudPulse]: hudPulse }]"
        >
          <span :class="styles.pill">
            {{ store.jumpSeverity === "RED_ONLY" ? "Filter: RED only" : "Filter: RED+YELLOW" }}
          </span>
          <span :class="styles.pill">
            RED rings: {{ store.redRingCount }} / {{ store.totalRingCount }}
          </span>
          <span
            v-if="store.jumpRingPosition.total > 0"
            :class="styles.pill"
          >
            Focus: {{ store.jumpRingPosition.pos || "—" }} / {{ store.jumpRingPosition.total }}
          </span>
          <!-- Bundle 32.3.8: HUD help tooltip -->
          <span
            :class="styles.hudHelp"
            tabindex="0"
            aria-label="Jump hotkeys help"
          >
            ?
            <span
              :class="styles.hudTooltip"
              role="tooltip"
            >
              <div :class="styles.ttTitle">Jump hotkeys</div>
              <div :class="styles.ttRow"><kbd :class="styles.kbd">[</kbd> Prev problem</div>
              <div :class="styles.ttRow"><kbd :class="styles.kbd">]</kbd> Next problem</div>
              <div :class="styles.ttRow"><kbd :class="styles.kbd">w</kbd> Jump to worst</div>
              <div :class="styles.ttRow"><kbd :class="styles.kbd">Shift</kbd> + <kbd :class="styles.kbd">R</kbd> Toggle filter</div>
            </span>
          </span>
        </div>
        <!-- Bundle 32.4.0: Undo button -->
        <button
          ref="undoBtnRef"
          :class="[styles.jumpBtn, styles.undoBtn, { [styles.shake]: shakeUndo }]"
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
          :class="[styles.jumpBtn, styles.redoBtn, { [styles.shake]: shakeRedo }]"
          type="button"
          :title="redoTitle"
          :disabled="store.redoStack.length === 0"
          @click="() => redo('clicked')"
        >
          Redo
        </button>
        <!-- Bundle 32.4.18: Reset tips button -->
        <button
          :class="[styles.jumpBtn, styles.resetTipsBtn]"
          type="button"
          title="Reset onboarding tips (clears cooldown)"
          @click="resetTips"
        >
          Reset tips
        </button>
      </div>

      <!-- Bundle 32.4.0: Ring Nudge Section -->
      <div
        v-if="store.currentParams?.ring_params?.length"
        :class="styles.ringNudgeSection"
      >
        <div :class="styles.nudgeTitle">
          Ring Widths
        </div>
        <div
          v-for="(ring, idx) in store.currentParams.ring_params"
          :key="idx"
          :class="[styles.ringRow, { [styles.ringRowFocused]: store.focusedRingIndex === idx }]"
          :data-ring-index="idx"
        >
          <span :class="styles.ringLabel">Ring {{ idx + 1 }}</span>
          <span :class="styles.ringWidth">{{ Number(ring.width_mm || 0).toFixed(2) }} mm</span>
          <div :class="styles.ringActions">
            <button
              :class="styles.mini"
              type="button"
              title="Shrink width by 0.10 mm"
              :disabled="store.isRedBlocked"
              @click="store.nudgeRingWidth(idx, -0.1)"
            >
              −0.10
            </button>
            <button
              :class="styles.mini"
              type="button"
              title="Grow width by 0.10 mm"
              :disabled="store.isRedBlocked"
              @click="store.nudgeRingWidth(idx, 0.1)"
            >
              +0.10
            </button>
            <button
              :class="[styles.mini, styles.miniDist]"
              type="button"
              title="Shrink width, distribute to neighbors"
              :disabled="store.isRedBlocked"
              @click="store.nudgeRingWidthDistribute(idx, -0.1)"
            >
              −0.10↔
            </button>
            <button
              :class="[styles.mini, styles.miniDist]"
              type="button"
              title="Grow width, distribute to neighbors"
              :disabled="store.isRedBlocked"
              @click="store.nudgeRingWidthDistribute(idx, 0.1)"
            >
              +0.10↔
            </button>
          </div>
        </div>
      </div>

      <!-- Bundle 32.4.2 + 32.4.15: History mini-stack panel with keyboard hint overlay -->
      <div :class="styles.historyWrap">
        <HistoryStackPanel
          :highlight-idx-from-top="historyHotkeyFlash"
          @hover-hint="showHintFromHover"
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
        <div
          v-if="showHistoryHotkeyHint && hasHistory"
          :class="styles.hotkeyHint"
          role="note"
        >
          <div :class="styles.hotkeyHintTitle">
            Keyboard tip
          </div>
          <div :class="styles.hotkeyHintBody">
            Try <b>1–5</b> to revert history (1 = newest)
          </div>
          <button
            :class="styles.hotkeyHintClose"
            type="button"
            aria-label="Dismiss"
            @click="() => hideHint(true)"
          >
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
import styles from "./RosetteEditorView.module.css";

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

// Bundle 32.4.17: localStorage cooldown to prevent nagging
const HINT_COOLDOWN_KEY = "artstudio.historyHotkeyHintDismissedAt";
const HINT_COOLDOWN_MIN = 10;

function getDismissedAt(): number {
  try {
    return Number(localStorage.getItem(HINT_COOLDOWN_KEY) ?? 0) || 0;
  } catch {
    return 0;
  }
}

function setDismissedNow() {
  try {
    localStorage.setItem(HINT_COOLDOWN_KEY, String(Date.now()));
  } catch {
    // ignore
  }
}

function cooldownActive(): boolean {
  const dismissedAt = getDismissedAt();
  if (!dismissedAt) return false;
  const ms = HINT_COOLDOWN_MIN * 60_000;
  return Date.now() - dismissedAt < ms;
}

// Bundle 32.4.18: Reset tips (clears cooldown key)
function resetTips() {
  try {
    // History hotkey hint cooldown
    localStorage.removeItem("artstudio.historyHotkeyHintDismissedAt");

    // (future-proof) if you add more tip keys later, clear them here too
    // localStorage.removeItem("artstudio.someOtherTipKey");

    toast.push({
      level: "success",
      message: "Tips reset",
      detail: "Onboarding hints will reappear",
      durationMs: 2500,
    });
  } catch {
    // ignore localStorage errors
  }
}

function hideHint(userDismissed = true) {
  showHistoryHotkeyHint.value = false;
  if (hintTimer) window.clearTimeout(hintTimer);
  hintTimer = null;

  if (userDismissed) setDismissedNow();
}

function scheduleHint() {
  if (cooldownActive()) return;

  hideHint(false); // reset timer/visibility without marking dismissal
  showHistoryHotkeyHint.value = true;

  hintTimer = window.setTimeout(() => {
    showHistoryHotkeyHint.value = false;
    hintTimer = null;
  }, 6000);
}

// Bundle 32.4.15: Computed for checking if history exists
const hasHistory = computed(() => (store.historyStack?.length ?? 0) > 0);

// Bundle 32.4.16: Show hint from hover (reuses existing scheduleHint)
function showHintFromHover() {
  if (!hasHistory.value) return;
  if (cooldownActive()) return;
  scheduleHint(); // uses the existing 6s timer + safe reset
}

// Bundle 32.4.15: Show hint when history becomes available
watch(hasHistory, (v) => {
  if (v) scheduleHint();
  else hideHint(false); // auto-hide, not user dismissal
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
    hideHint(false); // typing is not a dismissal
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
