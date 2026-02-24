<template>
  <div class="border rounded bg-white p-2 mb-2">
    <div class="text-[10px] font-semibold text-gray-900 mb-1.5">
      Risk Overview
    </div>
    <div class="grid grid-cols-2 gap-2 text-[9px]">
      <div>
        <div class="text-gray-600">
          Total
        </div>
        <div class="font-semibold text-gray-900">
          {{ total }}
        </div>
      </div>
      <div>
        <div class="text-gray-600">
          Avg Risk
        </div>
        <div
          class="font-semibold"
          :class="riskTextClass(averageRisk)"
        >
          {{ averageRisk.toFixed(1) }}%
        </div>
      </div>
      <div>
        <div class="text-green-700">
          Low (&lt;40%)
        </div>
        <div class="font-semibold text-green-800">
          {{ lowRiskCount }}
        </div>
      </div>
      <div>
        <div class="text-yellow-700">
          Med (40-70%)
        </div>
        <div class="font-semibold text-yellow-800">
          {{ mediumRiskCount }}
        </div>
      </div>
      <div class="col-span-2">
        <div class="text-red-700">
          High (&gt;70%)
        </div>
        <div class="font-semibold text-red-800">
          {{ highRiskCount }}
        </div>
      </div>
    </div>

    <!-- Risk distribution bar -->
    <div class="mt-2 flex h-2 rounded overflow-hidden">
      <div
        v-if="lowRiskCount > 0"
        class="bg-green-500"
        :style="{ width: `${(lowRiskCount / total) * 100}%` }"
      />
      <div
        v-if="mediumRiskCount > 0"
        class="bg-yellow-500"
        :style="{ width: `${(mediumRiskCount / total) * 100}%` }"
      />
      <div
        v-if="highRiskCount > 0"
        class="bg-red-500"
        :style="{ width: `${(highRiskCount / total) * 100}%` }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  total: number
  averageRisk: number
  lowRiskCount: number
  mediumRiskCount: number
  highRiskCount: number
}>()

function riskTextClass(score: number): string {
  if (score >= 70) return "text-red-700";
  if (score >= 40) return "text-yellow-700";
  return "text-green-700";
}
</script>
