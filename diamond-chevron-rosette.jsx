import { useState, useEffect, useRef } from "react";

// ═══════════════════════════════════════════════════════════
// MATERIALS
// ═══════════════════════════════════════════════════════════
const WOODS = [
  { id:"ebony",    name:"Ebony",          base:"#1a1008", grain:"#0d0804", hi:"#2a1c10" },
  { id:"maple",    name:"Maple",          base:"#f2e8c8", grain:"#c8a860", hi:"#fff8e8" },
  { id:"rosewood", name:"Rosewood",       base:"#4a1e10", grain:"#2e1008", hi:"#6a3020" },
  { id:"koa",      name:"Koa",            base:"#c87828", grain:"#804810", hi:"#e8a848" },
  { id:"walnut",   name:"Walnut",         base:"#5c3818", grain:"#382008", hi:"#7c5838" },
  { id:"cedar",    name:"Cedar",          base:"#c07040", grain:"#883020", hi:"#d89060" },
  { id:"spruce",   name:"Spruce",         base:"#e8d8a0", grain:"#b89840", hi:"#f8f0c0" },
  { id:"mahogany", name:"Mahogany",       base:"#7a3018", grain:"#4a1808", hi:"#9a5030" },
  { id:"ovangkol", name:"Ovangkol",       base:"#a87828", grain:"#685010", hi:"#c89838" },
  { id:"mop",      name:"Mother-of-Pearl",base:"#ddeef8", grain:"#a8ccec", hi:"#f0f8ff", irid:true },
  { id:"abalone",  name:"Abalone",        base:"#508868", grain:"#306848", hi:"#80b898", irid:true },
  { id:"bone",     name:"Bone",           base:"#f0e8d0", grain:"#c8b888", hi:"#fff8f0" },
];
const W = id => WOODS.find(w=>w.id===id) ?? WOODS[0];

// ═══════════════════════════════════════════════════════════
// GRAIN ENGINE
// ═══════════════════════════════════════════════════════════
function grainFill(ctx, wood, bw, bh, seed, dir="tangential") {
  let s = seed * 9301 + 49297;
  const rng = () => { s=(s*9301+49297)%233280; return s/233280; };
  if (wood.irid) {
    for(let i=0;i<6;i++){
      const gr=ctx.createRadialGradient((rng()-.5)*bw,(rng()-.5)*bh,0,(rng()-.5)*bw,(rng()-.5)*bh,bw*.8);
      const h=(seed*37+i*53)%360;
      gr.addColorStop(0,`hsla(${h},60%,82%,.42)`); gr.addColorStop(1,"transparent");
      ctx.fillStyle=gr; ctx.fillRect(-bw,-bh,bw*2,bh*2);
    }
    return;
  }
  const n = 14;
  for(let i=0;i<n;i++){
    ctx.beginPath();
    if(dir==="radial"){
      const x=(rng()-.5)*bw*2.4; ctx.moveTo(x,-bh); ctx.lineTo(x+rng()*3-1.5,bh);
    } else if(dir==="diagonal"){
      const t=(rng()-.5)*bw*3; ctx.moveTo(-bw,t-bw); ctx.lineTo(bw,t+bw);
    } else {
      const y=(rng()-.5)*bh*2.4; ctx.moveTo(-bw,y); ctx.lineTo(bw,y+rng()*3-1.5);
    }
    ctx.strokeStyle=rng()>.5?wood.grain:wood.hi;
    ctx.lineWidth=rng()*1.2+.2; ctx.globalAlpha=.2+rng()*.32; ctx.stroke();
  }
  ctx.globalAlpha=1;
}

// ═══════════════════════════════════════════════════════════
// SHAPE DRAW FUNCTIONS (ported from compositor)
// ═══════════════════════════════════════════════════════════
// S = square side (use tH for both axes so it's a proper diamond, not a flat lozenge)
function drawDiamond(ctx, S, _H, p, idx) {
  const hw  = S / 2;                                    // half-width = half-height
  const amp = hw * p.wave * 0.55;                       // wave shift, capped to ≤40% of hw
  const lx  = S * p.lean * 0.5;                        // lean scales with S not full W
  const bv  = S * p.bevel * 0.4;
  // clamp dy so top/bottom tips never blow past the annular clip
  const dy  = Math.max(-hw*.35, Math.min(hw*.35,
               amp * Math.sin((idx * 0.28 + p.density * 0.15) * Math.PI)));

  if (bv < 1.2) {
    // Clean sharp-tipped diamond — the canonical shape
    ctx.moveTo( lx,       -hw + dy);   // top tip
    ctx.lineTo( hw,         0 + dy);   // right tip
    ctx.lineTo( lx,        hw + dy);   // bottom tip
    ctx.lineTo(-hw,         0 + dy);   // left tip
  } else {
    // Beveled — chamfer all 4 tips by bv
    const N = 8;
    const edgeWave = (t, ti) => bv * 0.25 * Math.sin(t * Math.PI * 2 + ti * 1.3 + idx * 0.3);
    // Top tip
    ctx.moveTo(lx - bv*.5, -hw + bv*.5 + dy);
    ctx.lineTo(lx + bv*.5, -hw + bv*.5 + dy);
    // Top-right edge (wavy)
    for(let i=0;i<=N;i++){
      const t=i/N;
      ctx.lineTo(lx + t*(hw-lx), -hw + t*hw + edgeWave(t,0) + dy);
    }
    // Right tip
    ctx.lineTo(hw - bv*.5, -bv*.3 + dy);
    ctx.lineTo(hw - bv*.5,  bv*.3 + dy);
    // Bottom-right edge
    for(let i=0;i<=N;i++){
      const t=i/N;
      ctx.lineTo(hw - t*(hw-lx), t*hw + edgeWave(t,1) + dy);
    }
    // Bottom tip
    ctx.lineTo(lx + bv*.5, hw - bv*.5 + dy);
    ctx.lineTo(lx - bv*.5, hw - bv*.5 + dy);
    // Bottom-left edge
    for(let i=0;i<=N;i++){
      const t=i/N;
      ctx.lineTo(lx - t*(hw+lx), hw - t*hw + edgeWave(t,2) + dy);
    }
    // Left tip
    ctx.lineTo(-hw + bv*.5,  bv*.3 + dy);
    ctx.lineTo(-hw + bv*.5, -bv*.3 + dy);
    // Top-left edge
    for(let i=0;i<=N;i++){
      const t=i/N;
      ctx.lineTo(-hw + t*(hw+lx), -t*hw + edgeWave(t,3) + dy);
    }
  }
  ctx.closePath();
}

function drawChevron(ctx, W, H, p) {
  const n  = Math.max(1, Math.round(p.steps));
  const lx = W * p.lean;
  const sz = H / n;
  const hw = W/2 * p.depth;
  const r  = Math.min(sz,hw) * p.round;
  const rSteps=[];
  for(let i=0;i<n;i++){
    const y=-H/2+i*sz, x=(i%2===0?hw:-hw)+lx*(i/n-.5)*2;
    rSteps.push([x,y],[x,y+sz]);
  }
  const lSteps=rSteps.map(([x,y])=>[-x+lx*2,y]).reverse();
  if(r<1){
    ctx.moveTo(lx,-H/2);
    rSteps.forEach(([x,y])=>ctx.lineTo(x,y));
    ctx.lineTo(lx,H/2);
    lSteps.forEach(([x,y])=>ctx.lineTo(x,y));
  } else {
    const P=[[lx,-H/2],...rSteps,[lx,H/2],...lSteps];
    ctx.moveTo((P[0][0]+P[1][0])/2,(P[0][1]+P[1][1])/2);
    for(let i=1;i<P.length;i++) ctx.arcTo(P[i][0],P[i][1],P[(i+1)%P.length][0],P[(i+1)%P.length][1],r);
  }
  ctx.closePath();
}

// ═══════════════════════════════════════════════════════════
// RING TYPES
// ═══════════════════════════════════════════════════════════
let _uid=1; const uid=()=>_uid++;

const PRESETS = {
  dial_in: {
    name:"Dial-In (DiamWave)",
    desc:"Your exact dial-in settings — rosewood/ebony diamonds, checker friezes, radial grain",
    innerR:40.8,
    rings:[
      {id:uid(),label:"Inner Binding", type:"solid",   widthMm:0.8, mat:"ebony"},
      {id:uid(),label:"Maple Frieze",  type:"checker",  widthMm:3.2, matA:"ebony",    matB:"maple",    bw:3},
      {id:uid(),label:"Border",        type:"solid",   widthMm:0.5, mat:"ebony"},
      {id:uid(),label:"Diamond Wave",  type:"diamond",  widthMm:9.0,
        matA:"rosewood",matB:"ebony",matC:"maple", altMode:"ab",
        N:20, gap:0.88, density:2.8, wave:0.28, lean:0.18, bevel:0.22, grainDir:"radial", showOut:true},
      {id:uid(),label:"Border",        type:"solid",   widthMm:0.5, mat:"ebony"},
      {id:uid(),label:"Maple Frieze",  type:"checker",  widthMm:2.5, matA:"ebony",    matB:"maple",    bw:3},
      {id:uid(),label:"Outer Binding", type:"solid",   widthMm:0.8, mat:"ebony"},
    ]
  },
  chev3: {
    name:"Chevron 3-Step",
    desc:"N=16 pure interlocking zigzags — maple/rosewood on ebony, marching inward",
    innerR:40.8,
    rings:[
      {id:uid(),label:"Ebony Bind",   type:"solid",   widthMm:0.8, mat:"ebony"},
      {id:uid(),label:"Koa Stripe",   type:"stripe",  widthMm:2.0, matA:"koa",   matB:"ebony",  sw:5},
      {id:uid(),label:"Border",       type:"solid",   widthMm:0.5, mat:"ebony"},
      {id:uid(),label:"Stepped Chev", type:"chevron", widthMm:9.0,
        matA:"maple",matB:"rosewood",matC:"ebony", altMode:"ab",
        N:16, gap:0.92, steps:3, lean:0.0, round:0.0, depth:1.0, grainDir:"tangential", showOut:true},
      {id:uid(),label:"Border",       type:"solid",   widthMm:0.5, mat:"ebony"},
      {id:uid(),label:"Koa Stripe",   type:"stripe",  widthMm:2.0, matA:"koa",   matB:"ebony",  sw:5},
      {id:uid(),label:"Ebony Bind",   type:"solid",   widthMm:0.8, mat:"ebony"},
    ]
  },
  combined: {
    name:"Combined (Both Shapes)",
    desc:"Diamond wave outer, chevron inner — two hero bands with friezes between",
    innerR:40.8,
    rings:[
      {id:uid(),label:"Ebony Bind",   type:"solid",   widthMm:0.8, mat:"ebony"},
      {id:uid(),label:"Bone Stripe",  type:"stripe",  widthMm:1.5, matA:"bone",  matB:"ebony",  sw:4},
      {id:uid(),label:"Border",       type:"solid",   widthMm:0.4, mat:"ebony"},
      {id:uid(),label:"Chev 3-Step",  type:"chevron", widthMm:5.5,
        matA:"maple",matB:"rosewood",matC:"ebony", altMode:"ab",
        N:18, gap:0.90, steps:3, lean:0.08, round:0.04, depth:0.95, grainDir:"tangential", showOut:true},
      {id:uid(),label:"Border",       type:"solid",   widthMm:0.4, mat:"ebony"},
      {id:uid(),label:"Diamond Wave", type:"diamond", widthMm:7.5,
        matA:"koa",matB:"ebony",matC:"maple", altMode:"ab",
        N:22, gap:0.88, density:2.8, wave:0.24, lean:0.16, bevel:0.18, grainDir:"radial", showOut:false},
      {id:uid(),label:"Border",       type:"solid",   widthMm:0.4, mat:"ebony"},
      {id:uid(),label:"Bone Stripe",  type:"stripe",  widthMm:1.5, matA:"bone",  matB:"ebony",  sw:4},
      {id:uid(),label:"Outer Bind",   type:"solid",   widthMm:0.8, mat:"ebony"},
    ]
  },
  pearl: {
    name:"Pearl Diamond",
    desc:"MOP lozenges on ebony — bevel high, flow wave, diagonal grain for maximum shimmer",
    innerR:40.8,
    rings:[
      {id:uid(),label:"Ebony Bind",  type:"solid",   widthMm:1.0, mat:"ebony"},
      {id:uid(),label:"MOP Line",    type:"stripe",  widthMm:1.8, matA:"mop",  matB:"ebony",  sw:6},
      {id:uid(),label:"Border",      type:"solid",   widthMm:0.4, mat:"ebony"},
      {id:uid(),label:"Diam·Flow",   type:"diamond", widthMm:9.5,
        matA:"mop",matB:"abalone",matC:"ebony", altMode:"ab",
        N:24, gap:0.92, density:1.8, wave:0.38, lean:0.22, bevel:0.28, grainDir:"diagonal", showOut:false},
      {id:uid(),label:"Border",      type:"solid",   widthMm:0.4, mat:"ebony"},
      {id:uid(),label:"Abalone Line",type:"stripe",  widthMm:1.8, matA:"abalone",matB:"ebony",sw:6},
      {id:uid(),label:"Ebony Bind",  type:"solid",   widthMm:1.0, mat:"ebony"},
    ]
  },
  chev_lean: {
    name:"Chevron Lean (Koa)",
    desc:"2-step lean chevrons, rounded corners — feels like interlocking arrowheads in warm koa",
    innerR:40.8,
    rings:[
      {id:uid(),label:"Walnut Bind",  type:"solid",   widthMm:0.8, mat:"walnut"},
      {id:uid(),label:"Checker",      type:"checker", widthMm:2.8, matA:"walnut",matB:"maple",  bw:4},
      {id:uid(),label:"Border",       type:"solid",   widthMm:0.4, mat:"ebony"},
      {id:uid(),label:"Chev·Lean",    type:"chevron", widthMm:9.5,
        matA:"koa",matB:"maple",matC:"walnut", altMode:"abc",
        N:24, gap:0.88, steps:2, lean:0.22, round:0.10, depth:1.1, grainDir:"diagonal", showOut:true},
      {id:uid(),label:"Border",       type:"solid",   widthMm:0.4, mat:"ebony"},
      {id:uid(),label:"Checker",      type:"checker", widthMm:2.2, matA:"walnut",matB:"maple",  bw:4},
      {id:uid(),label:"Walnut Bind",  type:"solid",   widthMm:0.8, mat:"walnut"},
    ]
  },
};

// ═══════════════════════════════════════════════════════════
// CANVAS RENDERER
// ═══════════════════════════════════════════════════════════
const SZ=540; const CX=SZ/2, CY=SZ/2;

function renderRosette(canvas, rings, innerR) {
  if(!canvas) return;
  const ctx=canvas.getContext("2d");
  ctx.clearRect(0,0,SZ,SZ);
  const bg=ctx.createRadialGradient(CX,CY,0,CX,CY,SZ/2);
  bg.addColorStop(0,"#0f0a06"); bg.addColorStop(1,"#060402");
  ctx.fillStyle=bg; ctx.fillRect(0,0,SZ,SZ);

  const totalW=rings.reduce((s,r)=>s+r.widthMm,0);
  const outerR=innerR+totalW;
  const MM=(SZ*.46)/outerR;

  let rCur=innerR;
  const bounds=rings.map(ring=>{
    const iR=rCur*MM, oR=(rCur+ring.widthMm)*MM;
    rCur+=ring.widthMm;
    return {iR,oR,midR:(iR+oR)/2,ring};
  });

  bounds.forEach(({iR,oR,midR,ring})=>{

    // ── SOLID ────────────────────────────────────────────────
    if(ring.type==="solid"){
      ctx.save();
      ctx.beginPath();
      ctx.arc(CX,CY,oR,0,Math.PI*2);
      ctx.arc(CX,CY,iR,0,Math.PI*2,true);
      ctx.clip();
      const wood=W(ring.mat);
      ctx.fillStyle=wood.base; ctx.fill();
      // grain overlay
      ctx.save(); ctx.translate(CX,CY);
      grainFill(ctx,wood,oR*2,oR*2,ring.id*7,"tangential");
      ctx.globalAlpha=.45; ctx.restore();
      ctx.restore();
    }

    // ── STRIPE / CHECKER (pixel scanline) ───────────────────
    else if(ring.type==="stripe"||ring.type==="checker"){
      const {matA,matB,bw=4,sw=4}=ring;
      const COLS=512, ROWS=Math.max(2,Math.round(ring.widthMm/.5));
      const img=ctx.createImageData(SZ,SZ); const d=img.data;
      for(let py=0;py<SZ;py++) for(let px=0;px<SZ;px++){
        const dx=(px-CX)/MM, dy=(py-CY)/MM;
        const dist=Math.sqrt(dx*dx+dy*dy);
        if(dist<iR/MM||dist>oR/MM) continue;
        const ang=((Math.atan2(dy,dx)+Math.PI*2.5)%(Math.PI*2))/(Math.PI*2);
        const col=Math.floor(ang*COLS);
        let woodId;
        if(ring.type==="stripe"){ woodId=Math.floor(col/sw)%2===0?matA:matB; }
        else { const bR=Math.floor((dist-iR/MM)/(oR/MM-iR/MM)*ROWS/bw); woodId=(Math.floor(col/bw)+bR)%2===0?matA:matB; }
        const wood=W(woodId);
        const r8=parseInt(wood.base.slice(1,3),16), g8=parseInt(wood.base.slice(3,5),16), b8=parseInt(wood.base.slice(5,7),16);
        const ii=(py*SZ+px)*4; d[ii]=r8;d[ii+1]=g8;d[ii+2]=b8;d[ii+3]=255;
      }
      ctx.putImageData(img,0,0);
      ctx.save();
      ctx.beginPath(); ctx.arc(CX,CY,oR,0,Math.PI*2); ctx.arc(CX,CY,iR,0,Math.PI*2,true); ctx.clip();
      ctx.save(); ctx.translate(CX,CY);
      grainFill(ctx,W(matA),oR*2,oR*2,ring.id*11,"tangential");
      ctx.restore(); ctx.globalAlpha=.38; ctx.restore();
    }

    // ── DIAMOND WAVE ─────────────────────────────────────────
    else if(ring.type==="diamond"){
      const {N,gap=.88,density=2.8,wave=.22,lean=.18,bevel=.15,matA,matB,matC,altMode="ab",grainDir="radial",showOut}=ring;
      const aStep=Math.PI*2/N;
      const tH=(oR-iR)*gap;
      const tS=tH;                // square tile — diamond must be drawn on equal W×H
      const tW=midR*aStep*gap;    // circumferential slot (grain fill coverage only)
      const bgWood=W(matC??"ebony");
      const mats=[W(matA),W(matB),W(matC??"ebony")];

      // Flood ring with bg
      ctx.save();
      ctx.beginPath(); ctx.arc(CX,CY,oR,0,Math.PI*2); ctx.arc(CX,CY,iR,0,Math.PI*2,true); ctx.clip();
      ctx.fillStyle=bgWood.base; ctx.fill();
      ctx.save(); ctx.translate(CX,CY);
      grainFill(ctx,bgWood,oR*2,oR*2,ring.id*3,grainDir);
      ctx.globalAlpha=.4; ctx.restore();
      ctx.restore();

      // Tiles
      for(let i=0;i<N;i++){
        const midAng=(i+.5)*aStep-Math.PI/2;
        const tcx=CX+Math.cos(midAng)*midR, tcy=CY+Math.sin(midAng)*midR;
        const woodIdx=altMode==="ab"?i%2 : altMode==="abc"?i%3 : 0;
        const wood=mats[woodIdx]??mats[0];
        const p={density,wave,lean,bevel};

        ctx.save();
        ctx.translate(tcx,tcy); ctx.rotate(midAng+Math.PI/2);
        // Annular clip in tile-local space
        ctx.save();
        ctx.translate(-tcx,-tcy);
        ctx.beginPath(); ctx.arc(CX,CY,oR,0,Math.PI*2); ctx.arc(CX,CY,iR,0,Math.PI*2,true); ctx.clip();
        ctx.translate(tcx,tcy);

        ctx.beginPath();
        drawDiamond(ctx,tS,tS,p,i);
        ctx.save(); ctx.clip();
        ctx.fillStyle=wood.base; ctx.fillRect(-tS*1.5,-tS*1.5,tS*3,tS*3);
        grainFill(ctx,wood,tS*2,tS*2,i*17+ring.id,grainDir);
        // Facet light — top-left bright, bottom-right shadow
        const eg=ctx.createLinearGradient(-tS/2,-tS/2,tS/2,tS/2);
        eg.addColorStop(0,"rgba(255,235,170,.2)"); eg.addColorStop(.42,"rgba(0,0,0,0)"); eg.addColorStop(1,"rgba(0,0,0,.22)");
        ctx.fillStyle=eg; ctx.fillRect(-tS*1.5,-tS*1.5,tS*3,tS*3);
        ctx.restore();
        if(showOut){ ctx.beginPath(); drawDiamond(ctx,tS,tS,p,i); ctx.strokeStyle="rgba(0,0,0,.55)"; ctx.lineWidth=.7; ctx.stroke(); }
        ctx.restore(); // annular clip
        ctx.restore(); // tile transform
      }
    }

    // ── STEPPED CHEVRON ──────────────────────────────────────
    else if(ring.type==="chevron"){
      const {N,gap=.92,steps=3,lean=0,round:rnd=0,depth=1,matA,matB,matC,altMode="ab",grainDir="tangential",showOut}=ring;
      const aStep=Math.PI*2/N;
      const tH=(oR-iR)*gap, tW=midR*aStep*gap;
      const bgWood=W(matC??"ebony");
      const mats=[W(matA),W(matB),W(matC??"ebony")];

      // Bg flood
      ctx.save();
      ctx.beginPath(); ctx.arc(CX,CY,oR,0,Math.PI*2); ctx.arc(CX,CY,iR,0,Math.PI*2,true); ctx.clip();
      ctx.fillStyle=bgWood.base; ctx.fill();
      ctx.save(); ctx.translate(CX,CY);
      grainFill(ctx,bgWood,oR*2,oR*2,ring.id*5,grainDir);
      ctx.globalAlpha=.38; ctx.restore();
      ctx.restore();

      for(let i=0;i<N;i++){
        const midAng=(i+.5)*aStep-Math.PI/2;
        const tcx=CX+Math.cos(midAng)*midR, tcy=CY+Math.sin(midAng)*midR;
        const woodIdx=altMode==="ab"?i%2 : altMode==="abc"?i%3 : 0;
        const wood=mats[woodIdx]??mats[0];
        const p={steps,lean,round:rnd,depth};

        ctx.save();
        ctx.translate(tcx,tcy); ctx.rotate(midAng+Math.PI/2);

        // Annular clip
        ctx.save();
        ctx.translate(-tcx,-tcy);
        ctx.beginPath(); ctx.arc(CX,CY,oR,0,Math.PI*2); ctx.arc(CX,CY,iR,0,Math.PI*2,true); ctx.clip();
        ctx.translate(tcx,tcy);

        ctx.beginPath();
        drawChevron(ctx,tW,tH,p);
        ctx.save(); ctx.clip();
        ctx.fillStyle=wood.base; ctx.fillRect(-tW*1.5,-tH*1.5,tW*3,tH*3);
        grainFill(ctx,wood,tW*2,tH*2,i*19+ring.id,grainDir);
        // Step-edge light
        const eg=ctx.createLinearGradient(-tW/2,-tH/2,tW/2,tH/2);
        eg.addColorStop(0,"rgba(255,230,160,.12)"); eg.addColorStop(.5,"rgba(0,0,0,0)"); eg.addColorStop(1,"rgba(0,0,0,.18)");
        ctx.fillStyle=eg; ctx.fillRect(-tW*1.5,-tH*1.5,tW*3,tH*3);
        ctx.restore();
        if(showOut){ ctx.beginPath(); drawChevron(ctx,tW,tH,p); ctx.strokeStyle="rgba(0,0,0,.5)"; ctx.lineWidth=.7; ctx.stroke(); }
        ctx.restore();
        ctx.restore();
      }
    }

    // Ring guide lines
    [iR,oR].forEach(r=>{
      ctx.beginPath(); ctx.arc(CX,CY,r,0,Math.PI*2);
      ctx.strokeStyle="rgba(200,150,40,.13)"; ctx.lineWidth=.6;
      ctx.setLineDash([2,5]); ctx.stroke(); ctx.setLineDash([]);
    });
  });

  // Soundhole
  ctx.beginPath(); ctx.arc(CX,CY,innerR*MM,0,Math.PI*2);
  const sf=ctx.createRadialGradient(CX,CY-8,2,CX,CY,innerR*MM);
  sf.addColorStop(0,"#1a1208"); sf.addColorStop(1,"#040202");
  ctx.fillStyle=sf; ctx.fill();
  ctx.strokeStyle="rgba(200,155,45,.55)"; ctx.lineWidth=1.3; ctx.stroke();

  // Outer ring glow
  ctx.beginPath(); ctx.arc(CX,CY,outerR*MM,0,Math.PI*2);
  ctx.strokeStyle="rgba(200,155,45,.18)"; ctx.lineWidth=2; ctx.stroke();

  // Vignette
  const vig=ctx.createRadialGradient(CX,CY,outerR*MM*.5,CX,CY,SZ*.7);
  vig.addColorStop(0,"transparent"); vig.addColorStop(1,"rgba(2,1,0,.6)");
  ctx.fillStyle=vig; ctx.fillRect(0,0,SZ,SZ);
}

// ═══════════════════════════════════════════════════════════
// SLIDER
// ═══════════════════════════════════════════════════════════
function Sl({label,val,set,min,max,step=1,note=""}){
  const fmt=v=>step<.05?v.toFixed(2):step<.5?v.toFixed(1):Math.round(v);
  return(
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

function MatPick({label,val,set}){
  const wood=W(val);
  return(
    <div style={{display:"flex",alignItems:"center",gap:"6px",marginBottom:"5px"}}>
      <div style={{width:"20px",height:"14px",borderRadius:"2px",flexShrink:0,
        background:wood.base,border:"1px solid #2e2010",overflow:"hidden",position:"relative"}}>
        {wood.irid&&<div style={{position:"absolute",inset:0,background:"linear-gradient(45deg,#e8f0f844,#c0f8e044)"}}/>}
      </div>
      <span style={{fontSize:"8px",color:"#4a3010",minWidth:"60px"}}>{label}</span>
      <select value={val} onChange={e=>set(e.target.value)}
        style={{flex:1,background:"#0a0704",border:"1px solid #2e2010",borderRadius:"2px",
          color:"#c9a96e",fontSize:"8px",padding:"2px 4px",fontFamily:"'Courier New',monospace"}}>
        {WOODS.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}
      </select>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════
export default function DiamondChevronRosette(){
  const [presetKey,setPresetKey]=useState("dial_in");
  const [rings,setRings]=useState(()=>PRESETS.dial_in.rings.map(r=>({...r})));
  const [innerR,setInnerR]=useState(40.8);
  const [selId,setSelId]=useState(()=>PRESETS.dial_in.rings[3].id);
  const canvasRef=useRef(null);
  const timer=useRef(null);

  const sel=rings.find(r=>r.id===selId);
  const totalW=rings.reduce((s,r)=>s+r.widthMm,0);
  const updRing=(id,patch)=>setRings(rs=>rs.map(r=>r.id===id?{...r,...patch}:r));
  const updSel=patch=>sel&&updRing(sel.id,patch);

  useEffect(()=>{
    clearTimeout(timer.current);
    timer.current=setTimeout(()=>renderRosette(canvasRef.current,rings,innerR),60);
    return()=>clearTimeout(timer.current);
  },[rings,innerR]);

  const loadPreset=key=>{
    const pr=PRESETS[key]; if(!pr) return;
    const rs=pr.rings.map(r=>({...r,id:uid()}));
    setRings(rs); setInnerR(pr.innerR); setPresetKey(key);
    setSelId(rs.find(r=>r.type==="diamond"||r.type==="chevron")?.id??rs[3]?.id);
  };

  const heroColor = sel?.type==="diamond"?"#c9a050":sel?.type==="chevron"?"#88b868":"#c9a96e";

  return(
    <div style={{height:"100vh",background:"#070503",fontFamily:"'Courier New',monospace",
      color:"#c9a96e",display:"flex",flexDirection:"column",overflow:"hidden"}}>

      {/* HEADER */}
      <div style={{padding:"9px 18px",borderBottom:"1px solid #140c04",
        display:"flex",justifyContent:"space-between",alignItems:"center",flexShrink:0}}>
        <div>
          <div style={{fontSize:"7px",letterSpacing:"5px",color:"#201208"}}>THE PRODUCTION SHOP · INLAY MODULE</div>
          <div style={{fontSize:"20px",fontWeight:"bold",color:"#e8c87a",letterSpacing:"3px",marginTop:"1px"}}>
            Diamond · Chevron Rosette
          </div>
        </div>
        <div style={{display:"flex",gap:"4px",flexWrap:"wrap",justifyContent:"flex-end"}}>
          {Object.entries(PRESETS).map(([k,pr])=>(
            <div key={k} onClick={()=>loadPreset(k)} style={{
              padding:"4px 9px",cursor:"pointer",fontSize:"7px",letterSpacing:"1px",borderRadius:"2px",
              border:presetKey===k?"1px solid #c9a96e":"1px solid #1e1208",
              background:presetKey===k?"#130f08":"transparent",
              color:presetKey===k?"#e8c87a":"#3a2010"}}>{pr.name}</div>
          ))}
        </div>
      </div>

      <div style={{flex:1,display:"flex",overflow:"hidden"}}>

        {/* ══ LEFT: RING STACK ══ */}
        <div style={{width:"196px",flexShrink:0,borderRight:"1px solid #140c04",
          display:"flex",flexDirection:"column",overflow:"hidden"}}>
          <div style={{padding:"7px 10px 2px",fontSize:"7px",letterSpacing:"3px",color:"#1e1006"}}>
            ← INSIDE → OUTSIDE →
          </div>
          <div style={{flex:1,overflowY:"auto",padding:"3px 7px"}}>
            {rings.map(ring=>{
              const isSel=ring.id===selId;
              const accent=ring.type==="diamond"?"#c9a050":ring.type==="chevron"?"#88b868":"#c9a96e";
              const swatches={
                solid:[ring.mat],
                stripe:[ring.matA,ring.matB],
                checker:[ring.matA,ring.matB],
                diamond:[ring.matA,ring.matB,ring.matC??"ebony"],
                chevron:[ring.matA,ring.matB,ring.matC??"ebony"],
              }[ring.type]??[ring.mat??"ebony"];
              return(
                <div key={ring.id} onClick={()=>setSelId(ring.id)}
                  style={{marginBottom:"3px",padding:"5px 7px",cursor:"pointer",borderRadius:"3px",
                    background:isSel?"#120e07":"transparent",
                    border:isSel?`1px solid ${accent}`:"1px solid #180e04",transition:"all .07s"}}>
                  <div style={{display:"flex",alignItems:"center",gap:"5px"}}>
                    <div style={{display:"flex",gap:"1px",flexShrink:0}}>
                      {swatches.map((m,mi)=>(
                        <div key={mi} style={{width:"7px",height:"10px",borderRadius:"1px",
                          background:W(m).base,border:"1px solid #1e1208"}}/>
                      ))}
                    </div>
                    <div style={{flex:1,minWidth:0}}>
                      <div style={{fontSize:"9px",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap",
                        color:isSel?accent:ring.type==="diamond"?"#8a6820":ring.type==="chevron"?"#508040":"#5a3e18"}}>
                        {ring.label}
                      </div>
                      <div style={{fontSize:"7px",color:"#2a1808"}}>{ring.type} · {ring.widthMm.toFixed(1)}mm</div>
                    </div>
                  </div>
                  <div style={{marginTop:"3px",height:"2px",background:"#180e04",borderRadius:"1px"}}>
                    <div style={{width:`${Math.min(ring.widthMm/totalW*100,100)}%`,height:"100%",
                      borderRadius:"1px",background:isSel?accent:"#2a1808"}}/>
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{padding:"7px 10px",borderTop:"1px solid #140c04",fontSize:"7px",
            color:"#2a1808",lineHeight:2}}>
            ⌀{(innerR*2).toFixed(0)}mm soundhole<br/>
            <span style={{color:"#e8c87a"}}>{totalW.toFixed(1)}mm</span> band<br/>
            ⌀{((innerR+totalW)*2).toFixed(0)}mm outer
          </div>
        </div>

        {/* ══ CENTER ══ */}
        <div style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",
          justifyContent:"center",padding:"12px",gap:"10px",background:"#060402"}}>

          <canvas ref={canvasRef} width={SZ} height={SZ}
            onClick={e=>{
              const rect=canvasRef.current.getBoundingClientRect();
              const dx=e.clientX-rect.left-SZ/2, dy=e.clientY-rect.top-SZ/2;
              const distMM=Math.sqrt(dx*dx+dy*dy)/((SZ*.46)/(innerR+totalW));
              let rr=innerR;
              for(const ring of rings){ if(distMM>=rr&&distMM<rr+ring.widthMm){setSelId(ring.id);break;} rr+=ring.widthMm; }
            }}
            style={{cursor:"crosshair",borderRadius:"50%",
              boxShadow:"0 0 60px rgba(180,130,30,.06),0 0 120px rgba(0,0,0,.95)"}}/>

          <div style={{fontSize:"7px",color:"#1a1006",letterSpacing:"2px"}}>
            CLICK RING TO SELECT · ◈ DIAMOND WAVE · ◇ STEPPED CHEVRON
          </div>
          <div style={{fontSize:"7px",color:"#281808",textAlign:"center",maxWidth:"380px",lineHeight:1.9}}>
            {PRESETS[presetKey]?.desc}
          </div>
        </div>

        {/* ══ RIGHT: EDITOR ══ */}
        <div style={{width:"228px",flexShrink:0,borderLeft:"1px solid #140c04",overflowY:"auto",padding:"10px"}}>
          {sel?(
            <>
              <div style={{marginBottom:"8px"}}>
                <div style={{fontSize:"7px",letterSpacing:"2px",color:"#2a1808",marginBottom:"3px"}}>RING LABEL</div>
                <input value={sel.label} onChange={e=>updSel({label:e.target.value})}
                  style={{width:"100%",background:"#0a0704",border:"1px solid #2e2010",borderRadius:"2px",
                    padding:"4px 7px",color:"#e8c87a",fontSize:"9px",fontFamily:"'Courier New',monospace",boxSizing:"border-box"}}/>
              </div>

              {sel.type==="solid"&&(
                <div style={{padding:"8px",background:"#0a0704",border:"1px solid #1a1008",borderRadius:"3px"}}>
                  <div style={{fontSize:"7px",letterSpacing:"2px",color:"#2a1808",marginBottom:"6px"}}>SOLID BINDING</div>
                  <MatPick label="Material" val={sel.mat} set={v=>updSel({mat:v})}/>
                  <Sl label="Width" val={sel.widthMm} set={v=>updSel({widthMm:v})} min={.3} max={5} step={.1} note="mm"/>
                </div>
              )}

              {(sel.type==="stripe"||sel.type==="checker")&&(
                <div style={{padding:"8px",background:"#0a0704",border:"1px solid #1a1008",borderRadius:"3px"}}>
                  <div style={{fontSize:"7px",letterSpacing:"2px",color:"#2a1808",marginBottom:"6px"}}>{sel.type.toUpperCase()}</div>
                  <MatPick label="Material A" val={sel.matA} set={v=>updSel({matA:v})}/>
                  <MatPick label="Material B" val={sel.matB} set={v=>updSel({matB:v})}/>
                  <Sl label="Width" val={sel.widthMm} set={v=>updSel({widthMm:v})} min={.5} max={6} step={.1} note="mm"/>
                  <Sl label="Cell size" val={sel.bw??sel.sw??4} set={v=>updSel(sel.type==="checker"?{bw:v}:{sw:v})} min={1} max={14}/>
                </div>
              )}

              {sel.type==="diamond"&&(
                <div style={{padding:"8px",background:"#0a0704",border:`1px solid #c9a050`,borderRadius:"3px",
                  boxShadow:"0 0 10px rgba(200,160,40,.05)"}}>
                  <div style={{fontSize:"7px",letterSpacing:"2px",color:"#8a6820",marginBottom:"8px"}}>◈ DIAMOND WAVE</div>
                  <MatPick label="Tile A"     val={sel.matA} set={v=>updSel({matA:v})}/>
                  <MatPick label="Tile B"     val={sel.matB} set={v=>updSel({matB:v})}/>
                  <MatPick label="Ground"     val={sel.matC??"ebony"} set={v=>updSel({matC:v})}/>
                  <div style={{borderTop:"1px solid #1a1008",paddingTop:"8px",marginTop:"6px"}}>
                    <Sl label="N tiles"  val={sel.N}       set={v=>updSel({N:v})}       min={8}  max={36} step={2}/>
                    <Sl label="Width"    val={sel.widthMm} set={v=>updSel({widthMm:v})} min={4}  max={18} step={.5} note="mm"/>
                    <Sl label="Gap"      val={sel.gap}     set={v=>updSel({gap:v})}     min={.5} max={1.1} step={.01}/>
                    <Sl label="Density"  val={sel.density} set={v=>updSel({density:v})} min={1}  max={6}  step={.2}/>
                    <Sl label="Wave amp" val={sel.wave}    set={v=>updSel({wave:v})}    min={0}  max={.45} step={.01}/>
                    <Sl label="Lean"     val={sel.lean}    set={v=>updSel({lean:v})}    min={-.4}max={.4}  step={.01}/>
                    <Sl label="Bevel"    val={sel.bevel}   set={v=>updSel({bevel:v})}   min={0}  max={.35} step={.01}/>
                    <div style={{display:"flex",gap:"3px",marginTop:"5px"}}>
                      {[["ab","A·B"],["abc","A·B·C"],["solid","All A"]].map(([k,l])=>(
                        <div key={k} onClick={()=>updSel({altMode:k})} style={{
                          flex:1,padding:"3px 4px",cursor:"pointer",fontSize:"7px",textAlign:"center",
                          border:sel.altMode===k?"1px solid #c9a050":"1px solid #1e1208",
                          background:sel.altMode===k?"#130f08":"transparent",
                          color:sel.altMode===k?"#c9a050":"#3a2010",borderRadius:"2px"}}>{l}</div>
                      ))}
                    </div>
                    <div style={{display:"flex",gap:"3px",marginTop:"4px"}}>
                      {[["tangential","Tang."],["radial","Radial"],["diagonal","Diag."]].map(([k,l])=>(
                        <div key={k} onClick={()=>updSel({grainDir:k})} style={{
                          flex:1,padding:"3px 4px",cursor:"pointer",fontSize:"7px",textAlign:"center",
                          border:sel.grainDir===k?"1px solid #c9a050":"1px solid #1e1208",
                          background:sel.grainDir===k?"#130f08":"transparent",
                          color:sel.grainDir===k?"#c9a050":"#3a2010",borderRadius:"2px"}}>{l}</div>
                      ))}
                    </div>
                    <div onClick={()=>updSel({showOut:!sel.showOut})} style={{
                      marginTop:"5px",padding:"3px 8px",cursor:"pointer",fontSize:"8px",borderRadius:"2px",
                      border:sel.showOut?"1px solid #c9a050":"1px solid #1e1208",
                      color:sel.showOut?"#c9a050":"#3a2010",background:sel.showOut?"#130f08":"transparent"}}>
                      Outlines {sel.showOut?"ON":"OFF"}
                    </div>
                  </div>
                </div>
              )}

              {sel.type==="chevron"&&(
                <div style={{padding:"8px",background:"#0a0704",border:"1px solid #88b868",borderRadius:"3px",
                  boxShadow:"0 0 10px rgba(136,184,104,.04)"}}>
                  <div style={{fontSize:"7px",letterSpacing:"2px",color:"#508040",marginBottom:"8px"}}>◇ STEPPED CHEVRON</div>
                  <MatPick label="Tile A"  val={sel.matA} set={v=>updSel({matA:v})}/>
                  <MatPick label="Tile B"  val={sel.matB} set={v=>updSel({matB:v})}/>
                  <MatPick label="Ground"  val={sel.matC??"ebony"} set={v=>updSel({matC:v})}/>
                  <div style={{borderTop:"1px solid #1a1008",paddingTop:"8px",marginTop:"6px"}}>
                    <Sl label="N tiles" val={sel.N}       set={v=>updSel({N:v})}       min={8}  max={36} step={2}/>
                    <Sl label="Width"   val={sel.widthMm} set={v=>updSel({widthMm:v})} min={4}  max={18} step={.5} note="mm"/>
                    <Sl label="Gap"     val={sel.gap}     set={v=>updSel({gap:v})}     min={.5} max={1.1} step={.01}/>
                    <Sl label="Steps"   val={sel.steps}   set={v=>updSel({steps:v})}   min={1}  max={6}  step={.5}/>
                    <Sl label="Lean"    val={sel.lean}    set={v=>updSel({lean:v})}    min={-.4}max={.4}  step={.01}/>
                    <Sl label="Corner R"val={sel.round}   set={v=>updSel({round:v})}   min={0}  max={.25} step={.005}/>
                    <Sl label="Depth"   val={sel.depth}   set={v=>updSel({depth:v})}   min={.3} max={1.2} step={.01}/>
                    <div style={{display:"flex",gap:"3px",marginTop:"5px"}}>
                      {[["ab","A·B"],["abc","A·B·C"],["solid","All A"]].map(([k,l])=>(
                        <div key={k} onClick={()=>updSel({altMode:k})} style={{
                          flex:1,padding:"3px 4px",cursor:"pointer",fontSize:"7px",textAlign:"center",
                          border:sel.altMode===k?"1px solid #88b868":"1px solid #1e1208",
                          background:sel.altMode===k?"#0f1208":"transparent",
                          color:sel.altMode===k?"#88b868":"#3a2010",borderRadius:"2px"}}>{l}</div>
                      ))}
                    </div>
                    <div onClick={()=>updSel({showOut:!sel.showOut})} style={{
                      marginTop:"5px",padding:"3px 8px",cursor:"pointer",fontSize:"8px",borderRadius:"2px",
                      border:sel.showOut?"1px solid #88b868":"1px solid #1e1208",
                      color:sel.showOut?"#88b868":"#3a2010",background:sel.showOut?"#0f1208":"transparent"}}>
                      Outlines {sel.showOut?"ON":"OFF"}
                    </div>
                  </div>
                </div>
              )}
            </>
          ):(
            <div style={{fontSize:"8px",color:"#2a1808",padding:"20px 8px",textAlign:"center"}}>
              Click a ring to edit it
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
