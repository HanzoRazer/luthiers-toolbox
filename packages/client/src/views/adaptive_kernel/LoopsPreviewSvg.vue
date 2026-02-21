<template>
  <svg
    :viewBox="`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`"
    class="w-full h-full"
  >
    <!-- pocket loops -->
    <g
      fill="none"
      stroke="#0f766e"
      stroke-width="0.3"
    >
      <polyline
        v-for="(loop, idx) in previewLoops"
        :key="idx"
        :points="loop.pts.map(([x,y]: [number, number]) => `${x},${y}`).join(' ')"
      />
    </g>

    <!-- toolpath preview -->
    <g
      v-if="showToolpathPreview && toolpathSegments.length"
      fill="none"
    >
      <polyline
        v-for="(seg, idx) in toolpathSegments"
        :key="`tp-${idx}`"
        :points="seg.pts.map(([x,y]) => `${x},${y}`).join(' ')"
        :stroke="seg.kind === 'rapid' ? '#9ca3af' : '#1d4ed8'"
        :stroke-width="seg.kind === 'rapid' ? 0.2 : 0.35"
        :stroke-dasharray="seg.kind === 'rapid' ? '1,1' : 'none'"
      />
    </g>

    <!-- overlays -->
    <g v-if="overlays.length">
      <circle
        v-for="(o, idx) in overlays"
        :key="`ov-${idx}`"
        :cx="o.x"
        :cy="o.y"
        :r="(o.radius || 2)"
        :fill="overlayColor(o)"
        fill-opacity="0.35"
        stroke="#111827"
        stroke-width="0.2"
      />
    </g>
  </svg>
</template>

<script setup lang="ts">
interface PreviewLoop {
  pts: [number, number][]
}

interface ToolpathSegment {
  pts: [number, number][]
  kind: 'rapid' | 'cut'
}

interface Overlay {
  x: number
  y: number
  radius?: number
  type?: string
  severity?: string
}

interface ViewBox {
  x: number
  y: number
  w: number
  h: number
}

defineProps<{
  previewLoops: PreviewLoop[]
  viewBox: ViewBox
  showToolpathPreview: boolean
  toolpathSegments: ToolpathSegment[]
  overlays: Overlay[]
}>()

function overlayColor(o: Overlay): string {
  if (o.type === 'tight_radius') {
    if (o.severity === 'high') return '#ef4444'
    if (o.severity === 'medium') return '#f97316'
    return '#facc15'
  }
  if (o.type === 'slowdown') return '#3b82f6'
  return '#22c55e'
}
</script>
