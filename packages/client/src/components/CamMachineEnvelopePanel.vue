<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Machine Envelope Panel Component

Part of Phase 24.5: Machine Envelope Integration
Repository: HanzoRazer/luthiers-toolbox
Created: January 2025

Features:
- Machine selector with work envelope display
- CAM defaults auto-fill (feed rates, rapid speed, safe Z)
- Per-machine configuration persistence
- Integrates with /cam/machines API endpoint
-->

<template>
  <div class="border rounded-lg p-3 bg-white text-[11px] space-y-2">
    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold text-gray-700">
        Machine Envelope
      </h3>
      <span class="text-[10px] text-gray-400">/cam/machines</span>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <label class="flex items-center gap-1">
        <span>Machine</span>
        <select
          v-model="selectedId"
          class="border rounded px-2 py-1 text-[11px] w-44"
        >
          <option disabled value="">
            Select machine…
          </option>
          <option
            v-for="m in machines"
            :key="m.id"
            :value="m.id"
          >
            {{ m.name }}
          </option>
        </select>
      </label>

      <button
        class="px-2 py-1 rounded border border-gray-300 text-[11px] disabled:opacity-50"
        :disabled="loading"
        @click="loadMachines"
      >
        <span v-if="!loading">Reload</span>
        <span v-else>Loading…</span>
      </button>
    </div>

    <p v-if="error" class="text-[11px] text-red-600">
      {{ error }}
    </p>

    <div v-if="current" class="space-y-1">
      <div class="text-[11px] text-gray-700">
        <span class="font-semibold">{{ current.name }}</span>
        <span v-if="current.controller" class="text-[10px] text-gray-500">
          · {{ current.controller }}
        </span>
      </div>

      <div class="grid grid-cols-2 gap-2 text-[10px] text-gray-500">
        <div>
          <div class="uppercase text-gray-400">Envelope X/Y</div>
          <div>
            X: {{ fmt(current.limits?.min_x) }} → {{ fmt(current.limits?.max_x) }}
            {{ units }}
          </div>
          <div>
            Y: {{ fmt(current.limits?.min_y) }} → {{ fmt(current.limits?.max_y) }}
            {{ units }}
          </div>
        </div>
        <div>
          <div class="uppercase text-gray-400">Envelope Z</div>
          <div>
            Z: {{ fmt(current.limits?.min_z) }} → {{ fmt(current.limits?.max_z) }}
            {{ units }}
          </div>
          <div v-if="current.feed_xy">
            F<sub>max</sub>: {{ Math.round(current.feed_xy) }} {{ units }}/min
          </div>
        </div>
      </div>

      <div
        v-if="current.camDefaults"
        class="border rounded p-2 bg-gray-50 space-y-1"
      >
        <div class="text-[10px] uppercase text-gray-400">
          CAM Defaults
        </div>
        <div class="grid grid-cols-2 gap-1 text-[10px] text-gray-600">
          <div>
            Tool ⌀: {{ fmt(current.camDefaults.tool_d) }} {{ units }}
          </div>
          <div>
            Stepover: {{ (current.camDefaults.stepover * 100).toFixed(0) }}%
          </div>
          <div>
            Stepdown: {{ fmt(current.camDefaults.stepdown) }} {{ units }}
          </div>
          <div>
            Feed XY: {{ Math.round(current.camDefaults.feed_xy) }} {{ units }}/min
          </div>
          <div>
            Safe Z: {{ fmt(current.camDefaults.safe_z) }} {{ units }}
          </div>
          <div>
            Z rough: {{ fmt(current.camDefaults.z_rough) }} {{ units }}
          </div>
        </div>
        <p class="text-[10px] text-gray-500 mt-1">
          These values are emitted to BridgeLab as per-machine presets.
        </p>
      </div>

      <p class="text-[10px] text-gray-500" v-else>
        No CAM defaults defined for this machine. Manual values in BridgeLab will be used.
      </p>

      <p class="text-[10px] text-gray-500">
        Backplot will highlight over-travel when toolpath bounds exceed these limits.
      </p>
    </div>

    <p v-else-if="!loading && !error" class="text-[11px] text-gray-500">
      No machines loaded. Click Reload to fetch from
      <span class="font-mono">/cam/machines</span>.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

interface MachineLimits {
  min_x?: number | null
  max_x?: number | null
  min_y?: number | null
  max_y?: number | null
  min_z?: number | null
  max_z?: number | null
}

interface MachineCamDefaults {
  tool_d?: number | null
  stepover?: number | null
  stepdown?: number | null
  feed_xy?: number | null
  safe_z?: number | null
  z_rough?: number | null
}

interface Machine {
  id: string
  name: string
  controller?: string | null
  units?: 'mm' | 'inch' | string | null
  limits?: MachineLimits | null
  feed_xy?: number | null
  camDefaults?: MachineCamDefaults | null
}

const emit = defineEmits<{
  (e: 'machine-selected', machine: Machine | null): void
  (e: 'limits-changed', limits: MachineLimits | null): void
  (e: 'cam-defaults-changed', defaults: MachineCamDefaults | null): void
}>()

const machines = ref<Machine[]>([])
const selectedId = ref<string>('')
const loading = ref(false)
const error = ref<string | null>(null)

const current = computed<Machine | null>(() => {
  if (!selectedId.value) return null
  return machines.value.find(m => m.id === selectedId.value) ?? null
})

const units = computed(() => {
  if (!current.value?.units) return 'mm'
  return current.value.units
})

function fmt (v: number | null | undefined): string {
  if (v == null) return '—'
  return v.toFixed(1)
}

async function loadMachines () {
  loading.value = true
  error.value = null

  try {
    const resp = await fetch('/cam/machines')
    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(text || `HTTP ${resp.status}`)
    }
    const data = await resp.json() as Machine[]
    machines.value = data
    if (!selectedId.value && machines.value.length > 0) {
      selectedId.value = machines.value[0].id
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e)
  } finally {
    loading.value = false
  }
}

watch(current, (val) => {
  emit('machine-selected', val)
  emit('limits-changed', val?.limits ?? null)
  emit('cam-defaults-changed', val?.camDefaults ?? null)
})

onMounted(() => {
  void loadMachines()
})
</script>
