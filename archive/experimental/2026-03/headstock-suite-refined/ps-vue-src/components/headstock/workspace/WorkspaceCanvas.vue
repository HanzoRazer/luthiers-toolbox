<template>
  <div ref="canvasEl" class="ws-canvas" />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, inject } from 'vue'
import Konva from 'konva'
import { useHeadstockStore } from '@/stores/headstock'
import { useKonvaCanvas } from '@/composables/useKonvaCanvas'
import { HS_MODELS } from '../constants'
import type { InlayType } from '@/types/headstock'

const store = useHeadstockStore()
const toast = inject<(msg: string) => void>('toast', () => {})
const setStatusA = inject<(v: string) => void>('setStatusA', () => {})
const setStatusB = inject<(v: string) => void>('setStatusB', () => {})

const canvasEl = ref<HTMLElement | null>(null)
const { stage, getLayer, draw } = useKonvaCanvas(canvasEl, ['bg', 'hs', 'inlay', 'guide'])

const MM = 0.215
let SC = 1.42, OX = 0, OY = 0
let nI = 0

// boundary check
const bsvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
bsvg.setAttribute('viewBox', '0 0 200 320')
bsvg.style.cssText = 'position:fixed;top:-9999px;visibility:hidden;pointer-events:none;width:200px;height:320px'
const bpth = document.createElementNS('http://www.w3.org/2000/svg', 'path')
bsvg.appendChild(bpth); document.body.appendChild(bsvg)

function setBnd(d: string) { bpth.setAttribute('d', d) }
function inBnd(cx: number, cy: number) {
  if (!store.boundaryOn) return true
  try { const pt = bsvg.createSVGPoint(); pt.x = (cx-OX)/SC; pt.y = (cy-OY)/SC; return bpth.isPointInFill(pt) }
  catch { return true }
}

const p2cx = (p: number) => OX + p * SC
const p2cy = (p: number) => OY + p * SC

function computeLayout() {
  const s = stage.value
  if (!s) return
  SC = Math.min((s.width() - 56) / 200, (s.height() - 56) / 320)
  OX = (s.width()  - 200 * SC) / 2
  OY = (s.height() - 320 * SC) / 2 + 8
}

// ─── Background + grid ────────────────────────────────────────────────────────
function drawBg() {
  const l = getLayer('bg'); if (!l || !stage.value) return
  l.destroyChildren()
  const s = stage.value, pad = 30
  l.add(new Konva.Rect({ x:0, y:0, width:s.width(), height:s.height(), fill:'#0f0d0a' }))
  l.add(new Konva.Rect({ x:OX-pad+3, y:OY-pad+3, width:200*SC+pad*2, height:320*SC+pad*2, fill:'rgba(0,0,0,.25)', cornerRadius:3 }))
  l.add(new Konva.Rect({ x:OX-pad, y:OY-pad, width:200*SC+pad*2, height:320*SC+pad*2, fill:'#f0e8d4', cornerRadius:3 }))
  if (store.showGrid) {
    const gs = 10*SC, x0 = OX-pad, x1 = OX+200*SC+pad, y0 = OY-pad, y1 = OY+320*SC+pad
    for (let x=x0; x<x1; x+=gs) l.add(new Konva.Line({ points:[x,y0,x,y1], stroke:'#ddd4b4', strokeWidth:.35 }))
    for (let y=y0; y<y1; y+=gs) l.add(new Konva.Line({ points:[x0,y,x1,y], stroke:'#ddd4b4', strokeWidth:.35 }))
    const mgs = 50*SC
    for (let x=x0; x<x1+1; x+=mgs) l.add(new Konva.Line({ points:[x,y0,x,y1], stroke:'#c8bfa0', strokeWidth:.7 }))
    for (let y=y0; y<y1+1; y+=mgs) l.add(new Konva.Line({ points:[x0,y,x1,y], stroke:'#c8bfa0', strokeWidth:.7 }))
  }
  draw('bg')
}

// ─── Headstock ────────────────────────────────────────────────────────────────
function drawHS() {
  const l = getLayer('hs'), gl = getLayer('guide'); if (!l || !gl) return
  l.destroyChildren(); gl.destroyChildren()

  const hs = store.currentModel === 'Custom' && store.customShape
    ? { col:'#7a5030', gr:'#5a3018', path:store.customShape.path, cx:100, nutY:290, nw:70, tuners:[] as [number,number][] }
    : HS_MODELS[store.currentModel]
  if (!hs) return

  const ko = { data:hs.path, x:OX, y:OY, scaleX:SC, scaleY:SC, listening:false }
  l.add(new Konva.Path({ ...ko, fill:'rgba(0,0,0,.2)', offsetX:-3, offsetY:3 }))
  l.add(new Konva.Path({ ...ko, fill:hs.col }))
  for (let i=0; i<8; i++) {
    const yo = OY + (28+i*34)*SC
    l.add(new Konva.Line({ points:[OX+18*SC,yo,OX+182*SC,yo], stroke:'#fff', strokeWidth:.3, opacity:.05, listening:false }))
  }
  l.add(new Konva.Path({ ...ko, fill:'none', stroke:hs.gr, strokeWidth:2 }))
  hs.tuners.forEach(([px,py]) => {
    const tx = p2cx(px), ty = p2cy(py)
    l.add(new Konva.Circle({ x:tx, y:ty, radius:6.5, fill:'#120c06', stroke:'#3a1c08', strokeWidth:.8, listening:false }))
    l.add(new Konva.Circle({ x:tx, y:ty, radius:3,   fill:'#d4b060', listening:false }))
  })

  if (store.showCL) {
    const cx = p2cx(hs.cx)
    gl.add(new Konva.Line({ points:[cx,OY-22,cx,OY+320*SC+14], stroke:'#5b8fa8', strokeWidth:.8, dash:[5,4], opacity:.65 }))
    gl.add(new Konva.Text({ x:cx+3, y:OY-20, text:'CL', fill:'#5b8fa8', fontSize:8, fontFamily:'Courier New', opacity:.7 }))
  }
  if (store.showNut && hs.nutY) {
    const ny = p2cy(hs.nutY), cx = p2cx(hs.cx), hw = hs.nw * SC / 2
    gl.add(new Konva.Line({ points:[cx-hw,ny,cx+hw,ny], stroke:'#b8962e', strokeWidth:2, strokeLinecap:'round' }))
    gl.add(new Konva.Text({ x:cx, y:ny+13, text:`${(hs.nw*MM).toFixed(1)} mm`, fill:'#b8962e', fontSize:7.5, fontFamily:'Courier New', align:'center', width:50, offsetX:25, opacity:.8 }))
  }
  setBnd(hs.path)
  draw('hs'); draw('guide')
}

// ─── Inlay placement ──────────────────────────────────────────────────────────
defineExpose({ placeInlay })

const PIPS = ['#c8a870','#b49060','#d4b880','#a87840','#c0a060']
let snapLineNode: Konva.Line | null = null

function placeInlay(type: InlayType) {
  const il = getLayer('inlay'); if (!il) return
  const hs = store.currentModel === 'Custom' && store.customShape
    ? { cx:100, nutY:290, nw:70 }
    : HS_MODELS[store.currentModel]
  const cx = p2cx(hs?.cx ?? 100)
  const cy = p2cy((hs?.nutY ?? 290) - 55 - (store.inlays.length % 6) * 26)

  const id = `E${++nI}`
  const g = new Konva.Group({ x:cx, y:cy, draggable:true, id })
  const fill = '#e8dfc0', stroke = '#7a5a30'

  let sh: Konva.Shape
  switch (type) {
    case 'dot':     sh = new Konva.Circle({ radius:8, fill, stroke, strokeWidth:.8 }); break
    case 'diamond': sh = new Konva.RegularPolygon({ sides:4, radius:10, fill, stroke, strokeWidth:.8 }); break
    case 'block':   sh = new Konva.Rect({ width:28, height:11, offsetX:14, offsetY:5.5, fill, stroke, strokeWidth:.8, cornerRadius:2 }); break
    case 'crown':   sh = new Konva.Path({ data:'M-12,6 L-12,-2 L-7,4 L0,-8 L7,4 L12,-2 L12,6Z', fill, stroke, strokeWidth:.8 }); break
    case 'oval':    sh = new Konva.Ellipse({ radiusX:12, radiusY:7, fill, stroke, strokeWidth:.8 }); break
    case 'star':    sh = new Konva.Star({ numPoints:5, innerRadius:4.5, outerRadius:10, fill, stroke, strokeWidth:.8 }); break
    case 'hex':     sh = new Konva.RegularPolygon({ sides:6, radius:10, fill, stroke, strokeWidth:.8 }); break
    case 'text': {
      const txt = prompt('Inlay text:', 'LOGO') || 'LOGO'
      sh = new Konva.Text({ text:txt, fontSize:11, fill, fontFamily:'Georgia,serif', align:'center', width:60, offsetX:30, offsetY:7 })
      break
    }
    default: sh = new Konva.Circle({ radius:8, fill, stroke, strokeWidth:.8 })
  }

  const sel = new Konva.Rect({ x:-16, y:-16, width:32, height:32, stroke:'#b8962e', strokeWidth:.8, dash:[3,3], visible:false, listening:false })
  g.add(sh, sel)

  g.on('dragmove', () => {
    if (store.snapOn) {
      const sx = p2cx(hs?.cx ?? 100)
      if (Math.abs(g.x() - sx) < 20) {
        g.x(sx)
        if (!snapLineNode) {
          snapLineNode = new Konva.Line({ points:[sx,0,sx,stage.value?.height()||500], stroke:'#5b8fa8', strokeWidth:.7, dash:[4,4], opacity:.5 })
          getLayer('guide')?.add(snapLineNode)
        }
        snapLineNode.visible(true); draw('guide')
      } else {
        snapLineNode?.visible(false); draw('guide')
      }
    }
    syncInlayPos(id, g)
  })

  g.on('dragend', () => {
    snapLineNode?.visible(false); draw('guide')
    if (!inBnd(g.x(), g.y())) {
      g.x(p2cx(hs?.cx ?? 100)); g.y(p2cy((hs?.nutY ?? 290) - 60))
    }
    syncInlayPos(id, g)
  })

  g.on('click tap', () => emit('select', id))

  il.add(g); draw('inlay')

  store.addInlay({
    id, name:`${type} ${nI}`, type, pip: PIPS[nI % PIPS.length],
    visible:true, x: (g.x()-OX)/SC, y: (g.y()-OY)/SC,
    scaleX:1, rotation:0, fill,
  })
}

function syncInlayPos(id: string, g: Konva.Group) {
  store.updateInlay(id, { x:(g.x()-OX)/SC, y:(g.y()-OY)/SC, scaleX:g.scaleX(), rotation:g.rotation() })
  setStatusA(`x ${((g.x()-OX)/SC*MM).toFixed(1)}mm · y ${((g.y()-OY)/SC*MM).toFixed(1)}mm`)
}

// ─── Export helper ────────────────────────────────────────────────────────────
function exportSVG(): string {
  const hs = store.currentModel === 'Custom' && store.customShape
    ? { col:'#7a5030', gr:'#5a3018', path:store.customShape.path, cx:100, nutY:290, nw:70 }
    : HS_MODELS[store.currentModel]
  const il = getLayer('inlay'); if (!il) return ''
  const lines = il.getChildren()
    .filter((g): g is Konva.Group => g instanceof Konva.Group)
    .map(g => {
      const x = ((g.x()-OX)/SC).toFixed(2), y = ((g.y()-OY)/SC).toFixed(2)
      const s = g.scaleX().toFixed(3), r = g.rotation().toFixed(1)
      const ch = g.children[0] as Konva.Shape
      const col = (ch as any).fill?.() || '#e8dfc0'
      const t = `translate(${x},${y}) rotate(${r}) scale(${s})`
      if (ch instanceof Konva.Circle)           return `  <circle transform="${t}" r="${(ch as Konva.Circle).radius()}" fill="${col}" stroke="#7a5a30" stroke-width="0.4"/>`
      if (ch instanceof Konva.Rect)             return `  <rect transform="${t}" x="-14" y="-5.5" width="28" height="11" rx="2" fill="${col}" stroke="#7a5a30" stroke-width="0.4"/>`
      if (ch instanceof Konva.Path)             return `  <path transform="${t}" d="${(ch as Konva.Path).data()}" fill="${col}" stroke="#7a5a30" stroke-width="0.4"/>`
      if (ch instanceof Konva.Text)             return `  <text transform="${t}" font-size="11" font-family="Georgia,serif" fill="${col}" text-anchor="middle">${(ch as Konva.Text).text()}</text>`
      return `  <circle transform="${t}" r="10" fill="${col}" stroke="#7a5a30" stroke-width="0.4"/>`
    }).filter(Boolean).join('\n')
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 320">\n  <!-- Production Shop · ${store.currentModel} · ${new Date().toLocaleDateString()} -->\n  <path d="${hs?.path}" fill="${hs?.col||'#7a3d1a'}" stroke="${hs?.gr||'#4a2010'}" stroke-width="1.5"/>\n${lines}\n</svg>`
}

defineExpose({ exportSVG, placeInlay })

const emit = defineEmits<{ select: [id: string] }>()

// ─── Watchers ────────────────────────────────────────────────────────────────
watch(() => store.currentModel,  () => { drawHS() })
watch(() => store.customShape,   () => { drawHS() })
watch(() => store.showGrid,      () => { drawBg(); drawHS() })
watch(() => [store.showCL, store.showNut], () => { drawHS() }, { deep:true })

onMounted(() => {
  computeLayout()
  drawBg()
  drawHS()
  stage.value?.on('mousemove', () => {
    const p = stage.value?.getPointerPosition()
    if (!p) return
    setStatusA(`x ${((p.x-OX)/SC*MM).toFixed(1)}mm · y ${((p.y-OY)/SC*MM).toFixed(1)}mm`)
  })
  setStatusB(`${store.inlayCount} inlays`)
})
</script>

<style scoped>
.ws-canvas { width: 100%; height: 100%; }
</style>
