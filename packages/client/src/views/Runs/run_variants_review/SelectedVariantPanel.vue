<template>
  <div
    v-if="advisoryId"
    class="panel"
  >
    <div class="panel-title">
      Selected Variant
    </div>

    <div class="actions-inline">
      <PromoteToManufacturingButton
        :run-id="runId"
        :advisory-id="advisoryId"
        api-base="/api/rmos"
      />
      <RejectVariantButton
        :run-id="runId"
        :advisory-id="advisoryId"
        @rejected="$emit('refresh')"
      />
      <UndoRejectButton
        v-if="isRejected"
        :run-id="runId"
        :advisory-id="advisoryId"
        @cleared="$emit('refresh')"
      />
    </div>

    <div class="spacer" />
    <VariantNotes
      :run-id="runId"
      :advisory-id="advisoryId"
      api-base="/api/rmos"
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
import RejectVariantButton from "@/components/rmos/RejectVariantButton.vue";
import UndoRejectButton from "@/components/rmos/UndoRejectButton.vue";
import VariantNotes from "@/components/rmos/VariantNotes.vue";
import PromoteToManufacturingButton from "@/components/rmos/PromoteToManufacturingButton.vue";
import PromptLineageViewer from "@/components/rmos/PromptLineageViewer.vue";

defineProps<{
  runId: string
  advisoryId: string | null
  isRejected: boolean
}>()

defineEmits<{
  refresh: []
}>()
</script>

<style scoped>
.panel {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 10px;
  background: white;
}

.panel-title {
  font-weight: 800;
  margin-bottom: 8px;
}

.actions-inline {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.spacer {
  height: 10px;
}
</style>
