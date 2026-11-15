<script setup lang="ts">
/**
 * FiltersBar.vue - Reusable filters bar for dashboards
 *
 * Provides lane, preset, job hint, date range, and quick range filters.
 * All filter values are v-model props for two-way binding.
 *
 * Example:
 * ```vue
 * <FiltersBar
 *   v-model:lane="laneFilter"
 *   v-model:preset="presetFilter"
 *   v-model:job-hint="jobFilter"
 *   v-model:since="since"
 *   v-model:until="until"
 *   v-model:quick-range="quickRangeMode"
 *   :all-lanes="allLanes"
 *   :all-presets="allPresets"
 *   :lane-presets="lanePresets"
 *   @apply-quick-range="applyQuickRange"
 *   @apply-lane-preset="applyLanePreset"
 * />
 * ```
 */
import { computed } from "vue";

// Types
export type QuickRangeMode = "" | "all" | "last7" | "last30" | "last90" | "year";

export interface QuickRangeModeOption {
  id: QuickRangeMode;
  label: string;
}

export interface LanePresetDef {
  id: string;
  label: string;
  lane: string;
  preset?: string;
  defaultQuickRange?: QuickRangeMode;
  badge?: string;
}

// Props
const props = withDefaults(
  defineProps<{
    lane: string;
    preset: string;
    jobHint: string;
    since: string;
    until: string;
    quickRange: QuickRangeMode;
    allLanes: string[];
    allPresets: string[];
    lanePresets?: LanePresetDef[];
    quickRangeModes?: QuickRangeModeOption[];
  }>(),
  {
    lanePresets: () => [],
    quickRangeModes: () => [
      { id: "all", label: "All" },
      { id: "last7", label: "Last 7d" },
      { id: "last30", label: "Last 30d" },
      { id: "last90", label: "Last 90d" },
      { id: "year", label: "This year" },
    ],
  }
);

// Emits
const emit = defineEmits<{
  "update:lane": [value: string];
  "update:preset": [value: string];
  "update:jobHint": [value: string];
  "update:since": [value: string];
  "update:until": [value: string];
  "update:quickRange": [value: QuickRangeMode];
  applyQuickRange: [mode: QuickRangeMode];
  applyLanePreset: [id: string];
}>();

// Local v-model helpers
const laneModel = computed({
  get: () => props.lane,
  set: (v) => emit("update:lane", v),
});
const presetModel = computed({
  get: () => props.preset,
  set: (v) => emit("update:preset", v),
});
const jobHintModel = computed({
  get: () => props.jobHint,
  set: (v) => emit("update:jobHint", v),
});
const sinceModel = computed({
  get: () => props.since,
  set: (v) => emit("update:since", v),
});
const untilModel = computed({
  get: () => props.until,
  set: (v) => emit("update:until", v),
});

// Check if a lane preset is currently active
function isLanePresetActive(p: LanePresetDef): boolean {
  const laneMatch =
    props.lane && props.lane.toLowerCase() === p.lane.toLowerCase();
  const presetVal = p.preset?.toLowerCase() || "";
  const currentPreset = props.preset?.toLowerCase() || "";
  const presetMatch = presetVal === currentPreset;
  const mode = p.defaultQuickRange || "all";
  const rangeMatch = props.quickRange === mode;
  return !!(laneMatch && presetMatch && rangeMatch);
}
</script>

<template>
  <div class="flex flex-col gap-2 text-[11px] text-gray-700">
    <!-- Row 1: Lane, Preset, Job hint -->
    <div class="flex flex-wrap items-center gap-3">
      <div class="flex items-center gap-2">
        <span class="font-semibold">Lane:</span>
        <select
          v-model="laneModel"
          class="px-2 py-1 border rounded text-[11px]"
        >
          <option value="">
            All
          </option>
          <option
            v-for="laneOpt in allLanes"
            :key="laneOpt"
            :value="laneOpt"
          >
            {{ laneOpt }}
          </option>
        </select>
      </div>

      <div class="flex items-center gap-2">
        <span class="font-semibold">Preset:</span>
        <select
          v-model="presetModel"
          class="px-2 py-1 border rounded text-[11px]"
        >
          <option value="">
            All
          </option>
          <option
            v-for="presetOpt in allPresets"
            :key="presetOpt"
            :value="presetOpt"
          >
            {{ presetOpt }}
          </option>
        </select>
      </div>

      <div class="flex items-center gap-2">
        <span class="font-semibold">Job hint:</span>
        <input
          v-model="jobHintModel"
          type="text"
          placeholder="rosette_, neck_pocket..."
          class="px-2 py-1 border rounded text-[11px] w-48"
        >
        <span class="text-[10px] text-gray-500">
          Used for deep links &amp; bucket details (not filtering aggregates).
        </span>
      </div>
    </div>

    <!-- Row 2: Date inputs + quick range chips -->
    <div class="flex flex-wrap items-center gap-3">
      <div class="flex items-center gap-2">
        <span class="font-semibold">Since:</span>
        <input
          v-model="sinceModel"
          type="date"
          class="px-2 py-1 border rounded text-[11px]"
        >
        <span class="font-semibold">Until:</span>
        <input
          v-model="untilModel"
          type="date"
          class="px-2 py-1 border rounded text-[11px]"
        >
      </div>

      <!-- Quick time range chips -->
      <div class="flex flex-wrap items-center gap-1">
        <span class="text-[10px] text-gray-500 mr-1">
          Quick range:
        </span>
        <button
          v-for="mode in quickRangeModes"
          :key="mode.id"
          class="px-2 py-0.5 rounded-full border text-[10px] transition"
          :class="quickRange === mode.id
            ? 'bg-indigo-600 text-white border-indigo-600'
            : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'"
          @click="$emit('applyQuickRange', mode.id)"
        >
          {{ mode.label }}
        </button>
      </div>

      <span class="text-[10px] text-gray-500">
        Quick ranges set dates &amp; reload aggregates; manual edits still work.
      </span>
    </div>

    <!-- Row 3: Lane preset chips -->
    <div
      v-if="lanePresets.length"
      class="flex flex-wrap items-center gap-2"
    >
      <span class="text-[10px] text-gray-500 mr-1">
        Lane presets:
      </span>
      <button
        v-for="p in lanePresets"
        :key="p.id"
        class="px-2 py-0.5 rounded-full border text-[10px] transition inline-flex items-center gap-1"
        :class="isLanePresetActive(p)
          ? 'bg-emerald-600 text-white border-emerald-600'
          : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'"
        @click="$emit('applyLanePreset', p.id)"
      >
        <span>{{ p.label }}</span>
        <span
          v-if="p.badge"
          class="px-1 rounded-full text-[9px]"
          :class="isLanePresetActive(p)
            ? 'bg-emerald-500 text-white'
            : 'bg-gray-100 text-gray-700'"
        >
          {{ p.badge }}
        </span>
      </button>
      <span class="text-[10px] text-gray-500">
        One-click lane + preset + window presets (editable in code).
      </span>
    </div>
  </div>
</template>
