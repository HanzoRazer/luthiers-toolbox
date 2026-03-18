<script setup lang="ts">
/**
 * NeckView.vue
 *
 * Four-tab neck workspace.  Each tab shows its panel on the left and
 * a live Konva canvas in the centre.
 *
 * Tab → Canvas drawing:
 *   Taper      — top view, neck outline + string lines
 *   Fretboard  — cross-section at preview fret showing radius arc + toolpath
 *   Profile    — cross-section showing back profile with coupling annotation
 *   Transition — side view showing blend zone + volute
 *
 * Right panel shows the shared summary and export controls.
 */

import { ref, watch, onMounted } from 'vue'
import Konva from 'konva'
import { useNeckStore } from '@/stores/neck'
import { useKonvaCanvas } from '@/composables/useKonvaCanvas'
import NeckTaperPanel          from '@/components/cam/neck/NeckTaperPanel.vue'
import FretboardPanel          from '@/components/cam/neck/FretboardPanel.vue'
import NeckProfilePanel        from '@/components/cam/neck/NeckProfilePanel.vue'
import HeadstockTransitionPanel from '@/components/cam/neck/HeadstockTransitionPanel.vue'

const emit = defineEmits<{ toast: [msg: string] }>()

const store = useNeckStore()
const containerRef = ref<HTMLElement | null>(null)
const canvas = useKonvaCanvas(containerRef)
let layer: Konva.Layer

onMounted(() => {
  layer = canvas.addLayer()
  redraw()
})

watch(
  [
    () => store.activeTab,
    () => store.previewFret,
    () => store.summary,
    () => store.fretboard.fretStations.value,
    () => store.taper.stations.value,
    () => store.profile.profileStations.value,
    () => store.transition.derived.value,
  ],
  redraw,
  { deep: true },
)

// ── Canvas drawing ────────────────────────────────────────────────────────────

const CX = () => canvas.W.value / 2
const CY = () => canvas.H.value / 2

function bg() {
  layer.destroyChildren()
  layer.add(new Konva.Rect({ x:0, y:0, width: canvas.W.value, height: canvas.H.value, fill:'#0f0d0a' }))
}

function redraw() {
  if (!layer) return
  bg()
  if (store.activeTab === 'taper')      drawTaper()
  else if (store.activeTab === 'fretboard') drawFretboard()
  else if (store.activeTab === 'profile')   drawProfile()
  else                                       drawTransition()
  layer.draw()
}

// ── Taper — top view ──────────────────────────────────────────────────────────
function drawTaper() {
  const pm = 4.8
  const nutX = 80
  const cy2 = CY()
  const spec = store.taper.spec
  const stations = store.taper.stations.value

  // Fretboard outline
  const outlineL: number[] = [], outlineR: number[] = []
  stations.forEach(st => {
    const x = nutX + st.positionMm * pm
    outlineL.push(x, cy2 - st.neckWidthMm / 2 * pm)
    outlineR.push(x, cy2 + st.neckWidthMm / 2 * pm)
  })
  if (outlineL.length >= 4) {
    layer.add(new Konva.Line({ points: [...outlineL, ...outlineR.reverse()], closed: true, fill: 'rgba(100,60,20,.3)', stroke: '#7a4020', strokeWidth: 1.2, listening: false }))
  }

  // Fret slots
  stations.forEach(st => {
    if (st.fret === 0) return
    const x = nutX + st.positionMm * pm
    const hw = st.neckWidthMm / 2 * pm
    layer.add(new Konva.Line({ points: [x, cy2-hw, x, cy2+hw], stroke: [1,3,5,7,9,12,15,17,19].includes(st.fret) ? 'rgba(200,180,100,.5)' : 'rgba(100,80,40,.3)', strokeWidth: st.fret === 12 ? 1.4 : .8, listening: false }))
    if ([1,3,5,7,9,12].includes(st.fret)) {
      layer.add(new Konva.Text({ x, y: cy2 - st.neckWidthMm/2*pm - 14, text: String(st.fret), fill:'#5a4830', fontSize:7, fontFamily:'Courier New', align:'center', width:20, offsetX:10, listening:false }))
    }
  })

  // String lines
  const colors = ['#c8c0a0','#b8b090','#a8a080','#989070','#888060','#787050']
  const nutSt = stations[0]
  const lastSt = stations[stations.length - 1]
  if (nutSt && lastSt) {
    nutSt.stringPositions.forEach((xn, i) => {
      const xl = stations[stations.length-1]
      const x0 = nutX + xn * pm, x1 = nutX + lastSt.positionMm * pm
      const y0 = cy2 + xn * pm, y1 = cy2 + (xl?.stringPositions[i] ?? xn) * pm
      layer.add(new Konva.Line({ points: [nutX, y0, x1, y1], stroke: colors[i] ?? '#a0a080', strokeWidth: .9+i*.06, listening: false }))
    })
    // Width dimension at nut
    const nw = nutSt.neckWidthMm
    layer.add(new Konva.Line({ points: [nutX, cy2-nw/2*pm-14, nutX, cy2+nw/2*pm+14], stroke:'rgba(184,150,46,.25)', strokeWidth:.5, listening:false }))
    layer.add(new Konva.Text({ x:nutX-20, y:cy2+nw/2*pm+16, text:`${nw.toFixed(1)}mm`, fill:'#b8962e', fontSize:8, fontFamily:'Courier New', listening:false }))
  }

  // Nut
  const nutHw = (nutSt?.neckWidthMm ?? store.taper.spec.nutWidthMm) / 2 * pm
  layer.add(new Konva.Rect({ x:nutX-3, y:cy2-nutHw, width:3, height:nutHw*2, fill:'rgba(232,223,200,.18)', stroke:'#b8962e', strokeWidth:1.2, listening:false }))

  layer.add(new Konva.Text({ x:10, y:CY()-8, text:'← HS', fill:'#5a4830', fontSize:8, fontFamily:'Courier New', listening:false }))
  layer.add(new Konva.Text({ x:canvas.W.value-40, y:CY()-8, text:'Body →', fill:'#5a4830', fontSize:8, fontFamily:'Courier New', listening:false }))
}

// ── Fretboard — cross-section ─────────────────────────────────────────────────
function drawFretboard() {
  const pm = 5.2
  const cx2 = CX(), cy2 = CY()
  const stations = store.fretboard.fretStations.value
  const st = stations.find(s => s.fret === store.previewFret) ?? stations[0]
  if (!st) return

  const r = st.radiusInch * 25.4
  const w = st.widthMm
  const h = st.crownMm
  const rpx = r * pm, wpx = w * pm, hpx = h * pm

  // Board cross-section arc
  const startA = -Math.asin(Math.min(1, wpx/2/rpx))
  const endA   =  Math.asin(Math.min(1, wpx/2/rpx))
  // angle + rotation take degrees; convert radians once, no double-conversion
  layer.add(new Konva.Arc({ x:cx2, y:cy2-hpx+rpx, innerRadius:0, outerRadius:rpx,
    angle:   (endA - startA)    * 180/Math.PI,
    rotation:(Math.PI + startA) * 180/Math.PI,
    fill:'rgba(100,60,20,.28)', listening:false }))

  // Arc stroke — same angles, thin annulus
  layer.add(new Konva.Arc({ x:cx2, y:cy2-hpx+rpx, innerRadius:rpx-.8, outerRadius:rpx+.8,
    angle:   (endA - startA)    * 180/Math.PI,
    rotation:(Math.PI + startA) * 180/Math.PI,
    fill:'#b8962e', listening:false }))

  // Fret wire
  layer.add(new Konva.Rect({ x:cx2-wpx/2, y:cy2-hpx-1.0*pm, width:wpx, height:1.0*pm, fill:'rgba(200,200,160,.45)', listening:false }))

  // Ball-nose pass circles
  const step = store.fretboard.spec.ballNoseMm * store.fretboard.spec.stepoverPct/100 * pm
  const bnR = store.fretboard.spec.ballNoseMm/2 * pm
  const nPasses = Math.ceil((wpx + bnR*2) / step) + 1
  for(let i=0;i<nPasses;i++){
    const px = cx2 - wpx/2 - bnR + i*step
    if(px > cx2+wpx/2+bnR+2) break
    layer.add(new Konva.Circle({ x:px, y:cy2-hpx/2, radius:bnR*0.55, stroke:'rgba(200,112,48,.3)', strokeWidth:.5, fill:'none', listening:false }))
  }

  // Labels
  layer.add(new Konva.Text({ x:cx2-wpx/2, y:cy2+10, text:`Fret ${st.fret === 0 ? 'Nut' : st.fret}  r=${st.radiusInch.toFixed(2)}"  w=${w.toFixed(1)}mm  crown=${h.toFixed(4)}mm`, fill:'#b8962e', fontSize:8, fontFamily:'Courier New', listening:false }))

  // Width dim
  layer.add(new Konva.Line({ points:[cx2-wpx/2,cy2+24,cx2+wpx/2,cy2+24], stroke:'rgba(184,150,46,.4)', strokeWidth:.6, listening:false }))
  layer.add(new Konva.Text({ x:cx2, y:cy2+30, text:`${w.toFixed(1)}mm`, fill:'#b8962e', fontSize:7.5, fontFamily:'Courier New', align:'center', width:60, offsetX:30, listening:false }))
}

// ── Profile — back cross-section ──────────────────────────────────────────────
function drawProfile() {
  const pm = 5.0
  const cx2 = CX(), cy2 = CY()
  const n = store.previewFret
  const bd  = store.profile.backDepth(n)
  const crown = store.profile.crownComp(n)
  const hw = store.profile.neckWidthAt(n) / 2
  const pts = store.profile.sampleProfile(bd, hw, store.profile.spec.shape, store.profile.spec.asymBassAddMm)

  // Back profile
  const konvaPts: number[] = []
  pts.forEach(([x,y]) => { konvaPts.push(cx2 + x*pm, cy2 - y*pm) })
  konvaPts.push(cx2+hw*pm, cy2, cx2-hw*pm, cy2)
  layer.add(new Konva.Line({ points: konvaPts, closed: true, fill:'rgba(100,60,20,.28)', stroke:'#b8962e', strokeWidth:1.8, listening:false }))

  // Fretboard block
  const fbH = store.profile.spec.fbThicknessMm * pm
  const crownPx = crown * pm
  layer.add(new Konva.Rect({ x:cx2-hw*pm, y:cy2-fbH-crownPx, width:hw*2*pm, height:fbH, fill:'rgba(160,100,40,.22)', stroke:'rgba(184,150,46,.4)', strokeWidth:.8, listening:false }))

  // Spine
  layer.add(new Konva.Line({ points:[cx2, cy2-bd*pm-crownPx-fbH-4, cx2, cy2+4], stroke:'rgba(91,143,168,.25)', strokeWidth:.6, dash:[3,3], listening:false }))

  // Label
  const total = store.profile.spec.depth1mm + (store.profile.spec.depth12mm - store.profile.spec.depth1mm) * (n/12)
  layer.add(new Konva.Text({ x:cx2, y:cy2+12, text:`Fret ${n === 0 ? 'Nut' : n}  back=${bd.toFixed(3)}mm  crown=${crown.toFixed(4)}mm  total=${total.toFixed(1)}mm`, fill:'#b8962e', fontSize:8, fontFamily:'Courier New', align:'center', width:400, offsetX:200, listening:false }))
}

// ── Transition — side view ────────────────────────────────────────────────────
function drawTransition() {
  const pm = 5.0
  const nutX = CX() - 20
  const bz = CY() + 40
  const spec = store.transition.spec as any

  const surfZ = (y: number) => store.transition.surfaceZ(y, spec)
  const yMin = -55, yMax = 70

  // Back surface fill
  const topPts: number[] = [], botPts: number[] = []
  for(let y=yMin;y<=yMax;y++) { topPts.push(nutX+y*pm, bz); botPts.push(nutX+y*pm, bz-surfZ(y)*pm) }
  layer.add(new Konva.Line({ points:[...topPts,...[...botPts].reverse()], closed:true, fill:'rgba(100,60,20,.32)', stroke:'#7a4020', strokeWidth:1.2, listening:false }))

  // Back curve highlight
  const curvePts: number[] = []
  for(let y=yMin;y<=yMax;y+=.5) curvePts.push(nutX+y*pm, bz-surfZ(y)*pm)
  layer.add(new Konva.Line({ points:curvePts, stroke:'#b8962e', strokeWidth:2, listening:false }))

  // HS plane ghost
  const hsPts: number[] = []
  for(let y=yMin;y<=-3;y++) hsPts.push(nutX+y*pm, bz-store.transition.headstockPlaneZ(y,spec)*pm)
  layer.add(new Konva.Line({ points:hsPts, stroke:'rgba(91,143,168,.4)', strokeWidth:.8, dash:[4,3], listening:false }))

  // Nut
  layer.add(new Konva.Line({ points:[nutX, bz-2, nutX, bz-spec.neckDepthMm*pm-10], stroke:'#b8962e', strokeWidth:2, listening:false }))
  layer.add(new Konva.Text({ x:nutX, y:bz-spec.neckDepthMm*pm-18, text:'NUT', fill:'#b8962e', fontSize:8, fontFamily:'Courier New', align:'center', width:40, offsetX:20, listening:false }))

  // Blend zone bracket
  const bs = spec.blendCentreMm-spec.blendLengthMm/2
  const be = spec.blendCentreMm+spec.blendLengthMm/2
  const bby = bz-spec.neckDepthMm*pm-22
  layer.add(new Konva.Line({ points:[nutX+bs*pm,bby,nutX+be*pm,bby], stroke:'rgba(200,112,48,.4)', strokeWidth:.7, dash:[3,3], listening:false }))
  layer.add(new Konva.Text({ x:nutX+(bs+be)/2*pm, y:bby-12, text:`blend ${spec.blendLengthMm}mm`, fill:'rgba(200,112,48,.7)', fontSize:7, fontFamily:'Courier New', align:'center', width:80, offsetX:40, listening:false }))

  // Volute
  if(spec.voluteType !== 'none' && spec.voluteHeightMm > 0) {
    const vx = nutX+spec.volutePositionMm*pm
    const vy = bz-surfZ(spec.volutePositionMm)*pm-6
    layer.add(new Konva.Line({ points:[vx,vy-14,vx,vy], stroke:'rgba(90,184,106,.5)', strokeWidth:.8, listening:false }))
    layer.add(new Konva.Text({ x:vx, y:vy-20, text:`${spec.voluteType}  +${spec.voluteHeightMm.toFixed(1)}mm`, fill:'#5ab86a', fontSize:7.5, fontFamily:'Courier New', align:'center', width:100, offsetX:50, listening:false }))
  }

  layer.add(new Konva.Text({ x:10, y:CY()-8, text:'← HS', fill:'#5a4830', fontSize:8, fontFamily:'Courier New', listening:false }))
  layer.add(new Konva.Text({ x:canvas.W.value-46, y:CY()-8, text:'Neck →', fill:'#5a4830', fontSize:8, fontFamily:'Courier New', listening:false }))
}

// ── Export ─────────────────────────────────────────────────────────────────────
function exportAll() {
  const payload = JSON.stringify(store.fullExportPayload.value, null, 2)
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([payload], { type: 'application/json' })),
    download: 'neck-spec.json',
  })
  a.click()
  emit('toast', 'Neck spec exported as neck-spec.json')
}

</script>

<template>
  <div class="neck-layout">

    <!-- Left: active tab panel -->
    <aside class="neck-left">
      <!-- Sub-tabs -->
      <div class="sub-tabs">
        <button v-for="tab in ['taper','fretboard','profile','transition'] as const" :key="tab"
          class="sub-tab" :class="{ on: store.activeTab === tab }"
          @click="store.activeTab = tab">
          {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
        </button>
      </div>

      <!-- Panel content -->
      <div class="panel-scroll">
        <NeckTaperPanel          v-if="store.activeTab === 'taper'" />
        <FretboardPanel          v-if="store.activeTab === 'fretboard'" />
        <NeckProfilePanel        v-if="store.activeTab === 'profile'" />
        <HeadstockTransitionPanel v-if="store.activeTab === 'transition'" />
      </div>
    </aside>

    <!-- Canvas -->
    <div class="neck-canvas" ref="containerRef"></div>

    <!-- Right: summary + export -->
    <aside class="neck-right">
      <!-- Preview fret slider -->
      <div class="sec">
        <div class="sec-lbl">Preview station</div>
        <div class="param-row">
          <span class="param-name">Fret</span>
          <input class="param-slider" type="range" :min="0" :max="store.fretboard.spec.fretCount" step="1"
            :value="store.previewFret"
            @input="store.previewFret = +($event.target as HTMLInputElement).value">
          <span class="param-val">{{ store.previewFret === 0 ? 'Nut' : store.previewFret }}</span>
        </div>
      </div>

      <!-- Summary -->
      <div class="sec">
        <div class="sec-lbl">Summary</div>
        <div class="info-row"><span class="info-k">Scale</span><span class="info-v">{{ store.summary.scale }}mm</span></div>
        <div class="info-row"><span class="info-k">Frets</span><span class="info-v">{{ store.summary.frets }}</span></div>
        <div class="info-row"><span class="info-k">Nut width</span><span class="info-v">{{ store.summary.nutWidth.toFixed(1) }}mm</span></div>
        <div class="info-row"><span class="info-k">Radius</span><span class="info-v">{{ store.summary.r1 }}"{{ store.summary.radType === 'compound' ? `→${store.summary.r2}"` : '' }}</span></div>
        <div class="info-row"><span class="info-k">Crown nut</span><span class="info-v">{{ store.summary.crownNut }}mm</span></div>
        <div class="info-row"><span class="info-k">Crown 12th</span><span class="info-v">{{ store.summary.crown12 }}mm</span></div>
        <div class="info-row"><span class="info-k">Back @1st</span><span class="info-v">{{ store.summary.backDepth1 }}mm</span></div>
        <div class="info-row"><span class="info-k">Back @12th</span><span class="info-v">{{ store.summary.backDepth12 }}mm</span></div>
        <div class="info-row">
          <span class="info-k">Thin point</span>
          <span class="info-v" :class="{ warn: parseFloat(store.summary.thinPoint) < 12 }">{{ store.summary.thinPoint }}mm</span>
        </div>
        <div class="info-row">
          <span class="info-k">All gates</span>
          <span class="info-v" :class="store.summary.allGatesPass ? 'ok' : 'warn'">
            {{ store.summary.allGatesPass ? '✓ pass' : '! warn/fail' }}
          </span>
        </div>
      </div>

      <div class="sec" style="border-bottom:none;margin-top:auto;padding-top:14px">
        <button class="sbtn go" style="width:100%;padding:7px 0" @click="exportAll">
          ↓ Export neck spec JSON
        </button>
      </div>
    </aside>

  </div>
</template>

<style scoped>
.neck-layout {
  display: grid;
  grid-template-columns: 222px 1fr 192px;
  height: 100%;
}
.neck-left {
  background: var(--w1);
  border-right: 1px solid var(--w3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.neck-right {
  background: var(--w1);
  border-left: 1px solid var(--w3);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.neck-canvas { overflow: hidden; background: var(--w0); }

/* Sub-tabs */
.sub-tabs {
  display: flex;
  border-bottom: 1px solid var(--w3);
  flex-shrink: 0;
}
.sub-tab {
  flex: 1;
  padding: 7px 2px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-family: var(--mono);
  font-size: 8px;
  letter-spacing: .4px;
  text-transform: uppercase;
  color: var(--dim);
  cursor: pointer;
  transition: all .12s;
}
.sub-tab:hover { color: var(--v1); }
.sub-tab.on { color: var(--br2); border-bottom-color: var(--br); }

.panel-scroll { flex: 1; overflow-y: auto; }

/* Shared info */
.info-row { display:flex; justify-content:space-between; margin-bottom:3px; }
.info-k   { font-size:9px; color:var(--dim); }
.info-v   { font-size:9px; color:var(--v1); }
.info-v.warn { color:var(--amber); }
.info-v.ok   { color:var(--green2); }
</style>
