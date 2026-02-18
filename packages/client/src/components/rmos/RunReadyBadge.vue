<script setup lang="ts">
/**
 * RunReadyBadge - Visual indicator for manufacturing run readiness
 * Extracted from ManufacturingCandidateList.vue
 */
import { computed } from 'vue'

type RunReadyStatus = 'READY' | 'BLOCKED' | 'EMPTY'

const props = defineProps<{
  status: RunReadyStatus
  hoverText: string
  loading?: boolean
}>()

const label = computed(() => {
  if (props.loading) return 'LOADING…'
  if (props.status === 'READY') return 'RUN READY'
  if (props.status === 'EMPTY') return 'NO CANDIDATES'
  return 'RUN BLOCKED'
})

const badgeClass = computed(() => ({
  'badge': true,
  'badge-ready': props.status === 'READY',
  'badge-blocked': props.status === 'BLOCKED',
  'badge-empty': props.status === 'EMPTY',
  'badge-loading': props.loading,
}))
</script>

<template>
  <span
    :class="badgeClass"
    :title="hoverText"
  >
    {{ label }}
  </span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  cursor: help;
}

.badge-ready {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}

.badge-blocked {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.badge-empty {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.badge-loading {
  background: #e0e7ff;
  color: #4338ca;
  border: 1px solid #a5b4fc;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
