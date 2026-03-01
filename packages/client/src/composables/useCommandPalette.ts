/**
 * Command Palette composable for global keyboard navigation.
 *
 * Provides Ctrl+K (Cmd+K on Mac) command palette for quick navigation
 * and actions across the application.
 */

import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";

export interface Command {
  id: string;
  label: string;
  category: "navigation" | "tools" | "actions" | "recent";
  keywords?: string[];
  icon?: string;
  shortcut?: string;
  action: () => void | Promise<void>;
}

const isOpen = ref(false);
const query = ref("");
const selectedIndex = ref(0);
const recentCommands = ref<string[]>([]);

// Load recent commands from localStorage
const RECENT_KEY = "commandPalette.recent.v1";
const MAX_RECENT = 5;

function loadRecent(): string[] {
  try {
    const stored = localStorage.getItem(RECENT_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveRecent(ids: string[]): void {
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(ids.slice(0, MAX_RECENT)));
  } catch {
    // Ignore localStorage errors
  }
}

export function useCommandPalette() {
  const router = useRouter();

  // Initialize recent on first use
  if (recentCommands.value.length === 0) {
    recentCommands.value = loadRecent();
  }

  // Define available commands
  const commands = computed<Command[]>(() => {
    const nav: Command[] = [
      {
        id: "nav-home",
        label: "Home",
        category: "navigation",
        keywords: ["rosette", "pipeline", "main"],
        icon: "🏠",
        action: () => router.push("/"),
      },
      {
        id: "nav-quick-cut",
        label: "Quick Cut",
        category: "navigation",
        keywords: ["dxf", "gcode", "cnc", "fast"],
        icon: "⚡",
        action: () => router.push("/quick-cut"),
      },
      {
        id: "nav-calculators",
        label: "Calculators",
        category: "navigation",
        keywords: ["math", "fret", "scale", "bridge"],
        icon: "🧮",
        action: () => router.push("/calculators"),
      },
      {
        id: "nav-art-studio",
        label: "Art Studio",
        category: "navigation",
        keywords: ["design", "rosette", "inlay", "art"],
        icon: "🎨",
        action: () => router.push("/art-studio"),
      },
      {
        id: "nav-rmos",
        label: "RMOS Dashboard",
        category: "navigation",
        keywords: ["manufacturing", "runs", "operations"],
        icon: "📊",
        action: () => router.push("/rmos"),
      },
      {
        id: "nav-live-monitor",
        label: "Live Monitor",
        category: "navigation",
        keywords: ["realtime", "websocket", "status"],
        icon: "📡",
        action: () => router.push("/rmos/live-monitor"),
      },
      {
        id: "nav-rosette-designer",
        label: "Rosette Designer",
        category: "navigation",
        keywords: ["pattern", "rings", "soundhole"],
        icon: "🔘",
        action: () => router.push("/rmos/rosette-designer"),
      },
      {
        id: "nav-cam-settings",
        label: "CAM Settings",
        category: "navigation",
        keywords: ["config", "machine", "tools"],
        icon: "⚙️",
        action: () => router.push("/settings/cam"),
      },
    ];

    const labs: Command[] = [
      {
        id: "lab-bridge",
        label: "Bridge Lab",
        category: "tools",
        keywords: ["bridge", "saddle", "compensation"],
        icon: "🌉",
        action: () => router.push("/lab/bridge"),
      },
      {
        id: "lab-adaptive",
        label: "Adaptive Lab",
        category: "tools",
        keywords: ["adaptive", "clearing", "pocket"],
        icon: "🔄",
        action: () => router.push("/lab/adaptive"),
      },
      {
        id: "lab-pipeline",
        label: "Pipeline Lab",
        category: "tools",
        keywords: ["workflow", "pipeline", "steps"],
        icon: "🔧",
        action: () => router.push("/lab/pipeline"),
      },
      {
        id: "lab-saw-slice",
        label: "Saw Lab: Slice",
        category: "tools",
        keywords: ["saw", "cut", "slice"],
        icon: "🪚",
        action: () => router.push("/lab/saw/slice"),
      },
      {
        id: "lab-saw-batch",
        label: "Saw Lab: Batch",
        category: "tools",
        keywords: ["saw", "batch", "multiple"],
        icon: "📦",
        action: () => router.push("/lab/saw/batch"),
      },
      {
        id: "lab-risk-timeline",
        label: "Risk Timeline",
        category: "tools",
        keywords: ["risk", "history", "timeline"],
        icon: "📈",
        action: () => router.push("/lab/risk-timeline"),
      },
    ];

    const tools: Command[] = [
      {
        id: "tool-acoustics-library",
        label: "Acoustics Library",
        category: "tools",
        keywords: ["audio", "analyzer", "viewer", "pack"],
        icon: "🎵",
        action: () => router.push("/tools/audio-analyzer/library"),
      },
      {
        id: "tool-acoustics-viewer",
        label: "Acoustics Viewer",
        category: "tools",
        keywords: ["spectrum", "waveform", "audio"],
        icon: "📊",
        action: () => router.push("/tools/audio-analyzer"),
      },
      {
        id: "tool-dxf-gcode",
        label: "DXF to G-code",
        category: "tools",
        keywords: ["convert", "cnc", "machining"],
        icon: "📐",
        action: () => router.push("/tools/dxf-to-gcode"),
      },
    ];

    return [...nav, ...labs, ...tools];
  });

  // Fuzzy search filter
  const filteredCommands = computed(() => {
    const q = query.value.toLowerCase().trim();

    if (!q) {
      // Show recent first, then all commands
      const recent = recentCommands.value
        .map((id) => commands.value.find((c) => c.id === id))
        .filter((c): c is Command => c !== undefined)
        .map((c) => ({ ...c, category: "recent" as const }));

      const others = commands.value.filter(
        (c) => !recentCommands.value.includes(c.id)
      );

      return [...recent, ...others];
    }

    return commands.value.filter((cmd) => {
      const searchText = [cmd.label, ...(cmd.keywords || [])].join(" ").toLowerCase();
      return q.split(" ").every((word) => searchText.includes(word));
    });
  });

  // Group by category
  const groupedCommands = computed(() => {
    const groups: Record<string, Command[]> = {};
    for (const cmd of filteredCommands.value) {
      if (!groups[cmd.category]) {
        groups[cmd.category] = [];
      }
      groups[cmd.category].push(cmd);
    }
    return groups;
  });

  // Actions
  function open() {
    isOpen.value = true;
    query.value = "";
    selectedIndex.value = 0;
  }

  function close() {
    isOpen.value = false;
    query.value = "";
  }

  function toggle() {
    if (isOpen.value) {
      close();
    } else {
      open();
    }
  }

  function executeCommand(cmd: Command) {
    // Track as recent
    const newRecent = [
      cmd.id,
      ...recentCommands.value.filter((id) => id !== cmd.id),
    ].slice(0, MAX_RECENT);
    recentCommands.value = newRecent;
    saveRecent(newRecent);

    close();
    cmd.action();
  }

  function selectNext() {
    const max = filteredCommands.value.length - 1;
    selectedIndex.value = Math.min(selectedIndex.value + 1, max);
  }

  function selectPrev() {
    selectedIndex.value = Math.max(selectedIndex.value - 1, 0);
  }

  function executeSelected() {
    const cmd = filteredCommands.value[selectedIndex.value];
    if (cmd) {
      executeCommand(cmd);
    }
  }

  // Global keyboard listener
  function handleKeydown(e: KeyboardEvent) {
    // Ctrl+K or Cmd+K to open
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      toggle();
      return;
    }

    if (!isOpen.value) return;

    // Escape to close
    if (e.key === "Escape") {
      e.preventDefault();
      close();
      return;
    }

    // Arrow navigation
    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectNext();
      return;
    }

    if (e.key === "ArrowUp") {
      e.preventDefault();
      selectPrev();
      return;
    }

    // Enter to execute
    if (e.key === "Enter") {
      e.preventDefault();
      executeSelected();
      return;
    }
  }

  // Lifecycle
  onMounted(() => {
    window.addEventListener("keydown", handleKeydown);
  });

  onUnmounted(() => {
    window.removeEventListener("keydown", handleKeydown);
  });

  return {
    // State
    isOpen,
    query,
    selectedIndex,
    filteredCommands,
    groupedCommands,

    // Actions
    open,
    close,
    toggle,
    executeCommand,
    selectNext,
    selectPrev,
    executeSelected,
  };
}
