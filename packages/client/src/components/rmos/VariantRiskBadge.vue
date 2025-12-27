<script setup lang="ts">
/**
 * VariantRiskBadge.vue
 *
 * Visual indicator for variant risk level (GREEN/YELLOW/RED).
 * Part of the Variant Status & Filters UX bundle.
 */

type RiskLevel = "GREEN" | "YELLOW" | "RED";

const props = defineProps<{
  risk: RiskLevel;
  showLabel?: boolean;
  small?: boolean;
}>();

const riskConfig: Record<RiskLevel, { label: string; icon: string; cssClass: string }> = {
  GREEN: { label: "Safe", icon: "✓", cssClass: "risk-green" },
  YELLOW: { label: "Caution", icon: "⚠", cssClass: "risk-yellow" },
  RED: { label: "Blocked", icon: "✕", cssClass: "risk-red" },
};

const config = computed(() => riskConfig[props.risk] ?? riskConfig.GREEN);

import { computed } from "vue";
</script>

<template>
  <span
    class="variant-risk-badge"
    :class="[config.cssClass, { small, 'with-label': showLabel }]"
    :title="`Risk: ${config.label}`"
  >
    <span class="icon">{{ config.icon }}</span>
    <span v-if="showLabel" class="label">{{ config.label }}</span>
  </span>
</template>

<style scoped>
.variant-risk-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.variant-risk-badge.small {
  padding: 1px 4px;
  font-size: 0.65rem;
}

.variant-risk-badge.with-label {
  padding: 2px 8px;
}

.icon {
  font-size: 0.85em;
}

.label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

/* GREEN: Safe */
.risk-green {
  background: #d1e7dd;
  color: #0f5132;
}

/* YELLOW: Caution / needs attention */
.risk-yellow {
  background: #fff3cd;
  color: #856404;
}

/* RED: Blocked / critical issue */
.risk-red {
  background: #f8d7da;
  color: #842029;
}
</style>
