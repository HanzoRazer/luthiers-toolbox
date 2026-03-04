<template>
  <div class="preset-browser">
    <div class="browser-header">
      <h3 class="browser-title">
        Rosette Preset Library
      </h3>
      <p class="browser-subtitle">
        {{ catalog.totalPresets }} variations across {{ catalog.families.length }} pattern families
      </p>
    </div>

    <!-- Category Filter -->
    <div class="category-filter">
      <button
        v-for="cat in ['all', ...catalog.categories]"
        :key="cat"
        class="category-btn"
        :class="{ active: selectedCategory === cat }"
        @click="selectedCategory = cat"
      >
        {{ cat.charAt(0).toUpperCase() + cat.slice(1) }}
      </button>
    </div>

    <!-- Pattern Families -->
    <div class="families-container">
      <div
        v-for="family in filteredFamilies"
        :key="family.id"
        class="family-section"
      >
        <div
          class="family-header"
          @click="toggleFamily(family.id)"
        >
          <div class="family-info">
            <h4 class="family-name">
              {{ family.name }}
            </h4>
            <p class="family-desc">
              {{ family.description }}
            </p>
            <span class="family-badge">{{ family.category }}</span>
          </div>
          <button
            class="expand-btn"
            :class="{ expanded: expandedFamilies.has(family.id) }"
          >
            {{ expandedFamilies.has(family.id) ? '▼' : '▶' }}
          </button>
        </div>

        <!-- Variations Grid -->
        <div
          v-if="expandedFamilies.has(family.id)"
          class="variations-grid"
        >
          <div
            v-for="(variation, idx) in family.variations"
            :key="idx"
            class="variation-card"
            @click="selectVariation(family, variation)"
          >
            <!-- Visual Preview -->
            <div class="variation-preview">
              <!-- Try to load actual SVG file if it exists -->
              <img
                v-if="variation.svgFile"
                :src="getSvgPath(variation.svgFile)"
                :alt="variation.name"
                class="preview-svg-img"
                @error="handleImageError($event, variation)"
              >

              <!-- Fallback: Programmatic SVG (always render, hide if image loads successfully) -->
              <svg
                viewBox="0 0 100 100"
                class="preview-svg"
                :class="{ 'svg-fallback': variation.svgFile }"
              >
                <!-- Background -->
                <circle
                  cx="50"
                  cy="50"
                  r="48"
                  fill="#f8fafc"
                />

                <!-- SEGMENTED PATTERNS (segments > 1) - Show pie slices -->
                <g v-if="variation.params.segments > 1">
                  <path
                    v-for="seg in variation.params.segments"
                    :key="seg"
                    :d="getSegmentPath(50, 50, 5, 42, ((seg - 1) * 360 / variation.params.segments), (seg * 360 / variation.params.segments))"
                    :fill="variation.params.colorScheme[(seg - 1) % variation.params.colorScheme.length]"
                    stroke="white"
                    stroke-width="0.5"
                    opacity="0.85"
                  />
                  <!-- Ring dividers -->
                  <circle
                    v-for="ringIdx in Math.max(1, variation.params.rings - 1)"
                    :key="'ring-' + ringIdx"
                    cx="50"
                    cy="50"
                    :r="5 + (ringIdx * (37 / Math.max(variation.params.rings, 1)))"
                    fill="none"
                    stroke="white"
                    :stroke-width="1.5"
                    opacity="0.6"
                  />
                </g>

                <!-- SOLID RINGS (segments = 1) - Show concentric circles only -->
                <g v-else>
                  <circle
                    v-for="ringIdx in variation.params.rings"
                    :key="'solid-ring-' + ringIdx"
                    cx="50"
                    cy="50"
                    :r="Math.max(2, 45 - ((ringIdx - 1) * (40 / variation.params.rings)))"
                    fill="none"
                    :stroke="variation.params.colorScheme[(ringIdx - 1) % variation.params.colorScheme.length]"
                    :stroke-width="Math.max(3, 36 / variation.params.rings)"
                    opacity="0.85"
                  />
                </g>

                <!-- Outer border -->
                <circle
                  cx="50"
                  cy="50"
                  r="47"
                  fill="none"
                  stroke="#cbd5e1"
                  stroke-width="1"
                />
              </svg>
            </div>

            <!-- Info -->
            <div class="variation-info">
              <h5 class="variation-name">
                {{ variation.name }}
              </h5>
              <p class="variation-desc">
                {{ variation.description }}
              </p>
              <div class="variation-meta">
                <span class="meta-tag">{{ variation.params.segments }} seg</span>
                <span class="meta-tag">{{ variation.params.rings }} rings</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Info Panel -->
    <div
      v-if="selectedPreset"
      class="info-panel"
    >
      <h4 class="info-title">
        Selected: {{ selectedPreset.variation.name }}
      </h4>
      <p class="info-desc">
        {{ selectedPreset.variation.description }}
      </p>
      <div class="info-details">
        <div class="detail-item">
          <span class="detail-label">Segments:</span>
          <span class="detail-value">{{ selectedPreset.variation.params.segments }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Rings:</span>
          <span class="detail-value">{{ selectedPreset.variation.params.rings }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Family:</span>
          <span class="detail-value">{{ selectedPreset.family.name }}</span>
        </div>
      </div>
      <button
        class="btn-apply"
        @click="applyPreset"
      >
        Apply This Preset
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { getPresetCatalog, createPatternFromVariation, type PatternFamily, type PatternVariation } from '@/lib/rosettePresets'
import type { RosettePattern } from '@/models/rmos'

const emit = defineEmits<{
  (e: 'preset-selected', pattern: Omit<RosettePattern, 'id'>): void
}>()

const catalog = getPresetCatalog()
const selectedCategory = ref<string>('all')
const expandedFamilies = ref<Set<string>>(new Set(['repeating_single'])) // Default expand first family
const selectedPreset = ref<{ family: PatternFamily; variation: PatternVariation } | null>(null)

const filteredFamilies = computed(() => {
  let families = []
  if (selectedCategory.value === 'all') {
    families = catalog.families
  } else {
    families = catalog.families.filter(f => f.category === selectedCategory.value)
  }

  // Auto-expand all families in the filtered list
  families.forEach(f => expandedFamilies.value.add(f.id))

  return families
})

function toggleFamily(familyId: string) {
  if (expandedFamilies.value.has(familyId)) {
    expandedFamilies.value.delete(familyId)
  } else {
    expandedFamilies.value.add(familyId)
  }
}

function selectVariation(family: PatternFamily, variation: PatternVariation) {
  selectedPreset.value = { family, variation }
}

function applyPreset() {
  if (!selectedPreset.value) return
  const pattern = createPatternFromVariation(
    selectedPreset.value.family,
    selectedPreset.value.variation
  )
  emit('preset-selected', pattern)
}

// Get the path to an SVG asset file
function getSvgPath(filename: string): string {
  try {
    // Vite's dynamic import for assets
    return new URL(`../../assets/rosette-presets/${filename}`, import.meta.url).href
  } catch (e) {
    console.warn(`SVG file not found: ${filename}`, e)
    return ''
  }
}

// Handle image load errors (SVG file doesn't exist yet)
function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement
  // Hide the image, let the fallback SVG show instead
  img.style.display = 'none'
}

// Helper function to generate SVG path for a pie slice segment
function getSegmentPath(cx: number, cy: number, innerRadius: number, outerRadius: number, startAngle: number, endAngle: number): string {
  const toRadians = (deg: number) => (deg - 90) * Math.PI / 180

  const startInner = {
    x: cx + innerRadius * Math.cos(toRadians(startAngle)),
    y: cy + innerRadius * Math.sin(toRadians(startAngle))
  }
  const endInner = {
    x: cx + innerRadius * Math.cos(toRadians(endAngle)),
    y: cy + innerRadius * Math.sin(toRadians(endAngle))
  }
  const startOuter = {
    x: cx + outerRadius * Math.cos(toRadians(startAngle)),
    y: cy + outerRadius * Math.sin(toRadians(startAngle))
  }
  const endOuter = {
    x: cx + outerRadius * Math.cos(toRadians(endAngle)),
    y: cy + outerRadius * Math.sin(toRadians(endAngle))
  }

  const largeArc = endAngle - startAngle > 180 ? 1 : 0

  return [
    `M ${startInner.x} ${startInner.y}`,
    `L ${startOuter.x} ${startOuter.y}`,
    `A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${endOuter.x} ${endOuter.y}`,
    `L ${endInner.x} ${endInner.y}`,
    `A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${startInner.x} ${startInner.y}`,
    'Z'
  ].join(' ')
}
</script>

<style scoped>
.preset-browser {
  display: flex;
  flex-direction: column;
  gap: var(--space-4, 1rem);
  background: var(--color-surface, #ffffff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: var(--radius-lg, 0.75rem);
  padding: var(--space-4, 1rem);
  max-height: 80vh;
  overflow-y: auto;
}

.browser-header {
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  padding-bottom: var(--space-3, 0.75rem);
}

.browser-title {
  font-size: var(--font-size-lg, 1.125rem);
  font-weight: 700;
  color: var(--color-text, #1e293b);
  margin: 0 0 var(--space-1, 0.25rem) 0;
}

.browser-subtitle {
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-muted, #64748b);
  margin: 0;
}

/* Category Filter */
.category-filter {
  display: flex;
  gap: var(--space-2, 0.5rem);
  flex-wrap: wrap;
}

.category-btn {
  padding: var(--space-1, 0.25rem) var(--space-3, 0.75rem);
  background: var(--color-surface-alt, #f8fafc);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: var(--radius-full, 9999px);
  font-size: var(--font-size-xs, 0.75rem);
  font-weight: 500;
  color: var(--color-text-muted, #64748b);
  cursor: pointer;
  transition: all 0.2s;
}

.category-btn:hover {
  border-color: var(--color-primary, #2563eb);
  color: var(--color-primary, #2563eb);
}

.category-btn.active {
  background: var(--color-primary, #2563eb);
  color: white;
  border-color: var(--color-primary, #2563eb);
}

/* Family Sections */
.families-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-4, 1rem);
}

.family-section {
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: var(--radius-md, 0.5rem);
  overflow: hidden;
}

.family-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3, 0.75rem);
  background: var(--color-surface-alt, #f8fafc);
  cursor: pointer;
  transition: background 0.2s;
}

.family-header:hover {
  background: #f1f5f9;
}

.family-info {
  flex: 1;
}

.family-name {
  font-size: var(--font-size-base, 1rem);
  font-weight: 600;
  color: var(--color-text, #1e293b);
  margin: 0 0 var(--space-1, 0.25rem) 0;
}

.family-desc {
  font-size: var(--font-size-xs, 0.75rem);
  color: var(--color-text-muted, #64748b);
  margin: 0 0 var(--space-2, 0.5rem) 0;
  line-height: 1.4;
}

.family-badge {
  display: inline-block;
  font-size: var(--font-size-xs, 0.75rem);
  padding: var(--space-1, 0.25rem) var(--space-2, 0.5rem);
  background: var(--color-primary-light, #dbeafe);
  color: var(--color-primary, #2563eb);
  border-radius: var(--radius-full, 9999px);
  font-weight: 600;
}

.expand-btn {
  background: none;
  border: none;
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-muted, #64748b);
  cursor: pointer;
  padding: var(--space-2, 0.5rem);
  transition: transform 0.2s;
}

.expand-btn.expanded {
  transform: rotate(0deg);
}

/* Variations Grid */
.variations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--space-3, 0.75rem);
  padding: var(--space-3, 0.75rem);
  background: white;
}

.variation-card {
  border: 2px solid var(--color-border, #e2e8f0);
  border-radius: var(--radius-md, 0.5rem);
  padding: var(--space-2, 0.5rem);
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  min-height: 200px;
}

.variation-card:hover {
  border-color: var(--color-primary, #2563eb);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
  transform: translateY(-2px);
}

.variation-preview {
  width: 100%;
  aspect-ratio: 1;
  margin-bottom: var(--space-2, 0.5rem);
}

.preview-svg {
  width: 100%;
  height: 100%;
}

.preview-svg-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.variation-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-1, 0.25rem);
}

.variation-name {
  font-size: 0.875rem !important;
  font-weight: 600;
  color: #1e293b !important;
  margin: 0;
}

.variation-desc {
  font-size: 0.75rem !important;
  color: #64748b !important;
  margin: 0;
  line-height: 1.3;
}

.variation-meta {
  display: flex;
  gap: var(--space-1, 0.25rem);
  margin-top: var(--space-1, 0.25rem);
}

.meta-tag {
  font-size: 0.625rem !important;
  padding: 2px 6px;
  background: #f8fafc;
  border-radius: 0.25rem;
  color: #64748b !important;
  font-weight: 500;
}

/* Info Panel */
.info-panel {
  background: var(--color-primary-light, #dbeafe);
  border: 1px solid var(--color-primary, #2563eb);
  border-radius: var(--radius-md, 0.5rem);
  padding: var(--space-4, 1rem);
  margin-top: var(--space-4, 1rem);
}

.info-title {
  font-size: var(--font-size-base, 1rem);
  font-weight: 700;
  color: var(--color-primary-dark, #1d4ed8);
  margin: 0 0 var(--space-2, 0.5rem) 0;
}

.info-desc {
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text, #1e293b);
  margin: 0 0 var(--space-3, 0.75rem) 0;
}

.info-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-2, 0.5rem);
  margin-bottom: var(--space-4, 1rem);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-sm, 0.875rem);
}

.detail-label {
  font-weight: 500;
  color: var(--color-text-muted, #64748b);
}

.detail-value {
  font-weight: 600;
  color: var(--color-text, #1e293b);
}

.btn-apply {
  width: 100%;
  padding: var(--space-2, 0.5rem) var(--space-4, 1rem);
  background: var(--color-primary, #2563eb);
  color: white;
  border: none;
  border-radius: var(--radius-md, 0.5rem);
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-apply:hover {
  background: var(--color-primary-dark, #1d4ed8);
}
</style>
