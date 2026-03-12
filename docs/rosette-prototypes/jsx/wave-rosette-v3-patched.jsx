import { useState, useEffect, useRef } from "react";

const UI = {
  bg:"#0b0806", panel:"#0f0c08", border:"#2e2010", border2:"#1e1508",
  gold:"#e8c87a", amber:"#c9a96e", dim:"#7a5c2e", dimmer:"#4a3010",
  dimmest:"#2a1e0a", text:"#c9a96e",
};

// ─── THE CRASHING WAVE FORMULA ───────────────────────────────────
//
// Each strand segment is an ASYMMETRIC arch:
//
//   peak sits at x = skew · segLen  (e.g. skew=0.75 → peak near the front)
//
//   SWELL side  (x < peakX):  y = A · sin( π/2 · x / peakX )
//     → gradual rise from 0 → A   (the long back of the swell)
//
//   CRASH side  (x ≥ peakX):  y = A · cos( π/2 · (x − peakX) / (segLen − peakX) )
//     → steep fall from A → 0     (the face of the breaking wave)
//
// Rows are staggered by `chase` squares so each successive row looks
// like the wave behind it is just beginning to rise as the front crashes.
//
// This creates:  ~~~  ~~~  ~~~  all moving in the same direction →
//                  ~~~  ~~~  ~~~   (row below, offset by chase)
//
function archY(localX, segLen, A, skew) {
  const peakX = skew * segLen;
  if (peakX <= 0 || segLen <= 0) return 0;
  if (localX <= peakX) {
    return A * Math.sin((Math.PI / 2) * (localX / peakX));
  } else {
    return A * Math.cos((Math.PI / 2) * ((localX - peakX) / (segLen - peakX)));
  }
}

function buildCrashGrid({ cols, rows, A, segLen, gap, d, strandW, numStrands, skew, chase, colorMode }) {
  const pitch = segLen + gap;
  const grid = [];

  for (let r = 0; r < rows; r++) {
    const row = [];
    for (let c = 0; c < cols; c++) {
      let hit = false;
      let hitN = 0;

      for (let n = -2; n <= numStrands + 2; n++) {
        // Each row n is chased forward by n·chase squares
        const offset = ((n * chase) % pitch + pitch * 100) % pitch;
        const xShifted = ((c - offset) % pitch + pitch * 100) % pitch;
        const inSeg = xShifted < segLen;
        if (!inSeg) continue;

        const cy = n * d + archY(xShifted, segLen, A, skew);
        if (Math.abs(r - cy) < strandW / 2) {
          hit = true; hitN = n; break;
        }
      }

      if (hit) {
        const idx = ((hitN % 3) + 3) % 3;
        // FIX: bw alternates cleanly on even/odd strand, not every-3rd
        if (colorMode === "bw")   row.push(((hitN % 2) + 2) % 2 === 0 ? 1 : 2);
        else if (colorMode === "mono") row.push(1);
        else if (colorMode === "tri")  row.push(idx === 0 ? 1 : idx === 1 ? 2 : 3);
        else row.push(1);
      } else {
        row.push(0);
      }
    }
    grid.push(row);
  }
  return grid;
}

// ─── PROFILE CANVAS (single wave cross-section) ──────────────────
function ProfileCanvas({ A, segLen, gap, skew, strandW, vColors, W, H }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = UI.bg; ctx.fillRect(0, 0, W, H);

    const pitch = segLen + gap;
    const scaleX = W / (pitch * 2.2);
    const scaleY = H / (A * 3 + strandW * 2);
    const baseY = H * 0.85;

    // Draw two consecutive segments to show the chase relationship
    for (let seg = 0; seg < 2; seg++) {
      const xOff = seg * pitch * scaleX + 10;

      // Fill the arch shape
      ctx.beginPath();
      ctx.moveTo(xOff, baseY);
      for (let lx = 0; lx <= segLen; lx += 0.2) {
        const y = archY(lx, segLen, A, skew);
        ctx.lineTo(xOff + lx * scaleX, baseY - y * scaleY);
      }
      ctx.lineTo(xOff + segLen * scaleX, baseY);
      ctx.closePath();
      ctx.fillStyle = seg === 0 ? "rgba(200,160,50,0.15)" : "rgba(200,160,50,0.08)";
      ctx.fill();

      // Centerline
      ctx.beginPath();
      ctx.moveTo(xOff, baseY);
      for (let lx = 0; lx <= segLen; lx += 0.3) {
        const y = archY(lx, segLen, A, skew);
        ctx.lineTo(xOff + lx * scaleX, baseY - y * scaleY);
      }
      ctx.strokeStyle = seg === 0 ? UI.gold : "rgba(200,160,50,0.5)";
      ctx.lineWidth = strandW * scaleY;
      ctx.lineCap = "round";
      ctx.stroke();
    }

    // Peak marker
    const peakX = skew * segLen;
    const peakPx = 10 + peakX * scaleX;
    const peakPy = baseY - A * scaleY;
    ctx.strokeStyle = "rgba(200,80,50,0.6)";
    ctx.lineWidth = 1; ctx.setLineDash([2, 3]);
    ctx.beginPath(); ctx.moveTo(peakPx, peakPy - 4); ctx.lineTo(peakPx, baseY); ctx.stroke();
    ctx.setLineDash([]);

    // Swell label (long gradual side)
    ctx.fillStyle = "rgba(200,160,50,0.5)";
    ctx.font = "8px 'Courier New'";
    ctx.fillText("swell ←", 12, baseY - A * scaleY * 0.5);
    ctx.fillText("→ crash", peakPx + 3, baseY - A * scaleY * 0.5);

    // Amplitude arrow
    ctx.strokeStyle = "rgba(200,160,50,0.4)"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(4, baseY); ctx.lineTo(4, peakPy); ctx.stroke();
    ctx.fillStyle = "rgba(200,160,50,0.6)";
    ctx.fillText(`A`, 6, (baseY + peakPy) / 2 + 3);

    // Gap zone
    const gapStart = 10 + segLen * scaleX;
    const gapEnd = 10 + pitch * scaleX;
    ctx.fillStyle = "rgba(200,80,50,0.06)";
    ctx.fillRect(gapStart, 0, gapEnd - gapStart, H);
    ctx.fillStyle = "rgba(200,80,50,0.4)";
    ctx.font = "7px 'Courier New'";
    ctx.fillText("gap", gapStart + 2, baseY - 4);

  }, [A, segLen, gap, skew, strandW, W, H]);
  return <canvas ref={ref} style={{ border:`1px solid ${UI.border}`, borderRadius:"3px", display:"block", width:"100%" }} />;
}

// ─── JIG CANVAS ──────────────────────────────────────────────────
function JigCanvas({ cols, rows, A, segLen, gap, d, strandW, numStrands, skew, chase, vColors, W, H }) {
  const ref = useRef(null);
  const pitch = segLen + gap;
  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = UI.bg; ctx.fillRect(0, 0, W, H);
    const scaleX = W / cols;
    const scaleY = H / rows;
    const midY = H * 0.5;

    for (let n = -1; n <= numStrands + 1; n++) {
      const offset = ((n * chase) % pitch + pitch * 100) % pitch;
      const baseY = n * d;
      ctx.strokeStyle = ((n % 3) + 3) % 3 === 0 ? "#f0e8d0" : vColors[2];
      ctx.lineWidth = Math.max(strandW * scaleY * 0.8, 1);
      ctx.lineCap = "round";

      for (let k = -1; k <= Math.ceil(cols / pitch) + 1; k++) {
        const xStart = k * pitch + offset;
        if (xStart > cols || xStart + segLen < 0) continue;
        ctx.beginPath();
        let started = false;
        for (let lx = 0; lx <= segLen; lx += 0.4) {
          const cx = xStart + lx;
          if (cx < 0 || cx > cols) continue;
          const y = archY(lx, segLen, A, skew);
          const px = cx * scaleX;
          const py = (baseY + y) * scaleY + midY;
          if (!started) { ctx.moveTo(px, py); started = true; }
          else ctx.lineTo(px, py);
        }
        ctx.stroke();
      }
    }

    // Direction arrow
    ctx.strokeStyle = "rgba(200,160,50,0.5)"; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(W - 40, 12); ctx.lineTo(W - 10, 12); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(W - 16, 8); ctx.lineTo(W - 10, 12); ctx.lineTo(W - 16, 16); ctx.stroke();
    ctx.fillStyle = "rgba(200,160,50,0.5)"; ctx.font = "8px 'Courier New'";
    ctx.fillText("→ travel", W - 60, 10);

  }, [cols, rows, A, segLen, gap, d, strandW, numStrands, skew, chase, vColors, W, H]);
  return <canvas ref={ref} style={{ border:`1px solid ${UI.border}`, borderRadius:"3px", display:"block", width:"100%" }} />;
}

// ─── GRID CANVAS ─────────────────────────────────────────────────
function GridCanvas({ grid, vColors, cellSize, showGuides, segLen, gap }) {
  const ref = useRef(null);
  const cols = grid[0]?.length ?? 0;
  const nRows = grid.length;
  const pitch = segLen + gap;

  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    const W = cols * cellSize, H = nRows * cellSize;
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    const hexToRgb = h => ({ r:parseInt(h.slice(1,3),16), g:parseInt(h.slice(3,5),16), b:parseInt(h.slice(5,7),16) });
    const rgb = vColors.map(hexToRgb);
    const imgData = ctx.createImageData(W, H);
    const data = imgData.data;
    for (let r = 0; r < nRows; r++) {
      for (let c = 0; c < cols; c++) {
        const v = grid[r][c];
        const px = rgb[v] ?? rgb[0];
        for (let py = r*cellSize; py < (r+1)*cellSize; py++) {
          for (let pxx = c*cellSize; pxx < (c+1)*cellSize; pxx++) {
            const idx = (py*W+pxx)*4;
            data[idx]=px.r; data[idx+1]=px.g; data[idx+2]=px.b; data[idx+3]=255;
          }
        }
      }
    }
    ctx.putImageData(imgData, 0, 0);
    if (cellSize >= 5) {
      ctx.strokeStyle = "rgba(90,60,20,0.12)"; ctx.lineWidth = 0.5;
      for (let c=0;c<=cols;c++){ctx.beginPath();ctx.moveTo(c*cellSize,0);ctx.lineTo(c*cellSize,H);ctx.stroke();}
      for (let r=0;r<=nRows;r++){ctx.beginPath();ctx.moveTo(0,r*cellSize);ctx.lineTo(W,r*cellSize);ctx.stroke();}
    }
    if (showGuides) {
      ctx.strokeStyle="rgba(200,160,50,0.3)"; ctx.lineWidth=1; ctx.setLineDash([3,3]);
      for (let k=0; k*pitch<=cols+pitch; k++) {
        const x = k*pitch*cellSize;
        if (x<=W){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
      }
      ctx.setLineDash([]);
      // Direction arrow
      ctx.strokeStyle="rgba(200,160,50,0.45)"; ctx.lineWidth=1.5;
      const ay=H-10, ax1=10, ax2=60;
      ctx.beginPath();ctx.moveTo(ax1,ay);ctx.lineTo(ax2,ay);ctx.stroke();
      ctx.beginPath();ctx.moveTo(ax2-8,ay-5);ctx.lineTo(ax2,ay);ctx.lineTo(ax2-8,ay+5);ctx.stroke();
    }
  }, [grid, vColors, cellSize, showGuides, segLen, gap]);

  return <canvas ref={ref} style={{ border:`1px solid ${UI.border}`, borderRadius:"3px", display:"block", maxWidth:"100%", imageRendering:cellSize<=4?"pixelated":"auto" }} />;
}

// ─── ROSETTE RING ────────────────────────────────────────────────
function RosetteCanvas({ grid, vColors, rIn, rOut, size }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    canvas.width = size; canvas.height = size;
    const ctx = canvas.getContext("2d");
    const cx=size/2, cy=size/2;
    ctx.fillStyle=UI.bg; ctx.fillRect(0,0,size,size);
    if (!grid?.length) return;
    const nR=grid.length, nC=grid[0].length;
    const ringW=rOut-rIn, circ=2*Math.PI*(rIn+rOut)/2;
    const h = hex => ({r:parseInt(hex.slice(1,3),16),g:parseInt(hex.slice(3,5),16),b:parseInt(hex.slice(5,7),16)});
    const rgb = vColors.map(h);
    ctx.beginPath();ctx.arc(cx,cy,rIn,0,Math.PI*2);ctx.fillStyle="#060402";ctx.fill();
    const img=ctx.createImageData(size,size); const d=img.data;
    for (let py=0;py<size;py++) for (let px=0;px<size;px++){
      const dx=px-cx,dy=py-cy,dist=Math.sqrt(dx*dx+dy*dy);
      if(dist<rIn||dist>rOut)continue;
      const row=Math.min(Math.floor((dist-rIn)/ringW*nR),nR-1);
      const ang=Math.atan2(dy,dx)+Math.PI;
      const col=((Math.floor(ang*(rIn+rOut)/2/(circ/nC))%nC)+nC)%nC;
      const v=grid[row]?.[col]??0;
      const c=rgb[v]??rgb[0];
      const i=(py*size+px)*4;
      d[i]=c.r;d[i+1]=c.g;d[i+2]=c.b;d[i+3]=255;
    }
    ctx.putImageData(img,0,0);
    ctx.strokeStyle="rgba(200,160,50,0.3)";ctx.lineWidth=0.8;ctx.setLineDash([3,4]);
    [rIn,rOut].forEach(r=>{ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();});
    ctx.setLineDash([]);
  }, [grid, vColors, rIn, rOut, size]);
  return <canvas ref={ref} style={{ borderRadius:"50%", border:`1px solid ${UI.border}`, display:"block" }} />;
}

// ─── KNOB ────────────────────────────────────────────────────────
function Knob({ label, val, set, min, max, step=1, unit="", note="" }) {
  return (
    <div style={{ marginBottom:"10px" }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"2px" }}>
        <span style={{ fontSize:"9px", letterSpacing:"1.5px", color:UI.dim }}>{label}</span>
        <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{typeof val==="number"&&!Number.isInteger(val)?val.toFixed(2):val}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val}
        onChange={e=>set(Number(e.target.value))} style={{ width:"100%", accentColor:"#c9a96e" }} />
      {note&&<div style={{ fontSize:"8px", color:UI.dimmer, marginTop:"1px" }}>{note}</div>}
    </div>
  );
}

// ─── MAIN ────────────────────────────────────────────────────────
export default function WaveRosetteV3() {
  // Core wave parameters
  const [A,          setA]          = useState(6);
  const [segLen,     setSegLen]     = useState(18);
  const [gap,        setGap]        = useState(2);
  const [skew,       setSkew]       = useState(0.72);  // peak position along segment
  const [chase,      setChase]      = useState(13);    // row stagger — optimal: skew×segLen = 0.72×18 = 13

  // Strand array
  const [d,          setD]          = useState(4);
  const [strandW,    setStrandW]    = useState(1.8);
  const [numStrands, setNumStrands] = useState(7);

  // Grid
  const [cols, setCols] = useState(52);
  const [rows, setRows] = useState(18);

  // Color
  const [colorMode, setColorMode] = useState("tri");
  const [c0, setC0] = useState("#1a1008");
  const [c1, setC1] = useState("#f0e8d0");
  const [c2, setC2] = useState("#8b2020");
  const [c3, setC3] = useState("#2d6a4f");

  // View
  const [cellSize,   setCellSize]   = useState(12);
  const [showGuides, setShowGuides] = useState(true);
  const [rIn,        setRIn]        = useState(90);
  const [rOut,       setROut]       = useState(138);
  const [tab,        setTab]        = useState("grid");

  const pitch = segLen + gap;
  const vColors = [c0, c1, c2, c3];
  const grid = buildCrashGrid({ cols, rows, A, segLen, gap, d, strandW, numStrands, skew, chase, colorMode });

  const counts = {};
  grid.forEach(row => row.forEach(v => counts[v]=(counts[v]||0)+1));
  const total = cols*rows;
  const mmW = (cols*0.5).toFixed(1);
  const mmH = (rows*0.5).toFixed(1);
  const peakAt = (skew*100).toFixed(0);

  return (
    <div style={{ minHeight:"100vh", background:UI.bg, fontFamily:"'Courier New',monospace", color:UI.text, padding:"20px", userSelect:"none" }}>

      {/* HEADER */}
      <div style={{ borderBottom:`1px solid ${UI.border2}`, paddingBottom:"12px", marginBottom:"16px" }}>
        <div style={{ fontSize:"9px", letterSpacing:"4px", color:UI.dimmer }}>
          THE PRODUCTION SHOP · CUSTOM INLAY MODULE · V3
        </div>
        <div style={{ fontSize:"22px", fontWeight:"bold", color:UI.gold, letterSpacing:"3px", marginTop:"3px" }}>
          Crashing Wave Rosette
        </div>
        <div style={{ fontSize:"10px", color:UI.dimmer, marginTop:"2px", letterSpacing:"1px" }}>
          Asymmetric arch · directional momentum · each wave chasing the one ahead
        </div>

        {/* PRESET BUTTONS */}
        <div style={{ marginTop:"10px", display:"flex", gap:"6px", flexWrap:"wrap", alignItems:"center" }}>
          <span style={{ fontSize:"8px", letterSpacing:"2px", color:UI.dimmer }}>PRESETS</span>
          {[
            { label:"Torres / Ramirez", params:{ A:6, segLen:18, gap:2, skew:0.72, chase:13, d:4, strandW:1.8, numStrands:7, cols:52, rows:18, colorMode:"tri", c2:"#8b2020" } },
            { label:"Gentle Swell",     params:{ A:4, segLen:22, gap:3, skew:0.55, chase:12, d:5, strandW:2,   numStrands:6, cols:52, rows:18, colorMode:"bw",  c2:"#8b2020" } },
            { label:"Tight Crash",      params:{ A:8, segLen:14, gap:2, skew:0.82, chase:11, d:4, strandW:1.5, numStrands:8, cols:52, rows:18, colorMode:"tri", c2:"#1a4a8b" } },
          ].map(({ label, params }) => (
            <div key={label} onClick={() => {
              setA(params.A); setSegLen(params.segLen); setGap(params.gap);
              setSkew(params.skew); setChase(params.chase); setD(params.d);
              setStrandW(params.strandW); setNumStrands(params.numStrands);
              setCols(params.cols); setRows(params.rows);
              setColorMode(params.colorMode); setC2(params.c2);
            }} style={{
              padding:"4px 10px", cursor:"pointer", fontSize:"9px", letterSpacing:"0.5px",
              border:`1px solid ${UI.border}`, borderRadius:"3px",
              background:"transparent", color:UI.amber,
              transition:"all .1s",
            }}
            onMouseEnter={e=>{ e.target.style.borderColor="#c9a96e"; e.target.style.background="#1e1508"; }}
            onMouseLeave={e=>{ e.target.style.borderColor=UI.border; e.target.style.background="transparent"; }}
            >{label}</div>
          ))}
        </div>

        {/* Formula */}
        <div style={{ marginTop:"8px", padding:"8px 12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px", display:"inline-flex", flexWrap:"wrap", gap:"6px", alignItems:"center" }}>
          <span style={{ fontSize:"9px", color:UI.dimmer }}>
            swell: <span style={{ color:UI.gold }}>A·sin(π/2 · x / peakX)</span>
          </span>
          <span style={{ fontSize:"9px", color:UI.dimmest }}>|</span>
          <span style={{ fontSize:"9px", color:UI.dimmer }}>
            crash: <span style={{ color:UI.gold }}>A·cos(π/2 · (x−peakX) / (segLen−peakX))</span>
          </span>
          <span style={{ fontSize:"9px", color:UI.dimmest }}>|</span>
          <span style={{ fontSize:"9px", color:UI.dimmer }}>
            peak at <span style={{ color:UI.gold }}>{peakAt}%</span> · chase <span style={{ color:UI.gold }}>{chase}</span> sq/row
          </span>
        </div>

        <div style={{ marginTop:"8px", display:"flex", gap:"5px", flexWrap:"wrap" }}>
          {[
            ["skew",`${peakAt}% → crash steepness`],
            ["swell",`${(skew*segLen*0.5).toFixed(1)}mm`],
            ["crash face",`${((1-skew)*segLen*0.5).toFixed(1)}mm`],
            ["chase",`${(chase*0.5).toFixed(1)}mm/row`],
            ["tile",`${mmW}×${mmH}mm`],
          ].map(([a,b])=>(
            <div key={a} style={{ padding:"3px 8px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px", fontSize:"9px", color:UI.dimmer }}>
              <span style={{ color:UI.gold, fontWeight:"bold" }}>{a}</span> {b}
            </div>
          ))}
        </div>
      </div>

      {/* TABS */}
      <div style={{ display:"flex", gap:"4px", marginBottom:"16px", flexWrap:"wrap" }}>
        {[["grid","Pixel Grid"],["profile","Wave Profile"],["jig","Jig View"],["ring","Rosette Ring"],["bom","BOM"],["csv","CSV Export"]].map(([k,l])=>(
          <div key={k} onClick={()=>setTab(k)} style={{
            padding:"5px 14px", cursor:"pointer", fontSize:"10px", letterSpacing:"1px",
            border:tab===k?"1px solid #c9a96e":`1px solid ${UI.border}`,
            borderRadius:"3px", background:tab===k?"#1e1508":"transparent",
            color:tab===k?UI.gold:UI.dim, transition:"all .12s",
          }}>{l}</div>
        ))}
      </div>

      <div style={{ display:"flex", gap:"18px", flexWrap:"wrap" }}>

        {/* ── CONTROLS ── */}
        <div style={{ width:"202px", flexShrink:0 }}>

          {/* THE KEY CONTROLS */}
          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>WAVE SHAPE</div>

            <Knob label="A — Arch height" val={A} set={setA} min={0} max={16} step={0.5}
              unit=" sq" note={`${(A*0.5).toFixed(1)}mm peak height`} />

            <Knob label="segLen — Wave length" val={segLen} set={setSegLen} min={6} max={40}
              unit=" sq" note={`${(segLen*0.5).toFixed(1)}mm per wave`} />

            <Knob label="gap — Air between waves" val={gap} set={setGap} min={0} max={12}
              unit=" sq" note={`${(gap*0.5).toFixed(1)}mm gap`} />

            {/* The critical skew slider */}
            <div style={{ marginBottom:"10px" }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"2px" }}>
                <span style={{ fontSize:"9px", letterSpacing:"1.5px", color:UI.dim }}>skew — Peak position</span>
                <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{peakAt}%</span>
              </div>
              <input type="range" min={0.1} max={0.95} step={0.01} value={skew}
                onChange={e=>setSkew(Number(e.target.value))} style={{ width:"100%", accentColor:"#c9a96e" }} />
              <div style={{ display:"flex", justifyContent:"space-between", marginTop:"2px" }}>
                <span style={{ fontSize:"7px", color:UI.dimmer }}>← crash-first</span>
                <span style={{ fontSize:"7px", color:UI.amber }}>50% = symmetric</span>
                <span style={{ fontSize:"7px", color:UI.dimmer }}>swell-first →</span>
              </div>
              <div style={{ fontSize:"8px", color:UI.dimmer, marginTop:"2px" }}>
                swell={`${(skew*segLen*0.5).toFixed(1)}`}mm · crash={`${((1-skew)*segLen*0.5).toFixed(1)}`}mm
              </div>
            </div>
          </div>

          {/* CHASE — the key to the "chasing" illusion */}
          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"4px" }}>WAVE PROCESSION</div>
            <div style={{ fontSize:"8px", color:UI.dimmer, marginBottom:"8px", lineHeight:"1.6" }}>
              How far back each successive row starts its wave. Set to match swell length for waves in-phase behind each other.
            </div>
            <Knob label="chase — Lag per row" val={chase} set={setChase} min={0} max={pitch} step={1}
              unit=" sq"
              note={chase===0?"no lag — all waves aligned":Math.abs(chase - Math.round(skew*segLen))<=1?`✓ in-phase (≈ swell length)`:`${(chase*0.5).toFixed(1)}mm lag · optimal=${Math.round(skew*segLen)}`} />

            {/* Preset chase values */}
            <div style={{ marginTop:"4px" }}>
              <div style={{ fontSize:"8px", color:UI.dimmer, marginBottom:"4px" }}>Presets</div>
              <div style={{ display:"flex", gap:"3px", flexWrap:"wrap" }}>
                {[
                  [0,                         "locked"],
                  [Math.round(skew*segLen*0.5), "½ swell"],
                  [Math.round(skew*segLen),     "full swell"],
                  [Math.round(pitch/3),         "⅓ pitch"],
                  [Math.round(pitch/2),         "½ pitch"],
                ].map(([v,l])=>(
                  <div key={l} onClick={()=>setChase(v)} style={{
                    padding:"2px 6px", cursor:"pointer", fontSize:"8px",
                    border:chase===v?"1px solid #c9a96e":`1px solid ${UI.border}`,
                    borderRadius:"3px", background:chase===v?"#1e1508":"transparent",
                    color:chase===v?UI.gold:UI.dim,
                  }}>{l}</div>
                ))}
              </div>
            </div>
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>STRAND ARRAY</div>
            <Knob label="d — Row pitch" val={d} set={setD} min={2} max={14} step={0.5}
              unit=" sq" note={`${(d*0.5).toFixed(1)}mm center-to-center`} />
            <Knob label="w — Strand width" val={strandW} set={setStrandW} min={0.5} max={6} step={0.5}
              unit=" sq" note={`${(strandW*0.5).toFixed(1)}mm veneer`} />
            <Knob label="N — Strand rows" val={numStrands} set={setNumStrands} min={2} max={14} />
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"8px" }}>TILE SIZE</div>
            <Knob label="Columns" val={cols} set={setCols} min={16} max={80} note={`${mmW}mm`} />
            <Knob label="Rows"    val={rows} set={setRows} min={8}  max={44} note={`${mmH}mm`} />
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"8px" }}>VENEER</div>
            {[["bw","Alt B/W"],["mono","Single"],["tri","3-color"]].map(([v,l])=>(
              <div key={v} onClick={()=>setColorMode(v)} style={{
                padding:"3px 7px", marginBottom:"3px", cursor:"pointer", fontSize:"9px",
                border:colorMode===v?"1px solid #c9a96e":`1px solid ${UI.border}`,
                borderRadius:"3px", background:colorMode===v?"#1e1508":"transparent",
                color:colorMode===v?UI.gold:UI.dim,
              }}>{l}</div>
            ))}
            <div style={{ marginTop:"8px" }}>
              {[["Background",c0,setC0],["Strand A",c1,setC1],["Strand B",c2,setC2],["Strand C",c3,setC3]].map(([l,v,s])=>(
                <div key={l} style={{ display:"flex", alignItems:"center", gap:"7px", marginBottom:"5px" }}>
                  <input type="color" value={v} onChange={e=>s(e.target.value)}
                    style={{ width:"24px", height:"20px", border:`1px solid ${UI.border}`, borderRadius:"2px", cursor:"pointer", padding:"1px" }} />
                  <span style={{ fontSize:"9px", color:UI.dim }}>{l}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"8px" }}>VIEW</div>
            <Knob label="Cell size" val={cellSize} set={setCellSize} min={3} max={26} unit=" px" />
            <Knob label="Ring r_in"  val={rIn}  set={setRIn}  min={40} max={180} unit=" px" />
            <Knob label="Ring r_out" val={rOut} set={setROut} min={60} max={200} unit=" px" />
            <div onClick={()=>setShowGuides(g=>!g)} style={{
              padding:"4px 7px", cursor:"pointer", fontSize:"9px",
              border:showGuides?"1px solid #c9a96e":`1px solid ${UI.border}`,
              borderRadius:"3px", background:showGuides?"#1e1508":"transparent",
              color:showGuides?UI.gold:UI.dim,
            }}>Wave guides</div>
          </div>
        </div>

        {/* ── MAIN VIEW ── */}
        <div style={{ flex:1, minWidth:0 }}>

          {tab==="grid" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                PIXEL GRID · {cols}×{rows} · 0.5mm/sq · waves travel →
              </div>
              <GridCanvas grid={grid} vColors={vColors} cellSize={cellSize}
                showGuides={showGuides} segLen={segLen} gap={gap} />
              <div style={{ marginTop:"8px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.8" }}>
                Peak at <span style={{ color:UI.gold }}>{peakAt}%</span> through segment —
                left of peak = gradual swell, right of peak = steep crash face.
                Each row lags <span style={{ color:UI.gold }}>{chase}</span> sq behind the row above.
              </div>
            </div>
          )}

          {tab==="profile" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                SINGLE WAVE CROSS-SECTION · Two consecutive segments shown
              </div>
              <ProfileCanvas A={A} segLen={segLen} gap={gap} skew={skew} strandW={strandW}
                vColors={vColors} W={Math.min(cols*cellSize, 580)} H={120} />
              <div style={{ marginTop:"10px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
                <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>WAVE ANATOMY</div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:"5px" }}>
                  {[
                    ["Swell length",   `${(skew*segLen*0.5).toFixed(2)}mm`],
                    ["Crash length",   `${((1-skew)*segLen*0.5).toFixed(2)}mm`],
                    ["Peak height A",  `${(A*0.5).toFixed(2)}mm`],
                    ["Gap",            `${(gap*0.5).toFixed(2)}mm`],
                    ["Pitch",          `${(pitch*0.5).toFixed(2)}mm`],
                    ["Swell/crash ratio", `${(skew/(1-skew)).toFixed(2)}:1`],
                  ].map(([k,v])=>(
                    <div key={k} style={{ padding:"4px 6px", background:UI.bg, border:`1px solid ${UI.border2}`, borderRadius:"2px" }}>
                      <div style={{ fontSize:"8px", color:UI.dimmer }}>{k}</div>
                      <div style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{v}</div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop:"8px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.8" }}>
                  Swell/crash ratio of <span style={{ color:UI.gold }}>{(skew/(1-skew)).toFixed(2)}:1</span> —
                  {skew > 0.6 ? " steep crash face (wave breaking forward)" :
                   skew < 0.4 ? " steep swell face (wave pulling back)" :
                   " near-symmetric (gentle wave)"}.<br/>
                  Adjust <span style={{ color:UI.amber }}>skew</span> to control how aggressively the wave breaks.
                  Classical guitar rosettes typically use skew 0.6–0.8.
                </div>
              </div>
            </div>
          )}

          {tab==="jig" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                JIG PROFILE · All strand rows · Arrow shows wave travel direction
              </div>
              <JigCanvas cols={cols} rows={rows} A={A} segLen={segLen} gap={gap}
                d={d} strandW={strandW} numStrands={numStrands} skew={skew} chase={chase}
                vColors={vColors}
                W={Math.min(cols*cellSize, 620)} H={Math.max(rows*cellSize, 160)} />
              <div style={{ marginTop:"10px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.9" }}>
                <span style={{ color:UI.amber }}>Caul profile:</span> asymmetric arch A={(A*0.5).toFixed(1)}mm over {(segLen*0.5).toFixed(1)}mm, peak at {peakAt}%.<br/>
                Each row of the caul is offset <span style={{ color:UI.gold }}>{(chase*0.5).toFixed(1)}mm</span> in the wave direction, creating the chasing procession.<br/>
                The angle of the crash face ≈ <span style={{ color:UI.gold }}>{(Math.atan(A/((1-skew)*segLen))*180/Math.PI).toFixed(1)}°</span> from horizontal.
              </div>
            </div>
          )}

          {tab==="ring" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                ROSETTE RING · Tile wrapped to annulus · r_in={rIn}px r_out={rOut}px
              </div>
              <RosetteCanvas grid={grid} vColors={vColors} rIn={rIn} rOut={rOut} size={360} />
              <div style={{ marginTop:"8px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.7" }}>
                Waves crash radially — steep face toward the inner ring, swell toward outer.
                The chasing procession appears as a rotational sweep around the soundhole.
              </div>
            </div>
          )}

          {tab==="bom" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>VENEER BOM · {rows} rows × {cols} cols</div>
              <div style={{ maxHeight:"400px", overflowY:"auto", border:`1px solid ${UI.border}`, borderRadius:"3px" }}>
                {grid.map((row,r)=>{
                  const parts=[];let cur=row[0],run=1;
                  for(let c=1;c<cols;c++){if(row[c]===cur)run++;else{parts.push({v:cur,n:run});cur=row[c];run=1;}}
                  parts.push({v:cur,n:run});
                  const lbl=["BG","A","B","C"];
                  const tc=v=>v===1?"#1a1008":"#c9a96e";
                  return(
                    <div key={r} style={{ display:"flex",alignItems:"center",gap:"4px",padding:"3px 8px",borderBottom:`1px solid ${UI.dimmest}`,background:r%2===0?"transparent":"#0c0903" }}>
                      <span style={{ fontSize:"7px",color:UI.dimmer,width:"18px",flexShrink:0 }}>{r+1}</span>
                      <span style={{ fontSize:"7px",color:UI.dimmer,width:"26px",flexShrink:0 }}>{((r+1)*0.5).toFixed(1)}</span>
                      <div style={{ display:"flex",gap:"2px",flexWrap:"wrap",flex:1 }}>
                        {parts.map((p,i)=>(
                          <span key={i} style={{ padding:"1px 3px",borderRadius:"2px",background:vColors[p.v],border:p.v===0?`1px solid ${UI.border}`:"none",fontSize:"8px",color:tc(p.v),fontWeight:"bold" }}>
                            {p.n}{lbl[p.v]}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div style={{ marginTop:"8px",padding:"8px",background:UI.panel,border:`1px solid ${UI.border}`,borderRadius:"3px",display:"grid",gridTemplateColumns:"1fr 1fr",gap:"4px" }}>
                {[["BG cells",counts[0]||0],["Strand A",counts[1]||0],["Strand B",counts[2]||0],["Strand C",counts[3]||0],["Tile",`${mmW}×${mmH}`],["Pitch",`${(pitch*0.5).toFixed(1)}mm`]].map(([k,v])=>(
                  <div key={k} style={{ display:"flex",justifyContent:"space-between",padding:"3px 6px",background:UI.bg,borderRadius:"2px",border:`1px solid ${UI.border2}` }}>
                    <span style={{ fontSize:"9px",color:UI.dimmer }}>{k}</span>
                    <span style={{ fontSize:"10px",color:UI.gold,fontWeight:"bold" }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {tab==="csv" && (() => {
            const csvContent = grid.map(r => r.join(",")).join("\n");
            const header = `# Wave Rosette Tile · ${cols}×${rows} · 0.5mm/sq\n# A=${A} segLen=${segLen} gap=${gap} skew=${skew} chase=${chase} d=${d} strandW=${strandW}\n# 0=bg  1=strandA  2=strandB  3=strandC\n`;
            const full = header + csvContent;
            const blob = new Blob([full], { type:"text/csv" });
            const url = URL.createObjectURL(blob);
            return (
              <div>
                <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                  CSV EXPORT · {cols}×{rows} · Fusion 360 / CNC ready
                </div>
                <div style={{ padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
                  <div style={{ fontSize:"9px", color:UI.dim, letterSpacing:"2px", marginBottom:"6px" }}>FORMAT</div>
                  <div style={{ fontSize:"8px", color:UI.dimmer, lineHeight:"2" }}>
                    Rows = tile rows (Y axis) · Cols = tile columns (X axis)<br/>
                    Values: <span style={{ color:UI.gold }}>0</span>=background · <span style={{ color:UI.gold }}>1</span>=strand A · <span style={{ color:UI.gold }}>2</span>=strand B · <span style={{ color:UI.gold }}>3</span>=strand C<br/>
                    Scale: <span style={{ color:UI.gold }}>0.5mm per cell</span> · {mmW}mm × {mmH}mm tile<br/>
                    Python: <span style={{ color:UI.amber }}>np.loadtxt('wave_tile.csv', delimiter=',')</span>
                  </div>
                </div>
                <div style={{ marginBottom:"10px", fontFamily:"'Courier New',monospace", fontSize:"8px", color:UI.dimmer,
                  background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px",
                  padding:"8px", maxHeight:"220px", overflowY:"auto", lineHeight:"1.6" }}>
                  {grid.slice(0,8).map((r,i)=>(
                    <div key={i}>{r.join(",")}</div>
                  ))}
                  <div style={{ color:UI.dimmest }}>... {rows - 8} more rows ...</div>
                </div>
                <a href={url} download={`wave_rosette_${cols}x${rows}_A${A}_skew${Math.round(skew*100)}_chase${chase}.csv`}
                  style={{ display:"inline-block", padding:"8px 18px", background:"#1e1508",
                    border:"1px solid #c9a96e", borderRadius:"3px", color:UI.gold,
                    fontSize:"10px", letterSpacing:"1px", textDecoration:"none", cursor:"pointer" }}>
                  ↓ Download CSV
                </a>
                <div style={{ marginTop:"8px", fontSize:"8px", color:UI.dimmer }}>
                  Filename: wave_rosette_{cols}x{rows}_A{A}_skew{Math.round(skew*100)}_chase{chase}.csv
                </div>
              </div>
            );
          })()}


        <div style={{ width:"186px", flexShrink:0 }}>
          <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>RING PREVIEW</div>
          <RosetteCanvas grid={grid} vColors={vColors} rIn={rIn*0.42} rOut={rOut*0.42} size={182} />

          <div style={{ marginTop:"10px", marginBottom:"5px", fontSize:"9px", letterSpacing:"2px", color:UI.dim }}>TILE SNAPSHOT</div>
          <div style={{ display:"inline-block", border:`1px solid ${UI.border}`, borderRadius:"2px", overflow:"hidden" }}>
            {grid.map((row,r)=>(
              <div key={r} style={{ display:"flex" }}>
                {row.map((v,c)=>(<div key={c} style={{ width:"4px",height:"4px",background:vColors[v] }}/>))}
              </div>
            ))}
          </div>
          <div style={{ fontSize:"8px", color:UI.dimmer, marginTop:"2px" }}>{cols}×{rows} @ 4px</div>

          {/* Wave profile mini-diagram */}
          <div style={{ marginTop:"10px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>WAVE PROFILE</div>
            <svg width="162" height="56">
              {/* Draw live wave profile */}
              <path
                d={`M 4,46 ` + Array.from({length:100},(_,i)=>{
                  const lx = i/99*segLen;
                  const y = archY(lx, segLen, 1, skew);
                  const px = 4 + (lx/Math.max(segLen+gap,1))*150;
                  const py = 46 - y*32;
                  return `L ${px.toFixed(1)},${py.toFixed(1)}`;
                }).join(" ")}
                fill="rgba(200,160,50,0.1)" stroke={UI.gold} strokeWidth="2" strokeLinecap="round"
              />
              {/* Gap zone */}
              <rect x={4+segLen/(segLen+gap)*150} y="10" width={gap/(segLen+gap)*150} height="40"
                fill="rgba(200,80,50,0.06)" />
              {/* Baseline */}
              <line x1="4" y1="46" x2="154" y2="46" stroke={UI.dimmest} strokeWidth="0.5" />
              {/* Peak marker */}
              <line x1={4+skew*segLen/(segLen+gap)*150} y1="12" x2={4+skew*segLen/(segLen+gap)*150} y2="46"
                stroke="rgba(200,80,50,0.4)" strokeWidth="1" strokeDasharray="2,2" />
              {/* Labels */}
              <text x="5" y="55" fill={UI.dimmer} fontSize="7" fontFamily="Courier New">swell</text>
              <text x={4+skew*segLen/(segLen+gap)*150+2} y="55" fill={UI.dimmer} fontSize="7" fontFamily="Courier New">crash</text>
            </svg>
          </div>

          {/* Geometry check */}
          <div style={{ marginTop:"8px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>CHECK</div>
            <div style={{ fontSize:"8px", color:UI.dimmer, lineHeight:"2" }}>
              <span style={{ color:d>strandW?"#2d9a6f":"#8b2020" }}>{d>strandW?"✓":"⚠"} d&gt;w</span><br/>
              <span style={{ color:gap>0?"#2d9a6f":"#e8c87a" }}>{gap>0?"✓":"△"} gap&gt;0</span><br/>
              <span style={{ color:A<d*numStrands?"#2d9a6f":"#e8c87a" }}>{A<d*numStrands?"✓":"△"} A fits grid</span><br/>
              <span style={{ color:parseFloat(mmH)>=5&&parseFloat(mmH)<=9?"#2d9a6f":"#e8c87a" }}>
                {parseFloat(mmH)>=5&&parseFloat(mmH)<=9?"✓":"△"} {mmH}mm tile height
              </span><br/>
              <span style={{ color:skew>0.5&&skew<0.9?"#2d9a6f":"#e8c87a" }}>
                {skew>0.5&&skew<0.9?"✓":"△"} skew {peakAt}% {skew>0.5&&skew<0.9?"(guitaristic range)":""}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
