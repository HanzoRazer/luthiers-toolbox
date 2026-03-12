import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════
// MATERIAL LIBRARY
// ═══════════════════════════════════════════════════════════
const WOODS = [
  { id:"ebony",    name:"Ebony",          base:"#1a1008", grain:"#0e0804" },
  { id:"maple",    name:"Maple",          base:"#f2e8c8", grain:"#cdb87a" },
  { id:"maple_q",  name:"Quilted Maple",  base:"#f0d880", grain:"#b89030" },
  { id:"rosewood", name:"Rosewood",       base:"#4a1e10", grain:"#2e1008" },
  { id:"spruce",   name:"Spruce",         base:"#e8d8a0", grain:"#b89840" },
  { id:"cedar",    name:"Cedar",          base:"#c07040", grain:"#883010" },
  { id:"mahogany", name:"Mahogany",       base:"#7a3018", grain:"#4a1808" },
  { id:"koa",      name:"Koa",            base:"#c87828", grain:"#804810" },
  { id:"walnut",   name:"Walnut",         base:"#5c3818", grain:"#382008" },
  { id:"mop",      name:"Mother-of-Pearl",base:"#e8f0f8", grain:"#a0c8f0", irid:true },
  { id:"abalone",  name:"Abalone",        base:"#508868", grain:"#306848", irid:true },
  { id:"bone",     name:"Bone",           base:"#f0e8d0", grain:"#c8b888" },
  { id:"ovangkol", name:"Ovangkol",       base:"#a87828", grain:"#685010" },
  { id:"air",      name:"Air / Open",     base:"#0a0806", grain:"#060402" },
];
const wById = id => WOODS.find(w => w.id === id) ?? WOODS[0];

// ═══════════════════════════════════════════════════════════
// SHAPE LIBRARY
// Each shape: draw(ctx, W, H, p, idx) in tile-local coords
// Origin = tile center, X = tangential, Y = radial
// W = tile width px, H = tile height px
// ═══════════════════════════════════════════════════════════
const SHAPES = {
  parallelogram: {
    label: "Parallelogram", group: "polygon",
    hint: "The Fusion 360 tile — chamfered corners, lean controls direction",
    params: [
      { k:"w",    l:"Width",   min:0.2, max:1.1,  s:0.01, d:0.88 },
      { k:"h",    l:"Height",  min:0.2, max:1.1,  s:0.01, d:0.90 },
      { k:"lean", l:"Lean",    min:-0.6,max:0.6,  s:0.01, d:0.28 },
      { k:"ch",   l:"Chamfer", min:0,   max:0.45, s:0.01, d:0.14 },
    ],
    draw(ctx, W, H, p) {
      const hw=W/2*p.w, hh=H/2*p.h, lx=W*p.lean, ch=Math.min(hw,hh)*p.ch;
      if (ch > 1) {
        ctx.moveTo(-hw+lx+ch, -hh);  ctx.lineTo(hw+lx-ch, -hh);
        ctx.lineTo(hw+lx, -hh+ch);   ctx.lineTo(hw-lx, hh-ch);
        ctx.lineTo(hw-lx-ch, hh);    ctx.lineTo(-hw-lx+ch, hh);
        ctx.lineTo(-hw-lx, hh-ch);   ctx.lineTo(-hw+lx, -hh+ch);
      } else {
        ctx.moveTo(-hw+lx,-hh); ctx.lineTo(hw+lx,-hh);
        ctx.lineTo(hw-lx, hh); ctx.lineTo(-hw-lx, hh);
      }
      ctx.closePath();
    }
  },

  ellipse: {
    label: "Ellipse", group: "curve",
    hint: "Floating ovals — gap shows through between tiles",
    params: [
      { k:"rx", l:"X radius", min:0.1, max:1.1, s:0.01, d:0.82 },
      { k:"ry", l:"Y radius", min:0.1, max:1.1, s:0.01, d:0.85 },
    ],
    draw(ctx, W, H, p) {
      ctx.ellipse(0, 0, W/2*p.rx, H/2*p.ry, 0, 0, Math.PI*2);
    }
  },

  oval_lean: {
    label: "Leaning Oval", group: "curve",
    hint: "Sheared ellipse — the lean creates implied rotation and movement",
    params: [
      { k:"rx",   l:"X radius", min:0.1, max:1.1, s:0.01, d:0.78 },
      { k:"ry",   l:"Y radius", min:0.1, max:1.1, s:0.01, d:0.88 },
      { k:"lean", l:"Lean",     min:-1,  max:1,   s:0.02, d:0.45 },
    ],
    draw(ctx, W, H, p) {
      const N=52, rx=W/2*p.rx, ry=H/2*p.ry, lx=W/2*p.lean;
      for (let i=0; i<=N; i++) {
        const a=i/N*Math.PI*2;
        const x=Math.cos(a)*rx + lx*Math.sin(a);
        const y=Math.sin(a)*ry;
        i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
      }
      ctx.closePath();
    }
  },

  diamond: {
    label: "Diamond", group: "polygon",
    hint: "Rhombus with optional corner rounding and lean",
    params: [
      { k:"w",    l:"Width",       min:0.1, max:1.2, s:0.01, d:0.82 },
      { k:"h",    l:"Height",      min:0.1, max:1.2, s:0.01, d:0.90 },
      { k:"lean", l:"Lean",        min:-0.8,max:0.8, s:0.01, d:0.0 },
      { k:"r",    l:"Corner round",min:0,   max:0.5, s:0.01, d:0.0 },
    ],
    draw(ctx, W, H, p) {
      const hw=W/2*p.w, hh=H/2*p.h, lx=hw*p.lean;
      const r=Math.min(hw,hh)*p.r;
      if (r > 1) {
        const f=0.55;
        ctx.moveTo(lx, -hh+r);
        ctx.bezierCurveTo(lx+r*f,-hh, hw+lx-r*f,-(r*0.3), hw+lx, 0);
        ctx.bezierCurveTo(hw+lx+r*f,r*0.3, lx+r*f,hh, lx, hh-r);
        ctx.bezierCurveTo(lx-r*f,hh, -hw+lx+r*f,r*0.3, -hw+lx, 0);
        ctx.bezierCurveTo(-hw+lx-r*f,-r*0.3, lx-r*f,-hh, lx, -hh+r);
      } else {
        ctx.moveTo(lx,-hh); ctx.lineTo(hw+lx,0); ctx.lineTo(lx,hh); ctx.lineTo(-hw+lx,0);
      }
      ctx.closePath();
    }
  },

  crescent: {
    label: "Crescent", group: "curve", special: "crescent",
    hint: "Moon shape — outer ellipse minus inner. Background shows through the void",
    params: [
      { k:"orx",  l:"Outer X",     min:0.2, max:1.1, s:0.01, d:0.88 },
      { k:"ory",  l:"Outer Y",     min:0.2, max:1.1, s:0.01, d:0.90 },
      { k:"irx",  l:"Inner X",     min:0.1, max:1.0, s:0.01, d:0.70 },
      { k:"iry",  l:"Inner Y",     min:0.1, max:1.0, s:0.01, d:0.72 },
      { k:"iox",  l:"Inner offset X",min:-0.5,max:0.5,s:0.01,d:0.18},
      { k:"ioy",  l:"Inner offset Y",min:-0.5,max:0.5,s:0.01,d:0.0 },
    ],
    draw(ctx, W, H, p) {
      ctx.ellipse(0,0,W/2*p.orx, H/2*p.ory, 0,0,Math.PI*2);
    },
    drawInner(ctx, W, H, p) {
      ctx.ellipse(W/2*p.iox, H/2*p.ioy, W/2*p.irx, H/2*p.iry, 0,0,Math.PI*2);
    }
  },

  lens: {
    label: "Lens / Vesica", group: "curve",
    hint: "Two arcs meeting at points — Gothic window, eye, almond",
    params: [
      { k:"w",    l:"Width",     min:0.1, max:1.1, s:0.01, d:0.65 },
      { k:"h",    l:"Height",    min:0.2, max:1.2, s:0.01, d:0.92 },
      { k:"curve",l:"Curvature", min:0.05,max:2.5, s:0.05, d:0.75 },
      { k:"lean", l:"Lean",      min:-0.5,max:0.5, s:0.01, d:0.0  },
    ],
    draw(ctx, W, H, p) {
      const hw=W/2*p.w, hh=H/2*p.h;
      const cx=hw*p.curve*1.2, lx=W/4*p.lean;
      ctx.moveTo(lx, -hh);
      ctx.bezierCurveTo(cx+lx,-hh*0.4, cx,-hh*0.1, 0, hh);
      ctx.bezierCurveTo(-cx,-hh*0.1, -cx+lx,-hh*0.4, lx,-hh);
      ctx.closePath();
    }
  },

  teardrop: {
    label: "Teardrop", group: "curve",
    hint: "Botanical — petal, leaf, seed. Flip inverts orientation in ring",
    params: [
      { k:"w",    l:"Width",     min:0.1, max:1.1, s:0.01, d:0.68 },
      { k:"h",    l:"Height",    min:0.2, max:1.2, s:0.01, d:0.90 },
      { k:"bulge",l:"Bulge",     min:0.1, max:1.2, s:0.01, d:0.65 },
      { k:"tip",  l:"Tip tight", min:0.0, max:1.0, s:0.01, d:0.55 },
      { k:"flip", l:"Flip (0/1)",min:0,   max:1,   s:1,    d:0    },
    ],
    draw(ctx, W, H, p) {
      const hw=W/2*p.w, hh=H/2*p.h, d=p.flip>0.5?-1:1;
      const tipY=-hh*d, botY=hh*d, tc=hh*p.tip*d*0.8;
      ctx.moveTo(0, tipY);
      ctx.bezierCurveTo(hw,tipY+tc, hw*1.1*p.bulge, 0, hw*0.85, botY);
      const N=16;
      for(let i=1;i<=N;i++){
        const a=i/N*Math.PI;
        ctx.lineTo(Math.cos(Math.PI-a)*hw*0.85, botY + Math.sin(Math.PI-a)*hw*0.22);
      }
      ctx.bezierCurveTo(-hw*1.1*p.bulge, 0, -hw, tipY+tc, 0, tipY);
      ctx.closePath();
    }
  },

  star: {
    label: "Star", group: "polygon",
    hint: "N-pointed star — 3–12 points, inner radius controls fatness",
    params: [
      { k:"n",     l:"Points",       min:3,  max:12, s:1,    d:5    },
      { k:"outer", l:"Outer radius", min:0.2,max:1.1,s:0.01, d:0.88 },
      { k:"inner", l:"Inner radius", min:0.05,max:0.9,s:0.01,d:0.42 },
      { k:"spin",  l:"Spin offset",  min:0,  max:1,  s:0.01, d:0.0  },
    ],
    draw(ctx, W, H, p) {
      const n=Math.round(p.n), sc=Math.min(W,H)/2;
      const ro=sc*p.outer, ri=sc*p.inner, spin=p.spin*Math.PI;
      for(let i=0;i<n*2;i++){
        const r=i%2===0?ro:ri;
        const a=i*Math.PI/n - Math.PI/2 + spin;
        const x=Math.cos(a)*r, y=Math.sin(a)*r;
        i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
      }
      ctx.closePath();
    }
  },

  ogee: {
    label: "Ogee Tile", group: "curve",
    hint: "S-curve sides — tiles interlock like a Gothic tracery repeat",
    params: [
      { k:"w",    l:"Width",      min:0.2, max:1.1, s:0.01, d:0.92 },
      { k:"h",    l:"Height",     min:0.2, max:1.1, s:0.01, d:0.92 },
      { k:"bulge",l:"S-depth",    min:0.0, max:0.9, s:0.01, d:0.38 },
      { k:"waist",l:"Waist",      min:0.0, max:0.8, s:0.01, d:0.0  },
      { k:"top",  l:"Top curve",  min:-0.5,max:0.5, s:0.01, d:0.0  },
    ],
    draw(ctx, W, H, p) {
      const hw=W/2*p.w, hh=H/2*p.h, bx=hw*p.bulge, wy=hh*p.waist, tc=H/2*p.top;
      ctx.moveTo(-hw, -hh);
      // top edge — can be straight or arched
      ctx.bezierCurveTo(-hw/2, -hh-tc, hw/2, -hh-tc, hw, -hh);
      // right side — S-curve (ogee)
      ctx.bezierCurveTo(hw+bx,-hh/2, hw-bx,-wy, hw,0);
      ctx.bezierCurveTo(hw+bx, wy,   hw-bx, hh/2, hw, hh);
      // bottom
      ctx.bezierCurveTo(hw/2,hh+tc, -hw/2,hh+tc, -hw, hh);
      // left side — mirror S-curve
      ctx.bezierCurveTo(-hw+bx, hh/2, -hw-bx, wy,   -hw, 0);
      ctx.bezierCurveTo(-hw+bx,-wy,  -hw-bx,-hh/2, -hw,-hh);
      ctx.closePath();
    }
  },

  scale: {
    label: "Fish Scale", group: "curve",
    hint: "Écaille — arch top bleeds into neighbor, creating layered scale effect",
    params: [
      { k:"w",    l:"Width",      min:0.2, max:1.2, s:0.01, d:0.98 },
      { k:"h",    l:"Height",     min:0.2, max:1.2, s:0.01, d:0.92 },
      { k:"arch", l:"Arch depth", min:0.0, max:1.2, s:0.01, d:0.55 },
      { k:"tail", l:"Tail round", min:0.0, max:0.6, s:0.01, d:0.0  },
    ],
    draw(ctx, W, H, p) {
      const hw=W/2*p.w, hh=H/2*p.h, arch=H*p.arch*0.5, tr=hh*p.tail;
      ctx.moveTo(-hw, -hh+arch);
      // arch top (concave up — overflows into ring above)
      ctx.bezierCurveTo(-hw*0.5,-hh-arch*0.5, hw*0.5,-hh-arch*0.5, hw,-hh+arch);
      // right straight side
      if(tr>1){ ctx.lineTo(hw,hh-tr); ctx.quadraticCurveTo(hw,hh,hw-tr,hh); }
      else { ctx.lineTo(hw,hh); }
      // bottom — straight or curved
      ctx.lineTo(-hw,hh);
      if(tr>1){ ctx.lineTo(-hw,hh); ctx.quadraticCurveTo(-hw,hh,-hw,hh-tr); }
      ctx.closePath();
    }
  },

  rope_asym: {
    label: "Asymm. Rope", group: "organic", special: "drift",
    hint: "Non-symmetric strand — skew + drift make it non-periodic. No tile repeats exactly",
    params: [
      { k:"thick",l:"Thickness", min:0.1, max:0.95,s:0.01, d:0.58 },
      { k:"wave", l:"Wave depth",min:0.0, max:0.9, s:0.01, d:0.42 },
      { k:"skew", l:"Skew",      min:0.0, max:0.95,s:0.01, d:0.62 },
      { k:"drift",l:"Drift",     min:0.0, max:0.8, s:0.01, d:0.12 },
      { k:"cap",  l:"Cap round", min:0.0, max:1.0, s:0.01, d:0.6  },
    ],
    draw(ctx, W, H, p, idx) {
      const hh=H/2*p.thick;
      const wave=H/2*p.wave;
      const peakX=-W/2 + W*p.skew;
      // Drift accumulates: each tile is slightly shifted
      const driftY = (H/2 - hh) * Math.sin((idx??0) * p.drift * 0.8);
      const y0=driftY, cr=hh*p.cap;
      // Top surface — asymmetric swell
      ctx.moveTo(-W/2, y0-hh+cr);
      if(cr>1) ctx.quadraticCurveTo(-W/2, y0-hh, -W/2+cr, y0-hh);
      ctx.bezierCurveTo(peakX-W/6, y0-hh-wave, peakX+W/6, y0-hh-wave*0.8, W/2, y0-hh+wave*0.3);
      if(cr>1) { ctx.quadraticCurveTo(W/2+cr*0.5,y0-hh+wave*0.3,W/2+cr,y0); }
      // Bottom surface
      const bx=peakX + W*0.1;
      if(cr>1) { ctx.quadraticCurveTo(W/2+cr*0.5,y0+hh-wave*0.3,W/2,y0+hh-wave*0.3); }
      else { ctx.lineTo(W/2, y0+hh-wave*0.3); }
      ctx.bezierCurveTo(bx+W/6, y0+hh+wave*0.8, bx-W/6, y0+hh+wave, -W/2, y0+hh);
      if(cr>1) ctx.quadraticCurveTo(-W/2, y0+hh, -W/2, y0+hh-cr);
      ctx.closePath();
    }
  },

  hexagon: {
    label: "Hexagon", group: "polygon",
    hint: "Flat-top or pointy-top hex — tiles can pack edge-to-edge",
    params: [
      { k:"r",    l:"Radius",  min:0.2, max:1.0, s:0.01, d:0.82 },
      { k:"rot",  l:"Rotation",min:0,   max:1,   s:0.01, d:0.0  },
      { k:"squish",l:"Squish", min:0.3, max:1.5, s:0.01, d:1.0  },
    ],
    draw(ctx, W, H, p) {
      const r=Math.min(W,H)/2*p.r, spin=p.rot*Math.PI;
      for(let i=0;i<6;i++){
        const a=i*Math.PI/3 + spin;
        const x=Math.cos(a)*r, y=Math.sin(a)*r*p.squish;
        i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
      }
      ctx.closePath();
    }
  },

  hyperbolic_wave: {
    label: "Hyperbolic Wave", group: "organic", special: "drift",
    hint: "Non-repeating wave — hyperbolic drift makes each tile slightly different, creating moiré beats",
    params: [
      { k:"thick",l:"Thickness",       min:0.1, max:0.95,s:0.01, d:0.45 },
      { k:"wave", l:"Wave amp",        min:0.0, max:1.2, s:0.01, d:0.68 },
      { k:"skew", l:"Skew",            min:0.0, max:1.0, s:0.01, d:0.75 },
      { k:"drift",l:"Hyperbolic drift",min:0.0, max:2.0, s:0.02, d:1.2  },
      { k:"chaos",l:"Chaos",           min:0.0, max:1.0, s:0.01, d:0.33 },
    ],
    draw(ctx, W, H, p, idx) {
      const hh = H/2*p.thick;
      const t = idx*0.3 + p.drift*Math.log(idx+2) + p.chaos*Math.sin(idx*0.17);
      const peakX = -W/2 + W*(p.skew + 0.1*Math.sin(t));
      const waveY = H/2*p.wave*Math.sin(t*2.3);
      ctx.moveTo(-W/2, -hh+waveY);
      ctx.bezierCurveTo(peakX-W/6,-hh-waveY*0.5, peakX+W/6,-hh+waveY, W/2,-hh+waveY*0.3);
      ctx.lineTo(W/2, hh-waveY*0.3);
      ctx.bezierCurveTo(peakX+W/6,hh+waveY, peakX-W/6,hh+waveY*0.5, -W/2,hh-waveY);
      ctx.closePath();
    },
  },

  petal: {
    label: "Petal / Paisley", group: "organic",
    hint: "Curved quadrilateral — rotate around ring for mandala-like effects",
    params: [
      { k:"w",    l:"Width",     min:0.1, max:1.1, s:0.01, d:0.72 },
      { k:"h",    l:"Height",    min:0.2, max:1.2, s:0.01, d:0.92 },
      { k:"c1",   l:"Curve A",   min:-1,  max:1,   s:0.01, d:0.6  },
      { k:"c2",   l:"Curve B",   min:-1,  max:1,   s:0.01, d:-0.3 },
      { k:"lean", l:"Lean",      min:-0.6,max:0.6, s:0.01, d:0.2  },
    ],
    draw(ctx, W, H, p) {
      const hw=W/2*p.w, hh=H/2*p.h, lx=W*p.lean;
      ctx.moveTo(lx, -hh);
      ctx.bezierCurveTo(hw+lx+W*p.c1,-hh*0.5, hw,0, hw*0.6,hh);
      ctx.bezierCurveTo(hw*0.2,hh*1.1, -hw*0.2,hh*1.1, -hw*0.6,hh);
      ctx.bezierCurveTo(-hw,0, -hw+lx+W*p.c2,-hh*0.5, lx,-hh);
      ctx.closePath();
    }
  },
};

// ═══════════════════════════════════════════════════════════
// GRAIN FILL (in tile-local clipped space)
// ═══════════════════════════════════════════════════════════
function fillGrain(ctx, wood, W, H, seed, dir="tangential") {
  let s = seed * 9301 + 4927;
  const rng = () => { s=(s*9301+49297)%233280; return s/233280; };

  if (wood.irid) {
    for(let i=0;i<5;i++){
      const grd=ctx.createRadialGradient((rng()-0.5)*W,(rng()-0.5)*H,0,(rng()-0.5)*W,(rng()-0.5)*H,Math.max(W,H)*0.7);
      const h=(seed*37+i*53)%360;
      grd.addColorStop(0,`hsla(${h},55%,80%,0.4)`);
      grd.addColorStop(1,"transparent");
      ctx.fillStyle=grd; ctx.fillRect(-W,-H,W*2,H*2);
    }
  }

  const lines=12;
  for(let i=0;i<lines;i++){
    ctx.beginPath();
    if(dir==="tangential"){
      const y=(rng()-0.5)*H*2.5;
      ctx.moveTo(-W, y+(rng()-0.5)*4); ctx.lineTo(W, y+(rng()-0.5)*4);
    } else if(dir==="radial"){
      const x=(rng()-0.5)*W*2.5;
      ctx.moveTo(x+(rng()-0.5)*4,-H); ctx.lineTo(x+(rng()-0.5)*4,H);
    } else {
      const t=(rng()-0.5)*W*3;
      ctx.moveTo(-W,t-W); ctx.lineTo(W,t+W);
    }
    ctx.strokeStyle=wood.grain;
    ctx.lineWidth=rng()*1.2+0.2;
    ctx.globalAlpha=0.22+rng()*0.3;
    ctx.stroke();
  }
  ctx.globalAlpha=1;
}

// ═══════════════════════════════════════════════════════════
// WHEEL RENDERER
// ═══════════════════════════════════════════════════════════
function renderWheel(canvas, state) {
  if(!canvas) return;
  const { shape, params, N, ringW, innerR, gap, matFg, matBg, matAlt, matC,
          altMode, grainDir, showGrid, showOutlines } = state;
  const S=canvas.width, cx=S/2, cy=S/2;
  const ctx=canvas.getContext("2d");
  ctx.clearRect(0,0,S,S);

  // Background
  const bg=ctx.createRadialGradient(cx,cy,0,cx,cy,S/2);
  bg.addColorStop(0,"#0e0a06"); bg.addColorStop(1,"#060402");
  ctx.fillStyle=bg; ctx.fillRect(0,0,S,S);

  // Scale: fit (innerR + ringW + margin) into canvas
  const totalR = innerR + ringW + 8;
  const MM = S / (totalR * 2);
  const iR = innerR * MM;
  const oR = (innerR + ringW) * MM;
  const midR = (iR + oR) / 2;

  // Background ring (full annulus)
  const bgWood = wById(matBg);
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx,cy,oR,0,Math.PI*2);
  ctx.arc(cx,cy,iR,0,Math.PI*2,true);
  ctx.fillStyle=bgWood.base;
  ctx.fill("evenodd");
  fillGrain(ctx,bgWood,oR*2,oR*2,42,grainDir);
  ctx.restore();

  // Tiles
  const shapeDef = SHAPES[shape];
  const angStep = Math.PI*2/N;
  const tileH = (oR-iR)*gap;
  const tileW = midR*angStep*gap;

  const matCycle = [matFg, matAlt, matC, matBg];

  for(let i=0;i<N;i++){
    const midAng = (i+0.5)*angStep - Math.PI/2;
    const tcx = cx + Math.cos(midAng)*midR;
    const tcy = cy + Math.sin(midAng)*midR;

    // Material selection
    let wid = matFg;
    if(altMode==="ab")   wid = matCycle[i%2];
    else if(altMode==="aba") wid = i%4===2 ? matAlt : matFg;
    else if(altMode==="abc") wid = matCycle[i%3];
    else if(altMode==="abcd")wid = matCycle[i%4];
    else if(altMode==="wave"){ const t=Math.sin(i/N*Math.PI*2)*0.5+0.5; wid = t>0.5?matFg:matAlt; }

    const wood=wById(wid);

    ctx.save();
    ctx.translate(tcx,tcy);
    ctx.rotate(midAng+Math.PI/2);

    if(shapeDef.special==="crescent"){
      // Painter approach: outer fill, then punch inner with bg
      ctx.beginPath();
      shapeDef.draw(ctx,tileW,tileH,params,i);
      ctx.fillStyle=wood.base; ctx.fill();
      ctx.save();
      ctx.beginPath();
      shapeDef.draw(ctx,tileW,tileH,params,i);
      ctx.clip();
      fillGrain(ctx,wood,tileW,tileH,i,grainDir);
      ctx.restore();
      // inner void
      ctx.beginPath();
      shapeDef.drawInner(ctx,tileW,tileH,params,i);
      ctx.fillStyle=bgWood.base; ctx.fill();
      // outline
      if(showOutlines){
        ctx.beginPath();
        shapeDef.draw(ctx,tileW,tileH,params,i);
        ctx.strokeStyle="rgba(0,0,0,0.45)"; ctx.lineWidth=0.7; ctx.stroke();
      }
    } else {
      ctx.beginPath();
      shapeDef.draw(ctx,tileW,tileH,params,i);
      ctx.save(); ctx.clip();
      ctx.fillStyle=wood.base; ctx.fillRect(-tileW*1.5,-tileH*1.5,tileW*3,tileH*3);
      fillGrain(ctx,wood,tileW*2,tileH*2,i*13+shape.length,grainDir);
      ctx.restore();
      if(showOutlines){
        ctx.beginPath();
        shapeDef.draw(ctx,tileW,tileH,params,i);
        ctx.strokeStyle="rgba(0,0,0,0.5)"; ctx.lineWidth=0.8; ctx.stroke();
      }
    }
    ctx.restore();
  }

  // Grid lines
  if(showGrid){
    for(let i=0;i<N;i++){
      const a=i*angStep-Math.PI/2;
      ctx.beginPath();
      ctx.moveTo(cx+Math.cos(a)*iR,cy+Math.sin(a)*iR);
      ctx.lineTo(cx+Math.cos(a)*oR,cy+Math.sin(a)*oR);
      ctx.strokeStyle="rgba(200,160,50,0.1)"; ctx.lineWidth=0.5;
      ctx.setLineDash([2,3]); ctx.stroke(); ctx.setLineDash([]);
    }
    [iR,midR,oR].forEach(r=>{
      ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2);
      ctx.strokeStyle="rgba(200,160,50,0.12)"; ctx.lineWidth=0.6;
      ctx.setLineDash([2,4]); ctx.stroke(); ctx.setLineDash([]);
    });
  }

  // Soundhole
  ctx.beginPath(); ctx.arc(cx,cy,iR,0,Math.PI*2);
  const sf=ctx.createRadialGradient(cx,cy-6,1,cx,cy,iR);
  sf.addColorStop(0,"#1a1208"); sf.addColorStop(1,"#050302");
  ctx.fillStyle=sf; ctx.fill();
  ctx.strokeStyle="rgba(200,160,50,0.35)"; ctx.lineWidth=1.2; ctx.stroke();

  // Outer edge
  ctx.beginPath(); ctx.arc(cx,cy,oR,0,Math.PI*2);
  ctx.strokeStyle="rgba(200,160,50,0.18)"; ctx.lineWidth=1.5; ctx.stroke();
}

// ═══════════════════════════════════════════════════════════
// SHAPE THUMBNAIL (mini SVG canvas per shape)
// ═══════════════════════════════════════════════════════════
function ShapeThumb({ shapeKey, selected, onClick }) {
  const ref = useRef(null);
  const def = SHAPES[shapeKey];
  useEffect(()=>{
    const c=ref.current; if(!c) return;
    const ctx=c.getContext("2d");
    ctx.clearRect(0,0,44,34);
    ctx.fillStyle="#0a0806"; ctx.fillRect(0,0,44,34);
    ctx.save(); ctx.translate(22,17);
    ctx.beginPath();
    const p = Object.fromEntries((def.params??[]).map(d=>[d.k,d.d]));
    def.draw(ctx,36,26,p,0);
    ctx.fillStyle = selected?"#c9a96e":"#4a3020";
    ctx.fill();
    if(def.special==="crescent"&&def.drawInner){
      ctx.beginPath(); def.drawInner(ctx,36,26,p,0);
      ctx.fillStyle="#0a0806"; ctx.fill();
    }
    ctx.strokeStyle=selected?"#e8c87a":"#2a1a0a";
    ctx.lineWidth=selected?1.5:1; ctx.stroke();
    ctx.restore();
  },[selected]);
  return (
    <div onClick={onClick} title={def.label} style={{
      cursor:"pointer", borderRadius:"4px", padding:"3px",
      border:selected?"1px solid #c9a96e":"1px solid #1e1208",
      background:selected?"#130f08":"#0a0806",
      display:"flex",flexDirection:"column",alignItems:"center",gap:"2px",
      transition:"all .08s"
    }}>
      <canvas ref={ref} width={44} height={34} style={{borderRadius:"2px"}}/>
      <div style={{fontSize:"7px",color:selected?"#e8c87a":"#3a2010",letterSpacing:"0.5px",textAlign:"center",lineHeight:1}}>
        {def.label}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// PARAM SLIDER
// ═══════════════════════════════════════════════════════════
function Sl({ label, val, set, min, max, step, note }) {
  const fmt = v => Number.isInteger(v) ? v : v.toFixed(step<0.05?2:1);
  return (
    <div style={{marginBottom:"7px"}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:"1px"}}>
        <span style={{fontSize:"8px",color:"#4a3010"}}>{label}</span>
        <span style={{fontSize:"9px",color:"#e8c87a"}}>{fmt(val)}{note?` ${note}`:""}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val}
        onChange={e=>set(Number(e.target.value))}
        style={{width:"100%",accentColor:"#c9a96e"}}/>
    </div>
  );
}

function MatPick({ label, val, set }) {
  const w=wById(val);
  return (
    <div style={{display:"flex",alignItems:"center",gap:"6px",marginBottom:"5px"}}>
      <div style={{width:"22px",height:"16px",borderRadius:"2px",flexShrink:0,
        background:w.base,border:"1px solid #2e2010",position:"relative",overflow:"hidden"}}>
        {w.irid&&<div style={{position:"absolute",inset:0,background:"linear-gradient(45deg,#e8f0f844,#c0f0e044,#f0d08044)"}}/>}
      </div>
      <span style={{fontSize:"8px",color:"#4a3010",minWidth:"55px"}}>{label}</span>
      <select value={val} onChange={e=>set(e.target.value)}
        style={{flex:1,background:"#0f0c08",border:"1px solid #2e2010",borderRadius:"2px",
          color:"#c9a96e",fontSize:"8px",padding:"2px 4px",fontFamily:"'Courier New',monospace"}}>
        {WOODS.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}
      </select>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// GROUP LABELS
// ═══════════════════════════════════════════════════════════
const GROUPS = [
  { key:"polygon", label:"POLYGON" },
  { key:"curve",   label:"CURVED" },
  { key:"organic", label:"ORGANIC" },
];

// ═══════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════
export default function ShapeCompositor() {
  const CANVAS = 520;
  const [shape, setShape]   = useState("parallelogram");
  const [params, setParams] = useState(()=>Object.fromEntries((SHAPES.parallelogram.params??[]).map(d=>[d.k,d.d])));
  const [N, setN]           = useState(12);
  const [ringW, setRingW]   = useState(9.0);
  const [innerR, setInnerR] = useState(40.8);
  const [gap, setGap]       = useState(0.85);
  const [matFg, setMatFg]   = useState("rosewood");
  const [matBg, setMatBg]   = useState("ebony");
  const [matAlt, setMatAlt] = useState("maple");
  const [matC, setMatC]     = useState("bone");
  const [altMode, setAltMode] = useState("solid");
  const [grainDir, setGrainDir] = useState("tangential");
  const [showGrid, setShowGrid] = useState(false);
  const [showOutlines, setShowOutlines] = useState(true);
  const canvasRef = useRef(null);
  const timer = useRef(null);

  const setShape_ = s => {
    setShape(s);
    setParams(Object.fromEntries((SHAPES[s].params??[]).map(d=>[d.k,d.d])));
  };
  const setP = (k,v) => setParams(p=>({...p,[k]:v}));

  const state = { shape,params,N,ringW,innerR,gap,matFg,matBg,matAlt,matC,altMode,grainDir,showGrid,showOutlines };

  useEffect(()=>{
    clearTimeout(timer.current);
    timer.current=setTimeout(()=>renderWheel(canvasRef.current,state),40);
    return()=>clearTimeout(timer.current);
  },[shape,params,N,ringW,innerR,gap,matFg,matBg,matAlt,matC,altMode,grainDir,showGrid,showOutlines]);

  const def=SHAPES[shape];
  const totalW=ringW;

  const PRESETS = [
    { name:"Fusion 360", shape:"parallelogram",params:{w:0.88,h:0.90,lean:0.28,ch:0.14},N:12,gap:0.82,matFg:"rosewood",matBg:"ebony",matAlt:"maple",altMode:"ab",ringW:9 },
    { name:"Pearl Ovals", shape:"ellipse",params:{rx:0.78,ry:0.88},N:20,gap:0.78,matFg:"mop",matBg:"ebony",matAlt:"abalone",altMode:"ab",ringW:7 },
    { name:"Koa Scales",  shape:"scale",params:{w:0.98,h:0.92,arch:0.55,tail:0.0},N:18,gap:0.95,matFg:"koa",matBg:"ebony",matAlt:"walnut",altMode:"ab",ringW:8 },
    { name:"Star Burst",  shape:"star",params:{n:6,outer:0.88,inner:0.42,spin:0},N:12,gap:0.85,matFg:"maple",matBg:"ebony",matAlt:"rosewood",altMode:"ab",ringW:10 },
    { name:"Moon Ring",   shape:"crescent",params:{orx:0.88,ory:0.90,irx:0.70,iry:0.72,iox:0.18,ioy:0.0},N:16,gap:0.85,matFg:"mop",matBg:"ebony",matAlt:"maple",altMode:"solid",ringW:8 },
    { name:"Ogee Flow",   shape:"ogee",params:{w:0.92,h:0.92,bulge:0.38,waist:0.0,top:0.0},N:14,gap:0.96,matFg:"walnut",matBg:"ebony",matAlt:"maple",altMode:"ab",ringW:9 },
    { name:"Teardrops",   shape:"teardrop",params:{w:0.68,h:0.90,bulge:0.65,tip:0.55,flip:0},N:16,gap:0.82,matFg:"cedar",matBg:"ebony",matAlt:"spruce",altMode:"ab",ringW:8 },
    { name:"Paisley",     shape:"petal",params:{w:0.72,h:0.92,c1:0.6,c2:-0.3,lean:0.2},N:14,gap:0.85,matFg:"koa",matBg:"ebony",matAlt:"maple",altMode:"ab",ringW:9 },
    { name:"Rope Wave",   shape:"rope_asym",params:{thick:0.58,wave:0.42,skew:0.62,drift:0.22,cap:0.6},N:24,gap:0.92,matFg:"maple",matBg:"ebony",matAlt:"rosewood",altMode:"abc",ringW:7 },
    { name:"Hyp·Calm",   shape:"hyperbolic_wave",params:{thick:0.45,wave:0.68,skew:0.75,drift:1.2, chaos:0.33},N:24,gap:0.98,matFg:"maple",  matBg:"ebony",   matAlt:"rosewood",matC:"bone",   altMode:"abc", ringW:8  },
    { name:"Hyp·Storm",  shape:"hyperbolic_wave",params:{thick:0.38,wave:1.18,skew:0.88,drift:2.0, chaos:0.95},N:36,gap:1.05,matFg:"mop",    matBg:"ebony",   matAlt:"abalone", matC:"maple",  altMode:"abcd",ringW:10 },
    { name:"Hyp·Drift",  shape:"hyperbolic_wave",params:{thick:0.55,wave:0.42,skew:0.50,drift:1.8, chaos:0.0 },N:48,gap:0.92,matFg:"maple",  matBg:"rosewood",matAlt:"bone",    matC:"koa",    altMode:"ab",  ringW:7  },
    { name:"Hyp·Chaos",  shape:"hyperbolic_wave",params:{thick:0.28,wave:1.20,skew:0.30,drift:0.6, chaos:1.0 },N:32,gap:1.08,matFg:"abalone",matBg:"ebony",   matAlt:"mop",     matC:"walnut", altMode:"wave",ringW:9  },
    { name:"Hyp·Slow",   shape:"hyperbolic_wave",params:{thick:0.62,wave:0.22,skew:0.60,drift:0.3, chaos:0.08},N:18,gap:0.88,matFg:"koa",    matBg:"ebony",   matAlt:"maple",   matC:"spruce", altMode:"ab",  ringW:9  },
  ];

  const loadPreset = pr => {
    setShape_(pr.shape);
    setParams(pr.params);
    setN(pr.N); setGap(pr.gap); setRingW(pr.ringW);
    setMatFg(pr.matFg); setMatBg(pr.matBg); setMatAlt(pr.matAlt);
    setAltMode(pr.altMode);
  };

  return (
    <div style={{height:"100vh",background:"#070503",fontFamily:"'Courier New',monospace",
      color:"#c9a96e",display:"flex",flexDirection:"column",overflow:"hidden"}}>

      {/* HEADER */}
      <div style={{padding:"8px 18px",borderBottom:"1px solid #160e06",
        display:"flex",justifyContent:"space-between",alignItems:"center",flexShrink:0}}>
        <div>
          <div style={{fontSize:"7px",letterSpacing:"5px",color:"#251508"}}>THE PRODUCTION SHOP · SHAPE COMPOSITOR</div>
          <div style={{fontSize:"19px",fontWeight:"bold",color:"#e8c87a",letterSpacing:"3px",marginTop:"1px"}}>
            Tile Shape Studio
          </div>
        </div>
        <div style={{display:"flex",gap:"6px",flexWrap:"wrap",justifyContent:"flex-end"}}>
          {PRESETS.map(pr=>(
            <div key={pr.name} onClick={()=>loadPreset(pr)} style={{
              padding:"3px 8px",cursor:"pointer",fontSize:"7px",borderRadius:"2px",
              border:"1px solid #201408",color:"#5a3818",background:"#0a0806",
              transition:"all .08s",letterSpacing:"0.5px"
            }}>{pr.name}</div>
          ))}
        </div>
      </div>

      <div style={{flex:1,display:"flex",overflow:"hidden"}}>

        {/* ══ LEFT: SHAPE PICKER ══ */}
        <div style={{width:"210px",flexShrink:0,borderRight:"1px solid #160e06",
          overflowY:"auto",padding:"8px"}}>
          {GROUPS.map(g=>{
            const shapes=Object.entries(SHAPES).filter(([,d])=>d.group===g.key);
            return (
              <div key={g.key} style={{marginBottom:"12px"}}>
                <div style={{fontSize:"7px",letterSpacing:"3px",color:"#2e1a08",
                  marginBottom:"6px",paddingBottom:"3px",borderBottom:"1px solid #160e06"}}>
                  {g.label}
                </div>
                <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:"4px"}}>
                  {shapes.map(([k])=>(
                    <ShapeThumb key={k} shapeKey={k} selected={shape===k} onClick={()=>setShape_(k)}/>
                  ))}
                </div>
              </div>
            );
          })}

          {/* Hint */}
          <div style={{marginTop:"8px",padding:"8px",background:"#0a0806",
            border:"1px solid #1a1008",borderRadius:"3px",fontSize:"7px",
            color:"#2e1a08",lineHeight:1.9}}>
            {def.hint}
          </div>
        </div>

        {/* ══ CENTER: WHEEL ══ */}
        <div style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",
          justifyContent:"center",padding:"16px",gap:"10px"}}>

          <canvas ref={canvasRef} width={CANVAS} height={CANVAS}
            style={{borderRadius:"50%",
              boxShadow:"0 0 80px rgba(200,150,30,0.06),0 0 180px rgba(0,0,0,0.95)"}}/>

          {/* Stats strip */}
          <div style={{display:"flex",gap:"20px",fontSize:"7px",color:"#2a1808",letterSpacing:"1px"}}>
            <span>⌀{(innerR*2).toFixed(0)}mm soundhole</span>
            <span style={{color:"#e8c87a"}}>{N} tiles</span>
            <span>{ringW.toFixed(1)}mm band</span>
            <span>⌀{((innerR+ringW)*2).toFixed(0)}mm outer</span>
            <span>{def.label}</span>
          </div>
        </div>

        {/* ══ RIGHT: CONTROLS ══ */}
        <div style={{width:"230px",flexShrink:0,borderLeft:"1px solid #160e06",
          overflowY:"auto",padding:"10px"}}>

          {/* Ring settings */}
          <div style={{padding:"8px",background:"#0a0806",border:"1px solid #1a1008",
            borderRadius:"3px",marginBottom:"9px"}}>
            <div style={{fontSize:"7px",letterSpacing:"3px",color:"#2e1a08",marginBottom:"7px"}}>RING</div>
            <Sl label="N tiles"     val={N}      set={setN}      min={3}  max={48} step={1}   />
            <Sl label="Band width"  val={ringW}  set={setRingW}  min={2}  max={20} step={0.1} note="mm"/>
            <Sl label="Gap / fill"  val={gap}    set={setGap}    min={0.3}max={1.2}step={0.01}/>
            <Sl label="Soundhole r" val={innerR} set={setInnerR} min={30} max={60} step={0.1} note="mm"/>
          </div>

          {/* Shape params */}
          <div style={{padding:"8px",background:"#0a0806",border:"1px solid #1a1008",
            borderRadius:"3px",marginBottom:"9px"}}>
            <div style={{fontSize:"7px",letterSpacing:"3px",color:"#2e1a08",marginBottom:"7px"}}>
              {def.label.toUpperCase()} PARAMS
            </div>
            {(def.params??[]).map(pd=>(
              <Sl key={pd.k} label={pd.l} val={params[pd.k]??pd.d}
                set={v=>setP(pd.k,v)} min={pd.min} max={pd.max} step={pd.s}/>
            ))}
          </div>

          {/* Materials */}
          <div style={{padding:"8px",background:"#0a0806",border:"1px solid #1a1008",
            borderRadius:"3px",marginBottom:"9px"}}>
            <div style={{fontSize:"7px",letterSpacing:"3px",color:"#2e1a08",marginBottom:"7px"}}>MATERIALS</div>
            <MatPick label="Foreground" val={matFg}  set={setMatFg}  />
            <MatPick label="Alternate"  val={matAlt} set={setMatAlt} />
            <MatPick label="Third"      val={matC}   set={setMatC}   />
            <MatPick label="Background" val={matBg}  set={setMatBg}  />
          </div>

          {/* Alternation */}
          <div style={{padding:"8px",background:"#0a0806",border:"1px solid #1a1008",
            borderRadius:"3px",marginBottom:"9px"}}>
            <div style={{fontSize:"7px",letterSpacing:"3px",color:"#2e1a08",marginBottom:"7px"}}>DISTRIBUTION</div>
            {[
              ["solid","All foreground"],
              ["ab","A · B  alternate"],
              ["aba","A B A pattern"],
              ["abc","A · B · C  cycle"],
              ["abcd","A B C D  cycle"],
              ["wave","Wave A↔B"],
            ].map(([k,l])=>(
              <div key={k} onClick={()=>setAltMode(k)} style={{
                padding:"3px 7px",marginBottom:"3px",cursor:"pointer",fontSize:"8px",
                borderRadius:"2px",letterSpacing:"0.5px",
                border:altMode===k?"1px solid #c9a96e":"1px solid #1e1208",
                background:altMode===k?"#130f08":"transparent",
                color:altMode===k?"#e8c87a":"#3a2010"}}>{l}</div>
            ))}
          </div>

          {/* Grain + display */}
          <div style={{padding:"8px",background:"#0a0806",border:"1px solid #1a1008",
            borderRadius:"3px"}}>
            <div style={{fontSize:"7px",letterSpacing:"3px",color:"#2e1a08",marginBottom:"7px"}}>DISPLAY</div>
            <div style={{fontSize:"7px",color:"#2e1a08",marginBottom:"4px"}}>Grain direction</div>
            <div style={{display:"flex",gap:"3px",marginBottom:"8px"}}>
              {[["tangential","Tangential"],["radial","Radial"],["diagonal","Diagonal"]].map(([k,l])=>(
                <div key={k} onClick={()=>setGrainDir(k)} style={{
                  flex:1,padding:"3px 4px",cursor:"pointer",fontSize:"7px",textAlign:"center",
                  border:grainDir===k?"1px solid #c9a96e":"1px solid #1e1208",
                  background:grainDir===k?"#130f08":"transparent",
                  color:grainDir===k?"#e8c87a":"#3a2010",borderRadius:"2px"}}>{l}</div>
              ))}
            </div>
            <div style={{display:"flex",gap:"5px"}}>
              {[[showGrid,setShowGrid,"Grid"],[showOutlines,setShowOutlines,"Outlines"]].map(([val,set,l])=>(
                <div key={l} onClick={()=>set(v=>!v)} style={{
                  flex:1,padding:"3px",cursor:"pointer",fontSize:"7px",textAlign:"center",
                  border:val?"1px solid #c9a96e":"1px solid #1e1208",
                  background:val?"#130f08":"transparent",
                  color:val?"#e8c87a":"#3a2010",borderRadius:"2px"}}>{l}</div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
