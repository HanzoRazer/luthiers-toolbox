<script setup lang="ts">
/**
 * VariantStatusBadge.vue
 *
 * Visual badge for variant triage status (NEW/REVIEWED/PROMOTED/REJECTED)
 * with integrated risk dot indicator.
 */
type VariantStatus = "NEW" | "REVIEWED" | "PROMOTED" | "REJECTED";

const props = defineProps<{
  status: VariantStatus;
  risk?: "GREEN" | "YELLOW" | "RED" | "UNKNOWN" | "ERROR" | null;
}>();

function label() {
  return props.status;
}

function cls() {
  const s = props.status;
  if (s === "PROMOTED") return "badge promoted";
  if (s === "REJECTED") return "badge rejected";
  if (s === "REVIEWED") return "badge reviewed";
  return "badge new";
}

function riskDotCls() {
  const r = props.risk ?? "UNKNOWN";
  if (r === "RED") return "dot red";
  if (r === "YELLOW") return "dot yellow";
  if (r === "GREEN") return "dot green";
  return "dot unknown";
}
</script>

<template>
  <span :class="cls()">
    <span :class="riskDotCls()" aria-hidden="true"></span>
    {{ label() }}
  </span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.18);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}
.badge.new {
  background: rgba(0, 0, 0, 0.02);
}
.badge.reviewed {
  background: rgba(66, 133, 244, 0.1);
}
.badge.promoted {
  background: rgba(52, 168, 83, 0.12);
}
.badge.rejected {
  background: rgba(0, 0, 0, 0.06);
  opacity: 0.85;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.2);
}
.dot.green {
  background: rgba(52, 168, 83, 0.9);
}
.dot.yellow {
  background: rgba(251, 188, 5, 0.9);
}
.dot.red {
  background: rgba(234, 67, 53, 0.9);
}
.dot.unknown {
  background: rgba(0, 0, 0, 0.25);
}
</style>
