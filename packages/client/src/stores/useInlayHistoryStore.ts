/**
 * Inlay History Store — Snapshot-based Undo/Redo
 *
 * Pushes a snapshot of inlay pattern params on each generate.
 * Pop on undo, re-push on redo. Snapshot stack capped at MAX_HISTORY.
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface InlaySnapshot {
  shape: string;
  params: Record<string, unknown>;
  materials: string[];
  bgMaterial: string;
  includeOffsets: boolean;
  maleOffsetMm: number;
  pocketOffsetMm: number;
  timestamp: number;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_HISTORY = 50;

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useInlayHistoryStore = defineStore("inlayHistory", () => {
  // ── State ────────────────────────────────────────────────────────────────
  const undoStack = ref<InlaySnapshot[]>([]);
  const redoStack = ref<InlaySnapshot[]>([]);

  // ── Computed ─────────────────────────────────────────────────────────────
  const canUndo = computed(() => undoStack.value.length > 0);
  const canRedo = computed(() => redoStack.value.length > 0);
  const undoCount = computed(() => undoStack.value.length);
  const redoCount = computed(() => redoStack.value.length);

  // ── Actions ──────────────────────────────────────────────────────────────

  /**
   * Push the current param state onto the undo stack.
   * Call this *before* each generate so the previous state is recoverable.
   */
  function pushState(snapshot: InlaySnapshot): void {
    undoStack.value.push(snapshot);
    if (undoStack.value.length > MAX_HISTORY) {
      undoStack.value.shift();
    }
    // New action invalidates the redo branch
    redoStack.value = [];
  }

  /**
   * Pop the last snapshot from the undo stack and return it.
   * The caller must pass in the *current* state so it goes onto redo.
   */
  function undo(current: InlaySnapshot): InlaySnapshot | null {
    if (undoStack.value.length === 0) return null;
    redoStack.value.push(current);
    return undoStack.value.pop()!;
  }

  /**
   * Pop from redo and return it.
   * The caller must pass in the *current* state so it goes back onto undo.
   */
  function redo(current: InlaySnapshot): InlaySnapshot | null {
    if (redoStack.value.length === 0) return null;
    undoStack.value.push(current);
    return redoStack.value.pop()!;
  }

  /** Clear all history. */
  function clear(): void {
    undoStack.value = [];
    redoStack.value = [];
  }

  return {
    undoStack,
    redoStack,
    canUndo,
    canRedo,
    undoCount,
    redoCount,
    pushState,
    undo,
    redo,
    clear,
  };
});
