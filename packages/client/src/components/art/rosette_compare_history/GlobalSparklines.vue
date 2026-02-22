<template>
  <div class="flex items-center gap-2 text-[10px] text-gray-600">
    <div class="flex items-center gap-1">
      <svg
        :width="sparkWidth"
        :height="sparkHeight"
        viewBox="0 0 60 20"
      >
        <polyline
          v-if="addedSparkPath"
          :points="addedSparkPath"
          fill="none"
          stroke="#22c55e"
          stroke-width="1.2"
        />
      </svg>
      <span>Added trend</span>
    </div>
    <div class="flex items-center gap-1">
      <svg
        :width="sparkWidth"
        :height="sparkHeight"
        viewBox="0 0 60 20"
      >
        <polyline
          v-if="removedSparkPath"
          :points="removedSparkPath"
          fill="none"
          stroke="#ef4444"
          stroke-width="1.2"
        />
      </svg>
      <span>Removed trend</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  sparkWidth: number
  sparkHeight: number
  addedSparkPath: string
  removedSparkPath: string
}>()
</script>
