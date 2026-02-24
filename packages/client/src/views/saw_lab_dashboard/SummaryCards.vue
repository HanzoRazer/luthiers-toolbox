<template>
  <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
    <div class="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
      <div class="text-sm text-gray-600 mb-1">
        Total Runs
      </div>
      <div class="text-2xl font-bold text-gray-900">
        {{ totalRuns }}
      </div>
    </div>

    <div class="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
      <div class="text-sm text-gray-600 mb-1">
        Green (Safe)
      </div>
      <div class="text-2xl font-bold text-green-700">
        {{ riskCounts.green }}
      </div>
    </div>

    <div class="bg-white rounded-lg shadow p-4 border-l-4 border-amber-500">
      <div class="text-sm text-gray-600 mb-1">
        Yellow + Orange
      </div>
      <div class="text-2xl font-bold text-amber-700">
        {{ riskCounts.yellow + riskCounts.orange }}
      </div>
    </div>

    <div class="bg-white rounded-lg shadow p-4 border-l-4 border-rose-500">
      <div class="text-sm text-gray-600 mb-1">
        Red (Danger)
      </div>
      <div class="text-2xl font-bold text-rose-700">
        {{ riskCounts.red }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  totalRuns: number
  riskCounts: {
    green: number
    yellow: number
    orange: number
    red: number
  }
}>()
</script>
