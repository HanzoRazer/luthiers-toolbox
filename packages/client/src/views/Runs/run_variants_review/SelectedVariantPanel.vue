<template>
  <div
    v-if="advisoryId"
    class="panel"
  >
    <!-- Streamlined Quick Actions Panel -->
    <QuickActionsPanel
      :run-id="runId"
      :advisory-id="advisoryId"
      :variant-status="variantStatus"
      :risk-level="riskLevel"
      @done="$emit('refresh')"
      @close="$emit('refresh')"
    />

    <div class="spacer" />
    <PromptLineageViewer
      :run-id="runId"
      :advisory-id="advisoryId"
      api-base="/api/rmos"
    />
  </div>
</template>

<script setup lang="ts">
import QuickActionsPanel from "@/components/rmos/QuickActionsPanel.vue";
import PromptLineageViewer from "@/components/rmos/PromptLineageViewer.vue";

defineProps<{
  runId: string
  advisoryId: string | null
  isRejected?: boolean
  variantStatus?: string
  riskLevel?: string
}>()

defineEmits<{
  refresh: []
}>()
</script>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.spacer {
  height: 8px;
}
</style>
