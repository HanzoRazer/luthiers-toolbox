<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import Konva from 'konva'
import { storeToRefs } from 'pinia'
import { useHeadstockStore } from '@/stores/headstock'
import { useKonvaCanvas } from '@/composables/useKonvaCanvas'
import {
  buildParametricPath, buildTunerPositions,
  scoreNovelty, runGates, exportParametricSVG,
} from '@/composables/useParametric'
import { drawBackground } from '@/composables/useHeadstock'
import {
  BODY_PARAM_DEFS, SHOULDER_PARAM_DEFS, TUNER_PARAM_DEFS,
  TIP_STYLE_NAMES, TUNER_PATTERNS, CORPUS, CORPUS_COLORS, PARAM_RANGES, MM,
} from '@/assets/data/headstockData'
import type { TipStyle, TunerPattern } from '@/types/headstock'

const store = useHeadstockStore()
const { params, tipStyle, tunerPat, showCorpusOverlay, toolDiameter } = storeToRefs(store)

const emit = defineEmits<{ navigate: [tab: string]; toast: [msg: string] }>()

const containerRef = ref<HTMLElement | null>(null)
const canvas = useKonvaCanvas(containerRef)

let bgL: Konva.Layer, hsL: Konva.Layer, ovL: Konva.Layer, guL: Konva.Layer

onMounted(() => {
  bgL = canvas.addLayer(); ovL = canvas.addLayer()
  hsL = canvas.addLayer(); guL = canvas.addLayer()
  redraw()
})

watch([params, tipStyle, tunerPat, showCorpusOverlay], redraw, { deep: true })

function redraw() {
  if (!hsL) return
  drawBackground(bgL, canvas, true)
  drawHS(); drawOverlay(); drawGuides()
}

function drawHS() {
  hsL.destroyChildren()
  const d = buildParametricPath(params.value, tipStyle.value)
  const ko = { data: d, x: canvas.OX.value, y: canvas.OY.value, scaleX: canvas.SC.value, scaleY: canvas.SC.value, listening: false }
  hsL.add(new Konva.Path({ ...ko, fill: 'rgba(0,0,0,.2)', offsetX: -3, offsetY: 3 }))
  hsL.add(new Konva.Path({ ...ko, fill: '#7a3d1a' }))
  for (let i = 0; i < 8; i++) {
    const yo = canvas.OY.value + (28 + i * 34) * canvas.SC.value
    hsL.add(new Konva.Line({ points: [canvas.OX.value + 18 * canvas.SC.value, yo, canvas.OX.value + 182 * canvas.SC.value, yo], stroke: '#fff', strokeWidth: 0.3, opacity: 0.05, listening: false }))
  }
  hsL.add(new Konva.Path({ ...ko, fill: 'none', stroke: '#4a2010', strokeWidth: 2 }))
  buildTunerPositions(params.value, tunerPat.value).forEach(t => {
    const tx = canvas.p2cx(t.x), ty = canvas.p2cy(t.y)
    hsL.add(new Konva.Circle({ x: tx, y: ty, radius: 6.5, fill: '#120c06', stroke: '#3a1c08', strokeWidth: 0.8, listening: false }))
    hsL.add(new Konva.Circle({ x: tx, y: ty, radius: 3, fill: '#d4b060', listening: false }))
  })
  hsL.draw()
}

function drawOverlay() {
  ovL.destroyChildren()
  if (!showCorpusOverlay.value) { ovL.draw(); return }
  Object.entries(CORPUS).forEach(([name, cp]) => {
    ovL.add(new Konva.Path({
      data: buildParametricPath(cp, 0),
      x: canvas.OX.value, y: canvas.OY.value, scaleX: canvas.SC.value, scaleY: canvas.SC.value,
      fill: 'none', stroke: CORPUS_COLORS[name] ?? '#888', strokeWidth: 0.8, opacity: 0.22, dash: [4, 3],
    }))
  })
  ovL.draw()
}

function drawGuides() {
  guL.destroyChildren()
  const { p2cx, p2cy, OX, OY, SC } = canvas
  const ny = p2cy(298), cx2 = p2cx(100), nw = params.value.nutWidth * SC.value / 2
  const tipY = p2cy(298 - params.value.length)
  guL.add(new Konva.Line({ points: [cx2, OY.value - 22, cx2, OY.value + 320 * SC.value + 14], stroke: '#5b8fa8', strokeWidth: 0.8, dash: [5, 4], opacity: 0.65 }))
  guL.add(new Konva.Line({ points: [cx2 - nw, ny, cx2 + nw, ny], stroke: '#b8962e', strokeWidth: 2.2, strokeLinecap: 'round' }))
  guL.add(new Konva.Text({ x: cx2, y: ny + 12, text: `${(params.value.nutWidth * MM).toFixed(1)} mm`, fill: '#b8962e', fontSize: 7.5, fontFamily: 'Courier New', align: 'center', width: 50, offsetX: 25, opacity: 0.8 }))
  guL.add(new Konva.Line({ points: [OX.value - 22, ny, OX.value - 22, tipY], stroke: '#8a7448', strokeWidth: 0.6, opacity: 0.5 }))
  guL.add(new Konva.Line({ points: [OX.value - 26, ny, OX.value - 18, ny], stroke: '#8a7448', strokeWidth: 0.5, opacity: 0.5 }))
  guL.add(new Konva.Line({ points: [OX.value - 26, tipY, OX.value - 18, tipY], stroke: '#8a7448', strokeWidth: 0.5, opacity: 0.5 }))
  guL.draw()
}

const novelty = computed(() => scoreNovelty(params.value))
const gates   = computed(() => runGates(params.value, toolDiameter.value))
const novColor = computed(() => novelty.value.value < 30 ? '#c85040' : novelty.value.value < 55 ? '#b87020' : '#5ab86a')

function onSlider(key: string, val: string) {
  store.updateParam(key as any, parseFloat(val) as never)
}
function dispVal(id: string, pct = false): string {
  const v = (params.value as any)[id]
  return pct ? `${Math.round(v * 100)}` : String(v)
}
function randomize() { store.randomizeParams(PARAM_RANGES) }
function loadPreset(name: string) { const cp = CORPUS[name]; if (cp) store.loadPreset(cp) }

function doExport() {
  const svg = exportParametricSVG(params.value, tipStyle.value, tunerPat.value)
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml' })),
    download: 'ps-parametric.svg',
  })
  a.click()
}

function sendToWorkspace() {
  store.receiveHandoff({
    path: buildParametricPath(params.value, tipStyle.value),
    label: `Parametric (nov:${novelty.value.value})`,
    source: 'parametric',
    useAs: 'hs',
  })
  emit('navigate', 'workspace')
  emit('toast', 'Parametric design sent to workspace')
}
</script>

<template>
  <div class="p3-layout">
    <aside class="p3-left">
      <div class="pcat">
        <div class="pcat-lbl">Body geometry</div>
        <div v-for="def in BODY_PARAM_DEFS" :key="def.id" class="param-row">
          <span class="param-name">{{ def.label }}</span>
          <input class="param-slider" type="range" :min="def.min" :max="def.max" :step="def.step"
            :value="(params as any)[def.id]" @input="onSlider(def.id, ($event.target as HTMLInputElement).value)">
          <span class="param-val">{{ dispVal(def.id, def.pct) }}</span>
          <span class="param-unit">{{ def.unit }}</span>
        </div>
      </div>
      <div class="pcat">
        <div class="pcat-lbl">Tip style</div>
        <div class="tip-grid">
          <div v-for="(name, i) in TIP_STYLE_NAMES" :key="i" class="sbtn" :class="{ on: tipStyle === i }"
            @click="store.tipStyle = i as TipStyle">{{ name }}</div>
        </div>
      </div>
      <div class="pcat">
        <div class="pcat-lbl">Shoulder &amp; waist</div>
        <div v-for="def in SHOULDER_PARAM_DEFS" :key="def.id" class="param-row">
          <span class="param-name">{{ def.label }}</span>
          <input class="param-slider" type="range" :min="def.min" :max="def.max" :step="def.step"
            :value="(params as any)[def.id]" @input="onSlider(def.id, ($event.target as HTMLInputElement).value)">
          <span class="param-val">{{ dispVal(def.id, def.pct) }}</span>
          <span class="param-unit">{{ def.unit }}</span>
        </div>
      </div>
      <div class="pcat">
        <div class="pcat-lbl">Tuner pattern</div>
        <div class="tpat-row">
          <div v-for="pat in TUNER_PATTERNS" :key="pat" class="sbtn" style="padding:4px 6px;font-size:8px"
            :class="{ on: tunerPat === pat }" @click="store.tunerPat = pat as TunerPattern">{{ pat }}</div>
        </div>
        <div v-for="def in TUNER_PARAM_DEFS" :key="def.id" class="param-row" style="margin-top:8px">
          <span class="param-name">{{ def.label }}</span>
          <input class="param-slider" type="range" :min="def.min" :max="def.max" :step="def.step"
            :value="(params as any)[def.id]" @input="onSlider(def.id, ($event.target as HTMLInputElement).value)">
          <span class="param-val">{{ dispVal(def.id) }}</span>
          <span class="param-unit">{{ def.unit }}</span>
        </div>
      </div>
      <div class="pcat" style="border-bottom:none">
        <div class="pcat-lbl">Presets</div>
        <div class="preset-grid">
          <div v-for="name in Object.keys(CORPUS)" :key="name" class="preset-btn" @click="loadPreset(name)">{{ name }}</div>
        </div>
      </div>
    </aside>

    <div class="p3-canvas" ref="containerRef"></div>

    <aside class="p3-right">
      <div class="sec">
        <div class="sec-ttl">Design score</div>
        <div class="nov-row">
          <span class="nov-val" :style="{ color: novColor }">{{ novelty.value }}</span>
          <span style="font-size:9px;color:var(--dim)">novelty</span>
        </div>
        <div class="nov-bar-bg"><div class="nov-bar-fg" :style="{ width: novelty.value + '%', background: novColor }"></div></div>
        <div style="font-size:9px;color:var(--dim)">{{ novelty.label }}</div>
      </div>
      <div class="sec">
        <div class="sec-lbl">Corpus distance</div>
        <div v-for="(dist, name) in novelty.corpusDists" :key="name" class="corpus-row">
          <span class="corp-name">{{ name }}</span>
          <div class="corp-bar-bg"><div class="corp-bar-fg" :style="{ width: `${(1 - dist / Math.max(...Object.values(novelty.corpusDists))) * 100}%`, background: (CORPUS_COLORS as any)[name] + '44' }"></div></div>
          <span class="corp-val" :style="{ color: dist < 0.25 ? 'var(--red)' : 'var(--dim2)' }">{{ dist.toFixed(3) }}</span>
        </div>
      </div>
      <div class="sec">
        <div class="sec-lbl">Manufacture gates</div>
        <div v-for="gate in gates" :key="gate.name" class="gate-item">
          <div class="gate-icon" :class="gate.pass">{{ gate.pass === 'pass' ? '✓' : gate.pass === 'warn' ? '!' : '✗' }}</div>
          <div class="gate-text"><div class="gname">{{ gate.name }}</div><div class="gdetail">{{ gate.detail }}</div></div>
        </div>
      </div>
      <div class="sec">
        <div class="sec-lbl">Tool diameter</div>
        <div class="param-row">
          <input class="param-slider" type="range" min="0.5" max="6" step="0.5" :value="toolDiameter"
            @input="store.toolDiameter = +($event.target as HTMLInputElement).value">
          <span class="param-val">{{ toolDiameter.toFixed(1) }}</span>
          <span class="param-unit">mm</span>
        </div>
      </div>
      <div class="sec" style="border-bottom:none;margin-top:auto">
        <div style="display:flex;gap:6px">
          <button class="sbtn" style="flex:1" @click="randomize">⚄ Random</button>
          <button class="sbtn" :class="{ on: showCorpusOverlay }" style="flex:1" @click="store.showCorpusOverlay = !store.showCorpusOverlay">Overlay</button>
        </div>
        <button class="sbtn go" style="width:100%;margin-top:6px;padding:7px 0" @click="doExport">↓ Export SVG</button>
        <button class="sbtn go" style="width:100%;margin-top:5px;padding:7px 0" @click="sendToWorkspace">Send to workspace →</button>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.p3-layout { display:grid; grid-template-columns:232px 1fr 218px; height:100%; }
.p3-left,.p3-right { background:var(--w1); overflow-y:auto; display:flex; flex-direction:column; }
.p3-left { border-right:1px solid var(--w3); } .p3-right { border-left:1px solid var(--w3); }
.p3-canvas { overflow:hidden; background:var(--w0); }
.tip-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:3px; }
.tpat-row { display:flex; gap:3px; flex-wrap:wrap; }
.preset-grid { display:grid; grid-template-columns:1fr 1fr; gap:4px; }
.preset-btn { padding:6px 4px; background:var(--w2); border:1px solid var(--w3); border-radius:3px; font-family:var(--serif); font-size:10px; font-style:italic; color:var(--dim); cursor:pointer; text-align:center; transition:all .1s; }
.preset-btn:hover { border-color:var(--br3); color:var(--v1); }
.nov-row { display:flex; align-items:baseline; gap:8px; }
.nov-val { font-size:20px; font-family:var(--serif); }
.nov-bar-bg { height:5px; background:var(--w3); border-radius:3px; overflow:hidden; margin:4px 0 3px; }
.nov-bar-fg { height:100%; border-radius:3px; transition:width .3s,background .3s; }
.corpus-row { display:flex; align-items:center; gap:6px; margin-bottom:4px; }
.corp-name { width:68px; font-size:9px; color:var(--dim); }
.corp-bar-bg { flex:1; height:3px; background:var(--w3); border-radius:2px; overflow:hidden; }
.corp-bar-fg { height:100%; transition:width .2s; }
.corp-val { width:30px; text-align:right; font-size:8px; }
</style>
