<template>
  <div class="curve-lab p-4 space-y-4">
    <div class="header">
      <h3 class="text-xl font-semibold text-gray-800">
        🎨 Curve Lab — Offsets · Fillets · Clothoid · Fairing
      </h3>
      <p class="text-sm text-gray-600 mt-1">
        Advanced curve operations for CAD/CAM lutherie work
      </p>
    </div>

    <!-- Mode Selection -->
    <div class="controls flex gap-3 items-center flex-wrap">
      <button
        v-for="m in modes"
        :key="m.id"
        @click="mode = m.id"
        :class="['btn', mode === m.id ? 'btn-active' : 'btn-normal']"
      >
        {{ m.label }}
      </button>
      <span class="ml-2 text-gray-600 font-medium">Mode: {{ currentMode?.label }}</span>
    </div>

    <!-- Mode-Specific Controls -->
    <div v-if="mode === 'offset'" class="params flex gap-3 items-center flex-wrap">
      <label class="param-label">
        Distance (mm)
        <input
          type="number"
          v-model.number="offsetDist"
          class="param-input"
          step="0.5"
        />
      </label>
      <label class="param-label">
        Join Type
        <select v-model="join" class="param-select">
          <option value="round">Round</option>
          <option value="miter">Miter</option>
          <option value="bevel">Bevel</option>
        </select>
      </label>
      <button @click="doOffset" class="btn btn-primary">Apply Offset</button>
    </div>

    <div v-if="mode === 'fillet'" class="params flex gap-3 items-center flex-wrap">
      <label class="param-label">
        Radius (mm)
        <input
          type="number"
          v-model.number="filletR"
          class="param-input"
          step="0.5"
          min="0.1"
        />
      </label>
      <button @click="doFillet" class="btn btn-primary">Apply Fillet</button>
    </div>

    <div v-if="mode === 'fair'" class="params flex gap-3 items-center flex-wrap">
      <label class="param-label">
        λ (Lambda)
        <input
          type="number"
          v-model.number="lam"
          class="param-input"
          step="1"
          min="0"
        />
      </label>
      <label class="param-checkbox">
        <input type="checkbox" v-model="preserve" />
        Preserve endpoints
      </label>
      <button @click="doFair" class="btn btn-primary">Apply Fairing</button>
    </div>

    <div v-if="mode === 'clothoid'" class="params flex gap-3 items-center flex-wrap">
      <span class="text-sm text-gray-700">
        Pick: p0 (green) → t0 (tangent) → p1 (green) → t1 (tangent)
      </span>
      <button @click="resetClothoid" class="btn btn-normal">Reset</button>
      <button @click="doClothoid" class="btn btn-primary">Blend</button>
    </div>

    <!-- Canvas -->
    <canvas
      ref="canvas"
      @click="onClick"
      class="canvas-drawing"
      :style="{ width: '100%', height: canvasHeight + 'px' }"
    ></canvas>

    <!-- Actions -->
    <div class="actions flex gap-3">
      <button @click="clearAll" class="btn btn-danger">Clear All</button>
      <button @click="undo" class="btn btn-normal">Undo</button>
      <button @click="exportJSON" class="btn btn-success">Export JSON</button>
      <button @click="exportDXF" class="btn btn-success">Export DXF</button>
    </div>

    <!-- Info Display -->
    <div class="info text-sm text-gray-600">
      Points: {{ pts.length }} | History: {{ stack.length }} states
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { offsetPolycurve, autoFillet, fairCurve, blendClothoid } from '../utils/curvemath'

type Point = { x: number; y: number }
type Mode = 'draw' | 'offset' | 'fillet' | 'fair' | 'clothoid'

const modes = [
  { id: 'draw' as Mode, label: '✏️ Draw' },
  { id: 'offset' as Mode, label: '↔️ Offset' },
  { id: 'fillet' as Mode, label: '⌓ Fillet' },
  { id: 'fair' as Mode, label: '〰️ Fair' },
  { id: 'clothoid' as Mode, label: '⤴️ Clothoid' }
]

const mode = ref<Mode>('draw')
const currentMode = computed(() => modes.find(m => m.id === mode.value))

const canvas = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D
let W = 0
let H = 0
let dpr = 1

const pts = ref<Point[]>([])
const stack: Point[][] = []

// Parameters
const offsetDist = ref(10)
const join = ref<'round' | 'miter' | 'bevel'>('round')
const filletR = ref(6)
const lam = ref(10)
const preserve = ref(true)
const canvasHeight = ref(400)

// Clothoid picking state
const cPick = ref<{
  p0?: Point
  t0?: Point
  p1?: Point
  t1?: Point
}>({})

// History management
function pushHistory() {
  stack.push(pts.value.map(p => ({ x: p.x, y: p.y })))
}

function undo() {
  if (stack.length) {
    pts.value = stack.pop()!
    draw()
  }
}

function clearAll() {
  pushHistory()
  pts.value = []
  cPick.value = {}
  draw()
}

function exportJSON() {
  const data = JSON.stringify(
    { points: pts.value.map(p => [p.x, p.y]) },
    null,
    2
  )
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'curve.json'
  a.click()
  URL.revokeObjectURL(url)
}

function exportDXF() {
  // TODO: Implement DXF export via API
  alert('DXF export coming soon! Use Export JSON for now.')
}

// Canvas setup
function setup() {
  const c = canvas.value!
  dpr = window.devicePixelRatio || 1
  c.width = c.clientWidth * dpr
  c.height = c.clientHeight * dpr
  ctx = c.getContext('2d')!
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  W = c.clientWidth
  H = c.clientHeight
  draw()
}

// Drawing
function draw() {
  if (!ctx) return

  // Clear
  ctx.clearRect(0, 0, W, H)

  // Grid
  ctx.strokeStyle = '#f1f5f9'
  ctx.lineWidth = 1
  for (let x = 0; x < W; x += 50) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, H)
    ctx.stroke()
  }
  for (let y = 0; y < H; y += 50) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(W, y)
    ctx.stroke()
  }

  // Polyline
  if (pts.value.length > 0) {
    ctx.strokeStyle = '#1e293b'
    ctx.lineWidth = 2
    ctx.beginPath()
    pts.value.forEach((p, i) => {
      if (i === 0) ctx.moveTo(p.x, p.y)
      else ctx.lineTo(p.x, p.y)
    })
    ctx.stroke()

    // Points
    pts.value.forEach(p => {
      ctx.fillStyle = '#0ea5e9'
      ctx.beginPath()
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2)
      ctx.fill()
    })
  }

  // Clothoid picking visualization
  ctx.fillStyle = '#22c55e'
  if (cPick.value.p0) {
    ctx.beginPath()
    ctx.arc(cPick.value.p0.x, cPick.value.p0.y, 5, 0, Math.PI * 2)
    ctx.fill()
  }
  if (cPick.value.p1) {
    ctx.beginPath()
    ctx.arc(cPick.value.p1.x, cPick.value.p1.y, 5, 0, Math.PI * 2)
    ctx.fill()
  }

  // Tangent vectors
  ctx.strokeStyle = '#16a34a'
  ctx.lineWidth = 2
  if (cPick.value.t0 && cPick.value.p0) {
    ctx.beginPath()
    ctx.moveTo(cPick.value.p0.x, cPick.value.p0.y)
    ctx.lineTo(cPick.value.t0.x, cPick.value.t0.y)
    ctx.stroke()
  }
  if (cPick.value.t1 && cPick.value.p1) {
    ctx.beginPath()
    ctx.moveTo(cPick.value.p1.x, cPick.value.p1.y)
    ctx.lineTo(cPick.value.t1.x, cPick.value.t1.y)
    ctx.stroke()
  }
}

// Interaction
function onClick(evt: MouseEvent) {
  const r = canvas.value!.getBoundingClientRect()
  const p = { x: evt.clientX - r.left, y: evt.clientY - r.top }

  if (mode.value === 'draw') {
    pushHistory()
    pts.value.push(p)
    draw()
  } else if (mode.value === 'clothoid') {
    const c = cPick.value
    if (!c.p0) {
      c.p0 = p
    } else if (!c.t0) {
      c.t0 = p
    } else if (!c.p1) {
      c.p1 = p
    } else if (!c.t1) {
      c.t1 = p
    }
    draw()
  }
}

// Operations
async function doOffset() {
  if (pts.value.length < 2) {
    alert('Need at least 2 points for offset')
    return
  }
  pushHistory()
  try {
    const body = await offsetPolycurve(
      pts.value.map(p => [p.x, p.y]),
      offsetDist.value,
      join.value
    )
    pts.value = body.polyline.points.map(([x, y]) => ({ x, y }))
    draw()
  } catch (err) {
    alert(`Offset failed: ${err}`)
  }
}

async function doFillet() {
  if (pts.value.length < 3) {
    alert('Need at least 3 points for fillet')
    return
  }
  pushHistory()
  try {
    const body = await autoFillet(
      pts.value.map(p => [p.x, p.y]),
      filletR.value,
      10
    )
    pts.value = body.polyline.points.map(([x, y]) => ({ x, y }))
    draw()
  } catch (err) {
    alert(`Fillet failed: ${err}`)
  }
}

async function doFair() {
  if (pts.value.length < 3) {
    alert('Need at least 3 points for fairing')
    return
  }
  pushHistory()
  try {
    const body = await fairCurve(
      pts.value.map(p => [p.x, p.y]),
      lam.value,
      preserve.value
    )
    pts.value = body.polyline.points.map(([x, y]) => ({ x, y }))
    draw()
  } catch (err) {
    alert(`Fairing failed: ${err}`)
  }
}

function resetClothoid() {
  cPick.value = {}
  draw()
}

async function doClothoid() {
  const c = cPick.value
  if (!c.p0 || !c.t0 || !c.p1 || !c.t1) {
    alert('Pick all 4 points: p0, t0, p1, t1')
    return
  }

  pushHistory()
  try {
    const p0: [number, number] = [c.p0.x, c.p0.y]
    const p1: [number, number] = [c.p1.x, c.p1.y]
    const t0: [number, number] = [c.t0.x - c.p0.x, c.t0.y - c.p0.y]
    const t1: [number, number] = [c.t1.x - c.p1.x, c.t1.y - c.p1.y]

    const body = await blendClothoid(p0, t0, p1, t1, 1.0)
    pts.value = body.polyline.points.map(([x, y]) => ({ x, y }))
    cPick.value = {}
    draw()
  } catch (err) {
    alert(`Clothoid blend failed: ${err}`)
  }
}

onMounted(() => {
  setup()
  window.addEventListener('resize', setup)
})
</script>

<style scoped>
.curve-lab {
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.btn {
  border: 1px solid #e2e8f0;
  padding: 8px 16px;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn:hover {
  background: #f1f5f9;
}

.btn-normal {
  color: #475569;
}

.btn-active {
  background: #0ea5e9;
  color: white;
  border-color: #0284c7;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border-color: #2563eb;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-success {
  background: #22c55e;
  color: white;
  border-color: #16a34a;
}

.btn-success:hover {
  background: #16a34a;
}

.btn-danger {
  background: #ef4444;
  color: white;
  border-color: #dc2626;
}

.btn-danger:hover {
  background: #dc2626;
}

.param-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #475569;
}

.param-input,
.param-select {
  border: 1px solid #cbd5e1;
  padding: 6px 10px;
  border-radius: 4px;
  width: 100px;
  font-size: 14px;
}

.param-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #475569;
}

.canvas-drawing {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  cursor: crosshair;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.info {
  padding: 8px;
  background: #f1f5f9;
  border-radius: 6px;
  font-family: monospace;
}
</style>
