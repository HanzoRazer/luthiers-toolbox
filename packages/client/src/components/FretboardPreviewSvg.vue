<template>
  <svg
    :width="svgWidth"
    :height="svgHeight"
    :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
    class="fretboard-preview"
  >
    <!-- Background -->
    <rect
      x="0"
      y="0"
      :width="svgWidth"
      :height="svgHeight"
      fill="#1e1e1e"
      stroke="#444"
      stroke-width="1"
    />

    <!-- Fretboard outline -->
    <path
      :d="fretboardOutline"
      fill="#654321"
      stroke="#333"
      stroke-width="2"
    />

    <!-- Fret slots with risk coloring -->
    <g
      v-for="toolpath in toolpaths"
      :key="toolpath.fret_number"
    >
      <rect
        :x="margin + toolpath.position_mm * scale"
        :y="margin + (centerY - (toolpath.width_mm * scale) / 2)"
        :width="spec.slot_width_mm * scale"
        :height="toolpath.width_mm * scale"
        :fill="getFretColor(toolpath)"
        :stroke="getFretStrokeColor(toolpath)"
        stroke-width="1"
        :opacity="0.8"
      >
        <title>
          Fret #{{ toolpath.fret_number }} Position:
          {{ toolpath.position_mm.toFixed(2) }}mm Width:
          {{ toolpath.width_mm.toFixed(2) }}mm Depth:
          {{ toolpath.depth_mm.toFixed(2) }}mm Feed:
          {{ toolpath.feed_rate }} mm/min RPM: {{ toolpath.spindle_rpm }}
        </title>
      </rect>

      <!-- Fret number labels (every 3rd fret) -->
      <text
        v-if="showLabels && toolpath.fret_number % 3 === 0"
        :x="margin + toolpath.position_mm * scale"
        :y="margin - 5"
        font-size="10"
        fill="#999"
        text-anchor="middle"
      >
        {{ toolpath.fret_number }}
      </text>
    </g>

    <!-- Inlay markers (dots at 3, 5, 7, 9, double at 12) -->
    <g v-if="showInlays">
      <circle
        v-for="fret in [3, 5, 7, 9, 15, 17, 19, 21]"
        :key="`dot-${fret}`"
        :cx="margin + getFretPosition(fret) * scale"
        :cy="svgHeight / 2"
        r="4"
        fill="#ddd"
        opacity="0.4"
      />
      <circle
        v-for="offset in [-0.15, 0.15]"
        :key="`dot-12-${offset}`"
        :cx="
          margin + (getFretPosition(12) + offset * spec.bridge_width_mm) * scale
        "
        :cy="svgHeight / 2"
        r="4"
        fill="#ddd"
        opacity="0.4"
      />
    </g>

    <!-- Nut (fret 0) -->
    <line
      :x1="margin"
      :y1="margin"
      :x2="margin"
      :y2="svgHeight - margin"
      stroke="#fff"
      stroke-width="3"
    />

    <!-- Bridge line -->
    <line
      :x1="margin + spec.scale_length_mm * scale"
      :y1="margin"
      :x2="margin + spec.scale_length_mm * scale"
      :y2="svgHeight - margin"
      stroke="#888"
      stroke-width="2"
      stroke-dasharray="4,4"
    />

    <!-- Risk legend (if enabled) -->
    <g
      v-if="showRiskLegend"
      transform="translate(10, 10)"
    >
      <rect
        x="0"
        y="0"
        width="120"
        height="80"
        fill="#000"
        opacity="0.8"
        rx="4"
      />

      <!-- GREEN -->
      <circle
        cx="15"
        cy="15"
        r="5"
        :fill="RISK_COLORS.GREEN"
      />
      <text
        x="25"
        y="19"
        font-size="12"
        fill="#fff"
      >Safe</text>

      <!-- YELLOW -->
      <circle
        cx="15"
        cy="35"
        r="5"
        :fill="RISK_COLORS.YELLOW"
      />
      <text
        x="25"
        y="39"
        font-size="12"
        fill="#fff"
      >Caution</text>

      <!-- RED -->
      <circle
        cx="15"
        cy="55"
        r="5"
        :fill="RISK_COLORS.RED"
      />
      <text
        x="25"
        y="59"
        font-size="12"
        fill="#fff"
      >Warning</text>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type {
  FretboardSpec,
  ToolpathSummary,
} from "@/stores/instrumentGeometryStore";

// ============================================================================
// Props
// ============================================================================

interface Props {
  spec: FretboardSpec;
  toolpaths: ToolpathSummary[];
  width?: number;
  height?: number;
  showLabels?: boolean;
  showInlays?: boolean;
  showRiskLegend?: boolean;
  riskColoring?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  width: 800,
  height: 200,
  showLabels: true,
  showInlays: true,
  showRiskLegend: true,
  riskColoring: true,
});

// ============================================================================
// Constants
// ============================================================================

const RISK_COLORS = {
  GREEN: "#22c55e",
  YELLOW: "#eab308",
  RED: "#ef4444",
  UNKNOWN: "#6b7280",
};

const margin = 40;
const svgWidth = computed(() => props.width);
const svgHeight = computed(() => props.height);
const centerY = computed(() => (svgHeight.value - 2 * margin) / 2);

// Scale factor to fit fretboard in SVG viewport
const scale = computed(() => {
  const availableWidth = svgWidth.value - 2 * margin;
  return availableWidth / props.spec.scale_length_mm;
});

// ============================================================================
// Computed
// ============================================================================

/**
 * Generate fretboard outline path (tapered trapezoid)
 */
const fretboardOutline = computed(() => {
  const nutW = props.spec.nut_width_mm * scale.value;
  const bridgeW = props.spec.bridge_width_mm * scale.value;
  const length = props.spec.scale_length_mm * scale.value;

  const x1 = margin;
  const x2 = margin + length;
  const y1 = margin + centerY.value - nutW / 2;
  const y2 = margin + centerY.value + nutW / 2;
  const y3 = margin + centerY.value + bridgeW / 2;
  const y4 = margin + centerY.value - bridgeW / 2;

  return `M ${x1},${y1} L ${x1},${y2} L ${x2},${y3} L ${x2},${y4} Z`;
});

/**
 * Get fret position using equal temperament formula
 */
function getFretPosition(fretNumber: number): number {
  if (fretNumber === 0) return 0;
  const scaleLength = props.spec.scale_length_mm;
  // Distance from nut: L * (1 - 2^(-n/12))
  return scaleLength * (1 - Math.pow(2, -fretNumber / 12));
}

/**
 * Get fret color based on risk (Wave 16 enhancement)
 */
function getFretColor(toolpath: ToolpathSummary): string {
  if (!props.riskColoring) {
    return "#4ade80"; // Default green
  }

  // Risk assessment based on feed rate and spindle speed
  // This is a simplified heuristic - real risk comes from feasibility scoring
  const feedRatio = toolpath.feed_rate / 1200; // Normalize to typical 1200 mm/min
  const rpmRatio = toolpath.spindle_rpm / 18000; // Normalize to typical 18k RPM

  // High feed + low RPM = potential chipload issues (YELLOW/RED)
  if (feedRatio > 1.2 || rpmRatio < 0.8) {
    return RISK_COLORS.YELLOW;
  } else if (feedRatio > 1.5 || rpmRatio < 0.6) {
    return RISK_COLORS.RED;
  }

  return RISK_COLORS.GREEN;
}

/**
 * Get fret stroke color (highlights selected or problematic frets)
 */
function getFretStrokeColor(toolpath: ToolpathSummary): string {
  const color = getFretColor(toolpath);
  // Darken stroke for contrast
  if (color === RISK_COLORS.RED) return "#b91c1c";
  if (color === RISK_COLORS.YELLOW) return "#a16207";
  return "#15803d";
}
</script>

<style scoped>
.fretboard-preview {
  border: 1px solid #333;
  border-radius: 4px;
  background: #0a0a0a;
}

.fretboard-preview text {
  user-select: none;
  pointer-events: none;
}
</style>
