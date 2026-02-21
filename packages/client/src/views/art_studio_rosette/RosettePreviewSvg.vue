<template>
  <div
    v-if="preview && preview.paths.length"
    class="w-full h-full"
  >
    <svg
      :viewBox="svgViewBox"
      preserveAspectRatio="xMidYMid meet"
      class="w-full h-full"
    >
      <rect
        v-if="previewBBox"
        :x="previewBBox[0]"
        :y="previewBBox[1]"
        :width="previewBBox[2] - previewBBox[0]"
        :height="previewBBox[3] - previewBBox[1]"
        fill="none"
        stroke="#e5e7eb"
        stroke-width="0.2"
      />
      <g>
        <polyline
          v-for="(path, idx) in preview.paths"
          :key="idx"
          :points="polylinePoints(path.points)"
          fill="none"
          stroke="#111827"
          stroke-width="0.4"
        />
      </g>
    </svg>
  </div>
  <svg
    v-else
    viewBox="-60 -60 120 120"
    class="w-full h-full"
    style="max-width: 240px; max-height: 240px;"
  >
    <!-- Placeholder rosette graphic -->
    <defs>
      <pattern
        id="herringbone"
        patternUnits="userSpaceOnUse"
        width="8"
        height="8"
        patternTransform="rotate(45)"
      >
        <line
          x1="0"
          y1="0"
          x2="0"
          y2="8"
          stroke="#d1d5db"
          stroke-width="2"
        />
      </pattern>
    </defs>
    <!-- Outer ring -->
    <circle
      cx="0"
      cy="0"
      r="50"
      fill="none"
      stroke="#9ca3af"
      stroke-width="0.5"
      stroke-dasharray="2,2"
    />
    <!-- Decorative band -->
    <circle
      cx="0"
      cy="0"
      r="45"
      fill="none"
      stroke="#6b7280"
      stroke-width="8"
    />
    <circle
      cx="0"
      cy="0"
      r="45"
      fill="url(#herringbone)"
      opacity="0.3"
    />
    <!-- Middle ring -->
    <circle
      cx="0"
      cy="0"
      r="35"
      fill="none"
      stroke="#9ca3af"
      stroke-width="0.5"
      stroke-dasharray="2,2"
    />
    <!-- Inner decorative -->
    <circle
      cx="0"
      cy="0"
      r="30"
      fill="none"
      stroke="#6b7280"
      stroke-width="6"
    />
    <!-- Center circle -->
    <circle
      cx="0"
      cy="0"
      r="20"
      fill="none"
      stroke="#9ca3af"
      stroke-width="0.5"
      stroke-dasharray="2,2"
    />
    <!-- Radial segments (12 divisions) -->
    <g opacity="0.2">
      <line
        v-for="i in 12"
        :key="i"
        x1="0"
        y1="0"
        :x2="Math.cos((i * 30 - 90) * Math.PI / 180) * 50"
        :y2="Math.sin((i * 30 - 90) * Math.PI / 180) * 50"
        stroke="#6b7280"
        stroke-width="0.3"
      />
    </g>
    <!-- Center dot -->
    <circle
      cx="0"
      cy="0"
      r="2"
      fill="#9ca3af"
    />
    <!-- Placeholder text -->
    <text
      x="0"
      y="68"
      text-anchor="middle"
      class="fill-gray-400 text-[8px]"
      font-family="system-ui"
    >
      Click "Preview Rosette" to generate
    </text>
  </svg>
</template>

<script setup lang="ts">
interface RosettePath {
  points: [number, number][]
}

interface RosettePreview {
  job_id: string
  pattern_type: string
  segments: number
  inner_radius: number
  outer_radius: number
  units: string
  preset: string | null
  name: string | null
  paths: RosettePath[]
  bbox: [number, number, number, number]
}

defineProps<{
  preview: RosettePreview | null
  previewBBox: [number, number, number, number] | null
  svgViewBox: string
}>()

function polylinePoints(pts: [number, number][]): string {
  return pts.map(([x, y]) => `${x},${y}`).join(' ')
}
</script>
