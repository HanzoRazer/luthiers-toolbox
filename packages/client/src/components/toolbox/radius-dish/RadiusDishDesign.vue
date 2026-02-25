<script setup lang="ts">
/**
 * RadiusDishDesign.vue - Design tab content
 * Extracted from RadiusDishDesigner.vue
 */
defineProps<{
  selectedRadius: '15ft' | '25ft'
}>()

const emit = defineEmits<{
  'update:selectedRadius': [value: '15ft' | '25ft']
  'download-dxf': []
  'download-gcode': []
  'view-svg': []
}>()
</script>

<template>
  <div class="space-y-4">
    <div class="grid md:grid-cols-2 gap-4">
      <div class="space-y-2">
        <h3 class="font-semibold text-lg">
          Radius Selection
        </h3>
        <p class="text-sm opacity-80">
          Choose radius for archtop guitar tops/backs. 15ft (4572mm) is more curved, 25ft (7620mm) is flatter.
        </p>

        <div class="space-y-2">
          <label class="flex items-center gap-2">
            <input
              :checked="selectedRadius === '15ft'"
              type="radio"
              value="15ft"
              class="form-radio"
              @change="emit('update:selectedRadius', '15ft')"
            >
            <span>15 ft (4572 mm) - Traditional Archtop</span>
          </label>
          <label class="flex items-center gap-2">
            <input
              :checked="selectedRadius === '25ft'"
              type="radio"
              value="25ft"
              class="form-radio"
              @change="emit('update:selectedRadius', '25ft')"
            >
            <span>25 ft (7620 mm) - Shallow Arch</span>
          </label>
        </div>

        <div class="mt-4 p-4 bg-gray-50 rounded">
          <h4 class="font-medium mb-2">
            Current Selection:
          </h4>
          <p><strong>Radius:</strong> {{ selectedRadius === '15ft' ? '15 feet (4572 mm)' : '25 feet (7620 mm)' }}</p>
          <p class="text-sm opacity-70 mt-1">
            {{ selectedRadius === '15ft'
              ? 'Deeper arch - classic carved-top sound with more projection'
              : 'Shallow arch - balanced tone with easier construction' }}
          </p>
        </div>
      </div>

      <div class="space-y-2">
        <h3 class="font-semibold text-lg">
          Preview
        </h3>
        <div
          class="border rounded p-4 bg-white"
          style="min-height: 300px;"
        >
          <img
            :src="`/radius_dish/Radius_Arc_${selectedRadius}.svg`"
            :alt="`Radius Arc ${selectedRadius}`"
            class="w-full h-auto"
            style="max-height: 400px; object-fit: contain;"
          >
        </div>
      </div>
    </div>

    <div class="flex gap-2 flex-wrap">
      <button
        class="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        @click="emit('download-dxf')"
      >
        Download DXF for CAM
      </button>
      <button
        class="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 transition-colors"
        @click="emit('download-gcode')"
      >
        Download G-code (GRBL)
      </button>
      <button
        class="px-4 py-2 rounded border hover:bg-gray-50 transition-colors"
        @click="emit('view-svg')"
      >
        View SVG in Gallery
      </button>
    </div>
  </div>
</template>
