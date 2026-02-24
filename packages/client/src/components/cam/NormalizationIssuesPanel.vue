<script setup lang="ts">
/**
 * NormalizationIssuesPanel - CAM intent normalization issues display
 * Extracted from CamPipelineRunner.vue
 */
import type { NormalizationEntry } from './composables/camPipelineTypes'

defineProps<{
  issues: NormalizationEntry[]
}>()
</script>

<template>
  <details
    v-if="issues.length"
    class="mt-2 text-xs"
  >
    <summary class="cursor-pointer text-amber-700 hover:underline">
      CAM intent normalization issues ({{ issues.length }})
    </summary>
    <div class="mt-2 space-y-2">
      <div
        v-for="(entry, idx) in issues.slice(0, 50)"
        :key="idx"
        class="p-2 border border-amber-200 rounded-lg bg-amber-50"
      >
        <div class="font-semibold text-[11px] text-amber-800">
          {{ entry.path }}
        </div>
        <ul class="mt-1 ml-4 list-disc text-[11px] text-amber-700">
          <li
            v-for="(iss, j) in entry.issues"
            :key="j"
          >
            <span
              v-if="iss.code"
              class="font-mono"
            >[{{ iss.code }}]</span>
            {{ iss.message }}
            <span
              v-if="iss.path"
              class="opacity-70"
            > ({{ iss.path }})</span>
          </li>
        </ul>
      </div>
      <div
        v-if="issues.length > 50"
        class="text-[11px] text-gray-500"
      >
        Showing first 50 issue groups...
      </div>
    </div>
  </details>
</template>
