<script setup lang="ts">
/**
 * StandardAperturePanel — Round, Oval, and F-hole aperture geometry panel
 *
 * Dev Order 10: Standard aperture types panel for ApertureWorkspace.
 *
 * Uses backend API: POST /api/instrument/soundhole
 * Returns: area_mm2, perimeter_mm, pa_ratio_mm_inv, equivalent_diameter_mm
 */
import { ref, computed, watch, onMounted } from 'vue'
import { GateBadge, SectionLabel, PrerequisiteNotice } from '@/components/shared/workflow'
import { ApertureResultCard, type ApertureGeometry } from '@/components/shared/aperture'

// Types
type ApertureType = 'round' | 'oval' | 'fhole'

interface BodyStyleOption {
  value: string
  label: string
  diameter: number
}

interface GeometryResult {
  diameter_mm: number
  position_from_neck_block_mm: number
  body_style: string
  gate: string
  notes: string[]
  soundhole_type: string
  area_mm2?: number
  perimeter_mm?: number
  pa_ratio_mm_inv?: number
}

// State
const apertureType = ref<ApertureType>('round')
const bodyStyle = ref('dreadnought')
const bodyLengthMm = ref(508) // 20" standard dreadnought
const customDiameterMm = ref<number | null>(null)
const useCustomDiameter = ref(false)

// Oval-specific
const ovalWidthMm = ref(80)
const ovalHeightMm = ref(110)

// API state
const loading = ref(false)
const error = ref('')
const bodyStyles = ref<BodyStyleOption[]>([])
const result = ref<GeometryResult | null>(null)

// Computed
const API_BASE = '/api/instrument'

const equivalentDiameterMm = computed(() => {
  if (!result.value?.area_mm2) return null
  return 2 * Math.sqrt(result.value.area_mm2 / Math.PI)
})

const gateLevel = computed<'green' | 'yellow' | 'red'>(() => {
  if (!result.value) return 'yellow'
  switch (result.value.gate) {
    case 'GREEN':
      return 'green'
    case 'YELLOW':
      return 'yellow'
    case 'RED':
      return 'red'
    default:
      return 'yellow'
  }
})

const resultGeometry = computed<ApertureGeometry | null>(() => {
  if (!result.value) return null
  const area = result.value.area_mm2 ?? Math.PI * (result.value.diameter_mm / 2) ** 2
  return {
    aperture_type: result.value.soundhole_type,
    area_mm2: area,
    perimeter_mm: result.value.perimeter_mm ?? Math.PI * result.value.diameter_mm,
    equivalent_diameter_mm: equivalentDiameterMm.value ?? result.value.diameter_mm,
    pa_ratio_mm_inv: result.value.pa_ratio_mm_inv ?? null,
    characteristic_width_mm: apertureType.value === 'oval' ? ovalWidthMm.value : null,
    path_length_mm: null,
  }
})

const apertureTypeOptions: { value: ApertureType; label: string; description: string }[] = [
  { value: 'round', label: 'Round', description: 'Traditional circular soundhole' },
  { value: 'oval', label: 'Oval', description: 'Selmer/Maccaferri elliptical' },
  { value: 'fhole', label: 'F-hole', description: 'Archtop f-holes' },
]

// Fetch body styles on mount
async function fetchBodyStyles() {
  try {
    const res = await fetch(`${API_BASE}/soundhole/body-styles`)
    if (!res.ok) throw new Error('Failed to fetch body styles')
    const data = await res.json()

    bodyStyles.value = data.body_styles.map((style: string) => ({
      value: style,
      label: style.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
      diameter: data.standard_diameters_mm?.[style] ?? 95,
    }))
  } catch (e) {
    console.error('Failed to fetch body styles:', e)
    // Fallback defaults
    bodyStyles.value = [
      { value: 'dreadnought', label: 'Dreadnought', diameter: 100 },
      { value: 'om_000', label: 'OM/000', diameter: 98 },
      { value: 'parlor', label: 'Parlor', diameter: 85 },
      { value: 'classical', label: 'Classical', diameter: 85 },
      { value: 'jumbo', label: 'Jumbo', diameter: 102 },
    ]
  }
}

// Compute geometry
async function computeGeometry() {
  loading.value = true
  error.value = ''

  try {
    const payload: Record<string, unknown> = {
      body_style: bodyStyle.value,
      body_length_mm: bodyLengthMm.value,
      soundhole_type: apertureType.value,
    }

    // For round/oval, include custom diameter if set
    if (apertureType.value === 'round' && useCustomDiameter.value && customDiameterMm.value) {
      payload.custom_diameter_mm = customDiameterMm.value
    }
    if (apertureType.value === 'oval') {
      payload.custom_diameter_mm = ovalWidthMm.value
    }

    const res = await fetch(API_BASE + '/soundhole', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'API error')
    }

    result.value = await res.json()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error'
    result.value = null
  } finally {
    loading.value = false
  }
}

// Watch for changes and recompute
watch(
  [apertureType, bodyStyle, bodyLengthMm, customDiameterMm, useCustomDiameter, ovalWidthMm, ovalHeightMm],
  () => {
    computeGeometry()
  },
  { deep: true }
)

onMounted(() => {
  fetchBodyStyles()
  computeGeometry()
})
</script>

<template>
  <div :class="$style.panel">
    <!-- Type Selection -->
    <section :class="$style.section">
      <SectionLabel text="Aperture Type" />
      <div :class="$style.typeGrid">
        <button
          v-for="opt in apertureTypeOptions"
          :key="opt.value"
          :class="[$style.typeButton, apertureType === opt.value && $style.active]"
          @click="apertureType = opt.value"
        >
          <span :class="$style.typeLabel">{{ opt.label }}</span>
          <span :class="$style.typeDesc">{{ opt.description }}</span>
        </button>
      </div>
    </section>

    <!-- F-hole notice -->
    <PrerequisiteNotice
      v-if="apertureType === 'fhole'"
      message="F-hole design uses a separate dedicated calculator. Configure paired f-holes with upper/lower bout placement, notch dimensions, and bout curve alignment."
    />

    <!-- Configuration -->
    <section v-if="apertureType !== 'fhole'" :class="$style.section">
      <SectionLabel text="Configuration" />

      <div :class="$style.formGrid">
        <!-- Body Style -->
        <div :class="$style.field">
          <label :class="$style.label">Body Style</label>
          <select v-model="bodyStyle" :class="$style.select">
            <option v-for="opt in bodyStyles" :key="opt.value" :value="opt.value">
              {{ opt.label }} ({{ opt.diameter }}mm)
            </option>
          </select>
        </div>

        <!-- Body Length -->
        <div :class="$style.field">
          <label :class="$style.label">Body Length (mm)</label>
          <input
            v-model.number="bodyLengthMm"
            type="number"
            :class="$style.input"
            min="300"
            max="700"
            step="1"
          />
        </div>

        <!-- Round: Custom Diameter -->
        <template v-if="apertureType === 'round'">
          <div :class="$style.field">
            <label :class="$style.checkboxLabel">
              <input v-model="useCustomDiameter" type="checkbox" />
              Custom Diameter
            </label>
          </div>
          <div v-if="useCustomDiameter" :class="$style.field">
            <label :class="$style.label">Diameter (mm)</label>
            <input
              v-model.number="customDiameterMm"
              type="number"
              :class="$style.input"
              min="50"
              max="150"
              step="0.5"
            />
          </div>
        </template>

        <!-- Oval: Width/Height -->
        <template v-if="apertureType === 'oval'">
          <div :class="$style.field">
            <label :class="$style.label">Width (mm)</label>
            <input
              v-model.number="ovalWidthMm"
              type="number"
              :class="$style.input"
              min="50"
              max="150"
              step="1"
            />
          </div>
          <div :class="$style.field">
            <label :class="$style.label">Height (mm)</label>
            <input
              v-model.number="ovalHeightMm"
              type="number"
              :class="$style.input"
              min="70"
              max="200"
              step="1"
            />
          </div>
        </template>
      </div>
    </section>

    <!-- Results -->
    <ApertureResultCard
      v-if="apertureType !== 'fhole'"
      title="Geometry Results"
      :geometry="resultGeometry"
      :gate="gateLevel"
      :notes="result?.notes ?? []"
      :loading="loading"
      :error="error"
    />
  </div>
</template>

<style module>
.panel {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.5rem;
  padding: 1rem;
}

.typeGrid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.typeButton {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
  padding: 0.75rem;
  background: #111827;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.typeButton:hover {
  background: #1f2937;
  border-color: #4b5563;
}

.typeButton.active {
  background: #374151;
  border-color: #6366f1;
}

.typeLabel {
  font-size: 0.875rem;
  font-weight: 600;
  color: #f9fafb;
}

.typeDesc {
  font-size: 0.75rem;
  color: #9ca3af;
}

.formGrid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-top: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.checkboxLabel {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: #f9fafb;
  cursor: pointer;
}

.checkboxLabel input {
  accent-color: #6366f1;
}

.select,
.input {
  padding: 0.5rem 0.75rem;
  background: #111827;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  color: #f9fafb;
  font-size: 0.875rem;
}

.select:focus,
.input:focus {
  outline: none;
  border-color: #6366f1;
}
</style>
