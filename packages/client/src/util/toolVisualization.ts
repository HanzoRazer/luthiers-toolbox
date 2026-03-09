/**
 * Tool Visualization Module
 *
 * Draws a 2D representation of the current CNC tool on the canvas:
 * circle for the cutter diameter, center dot, optional spindle indicator.
 */

export interface ToolDef {
  id: number;
  name: string;
  type: "endmill" | "ballnose" | "drill" | "facemill";
  diameter: number; // mm
  color: string;
}

const DEFAULT_TOOL: ToolDef = {
  id: 0,
  name: "Default Endmill",
  type: "endmill",
  diameter: 6,
  color: "#888888",
};

export class ToolVisualizer {
  private tools = new Map<number, ToolDef>();
  private current: ToolDef;

  constructor(tools?: ToolDef[]) {
    if (tools) tools.forEach((t) => this.tools.set(t.id, t));
    this.current = this.tools.get(0) ?? DEFAULT_TOOL;
  }

  setTool(id: number): void {
    this.current = this.tools.get(id) ?? this.current;
  }

  addTool(t: ToolDef): void {
    this.tools.set(t.id, t);
  }

  /**
   * Draw the tool at the given canvas pixel position.
   * @param scale  viewport pixels-per-mm so we can size the cutter circle
   */
  draw(
    ctx: CanvasRenderingContext2D,
    canvasX: number,
    canvasY: number,
    scale: number,
    isCutting: boolean,
    spindleOn: boolean,
  ): void {
    const radiusPx = Math.max(3, (this.current.diameter / 2) * scale);

    // Cutter envelope circle
    ctx.beginPath();
    ctx.arc(canvasX, canvasY, radiusPx, 0, Math.PI * 2);
    ctx.strokeStyle = isCutting ? "#ffaa00" : "#555";
    ctx.lineWidth = isCutting ? 2 : 1;
    ctx.setLineDash(isCutting ? [] : [3, 3]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Centre dot
    ctx.beginPath();
    ctx.arc(canvasX, canvasY, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#E74C3C";
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Spindle rotation indicator (small arc)
    if (spindleOn && radiusPx > 8) {
      ctx.beginPath();
      ctx.arc(canvasX, canvasY, radiusPx + 4, 0, Math.PI * 1.4);
      ctx.strokeStyle = "rgba(255,200,0,0.45)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }

  get currentTool(): ToolDef {
    return this.current;
  }
}
