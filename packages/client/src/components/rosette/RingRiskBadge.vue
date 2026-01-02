<script setup lang="ts">
type RingDiagLike = {
  risk_bucket?: string;
  riskBucket?: string;
  warnings?: string[];
};

const props = defineProps<{
  diag?: RingDiagLike | null;
}>();

function riskOf() {
  return props.diag?.risk_bucket ?? props.diag?.riskBucket ?? "UNKNOWN";
}

function warnCount() {
  return props.diag?.warnings?.length ?? 0;
}
</script>

<template>
  <span v-if="diag" class="badge" :class="riskOf().toLowerCase()">
    {{ riskOf() }}
    <span v-if="warnCount() > 0" class="warn-count">&bull; {{ warnCount() }}</span>
  </span>
</template>

<style scoped>
.badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 999px;
  border: 1px solid transparent;
  white-space: nowrap;
}
.badge.green {
  background: #e6f7f1;
  color: #0b6;
  border-color: #bfeadd;
}
.badge.yellow {
  background: #fff6db;
  color: #b08900;
  border-color: #ffe3a3;
}
.badge.red {
  background: #fdeaea;
  color: #a00;
  border-color: #f3bcbc;
}
.badge.unknown {
  background: #f5f5f5;
  color: #666;
  border-color: #ddd;
}
.warn-count {
  font-weight: 600;
  margin-left: 4px;
}
</style>
