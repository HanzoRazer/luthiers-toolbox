<script setup lang="ts">
/**
 * AttachActionSection - Final attach action with summary
 * Extracted from VisionAttachToRunWidget.vue
 */

defineProps<{
  selectedAssetSha: string | null
  selectedRunId: string | null
  canAttach: boolean
  isAttaching: boolean
  showGoToReview: boolean
  lastAttachedRunId: string | null
  styles: Record<string, string>
}>()

const emit = defineEmits<{
  'attach': []
  'go-to-review': [runId: string]
}>()
</script>

<template>
  <section :class="styles.actionSection">
    <h4>4. Attach</h4>
    <div :class="styles.attachSummary">
      <div :class="styles.summaryItem">
        <span :class="styles.summaryItemLabel">Asset:</span>
        <span :class="styles.summaryItemValue">{{ selectedAssetSha?.slice(0, 12) }}...</span>
      </div>
      <div :class="styles.summaryItem">
        <span :class="styles.summaryItemLabel">Run:</span>
        <span :class="styles.summaryItemValue">{{ selectedRunId?.slice(0, 12) }}...</span>
      </div>
    </div>
    <button
      :class="styles.attachBtn"
      :disabled="!canAttach"
      @click="emit('attach')"
    >
      <span v-if="isAttaching">Attaching...</span>
      <span v-else>Attach &amp; Review</span>
    </button>
    <div
      v-if="showGoToReview && lastAttachedRunId"
      :class="styles.successActions"
    >
      <button
        :class="styles.btn"
        type="button"
        @click="emit('go-to-review', lastAttachedRunId)"
      >
        Go to Review
      </button>
    </div>
  </section>
</template>
