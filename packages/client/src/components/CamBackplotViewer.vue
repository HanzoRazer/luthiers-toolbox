<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
CAM Backplot Viewer Component

Enhanced in Phase 24.5: Machine Envelope Integration
Repository: HanzoRazer/luthiers-toolbox
Updated: January 2025

Features:
- Toolpath visualization with moves and overlays
- Machine work envelope display with over-travel detection
- Playhead animation support
- Focus point and zoom controls
-->

<template>
  <div class="border rounded-lg p-3 bg-white text-[11px] space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-xs font-semibold text-gray-700">CAM Backplot</h3>
        <p class="text-[11px] text-gray-500">
          Visualize toolpath, feeds, envelope, and playhead
        </p>
      </div>
      <div class="text-right text-[10px] text-gray-500 space-y-0.5">
        <div v-if="stats">
          moves: {{ stats.move_count ?? visibleSegmentCount }} ·
          time ≈
          <span v-if="stats.time_s != null">
            {{ stats.time_s.toFixed(2) }} s
          </span>
          <span v-else>—</span>
        </div>
        <div>
          span: {{ bboxWidth.toFixed(1) }} × {{ bboxHeight.toFixed(1) }}
          {{ unitsLabel }}
        </div>
        <div v-if="hasMachineLimits">
          <span
            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full"
            :class="overTravel ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'"
          >
            <span
              class="w-1.5 h-1.5 rounded-full"
              :class="overTravel ? 'bg-rose-500' : 'bg-emerald-500'"
            />
            <span class="uppercase">
              {{ overTravel ? 'Over-travel' : 'Within envelope' }}
            </span>
          </span>
        </div>
      </div>
    </div>

    <!-- Backplot canvas -->
    <div class="border rounded bg-gray-50 flex items-center justify-center">
      <svg
        v-if="hasSegments"
        :viewBox="viewBox"
        class="w-full h-64"
        preserveAspectRatio="xMidYMid meet"
      >
        <!-- Machine envelope (limits) -->
        <rect
          v-if="hasMachineLimits"
          :x="machineRect.x"
          :y="machineRect.y"
          :width="machineRect.w"
          :height="machineRect.h"
          fill="none"
          :stroke="overTravel ? '#ef4444' : '#22c55e'"
          stroke-dasharray="4 4"
          stroke-width="0.6"
        />

        <!-- Path bounds -->
        <rect
          v-if="hasBounds"
          :x="bounds.minX"
          :y="bounds.minY"
          :width="boundsWidth"
          :height="boundsHeight"
          fill="none"
          stroke="#9ca3af"
          stroke-dasharray="3 3"
          stroke-width="0.4"
        />

        <!-- Path segments (feed-colored, playhead-limited) -->
        <g>
          <line
            v-for="(seg, idx) in visibleSegments"
            :key="'seg-' + idx"
            :x1="seg.x1"
            :y1="seg.y1"
            :x2="seg.x2"
            :y2="seg.y2"
            :stroke="segmentColor(seg)"
            :stroke-width="segmentStrokeWidth(seg)"
            stroke-linecap="round"
          />
        </g>

        <!-- Issues overlay (optional: simIssues/overlays) -->
        <g v-if="simIssues && simIssues.length">
          <circle
            v-for="(issue, idx) in issueMarkers"
            :key="'iss-' + idx"
            :cx="issue.x"
            :cy="issue.y"
            :r="issueRadius"
            :fill="issue.color"
            fill-opacity="0.7"
          />
        </g>
      </svg>

      <div
        v-else
        class="text-[11px] text-gray-500 py-10"
      >
        No toolpath moves. Run an adaptive plan, simulation, or load G-code to view the path here.
      </div>
    </div>

    <!-- Playhead & legend -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <!-- Play slider -->
      <div class="flex items-center gap-2 flex-1 min-w-[180px]">
        <span class="text-[10px] text-gray-500">Play</span>
        <input
          type="range"
          min="0"
          max="100"
          v-model.number="playPercent"
          class="flex-1"
        />
        <span class="text-[10px] text-gray-500">
          {{ visibleSegmentCount }}/{{ totalSegmentCount }}
        </span>
      </div>

      <!-- Legend -->
      <div class="flex flex-wrap items-center gap-3 text-[10px] text-gray-500">
        <div class="flex items-center gap-1">
          <span class="inline-block w-3 h-[2px]" :style="{ background: cutColor }" />
          <span>Cut</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="inline-block w-3 h-[2px]" :style="{ background: rapidColor }" />
          <span>Rapid</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="inline-block w-3 h-[2px]" :style="{ background: slowColor }" />
          <span>Slow / feed floor</span>
        </div>
        <div
          v-if="simIssues && simIssues.length"
          class="flex items-center gap-1"
        >
          <span class="inline-block w-2 h-2 rounded-full" :style="{ background: issueColor }" />
          <span>Issues</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

type MoveCode = 'G0' | 'G1' | 'G2' | 'G3' | string

interface Move {
  code?: MoveCode
  x?: number | null
  y?: number | null
  z?: number | null
  f?: number | null
  [key: string]: any
}

interface Stats {
  move_count?: number | null
  time_s?: number | null
  [key: string]: any
}

interface SimIssue {
  x?: number | null
  y?: number | null
  severity?: 'error' | 'warning' | 'info'
  [key: string]: any
}

interface MachineLimits {
  min_x?: number | null
  max_x?: number | null
  min_y?: number | null
  max_y?: number | null
  min_z?: number | null
  max_z?: number | null
}

const props = defineProps<{
  moves: Move[]
  stats?: Stats | null
  overlays?: any[] | null
  simIssues?: SimIssue[] | null
  units?: 'mm' | 'inch'
  feedFloor?: number
  machineLimits?: MachineLimits | null
}>()

// internal playhead: 0–100%
const playPercent = ref(100)

// colors (keep here for easy tuning)
const cutColor = '#1d4ed8'   // blue
const rapidColor = '#6b7280' // gray
const slowColor = '#f97316'  // orange
const issueColor = '#ef4444' // red

// basic feed floor hint (mm/min); can be overridden via prop
const feedFloorDefault = 200.0

// Preprocess moves into segments
interface Segment {
  x1: number
  y1: number
  x2: number
  y2: number
  code: MoveCode
  f?: number | null
}

const segments = computed<Segment[]>(() => {
  const segs: Segment[] = []
  const ms = props.moves || []
  let last: Move | null = null

  for (const m of ms) {
    const hasXY = m.x != null && m.y != null
    if (!last) {
      last = hasXY ? m : null
      continue
    }
    if (hasXY && last.x != null && last.y != null) {
      segs.push({
        x1: Number(last.x),
        y1: Number(last.y),
        x2: Number(m.x),
        y2: Number(m.y),
        code: (m.code || last.code || 'G1') as MoveCode,
        f: m.f ?? last.f ?? null
      })
      last = m
    } else if (hasXY) {
      last = m
    }
  }

  return segs
})

const totalSegmentCount = computed(() => segments.value.length)

const visibleSegmentCount = computed(() => {
  if (!segments.value.length) return 0
  const pct = playPercent.value / 100
  return Math.max(1, Math.round(segments.value.length * pct))
})

const visibleSegments = computed<Segment[]>(() => {
  if (!segments.value.length) return []
  return segments.value.slice(0, visibleSegmentCount.value)
})

// Bounds / viewBox
const bounds = computed(() => {
  const segs = segments.value
  if (!segs.length) {
    return { minX: 0, minY: 0, maxX: 100, maxY: 50 }
  }
  let minX = Number.POSITIVE_INFINITY
  let minY = Number.POSITIVE_INFINITY
  let maxX = Number.NEGATIVE_INFINITY
  let maxY = Number.NEGATIVE_INFINITY

  const push = (x: number, y: number) => {
    if (x < minX) minX = x
    if (y < minY) minY = y
    if (x > maxX) maxX = x
    if (y > maxY) maxY = y
  }

  for (const s of segs) {
    push(s.x1, s.y1)
    push(s.x2, s.y2)
  }

  if (!isFinite(minX) || !isFinite(minY) || !isFinite(maxX) || !isFinite(maxY)) {
    return { minX: 0, minY: 0, maxX: 100, maxY: 50 }
  }

  // If degenerate, give it a minimum span
  if (maxX - minX < 1) {
    maxX = minX + 1
  }
  if (maxY - minY < 1) {
    maxY = minY + 1
  }

  return { minX, minY, maxX, maxY }
})

const hasSegments = computed(() => segments.value.length > 0)
const hasBounds = computed(() => hasSegments.value)

const boundsWidth = computed(() => bounds.value.maxX - bounds.value.minX)
const boundsHeight = computed(() => bounds.value.maxY - bounds.value.minY)

const bboxWidth = computed(() => boundsWidth.value)
const bboxHeight = computed(() => boundsHeight.value)

const viewBox = computed(() => {
  const pad = 5
  const { minX, minY, maxX, maxY } = bounds.value
  const w = maxX - minX
  const h = maxY - minY
  return `${minX - pad} ${minY - pad} ${w + 2 * pad} ${h + 2 * pad}`
})

const unitsLabel = computed(() => {
  if (props.units === 'inch') return 'in'
  // default to stats or mm
  return 'mm'
})

// Machine limits
const hasMachineLimits = computed(() => {
  const lim = props.machineLimits
  if (!lim) return false
  return (
    lim.min_x != null &&
    lim.max_x != null &&
    lim.min_y != null &&
    lim.max_y != null
  )
})

const machineRect = computed(() => {
  const lim = props.machineLimits || {}
  const minX = Number(lim.min_x ?? bounds.value.minX)
  const maxX = Number(lim.max_x ?? bounds.value.maxX)
  const minY = Number(lim.min_y ?? bounds.value.minY)
  const maxY = Number(lim.max_y ?? bounds.value.maxY)
  return {
    x: minX,
    y: minY,
    w: maxX - minX,
    h: maxY - minY
  }
})

const overTravel = computed(() => {
  if (!hasMachineLimits.value) return false
  const lim = props.machineLimits!
  const b = bounds.value
  if (lim.min_x != null && b.minX < lim.min_x) return true
  if (lim.max_x != null && b.maxX > lim.max_x) return true
  if (lim.min_y != null && b.minY < lim.min_y) return true
  if (lim.max_y != null && b.maxY > lim.max_y) return true
  return false
})

// Feed-based coloring
function segmentColor (seg: Segment): string {
  const code = (seg.code || '').toUpperCase()
  const f = seg.f ?? null
  const feedFloor = props.feedFloor ?? feedFloorDefault

  if (code === 'G0') {
    return rapidColor
  }

  if (f != null && f > 0 && f < feedFloor) {
    return slowColor
  }

  return cutColor
}

function segmentStrokeWidth (seg: Segment): number {
  const code = (seg.code || '').toUpperCase()
  if (code === 'G0') return 0.4
  return 0.6
}

// Issues -> markers
const issueRadius = 0.8

const issueMarkers = computed(() => {
  const issues = props.simIssues || []
  const list: Array<{ x: number; y: number; color: string }> = []

  for (const iss of issues) {
    const x = iss.x
    const y = iss.y
    if (x == null || y == null) continue

    let color = issueColor
    if (iss.severity === 'warning') {
      color = '#facc15' // amber
    } else if (iss.severity === 'info') {
      color = '#0ea5e9' // cyan
    }

    list.push({ x: Number(x), y: Number(y), color })
  }

  return list
})
</script>
