<script setup lang="ts">
/**
 * HeatTimeSeriesPanel.vue - M.3 Heat over Time display panel
 *
 * Shows heat time series with power charts and learning controls.
 *
 * Example:
 * ```vue
 * <HeatTimeSeriesPanel
 *   :has-moves="!!planOut?.moves"
 *   :material-id="materialId"
 *   :profile-id="profileId"
 *   :heat-ts="heatTS"
 *   v-model:include-csv-links="includeCsvLinks"
 *   v-model:adopt-overrides="adoptOverrides"
 *   v-model:live-learn-applied="liveLearnApplied"
 *   v-model:measured-seconds="measuredSeconds"
 *   :session-override-factor="sessionOverrideFactor"
 *   @run-heat-ts="runHeatTS"
 *   @export-report="exportThermalReport"
 *   @export-bundle="exportThermalBundle"
 *   @log-run="logCurrentRun"
 *   @train-overrides="trainOverrides"
 *   @reset-live-learn="resetLiveLearn"
 * />
 * ```
 */

export interface HeatTSData {
  total_s?: number;
  p_chip?: number[];
  p_tool?: number[];
  p_work?: number[];
  t?: number[];
}

const props = defineProps<{
  hasMoves: boolean;
  materialId: string;
  profileId: string;
  heatTs: HeatTSData | null;
  includeCsvLinks: boolean;
  adoptOverrides: boolean;
  liveLearnApplied: boolean;
  measuredSeconds: number | null;
  sessionOverrideFactor: number | null;
}>();

const emit = defineEmits<{
  "update:includeCsvLinks": [value: boolean];
  "update:adoptOverrides": [value: boolean];
  "update:liveLearnApplied": [value: boolean];
  "update:measuredSeconds": [value: number | null];
  runHeatTs: [];
  exportReport: [];
  exportBundle: [];
  logRun: [measuredSeconds?: number];
  trainOverrides: [];
  resetLiveLearn: [];
}>();

const canCompute = computed(() => props.hasMoves && props.materialId && props.profileId);

function tsPolyline(key: "p_chip" | "p_tool" | "p_work"): string {
  if (!props.heatTs) return "";
  const arr = props.heatTs[key];
  if (!arr || !arr.length) return "";
  const maxY = Math.max(...arr, 0.01);
  const W = 300,
    H = 120;
  return arr
    .map((v, i) => {
      const x = (i / (arr.length - 1)) * W;
      const y = H - (v / maxY) * H;
      return `${x},${y}`;
    })
    .join(" ");
}

import { computed } from "vue";
</script>

<template>
  <div class="border rounded-lg p-4 bg-white shadow-sm">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-lg font-semibold">
        Heat over Time
      </h2>
      <div class="space-y-2">
        <div class="flex gap-2">
          <button
            class="px-3 py-1 rounded bg-purple-600 text-white text-sm hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!canCompute"
            @click="$emit('runHeatTs')"
          >
            Compute
          </button>
          <button
            class="px-3 py-1 rounded border border-purple-600 text-purple-600 text-sm hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!hasMoves"
            title="Export Thermal Report (Markdown)"
            @click="$emit('exportReport')"
          >
            Export Report (MD)
          </button>
        </div>
        <label class="text-xs flex items-center gap-2">
          <input
            :checked="includeCsvLinks"
            type="checkbox"
            @change="$emit('update:includeCsvLinks', ($event.target as HTMLInputElement).checked)"
          >
          Include CSV download links in report
        </label>
        <div class="flex gap-2">
          <button
            class="px-3 py-1 rounded border border-blue-600 text-blue-600 text-sm hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!hasMoves"
            title="Export Thermal Bundle (MD + moves.json ZIP)"
            @click="$emit('exportBundle')"
          >
            Export Bundle (ZIP)
          </button>
          <button
            class="px-3 py-1 rounded border border-green-600 text-green-600 text-sm hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!hasMoves"
            title="Log this plan to database"
            @click="$emit('logRun')"
          >
            Log Plan
          </button>
          <button
            class="px-3 py-1 rounded border border-orange-600 text-orange-600 text-sm hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!profileId"
            title="Train feed overrides from logged runs"
            @click="$emit('trainOverrides')"
          >
            Train Overrides
          </button>
        </div>
        <label class="text-xs flex items-center gap-2">
          <input
            :checked="adoptOverrides"
            type="checkbox"
            @change="$emit('update:adoptOverrides', ($event.target as HTMLInputElement).checked)"
          >
          Adopt learned feed overrides
        </label>

        <!-- Live Learn Controls -->
        <div class="mt-3 pt-3 border-t border-gray-200 space-y-2">
          <div class="flex items-center gap-3">
            <label class="text-xs flex items-center gap-2">
              <input
                :checked="liveLearnApplied"
                type="checkbox"
                :disabled="!sessionOverrideFactor"
                title="Apply session-only feed override from measured runtime"
                @change="$emit('update:liveLearnApplied', ($event.target as HTMLInputElement).checked)"
              >
              Live learn (session only)
            </label>
            <span
              v-if="sessionOverrideFactor"
              class="text-xs px-2 py-0.5 border rounded bg-amber-50 text-amber-900 font-mono"
              title="Session feed scale factor (actual/estimated time)"
            >
              &times;{{ sessionOverrideFactor.toFixed(3) }}
            </span>
            <button
              v-if="sessionOverrideFactor"
              class="text-xs px-2 py-0.5 rounded border border-gray-400 text-gray-600 hover:bg-gray-50"
              title="Reset session override"
              @click="$emit('resetLiveLearn')"
            >
              Reset
            </button>
          </div>
          <div class="flex items-center gap-2">
            <input
              :value="measuredSeconds"
              type="number"
              step="0.1"
              placeholder="Actual sec"
              class="px-2 py-1 border rounded text-xs w-28"
              title="Enter measured runtime in seconds"
              @input="$emit('update:measuredSeconds', ($event.target as HTMLInputElement).valueAsNumber || null)"
            >
            <button
              class="px-3 py-1 rounded border border-amber-600 text-amber-600 text-xs hover:bg-amber-50 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!hasMoves || !measuredSeconds"
              title="Log plan with measured runtime (computes session override)"
              @click="$emit('logRun', measuredSeconds ?? undefined)"
            >
              Log with actual time
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="heatTs"
      class="space-y-3"
    >
      <!-- Summary -->
      <div class="grid grid-cols-3 gap-3 text-sm p-2 bg-purple-50 rounded">
        <div>
          <div class="text-xs text-gray-600">
            Total Time
          </div>
          <div class="font-medium">
            {{ heatTs.total_s?.toFixed(1) || 0 }} s
          </div>
        </div>
        <div>
          <div class="text-xs text-gray-600">
            Peak Chip Power
          </div>
          <div class="font-medium">
            {{ Math.max(...(heatTs.p_chip || [0])).toFixed(1) }} W
          </div>
        </div>
        <div>
          <div class="text-xs text-gray-600">
            Peak Tool Power
          </div>
          <div class="font-medium">
            {{ Math.max(...(heatTs.p_tool || [0])).toFixed(1) }} W
          </div>
        </div>
      </div>

      <!-- Power Chart -->
      <div class="border rounded p-2 bg-white">
        <div class="text-sm font-medium mb-2">
          Power over Time
        </div>
        <svg
          viewBox="0 0 300 120"
          class="w-full h-32"
        >
          <polyline
            :points="tsPolyline('p_chip')"
            fill="none"
            stroke="#f59e0b"
            stroke-width="2"
            opacity="0.9"
          />
          <polyline
            :points="tsPolyline('p_tool')"
            fill="none"
            stroke="#ef4444"
            stroke-width="2"
            opacity="0.9"
          />
          <polyline
            :points="tsPolyline('p_work')"
            fill="none"
            stroke="#14b8a6"
            stroke-width="2"
            opacity="0.9"
          />
        </svg>
        <div class="text-xs mt-2 flex items-center gap-3">
          <span class="flex items-center gap-1">
            <i
              class="inline-block w-3 h-3 rounded"
              style="background: #f59e0b"
            />
            Chip heat
          </span>
          <span class="flex items-center gap-1">
            <i
              class="inline-block w-3 h-3 rounded"
              style="background: #ef4444"
            />
            Tool heat
          </span>
          <span class="flex items-center gap-1">
            <i
              class="inline-block w-3 h-3 rounded"
              style="background: #14b8a6"
            />
            Work heat
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
