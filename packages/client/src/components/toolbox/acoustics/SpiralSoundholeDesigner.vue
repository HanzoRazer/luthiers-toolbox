<template>
  <div class="spiral-designer">

    <div class="designer-header">
      <div class="designer-title">Spiral Soundhole Designer</div>
      <div class="designer-sub">
        Logarithmic spiral geometry · Carlos Jumbo body · Displaced f-hole logic
      </div>
    </div>

    <!-- Metric strip -->
    <div class="metric-strip">
      <div class="metric-card">
        <div class="metric-label">Upper area</div>
        <div class="metric-value upper">{{ upperStats.area }} mm²</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Upper P:A</div>
        <div class="metric-value" :class="paClass(upperStats.pa)">
          {{ upperStats.pa }} mm⁻¹
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Lower area</div>
        <div class="metric-value lower">{{ lowerStats.area }} mm²</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Lower P:A</div>
        <div class="metric-value" :class="paClass(lowerStats.pa)">
          {{ lowerStats.pa }} mm⁻¹
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Total area</div>
        <div class="metric-value total">{{ totalArea }} mm²</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">vs 4" round</div>
        <div class="metric-value" :class="areaRatioClass">{{ areaRatioPct }}%</div>
      </div>
    </div>

    <div class="designer-body">

      <!-- Left controls -->
      <div class="controls-panel">

        <div class="controls-section upper">Upper bout — bass side</div>
        <SliderRow v-for="c in upperControls" :key="c.id"
          :label="c.label" :id="`u_${c.id}`"
          :min="c.min" :max="c.max" :step="c.step"
          v-model="upper[c.id]" :unit="c.unit"
          accent="upper" />

        <div class="controls-section lower">Lower bout — treble side</div>
        <SliderRow v-for="c in lowerControls" :key="c.id"
          :label="c.label" :id="`l_${c.id}`"
          :min="c.min" :max="c.max" :step="c.step"
          v-model="lower[c.id]" :unit="c.unit"
          accent="lower" />

        <div class="controls-section">Display</div>
        <label class="check-row">
          <input type="checkbox" v-model="display.centerlines">
          <span>Centerlines</span>
        </label>
        <label class="check-row">
          <input type="checkbox" v-model="display.bodyFill">
          <span>Body fill</span>
        </label>
        <label class="check-row">
          <input type="checkbox" v-model="display.braceZones">
          <span>Brace keepout zones</span>
        </label>
        <label class="check-row">
          <input type="checkbox" v-model="display.grid">
          <span>Coordinate grid</span>
        </label>

      </div>

      <!-- Canvas -->
      <div class="canvas-wrap">
        <canvas ref="canvasEl" :width="canvasW" :height="canvasH" />
      </div>

      <!-- Right: stats + export -->
      <div class="stats-panel">

        <div class="controls-section">P:A efficiency</div>

        <div class="pa-row">
          <span class="pa-row-label">Upper</span>
          <span class="pa-tag" :class="paClass(upperStats.pa)">
            {{ paLabel(upperStats.pa) }}
          </span>
        </div>
        <div class="pa-bar-wrap">
          <div class="pa-bar upper"
            :style="{ width: paBarPct(upperStats.pa) + '%' }" />
        </div>
        <div class="pa-thresholds">
          <span>0</span><span class="warn">0.08</span>
          <span class="good">0.10</span><span>0.15</span>
        </div>

        <div class="pa-row" style="margin-top:10px">
          <span class="pa-row-label">Lower</span>
          <span class="pa-tag" :class="paClass(lowerStats.pa)">
            {{ paLabel(lowerStats.pa) }}
          </span>
        </div>
        <div class="pa-bar-wrap">
          <div class="pa-bar lower"
            :style="{ width: paBarPct(lowerStats.pa) + '%' }" />
        </div>
        <div class="pa-thresholds">
          <span>0</span><span class="warn">0.08</span>
          <span class="good">0.10</span><span>0.15</span>
        </div>

        <div class="pa-note">
          P:A = 2 / slot_width for a constant-width spiral slot.
          Target &gt; 0.10 mm⁻¹ for +60% acoustic efficiency vs round hole
          (Williams 2019).
        </div>

        <div class="controls-section" style="margin-top:14px">Math reference</div>
        <div class="math-ref">
          r(θ) = r₀ · e^(k·θ)<br>
          P = 2·(r_end − r₀) / sin(atan(1/k))<br>
          A = slot_w · (r_end − r₀) / sin(atan(1/k))<br>
          P:A = 2 / slot_w
        </div>

        <div class="controls-section" style="margin-top:14px">Export</div>

        <button class="action-btn primary" :disabled="exportLoading" @click="exportDxf">
          {{ exportLoading ? 'Generating DXF…' : 'Download DXF → CNC pipeline' }}
        </button>
        <button class="action-btn" @click="validateSpec">
          Validate geometry
        </button>
        <button class="action-btn" @click="resetToDefault">
          Reset to Carlos Jumbo defaults
        </button>

        <div v-if="validationResult" class="validation-result">
          <div v-for="w in validationResult.warnings" :key="w" class="v-warn">⚠ {{ w }}</div>
          <div v-for="i in validationResult.info" :key="i" class="v-info">✓ {{ i }}</div>
          <div v-if="validationResult.valid && !validationResult.warnings.length"
            class="v-ok">Geometry validated — ready for DXF export.</div>
        </div>

        <div v-if="exportError" class="v-warn" style="margin-top:8px">{{ exportError }}</div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'

// ── Types ─────────────────────────────────────────────────────────────────────

interface SpiralParams {
  cx: number
  cy: number
  r0: number
  k: number
  turns: number
  slotW: number
  rot: number
}

interface SpiralStats {
  area: number
  perim: number
  pa: number
  rEnd: number
}

// ── Constants ─────────────────────────────────────────────────────────────────

const API_BASE = '/api/woodworking/soundhole/spiral'
const ROUND_REF_AREA = Math.PI * (50.8 / 2) ** 2  // 4" round hole mm²

const CONTROL_DEFS = [
  { id: 'cx',    label: 'Center X (mm)',       min: -170, max: 170,  step: 1,    unit: 'mm' },
  { id: 'cy',    label: 'Center Y (mm)',       min: -170, max: 220,  step: 1,    unit: 'mm' },
  { id: 'r0',    label: 'Start radius (mm)',   min: 5,    max: 30,   step: 0.5,  unit: 'mm' },
  { id: 'k',     label: 'Growth rate k',       min: 0.05, max: 0.45, step: 0.005, unit: '' },
  { id: 'turns', label: 'Turns',               min: 0.5,  max: 2.5,  step: 0.05, unit: '' },
  { id: 'slotW', label: 'Slot width (mm)',     min: 6,    max: 22,   step: 0.5,  unit: 'mm' },
  { id: 'rot',   label: 'Rotation (°)',        min: 0,    max: 360,  step: 1,    unit: '°' },
]

const upperControls = CONTROL_DEFS
const lowerControls = CONTROL_DEFS

// ── State ─────────────────────────────────────────────────────────────────────

const canvasEl = ref<HTMLCanvasElement | null>(null)
const canvasW = 500
const canvasH = 660
const SCALE = 1.0
const OX = canvasW / 2
const OY = canvasH * 0.41

const upper = reactive<SpiralParams>({
  cx: -88, cy: -62, r0: 10, k: 0.18, turns: 1.1, slotW: 14, rot: 270
})

const lower = reactive<SpiralParams>({
  cx: 78, cy: 112, r0: 10, k: 0.18, turns: 1.1, slotW: 14, rot: 90
})

const display = reactive({
  centerlines: true,
  bodyFill: true,
  braceZones: true,
  grid: false,
})

const exportLoading = ref(false)
const exportError = ref('')
const validationResult = ref<any>(null)

// ── Computed stats (client-side closed form) ──────────────────────────────────

function spiralStats(p: SpiralParams): SpiralStats {
  const thetaEnd = p.turns * 2 * Math.PI
  const rEnd = p.r0 * Math.exp(p.k * thetaEnd)
  const alpha = Math.atan(1.0 / p.k)
  const oneWall = (rEnd - p.r0) / Math.sin(alpha)
  const perim = 2 * oneWall
  const area = p.slotW * oneWall
  const pa = area > 0 ? perim / area : 0
  return {
    area: Math.round(area),
    perim: Math.round(perim),
    pa: Math.round(pa * 1000) / 1000,
    rEnd: Math.round(rEnd * 10) / 10,
  }
}

const upperStats = computed(() => spiralStats(upper))
const lowerStats = computed(() => spiralStats(lower))
const totalArea = computed(() => upperStats.value.area + lowerStats.value.area)
const areaRatioPct = computed(() =>
  Math.round(totalArea.value / ROUND_REF_AREA * 100)
)
const areaRatioClass = computed(() =>
  areaRatioPct.value >= 70 ? 'good' : areaRatioPct.value >= 50 ? 'warn' : 'bad'
)

// ── P:A helpers ───────────────────────────────────────────────────────────────

function paClass(pa: number) {
  if (pa >= 0.10) return 'good'
  if (pa >= 0.08) return 'warn'
  return 'bad'
}

function paLabel(pa: number) {
  if (pa >= 0.10) return 'above threshold'
  if (pa >= 0.08) return 'approaching'
  return 'below threshold'
}

function paBarPct(pa: number) {
  return Math.min(100, pa / 0.15 * 100)
}

// ── Canvas drawing ─────────────────────────────────────────────────────────────

function mm(v: number) { return v * SCALE }

function carlosJumboPoints() {
  const pts: [number, number][] = []
  const lW = 194, uW = 147, waW = 107
  const lH = 242, uH = 163

  for (let i = 0; i <= 400; i++) {
    const t = i / 400
    const a = t * Math.PI * 2
    let x = 0, y = 0

    if (t < 0.5) {
      const s = t / 0.5
      if (s < 0.44) {
        const ss = s / 0.44
        const r = uW * (0.68 + 0.32 * Math.sin(ss * Math.PI))
        x = r * Math.sin(a); y = -uH + uH * (1 - ss * 0.83)
      } else if (s < 0.56) {
        const tt = (s - 0.44) / 0.12
        const r = uW * (1 - tt) + waW * tt
        x = r * Math.sin(a); y = (tt - 0.5) * 20
      } else {
        const ss = (s - 0.56) / 0.44
        const r = waW + (lW - waW) * Math.sin(ss * Math.PI * 0.9)
        x = r * Math.sin(a); y = ss * lH * 0.92
      }
    } else {
      const s = (t - 0.5) / 0.5
      if (s < 0.44) {
        const ss = s / 0.44
        const r = lW - (lW - waW) * Math.sin(ss * Math.PI * 0.9)
        x = -r * Math.sin(a - Math.PI); y = lH * 0.92 * (1 - ss)
      } else if (s < 0.56) {
        const tt = (s - 0.44) / 0.12
        const r = waW + (uW - waW) * tt
        x = -r * Math.sin(a - Math.PI); y = (0.5 - tt) * 20
      } else {
        const ss = (s - 0.56) / 0.44
        const r = uW * (0.68 + 0.32 * Math.sin((1 - ss) * Math.PI))
        x = -r * Math.sin(a - Math.PI); y = -ss * uH * 0.83
      }
    }
    pts.push([OX + mm(x), OY + mm(y)])
  }
  return pts
}

function spiralWallPts(p: SpiralParams, nSteps = 280) {
  const cx = OX + mm(p.cx)
  const cy = OY + mm(p.cy)
  const r0 = mm(p.r0)
  const w = mm(p.slotW)
  const thetaEnd = p.turns * 2 * Math.PI
  const rotRad = p.rot * Math.PI / 180
  const half = w / 2
  const outer: [number, number][] = []
  const inner: [number, number][] = []

  for (let i = 0; i <= nSteps; i++) {
    const theta = i / nSteps * thetaEnd
    const r = r0 * Math.exp(p.k * theta)
    const angle = theta + rotRad
    const txR = p.k * Math.cos(angle) - Math.sin(angle)
    const tyR = p.k * Math.sin(angle) + Math.cos(angle)
    const tLen = Math.sqrt(txR * txR + tyR * tyR)
    const nx = -tyR / tLen
    const ny = txR / tLen
    const px = cx + r * Math.cos(angle)
    const py = cy + r * Math.sin(angle)
    outer.push([px + nx * half, py + ny * half])
    inner.push([px - nx * half, py - ny * half])
  }
  return { outer, inner }
}

function spiralCenterline(p: SpiralParams, nSteps = 200): [number, number][] {
  const cx = OX + mm(p.cx)
  const cy = OY + mm(p.cy)
  const r0 = mm(p.r0)
  const thetaEnd = p.turns * 2 * Math.PI
  const rotRad = p.rot * Math.PI / 180
  return Array.from({ length: nSteps + 1 }, (_, i) => {
    const theta = i / nSteps * thetaEnd
    const r = r0 * Math.exp(p.k * theta)
    const angle = theta + rotRad
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)] as [number, number]
  })
}

function drawPolyline(ctx: CanvasRenderingContext2D, pts: [number, number][], close = false) {
  if (pts.length < 2) return
  ctx.beginPath()
  ctx.moveTo(pts[0][0], pts[0][1])
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1])
  if (close) ctx.closePath()
}

function drawSpiral(ctx: CanvasRenderingContext2D, p: SpiralParams, accentColor: string) {
  const { outer, inner } = spiralWallPts(p)

  // Fill slot black
  ctx.beginPath()
  ctx.moveTo(outer[0][0], outer[0][1])
  for (let i = 1; i < outer.length; i++) ctx.lineTo(outer[i][0], outer[i][1])
  const innerRev = [...inner].reverse()
  for (const pt of innerRev) ctx.lineTo(pt[0], pt[1])
  ctx.closePath()
  ctx.fillStyle = '#050505'
  ctx.fill()
  ctx.strokeStyle = accentColor
  ctx.lineWidth = 0.8
  ctx.stroke()

  // Centerline
  if (display.centerlines) {
    const cl = spiralCenterline(p)
    drawPolyline(ctx, cl)
    ctx.strokeStyle = accentColor + '60'
    ctx.lineWidth = 0.5
    ctx.setLineDash([4, 4])
    ctx.stroke()
    ctx.setLineDash([])
  }
}

function draw() {
  const canvas = canvasEl.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, canvasW, canvasH)
  ctx.fillStyle = '#0a0a0a'
  ctx.fillRect(0, 0, canvasW, canvasH)

  const bodyPts = carlosJumboPoints()

  // Body
  drawPolyline(ctx, bodyPts, true)
  if (display.bodyFill) {
    ctx.fillStyle = '#2a1f0e'
    ctx.fill()
    // Flame maple grain lines
    ctx.save()
    ctx.clip()
    for (let i = 0; i < 70; i++) {
      const y = OY - 270 + i * 8
      ctx.beginPath()
      ctx.moveTo(OX - 210, y)
      for (let x = -210; x <= 210; x += 6) {
        const yw = y + Math.sin((x + i * 9) * 0.07) * 5 + Math.sin((x + i * 4) * 0.12) * 2
        ctx.lineTo(OX + x, yw)
      }
      ctx.strokeStyle = `rgba(${155 + (i % 4) * 10},${90 + (i % 5) * 5},${35 + (i % 3) * 4},0.16)`
      ctx.lineWidth = 0.7
      ctx.stroke()
    }
    ctx.restore()
  } else {
    ctx.fillStyle = '#1a1208'
    ctx.fill()
  }
  ctx.strokeStyle = '#c8a050'
  ctx.lineWidth = 2.5
  drawPolyline(ctx, bodyPts, true)
  ctx.stroke()

  // Coordinate grid
  if (display.grid) {
    ctx.save()
    ctx.strokeStyle = 'rgba(100,140,200,0.15)'
    ctx.lineWidth = 0.4
    for (let x = OX - 200; x <= OX + 200; x += 20) {
      ctx.beginPath(); ctx.moveTo(x, OY - 270); ctx.lineTo(x, OY + 280); ctx.stroke()
    }
    for (let y = OY - 270; y <= OY + 280; y += 20) {
      ctx.beginPath(); ctx.moveTo(OX - 200, y); ctx.lineTo(OX + 200, y); ctx.stroke()
    }
    ctx.restore()
  }

  // Brace keepout zones
  if (display.braceZones) {
    ctx.save()
    ctx.setLineDash([4, 4])
    ctx.strokeStyle = 'rgba(240,80,50,0.35)'
    ctx.lineWidth = 0.8
    ctx.beginPath(); ctx.arc(OX, OY, mm(32), 0, Math.PI * 2); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(OX - mm(85), OY - mm(85)); ctx.lineTo(OX + mm(85), OY + mm(85)); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(OX - mm(85), OY + mm(85)); ctx.lineTo(OX + mm(85), OY - mm(85)); ctx.stroke()
    ctx.strokeStyle = 'rgba(240,180,50,0.25)'
    ctx.beginPath(); ctx.moveTo(OX - mm(155), OY - mm(32)); ctx.lineTo(OX + mm(155), OY - mm(32)); ctx.stroke()
    ctx.restore()
  }

  // Centerlines
  if (display.centerlines) {
    ctx.save()
    ctx.setLineDash([6, 5])
    ctx.strokeStyle = 'rgba(100,150,255,0.25)'
    ctx.lineWidth = 0.5
    ctx.beginPath(); ctx.moveTo(OX, OY - mm(200)); ctx.lineTo(OX, OY + mm(270)); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(OX - mm(180), OY); ctx.lineTo(OX + mm(180), OY); ctx.stroke()
    ctx.restore()
  }

  // Bridge reference
  ctx.fillStyle = '#1a1008'
  ctx.strokeStyle = '#8a7040'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.roundRect(OX - mm(33), OY - mm(7), mm(66), mm(11), 3)
  ctx.fill(); ctx.stroke()

  // Neck heel
  ctx.fillStyle = '#1e140a'
  ctx.strokeStyle = '#c8a050'
  ctx.lineWidth = 1.2
  ctx.beginPath()
  ctx.roundRect(OX - mm(24), OY - mm(170), mm(48), mm(28), 3)
  ctx.fill(); ctx.stroke()

  // Spirals
  drawSpiral(ctx, upper, '#e8c06080')
  drawSpiral(ctx, lower, '#60c8e880')
}

// ── API calls ─────────────────────────────────────────────────────────────────

function buildRequestBody() {
  return {
    upper: {
      center_x_mm: upper.cx, center_y_mm: upper.cy,
      start_radius_mm: upper.r0, growth_rate_k: upper.k,
      turns: upper.turns, slot_width_mm: upper.slotW,
      rotation_deg: upper.rot, label: 'Upper bass-side spiral',
    },
    lower: {
      center_x_mm: lower.cx, center_y_mm: lower.cy,
      start_radius_mm: lower.r0, growth_rate_k: lower.k,
      turns: lower.turns, slot_width_mm: lower.slotW,
      rotation_deg: lower.rot, label: 'Lower treble-side spiral',
    },
    body_type: 'carlos_jumbo',
    notes: 'Displaced f-hole spiral soundhole design',
  }
}

async function exportDxf() {
  exportLoading.value = true
  exportError.value = ''
  try {
    const res = await fetch(`${API_BASE}/dxf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildRequestBody()),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'DXF export failed')
    }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'spiral_soundhole_carlos_jumbo.dxf'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    exportError.value = e.message
  } finally {
    exportLoading.value = false
  }
}

async function validateSpec() {
  validationResult.value = null
  exportError.value = ''
  try {
    const res = await fetch(`${API_BASE}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildRequestBody()),
    })
    validationResult.value = await res.json()
  } catch (e: any) {
    exportError.value = 'Validation request failed: ' + e.message
  }
}

function resetToDefault() {
  upper.cx = -88; upper.cy = -62; upper.r0 = 10
  upper.k = 0.18; upper.turns = 1.1; upper.slotW = 14; upper.rot = 270
  lower.cx = 78; lower.cy = 112; lower.r0 = 10
  lower.k = 0.18; lower.turns = 1.1; lower.slotW = 14; lower.rot = 90
  validationResult.value = null
  exportError.value = ''
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

watch([upper, lower, display], () => nextTick(draw), { deep: true })
onMounted(() => { nextTick(draw) })
</script>

<style scoped>
.spiral-designer {
  font-family: var(--font-sans, system-ui);
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  min-height: 100%;
}

.designer-header { margin-bottom: 4px; }
.designer-title { font-size: 15px; font-weight: 500; margin-bottom: 2px; }
.designer-sub { font-size: 12px; color: var(--color-text-secondary); }

.metric-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}
.metric-card {
  background: var(--color-background-secondary);
  border-radius: 8px;
  padding: 9px 11px;
}
.metric-label { font-size: 11px; color: var(--color-text-secondary); margin-bottom: 3px; }
.metric-value { font-size: 16px; font-weight: 600; }
.metric-value.upper { color: #c8a050; }
.metric-value.lower { color: #50a8c8; }
.metric-value.total { color: #50b880; }
.metric-value.good  { color: #50b880; }
.metric-value.warn  { color: #c89050; }
.metric-value.bad   { color: #c05040; }

.designer-body {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 220px;
  gap: 12px;
  align-items: start;
}

.controls-panel,
.stats-panel {
  background: var(--color-background-primary);
  border: 0.5px solid var(--color-border-tertiary);
  border-radius: 10px;
  padding: 12px;
}

.controls-section {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-tertiary);
  margin: 12px 0 7px;
  padding-bottom: 4px;
  border-bottom: 0.5px solid var(--color-border-tertiary);
}
.controls-section:first-child { margin-top: 0; }
.controls-section.upper { color: #c8a050; }
.controls-section.lower { color: #50a8c8; }

.check-row {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 5px;
  cursor: pointer;
  font-size: 11px;
  color: var(--color-text-secondary);
}

.canvas-wrap {
  display: flex;
  justify-content: center;
  background: var(--color-background-secondary);
  border-radius: 10px;
  padding: 10px;
}
canvas {
  border-radius: 6px;
  max-width: 100%;
}

.pa-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.pa-row-label { font-size: 11px; color: var(--color-text-secondary); }
.pa-tag {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 4px;
  font-weight: 600;
}
.pa-tag.good { background: #50b88020; color: #50b880; border: 1px solid #50b88040; }
.pa-tag.warn { background: #c8905020; color: #c89050; border: 1px solid #c8905040; }
.pa-tag.bad  { background: #c0504020; color: #c05040; border: 1px solid #c0504040; }

.pa-bar-wrap {
  height: 5px;
  background: var(--color-background-secondary);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 3px;
}
.pa-bar { height: 100%; border-radius: 3px; transition: width 0.2s; }
.pa-bar.upper { background: #c8a050; }
.pa-bar.lower { background: #50a8c8; }

.pa-thresholds {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  color: var(--color-text-tertiary);
  margin-bottom: 8px;
}
.pa-thresholds .good { color: #50b880; }
.pa-thresholds .warn { color: #c89050; }

.pa-note {
  font-size: 10px;
  color: var(--color-text-tertiary);
  line-height: 1.6;
  margin-bottom: 4px;
}

.math-ref {
  font-family: var(--font-mono, monospace);
  font-size: 10px;
  color: var(--color-text-secondary);
  line-height: 1.9;
  background: var(--color-background-secondary);
  padding: 8px;
  border-radius: 6px;
}

.action-btn {
  display: block;
  width: 100%;
  padding: 7px 10px;
  margin-bottom: 6px;
  border: 0.5px solid var(--color-border-secondary);
  border-radius: 6px;
  background: none;
  color: var(--color-text-primary);
  font-family: var(--font-sans, system-ui);
  font-size: 11px;
  cursor: pointer;
  text-align: left;
}
.action-btn:hover { background: var(--color-background-secondary); }
.action-btn.primary { border-color: #50b880; color: #50b880; }
.action-btn.primary:hover { background: #50b88015; }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.validation-result { margin-top: 8px; }
.v-warn { font-size: 10px; color: #c89050; line-height: 1.5; margin-bottom: 4px; }
.v-info { font-size: 10px; color: #50b880; line-height: 1.5; margin-bottom: 4px; }
.v-ok   { font-size: 10px; color: #50b880; font-weight: 500; }
</style>
