<template>
  <div :class="styles.svgPreview">
    <h3 :class="styles.sectionTitle">Batch Path Preview</h3>
    <svg
      :viewBox="svgViewBox"
      width="100%"
      height="400"
      :class="styles.previewCanvas"
    >
      <!-- Grid -->
      <defs>
        <pattern
          id="batch-grid"
          width="20"
          height="20"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M 20 0 L 0 0 0 20"
            fill="none"
            stroke="#e0e0e0"
            stroke-width="0.5"
          />
        </pattern>
      </defs>
      <rect
        width="100%"
        height="100%"
        fill="url(#batch-grid)"
      />

      <!-- Slice paths -->
      <g
        v-for="(slice, i) in slicePaths"
        :key="i"
      >
        <line
          :x1="slice.x1"
          :y1="slice.y1"
          :x2="slice.x2"
          :y2="slice.y2"
          :stroke="i === 0 ? '#2196F3' : '#64B5F6'"
          stroke-width="2"
        />
        <text
          :x="slice.x1 - 10"
          :y="slice.y1"
          font-size="10"
          fill="#666"
        >{{ i + 1 }}</text>
      </g>

      <!-- Kerf boundaries (first slice) -->
      <line
        v-if="slicePaths.length > 0 && selectedBlade"
        :x1="slicePaths[0].x1"
        :y1="slicePaths[0].y1 + (selectedBlade.kerf_mm / 2)"
        :x2="slicePaths[0].x2"
        :y2="slicePaths[0].y2 + (selectedBlade.kerf_mm / 2)"
        stroke="#FF9800"
        stroke-width="1"
        stroke-dasharray="2,2"
      />
      <line
        v-if="slicePaths.length > 0 && selectedBlade"
        :x1="slicePaths[0].x1"
        :y1="slicePaths[0].y1 - (selectedBlade.kerf_mm / 2)"
        :x2="slicePaths[0].x2"
        :y2="slicePaths[0].y2 - (selectedBlade.kerf_mm / 2)"
        stroke="#FF9800"
        stroke-width="1"
        stroke-dasharray="2,2"
      />
    </svg>
    <div :class="styles.legend">
      <span><span
        :class="styles.colorBox"
        style="background: #2196F3;"
      /> First slice</span>
      <span><span
        :class="styles.colorBox"
        style="background: #64B5F6;"
      /> Other slices</span>
      <span><span
        :class="styles.colorBox"
        style="background: #FF9800;"
      /> Kerf boundary</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from '../SawBatchPanel.module.css'

interface SlicePath {
  x1: number
  y1: number
  x2: number
  y2: number
}

interface Blade {
  kerf_mm: number
}

defineProps<{
  svgViewBox: string
  slicePaths: SlicePath[]
  selectedBlade: Blade | null
}>()
</script>
