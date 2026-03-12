import { useState, useEffect, useRef } from "react";

const UI = {
  bg:"#0b0806", panel:"#0f0c08", border:"#2e2010", border2:"#1e1508",
  gold:"#e8c87a", amber:"#c9a96e", dim:"#7a5c2e", dimmer:"#4a3010",
  dimmest:"#2a1e0a", text:"#c9a96e",
};

// ─── THE FORMULA ─────────────────────────────────────────────────
//
// Single strand traveling along Y.
// At each row y, the strand's X center is:
//
//   x(y) = centerX + A · arch(y_local, segLen, skew)
//
// where y_local = y mod (segLen + gap)
//
// arch = swell side:  sin(π/2 · y_local / peakY)         → 0 → A
//        crash side:  cos(π/2 · (y_local−peakY) / (segLen−peakY)) · A  → A → 0
//        gap zone:    strand absent (background only)
//
// Pixel (col, row) is ON the strand if:
//   row is in an active segment AND |col − x(row)| < strandW/2

function archDisplace(localY, segLen, A, skew) {
  const peakY = skew * segLen;
  if (localY <= peakY) {
    return A * Math.sin((Math.PI / 2) * (localY / Math.max(peakY, 0.001)));
  } else {
    return A * Math.cos((Math.PI / 2) * ((localY - peakY) / Math.max(segLen - peakY, 0.001)));
  }
}

function buildStrandGrid({ cols, rows, A, segLen, gap, strandW, skew, centerFrac }) {
  const pitch = segLen + gap;
  const centerX = cols * centerFrac;
  const grid = [];

  for (let r = 0; r < rows; r++) {
    const row = new Array(cols).fill(0);
    const localY = r % pitch;
    if (localY >= segLen) {
      // gap zone — no strand
      grid.push(row);
      continue;
    }
    const dx = archDisplace(localY, segLen, A, skew);
    const strandX = centerX + dx;

    for (let c = 0; c < cols; c++) {
      if (Math.abs(c - strandX) < strandW / 2) {
        row[c] = 1;
      }
    }
    grid.push(row);
  }
  return grid;
}

// ─── PROFILE CANVAS ──────────────────────────────────────────────
// "Looking at a string from the side" — just the x(y) displacement curve
// Y = travel direction (vertical), X = displacement (horizontal)
// Renders as a single line, like an oscilloscope trace
function ProfileCanvas({ rows, A, segLen, gap, skew, strandW, cols, centerFrac, W, H }) {
  const ref = useRef(null);
  const pitch = segLen + gap;
  const centerX = W * centerFrac;

  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = UI.bg; ctx.fillRect(0, 0, W, H);

    const scaleY = H / rows;
    // X scale: map displacement range to canvas width
    const maxDisp = Math.abs(A) + strandW;
    const dispScale = (W * 0.35) / Math.max(maxDisp, 1);

    // Center axis
    ctx.strokeStyle = `rgba(200,160,50,0.12)`; ctx.lineWidth = 1; ctx.setLineDash([4,4]);
    ctx.beginPath(); ctx.moveTo(centerX, 0); ctx.lineTo(centerX, H); ctx.stroke();
    ctx.setLineDash([]);

    // Draw gap zones
    for (let r = 0; r < rows; r++) {
      const localY = r % pitch;
      if (localY >= segLen) {
        ctx.fillStyle = "rgba(200,80,50,0.05)";
        ctx.fillRect(0, r * scaleY, W, scaleY);
      }
    }

    // Draw strand as a thick path — the "string face"
    ctx.lineWidth = strandW * dispScale;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#f0e8d0";

    let inPath = false;
    ctx.beginPath();
    for (let r = 0; r < rows; r++) {
      const localY = r % pitch;
      if (localY >= segLen) {
        if (inPath) { ctx.stroke(); ctx.beginPath(); inPath = false; }
        continue;
      }
      const dx = archDisplace(localY, segLen, A, skew);
      const px = centerX + dx * dispScale;
      const py = r * scaleY;
      if (!inPath) { ctx.moveTo(px, py); inPath = true; }
      else ctx.lineTo(px, py);
    }
    if (inPath) ctx.stroke();

    // Draw the crash/swell annotation on the first segment
    const peakY = skew * segLen;
    const peakPy = peakY * scaleY;
    const peakPx = centerX + A * dispScale;

    // Swell bracket
    ctx.strokeStyle = "rgba(200,160,50,0.35)"; ctx.lineWidth = 1; ctx.setLineDash([2,3]);
    ctx.beginPath(); ctx.moveTo(W - 14, 0); ctx.lineTo(W - 14, peakPy); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(200,160,50,0.5)"; ctx.font = "8px 'Courier New'";
    ctx.save(); ctx.translate(W - 6, peakPy / 2); ctx.rotate(Math.PI / 2);
    ctx.fillText("swell", -16, 0); ctx.restore();

    // Crash bracket
    ctx.strokeStyle = "rgba(200,80,50,0.35)"; ctx.lineWidth = 1; ctx.setLineDash([2,3]);
    ctx.beginPath(); ctx.moveTo(W - 14, peakPy); ctx.lineTo(W - 14, segLen * scaleY); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(200,80,50,0.5)";
    ctx.save(); ctx.translate(W - 6, peakPy + (segLen - peakY) * scaleY / 2); ctx.rotate(Math.PI / 2);
    ctx.fillText("crash", -16, 0); ctx.restore();

    // Peak marker
    ctx.strokeStyle = "rgba(200,80,50,0.4)"; ctx.lineWidth = 1; ctx.setLineDash([2,3]);
    ctx.beginPath(); ctx.moveTo(0, peakPy); ctx.lineTo(W, peakPy); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(200,160,50,0.6)"; ctx.font = "8px 'Courier New'";
    ctx.fillText(`← A=${A}sq`, peakPx + 4, peakPy - 3);

    // Displacement arrow at peak
    ctx.strokeStyle = "rgba(200,160,50,0.4)"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(centerX, peakPy - 2); ctx.lineTo(peakPx - strandW*dispScale/2, peakPy - 2); ctx.stroke();

    // Y axis label
    ctx.fillStyle = UI.dimmer; ctx.font = "8px 'Courier New'";
    ctx.fillText("↓ y (travel)", 4, 10);
    ctx.fillText("x →", centerX + 4, H - 5);

  }, [rows, A, segLen, gap, skew, strandW, cols, centerFrac, W, H]);

  return <canvas ref={ref} style={{ border:`1px solid ${UI.border}`, borderRadius:"3px", display:"block" }} />;
}

// ─── GRID CANVAS ─────────────────────────────────────────────────
function GridCanvas({ grid, c0, c1, cellSize, showGuides, segLen, gap, rows, cols }) {
  const ref = useRef(null);
  const pitch = segLen + gap;

  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    const W = cols * cellSize, H = rows * cellSize;
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");

    const toRgb = h => ({ r:parseInt(h.slice(1,3),16), g:parseInt(h.slice(3,5),16), b:parseInt(h.slice(5,7),16) });
    const rgb = [toRgb(c0), toRgb(c1)];

    const img = ctx.createImageData(W, H); const d = img.data;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const v = grid[r]?.[c] ?? 0;
        const px = rgb[v];
        for (let py = r*cellSize; py < (r+1)*cellSize; py++) {
          for (let pxx = c*cellSize; pxx < (c+1)*cellSize; pxx++) {
            const i = (py*W+pxx)*4;
            d[i]=px.r; d[i+1]=px.g; d[i+2]=px.b; d[i+3]=255;
          }
        }
      }
    }
    ctx.putImageData(img, 0, 0);

    if (cellSize >= 5) {
      ctx.strokeStyle = "rgba(90,60,20,0.12)"; ctx.lineWidth = 0.5;
      for (let c=0;c<=cols;c++){ctx.beginPath();ctx.moveTo(c*cellSize,0);ctx.lineTo(c*cellSize,H);ctx.stroke();}
      for (let r=0;r<=rows;r++){ctx.beginPath();ctx.moveTo(0,r*cellSize);ctx.lineTo(W,r*cellSize);ctx.stroke();}
    }

    if (showGuides) {
      // Segment start lines (gold)
      ctx.strokeStyle = "rgba(200,160,50,0.35)"; ctx.lineWidth = 1; ctx.setLineDash([3,3]);
      for (let k=0; k*pitch<=rows; k++) {
        const y = k*pitch*cellSize;
        ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke();
      }
      // Gap zone
      ctx.strokeStyle = "rgba(200,80,50,0.25)";
      for (let k=0; k*pitch<=rows; k++) {
        const yEnd = (k*pitch + segLen)*cellSize;
        if (yEnd <= H) { ctx.beginPath(); ctx.moveTo(0,yEnd); ctx.lineTo(W,yEnd); ctx.stroke(); }
      }
      ctx.setLineDash([]);
      // Center axis
      ctx.strokeStyle = "rgba(200,160,50,0.15)"; ctx.lineWidth = 1; ctx.setLineDash([4,6]);
      const cx = Math.round(cols/2)*cellSize;
      ctx.beginPath(); ctx.moveTo(cx,0); ctx.lineTo(cx,H); ctx.stroke();
      ctx.setLineDash([]);
    }

    // Travel direction arrow
    ctx.strokeStyle = "rgba(200,160,50,0.5)"; ctx.lineWidth = 1.5;
    const ax = W - 12, ay1 = 10, ay2 = 50;
    ctx.beginPath(); ctx.moveTo(ax, ay1); ctx.lineTo(ax, ay2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ax-5, ay2-8); ctx.lineTo(ax, ay2); ctx.lineTo(ax+5, ay2-8); ctx.stroke();
    ctx.fillStyle="rgba(200,160,50,0.45)"; ctx.font="7px 'Courier New'";
    ctx.fillText("↓", ax-3, ay1-2);

  }, [grid, c0, c1, cellSize, showGuides, segLen, gap, rows, cols]);

  return <canvas ref={ref} style={{ border:`1px solid ${UI.border}`, borderRadius:"3px", display:"block", imageRendering:cellSize<=4?"pixelated":"auto" }} />;
}

// ─── ROSETTE RING ────────────────────────────────────────────────
function RosetteCanvas({ grid, c0, c1, rIn, rOut, size }) {
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
    const toRgb=h=>({r:parseInt(h.slice(1,3),16),g:parseInt(h.slice(3,5),16),b:parseInt(h.slice(5,7),16)});
    const rgb=[toRgb(c0),toRgb(c1)];
    ctx.beginPath();ctx.arc(cx,cy,rIn,0,Math.PI*2);ctx.fillStyle="#060402";ctx.fill();
    const img=ctx.createImageData(size,size);const d=img.data;
    for(let py=0;py<size;py++) for(let px=0;px<size;px++){
      const dx=px-cx,dy=py-cy,dist=Math.sqrt(dx*dx+dy*dy);
      if(dist<rIn||dist>rOut) continue;
      // For vertical strand: rows = angular, cols = radial
      const ang=(Math.atan2(dy,dx)+Math.PI);
      const row=Math.min(Math.floor(ang/(2*Math.PI)*nR),nR-1);
      const t=(dist-rIn)/ringW;
      const col=Math.min(Math.floor(t*nC),nC-1);
      const v=grid[row]?.[col]??0;
      const c=rgb[v]??rgb[0];
      const i=(py*size+px)*4;
      d[i]=c.r;d[i+1]=c.g;d[i+2]=c.b;d[i+3]=255;
    }
    ctx.putImageData(img,0,0);
    ctx.strokeStyle="rgba(200,160,50,0.3)";ctx.lineWidth=0.8;ctx.setLineDash([3,4]);
    [rIn,rOut].forEach(r=>{ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();});
    ctx.setLineDash([]);
  },[grid, c0, c1, rIn, rOut, size]);
  return <canvas ref={ref} style={{ borderRadius:"50%", border:`1px solid ${UI.border}`, display:"block" }} />;
}

// ─── KNOB ────────────────────────────────────────────────────────
function Knob({ label, val, set, min, max, step=1, unit="", note="" }) {
  return (
    <div style={{ marginBottom:"10px" }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"2px" }}>
        <span style={{ fontSize:"9px", letterSpacing:"1.5px", color:UI.dim }}>{label}</span>
        <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>
          {typeof val==="number"&&!Number.isInteger(val)?val.toFixed(2):val}{unit}
        </span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val}
        onChange={e=>set(Number(e.target.value))} style={{ width:"100%", accentColor:"#c9a96e" }} />
      {note&&<div style={{ fontSize:"8px", color:UI.dimmer, marginTop:"1px" }}>{note}</div>}
    </div>
  );
}

// ─── MAIN ────────────────────────────────────────────────────────
export default function WaveRosetteV4() {
  const [A,           setA]           = useState(5);
  const [segLen,      setSegLen]      = useState(16);
  const [gap,         setGap]         = useState(3);
  const [skew,        setSkew]        = useState(0.72);
  const [strandW,     setStrandW]     = useState(2);
  const [centerFrac,  setCenterFrac]  = useState(0.5);

  const [cols, setCols] = useState(24);
  const [rows, setRows] = useState(60);

  const [c0, setC0] = useState("#1a1008");
  const [c1, setC1] = useState("#f0e8d0");

  const [cellSize,   setCellSize]   = useState(14);
  const [showGuides, setShowGuides] = useState(true);
  const [rIn,        setRIn]        = useState(90);
  const [rOut,       setROut]       = useState(136);
  const [tab,        setTab]        = useState("profile");

  const pitch = segLen + gap;
  const peakAt = (skew * 100).toFixed(0);
  const mmW = (cols * 0.5).toFixed(1);
  const mmH = (rows * 0.5).toFixed(1);

  const grid = buildStrandGrid({ cols, rows, A, segLen, gap, strandW, skew, centerFrac });

  const profileW = 220;
  const profileH = Math.min(rows * 7, 500);

  return (
    <div style={{ minHeight:"100vh", background:UI.bg, fontFamily:"'Courier New',monospace", color:UI.text, padding:"20px", userSelect:"none" }}>

      {/* HEADER */}
      <div style={{ borderBottom:`1px solid ${UI.border2}`, paddingBottom:"12px", marginBottom:"16px" }}>
        <div style={{ fontSize:"9px", letterSpacing:"4px", color:UI.dimmer }}>
          THE PRODUCTION SHOP · CUSTOM INLAY MODULE · V4
        </div>
        <div style={{ fontSize:"22px", fontWeight:"bold", color:UI.gold, letterSpacing:"3px", marginTop:"3px" }}>
          Single Strand · Vertical
        </div>
        <div style={{ fontSize:"10px", color:UI.dimmer, marginTop:"2px", letterSpacing:"1px" }}>
          One strand · Y-axis travel · asymmetric crash arch · string-face profile
        </div>

        {/* Formula */}
        <div style={{ marginTop:"8px", padding:"8px 12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px", display:"inline-flex", gap:"10px", alignItems:"baseline", flexWrap:"wrap" }}>
          <span style={{ fontSize:"9px", color:UI.dimmer }}>
            x(y) = centerX +
          </span>
          <span style={{ fontSize:"10px", color:UI.gold }}>
            A · arch(y_local, segLen, skew)
          </span>
          <span style={{ fontSize:"9px", color:UI.dimmest }}>|</span>
          <span style={{ fontSize:"9px", color:UI.dimmer }}>
            A=<span style={{ color:UI.gold }}>{A}</span> ·
            seg=<span style={{ color:UI.gold }}>{segLen}</span> ·
            gap=<span style={{ color:UI.gold }}>{gap}</span> ·
            skew=<span style={{ color:UI.gold }}>{peakAt}%</span>
          </span>
        </div>

        <div style={{ marginTop:"8px", display:"flex", gap:"5px", flexWrap:"wrap" }}>
          {[
            ["swell", `${(skew*segLen*0.5).toFixed(1)}mm`],
            ["crash", `${((1-skew)*segLen*0.5).toFixed(1)}mm`],
            ["gap",   `${(gap*0.5).toFixed(1)}mm`],
            ["pitch", `${(pitch*0.5).toFixed(1)}mm`],
            ["tile",  `${mmW}×${mmH}mm`],
          ].map(([a,b])=>(
            <div key={a} style={{ padding:"3px 8px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px", fontSize:"9px", color:UI.dimmer }}>
              <span style={{ color:UI.gold, fontWeight:"bold" }}>{a}</span> {b}
            </div>
          ))}
        </div>
      </div>

      {/* TABS */}
      <div style={{ display:"flex", gap:"4px", marginBottom:"16px" }}>
        {[["profile","String Face"],["grid","Pixel Grid"],["ring","Rosette Ring"],["bom","BOM"]].map(([k,l])=>(
          <div key={k} onClick={()=>setTab(k)} style={{
            padding:"5px 14px", cursor:"pointer", fontSize:"10px", letterSpacing:"1px",
            border:tab===k?"1px solid #c9a96e":`1px solid ${UI.border}`,
            borderRadius:"3px", background:tab===k?"#1e1508":"transparent",
            color:tab===k?UI.gold:UI.dim, transition:"all .12s",
          }}>{l}</div>
        ))}
      </div>

      <div style={{ display:"flex", gap:"18px", flexWrap:"wrap" }}>

        {/* CONTROLS */}
        <div style={{ width:"196px", flexShrink:0 }}>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>ARCH SHAPE</div>
            <Knob label="A — Displacement" val={A} set={setA} min={0} max={14} step={0.5}
              unit=" sq" note={`${(A*0.5).toFixed(1)}mm peak offset`} />
            <Knob label="segLen — Wave run" val={segLen} set={setSegLen} min={4} max={40}
              unit=" sq" note={`${(segLen*0.5).toFixed(1)}mm active`} />
            <Knob label="gap — Rest zone" val={gap} set={setGap} min={0} max={14}
              unit=" sq" note={`${(gap*0.5).toFixed(1)}mm gap`} />

            <div style={{ marginBottom:"10px" }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"2px" }}>
                <span style={{ fontSize:"9px", letterSpacing:"1.5px", color:UI.dim }}>skew — Peak position</span>
                <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{peakAt}%</span>
              </div>
              <input type="range" min={0.1} max={0.95} step={0.01} value={skew}
                onChange={e=>setSkew(Number(e.target.value))} style={{ width:"100%", accentColor:"#c9a96e" }} />
              <div style={{ display:"flex", justifyContent:"space-between", marginTop:"2px" }}>
                <span style={{ fontSize:"7px", color:UI.dimmer }}>← crash-first</span>
                <span style={{ fontSize:"7px", color:UI.dimmer }}>swell-first →</span>
              </div>
            </div>
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>STRAND</div>
            <Knob label="w — Strand width" val={strandW} set={setStrandW} min={0.5} max={8} step={0.5}
              unit=" sq" note={`${(strandW*0.5).toFixed(1)}mm veneer`} />
            <Knob label="Center position" val={centerFrac} set={setCenterFrac} min={0.1} max={0.9} step={0.05}
              unit="" note={`col ${(centerFrac*cols).toFixed(0)} of ${cols}`} />
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>TILE SIZE</div>
            <Knob label="Width (cols)" val={cols} set={setCols} min={8} max={40} note={`${mmW}mm`} />
            <Knob label="Height (rows)" val={rows} set={setRows} min={16} max={120} note={`${mmH}mm`} />
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"8px" }}>VENEER</div>
            {[["Background",c0,setC0],["Strand",c1,setC1]].map(([l,v,s])=>(
              <div key={l} style={{ display:"flex", alignItems:"center", gap:"7px", marginBottom:"7px" }}>
                <input type="color" value={v} onChange={e=>s(e.target.value)}
                  style={{ width:"24px", height:"20px", border:`1px solid ${UI.border}`, borderRadius:"2px", cursor:"pointer", padding:"1px" }} />
                <span style={{ fontSize:"9px", color:UI.dim }}>{l}</span>
              </div>
            ))}
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"8px" }}>VIEW</div>
            <Knob label="Cell size" val={cellSize} set={setCellSize} min={3} max={28} unit=" px" />
            <Knob label="Ring r_in"  val={rIn}  set={setRIn}  min={40} max={180} unit=" px" />
            <Knob label="Ring r_out" val={rOut} set={setROut} min={60} max={200} unit=" px" />
            <div onClick={()=>setShowGuides(g=>!g)} style={{
              padding:"4px 7px", cursor:"pointer", fontSize:"9px",
              border:showGuides?"1px solid #c9a96e":`1px solid ${UI.border}`,
              borderRadius:"3px", background:showGuides?"#1e1508":"transparent",
              color:showGuides?UI.gold:UI.dim,
            }}>Guides</div>
          </div>

          {/* Check */}
          <div style={{ padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>CHECK</div>
            <div style={{ fontSize:"8px", color:UI.dimmer, lineHeight:"2.1" }}>
              <span style={{ color: A < cols*0.4 ? "#2d9a6f":"#e8c87a" }}>
                {A < cols*0.4 ?"✓":"△"} A fits width
              </span><br/>
              <span style={{ color: gap > 0 ? "#2d9a6f":"#e8c87a" }}>
                {gap > 0 ?"✓":"△"} gap &gt; 0
              </span><br/>
              <span style={{ color: skew>0.5&&skew<0.9?"#2d9a6f":"#e8c87a" }}>
                {skew>0.5&&skew<0.9?"✓":"△"} skew {peakAt}%
              </span><br/>
              <span style={{ color: parseFloat(mmH)>=5?"#2d9a6f":"#e8c87a" }}>
                {parseFloat(mmH)>=5?"✓":"△"} height {mmH}mm
              </span><br/><br/>
              <span style={{ color:UI.amber }}>swell/crash:</span><br/>
              {(skew/(1-skew)).toFixed(2)}:1
            </div>
          </div>
        </div>

        {/* ── MAIN CONTENT ── */}
        <div style={{ flex:1, minWidth:0, display:"flex", gap:"18px", flexWrap:"wrap", alignItems:"flex-start" }}>

          {/* Always-visible profile alongside main view */}
          <div style={{ flexShrink:0 }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>
              {tab==="profile" ? "STRING FACE · x(y) displacement" : "PROFILE"}
            </div>
            <ProfileCanvas
              rows={rows} A={A} segLen={segLen} gap={gap} skew={skew}
              strandW={strandW} cols={cols} centerFrac={centerFrac}
              W={profileW} H={profileH}
            />
            <div style={{ marginTop:"6px", fontSize:"8px", color:UI.dimmer, lineHeight:"1.8", maxWidth:`${profileW}px` }}>
              <span style={{ color:UI.gold }}>Y</span> = travel ·
              <span style={{ color:UI.amber }}> X</span> = displacement<br/>
              <span style={{ color:"rgba(200,160,50,0.5)" }}>gold line</span> = center axis<br/>
              <span style={{ color:"rgba(200,80,50,0.5)" }}>red zones</span> = gap (no strand)
            </div>
          </div>

          {/* Main tab content */}
          <div style={{ flex:1, minWidth:0 }}>

            {tab==="profile" && (
              <div>
                <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"10px", letterSpacing:"2px" }}>
                  WAVE ANATOMY
                </div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"6px", marginBottom:"12px" }}>
                  {[
                    ["Swell run",     `${(skew*segLen*0.5).toFixed(2)}mm`],
                    ["Crash run",     `${((1-skew)*segLen*0.5).toFixed(2)}mm`],
                    ["Peak A",        `${(A*0.5).toFixed(2)}mm`],
                    ["Strand w",      `${(strandW*0.5).toFixed(2)}mm`],
                    ["Gap",           `${(gap*0.5).toFixed(2)}mm`],
                    ["Pitch",         `${(pitch*0.5).toFixed(2)}mm`],
                    ["Swell:crash",   `${(skew/(1-skew)).toFixed(2)}:1`],
                    ["Crash angle",   `${(Math.atan(A/((1-skew)*segLen))*180/Math.PI).toFixed(1)}°`],
                  ].map(([k,v])=>(
                    <div key={k} style={{ padding:"6px 8px", background:UI.panel, border:`1px solid ${UI.border2}`, borderRadius:"3px" }}>
                      <div style={{ fontSize:"8px", color:UI.dimmer }}>{k}</div>
                      <div style={{ fontSize:"13px", color:UI.gold, fontWeight:"bold" }}>{v}</div>
                    </div>
                  ))}
                </div>
                <div style={{ padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", fontSize:"9px", color:UI.dimmer, lineHeight:"2" }}>
                  <div style={{ color:UI.amber, marginBottom:"4px", letterSpacing:"2px" }}>CONSTRUCTION METHOD</div>
                  <span style={{ color:UI.gold }}>1.</span> Shape a caul with this asymmetric profile — swell side gradual, crash side steep.<br/>
                  <span style={{ color:UI.gold }}>2.</span> Clamp a single veneer strip in the caul. It takes the arch shape.<br/>
                  <span style={{ color:UI.gold }}>3.</span> The gap zones = flat sections at the ends of each arch where glue joints fall.<br/>
                  <span style={{ color:UI.gold }}>4.</span> Tile the shaped strips end-to-end down the rosette channel.<br/>
                  <span style={{ color:UI.gold }}>5.</span> Each arch crashes into the swell of the next — the procession reads as one continuous movement around the soundhole.
                </div>
              </div>
            )}

            {tab==="grid" && (
              <div>
                <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                  PIXEL GRID · {cols}×{rows} · 0.5mm/sq · strand travels ↓
                </div>
                <GridCanvas grid={grid} c0={c0} c1={c1} cellSize={cellSize}
                  showGuides={showGuides} segLen={segLen} gap={gap} rows={rows} cols={cols} />
                <div style={{ marginTop:"8px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.8" }}>
                  <span style={{ color:"rgba(200,160,50,0.6)" }}>Gold lines</span> = segment start ·
                  <span style={{ color:"rgba(200,80,50,0.6)" }}> red lines</span> = segment end (gap begins) ·
                  <span style={{ color:"rgba(200,160,50,0.3)" }}> center axis</span> = rest position
                </div>
              </div>
            )}

            {tab==="ring" && (
              <div>
                <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                  ROSETTE RING · Angular = Y (travel) · Radial = X (displacement)
                </div>
                <RosetteCanvas grid={grid} c0={c0} c1={c1} rIn={rIn} rOut={rOut} size={340} />
                <div style={{ marginTop:"8px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.7" }}>
                  Strand travels angularly around the ring. Displacement maps radially —
                  the crash face pushes inward, the swell pulls outward.
                  Gap zones appear as clean background between each arch.
                </div>
              </div>
            )}

            {tab==="bom" && (
              <div>
                <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                  VENEER BOM · {rows} rows × {cols} cols
                </div>
                <div style={{ maxHeight:"420px", overflowY:"auto", border:`1px solid ${UI.border}`, borderRadius:"3px" }}>
                  {grid.map((row,r)=>{
                    const parts=[];let cur=row[0],run=1;
                    for(let c=1;c<cols;c++){if(row[c]===cur)run++;else{parts.push({v:cur,n:run});cur=row[c];run=1;}}
                    parts.push({v:cur,n:run});
                    const localY = r % pitch;
                    const zone = localY >= segLen ? "gap" : localY < skew*segLen ? "swell" : "crash";
                    const zoneColor = zone==="gap"?"rgba(200,80,50,0.5)":zone==="swell"?"rgba(200,160,50,0.4)":"rgba(200,100,50,0.4)";
                    return(
                      <div key={r} style={{ display:"flex",alignItems:"center",gap:"4px",padding:"3px 8px",borderBottom:`1px solid ${UI.dimmest}`,background:r%2===0?"transparent":"#0c0903" }}>
                        <span style={{ fontSize:"7px",color:UI.dimmer,width:"18px",flexShrink:0 }}>{r+1}</span>
                        <span style={{ fontSize:"7px",color:UI.dimmer,width:"26px",flexShrink:0 }}>{((r+1)*0.5).toFixed(1)}</span>
                        <span style={{ fontSize:"7px",color:zoneColor,width:"32px",flexShrink:0 }}>{zone}</span>
                        <div style={{ display:"flex",gap:"2px",flexWrap:"wrap",flex:1 }}>
                          {parts.map((p,i)=>(
                            <span key={i} style={{ padding:"1px 3px",borderRadius:"2px",background:p.v===0?c0:c1,border:p.v===0?`1px solid ${UI.border}`:"none",fontSize:"8px",color:p.v===0?"#7a6a5a":"#1a1008",fontWeight:"bold" }}>
                              {p.n}{p.v===0?"·":"S"}
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: mini snapshot */}
        <div style={{ width:"100px", flexShrink:0 }}>
          <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>SNAPSHOT</div>
          <div style={{ display:"inline-block", border:`1px solid ${UI.border}`, borderRadius:"2px", overflow:"hidden" }}>
            {grid.map((row,r)=>(
              <div key={r} style={{ display:"flex" }}>
                {row.map((v,c)=>(<div key={c} style={{ width:"4px",height:"4px",background:v===0?c0:c1 }}/>))}
              </div>
            ))}
          </div>
          <div style={{ fontSize:"7px", color:UI.dimmer, marginTop:"3px" }}>{cols}×{rows}</div>

          <div style={{ marginTop:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>RING</div>
            <RosetteCanvas grid={grid} c0={c0} c1={c1} rIn={rIn*0.35} rOut={rOut*0.35} size={98} />
          </div>
        </div>

      </div>
    </div>
  );
}
