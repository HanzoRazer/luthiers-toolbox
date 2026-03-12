import { useState, useEffect, useRef, useCallback } from "react";

// ─── COLOR TOKENS ────────────────────────────────────────────────
const UI = {
  bg:      "#0b0806",
  panel:   "#0f0c08",
  border:  "#2e2010",
  border2: "#1e1508",
  gold:    "#e8c87a",
  amber:   "#c9a96e",
  dim:     "#7a5c2e",
  dimmer:  "#4a3010",
  dimmest: "#2a1e0a",
  text:    "#c9a96e",
  green:   "#2d7a4f",
  red:     "#8b2020",
};

// ─── VENEER DEFAULTS ─────────────────────────────────────────────
const VENEER_DEFAULTS = {
  black:  { fill: "#1a1008", label: "Black (Ebony)" },
  white:  { fill: "#f0e8d0", label: "White (Maple)" },
  accent: { fill: "#2d6a4f", label: "Accent (Green)" },
  border: { fill: "#1a1008", label: "Border (Ebony)" },
};

// ─── ACCENT COLOR PRESETS ────────────────────────────────────────
const ACCENT_PRESETS = [
  { name:"Green",  fill:"#2d6a4f" },
  { name:"Red",    fill:"#8b2020" },
  { name:"Gold",   fill:"#c8920a" },
  { name:"Blue",   fill:"#1e3f7a" },
  { name:"White",  fill:"#f0e8d0" },
  { name:"Purple", fill:"#4a1a6a" },
];

// ─── GRID BUILDER ────────────────────────────────────────────────
// Builds the flat ladder tile matrix
// 0=black  1=white  2=accent  3=border-black
function buildLadderGrid({
  numPairs,      // how many B/W column pairs
  blackWidth,    // columns per black strip
  whiteWidth,    // columns per white strip
  sectionRows,   // rows of B/W stripes per section
  numSections,   // number of ladder sections
  hasBorder,     // solid black row at top & bottom
  hasRung,       // green accent row between sections
  hasOuterAccent,// green row just inside border
}) {
  const rows = [];

  // Top solid black border
  if (hasBorder) rows.push("border");
  // Top accent line just inside border
  if (hasOuterAccent) rows.push("accent");

  for (let s = 0; s < numSections; s++) {
    // Add rung between sections (not before first)
    if (s > 0 && hasRung) rows.push("accent");
    for (let r = 0; r < sectionRows; r++) rows.push("stripe");
  }

  // Bottom accent line just inside border
  if (hasOuterAccent) rows.push("accent");
  // Bottom solid black border
  if (hasBorder) rows.push("border");

  const totalCols = numPairs * (blackWidth + whiteWidth);

  // Build col pattern for one stripe row
  const stripeRow = [];
  for (let p = 0; p < numPairs; p++) {
    for (let b = 0; b < blackWidth; b++) stripeRow.push(0);
    for (let w = 0; w < whiteWidth; w++) stripeRow.push(1);
  }

  return rows.map(type => {
    if (type === "stripe") return [...stripeRow];
    if (type === "accent") return Array(totalCols).fill(2);
    if (type === "border") return Array(totalCols).fill(3);
    return Array(totalCols).fill(0);
  });
}

// ─── COUNT HELPERS ───────────────────────────────────────────────
function countColors(grid) {
  const c = { 0:0, 1:0, 2:0, 3:0 };
  grid.forEach(row => row.forEach(v => c[v]++));
  return c;
}

// ─── ROSETTE RING CANVAS ─────────────────────────────────────────
function RosetteCanvas({ grid, veneers, rIn, rOut, canvasSize }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return;
    canvas.width = canvasSize; canvas.height = canvasSize;
    const ctx = canvas.getContext("2d");
    const cx = canvasSize / 2, cy = canvasSize / 2;

    // Background
    ctx.fillStyle = UI.bg; ctx.fillRect(0, 0, canvasSize, canvasSize);

    if (!grid || grid.length === 0) return;

    const rows = grid.length;
    const cols = grid[0].length;
    const ringWidth = rOut - rIn;
    const rowHeight = ringWidth / rows; // mm equivalent per row in px

    // Draw soundhole fill
    ctx.beginPath(); ctx.arc(cx, cy, rIn, 0, Math.PI * 2);
    ctx.fillStyle = "#060402"; ctx.fill();

    // For each tiny angular segment, sample the grid row
    // Map radial distance → grid row, angle → grid column tile
    const totalAngle = Math.PI * 2;
    const tileCircumference = 2 * Math.PI * ((rIn + rOut) / 2);
    // Each column in the grid = ~0.5mm wide; tile repeats around ring
    const colWidthPx = tileCircumference / cols;

    // Use imageData for performance
    const imgData = ctx.createImageData(canvasSize, canvasSize);
    const data = imgData.data;

    const colorMap = [
      hexToRgb(veneers.black),
      hexToRgb(veneers.white),
      hexToRgb(veneers.accent),
      hexToRgb(veneers.border),
    ];

    for (let py = 0; py < canvasSize; py++) {
      for (let px = 0; px < canvasSize; px++) {
        const dx = px - cx, dy = py - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < rIn || dist > rOut) continue;

        // Radial → row index
        const t = (dist - rIn) / ringWidth;
        const row = Math.min(Math.floor(t * rows), rows - 1);

        // Angular → col index (tiled)
        let angle = Math.atan2(dy, dx) + Math.PI; // 0..2π
        const arcLen = angle * ((rIn + rOut) / 2);
        const col = Math.floor(arcLen / (tileCircumference / cols)) % cols;
        const safeCol = ((col % cols) + cols) % cols;

        const v = grid[row]?.[safeCol] ?? 0;
        const rgb = colorMap[v] ?? colorMap[0];
        const idx = (py * canvasSize + px) * 4;
        data[idx]     = rgb.r;
        data[idx + 1] = rgb.g;
        data[idx + 2] = rgb.b;
        data[idx + 3] = 255;
      }
    }
    ctx.putImageData(imgData, 0, 0);

    // Ring border guides
    ctx.strokeStyle = "rgba(200,160,50,0.4)"; ctx.lineWidth = 0.8;
    ctx.setLineDash([3, 4]);
    [rIn, rOut].forEach(r => {
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
    });
    ctx.setLineDash([]);

    // Center dot
    ctx.beginPath(); ctx.arc(cx, cy, 2, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(200,160,50,0.5)"; ctx.fill();

    // Scale bar 5mm = 5 * (rOut-rIn)/ringWidth_mm ... approximate
    const scaleBar = (rOut - rIn) * 0.83; // ~5mm if ring is 6mm
    ctx.strokeStyle = "rgba(200,160,50,0.65)"; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(10, canvasSize - 14); ctx.lineTo(10 + scaleBar, canvasSize - 14); ctx.stroke();
    ctx.fillStyle = "rgba(200,160,50,0.65)"; ctx.font = "8px 'Courier New'";
    ctx.fillText("~5mm", 10, canvasSize - 20);

  }, [grid, veneers, rIn, rOut, canvasSize]);

  return (
    <canvas ref={canvasRef}
      style={{ borderRadius: "50%", border: `1px solid ${UI.border}`, display: "block" }} />
  );
}

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return { r, g, b };
}

// ─── FLAT GRID DISPLAY ───────────────────────────────────────────
function FlatGrid({ grid, veneers, cellSize, onPaint, isPainting }) {
  if (!grid || grid.length === 0) return null;
  const rows = grid.length, cols = grid[0].length;
  const colorMap = [veneers.black, veneers.white, veneers.accent, veneers.border];

  return (
    <div style={{ display: "inline-block", border: `1px solid ${UI.border}`, cursor: "crosshair", position: "relative" }}>
      {/* Row type labels */}
      {grid.map((row, r) => (
        <div key={r} style={{ display: "flex" }}>
          {row.map((v, c) => (
            <div key={c}
              onMouseDown={() => onPaint && onPaint(r, c, v)}
              onMouseEnter={(e) => { if (isPainting && onPaint) onPaint(r, c, v); }}
              style={{
                width: `${cellSize}px`, height: `${cellSize}px`,
                background: colorMap[v] ?? colorMap[0],
                boxSizing: "border-box",
                borderRight: "0.5px solid rgba(120,80,20,0.18)",
                borderBottom: "0.5px solid rgba(120,80,20,0.18)",
                transition: "background 0.04s",
              }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

// ─── KNOB CONTROL ────────────────────────────────────────────────
function Knob({ label, val, set, min, max, step = 1, unit = "", note = "" }) {
  return (
    <div style={{ marginBottom: "10px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
        <span style={{ fontSize: "9px", letterSpacing: "1.5px", color: UI.dim }}>{label}</span>
        <span style={{ fontSize: "11px", color: UI.gold, fontWeight: "bold" }}>{val}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val}
        onChange={e => set(Number(e.target.value))}
        style={{ width: "100%", accentColor: "#c9a96e" }} />
      {note && <div style={{ fontSize: "8px", color: UI.dimmer, marginTop: "1px" }}>{note}</div>}
    </div>
  );
}

function Toggle({ label, val, set }) {
  return (
    <div onClick={() => set(!val)} style={{
      display: "flex", alignItems: "center", gap: "7px",
      padding: "4px 7px", marginBottom: "4px", cursor: "pointer",
      border: val ? "1px solid #c9a96e" : `1px solid ${UI.border}`,
      borderRadius: "3px", background: val ? "#1e1508" : "transparent",
    }}>
      <div style={{
        width: "10px", height: "10px", borderRadius: "2px",
        background: val ? UI.gold : UI.dimmest, flexShrink: 0,
      }} />
      <span style={{ fontSize: "10px", color: val ? UI.gold : UI.dim }}>{label}</span>
    </div>
  );
}

// ─── MAIN COMPONENT ──────────────────────────────────────────────
export default function SpanishLadderDesigner() {
  // Pattern params
  const [numPairs,       setNumPairs]       = useState(9);
  const [blackWidth,     setBlackWidth]     = useState(1);
  const [whiteWidth,     setWhiteWidth]     = useState(2);
  const [sectionRows,    setSectionRows]    = useState(3);
  const [numSections,    setNumSections]    = useState(3);
  const [hasBorder,      setHasBorder]      = useState(true);
  const [hasRung,        setHasRung]        = useState(true);
  const [hasOuterAccent, setHasOuterAccent] = useState(true);

  // Veneer colors
  const [vBlack,  setVBlack]  = useState(VENEER_DEFAULTS.black.fill);
  const [vWhite,  setVWhite]  = useState(VENEER_DEFAULTS.white.fill);
  const [vAccent, setVAccent] = useState(ACCENT_PRESETS[0].fill);
  const [vBorder, setVBorder] = useState(VENEER_DEFAULTS.border.fill);

  // View
  const [zoom,    setZoom]    = useState(18);
  const [rIn,     setRIn]     = useState(90);
  const [rOut,    setROut]    = useState(140);
  const [tab,     setTab]     = useState("design");

  const veneers = { black: vBlack, white: vWhite, accent: vAccent, border: vBorder };

  // Build grid
  const grid = buildLadderGrid({
    numPairs, blackWidth, whiteWidth,
    sectionRows, numSections,
    hasBorder, hasRung, hasOuterAccent,
  });
  const rows = grid.length;
  const cols = grid[0]?.length ?? 0;
  const counts = countColors(grid);
  const mmW = (cols * 0.5).toFixed(1);
  const mmH = (rows * 0.5).toFixed(1);

  // Row type labels for BOM
  const rowTypes = [];
  if (hasBorder)      rowTypes.push("border");
  if (hasOuterAccent) rowTypes.push("accent");
  for (let s = 0; s < numSections; s++) {
    if (s > 0 && hasRung) rowTypes.push("accent");
    for (let r = 0; r < sectionRows; r++) rowTypes.push("stripe");
  }
  if (hasOuterAccent) rowTypes.push("accent");
  if (hasBorder)      rowTypes.push("border");

  const typeLabel = { border: "Ebony border", accent: "Accent rung", stripe: "B/W ladder" };
  const typeColor = { border: vBorder, accent: vAccent, stripe: null };

  // Stats for each row type
  const stripeSeq = [];
  for (let p = 0; p < numPairs; p++) {
    for (let b = 0; b < blackWidth; b++) stripeSeq.push({ v: 0, n: blackWidth, p });
    for (let w = 0; w < whiteWidth; w++) stripeSeq.push({ v: 1, n: whiteWidth, p });
  }

  // Unique row stacks (for BOM)
  const uniqueRows = [
    { id: "border", label: "Border (solid ebony)", count: (hasBorder ? 2 : 0), colSeq: `${cols}B` },
    { id: "accent", label: "Accent rung", count: (hasOuterAccent ? 2 : 0) + (hasRung ? Math.max(0, numSections - 1) : 0), colSeq: `${cols}A` },
    { id: "stripe", label: `B/W ladder (×${sectionRows} per section, ×${numSections} sections)`, count: sectionRows * numSections,
      colSeq: Array.from({length: numPairs}, (_, p) => `${blackWidth}B${whiteWidth}W`).join(" ") },
  ].filter(r => r.count > 0);

  const canvasSz = 340;

  return (
    <div style={{
      minHeight: "100vh", background: UI.bg,
      fontFamily: "'Courier New', monospace", color: UI.text,
      padding: "24px", userSelect: "none",
    }}>

      {/* ── HEADER ── */}
      <div style={{ borderBottom: `1px solid ${UI.border2}`, paddingBottom: "12px", marginBottom: "18px" }}>
        <div style={{ fontSize: "9px", letterSpacing: "4px", color: UI.dimmer, textTransform: "uppercase" }}>
          The Production Shop · Custom Inlay Module
        </div>
        <div style={{ fontSize: "22px", fontWeight: "bold", color: UI.gold, letterSpacing: "3px", marginTop: "3px" }}>
          Spanish Ladder Rosette
        </div>
        <div style={{ fontSize: "10px", color: UI.dimmer, marginTop: "3px", letterSpacing: "1px" }}>
          Escalera Española · Classical / Flamenco Guitar · Parametric Generator
        </div>
        <div style={{ marginTop: "8px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
          {[
            [`${cols} cols`, `${mmW}mm wide`],
            [`${rows} rows`, `${mmH}mm tall`],
            [`${counts[0]} black`, `strips`],
            [`${counts[1]} white`, `strips`],
            [`${counts[2]+counts[3]} accent`, `strips`],
          ].map(([a, b]) => (
            <div key={a} style={{ padding: "3px 8px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "3px", fontSize: "9px", color: UI.dimmer }}>
              <span style={{ color: UI.gold, fontWeight: "bold" }}>{a}</span> {b}
            </div>
          ))}
        </div>
      </div>

      {/* ── TABS ── */}
      <div style={{ display: "flex", gap: "4px", marginBottom: "18px" }}>
        {[["design","Design"], ["preview","Rosette Preview"], ["bom","Veneer BOM"]].map(([k, l]) => (
          <div key={k} onClick={() => setTab(k)} style={{
            padding: "5px 14px", cursor: "pointer", fontSize: "10px", letterSpacing: "1px",
            border: tab === k ? "1px solid #c9a96e" : `1px solid ${UI.border}`,
            borderRadius: "3px",
            background: tab === k ? "#1e1508" : "transparent",
            color: tab === k ? UI.gold : UI.dim,
            transition: "all .12s",
          }}>{l}</div>
        ))}
      </div>

      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>

        {/* ── LEFT: CONTROLS ── */}
        <div style={{ width: "200px", flexShrink: 0 }}>

          {/* Pattern structure */}
          <div style={{ padding: "12px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "4px", marginBottom: "12px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: UI.dim, marginBottom: "10px" }}>LADDER STRUCTURE</div>
            <Knob label="B/W Pairs (columns)" val={numPairs} set={setNumPairs} min={4} max={16} note={`${numPairs*(blackWidth+whiteWidth)} total columns`} />
            <Knob label="Black strip width" val={blackWidth} set={setBlackWidth} min={1} max={4} unit=" sq" note={`${(blackWidth*0.5).toFixed(1)}mm`} />
            <Knob label="White strip width" val={whiteWidth} set={setWhiteWidth} min={1} max={4} unit=" sq" note={`${(whiteWidth*0.5).toFixed(1)}mm`} />
            <Knob label="Rows per section" val={sectionRows} set={setSectionRows} min={1} max={8} note={`${(sectionRows*0.5).toFixed(1)}mm per section`} />
            <Knob label="Sections (rungs+1)" val={numSections} set={setNumSections} min={1} max={6} />
          </div>

          {/* Structure toggles */}
          <div style={{ padding: "12px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "4px", marginBottom: "12px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: UI.dim, marginBottom: "8px" }}>FRAMING</div>
            <Toggle label="Solid border strips" val={hasBorder} set={setHasBorder} />
            <Toggle label="Accent rungs between sections" val={hasRung} set={setHasRung} />
            <Toggle label="Accent inside borders" val={hasOuterAccent} set={setHasOuterAccent} />
          </div>

          {/* Veneer colors */}
          <div style={{ padding: "12px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "4px", marginBottom: "12px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: UI.dim, marginBottom: "10px" }}>VENEER COLORS</div>
            {[
              ["Black strips", vBlack, setVBlack],
              ["White strips", vWhite, setVWhite],
              ["Border rows",  vBorder, setVBorder],
            ].map(([l, v, s]) => (
              <div key={l} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "7px" }}>
                <input type="color" value={v} onChange={e => s(e.target.value)}
                  style={{ width: "28px", height: "22px", border: `1px solid ${UI.border}`, borderRadius: "2px", cursor: "pointer", padding: "1px" }} />
                <span style={{ fontSize: "9px", color: UI.dim }}>{l}</span>
              </div>
            ))}

            {/* Accent color with presets */}
            <div style={{ marginTop: "4px" }}>
              <div style={{ fontSize: "9px", color: UI.dim, marginBottom: "5px" }}>Accent / Rung color</div>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap", marginBottom: "6px" }}>
                {ACCENT_PRESETS.map(p => (
                  <div key={p.name}
                    onClick={() => setVAccent(p.fill)}
                    title={p.name}
                    style={{
                      width: "20px", height: "20px", borderRadius: "3px",
                      background: p.fill,
                      border: vAccent === p.fill ? "2px solid #e8c87a" : "1px solid #3a2e1a",
                      cursor: "pointer", flexShrink: 0,
                    }}
                  />
                ))}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <input type="color" value={vAccent} onChange={e => setVAccent(e.target.value)}
                  style={{ width: "28px", height: "22px", border: `1px solid ${UI.border}`, borderRadius: "2px", cursor: "pointer", padding: "1px" }} />
                <span style={{ fontSize: "8px", color: UI.dimmer }}>custom</span>
              </div>
            </div>
          </div>

          {/* Zoom */}
          <div style={{ padding: "12px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "4px", marginBottom: "12px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: UI.dim, marginBottom: "8px" }}>VIEW</div>
            <Knob label="Flat grid zoom" val={zoom} set={setZoom} min={8} max={32} unit=" px/sq" />
            <Knob label="Ring r_in" val={rIn} set={setRIn} min={40} max={180} unit=" px" />
            <Knob label="Ring r_out" val={rOut} set={setROut} min={60} max={200} unit=" px" />
          </div>

          {/* Pattern formula */}
          <div style={{ padding: "10px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "4px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "2px", color: UI.dim, marginBottom: "6px" }}>PATTERN FORMULA</div>
            <div style={{ fontSize: "8px", color: UI.dimmer, lineHeight: "1.8" }}>
              Column seq:<br />
              <span style={{ color: UI.amber }}>({blackWidth}B·{whiteWidth}W) × {numPairs}</span><br />
              = {cols} total cols<br /><br />
              Row seq:<br />
              {hasBorder && <><span style={{ color: UI.amber }}>1 border</span><br /></>}
              {hasOuterAccent && <><span style={{ color: vAccent, filter: "brightness(1.8)" }}>1 accent</span><br /></>}
              {Array.from({ length: numSections }, (_, s) => (
                <span key={s} style={{ color: UI.amber }}>
                  {s > 0 && hasRung ? `1 rung · ` : ""}
                  {sectionRows}×stripe<br />
                </span>
              ))}
              {hasOuterAccent && <><span style={{ color: vAccent, filter: "brightness(1.8)" }}>1 accent</span><br /></>}
              {hasBorder && <><span style={{ color: UI.amber }}>1 border</span><br /></>}
              = {rows} total rows · {mmH}mm
            </div>
          </div>
        </div>

        {/* ── CENTER ── */}
        <div style={{ flex: 1, minWidth: 0 }}>

          {/* DESIGN TAB */}
          {tab === "design" && (
            <div>
              {/* Row type ruler */}
              <div style={{ display: "flex", flexDirection: "column", gap: "0", marginLeft: "2px", marginBottom: "8px" }}>
                {rowTypes.map((type, r) => (
                  <div key={r} style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "1px" }}>
                    <div style={{ width: "60px", fontSize: "7px", color: UI.dimmer, textAlign: "right", flexShrink: 0, lineHeight: `${zoom}px`, height: `${zoom}px` }}>
                      {type === "border" ? "ebony" : type === "accent" ? "accent" : "B/W"}
                    </div>
                  </div>
                ))}
              </div>

              {/* Flat grid with ruler */}
              <div style={{ display: "flex", gap: "8px", alignItems: "flex-start" }}>
                {/* Row type sidebar */}
                <div style={{ flexShrink: 0, paddingTop: "0px" }}>
                  {rowTypes.map((type, r) => {
                    const bg = type === "border" ? vBorder : type === "accent" ? vAccent : "transparent";
                    return (
                      <div key={r} style={{
                        height: `${zoom}px`, width: "48px",
                        display: "flex", alignItems: "center", justifyContent: "flex-end",
                        paddingRight: "6px", fontSize: "7px",
                        color: type === "stripe" ? UI.dimmer : "#fff",
                        background: type === "stripe" ? "transparent" : bg + "40",
                        borderLeft: type !== "stripe" ? `2px solid ${bg}` : `1px solid ${UI.dimmest}`,
                        marginBottom: "0px",
                      }}>
                        {type === "border" ? "BDR" : type === "accent" ? "ACC" : `${((r)*0.5).toFixed(1)}`}
                      </div>
                    );
                  })}
                </div>

                {/* The grid */}
                <FlatGrid grid={grid} veneers={veneers} cellSize={zoom} />

                {/* Column header */}
              </div>

              {/* Col dimension ruler */}
              <div style={{ marginTop: "6px", marginLeft: "56px" }}>
                <div style={{ display: "flex", gap: "0" }}>
                  {Array.from({ length: numPairs }, (_, p) => (
                    <div key={p} style={{ display: "flex" }}>
                      {Array.from({ length: blackWidth }, (_, b) => (
                        <div key={`b${b}`} style={{
                          width: `${zoom}px`, height: "16px",
                          background: vBlack + "60",
                          border: `1px solid ${UI.border}`,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: "7px", color: UI.dimmer, borderRadius: "1px",
                        }}>B</div>
                      ))}
                      {Array.from({ length: whiteWidth }, (_, w) => (
                        <div key={`w${w}`} style={{
                          width: `${zoom}px`, height: "16px",
                          background: vWhite + "60",
                          border: `1px solid ${UI.border}`,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: "7px", color: UI.dimmer, borderRadius: "1px",
                        }}>W</div>
                      ))}
                    </div>
                  ))}
                </div>
                <div style={{ fontSize: "8px", color: UI.dimmer, marginTop: "3px" }}>
                  ← {cols} columns · {mmW}mm total width · one tile repeat →
                </div>
              </div>

              {/* Dimension summary */}
              <div style={{ marginTop: "10px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {[
                  ["Tile width",   `${mmW}mm`],
                  ["Tile height",  `${mmH}mm`],
                  ["Col pitch",    `${((blackWidth+whiteWidth)*0.5).toFixed(1)}mm`],
                  ["B strip",      `${(blackWidth*0.5).toFixed(1)}mm`],
                  ["W strip",      `${(whiteWidth*0.5).toFixed(1)}mm`],
                  ["0.5mm/sq",     "scale"],
                ].map(([k, v]) => (
                  <div key={k} style={{ padding: "3px 8px", background: UI.panel, border: `1px solid ${UI.border2}`, borderRadius: "3px", fontSize: "9px", color: UI.dimmer }}>
                    {k} <span style={{ color: UI.gold, fontWeight: "bold" }}>{v}</span>
                  </div>
                ))}
              </div>

              {/* Construction note */}
              <div style={{ marginTop: "10px", padding: "10px", background: UI.panel, border: `1px solid ${UI.border2}`, borderRadius: "4px" }}>
                <div style={{ fontSize: "9px", letterSpacing: "2px", color: UI.dim, marginBottom: "6px" }}>CONSTRUCTION METHOD</div>
                <div style={{ fontSize: "9px", color: UI.dimmer, lineHeight: "1.9" }}>
                  <span style={{ color: UI.amber }}>1.</span> Glue veneer strips face-to-face in column sequence: ({blackWidth}B·{whiteWidth}W)×{numPairs} — produces a "book" {mmW}mm wide.<br />
                  <span style={{ color: UI.amber }}>2.</span> Slice the book crosswise into {mmH}mm tall slices. Each slice = one tile.<br />
                  <span style={{ color: UI.amber }}>3.</span> Stack tiles vertically adding accent/border rows between sections.<br />
                  <span style={{ color: UI.amber }}>4.</span> Glue stack into a rod. The cross-section = your grid above.<br />
                  <span style={{ color: UI.amber }}>5.</span> Slice the rod thin (~{(mmH).valueOf()}mm slices) — each slice fits the rosette channel.<br />
                  <span style={{ color: UI.amber }}>6.</span> Bend or arrange slices around the soundhole ring. Tiles repeat continuously.
                </div>
              </div>
            </div>
          )}

          {/* PREVIEW TAB */}
          {tab === "preview" && (
            <div>
              <div style={{ fontSize: "9px", color: UI.dimmer, marginBottom: "12px", letterSpacing: "2px" }}>
                ROSETTE RING PREVIEW · Tiles mapped to annulus · r_in={rIn}px r_out={rOut}px
              </div>
              <RosetteCanvas
                grid={grid} veneers={veneers}
                rIn={rIn} rOut={rOut}
                canvasSize={canvasSz}
              />
              <div style={{ marginTop: "10px", padding: "8px 10px", background: UI.panel, border: `1px solid ${UI.border2}`, borderRadius: "3px", fontSize: "9px", color: UI.dimmer, lineHeight: "1.7" }}>
                Radial direction (r_in → r_out) maps to <span style={{ color: UI.amber }}>rows top→bottom</span>.<br />
                Angular direction maps to <span style={{ color: UI.amber }}>columns tiling continuously</span> around the ring.<br />
                Adjust r_in/r_out sliders to match your soundhole diameter and ring channel width.
              </div>
            </div>
          )}

          {/* BOM TAB */}
          {tab === "bom" && (
            <div>
              <div style={{ fontSize: "9px", color: UI.dimmer, marginBottom: "10px", letterSpacing: "2px" }}>
                VENEER BILL OF MATERIALS · {rows} rows × {cols} cols
              </div>

              {/* Unique row types */}
              <div style={{ marginBottom: "14px" }}>
                <div style={{ fontSize: "9px", color: UI.dim, marginBottom: "6px", letterSpacing: "2px" }}>UNIQUE ROW STACKS</div>
                {uniqueRows.map(ur => (
                  <div key={ur.id} style={{ padding: "8px 10px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "3px", marginBottom: "6px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                      <span style={{ fontSize: "10px", color: UI.amber }}>{ur.label}</span>
                      <span style={{ fontSize: "10px", color: UI.gold, fontWeight: "bold" }}>×{ur.count}</span>
                    </div>
                    <div style={{ fontSize: "9px", color: UI.dimmer }}>{ur.colSeq}</div>
                  </div>
                ))}
              </div>

              {/* Row-by-row detail */}
              <div style={{ fontSize: "9px", color: UI.dim, marginBottom: "6px", letterSpacing: "2px" }}>ROW-BY-ROW DETAIL</div>
              <div style={{ maxHeight: "340px", overflowY: "auto", border: `1px solid ${UI.border}`, borderRadius: "3px" }}>
                {grid.map((row, r) => {
                  // Run-length encode
                  const parts = [];
                  let cur = row[0], run = 1;
                  for (let c = 1; c < cols; c++) {
                    if (row[c] === cur) run++;
                    else { parts.push({ v: cur, n: run }); cur = row[c]; run = 1; }
                  }
                  parts.push({ v: cur, n: run });
                  const label = ["B", "W", "A", "BDR"];
                  const fillC = [vBlack, vWhite, vAccent, vBorder];
                  const textC = (v) => v === 1 ? "#1a1008" : v === 2 ? "#ffffff" : "#c9a96e";
                  const rType = rowTypes[r];
                  return (
                    <div key={r} style={{
                      display: "flex", alignItems: "center", gap: "6px",
                      padding: "4px 8px",
                      borderBottom: `1px solid ${UI.dimmest}`,
                      background: r % 2 === 0 ? "transparent" : "#0c0903",
                    }}>
                      <span style={{ fontSize: "8px", color: UI.dimmer, width: "22px", flexShrink: 0 }}>{r + 1}</span>
                      <span style={{ fontSize: "7px", color: UI.dimmer, width: "28px", flexShrink: 0 }}>
                        {((r + 1) * 0.5).toFixed(1)}
                      </span>
                      <span style={{
                        fontSize: "7px", width: "30px", flexShrink: 0,
                        color: rType === "border" ? UI.amber : rType === "accent" ? vAccent : UI.dimmer,
                        filter: rType === "accent" ? "brightness(2)" : "none",
                      }}>
                        {rType === "border" ? "BORDER" : rType === "accent" ? "ACCENT" : "STRIPE"}
                      </span>
                      <div style={{ display: "flex", gap: "2px", flexWrap: "wrap", flex: 1 }}>
                        {parts.map((p, i) => (
                          <span key={i} style={{
                            display: "inline-block",
                            padding: "1px 4px", borderRadius: "2px",
                            background: fillC[p.v],
                            border: p.v === 1 ? `1px solid ${UI.border}` : "none",
                            fontSize: "8px", color: textC(p.v), fontWeight: "bold",
                            minWidth: "16px", textAlign: "center",
                          }}>
                            {p.n}{label[p.v]}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Totals */}
              <div style={{ marginTop: "10px", padding: "10px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "3px" }}>
                <div style={{ fontSize: "9px", color: UI.dim, marginBottom: "6px", letterSpacing: "2px" }}>TOTAL VENEER COUNT</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "5px" }}>
                  {[
                    ["Black strips", counts[0], vBlack],
                    ["White strips", counts[1], vWhite],
                    ["Accent strips", counts[2], vAccent],
                    ["Border strips", counts[3], vBorder],
                    ["Total cells", counts[0]+counts[1]+counts[2]+counts[3], null],
                    ["Grid", `${cols}×${rows}`, null],
                  ].map(([k, v, col]) => (
                    <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "3px 6px", background: UI.bg, borderRadius: "2px", border: `1px solid ${UI.border2}` }}>
                      <span style={{ fontSize: "9px", color: UI.dimmer }}>{k}</span>
                      <span style={{ fontSize: "10px", fontWeight: "bold", color: col ? (col === vWhite ? "#c9b890" : UI.gold) : UI.gold }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: MINI PREVIEW ── */}
        <div style={{ width: "200px", flexShrink: 0 }}>

          {/* Mini rosette preview always visible */}
          <div style={{ marginBottom: "12px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "2px", color: UI.dim, marginBottom: "8px" }}>ROSETTE PREVIEW</div>
            <RosetteCanvas
              grid={grid} veneers={veneers}
              rIn={rIn * 0.44} rOut={rOut * 0.44}
              canvasSize={190}
            />
          </div>

          {/* Pattern snapshot */}
          <div style={{ marginBottom: "12px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "2px", color: UI.dim, marginBottom: "6px" }}>TILE SNAPSHOT</div>
            <div style={{ display: "inline-block", border: `1px solid ${UI.border}`, borderRadius: "2px", overflow: "hidden" }}>
              {grid.map((row, r) => (
                <div key={r} style={{ display: "flex" }}>
                  {row.map((v, c) => (
                    <div key={c} style={{
                      width: "5px", height: "5px",
                      background: [vBlack, vWhite, vAccent, vBorder][v],
                    }} />
                  ))}
                </div>
              ))}
            </div>
            <div style={{ fontSize: "8px", color: UI.dimmer, marginTop: "3px" }}>{cols}×{rows} · 5px/sq</div>
          </div>

          {/* Quick stats */}
          <div style={{ padding: "10px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "4px", marginBottom: "10px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "2px", color: UI.dim, marginBottom: "8px" }}>DIMENSIONS</div>
            {[
              ["Width", `${mmW} mm`],
              ["Height", `${mmH} mm`],
              ["Cols", cols],
              ["Rows", rows],
              ["Sections", numSections],
              ["Rungs", hasRung ? numSections - 1 : 0],
              ["Border rows", hasBorder ? 2 : 0],
              ["Accent rows", (hasOuterAccent ? 2 : 0) + (hasRung ? Math.max(0, numSections - 1) : 0)],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "2px 0", borderBottom: `1px solid ${UI.dimmest}` }}>
                <span style={{ fontSize: "9px", color: UI.dimmer }}>{k}</span>
                <span style={{ fontSize: "10px", color: UI.text, fontWeight: "bold" }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Classical guitar reference */}
          <div style={{ padding: "10px", background: UI.panel, border: `1px solid ${UI.border}`, borderRadius: "4px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "2px", color: UI.dim, marginBottom: "6px" }}>REFERENCE</div>
            <div style={{ fontSize: "8px", color: UI.dimmer, lineHeight: "1.8" }}>
              <span style={{ color: UI.amber }}>Soundhole:</span> ~87mm (r=43.5)<br />
              <span style={{ color: UI.amber }}>Rosette ring:</span> 5–8mm wide<br />
              <span style={{ color: UI.amber }}>Typical tile:</span> 6–8mm tall<br />
              <span style={{ color: UI.amber }}>Strip width:</span> 0.5–1.5mm<br />
              <span style={{ color: UI.amber }}>Veneer thick:</span> 0.5–1mm<br /><br />
              Current tile is {mmH}mm tall —<br />
              {parseFloat(mmH) >= 5 && parseFloat(mmH) <= 9
                ? <span style={{ color: UI.green }}>✓ within standard range</span>
                : <span style={{ color: "#c0392b" }}>⚠ outside 5–9mm range</span>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
