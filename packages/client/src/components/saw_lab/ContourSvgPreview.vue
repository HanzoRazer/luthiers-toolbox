<template>
  <div :class="styles.svgPreview">
    <h3>Contour Preview</h3>
    <svg
      :viewBox="svgViewBox"
      width="100%"
      height="400"
      :class="styles.previewCanvas"
    >
      <!-- Grid -->
      <defs>
        <pattern
          id="contour-grid"
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
        fill="url(#contour-grid)"
      />

      <!-- Contour path -->
      <path
        v-if="contourPath"
        :d="contourPath"
        fill="none"
        stroke="#2196F3"
        stroke-width="3"
      />

      <!-- Center marker -->
      <circle
        :cx="centerX"
        :cy="centerY"
        r="3"
        fill="#F44336"
      />
      <text
        :x="centerX + 8"
        :y="centerY + 5"
        font-size="12"
        fill="#666"
      >Center</text>

      <!-- Radius indicator -->
      <line
        v-if="contourType !== 'rosette'"
        :x1="centerX"
        :y1="centerY"
        :x2="centerX + (radius || 0)"
        :y2="centerY"
        stroke="#9C27B0"
        stroke-width="1"
        stroke-dasharray="5,5"
      />
      <text
        v-if="contourType !== 'rosette'"
        :x="centerX + (radius || 0) / 2"
        :y="centerY - 8"
        font-size="11"
        fill="#9C27B0"
        text-anchor="middle"
      >R={{ radius }}</text>
    </svg>
    <div :class="styles.legend">
      <span><span
        :class="styles.colorBox"
        style="background: #2196F3;"
      /> Cut path</span>
      <span><span
        :class="styles.colorBox"
        style="background: #F44336;"
      /> Center</span>
      <span><span
        :class="styles.colorBox"
        style="background: #9C27B0;"
      /> Radius</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from './SawContourPanel.module.css'

defineProps<{
  svgViewBox: string
  contourPath: string
  centerX: number
  centerY: number
  contourType: 'arc' | 'circle' | 'rosette'
  radius: number
}>()
</script>
