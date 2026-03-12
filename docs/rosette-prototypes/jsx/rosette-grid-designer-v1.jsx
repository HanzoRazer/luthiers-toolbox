import { useState, useCallback, useRef } from "react";

// 0=Black, 1=White, 2=Blue
const COLS = 23;
const ROWS = 15;

// Approximate pattern from the luthier's notebook photo
const INITIAL_PATTERN = [
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  [0,0,0,1,1,0,0,0,0,0,1,1,0,1,1,0,0,0,0,0,1,1,0],
  [0,0,1,1,0,0,0,0,0,1,1,0,0,0,1,1,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  [0,1,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,1,0],
  [1,1,0,0,0,1,1,0,0,2,2,0,0,0,2,2,0,0,1,1,0,0,0],
  [0,0,0,1,1,0,0,0,2,2,0,0,0,0,0,2,2,0,0,0,1,1,0],
  [0,0,0,0,0,0,0,2,2,2,1,2,2,2,2,1,2,2,2,0,0,0,0],
  [0,0,0,0,1,0,2,2,1,1,1,1,2,1,1,1,1,2,2,0,1,0,0],
  [0,0,0,0,0,0,0,2,2,2,1,2,2,2,2,1,2,2,2,0,0,0,0],
  [0,0,0,1,1,0,0,0,2,2,0,0,0,0,0,2,2,0,0,0,1,1,0],
  [1,1,0,0,0,1,1,0,0,2,2,0,0,0,2,2,0,0,1,1,0,0,0],
  [0,1,1,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,1,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  [0,0,0,1,1,0,0,0,0,0,1,1,0,1,1,0,0,0,0,0,1,1,0],
];

const COL_WIDTHS = [1,1,2,3,4,5,6,7,8,9,9,8,7,6,5,4,3,2,1,1];

const COLORS = {
  0: { fill: "#1a1008", label: "Black", code: "B" },
  1: { fill: "#f5efe0", label: "White", code: "W" },
  2: { fill: "#3b5bdb", label: "Blue",  code: "L" },
};

const PAINT_COLORS = [0, 1, 2];

function countRow(grid, row) {
  const counts = { 0: 0, 1: 0, 2: 0 };
  for (let c = 0; c < COLS; c++) counts[grid[row][c]]++;
  return counts;
}

function countTotals(grid) {
  const t = { 0: 0, 1: 0, 2: 0 };
  for (let r = 0; r < ROWS; r++) {
    const rc = countRow(grid, r);
    t[0] += rc[0]; t[1] += rc[1]; t[2] += rc[2];
  }
  return t;
}

function mirrorPoint(r, c, mode) {
  const mirrors = [[r, c]];
  if (mode === "H" || mode === "4") mirrors.push([r, COLS - 1 - c]);
  if (mode === "V" || mode === "4") mirrors.push([ROWS - 1 - r, c]);
  if (mode === "4") mirrors.push([ROWS - 1 - r, COLS - 1 - c]);
  return [...new Set(mirrors.map(([a, b]) => `${a},${b}`))].map(s => s.split(",").map(Number));
}

export default function RosetteGridDesigner() {
  const [grid, setGrid] = useState(() => INITIAL_PATTERN.map(r => [...r]));
  const [paintColor, setPaintColor] = useState(0);
  const [symmetry, setSymmetry] = useState("4");
  const [isPainting, setIsPainting] = useState(false);
  const [showMM, setShowMM] = useState(true);
  const [zoom, setZoom] = useState(22);
  const lastPainted = useRef(null);

  const paint = useCallback((r, c) => {
    const key = `${r},${c}`;
    if (lastPainted.current === key) return;
    lastPainted.current = key;
    setGrid(prev => {
      const next = prev.map(row => [...row]);
      const pts = mirrorPoint(r, c, symmetry);
      pts.forEach(([pr, pc]) => { next[pr][pc] = paintColor; });
      return next;
    });
  }, [paintColor, symmetry]);

  const handleMouseDown = (r, c) => { setIsPainting(true); paint(r, c); };
  const handleMouseEnter = (r, c) => { if (isPainting) paint(r, c); };
  const handleMouseUp = () => { setIsPainting(false); lastPainted.current = null; };

  const totals = countTotals(grid);
  const cellSize = zoom;

  return (
    <div
      onMouseUp={handleMouseUp}
      style={{
        minHeight: "100vh",
        background: "#0e0b07",
        fontFamily: "'Courier New', monospace",
        color: "#c9a96e",
        padding: "20px",
        userSelect: "none",
      }}
    >
      {/* Header */}
      <div style={{ borderBottom: "1px solid #3a2e1a", paddingBottom: "12px", marginBottom: "16px" }}>
        <div style={{ fontSize: "11px", letterSpacing: "4px", color: "#7a5c2e", textTransform: "uppercase" }}>
          Classical / Flamenco Guitar
        </div>
        <div style={{ fontSize: "20px", fontWeight: "bold", color: "#e8c87a", letterSpacing: "2px", marginTop: "2px" }}>
          Rosette Tile Grid Designer
        </div>
        <div style={{ fontSize: "10px", color: "#5a4020", marginTop: "4px" }}>
          Spanish Right-Angle Pattern · 0.5mm / square · {COLS}×{ROWS} grid = {(COLS*0.5).toFixed(1)}mm × {(ROWS*0.5).toFixed(1)}mm
        </div>
      </div>

      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
        {/* Left panel: tools */}
        <div style={{ width: "160px", flexShrink: 0 }}>

          {/* Paint Color */}
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: "#7a5c2e", marginBottom: "6px" }}>MATERIAL</div>
            {PAINT_COLORS.map(c => (
              <div
                key={c}
                onClick={() => setPaintColor(c)}
                style={{
                  display: "flex", alignItems: "center", gap: "8px",
                  padding: "6px 8px", marginBottom: "4px",
                  border: paintColor === c ? "1px solid #c9a96e" : "1px solid #2a1e0a",
                  borderRadius: "3px",
                  background: paintColor === c ? "#1e1508" : "transparent",
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
              >
                <div style={{
                  width: "16px", height: "16px", borderRadius: "2px",
                  background: COLORS[c].fill,
                  border: c === 1 ? "1px solid #4a3820" : "none",
                }} />
                <span style={{ fontSize: "11px", color: paintColor === c ? "#e8c87a" : "#7a5c2e" }}>
                  {COLORS[c].label}
                </span>
              </div>
            ))}
          </div>

          {/* Symmetry */}
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: "#7a5c2e", marginBottom: "6px" }}>SYMMETRY</div>
            {[["None","N"],["Horiz","H"],["Vert","V"],["4-Way","4"]].map(([label, val]) => (
              <div
                key={val}
                onClick={() => setSymmetry(val)}
                style={{
                  padding: "5px 8px", marginBottom: "3px",
                  border: symmetry === val ? "1px solid #c9a96e" : "1px solid #2a1e0a",
                  borderRadius: "3px",
                  background: symmetry === val ? "#1e1508" : "transparent",
                  cursor: "pointer", fontSize: "11px",
                  color: symmetry === val ? "#e8c87a" : "#7a5c2e",
                }}
              >
                {label}
              </div>
            ))}
          </div>

          {/* Zoom */}
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: "#7a5c2e", marginBottom: "6px" }}>ZOOM</div>
            <input
              type="range" min="14" max="36" value={zoom}
              onChange={e => setZoom(Number(e.target.value))}
              style={{ width: "100%", accentColor: "#c9a96e" }}
            />
            <div style={{ fontSize: "10px", color: "#5a4020", textAlign: "center" }}>{zoom}px/sq</div>
          </div>

          {/* Options */}
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: "#7a5c2e", marginBottom: "6px" }}>DISPLAY</div>
            <div
              onClick={() => setShowMM(!showMM)}
              style={{
                padding: "5px 8px",
                border: showMM ? "1px solid #c9a96e" : "1px solid #2a1e0a",
                borderRadius: "3px",
                background: showMM ? "#1e1508" : "transparent",
                cursor: "pointer", fontSize: "11px",
                color: showMM ? "#e8c87a" : "#7a5c2e",
              }}
            >
              mm labels
            </div>
          </div>

          {/* Actions */}
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: "#7a5c2e", marginBottom: "6px" }}>ACTIONS</div>
            <div
              onClick={() => setGrid(INITIAL_PATTERN.map(r => [...r]))}
              style={{
                padding: "5px 8px", marginBottom: "3px",
                border: "1px solid #3a2e1a", borderRadius: "3px",
                cursor: "pointer", fontSize: "10px", color: "#9a6c3e",
              }}
            >
              ↺ Restore
            </div>
            <div
              onClick={() => setGrid(Array(ROWS).fill(null).map(() => Array(COLS).fill(0)))}
              style={{
                padding: "5px 8px",
                border: "1px solid #3a2e1a", borderRadius: "3px",
                cursor: "pointer", fontSize: "10px", color: "#9a6c3e",
              }}
            >
              ✕ Clear
            </div>
          </div>
        </div>

        {/* Center: grid + column sequence */}
        <div style={{ flex: 1, minWidth: 0 }}>

          {/* Column axis labels */}
          {showMM && (
            <div style={{ display: "flex", marginBottom: "4px", marginLeft: "28px" }}>
              {Array(COLS).fill(null).map((_, c) => (
                <div key={c} style={{
                  width: `${cellSize}px`, textAlign: "center",
                  fontSize: "8px", color: "#4a3010",
                  overflow: "hidden",
                }}>
                  {c < 10 ? c + 1 : (c === 11 ? "▼" : COLS - c)}
                </div>
              ))}
            </div>
          )}

          {/* Row labels + Grid */}
          <div style={{ display: "flex", gap: "6px" }}>
            {/* Row mm labels */}
            {showMM && (
              <div style={{ width: "22px", flexShrink: 0 }}>
                {Array(ROWS).fill(null).map((_, r) => (
                  <div key={r} style={{
                    height: `${cellSize}px`, display: "flex", alignItems: "center",
                    justifyContent: "flex-end", paddingRight: "4px",
                    fontSize: "8px", color: "#4a3010",
                  }}>
                    {((r + 1) * 0.5).toFixed(1)}
                  </div>
                ))}
              </div>
            )}

            {/* The grid */}
            <div
              style={{
                display: "inline-block",
                border: "1px solid #3a2e1a",
                cursor: "crosshair",
                boxShadow: "0 0 40px rgba(200,160,50,0.08)",
              }}
            >
              {grid.map((row, r) => (
                <div key={r} style={{ display: "flex" }}>
                  {row.map((cell, c) => {
                    const isCenter = (r === Math.floor(ROWS / 2) && c === Math.floor(COLS / 2));
                    return (
                      <div
                        key={c}
                        onMouseDown={() => handleMouseDown(r, c)}
                        onMouseEnter={() => handleMouseEnter(r, c)}
                        style={{
                          width: `${cellSize}px`,
                          height: `${cellSize}px`,
                          background: COLORS[cell].fill,
                          boxSizing: "border-box",
                          border: "0.5px solid rgba(90,60,20,0.25)",
                          position: "relative",
                          transition: "background 0.08s",
                        }}
                      >
                        {isCenter && (
                          <div style={{
                            position: "absolute", inset: 0,
                            border: "1px dashed rgba(200,160,50,0.4)",
                            pointerEvents: "none",
                          }} />
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          {/* Column width sequence */}
          <div style={{ marginTop: "10px", marginLeft: showMM ? "28px" : "0" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: "#7a5c2e", marginBottom: "4px" }}>
              COL WIDTH SEQUENCE (½mm units)
            </div>
            <div style={{ display: "flex", gap: "2px", flexWrap: "wrap" }}>
              {COL_WIDTHS.map((w, i) => (
                <div key={i} style={{
                  width: `${cellSize}px`, height: "18px",
                  background: "#1e1508",
                  border: "1px solid #3a2e1a",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "8px", color: "#c9a96e",
                  borderRadius: "2px",
                }}>
                  {w}
                </div>
              ))}
              {/* center marker */}
              <div style={{ width: "2px", alignSelf: "center", height: "14px", background: "#c9a96e30", margin: "0 2px" }} />
            </div>
            <div style={{ fontSize: "9px", color: "#4a3010", marginTop: "3px" }}>
              1 1 2 3 4 5 6 7 8 9 ← axis → 9 8 7 6 5 4 3 2 1 1
            </div>
          </div>
        </div>

        {/* Right panel: stats */}
        <div style={{ width: "220px", flexShrink: 0 }}>
          <div style={{ fontSize: "9px", letterSpacing: "3px", color: "#7a5c2e", marginBottom: "8px" }}>
            MATERIAL COUNT TABLE
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
            <thead>
              <tr>
                <td style={{ padding: "4px 6px", color: "#5a4020", fontSize: "9px" }}>ROW</td>
                {[0, 1, 2].map(c => (
                  <td key={c} style={{ padding: "4px 6px", textAlign: "center" }}>
                    <div style={{
                      width: "12px", height: "12px", borderRadius: "2px",
                      background: COLORS[c].fill,
                      border: c === 1 ? "1px solid #4a3820" : "none",
                      margin: "0 auto",
                    }} />
                  </td>
                ))}
              </tr>
            </thead>
            <tbody>
              {grid.map((_, r) => {
                const rc = countRow(grid, r);
                return (
                  <tr key={r} style={{ borderTop: "1px solid #1a1208" }}>
                    <td style={{ padding: "3px 6px", color: "#5a4020", fontSize: "9px" }}>
                      {((r + 1) * 0.5).toFixed(1)}
                    </td>
                    {[0, 1, 2].map(c => (
                      <td key={c} style={{
                        padding: "3px 6px", textAlign: "center",
                        color: rc[c] > 0 ? (c === 2 ? "#6b82db" : c === 1 ? "#c9b890" : "#6a5a4a") : "#2a1e0a",
                        fontWeight: rc[c] > 0 ? "bold" : "normal",
                      }}>
                        {rc[c] > 0 ? rc[c] : "·"}
                      </td>
                    ))}
                  </tr>
                );
              })}
              {/* Totals */}
              <tr style={{ borderTop: "1px solid #3a2e1a" }}>
                <td style={{ padding: "4px 6px", color: "#7a5c2e", fontSize: "9px", letterSpacing: "1px" }}>
                  TOT
                </td>
                {[0, 1, 2].map(c => (
                  <td key={c} style={{
                    padding: "4px 6px", textAlign: "center",
                    color: c === 2 ? "#6b82db" : c === 1 ? "#e8c87a" : "#9a7a5a",
                    fontWeight: "bold", fontSize: "12px",
                  }}>
                    {totals[c]}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>

          {/* Strip BOM */}
          <div style={{ marginTop: "16px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: "#7a5c2e", marginBottom: "6px" }}>
              STRIP BILL OF MATERIALS
            </div>
            <div style={{ background: "#0e0b07", border: "1px solid #2a1e0a", borderRadius: "3px", padding: "8px" }}>
              <div style={{ fontSize: "10px", color: "#7a5c2e", marginBottom: "4px" }}>Strip A</div>
              <div style={{ fontSize: "11px", color: "#c9a96e" }}>12 Black · 4 White</div>
              <div style={{ fontSize: "10px", color: "#7a5c2e", marginTop: "6px", marginBottom: "4px" }}>Strip B</div>
              <div style={{ fontSize: "11px", color: "#c9a96e" }}>14 Black · 6 White</div>
            </div>
          </div>

          {/* Dimensions */}
          <div style={{ marginTop: "16px" }}>
            <div style={{ fontSize: "9px", letterSpacing: "3px", color: "#7a5c2e", marginBottom: "6px" }}>
              TILE DIMENSIONS
            </div>
            <div style={{ background: "#0e0b07", border: "1px solid #2a1e0a", borderRadius: "3px", padding: "8px" }}>
              <div style={{ fontSize: "10px", color: "#9a7a5a" }}>Each square = 0.5mm</div>
              <div style={{ fontSize: "11px", color: "#e8c87a", marginTop: "4px" }}>
                W: {COLS} sq = <strong>{(COLS * 0.5).toFixed(1)}mm</strong>
              </div>
              <div style={{ fontSize: "11px", color: "#e8c87a", marginTop: "2px" }}>
                H: {ROWS} sq = <strong>{(ROWS * 0.5).toFixed(1)}mm</strong>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div style={{ marginTop: "16px", fontSize: "9px", color: "#3a2e1a", lineHeight: "1.6" }}>
            <div>Click or drag to paint.</div>
            <div>4-Way mirrors all quadrants.</div>
            <div>Design is cut as a rod, then</div>
            <div>sliced into rosette tiles.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
