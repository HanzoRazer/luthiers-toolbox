<script setup lang="ts">
/**
 * EventMetadataDisplay - Display fragility badge, materials, and lane hint
 * Extracted from LiveMonitor.vue
 */
import type { FragilityBand } from '@/models/live_monitor'
import { fragilityBadgeClass, fragilityLabel, fragilityTitle } from '@/models/live_monitor'

interface EventData {
  fragility_band?: FragilityBand
  worst_fragility_score?: number
  materials?: string[]
  lane_hint?: string
}

defineProps<{
  data: EventData
}>()
</script>

<template>
  <div class="event-metadata">
    <span
      v-if="data.fragility_band"
      class="fragility-badge"
      :class="fragilityBadgeClass(data.fragility_band)"
      :title="fragilityTitle(data.fragility_band, data.worst_fragility_score)"
    >
      {{ fragilityLabel(data.fragility_band) }}
      <span
        v-if="data.worst_fragility_score !== undefined"
        class="fragility-score"
      >
        {{ (data.worst_fragility_score * 100).toFixed(0) }}%
      </span>
    </span>
    <span
      v-if="data.materials && data.materials.length > 0"
      class="materials-list"
    >
      {{ data.materials.join(', ') }}
    </span>
    <span
      v-if="data.lane_hint"
      class="lane-hint"
    >
      Lane: {{ data.lane_hint }}
    </span>
  </div>
</template>

<style scoped>
.event-metadata {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.fragility-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.fragility-stable {
  background: #d1fae5;
  color: #065f46;
}

.fragility-medium {
  background: #fef3c7;
  color: #92400e;
}

.fragility-fragile {
  background: #fee2e2;
  color: #991b1b;
}

.fragility-unknown {
  background: #e5e7eb;
  color: #6b7280;
}

.fragility-score {
  font-weight: 900;
  margin-left: 0.125rem;
}

.materials-list {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: #f3f4f6;
  color: #374151;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}

.lane-hint {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
}
</style>
