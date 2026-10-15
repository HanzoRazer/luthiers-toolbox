<template>
  <div ref="canvasEl" class="p3-canvas" />
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import Konva from 'konva'
import { useHeadstockStore, CORPUS } from '@/stores/headstock'
import { useKonvaCanvas } from '@/composables/useKonvaCanvas'
import { buildHeadstockPath, buildTunerPositions } from '@/composables/useHeadstockPath'

const store = useHeadstockStore()
const canvasEl = ref<HTMLElement | null>(null)
const { stage, getLayer, draw } = useKonvaCanvas(canvasEl, ['bg', 'overlay', 'hs', 'guide'])

const MM = 0.215
let SC = 1.38, OX = 0, OY = 0

const CORPUS_COLORS: Record<string, string> = {
  'Les Paul':'#e8724a','Strat':'#5baae8','PRS':'#7a5ae8','Telecaster':'#5ec478','SG':'#e8c85a'
}

const p2cx = (p: number) => OX + p * SC
const p2cy = (p: number) => OY + p * SC

function computeLayout() {
  const s = stage.value; if (!s) return
  SC = Math.min((s.width() - 56) / 200, (s.height() - 56) / 320)
  OX = (s.width()  - 200 * SC) / 2
  OY = (s.height() - 320 * SC) / 2 + 6
}

function drawBg() {
  const l = getLayer('bg'); if (!l || !stage.value) return
  l.destroyChildren()
  const s = stage.value, pad = 28
  l.add(new Konva.Rect({ x:0, y:0, width:s.width(), height:s.height(), fill:'#0f0d0a' }))
  l.add(new Konva.Rect({ x:OX-pad+3, y:OY-pad+3, width:200*SC+pad*2, height:320*SC+pad*2, fill:'rgba(0,0,0,.25)', cornerRadius:3 }))
  l.add(new Konva.Rect({ x:OX-pad, y:OY-pad, width:200*SC+pad*2, height:320*SC+pad*2, fill:'#f0e8d4', cornerRadius:3 }))
  const gs = 10*SC, x0=OX-pad, x1=OX+200*SC+pad, y0=OY-pad, y1=OY+320*SC+pad
  for (let x=x0; x<x1; x+=gs) l.add(new Konva.Line({ points:[x,y0,x,y1], stroke:'#ddd4b4', strokeWidth:.35 }))
  for (let y=y0; y<y1; y+=gs) l.add(new Konva.Line({ points:[x0,y,x1,y], stroke:'#ddd4b4', strokeWidth:.35 }))
  draw('bg')
}

function drawHS() {
  const hl = getLayer('hs'), gl = getLayer('guide'), ol = getLayer('overlay')
  if (!hl || !gl || !ol) return
  hl.destroyChildren(); gl.destroyChildren(); ol.destroyChildren()

  const d = buildHeadstockPath(store.params, store.tipStyle)
  const ko = { data:d, x:OX, y:OY, scaleX:SC, scaleY:SC, listening:false }

  hl.add(new Konva.Path({ ...ko, fill:'rgba(0,0,0,.2)', offsetX:-3, offsetY:3 }))
  hl.add(new Konva.Path({ ...ko, fill:'#7a3d1a' }))
  for (let i=0; i<8; i++) {
    const yo = OY+(28+i*34)*SC
    hl.add(new Konva.Line({ points:[OX+18*SC,yo,OX+182*SC,yo], stroke:'#fff', strokeWidth:.3, opacity:.05, listening:false }))
  }
  hl.add(new Konva.Path({ ...ko, fill:'none', stroke:'#4a2010', strokeWidth:2 }))

  // Tuner positions
  buildTunerPositions(store.params, store.tunerPat).forEach(t => {
    const tx = p2cx(t.x), ty = p2cy(t.y)
    hl.add(new Konva.Circle({ x:tx, y:ty, radius:6.5, fill:'#120c06', stroke:'#3a1c08', strokeWidth:.8, listening:false }))
    hl.add(new Konva.Circle({ x:tx, y:ty, radius:3,   fill:'#d4b060', listening:false }))
  })

  // Guides
  const ny  = p2cy(298)
  const cx  = p2cx(100)
  const nw  = store.params.nutWidth * SC / 2
  const tipY = p2cy(298 - store.params.length)

  gl.add(new Konva.Line({ points:[cx,OY-22,cx,OY+320*SC+14], stroke:'#5b8fa8', strokeWidth:.8, dash:[5,4], opacity:.65 }))
  gl.add(new Konva.Line({ points:[cx-nw,ny,cx+nw,ny], stroke:'#b8962e', strokeWidth:2.2, strokeLinecap:'round' }))
  gl.add(new Konva.Text({ x:cx, y:ny+12, text:`${(store.params.nutWidth*MM).toFixed(1)} mm`, fill:'#b8962e', fontSize:7.5, fontFamily:'Courier New', align:'center', width:50, offsetX:25, opacity:.8 }))
  gl.add(new Konva.Line({ points:[OX-22,ny,OX-22,tipY], stroke:'#8a7448', strokeWidth:.6, opacity:.5 }))
  gl.add(new Konva.Line({ points:[OX-26,ny,OX-18,ny], stroke:'#8a7448', strokeWidth:.5, opacity:.5 }))
  gl.add(new Konva.Line({ points:[OX-26,tipY,OX-18,tipY], stroke:'#8a7448', strokeWidth:.5, opacity:.5 }))
  gl.add(new Konva.Text({ x:OX-40, y:(ny+tipY)/2-5, text:`${(store.params.length*MM).toFixed(0)}mm`, fill:'#8a7448', fontSize:7, fontFamily:'Courier New', rotation:-90, opacity:.6 }))

  // Corpus overlay
  if (store.showOverlay) {
    Object.entries(CORPUS).forEach(([name, cp]) => {
      ol.add(new Konva.Path({ data:buildHeadstockPath(cp, 0), x:OX, y:OY, scaleX:SC, scaleY:SC, fill:'none', stroke:CORPUS_COLORS[name]||'#888', strokeWidth:.8, opacity:.2, dash:[4,3] }))
    })
  }

  draw('hs'); draw('guide'); draw('overlay')
}

function exportSVG(): string {
  const d = buildHeadstockPath(store.params, store.tipStyle)
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 320">\n  <!-- Production Shop Parametric · ${new Date().toLocaleDateString()} -->\n  <path d="${d}" fill="#7a3d1a" stroke="#4a2010" stroke-width="1.5"/>\n</svg>`
}

defineExpose({ exportSVG })

// Watch everything that can change the canvas
watch(
  () => [store.params, store.tipStyle, store.tunerPat, store.showOverlay],
  () => drawHS(),
  { deep: true }
)

onMounted(() => {
  computeLayout()
  drawBg()
  drawHS()
})
</script>

<style scoped>
.p3-canvas { width: 100%; height: 100%; }
</style>
