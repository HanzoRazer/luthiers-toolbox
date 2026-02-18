<script setup lang="ts">
/**
 * OptimizeForMachinePanel - M.2 What-if optimizer for machine parameters
 * Extracted from AdaptivePocketLab.vue
 */
import { computed } from 'vue'

interface OptResult {
  baseline: {
    time_s: number
    passes: number
    hop_count: number
  }
  opt: {
    best: {
      feed_mm_min: number
      stepover: number
      rpm: number
      time_s: number
    }
    neighbors: Array<{
      feed_mm_min: number
      stepover: number
      time_s: number
    }>
  }
}

const props = defineProps<{
  optOut: OptResult | null
  hasToolpath: boolean
  hasMachine: boolean
  // Range inputs
  optFeedLo: number
  optFeedHi: number
  optStpLo: number
  optStpHi: number
  optRpmLo: number
  optRpmHi: number
  optFlutes: number
  optChip: number
  optGridF: number
  optGridS: number
  enforceChip: boolean
  chipTol: number
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:optFeedLo': [value: number]
  'update:optFeedHi': [value: number]
  'update:optStpLo': [value: number]
  'update:optStpHi': [value: number]
  'update:optRpmLo': [value: number]
  'update:optRpmHi': [value: number]
  'update:optFlutes': [value: number]
  'update:optChip': [value: number]
  'update:optGridF': [value: number]
  'update:optGridS': [value: number]
  'update:enforceChip': [value: boolean]
  'update:chipTol': [value: number]
  'runWhatIf': []
  'compareSettings': []
  'applyRecommendation': []
}>()

const canRunWhatIf = computed(() => props.hasToolpath && props.hasMachine && !props.disabled)
const canCompare = computed(() => !!props.optOut && !props.disabled)
</script>

<template>
  <div class="optimize-panel border rounded-xl p-3 bg-gradient-to-br from-blue-50 to-indigo-50">
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold text-sm">
        Optimize for Machine
      </h3>
      <div class="flex gap-2">
        <button
          class="px-3 py-1 text-sm border rounded bg-white hover:bg-gray-50 disabled:opacity-50"
          :disabled="!canRunWhatIf"
          @click="emit('runWhatIf')"
        >
          Run What-If
        </button>
        <button
          class="px-3 py-1 text-sm border rounded bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
          :disabled="!canCompare"
          @click="emit('compareSettings')"
        >
          Compare Settings
        </button>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-3 text-xs">
      <div>
        <label class="block mb-1">Feed (mm/min)</label>
        <div class="flex gap-1">
          <input
            :value="optFeedLo"
            type="number"
            class="border px-1 py-1 rounded w-full text-xs"
            :disabled="disabled"
            @input="emit('update:optFeedLo', Number(($event.target as HTMLInputElement).value))"
          >
          <input
            :value="optFeedHi"
            type="number"
            class="border px-1 py-1 rounded w-full text-xs"
            :disabled="disabled"
            @input="emit('update:optFeedHi', Number(($event.target as HTMLInputElement).value))"
          >
        </div>
      </div>
      <div>
        <label class="block mb-1">Stepover (0..1)</label>
        <div class="flex gap-1">
          <input
            :value="optStpLo"
            type="number"
            step="0.01"
            class="border px-1 py-1 rounded w-full text-xs"
            :disabled="disabled"
            @input="emit('update:optStpLo', Number(($event.target as HTMLInputElement).value))"
          >
          <input
            :value="optStpHi"
            type="number"
            step="0.01"
            class="border px-1 py-1 rounded w-full text-xs"
            :disabled="disabled"
            @input="emit('update:optStpHi', Number(($event.target as HTMLInputElement).value))"
          >
        </div>
      </div>
      <div>
        <label class="block mb-1">RPM</label>
        <div class="flex gap-1">
          <input
            :value="optRpmLo"
            type="number"
            class="border px-1 py-1 rounded w-full text-xs"
            :disabled="disabled"
            @input="emit('update:optRpmLo', Number(($event.target as HTMLInputElement).value))"
          >
          <input
            :value="optRpmHi"
            type="number"
            class="border px-1 py-1 rounded w-full text-xs"
            :disabled="disabled"
            @input="emit('update:optRpmHi', Number(($event.target as HTMLInputElement).value))"
          >
        </div>
      </div>
      <div>
        <label class="block mb-1">Flutes</label>
        <input
          :value="optFlutes"
          type="number"
          class="border px-1 py-1 rounded w-full text-xs"
          :disabled="disabled"
          @input="emit('update:optFlutes', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div>
        <label class="block mb-1">Chipload (mm)</label>
        <input
          :value="optChip"
          type="number"
          step="0.005"
          class="border px-1 py-1 rounded w-full text-xs"
          :disabled="disabled"
          @input="emit('update:optChip', Number(($event.target as HTMLInputElement).value))"
        >
      </div>
      <div>
        <label class="block mb-1">Grid (F×S)</label>
        <div class="flex gap-1">
          <input
            :value="optGridF"
            type="number"
            class="border px-1 py-1 rounded w-full text-xs"
            :disabled="disabled"
            @input="emit('update:optGridF', Number(($event.target as HTMLInputElement).value))"
          >
          <input
            :value="optGridS"
            type="number"
            class="border px-1 py-1 rounded w-full text-xs"
            :disabled="disabled"
            @input="emit('update:optGridS', Number(($event.target as HTMLInputElement).value))"
          >
        </div>
      </div>
    </div>

    <!-- Chipload enforcement controls -->
    <div class="flex items-center gap-3 mt-2 text-xs">
      <label class="flex items-center gap-1">
        <input
          :checked="enforceChip"
          type="checkbox"
          :disabled="disabled"
          @change="emit('update:enforceChip', ($event.target as HTMLInputElement).checked)"
        >
        <span>Enforce chipload</span>
      </label>
      <label class="flex items-center gap-1">
        <span>Tolerance (mm/tooth)</span>
        <input
          :value="chipTol"
          type="number"
          step="0.005"
          class="border px-2 py-1 rounded w-20"
          :disabled="!enforceChip || disabled"
          @input="emit('update:chipTol', Number(($event.target as HTMLInputElement).value))"
        >
      </label>
    </div>

    <!-- Results display -->
    <div
      v-if="optOut"
      class="mt-3 grid md:grid-cols-3 gap-2 text-xs"
    >
      <div class="border rounded p-2 bg-white">
        <div class="font-medium mb-1">
          Baseline
        </div>
        <div><b>Time:</b> {{ optOut.baseline.time_s }} s</div>
        <div class="text-gray-600">
          Passes: {{ optOut.baseline.passes }}
        </div>
        <div class="text-gray-600">
          Hops: {{ optOut.baseline.hop_count }}
        </div>
      </div>
      <div class="border rounded p-2 bg-white">
        <div class="font-medium mb-1">
          Recommended
        </div>
        <ul class="space-y-0.5">
          <li><b>Feed:</b> {{ optOut.opt.best.feed_mm_min }} mm/min</li>
          <li><b>Stepover:</b> {{ (optOut.opt.best.stepover * 100).toFixed(1) }}%</li>
          <li><b>RPM:</b> {{ optOut.opt.best.rpm }}</li>
          <li><b>Time:</b> {{ optOut.opt.best.time_s }} s</li>
        </ul>
        <button
          class="mt-2 px-2 py-1 border rounded text-xs bg-blue-600 text-white hover:bg-blue-700"
          @click="emit('applyRecommendation')"
        >
          Apply to Job
        </button>
      </div>
      <div class="border rounded p-2 bg-white">
        <div class="font-medium mb-1">
          Sensitivity (near best)
        </div>
        <table class="w-full mt-1">
          <thead>
            <tr>
              <th class="text-left">Feed</th>
              <th class="text-left">Stp%</th>
              <th class="text-left">Time</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="n in optOut.opt.neighbors.slice(0, 4)"
              :key="n.feed_mm_min + '-' + n.stepover"
              class="text-xs"
            >
              <td>{{ n.feed_mm_min }}</td>
              <td>{{ (n.stepover * 100).toFixed(0) }}</td>
              <td>{{ n.time_s }}s</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
