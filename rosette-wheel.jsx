import { useState, useEffect, useRef, useCallback } from "react";

// ─── WOOD MATERIAL LIBRARY ───────────────────────────────────────
const WOODS = [
  { id:"ebony",    name:"Ebony",       base:"#1a1008", grain:"#130c05", accent:"#221408", tight:true,  figure:false },
  { id:"maple",    name:"Maple",       base:"#f2e8c8", grain:"#e0d0a8", accent:"#f8f0d8", tight:true,  figure:false },
  { id:"maple_q",  name:"Quilted Maple",base:"#f0d890",grain:"#c8a840", accent:"#f8e8a0", tight:false, figure:true  },
  { id:"rosewood", name:"Rosewood",    base:"#4a1e10", grain:"#3a1408", accent:"#5a2818", tight:false, figure:false },
  { id:"spruce",   name:"Spruce",      base:"#e8d8a0", grain:"#c8b060", accent:"#f0e0b0", tight:true,  figure:false },
  { id:"cedar",    name:"Cedar",       base:"#c07040", grain:"#a05028", accent:"#d08050", tight:false, figure:false },
  { id:"mahogany", name:"Mahogany",    base:"#7a3018", grain:"#5a1e08", accent:"#8a4020", tight:false, figure:false },
  { id:"koa",      name:"Koa",         base:"#b86820", grain:"#8a4810", accent:"#d08030", tight:false, figure:true  },
  { id:"ovangkol", name:"Ovangkol",    base:"#a07830", grain:"#706020", accent:"#b88840", tight:true,  figure:true  },
  { id:"walnut",   name:"Walnut",      base:"#5c3818", grain:"#3c2008", accent:"#6c4828", tight:false, figure:false },
  { id:"mop",      name:"Mother-of-Pearl", base:"#e8f0f8", grain:"#c0d8f0", accent:"#f0f8ff", tight:false, figure:true, iridescent:true },
  { id:"abalone",  name:"Abalone",     base:"#609070", grain:"#408060", accent:"#80b090", tight:false, figure:true, iridescent:true },
  { id:"bone",     name:"Bone",        base:"#f0ead0", grain:"#d8d0a8", accent:"#f8f4e0", tight:true,  figure:false },
  { id:"none",     name:"None / Air",  base:"#080604", grain:"#060402", accent:"#0a0806", tight:false, figure:false },
];

// ─── GRAIN RENDERER ──────────────────────────────────────────────
function makeGrainPattern(ctx, wood, cellW, cellH, seed) {
  const off = document.createElement("canvas");
  off.width = cellW; off.height = cellH;
  const c = off.getContext("2d");

  // Base fill
  c.fillStyle = wood.base;
  c.fillRect(0,0,cellW,cellH);

  // Deterministic PRNG from seed
  let s = seed * 9301 + 49297;
  const rng = () => { s=(s*9301+49297)%233280; return s/233280; };

  if (wood.iridescent) {
    // Iridescent shimmer
    for (let i=0; i<8; i++) {
      const x = rng()*cellW, y = rng()*cellH;
      const grd = c.createRadialGradient(x,y,0,x,y,cellW*0.6);
      const hue = (seed*37+i*47)%360;
      grd.addColorStop(0, `hsla(${hue},60%,85%,0.4)`);
      grd.addColorStop(0.5, `hsla(${(hue+60)%360},50%,70%,0.2)`);
      grd.addColorStop(1, "transparent");
      c.fillStyle = grd; c.fillRect(0,0,cellW,cellH);
    }
  }

  if (wood.figure) {
    // Figured / wavy grain
    const lines = wood.tight ? 16 : 8;
    for (let i=0; i<lines; i++) {
      const y0 = (i/lines)*cellH + rng()*6-3;
      c.beginPath();
      c.moveTo(0, y0);
      for (let x=0; x<=cellW; x+=4) {
        const wave = Math.sin(x*0.15+rng()*2)*3 + Math.sin(x*0.08+rng())*5;
        c.lineTo(x, y0+wave);
      }
      c.strokeStyle = rng()>0.5 ? wood.grain : wood.accent;
      c.lineWidth = rng()*1.5+0.3;
      c.globalAlpha = 0.3+rng()*0.4;
      c.stroke();
    }
  } else {
    // Straight grain lines
    const lines = wood.tight ? 20 : 10;
    for (let i=0; i<lines; i++) {
      const y = (i+rng()*0.8)/lines*cellH;
      c.beginPath();
      c.moveTo(0, y);
      const drift = rng()*4-2;
      c.lineTo(cellW, y+drift);
      c.strokeStyle = rng()>0.5 ? wood.grain : wood.accent;
      c.lineWidth = rng()*1.2+0.2;
      c.globalAlpha = 0.25+rng()*0.35;
      c.stroke();
    }
  }
  c.globalAlpha = 1;

  // Pore dots for open-grain species
  if (!wood.tight && !wood.iridescent) {
    for (let i=0; i<cellW*cellH*0.012; i++) {
      c.beginPath();
      c.arc(rng()*cellW, rng()*cellH, rng()*0.7+0.2, 0, Math.PI*2);
      c.fillStyle = wood.grain;
      c.globalAlpha = 0.3+rng()*0.3;
      c.fill();
    }
    c.globalAlpha = 1;
  }

  return off;
};

// ─── MAIN COMPONENT ──────────────────────────────────────────────
const RING_NAMES = ["Inner Binding","Inner Frieze","Inner Border","Main Band","Outer Border","Outer Frieze","Outer Binding"];
const RING_WIDTHS = [0.6, 3.0, 0.5, 8.0, 0.5, 2.5, 0.6]; // mm

export default function RosetteWheel() {
  const SIZE = 540;
  const CX = SIZE/2, CY = SIZE/2;
  const SOUNDHOLE_R_MM = 40.8;
  const MM_PX = 4.8; // scale

  const totalMm = RING_WIDTHS.reduce((a,b)=>a+b,0);
  const outerMmR = SOUNDHOLE_R_MM + totalMm;

  // Build ring radius array
  const ringBounds = (() => {
    let r = SOUNDHOLE_R_MM;
    return RING_WIDTHS.map(w => { const o={inner:r,outer:r+w,widthMm:w}; r+=w; return o; });
  })();

  // State
  const [segments, setSegments] = useState(12);
  const [selWood, setSelWood] = useState("ebony");
  const [symmetry, setSymmetry] = useState("full"); // full, half, quarter, none
  const [cells, setCells] = useState(() => {
    // Default: classic Torres scheme
    const c = {};
    RING_WIDTHS.forEach((_,ri) => {
      for (let si=0; si<24; si++) {
        const defaults = ["ebony","maple","ebony","rosewood","ebony","maple","ebony"];
        c[`${ri}-${si}`] = defaults[ri] ?? "ebony";
      }
    });
    return c;
  });
  const [painting, setPainting] = useState(false);
  const [hoveredCell, setHoveredCell] = useState(null);
  const [showLabels, setShowLabels] = useState(false);

  const canvasRef = useRef(null);
  const grainCache = useRef({});

  // Get grain bitmap for a wood+size combo (cached)
  const getGrain = (woodId, ri, si) => {
    const key = `${woodId}-${ri}-${si%4}`; // reuse every 4 segs for performance
    if (!grainCache.current[key]) {
      const wood = WOODS.find(w=>w.id===woodId) ?? WOODS[0];
      grainCache.current[key] = makeGrainPattern(null, wood, 60, 30, ri*100+si);
    }
    return grainCache.current[key];
  };

  // Get symmetry-expanded set of segments to paint
  const getSymPeers = (ri, si) => {
    const peers = new Set([si]);
    if (symmetry==="full") {
      for (let i=0;i<segments;i++) peers.add(i);
    } else if (symmetry==="half") {
      peers.add(si); peers.add((si + Math.floor(segments/2)) % segments);
    } else if (symmetry==="quarter") {
      const q = Math.floor(segments/4);
      [0,q,q*2,q*3].forEach(o=>peers.add((si+o)%segments));
    }
    return [...peers];
  };

  const paintCell = useCallback((ri, si) => {
    setCells(prev => {
      const next = {...prev};
      getSymPeers(ri, si).forEach(s => { next[`${ri}-${s}`] = selWood; });
      return next;
    });
  }, [selWood, symmetry, segments]);

  // Polar hit test
  const hitTest = (mx, my) => {
    const dx = mx-CX, dy = my-CY;
    const dist = Math.sqrt(dx*dx+dy*dy)/MM_PX;
    const ang = (Math.atan2(dy,dx)+Math.PI*2.5)%(Math.PI*2); // 0=top, CW
    const ringIdx = ringBounds.findIndex(b=>dist>=b.inner&&dist<b.outer);
    if (ringIdx<0) return null;
    const segIdx = Math.floor(ang/(Math.PI*2)*segments);
    return { ri:ringIdx, si:segIdx };
  };

  // Draw
  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0,0,SIZE,SIZE);

    // Dark felt background
    const bgGrd = ctx.createRadialGradient(CX,CY,0,CX,CY,SIZE/2);
    bgGrd.addColorStop(0,"#0e0a06"); bgGrd.addColorStop(1,"#060402");
    ctx.fillStyle=bgGrd; ctx.fillRect(0,0,SIZE,SIZE);

    const angStep = (Math.PI*2)/segments;

    // Draw each cell as a filled arc sector
    ringBounds.forEach((rb, ri) => {
      const iR = rb.inner*MM_PX, oR = rb.outer*MM_PX;
      for (let si=0; si<segments; si++) {
        const a0 = si*angStep - Math.PI/2;
        const a1 = (si+1)*angStep - Math.PI/2;
        const woodId = cells[`${ri}-${si}`] ?? "ebony";
        const wood = WOODS.find(w=>w.id===woodId) ?? WOODS[0];
        const isHovered = hoveredCell?.ri===ri && hoveredCell?.si===si;

        // Clip to sector
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(CX,CY);
        ctx.arc(CX,CY,oR,a0,a1);
        ctx.arc(CX,CY,iR,a1,a0,true);
        ctx.closePath();
        ctx.clip();

        // Wood grain fill — map grain canvas into sector bounds
        const grain = getGrain(woodId, ri, si);
        const midAng = (a0+a1)/2;
        const midR = (iR+oR)/2;
        const gx = CX+Math.cos(midAng)*midR, gy = CY+Math.sin(midAng)*midR;
        const cellW = (oR-iR)*1.2+10, cellH = oR*angStep*1.2+10;
        ctx.save();
        ctx.translate(gx,gy);
        ctx.rotate(midAng+Math.PI/2);
        ctx.drawImage(grain,-cellW/2,-cellH/2,cellW,cellH);
        ctx.restore();

        // Hover highlight
        if (isHovered) {
          ctx.fillStyle="rgba(232,200,122,0.18)";
          ctx.fillRect(0,0,SIZE,SIZE);
        }

        ctx.restore();

        // Cell border
        ctx.beginPath();
        ctx.moveTo(CX,CY);
        ctx.arc(CX,CY,oR,a0,a1);
        ctx.arc(CX,CY,iR,a1,a0,true);
        ctx.closePath();
        ctx.strokeStyle = isHovered
          ? "rgba(232,200,122,0.7)"
          : "rgba(20,14,6,0.6)";
        ctx.lineWidth = isHovered ? 1.5 : 0.5;
        ctx.stroke();
      }
    });

    // Ring separation lines (amber dashes on rings)
    ringBounds.forEach((rb,ri) => {
      [rb.inner, rb.outer].forEach(r => {
        ctx.beginPath();
        ctx.arc(CX,CY,r*MM_PX,0,Math.PI*2);
        ctx.strokeStyle="rgba(200,160,50,0.18)";
        ctx.lineWidth=0.8;
        ctx.setLineDash([3,4]);
        ctx.stroke();
        ctx.setLineDash([]);
      });
    });

    // Soundhole
    ctx.beginPath();
    ctx.arc(CX,CY,SOUNDHOLE_R_MM*MM_PX,0,Math.PI*2);
    const sfGrd = ctx.createRadialGradient(CX,CY-10,2,CX,CY,SOUNDHOLE_R_MM*MM_PX);
    sfGrd.addColorStop(0,"#1a1208"); sfGrd.addColorStop(1,"#060402");
    ctx.fillStyle=sfGrd; ctx.fill();
    ctx.strokeStyle="rgba(200,160,50,0.35)"; ctx.lineWidth=1.2; ctx.stroke();

    // Labels
    if (showLabels) {
      ringBounds.forEach((rb,ri) => {
        const midR = (rb.inner+rb.outer)/2*MM_PX;
        ctx.save();
        ctx.font=`bold ${Math.max(6,rb.widthMm*MM_PX*0.38)}px 'Courier New'`;
        ctx.fillStyle="rgba(200,160,50,0.55)";
        ctx.textAlign="center";
        ctx.translate(CX, CY-midR);
        ctx.fillText(RING_NAMES[ri]??"Ring "+(ri+1), 0, 4);
        ctx.restore();
      });
    }

    // Outer glow ring
    ctx.beginPath();
    ctx.arc(CX,CY,outerMmR*MM_PX+1,0,Math.PI*2);
    ctx.strokeStyle="rgba(200,160,50,0.12)";
    ctx.lineWidth=2; ctx.stroke();

  }, [cells, hoveredCell, segments, showLabels]);

  // Interaction
  const onMove = e => {
    const r=canvasRef.current.getBoundingClientRect();
    const hit=hitTest(e.clientX-r.left, e.clientY-r.top);
    setHoveredCell(hit);
    if (painting && hit) paintCell(hit.ri, hit.si);
  };
  const onDown = e => {
    const r=canvasRef.current.getBoundingClientRect();
    const hit=hitTest(e.clientX-r.left, e.clientY-r.top);
    if (hit) { setPainting(true); paintCell(hit.ri, hit.si); }
  };
  const onUp = () => setPainting(false);

  const woodById = id => WOODS.find(w=>w.id===id)??WOODS[0];
  const selW = woodById(selWood);

  // Apply preset
  const applyPreset = name => {
    const schemes = {
      torres: ["ebony","maple","ebony","rosewood","ebony","maple","ebony"],
      celtic: ["walnut","bone","walnut","koa","walnut","bone","walnut"],
      pearl:  ["ebony","mop","ebony","abalone","ebony","mop","ebony"],
      cedar:  ["ebony","spruce","ebony","cedar","ebony","spruce","ebony"],
      blank:  ["none","none","none","none","none","none","none"],
    };
    const s = schemes[name] ?? schemes.torres;
    setCells(prev => {
      const next={};
      RING_WIDTHS.forEach((_,ri) => {
        for(let si=0;si<24;si++) next[`${ri}-${si}`]=s[ri]??"ebony";
      });
      return next;
    });
  };

  return (
    <div style={{ minHeight:"100vh", background:"#080604", fontFamily:"'Courier New',monospace",
      color:"#c9a96e", display:"flex", flexDirection:"column" }}>

      {/* HEADER */}
      <div style={{ padding:"14px 24px", borderBottom:"1px solid #1e1508",
        display:"flex", justifyContent:"space-between", alignItems:"center" }}>
        <div>
          <div style={{ fontSize:"7px", letterSpacing:"5px", color:"#3a2010" }}>
            THE PRODUCTION SHOP · CUSTOM INLAY MODULE
          </div>
          <div style={{ fontSize:"22px", fontWeight:"bold", color:"#e8c87a", letterSpacing:"2px", marginTop:"2px" }}>
            Rosette Wheel Designer
          </div>
        </div>
        <div style={{ display:"flex", gap:"8px", alignItems:"center" }}>
          <div style={{ fontSize:"8px", color:"#4a3010", textAlign:"right", lineHeight:2 }}>
            ⌀{(SOUNDHOLE_R_MM*2).toFixed(1)}mm soundhole · {totalMm.toFixed(1)}mm band · ⌀{(outerMmR*2).toFixed(1)}mm outer
          </div>
        </div>
      </div>

      <div style={{ flex:1, display:"flex", gap:"0" }}>

        {/* ── LEFT: MATERIAL PALETTE ── */}
        <div style={{ width:"168px", flexShrink:0, borderRight:"1px solid #1e1508",
          display:"flex", flexDirection:"column" }}>

          <div style={{ padding:"10px 12px 4px", fontSize:"7px", letterSpacing:"3px", color:"#4a3010" }}>
            MATERIALS
          </div>

          <div style={{ flex:1, overflowY:"auto", padding:"4px 10px" }}>
            {WOODS.map(wood => {
              const isSel = selWood===wood.id;
              return (
                <div key={wood.id} onClick={()=>setSelWood(wood.id)}
                  style={{ marginBottom:"3px", padding:"6px 8px", cursor:"pointer",
                    borderRadius:"3px", display:"flex", alignItems:"center", gap:"8px",
                    border:isSel?"1px solid #c9a96e":"1px solid #1e1508",
                    background:isSel?"#130f09":"transparent",
                    transition:"all .08s" }}>
                  {/* Swatch */}
                  <div style={{ width:"28px", height:"20px", borderRadius:"2px", flexShrink:0,
                    background:wood.base, border:"1px solid #2e2010", position:"relative", overflow:"hidden" }}>
                    {wood.figure && (
                      <div style={{ position:"absolute",inset:0,
                        background:`repeating-linear-gradient(75deg, transparent, transparent 3px, ${wood.grain}44 3px, ${wood.grain}44 4px)` }}/>
                    )}
                    {!wood.figure && (
                      <div style={{ position:"absolute",inset:0,
                        background:`repeating-linear-gradient(90deg, transparent, transparent 4px, ${wood.grain}33 4px, ${wood.grain}33 5px)` }}/>
                    )}
                  </div>
                  <div>
                    <div style={{ fontSize:"9px", color:isSel?"#e8c87a":"#7a5c2e", lineHeight:1.2 }}>{wood.name}</div>
                    <div style={{ fontSize:"7px", color:"#2e1e08", lineHeight:1 }}>
                      {wood.tight?"tight":"open"}{wood.figure?" · figured":""}{wood.iridescent?" · irid.":""}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Selected material preview */}
          <div style={{ margin:"8px 10px", padding:"10px", background:"#0f0c08",
            border:"1px solid #2e2010", borderRadius:"4px" }}>
            <div style={{ fontSize:"7px", letterSpacing:"2px", color:"#3a2010", marginBottom:"6px" }}>
              ACTIVE MATERIAL
            </div>
            <div style={{ width:"100%", height:"32px", borderRadius:"3px",
              background:selW.base, border:"1px solid #2e2010", overflow:"hidden", position:"relative", marginBottom:"6px" }}>
              <div style={{ position:"absolute",inset:0,
                background:`repeating-linear-gradient(${selW.figure?70:90}deg, transparent, transparent ${selW.tight?3:6}px, ${selW.grain}44 ${selW.tight?3:6}px, ${selW.grain}44 ${selW.tight?4:7}px)` }}/>
              {selW.iridescent && (
                <div style={{ position:"absolute",inset:0,
                  background:`linear-gradient(45deg, #e8f0f844, #c0f0e044, #f0e0d044)` }}/>
              )}
            </div>
            <div style={{ fontSize:"10px", color:"#e8c87a", fontWeight:"bold" }}>{selW.name}</div>
            <div style={{ fontSize:"7px", color:"#4a3010", marginTop:"2px" }}>{selW.base}</div>
          </div>
        </div>

        {/* ── CENTER: WHEEL ── */}
        <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center",
          justifyContent:"center", padding:"20px", gap:"12px" }}>

          <canvas ref={canvasRef} width={SIZE} height={SIZE}
            style={{ cursor:"crosshair", borderRadius:"50%",
              boxShadow:"0 0 60px rgba(200,160,50,0.06), 0 0 120px rgba(0,0,0,0.8)" }}
            onMouseMove={onMove} onMouseDown={onDown} onMouseUp={onUp} onMouseLeave={onUp}/>

          {/* Hint */}
          <div style={{ fontSize:"7px", letterSpacing:"2px", color:"#2e1e08" }}>
            CLICK OR DRAG TO PAINT · SYMMETRY APPLIES ACROSS ALL MATCHING SEGMENTS
          </div>

          {/* Ring legend strip */}
          <div style={{ display:"flex", gap:"0", height:"10px", width:"360px",
            borderRadius:"3px", overflow:"hidden", border:"1px solid #1e1508" }}>
            {ringBounds.map((rb,ri) => {
              const sampleWood = cells[`${ri}-0`] ?? "ebony";
              const w = woodById(sampleWood);
              return (
                <div key={ri} title={`${RING_NAMES[ri]} · ${rb.widthMm}mm`}
                  style={{ flex:rb.widthMm, background:w.base, minWidth:"2px",
                    borderRight:ri<ringBounds.length-1?"1px solid #1e1508":"none" }}/>
              );
            })}
          </div>
          <div style={{ fontSize:"7px", color:"#2a1e0a", letterSpacing:"1px" }}>
            ← SOUNDHOLE — RING STACK — EDGE →
          </div>
        </div>

        {/* ── RIGHT: CONTROLS ── */}
        <div style={{ width:"200px", flexShrink:0, borderLeft:"1px solid #1e1508",
          overflowY:"auto", padding:"12px" }}>

          {/* Segments */}
          <div style={{ marginBottom:"14px", padding:"10px", background:"#0f0c08",
            border:"1px solid #2e2010", borderRadius:"4px" }}>
            <div style={{ fontSize:"7px", letterSpacing:"3px", color:"#4a3010", marginBottom:"8px" }}>
              DIVISIONS
            </div>
            <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"4px" }}>
              <span style={{ fontSize:"8px", color:"#7a5c2e" }}>Segments</span>
              <span style={{ fontSize:"10px", color:"#e8c87a", fontWeight:"bold" }}>{segments}</span>
            </div>
            <input type="range" min={4} max={36} step={2} value={segments}
              onChange={e=>{ setSegments(Number(e.target.value)); setCells({}); }}
              style={{ width:"100%", accentColor:"#c9a96e", marginBottom:"4px" }}/>
            <div style={{ display:"flex", gap:"3px", flexWrap:"wrap" }}>
              {[6,8,12,16,24].map(n=>(
                <div key={n} onClick={()=>{setSegments(n);setCells({});}} style={{
                  padding:"2px 7px", cursor:"pointer", fontSize:"7px", borderRadius:"2px",
                  border:segments===n?"1px solid #c9a96e":"1px solid #2e2010",
                  background:segments===n?"#1a1208":"transparent",
                  color:segments===n?"#e8c87a":"#4a3010" }}>{n}</div>
              ))}
            </div>
          </div>

          {/* Symmetry */}
          <div style={{ marginBottom:"14px", padding:"10px", background:"#0f0c08",
            border:"1px solid #2e2010", borderRadius:"4px" }}>
            <div style={{ fontSize:"7px", letterSpacing:"3px", color:"#4a3010", marginBottom:"8px" }}>
              SYMMETRY
            </div>
            {[
              ["none","None — free paint"],
              ["quarter","Quarter (×4)"],
              ["half","Half (×2)"],
              ["full","Full ring fill"],
            ].map(([v,l])=>(
              <div key={v} onClick={()=>setSymmetry(v)} style={{
                padding:"4px 8px", marginBottom:"3px", cursor:"pointer", fontSize:"8px",
                border:symmetry===v?"1px solid #c9a96e":"1px solid #2e2010",
                borderRadius:"3px", background:symmetry===v?"#1a1208":"transparent",
                color:symmetry===v?"#e8c87a":"#4a3010" }}>{l}</div>
            ))}
          </div>

          {/* Presets */}
          <div style={{ marginBottom:"14px", padding:"10px", background:"#0f0c08",
            border:"1px solid #2e2010", borderRadius:"4px" }}>
            <div style={{ fontSize:"7px", letterSpacing:"3px", color:"#4a3010", marginBottom:"8px" }}>
              PRESETS
            </div>
            {[
              ["torres","Torres / Ramirez","#4a1e10"],
              ["celtic","Celtic — Koa","#b86820"],
              ["pearl","Pearl & Abalone","#609070"],
              ["cedar","Cedar & Spruce","#c07040"],
              ["blank","Clear All","#2a1e08"],
            ].map(([id,label,accent])=>(
              <div key={id} onClick={()=>applyPreset(id)} style={{
                padding:"5px 8px", marginBottom:"4px", cursor:"pointer", fontSize:"8px",
                border:`1px solid #2e2010`, borderRadius:"3px",
                borderLeft:`3px solid ${accent}`,
                background:"transparent", color:"#7a5c2e",
                transition:"all .08s" }}>{label}</div>
            ))}
          </div>

          {/* Options */}
          <div style={{ marginBottom:"14px", padding:"10px", background:"#0f0c08",
            border:"1px solid #2e2010", borderRadius:"4px" }}>
            <div style={{ fontSize:"7px", letterSpacing:"3px", color:"#4a3010", marginBottom:"8px" }}>
              OPTIONS
            </div>
            <div onClick={()=>setShowLabels(l=>!l)} style={{
              padding:"4px 8px", cursor:"pointer", fontSize:"8px", borderRadius:"3px",
              border:showLabels?"1px solid #c9a96e":"1px solid #2e2010",
              background:showLabels?"#1a1208":"transparent",
              color:showLabels?"#e8c87a":"#4a3010", marginBottom:"4px" }}>
              Ring labels
            </div>
            <div onClick={()=>{ grainCache.current={}; setCells(c=>({...c})); }} style={{
              padding:"4px 8px", cursor:"pointer", fontSize:"8px", borderRadius:"3px",
              border:"1px solid #2e2010", color:"#4a3010" }}>
              Reseed grain
            </div>
          </div>

          {/* BOM */}
          <div style={{ padding:"10px", background:"#0f0c08",
            border:"1px solid #2e2010", borderRadius:"4px" }}>
            <div style={{ fontSize:"7px", letterSpacing:"3px", color:"#4a3010", marginBottom:"8px" }}>
              RING SUMMARY
            </div>
            {ringBounds.map((rb,ri) => {
              const sampleId = cells[`${ri}-0`] ?? "ebony";
              const wood = woodById(sampleId);
              return (
                <div key={ri} style={{ display:"flex", gap:"6px", alignItems:"center",
                  marginBottom:"5px" }}>
                  <div style={{ width:"10px", height:"10px", borderRadius:"1px", flexShrink:0,
                    background:wood.base, border:"1px solid #2e2010" }}/>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ fontSize:"7px", color:"#7a5c2e", overflow:"hidden",
                      textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{RING_NAMES[ri]}</div>
                    <div style={{ fontSize:"6px", color:"#3a2010" }}>{rb.widthMm}mm · {wood.name}</div>
                  </div>
                </div>
              );
            })}
            <div style={{ marginTop:"8px", paddingTop:"6px", borderTop:"1px solid #1e1508",
              fontSize:"7px", color:"#3a2010" }}>
              Total band: <span style={{ color:"#e8c87a" }}>{totalMm.toFixed(1)}mm</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
