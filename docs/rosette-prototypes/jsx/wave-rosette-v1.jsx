import { useState, useEffect, useRef } from "react";

const UI = {
  bg:"#0b0806", panel:"#0f0c08", border:"#2e2010", border2:"#1e1508",
  gold:"#e8c87a", amber:"#c9a96e", dim:"#7a5c2e", dimmer:"#4a3010",
  dimmest:"#2a1e0a", text:"#c9a96e",
};

// ─── STRAND FORMULA ──────────────────────────────────────────────
// y_n(x) = n·d + A·sin(2π·x / λ + phase)
// Pixel (col, row) is ON a strand if:
//   ∃ n : |row − n·d − A·sin(2π·col/λ)| < w/2
function buildWaveGrid({ cols, rows, A, lambda, d, strandW, numStrands, phase, colorMode }) {
  const grid = [];
  for (let r = 0; r < rows; r++) {
    const row = [];
    for (let c = 0; c < cols; c++) {
      const wave = A * Math.sin(2 * Math.PI * c / lambda + phase);
      let closest = Infinity;
      let closestN = 0;
      for (let n = -numStrands; n <= numStrands * 2; n++) {
        const center = n * d + wave;
        const dist = Math.abs(r - center);
        if (dist < closest) { closest = dist; closestN = n; }
      }
      // Assign color by strand index and mode
      if (closest < strandW / 2) {
        if (colorMode === "bw")     row.push((closestN % 2 + 2) % 2);          // alt B/W
        else if (colorMode === "bwg") row.push(closestN % 3 === 0 ? 2 : closestN % 2); // B/W/Green
        else if (colorMode === "solid") row.push(1);                            // all white
        else row.push(1);
      } else {
        row.push(0); // background = black
      }
    }
    grid.push(row);
  }
  return grid;
}

// ─── COLOR MAP ───────────────────────────────────────────────────
const COLORS = {
  0: { fill:"#1a1008", label:"Background" },
  1: { fill:"#f0e8d0", label:"Strand (light)" },
  2: { fill:"#2d6a4f", label:"Accent strand" },
};

// ─── JIG PROFILE CANVAS ──────────────────────────────────────────
function JigCanvas({ cols, rows, A, lambda, phase, strandW, d, numStrands, vColors, cellSize, canvasW, canvasH }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    canvas.width = canvasW; canvas.height = canvasH;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = UI.bg; ctx.fillRect(0, 0, canvasW, canvasH);

    const midY = canvasH / 2;
    const scaleX = canvasW / cols;
    const scaleY = canvasH / rows;

    // Draw strand centerlines
    for (let n = -numStrands; n <= numStrands * 2; n++) {
      const isAccent = n % 3 === 0;
      ctx.strokeStyle = isAccent ? "#2d6a4f" : (n % 2 === 0 ? "#f0e8d0" : "rgba(200,160,50,0.4)");
      ctx.lineWidth = strandW * scaleY * 0.7;
      ctx.beginPath();
      for (let c = 0; c < cols; c++) {
        const wave = A * Math.sin(2 * Math.PI * c / lambda + phase);
        const x = c * scaleX;
        const y = (n * d + wave) * scaleY + midY;
        if (c === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    // Fold markers at x = λ/2, 3λ/2 ...
    ctx.strokeStyle = "rgba(200,160,50,0.5)";
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 4]);
    for (let k = 0.5; k * lambda < cols; k++) {
      const x = k * lambda * scaleX;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvasH); ctx.stroke();
    }
    ctx.setLineDash([]);

    // Amplitude arrows at first fold
    const foldX = 0.5 * lambda * scaleX;
    const baseY = midY;
    const tipY  = midY - A * scaleY;
    if (foldX < canvasW) {
      ctx.strokeStyle = "rgba(200,160,50,0.7)"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(foldX, baseY); ctx.lineTo(foldX, tipY); ctx.stroke();
      ctx.fillStyle = "rgba(200,160,50,0.7)"; ctx.font = "9px 'Courier New'";
      ctx.fillText(`A=${A.toFixed(1)}`, foldX + 4, (baseY + tipY) / 2 + 4);
    }

    // λ label
    ctx.fillStyle = "rgba(200,160,50,0.5)"; ctx.font = "9px 'Courier New'";
    ctx.fillText(`λ=${lambda.toFixed(1)}sq`, 4, canvasH - 6);

  }, [cols, rows, A, lambda, phase, strandW, d, numStrands, canvasW, canvasH]);

  return (
    <canvas ref={ref}
      style={{ border:`1px solid ${UI.border}`, borderRadius:"3px", display:"block", width:"100%" }} />
  );
}

// ─── GRID CANVAS (pixel render) ──────────────────────────────────
function GridCanvas({ grid, vColors, cellSize, showGuides, lambda, A, rows }) {
  const ref = useRef(null);
  const cols = grid[0]?.length ?? 0;
  const nRows = grid.length;

  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    const W = cols * cellSize, H = nRows * cellSize;
    canvas.width = W; canvas.height = H;
    const ctx = canvas.getContext("2d");

    // Draw cells via imageData for speed
    const imgData = ctx.createImageData(W, H);
    const data = imgData.data;
    const hexToRgb = hex => ({
      r: parseInt(hex.slice(1,3),16),
      g: parseInt(hex.slice(3,5),16),
      b: parseInt(hex.slice(5,7),16),
    });
    const c0 = hexToRgb(vColors[0]);
    const c1 = hexToRgb(vColors[1]);
    const c2 = hexToRgb(vColors[2]);
    const cmap = [c0, c1, c2];

    for (let r = 0; r < nRows; r++) {
      for (let c = 0; c < cols; c++) {
        const v = grid[r][c];
        const rgb = cmap[v] ?? c0;
        for (let py = r * cellSize; py < (r+1) * cellSize; py++) {
          for (let px = c * cellSize; px < (c+1) * cellSize; px++) {
            const idx = (py * W + px) * 4;
            data[idx] = rgb.r; data[idx+1] = rgb.g; data[idx+2] = rgb.b; data[idx+3] = 255;
          }
        }
      }
    }
    ctx.putImageData(imgData, 0, 0);

    // Grid lines
    if (cellSize >= 6) {
      ctx.strokeStyle = "rgba(90,60,20,0.2)"; ctx.lineWidth = 0.5;
      for (let c = 0; c <= cols; c++) { ctx.beginPath(); ctx.moveTo(c*cellSize,0); ctx.lineTo(c*cellSize,H); ctx.stroke(); }
      for (let r = 0; r <= nRows; r++) { ctx.beginPath(); ctx.moveTo(0,r*cellSize); ctx.lineTo(W,r*cellSize); ctx.stroke(); }
    }

    // Fold guide lines
    if (showGuides) {
      ctx.strokeStyle = "rgba(200,160,50,0.4)"; ctx.lineWidth = 1; ctx.setLineDash([3,4]);
      for (let k = 0.5; k * lambda < cols; k++) {
        const x = k * lambda * cellSize;
        ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke();
      }
      // Wave centerline
      ctx.setLineDash([]);
      ctx.strokeStyle = "rgba(200,160,50,0.25)"; ctx.lineWidth = 0.8;
      ctx.beginPath();
      const midRow = nRows / 2;
      for (let c = 0; c < cols; c++) {
        const y = midRow * cellSize;
        if (c===0) ctx.moveTo(c*cellSize,y); else ctx.lineTo(c*cellSize,y);
      }
      ctx.stroke();
    }

  }, [grid, vColors, cellSize, showGuides, lambda, A, rows]);

  return (
    <canvas ref={ref}
      style={{
        border:`1px solid ${UI.border}`, borderRadius:"3px",
        display:"block", maxWidth:"100%", imageRendering: cellSize <= 4 ? "pixelated" : "auto",
      }} />
  );
}

// ─── ROSETTE RING PREVIEW ────────────────────────────────────────
function RosetteCanvas({ grid, vColors, rIn, rOut, size }) {
  const ref = useRef(null);
  const hexToRgb = hex => ({ r:parseInt(hex.slice(1,3),16), g:parseInt(hex.slice(3,5),16), b:parseInt(hex.slice(5,7),16) });

  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    canvas.width = size; canvas.height = size;
    const ctx = canvas.getContext("2d");
    const cx = size/2, cy = size/2;
    ctx.fillStyle = UI.bg; ctx.fillRect(0,0,size,size);
    if (!grid || grid.length === 0) return;

    const nRows = grid.length, nCols = grid[0].length;
    const ringW = rOut - rIn;
    const circ = 2 * Math.PI * (rIn + rOut) / 2;
    const rgb = [hexToRgb(vColors[0]), hexToRgb(vColors[1]), hexToRgb(vColors[2])];

    ctx.beginPath(); ctx.arc(cx,cy,rIn,0,Math.PI*2); ctx.fillStyle="#060402"; ctx.fill();

    const imgData = ctx.createImageData(size, size);
    const data = imgData.data;
    for (let py=0; py<size; py++) {
      for (let px=0; px<size; px++) {
        const dx=px-cx, dy=py-cy;
        const dist=Math.sqrt(dx*dx+dy*dy);
        if (dist<rIn||dist>rOut) continue;
        const t=(dist-rIn)/ringW;
        const row=Math.min(Math.floor(t*nRows),nRows-1);
        let angle=Math.atan2(dy,dx)+Math.PI;
        const arcLen=angle*(rIn+rOut)/2;
        const col=((Math.floor(arcLen/(circ/nCols))%nCols)+nCols)%nCols;
        const v=grid[row]?.[col]??0;
        const c=rgb[v]??rgb[0];
        const idx=(py*size+px)*4;
        data[idx]=c.r; data[idx+1]=c.g; data[idx+2]=c.b; data[idx+3]=255;
      }
    }
    ctx.putImageData(imgData,0,0);

    // Ring guides
    ctx.strokeStyle="rgba(200,160,50,0.35)"; ctx.lineWidth=0.8; ctx.setLineDash([3,4]);
    [rIn,rOut].forEach(r=>{ ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2); ctx.stroke(); });
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
        <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{val}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val}
        onChange={e=>set(Number(e.target.value))}
        style={{ width:"100%", accentColor:"#c9a96e" }} />
      {note && <div style={{ fontSize:"8px", color:UI.dimmer, marginTop:"1px" }}>{note}</div>}
    </div>
  );
}

// ─── MAIN ────────────────────────────────────────────────────────
export default function WaveRosetteGenerator() {
  // Wave formula parameters
  const [A,          setA]          = useState(4);     // amplitude in sq (×0.5mm)
  const [lambda,     setLambda]     = useState(20);    // wavelength in sq
  const [d,          setD]          = useState(3);     // strand spacing in sq
  const [strandW,    setStrandW]    = useState(2);     // strand width in sq
  const [numStrands, setNumStrands] = useState(5);     // visible strands
  const [phase,      setPhase]      = useState(0);     // phase offset (radians ×10 for slider)

  // Grid dimensions
  const [cols, setCols] = useState(40);
  const [rows, setRows] = useState(24);

  // Color mode
  const [colorMode, setColorMode] = useState("bw");
  const [c0, setC0] = useState("#1a1008");  // background
  const [c1, setC1] = useState("#f0e8d0");  // strand
  const [c2, setC2] = useState("#2d6a4f");  // accent

  // View
  const [cellSize,   setCellSize]   = useState(14);
  const [showGuides, setShowGuides] = useState(true);
  const [rIn,        setRIn]        = useState(88);
  const [rOut,       setROut]       = useState(136);
  const [tab,        setTab]        = useState("grid");

  const phaseRad = phase / 10;
  const vColors = [c0, c1, c2];

  // Build grid
  const grid = buildWaveGrid({ cols, rows, A, lambda, d, strandW, numStrands, phase: phaseRad, colorMode });

  // Stats
  const counts = { 0:0, 1:0, 2:0 };
  grid.forEach(row => row.forEach(v => counts[v] = (counts[v]||0)+1));
  const total = cols * rows;
  const mmW = (cols * 0.5).toFixed(1);
  const mmH = (rows * 0.5).toFixed(1);

  return (
    <div style={{ minHeight:"100vh", background:UI.bg, fontFamily:"'Courier New',monospace", color:UI.text, padding:"20px", userSelect:"none" }}>

      {/* HEADER */}
      <div style={{ borderBottom:`1px solid ${UI.border2}`, paddingBottom:"12px", marginBottom:"16px" }}>
        <div style={{ fontSize:"9px", letterSpacing:"4px", color:UI.dimmer, textTransform:"uppercase" }}>
          The Production Shop · Custom Inlay Module
        </div>
        <div style={{ fontSize:"22px", fontWeight:"bold", color:UI.gold, letterSpacing:"3px", marginTop:"3px" }}>
          Wave Rosette Generator
        </div>
        <div style={{ fontSize:"10px", color:UI.dimmer, marginTop:"2px", letterSpacing:"1px" }}>
          yₙ(x) = n·d + A·sin(2π·x / λ + φ) &nbsp;·&nbsp; Classical / Flamenco Guitar
        </div>

        {/* Live formula */}
        <div style={{ marginTop:"8px", padding:"8px 12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px", display:"inline-block" }}>
          <span style={{ fontSize:"10px", color:UI.dimmer }}>y</span>
          <span style={{ fontSize:"10px", color:"#7a9adb" }}>ₙ</span>
          <span style={{ fontSize:"10px", color:UI.dimmer }}>(x) = n·</span>
          <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{d}</span>
          <span style={{ fontSize:"10px", color:UI.dimmer }}> + </span>
          <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{A}</span>
          <span style={{ fontSize:"10px", color:UI.dimmer }}>·sin(2π·x / </span>
          <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{lambda}</span>
          <span style={{ fontSize:"10px", color:UI.dimmer }}>{phaseRad !== 0 ? ` + ${phaseRad.toFixed(2)}` : ""})</span>
          <span style={{ fontSize:"9px", color:UI.dimmer, marginLeft:"12px" }}>
            strand width = <span style={{ color:UI.gold }}>{strandW}</span> sq ·
            n = 0…<span style={{ color:UI.gold }}>{numStrands}</span>
          </span>
        </div>

        {/* Dimension badges */}
        <div style={{ marginTop:"8px", display:"flex", gap:"6px", flexWrap:"wrap" }}>
          {[
            [`${cols}×${rows} grid`, `${mmW}×${mmH} mm`],
            [`A = ${A} sq`, `${(A*0.5).toFixed(1)}mm amplitude`],
            [`λ = ${lambda} sq`, `${(lambda*0.5).toFixed(1)}mm wavelength`],
            [`d = ${d} sq`, `${(d*0.5).toFixed(1)}mm strand pitch`],
            [`fold at`, `x = λ/2 = ${(lambda/2).toFixed(0)} sq`],
          ].map(([a,b]) => (
            <div key={a} style={{ padding:"3px 8px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px", fontSize:"9px", color:UI.dimmer }}>
              <span style={{ color:UI.gold, fontWeight:"bold" }}>{a}</span>&nbsp;{b}
            </div>
          ))}
        </div>
      </div>

      {/* TABS */}
      <div style={{ display:"flex", gap:"4px", marginBottom:"16px", flexWrap:"wrap" }}>
        {[["grid","Pixel Grid"],["jig","Jig Profile"],["ring","Rosette Ring"],["bom","Veneer BOM"]].map(([k,l]) => (
          <div key={k} onClick={()=>setTab(k)} style={{
            padding:"5px 14px", cursor:"pointer", fontSize:"10px", letterSpacing:"1px",
            border:tab===k?"1px solid #c9a96e":`1px solid ${UI.border}`,
            borderRadius:"3px", background:tab===k?"#1e1508":"transparent",
            color:tab===k?UI.gold:UI.dim, transition:"all .12s",
          }}>{l}</div>
        ))}
      </div>

      <div style={{ display:"flex", gap:"18px", flexWrap:"wrap" }}>

        {/* ── LEFT CONTROLS ── */}
        <div style={{ width:"200px", flexShrink:0 }}>

          {/* Wave formula */}
          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>WAVE FORMULA</div>
            <Knob label="A — Amplitude" val={A} set={setA} min={0} max={14} step={0.5}
              unit=" sq" note={`${(A*0.5).toFixed(1)}mm peak deflection`} />
            <Knob label="λ — Wavelength" val={lambda} set={setLambda} min={4} max={60} step={1}
              unit=" sq" note={`fold at ${(lambda/2).toFixed(0)} sq = ${(lambda*0.25).toFixed(1)}mm`} />
            <Knob label="d — Strand pitch" val={d} set={setD} min={1} max={12} step={0.5}
              unit=" sq" note={`${(d*0.5).toFixed(1)}mm center-to-center`} />
            <Knob label="w — Strand width" val={strandW} set={setStrandW} min={0.5} max={6} step={0.5}
              unit=" sq" note={`${(strandW*0.5).toFixed(1)}mm veneer thickness`} />
            <Knob label="N — Strands visible" val={numStrands} set={setNumStrands} min={1} max={12} />
            <Knob label="φ — Phase offset" val={phase} set={setPhase} min={-31} max={31}
              unit="" note={`${phaseRad.toFixed(2)} rad`} />
          </div>

          {/* Grid size */}
          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>TILE SIZE</div>
            <Knob label="Columns" val={cols} set={setCols} min={8} max={80}
              note={`${mmW}mm wide`} />
            <Knob label="Rows" val={rows} set={setRows} min={4} max={40}
              note={`${mmH}mm tall`} />
          </div>

          {/* Color mode */}
          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"8px" }}>COLOR MODE</div>
            {[["bw","Alt Black / White"],["bwg","B / W / Accent"],["solid","Solid strand"]].map(([v,l]) => (
              <div key={v} onClick={()=>setColorMode(v)} style={{
                padding:"4px 7px", marginBottom:"3px", cursor:"pointer", fontSize:"10px",
                border:colorMode===v?"1px solid #c9a96e":`1px solid ${UI.border}`,
                borderRadius:"3px", background:colorMode===v?"#1e1508":"transparent",
                color:colorMode===v?UI.gold:UI.dim,
              }}>{l}</div>
            ))}
            <div style={{ marginTop:"8px" }}>
              {[["Background",c0,setC0],["Strand (light)",c1,setC1],["Accent",c2,setC2]].map(([l,v,s]) => (
                <div key={l} style={{ display:"flex", alignItems:"center", gap:"7px", marginBottom:"6px" }}>
                  <input type="color" value={v} onChange={e=>s(e.target.value)}
                    style={{ width:"24px", height:"20px", border:`1px solid ${UI.border}`, borderRadius:"2px", cursor:"pointer", padding:"1px" }}/>
                  <span style={{ fontSize:"9px", color:UI.dim }}>{l}</span>
                </div>
              ))}
            </div>
          </div>

          {/* View controls */}
          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"8px" }}>VIEW</div>
            <Knob label="Cell size" val={cellSize} set={setCellSize} min={3} max={28} unit=" px" />
            <Knob label="Ring r_in" val={rIn} set={setRIn} min={40} max={180} unit=" px" />
            <Knob label="Ring r_out" val={rOut} set={setROut} min={60} max={200} unit=" px" />
            <div onClick={()=>setShowGuides(g=>!g)} style={{
              padding:"4px 7px", cursor:"pointer", fontSize:"10px",
              border:showGuides?"1px solid #c9a96e":`1px solid ${UI.border}`,
              borderRadius:"3px", background:showGuides?"#1e1508":"transparent",
              color:showGuides?UI.gold:UI.dim,
            }}>Fold guides</div>
          </div>

          {/* Formula legend */}
          <div style={{ padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>GEOMETRY</div>
            <div style={{ fontSize:"8px", color:UI.dimmer, lineHeight:"1.9" }}>
              <span style={{ color:UI.amber }}>Fold point:</span><br/>
              x = λ/2 = <span style={{ color:UI.gold }}>{(lambda/2).toFixed(1)}</span> sq<br/>
              = <span style={{ color:UI.gold }}>{(lambda*0.25).toFixed(2)}</span> mm<br/><br/>
              <span style={{ color:UI.amber }}>Strand gap:</span><br/>
              d − w = <span style={{ color:UI.gold }}>{(d-strandW).toFixed(1)}</span> sq<br/>
              = <span style={{ color:UI.gold }}>{((d-strandW)*0.5).toFixed(2)}</span> mm<br/><br/>
              <span style={{ color:UI.amber }}>Tile repeats:</span><br/>
              {(cols/lambda).toFixed(2)}× per row<br/><br/>
              <span style={{ color:UI.amber }}>Wave speed:</span><br/>
              v = λ·f (physical analogy)
            </div>
          </div>
        </div>

        {/* ── CENTER ── */}
        <div style={{ flex:1, minWidth:0 }}>

          {/* PIXEL GRID */}
          {tab==="grid" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"10px", letterSpacing:"2px" }}>
                PIXEL GRID · {cols}×{rows} · each sq = 0.5mm · strand formula rendered
              </div>
              <GridCanvas grid={grid} vColors={vColors} cellSize={cellSize}
                showGuides={showGuides} lambda={lambda} A={A} rows={rows} />
              <div style={{ marginTop:"8px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.7" }}>
                <span style={{ color:UI.amber }}>Gold dashed lines</span> = fold points at x = λ/2, 3λ/2, …
                where dy/dx = 0 and the strand reverses direction — this is the physical fold of the jig.
              </div>
            </div>
          )}

          {/* JIG PROFILE */}
          {tab==="jig" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"10px", letterSpacing:"2px" }}>
                CONSTRUCTION JIG PROFILE · Caul curvature = A·sin(2πx/λ)
              </div>
              <JigCanvas cols={cols} rows={rows} A={A} lambda={lambda} phase={phaseRad}
                strandW={strandW} d={d} numStrands={numStrands} vColors={vColors}
                cellSize={cellSize} canvasW={Math.min(cols*cellSize, 600)} canvasH={rows*cellSize} />
              <div style={{ marginTop:"10px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
                <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>JIG READING</div>
                <div style={{ fontSize:"9px", color:UI.dimmer, lineHeight:"1.8" }}>
                  Each colored line = one veneer strand centerline.<br/>
                  <span style={{ color:"#f0e8d0" }}>White</span> / <span style={{ color:UI.amber }}>amber</span> strands alternate B/W veneers.<br/>
                  <span style={{ color:"#2d9a6f" }}>Green</span> lines = accent strands (every 3rd, in BWG mode).<br/>
                  <span style={{ color:"rgba(200,160,50,0.7)" }}>Dashed verticals</span> = fold points — where the caul reverses and the glued stack is sliced.<br/><br/>
                  <span style={{ color:UI.amber }}>Physical jig:</span> CNC the caul profile to A={A}sq={( A*0.5).toFixed(1)}mm amplitude,
                  λ={lambda}sq={(lambda*0.5).toFixed(1)}mm wavelength.
                  Clamp veneer stack in caul → slice at fold lines → each slice = one rosette tile.
                </div>
              </div>
            </div>
          )}

          {/* ROSETTE RING */}
          {tab==="ring" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"10px", letterSpacing:"2px" }}>
                ROSETTE RING PREVIEW · Tile mapped to annulus r_in={rIn}px r_out={rOut}px
              </div>
              <RosetteCanvas grid={grid} vColors={vColors} rIn={rIn} rOut={rOut} size={360} />
              <div style={{ marginTop:"8px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.7" }}>
                Rows map radially (top row = inner edge). Columns tile continuously around the ring.
                The wave pattern should create a continuous undulating strand around the soundhole.
              </div>
            </div>
          )}

          {/* VENEER BOM */}
          {tab==="bom" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"10px", letterSpacing:"2px" }}>
                VENEER BOM · Row-by-row glue sequence
              </div>
              <div style={{ maxHeight:"400px", overflowY:"auto", border:`1px solid ${UI.border}`, borderRadius:"3px" }}>
                {grid.map((row, r) => {
                  const parts = [];
                  let cur = row[0], run = 1;
                  for (let c=1; c<cols; c++) {
                    if (row[c]===cur) run++;
                    else { parts.push({v:cur,n:run}); cur=row[c]; run=1; }
                  }
                  parts.push({v:cur,n:run});
                  const lbl = ["B","S","A"];
                  const fc  = [c0, c1, c2];
                  const tc  = v => v===1?"#1a1008":v===2?"#fff":"#c9a96e";
                  return (
                    <div key={r} style={{ display:"flex", alignItems:"center", gap:"5px", padding:"3px 8px", borderBottom:`1px solid ${UI.dimmest}`, background:r%2===0?"transparent":"#0c0903" }}>
                      <span style={{ fontSize:"8px", color:UI.dimmer, width:"20px", flexShrink:0 }}>{r+1}</span>
                      <span style={{ fontSize:"7px", color:UI.dimmer, width:"28px", flexShrink:0 }}>{((r+1)*0.5).toFixed(1)}</span>
                      <div style={{ display:"flex", gap:"2px", flexWrap:"wrap", flex:1 }}>
                        {parts.map((p,i) => (
                          <span key={i} style={{
                            padding:"1px 3px", borderRadius:"2px",
                            background:fc[p.v], border:p.v===0?`1px solid ${UI.border}`:"none",
                            fontSize:"8px", color:tc(p.v), fontWeight:"bold",
                          }}>{p.n}{lbl[p.v]}</span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div style={{ marginTop:"10px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
                <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>TOTALS</div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"5px" }}>
                  {[
                    ["Background cells", counts[0]],
                    ["Strand cells", counts[1]],
                    ["Accent cells", counts[2]||0],
                    ["Total cells", total],
                    ["Grid", `${cols}×${rows}`],
                    ["Tile size", `${mmW}×${mmH}mm`],
                  ].map(([k,v]) => (
                    <div key={k} style={{ display:"flex", justifyContent:"space-between", padding:"3px 6px", background:UI.bg, borderRadius:"2px", border:`1px solid ${UI.border2}` }}>
                      <span style={{ fontSize:"9px", color:UI.dimmer }}>{k}</span>
                      <span style={{ fontSize:"10px", color:UI.gold, fontWeight:"bold" }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: mini previews ── */}
        <div style={{ width:"190px", flexShrink:0 }}>
          <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>RING PREVIEW</div>
          <RosetteCanvas grid={grid} vColors={vColors} rIn={rIn*0.44} rOut={rOut*0.44} size={186} />

          <div style={{ marginTop:"10px", marginBottom:"6px", fontSize:"9px", letterSpacing:"2px", color:UI.dim }}>TILE SNAPSHOT</div>
          <div style={{ display:"inline-block", border:`1px solid ${UI.border}`, borderRadius:"2px", overflow:"hidden" }}>
            {grid.map((row,r) => (
              <div key={r} style={{ display:"flex" }}>
                {row.map((v,c) => (
                  <div key={c} style={{ width:"4px", height:"4px", background:vColors[v] }} />
                ))}
              </div>
            ))}
          </div>
          <div style={{ fontSize:"8px", color:UI.dimmer, marginTop:"2px" }}>{cols}×{rows} @ 4px/sq</div>

          {/* Wave stats */}
          <div style={{ marginTop:"10px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>WAVE STATS</div>
            {[
              ["Amplitude A",    `${A} sq = ${(A*0.5).toFixed(1)}mm`],
              ["Wavelength λ",   `${lambda} sq = ${(lambda*0.5).toFixed(1)}mm`],
              ["Pitch d",        `${d} sq = ${(d*0.5).toFixed(1)}mm`],
              ["Strand w",       `${strandW} sq = ${(strandW*0.5).toFixed(1)}mm`],
              ["Gap d-w",        `${(d-strandW).toFixed(1)} sq`],
              ["Fold at",        `x=${(lambda/2).toFixed(0)} sq`],
              ["A/λ ratio",      `${(A/lambda).toFixed(3)}`],
              ["Repeats/row",    `${(cols/lambda).toFixed(2)}×`],
            ].map(([k,v]) => (
              <div key={k} style={{ display:"flex", justifyContent:"space-between", padding:"2px 0", borderBottom:`1px solid ${UI.dimmest}` }}>
                <span style={{ fontSize:"8px", color:UI.dimmer }}>{k}</span>
                <span style={{ fontSize:"9px", color:UI.text }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Classical reference */}
          <div style={{ marginTop:"8px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>LUTHIER RANGE</div>
            <div style={{ fontSize:"8px", color:UI.dimmer, lineHeight:"1.8" }}>
              <span style={{ color:d-strandW>0?"#2d9a6f":"#8b2020" }}>
                {d-strandW>0?"✓":"⚠"} Gap d−w = {(d-strandW).toFixed(1)} sq
              </span><br/>
              <span style={{ color:A<lambda/2?"#2d9a6f":"#c9a96e" }}>
                {A<lambda/2?"✓":"⚠"} A &lt; λ/2 {A<lambda/2?"(strands won't cross)":"(may cross!)"}
              </span><br/>
              <span style={{ color:(rows*0.5)>=5&&(rows*0.5)<=9?"#2d9a6f":"#c9a96e" }}>
                {(rows*0.5)>=5&&(rows*0.5)<=9?"✓":"⚠"} Tile {mmH}mm tall
                {(rows*0.5)>=5&&(rows*0.5)<=9?" (5–9mm ✓)":""}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
