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
  confidenceColor,
  confidenceLabel,
} from "@/utils/designConfidence";

const props = defineProps<{
  level: ConfidenceLevel;
  tooltip?: string;
}>();

const bgColor = computed(() => confidenceColor(props.level));
const label = computed(() => confidenceLabel(props.level));
const textColor = computed(() => (props.level === "medium" ? "#000" : "#fff"));
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
