<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
MachineManagerView - Machine list + detail viewer

Repository: HanzoRazer/luthiers-toolbox
Updated: November 2025
-->

<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold">Machine Manager</h2>
        <p class="text-[11px] text-gray-500">
          Inspect configured CNC machines, envelopes, and CAM defaults
        </p>
      </div>
      <span class="text-[10px] text-gray-400">/lab/machines</span>
    </div>

    <div class="grid lg:grid-cols-[1.1fr,1.4fr] gap-4">
      <!-- Left: list -->
      <div class="border rounded-lg p-3 bg-white text-[11px] space-y-2">
        <div class="flex items-center justify-between">
          <h3 class="text-xs font-semibold text-gray-700">
            Machines
          </h3>
          <div class="flex items-center gap-2">
            <input
              v-model="query"
              placeholder="Filter…"
              class="border rounded px-2 py-0.5 text-[10px] w-32"
            />
            <button
              class="px-2 py-0.5 rounded border border-gray-300 text-[10px] disabled:opacity-50"
              :disabled="loading"
              @click="loadMachines"
            >
              <span v-if="!loading">Reload</span>
              <span v-else>Loading…</span>
            </button>
          </div>
        </div>

        <p v-if="error" class="text-[11px] text-red-600">
          {{ error }}
        </p>

        <div
          v-if="!filteredMachines.length && !loading && !error"
          class="text-[11px] text-gray-500"
        >
          No machines configured yet.
        </div>

        <ul v-else class="space-y-1 max-h-64 overflow-auto pr-1">
          <li
            v-for="m in filteredMachines"
            :key="m.id"
            class="flex items-center justify-between gap-2 px-2 py-1 rounded cursor-pointer hover:bg-gray-50"
            :class="m.id === selectedId ? 'bg-gray-100' : ''"
            @click="selectMachine(m.id)"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-1">
                <div class="truncate">
                  <span class="font-semibold">{{ m.name }}</span>
                  <span v-if="m.controller" class="text-[10px] text-gray-500">
                    · {{ m.controller }}
                  </span>
                </div>
                <span class="text-[9px] text-gray-400 font-mono">
                  {{ m.id }}
                </span>
              </div>
              <p class="text-[10px] text-gray-500 truncate">
                {{ m.description || '—' }}
              </p>
            </div>
          </li>
        </ul>
      </div>

      <!-- Right: detail -->
      <div class="border rounded-lg p-3 bg-white text-[11px] space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-xs font-semibold text-gray-700">
            Machine Detail
          </h3>
          <span class="text-[10px] text-gray-400">
            {{ current ? current.id : 'none selected' }}
          </span>
        </div>

        <div v-if="!current" class="text-[11px] text-gray-500">
          Select a machine from the list to inspect its limits and defaults.
        </div>

        <div v-else class="space-y-3">
          <div>
            <div class="text-[11px] text-gray-700">
              <span class="font-semibold">{{ current.name }}</span>
              <span v-if="current.controller" class="text-[10px] text-gray-500">
                · {{ current.controller }}
              </span>
            </div>
            <p
              v-if="current.description"
              class="text-[10px] text-gray-500"
            >
              {{ current.description }}
            </p>
          </div>

          <div class="grid md:grid-cols-2 gap-3 text-[10px] text-gray-600">
            <div class="space-y-1">
              <div class="text-[10px] uppercase text-gray-400">
                Work Envelope
              </div>
              <p>
                X:
                {{ fmt(current.limits?.min_x) }} → {{ fmt(current.limits?.max_x) }}
                {{ units }}
              </p>
              <p>
                Y:
                {{ fmt(current.limits?.min_y) }} → {{ fmt(current.limits?.max_y) }}
                {{ units }}
              </p>
              <p>
                Z:
                {{ fmt(current.limits?.min_z) }} → {{ fmt(current.limits?.max_z) }}
                {{ units }}
              </p>
            </div>

            <div class="space-y-1">
              <div class="text-[10px] uppercase text-gray-400">
                Dynamics
              </div>
              <p v-if="current.feed_xy">
                F<sub>max</sub> XY: {{ Math.round(current.feed_xy) }} {{ units }}/min
              </p>
              <p v-if="current.rapid">
                Rapid: {{ Math.round(current.rapid) }} {{ units }}/min
              </p>
              <p v-if="current.accel">
                Accel: {{ Math.round(current.accel) }} {{ units }}/s²
              </p>
            </div>
          </div>

          <div
            v-if="current.camDefaults"
            class="border rounded p-2 bg-gray-50 space-y-1"
          >
            <div class="text-[10px] uppercase text-gray-400">
              CAM Defaults
            </div>
            <div class="grid md:grid-cols-2 gap-1 text-[10px] text-gray-600">
              <p>Tool ⌀: {{ fmt(current.camDefaults.tool_d) }} {{ units }}</p>
              <p>
                Stepover:
                {{
                  current.camDefaults.stepover != null
                    ? (current.camDefaults.stepover * 100).toFixed(0)
                    : '—'
                }}%
              </p>
              <p>Stepdown: {{ fmt(current.camDefaults.stepdown) }} {{ units }}</p>
              <p>
                Feed XY:
                {{
                  current.camDefaults.feed_xy != null
                    ? Math.round(current.camDefaults.feed_xy)
                    : '—'
                }}
                {{ units }}/min
              </p>
              <p>Safe Z: {{ fmt(current.camDefaults.safe_z) }} {{ units }}</p>
              <p>Z rough: {{ fmt(current.camDefaults.z_rough) }} {{ units }}</p>
            </div>
            <p class="text-[10px] text-gray-500">
              These defaults are propagated into BridgeLab and Adaptive Lab for this machine.
            </p>
          </div>

          <details class="text-[10px] text-gray-500">
            <summary class="cursor-pointer">
              Raw JSON
            </summary>
            <pre class="mt-1 bg-gray-50 border rounded p-2 whitespace-pre-wrap">{{ prettyCurrent }}</pre>
          </details>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

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
  description?: string | null
  units?: 'mm' | 'inch' | string | null
  limits?: MachineLimits | null
  feed_xy?: number | null
  rapid?: number | null
  accel?: number | null
  camDefaults?: MachineCamDefaults | null
}

const machines = ref<Machine[]>([])
const selectedId = ref<string>('')
const loading = ref(false)
const error = ref<string | null>(null)
const query = ref('')

const filteredMachines = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return machines.value
  return machines.value.filter((m) => {
    const hay = `${m.id} ${m.name} ${m.controller || ''} ${m.description || ''}`.toLowerCase()
    return hay.includes(q)
  })
})

const current = computed<Machine | null>(() => {
  if (!selectedId.value) return null
  return machines.value.find((m) => m.id === selectedId.value) ?? null
})

const units = computed(() => {
  if (!current.value?.units) return 'mm'
  return current.value.units
})

const prettyCurrent = computed(() => {
  if (!current.value) return ''
  try {
    return JSON.stringify(current.value, null, 2)
  } catch {
    return ''
  }
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

function selectMachine (id: string) {
  selectedId.value = id
}

onMounted(() => {
  void loadMachines()
})
</script>
