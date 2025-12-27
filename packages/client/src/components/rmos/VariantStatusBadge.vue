<script setup lang="ts">
/**
 * VariantStatusBadge.vue
 *
 * Visual badge for variant triage status (NEW/REVIEWED/PROMOTED/REJECTED).
 * Part of the Variant Status & Filters UX bundle.
 */

type VariantStatus = "NEW" | "REVIEWED" | "PROMOTED" | "REJECTED";

const props = defineProps<{
  status: VariantStatus;
  small?: boolean;
}>();

const statusConfig: Record<VariantStatus, { label: string; cssClass: string }> = {
  NEW: { label: "New", cssClass: "status-new" },
  REVIEWED: { label: "Reviewed", cssClass: "status-reviewed" },
  PROMOTED: { label: "Promoted", cssClass: "status-promoted" },
  REJECTED: { label: "Rejected", cssClass: "status-rejected" },
};

const config = computed(() => statusConfig[props.status] ?? statusConfig.NEW);

import { computed } from "vue";
</script>

<template>
  <span
    class="variant-status-badge"
    :class="[config.cssClass, { small }]"
    :title="`Status: ${config.label}`"
  >
    {{ config.label }}
  </span>
</template>

<style scoped>
.variant-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.variant-status-badge.small {
  padding: 1px 6px;
  font-size: 0.65rem;
}

/* NEW: Outline style (unreviewed) */
.status-new {
  background: transparent;
  border: 1.5px solid #6c757d;
  color: #6c757d;
}

/* REVIEWED: Blue solid (has rating/notes) */
.status-reviewed {
  background: #cfe2ff;
  border: 1px solid #9ec5fe;
  color: #084298;
}

/* PROMOTED: Green solid (manufacturing candidate) */
.status-promoted {
  background: #d1e7dd;
  border: 1px solid #a3cfbb;
  color: #0f5132;
}

/* REJECTED: Gray solid (explicitly rejected) */
.status-rejected {
  background: #e9ecef;
  border: 1px solid #ced4da;
  color: #6c757d;
  text-decoration: line-through;
}
</style>
