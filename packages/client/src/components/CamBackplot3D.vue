<template>
  <div class="relative w-full h-[480px] bg-black/90 rounded-lg overflow-hidden">
    <canvas
      ref="canvasEl"
      class="w-full h-full block"
    />

    <!-- HUD -->
    <div class="absolute top-2 left-2 text-[10px] text-white/90 space-y-1 pointer-events-none">
      <div class="px-2 py-1 bg-white/10 rounded">
        <div class="font-semibold">
          3D Backplot
        </div>
        <div v-if="metrics">
          <div>t = {{ (metrics.total_time_s).toFixed(2) }} s</div>
          <div>E = {{ (metrics.total_energy_j).toFixed(0) }} J</div>
          <div>P<sub>peak</sub> = {{ (metrics.peak_power_w).toFixed(0) }} W</div>
        </div>
        <div v-else>
          no metrics (click "Simulate")
        </div>
      </div>
      <div class="px-2 py-1 bg-white/10 rounded">
        <div class="font-semibold">
          Color Map
        </div>
        <div>{{ colorMode === 'feed' ? 'Feed speed' : 'Power' }}</div>
        <div class="flex gap-1 mt-1">
          <span
            class="inline-block w-10 h-2"
            :style="{ background: gradientCss }"
          />
          <span class="opacity-80">low → high</span>
        </div>
      </div>
    </div>

    <!-- Controls -->
    <div class="absolute top-2 right-2 flex gap-2">
      <button
        class="px-2 py-1 rounded text-[10px] bg-white/10 text-white hover:bg-white/20"
        @click="toggleAxes"
      >
        {{ showAxes ? 'Hide Axes' : 'Show Axes' }}
      </button>
      <button
        class="px-2 py-1 rounded text-[10px] bg-white/10 text-white hover:bg-white/20"
        @click="toggleMode"
      >
        Mode: {{ colorMode === 'feed' ? 'Feed' : 'Power' }}
      </button>
      <button
        class="px-2 py-1 rounded text-[10px] bg-white/10 text-white hover:bg-white/20"
        title="Fit view"
        @click="fitView"
      >
        Fit
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Props:
 *  - moves: Array<{ code: 'G0'|'G1'|'G2'|'G3', x?: number, y?: number, z?: number, f?: number }>
 *  - metrics: SimMetricsOut | null  (from /cam/sim/metrics; optional but enables power colormap)
 *  - units: 'mm' | 'inch'
 *  - toolD?: number (for Z stacking)
 */
import { onMounted, onBeforeUnmount, ref, watch, computed } from 'vue'
import * as THREE from 'three'
// OrbitControls is shipped inside examples; vite handles it by direct import
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

type Move = { code: 'G0'|'G1'|'G2'|'G3', x?: number, y?: number, z?: number, f?: number }
type SegTS = { idx: number, code: string, length_mm: number, feed_u_per_min: number, time_s: number, power_w: number, energy_j: number }
type SimMetricsOut = {
  total_time_s: number
  total_length_mm: number
  avg_feed_u_per_min: number
  total_energy_j: number
  chip_energy_j: number
  tool_energy_j: number
  work_energy_j: number
  peak_power_w: number
  mean_power_w: number
  feed_limited_pct: number
  timeseries?: SegTS[]
  units: 'mm'|'inch'
  tool_d: number
  stepdown: number
  stepover_frac: number
  engagement_pct: number
  material_name: string
}

const props = withDefaults(defineProps<{
  moves: Move[] | null
  metrics?: SimMetricsOut | null
  units?: 'mm' | 'inch'
  toolD?: number
}>(), {
  moves: null,
  metrics: null,
  units: 'mm',
  toolD: 6
})

const canvasEl = ref<HTMLCanvasElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let axesHelper: THREE.AxesHelper | null = null
let plotGroup: THREE.Group | null = null

const showAxes = ref(false)
const colorMode = ref<'feed'|'power'>('feed')

const gradientCss = computed(() => {
  // Blue → Green → Yellow → Red
  return 'linear-gradient(90deg, #2563eb, #16a34a, #facc15, #ef4444)'
})

function makeColorLerp(t: number): THREE.Color {
  // clamp 0..1
  const x = Math.max(0, Math.min(1, t))
  // 0..1: blue(0) -> green(0.33) -> yellow(0.66) -> red(1)
  const c = new THREE.Color()
  if (x < 1/3) {
    // blue -> green
    const k = x * 3
    c.setRGB(0 * (1-k) + 0 * k, 0.4 * (1-k) + 0.8 * k, 1 * (1-k) + 0.1 * k)
  } else if (x < 2/3) {
    const k = (x - 1/3) * 3
    c.setRGB(0 * (1-k) + 1 * k, 0.8 * (1-k) + 0.9 * k, 0.1 * (1-k) + 0.1 * k)
  } else {
    const k = (x - 2/3) * 3
    c.setRGB(1 * (1-k) + 0.9 * k, 0.9 * (1-k) + 0.2 * k, 0.1 * (1-k) + 0.1 * k)
  }
  return c
}

function rebuild() {
  if (!canvasEl.value) return

  // dispose previous
  if (renderer) { renderer.dispose(); renderer = null }
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0b0b0b)
  camera = new THREE.PerspectiveCamera(50, canvasEl.value.clientWidth / canvasEl.value.clientHeight, 0.1, 10000)
  camera.position.set(0, -200, 180)

  renderer = new THREE.WebGLRenderer({ canvas: canvasEl.value, antialias: true })
  renderer.setPixelRatio(window.devicePixelRatio || 1)
  renderer.setSize(canvasEl.value.clientWidth, canvasEl.value.clientHeight, false)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.target.set(0, 0, 0)

  axesHelper = new THREE.AxesHelper(50)
  axesHelper.visible = showAxes.value
  scene.add(axesHelper)

  // lights
  const ambient = new THREE.AmbientLight(0xffffff, 0.7)
  scene.add(ambient)
  const dir = new THREE.DirectionalLight(0xffffff, 0.6)
  dir.position.set(120, -80, 200)
  scene.add(dir)

  // group for plotted lines
  plotGroup = new THREE.Group()
  scene.add(plotGroup)

  // Build geometry from moves
  if (props.moves && props.moves.length) {
    buildPlotFromMoves(props.moves, props.metrics || null)
  }

  fitView()
  animate()
}

function buildPlotFromMoves(moves: Move[], metrics: SimMetricsOut | null) {
  if (!scene || !plotGroup) return

  // compute bounds / scaling
  let minX = +Infinity, minY = +Infinity, maxX = -Infinity, maxY = -Infinity
  let last: {x?: number, y?: number, z?: number} = {}
  for (const m of moves) {
    if (m.x !== undefined && m.y !== undefined) {
      minX = Math.min(minX, m.x); minY = Math.min(minY, m.y)
      maxX = Math.max(maxX, m.x); maxY = Math.max(maxY, m.y)
    }
  }
  const cx = (minX + maxX) / 2
  const cy = (minY + maxY) / 2

  // color normalization ranges
  let feedMin = +Infinity, feedMax = 0
  let powMin = +Infinity, powMax = 0
  const byIdx = new Map<number, SegTS>()
  if (metrics?.timeseries?.length) {
    for (const ts of metrics.timeseries) {
      byIdx.set(ts.idx, ts)
      if (ts.feed_u_per_min > 0) {
        feedMin = Math.min(feedMin, ts.feed_u_per_min)
        feedMax = Math.max(feedMax, ts.feed_u_per_min)
      }
      if (ts.power_w >= 0) {
        powMin = Math.min(powMin, ts.power_w)
        powMax = Math.max(powMax, ts.power_w)
      }
    }
  }
  if (!isFinite(feedMin)) feedMin = 0
  if (feedMax <= 0) feedMax = 1
  if (!isFinite(powMin)) powMin = 0
  if (powMax <= 0) powMax = 1

  // Convert to mm if needed
  const toMM = (v: number) => props.units === 'inch' ? v * 25.4 : v
  const zLift = Math.max(1.0, (props.toolD || 6) * 0.6) // small z separation

  // Build segments
  let lastX: number | undefined, lastY: number | undefined
  let segIdx = 0
  for (const m of moves) {
    if (m.x === undefined || m.y === undefined) {
      // state update only
      if (m.x !== undefined) lastX = m.x
      if (m.y !== undefined) lastY = m.y
      continue
    }
    if (lastX === undefined || lastY === undefined) {
      lastX = m.x; lastY = m.y
      continue
    }

    const x0 = toMM(lastX) - toMM(cx)
    const y0 = toMM(lastY) - toMM(cy)
    const x1 = toMM(m.x) - toMM(cx)
    const y1 = toMM(m.y) - toMM(cy)

    // stack G0 (rapids) slightly higher to see separation
    const z = (m.code === 'G0') ? zLift : 0

    // choose color scalar
    let t = 0.2 // default
    if (colorMode.value === 'feed') {
      const feed = byIdx.get(segIdx)?.feed_u_per_min ?? m.f ?? 0
      t = (feed - feedMin) / (feedMax - feedMin)
    } else {
      const p = byIdx.get(segIdx)?.power_w ?? 0
      t = (p - powMin) / (powMax - powMin)
    }
    t = Math.max(0, Math.min(1, t))
    const color = makeColorLerp(t)

    // linewidth: slightly thicker for cutting
    const width = (m.code === 'G0') ? 1.0 : 2.0

    const geom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(x0, y0, z),
      new THREE.Vector3(x1, y1, z)
    ])

    const mat = new THREE.LineBasicMaterial({ color, linewidth: width })
    const line = new THREE.Line(geom, mat)
    plotGroup.add(line)

    lastX = m.x; lastY = m.y
    segIdx += 1
  }
}

function fitView() {
  if (!plotGroup || !camera || !controls) return
  // compute group bounding box
  const box = new THREE.Box3().setFromObject(plotGroup)
  const size = new THREE.Vector3()
  const center = new THREE.Vector3()
  box.getSize(size)
  box.getCenter(center)

  // place camera
  const maxDim = Math.max(size.x, size.y, size.z)
  const dist = maxDim * 1.6 + 120
  camera.position.set(center.x, center.y - dist, dist * 0.9)
  controls.target.copy(center)
  controls.update()
}

function animate() {
  if (!renderer || !scene || !camera || !controls) return
  const renderLoop = () => {
    controls!.update()
    renderer!.render(scene!, camera!)
    window.requestAnimationFrame(renderLoop)
  }
  renderLoop()
}

function onResize() {
  if (!renderer || !camera || !canvasEl.value) return
  const w = canvasEl.value.clientWidth
  const h = canvasEl.value.clientHeight
  renderer.setSize(w, h, false)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

function toggleAxes() {
  showAxes.value = !showAxes.value
  if (axesHelper) axesHelper.visible = showAxes.value
}

function toggleMode() {
  colorMode.value = (colorMode.value === 'feed') ? 'power' : 'feed'
  // rebuild to recolor quickly
  rebuild()
}

onMounted(() => {
  rebuild()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (renderer) renderer.dispose()
})

watch(() => [props.moves, props.metrics, props.units, props.toolD], () => {
  rebuild()
})
</script>

<style scoped>
/* no fixed colors; rely on scene background + HUD */
</style>
