<template>
  <section class="workflow-section phase-2">
    <div class="section-header">
      <h2>
        <span class="step-number">2</span>
        Geometry Vectorization (OpenCV)
      </h2>
    </div>

    <!-- Pre-Vectorization Action Card -->
    <VectorizationControls
      v-if="!vectorizedGeometry"
      :vector-params="vectorParams"
      :is-vectorizing="isVectorizing"
      :use-phase3="usePhase3"
      :phase3-available="phase3Available"
      @vectorize="emit('vectorize')"
      @update:vector-params="emit('update:vectorParams', $event)"
      @update:use-phase3="emit('update:usePhase3', $event)"
      @check-phase3="emit('checkPhase3')"
    />

    <!-- Vectorization Results -->
    <VectorizationResults
      v-if="vectorizedGeometry"
      :vectorized-geometry="vectorizedGeometry"
      @download-svg="emit('download-svg')"
      @download-dxf="emit('download-dxf')"
      @re-vectorize="emit('re-vectorize')"
    />
  </section>
</template>

<script setup lang="ts">
import type { VectorParams, VectorizedGeometry } from "@/composables/useBlueprintWorkflow";
import { VectorizationControls, VectorizationResults } from "./phase2-vectorization";

defineProps<{
  vectorizedGeometry: VectorizedGeometry | null;
  vectorParams: VectorParams;
  isVectorizing: boolean;
  usePhase3?: boolean;
  phase3Available?: boolean | null;
}>();

const emit = defineEmits<{
  vectorize: [];
  "download-svg": [];
  "download-dxf": [];
  "re-vectorize": [];
  "update:vectorParams": [params: VectorParams];
  "update:usePhase3": [value: boolean];
  checkPhase3: [];
}>();
</script>

<style scoped>
.workflow-section {
  border: 2px solid #e5e7eb;
  border-radius: 1rem;
  padding: 1.5rem;
  background: white;
}

.workflow-section.phase-2 {
  border-color: #10b981;
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
  background: #10b981;
  color: white;
  font-weight: bold;
  font-size: 1rem;
}
</style>
