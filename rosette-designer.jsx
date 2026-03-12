import { useState, useEffect, useRef } from "react";

const UI = {
  bg:"#0b0806", panel:"#0f0c08", panel2:"#130f09", border:"#2e2010", border2:"#1e1508",
  gold:"#e8c87a", amber:"#c9a96e", dim:"#7a5c2e", dimmer:"#4a3010",
  dimmest:"#2a1e0a", text:"#c9a96e", highlight:"#1a1208",
};

// ─────────────────────────────────────────────────────────────────
// PATTERN TYPES
// ─────────────────────────────────────────────────────────────────
const TYPES = ["solid","brick","wave","rope","scroll","custom"];
const TYPE_LABELS = {
  solid:"Solid", brick:"Brick Frieze", wave:"Wave",
  rope:"Rope Twist", scroll:"Scroll", custom:"Custom Grid",
};

// ─────────────────────────────────────────────────────────────────
// PATTERN GENERATORS  →  grid[row][col] = color index 0..3
// ─────────────────────────────────────────────────────────────────
function archY(lx, segLen, A, skew) {
  const px = skew * segLen;
  if (px <= 0 || segLen <= 0) return 0;
  return lx <= px
    ? A * Math.sin((Math.PI / 2) * (lx / px))
    : A * Math.cos((Math.PI / 2) * ((lx - px) / (segLen - px)));
}

const ROPE_GRID = [
  [0,0,0,0,0,1,1],[0,0,0,0,1,1,0],[0,0,0,1,1,0,0],
  [0,0,1,1,0,0,1],[0,1,1,0,0,1,0],
];
const ROPE_MIRROR = ROPE_GRID.map(r => [...r].reverse());

function generatePattern(type, params, nCols, nRows) {
  const g = [];
  for (let r = 0; r < nRows; r++) {
    const row = [];
    for (let c = 0; c < nCols; c++) {
      let v = 0;
      if (type === "brick") {
        const { blockW=4, blockH=2 } = params;
        const bRow = Math.floor(r / blockH);
        const off = bRow % 2 === 0 ? 0 : Math.floor(blockW / 2);
        v = Math.floor((c + off) / blockW) % 2;
      } else if (type === "wave") {
        const { A=6, segLen=18, gap=2, d=4, strandW=1.8, numStrands=7,
                skew=0.72, chase=13, colorMode="tri" } = params;
        const pitch = segLen + gap;
        let hit = false, hitN = 0;
        for (let n = -2; n <= numStrands + 2; n++) {
          const off = ((n * chase) % pitch + pitch * 100) % pitch;
          const xs = ((c - off) % pitch + pitch * 100) % pitch;
          if (xs >= segLen) continue;
          if (Math.abs(r - (n * d + archY(xs, segLen, A, skew))) < strandW / 2) {
            hit = true; hitN = n; break;
          }
        }
        if (hit) {
          const idx = ((hitN % 3) + 3) % 3;
          v = colorMode==="bw" ? (((hitN%2)+2)%2===0?1:2)
            : colorMode==="mono" ? 1
            : (idx===0?1:idx===1?2:3);
        }
      } else if (type === "rope") {
        const tileW=7, tileH=5;
        const rep = Math.floor(c / tileW);
        const tile = rep % 2 === 0 ? ROPE_GRID : ROPE_MIRROR;
        const gr = Math.min(Math.floor(r * tileH / nRows), tileH - 1);
        v = tile[gr][c % tileW];
      } else if (type === "scroll") {
        const { scrollR=6, strandW=1.5 } = params;
        const sp = scrollR * 2 + 3;
        const midR = nRows / 2;
        const topCy = midR * 0.42, botCy = midR * 1.58;
        for (let si = -2; si <= Math.ceil(nCols / sp) + 2; si++) {
          const scx = si * sp + scrollR;
          // top C (opens down)
          const dx1=c-scx, dy1=r-topCy, dist1=Math.sqrt(dx1*dx1+dy1*dy1);
          if (dist1 > scrollR-strandW && dist1 < scrollR) {
            const ang = Math.atan2(dy1,dx1)*180/Math.PI;
            if (!(ang>-130 && ang<-50)) { v=1; break; }
          }
          // bottom C (opens up)
          const dx2=c-scx, dy2=r-botCy, dist2=Math.sqrt(dx2*dx2+dy2*dy2);
          if (dist2 > scrollR-strandW && dist2 < scrollR) {
            const ang = Math.atan2(dy2,dx2)*180/Math.PI;
            if (!(ang>50 && ang<130)) { v=1; break; }
          }
        }
      } else if (type === "custom") {
        const { grid:cg } = params;
        if (cg?.length) {
          const gh=cg.length, gw=cg[0].length;
          v = cg[Math.min(Math.floor(r*gh/nRows),gh-1)]?.[c%gw] ?? 0;
        }
      }
      row.push(v);
    }
    g.push(row);
  }
  return g;
}

// ─────────────────────────────────────────────────────────────────
// ANNULAR RENDERER
// ─────────────────────────────────────────────────────────────────
const RENDER_COLS = 512;

function renderRosette(canvas, rings, soundholeR, scale) {
  if (!canvas) return;
  const size = canvas.width;
  const ctx = canvas.getContext("2d");
  const cx = size/2, cy = size/2;
  ctx.fillStyle = "#060402"; ctx.fillRect(0,0,size,size);

  // Build radii
  let rCur = soundholeR;
  const withR = rings.map(ring => {
    const innerR = rCur;
    rCur += ring.widthMm;
    return { ...ring, innerR, outerR: rCur };
  });

  // Pre-compute grids
  const prep = withR.map(ring => {
    const nRows = Math.max(1, Math.round(ring.widthMm / 0.5));
    return { ...ring, nRows, grid: generatePattern(ring.type, ring.params, RENDER_COLS, nRows) };
  });

  const cache = {};
  const hex2rgb = h => {
    if (cache[h]) return cache[h];
    return cache[h] = { r:parseInt(h.slice(1,3),16), g:parseInt(h.slice(3,5),16), b:parseInt(h.slice(5,7),16) };
  };

  const img = ctx.createImageData(size,size);
  const d = img.data;

  for (let py=0; py<size; py++) {
    for (let px=0; px<size; px++) {
      const dx=(px-cx)/scale, dy=(py-cy)/scale;
      const dist = Math.sqrt(dx*dx+dy*dy);
      const ring = prep.find(p => dist>=p.innerR && dist<p.outerR);
      if (!ring) continue;
      const ang = (Math.atan2(dy,dx)+Math.PI)/(2*Math.PI);
      const col = Math.min(Math.floor(ang*RENDER_COLS), RENDER_COLS-1);
      const row = Math.min(Math.floor((dist-ring.innerR)/ring.widthMm*ring.nRows), ring.nRows-1);
      const ci = ring.grid[row]?.[col] ?? 0;
      const hex = ring.colors[Math.min(ci, ring.colors.length-1)] ?? ring.colors[0] ?? "#1a1008";
      const { r:r8, g:g8, b:b8 } = hex2rgb(hex);
      const i = (py*size+px)*4;
      d[i]=r8; d[i+1]=g8; d[i+2]=b8; d[i+3]=255;
    }
  }
  ctx.putImageData(img,0,0);

  // Soundhole
  ctx.beginPath(); ctx.arc(cx,cy,soundholeR*scale,0,Math.PI*2);
  ctx.fillStyle="#060402"; ctx.fill();
  ctx.strokeStyle="rgba(200,160,50,0.25)"; ctx.lineWidth=0.8; ctx.stroke();

  // Outer border
  ctx.beginPath(); ctx.arc(cx,cy,rCur*scale,0,Math.PI*2);
  ctx.strokeStyle="rgba(200,160,50,0.2)"; ctx.lineWidth=0.8; ctx.stroke();
}

// ─────────────────────────────────────────────────────────────────
// RING DEFAULTS
// ─────────────────────────────────────────────────────────────────
const DEFAULTS = {
  solid:  { colors:["#1a1008","#f0e8d0"], params:{} },
  brick:  { colors:["#2a1e10","#c8b88a"], params:{ blockW:4, blockH:2 } },
  wave:   { colors:["#1a1008","#f0e8d0","#8b2020","#2d6a4f"], params:{ A:6,segLen:18,gap:2,skew:0.72,chase:13,d:4,strandW:1.8,numStrands:7,colorMode:"tri" } },
  rope:   { colors:["#1a1008","#f0e8d0"], params:{} },
  scroll: { colors:["#1a1008","#e8d888"], params:{ scrollR:6, strandW:1.5 } },
  custom: { colors:["#1a1008","#f0e8d0","#8b2020","#2d6a4f"], params:{ grid:Array.from({length:6},()=>new Array(12).fill(0)) } },
};

let _uid = 0;
const uid = () => ++_uid;

const DEFAULT_STACK = [
  { id:uid(), label:"Inner binding", type:"solid", widthMm:0.8, ...DEFAULTS.solid },
  { id:uid(), label:"Inner frieze",  type:"brick", widthMm:3.5, ...DEFAULTS.brick },
  { id:uid(), label:"Inner border",  type:"solid", widthMm:0.5, colors:["#1a1008","#f0e8d0"], params:{} },
  { id:uid(), label:"Wave zone",     type:"wave",  widthMm:9.0, ...DEFAULTS.wave },
  { id:uid(), label:"Outer border",  type:"solid", widthMm:0.5, colors:["#1a1008","#f0e8d0"], params:{} },
  { id:uid(), label:"Outer frieze",  type:"brick", widthMm:2.5, ...DEFAULTS.brick },
  { id:uid(), label:"Outer binding", type:"solid", widthMm:0.8, colors:["#1a1008","#f0e8d0"], params:{} },
];

// ─────────────────────────────────────────────────────────────────
// SHARED SLIDER
// ─────────────────────────────────────────────────────────────────
function Slider({ label, val, set, min, max, step=1, unit="", note="" }) {
  return (
    <div style={{ marginBottom:"8px" }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"1px" }}>
        <span style={{ fontSize:"8px", color:UI.dimmer }}>{label}</span>
        <span style={{ fontSize:"9px", color:UI.gold }}>{typeof val==="number"&&!Number.isInteger(val)?val.toFixed(2):val}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val}
        onChange={e=>set(Number(e.target.value))} style={{ width:"100%", accentColor:"#c9a96e" }} />
      {note&&<div style={{ fontSize:"7px", color:UI.dimmest, marginTop:"1px" }}>{note}</div>}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// PARAM EDITORS
// ─────────────────────────────────────────────────────────────────
function BrickParams({ p, u }) {
  return <>
    <Slider label="Block width"  val={p.blockW??4} set={v=>u({blockW:v})} min={2} max={20} unit=" sq" note={`${((p.blockW??4)*0.5).toFixed(1)}mm`} />
    <Slider label="Block height" val={p.blockH??2} set={v=>u({blockH:v})} min={1} max={8}  unit=" sq" note={`${((p.blockH??2)*0.5).toFixed(1)}mm`} />
  </>;
}

function WaveParams({ p, u }) {
  const { A=6,segLen=18,gap=2,d=4,strandW=1.8,numStrands=7,skew=0.72,chase=13,colorMode="tri" } = p;
  const opt = Math.round(skew*segLen);
  return <>
    <Slider label="A — arch height"  val={A}          set={v=>u({A:v})}          min={0} max={16}  step={0.5} unit=" sq" note={`${(A*0.5).toFixed(1)}mm`} />
    <Slider label="segLen"           val={segLen}      set={v=>u({segLen:v})}      min={4} max={40}  unit=" sq" note={`${(segLen*0.5).toFixed(1)}mm per arch`} />
    <Slider label="gap"              val={gap}         set={v=>u({gap:v})}         min={0} max={12}  unit=" sq" />
    <Slider label="skew — peak pos"  val={skew}        set={v=>u({skew:v})}        min={0.1} max={0.95} step={0.01} note={`peak at ${(skew*100).toFixed(0)}% · swell/crash ${(skew/(1-skew)).toFixed(2)}:1`} />
    <Slider label="chase — lag/row"  val={chase}       set={v=>u({chase:v})}       min={0} max={segLen+gap} unit=" sq" note={Math.abs(chase-opt)<=1?"✓ in-phase":`optimal = ${opt}`} />
    <Slider label="d — row pitch"    val={d}           set={v=>u({d:v})}           min={2} max={12}  step={0.5} unit=" sq" />
    <Slider label="strand width"     val={strandW}     set={v=>u({strandW:v})}     min={0.5} max={5} step={0.5} unit=" sq" />
    <Slider label="N strands"        val={numStrands}  set={v=>u({numStrands:v})}  min={2} max={14} />
    <div style={{ fontSize:"8px", color:UI.dimmer, marginBottom:"4px", marginTop:"4px" }}>Color mode</div>
    <div style={{ display:"flex", gap:"4px" }}>
      {["mono","bw","tri"].map(m=>(
        <div key={m} onClick={()=>u({colorMode:m})} style={{
          padding:"2px 9px", cursor:"pointer", fontSize:"8px", borderRadius:"3px",
          border:colorMode===m?`1px solid ${UI.amber}`:`1px solid ${UI.border}`,
          background:colorMode===m?UI.highlight:"transparent",
          color:colorMode===m?UI.gold:UI.dim,
        }}>{m}</div>
      ))}
    </div>
  </>;
}

function ScrollParams({ p, u }) {
  return <>
    <Slider label="Scroll radius" val={p.scrollR??6}  set={v=>u({scrollR:v})} min={2} max={14} step={0.5} unit=" sq" note={`${((p.scrollR??6)*0.5).toFixed(1)}mm`} />
    <Slider label="Strand width"  val={p.strandW??1.5} set={v=>u({strandW:v})} min={0.5} max={4} step={0.5} unit=" sq" />
  </>;
}

function CustomGrid({ p, u, nColors }) {
  const grid = p.grid ?? Array.from({length:6},()=>new Array(12).fill(0));
  const [paint, setPaint] = useState(1);
  const COLOR_FILLS = ["#1a1008","#f0e8d0","#8b2020","#2d6a4f"];

  return (
    <div>
      <div style={{ display:"flex", gap:"4px", marginBottom:"8px", flexWrap:"wrap", alignItems:"center" }}>
        <span style={{ fontSize:"8px", color:UI.dimmer }}>Paint:</span>
        {Array.from({length:nColors},(_,i)=>(
          <div key={i} onClick={()=>setPaint(i)} style={{
            width:"18px", height:"18px", borderRadius:"2px", cursor:"pointer",
            background:COLOR_FILLS[i]??"#888",
            border:paint===i?`2px solid ${UI.gold}`:`1px solid ${UI.border}`,
          }}/>
        ))}
        <div onClick={()=>u({grid:Array.from({length:grid.length},()=>new Array(grid[0].length).fill(0))})}
          style={{ padding:"2px 7px", fontSize:"7px", cursor:"pointer", border:`1px solid ${UI.border}`, borderRadius:"2px", color:UI.dim }}>clear</div>
      </div>
      <div style={{ display:"inline-block", border:`1px solid ${UI.border}`, borderRadius:"2px", overflow:"hidden", cursor:"crosshair" }}>
        {grid.map((row,r)=>(
          <div key={r} style={{ display:"flex" }}>
            {row.map((v,c)=>(
              <div key={c} onClick={()=>{
                const ng=grid.map(rr=>[...rr]); ng[r][c]=paint; u({grid:ng});
              }} style={{
                width:"11px", height:"11px",
                background:COLOR_FILLS[v]??"#888",
                border:"0.5px solid rgba(200,160,50,0.08)",
              }}/>
            ))}
          </div>
        ))}
      </div>
      <div style={{ fontSize:"7px", color:UI.dimmest, marginTop:"4px" }}>{grid[0].length}×{grid.length} grid · click cells to paint</div>
      <div style={{ marginTop:"6px", display:"flex", gap:"3px", flexWrap:"wrap" }}>
        {[[8,4],[12,6],[16,8],[24,10]].map(([w,h])=>(
          <div key={`${w}x${h}`} onClick={()=>u({ grid:Array.from({length:h},(_,rr)=>Array.from({length:w},(_,cc)=>grid[rr]?.[cc]??0)) })}
            style={{ padding:"2px 6px", fontSize:"7px", cursor:"pointer", border:`1px solid ${UI.border}`, borderRadius:"2px", color:UI.dim }}>
            {w}×{h}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// RING EDITOR PANEL
// ─────────────────────────────────────────────────────────────────
function RingEditor({ ring, update, updateParams }) {
  const { id, type, widthMm, colors, params, label } = ring;
  const nColors = { solid:1, brick:2, rope:2, wave:4, scroll:2, custom:4 }[type] ?? 2;
  const COLOR_NAMES = ["Background","Veneer A","Veneer B","Veneer C"];

  const setColor = (idx, val) => {
    const nc = [...colors]; nc[idx]=val; update(id,{colors:nc});
  };

  return (
    <div>
      <div style={{ fontSize:"8px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>RING EDITOR</div>

      {/* Label */}
      <div style={{ marginBottom:"10px" }}>
        <div style={{ fontSize:"8px", color:UI.dimmer, marginBottom:"3px", letterSpacing:"1px" }}>LABEL</div>
        <input value={label} onChange={e=>update(id,{label:e.target.value})}
          style={{ width:"100%", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px",
            padding:"5px 8px", color:UI.gold, fontSize:"10px", fontFamily:"'Courier New',monospace", boxSizing:"border-box" }}/>
      </div>

      {/* Type */}
      <div style={{ marginBottom:"10px" }}>
        <div style={{ fontSize:"8px", color:UI.dimmer, marginBottom:"4px", letterSpacing:"1px" }}>PATTERN TYPE</div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:"3px" }}>
          {TYPES.map(t=>(
            <div key={t} onClick={()=>{ update(id,{type:t,...DEFAULTS[t]}); }} style={{
              padding:"3px 8px", cursor:"pointer", fontSize:"8px", borderRadius:"3px",
              border:type===t?`1px solid ${UI.amber}`:`1px solid ${UI.border}`,
              background:type===t?UI.highlight:"transparent",
              color:type===t?UI.gold:UI.dim,
            }}>{TYPE_LABELS[t]}</div>
          ))}
        </div>
      </div>

      {/* Width */}
      <div style={{ marginBottom:"12px", padding:"8px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
        <Slider label="RING WIDTH" val={widthMm} set={v=>update(id,{widthMm:v})} min={0.3} max={15} step={0.1} unit="mm" />
        <div style={{ fontSize:"7px", color:UI.dimmest }}>{Math.round(widthMm/0.5)} cells @ 0.5mm/sq</div>
      </div>

      {/* Colors */}
      <div style={{ marginBottom:"12px", padding:"8px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
        <div style={{ fontSize:"8px", letterSpacing:"2px", color:UI.dim, marginBottom:"8px" }}>VENEER COLORS</div>
        {Array.from({length:nColors},(_,idx)=>(
          <div key={idx} style={{ display:"flex", alignItems:"center", gap:"7px", marginBottom:"6px" }}>
            <input type="color" value={colors[idx]??"#1a1008"} onChange={e=>setColor(idx,e.target.value)}
              style={{ width:"26px", height:"22px", border:`1px solid ${UI.border}`, borderRadius:"2px", cursor:"pointer", padding:"1px" }}/>
            <span style={{ fontSize:"8px", color:UI.dim }}>{COLOR_NAMES[idx]}</span>
            <span style={{ fontSize:"8px", color:UI.dimmest, marginLeft:"auto" }}>{colors[idx]??"#1a1008"}</span>
          </div>
        ))}
      </div>

      {/* Pattern params */}
      {(type==="brick"||type==="wave"||type==="scroll"||type==="custom") && (
        <div style={{ padding:"8px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
          <div style={{ fontSize:"8px", letterSpacing:"2px", color:UI.dim, marginBottom:"8px" }}>
            {TYPE_LABELS[type].toUpperCase()} PARAMETERS
          </div>
          {type==="brick"  && <BrickParams  p={params} u={p=>updateParams(id,p)} />}
          {type==="wave"   && <WaveParams   p={params} u={p=>updateParams(id,p)} />}
          {type==="scroll" && <ScrollParams p={params} u={p=>updateParams(id,p)} />}
          {type==="custom" && <CustomGrid   p={params} u={p=>updateParams(id,p)} nColors={nColors} />}
        </div>
      )}
      {type==="rope" && (
        <div style={{ padding:"8px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", fontSize:"8px", color:UI.dimmer, lineHeight:1.8 }}>
          7×5 diagonal staircase.<br/>
          Alternate repeats mirror horizontally for the rope helix.
          No free parameters.
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────────
export default function RosetteDesigner() {
  const [rings, setRings]       = useState(DEFAULT_STACK);
  const [selId, setSelId]       = useState(DEFAULT_STACK[3].id);
  const [soundholeR, setSR]     = useState(40.8);
  const [scale, setScale]       = useState(3.4);
  const [canvasSize, setCSz]    = useState(420);
  const canvasRef = useRef(null);
  const timer = useRef(null);

  const sel = rings.find(r=>r.id===selId);
  const totalW = rings.reduce((s,r)=>s+r.widthMm, 0);
  const outerR = soundholeR + totalW;

  const update = (id, patch) => setRings(rs=>rs.map(r=>r.id===id?{...r,...patch}:r));
  const updateParams = (id, patch) => setRings(rs=>rs.map(r=>r.id===id?{...r,params:{...r.params,...patch}}:r));

  // Debounced render
  useEffect(()=>{
    clearTimeout(timer.current);
    timer.current = setTimeout(()=>{
      renderRosette(canvasRef.current, rings, soundholeR, scale);
    }, 60);
    return ()=>clearTimeout(timer.current);
  }, [rings, soundholeR, scale, canvasSize]);

  const addRing = type => {
    const ring = { id:uid(), label:TYPE_LABELS[type], type, widthMm:2.0, ...DEFAULTS[type] };
    setRings(rs=>[...rs, ring]);
    setSelId(ring.id);
  };

  const removeRing = id => {
    setRings(rs=>rs.filter(r=>r.id!==id));
    if (selId===id) setSelId(rings[0]?.id ?? null);
  };

  const moveRing = (id, dir) => {
    setRings(rs=>{
      const i=rs.findIndex(r=>r.id===id), j=i+dir;
      if(j<0||j>=rs.length) return rs;
      const n=[...rs]; [n[i],n[j]]=[n[j],n[i]]; return n;
    });
  };

  // SVG export
  const exportSVG = () => {
    const pad=5, vb=outerR+pad;
    let rCur=soundholeR;
    const ringCircles = rings.map(ring=>{
      const iR=rCur; rCur+=ring.widthMm;
      const bg=ring.colors[0]??"#1a1008";
      return `<circle cx="0" cy="0" r="${rCur.toFixed(2)}" fill="${bg}" stroke="${bg}" stroke-width="0"/>`;
    }).join("\n");
    const guides=rings.map(ring=>{
      let rr=soundholeR; rings.forEach((r2,i2)=>{ if(r2.id===ring.id)return; if(rings.indexOf(r2)<rings.indexOf(ring)) rr+=r2.widthMm; });
      return `<circle cx="0" cy="0" r="${rr.toFixed(2)}" fill="none" stroke="rgba(200,160,50,0.3)" stroke-width="0.2" stroke-dasharray="1,1"/>`;
    }).join("\n");
    const svg=[
      `<?xml version="1.0" encoding="UTF-8"?>`,
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${-vb} ${-vb} ${2*vb} ${2*vb}" width="${2*vb}mm" height="${2*vb}mm">`,
      `<title>Rosette Design</title>`,
      `<circle cx="0" cy="0" r="${outerR.toFixed(2)}" fill="#2a1e0a"/>`,
      ringCircles,
      guides,
      `<circle cx="0" cy="0" r="${soundholeR.toFixed(2)}" fill="#060402" stroke="rgba(200,160,50,0.4)" stroke-width="0.3"/>`,
      `<text x="${soundholeR+0.5}" y="3" font-size="2.5" fill="#c8a032" font-family="monospace">⌀${(soundholeR*2).toFixed(1)}mm soundhole</text>`,
      `<text x="${outerR+0.5}" y="3" font-size="2.5" fill="#c8a032" font-family="monospace">⌀${(outerR*2).toFixed(1)}mm outer</text>`,
      `</svg>`
    ].join("\n");
    const blob=new Blob([svg],{type:"image/svg+xml"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url;
    a.download=`rosette_${rings.length}rings_${totalW.toFixed(1)}mm.svg`; a.click();
  };

  return (
    <div style={{ height:"100vh", background:UI.bg, fontFamily:"'Courier New',monospace",
      color:UI.text, display:"flex", flexDirection:"column", overflow:"hidden" }}>

      {/* ── HEADER ── */}
      <div style={{ padding:"10px 18px", borderBottom:`1px solid ${UI.border2}`,
        display:"flex", justifyContent:"space-between", alignItems:"center", flexShrink:0 }}>
        <div>
          <div style={{ fontSize:"7px", letterSpacing:"4px", color:UI.dimmer }}>THE PRODUCTION SHOP · CUSTOM INLAY MODULE</div>
          <div style={{ fontSize:"18px", fontWeight:"bold", color:UI.gold, letterSpacing:"2px" }}>Rosette Designer</div>
        </div>
        <div style={{ display:"flex", gap:"10px", alignItems:"center" }}>
          <div style={{ fontSize:"8px", color:UI.dimmer, textAlign:"right", lineHeight:1.8 }}>
            <span style={{ color:UI.gold }}>⌀{(soundholeR*2).toFixed(1)}</span>mm soundhole ·
            <span style={{ color:UI.gold }}> {totalW.toFixed(1)}</span>mm wide ·
            <span style={{ color:UI.gold }}> ⌀{(outerR*2).toFixed(1)}</span>mm outer ·
            <span style={{ color:UI.gold }}> {rings.length}</span> rings
          </div>
          <div onClick={exportSVG} style={{
            padding:"6px 14px", cursor:"pointer", fontSize:"9px", letterSpacing:"1px",
            border:`1px solid ${UI.border}`, borderRadius:"3px", color:UI.amber,
          }}>↓ SVG</div>
        </div>
      </div>

      {/* ── BODY ── */}
      <div style={{ flex:1, display:"flex", overflow:"hidden" }}>

        {/* ── LEFT: RING STACK ── */}
        <div style={{ width:"210px", flexShrink:0, borderRight:`1px solid ${UI.border2}`,
          display:"flex", flexDirection:"column", overflow:"hidden" }}>

          <div style={{ padding:"10px 12px 4px", fontSize:"7px", letterSpacing:"3px", color:UI.dim }}>
            RING STACK · inside → outside
          </div>

          {/* Stack list */}
          <div style={{ flex:1, overflowY:"auto", padding:"4px 10px" }}>
            {rings.map((ring, idx)=>(
              <div key={ring.id} onClick={()=>setSelId(ring.id)}
                style={{ marginBottom:"3px", padding:"7px 8px", cursor:"pointer", borderRadius:"3px",
                  background:selId===ring.id?UI.highlight:"transparent",
                  border:selId===ring.id?`1px solid ${UI.amber}`:`1px solid ${UI.border2}`,
                  transition:"all .08s" }}>
                <div style={{ display:"flex", alignItems:"center", gap:"5px" }}>
                  {/* Color swatches */}
                  <div style={{ display:"flex", gap:"2px", flexShrink:0 }}>
                    {ring.colors.slice(0,2).map((c,ci)=>(
                      <div key={ci} style={{ width:"9px", height:"9px", borderRadius:"1px",
                        background:c, border:`1px solid ${UI.border}` }}/>
                    ))}
                  </div>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ fontSize:"9px", color:selId===ring.id?UI.gold:UI.amber,
                      overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{ring.label}</div>
                    <div style={{ fontSize:"7px", color:UI.dimmer }}>{TYPE_LABELS[ring.type]} · {ring.widthMm.toFixed(1)}mm</div>
                  </div>
                  <div style={{ display:"flex", flexDirection:"column", gap:"0px", flexShrink:0 }}>
                    <div onClick={e=>{e.stopPropagation();moveRing(ring.id,-1);}}
                      style={{ fontSize:"8px", color:UI.dim, cursor:"pointer", lineHeight:"1.1", padding:"1px 3px", userSelect:"none" }}>▲</div>
                    <div onClick={e=>{e.stopPropagation();moveRing(ring.id, 1);}}
                      style={{ fontSize:"8px", color:UI.dim, cursor:"pointer", lineHeight:"1.1", padding:"1px 3px", userSelect:"none" }}>▼</div>
                  </div>
                  <div onClick={e=>{e.stopPropagation();removeRing(ring.id);}}
                    style={{ fontSize:"9px", color:UI.dimmer, cursor:"pointer", padding:"0 2px", flexShrink:0, userSelect:"none" }}>✕</div>
                </div>
                {/* Width bar */}
                <div style={{ marginTop:"4px", height:"2px", background:UI.dimmest, borderRadius:"1px" }}>
                  <div style={{ width:`${Math.min(ring.widthMm/totalW*100,100)}%`, height:"100%",
                    background:selId===ring.id?UI.amber:UI.dimmer, borderRadius:"1px" }}/>
                </div>
              </div>
            ))}
          </div>

          {/* Add ring */}
          <div style={{ padding:"10px 12px", borderTop:`1px solid ${UI.border2}` }}>
            <div style={{ fontSize:"7px", letterSpacing:"2px", color:UI.dimmer, marginBottom:"5px" }}>ADD RING</div>
            <div style={{ display:"flex", flexWrap:"wrap", gap:"3px" }}>
              {TYPES.map(t=>(
                <div key={t} onClick={()=>addRing(t)} style={{
                  padding:"3px 7px", cursor:"pointer", fontSize:"7px", letterSpacing:"0.5px",
                  border:`1px solid ${UI.border}`, borderRadius:"3px", color:UI.dim,
                  background:"transparent",
                }}>+ {TYPE_LABELS[t]}</div>
              ))}
            </div>
          </div>

          {/* Global controls */}
          <div style={{ padding:"10px 12px", borderTop:`1px solid ${UI.border2}` }}>
            <Slider label="Soundhole radius" val={soundholeR} set={setSR} min={30} max={65} step={0.1} unit="mm" note={`⌀${(soundholeR*2).toFixed(1)}mm`} />
            <Slider label="Preview zoom" val={scale} set={setScale} min={1.5} max={5.5} step={0.1} unit="px/mm" />
          </div>
        </div>

        {/* ── CENTER: CANVAS ── */}
        <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center",
          justifyContent:"center", background:UI.bg, padding:"16px", gap:"10px" }}>
          <canvas ref={canvasRef} width={canvasSize} height={canvasSize}
            style={{ borderRadius:"50%", border:`1px solid ${UI.border}`, display:"block",
              boxShadow:"0 0 40px rgba(200,160,50,0.04)" }}/>
          <div style={{ fontSize:"7px", color:UI.dimmest, letterSpacing:"2px" }}>
            LIVE ANNULAR PREVIEW · {RENDER_COLS}col resolution
          </div>
          {/* Ring scale legend */}
          <div style={{ display:"flex", gap:"0", height:"8px", borderRadius:"2px", overflow:"hidden",
            width:"min(300px,80%)", border:`1px solid ${UI.border2}` }}>
            {rings.map(ring=>(
              <div key={ring.id} title={`${ring.label} · ${ring.widthMm.toFixed(1)}mm`}
                onClick={()=>setSelId(ring.id)}
                style={{ flex:ring.widthMm, background:ring.colors[0]??"#1a1008",
                  outline:selId===ring.id?`2px solid ${UI.gold}`:"none",
                  cursor:"pointer", minWidth:"2px" }}/>
            ))}
          </div>
          <div style={{ fontSize:"7px", color:UI.dimmest }}>
            ← click the scale bar to select a ring
          </div>
        </div>

        {/* ── RIGHT: EDITOR ── */}
        <div style={{ width:"256px", flexShrink:0, borderLeft:`1px solid ${UI.border2}`,
          overflowY:"auto", padding:"12px" }}>
          {sel
            ? <RingEditor ring={sel} update={update} updateParams={updateParams} />
            : <div style={{ fontSize:"9px", color:UI.dimmer, padding:"20px 10px", textAlign:"center" }}>
                Click a ring in the stack to edit it
              </div>
          }
        </div>
      </div>
    </div>
  );
}
