import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════════
// MATERIAL LIBRARY
// ═══════════════════════════════════════════════════════════════════
const WOODS = [
  { id:"ebony",    name:"Ebony",         base:"#1a1008", grain:"#130c05", tight:true,  figure:false },
  { id:"maple",    name:"Maple",         base:"#f2e8c8", grain:"#d8c898", tight:true,  figure:false },
  { id:"maple_q",  name:"Quilted Maple", base:"#f0d890", grain:"#c8a840", tight:false, figure:true  },
  { id:"rosewood", name:"Rosewood",      base:"#4a1e10", grain:"#3a1408", tight:false, figure:false },
  { id:"spruce",   name:"Spruce",        base:"#e8d8a0", grain:"#c0a850", tight:true,  figure:false },
  { id:"cedar",    name:"Cedar",         base:"#c07040", grain:"#903820", tight:false, figure:false },
  { id:"mahogany", name:"Mahogany",      base:"#7a3018", grain:"#5a1e08", tight:false, figure:false },
  { id:"koa",      name:"Koa",           base:"#b86820", grain:"#7a4010", tight:false, figure:true  },
  { id:"ovangkol", name:"Ovangkol",      base:"#a07830", grain:"#706020", tight:true,  figure:true  },
  { id:"walnut",   name:"Walnut",        base:"#5c3818", grain:"#3c2008", tight:false, figure:false },
  { id:"mop",      name:"Mother-of-Pearl",base:"#e8f0f8",grain:"#c0d8f0", tight:false, figure:true, iridescent:true },
  { id:"abalone",  name:"Abalone",       base:"#609070", grain:"#408060", tight:false, figure:true, iridescent:true },
  { id:"bone",     name:"Bone",          base:"#f0ead0", grain:"#d0c898", tight:true,  figure:false },
  { id:"none",     name:"Air / Open",    base:"#080604", grain:"#060402", tight:false, figure:false },
];
const woodById = id => WOODS.find(w=>w.id===id) ?? WOODS[0];

// ═══════════════════════════════════════════════════════════════════
// GRAIN CANVAS (per cell, cached)
// ═══════════════════════════════════════════════════════════════════
const grainCache = {};
function getGrain(woodId, seed) {
  const key = `${woodId}:${seed%8}`;
  if (grainCache[key]) return grainCache[key];
  const wood = woodById(woodId);
  const W=72, H=36;
  const off = document.createElement("canvas"); off.width=W; off.height=H;
  const c = off.getContext("2d");
  c.fillStyle = wood.base; c.fillRect(0,0,W,H);
  let s = seed*9301+49297;
  const rng = () => { s=(s*9301+49297)%233280; return s/233280; };
  if (wood.iridescent) {
    for (let i=0;i<6;i++){
      const grd=c.createRadialGradient(rng()*W,rng()*H,0,rng()*W,rng()*H,W*0.7);
      const h=(seed*37+i*53)%360;
      grd.addColorStop(0,`hsla(${h},55%,82%,0.45)`);
      grd.addColorStop(1,"transparent");
      c.fillStyle=grd; c.fillRect(0,0,W,H);
    }
  }
  const lines = wood.tight?20:9;
  for (let i=0;i<lines;i++){
    const y=(i+rng()*0.6)/lines*H;
    c.beginPath(); c.moveTo(0,y);
    if (wood.figure) {
      for(let x=0;x<=W;x+=3) c.lineTo(x,y+Math.sin(x*0.12+rng()*3)*4+rng()*2-1);
    } else {
      c.lineTo(W,y+rng()*3-1.5);
    }
    c.strokeStyle=rng()>0.5?wood.grain:wood.base;
    c.lineWidth=rng()*1.4+0.2; c.globalAlpha=0.3+rng()*0.4; c.stroke();
  }
  c.globalAlpha=1;
  if(!wood.tight&&!wood.iridescent){
    for(let i=0;i<W*H*0.01;i++){
      c.beginPath(); c.arc(rng()*W,rng()*H,rng()*0.6+0.1,0,Math.PI*2);
      c.fillStyle=wood.grain; c.globalAlpha=0.25+rng()*0.3; c.fill();
    }
    c.globalAlpha=1;
  }
  grainCache[key]=off;
  return off;
}

// ═══════════════════════════════════════════════════════════════════
// TILE PATTERN GENERATORS → grid[row][col] = woodId string
// ═══════════════════════════════════════════════════════════════════
const ROPE_BASE = [
  [0,0,0,0,0,1,1],[0,0,0,0,1,1,0],[0,0,0,1,1,0,0],
  [0,0,1,1,0,0,1],[0,1,1,0,0,1,0],
];
const ROPE_MIRR = ROPE_BASE.map(r=>[...r].reverse());

function archY(lx,sl,A,sk){
  const px=sk*sl; if(px<=0||sl<=0) return 0;
  return lx<=px ? A*Math.sin(Math.PI/2*lx/px) : A*Math.cos(Math.PI/2*(lx-px)/(sl-px));
}

function generateGrid(ring, nC, nR) {
  const { type, params, materials } = ring;
  const mat = materials ?? ["ebony","maple","rosewood","bone"];
  const get = i => mat[Math.min(i, mat.length-1)] ?? "ebony";

  const g = [];
  for (let r=0; r<nR; r++) {
    const row = [];
    for (let c=0; c<nC; c++) {
      let v = 0;
      if (type==="solid") {
        v = 0;
      } else if (type==="checkerboard") {
        const { w=4, h=2 } = params??{};
        const bR=Math.floor(r/h), bC=Math.floor(c/w);
        v = (bR+bC)%2;
      } else if (type==="brick") {
        const { w=6, h=3 } = params??{};
        const bR=Math.floor(r/h);
        const off=bR%2===0?0:Math.floor(w/2);
        v = Math.floor((c+off)/w)%2;
      } else if (type==="stripe") {
        const { w=4, count=2 } = params??{};
        v = Math.floor(c/w)%count;
      } else if (type==="wave") {
        const {A=6,sl=18,gap=2,d=4,sw=1.8,N=7,sk=0.72,ch=13,cmode="tri"} = params??{};
        const pitch=sl+gap; let hit=false,hitN=0;
        for(let n=-2;n<=N+2;n++){
          const off=((n*ch)%pitch+pitch*100)%pitch;
          const xs=((c-off)%pitch+pitch*100)%pitch;
          if(xs>=sl) continue;
          if(Math.abs(r-(n*d+archY(xs,sl,A,sk)))<sw/2){hit=true;hitN=n;break;}
        }
        if(hit){
          const idx=((hitN%3)+3)%3;
          v = cmode==="mono"?0 : cmode==="bw"?(((hitN%2)+2)%2===0?0:1) : idx;
        } else { v=-1; }
      } else if (type==="rope") {
        const tH=5;
        const rep=Math.floor(c/7);
        const tile=rep%2===0?ROPE_BASE:ROPE_MIRR;
        const gr=Math.min(Math.floor(r*tH/nR),tH-1);
        v=tile[gr][c%7];
      } else if (type==="custom") {
        const cg=params?.grid;
        if(cg?.length){ const gh=cg.length,gw=cg[0].length;
          v=cg[Math.min(Math.floor(r*gh/nR),gh-1)]?.[c%gw]??0; }
      }
      row.push(v<0 ? null : get(v));
    }
    g.push(row);
  }
  return g;
}

// ═══════════════════════════════════════════════════════════════════
// RING DEFINITIONS
// ═══════════════════════════════════════════════════════════════════
const TYPES = ["solid","checkerboard","brick","stripe","wave","rope","custom"];
const TYPE_LABEL = { solid:"Solid",checkerboard:"Checkerboard",brick:"Brick",stripe:"Stripe",wave:"Wave",rope:"Rope Twist",custom:"Custom Grid" };

let _uid=1; const uid=()=>_uid++;
const DEFAULTS = {
  solid:        { params:{},                materials:["ebony","maple","rosewood","bone"] },
  checkerboard: { params:{w:4,h:2},         materials:["ebony","maple","rosewood","bone"] },
  brick:        { params:{w:6,h:3},         materials:["ebony","maple","rosewood","bone"] },
  stripe:       { params:{w:4,count:2},     materials:["ebony","maple","rosewood","bone"] },
  wave:         { params:{A:6,sl:18,gap:2,sk:0.72,ch:13,d:4,sw:1.8,N:7,cmode:"tri"}, materials:["ebony","maple","rosewood","bone"] },
  rope:         { params:{},                materials:["ebony","maple","rosewood","bone"] },
  custom:       { params:{grid:Array.from({length:6},()=>new Array(12).fill(0))}, materials:["ebony","maple","rosewood","bone"] },
};

const INITIAL_RINGS = [
  { id:uid(), label:"Inner Binding", type:"solid",        widthMm:0.8, ...DEFAULTS.solid,        materials:["ebony","maple","rosewood","bone"] },
  { id:uid(), label:"Inner Frieze",  type:"checkerboard", widthMm:3.5, ...DEFAULTS.checkerboard, materials:["walnut","maple","rosewood","bone"] },
  { id:uid(), label:"Inner Border",  type:"solid",        widthMm:0.5, ...DEFAULTS.solid,        materials:["ebony","maple","rosewood","bone"] },
  { id:uid(), label:"Wave Band",     type:"wave",         widthMm:9.0, ...DEFAULTS.wave,         materials:["ebony","maple","rosewood","bone"] },
  { id:uid(), label:"Outer Border",  type:"solid",        widthMm:0.5, ...DEFAULTS.solid,        materials:["ebony","maple","rosewood","bone"] },
  { id:uid(), label:"Outer Frieze",  type:"brick",        widthMm:2.5, ...DEFAULTS.brick,        materials:["walnut","maple","rosewood","bone"] },
  { id:uid(), label:"Outer Binding", type:"solid",        widthMm:0.8, ...DEFAULTS.solid,        materials:["ebony","maple","rosewood","bone"] },
];

// ═══════════════════════════════════════════════════════════════════
// CANVAS RENDERER
// ═══════════════════════════════════════════════════════════════════
const CIRC_COLS = 480;
const SH_R = 40.8;
const MM_PX = 4.6;

function renderWheel(canvas, rings, selId) {
  if (!canvas) return;
  const S=canvas.width, cx=S/2, cy=S/2;
  const ctx=canvas.getContext("2d");
  ctx.clearRect(0,0,S,S);
  const bg=ctx.createRadialGradient(cx,cy,0,cx,cy,S/2);
  bg.addColorStop(0,"#0e0a06"); bg.addColorStop(1,"#060402");
  ctx.fillStyle=bg; ctx.fillRect(0,0,S,S);

  let rCur=SH_R;
  const prep=rings.map(ring=>{
    const iR=rCur; rCur+=ring.widthMm;
    const nR=Math.max(2,Math.round(ring.widthMm/0.5));
    return { ...ring, iR, oR:rCur, nR, grid:generateGrid(ring,CIRC_COLS,nR) };
  });

  const img=ctx.createImageData(S,S); const d=img.data;
  for(let py=0;py<S;py++) for(let px=0;px<S;px++){
    const dx=(px-cx)/MM_PX, dy=(py-cy)/MM_PX;
    const dist=Math.sqrt(dx*dx+dy*dy);
    const ring=prep.find(p=>dist>=p.iR&&dist<p.oR);
    if(!ring) continue;
    const ang=(Math.atan2(dy,dx)+Math.PI)/(Math.PI*2);
    const col=Math.min(Math.floor(ang*CIRC_COLS),CIRC_COLS-1);
    const row=Math.min(Math.floor((dist-ring.iR)/ring.widthMm*ring.nR),ring.nR-1);
    const wid=ring.grid[row]?.[col];
    if(!wid) continue;
    const wood=woodById(wid);
    const r8=parseInt(wood.base.slice(1,3),16);
    const g8=parseInt(wood.base.slice(3,5),16);
    const b8=parseInt(wood.base.slice(5,7),16);
    const i=(py*S+px)*4;
    d[i]=r8;d[i+1]=g8;d[i+2]=b8;d[i+3]=255;
  }
  ctx.putImageData(img,0,0);

  // Ring grain overlay — draw grain bitmaps into each ring sector
  prep.forEach(ring=>{
    const angStep=(Math.PI*2)/24;
    for(let si=0;si<24;si++){
      const wid=ring.grid[0]?.[Math.floor(si/24*CIRC_COLS)];
      if(!wid) continue;
      const a0=si*angStep-Math.PI/2, a1=(si+1)*angStep-Math.PI/2;
      const midA=(a0+a1)/2, midR=(ring.iR+ring.oR)/2*MM_PX;
      const grain=getGrain(wid, ring.id*100+si);
      const cw=(ring.oR-ring.iR)*MM_PX*1.3+6, ch=ring.oR*MM_PX*angStep*1.3+6;
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx,cy,ring.oR*MM_PX,a0,a1);
      ctx.arc(cx,cy,ring.iR*MM_PX,a1,a0,true);
      ctx.closePath(); ctx.clip();
      ctx.globalAlpha=0.55;
      ctx.translate(cx+Math.cos(midA)*midR, cy+Math.sin(midA)*midR);
      ctx.rotate(midA+Math.PI/2);
      ctx.drawImage(grain,-cw/2,-ch/2,cw,ch);
      ctx.restore();
    }
  });

  // Ring borders
  prep.forEach(ring=>{
    const isSel=ring.id===selId;
    [ring.iR,ring.oR].forEach(r=>{
      ctx.beginPath(); ctx.arc(cx,cy,r*MM_PX,0,Math.PI*2);
      ctx.strokeStyle=isSel?"rgba(232,200,122,0.6)":"rgba(200,160,50,0.15)";
      ctx.lineWidth=isSel?1.5:0.6; ctx.setLineDash(isSel?[]:[3,4]);
      ctx.stroke(); ctx.setLineDash([]);
    });
  });

  // Soundhole
  ctx.beginPath(); ctx.arc(cx,cy,SH_R*MM_PX,0,Math.PI*2);
  const sf=ctx.createRadialGradient(cx,cy-8,1,cx,cy,SH_R*MM_PX);
  sf.addColorStop(0,"#1a1208"); sf.addColorStop(1,"#060402");
  ctx.fillStyle=sf; ctx.fill();
  ctx.strokeStyle="rgba(200,160,50,0.4)"; ctx.lineWidth=1.2; ctx.stroke();

  // Outer ring
  ctx.beginPath(); ctx.arc(cx,cy,rCur*MM_PX+1,0,Math.PI*2);
  ctx.strokeStyle="rgba(200,160,50,0.12)"; ctx.lineWidth=2; ctx.stroke();
}

// ═══════════════════════════════════════════════════════════════════
// PARAM EDITORS
// ═══════════════════════════════════════════════════════════════════
function Sl({ label, val, set, min, max, step=1, note="" }) {
  return (
    <div style={{ marginBottom:"8px" }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"1px" }}>
        <span style={{ fontSize:"8px", color:"#4a3010" }}>{label}</span>
        <span style={{ fontSize:"9px", color:"#e8c87a" }}>{typeof val==="number"&&!Number.isInteger(val)?val.toFixed(2):val}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val}
        onChange={e=>set(Number(e.target.value))} style={{ width:"100%", accentColor:"#c9a96e" }}/>
      {note&&<div style={{ fontSize:"7px", color:"#2e1e08" }}>{note}</div>}
    </div>
  );
}

function MatSlot({ label, val, set }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:"6px", marginBottom:"5px" }}>
      <div style={{ width:"18px", height:"14px", borderRadius:"2px", background:woodById(val).base,
        border:"1px solid #2e2010", flexShrink:0 }}/>
      <span style={{ fontSize:"8px", color:"#4a3010", minWidth:"60px" }}>{label}</span>
      <select value={val} onChange={e=>set(e.target.value)}
        style={{ flex:1, background:"#0f0c08", border:"1px solid #2e2010", borderRadius:"2px",
          color:"#e8c87a", fontSize:"8px", padding:"2px 4px", fontFamily:"'Courier New',monospace" }}>
        {WOODS.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}
      </select>
    </div>
  );
}

function PatternParams({ ring, u, um }) {
  const { type, params:p, materials:mat } = ring;
  const setP = patch => u({ params:{ ...p, ...patch } });
  const setM = (i,v) => { const m=[...mat]; m[i]=v; u({ materials:m }); };

  const matSlots = {
    solid:        [["Fill",0]],
    checkerboard: [["Color A",0],["Color B",1]],
    brick:        [["Mortar",0],["Brick",1]],
    stripe:       [["Stripe A",0],["Stripe B",1],["Stripe C",2]],
    wave:         [["Background",0],["Strand A",1],["Strand B",2],["Strand C",3]],
    rope:         [["Dark",0],["Light",1]],
    custom:       [["Color 0",0],["Color 1",1],["Color 2",2],["Color 3",3]],
  }[type] ?? [];

  return (
    <div style={{ padding:"8px", background:"#0f0c08", border:"1px solid #2e2010", borderRadius:"4px" }}>
      {/* Materials */}
      <div style={{ fontSize:"7px", letterSpacing:"2px", color:"#4a3010", marginBottom:"7px" }}>MATERIALS</div>
      {matSlots.map(([label,i])=>(
        <MatSlot key={i} label={label} val={mat[i]??"ebony"} set={v=>setM(i,v)} />
      ))}

      {/* Pattern-specific params */}
      {(type==="checkerboard"||type==="brick") && <>
        <div style={{ fontSize:"7px", letterSpacing:"2px", color:"#4a3010", margin:"10px 0 7px" }}>TILE SIZE</div>
        <Sl label="Width" val={p?.w??4} set={v=>setP({w:v})} min={1} max={20} note={`${((p?.w??4)*0.5).toFixed(1)}mm`}/>
        <Sl label="Height" val={p?.h??2} set={v=>setP({h:v})} min={1} max={10} note={`${((p?.h??2)*0.5).toFixed(1)}mm`}/>
      </>}

      {type==="stripe" && <>
        <div style={{ fontSize:"7px", letterSpacing:"2px", color:"#4a3010", margin:"10px 0 7px" }}>STRIPE</div>
        <Sl label="Width" val={p?.w??4} set={v=>setP({w:v})} min={1} max={20} note={`${((p?.w??4)*0.5).toFixed(1)}mm`}/>
        <Sl label="Colors" val={p?.count??2} set={v=>setP({count:v})} min={2} max={4}/>
      </>}

      {type==="wave" && <>
        <div style={{ fontSize:"7px", letterSpacing:"2px", color:"#4a3010", margin:"10px 0 7px" }}>WAVE PARAMS</div>
        <Sl label="A — height" val={p?.A??6} set={v=>setP({A:v})} min={0} max={16} step={0.5} note={`${((p?.A??6)*0.5).toFixed(1)}mm`}/>
        <Sl label="segLen"     val={p?.sl??18} set={v=>setP({sl:v})} min={4} max={40} note={`${((p?.sl??18)*0.5).toFixed(1)}mm`}/>
        <Sl label="gap"        val={p?.gap??2} set={v=>setP({gap:v})} min={0} max={12}/>
        <Sl label="skew"       val={p?.sk??0.72} set={v=>setP({sk:v})} min={0.1} max={0.95} step={0.01} note={`peak at ${((p?.sk??0.72)*100).toFixed(0)}%`}/>
        <Sl label="chase"      val={p?.ch??13} set={v=>setP({ch:v})} min={0} max={(p?.sl??18)+(p?.gap??2)} note={Math.abs((p?.ch??13)-Math.round((p?.sk??0.72)*(p?.sl??18)))<=1?"✓ in-phase":`optimal=${Math.round((p?.sk??0.72)*(p?.sl??18))}`}/>
        <Sl label="d — pitch"  val={p?.d??4} set={v=>setP({d:v})} min={2} max={12} step={0.5}/>
        <Sl label="strand w"   val={p?.sw??1.8} set={v=>setP({sw:v})} min={0.5} max={6} step={0.5}/>
        <Sl label="N strands"  val={p?.N??7} set={v=>setP({N:v})} min={2} max={14}/>
        <div style={{ display:"flex", gap:"3px", marginTop:"4px" }}>
          {["mono","bw","tri"].map(m=>(
            <div key={m} onClick={()=>setP({cmode:m})} style={{
              padding:"2px 8px", cursor:"pointer", fontSize:"7px", borderRadius:"2px",
              border:(p?.cmode??"tri")===m?"1px solid #c9a96e":"1px solid #2e2010",
              background:(p?.cmode??"tri")===m?"#1a1208":"transparent",
              color:(p?.cmode??"tri")===m?"#e8c87a":"#4a3010" }}>{m}</div>
          ))}
        </div>
      </>}

      {type==="custom" && (()=>{
        const grid=p?.grid??Array.from({length:6},()=>new Array(12).fill(0));
        const [paint,setPaint]=useState(0);
        const FILLS=mat.map(m=>woodById(m).base);
        return <>
          <div style={{ fontSize:"7px", letterSpacing:"2px", color:"#4a3010", margin:"10px 0 7px" }}>PIXEL GRID</div>
          <div style={{ display:"flex", gap:"3px", marginBottom:"6px" }}>
            {mat.map((m,i)=>(
              <div key={i} onClick={()=>setPaint(i)} style={{
                width:"16px",height:"16px",borderRadius:"2px",cursor:"pointer",
                background:woodById(m).base, border:paint===i?"2px solid #e8c87a":"1px solid #2e2010" }}/>
            ))}
          </div>
          <div style={{ display:"inline-block",border:"1px solid #2e2010",borderRadius:"2px",overflow:"hidden",cursor:"crosshair" }}>
            {grid.map((row,r)=>(
              <div key={r} style={{ display:"flex" }}>
                {row.map((v,c)=>(
                  <div key={c} onClick={()=>{
                    const ng=grid.map(rr=>[...rr]); ng[r][c]=paint;
                    setP({grid:ng});
                  }} style={{ width:"10px",height:"10px",background:FILLS[v]??FILLS[0],border:"0.5px solid rgba(200,160,50,0.07)" }}/>
                ))}
              </div>
            ))}
          </div>
          <div style={{ marginTop:"5px",display:"flex",gap:"3px",flexWrap:"wrap" }}>
            {[[8,4],[12,6],[16,8]].map(([w,h])=>(
              <div key={`${w}x${h}`} onClick={()=>setP({grid:Array.from({length:h},(_,r)=>Array.from({length:w},(_,c)=>p?.grid?.[r]?.[c]??0))})}
                style={{ padding:"1px 5px",fontSize:"7px",cursor:"pointer",border:"1px solid #2e2010",borderRadius:"2px",color:"#4a3010" }}>
                {w}×{h}
              </div>
            ))}
          </div>
        </>;
      })()}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════
const CANVAS_SIZE = 520;

export default function RosetteStudio() {
  const [rings, setRings]   = useState(INITIAL_RINGS);
  const [selId, setSelId]   = useState(INITIAL_RINGS[3].id);
  const [soundR, setSoundR] = useState(SH_R);
  const [zoom, setZoom]     = useState(1);
  const [tab, setTab]       = useState("stack"); // stack | materials
  const canvasRef = useRef(null);
  const timer = useRef(null);

  const sel = rings.find(r=>r.id===selId);
  const totalW = rings.reduce((s,r)=>s+r.widthMm,0);
  const outerR = soundR + totalW;

  const upd = (id,patch) => setRings(rs=>rs.map(r=>r.id===id?{...r,...patch}:r));
  const updRing = patch => sel && upd(sel.id, patch);

  useEffect(()=>{
    clearTimeout(timer.current);
    timer.current=setTimeout(()=>renderWheel(canvasRef.current,rings,selId),55);
    return ()=>clearTimeout(timer.current);
  },[rings,selId,soundR]);

  const addRing = t => {
    const r={id:uid(),label:TYPE_LABEL[t],type:t,widthMm:2.0,...DEFAULTS[t],materials:["ebony","maple","rosewood","bone"]};
    setRings(rs=>[...rs,r]); setSelId(r.id);
  };
  const delRing = id => { setRings(rs=>rs.filter(r=>r.id!==id)); if(selId===id) setSelId(rings[0]?.id??null); };
  const moveRing = (id,dir) => setRings(rs=>{
    const i=rs.findIndex(r=>r.id===id),j=i+dir;
    if(j<0||j>=rs.length) return rs;
    const n=[...rs]; [n[i],n[j]]=[n[j],n[i]]; return n;
  });

  const presets = {
    torres: { rings:[
      {label:"Inner Binding",type:"solid",widthMm:0.8,materials:["ebony","maple","rosewood","bone"]},
      {label:"Inner Frieze",type:"brick",widthMm:3.5,params:{w:5,h:2},materials:["walnut","maple","rosewood","bone"]},
      {label:"Border",type:"solid",widthMm:0.5,materials:["ebony","maple","rosewood","bone"]},
      {label:"Wave Band",type:"wave",widthMm:9.0,params:{A:6,sl:18,gap:2,sk:0.72,ch:13,d:4,sw:1.8,N:7,cmode:"tri"},materials:["ebony","maple","rosewood","bone"]},
      {label:"Border",type:"solid",widthMm:0.5,materials:["ebony","maple","rosewood","bone"]},
      {label:"Outer Frieze",type:"brick",widthMm:2.5,params:{w:5,h:2},materials:["walnut","maple","rosewood","bone"]},
      {label:"Outer Binding",type:"solid",widthMm:0.8,materials:["ebony","maple","rosewood","bone"]},
    ]},
    pearl: { rings:[
      {label:"Ebony Ring",type:"solid",widthMm:1.0,materials:["ebony","maple","rosewood","bone"]},
      {label:"MOP Checks",type:"checkerboard",widthMm:4.0,params:{w:4,h:2},materials:["ebony","mop","rosewood","bone"]},
      {label:"Ebony",type:"solid",widthMm:0.5,materials:["ebony","maple","rosewood","bone"]},
      {label:"Abalone Band",type:"stripe",widthMm:6.0,params:{w:6,count:2},materials:["abalone","mop","rosewood","bone"]},
      {label:"Ebony",type:"solid",widthMm:0.5,materials:["ebony","maple","rosewood","bone"]},
      {label:"MOP Rope",type:"rope",widthMm:3.0,materials:["ebony","mop","rosewood","bone"]},
      {label:"Ebony Ring",type:"solid",widthMm:1.0,materials:["ebony","maple","rosewood","bone"]},
    ]},
    celtic: { rings:[
      {label:"Walnut Bind",type:"solid",widthMm:0.8,materials:["walnut","maple","rosewood","bone"]},
      {label:"Koa Stripe",type:"stripe",widthMm:2.5,params:{w:3,count:2},materials:["walnut","koa","rosewood","bone"]},
      {label:"Ebony",type:"solid",widthMm:0.5,materials:["ebony","maple","rosewood","bone"]},
      {label:"Rope Band",type:"rope",widthMm:5.0,materials:["walnut","koa","rosewood","bone"]},
      {label:"Ebony",type:"solid",widthMm:0.5,materials:["ebony","maple","rosewood","bone"]},
      {label:"Koa Checks",type:"checkerboard",widthMm:3.5,params:{w:4,h:2},materials:["walnut","koa","rosewood","bone"]},
      {label:"Walnut Bind",type:"solid",widthMm:0.8,materials:["walnut","maple","rosewood","bone"]},
    ]},
  };

  const loadPreset = key => {
    const p=presets[key]; if(!p) return;
    const rs=p.rings.map(r=>({...r,id:uid(),...DEFAULTS[r.type],params:r.params??DEFAULTS[r.type].params,materials:r.materials}));
    setRings(rs); setSelId(rs[3]?.id??rs[0]?.id);
  };

  return (
    <div style={{ height:"100vh", background:"#080604", fontFamily:"'Courier New',monospace",
      color:"#c9a96e", display:"flex", flexDirection:"column", overflow:"hidden" }}>

      {/* HEADER */}
      <div style={{ padding:"10px 18px", borderBottom:"1px solid #1a1008",
        display:"flex", justifyContent:"space-between", alignItems:"center", flexShrink:0 }}>
        <div>
          <div style={{ fontSize:"7px", letterSpacing:"5px", color:"#2a1808" }}>THE PRODUCTION SHOP · INLAY MODULE</div>
          <div style={{ fontSize:"20px", fontWeight:"bold", color:"#e8c87a", letterSpacing:"2px", marginTop:"1px" }}>
            Rosette Studio
          </div>
        </div>
        <div style={{ fontSize:"8px", color:"#3a2010", textAlign:"right", lineHeight:2 }}>
          ⌀{(soundR*2).toFixed(1)}mm soundhole ·
          <span style={{ color:"#e8c87a" }}> {totalW.toFixed(1)}mm</span> band ·
          ⌀{(outerR*2).toFixed(1)}mm outer ·
          <span style={{ color:"#e8c87a" }}> {rings.length}</span> rings
        </div>
      </div>

      <div style={{ flex:1, display:"flex", overflow:"hidden" }}>

        {/* ══ LEFT PANEL ══ */}
        <div style={{ width:"220px", flexShrink:0, borderRight:"1px solid #1a1008",
          display:"flex", flexDirection:"column", overflow:"hidden" }}>

          {/* Tab switcher */}
          <div style={{ display:"flex", borderBottom:"1px solid #1a1008" }}>
            {[["stack","Ring Stack"],["global","Global"]].map(([k,l])=>(
              <div key={k} onClick={()=>setTab(k)} style={{
                flex:1, padding:"7px", textAlign:"center", cursor:"pointer", fontSize:"8px",
                letterSpacing:"1px", color:tab===k?"#e8c87a":"#3a2010",
                background:tab===k?"#0f0c08":"transparent",
                borderBottom:tab===k?"2px solid #c9a96e":"2px solid transparent",
              }}>{l}</div>
            ))}
          </div>

          {tab==="stack" && <>
            <div style={{ padding:"8px 10px 3px", fontSize:"7px", letterSpacing:"3px", color:"#3a2010" }}>
              ← INSIDE → OUTSIDE →
            </div>
            <div style={{ flex:1, overflowY:"auto", padding:"4px 8px" }}>
              {rings.map((ring,idx)=>(
                <div key={ring.id} onClick={()=>setSelId(ring.id)}
                  style={{ marginBottom:"3px", padding:"6px 8px", cursor:"pointer", borderRadius:"3px",
                    background:selId===ring.id?"#130f09":"transparent",
                    border:selId===ring.id?"1px solid #c9a96e":"1px solid #1e1508",
                    transition:"all .07s" }}>
                  <div style={{ display:"flex", alignItems:"center", gap:"5px" }}>
                    {/* Material swatch(es) */}
                    <div style={{ display:"flex", gap:"1px", flexShrink:0 }}>
                      {ring.materials.slice(0,ring.type==="solid"?1:2).map((m,mi)=>(
                        <div key={mi} style={{ width:"8px",height:"8px",borderRadius:"1px",
                          background:woodById(m).base,border:"1px solid #1e1508" }}/>
                      ))}
                    </div>
                    <div style={{ flex:1, minWidth:0 }}>
                      <div style={{ fontSize:"9px", color:selId===ring.id?"#e8c87a":"#7a5c2e",
                        overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap" }}>
                        {ring.label}
                      </div>
                      <div style={{ fontSize:"7px", color:"#2e1e08" }}>
                        {TYPE_LABEL[ring.type]} · {ring.widthMm.toFixed(1)}mm
                      </div>
                    </div>
                    <div style={{ display:"flex",flexDirection:"column",gap:"1px",flexShrink:0 }}>
                      <div onClick={e=>{e.stopPropagation();moveRing(ring.id,-1);}} style={{ fontSize:"7px",color:"#3a2010",cursor:"pointer",padding:"1px 3px" }}>▲</div>
                      <div onClick={e=>{e.stopPropagation();moveRing(ring.id, 1);}} style={{ fontSize:"7px",color:"#3a2010",cursor:"pointer",padding:"1px 3px" }}>▼</div>
                    </div>
                    <div onClick={e=>{e.stopPropagation();delRing(ring.id);}} style={{ fontSize:"8px",color:"#2e1e08",cursor:"pointer",padding:"0 2px",flexShrink:0 }}>✕</div>
                  </div>
                  {/* Width bar */}
                  <div style={{ marginTop:"4px",height:"2px",background:"#1e1508",borderRadius:"1px" }}>
                    <div style={{ width:`${Math.min(ring.widthMm/totalW*100,100)}%`,height:"100%",
                      background:selId===ring.id?"#c9a96e":"#3a2010",borderRadius:"1px" }}/>
                  </div>
                </div>
              ))}
            </div>
            {/* Add ring */}
            <div style={{ padding:"8px", borderTop:"1px solid #1a1008" }}>
              <div style={{ fontSize:"7px",letterSpacing:"2px",color:"#2e1e08",marginBottom:"5px" }}>ADD RING</div>
              <div style={{ display:"flex",flexWrap:"wrap",gap:"3px" }}>
                {TYPES.map(t=>(
                  <div key={t} onClick={()=>addRing(t)} style={{ padding:"3px 6px",cursor:"pointer",
                    fontSize:"7px",border:"1px solid #1e1508",borderRadius:"2px",color:"#3a2010" }}>
                    +{TYPE_LABEL[t]}
                  </div>
                ))}
              </div>
            </div>
            {/* Presets */}
            <div style={{ padding:"8px",borderTop:"1px solid #1a1008" }}>
              <div style={{ fontSize:"7px",letterSpacing:"2px",color:"#2e1e08",marginBottom:"5px" }}>PRESETS</div>
              <div style={{ display:"flex",gap:"4px",flexWrap:"wrap" }}>
                {[["torres","Torres"],["pearl","Pearl"],["celtic","Celtic"]].map(([k,l])=>(
                  <div key={k} onClick={()=>loadPreset(k)} style={{ padding:"3px 8px",cursor:"pointer",
                    fontSize:"7px",border:"1px solid #2e2010",borderRadius:"2px",color:"#7a5c2e" }}>{l}</div>
                ))}
              </div>
            </div>
          </>}

          {tab==="global" && (
            <div style={{ flex:1, overflowY:"auto", padding:"10px" }}>
              <div style={{ padding:"10px",background:"#0f0c08",border:"1px solid #1e1508",borderRadius:"4px",marginBottom:"10px" }}>
                <div style={{ fontSize:"7px",letterSpacing:"2px",color:"#3a2010",marginBottom:"8px" }}>DIMENSIONS</div>
                <Sl label="Soundhole radius" val={soundR} set={setSoundR} min={30} max={65} step={0.1} note={`⌀${(soundR*2).toFixed(1)}mm`}/>
              </div>
              {/* Full BOM */}
              <div style={{ padding:"10px",background:"#0f0c08",border:"1px solid #1e1508",borderRadius:"4px" }}>
                <div style={{ fontSize:"7px",letterSpacing:"2px",color:"#3a2010",marginBottom:"8px" }}>BILL OF MATERIALS</div>
                {rings.map((ring,ri)=>(
                  <div key={ring.id} style={{ marginBottom:"7px",paddingBottom:"7px",borderBottom:"1px solid #1a1008" }}>
                    <div style={{ fontSize:"8px",color:"#7a5c2e",marginBottom:"3px" }}>{ring.label}</div>
                    <div style={{ fontSize:"7px",color:"#3a2010",lineHeight:1.9 }}>
                      {TYPE_LABEL[ring.type]} · {ring.widthMm.toFixed(1)}mm wide<br/>
                      {ring.materials.slice(0,{solid:1,checkerboard:2,brick:2,stripe:ring.params?.count??2,wave:4,rope:2,custom:4}[ring.type]??2)
                        .map(m=>woodById(m).name).join(" / ")}
                    </div>
                  </div>
                ))}
                <div style={{ fontSize:"7px",color:"#3a2010",marginTop:"4px" }}>
                  Total: <span style={{ color:"#e8c87a" }}>{totalW.toFixed(1)}mm</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ══ CENTER: WHEEL ══ */}
        <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center",
          justifyContent:"center", background:"#080604", padding:"16px", gap:"10px" }}>

          <canvas ref={canvasRef} width={CANVAS_SIZE} height={CANVAS_SIZE}
            onClick={e=>{
              // Click ring in wheel to select it
              const rect=canvasRef.current.getBoundingClientRect();
              const dx=(e.clientX-rect.left-CANVAS_SIZE/2)/MM_PX;
              const dy=(e.clientY-rect.top-CANVAS_SIZE/2)/MM_PX;
              const dist=Math.sqrt(dx*dx+dy*dy);
              let rr=soundR;
              for(const ring of rings){
                if(dist>=rr&&dist<rr+ring.widthMm){ setSelId(ring.id); break; }
                rr+=ring.widthMm;
              }
            }}
            style={{ cursor:"crosshair",borderRadius:"50%",
              boxShadow:"0 0 80px rgba(200,160,50,0.05),0 0 160px rgba(0,0,0,0.9)" }}/>

          <div style={{ fontSize:"7px",letterSpacing:"2px",color:"#1e1208" }}>
            CLICK A RING ON THE WHEEL TO SELECT IT
          </div>

          {/* Proportional band strip */}
          <div style={{ display:"flex",gap:"0",height:"8px",width:"340px",
            borderRadius:"2px",overflow:"hidden",border:"1px solid #1a1008" }}>
            {rings.map(ring=>{
              const w=woodById(ring.materials[0]??"ebony");
              return (
                <div key={ring.id} title={`${ring.label} · ${ring.widthMm.toFixed(1)}mm`}
                  onClick={()=>setSelId(ring.id)}
                  style={{ flex:ring.widthMm,background:w.base,minWidth:"2px",cursor:"pointer",
                    outline:selId===ring.id?"2px solid #e8c87a":"none" }}/>
              );
            })}
          </div>
          <div style={{ fontSize:"7px",color:"#1a1208",letterSpacing:"1px" }}>← SOUNDHOLE — BAND CROSS-SECTION — EDGE →</div>
        </div>

        {/* ══ RIGHT: RING EDITOR ══ */}
        <div style={{ width:"240px", flexShrink:0, borderLeft:"1px solid #1a1008",
          overflowY:"auto", padding:"10px" }}>
          {sel ? <>
            {/* Ring label */}
            <div style={{ marginBottom:"10px" }}>
              <div style={{ fontSize:"7px",letterSpacing:"2px",color:"#3a2010",marginBottom:"4px" }}>RING LABEL</div>
              <input value={sel.label} onChange={e=>updRing({label:e.target.value})}
                style={{ width:"100%",background:"#0f0c08",border:"1px solid #2e2010",borderRadius:"3px",
                  padding:"5px 8px",color:"#e8c87a",fontSize:"9px",fontFamily:"'Courier New',monospace",boxSizing:"border-box" }}/>
            </div>

            {/* Pattern type selector */}
            <div style={{ marginBottom:"10px" }}>
              <div style={{ fontSize:"7px",letterSpacing:"2px",color:"#3a2010",marginBottom:"5px" }}>PATTERN TYPE</div>
              <div style={{ display:"flex",flexWrap:"wrap",gap:"3px" }}>
                {TYPES.map(t=>(
                  <div key={t} onClick={()=>updRing({type:t,...DEFAULTS[t]})} style={{
                    padding:"3px 7px",cursor:"pointer",fontSize:"7px",borderRadius:"2px",
                    border:sel.type===t?"1px solid #c9a96e":"1px solid #1e1508",
                    background:sel.type===t?"#130f09":"transparent",
                    color:sel.type===t?"#e8c87a":"#3a2010" }}>{TYPE_LABEL[t]}</div>
                ))}
              </div>
            </div>

            {/* Width */}
            <div style={{ padding:"8px",background:"#0f0c08",border:"1px solid #1e1508",borderRadius:"3px",marginBottom:"10px" }}>
              <Sl label="RING WIDTH" val={sel.widthMm} set={v=>updRing({widthMm:v})} min={0.3} max={15} step={0.1} note={`${Math.round(sel.widthMm/0.5)} cells @ 0.5mm`}/>
            </div>

            {/* Pattern + material params */}
            <PatternParams ring={sel} u={updRing} um={updRing} />

            {/* Visual type explanation */}
            <div style={{ marginTop:"10px",padding:"8px",background:"#0a0704",border:"1px solid #1a1008",
              borderRadius:"3px",fontSize:"7px",color:"#2e1e08",lineHeight:2 }}>
              {{
                solid:"One material fills the entire ring. Use for bindings and borders.",
                checkerboard:"Alternating tiles in a true checkerboard — (A,B) repeat across row and column.",
                brick:"Running bond — rows offset by half a brick width. Classic frieze.",
                stripe:"Parallel bands of 2–4 materials running around the ring.",
                wave:"Asymmetric crash-arch strands. Full Torres/Ramirez parameter set.",
                rope:"7×5 diagonal staircase, mirrored every repeat for the rope helix.",
                custom:"Paint your own pixel tile — repeats around the ring.",
              }[sel.type]}
            </div>
          </> : (
            <div style={{ fontSize:"8px",color:"#2e1e08",padding:"20px 10px",textAlign:"center" }}>
              Click a ring on the wheel or in the stack to edit it
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
