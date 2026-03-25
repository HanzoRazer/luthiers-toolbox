<script setup lang="ts">
/**
 * WorkspaceView.vue — Path 1 (Workspace)
 *
 * WORKSPACE_CAM_INTEGRATION applied:
 *   Section 1: useCamSpec, drawCamOverlay, WoodGrainPanel, CamSpecPanel wired
 *   Section 2: camSpec, grain, exporter composable instances
 *   Section 3: camLayer Konva layer
 *   Section 4: redrawHS() now applies grain texture + cam overlay
 *   Section 5: onCamChange(), showCamOverlay, exportDxf()
 *   Section 6: WoodGrainPanel + CamSpecPanel in left panel
 *   Section 7: dxf_export.py payload (see backend file)
 */
import { ref, watch, onMounted, computed } from 'vue'
import Konva from 'konva'
import { storeToRefs } from 'pinia'
import { useHeadstockStore } from '@/stores/headstock'
import { useKonvaCanvas } from '@/composables/useKonvaCanvas'
import { drawBackground, drawHeadstock, createInlayGroup, exportWorkspaceSVG } from '@/composables/useHeadstock'
import { HS_MODELS, MM } from '@/assets/data/headstockData'
import type { InlayType } from '@/types/headstock'
// ── Section 1: CAM integration imports ──────────────────────────────────────
import { useCamSpec }     from '@/composables/useCamSpec'
import { drawCamOverlay } from '@/composables/drawCamOverlay'
import { useWoodGrain }   from '@/composables/useWoodGrain'
import { useExportDxf }   from '@/composables/useExportDxf'
import CamSpecPanel          from '@/components/CamSpecPanel.vue'
import VariantLibraryPanel   from '@/components/VariantLibraryPanel.vue'
import { useVariantStore }   from '@/stores/variants'
import WoodGrainPanel     from '@/components/WoodGrainPanel.vue'

const store = useHeadstockStore()
const { currentModelKey, inlays, customShape, showGrid, showCL, showNut, snapOn, boundaryOn, selectedInlay, selectedInlayId } = storeToRefs(store)

const containerRef = ref<HTMLElement | null>(null)
const canvas = useKonvaCanvas(containerRef)
const { stage } = canvas

let bgLayer: Konva.Layer, hsLayer: Konva.Layer, inlayLayer: Konva.Layer, guideLayer: Konva.Layer
// ── Section 3: camLayer ─────────────────────────────────────────────────────
let camLayer: Konva.Layer

let selIndicator = ref<Konva.Rect | null>(null)
const history = ref<any[]>([])
const histIdx = ref(-1)
const statusXY = ref('x — · y —')

// ── Section 5: cam overlay state ─────────────────────────────────────────────
const showCamOverlay = ref(false)

// ── Section 2: composable instances ──────────────────────────────────────────
// nutWidthMm derived from active headstock model
const nutWidthMm = computed(() => (currentHS().nw ?? 70) * MM)

const camSpec  = useCamSpec(nutWidthMm.value, 175)
const grain    = useWoodGrain()
const exporter     = useExportDxf()
const variantStore = useVariantStore()
const showVariants = ref(false)

onMounted(() => {
  bgLayer = canvas.addLayer(); hsLayer = canvas.addLayer()
  inlayLayer = canvas.addLayer(); guideLayer = canvas.addLayer()
  // ── Section 3: add camLayer after guide layer ────────────────────────────
  camLayer = canvas.addLayer()

  stage.value?.on('click', e => { if ([bgLayer, hsLayer].includes(e.target.getLayer())) deselect() })
  stage.value?.on('mousemove', () => {
    const p = stage.value?.getPointerPosition()
    if (p) statusXY.value = `x ${(canvas.c2px(p.x)*MM).toFixed(1)}mm · y ${(canvas.c2py(p.y)*MM).toFixed(1)}mm`
  })
  redrawAll(); saveHistory()
})

watch([showGrid], () => { drawBackground(bgLayer, canvas, showGrid.value) })
watch([showCL, showNut, currentModelKey, customShape], redrawHS)
watch(customShape, shape => { if (shape && canvas.stage.value) wLoadCustomShape(shape) })
// Watch cam spec for live overlay updates
watch(
  [() => camSpec.spec, showCamOverlay, () => grain.species.value],
  () => { if (showCamOverlay.value) onCamChange() },
  { deep: true }
)

function currentHS() {
  if (currentModelKey.value === 'Custom' && customShape.value)
    return { col:'#7a5030', gr:'#5a3018', path: customShape.value.path, cx:100, nutY:290, nw:70, tuners:[] as [number,number][] }
  return HS_MODELS[currentModelKey.value] ?? HS_MODELS['Les Paul']
}

// ── Section 4: redrawHS with grain + cam overlay ──────────────────────────
function redrawHS() {
  if (!hsLayer) return
  const hs = currentHS()
  // Apply wood grain texture to headstock fill if species selected
  if (grain.species.value !== 'none') {
    grain.applyToPath(hs.path, hsLayer, canvas)
  }
  drawHeadstock(hsLayer, guideLayer, canvas, hs, showCL.value, showNut.value)
  // Redraw cam overlay if visible
  if (showCamOverlay.value && camLayer) {
    onCamChange()
  }
}

function redrawAll() { drawBackground(bgLayer, canvas, showGrid.value); redrawHS() }

// ── Section 5: cam overlay draw + DXF export ─────────────────────────────
function onCamChange() {
  if (!camLayer) return
  camLayer.destroyChildren()
  if (!showCamOverlay.value) { camLayer.draw(); return }
  const hs = currentHS()
  drawCamOverlay(camLayer, canvas, camSpec.spec, hs)
  camLayer.draw()
}

function exportDxf() {
  const hs = currentHS()
  // Build payload including cam spec (truss rod, pitch, tuner holes)
  const camPayload = camSpec.exportPayload.value
  const payload = {
    outline_path:  hs.path ?? '',
    tuner_holes:   camPayload.tunerHoles ?? [],
    nut_x1: (hs.cx ?? 100) - (hs.nw ?? 70) / 2,
    nut_x2: (hs.cx ?? 100) + (hs.nw ?? 70) / 2,
    nut_y:  hs.nutY ?? 298,
    nut_width_mm: nutWidthMm.value,
    kerf_mm:  3.175,
    dogbone:  true,
    tool_dia_mm: 3.175,
    label: currentModelKey.value,
    // CAM extension fields (Section 7)
    truss_rod: {
      access:       camPayload.rodAccess,
      type:         camPayload.rodType,
      width_mm:     camPayload.rodWidthMm,
      depth_mm:     camPayload.rodDepthMm,
      length_mm:    camPayload.rodLengthMm,
      end_mill_mm:  camPayload.endMillMm,
      cx_u:         hs.cx ?? 100,
      start_y_u:    hs.nutY ?? 298,
      end_y_u:      (hs.nutY ?? 298) - camPayload.rodLengthMm / MM,
    },
    pitch: {
      style:     camPayload.pitchStyle,
      angle_deg: camPayload.pitchAngle,
      fixture_note: `Fixture angle: ${camPayload.pitchAngle}°`,
    },
    screw_holes: camPayload.screwHoles ?? [],
  }

  exporter.exportDxf(payload)
    .then(() => emit('toast', `DXF exported — ${currentModelKey.value}`))
    .catch(err => emit('toast', `DXF error: ${err}`))
}

function wLoadCustomShape(shape: any) {
  store.currentModelKey = 'Custom'
  redrawHS()
}

function placeInlay(type: InlayType) {
  const hs = currentHS()
  const cx = canvas.p2cx(hs.cx), cy = canvas.p2cy(hs.nutY - 55 - (inlays.value.length % 6) * 26)
  const layer = createInlayGroup(type, cx, cy, inlayLayer, canvas, snapOn.value, boundaryOn.value, hs,
    (g, sel) => doSelect(g, sel), () => saveHistory())
  store.addInlay(layer); saveHistory()
}

function doSelect(g: Konva.Group, sel: Konva.Rect) {
  if (selIndicator.value) selIndicator.value.visible(false)
  selIndicator.value = sel; sel.visible(true); inlayLayer.draw(); store.selectInlay(g.id())
}
function deselect() {
  if (selIndicator.value) { selIndicator.value.visible(false); inlayLayer.draw() }
  selIndicator.value = null; store.selectInlay(null)
}

function deleteSelected() {
  if (!selectedInlayId.value) return
  deselect(); store.removeInlay(selectedInlayId.value); inlayLayer.draw(); saveHistory()
}

function snapshotInlays() { return inlays.value.map(l => ({ id:l.id, x:l.node.x(), y:l.node.y(), s:l.node.scaleX(), r:l.node.rotation(), v:l.node.visible() })) }
function saveHistory() { const s = snapshotInlays(); history.value = history.value.slice(0, histIdx.value+1); history.value.push(s); if(history.value.length>80) history.value.shift(); histIdx.value = history.value.length-1 }
function undo() {
  if (histIdx.value <= 0) return; histIdx.value--
  history.value[histIdx.value].forEach((s:any) => { const l = inlays.value.find(x=>x.id===s.id); if(l){l.node.x(s.x);l.node.y(s.y);l.node.scaleX(s.s);l.node.scaleY(s.s);l.node.rotation(s.r);l.node.visible(s.v)} })
  inlayLayer.draw()
}

// Load a variant's headstock payload back into the store
function onLoadVariant(v: import('@/stores/variants').Variant) {
  if (v.headstock) {
    // Restore model key if present
    if (v.headstock.modelKey) store.currentModelKey = v.headstock.modelKey
    // customShape path if present
    if (v.headstock.customPath) {
      store.receiveHandoff?.({ path: v.headstock.customPath, label: v.name, source: 'variant', useAs: 'workspace' })
    }
  }
  emit('toast', `Loaded: ${v.name}`)
}

function exportSVG() {
  const svg = exportWorkspaceSVG(currentHS(), currentModelKey.value, inlays.value, canvas)
  const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(new Blob([svg], {type:'image/svg+xml'})), download: `ps-${currentModelKey.value.toLowerCase().replace(/\s+/g,'-')}.svg` })
  a.click()
}

const headstockExportPayload = computed(() => ({
  modelKey: currentModelKey.value,
  customPath: customShape.value?.path ?? null,
  camSpec: camSpec.exportPayload.value,
}))

const emit = defineEmits<{ toast: [msg: string] }>()
</script>

<template>
  <div class="workspace" @keydown.delete="deleteSelected" @keydown.backspace="deleteSelected" @keydown.escape="deselect" tabindex="0">
    <aside class="ws-left">
      <div class="pcat">
        <div class="pcat-lbl">Model</div>
        <div class="model-list">
          <button v-for="(hs, name) in HS_MODELS" :key="name" class="mbtn" :class="{ on: currentModelKey === name }" @click="store.currentModelKey = name">
            <span class="mswatch" :style="{ background: hs.col }"></span>{{ name }}
          </button>
          <button v-if="customShape" class="mbtn" :class="{ on: currentModelKey === 'Custom' }" @click="store.currentModelKey = 'Custom'">
            <span class="mswatch" style="background:#7a5030"></span>Custom
          </button>
        </div>
      </div>
      <div class="pcat">
        <div class="pcat-lbl">Inlay library</div>
        <div class="inlay-grid">
          <div v-for="def in [
            {id:'dot',lbl:'Dot'},{id:'diamond',lbl:'Dmd'},{id:'block',lbl:'Blk'},{id:'crown',lbl:'Crown'},
            {id:'oval',lbl:'Oval'},{id:'star',lbl:'Star'},{id:'hex',lbl:'Hex'},{id:'text',lbl:'Text'}
          ]" :key="def.id" class="ibtn" @click="placeInlay(def.id as InlayType)">
            {{ def.lbl }}
          </div>
        </div>
      </div>
      <div class="pcat">
        <div class="pcat-lbl">Canvas</div>
        <div class="tgl-row"><span class="tgl-lbl">Grid</span><div class="tgl" :class="{on:showGrid}" @click="store.showGrid=!store.showGrid"><div class="kn"></div></div></div>
        <div class="tgl-row"><span class="tgl-lbl">Centerline</span><div class="tgl" :class="{on:showCL}" @click="store.showCL=!store.showCL"><div class="kn"></div></div></div>
        <div class="tgl-row"><span class="tgl-lbl">Nut guide</span><div class="tgl" :class="{on:showNut}" @click="store.showNut=!store.showNut"><div class="kn"></div></div></div>
        <div class="tgl-row"><span class="tgl-lbl">CL snap</span><div class="tgl" :class="{on:snapOn}" @click="store.snapOn=!store.snapOn"><div class="kn"></div></div></div>
        <div class="tgl-row"><span class="tgl-lbl">Boundary lock</span><div class="tgl" :class="{on:boundaryOn}" @click="store.boundaryOn=!store.boundaryOn"><div class="kn"></div></div></div>
      </div>

      <!-- ── Section 6: Wood grain panel ────────────────────────────────── -->
      <div class="pcat">
        <div class="pcat-lbl">Wood grain</div>
        <WoodGrainPanel :grain="grain" @change="redrawHS" />
      </div>

      <!-- ── Section 6: CAM spec panel ──────────────────────────────────── -->
      <div class="pcat">
        <div class="pcat-lbl" style="display:flex;justify-content:space-between;align-items:center">
          CAM spec
          <span class="sbtn" style="padding:2px 6px;font-size:8px"
            @click="showCamOverlay = !showCamOverlay; onCamChange()">
            {{ showCamOverlay ? 'hide' : 'show' }}
          </span>
        </div>
        <CamSpecPanel :cam="camSpec" @change="onCamChange" />
      </div>
    </aside>

    <div class="ws-canvas" ref="containerRef"></div>

    <!-- Variant library slide-over (replaces right panel when open) -->
    <aside class="ws-right" v-if="showVariants">
      <VariantLibraryPanel
        :headstock-payload="headstockExportPayload"
        :neck-payload="null"
        @load="onLoadVariant"
        @toast="emit('toast', $event)"
      />
    </aside>
    <aside class="ws-right" v-else>
      <div class="sec">
        <div class="sec-lbl">Element</div>
        <div v-if="!selectedInlay" class="no-sel">No selection</div>
        <template v-else>
          <div class="param-row"><span class="param-name">Scale</span><input class="prop-val" type="number" step="0.05" :value="selectedInlay.node.scaleX().toFixed(2)" @change="e => { selectedInlay!.node.scaleX(+(e.target as HTMLInputElement).value); selectedInlay!.node.scaleY(+(e.target as HTMLInputElement).value); inlayLayer?.draw() }"><span class="param-unit">×</span></div>
          <div class="param-row"><span class="param-name">Rotate</span><input class="prop-val" type="number" step="1" :value="Math.round(selectedInlay.node.rotation())" @change="e => { selectedInlay!.node.rotation(+(e.target as HTMLInputElement).value); inlayLayer?.draw() }"><span class="param-unit">°</span></div>
          <div style="display:flex;gap:4px;margin-top:4px">
            <button class="sbtn" style="flex:1" @click="selectedInlay.node.scaleX(-selectedInlay.node.scaleX()); inlayLayer?.draw()">⇔ Flip</button>
            <button class="sbtn" style="flex:1;color:var(--red)" @click="deleteSelected">✕ Del</button>
          </div>
        </template>
      </div>
      <div style="padding:8px 12px 4px" class="sec-lbl">Layers</div>
      <div class="layer-list">
        <div v-if="!inlays.length" class="no-sel">No inlays</div>
        <div v-for="l in [...inlays].reverse()" :key="l.id" class="layer-item" :class="{sel: selectedInlayId===l.id}" @click="doSelect(l.node, l.sel)">
          <span class="lpip" :style="{background:l.pip}"></span>
          <span class="lname">{{ l.name }}</span>
          <span class="lvis" @click.stop="store.toggleInlayVisibility(l.id)">{{ l.visible ? '◉' : '○' }}</span>
        </div>
      </div>
    </aside>

    <div class="ws-status">
      <span>{{ statusXY }}</span>
      <span>{{ inlays.length }} inlay{{ inlays.length!==1?'s':'' }}</span>
      <span v-if="showCamOverlay" style="color:var(--amber)">CAM overlay on</span>
      <div style="flex:1"></div>
      <button class="sbtn" :class="{ on: showVariants }" @click="showVariants = !showVariants">☰ Variants</button>
      <button class="sbtn" @click="undo">← Undo</button>
      <button class="sbtn" @click="store.clearInlays()">Clear</button>
      <button class="sbtn" @click="exportSVG">↓ SVG</button>
      <!-- ── Section 6: DXF export button ────────────────────────────────── -->
      <button class="sbtn go" @click="exportDxf">↓ DXF</button>
    </div>
  </div>
</template>

<style scoped>
.workspace { display:grid; grid-template-columns:196px 1fr 196px; grid-template-rows:1fr 28px; height:100%; outline:none; }
.ws-left,.ws-right { background:var(--w1); overflow-y:auto; display:flex; flex-direction:column; }
.ws-left { border-right:1px solid var(--w3); }
.ws-right { border-left:1px solid var(--w3); }
.ws-canvas { grid-column:2; grid-row:1; overflow:hidden; background:var(--w0); }
.ws-status { grid-column:1/-1; background:var(--w1); border-top:1px solid var(--w3); display:flex; align-items:center; gap:10px; padding:0 12px; font-size:9px; color:var(--dim); }
.layer-list { flex:1; overflow-y:auto; padding:4px 12px; }
</style>
