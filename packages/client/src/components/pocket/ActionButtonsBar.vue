<script setup lang="ts">
/**
 * ActionButtonsBar.vue - Main action buttons for pocket planning
 *
 * Plan, Preview NC, Compare modes, Export G-code buttons.
 *
 * Example:
 * ```vue
 * <ActionButtonsBar
 *   :has-moves="moves.length > 0"
 *   :job-name="jobName"
 *   @plan="plan"
 *   @preview-nc="previewNc"
 *   @compare="openCompare"
 *   @export="exportProgram"
 * />
 * ```
 */

import CompareModeButton from "@/components/compare/CompareModeButton.vue";

defineProps<{
  hasMoves: boolean;
  jobName: string;
}>();

defineEmits<{
  plan: [];
  previewNc: [];
  compare: [];
  export: [];
}>();
</script>

<template>
  <div class="flex gap-2 pt-2 flex-wrap">
    <button
      class="px-3 py-1 border rounded bg-blue-50"
      @click="$emit('plan')"
    >
      Plan
    </button>
    <button
      class="px-3 py-1 border rounded bg-purple-50"
      :disabled="!hasMoves"
      @click="$emit('previewNc')"
    >
      Preview NC
    </button>
    <button
      class="px-3 py-1 border rounded"
      :disabled="!hasMoves"
      aria-label="Open compare modes"
      @click="$emit('compare')"
    >
      Compare modes
    </button>
    <CompareModeButton
      v-if="hasMoves"
      :baseline-id="jobName || 'baseline'"
      :candidate-id="'candidate'"
      class="ml-2"
      aria-label="Go to Compare Lab"
    >
      Compare in Lab
    </CompareModeButton>
    <button
      class="px-3 py-1 border rounded bg-green-50"
      :disabled="!hasMoves"
      aria-label="Export G-code"
      @click="$emit('export')"
    >
      Export G-code
    </button>
  </div>
</template>
