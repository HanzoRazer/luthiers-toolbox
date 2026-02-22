<template>
  <div class="flex flex-wrap items-center gap-4 text-[10px] text-gray-600">
    <div
      v-for="preset in presetSparklines"
      :key="preset.name"
      class="flex items-center gap-2"
    >
      <span class="font-semibold">{{ preset.name }}</span>
      <svg
        :width="sparkWidth"
        :height="sparkHeight"
        viewBox="0 0 60 20"
      >
        <polyline
          v-if="preset.addedPath"
          :points="preset.addedPath"
          fill="none"
          stroke="#22c55e"
          stroke-width="1.2"
        />
      </svg>
      <svg
        :width="sparkWidth"
        :height="sparkHeight"
        viewBox="0 0 60 20"
      >
        <polyline
          v-if="preset.removedPath"
          :points="preset.removedPath"
          fill="none"
          stroke="#ef4444"
          stroke-width="1.2"
        />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
interface PresetSparkline {
  name: string
  addedPath: string
  removedPath: string
}

defineProps<{
  sparkWidth: number
  sparkHeight: number
  presetSparklines: PresetSparkline[]
}>()
</script>
