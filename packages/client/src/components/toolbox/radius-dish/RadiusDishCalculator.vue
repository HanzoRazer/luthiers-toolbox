<script setup lang="ts">
/**
 * RadiusDishCalculator.vue - Calculator tab content
 * Extracted from RadiusDishDesigner.vue
 */
import { ref } from 'vue'

interface CalcResult {
  width_in: string
  width_mm: string
  radius_ft: number
  radius_mm: string
  depth_in: string
  depth_mm: string
}

const calc = ref({
  width: 16,
  radius: 15
})

const calcResult = ref<CalcResult | null>(null)

function calculateDepth() {
  const width_in = calc.value.width
  const radius_ft = calc.value.radius

  // Convert to same units (inches)
  const radius_in = radius_ft * 12
  const half_width = width_in / 2

  // Calculate depth using circular segment formula
  // depth = R - sqrt(R^2 - (W/2)^2)
  const depth_in = radius_in - Math.sqrt(Math.pow(radius_in, 2) - Math.pow(half_width, 2))

  // Convert to mm
  const width_mm = width_in * 25.4
  const radius_mm = radius_ft * 304.8
  const depth_mm = depth_in * 25.4

  calcResult.value = {
    width_in: width_in.toFixed(3),
    width_mm: width_mm.toFixed(1),
    radius_ft: radius_ft,
    radius_mm: radius_mm.toFixed(0),
    depth_in: depth_in.toFixed(4),
    depth_mm: depth_mm.toFixed(2)
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="grid md:grid-cols-2 gap-4">
      <div class="space-y-4">
        <h3 class="font-semibold text-lg">
          Dish Depth Calculator
        </h3>
        <p class="text-sm opacity-80">
          Calculate the depth of dish for a given width and radius.
        </p>

        <div class="space-y-3">
          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Dish Width (inches)</span>
            <input
              v-model.number="calc.width"
              type="number"
              step="0.125"
              class="border p-2 rounded"
              placeholder="e.g., 16"
            >
          </label>

          <label class="flex flex-col">
            <span class="text-sm font-medium mb-1">Radius (feet)</span>
            <select
              v-model.number="calc.radius"
              class="border p-2 rounded"
            >
              <option :value="15">15 ft (4572 mm)</option>
              <option :value="25">25 ft (7620 mm)</option>
              <option :value="12">12 ft (3658 mm) - Custom</option>
              <option :value="20">20 ft (6096 mm) - Custom</option>
            </select>
          </label>

          <button
            class="w-full px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            @click="calculateDepth"
          >
            Calculate Depth
          </button>
        </div>
      </div>

      <div class="space-y-2">
        <h3 class="font-semibold text-lg">
          Results
        </h3>
        <div
          v-if="calcResult"
          class="p-4 bg-gray-50 rounded space-y-2"
        >
          <div>
            <strong>Dish Width:</strong> {{ calcResult.width_in }} inches ({{ calcResult.width_mm }} mm)
          </div>
          <div>
            <strong>Radius:</strong> {{ calcResult.radius_ft }} feet ({{ calcResult.radius_mm }} mm)
          </div>
          <div class="text-lg font-bold text-blue-600">
            <strong>Dish Depth:</strong> {{ calcResult.depth_in }} inches ({{ calcResult.depth_mm }} mm)
          </div>
          <div class="text-sm opacity-70 mt-3">
            <strong>Formula:</strong> depth = R - sqrt(R^2 - (W/2)^2)
            <br>
            Where R = radius, W = width
          </div>
        </div>
        <div
          v-else
          class="p-4 bg-gray-50 rounded text-sm opacity-70"
        >
          Enter values and click Calculate to see results.
        </div>
      </div>
    </div>
  </div>
</template>
