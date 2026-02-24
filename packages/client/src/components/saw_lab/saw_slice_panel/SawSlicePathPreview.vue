<script setup lang="ts">
/**
 * SawSlicePathPreview.vue - SVG path visualization with kerf boundaries
 * Extracted from SawSlicePanel.vue
 */
import styles from "../SawSlicePanel.module.css";

export interface PathGeometry {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

defineProps<{
  geometry: PathGeometry;
  kerfMm: number | null;
  svgViewBox: string;
}>();
</script>

<template>
  <div :class="styles.svgPreview">
    <h3>Path Preview</h3>
    <svg
      :viewBox="svgViewBox"
      width="400"
      height="300"
      :class="styles.previewCanvas"
    >
      <!-- Grid -->
      <defs>
        <pattern
          id="grid"
          width="10"
          height="10"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M 10 0 L 0 0 0 10"
            fill="none"
            stroke="#e0e0e0"
            stroke-width="0.5"
          />
        </pattern>
      </defs>
      <rect
        width="100%"
        height="100%"
        fill="url(#grid)"
      />

      <!-- Cut path -->
      <line
        v-if="geometry.startX !== null && geometry.endX !== null"
        :x1="geometry.startX"
        :y1="geometry.startY"
        :x2="geometry.endX"
        :y2="geometry.endY"
        stroke="#2196F3"
        stroke-width="2"
      />

      <!-- Kerf width visualization -->
      <line
        v-if="geometry.startX !== null && geometry.endX !== null && kerfMm"
        :x1="geometry.startX"
        :y1="geometry.startY + kerfMm / 2"
        :x2="geometry.endX"
        :y2="geometry.endY + kerfMm / 2"
        stroke="#FF9800"
        stroke-width="1"
        stroke-dasharray="2,2"
      />
      <line
        v-if="geometry.startX !== null && geometry.endX !== null && kerfMm"
        :x1="geometry.startX"
        :y1="geometry.startY - kerfMm / 2"
        :x2="geometry.endX"
        :y2="geometry.endY - kerfMm / 2"
        stroke="#FF9800"
        stroke-width="1"
        stroke-dasharray="2,2"
      />

      <!-- Start/End markers -->
      <circle
        v-if="geometry.startX !== null"
        :cx="geometry.startX"
        :cy="geometry.startY"
        r="2"
        fill="#4CAF50"
      />
      <circle
        v-if="geometry.endX !== null"
        :cx="geometry.endX"
        :cy="geometry.endY"
        r="2"
        fill="#F44336"
      />
    </svg>
    <div :class="styles.legend">
      <span>
        <span
          :class="styles.colorBox"
          style="background: #2196f3"
        /> Cut path
      </span>
      <span>
        <span
          :class="styles.colorBox"
          style="background: #ff9800"
        /> Kerf boundary
      </span>
      <span>
        <span
          :class="styles.colorBox"
          style="background: #4caf50"
        /> Start
      </span>
      <span>
        <span
          :class="styles.colorBox"
          style="background: #f44336"
        /> End
      </span>
    </div>
  </div>
</template>
