<script setup lang="ts">
/**
 * RadiusDishDesign.vue — Design tab
 *
 * Now calls the parametric backend instead of downloading static files.
 * Supports any radius (not just 15ft / 25ft).
 */
import { ref, computed } from 'vue'
import {
  generateGcode,
  downloadBlob,
  calculateDish,
  getCommonRadii,
  type CommonRadius,
} from '@/api/radius-dish'

const emit = defineEmits<{
  'update:selectedRadius': [value: number]
}>()

const props = defineProps<{ selectedRadius: number }>()

// ── State ─────────────────────────────────────────────────────────────────────

const customRadius = ref<number>(props.selectedRadius || 20)
const dishWidth    = ref<number>(381)      // 15" dish width in mm
const dishLength   = ref<number>(381)
const ballNose     = ref<number>(12.7)     // 1/2" ball nose
const stepover     = ref<number>(3.0)
const roughingStep = ref<number>(8.0)
const feed         = ref<number>(2500)
const spindle      = ref<number>(18000)
const units        = ref<'mm' | 'inch'>('mm')
const includeRough = ref<boolean>(true)

const loading   = ref(false)
const error     = ref<string | null>(null)
const calcResult = ref<any>(null)
const commonRadii = ref<CommonRadius[]>([])

// ── Computed ──────────────────────────────────────────────────────────────────

const radiusMm = computed(() => customRadius.value * 304.8)
const radiusLabel = computed(() => `${customRadius.value}ft (${Math.round(radiusMm.value)}mm)`)

// ── Actions ───────────────────────────────────────────────────────────────────

async function calculate() {
  loading.value = true
  error.value = null
  try {
    calcResult.value = await calculateDish(customRadius.value, dishWidth.value, dishLength.value)
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function downloadGcode() {
  loading.value = true
  error.value = null
  try {
    const { blob, filename } = await generateGcode({
      radius_ft:            customRadius.value,
      dish_width_mm:        dishWidth.value,
      dish_length_mm:       dishLength.value,
      ball_nose_dia_mm:     ballNose.value,
      stepover_mm:          stepover.value,
      roughing_stepover_mm: roughingStep.value,
      feed_mm_min:          feed.value,
      spindle_rpm:          spindle.value,
      units:                units.value,
      include_roughing:     includeRough.value,
    })
    downloadBlob(blob, filename)
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadCommonRadii() {
  try {
    commonRadii.value = await getCommonRadii()
  } catch {
    // non-critical
  }
}

function selectRadius(ft: number) {
  customRadius.value = ft
  emit('update:selectedRadius', ft)
}

loadCommonRadii()
</script>

<template>
  <div class="space-y-5">

    <!-- Radius selection -->
    <div class="grid md:grid-cols-2 gap-5">
      <div class="space-y-3">
        <h3 class="font-semibold text-lg">Radius selection</h3>
        <p class="text-sm opacity-70">
          Any radius supported. Common values below, or enter a custom value.
        </p>

        <!-- Quick-select buttons from backend -->
        <div v-if="commonRadii.length" class="flex flex-wrap gap-2">
          <button
            v-for="r in commonRadii"
            :key="r.ft"
            class="px-3 py-1.5 rounded border text-sm transition-colors"
            :class="customRadius === r.ft
              ? 'bg-blue-100 border-blue-500 font-medium'
              : 'hover:bg-gray-50'"
            :title="r.use"
            @click="selectRadius(r.ft)"
          >
            {{ r.ft }}ft
          </button>
        </div>

        <!-- Custom input -->
        <label class="flex flex-col">
          <span class="text-sm font-medium mb-1">Custom radius (feet)</span>
          <input
            v-model.number="customRadius"
            type="number"
            step="1"
            min="5"
            max="50"
            class="border p-2 rounded w-32"
            @change="emit('update:selectedRadius', customRadius)"
          >
        </label>

        <!-- Dish dimensions -->
        <div class="grid grid-cols-2 gap-3">
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Width (mm)</span>
            <input v-model.number="dishWidth" type="number" step="5" class="border p-2 rounded">
          </label>
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Length (mm)</span>
            <input v-model.number="dishLength" type="number" step="5" class="border p-2 rounded">
          </label>
        </div>

        <button
          class="px-4 py-2 rounded border hover:bg-gray-50 transition-colors text-sm"
          :disabled="loading"
          @click="calculate"
        >
          Calculate depth
        </button>

        <!-- Depth result -->
        <div v-if="calcResult" class="p-3 bg-blue-50 rounded text-sm space-y-1">
          <div class="font-medium text-blue-800">{{ radiusLabel }}</div>
          <div>Max depth: <strong>{{ calcResult.max_depth_mm }}mm</strong>
            ({{ (calcResult.max_depth_mm / 25.4).toFixed(4) }}")</div>
          <div class="opacity-60 text-xs">{{ calcResult.formula }}</div>
        </div>
      </div>

      <!-- Common radii reference -->
      <div v-if="commonRadii.length" class="space-y-2">
        <h3 class="font-semibold text-lg">Reference</h3>
        <div class="border rounded overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left p-2">Radius</th>
                <th class="text-left p-2">Depth @15"</th>
                <th class="text-left p-2">Use</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in commonRadii"
                :key="r.ft"
                class="border-t cursor-pointer hover:bg-blue-50 transition-colors"
                :class="customRadius === r.ft ? 'bg-blue-50' : ''"
                @click="selectRadius(r.ft)"
              >
                <td class="p-2 font-mono">{{ r.ft }}ft</td>
                <td class="p-2 font-mono">{{ r.depth_for_15in_wide_mm }}mm</td>
                <td class="p-2 opacity-70">{{ r.use }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- G-code options -->
    <div class="border rounded p-4 space-y-4">
      <h3 class="font-semibold">G-code options</h3>
      <div class="grid sm:grid-cols-2 md:grid-cols-3 gap-3 text-sm">
        <label class="flex flex-col">
          <span class="font-medium mb-1">Ball nose (mm)</span>
          <input v-model.number="ballNose" type="number" step="0.1" class="border p-1.5 rounded">
        </label>
        <label class="flex flex-col">
          <span class="font-medium mb-1">Finish stepover (mm)</span>
          <input v-model.number="stepover" type="number" step="0.5" class="border p-1.5 rounded">
        </label>
        <label class="flex flex-col">
          <span class="font-medium mb-1">Rough stepover (mm)</span>
          <input v-model.number="roughingStep" type="number" step="0.5" class="border p-1.5 rounded">
        </label>
        <label class="flex flex-col">
          <span class="font-medium mb-1">Feed (mm/min)</span>
          <input v-model.number="feed" type="number" step="100" class="border p-1.5 rounded">
        </label>
        <label class="flex flex-col">
          <span class="font-medium mb-1">Spindle (RPM)</span>
          <input v-model.number="spindle" type="number" step="500" class="border p-1.5 rounded">
        </label>
        <label class="flex flex-col">
          <span class="font-medium mb-1">Units</span>
          <select v-model="units" class="border p-1.5 rounded">
            <option value="mm">mm (G21)</option>
            <option value="inch">inch (G20)</option>
          </select>
        </label>
      </div>
      <label class="flex items-center gap-2 text-sm">
        <input v-model="includeRough" type="checkbox">
        Include roughing pass
      </label>
    </div>

    <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
      {{ error }}
    </div>

    <div class="flex gap-3 flex-wrap">
      <button
        class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
        :disabled="loading"
        @click="downloadGcode"
      >
        {{ loading ? 'Generating...' : `Download G-code (${customRadius}ft)` }}
      </button>
    </div>

  </div>
</template>
