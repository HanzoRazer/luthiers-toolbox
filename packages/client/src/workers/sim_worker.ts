/**
 * SimWorker - OffscreenCanvas Worker for G-code Rendering (Patch I1.3)
 * 
 * Runs in a Web Worker thread to avoid blocking the main UI during heavy rendering.
 * Supports the same arc interpolation as SimLab (G2/G3 with IJK format).
 * 
 * Performance Benefits:
 * - Renders 10,000+ moves without UI lag
 * - Main thread remains responsive
 * - Uses OffscreenCanvas API (Chrome 69+, Firefox 105+)
 * 
 * Messages:
 * - init: Setup canvas context and dimensions
 * - frame: Render current frame at tCursor time
 */

type Move = { code:string, x?:number, y?:number, z?:number, i?:number, j?:number, t:number }

let ctx: OffscreenCanvasRenderingContext2D | null = null
let W=0, H=0, mm=1

function grid(){
  if (!ctx) return
  
  ctx.strokeStyle = '#f1f5f9'
  
  for (let x=0;x<W;x+=50){ 
    ctx.beginPath()
    ctx.moveTo(x,0)
    ctx.lineTo(x,H)
    ctx.stroke() 
  }
  
  for (let y=0;y<H;y+=50){ 
    ctx.beginPath()
    ctx.moveTo(0,y)
    ctx.lineTo(W,y)
    ctx.stroke() 
  }
}

function lerp(a:number,b:number,t:number){ 
  return a+(b-a)*t 
}

function drawMove(last:any, m:Move, frac:number){
  if (!ctx) return
  
  const code = m.code || 'G1'
  ctx.lineWidth = 2
  ctx.strokeStyle = (code==='G0') ? '#ef4444' : '#0ea5e9'
  
  // Arc moves (G2/G3)
  if (m.i!=null && m.j!=null && m.x!=null && m.y!=null){
    const cx = last.x + (m.i||0)
    const cy = last.y + (m.j||0)
    const sx = last.x, sy = last.y
    const ex = m.x, ey = m.y
    const r = Math.hypot(sx-cx, sy-cy)
    const segs = Math.max(8, Math.floor(64*frac))
    
    let px = sx, py = sy
    
    for (let k=1;k<=segs;k++){
      const tt = k/segs
      const a0 = Math.atan2(sy-cy, sx-cx)
      const a1 = Math.atan2(ey-cy, ex-cx)
      let da = (a1 - a0)
      
      // Sweep direction
      if (code==='G2'){ // CW
        while (da>0) da-=Math.PI*2 
      } else { // G3 CCW
        while (da<0) da+=Math.PI*2 
      }
      
      const ang = a0 + da*tt*frac
      const x = cx + r*Math.cos(ang)
      const y = cy + r*Math.sin(ang)
      
      ctx.beginPath()
      ctx.moveTo(px*mm, py*mm)
      ctx.lineTo(x*mm, y*mm)
      ctx.stroke()
      
      px=x; py=y
    }
  } else {
    // Linear moves (G0/G1)
    const x1 = last.x, y1 = last.y
    const x2 = (m.x ?? x1), y2 = (m.y ?? y1)
    const x = lerp(x1, x2, frac)
    const y = lerp(y1, y2, frac)
    
    ctx.beginPath()
    ctx.moveTo(x1*mm, y1*mm)
    ctx.lineTo(x*mm, y*mm)
    ctx.stroke()
  }
}

self.onmessage = (e:MessageEvent)=>{
  const data = e.data
  
  if (data.type === 'init'){
    // Initialize OffscreenCanvas context
    const { canvas, width, height } = data
    
    if (canvas){
      ctx = (canvas as OffscreenCanvas).getContext('2d') as OffscreenCanvasRenderingContext2D
      W = width
      H = height
      mm = 1
    }
  } else if (data.type === 'frame'){
    // Render frame at tCursor time
    if (!ctx) return
    
    const { moves, tCursor } = data
    
    ctx.clearRect(0,0,W,H)
    grid()
    
    let t = 0
    let last = {x:0,y:0,z:5,code:'G0'}
    
    for (const m of moves as Move[]){
      if (t + m.t < tCursor){ 
        // Fully completed move
        drawMove(last, m, 1)
        last={
          x:m.x??last.x,
          y:m.y??last.y,
          z:m.z??last.z,
          code:m.code
        }
        t+=m.t 
      } else { 
        // Partially completed move (interpolate)
        const rem = Math.max(0, tCursor - t) / Math.max(1e-9, m.t)
        drawMove(last, m, Math.min(1, rem))
        break 
      }
    }
  }
}
