<script setup lang="ts">
/**
 * ToolParametersPanel.vue - Tool & cutting parameters form
 *
 * Contains all basic tool and cutting parameters for adaptive pocket planning.
 *
 * Example:
 * ```vue
 * <ToolParametersPanel
 *   v-model:tool-d="toolD"
 *   v-model:stepover-pct="stepoverPct"
 *   v-model:stepdown="stepdown"
 *   v-model:margin="margin"
 *   v-model:strategy="strategy"
 *   v-model:corner-radius-min="cornerRadiusMin"
 *   v-model:slowdown-feed-pct="slowdownFeedPct"
 *   v-model:climb="climb"
 *   v-model:feed-x-y="feedXY"
 *   v-model:units="units"
 * />
 * ```
 */

defineProps<{
  toolD: number;
  stepoverPct: number;
  stepdown: number;
  margin: number;
  strategy: string;
  cornerRadiusMin: number;
  slowdownFeedPct: number;
  climb: boolean;
  feedXY: number;
  units: string;
}>();

defineEmits<{
  "update:toolD": [value: number];
  "update:stepoverPct": [value: number];
  "update:stepdown": [value: number];
  "update:margin": [value: number];
  "update:strategy": [value: string];
  "update:cornerRadiusMin": [value: number];
  "update:slowdownFeedPct": [value: number];
  "update:climb": [value: boolean];
  "update:feedXY": [value: number];
  "update:units": [value: string];
}>();
</script>

<template>
  <div class="space-y-2">
    <label class="block text-sm font-medium">Tool Ø (mm)</label>
    <input
      :value="toolD"
      type="number"
      step="0.1"
      class="border px-2 py-1 rounded w-full"
      @input="$emit('update:toolD', Number(($event.target as HTMLInputElement).value))"
    >

    <label class="block text-sm font-medium">Step-over (%)</label>
    <input
      :value="stepoverPct"
      type="number"
      step="1"
      min="5"
      max="95"
      class="border px-2 py-1 rounded w-full"
      @input="$emit('update:stepoverPct', Number(($event.target as HTMLInputElement).value))"
    >

    <label class="block text-sm font-medium">Step-down (mm)</label>
    <input
      :value="stepdown"
      type="number"
      step="0.1"
      class="border px-2 py-1 rounded w-full"
      @input="$emit('update:stepdown', Number(($event.target as HTMLInputElement).value))"
    >

    <label class="block text-sm font-medium">Margin (mm)</label>
    <input
      :value="margin"
      type="number"
      step="0.1"
      class="border px-2 py-1 rounded w-full"
      @input="$emit('update:margin', Number(($event.target as HTMLInputElement).value))"
    >

    <label class="block text-sm font-medium">Strategy</label>
    <select
      :value="strategy"
      class="border px-2 py-1 rounded w-full"
      @change="$emit('update:strategy', ($event.target as HTMLSelectElement).value)"
    >
      <option>Spiral</option>
      <option>Lanes</option>
    </select>

    <label class="block text-sm font-medium">Corner Radius Min (mm) <span class="text-xs text-gray-500">L.2</span></label>
    <input
      :value="cornerRadiusMin"
      type="number"
      step="0.1"
      class="border px-2 py-1 rounded w-full"
      @input="$emit('update:cornerRadiusMin', Number(($event.target as HTMLInputElement).value))"
    >

    <label class="block text-sm font-medium">Slowdown Feed (%) <span class="text-xs text-gray-500">L.2</span></label>
    <input
      :value="slowdownFeedPct"
      type="number"
      step="5"
      min="30"
      max="100"
      class="border px-2 py-1 rounded w-full"
      @input="$emit('update:slowdownFeedPct', Number(($event.target as HTMLInputElement).value))"
    >

    <label class="flex items-center gap-2 text-sm">
      <input
        :checked="climb"
        type="checkbox"
        @change="$emit('update:climb', ($event.target as HTMLInputElement).checked)"
      >
      <span>Climb milling</span>
    </label>

    <label class="block text-sm font-medium">Feed XY (mm/min)</label>
    <input
      :value="feedXY"
      type="number"
      step="100"
      class="border px-2 py-1 rounded w-full"
      @input="$emit('update:feedXY', Number(($event.target as HTMLInputElement).value))"
    >

    <label class="block text-sm font-medium">Units</label>
    <select
      :value="units"
      class="border px-2 py-1 rounded w-full"
      @change="$emit('update:units', ($event.target as HTMLSelectElement).value)"
    >
      <option value="mm">
        mm (G21)
      </option>
      <option value="inch">
        inch (G20)
      </option>
    </select>
  </div>
</template>
