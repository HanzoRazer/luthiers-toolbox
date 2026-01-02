<template>
  <span
    class="confidence-badge"
    :style="{ backgroundColor: bgColor, color: textColor }"
    :title="tooltip"
  >
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  type ConfidenceLevel,
  computeDesignConfidence,
  confidenceColor,
  confidenceLabel,
} from "@/utils/designConfidence";

const props = defineProps<{
  feasibility?: any;
  level?: ConfidenceLevel;
  tooltip?: string;
}>();

const effectiveLevel = computed<ConfidenceLevel>(() => {
  if (props.level) return props.level;
  return computeDesignConfidence(props.feasibility ?? null);
});

const bgColor = computed(() => confidenceColor(effectiveLevel.value));
const label = computed(() => confidenceLabel(effectiveLevel.value));
const textColor = computed(() => (effectiveLevel.value === "medium" ? "#000" : "#fff"));
</script>

<style scoped>
.confidence-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>
