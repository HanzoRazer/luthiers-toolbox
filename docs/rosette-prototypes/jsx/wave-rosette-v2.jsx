import { useState, useEffect, useRef } from "react";

const UI = {
  bg:"#0b0806", panel:"#0f0c08", border:"#2e2010", border2:"#1e1508",
  gold:"#e8c87a", amber:"#c9a96e", dim:"#7a5c2e", dimmer:"#4a3010",
  dimmest:"#2a1e0a", text:"#c9a96e",
};

// ─── STRAND SEGMENT FORMULA ──────────────────────────────────────
//
// Each strand is a sequence of DISCRETE arched segments, not a continuous wave.
//
// Segment k of strand n starts at:
//   x_start(n,k) = k · (segLen + gap)  +  (n · rowOffset) mod (segLen + gap)
//
// Within that segment, the centerline is:
//   y_center(x) = n·d + A · sin( π · (x - x_start) / segLen )
//
// This is a half-sine arch — starts flat, peaks at mid-segment, returns flat.
// The arch only exists for x in [x_start, x_start + segLen].
// Between segments (the gap): background only.
//
// A pixel (col, row) is ON the strand if:
//   1. col falls within an active segment window
//   2. |row - y_center(col)| < strandW/2

function buildSegmentGrid({
  cols, rows, A, segLen, gap, d, strandW, numStrands, rowOffset, archShape, colorMode
}) {
  const pitch = segLen + gap;
  const grid = [];

  for (let r = 0; r < rows; r++) {
    const row = [];
    for (let c = 0; c < cols; c++) {
      let hit = false;
      let hitN = 0;

      for (let n = -2; n <= numStrands + 2; n++) {
        // Row offset staggers alternate strands
        const strandPhase = (n * rowOffset) % pitch;
        // Which segment does this x fall in, accounting for phase?
        const xShifted = ((c - strandPhase) % pitch + pitch * 100) % pitch;
        const inSegment = xShifted < segLen;

        if (!inSegment) continue;

        // Local x position within segment [0 .. segLen]
        const localX = xShifted;
        let arch;
        if (archShape === "sine")     arch = A * Math.sin(Math.PI * localX / segLen);
        else if (archShape === "tri") arch = A * (localX < segLen/2 ? (2*localX/segLen) : (2 - 2*localX/segLen));
        else if (archShape === "flat") arch = A * Math.sin(Math.PI * localX / segLen) * Math.sin(Math.PI * localX / segLen); // squared = flatter top
        else arch = A * Math.sin(Math.PI * localX / segLen); // default sine

        const centerY = n * d + arch;
        const dist = Math.abs(r - centerY);

        if (dist < strandW / 2) {
          hit = true;
          hitN = n;
          break;
        }
      }

      if (hit) {
        if (colorMode === "bw")    row.push(((hitN % 2) + 2) % 2 === 0 ? 1 : 2);
        else if (colorMode === "mono") row.push(1);
        else if (colorMode === "alt3") row.push(((hitN % 3) + 3) % 3 === 0 ? 1 : ((hitN % 3) + 3) % 3 === 1 ? 2 : 3);
        else row.push(1);
      } else {
        row.push(0);
      }
    }
    grid.push(row);
  }
  return grid;
}

// ─── JIG PROFILE CANVAS ──────────────────────────────────────────
function JigCanvas({ cols, rows, A, segLen, gap, d, strandW, numStrands, rowOffset, archShape, vColors, canvasW, canvasH }) {
  const ref = useRef(null);
  const pitch = segLen + gap;

  useEffect(() => {
    const canvas = ref.current; if (!canvas) return;
    canvas.width = canvasW; canvas.height = canvasH;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = UI.bg; ctx.fillRect(0, 0, canvasW, canvasH);

    const scaleX = canvasW / cols;
    const scaleY = canvasH / rows;
    const midY = canvasH / 2;

    const archY = (localX) => {
      if (archShape === "sine") return A * Math.sin(Math.PI * localX / segLen);
      if (archShape === "tri")  return A * (localX < segLen/2 ? (2*localX/segLen) : (2 - 2*localX/segLen));
      return A * Math.pow(Math.sin(Math.PI * localX / segLen), 2);
    };

    // Draw strand segments
    for (let n = -1; n <= numStrands + 1; n++) {
      const strandPhase = (n * rowOffset) % pitch;
      const baseY = n * d;
      const col = ((hitN) => hitN % 3)(n);
      ctx.strokeStyle = col === 0 ? "#f0e8d0" : col === 1 ? vColors[2] : "rgba(200,160,50,0.5)";
      ctx.lineWidth = strandW * scaleY;
      ctx.lineCap = "round";

      // Draw all segments across the width
      for (let k = -1; k <= Math.ceil(cols / pitch) + 1; k++) {
        const xStart = k * pitch + strandPhase;
        if (xStart > cols || xStart + segLen < 0) continue;

        ctx.beginPath();
        let started = false;
        for (let lx = 0; lx <= segLen; lx += 0.5) {
          const x = (xStart + lx) * scaleX;
          const y = (baseY + archY(lx)) * scaleY + midY;
          if (!started) { ctx.moveTo(x, y); started = true; }
          else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // Gap dots
        if (gap > 0) {
          ctx.fillStyle = "rgba(200,160,50,0.2)";
          const gapX = (xStart + segLen + gap / 2) * scaleX;
          const gapY = baseY * scaleY + midY;
          if (gapX > 0 && gapX < canvasW) {
            ctx.beginPath(); ctx.arc(gapX, gapY, 1.5, 0, Math.PI * 2); ctx.fill();
          }
        }
      }
    }

    // Segment boundary guides
    ctx.strokeStyle = "rgba(200,160,50,0.3)";
    ctx.lineWidth = 0.8; ctx.setLineDash([2, 4]);
    for (let k = 0; k * pitch < cols + pitch; k++) {
      const x = k * pitch * scaleX;
      if (x >= 0 && x <= canvasW) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvasH); ctx.stroke();
      }
      const xEnd = (k * pitch + segLen) * scaleX;
      if (xEnd >= 0 && xEnd <= canvasW) {
        ctx.strokeStyle = "rgba(200,80,50,0.25)";
        ctx.beginPath(); ctx.moveTo(xEnd, 0); ctx.lineTo(xEnd, canvasH); ctx.stroke();
        ctx.strokeStyle = "rgba(200,160,50,0.3)";
      }
    }
    ctx.setLineDash([]);

    // Amplitude annotation
    const annoX = (segLen * 0.5) * scaleX;
    const annoYBase = midY;
    const annoYTip  = midY - A * scaleY;
    ctx.strokeStyle = "rgba(200,160,50,0.6)"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(annoX, annoYBase); ctx.lineTo(annoX, annoYTip); ctx.stroke();
    ctx.fillStyle = "rgba(200,160,50,0.7)"; ctx.font = "9px 'Courier New'";
    ctx.fillText(`A=${A}`, annoX + 4, (annoYBase + annoYTip) / 2 + 3);

    // Labels
    ctx.fillStyle = "rgba(200,160,50,0.4)"; ctx.font = "8px 'Courier New'";
    ctx.fillText(`seg=${segLen}sq`, 4, canvasH - 16);
    ctx.fillText(`gap=${gap}sq`, 4, canvasH - 5);

  }, [cols, rows, A, segLen, gap, d, strandW, numStrands, rowOffset, archShape, vColors, canvasW, canvasH]);

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
    const cmapRgb = vColors.map(hexToRgb);

    const imgData = ctx.createImageData(W, H);
    const data = imgData.data;
    for (let r=0; r<nRows; r++) {
      for (let c=0; c<cols; c++) {
        const v = grid[r][c];
        const rgb = cmapRgb[v] ?? cmapRgb[0];
        for (let py=r*cellSize; py<(r+1)*cellSize; py++) {
          for (let px=c*cellSize; px<(c+1)*cellSize; px++) {
            const idx=(py*W+px)*4;
            data[idx]=rgb.r; data[idx+1]=rgb.g; data[idx+2]=rgb.b; data[idx+3]=255;
          }
        }
      }
    }
    ctx.putImageData(imgData, 0, 0);

    if (cellSize >= 5) {
      ctx.strokeStyle = "rgba(90,60,20,0.15)"; ctx.lineWidth = 0.5;
      for (let c=0; c<=cols; c++) { ctx.beginPath(); ctx.moveTo(c*cellSize,0); ctx.lineTo(c*cellSize,H); ctx.stroke(); }
      for (let r=0; r<=nRows; r++) { ctx.beginPath(); ctx.moveTo(0,r*cellSize); ctx.lineTo(W,r*cellSize); ctx.stroke(); }
    }

    if (showGuides) {
      // Segment start lines (gold)
      ctx.strokeStyle = "rgba(200,160,50,0.35)"; ctx.lineWidth = 1; ctx.setLineDash([3,3]);
      for (let k=0; k*pitch<=cols; k++) {
        const x = k * pitch * cellSize;
        ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke();
      }
      // Segment end lines (red)
      ctx.strokeStyle = "rgba(200,80,50,0.3)";
      for (let k=0; k*pitch<=cols; k++) {
        const x = (k * pitch + segLen) * cellSize;
        if (x <= W) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
      }
      ctx.setLineDash([]);
    }

  }, [grid, vColors, cellSize, showGuides, segLen, gap]);

  return <canvas ref={ref} style={{ border:`1px solid ${UI.border}`, borderRadius:"3px", display:"block", maxWidth:"100%", imageRendering: cellSize<=4?"pixelated":"auto" }} />;
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
    const nRows=grid.length, nCols=grid[0].length;
    const ringW=rOut-rIn;
    const circ=2*Math.PI*(rIn+rOut)/2;
    const hexToRgb=h=>({r:parseInt(h.slice(1,3),16),g:parseInt(h.slice(3,5),16),b:parseInt(h.slice(5,7),16)});
    const rgb=vColors.map(hexToRgb);
    ctx.beginPath(); ctx.arc(cx,cy,rIn,0,Math.PI*2); ctx.fillStyle="#060402"; ctx.fill();
    const imgData=ctx.createImageData(size,size); const data=imgData.data;
    for (let py=0;py<size;py++) for (let px=0;px<size;px++) {
      const dx=px-cx,dy=py-cy,dist=Math.sqrt(dx*dx+dy*dy);
      if (dist<rIn||dist>rOut) continue;
      const row=Math.min(Math.floor((dist-rIn)/ringW*nRows),nRows-1);
      const angle=Math.atan2(dy,dx)+Math.PI;
      const col=((Math.floor(angle*(rIn+rOut)/2/(circ/nCols))%nCols)+nCols)%nCols;
      const v=grid[row]?.[col]??0;
      const c=rgb[v]??rgb[0];
      const idx=(py*size+px)*4;
      data[idx]=c.r;data[idx+1]=c.g;data[idx+2]=c.b;data[idx+3]=255;
    }
    ctx.putImageData(imgData,0,0);
    ctx.strokeStyle="rgba(200,160,50,0.3)"; ctx.lineWidth=0.8; ctx.setLineDash([3,4]);
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
        <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{val}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val}
        onChange={e=>set(Number(e.target.value))} style={{ width:"100%", accentColor:"#c9a96e" }} />
      {note && <div style={{ fontSize:"8px", color:UI.dimmer, marginTop:"1px" }}>{note}</div>}
    </div>
  );
}

// ─── MAIN ────────────────────────────────────────────────────────
export default function WaveRosetteV2() {
  // Strand segment parameters
  const [A,          setA]          = useState(5);
  const [segLen,     setSegLen]     = useState(14);
  const [gap,        setGap]        = useState(3);
  const [d,          setD]          = useState(4);
  const [strandW,    setStrandW]    = useState(1.5);
  const [numStrands, setNumStrands] = useState(6);
  const [rowOffset,  setRowOffset]  = useState(0);   // stagger between rows (in squares)
  const [archShape,  setArchShape]  = useState("sine");

  // Grid
  const [cols, setCols] = useState(48);
  const [rows, setRows] = useState(28);

  // Color
  const [colorMode, setColorMode] = useState("bw");
  const [c0, setC0] = useState("#1a1008");
  const [c1, setC1] = useState("#f0e8d0");
  const [c2, setC2] = useState("#c9a020");
  const [c3, setC3] = useState("#2d6a4f");

  // View
  const [cellSize,   setCellSize]   = useState(12);
  const [showGuides, setShowGuides] = useState(true);
  const [rIn,        setRIn]        = useState(90);
  const [rOut,       setROut]       = useState(138);
  const [tab,        setTab]        = useState("grid");

  const pitch = segLen + gap;
  const vColors = [c0, c1, c2, c3];

  const grid = buildSegmentGrid({
    cols, rows, A, segLen, gap, d, strandW, numStrands, rowOffset, archShape, colorMode
  });

  const counts = {};
  grid.forEach(row => row.forEach(v => counts[v] = (counts[v]||0)+1));
  const total = cols * rows;
  const mmW = (cols * 0.5).toFixed(1);
  const mmH = (rows * 0.5).toFixed(1);
  const fill = ((total - (counts[0]||0)) / total * 100).toFixed(1);

  return (
    <div style={{ minHeight:"100vh", background:UI.bg, fontFamily:"'Courier New',monospace", color:UI.text, padding:"20px", userSelect:"none" }}>

      {/* HEADER */}
      <div style={{ borderBottom:`1px solid ${UI.border2}`, paddingBottom:"12px", marginBottom:"16px" }}>
        <div style={{ fontSize:"9px", letterSpacing:"4px", color:UI.dimmer }}>
          THE PRODUCTION SHOP · CUSTOM INLAY MODULE · V2
        </div>
        <div style={{ fontSize:"22px", fontWeight:"bold", color:UI.gold, letterSpacing:"3px", marginTop:"3px" }}>
          Wave Rosette · Discrete Segments
        </div>
        <div style={{ fontSize:"10px", color:UI.dimmer, marginTop:"2px", letterSpacing:"1px" }}>
          Isolated arched strands end-to-end · y(x) = n·d + A·sin(π·x_local / segLen)
        </div>

        {/* Live formula display */}
        <div style={{ marginTop:"8px", padding:"8px 12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px", display:"inline-block" }}>
          <span style={{ fontSize:"10px", color:"#7a9adb" }}>yₙ</span>
          <span style={{ fontSize:"10px", color:UI.dimmer }}>(x) = n·</span>
          <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{d}</span>
          <span style={{ fontSize:"10px", color:UI.dimmer }}> + </span>
          <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{A}</span>
          <span style={{ fontSize:"10px", color:UI.dimmer }}>·{archShape}(π·x_local / </span>
          <span style={{ fontSize:"11px", color:UI.gold, fontWeight:"bold" }}>{segLen}</span>
          <span style={{ fontSize:"10px", color:UI.dimmer }}>)</span>
          <span style={{ fontSize:"9px", color:UI.dimmer, marginLeft:"10px" }}>
            active for x_local ∈ [0, <span style={{ color:UI.gold }}>{segLen}</span>] · gap = <span style={{ color:UI.gold }}>{gap}</span> sq
          </span>
        </div>

        <div style={{ marginTop:"8px", display:"flex", gap:"5px", flexWrap:"wrap" }}>
          {[
            [`pitch ${segLen}+${gap}`, `= ${pitch} sq`],
            [`segment`, `${(segLen*0.5).toFixed(1)}mm`],
            [`gap`, `${(gap*0.5).toFixed(1)}mm`],
            [`A`, `${(A*0.5).toFixed(1)}mm arch`],
            [`${fill}%`, `strand fill`],
            [`tile`, `${mmW}×${mmH}mm`],
          ].map(([a,b]) => (
            <div key={a} style={{ padding:"3px 8px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"3px", fontSize:"9px", color:UI.dimmer }}>
              <span style={{ color:UI.gold, fontWeight:"bold" }}>{a}</span> {b}
            </div>
          ))}
        </div>
      </div>

      {/* TABS */}
      <div style={{ display:"flex", gap:"4px", marginBottom:"16px", flexWrap:"wrap" }}>
        {[["grid","Pixel Grid"],["jig","Jig Profile"],["ring","Rosette Ring"],["bom","BOM"]].map(([k,l]) => (
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
        <div style={{ width:"200px", flexShrink:0 }}>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>SEGMENT SHAPE</div>
            <Knob label="A — Arch height" val={A} set={setA} min={0} max={16} step={0.5}
              unit=" sq" note={`${(A*0.5).toFixed(1)}mm peak`} />
            <Knob label="segLen — Segment length" val={segLen} set={setSegLen} min={4} max={40}
              unit=" sq" note={`${(segLen*0.5).toFixed(1)}mm per segment`} />
            <Knob label="gap — Space between" val={gap} set={setGap} min={0} max={16}
              unit=" sq" note={`${(gap*0.5).toFixed(1)}mm gap`} />

            {/* Arch shape selector */}
            <div style={{ marginTop:"4px", marginBottom:"8px" }}>
              <div style={{ fontSize:"9px", color:UI.dim, marginBottom:"5px", letterSpacing:"1px" }}>ARCH SHAPE</div>
              {[
                ["sine",  "Sine  — smooth arch"],
                ["tri",   "Triangle  — sharp peak"],
                ["flat",  "Sin² — flat top"],
              ].map(([v,l]) => (
                <div key={v} onClick={()=>setArchShape(v)} style={{
                  padding:"3px 7px", marginBottom:"3px", cursor:"pointer", fontSize:"9px",
                  border:archShape===v?"1px solid #c9a96e":`1px solid ${UI.border}`,
                  borderRadius:"3px", background:archShape===v?"#1e1508":"transparent",
                  color:archShape===v?UI.gold:UI.dim,
                }}>{l}</div>
              ))}
            </div>
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>STRAND ARRAY</div>
            <Knob label="d — Strand pitch" val={d} set={setD} min={2} max={14} step={0.5}
              unit=" sq" note={`${(d*0.5).toFixed(1)}mm center-to-center`} />
            <Knob label="w — Strand width" val={strandW} set={setStrandW} min={0.5} max={6} step={0.5}
              unit=" sq" note={`${(strandW*0.5).toFixed(1)}mm veneer`} />
            <Knob label="N — Strand rows" val={numStrands} set={setNumStrands} min={1} max={14} />
            <Knob label="Stagger offset" val={rowOffset} set={setRowOffset} min={0} max={pitch} step={1}
              unit=" sq" note={rowOffset===0?"no stagger":rowOffset===Math.round(pitch/2)?"½ pitch stagger":`${rowOffset}/${pitch} pitch`} />
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"10px" }}>TILE SIZE</div>
            <Knob label="Columns" val={cols} set={setCols} min={12} max={80} note={`${mmW}mm`} />
            <Knob label="Rows"    val={rows} set={setRows} min={6}  max={44} note={`${mmH}mm`} />
          </div>

          <div style={{ padding:"12px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", marginBottom:"10px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"3px", color:UI.dim, marginBottom:"8px" }}>VENEER COLORS</div>
            <div style={{ fontSize:"9px", color:UI.dim, marginBottom:"6px" }}>Color mode</div>
            {[["bw","Alternating B/W"],["mono","Single color"],["alt3","3-color cycle"]].map(([v,l]) => (
              <div key={v} onClick={()=>setColorMode(v)} style={{
                padding:"3px 7px", marginBottom:"3px", cursor:"pointer", fontSize:"9px",
                border:colorMode===v?"1px solid #c9a96e":`1px solid ${UI.border}`,
                borderRadius:"3px", background:colorMode===v?"#1e1508":"transparent",
                color:colorMode===v?UI.gold:UI.dim,
              }}>{l}</div>
            ))}
            <div style={{ marginTop:"8px" }}>
              {[["Background",c0,setC0],["Strand A",c1,setC1],["Strand B",c2,setC2],["Strand C",c3,setC3]].map(([l,v,s]) => (
                <div key={l} style={{ display:"flex", alignItems:"center", gap:"7px", marginBottom:"5px" }}>
                  <input type="color" value={v} onChange={e=>s(e.target.value)}
                    style={{ width:"24px", height:"20px", border:`1px solid ${UI.border}`, borderRadius:"2px", cursor:"pointer", padding:"1px" }} />
                  <span style={{ fontSize:"9px", color:UI.dim }}>{l}</span>
                </div>
              ))}
            </div>
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
            }}>Segment guides</div>
          </div>

          {/* Geometry panel */}
          <div style={{ padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>GEOMETRY CHECK</div>
            <div style={{ fontSize:"8px", color:UI.dimmer, lineHeight:"2" }}>
              <span style={{ color: gap > 0 ? "#2d9a6f" : "#8b2020" }}>
                {gap > 0 ? "✓" : "⚠"} gap = {gap} sq ({(gap*0.5).toFixed(1)}mm)
              </span><br/>
              <span style={{ color: d > strandW ? "#2d9a6f" : "#8b2020" }}>
                {d > strandW ? "✓" : "⚠"} d &gt; w ({d} &gt; {strandW})
              </span><br/>
              <span style={{ color: A <= d ? "#2d9a6f" : "#e8c87a" }}>
                {A <= d ? "✓" : "△"} A vs d: {A} vs {d}
              </span><br/>
              <span style={{ color: parseFloat(mmH)>=5 && parseFloat(mmH)<=9 ? "#2d9a6f" : "#e8c87a" }}>
                {parseFloat(mmH)>=5&&parseFloat(mmH)<=9?"✓":"△"} Tile {mmH}mm tall
              </span><br/>
              <br/>
              <span style={{ color:UI.amber }}>Pitch:</span> {pitch} sq = {(pitch*0.5).toFixed(1)}mm<br/>
              <span style={{ color:UI.amber }}>Fill:</span> {fill}% strand<br/>
              <span style={{ color:UI.amber }}>Segs/row:</span> {(cols/pitch).toFixed(2)}×
            </div>
          </div>
        </div>

        {/* MAIN VIEW */}
        <div style={{ flex:1, minWidth:0 }}>

          {tab === "grid" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                PIXEL GRID · {cols}×{rows} sq · 0.5mm/sq ·
                <span style={{ color:"rgba(200,160,50,0.6)" }}> gold = segment start</span> ·
                <span style={{ color:"rgba(200,80,50,0.6)" }}> red = segment end</span>
              </div>
              <GridCanvas grid={grid} vColors={vColors} cellSize={cellSize}
                showGuides={showGuides} segLen={segLen} gap={gap} />

              {/* Segment anatomy diagram */}
              <div style={{ marginTop:"12px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
                <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"8px" }}>SEGMENT ANATOMY</div>
                <div style={{ position:"relative", height:"60px", background:UI.bg, borderRadius:"3px", border:`1px solid ${UI.border2}`, overflow:"hidden" }}>
                  <svg width="100%" height="60" style={{ position:"absolute", top:0, left:0 }}>
                    {/* Segment arc */}
                    <path d={`M 20,45 Q ${20 + segLen*5*0.5},${45 - A*3} ${20 + segLen*5},45`}
                      fill="none" stroke="#f0e8d0" strokeWidth="3" strokeLinecap="round" />
                    {/* Gap */}
                    <line x1={20 + segLen*5} y1="45" x2={20 + segLen*5 + gap*5} y2="45"
                      stroke="rgba(200,160,50,0.2)" strokeWidth="1" strokeDasharray="2,2" />
                    {/* Next segment arc */}
                    <path d={`M ${20+segLen*5+gap*5},45 Q ${20+segLen*5+gap*5+segLen*5*0.5},${45-A*3} ${20+segLen*5*2+gap*5},45`}
                      fill="none" stroke="#f0e8d0" strokeWidth="3" strokeLinecap="round" />
                    {/* Annotations */}
                    <line x1="20" y1="52" x2={20+segLen*5} y2="52" stroke="rgba(200,160,50,0.5)" strokeWidth="1" />
                    <text x={20 + segLen*5/2} y="60" textAnchor="middle" fill="rgba(200,160,50,0.7)" fontSize="8" fontFamily="Courier New">seg={segLen}sq</text>
                    <line x1={20+segLen*5} y1="52" x2={20+segLen*5+gap*5} y2="52" stroke="rgba(200,80,50,0.5)" strokeWidth="1" />
                    <text x={20+segLen*5+gap*5/2} y="60" textAnchor="middle" fill="rgba(200,80,50,0.7)" fontSize="8" fontFamily="Courier New">gap</text>
                    {/* Amplitude arrow */}
                    <line x1={20+segLen*5*0.5} y1="45" x2={20+segLen*5*0.5} y2={45-A*3}
                      stroke="rgba(200,160,50,0.5)" strokeWidth="1" />
                    <text x={20+segLen*5*0.5+3} y={45-A*1.5} fill="rgba(200,160,50,0.7)" fontSize="8" fontFamily="Courier New">A</text>
                  </svg>
                </div>
              </div>
            </div>
          )}

          {tab === "jig" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                JIG PROFILE · Caul shape for each strand row · Slice at segment boundaries
              </div>
              <JigCanvas cols={cols} rows={rows} A={A} segLen={segLen} gap={gap}
                d={d} strandW={strandW} numStrands={numStrands} rowOffset={rowOffset}
                archShape={archShape} vColors={vColors}
                canvasW={Math.min(cols*cellSize, 640)} canvasH={rows*cellSize} />
              <div style={{ marginTop:"10px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.9" }}>
                <span style={{ color:UI.amber }}>Gold verticals</span> = segment start (glue stack here, begin slice).<br/>
                <span style={{ color:"rgba(200,80,50,0.8)" }}>Red verticals</span> = segment end (end of arch, gap begins).<br/>
                <span style={{ color:UI.dimmer }}>Dots in gap zone</span> = gap region — no veneer contact, background shows through.<br/><br/>
                Caul CNC profile: arch height A={(A*0.5).toFixed(1)}mm over {(segLen*0.5).toFixed(1)}mm run.
                Slice pitch = {(pitch*0.5).toFixed(1)}mm. Each slice = one rosette tile segment.
              </div>
            </div>
          )}

          {tab === "ring" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                ROSETTE RING · r_in={rIn}px · r_out={rOut}px · tile wraps continuously
              </div>
              <RosetteCanvas grid={grid} vColors={vColors} rIn={rIn} rOut={rOut} size={360} />
              <div style={{ marginTop:"8px", fontSize:"9px", color:UI.dimmer, lineHeight:"1.7" }}>
                Strands arch radially inward at each segment · gap appears as background ring between arches.
                Try stagger offset = {Math.round(pitch/2)} sq for a fish-scale / overlapping effect.
              </div>
            </div>
          )}

          {tab === "bom" && (
            <div>
              <div style={{ fontSize:"9px", color:UI.dimmer, marginBottom:"8px", letterSpacing:"2px" }}>
                VENEER BOM · {rows} rows × {cols} cols · run-length encoded
              </div>
              <div style={{ maxHeight:"380px", overflowY:"auto", border:`1px solid ${UI.border}`, borderRadius:"3px" }}>
                {grid.map((row, r) => {
                  const parts=[];
                  let cur=row[0], run=1;
                  for (let c=1;c<cols;c++) {
                    if(row[c]===cur) run++;
                    else { parts.push({v:cur,n:run}); cur=row[c]; run=1; }
                  }
                  parts.push({v:cur,n:run});
                  const lbl=["B","A","C","D"];
                  const tc=v=>v===1?"#1a1008":"#c9a96e";
                  return (
                    <div key={r} style={{ display:"flex", alignItems:"center", gap:"5px", padding:"3px 8px", borderBottom:`1px solid ${UI.dimmest}`, background:r%2===0?"transparent":"#0c0903" }}>
                      <span style={{ fontSize:"7px", color:UI.dimmer, width:"18px", flexShrink:0 }}>{r+1}</span>
                      <span style={{ fontSize:"7px", color:UI.dimmer, width:"26px", flexShrink:0 }}>{((r+1)*0.5).toFixed(1)}</span>
                      <div style={{ display:"flex", gap:"2px", flexWrap:"wrap", flex:1 }}>
                        {parts.map((p,i) => (
                          <span key={i} style={{
                            padding:"1px 3px", borderRadius:"2px",
                            background:vColors[p.v], border:p.v===0?`1px solid ${UI.border}`:"none",
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
                    ["Background",counts[0]||0],["Strand A",counts[1]||0],
                    ["Strand B",counts[2]||0],["Strand C",counts[3]||0],
                    ["Total cells",total],["Fill %",fill+"%"],
                    ["Tile",`${mmW}×${mmH}mm`],["Pitch",`${(pitch*0.5).toFixed(1)}mm`],
                  ].map(([k,v])=>(
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

        {/* RIGHT SIDEBAR */}
        <div style={{ width:"186px", flexShrink:0 }}>
          <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>RING PREVIEW</div>
          <RosetteCanvas grid={grid} vColors={vColors} rIn={rIn*0.42} rOut={rOut*0.42} size={182} />

          <div style={{ marginTop:"10px", marginBottom:"5px", fontSize:"9px", letterSpacing:"2px", color:UI.dim }}>TILE SNAPSHOT</div>
          <div style={{ display:"inline-block", border:`1px solid ${UI.border}`, borderRadius:"2px", overflow:"hidden" }}>
            {grid.map((row,r)=>(
              <div key={r} style={{ display:"flex" }}>
                {row.map((v,c)=>(<div key={c} style={{ width:"4px", height:"4px", background:vColors[v] }}/>))}
              </div>
            ))}
          </div>
          <div style={{ fontSize:"8px", color:UI.dimmer, marginTop:"2px" }}>{cols}×{rows} @ 4px</div>

          {/* Stagger presets */}
          <div style={{ marginTop:"10px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"7px" }}>STAGGER PRESETS</div>
            {[
              [0,           "No stagger"],
              [Math.round(pitch/2), "½ pitch (fish-scale)"],
              [Math.round(pitch/3), "⅓ pitch"],
              [Math.round(pitch/4), "¼ pitch"],
            ].map(([v,l]) => (
              <div key={l} onClick={()=>setRowOffset(v)} style={{
                padding:"4px 7px", marginBottom:"3px", cursor:"pointer",
                border:rowOffset===v?"1px solid #c9a96e":`1px solid ${UI.border}`,
                borderRadius:"3px", background:rowOffset===v?"#1e1508":"transparent",
                fontSize:"9px", color:rowOffset===v?UI.gold:UI.dim,
              }}>{l}</div>
            ))}
          </div>

          {/* Arch shape diagram */}
          <div style={{ marginTop:"8px", padding:"10px", background:UI.panel, border:`1px solid ${UI.border}`, borderRadius:"4px" }}>
            <div style={{ fontSize:"9px", letterSpacing:"2px", color:UI.dim, marginBottom:"6px" }}>ARCH PROFILE</div>
            <svg width="160" height="50">
              {/* sine */}
              <path d="M 10,40 Q 45,8 80,40" fill="none" stroke={archShape==="sine"?UI.gold:"#3a2e1a"} strokeWidth="2" strokeLinecap="round" />
              <text x="37" y="48" fill={archShape==="sine"?UI.gold:"#3a2e1a"} fontSize="8" fontFamily="Courier New">sine</text>
              {/* tri */}
              <polyline points="90,40 115,10 140,40" fill="none" stroke={archShape==="tri"?UI.gold:"#3a2e1a"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <text x="105" y="48" fill={archShape==="tri"?UI.gold:"#3a2e1a"} fontSize="8" fontFamily="Courier New">tri</text>
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
