import { useState, useCallback, useRef, useEffect } from "react";

// ─── PALETTE ─────────────────────────────────────────────────────
const COLORS = {
  0: { fill:"#1a1008", label:"Black", code:"B" },
  1: { fill:"#f5efe0", label:"White", code:"W" },
  2: { fill:"#3b5bdb", label:"Blue",  code:"L" },
  3: { fill:"#c0392b", label:"Red",   code:"R" },
};

const UI = {
  bg:"#0e0b07", panel:"#0a0805", border:"#2a1e0a", border2:"#1e1508",
  gold:"#e8c87a", dim:"#7a5c2e", dimmer:"#4a3010", dimmest:"#2a1e0a",
  text:"#c9a96e", blue:"#6b82db", red:"#e05545",
};

// ─── CELTIC TILE LIBRARY ─────────────────────────────────────────
const CELTIC_TILES = {
  simple4: {
    label:"Simple 4×4 Knot",
    desc:"Basic interlace — toy example from paper",
    grid:[
      [0,1,1,0],
      [1,1,1,1],
      [1,1,1,1],
      [0,1,1,0],
    ],
  },
  square8: {
    label:"Square Interlace 8×8",
    desc:"Single-band square knot, repeatable",
    grid:[
      [0,0,1,1,1,1,0,0],
      [0,1,1,0,0,1,1,0],
      [1,1,0,0,0,0,1,1],
      [1,0,0,1,1,0,0,1],
      [1,0,0,1,1,0,0,1],
      [1,1,0,0,0,0,1,1],
      [0,1,1,0,0,1,1,0],
      [0,0,1,1,1,1,0,0],
    ],
  },
  braid8: {
    label:"3-Strand Braid 8×8",
    desc:"Vertical braid with over/under accents",
    grid:[
      [1,1,0,1,1,0,1,1],
      [1,0,0,1,0,0,1,0],
      [0,0,1,0,0,1,0,0],
      [0,1,1,0,1,1,0,1],
      [1,1,0,1,1,0,1,1],
      [1,0,0,1,0,0,1,0],
      [0,0,1,0,0,1,0,0],
      [0,1,1,0,1,1,0,1],
    ],
  },
  step12: {
    label:"Step / Key Pattern 12×12",
    desc:"Greek-key derived step pattern",
    grid:[
      [0,0,0,0,0,0,0,0,0,0,0,0],
      [0,1,1,1,1,1,1,1,1,1,1,0],
      [0,1,0,0,0,0,0,0,0,0,1,0],
      [0,1,0,1,1,1,1,1,1,0,1,0],
      [0,1,0,1,0,0,0,0,1,0,1,0],
      [0,1,0,1,0,1,1,0,1,0,1,0],
      [0,1,0,1,0,1,1,0,1,0,1,0],
      [0,1,0,1,0,0,0,0,1,0,1,0],
      [0,1,0,1,1,1,1,1,1,0,1,0],
      [0,1,0,0,0,0,0,0,0,0,1,0],
      [0,1,1,1,1,1,1,1,1,1,1,0],
      [0,0,0,0,0,0,0,0,0,0,0,0],
    ],
  },
  tricolor12: {
    label:"Tri-color Weave 12×12",
    desc:"Over/under strands with accent color",
    grid:[
      [0,0,1,0,0,1,0,0,1,0,0,1],
      [0,1,1,0,1,1,0,1,1,0,1,1],
      [1,1,0,1,1,2,1,1,0,1,1,2],
      [1,0,0,1,0,0,1,0,0,1,0,0],
      [0,0,1,0,0,1,0,0,1,0,0,1],
      [0,1,1,0,1,1,0,1,1,0,1,1],
      [1,1,2,1,1,0,1,1,2,1,1,0],
      [1,0,0,1,0,0,1,0,0,1,0,0],
      [0,0,1,0,0,1,0,0,1,0,0,1],
      [0,1,1,0,1,1,0,1,1,0,1,1],
      [1,1,0,1,1,2,1,1,0,1,1,2],
      [1,0,0,1,0,0,1,0,0,1,0,0],
    ],
  },
  rosette16: {
    label:"Rosette Border 16×16",
    desc:"Full rosette tile — classic interlace ring",
    grid:[
      [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
      [0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0],
      [0,0,1,1,0,0,1,1,1,1,0,0,1,1,0,0],
      [0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0],
      [1,1,0,0,1,1,0,0,0,0,1,1,0,0,1,1],
      [1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1],
      [1,0,1,1,0,0,1,1,1,1,0,0,1,1,0,1],
      [1,1,1,0,0,1,1,0,0,1,1,0,0,1,1,1],
      [1,1,1,0,0,1,1,0,0,1,1,0,0,1,1,1],
      [1,0,1,1,0,0,1,1,1,1,0,0,1,1,0,1],
      [1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1],
      [1,1,0,0,1,1,0,0,0,0,1,1,0,0,1,1],
      [0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0],
      [0,0,1,1,0,0,1,1,1,1,0,0,1,1,0,0],
      [0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0],
      [0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0],
    ],
  },
};

// ─── HELPERS ─────────────────────────────────────────────────────
function countRow(grid,row,cols){const c={0:0,1:0,2:0,3:0};for(let i=0;i<cols;i++)c[grid[row]?.[i]??0]++;return c;}
function countTotals(grid,rows,cols){const t={0:0,1:0,2:0,3:0};for(let r=0;r<rows;r++){const rc=countRow(grid,r,cols);Object.keys(t).forEach(k=>t[k]+=rc[k]);}return t;}
function mirrorPoints(r,c,rows,cols,mode){const pts=[[r,c]];if(mode==="H"||mode==="4")pts.push([r,cols-1-c]);if(mode==="V"||mode==="4")pts.push([rows-1-r,c]);if(mode==="4")pts.push([rows-1-r,cols-1-c]);return[...new Map(pts.map(p=>[p.join(","),p])).values()];}

// ─── PARAMETRIC GENERATOR ─────────────────────────────────────────
function generateParametric(N, threshold, mode) {
  return Array.from({length:N},(_,i)=>
    Array.from({length:N},(_,j)=>{
      const si = Math.abs(Math.sin(2*Math.PI*i/N));
      const cj = Math.abs(Math.cos(2*Math.PI*j/N));
      const val = si + cj;
      if(mode==="sine")   return val > threshold ? 1 : 0;
      if(mode==="braid"){
        // Diagonal braid: phase offset
        const s = Math.abs(Math.sin(2*Math.PI*(i+j*0.5)/N));
        const c2= Math.abs(Math.cos(2*Math.PI*(j+i*0.5)/N));
        return (s+c2) > threshold ? 1 : 0;
      }
      if(mode==="diamond"){
        const d=Math.abs(Math.sin(2*Math.PI*(i-j)/N))+Math.abs(Math.sin(2*Math.PI*(i+j)/N));
        return d > threshold ? 1 : 0;
      }
      return 0;
    })
  );
}

// ─── WEAVE CANVAS ────────────────────────────────────────────────
function WeaveCanvas({grid,cellSize=20,showDiamond,showWeave,colors}){
  const canvasRef=useRef(null);
  const rows=grid.length, cols=grid[0]?.length??0;

  useEffect(()=>{
    const canvas=canvasRef.current; if(!canvas)return;
    const W=cols*cellSize, H=rows*cellSize;
    canvas.width=W; canvas.height=H;
    const ctx=canvas.getContext("2d");
    ctx.fillStyle=UI.bg; ctx.fillRect(0,0,W,H);

    // Draw cells
    for(let r=0;r<rows;r++){
      for(let c=0;c<cols;c++){
        const v=grid[r]?.[c]??0;
        const fillC=colors?.[v]??COLORS[v]?.fill??"#1a1008";
        ctx.fillStyle=fillC;
        ctx.fillRect(c*cellSize,r*cellSize,cellSize,cellSize);
        ctx.strokeStyle="rgba(90,60,20,0.2)";
        ctx.lineWidth=0.5;
        ctx.strokeRect(c*cellSize,r*cellSize,cellSize,cellSize);
      }
    }

    // Diamond grid overlay
    if(showDiamond){
      ctx.strokeStyle="rgba(200,160,50,0.25)";
      ctx.lineWidth=0.7;
      ctx.setLineDash([2,3]);
      for(let r=0;r<=rows;r++){
        for(let c=0;c<=cols;c++){
          // NE diagonals
          if(r<rows&&c<cols){
            ctx.beginPath();
            ctx.moveTo(c*cellSize, r*cellSize+cellSize/2);
            ctx.lineTo(c*cellSize+cellSize/2, r*cellSize);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(c*cellSize+cellSize/2, r*cellSize+cellSize);
            ctx.lineTo(c*cellSize+cellSize, r*cellSize+cellSize/2);
            ctx.stroke();
          }
        }
      }
      ctx.setLineDash([]);
    }

    // Weave over/under dots
    if(showWeave){
      for(let r=0;r<rows;r++){
        for(let c=0;c<cols;c++){
          const v=grid[r]?.[c]??0;
          if(v===1){
            // Check neighbours: over dot at crossings
            const above=grid[r-1]?.[c]??0;
            const left =grid[r]?.[c-1]??0;
            if(above===1&&left===1){
              // Crossing — mark over/under by (r+c) parity
              const isOver=(r+c)%2===0;
              ctx.fillStyle=isOver?"rgba(255,220,100,0.7)":"rgba(0,0,0,0.5)";
              ctx.beginPath();
              ctx.arc(c*cellSize+cellSize/2,r*cellSize+cellSize/2,cellSize*0.18,0,Math.PI*2);
              ctx.fill();
            }
          }
        }
      }
    }
  },[grid,cellSize,showDiamond,showWeave,colors]);

  return(
    <canvas ref={canvasRef}
      style={{border:`1px solid ${UI.border}`,borderRadius:"3px",display:"block",maxWidth:"100%",imageRendering:"pixelated"}}
    />
  );
}

// ─── CELTIC PANEL ────────────────────────────────────────────────
function CelticPanel(){
  const [tileKey,  setTileKey]   = useState("square8");
  const [grid,     setGrid]      = useState(()=>CELTIC_TILES.square8.grid.map(r=>[...r]));
  const [paintCol, setPaintCol]  = useState(1);
  const [symmetry, setSymmetry]  = useState("4");
  const [isPaint,  setIsPaint]   = useState(false);
  const [zoom,     setZoom]      = useState(24);
  const [showDia,  setShowDia]   = useState(true);
  const [showWeave,setShowWeave] = useState(true);
  const [tab,      setTab]       = useState("edit");    // edit | gen | preview

  // Generator state
  const [genN,     setGenN]      = useState(12);
  const [genThr,   setGenThr]    = useState(0.7);
  const [genMode,  setGenMode]   = useState("sine");

  // Color overrides
  const [c0fill,   setC0fill]    = useState(COLORS[0].fill);
  const [c1fill,   setC1fill]    = useState(COLORS[1].fill);
  const [c2fill,   setC2fill]    = useState(COLORS[2].fill);
  const colors={0:c0fill,1:c1fill,2:c2fill,3:COLORS[3].fill};

  const lastPainted=useRef(null);
  const rows=grid.length, cols=grid[0]?.length??0;

  const loadTile=(key)=>{
    setTileKey(key);
    setGrid(CELTIC_TILES[key].grid.map(r=>[...r]));
  };

  const applyGenerated=()=>{
    const g=generateParametric(genN,genThr,genMode);
    setGrid(g);
    setTileKey("custom");
  };

  const paint=useCallback((r,c)=>{
    const key=`${r},${c}`;
    if(lastPainted.current===key)return;
    lastPainted.current=key;
    setGrid(prev=>{
      const next=prev.map(row=>[...row]);
      mirrorPoints(r,c,rows,cols,symmetry).forEach(([pr,pc])=>{next[pr][pc]=paintCol;});
      return next;
    });
  },[paintCol,symmetry,rows,cols]);

  const handleMouseUp=()=>{setIsPaint(false);lastPainted.current=null;};
  const totals=countTotals(grid,rows,cols);

  // Build BOM string per row
  const bomRows=grid.map((row,r)=>{
    const rc=countRow(grid,r,cols);
    const parts=[];
    let cur=row[0], run=1;
    for(let c=1;c<cols;c++){
      if(row[c]===cur){run++;}
      else{parts.push({v:cur,n:run});cur=row[c];run=1;}
    }
    parts.push({v:cur,n:run});
    return{r,rc,parts};
  });

  const subTab=(label,val)=>(
    <div onClick={()=>setTab(val)} style={{
      padding:"4px 10px",cursor:"pointer",fontSize:"10px",letterSpacing:"1px",
      border:tab===val?"1px solid #c9a96e":"1px solid #2a1e0a",borderRadius:"3px",
      background:tab===val?"#1e1508":"transparent",color:tab===val?UI.gold:UI.dim,
      transition:"all .12s",
    }}>{label}</div>
  );

  return(
    <div onMouseUp={handleMouseUp}>

      {/* Sub-tabs */}
      <div style={{display:"flex",gap:"4px",marginBottom:"14px"}}>
        {subTab("Grid Editor","edit")}
        {subTab("Parametric Generator","gen")}
        {subTab("Weave Preview","preview")}
        {subTab("Veneer BOM","bom")}
      </div>

      <div style={{display:"flex",gap:"16px",flexWrap:"wrap"}}>

        {/* ── LEFT: Tile Library + Tools ── */}
        <div style={{width:"175px",flexShrink:0}}>

          {/* Tile library */}
          <div style={{marginBottom:"12px"}}>
            <div style={{fontSize:"9px",letterSpacing:"3px",color:UI.dim,marginBottom:"6px"}}>TILE LIBRARY</div>
            {Object.entries(CELTIC_TILES).map(([k,t])=>{
              const s=t.grid.length;
              return(
                <div key={k} onClick={()=>loadTile(k)} style={{
                  padding:"5px 7px",marginBottom:"3px",cursor:"pointer",
                  border:(tileKey===k&&tab!=="gen")?"1px solid #c9a96e":"1px solid #2a1e0a",
                  borderRadius:"3px",background:(tileKey===k&&tab!=="gen")?"#1e1508":"transparent",
                  transition:"all .12s",
                }}>
                  <div style={{fontSize:"10px",color:(tileKey===k&&tab!=="gen")?UI.gold:UI.dim}}>{t.label}</div>
                  <div style={{fontSize:"8px",color:UI.dimmer,marginTop:"1px"}}>{s}×{s} · {t.desc}</div>
                </div>
              );
            })}
          </div>

          {/* Paint */}
          <div style={{marginBottom:"12px"}}>
            <div style={{fontSize:"9px",letterSpacing:"3px",color:UI.dim,marginBottom:"5px"}}>PAINT</div>
            {[0,1,2].map(c=>(
              <div key={c} onClick={()=>setPaintCol(c)} style={{
                display:"flex",alignItems:"center",gap:"7px",
                padding:"4px 7px",marginBottom:"3px",cursor:"pointer",
                border:paintCol===c?"1px solid #c9a96e":"1px solid #2a1e0a",
                borderRadius:"3px",background:paintCol===c?"#1e1508":"transparent",
              }}>
                <div style={{width:"12px",height:"12px",borderRadius:"2px",background:colors[c],border:c===1?"1px solid #4a3820":"none",flexShrink:0}}/>
                <span style={{fontSize:"10px",color:paintCol===c?UI.gold:UI.dim}}>{COLORS[c].label}</span>
              </div>
            ))}
          </div>

          {/* Symmetry */}
          <div style={{marginBottom:"12px"}}>
            <div style={{fontSize:"9px",letterSpacing:"3px",color:UI.dim,marginBottom:"5px"}}>SYMMETRY</div>
            {[["None","N"],["Horiz","H"],["Vert","V"],["4-Way","4"]].map(([l,v])=>(
              <div key={v} onClick={()=>setSymmetry(v)} style={{
                padding:"4px 7px",marginBottom:"3px",cursor:"pointer",fontSize:"10px",
                border:symmetry===v?"1px solid #c9a96e":"1px solid #2a1e0a",
                borderRadius:"3px",background:symmetry===v?"#1e1508":"transparent",
                color:symmetry===v?UI.gold:UI.dim,
              }}>{l}</div>
            ))}
          </div>

          {/* Zoom */}
          <div style={{marginBottom:"12px"}}>
            <div style={{fontSize:"9px",letterSpacing:"3px",color:UI.dim,marginBottom:"4px"}}>ZOOM</div>
            <input type="range" min="10" max="40" value={zoom} onChange={e=>setZoom(Number(e.target.value))} style={{width:"100%",accentColor:"#c9a96e"}}/>
            <div style={{fontSize:"9px",color:UI.dimmer,textAlign:"center"}}>{zoom}px/sq</div>
          </div>

          {/* Overlays */}
          <div style={{marginBottom:"12px"}}>
            <div style={{fontSize:"9px",letterSpacing:"3px",color:UI.dim,marginBottom:"5px"}}>OVERLAYS</div>
            {[[showDia,setShowDia,"Diamond grid"],[showWeave,setShowWeave,"Weave dots"]].map(([val,set,lbl])=>(
              <div key={lbl} onClick={()=>set(!val)} style={{
                padding:"4px 7px",marginBottom:"3px",cursor:"pointer",fontSize:"10px",
                border:val?"1px solid #c9a96e":"1px solid #2a1e0a",
                borderRadius:"3px",background:val?"#1e1508":"transparent",
                color:val?UI.gold:UI.dim,
              }}>{lbl}</div>
            ))}
          </div>

          {/* Veneer colors */}
          <div style={{marginBottom:"12px"}}>
            <div style={{fontSize:"9px",letterSpacing:"3px",color:UI.dim,marginBottom:"6px"}}>VENEER COLORS</div>
            {[[0,c0fill,setC0fill,"Background"],[1,c1fill,setC1fill,"Strand"],[2,c2fill,setC2fill,"Accent"]].map(([idx,val,set,lbl])=>(
              <div key={idx} style={{display:"flex",alignItems:"center",gap:"7px",marginBottom:"5px"}}>
                <input type="color" value={val} onChange={e=>set(e.target.value)}
                  style={{width:"24px",height:"20px",border:`1px solid ${UI.border}`,borderRadius:"2px",background:"none",cursor:"pointer",padding:"1px"}}/>
                <span style={{fontSize:"9px",color:UI.dim}}>{lbl}</span>
              </div>
            ))}
          </div>

          {/* Actions */}
          <div style={{marginBottom:"12px"}}>
            <div style={{fontSize:"9px",letterSpacing:"3px",color:UI.dim,marginBottom:"5px"}}>ACTIONS</div>
            {[
              ["↺ Restore",()=>tileKey!=="custom"&&loadTile(tileKey)],
              ["✕ Clear",()=>setGrid(Array(rows).fill(null).map(()=>Array(cols).fill(0)))],
              ["⊞ Invert",()=>setGrid(prev=>prev.map(r=>r.map(v=>v===0?1:v===1?0:v)))],
            ].map(([l,fn])=>(
              <div key={l} onClick={fn} style={{padding:"4px 7px",marginBottom:"3px",cursor:"pointer",fontSize:"10px",color:UI.dim,border:`1px solid ${UI.border}`,borderRadius:"3px"}}>{l}</div>
            ))}
          </div>
        </div>

        {/* ── CENTER ── */}
        <div style={{flex:1,minWidth:0}}>

          {/* EDIT TAB */}
          {tab==="edit"&&(
            <div>
              <div style={{fontSize:"9px",color:UI.dimmer,marginBottom:"8px",letterSpacing:"2px"}}>
                GRID EDITOR · {cols}×{rows} · {(cols*.5).toFixed(1)}×{(rows*.5).toFixed(1)}mm @ 0.5mm/sq
              </div>
              <div style={{display:"inline-block",border:`1px solid ${UI.border}`,cursor:"crosshair"}}>
                {grid.map((row,r)=>(
                  <div key={r} style={{display:"flex"}}>
                    {Array(cols).fill(null).map((_,c)=>(
                      <div key={c}
                        onMouseDown={()=>{setIsPaint(true);paint(r,c);}}
                        onMouseEnter={()=>{if(isPaint)paint(r,c);}}
                        style={{
                          width:`${zoom}px`,height:`${zoom}px`,
                          background:colors[row[c]??0],
                          boxSizing:"border-box",
                          border:"0.5px solid rgba(90,60,20,.2)",
                          transition:"background .05s",position:"relative",
                        }}
                      />
                    ))}
                  </div>
                ))}
              </div>
              <div style={{marginTop:"8px",fontSize:"9px",color:UI.dimmer}}>
                Matrix K[{rows}×{cols}] · {totals[0]} background · {totals[1]} strand{totals[2]>0?` · ${totals[2]} accent`:""}
              </div>
            </div>
          )}

          {/* GENERATOR TAB */}
          {tab==="gen"&&(
            <div>
              <div style={{fontSize:"9px",color:UI.dimmer,marginBottom:"12px",letterSpacing:"2px"}}>PARAMETRIC STRAND GENERATOR</div>

              <div style={{padding:"12px",background:UI.panel,border:`1px solid ${UI.border}`,borderRadius:"4px",marginBottom:"12px"}}>
                <div style={{fontSize:"9px",color:UI.dimmer,marginBottom:"8px"}}>Formula: K[i,j] = 1 if |sin(2π·i/N)| + |cos(2π·j/N)| &gt; threshold</div>

                {/* Mode */}
                <div style={{marginBottom:"10px"}}>
                  <div style={{fontSize:"9px",color:UI.dim,marginBottom:"5px",letterSpacing:"2px"}}>STRAND MODE</div>
                  <div style={{display:"flex",gap:"4px",flexWrap:"wrap"}}>
                    {[["sine","Sine bands"],["braid","Diagonal braid"],["diamond","Diamond weave"]].map(([v,l])=>(
                      <div key={v} onClick={()=>setGenMode(v)} style={{
                        padding:"4px 10px",cursor:"pointer",fontSize:"10px",
                        border:genMode===v?"1px solid #c9a96e":"1px solid #2a1e0a",
                        borderRadius:"3px",background:genMode===v?"#1e1508":"transparent",
                        color:genMode===v?UI.gold:UI.dim,
                      }}>{l}</div>
                    ))}
                  </div>
                </div>

                {/* N */}
                <div style={{marginBottom:"10px"}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:"3px"}}>
                    <span style={{fontSize:"9px",color:UI.dim,letterSpacing:"1px"}}>N — Grid size</span>
                    <span style={{fontSize:"10px",color:UI.gold}}>{genN}×{genN}</span>
                  </div>
                  <input type="range" min="4" max="24" step="2" value={genN} onChange={e=>setGenN(Number(e.target.value))} style={{width:"100%",accentColor:"#c9a96e"}}/>
                </div>

                {/* Threshold */}
                <div style={{marginBottom:"12px"}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:"3px"}}>
                    <span style={{fontSize:"9px",color:UI.dim,letterSpacing:"1px"}}>Threshold</span>
                    <span style={{fontSize:"10px",color:UI.gold}}>{genThr.toFixed(2)}</span>
                  </div>
                  <input type="range" min="0.1" max="1.9" step="0.05" value={genThr} onChange={e=>setGenThr(Number(e.target.value))} style={{width:"100%",accentColor:"#c9a96e"}}/>
                  <div style={{fontSize:"8px",color:UI.dimmer,marginTop:"2px"}}>Low = dense weave · High = sparse strands</div>
                </div>

                <div onClick={applyGenerated} style={{
                  padding:"8px",textAlign:"center",cursor:"pointer",
                  border:"1px solid #c9a96e",borderRadius:"3px",
                  background:"#1e1508",color:UI.gold,fontSize:"11px",letterSpacing:"1px",
                }}>
                  ⟳ Generate → Load into Editor
                </div>
              </div>

              {/* Live preview of generation */}
              <div style={{fontSize:"9px",color:UI.dimmer,marginBottom:"6px"}}>PREVIEW ({genN}×{genN})</div>
              <div style={{display:"inline-block",border:`1px solid ${UI.border}`}}>
                {generateParametric(genN,genThr,genMode).map((row,r)=>(
                  <div key={r} style={{display:"flex"}}>
                    {row.map((v,c)=>(
                      <div key={c} style={{
                        width:"16px",height:"16px",
                        background:colors[v],
                        borderRight:"0.5px solid rgba(90,60,20,.15)",
                        borderBottom:"0.5px solid rgba(90,60,20,.15)",
                      }}/>
                    ))}
                  </div>
                ))}
              </div>

              <div style={{marginTop:"10px",padding:"8px",background:UI.panel,border:`1px solid ${UI.border2}`,borderRadius:"3px",fontSize:"9px",color:UI.dimmer,lineHeight:"1.7"}}>
                <span style={{color:UI.dim}}>Note: </span>
                Parametric grids give a starting skeleton. Traditional Celtic knots
                are hand-refined on graph paper — load into the editor above, then
                paint over/under crossings and clean strand continuity.
              </div>
            </div>
          )}

          {/* PREVIEW TAB */}
          {tab==="preview"&&(
            <div>
              <div style={{fontSize:"9px",color:UI.dimmer,marginBottom:"10px",letterSpacing:"2px"}}>
                WEAVE PREVIEW · Diamond grid overlay · Over/under crossing dots
              </div>
              <WeaveCanvas
                grid={grid}
                cellSize={Math.max(18,Math.min(zoom,32))}
                showDiamond={showDia}
                showWeave={showWeave}
                colors={colors}
              />
              <div style={{marginTop:"10px",padding:"8px",background:UI.panel,border:`1px solid ${UI.border2}`,borderRadius:"3px",fontSize:"9px",color:UI.dimmer,lineHeight:"1.7"}}>
                <span style={{color:UI.gold}}>◉</span> Gold dots = over-strand crossings (parity (r+c) even).<br/>
                <span style={{color:"rgba(80,80,80,0.9)"}}>●</span> Dark dots = under-strand crossings.<br/>
                Dashed gold lines = diamond grid construction guide.
              </div>
            </div>
          )}

          {/* BOM TAB */}
          {tab==="bom"&&(
            <div>
              <div style={{fontSize:"9px",color:UI.dimmer,marginBottom:"10px",letterSpacing:"2px"}}>VENEER BILL OF MATERIALS · ROW-BY-ROW STACK</div>
              <div style={{fontFamily:"'Courier New',monospace",fontSize:"9px"}}>
                <div style={{display:"flex",gap:"8px",padding:"4px 0",borderBottom:`1px solid ${UI.border}`,marginBottom:"4px"}}>
                  <span style={{width:"32px",color:UI.dimmer}}>ROW</span>
                  <span style={{width:"50px",color:UI.dimmer}}>mm</span>
                  <span style={{flex:1,color:UI.dimmer}}>STACK SEQUENCE</span>
                  <span style={{width:"40px",color:UI.dimmer,textAlign:"right"}}>0s</span>
                  <span style={{width:"40px",color:UI.dimmer,textAlign:"right"}}>1s</span>
                  {totals[2]>0&&<span style={{width:"40px",color:UI.dimmer,textAlign:"right"}}>2s</span>}
                </div>
                {bomRows.map(({r,rc,parts})=>(
                  <div key={r} style={{display:"flex",gap:"8px",padding:"3px 0",borderBottom:`1px solid #120d04`,alignItems:"center"}}>
                    <span style={{width:"32px",color:UI.dimmer}}>{r+1}</span>
                    <span style={{width:"50px",color:UI.dimmer}}>{((r+1)*.5).toFixed(1)}</span>
                    <span style={{flex:1,display:"flex",gap:"2px",flexWrap:"wrap"}}>
                      {parts.map((p,i)=>(
                        <span key={i} style={{
                          display:"inline-block",
                          padding:"1px 4px",borderRadius:"2px",
                          background:colors[p.v],
                          border:p.v===1?"1px solid #4a3820":"none",
                          fontSize:"8px",
                          color:p.v===0?"#7a6a5a":p.v===1?"#1a1008":p.v===2?"#f0f0f0":"#fff",
                          fontWeight:"bold",minWidth:"14px",textAlign:"center",
                        }}>
                          {p.n}{["B","W","A"][p.v]}
                        </span>
                      ))}
                    </span>
                    <span style={{width:"40px",color:"#7a6a5a",textAlign:"right"}}>{rc[0]}</span>
                    <span style={{width:"40px",color:"#c9b890",textAlign:"right"}}>{rc[1]}</span>
                    {totals[2]>0&&<span style={{width:"40px",color:UI.blue,textAlign:"right"}}>{rc[2]||"·"}</span>}
                  </div>
                ))}
                <div style={{display:"flex",gap:"8px",padding:"5px 0",borderTop:`1px solid ${UI.border}`,marginTop:"4px"}}>
                  <span style={{width:"32px",color:UI.dim,fontSize:"8px",letterSpacing:"1px"}}>TOT</span>
                  <span style={{width:"50px"}}/>
                  <span style={{flex:1}}/>
                  <span style={{width:"40px",color:"#9a7a5a",textAlign:"right",fontWeight:"bold",fontSize:"12px"}}>{totals[0]}</span>
                  <span style={{width:"40px",color:UI.gold,textAlign:"right",fontWeight:"bold",fontSize:"12px"}}>{totals[1]}</span>
                  {totals[2]>0&&<span style={{width:"40px",color:UI.blue,textAlign:"right",fontWeight:"bold",fontSize:"12px"}}>{totals[2]}</span>}
                </div>
              </div>
              <div style={{marginTop:"10px",padding:"8px",background:UI.panel,border:`1px solid ${UI.border2}`,borderRadius:"3px",fontSize:"9px",color:UI.dimmer,lineHeight:"1.7"}}>
                <span style={{color:UI.dim}}>Build order: </span>
                Glue veneer strips face-to-face in each row's sequence → clamp → slice thin crosswise →
                reassemble slices as columns → clamp again → final slice = one rosette tile thickness.
                B = background wood, W = strand wood, A = accent veneer.
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: Stats ── */}
        <div style={{width:"195px",flexShrink:0}}>
          <div style={{fontSize:"9px",letterSpacing:"3px",color:UI.dim,marginBottom:"6px"}}>MATRIX K[{rows}×{cols}]</div>

          <div style={{padding:"8px",background:UI.panel,border:`1px solid ${UI.border}`,borderRadius:"3px",marginBottom:"10px"}}>
            {[["Rows",rows],["Cols",cols],["Width",`${(cols*.5).toFixed(1)} mm`],["Height",`${(rows*.5).toFixed(1)} mm`],["Scale","0.5mm/sq"],["Background",totals[0]],["Strand",totals[1]],["Accent",totals[2]]].map(([k,v])=>(
              <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"2px 0",borderBottom:`1px solid ${UI.dimmest}`}}>
                <span style={{fontSize:"9px",color:UI.dimmer}}>{k}</span>
                <span style={{fontSize:"10px",color:UI.text,fontWeight:"bold"}}>{v}</span>
              </div>
            ))}
          </div>

          {/* Pixel count table */}
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"5px"}}>COUNT PER ROW</div>
          <div style={{maxHeight:"300px",overflowY:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:"9px"}}>
              <thead>
                <tr>
                  <td style={{padding:"2px 3px",color:UI.dimmer,fontSize:"8px"}}>R</td>
                  <td style={{padding:"2px 3px",textAlign:"center"}}><div style={{width:"9px",height:"9px",background:COLORS[0].fill,margin:"0 auto",borderRadius:"1px"}}/></td>
                  <td style={{padding:"2px 3px",textAlign:"center"}}><div style={{width:"9px",height:"9px",background:COLORS[1].fill,border:"1px solid #4a3820",margin:"0 auto",borderRadius:"1px"}}/></td>
                  {totals[2]>0&&<td style={{padding:"2px 3px",textAlign:"center"}}><div style={{width:"9px",height:"9px",background:COLORS[2].fill,margin:"0 auto",borderRadius:"1px"}}/></td>}
                </tr>
              </thead>
              <tbody>
                {grid.map((_,r)=>{
                  const rc=countRow(grid,r,cols);
                  return(
                    <tr key={r} style={{borderTop:"1px solid #120d04"}}>
                      <td style={{padding:"1px 3px",color:UI.dimmer,fontSize:"8px"}}>{r+1}</td>
                      <td style={{padding:"1px 3px",textAlign:"center",color:rc[0]>0?"#7a6a5a":"#1a1008",fontWeight:rc[0]>0?"bold":"normal"}}>{rc[0]>0?rc[0]:"·"}</td>
                      <td style={{padding:"1px 3px",textAlign:"center",color:rc[1]>0?"#c9b890":"#1a1008",fontWeight:rc[1]>0?"bold":"normal"}}>{rc[1]>0?rc[1]:"·"}</td>
                      {totals[2]>0&&<td style={{padding:"1px 3px",textAlign:"center",color:rc[2]>0?UI.blue:"#1a1008",fontWeight:rc[2]>0?"bold":"normal"}}>{rc[2]>0?rc[2]:"·"}</td>}
                    </tr>
                  );
                })}
                <tr style={{borderTop:`1px solid ${UI.border}`}}>
                  <td style={{padding:"2px 3px",color:UI.dim,fontSize:"8px"}}>∑</td>
                  <td style={{padding:"2px 3px",textAlign:"center",color:"#9a7a5a",fontWeight:"bold"}}>{totals[0]}</td>
                  <td style={{padding:"2px 3px",textAlign:"center",color:UI.gold,fontWeight:"bold"}}>{totals[1]}</td>
                  {totals[2]>0&&<td style={{padding:"2px 3px",textAlign:"center",color:UI.blue,fontWeight:"bold"}}>{totals[2]}</td>}
                </tr>
              </tbody>
            </table>
          </div>

          {/* Construction note */}
          <div style={{marginTop:"10px",padding:"8px",background:UI.panel,border:`1px solid ${UI.border2}`,borderRadius:"3px",fontSize:"8px",color:UI.dimmer,lineHeight:"1.7"}}>
            <span style={{color:UI.dim,letterSpacing:"1px"}}>RULES</span><br/>
            1. Diamond grid on graph paper.<br/>
            2. Strands follow diagonals.<br/>
            3. Alternate over/under at crossings.<br/>
            4. Rasterize → pixel matrix.<br/>
            5. Count per row → glue veneer stack.<br/>
            6. Slice thin → reassemble columns.<br/>
            7. Slice again → rosette tiles.
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── GRID PRESETS (Spanish / Rope / Wave) ────────────────────────
const PRESETS = {
  spanish:{
    name:"Spanish Right-Angle",subtitle:"Classical · Tile Section",
    cols:23,rows:15,colors:[0,1,2],
    colWidths:[1,1,2,3,4,5,6,7,8,9,9,8,7,6,5,4,3,2,1,1],
    bom:[{label:"Strip A",items:"12 Black · 4 White"},{label:"Strip B",items:"14 Black · 6 White"}],
    note:"Build as a long rod billet, sliced crosswise into tiles. 23×15 sq @ 0.5mm = 11.5×7.5mm.",
    grid:[
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
    ],
  },
  rope:{
    name:"Rope Rosette",subtitle:"Diagonal Staircase",
    cols:7,rows:5,colors:[0,1],
    colWidths:[1,2,2,1,3,4,5,4,3],
    bom:[{label:"Total Black",items:"23 strips"},{label:"Total White",items:"12 strips"}],
    note:"Diagonal staircase creates rope illusion. Mirror alternate tiles for full twist effect.",
    grid:[[0,0,0,0,0,1,1],[0,0,0,0,1,1,0],[0,0,0,1,1,0,0],[0,0,1,1,0,0,1],[0,1,1,0,0,1,0]],
  },
  wave:{
    name:"Wave Tile",subtitle:"Wave Motif · Red Accent",
    cols:9,rows:8,colors:[0,1,3],
    colWidths:[1,2,3,4,5,6,7,8],
    bom:[{label:"White",items:"→ count table"},{label:"Black",items:"→ count table"},{label:"Red",items:"→ count table"}],
    note:"⚠ Rows 6–8 reconstructed from partial photo. Verify against source video before cutting.",
    grid:[[0,0,0,0,0,0,1,1,3],[0,0,0,0,0,1,1,3,3],[0,0,0,0,1,1,3,3,0],[0,0,0,1,1,3,3,0,0],[0,0,1,1,0,0,0,0,0],[0,1,1,0,0,0,0,0,0],[1,1,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,3,3]],
  },
};

// ─── HERRINGBONE CANVAS ──────────────────────────────────────────
function HerringboneCanvas({theta,w,h,rIn,rOut,toothColors,showAnnulus,showGrid,canvasSize=420}){
  const canvasRef=useRef(null);
  useEffect(()=>{
    const canvas=canvasRef.current;if(!canvas)return;
    const size=canvasSize;canvas.width=size;canvas.height=size;
    const ctx=canvas.getContext("2d");
    const cx=size/2,cy=size/2;
    ctx.fillStyle=UI.bg;ctx.fillRect(0,0,size,size);
    const rad=theta*Math.PI/180;
    const ax=2*w,bx=w,by=2*h;
    const R=Math.max(rOut*1.5+w*4,size*.8);
    const steps=Math.ceil(R/Math.min(w,h))+6;
    ctx.save();ctx.beginPath();ctx.rect(0,0,size,size);ctx.clip();
    for(let i=-steps;i<=steps;i++){
      for(let j=-steps;j<=steps;j++){
        const px=cx+i*ax+j*bx,py=cy+j*by;
        const dist=Math.sqrt((px-cx)**2+(py-cy)**2);
        if(showAnnulus&&(dist>rOut+Math.max(w,h)||dist<rIn-Math.max(w,h)))continue;
        const tAngle=(i+j)%2===0?rad:-rad;
        const cos=Math.cos(tAngle),sin=Math.sin(tAngle);
        const corners=[[w/2,h/2],[w/2,-h/2],[-w/2,-h/2],[-w/2,h/2]];
        const pts=corners.map(([lx,ly])=>[px+lx*cos-ly*sin,py+lx*sin+ly*cos]);
        const anyIn=pts.some(([x,y])=>{const d=Math.sqrt((x-cx)**2+(y-cy)**2);return!showAnnulus||( d>=rIn&&d<=rOut);});
        if(showAnnulus&&!anyIn)continue;
        const fillColor=toothColors[(i+j)%2===0?0:1];
        if(showAnnulus){ctx.save();ctx.beginPath();ctx.arc(cx,cy,rOut,0,Math.PI*2);ctx.arc(cx,cy,rIn,0,Math.PI*2,true);ctx.clip("evenodd");}
        ctx.beginPath();ctx.moveTo(pts[0][0],pts[0][1]);for(let k=1;k<pts.length;k++)ctx.lineTo(pts[k][0],pts[k][1]);ctx.closePath();
        ctx.fillStyle=fillColor;ctx.fill();
        ctx.strokeStyle="rgba(90,60,20,.35)";ctx.lineWidth=.7;ctx.stroke();
        if(showAnnulus)ctx.restore();
      }
    }
    if(showAnnulus){
      ctx.strokeStyle="rgba(200,160,50,.5)";ctx.lineWidth=1;ctx.setLineDash([4,4]);
      ctx.beginPath();ctx.arc(cx,cy,rOut,0,Math.PI*2);ctx.stroke();
      ctx.beginPath();ctx.arc(cx,cy,rIn,0,Math.PI*2);ctx.stroke();
      ctx.setLineDash([]);
    }
    if(showGrid){ctx.strokeStyle="rgba(200,160,50,.12)";ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(cx,0);ctx.lineTo(cx,size);ctx.stroke();ctx.beginPath();ctx.moveTo(0,cy);ctx.lineTo(size,cy);ctx.stroke();}
    ctx.restore();
  },[theta,w,h,rIn,rOut,toothColors,showAnnulus,showGrid,canvasSize]);
  return(<canvas ref={canvasRef} style={{borderRadius:"4px",border:`1px solid ${UI.border}`,display:"block",maxWidth:"100%"}}/>);
}

function HerringbonePanel(){
  const[theta,setTheta]=useState(45);const[w,setW]=useState(14);const[h,setH]=useState(28);
  const[rIn,setRIn]=useState(80);const[rOut,setROut]=useState(130);
  const[showAnn,setShowAnn]=useState(true);const[showGrid,setShowGrid]=useState(true);
  const[tooth0,setTooth0]=useState("#1a1008");const[tooth1,setTooth1]=useState("#f5efe0");
  const knob=(label,val,set,min,max,step=1,unit="")=>(
    <div style={{marginBottom:"10px"}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:"2px"}}>
        <span style={{fontSize:"9px",letterSpacing:"1px",color:UI.dim}}>{label}</span>
        <span style={{fontSize:"10px",color:UI.gold}}>{val}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={val} onChange={e=>set(Number(e.target.value))} style={{width:"100%",accentColor:"#c9a96e"}}/>
    </div>
  );
  return(
    <div style={{display:"flex",gap:"16px",flexWrap:"wrap"}}>
      <div style={{width:"185px",flexShrink:0}}>
        <div style={{padding:"10px",background:UI.panel,border:`1px solid ${UI.border}`,borderRadius:"4px",marginBottom:"10px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"8px"}}>TOOTH GEOMETRY</div>
          {knob("θ — Rotation",theta,setTheta,0,90,1,"°")}
          {knob("w — Width",w,setW,4,40,1," px")}
          {knob("h — Height",h,setH,8,80,2," px")}
          <div style={{fontSize:"8px",color:UI.dimmer}}>h/w = {(h/w).toFixed(2)} {Math.abs(h/w-2)<.05?"✓ 2:1":""}</div>
        </div>
        <div style={{padding:"10px",background:UI.panel,border:`1px solid ${UI.border}`,borderRadius:"4px",marginBottom:"10px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"8px"}}>ANNULUS</div>
          {knob("r_in",rIn,setRIn,10,200,2," px")}
          {knob("r_out",rOut,setROut,20,220,2," px")}
          <div style={{fontSize:"8px",color:UI.dimmer}}>Width: {rOut-rIn} px</div>
        </div>
        <div style={{padding:"10px",background:UI.panel,border:`1px solid ${UI.border}`,borderRadius:"4px",marginBottom:"10px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"8px"}}>TOOTH COLORS</div>
          {[["Even",tooth0,setTooth0],["Odd",tooth1,setTooth1]].map(([l,v,s])=>(
            <div key={l} style={{display:"flex",alignItems:"center",gap:"7px",marginBottom:"6px"}}>
              <input type="color" value={v} onChange={e=>s(e.target.value)} style={{width:"26px",height:"22px",border:`1px solid ${UI.border}`,borderRadius:"2px",cursor:"pointer",padding:"1px"}}/>
              <span style={{fontSize:"10px",color:UI.dim}}>{l} tiles</span>
            </div>
          ))}
        </div>
        <div style={{padding:"10px",background:UI.panel,border:`1px solid ${UI.border}`,borderRadius:"4px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"6px"}}>DISPLAY</div>
          {[[showAnn,setShowAnn,"Annulus ring"],[showGrid,setShowGrid,"Center grid"]].map(([v,s,l])=>(
            <div key={l} onClick={()=>s(!v)} style={{padding:"4px 7px",marginBottom:"3px",cursor:"pointer",fontSize:"10px",border:v?"1px solid #c9a96e":"1px solid #2a1e0a",borderRadius:"3px",background:v?"#1e1508":"transparent",color:v?UI.gold:UI.dim}}>{l}</div>
          ))}
        </div>
      </div>
      <div style={{flex:1,minWidth:0}}>
        <HerringboneCanvas theta={theta} w={w} h={h} rIn={rIn} rOut={rOut} toothColors={[tooth0,tooth1]} showAnnulus={showAnn} showGrid={showGrid} canvasSize={420}/>
        <div style={{marginTop:"10px",padding:"10px",background:UI.panel,border:`1px solid ${UI.border}`,borderRadius:"4px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"8px"}}>LIVE FORMULA</div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"4px"}}>
            {[["θ",`${theta}°`],["cos θ",Math.cos(theta*Math.PI/180).toFixed(3)],["sin θ",Math.sin(theta*Math.PI/180).toFixed(3)],["w×h",`${w}×${h}`],["a"   ,`(${2*w}, 0)`],["b"   ,`(${w}, ${2*h})`],["r_in",`${rIn}px`],["r_out",`${rOut}px`],["ring",`${rOut-rIn}px`],["h/w",`${(h/w).toFixed(2)}`]].map(([k,v])=>(
              <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"3px 6px",background:UI.bg,borderRadius:"2px",border:`1px solid ${UI.border2}`}}>
                <span style={{fontSize:"9px",color:UI.dimmer}}>{k}</span>
                <span style={{fontSize:"10px",color:UI.gold,fontWeight:"bold"}}>{v}</span>
              </div>
            ))}
          </div>
          <div style={{marginTop:"8px",fontSize:"9px",color:UI.dimmer,lineHeight:"1.8"}}>
            p(i,j) = i·<span style={{color:UI.gold}}>({2*w},0)</span> + j·<span style={{color:UI.gold}}>({w},{2*h})</span><br/>
            X(i,j) = R(<span style={{color:UI.gold}}>{theta}°</span>)·C + p(i,j)<br/>
            Keep if <span style={{color:UI.gold}}>{rIn}</span> ≤ |p| ≤ <span style={{color:UI.gold}}>{rOut}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── GRID EDITOR (shared for Spanish/Rope/Wave) ──────────────────
function GridEditor({presetKey}){
  const preset=PRESETS[presetKey];const{cols,rows}=preset;
  const[grid,setGrid]=useState(()=>preset.grid.map(r=>[...r]));
  const[paintColor,setPaintColor]=useState(preset.colors[0]);
  const[symmetry,setSymmetry]=useState("4");
  const[isPainting,setIsPainting]=useState(false);
  const[zoom,setZoom]=useState(presetKey==="spanish"?20:28);
  const[showMM,setShowMM]=useState(true);
  const lastPainted=useRef(null);
  useEffect(()=>{setGrid(PRESETS[presetKey].grid.map(r=>[...r]));setPaintColor(PRESETS[presetKey].colors[0]);setZoom(presetKey==="spanish"?20:28);},[presetKey]);
  const paint=useCallback((r,c)=>{const key=`${r},${c}`;if(lastPainted.current===key)return;lastPainted.current=key;setGrid(prev=>{const next=prev.map(row=>[...row]);mirrorPoints(r,c,rows,cols,symmetry).forEach(([pr,pc])=>{next[pr][pc]=paintColor;});return next;});},[paintColor,symmetry,rows,cols]);
  const handleMouseUp=()=>{setIsPainting(false);lastPainted.current=null;};
  const totals=countTotals(grid,rows,cols);const ac=preset.colors;
  return(
    <div onMouseUp={handleMouseUp} style={{display:"flex",gap:"16px",flexWrap:"wrap"}}>
      <div style={{width:"150px",flexShrink:0}}>
        <div style={{marginBottom:"12px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"5px"}}>MATERIAL</div>
          {ac.map(c=>(<div key={c} onClick={()=>setPaintColor(c)} style={{display:"flex",alignItems:"center",gap:"7px",padding:"4px 7px",marginBottom:"3px",cursor:"pointer",border:paintColor===c?"1px solid #c9a96e":"1px solid #2a1e0a",borderRadius:"3px",background:paintColor===c?"#1e1508":"transparent"}}><div style={{width:"12px",height:"12px",borderRadius:"2px",background:COLORS[c].fill,border:c===1?"1px solid #4a3820":"none",flexShrink:0}}/><span style={{fontSize:"10px",color:paintColor===c?UI.gold:UI.dim}}>{COLORS[c].label}</span></div>))}
        </div>
        <div style={{marginBottom:"12px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"5px"}}>SYMMETRY</div>
          {[["None","N"],["Horiz","H"],["Vert","V"],["4-Way","4"]].map(([l,v])=>(<div key={v} onClick={()=>setSymmetry(v)} style={{padding:"3px 7px",marginBottom:"3px",cursor:"pointer",fontSize:"10px",border:symmetry===v?"1px solid #c9a96e":"1px solid #2a1e0a",borderRadius:"3px",background:symmetry===v?"#1e1508":"transparent",color:symmetry===v?UI.gold:UI.dim}}>{l}</div>))}
        </div>
        <div style={{marginBottom:"12px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"4px"}}>ZOOM</div>
          <input type="range" min="10" max="40" value={zoom} onChange={e=>setZoom(Number(e.target.value))} style={{width:"100%",accentColor:"#c9a96e"}}/>
          <div style={{fontSize:"9px",color:UI.dimmer,textAlign:"center"}}>{zoom}px/sq</div>
        </div>
        <div style={{marginBottom:"12px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"4px"}}>DISPLAY</div>
          <div onClick={()=>setShowMM(!showMM)} style={{padding:"3px 7px",cursor:"pointer",fontSize:"10px",border:showMM?"1px solid #c9a96e":"1px solid #2a1e0a",borderRadius:"3px",background:showMM?"#1e1508":"transparent",color:showMM?UI.gold:UI.dim}}>mm labels</div>
        </div>
        <div style={{marginBottom:"12px"}}>
          <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"4px"}}>ACTIONS</div>
          {[["↺ Restore",()=>setGrid(preset.grid.map(r=>[...r]))],["✕ Clear",()=>setGrid(Array(rows).fill(null).map(()=>Array(cols).fill(0)))]].map(([l,fn])=>(<div key={l} onClick={fn} style={{padding:"3px 7px",marginBottom:"3px",cursor:"pointer",fontSize:"10px",color:UI.dim,border:`1px solid ${UI.border}`,borderRadius:"3px"}}>{l}</div>))}
        </div>
      </div>
      <div style={{flex:1,minWidth:0}}>
        {showMM&&(<div style={{display:"flex",marginBottom:"2px",marginLeft:"22px"}}>{Array(cols).fill(null).map((_,c)=>(<div key={c} style={{width:`${zoom}px`,textAlign:"center",fontSize:"7px",color:UI.dimmest,overflow:"hidden"}}>{c+1}</div>))}</div>)}
        <div style={{display:"flex",gap:"4px"}}>
          {showMM&&(<div style={{width:"18px",flexShrink:0}}>{Array(rows).fill(null).map((_,r)=>(<div key={r} style={{height:`${zoom}px`,display:"flex",alignItems:"center",justifyContent:"flex-end",paddingRight:"2px",fontSize:"7px",color:UI.dimmest}}>{((r+1)*.5).toFixed(1)}</div>))}</div>)}
          <div style={{display:"inline-block",border:`1px solid ${UI.border}`,cursor:"crosshair"}}>
            {grid.map((row,r)=>(<div key={r} style={{display:"flex"}}>{Array(cols).fill(null).map((_,c)=>(<div key={c} onMouseDown={()=>{setIsPainting(true);paint(r,c);}} onMouseEnter={()=>{if(isPainting)paint(r,c);}} style={{width:`${zoom}px`,height:`${zoom}px`,background:COLORS[row[c]??0].fill,boxSizing:"border-box",border:"0.5px solid rgba(90,60,20,.2)",transition:"background .05s"}}/>))}</div>))}
          </div>
        </div>
        <div style={{marginTop:"7px",marginLeft:showMM?"22px":"0"}}>
          <div style={{fontSize:"7px",color:UI.dimmest,marginBottom:"3px"}}>COL WIDTHS (½mm)</div>
          <div style={{display:"flex",gap:"2px",flexWrap:"wrap"}}>{preset.colWidths.map((w,i)=>(<div key={i} style={{width:`${zoom}px`,height:"13px",background:"#150f05",border:`1px solid ${UI.border}`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:"7px",color:UI.text,borderRadius:"2px"}}>{w}</div>))}</div>
        </div>
        <div style={{marginTop:"7px",display:"flex",gap:"5px",flexWrap:"wrap"}}>
          {[[`W:${cols}sq`,`${(cols*.5).toFixed(1)}mm`],[`H:${rows}sq`,`${(rows*.5).toFixed(1)}mm`],["0.5mm/sq","scale"]].map(([a,b])=>(<div key={a} style={{padding:"2px 6px",background:UI.panel,border:`1px solid ${UI.border2}`,borderRadius:"3px",fontSize:"9px",color:UI.dimmer}}>{a} <span style={{color:UI.text}}>{b}</span></div>))}
        </div>
        <div style={{marginTop:"7px",padding:"7px",background:UI.panel,border:`1px solid ${UI.border2}`,borderRadius:"3px",fontSize:"9px",color:UI.dimmer,lineHeight:"1.6"}}>{preset.note}</div>
      </div>
      <div style={{width:"185px",flexShrink:0}}>
        <div style={{fontSize:"9px",letterSpacing:"2px",color:UI.dim,marginBottom:"5px"}}>COUNT TABLE</div>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:"9px"}}>
          <thead><tr><td style={{padding:"2px 3px",color:UI.dimmer,fontSize:"8px"}}>ROW</td>{ac.map(c=>(<td key={c} style={{padding:"2px 3px",textAlign:"center"}}><div style={{width:"9px",height:"9px",borderRadius:"2px",background:COLORS[c].fill,border:c===1?"1px solid #4a3820":"none",margin:"0 auto"}}/></td>))}</tr></thead>
          <tbody>
            {grid.map((_,r)=>{const rc=countRow(grid,r,cols);return(<tr key={r} style={{borderTop:"1px solid #120d04"}}><td style={{padding:"1px 3px",color:UI.dimmer,fontSize:"7px"}}>{((r+1)*.5).toFixed(1)}</td>{ac.map(c=>(<td key={c} style={{padding:"1px 3px",textAlign:"center",color:rc[c]>0?(c===2?UI.blue:c===3?UI.red:c===1?"#c9b890":"#7a6a5a"):"#1a1008",fontWeight:rc[c]>0?"bold":"normal"}}>{rc[c]>0?rc[c]:"·"}</td>))}</tr>);}}
            <tr style={{borderTop:`1px solid ${UI.border}`}}><td style={{padding:"2px 3px",color:UI.dim,fontSize:"8px"}}>∑</td>{ac.map(c=>(<td key={c} style={{padding:"2px 3px",textAlign:"center",fontWeight:"bold",fontSize:"11px",color:c===2?UI.blue:c===3?UI.red:c===1?UI.gold:"#9a7a5a"}}>{totals[c]}</td>))}</tr>
          </tbody>
        </table>
        <div style={{marginTop:"10px",padding:"8px",background:UI.panel,border:`1px solid ${UI.border2}`,borderRadius:"3px"}}>
          <div style={{fontSize:"8px",color:UI.dimmer,marginBottom:"5px",letterSpacing:"1px"}}>BOM</div>
          {preset.bom.map((b,i)=>(<div key={i} style={{marginBottom:i<preset.bom.length-1?"5px":0}}><div style={{fontSize:"8px",color:UI.dimmer}}>{b.label}</div><div style={{fontSize:"10px",color:UI.text}}>{b.items}</div></div>))}
        </div>
      </div>
    </div>
  );
}

// ─── ROOT ────────────────────────────────────────────────────────
export default function RosetteGridDesigner(){
  const[tab,setTab]=useState("spanish");
  const tabs=[["spanish","Spanish"],["rope","Rope"],["wave","Wave"],["herringbone","Herringbone ✦"],["celtic","Celtic Knot ✦"]];
  return(
    <div style={{minHeight:"100vh",background:UI.bg,fontFamily:"'Courier New',monospace",color:UI.text,padding:"20px",userSelect:"none"}}>
      <div style={{borderBottom:`1px solid ${UI.border2}`,paddingBottom:"10px",marginBottom:"14px"}}>
        <div style={{fontSize:"9px",letterSpacing:"4px",color:UI.dimmer,textTransform:"uppercase"}}>The Production Shop · Custom Inlay Module</div>
        <div style={{fontSize:"20px",fontWeight:"bold",color:UI.gold,letterSpacing:"2px",marginTop:"2px"}}>Rosette Tile Grid Designer</div>
        <div style={{fontSize:"10px",color:UI.dimmest,marginTop:"2px"}}>
          {tab==="herringbone"?"Herringbone · Geometric Lattice · Canvas Preview":tab==="celtic"?"Celtic Knot · Interlace Matrix · Weave Editor":PRESETS[tab]?.name+" · "+PRESETS[tab]?.subtitle}
        </div>
      </div>
      <div style={{display:"flex",gap:"4px",marginBottom:"16px",flexWrap:"wrap"}}>
        {tabs.map(([k,l])=>(<div key={k} onClick={()=>setTab(k)} style={{padding:"5px 12px",cursor:"pointer",fontSize:"10px",letterSpacing:"1px",border:tab===k?"1px solid #c9a96e":"1px solid #2a1e0a",borderRadius:"3px",background:tab===k?"#1e1508":"#0a0805",color:tab===k?UI.gold:UI.dim,transition:"all .14s"}}>{l}</div>))}
      </div>
      {tab==="celtic"     && <CelticPanel/>}
      {tab==="herringbone"&& <HerringbonePanel/>}
      {(tab==="spanish"||tab==="rope"||tab==="wave") && <GridEditor key={tab} presetKey={tab}/>}
    </div>
  );
}
