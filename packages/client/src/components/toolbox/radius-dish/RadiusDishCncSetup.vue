<script setup lang="ts">
/**
 * RadiusDishCncSetup.vue - CNC Setup tab content
 * Extracted from RadiusDishDesigner.vue
 */
defineProps<{
  selectedRadius: '15ft' | '25ft'
}>()

const emit = defineEmits<{
  'download-gcode': []
}>()
</script>

<template>
  <div class="space-y-4">
    <h3 class="font-semibold text-lg">
      CNC Machining Instructions
    </h3>

    <div class="space-y-3">
      <div class="p-4 border rounded">
        <h4 class="font-medium mb-2">
          1. Material Setup
        </h4>
        <ul class="list-disc list-inside text-sm space-y-1 opacity-80">
          <li>Mount blank securely to spoilboard with screws or T-track clamps</li>
          <li>Ensure material is flat and level</li>
          <li>Set Z-zero to top surface of workpiece</li>
        </ul>
      </div>

      <div class="p-4 border rounded">
        <h4 class="font-medium mb-2">
          2. Tool Selection
        </h4>
        <ul class="list-disc list-inside text-sm space-y-1 opacity-80">
          <li>Bit: 1/2" or 3/4" ball nose router bit</li>
          <li>Speed: 12,000-18,000 RPM (depending on material)</li>
          <li>Feed Rate: 60-100 inches/min for softwoods, 40-60 for hardwoods</li>
          <li>DOC (Depth of Cut): 0.060" to 0.125" per pass</li>
        </ul>
      </div>

      <div class="p-4 border rounded">
        <h4 class="font-medium mb-2">
          3. G-code Configuration
        </h4>
        <ul class="list-disc list-inside text-sm space-y-1 opacity-80">
          <li>Machine: GRBL-compatible (Arduino-based CNC)</li>
          <li>Units: Inches (G20)</li>
          <li>Work Coordinate System: G54</li>
          <li>Included files: Pre-generated toolpaths for 15ft and 25ft radius</li>
        </ul>
      </div>

      <div class="p-4 border rounded bg-yellow-50">
        <h4 class="font-medium mb-2">
          Safety Notes
        </h4>
        <ul class="list-disc list-inside text-sm space-y-1">
          <li>Always run air cuts first (Z above workpiece) to verify toolpath</li>
          <li>Use dust collection - routing generates significant dust</li>
          <li>Secure material properly - it will vibrate during routing</li>
          <li>Check bit sharpness - dull bits cause tearout in figured wood</li>
        </ul>
      </div>
    </div>

    <div class="mt-4">
      <button
        class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 transition-colors"
        @click="emit('download-gcode')"
      >
        Download G-code ({{ selectedRadius }})
      </button>
    </div>
  </div>
</template>
