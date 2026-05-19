<script setup lang="ts">
/**
 * ApertureResultCard — Shared result card for aperture geometry display
 *
 * Dev Order 12: Shared component for displaying normalized aperture geometry.
 * Used by StandardAperturePanel, ApertureComparisonPanel, and future aperture tools.
 */
import { computed } from 'vue'
import { GateBadge } from '@/components/shared/workflow'

export interface ApertureGeometry {
  aperture_type: string
  area_mm2: number
  perimeter_mm: number
  equivalent_diameter_mm: number
  characteristic_width_mm?: number | null
  path_length_mm?: number | null
  pa_ratio_mm_inv?: number | null
}

interface Props {
  title: string
  geometry: ApertureGeometry | null
  gate?: 'green' | 'yellow' | 'red'
  notes?: string[]
  loading?: boolean
  error?: string
}

const props = withDefaults(defineProps<Props>(), {
  gate: 'green',
  notes: () => [],
  loading: false,
  error: '',
})

const typeLabel = computed(() => {
  if (!props.geometry) return '-'
  switch (props.geometry.aperture_type) {
    case 'round':
      return 'Round'
    case 'oval':
      return 'Oval'
    case 'spiral':
      return 'Spiral'
    case 'dual_spiral':
      return 'Dual Spiral'
    case 'fhole':
      return 'F-hole'
    default:
      return props.geometry.aperture_type
  }
})

function formatNumber(n: number | undefined | null, decimals = 1): string {
  if (n == null) return '-'
  return n.toFixed(decimals)
}
</script>

<template>
  <div :class="$style.card">
    <div :class="$style.header">
      <h4 :class="$style.title">{{ title }}</h4>
      <GateBadge v-if="geometry" :gate="gate" :label="typeLabel" />
    </div>

    <div v-if="loading" :class="$style.loading">Computing...</div>
    <div v-else-if="error" :class="$style.error">{{ error }}</div>
    <div v-else-if="!geometry" :class="$style.empty">No geometry computed</div>

    <div v-else :class="$style.metrics">
      <div :class="$style.metric">
        <span :class="$style.label">Area</span>
        <span :class="$style.value">{{ formatNumber(geometry.area_mm2, 1) }} mm²</span>
      </div>
      <div :class="$style.metric">
        <span :class="$style.label">Perimeter</span>
        <span :class="$style.value">{{ formatNumber(geometry.perimeter_mm, 1) }} mm</span>
      </div>
      <div :class="$style.metric">
        <span :class="$style.label">Equiv. Diameter</span>
        <span :class="$style.value">{{ formatNumber(geometry.equivalent_diameter_mm, 1) }} mm</span>
      </div>
      <div :class="$style.metric">
        <span :class="$style.label">P:A Ratio</span>
        <span :class="$style.value">{{ formatNumber(geometry.pa_ratio_mm_inv, 4) }} mm⁻¹</span>
      </div>
      <div v-if="geometry.path_length_mm != null" :class="$style.metric">
        <span :class="$style.label">Path Length</span>
        <span :class="$style.value">{{ formatNumber(geometry.path_length_mm, 1) }} mm</span>
      </div>
      <div v-if="geometry.characteristic_width_mm != null" :class="$style.metric">
        <span :class="$style.label">Char. Width</span>
        <span :class="$style.value">{{ formatNumber(geometry.characteristic_width_mm, 1) }} mm</span>
      </div>
    </div>

    <ul v-if="notes.length > 0" :class="$style.notes">
      <li v-for="(note, i) in notes" :key="i">{{ note }}</li>
    </ul>
  </div>
</template>

<style module>
.card {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #374151;
}

.title {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #f9fafb;
}

.loading,
.error,
.empty {
  padding: 1rem;
  text-align: center;
  font-size: 0.875rem;
  border-radius: 0.375rem;
}

.loading {
  background: #1e3a5f;
  color: #93c5fd;
}

.error {
  background: #450a0a;
  color: #fca5a5;
}

.empty {
  background: #111827;
  color: #6b7280;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding: 0.5rem;
  background: #111827;
  border-radius: 0.375rem;
}

.label {
  font-size: 0.6875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.value {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f9fafb;
  font-family: var(--font-mono, ui-monospace, monospace);
}

.notes {
  margin: 0.75rem 0 0 0;
  padding: 0.5rem 0.75rem 0.5rem 1.5rem;
  background: #111827;
  border-radius: 0.375rem;
  list-style: disc;
}

.notes li {
  font-size: 0.75rem;
  color: #9ca3af;
  line-height: 1.5;
}
</style>
