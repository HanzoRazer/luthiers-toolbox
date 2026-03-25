<script setup lang="ts">
/**
 * RadiusDishCncSetup.vue — CNC Setup tab
 *
 * Previously a static instruction card with no connection to parameters.
 * Now shows setup notes derived from the actual selected radius and tool.
 */
const props = defineProps<{
  selectedRadius: number      // feet
  ballNoseMm?: number
  stepoverMm?: number
  feedMmMin?: number
  spindleRpm?: number
}>()

const emit = defineEmits<{ 'download-gcode': [] }>()

// Derived notes
function stepoverPct(stepover: number, dia: number) {
  return dia > 0 ? Math.round((stepover / dia) * 100) : 0
}
</script>

<template>
  <div class="space-y-4">
    <h3 class="font-semibold text-lg">CNC machining setup</h3>

    <div class="grid md:grid-cols-2 gap-4">

      <div class="space-y-3">
        <div class="p-4 border rounded">
          <h4 class="font-medium mb-2">1. Material setup</h4>
          <ul class="list-disc list-inside text-sm space-y-1 opacity-80">
            <li>Mount blank securely to spoilboard with screws or T-track clamps</li>
            <li>Ensure material is flat and level — level dish baseline is everything</li>
            <li>Set Z-zero to top surface of workpiece at dish centre</li>
            <li>For {{ selectedRadius }}ft radius: blank should be at least
              {{ Math.round(selectedRadius * 304.8 / 1000 * 0.02 * 25.4) }}mm
              thicker than max depth</li>
          </ul>
        </div>

        <div class="p-4 border rounded">
          <h4 class="font-medium mb-2">2. Tool selection</h4>
          <ul class="list-disc list-inside text-sm space-y-1 opacity-80">
            <li>Ball nose required — flat end mills cannot produce a spherical surface</li>
            <li v-if="ballNoseMm">
              Current: {{ ballNoseMm }}mm ({{ (ballNoseMm / 25.4).toFixed(3) }}")
              ball nose
            </li>
            <li>Speed: {{ spindleRpm ? spindleRpm.toLocaleString() : '12,000–18,000' }} RPM</li>
            <li>Feed: {{ feedMmMin ? feedMmMin.toLocaleString() + ' mm/min' : '60–100 in/min' }}</li>
            <li v-if="stepoverMm && ballNoseMm">
              Stepover: {{ stepoverMm }}mm
              ({{ stepoverPct(stepoverMm, ballNoseMm) }}% of diameter)
            </li>
          </ul>
        </div>
      </div>

      <div class="space-y-3">
        <div class="p-4 border rounded">
          <h4 class="font-medium mb-2">3. G-code notes</h4>
          <ul class="list-disc list-inside text-sm space-y-1 opacity-80">
            <li>Machine: GRBL-compatible (BCAM 2030A compatible)</li>
            <li>Units: G21 (mm) — change to G20 in options for inches</li>
            <li>Work coordinate system: G54</li>
            <li>Toolpath: raster X rows, Z follows sphere equation at each point</li>
            <li>Roughing + finishing in single file — comment sections marked</li>
          </ul>
        </div>

        <div class="p-4 bg-yellow-50 border border-yellow-200 rounded">
          <h4 class="font-medium mb-2">Safety</h4>
          <ul class="list-disc list-inside text-sm space-y-1">
            <li>Run air cut first (raise Z 20mm) to verify toolpath extent</li>
            <li>Confirm dish width/length before cutting — blank must be larger</li>
            <li>Use dust collection — routing dish generates volume of dust</li>
            <li>Check bit sharpness before each session</li>
          </ul>
        </div>
      </div>

    </div>

    <div class="mt-4">
      <button
        class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 transition-colors"
        @click="emit('download-gcode')"
      >
        Download G-code ({{ selectedRadius }}ft)
      </button>
    </div>
  </div>
</template>
