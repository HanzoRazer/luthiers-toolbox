<script setup lang="ts">
/**
 * RiskBadge.vue - Consistent risk level badge across all RMOS views
 *
 * Props:
 * - level: GREEN | YELLOW | RED | UNKNOWN
 * - showIcon: boolean (default true)
 * - size: 'sm' | 'md' | 'lg' (default 'md')
 *
 * Tooltips are semantic and deterministic (no AI):
 * - GREEN: "Safe to run under current parameters"
 * - YELLOW: "Review warnings before running"
 * - RED: "Blocked — parameters must change"
 */

type RiskLevel = 'GREEN' | 'YELLOW' | 'RED' | 'UNKNOWN' | string

const props = withDefaults(defineProps<{
  level?: RiskLevel | null
  showIcon?: boolean
  size?: 'sm' | 'md' | 'lg'
}>(), {
  level: 'UNKNOWN',
  showIcon: true,
  size: 'md',
})

const TOOLTIPS: Record<string, string> = {
  GREEN: 'Safe to run under current parameters',
  YELLOW: 'Review warnings before running',
  RED: 'Blocked — parameters must change',
  UNKNOWN: 'Risk level not determined',
}

const ICONS: Record<string, string> = {
  GREEN: '✓',
  YELLOW: '⚠',
  RED: '⛔',
  UNKNOWN: '?',
}

function normalized(): string {
  return (props.level || 'UNKNOWN').toUpperCase()
}

function tooltip(): string {
  return TOOLTIPS[normalized()] || TOOLTIPS.UNKNOWN
}

function icon(): string {
  return ICONS[normalized()] || ICONS.UNKNOWN
}
</script>

<template>
  <span
    class="risk-badge"
    :class="[normalized().toLowerCase(), size]"
    :title="tooltip()"
    role="status"
  >
    <span
      v-if="showIcon"
      class="icon"
      aria-hidden="true"
    >{{ icon() }}</span>
    <span class="label">{{ normalized() }}</span>
  </span>
</template>

<style scoped>
.risk-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 700;
  border-radius: 9999px;
  cursor: help;
  white-space: nowrap;
}

/* Sizes */
.risk-badge.sm {
  font-size: 0.625rem;
  padding: 0.125rem 0.5rem;
}
.risk-badge.md {
  font-size: 0.75rem;
  padding: 0.25rem 0.625rem;
}
.risk-badge.lg {
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
}

/* Colors - theme-independent, high contrast */
.risk-badge.green {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #10b981;
}
.risk-badge.yellow {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #f59e0b;
}
.risk-badge.red {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #ef4444;
}
.risk-badge.unknown {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.icon {
  font-size: 0.875em;
}
</style>
