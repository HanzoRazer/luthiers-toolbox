<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between text-[11px] text-gray-600">
      <div class="flex items-center gap-3">
        <span class="font-semibold text-sm text-gray-800">Backplot</span>
        <span v-if="stats" class="text-[10px] text-gray-500">
          {{ timeLabel }} · {{ moveCountLabel }}
        </span>
      </div>
      <div class="flex items-center gap-3">
        <label class="inline-flex items-center gap-1 cursor-pointer">
          <input
            type="checkbox"
            :checked="showToolpath"
            @change="emit('update:showToolpath', ($event.target as HTMLInputElement).checked)"
          />
          <span>Toolpath</span>
        </label>
        <label class="inline-flex items-center gap-1 cursor-pointer">
          <input type="checkbox" :checked="showOverlays" disabled />
          <span>Overlays</span>
        </label>
      </div>
    </div>

    <div class="border rounded bg-gray-50 flex items-center justify-center min-h-[260px]">
      <svg
        v-if="segments.length || loops.length"
        :viewBox="`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`"
        class="w-full h-full"
      >
        <!-- Boundary loops -->
        <g v-if="loops.length" fill="none" :stroke="boundaryColor || '#0f766e'" stroke-width="0.3">
          <polyline
            v-for="(loop, idx) in loops"
            :key="`loop-${idx}`"
            :points="loop.pts.map(([x,y]) => `${x},${y}`).join(' ')"
          />
        </g>

        <!-- Toolpath segments -->
        <g v-if="showToolpath && segments.length" fill="none">
          <line
            v-for="seg in segments"
            :key="`seg-${seg.idx}`"
            :x1="seg.x1n"
            :y1="seg.y1n"
            :x2="seg.x2n"
            :y2="seg.y2n"
            :stroke="segmentStroke(seg)"
            :stroke-width="seg.isRapid ? 0.6 : 0.9"
            stroke-linecap="round"
            @mouseenter="emit('segment-hover', { index: seg.idx, kind: seg.kind, severity: seg.severity })"
          />
        </g>

        <!-- Overlays -->
        <g v-if="showOverlays && overlays && overlays.length">
          <circle
            v-for="(ov, idx) in overlays"
            :key="`ov-${idx}`"
            :cx="ov.x"
            :cy="ov.y"
            :r="ov.radius || 2"
            :fill="overlayFill(ov)"
            fill-opacity="0.35"
            stroke="#111827"
            stroke-width="0.2"
            @mouseenter="emit('overlay-hover', { index: idx, overlay: ov })"
          />
        </g>
      </svg>
      <div v-else class="text-xs text-gray-500">No geometry to display.</div>
    </div>

    <!-- Legend -->
    <div class="flex flex-wrap gap-3 text-[11px] text-gray-500">
      <div class="inline-flex items-center gap-1">
        <span class="inline-block w-4 h-[2px] bg-[#0f766e]"></span>
        <span>Boundary</span>
      </div>
      <div class="inline-flex items-center gap-1">
        <span class="inline-block w-4 h-[2px] bg-[#1d4ed8]"></span>
        <span>Cut (normal)</span>
      </div>
      <div class="inline-flex items-center gap-1">
        <span class="inline-block w-4 h-[2px] bg-[#22c55e]"></span>
        <span>Cut (mild slowdown)</span>
      </div>
      <div class="inline-flex items-center gap-1">
        <span class="inline-block w-4 h-[2px] bg-[#f97316]"></span>
        <span>Cut (medium slowdown)</span>
      </div>
      <div class="inline-flex items-center gap-1">
        <span class="inline-block w-4 h-[2px] bg-[#ef4444]"></span>
        <span>Cut (heavy / collision)</span>
      </div>
      <div class="inline-flex items-center gap-1">
        <span class="inline-block w-4 h-[2px]" style="border-bottom:1px dashed #9ca3af"></span>
        <span>Rapid</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { BackplotLoop, BackplotMove, BackplotOverlay } from '@/types/cam'

interface Segment {
  idx: number
  x1: number
  y1: number
  x2: number
  y2: number
  x1n: number
  y1n: number
  x2n: number
  y2n: number
  isRapid: boolean
  kind: 'rapid' | 'cut'
  severity: 'none' | 'warning' | 'error'
}

const props = withDefaults(defineProps<{
  loops: BackplotLoop[]
  moves: BackplotMove[]
  overlays?: BackplotOverlay[] | null
  simIssues?: any[] | null
  showToolpath?: boolean
  showOverlays?: boolean
  autoFit?: boolean
  boundaryColor?: string
}>(), {
  showToolpath: true,
  showOverlays: true,
  autoFit: true,
  boundaryColor: '#0f766e'
})

const emit = defineEmits<{
  (e: 'update:showToolpath', value: boolean): void
  (e: 'segment-hover', payload: { index: number; kind: 'rapid' | 'cut'; severity: string }): void
  (e: 'overlay-hover', payload: { index: number; overlay: BackplotOverlay }): void
}>()

const stats = computed(() => {
  // Extract stats from moves metadata if available
  return null
})

const timeLabel = computed(() => {
  if (!stats.value) return '—'
  const t = (stats.value as any).time_s ?? (stats.value as any).time_jerk_s ?? null
  return typeof t === 'number' ? `${t.toFixed(1)}s` : '—'
})

const moveCountLabel = computed(() => {
  const c = props.moves?.length ?? 0
  return `${c} moves`
})

// Map sim issues -> move index -> severity
const severityByMoveIdx = computed(() => {
  const map = new Map<number, string>()
  if (!props.simIssues) return map
  for (const issue of props.simIssues) {
    const idx = issue.move_idx
    if (typeof idx === 'number') {
      map.set(idx, issue.severity || 'warning')
    }
  }
  return map
})

const viewBox = computed(() => {
  const allPts: [number, number][] = []
  props.loops.forEach(l => l.pts.forEach(p => allPts.push(p)))
  
  if (!allPts.length && props.moves) {
    props.moves.forEach(mv => {
      if (typeof mv.x === 'number' && typeof mv.y === 'number') {
        allPts.push([mv.x, mv.y])
      }
    })
  }

  if (!allPts.length) return { x: 0, y: 0, w: 100, h: 60 }

  const xs = allPts.map(p => p[0])
  const ys = allPts.map(p => p[1])
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const pad = 5

  return {
    x: minX - pad,
    y: minY - pad,
    w: maxX - minX + 2 * pad,
    h: maxY - minY + 2 * pad
  }
})

const segments = computed<Segment[]>(() => {
  const moves = props.moves || []
  if (!moves.length) return []

  const rawSegs: Omit<Segment, 'x1n' | 'y1n' | 'x2n' | 'y2n'>[] = []
  let x = 0, y = 0

  moves.forEach((mv, idx) => {
    const nx = typeof mv.x === 'number' ? mv.x : x
    const ny = typeof mv.y === 'number' ? mv.y : y

    if (nx !== x || ny !== y) {
      const code = (mv.code || '').toUpperCase()
      const isRapid = code === 'G0'
      const sev = severityByMoveIdx.value.get(idx)
      const severity: 'none' | 'warning' | 'error' =
        sev === 'error' ? 'error' : sev === 'warning' ? 'warning' : 'none'

      rawSegs.push({
        idx,
        x1: x,
        y1: y,
        x2: nx,
        y2: ny,
        isRapid,
        kind: isRapid ? 'rapid' : 'cut',
        severity
      })
    }
    x = nx
    y = ny
  })

  if (!rawSegs.length) return []

  // Compute bounding box and normalize
  let minX = rawSegs[0].x1, maxX = rawSegs[0].x1
  let minY = rawSegs[0].y1, maxY = rawSegs[0].y1

  for (const s of rawSegs) {
    minX = Math.min(minX, s.x1, s.x2)
    maxX = Math.max(maxX, s.x1, s.x2)
    minY = Math.min(minY, s.y1, s.y2)
    maxY = Math.max(maxY, s.y1, s.y2)
  }

  const width = maxX - minX || 1
  const height = maxY - minY || 1
  const pad = 5
  const sx = (100 - pad * 2) / width
  const sy = (100 - pad * 2) / height
  const scale = Math.min(sx, sy)
  const cx = (minX + maxX) / 2
  const cy = (minY + maxY) / 2

  return rawSegs.map(s => {
    const x1c = (s.x1 - cx) * scale
    const y1c = (s.y1 - cy) * scale
    const x2c = (s.x2 - cx) * scale
    const y2c = (s.y2 - cy) * scale

    return {
      ...s,
      x1n: x1c + 50,
      y1n: 50 - y1c,
      x2n: x2c + 50,
      y2n: 50 - y2c
    }
  })
})

function overlayFill(ov: BackplotOverlay): string {
  if (ov.type === 'tight_radius') {
    if (ov.severity === 'high') return '#ef4444'
    if (ov.severity === 'medium') return '#f97316'
    return '#facc15'
  }
  if (ov.type === 'slowdown') return '#3b82f6'
  if (ov.type === 'collision') return '#ef4444'
  return '#22c55e'
}

function segmentStroke(seg: Segment): string {
  if (seg.severity === 'error') return '#b91c1c'
  if (seg.severity === 'warning') return '#f97316'
  if (seg.isRapid) return '#9ca3af'
  return '#0f172a'
}
</script>
