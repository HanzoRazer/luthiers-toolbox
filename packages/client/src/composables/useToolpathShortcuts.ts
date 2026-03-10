/**
 * useToolpathShortcuts — P5 Keyboard Shortcuts for Toolpath Player
 *
 * Provides keyboard shortcuts for common toolpath player actions.
 *
 * Shortcuts:
 * - Space: Play/Pause
 * - Left Arrow: Step backward
 * - Right Arrow: Step forward
 * - Home: Jump to start
 * - End: Jump to end
 * - +/=: Speed up
 * - -: Slow down
 * - 1-5: Set speed (0.5x, 1x, 2x, 5x, 10x)
 * - R: Reset view (3D only)
 * - H: Toggle heatmap
 * - M: Toggle measure mode
 * - G: Toggle G-code panel
 * - Escape: Cancel measure / clear selection
 * - ?: Show shortcuts help
 */

import { onMounted, onUnmounted, ref } from "vue";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ShortcutAction {
  /** Key or key combination */
  key: string;
  /** Description for help overlay */
  description: string;
  /** Category for grouping */
  category: "playback" | "view" | "tools" | "navigation";
  /** Handler function */
  handler: () => void;
}

export interface UseToolpathShortcutsOptions {
  /** Callback to toggle heatmap */
  onToggleHeatmap?: () => void;
  /** Callback to toggle G-code panel */
  onToggleGcode?: () => void;
  /** Callback to reset 3D view */
  onResetView?: () => void;
  /** Callback to set top view */
  onSetViewTop?: () => void;
  /** Callback to set front view */
  onSetViewFront?: () => void;
  /** Callback to set side view */
  onSetViewSide?: () => void;
  /** Callback to toggle 2D/3D view */
  onToggleViewMode?: () => void;
  /** Whether shortcuts are enabled */
  enabled?: boolean;
}

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export function useToolpathShortcuts(options: UseToolpathShortcutsOptions = {}) {
  const store = useToolpathPlayerStore();
  const showHelp = ref(false);

  // Speed levels for number keys
  const speeds = [0.5, 1, 2, 5, 10];

  // Build shortcuts list
  const shortcuts: ShortcutAction[] = [
    // Playback
    {
      key: "Space",
      description: "Play / Pause",
      category: "playback",
      handler: () => {
        if (store.playState === "playing") {
          store.pause();
        } else {
          store.play();
        }
      },
    },
    {
      key: "←",
      description: "Step backward",
      category: "playback",
      handler: () => store.stepBackward(),
    },
    {
      key: "→",
      description: "Step forward",
      category: "playback",
      handler: () => store.stepForward(),
    },
    {
      key: "Home",
      description: "Jump to start",
      category: "playback",
      handler: () => store.seek(0),
    },
    {
      key: "End",
      description: "Jump to end",
      category: "playback",
      handler: () => store.seek(1),
    },
    {
      key: "+",
      description: "Speed up",
      category: "playback",
      handler: () => {
        const idx = speeds.indexOf(store.speed);
        if (idx < speeds.length - 1) {
          store.setSpeed(speeds[idx + 1]);
        }
      },
    },
    {
      key: "-",
      description: "Slow down",
      category: "playback",
      handler: () => {
        const idx = speeds.indexOf(store.speed);
        if (idx > 0) {
          store.setSpeed(speeds[idx - 1]);
        }
      },
    },
    {
      key: "1",
      description: "Speed 0.5×",
      category: "playback",
      handler: () => store.setSpeed(0.5),
    },
    {
      key: "2",
      description: "Speed 1×",
      category: "playback",
      handler: () => store.setSpeed(1),
    },
    {
      key: "3",
      description: "Speed 2×",
      category: "playback",
      handler: () => store.setSpeed(2),
    },
    {
      key: "4",
      description: "Speed 5×",
      category: "playback",
      handler: () => store.setSpeed(5),
    },
    {
      key: "5",
      description: "Speed 10×",
      category: "playback",
      handler: () => store.setSpeed(10),
    },

    // View
    {
      key: "H",
      description: "Toggle heatmap",
      category: "view",
      handler: () => options.onToggleHeatmap?.(),
    },
    {
      key: "G",
      description: "Toggle G-code panel",
      category: "view",
      handler: () => options.onToggleGcode?.(),
    },
    {
      key: "V",
      description: "Toggle 2D/3D view",
      category: "view",
      handler: () => options.onToggleViewMode?.(),
    },
    {
      key: "R",
      description: "Reset view",
      category: "view",
      handler: () => options.onResetView?.(),
    },
    {
      key: "T",
      description: "Top view (3D)",
      category: "view",
      handler: () => options.onSetViewTop?.(),
    },
    {
      key: "F",
      description: "Front view (3D)",
      category: "view",
      handler: () => options.onSetViewFront?.(),
    },
    {
      key: "S",
      description: "Side view (3D)",
      category: "view",
      handler: () => options.onSetViewSide?.(),
    },

    // Tools
    {
      key: "M",
      description: "Toggle measure mode",
      category: "tools",
      handler: () => store.toggleMeasureMode(),
    },
    {
      key: "Escape",
      description: "Cancel / Clear selection",
      category: "tools",
      handler: () => {
        if (store.measureMode) {
          store.cancelMeasurement();
          store.toggleMeasureMode();
        } else if (store.selectedSegmentIndex !== null) {
          store.clearSelection();
        }
      },
    },
    {
      key: "Delete",
      description: "Clear measurements",
      category: "tools",
      handler: () => store.clearMeasurements(),
    },

    // Navigation
    {
      key: "J",
      description: "Jump to selected",
      category: "navigation",
      handler: () => store.jumpToSelected(),
    },
    {
      key: "?",
      description: "Show/hide shortcuts help",
      category: "navigation",
      handler: () => {
        showHelp.value = !showHelp.value;
      },
    },
  ];

  // Key handler
  function handleKeyDown(e: KeyboardEvent): void {
    // Skip if disabled
    if (options.enabled === false) return;

    // Skip if typing in an input
    const target = e.target as HTMLElement;
    if (
      target.tagName === "INPUT" ||
      target.tagName === "TEXTAREA" ||
      target.tagName === "SELECT" ||
      target.isContentEditable
    ) {
      return;
    }

    // Skip if no segments loaded (except help)
    if (store.segments.length === 0 && e.key !== "?") {
      return;
    }

    // Match key
    let matched = false;

    switch (e.key) {
      case " ":
        shortcuts.find((s) => s.key === "Space")?.handler();
        matched = true;
        break;
      case "ArrowLeft":
        shortcuts.find((s) => s.key === "←")?.handler();
        matched = true;
        break;
      case "ArrowRight":
        shortcuts.find((s) => s.key === "→")?.handler();
        matched = true;
        break;
      case "Home":
        shortcuts.find((s) => s.key === "Home")?.handler();
        matched = true;
        break;
      case "End":
        shortcuts.find((s) => s.key === "End")?.handler();
        matched = true;
        break;
      case "=":
      case "+":
        shortcuts.find((s) => s.key === "+")?.handler();
        matched = true;
        break;
      case "-":
        shortcuts.find((s) => s.key === "-")?.handler();
        matched = true;
        break;
      case "1":
      case "2":
      case "3":
      case "4":
      case "5":
        shortcuts.find((s) => s.key === e.key)?.handler();
        matched = true;
        break;
      case "h":
      case "H":
        shortcuts.find((s) => s.key === "H")?.handler();
        matched = true;
        break;
      case "g":
      case "G":
        shortcuts.find((s) => s.key === "G")?.handler();
        matched = true;
        break;
      case "v":
      case "V":
        shortcuts.find((s) => s.key === "V")?.handler();
        matched = true;
        break;
      case "r":
      case "R":
        shortcuts.find((s) => s.key === "R")?.handler();
        matched = true;
        break;
      case "t":
      case "T":
        shortcuts.find((s) => s.key === "T")?.handler();
        matched = true;
        break;
      case "f":
      case "F":
        shortcuts.find((s) => s.key === "F")?.handler();
        matched = true;
        break;
      case "s":
      case "S":
        shortcuts.find((s) => s.key === "S")?.handler();
        matched = true;
        break;
      case "m":
      case "M":
        shortcuts.find((s) => s.key === "M")?.handler();
        matched = true;
        break;
      case "j":
      case "J":
        shortcuts.find((s) => s.key === "J")?.handler();
        matched = true;
        break;
      case "Escape":
        shortcuts.find((s) => s.key === "Escape")?.handler();
        matched = true;
        break;
      case "Delete":
      case "Backspace":
        shortcuts.find((s) => s.key === "Delete")?.handler();
        matched = true;
        break;
      case "?":
        shortcuts.find((s) => s.key === "?")?.handler();
        matched = true;
        break;
    }

    if (matched) {
      e.preventDefault();
      e.stopPropagation();
    }
  }

  // Lifecycle
  onMounted(() => {
    window.addEventListener("keydown", handleKeyDown);
  });

  onUnmounted(() => {
    window.removeEventListener("keydown", handleKeyDown);
  });

  return {
    shortcuts,
    showHelp,
    hideHelp: () => {
      showHelp.value = false;
    },
  };
}

export default useToolpathShortcuts;
