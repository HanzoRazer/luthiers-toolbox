<template>
  <section class="workflow-section phase-3">
    <div class="section-header">
      <h2>
        <span class="step-number">3</span>
        Send to CAM Pipeline (GRBL)
      </h2>
    </div>

    <!-- CAM Parameters -->
    <CamParametersCard
      :cam-params="camParams"
      :is-sending-to-c-a-m="isSendingToCAM"
      @send-to-cam="emit('send-to-cam')"
      @update:cam-params="emit('update:camParams', $event)"
    />

    <!-- RMOS Result -->
    <CamResultsCard
      v-if="rmosResult"
      :rmos-result="rmosResult"
      :gcode-ready="gcodeReady"
      @download-gcode="emit('download-gcode')"
    />
  </section>
</template>

<script setup lang="ts">
import type { CamParams, RmosResult } from "@/composables/useBlueprintWorkflow";
import { CamParametersCard, CamResultsCard } from "./phase3-cam";

defineProps<{
  camParams: CamParams;
  rmosResult: RmosResult | null;
  isSendingToCAM: boolean;
  gcodeReady: boolean;
}>();

const emit = defineEmits<{
  "send-to-cam": [];
  "download-gcode": [];
  "update:camParams": [params: CamParams];
}>();
</script>

<style scoped>
.workflow-section {
  border: 2px solid #e5e7eb;
  border-radius: 1rem;
  padding: 1.5rem;
  background: white;
}

.workflow-section.phase-3 {
  border-color: #f59e0b;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  font-size: 1.25rem;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f59e0b;
  color: white;
  font-weight: bold;
  font-size: 1rem;
}
</style>
