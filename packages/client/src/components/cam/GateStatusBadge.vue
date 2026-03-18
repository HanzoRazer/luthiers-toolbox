<script setup lang="ts">
/**
 * GateStatusBadge — CAM gate status (GREEN / YELLOW / RED / null).
 * Emits 'override' when user acknowledges a YELLOW warning.
 */
defineProps<{
  risk: 'GREEN' | 'YELLOW' | 'RED' | null;
  errors: string[];
  warnings: string[];
}>();

const emit = defineEmits<{ override: [] }>();
</script>

<template>
  <div
    class="gate-badge"
    :class="{
      green: risk === 'GREEN',
      yellow: risk === 'YELLOW',
      red: risk === 'RED',
      grey: risk === null,
    }"
  >
    <template v-if="risk === 'GREEN'">
      <span class="icon" aria-hidden="true">✓</span>
      <span>Ready to generate</span>
    </template>
    <template v-else-if="risk === 'YELLOW'">
      <span class="icon" aria-hidden="true">⚠</span>
      <ul v-if="warnings.length" class="list">
        <li v-for="(w, i) in warnings" :key="i">{{ w }}</li>
      </ul>
      <button type="button" class="override-btn" @click="emit('override')">
        Acknowledge & continue
      </button>
    </template>
    <template v-else-if="risk === 'RED'">
      <span class="icon" aria-hidden="true">⊘</span>
      <ul v-if="errors.length" class="list">
        <li v-for="(e, i) in errors" :key="i">{{ e }}</li>
      </ul>
    </template>
    <template v-else>
      <span class="icon" aria-hidden="true">○</span>
      <span>Configure parameters above</span>
    </template>
  </div>
</template>

<style scoped>
.gate-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
}
.gate-badge.green {
  background: #dcfce7;
  color: #166534;
}
.gate-badge.yellow {
  background: #fef3c7;
  color: #92400e;
  flex-wrap: wrap;
}
.gate-badge.red {
  background: #fee2e2;
  color: #991b1b;
}
.gate-badge.grey {
  background: #f1f5f9;
  color: #64748b;
}
.icon {
  font-weight: bold;
}
.list {
  margin: 0.25rem 0 0 0;
  padding-left: 1rem;
  width: 100%;
}
.override-btn {
  margin-top: 0.25rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  cursor: pointer;
}
</style>
