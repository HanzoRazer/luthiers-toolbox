import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════
// MATERIALS
// ═══════════════════════════════════════════════════════════
const WOODS = [
  { id:"ebony",    name:"Ebony",          base:"#1a1008", grain:"#0d0804", hi:"#2a1c10", tight:true  },
  { id:"maple",    name:"Maple",          base:"#f2e8c8", grain:"#c8a860", hi:"#fff8e8", tight:true  },
  { id:"rosewood", name:"Rosewood",       base:"#4a1e10", grain:"#2e1008", hi:"#6a3020", tight:false },
  { id:"koa",      name:"Koa",            base:"#c87828", grain:"#804810", hi:"#e8a848", tight:false },
  { id:"walnut",   name:"Walnut",         base:"#5c3818", grain:"#382008", hi:"#7c5838", tight:false },
  { id:"cedar",    name:"Cedar",          base:"#c07040", grain:"#883020", hi:"#d89060", tight:false },
  { id:"spruce",   name:"Spruce",         base:"#e8d8a0", grain:"#b89840", hi:"#f8f0c0", tight:true  },
  { id:"mahogany", name:"Mahogany",       base:"#7a3018", grain:"#4a1808", hi:"#9a5030", tight:false },
  { id:"mop",      name:"Mother-of-Pearl",base:"#ddeef8", grain:"#a8ccec", hi:"#f0f8ff", irid:true   },
  { id:"abalone",  name:"Abalone",        base:"#508868", grain:"#306848", hi:"#80b898", irid:true   },
  { id:"bone",     name:"Bone",           base:"#f0e8d0", grain:"#c8b888", hi:"#fff8f0", tight:true  },
  { id:"ovangkol", name:"Ovangkol",       base:"#a87828", grain:"#685010", hi:"#c89838", tight:true  },
];
const W = id => WOODS.find(w=>w.id===id) ?? WOODS[0];

// ═══════════════════════════════════════════════════════════
// GRAIN ENGINE
// ═══════════════════════════════════════════════════════════
const GC = {};
function grain(woodId, seed, bw, bh) {
  const k=`${woodId}:${seed%6}:${bw}:${bh}`;
  if(GC[k]) return GC[k];
  const wood=W(woodId);
  const c=document.createElement("canvas"); c.width=bw; c.height=bh;
  const g=c.getContext("2d");
  g.fillStyle=wood.base; g.fillRect(0,0,bw,bh);
  let s=seed*9301+49297;
  const rng=()=>{s=(s*9301+49297)%233280;return s/233280;};
  if(wood.irid){
    for(let i=0;i<7;i++){
      const gr=g.createRadialGradient(rng()*bw,rng()*bh,0,rng()*bw,rng()*bh,bw*0.8);
      const h=(seed*37+i*53)%360;
      gr.addColorStop(0,`hsla(${h},60%,82%,0.45)`);
      gr.addColorStop(0.6,`hsla(${(h+80)%360},40%,65%,0.2)`);
      gr.addColorStop(1,"transparent");
      g.fillStyle=gr; g.fillRect(0,0,bw,bh);
    }
  } else {
    const lines=wood.tight?22:10;
    for(let i=0;i<lines;i++){
      const y=(i+rng()*0.7)/lines*bh;
      g.beginPath(); g.moveTo(0,y);
      for(let x=0;x<=bw;x+=4) g.lineTo(x, y+Math.sin(x*0.09+rng()*2)*(wood.tight?2:5)+rng()*2-1);
      g.strokeStyle=rng()>0.5?wood.grain:wood.hi;
      g.lineWidth=rng()*1.3+0.2; g.globalAlpha=0.2+rng()*0.35; g.stroke();
    }
    if(!wood.tight) for(let i=0;i<bw*bh*0.008;i++){
      g.beginPath(); g.arc(rng()*bw,rng()*bh,rng()*0.7+0.1,0,Math.PI*2);
      g.fillStyle=wood.grain; g.globalAlpha=0.2+rng()*0.25; g.fill();
    }
    g.globalAlpha=1;
  }
  GC[k]=c; return c;
}

// ═══════════════════════════════════════════════════════════
// HYPERBOLIC WAVE SHAPE DRAW
// ═══════════════════════════════════════════════════════════
function hypDraw(ctx, W, H, p, idx) {
  const hh = H/2 * p.thick;
  const t = idx*0.3 + p.drift*Math.log(idx+2) + p.chaos*Math.sin(idx*0.17);
  const peakX = -W/2 + W*(p.skew + 0.1*Math.sin(t));
  const waveY = H/2 * p.wave * Math.sin(t*2.3);
  ctx.moveTo(-W/2, -hh+waveY);
  ctx.bezierCurveTo(peakX-W/6,-hh-waveY*0.5, peakX+W/6,-hh+waveY, W/2,-hh+waveY*0.3);
  ctx.lineTo(W/2, hh-waveY*0.3);
  ctx.bezierCurveTo(peakX+W/6,hh+waveY, peakX-W/6,hh+waveY*0.5, -W/2,hh-waveY);
  ctx.closePath();
}

// ═══════════════════════════════════════════════════════════
// RING DEFINITIONS  (inside → outside)
// Each ring: { widthMm, type, ...type-specific props }
// types: solid | stripe | checker | hyp
// ═══════════════════════════════════════════════════════════
let uid=1;
const mkRing = (r) => ({ id: uid++, ...r });

const PRESETS = {
  classic: {
    name:"Classic Dark",
    desc:"Ebony bindings, maple/rosewood checker frieze, deep wave band",
    innerR: 40.8,
    rings: [
      mkRing({ label:"Inner Binding", type:"solid",   widthMm:0.9,  mat:"ebony"    }),
      mkRing({ label:"Inner Frieze",  type:"checker", widthMm:3.5,  matA:"ebony",   matB:"maple",    bw:3, bh:2 }),
      mkRing({ label:"Inner Border",  type:"solid",   widthMm:0.6,  mat:"ebony"    }),
      mkRing({ label:"Hyp Wave",      type:"hyp",     widthMm:10.0, matA:"maple",   matB:"rosewood", matC:"ebony",
               N:28, gap:0.96, thick:0.48, wave:0.78, skew:0.72, drift:1.4, chaos:0.38, dist:"abc", showOut:true }),
      mkRing({ label:"Outer Border",  type:"solid",   widthMm:0.6,  mat:"ebony"    }),
      mkRing({ label:"Outer Frieze",  type:"checker", widthMm:2.5,  matA:"ebony",   matB:"maple",    bw:3, bh:2 }),
      mkRing({ label:"Outer Binding", type:"solid",   widthMm:0.9,  mat:"ebony"    }),
    ],
  },
  pearl: {
    name:"Pearl Storm",
    desc:"MOP & abalone on ebony — maximum iridescent chaos",
    innerR: 40.8,
    rings: [
      mkRing({ label:"Ebony Bind",    type:"solid",   widthMm:1.0,  mat:"ebony"    }),
      mkRing({ label:"MOP Stripe",    type:"stripe",  widthMm:2.5,  matA:"mop",     matB:"ebony",    sw:3 }),
      mkRing({ label:"Ebony Border",  type:"solid",   widthMm:0.5,  mat:"ebony"    }),
      mkRing({ label:"Hyp Wave",      type:"hyp",     widthMm:11.0, matA:"mop",     matB:"abalone",  matC:"ebony",
               N:36, gap:1.02, thick:0.42, wave:1.05, skew:0.80, drift:1.8, chaos:0.68, dist:"abc", showOut:false }),
      mkRing({ label:"Ebony Border",  type:"solid",   widthMm:0.5,  mat:"ebony"    }),
      mkRing({ label:"Abalone Line",  type:"stripe",  widthMm:2.0,  matA:"abalone", matB:"ebony",    sw:4 }),
      mkRing({ label:"Ebony Bind",    type:"solid",   widthMm:1.0,  mat:"ebony"    }),
    ],
  },
  koa: {
    name:"Koa Drift",
    desc:"Warm Hawaiian — slow drift, low chaos, high contrast",
    innerR: 40.8,
    rings: [
      mkRing({ label:"Walnut Bind",   type:"solid",   widthMm:0.8,  mat:"walnut"   }),
      mkRing({ label:"Koa/Maple",     type:"checker", widthMm:3.0,  matA:"koa",     matB:"maple",    bw:4, bh:2 }),
      mkRing({ label:"Ebony Border",  type:"solid",   widthMm:0.5,  mat:"ebony"    }),
      mkRing({ label:"Hyp Wave",      type:"hyp",     widthMm:9.5,  matA:"koa",     matB:"maple",    matC:"walnut",
               N:20, gap:0.90, thick:0.58, wave:0.48, skew:0.65, drift:0.5, chaos:0.12, dist:"ab", showOut:true }),
      mkRing({ label:"Ebony Border",  type:"solid",   widthMm:0.5,  mat:"ebony"    }),
      mkRing({ label:"Koa/Maple",     type:"checker", widthMm:2.5,  matA:"koa",     matB:"maple",    bw:4, bh:2 }),
      mkRing({ label:"Walnut Bind",   type:"solid",   widthMm:0.8,  mat:"walnut"   }),
    ],
  },
  fire: {
    name:"Cedar Fire",
    desc:"Cedar & spruce soundboard woods — maximum drift, organic chaos",
    innerR: 40.8,
    rings: [
      mkRing({ label:"Ebony Bind",    type:"solid",   widthMm:0.7,  mat:"ebony"    }),
      mkRing({ label:"Cedar Stripe",  type:"stripe",  widthMm:2.5,  matA:"cedar",   matB:"ebony",    sw:5 }),
      mkRing({ label:"Ebony",         type:"solid",   widthMm:0.4,  mat:"ebony"    }),
      mkRing({ label:"Hyp Wave",      type:"hyp",     widthMm:12.0, matA:"cedar",   matB:"spruce",   matC:"mahogany",
               N:32, gap:1.06, thick:0.36, wave:1.18, skew:0.88, drift:2.0, chaos:0.88, dist:"abc", showOut:false }),
      mkRing({ label:"Ebony",         type:"solid",   widthMm:0.4,  mat:"ebony"    }),
      mkRing({ label:"Spruce Stripe", type:"stripe",  widthMm:2.0,  matA:"spruce",  matB:"ebony",    sw:5 }),
      mkRing({ label:"Ebony Bind",    type:"solid",   widthMm:0.7,  mat:"ebony"    }),
    ],
  },
};

// ═══════════════════════════════════════════════════════════
// MAIN RENDERER
// ═══════════════════════════════════════════════════════════
const SZ = 540;
const CX = SZ/2, CY = SZ/2;

function renderRosette(canvas, rings, innerR) {
  if(!canvas) return;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0,0,SZ,SZ);

  // Atmosphere background
  const atm = ctx.createRadialGradient(CX,CY-20,10,CX,CY,SZ*0.6);
  atm.addColorStop(0,"#0f0a05"); atm.addColorStop(1,"#050302");
  ctx.fillStyle=atm; ctx.fillRect(0,0,SZ,SZ);

  // Build ring bounds
  let rCur = innerR;
  const totalW = rings.reduce((s,r)=>s+r.widthMm,0);
  const outerR = innerR + totalW;
  // Scale to fit
  const MM = (SZ*0.46) / outerR;

  const bounds = rings.map(ring => {
    const iR=rCur*MM, oR=(rCur+ring.widthMm)*MM;
    rCur += ring.widthMm;
    return { iR, oR, midR:(iR+oR)/2, ring };
  });

  // ── RENDER EACH RING ──
  bounds.forEach(({ iR, oR, midR, ring }) => {
    const angStep = Math.PI*2;

    if (ring.type === "solid") {
      ctx.save();
      ctx.beginPath();
      ctx.arc(CX,CY,oR,0,Math.PI*2);
      ctx.arc(CX,CY,iR,0,Math.PI*2,true);
      ctx.clip();
      const wood = W(ring.mat);
      ctx.fillStyle = wood.base;
      ctx.fill();
      // grain overlay
      const gr = grain(ring.mat, ring.id*7, Math.ceil(oR*2), Math.ceil(oR*2));
      ctx.globalAlpha=0.55;
      ctx.drawImage(gr, CX-oR, CY-oR, oR*2, oR*2);
      ctx.globalAlpha=1;
      ctx.restore();
    }

    else if (ring.type === "stripe") {
      const { matA, matB, sw=4 } = ring;
      // pixel-row paint
      const COLS = 512;
      const img = ctx.createImageData(SZ,SZ); const d=img.data;
      for(let py=0;py<SZ;py++) for(let px=0;px<SZ;px++){
        const dx=(px-CX)/MM, dy=(py-CY)/MM;
        const dist=Math.sqrt(dx*dx+dy*dy);
        if(dist<iR/MM||dist>oR/MM) continue;
        const ang=((Math.atan2(dy,dx)+Math.PI*2.5)%(Math.PI*2))/(Math.PI*2);
        const col=Math.floor(ang*COLS);
        const cellW = Math.floor(col/(sw)) % 2;
        const wood = W(cellW===0?matA:matB);
        const r8=parseInt(wood.base.slice(1,3),16);
        const g8=parseInt(wood.base.slice(3,5),16);
        const b8=parseInt(wood.base.slice(5,7),16);
        const i=(py*SZ+px)*4;
        d[i]=r8;d[i+1]=g8;d[i+2]=b8;d[i+3]=255;
      }
      ctx.putImageData(img,0,0);
      // grain overlay pass
      ctx.save();
      ctx.beginPath();
      ctx.arc(CX,CY,oR,0,Math.PI*2);
      ctx.arc(CX,CY,iR,0,Math.PI*2,true);
      ctx.clip();
      const grA=grain(matA, ring.id*11, Math.ceil(oR*2), Math.ceil(oR*2));
      ctx.globalAlpha=0.4; ctx.drawImage(grA,CX-oR,CY-oR,oR*2,oR*2);
      ctx.globalAlpha=1;
      ctx.restore();
    }

    else if (ring.type === "checker") {
      const { matA, matB, bw=4, bh=2 } = ring;
      const img = ctx.createImageData(SZ,SZ); const d=img.data;
      const COLS=512, ROWS=Math.max(2, Math.round(ring.widthMm/0.5));
      for(let py=0;py<SZ;py++) for(let px=0;px<SZ;px++){
        const dx=(px-CX)/MM, dy=(py-CY)/MM;
        const dist=Math.sqrt(dx*dx+dy*dy);
        if(dist<iR/MM||dist>oR/MM) continue;
        const ang=((Math.atan2(dy,dx)+Math.PI*2.5)%(Math.PI*2))/(Math.PI*2);
        const col=Math.floor(ang*COLS);
        const row=Math.floor((dist-iR/MM)/(oR/MM-iR/MM)*ROWS);
        const bC=Math.floor(col/bw), bR=Math.floor(row/bh);
        const wood=W((bC+bR)%2===0?matA:matB);
        const r8=parseInt(wood.base.slice(1,3),16);
        const g8=parseInt(wood.base.slice(3,5),16);
        const b8=parseInt(wood.base.slice(5,7),16);
        const i=(py*SZ+px)*4;
        d[i]=r8;d[i+1]=g8;d[i+2]=b8;d[i+3]=255;
      }
      ctx.putImageData(img,0,0);
      ctx.save();
      ctx.beginPath();
      ctx.arc(CX,CY,oR,0,Math.PI*2);
      ctx.arc(CX,CY,iR,0,Math.PI*2,true);
      ctx.clip();
      const grA=grain(matA,ring.id*13,Math.ceil(oR*2),Math.ceil(oR*2));
      ctx.globalAlpha=0.45; ctx.drawImage(grA,CX-oR,CY-oR,oR*2,oR*2);
      ctx.globalAlpha=1;
      ctx.restore();
    }

    else if (ring.type === "hyp") {
      const { N, gap=0.96, thick, wave, skew, drift, chaos, dist="ab", matA, matB, matC, showOut } = ring;
      const aStep = Math.PI*2/N;
      const tH = (oR-iR)*gap;
      const tW = midR*aStep*gap;
      const matCycle=[matA,matB,matC??"ebony",matA];

      // First: flood-fill ring with bg (matC = ground)
      ctx.save();
      ctx.beginPath();
      ctx.arc(CX,CY,oR,0,Math.PI*2);
      ctx.arc(CX,CY,iR,0,Math.PI*2,true);
      ctx.clip();
      const bgWood = W(matC??"ebony");
      ctx.fillStyle = bgWood.base; ctx.fill();
      const grBg=grain(matC??"ebony",ring.id*3+1,Math.ceil(oR*2),Math.ceil(oR*2));
      ctx.globalAlpha=0.5; ctx.drawImage(grBg,CX-oR,CY-oR,oR*2,oR*2);
      ctx.globalAlpha=1;
      ctx.restore();

      // Then stamp tiles
      for(let i=0;i<N;i++){
        const midAng=(i+0.5)*aStep - Math.PI/2;
        const tcx=CX+Math.cos(midAng)*midR;
        const tcy=CY+Math.sin(midAng)*midR;

        let wid=matA;
        if(dist==="ab")  wid=matCycle[i%2];
        else if(dist==="abc") wid=matCycle[i%3];
        else if(dist==="abcd")wid=matCycle[i%4];
        else if(dist==="wave") wid=Math.sin(i/N*Math.PI*4)>0?matA:matB;

        const wood=W(wid);
        const p={thick,wave,skew,drift,chaos};

        ctx.save();
        ctx.translate(tcx,tcy);
        ctx.rotate(midAng+Math.PI/2);

        // Clip tile to annular band (prevent overflow beyond ring)
        ctx.save();
        ctx.translate(-tcx,-tcy);
        ctx.beginPath();
        ctx.arc(CX,CY,oR,0,Math.PI*2);
        ctx.arc(CX,CY,iR,0,Math.PI*2,true);
        ctx.clip();
        ctx.translate(tcx,tcy);

        // Draw tile shape
        ctx.beginPath();
        hypDraw(ctx,tW,tH,p,i);
        ctx.save(); ctx.clip();
        ctx.fillStyle=wood.base;
        ctx.fillRect(-tW*1.5,-tH*1.5,tW*3,tH*3);
        // Grain overlay
        const grT=grain(wid, ring.id*100+i%8, Math.ceil(tW*3)+2, Math.ceil(tH*3)+2);
        ctx.globalAlpha=0.55;
        ctx.drawImage(grT,-tW*1.5,-tH*1.5,tW*3,tH*3);
        ctx.globalAlpha=1;
        ctx.restore();

        // Edge shading — subtle 3D lift
        ctx.beginPath();
        hypDraw(ctx,tW,tH,p,i);
        const eg=ctx.createLinearGradient(-tW/2,-tH/2,tW/2,tH/2);
        eg.addColorStop(0,`rgba(255,230,160,0.12)`);
        eg.addColorStop(0.4,"rgba(0,0,0,0)");
        eg.addColorStop(1,`rgba(0,0,0,0.18)`);
        ctx.fillStyle=eg; ctx.fill();

        if(showOut){
          ctx.beginPath();
          hypDraw(ctx,tW,tH,p,i);
          ctx.strokeStyle="rgba(0,0,0,0.55)"; ctx.lineWidth=0.7; ctx.stroke();
        }

        ctx.restore(); // annular clip
        ctx.restore(); // tile transform
      }
    }

    // Ring separator lines
    [iR,oR].forEach(r=>{
      ctx.beginPath(); ctx.arc(CX,CY,r,0,Math.PI*2);
      ctx.strokeStyle="rgba(200,150,40,0.15)"; ctx.lineWidth=0.7;
      ctx.setLineDash([2,4]); ctx.stroke(); ctx.setLineDash([]);
    });
  });

  // Soundhole
  ctx.beginPath(); ctx.arc(CX,CY,innerR*MM,0,Math.PI*2);
  const sf=ctx.createRadialGradient(CX,CY-8,2,CX,CY,innerR*MM);
  sf.addColorStop(0,"#1a1208"); sf.addColorStop(1,"#040202");
  ctx.fillStyle=sf; ctx.fill();
  // Soundhole rim glow
  ctx.beginPath(); ctx.arc(CX,CY,innerR*MM,0,Math.PI*2);
  ctx.strokeStyle="rgba(200,155,45,0.5)"; ctx.lineWidth=1.3; ctx.stroke();

  // Outer edge glow
  ctx.beginPath(); ctx.arc(CX,CY,outerR*MM,0,Math.PI*2);
  ctx.strokeStyle="rgba(200,155,45,0.2)"; ctx.lineWidth=2.0; ctx.stroke();

  // Ambient vignette over entire canvas
  const vig=ctx.createRadialGradient(CX,CY,outerR*MM*0.5,CX,CY,SZ*0.7);
  vig.addColorStop(0,"transparent"); vig.addColorStop(1,"rgba(2,1,0,0.55)");
  ctx.fillStyle=vig; ctx.fillRect(0,0,SZ,SZ);
}

// ═══════════════════════════════════════════════════════════
// SLIDER / PICKER HELPERS
// ═══════════════════════════════════════════════════════════
function Sl({label,val,set,min,max,step=1,note=""}) {
  const fmt=v=>step<0.05?v.toFixed(2):step<0.5?v.toFixed(1):Math.round(v);
  return (
    <div style={{marginBottom:"7px"}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:"1px"}}>
        <span style={{fontSize:"8px",color:"#4a3010"}}>{label}</span>
        <span style={{fontSize:"9px",color:"#e8c87a"}}>{fmt(val)}{note?` ${note}`:""}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val}
        onChange={e=>set(Number(e.target.value))} style={{width:"100%",accentColor:"#c9a96e"}}/>
    </div>
  );
}

function MatPick({label,val,set}) {
  const wood=W(val);
  return (
    <div style={{display:"flex",alignItems:"center",gap:"6px",marginBottom:"5px"}}>
      <div style={{width:"20px",height:"14px",borderRadius:"2px",flexShrink:0,
        background:wood.base,border:"1px solid #2e2010",overflow:"hidden",position:"relative"}}>
        {wood.irid&&<div style={{position:"absolute",inset:0,background:"linear-gradient(45deg,#e8f0f844,#c0f8e044,#f0d08044)"}}/>}
      </div>
      <span style={{fontSize:"8px",color:"#4a3010",minWidth:"68px"}}>{label}</span>
      <select value={val} onChange={e=>set(e.target.value)}
        style={{flex:1,background:"#0a0704",border:"1px solid #2e2010",borderRadius:"2px",
          color:"#c9a96e",fontSize:"8px",padding:"2px 4px",fontFamily:"'Courier New',monospace"}}>
        {WOODS.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}
      </select>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// RING EDITOR (focused on hyp wave ring)
// ═══════════════════════════════════════════════════════════
function HypEditor({ring, upd}) {
  const u=patch=>upd(patch);
  return (
    <div style={{display:"flex",flexDirection:"column",gap:"7px"}}>
      <MatPick label="Strand A"  val={ring.matA} set={v=>u({matA:v})}/>
      <MatPick label="Strand B"  val={ring.matB} set={v=>u({matB:v})}/>
      <MatPick label="Ground"    val={ring.matC??"ebony"} set={v=>u({matC:v})}/>
      <div style={{borderTop:"1px solid #1a1008",paddingTop:"8px"}}>
        <Sl label="N tiles"      val={ring.N}     set={v=>u({N:v})}     min={8}  max={48} step={2}/>
        <Sl label="Band width"   val={ring.widthMm} set={v=>u({widthMm:v})} min={4} max={20} step={0.5} note="mm"/>
        <Sl label="Gap / fill"   val={ring.gap}   set={v=>u({gap:v})}   min={0.5}max={1.2} step={0.01}/>
        <Sl label="Thickness"    val={ring.thick} set={v=>u({thick:v})} min={0.1} max={0.95} step={0.01}/>
        <Sl label="Wave amp"     val={ring.wave}  set={v=>u({wave:v})}  min={0}  max={1.2} step={0.01}/>
        <Sl label="Skew"         val={ring.skew}  set={v=>u({skew:v})}  min={0}  max={1}   step={0.01}/>
        <Sl label="Hyp drift"    val={ring.drift} set={v=>u({drift:v})} min={0}  max={2.0} step={0.02}/>
        <Sl label="Chaos"        val={ring.chaos} set={v=>u({chaos:v})} min={0}  max={1.0} step={0.01}/>
      </div>
      <div style={{borderTop:"1px solid #1a1008",paddingTop:"7px"}}>
        <div style={{fontSize:"7px",color:"#2e1a08",marginBottom:"4px",letterSpacing:"1px"}}>DISTRIBUTION</div>
        {[["ab","A · B"],["abc","A · B · C"],["abcd","A B C D"],["wave","Wave A↔B"]].map(([k,l])=>(
          <div key={k} onClick={()=>u({dist:k})} style={{
            padding:"3px 7px",marginBottom:"3px",cursor:"pointer",fontSize:"8px",borderRadius:"2px",
            border:ring.dist===k?"1px solid #c9a96e":"1px solid #1e1208",
            background:ring.dist===k?"#130f08":"transparent",
            color:ring.dist===k?"#e8c87a":"#3a2010"}}>{l}</div>
        ))}
      </div>
      <div onClick={()=>u({showOut:!ring.showOut})} style={{
        padding:"4px 8px",cursor:"pointer",fontSize:"8px",borderRadius:"2px",marginTop:"2px",
        border:ring.showOut?"1px solid #c9a96e":"1px solid #1e1208",
        background:ring.showOut?"#130f08":"transparent",
        color:ring.showOut?"#e8c87a":"#3a2010"}}>
        Tile outlines {ring.showOut?"ON":"OFF"}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════
export default function HyperbolicRosette() {
  const [preset, setPreset] = useState("classic");
  const [rings, setRings]   = useState(()=>PRESETS.classic.rings.map(r=>({...r})));
  const [innerR, setInnerR] = useState(PRESETS.classic.innerR);
  const [selId, setSelId]   = useState(()=>PRESETS.classic.rings[3].id);
  const [spin, setSpin]     = useState(false);
  const [angle, setAngle]   = useState(0);
  const canvasRef = useRef(null);
  const timer     = useRef(null);
  const animRef   = useRef(null);

  const sel      = rings.find(r=>r.id===selId);
  const hypRings = rings.filter(r=>r.type==="hyp");
  const totalW   = rings.reduce((s,r)=>s+r.widthMm,0);

  const updRing = (id,patch) => setRings(rs=>rs.map(r=>r.id===id?{...r,...patch}:r));
  const updSel  = patch => sel && updRing(sel.id, patch);

  useEffect(()=>{
    clearTimeout(timer.current);
    timer.current=setTimeout(()=>renderRosette(canvasRef.current, rings, innerR),55);
    return()=>clearTimeout(timer.current);
  },[rings,innerR]);

  // Slow spin animation
  useEffect(()=>{
    if(spin){
      let a=angle;
      const step=()=>{
        a+=0.003; setAngle(a);
        if(canvasRef.current){
          const c=canvasRef.current,ctx=c.getContext("2d");
          ctx.save(); ctx.translate(SZ/2,SZ/2); ctx.rotate(a);
          ctx.translate(-SZ/2,-SZ/2);
          renderRosette(c,rings,innerR);
          ctx.restore();
        }
        animRef.current=requestAnimationFrame(step);
      };
      animRef.current=requestAnimationFrame(step);
    } else {
      cancelAnimationFrame(animRef.current);
    }
    return()=>cancelAnimationFrame(animRef.current);
  },[spin]);

  const loadPreset = key => {
    const pr=PRESETS[key]; if(!pr) return;
    const rs=pr.rings.map(r=>({...r,id:uid++}));
    setRings(rs); setInnerR(pr.innerR); setPreset(key);
    setSelId(rs.find(r=>r.type==="hyp")?.id ?? rs[3]?.id);
  };

  return (
    <div style={{height:"100vh",background:"#070503",fontFamily:"'Courier New',monospace",
      color:"#c9a96e",display:"flex",flexDirection:"column",overflow:"hidden"}}>

      {/* HEADER */}
      <div style={{padding:"9px 18px",borderBottom:"1px solid #140c04",
        display:"flex",justifyContent:"space-between",alignItems:"center",flexShrink:0}}>
        <div>
          <div style={{fontSize:"7px",letterSpacing:"5px",color:"#201208"}}>THE PRODUCTION SHOP · INLAY MODULE</div>
          <div style={{fontSize:"20px",fontWeight:"bold",color:"#e8c87a",letterSpacing:"3px",marginTop:"1px"}}>
            Hyperbolic Rosette
          </div>
        </div>
        <div style={{display:"flex",gap:"5px",alignItems:"center"}}>
          {Object.entries(PRESETS).map(([k,pr])=>(
            <div key={k} onClick={()=>loadPreset(k)} style={{
              padding:"4px 10px",cursor:"pointer",fontSize:"7px",letterSpacing:"1px",borderRadius:"2px",
              border:preset===k?"1px solid #c9a96e":"1px solid #1e1208",
              background:preset===k?"#130f08":"transparent",
              color:preset===k?"#e8c87a":"#3a2010"}}>
              {pr.name}
            </div>
          ))}
          <div onClick={()=>setSpin(s=>!s)} style={{
            padding:"4px 10px",cursor:"pointer",fontSize:"7px",borderRadius:"2px",marginLeft:"6px",
            border:spin?"1px solid #a07030":"1px solid #1e1208",
            background:spin?"#0f0c06":"transparent",
            color:spin?"#c9a050":"#3a2010"}}>
            {spin?"⏸ Stop":"▷ Spin"}
          </div>
        </div>
      </div>

      <div style={{flex:1,display:"flex",overflow:"hidden"}}>

        {/* ══ LEFT: RING STACK ══ */}
        <div style={{width:"200px",flexShrink:0,borderRight:"1px solid #140c04",
          display:"flex",flexDirection:"column",overflow:"hidden"}}>
          <div style={{padding:"8px 10px 3px",fontSize:"7px",letterSpacing:"3px",color:"#201208"}}>
            ← INSIDE → OUTSIDE →
          </div>
          <div style={{flex:1,overflowY:"auto",padding:"4px 8px"}}>
            {rings.map((ring,idx)=>{
              const isSel=ring.id===selId;
              const accentCol = ring.type==="hyp"?"#c9a050" : "#c9a96e";
              return (
                <div key={ring.id} onClick={()=>setSelId(ring.id)}
                  style={{marginBottom:"3px",padding:"6px 8px",cursor:"pointer",borderRadius:"3px",
                    background:isSel?"#120e07":"transparent",
                    border:isSel?`1px solid ${accentCol}`:"1px solid #180e04",
                    transition:"all .07s"}}>
                  <div style={{display:"flex",alignItems:"center",gap:"5px"}}>
                    {/* swatch */}
                    {ring.type==="solid" && (
                      <div style={{width:"10px",height:"10px",borderRadius:"1px",flexShrink:0,
                        background:W(ring.mat).base,border:"1px solid #1e1208"}}/>
                    )}
                    {ring.type==="hyp" && (
                      <div style={{display:"flex",gap:"1px",flexShrink:0}}>
                        {[ring.matA,ring.matB,ring.matC??"ebony"].map((m,mi)=>(
                          <div key={mi} style={{width:"7px",height:"10px",borderRadius:"1px",
                            background:W(m).base,border:"1px solid #1e1208"}}/>
                        ))}
                      </div>
                    )}
                    {(ring.type==="checker"||ring.type==="stripe") && (
                      <div style={{display:"flex",gap:"1px",flexShrink:0}}>
                        {[ring.matA,ring.matB].map((m,mi)=>(
                          <div key={mi} style={{width:"7px",height:"10px",borderRadius:"1px",
                            background:W(m).base,border:"1px solid #1e1208"}}/>
                        ))}
                      </div>
                    )}
                    <div style={{flex:1,minWidth:0}}>
                      <div style={{fontSize:"9px",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap",
                        color:ring.type==="hyp"?(isSel?"#e8c050":"#a07828"):(isSel?"#e8c87a":"#6a4c20")}}>
                        {ring.label}
                      </div>
                      <div style={{fontSize:"7px",color:"#2a1808"}}>
                        {ring.type} · {ring.widthMm.toFixed(1)}mm
                      </div>
                    </div>
                  </div>
                  {/* width bar */}
                  <div style={{marginTop:"4px",height:"2px",background:"#180e04",borderRadius:"1px"}}>
                    <div style={{width:`${Math.min(ring.widthMm/totalW*100,100)}%`,height:"100%",
                      borderRadius:"1px",background:ring.type==="hyp"?"#c9a050":isSel?"#c9a96e":"#2a1808"}}/>
                  </div>
                </div>
              );
            })}
          </div>
          {/* Dimension summary */}
          <div style={{padding:"8px 10px",borderTop:"1px solid #140c04",fontSize:"7px",
            color:"#2a1808",lineHeight:2}}>
            ⌀{(innerR*2).toFixed(0)}mm soundhole<br/>
            <span style={{color:"#e8c87a"}}>{totalW.toFixed(1)}mm</span> band<br/>
            ⌀{((innerR+totalW)*2).toFixed(0)}mm outer
          </div>
        </div>

        {/* ══ CENTER: CANVAS ══ */}
        <div style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",
          justifyContent:"center",padding:"12px",gap:"10px",background:"#060402"}}>

          <canvas ref={canvasRef} width={SZ} height={SZ}
            onClick={e=>{
              const rect=canvasRef.current.getBoundingClientRect();
              const dx=(e.clientX-rect.left-SZ/2), dy=(e.clientY-rect.top-SZ/2);
              const distMM=Math.sqrt(dx*dx+dy*dy)/((SZ*0.46)/(innerR+totalW));
              let rr=innerR;
              for(const ring of rings){
                if(distMM>=rr&&distMM<rr+ring.widthMm){ setSelId(ring.id); break; }
                rr+=ring.widthMm;
              }
            }}
            style={{cursor:"crosshair",borderRadius:"50%",
              boxShadow:"0 0 60px rgba(180,130,30,0.07),0 0 120px rgba(0,0,0,0.95)"}}/>

          <div style={{fontSize:"7px",color:"#1a1006",letterSpacing:"2px"}}>
            CLICK A RING TO SELECT · {hypRings.length} HYPERBOLIC {hypRings.length===1?"BAND":"BANDS"}
          </div>

          {/* Preset description */}
          <div style={{fontSize:"7px",color:"#2e1a08",letterSpacing:"1px",textAlign:"center",
            maxWidth:"340px",lineHeight:1.9}}>
            {PRESETS[preset]?.desc}
          </div>
        </div>

        {/* ══ RIGHT: EDITOR ══ */}
        <div style={{width:"232px",flexShrink:0,borderLeft:"1px solid #140c04",
          overflowY:"auto",padding:"10px"}}>

          {sel ? <>
            {/* Ring label */}
            <div style={{marginBottom:"8px"}}>
              <div style={{fontSize:"7px",letterSpacing:"2px",color:"#2a1808",marginBottom:"3px"}}>RING LABEL</div>
              <input value={sel.label} onChange={e=>updSel({label:e.target.value})}
                style={{width:"100%",background:"#0a0704",border:"1px solid #2e2010",borderRadius:"2px",
                  padding:"4px 7px",color:"#e8c87a",fontSize:"9px",fontFamily:"'Courier New',monospace",
                  boxSizing:"border-box"}}/>
            </div>

            {sel.type==="solid" && (
              <div style={{padding:"8px",background:"#0a0704",border:"1px solid #1a1008",borderRadius:"3px"}}>
                <div style={{fontSize:"7px",letterSpacing:"2px",color:"#2a1808",marginBottom:"6px"}}>SOLID RING</div>
                <MatPick label="Material" val={sel.mat} set={v=>updSel({mat:v})}/>
                <Sl label="Width" val={sel.widthMm} set={v=>updSel({widthMm:v})} min={0.3} max={8} step={0.1} note="mm"/>
              </div>
            )}
            {(sel.type==="checker"||sel.type==="stripe") && (
              <div style={{padding:"8px",background:"#0a0704",border:"1px solid #1a1008",borderRadius:"3px"}}>
                <div style={{fontSize:"7px",letterSpacing:"2px",color:"#2a1808",marginBottom:"6px"}}>
                  {sel.type.toUpperCase()}
                </div>
                <MatPick label="Material A" val={sel.matA} set={v=>updSel({matA:v})}/>
                <MatPick label="Material B" val={sel.matB} set={v=>updSel({matB:v})}/>
                <Sl label="Width" val={sel.widthMm} set={v=>updSel({widthMm:v})} min={0.5} max={8} step={0.1} note="mm"/>
                <Sl label="Cell size" val={sel.bw??sel.sw??4} set={v=>updSel(sel.type==="checker"?{bw:v,bh:Math.ceil(v/2)}:{sw:v})} min={1} max={16}/>
              </div>
            )}
            {sel.type==="hyp" && (
              <div style={{padding:"8px",background:"#0a0704",border:"1px solid #c9a050",borderRadius:"3px",
                boxShadow:"0 0 12px rgba(200,160,40,0.06)"}}>
                <div style={{fontSize:"7px",letterSpacing:"2px",color:"#8a6820",marginBottom:"8px"}}>
                  ◈ HYPERBOLIC WAVE
                </div>
                <HypEditor ring={sel} upd={updSel}/>
              </div>
            )}

            {/* Tip box for hyp ring */}
            {sel.type==="hyp" && (
              <div style={{marginTop:"9px",padding:"8px",background:"#080503",
                border:"1px solid #1a1008",borderRadius:"3px",fontSize:"7px",
                color:"#2a1808",lineHeight:1.9}}>
                <span style={{color:"#6a4810"}}>Drift</span> = log accumulation — slow then steady.<br/>
                <span style={{color:"#6a4810"}}>Chaos</span> = sin(i·0.17) — almost-period of 37.<br/>
                At N=37 chaos nearly closes. N=36 or 38 never repeats.<br/>
                <span style={{color:"#6a4810"}}>Gap &gt; 1</span> = tiles overflow their cell — bleeding edge.
              </div>
            )}
          </> : (
            <div style={{fontSize:"8px",color:"#2a1808",padding:"20px 8px",textAlign:"center"}}>
              Click a ring to edit it
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
