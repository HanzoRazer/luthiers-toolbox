<script setup lang="ts">
/**
 * ToolpathPreviewSvg.vue - SVG preview of toolpath segments
 * Extracted from BlueprintPresetPanel.vue
 */
import { computed } from 'vue'

export interface Segment {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface MovePoint {
  x?: number
  y?: number
}

const props = defineProps<{
  moves: MovePoint[]
  placeholderText?: string
}>()

// Convert moves to line segments
function movesToSegments(moves: MovePoint[]): Segment[] {
  const segs: Segment[] = []
  let last = { x: 0, y: 0, has: false }

  for (const m of moves) {
    const x = typeof m.x === 'number' ? m.x : last.x
    const y = typeof m.y === 'number' ? m.y : last.y
    if (last.has) {
      segs.push({ x1: last.x, y1: last.y, x2: x, y2: y })
    }
    last = { x, y, has: true }
  }
  return segs
}

// Normalize segments to fit in viewBox
function normalizeSegments(segs: Segment[]): Segment[] {
  if (!segs.length) return []
  let minX = segs[0].x1, maxX = segs[0].x1
  let minY = segs[0].y1, maxY = segs[0].y1

  for (const s of segs) {
    minX = Math.min(minX, s.x1, s.x2)
    maxX = Math.max(maxX, s.x1, s.x2)
    minY = Math.min(minY, s.y1, s.y2)
    maxY = Math.max(maxY, s.y1, s.y2)
  }

  const dx = maxX - minX || 1
  const dy = maxY - minY || 1
  const scale = 90 / Math.max(dx, dy)
  const offsetX = (100 - dx * scale) / 2
  const offsetY = (100 - dy * scale) / 2

  return segs.map((s) => ({
    x1: (s.x1 - minX) * scale + offsetX,
    y1: 100 - ((s.y1 - minY) * scale + offsetY),
    x2: (s.x2 - minX) * scale + offsetX,
    y2: 100 - ((s.y2 - minY) * scale + offsetY)
  }))
}

function segToPoints(seg: Segment): string {
  return `${seg.x1},${seg.y1} ${seg.x2},${seg.y2}`
}

const segments = computed(() => {
  const raw = movesToSegments(props.moves)
  return normalizeSegments(raw)
})
</script>

<template>
  <div class="span-2">
    <h3 class="section-title">🔍 Toolpath Preview</h3>
    <div class="preview-container">
      <svg
        v-if="segments.length"
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid meet"
        class="preview-svg"
      >
        <polyline
          v-for="(seg, idx) in segments"
          :key="idx"
          :points="segToPoints(seg)"
          fill="none"
          stroke="lime"
          stroke-width="0.4"
        />
      </svg>
      <div
        v-else
        class="preview-placeholder"
      >
        {{ placeholderText || 'No toolpath to display' }}
      </div>
    </div>
    <div
      v-if="segments.length"
      class="preview-footer"
    >
      {{ segments.length }} segments
    </div>
  </div>
</template>

<style scoped>
.section-title {
  font-size: 1.1em;
  margin-bottom: 10px;
}

.span-2 {
  grid-column: span 2;
}

.preview-container {
  width: 100%;
  height: 300px;
  background: #1a1a1a;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.preview-svg {
  width: 100%;
  height: 100%;
}

.preview-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 0.9em;
}

.preview-footer {
  margin-top: 10px;
  text-align: center;
  font-size: 0.9em;
  color: #666;
}
</style>
