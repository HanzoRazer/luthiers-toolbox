<template>
  <section class="form-section preview">
    <h3>Preview (Top View)</h3>
    <svg
      :viewBox="viewBox"
      class="body-preview"
    >
      <!-- Background -->
      <rect
        x="0"
        y="0"
        :width="svgWidth"
        :height="svgHeight"
        fill="#fafafa"
      />

      <!-- Simplified body outline (based on dimensions) -->
      <g
        v-if="hasValidDimensions"
        transform="translate(250, 50)"
      >
        <!-- Upper bout -->
        <ellipse
          :cx="0"
          :cy="scaledBodyLength * 0.3"
          :rx="scaledBodyWidthUpper / 2"
          :ry="scaledBodyLength * 0.15"
          fill="none"
          stroke="#333"
          stroke-width="2"
        />

        <!-- Lower bout -->
        <ellipse
          :cx="0"
          :cy="scaledBodyLength * 0.7"
          :rx="scaledBodyWidthLower / 2"
          :ry="scaledBodyLength * 0.2"
          fill="none"
          stroke="#333"
          stroke-width="2"
        />

        <!-- Waist indicators -->
        <line
          :x1="-scaledWaistWidth / 2"
          :y1="scaledBodyLength * 0.5"
          :x2="scaledWaistWidth / 2"
          :y2="scaledBodyLength * 0.5"
          stroke="#666"
          stroke-width="1"
          stroke-dasharray="3,3"
        />

        <!-- Centerline -->
        <line
          x1="0"
          y1="0"
          x2="0"
          :y2="scaledBodyLength"
          stroke="#94a3b8"
          stroke-width="1"
          stroke-dasharray="5,5"
        />

        <!-- Dimension labels -->
        <text
          x="10"
          :y="scaledBodyLength / 2"
          font-size="10"
          fill="#666"
        >
          {{ dimensions.bodyLength }} {{ currentUnit }}
        </text>
      </g>

      <!-- Placeholder if no dimensions -->
      <text
        v-else
        x="250"
        y="250"
        text-anchor="middle"
        font-size="14"
        fill="#999"
      >
        Enter dimensions to see preview
      </text>
    </svg>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { GuitarDimensions } from '../composables/useGuitarDimensions'

const props = defineProps<{
  dimensions: GuitarDimensions
  currentUnit: string
  hasValidDimensions: boolean
}>()

// SVG sizing
const svgWidth = 500
const svgHeight = 600
const viewBox = `0 0 ${svgWidth} ${svgHeight}`

// Scaled dimensions for SVG
const scaledBodyLength = computed(() => {
  if (!props.dimensions.bodyLength) return 0
  return Math.min(props.dimensions.bodyLength * 0.8, 400)
})

const scaledBodyWidthUpper = computed(() => {
  if (!props.dimensions.bodyWidthUpper) return 0
  return Math.min(props.dimensions.bodyWidthUpper * 0.8, 300)
})

const scaledBodyWidthLower = computed(() => {
  if (!props.dimensions.bodyWidthLower) return 0
  return Math.min(props.dimensions.bodyWidthLower * 0.8, 300)
})

const scaledWaistWidth = computed(() => {
  if (!props.dimensions.waistWidth) return 0
  return Math.min(props.dimensions.waistWidth * 0.8, 200)
})
</script>

<style scoped>
.form-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #eee;
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section h3 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  color: #444;
}

.preview {
  background: #fafafa;
  padding: 1.5rem;
  border-radius: 8px;
}

.body-preview {
  width: 100%;
  height: 600px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}
</style>
