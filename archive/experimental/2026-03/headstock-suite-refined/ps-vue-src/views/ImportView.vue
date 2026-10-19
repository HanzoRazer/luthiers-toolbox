<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import Konva from 'konva'
import { useHeadstockStore } from '@/stores/headstock'
import { useKonvaCanvas }   from '@/composables/useKonvaCanvas'
import { useDxfImport }     from '@/composables/useDxfImport'

const store = useHeadstockStore()
const emit  = defineEmits<{ navigate:[tab:string]; toast:[msg:string] }>()

// ── Two canvases: left=raw, right=normalized ──────────────────────────────────
const leftRef  = ref<HTMLElement|null>(null)
const rightRef = ref<HTMLElement|null>(null)

// We manage Konva manually here (two stages, not the standard useKonvaCanvas
// which assumes one canvas per view). Raw left, norm right.
let rawStage:  Konva.Stage|null = null
let normStage: Konva.Stage|null = null
let rawLayer:  Konva.Layer
let normLayer: Konva.Layer

// ── Composable ────────────────────────────────────────────────────────────────
const {
  rawPaths, normPaths, rawBBox,
  fileType, fileName, fileSize, units,
  pipeStage, error,
  fitMode, pad, flipY,
  combinedNormPath,
  loadFile, applyNormalize, togglePath,
} = useDxfImport()

// ── Use-as toggle ─────────────────────────────────────────────────────────────
const useAs = ref<'hs'|'inlay'>('hs')

// ── Pipeline step labels ──────────────────────────────────────────────────────
const STEPS = ['Load','Parse','Normalize','Ready']
const stepIdx = computed(()=>
  pipeStage.value === 'idle'      ? -1 :
  pipeStage.value === 'load'      ?  0 :
  pipeStage.value === 'parse'     ?  1 :
  pipeStage.value === 'normalize' ?  2 : 3
)

// ── Init canvases ─────────────────────────────────────────────────────────────
const TW = 200, TH = 320

onMounted(()=>{
  if (leftRef.value) {
    const W = leftRef.value.clientWidth, H = leftRef.value.clientHeight
    rawStage  = new Konva.Stage({ container: leftRef.value,  width: W, height: H })
    rawLayer  = new Konva.Layer(); rawStage.add(rawLayer)
    drawLeftBg(W, H)
  }
  if (rightRef.value) {
    const W = rightRef.value.clientWidth, H = rightRef.value.clientHeight
    normStage = new Konva.Stage({ container: rightRef.value, width: W, height: H })
    normLayer = new Konva.Layer(); normStage.add(normLayer)
    drawRightBg(W, H)
  }
})

// ── Background helpers ────────────────────────────────────────────────────────
function vellumCard(layer: Konva.Layer, W: number, H: number, label: string) {
  layer.destroyChildren()
  const pad = 18
  layer.add(new Konva.Rect({x:0,y:0,width:W,height:H,fill:'#0f0d0a'}))
  layer.add(new Konva.Rect({x:pad,y:pad,width:W-pad*2,height:H-pad*2,fill:'#f0e8d4',cornerRadius:3}))
  layer.add(new Konva.Rect({x:pad,y:pad,width:W-pad*2,height:H-pad*2,fill:'none',stroke:'#d8cfb0',strokeWidth:.8,cornerRadius:3}))
  layer.add(new Konva.Text({x:pad+8,y:pad+8,text:label,fill:'#c0b090',fontSize:8,fontFamily:'Courier New',opacity:.7}))
  layer.draw()
}

function drawLeftBg(W: number, H: number) {
  if (!rawLayer) return
  vellumCard(rawLayer, W, H, 'RAW')
}

function drawRightBg(W: number, H: number) {
  if (!normLayer) return
  const pad = 18
  vellumCard(normLayer, W, H, `NORMALIZED  ${TW} × ${TH}`)
  // target frame
  const tSc = Math.min((W-pad*2-40)/TW, (H-pad*2-40)/TH)
  const tOX = pad + (W-pad*2-TW*tSc)/2
  const tOY = pad + (H-pad*2-TH*tSc)/2
  normLayer.add(new Konva.Rect({x:tOX,y:tOY,width:TW*tSc,height:TH*tSc,fill:'none',stroke:'#c0b488',strokeWidth:.6,dash:[4,4]}))
  normLayer.add(new Konva.Line({points:[tOX+TW*tSc/2,tOY,tOX+TW*tSc/2,tOY+TH*tSc],stroke:'#5b8fa8',strokeWidth:.6,dash:[4,4],opacity:.5}))
  const gs = 10*tSc
  for(let x=tOX;x<=tOX+TW*tSc;x+=gs) normLayer.add(new Konva.Line({points:[x,tOY,x,tOY+TH*tSc],stroke:'#d4c9a8',strokeWidth:.3}))
  for(let y=tOY;y<=tOY+TH*tSc;y+=gs) normLayer.add(new Konva.Line({points:[tOX,y,tOX+TW*tSc,y],stroke:'#d4c9a8',strokeWidth:.3}))
  normLayer.draw()
  // store tSc, tOX, tOY for path rendering
  ;(normLayer as any)._tSc = tSc; (normLayer as any)._tOX = tOX; (normLayer as any)._tOY = tOY
}

// ── Watch paths → redraw ──────────────────────────────────────────────────────
watch(rawPaths, renderRaw, { deep: true })
watch(normPaths, renderNorm, { deep: true })

function renderRaw() {
  if (!rawLayer || !rawStage || !rawBBox.value) return
  const W = rawStage.width(), H = rawStage.height(), pad = 18
  const bb = rawBBox.value
  const aW = W-pad*2-40, aH = H-pad*2-40
  const sc = Math.min(aW/bb.w, aH/bb.h)
  const ox = pad+(aW-bb.w*sc)/2+20 - bb.minX*sc
  const oy = pad+(aH-bb.h*sc)/2+20 - bb.minY*sc

  // Redraw bg + paths on same layer
  drawLeftBg(W, H)
  rawPaths.value.filter(p=>p.visible&&p.d).forEach(p=>{
    rawLayer.add(new Konva.Path({data:p.d,x:ox,y:oy,scaleX:sc,scaleY:sc,fill:'none',stroke:p.color,strokeWidth:1.5/sc}))
  })
  // bbox outline
  rawLayer.add(new Konva.Rect({
    x: pad+(aW-bb.w*sc)/2+20, y: pad+(aH-bb.h*sc)/2+20,
    width:bb.w*sc, height:bb.h*sc,
    fill:'none',stroke:'#b8962e',strokeWidth:.6,dash:[4,4],opacity:.5,
  }))
  rawLayer.add(new Konva.Text({
    x: pad+(aW-bb.w*sc)/2+22, y: pad+(aH-bb.h*sc)/2+22,
    text:`${bb.w.toFixed(1)} × ${bb.h.toFixed(1)} ${units.value}`,
    fill:'#b8962e',fontSize:8,fontFamily:'Courier New',opacity:.7,
  }))
  rawLayer.draw()
}

function renderNorm() {
  if (!normLayer || !normStage) return
  const W = normStage.width(), H = normStage.height()
  drawRightBg(W, H)
  const tSc: number = (normLayer as any)._tSc
  const tOX: number = (normLayer as any)._tOX
  const tOY: number = (normLayer as any)._tOY
  if (!tSc) return
  normPaths.value.filter(p=>p.visible&&p.d).forEach(p=>{
    normLayer.add(new Konva.Path({data:p.d,x:tOX,y:tOY,scaleX:tSc,scaleY:tSc,fill:'rgba(122,58,26,.06)',stroke:p.color,strokeWidth:1.5/tSc}))
  })
  normLayer.draw()
}

// ── File drop / input ─────────────────────────────────────────────────────────
const dragOver = ref(false)

function onDrop(e: DragEvent) {
  e.preventDefault(); dragOver.value = false
  const f = e.dataTransfer?.files[0]
  if (f) loadFile(f)
}

function onFileInput(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) loadFile(f);
  (e.target as HTMLInputElement).value = ''
}

const fileInputRef = ref<HTMLInputElement|null>(null)

// ── Send to workspace ─────────────────────────────────────────────────────────
function sendToWorkspace() {
  const path = combinedNormPath.value
  if (!path) { emit('toast','No normalized paths — load a file first'); return }
  store.receiveHandoff({
    path,
    label: `Import: ${fileName.value}`,
    source: 'import',
    useAs:  useAs.value,
  })
  emit('navigate','workspace')
  emit('toast', `Sent to workspace as ${useAs.value === 'hs' ? 'headstock template' : 'inlay element'}`)
}
</script>

<template>
  <div class="import-layout">

    <!-- Left: raw canvas -->
    <div class="import-canvas" ref="leftRef"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop="onDrop"
    >
      <!-- Drop overlay shown until a file is loaded -->
      <div v-if="pipeStage === 'idle'" class="drop-overlay" :class="{ 'drag-over': dragOver }">
        <div class="drop-zone" @click="fileInputRef?.click()">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect x="3" y="6" width="17" height="22" rx="2" stroke="#9a8460" stroke-width="1"/>
            <path d="M3 6l5-5h12l5 5" stroke="#9a8460" stroke-width="1" stroke-linejoin="round"/>
            <path d="M11 17v8M8 21l3 4 3-4" stroke="#b8962e" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="20" y="3" width="9" height="9" rx="1.5" fill="#0f0d0a" stroke="#5b8fa8" stroke-width=".8"/>
            <text x="24.5" y="10" text-anchor="middle" font-size="5.5" fill="#5b8fa8">DX</text>
          </svg>
          <div class="drop-title">Drop SVG or DXF here</div>
          <div class="drop-sub">or click to browse</div>
          <div class="drop-badges">
            <span class="badge">SVG</span>
            <span class="badge">DXF</span>
            <span class="badge">R12 · R14 · 2000+</span>
          </div>
        </div>
      </div>

      <!-- Error state -->
      <div v-if="error" class="import-error">{{ error }}</div>
    </div>

    <!-- Right: normalized canvas -->
    <div class="import-canvas" ref="rightRef"></div>

    <!-- Panel -->
    <div class="import-panel">

      <!-- Pipeline indicator -->
      <div class="sec">
        <div class="sec-ttl">Import pipeline</div>
        <div class="pipeline">
          <div v-for="(s, i) in STEPS" :key="s" class="pipe-step"
            :class="{ done: i < stepIdx, active: i === stepIdx }">{{ s }}</div>
        </div>
      </div>

      <!-- File info -->
      <div v-if="pipeStage !== 'idle'" class="sec">
        <div class="sec-lbl">File</div>
        <div class="info-grid">
          <span class="ikey">Name</span><span class="ival">{{ fileName }}</span>
          <span class="ikey">Type</span><span class="ival">{{ fileType?.toUpperCase() }}</span>
          <span class="ikey">Size</span><span class="ival">{{ (fileSize/1024).toFixed(1) }} KB</span>
          <span class="ikey">Paths</span><span class="ival ok">{{ rawPaths.length }}</span>
          <span class="ikey">Units</span><span class="ival">{{ units }}</span>
          <span v-if="rawBBox" class="ikey">Bbox</span>
          <span v-if="rawBBox" class="ival">{{ rawBBox.w.toFixed(1) }} × {{ rawBBox.h.toFixed(1) }}</span>
        </div>
      </div>

      <!-- Normalize controls -->
      <div v-if="pipeStage !== 'idle'" class="sec">
        <div class="sec-lbl">Normalize</div>
        <div class="param-row">
          <span class="param-name">Fit mode</span>
          <select class="ctrl-select" v-model="fitMode" @change="applyNormalize">
            <option value="contain">Contain</option>
            <option value="width">Width</option>
            <option value="height">Height</option>
            <option value="stretch">Stretch</option>
          </select>
        </div>
        <div class="param-row">
          <span class="param-name">Padding</span>
          <input class="prop-val" type="number" v-model.number="pad" min="0" max="40" @change="applyNormalize">
          <span class="param-unit">u</span>
        </div>
        <div class="param-row">
          <span class="param-name">Flip Y</span>
          <select class="ctrl-select" v-model="flipY" @change="applyNormalize">
            <option value="auto">Auto (DXF=yes)</option>
            <option value="yes">Always</option>
            <option value="no">Never</option>
          </select>
        </div>
        <button class="sbtn on" style="width:100%;margin-top:4px" @click="applyNormalize">↻ Re-apply</button>
      </div>

      <!-- Use as -->
      <div v-if="pipeStage === 'ready'" class="sec">
        <div class="sec-lbl">Send to workspace as</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:8px">
          <div class="sbtn" :class="{ on: useAs === 'hs' }"    @click="useAs = 'hs'">Template</div>
          <div class="sbtn" :class="{ on: useAs === 'inlay' }" @click="useAs = 'inlay'">Inlay</div>
        </div>
        <button class="sbtn go" style="width:100%;padding:7px 0" @click="sendToWorkspace">
          Send to workspace →
        </button>
      </div>

      <!-- Path list -->
      <div class="sec-lbl" style="padding:8px 13px 4px">Paths</div>
      <div class="layer-list">
        <div v-if="!rawPaths.length" class="no-sel">Load a file to see paths</div>
        <div
          v-for="p in rawPaths" :key="p.id"
          class="layer-item" :class="{ sel: p.visible }"
        >
          <span class="lpip" :style="{ background: p.color }"></span>
          <span class="lname">{{ p.label }}{{ p.layer && p.layer !== '0' ? ` [${p.layer}]` : '' }}</span>
          <span class="lvis" @click="togglePath(p.id)">{{ p.visible ? '◉' : '○' }}</span>
        </div>
      </div>

      <!-- Load new file button -->
      <div style="padding:10px 13px;margin-top:auto;border-top:1px solid var(--w3)">
        <input ref="fileInputRef" type="file" accept=".svg,.dxf" style="display:none" @change="onFileInput">
        <button class="sbtn" style="width:100%" @click="fileInputRef?.click()">↑ Load different file</button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.import-layout {
  display: grid;
  grid-template-columns: 1fr 1fr 272px;
  height: 100%;
}
.import-canvas { overflow: hidden; background: var(--w0); position: relative; }
.import-panel  { background: var(--w1); border-left: 1px solid var(--w3); display: flex; flex-direction: column; overflow: hidden; }

/* Drop overlay */
.drop-overlay {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(15,13,10,.6);
  transition: background .15s;
}
.drop-overlay.drag-over { background: rgba(184,150,46,.06); }
.drop-zone {
  width: 280px; height: 180px;
  border: 1px dashed var(--w4); border-radius: 4px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 9px;
  cursor: pointer; transition: all .12s;
}
.drop-zone:hover, .drag-over .drop-zone { border-color: var(--br); }
.drop-title { font-family: var(--serif); font-size: 12px; font-style: italic; color: var(--v1); }
.drop-sub   { font-size: 9px; color: var(--dim); }
.drop-badges { display: flex; gap: 5px; }
.badge { padding: 2px 5px; border: 1px solid var(--w3); border-radius: 2px; font-size: 8px; color: var(--dim); }

/* Pipeline */
.pipeline { display: flex; gap: 0; margin: 8px 0; }
.pipe-step {
  flex: 1; text-align: center; font-size: 7px; letter-spacing: .4px;
  padding: 4px 2px; border: 1px solid var(--w3); color: var(--dim); position: relative;
}
.pipe-step:not(:last-child)::after { content:'›'; position:absolute; right:-5px; top:50%; transform:translateY(-50%); color:var(--w4); }
.pipe-step.done   { border-color: var(--green); color: var(--green2); background: rgba(58,122,74,.06); }
.pipe-step.active { border-color: var(--br3);   color: var(--br2);   background: rgba(184,150,46,.06); }

/* Info grid */
.info-grid { display: grid; grid-template-columns: 48px 1fr; gap: 3px 8px; }
.ikey { font-size: 9px; color: var(--dim); }
.ival { font-size: 9px; color: var(--v1); }
.ival.ok { color: var(--green2); }

/* Controls */
.ctrl-select {
  flex: 1; background: var(--w2); border: 1px solid var(--w3); border-radius: 2px;
  color: var(--v1); font-family: var(--mono); font-size: 10px; padding: 3px 5px;
}
.ctrl-select:focus { outline: none; border-color: var(--br); }

/* Error */
.import-error {
  position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
  background: rgba(154,56,40,.12); border: 1px solid var(--red);
  border-radius: 3px; padding: 6px 12px; font-size: 9px; color: #c06050;
  max-width: 80%; text-align: center;
}
</style>
