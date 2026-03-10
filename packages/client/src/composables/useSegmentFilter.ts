/**
 * useSegmentFilter — P5 Segment Filtering & Highlighting
 *
 * Provides filtering and highlighting for toolpath segments:
 * - Filter by move type (rapid, linear, arc)
 * - Filter by Z depth range
 * - Filter by feed rate range
 * - Highlight mode (dim non-matching vs hide)
 * - Quick presets for common filters
 */

import { ref, computed, watch } from "vue";
import type { Ref } from "vue";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MoveSegment {
  type: "rapid" | "linear" | "arc_cw" | "arc_ccw";
  from_pos: [number, number, number];
  to_pos: [number, number, number];
  feed: number;
  duration_ms: number;
  line_number?: number;
  line_text?: string;
}

export interface SegmentFilterState {
  /** Show rapid moves */
  showRapid: boolean;
  /** Show linear cuts */
  showLinear: boolean;
  /** Show arc CW moves */
  showArcCW: boolean;
  /** Show arc CCW moves */
  showArcCCW: boolean;
  /** Z depth filter enabled */
  zFilterEnabled: boolean;
  /** Min Z depth (most negative = deepest) */
  zMin: number;
  /** Max Z depth */
  zMax: number;
  /** Feed rate filter enabled */
  feedFilterEnabled: boolean;
  /** Min feed rate */
  feedMin: number;
  /** Max feed rate */
  feedMax: number;
  /** Display mode for non-matching segments */
  displayMode: "hide" | "dim";
  /** Dim opacity (0-1) */
  dimOpacity: number;
}

export interface FilterPreset {
  id: string;
  name: string;
  icon: string;
  description: string;
  apply: (state: SegmentFilterState) => Partial<SegmentFilterState>;
}

export interface SegmentVisibility {
  /** Segment index */
  index: number;
  /** Whether segment passes filter */
  visible: boolean;
  /** Opacity to render (1 = full, dimOpacity = dimmed, 0 = hidden) */
  opacity: number;
}

// ---------------------------------------------------------------------------
// Default State
// ---------------------------------------------------------------------------

function createDefaultState(): SegmentFilterState {
  return {
    showRapid: true,
    showLinear: true,
    showArcCW: true,
    showArcCCW: true,
    zFilterEnabled: false,
    zMin: -100,
    zMax: 100,
    feedFilterEnabled: false,
    feedMin: 0,
    feedMax: 10000,
    displayMode: "dim",
    dimOpacity: 0.15,
  };
}

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------

export const FILTER_PRESETS: FilterPreset[] = [
  {
    id: "all",
    name: "Show All",
    icon: "🔄",
    description: "Reset to show all segments",
    apply: () => createDefaultState(),
  },
  {
    id: "cuts-only",
    name: "Cuts Only",
    icon: "✂️",
    description: "Show only cutting moves (hide rapids)",
    apply: () => ({
      showRapid: false,
      showLinear: true,
      showArcCW: true,
      showArcCCW: true,
    }),
  },
  {
    id: "rapids-only",
    name: "Rapids Only",
    icon: "⚡",
    description: "Show only rapid moves",
    apply: () => ({
      showRapid: true,
      showLinear: false,
      showArcCW: false,
      showArcCCW: false,
    }),
  },
  {
    id: "arcs-only",
    name: "Arcs Only",
    icon: "🌀",
    description: "Show only arc moves (G2/G3)",
    apply: () => ({
      showRapid: false,
      showLinear: false,
      showArcCW: true,
      showArcCCW: true,
    }),
  },
  {
    id: "linear-only",
    name: "Linear Only",
    icon: "📏",
    description: "Show only linear cuts (G1)",
    apply: () => ({
      showRapid: false,
      showLinear: true,
      showArcCW: false,
      showArcCCW: false,
    }),
  },
  {
    id: "below-zero",
    name: "Below Z0",
    icon: "⬇️",
    description: "Show only moves below Z=0 (actual cutting)",
    apply: () => ({
      zFilterEnabled: true,
      zMin: -1000,
      zMax: 0,
    }),
  },
  {
    id: "finishing",
    name: "Finishing Passes",
    icon: "✨",
    description: "Show shallow cuts (likely finishing)",
    apply: () => ({
      zFilterEnabled: true,
      zMin: -2,
      zMax: 0,
      showRapid: false,
    }),
  },
  {
    id: "roughing",
    name: "Roughing Passes",
    icon: "🔨",
    description: "Show deep cuts (likely roughing)",
    apply: () => ({
      zFilterEnabled: true,
      zMin: -1000,
      zMax: -2,
      showRapid: false,
    }),
  },
];

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export function useSegmentFilter(segments: Ref<MoveSegment[]>) {
  // State
  const filterState = ref<SegmentFilterState>(createDefaultState());
  const activePresetId = ref<string | null>("all");

  // Bounds computed from segments
  const segmentBounds = computed(() => {
    const segs = segments.value;
    if (segs.length === 0) {
      return { zMin: -100, zMax: 100, feedMin: 0, feedMax: 10000 };
    }

    let zMin = Infinity;
    let zMax = -Infinity;
    let feedMin = Infinity;
    let feedMax = -Infinity;

    for (const seg of segs) {
      const z1 = seg.from_pos[2];
      const z2 = seg.to_pos[2];
      zMin = Math.min(zMin, z1, z2);
      zMax = Math.max(zMax, z1, z2);

      if (seg.feed > 0) {
        feedMin = Math.min(feedMin, seg.feed);
        feedMax = Math.max(feedMax, seg.feed);
      }
    }

    return {
      zMin: isFinite(zMin) ? zMin : -100,
      zMax: isFinite(zMax) ? zMax : 100,
      feedMin: isFinite(feedMin) ? feedMin : 0,
      feedMax: isFinite(feedMax) ? feedMax : 10000,
    };
  });

  // Initialize bounds when segments change
  watch(
    () => segments.value.length,
    () => {
      const bounds = segmentBounds.value;
      filterState.value.zMin = bounds.zMin;
      filterState.value.zMax = bounds.zMax;
      filterState.value.feedMin = bounds.feedMin;
      filterState.value.feedMax = bounds.feedMax;
    },
    { immediate: true }
  );

  // Check if a segment passes the filter
  function passesFilter(seg: MoveSegment): boolean {
    const state = filterState.value;

    // Type filter
    switch (seg.type) {
      case "rapid":
        if (!state.showRapid) return false;
        break;
      case "linear":
        if (!state.showLinear) return false;
        break;
      case "arc_cw":
        if (!state.showArcCW) return false;
        break;
      case "arc_ccw":
        if (!state.showArcCCW) return false;
        break;
    }

    // Z depth filter
    if (state.zFilterEnabled) {
      const z1 = seg.from_pos[2];
      const z2 = seg.to_pos[2];
      const segZMin = Math.min(z1, z2);
      const segZMax = Math.max(z1, z2);

      // Segment must overlap with filter range
      if (segZMax < state.zMin || segZMin > state.zMax) {
        return false;
      }
    }

    // Feed rate filter (only for non-rapids)
    if (state.feedFilterEnabled && seg.type !== "rapid") {
      if (seg.feed < state.feedMin || seg.feed > state.feedMax) {
        return false;
      }
    }

    return true;
  }

  // Compute visibility for all segments
  const segmentVisibility = computed<SegmentVisibility[]>(() => {
    const state = filterState.value;
    return segments.value.map((seg, index) => {
      const visible = passesFilter(seg);
      let opacity = 1;

      if (!visible) {
        opacity = state.displayMode === "hide" ? 0 : state.dimOpacity;
      }

      return { index, visible, opacity };
    });
  });

  // Filtered segments (for hide mode)
  const filteredSegments = computed<MoveSegment[]>(() => {
    if (filterState.value.displayMode === "dim") {
      return segments.value; // Return all, canvas will handle opacity
    }
    return segments.value.filter((_, i) => segmentVisibility.value[i].visible);
  });

  // Statistics
  const filterStats = computed(() => {
    const vis = segmentVisibility.value;
    const visible = vis.filter((v) => v.visible).length;
    const hidden = vis.length - visible;
    const percent = vis.length > 0 ? (visible / vis.length) * 100 : 100;

    return {
      total: vis.length,
      visible,
      hidden,
      percent,
    };
  });

  // Check if any filter is active
  const hasActiveFilter = computed(() => {
    const state = filterState.value;
    return (
      !state.showRapid ||
      !state.showLinear ||
      !state.showArcCW ||
      !state.showArcCCW ||
      state.zFilterEnabled ||
      state.feedFilterEnabled
    );
  });

  // Actions
  function applyPreset(presetId: string): void {
    const preset = FILTER_PRESETS.find((p) => p.id === presetId);
    if (preset) {
      const changes = preset.apply(filterState.value);
      Object.assign(filterState.value, changes);
      activePresetId.value = presetId;
    }
  }

  function resetFilter(): void {
    filterState.value = createDefaultState();
    const bounds = segmentBounds.value;
    filterState.value.zMin = bounds.zMin;
    filterState.value.zMax = bounds.zMax;
    filterState.value.feedMin = bounds.feedMin;
    filterState.value.feedMax = bounds.feedMax;
    activePresetId.value = "all";
  }

  function setTypeFilter(type: "rapid" | "linear" | "arcCW" | "arcCCW", enabled: boolean): void {
    switch (type) {
      case "rapid":
        filterState.value.showRapid = enabled;
        break;
      case "linear":
        filterState.value.showLinear = enabled;
        break;
      case "arcCW":
        filterState.value.showArcCW = enabled;
        break;
      case "arcCCW":
        filterState.value.showArcCCW = enabled;
        break;
    }
    activePresetId.value = null;
  }

  function setZFilter(enabled: boolean, min?: number, max?: number): void {
    filterState.value.zFilterEnabled = enabled;
    if (min !== undefined) filterState.value.zMin = min;
    if (max !== undefined) filterState.value.zMax = max;
    activePresetId.value = null;
  }

  function setFeedFilter(enabled: boolean, min?: number, max?: number): void {
    filterState.value.feedFilterEnabled = enabled;
    if (min !== undefined) filterState.value.feedMin = min;
    if (max !== undefined) filterState.value.feedMax = max;
    activePresetId.value = null;
  }

  function setDisplayMode(mode: "hide" | "dim"): void {
    filterState.value.displayMode = mode;
  }

  function setDimOpacity(opacity: number): void {
    filterState.value.dimOpacity = Math.max(0, Math.min(1, opacity));
  }

  // Get opacity for a specific segment
  function getSegmentOpacity(index: number): number {
    const vis = segmentVisibility.value[index];
    return vis ? vis.opacity : 1;
  }

  return {
    // State
    filterState,
    activePresetId,
    segmentBounds,

    // Computed
    segmentVisibility,
    filteredSegments,
    filterStats,
    hasActiveFilter,

    // Presets
    presets: FILTER_PRESETS,

    // Actions
    applyPreset,
    resetFilter,
    setTypeFilter,
    setZFilter,
    setFeedFilter,
    setDisplayMode,
    setDimOpacity,
    getSegmentOpacity,
    passesFilter,
  };
}

export default useSegmentFilter;
