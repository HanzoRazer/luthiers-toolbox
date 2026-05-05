/**
 * useDxfImport
 *
 * Reactive composable wrapping the full import pipeline:
 *   SVG / DXF (browser) → parse → computeBBox → normalize → emit paths
 *
 * SPLINE entities POST to /api/dxf/spline/evaluate (ezdxf on FastAPI).
 * Falls back to Catmull-Rom approximation if server is unreachable.
 */

import { ref, computed } from 'vue'
import type { ImportedPath, BBox, NormalizeOptions, FitMode, FlipYMode } from '@/types/headstock'

const API_BASE = (import.meta.env.VITE_API_BASE ?? '') + '/api/dxf'

const PATH_COLORS = [
  '#8a4a2a','#3a6a8a','#4a8a5a','#7a5a2a',
  '#5a3a7a','#8a6a2a','#6a4a8a','#3a8a6a',
]

function svgElToPath(el: Element): string | null {
  const tag = el.tagName.toLowerCase()
  switch (tag) {
    case 'path': return el.getAttribute('d')
    case 'rect': {
      const x=+(el.getAttribute('x')||0), y=+(el.getAttribute('y')||0)
      const w=+(el.getAttribute('width')||0), h=+(el.getAttribute('height')||0)
      return `M${x},${y}H${x+w}V${y+h}H${x}Z`
    }
    case 'circle': {
      const cx=+(el.getAttribute('cx')||0), cy=+(el.getAttribute('cy')||0), r=+(el.getAttribute('r')||0)
      return `M${cx-r},${cy}A${r},${r},0,1,0,${cx+r},${cy}A${r},${r},0,1,0,${cx-r},${cy}Z`
    }
    case 'ellipse': {
      const cx=+(el.getAttribute('cx')||0), cy=+(el.getAttribute('cy')||0)
      const rx=+(el.getAttribute('rx')||0), ry=+(el.getAttribute('ry')||0)
      return `M${cx-rx},${cy}A${rx},${ry},0,1,0,${cx+rx},${cy}A${rx},${ry},0,1,0,${cx-rx},${cy}Z`
    }
    case 'polyline': case 'polygon': {
      const pts=(el.getAttribute('points')||'').trim().split(/[\s,]+/)
      if(pts.length<4) return null
      let d=`M${pts[0]},${pts[1]}`
      for(let i=2;i<pts.length-1;i+=2) d+=`L${pts[i]},${pts[i+1]}`
      if(tag==='polygon') d+='Z'
      return d
    }
    case 'line':
      return `M${el.getAttribute('x1')||0},${el.getAttribute('y1')||0}L${el.getAttribute('x2')||0},${el.getAttribute('y2')||0}`
    default: return null
  }
}

function lwpolyToPoints(verts: {x:number;y:number;bulge?:number}[]): [number,number][] {
  const pts: [number,number][] = []
  for(let i=0;i<verts.length;i++){
    const v=verts[i]; pts.push([v.x,v.y])
    const bulge=v.bulge??0
    if(Math.abs(bulge)>1e-6&&i<verts.length-1){
      const nv=verts[i+1], dx=nv.x-v.x, dy=nv.y-v.y, d=Math.sqrt(dx*dx+dy*dy)
      if(d<1e-10) continue
      const r=d*(1+bulge*bulge)/(4*Math.abs(bulge))
      const mx=(v.x+nv.x)/2, my=(v.y+nv.y)/2
      const px=-dy/d, py=dx/d
      const dc=Math.sqrt(Math.max(r*r-(d/2)**2,0))
      const sign=bulge>0?1:-1
      const acx=mx+sign*dc*px, acy=my+sign*dc*py
      let a1=Math.atan2(v.y-acy,v.x-acx), a2=Math.atan2(nv.y-acy,nv.x-acx)
      if(bulge>0&&a2<a1) a2+=2*Math.PI
      if(bulge<0&&a2>a1) a2-=2*Math.PI
      const steps=Math.max(8,Math.round(Math.abs(a2-a1)/(2*Math.PI)*48))
      for(let j=1;j<=steps;j++){const a=a1+(a2-a1)*j/steps;pts.push([acx+r*Math.cos(a),acy+r*Math.sin(a)])}
    }
  }
  return pts
}

function ptsToPath(pts:[number,number][],closed=false): string {
  if(!pts.length) return ''
  let d=`M${pts[0][0].toFixed(3)},${pts[0][1].toFixed(3)}`
  for(let i=1;i<pts.length;i++) d+=`L${pts[i][0].toFixed(3)},${pts[i][1].toFixed(3)}`
  if(closed) d+='Z'
  return d
}

function arcToPath(cx:number,cy:number,r:number,startDeg:number,endDeg:number,samples=48): string {
  let s=startDeg*Math.PI/180, e=endDeg*Math.PI/180
  if(e<s) e+=2*Math.PI
  const pts:[number,number][]=[]
  for(let i=0;i<=samples;i++){const a=s+(e-s)*i/samples;pts.push([cx+r*Math.cos(a),cy+r*Math.sin(a)])}
  return ptsToPath(pts)
}

function splineFallback(ent: any): string {
  const pts: any[] = ent.controlPoints||ent.fitPoints||[]
  if(pts.length<2) return ''
  let d=`M${pts[0].x.toFixed(3)},${pts[0].y.toFixed(3)}`
  for(let i=1;i<pts.length-1;i++){
    const cp=pts[i],next=pts[i+1]||pts[i]
    d+=`Q${cp.x.toFixed(3)},${cp.y.toFixed(3)},${((cp.x+next.x)/2).toFixed(3)},${((cp.y+next.y)/2).toFixed(3)}`
  }
  return d+`L${pts[pts.length-1].x.toFixed(3)},${pts[pts.length-1].y.toFixed(3)}`
}

async function evaluateSplineServer(ent: any, samples=128): Promise<string> {
  try {
    const res=await fetch(`${API_BASE}/spline/evaluate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({control_points:(ent.controlPoints||[]).map((p:any)=>({x:p.x,y:p.y,z:p.z??0})),knot_values:ent.knotValues??null,degree:ent.degree??3,fit_points:(ent.fitPoints||[]).map((p:any)=>({x:p.x,y:p.y})),closed:ent.closed??false,samples})})
    if(!res.ok) throw new Error(`${res.status}`)
    return ((await res.json()) as any).d as string
  } catch { return splineFallback(ent) }
}

function computeBBox(paths: ImportedPath[]): BBox|null {
  const sv=document.createElementNS('http://www.w3.org/2000/svg','svg')
  sv.setAttribute('viewBox','0 0 100000 100000')
  sv.style.cssText='position:fixed;top:-9999px;visibility:hidden;pointer-events:none;width:100000px;height:100000px'
  const g=document.createElementNS('http://www.w3.org/2000/svg','g')
  paths.filter(p=>p.visible&&p.d).forEach(p=>{const e=document.createElementNS('http://www.w3.org/2000/svg','path');e.setAttribute('d',p.d);g.appendChild(e)})
  sv.appendChild(g);document.body.appendChild(sv)
  try{const bb=g.getBBox();document.body.removeChild(sv);if(!bb||bb.width===0) return null;return{minX:bb.x,minY:bb.y,maxX:bb.x+bb.width,maxY:bb.y+bb.height,w:bb.width,h:bb.height}}
  catch{document.body.removeChild(sv);return null}
}

export function normalizePaths(paths:ImportedPath[],bbox:BBox,opts:NormalizeOptions,tw=200,th=320): ImportedPath[] {
  const {fitMode,pad,flipY}=opts, aw=tw-pad*2, ah=th-pad*2
  let sx:number,sy:number
  if(fitMode==='contain'){const sc=Math.min(aw/bbox.w,ah/bbox.h);sx=sy=sc}
  else if(fitMode==='width'){sx=sy=aw/bbox.w}
  else if(fitMode==='height'){sx=sy=ah/bbox.h}
  else{sx=aw/bbox.w;sy=ah/bbox.h}
  const scaledW=bbox.w*sx, scaledH=bbox.h*sy
  const offX=pad+(aw-scaledW)/2, offY=pad+(ah-scaledH)/2
  const flipStr=flipY?`scale(1,-1) translate(0,${-(bbox.minY*2+bbox.h)})`:''
  const transform=`translate(${offX},${offY}) scale(${sx},${sy}) ${flipStr} translate(${-bbox.minX},${-bbox.minY})`
  const svgEl=document.createElementNS('http://www.w3.org/2000/svg','svg')
  svgEl.setAttribute('viewBox',`0 0 ${tw} ${th}`)
  svgEl.style.cssText='position:fixed;top:-9999px;visibility:hidden;pointer-events:none;width:20000px;height:32000px'
  const gEl=document.createElementNS('http://www.w3.org/2000/svg','g')
  gEl.setAttribute('transform',transform)
  const visible=paths.filter(p=>p.visible&&p.d)
  const els: {p:ImportedPath;e:SVGPathElement}[]=[]
  visible.forEach(p=>{const e=document.createElementNS('http://www.w3.org/2000/svg','path') as SVGPathElement;e.setAttribute('d',p.d);gEl.appendChild(e);els.push({p,e})})
  svgEl.appendChild(gEl);document.body.appendChild(svgEl)
  const result=els.map(({p,e})=>{
    try{const len=e.getTotalLength(),samp=Math.min(Math.ceil(len/3)+4,512);let d='';for(let i=0;i<=samp;i++){const pt=e.getPointAtLength(i/samp*len);d+=(i===0?'M':'L')+pt.x.toFixed(2)+','+pt.y.toFixed(2)}return{...p,id:'n'+p.id,d:d+'Z'}}
    catch{return{...p,id:'n'+p.id}}
  })
  document.body.removeChild(svgEl)
  return result
}

export type PipelineStage='idle'|'load'|'parse'|'normalize'|'ready'

export function useDxfImport() {
  const rawPaths  = ref<ImportedPath[]>([])
  const normPaths = ref<ImportedPath[]>([])
  const rawBBox   = ref<BBox|null>(null)
  const fileType  = ref<'svg'|'dxf'|null>(null)
  const fileName  = ref('')
  const fileSize  = ref(0)
  const units     = ref('—')
  const pipeStage = ref<PipelineStage>('idle')
  const error     = ref<string|null>(null)

  const fitMode   = ref<FitMode>('contain')
  const pad       = ref(8)
  const flipY     = ref<FlipYMode>('auto')

  const normOpts = computed<NormalizeOptions>(()=>({
    fitMode:fitMode.value, alignH:'center', alignV:'center', pad:pad.value,
    flipY: flipY.value==='yes'||(flipY.value==='auto'&&fileType.value==='dxf'),
  }))

  function parseSVGText(text:string): ImportedPath[] {
    const doc=new DOMParser().parseFromString(text,'image/svg+xml')
    if(doc.querySelector('parsererror')) throw new Error('SVG parse error')
    const els=doc.querySelectorAll('path,rect,circle,ellipse,polyline,polygon,line')
    const results:ImportedPath[]=[]
    els.forEach((el,i)=>{
      const d=svgElToPath(el); if(!d) return
      results.push({id:`p${i}`,d,label:`${el.tagName.toLowerCase()} ${i+1}`,color:PATH_COLORS[i%PATH_COLORS.length],visible:true,type:el.tagName.toLowerCase()})
    })
    const root=doc.documentElement, w=root.getAttribute('width')??''
    const um=w.match(/[a-z]+/i); units.value=um?um[0]:'px'
    return results
  }

  async function parseDXFText(text:string): Promise<ImportedPath[]> {
    const DxfParser=(window as any).DxfParser
    if(!DxfParser) throw new Error('DxfParser not loaded')
    const dxf=new DxfParser().parseSync(text)
    const entities:any[]=dxf.entities??[]
    const uMap:Record<number,string>={0:'unitless',1:'in',2:'ft',4:'mm',5:'cm',6:'m'}
    units.value=uMap[dxf.header?.$INSUNITS??0]??'?'
    const results:ImportedPath[]=[]
    const splineJobs:{ent:any;idx:number}[]=[]
    for(const ent of entities){
      const type:string=ent.type; let d:string|null=null
      if(type==='SPLINE'){splineJobs.push({ent,idx:results.length});results.push({id:`sp${results.length}`,d:'',label:`SPLINE ${results.length+1}`,color:PATH_COLORS[results.length%PATH_COLORS.length],visible:true,type:'SPLINE',layer:ent.layer??'0'});continue}
      try{
        if(type==='LINE') d=`M${ent.start.x},${ent.start.y}L${ent.end.x},${ent.end.y}`
        else if(type==='LWPOLYLINE'||type==='POLYLINE'){const v=(ent.vertices??[]).map((v:any)=>({x:v.x,y:v.y,bulge:v.bulge??0}));d=ptsToPath(lwpolyToPoints(v),ent.shape)}
        else if(type==='CIRCLE'){const c=ent.center;d=`M${c.x-ent.radius},${c.y}A${ent.radius},${ent.radius},0,1,0,${c.x+ent.radius},${c.y}A${ent.radius},${ent.radius},0,1,0,${c.x-ent.radius},${c.y}Z`}
        else if(type==='ARC') d=arcToPath(ent.center.x,ent.center.y,ent.radius,ent.startAngle,ent.endAngle)
      }catch{}
      if(!d) continue
      const i=results.length
      results.push({id:`e${i}`,d,label:`${type} ${i+1}`,type,color:PATH_COLORS[i%PATH_COLORS.length],visible:true,layer:ent.layer??'0'})
    }
    const splineDs=await Promise.all(splineJobs.map(({ent})=>evaluateSplineServer(ent)))
    splineJobs.forEach(({idx},j)=>{if(results[idx]) results[idx].d=splineDs[j]})
    return results.filter(r=>r.d)
  }

  function applyNormalize() {
    if(!rawBBox.value||!rawPaths.value.length) return
    pipeStage.value='normalize'
    try{normPaths.value=normalizePaths(rawPaths.value,rawBBox.value,normOpts.value);pipeStage.value='ready'}
    catch(e){error.value=String(e);pipeStage.value='parse'}
  }

  async function loadFile(file:File) {
    error.value=null; fileName.value=file.name; fileSize.value=file.size
    fileType.value=file.name.toLowerCase().endsWith('.dxf')?'dxf':'svg'
    pipeStage.value='load'; rawPaths.value=[]; normPaths.value=[]; rawBBox.value=null
    try{
      const text=await file.text(); pipeStage.value='parse'
      rawPaths.value=fileType.value==='dxf'?await parseDXFText(text):parseSVGText(text)
      rawBBox.value=computeBBox(rawPaths.value)
      applyNormalize()
    }catch(e){error.value=String(e);pipeStage.value='idle'}
  }

  function togglePath(id:string) {
    const p=rawPaths.value.find(x=>x.id===id); if(!p) return
    p.visible=!p.visible; rawBBox.value=computeBBox(rawPaths.value); applyNormalize()
  }

  const combinedNormPath=computed(()=>normPaths.value.filter(p=>p.visible&&p.d).map(p=>p.d).join(' '))

  // ── Photo vectorizer path ─────────────────────────────────────────────────
  //
  // Called after the backend returns a VectorizeResponse. Injects the SVG
  // path into the same rawPaths pipeline as loadFile() so normalisation
  // and the two-canvas preview work identically for both entry points.

  const photoMeta = ref<{
    widthMm: number; heightMm: number
    widthIn: number; heightIn: number
    scaleSource: string; bgMethod: string
    perspectiveCorrected: boolean
    processingMs: number
    warnings: string[]
  } | null>(null)

  const isVectorizerAvailable = ref<boolean | null>(null)  // null = not yet checked

  async function checkVectorizerStatus(): Promise<boolean> {
    try {
      const res = await fetch('/api/vectorizer/status')
      const data = await res.json()
      isVectorizerAvailable.value = data.available ?? false
      return isVectorizerAvailable.value
    } catch {
      isVectorizerAvailable.value = false
      return false
    }
  }

  async function loadFromPhoto(file: File): Promise<void> {
    pipeStage.value = 'load'
    rawPaths.value  = []; normPaths.value = []; rawBBox.value = null
    error.value     = ''
    fileName.value  = file.name
    fileSize.value  = file.size
    fileType.value  = 'svg'   // vectorizer output is SVG paths
    photoMeta.value = null

    try {
      // Encode file as base64
      const buf = await file.arrayBuffer()
      const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)))
      const mediaType = file.type || (file.name.endsWith('.png') ? 'image/png' : 'image/jpeg')

      pipeStage.value = 'parse'

      const res = await fetch('/api/vectorizer/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_b64:           b64,
          media_type:          mediaType,
          correct_perspective: true,
          export_svg:          true,
          export_dxf:          false,
          label:               file.name.replace(/\.[^.]+$/, ''),
        }),
      })

      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(detail.detail ?? `HTTP ${res.status}`)
      }

      const data = await res.json()

      if (!data.ok) {
        const msg = data.export_block_reason || data.error || 'Vectorizer returned no usable path'
        error.value = msg
        pipeStage.value = 'idle'
        return
      }

      // Store photo metadata for UI display
      photoMeta.value = {
        widthMm:              data.body_width_mm,
        heightMm:             data.body_height_mm,
        widthIn:              data.body_width_in,
        heightIn:             data.body_height_in,
        scaleSource:          data.scale_source,
        bgMethod:             data.bg_method,
        perspectiveCorrected: data.perspective_corrected,
        processingMs:         data.processing_ms,
        warnings:             data.warnings ?? [],
      }

      // Inject the SVG compound path as a single ImportedPath
      loadFromVectorizerResult(data.svg_path_d, file.name)

    } catch (e) {
      error.value     = String(e)
      pipeStage.value = 'idle'
    }
  }

  /**
   * Inject a pre-fetched SVG path string (from vectorizer or other source)
   * directly into the import pipeline without going through file I/O.
   * Useful for server-side vectorization, clipboard paste, or drag-drop
   * of raw path strings.
   */
  function loadFromVectorizerResult(svgPathD: string, label = 'vectorized'): void {
    if (!svgPathD.trim()) {
      error.value = 'Empty path from vectorizer'
      pipeStage.value = 'idle'
      return
    }
    // Wrap as a synthetic SVG so parseSVGText can handle it
    const synthetic = `<svg xmlns="http://www.w3.org/2000/svg"><path d="${svgPathD.replace(/"/g, "'")}" /></svg>`
    rawPaths.value  = parseSVGText(synthetic)
    rawBBox.value   = computeBBox(rawPaths.value)
    // Tag paths with source metadata
    rawPaths.value.forEach((p, i) => {
      p.id    = `vec-${i}`
      p.label = label
    })
    applyNormalize()
    pipeStage.value = rawPaths.value.length > 0 ? 'ready' : 'idle'
    if (rawPaths.value.length === 0) error.value = 'Vectorizer path parsed to zero segments'
  }

  return {
    rawPaths, normPaths, rawBBox, fileType, fileName, fileSize, units,
    pipeStage, error, fitMode, pad, flipY, combinedNormPath,
    loadFile, applyNormalize, togglePath,
    // Photo vectorizer additions
    photoMeta, isVectorizerAvailable,
    checkVectorizerStatus, loadFromPhoto, loadFromVectorizerResult,
  }
}
