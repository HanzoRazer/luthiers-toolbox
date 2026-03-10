/**
 * toolpathTools — P6 Multi-Tool Visualization Support
 *
 * Utilities for color-coding and visualizing multiple tools in toolpath:
 * - Tool color palette (distinct colors for each tool number)
 * - Tool change markers
 * - Tool legend generation
 */

// ---------------------------------------------------------------------------
// Tool Color Palette
// ---------------------------------------------------------------------------

/**
 * Distinct colors for tool visualization (max 12 tools before cycling).
 * Colors chosen for maximum contrast and colorblind-friendliness.
 */
const TOOL_COLORS = [
  "#4A90D9", // Blue (T1)
  "#E74C3C", // Red (T2)
  "#2ECC71", // Green (T3)
  "#F39C12", // Orange (T4)
  "#9B59B6", // Purple (T5)
  "#1ABC9C", // Teal (T6)
  "#E91E63", // Pink (T7)
  "#00BCD4", // Cyan (T8)
  "#FF5722", // Deep Orange (T9)
  "#8BC34A", // Light Green (T10)
  "#673AB7", // Deep Purple (T11)
  "#FFC107", // Amber (T12)
];

/**
 * Get color for a tool number.
 * Tool numbers wrap around the palette if > 12 tools.
 */
export function getToolColor(toolNumber: number): string {
  const idx = ((toolNumber - 1) % TOOL_COLORS.length + TOOL_COLORS.length) % TOOL_COLORS.length;
  return TOOL_COLORS[idx];
}

/**
 * Get a darker shade of the tool color (for depth/emphasis).
 */
export function getToolColorDark(toolNumber: number): string {
  const base = getToolColor(toolNumber);
  // Convert to HSL and reduce lightness
  return adjustColorLightness(base, -20);
}

/**
 * Get a lighter shade of the tool color (for hover/highlight).
 */
export function getToolColorLight(toolNumber: number): string {
  const base = getToolColor(toolNumber);
  return adjustColorLightness(base, 20);
}

// ---------------------------------------------------------------------------
// Tool Info Types
// ---------------------------------------------------------------------------

export interface ToolInfo {
  /** Tool number (T1, T2, etc.) */
  number: number;
  /** Display color */
  color: string;
  /** Segment count for this tool */
  segmentCount: number;
  /** Total cut distance (mm) */
  cutDistance: number;
  /** Total cut time (ms) */
  cutTime: number;
  /** First line number where tool appears */
  firstLine: number;
  /** Last line number where tool appears */
  lastLine: number;
}

export interface ToolChangeMarker {
  /** Line number */
  lineNumber: number;
  /** Position [x, y, z] */
  position: [number, number, number];
  /** Tool switching from */
  fromTool: number;
  /** Tool switching to */
  toTool: number;
  /** Cumulative time at this point (ms) */
  timeMs: number;
  /** Segment index at this change */
  segmentIndex: number;
}

// ---------------------------------------------------------------------------
// Analysis Functions
// ---------------------------------------------------------------------------

import type { MoveSegment } from "@/sdk/endpoints/cam/simulate";

/**
 * Analyze segments and build tool info for each unique tool.
 */
export function analyzeToolUsage(segments: MoveSegment[]): ToolInfo[] {
  const toolMap = new Map<number, ToolInfo>();

  for (const seg of segments) {
    const toolNum = seg.tool_number ?? 1;

    if (!toolMap.has(toolNum)) {
      toolMap.set(toolNum, {
        number: toolNum,
        color: getToolColor(toolNum),
        segmentCount: 0,
        cutDistance: 0,
        cutTime: 0,
        firstLine: seg.line_number,
        lastLine: seg.line_number,
      });
    }

    const info = toolMap.get(toolNum)!;
    info.segmentCount++;
    info.lastLine = Math.max(info.lastLine, seg.line_number);
    info.cutTime += seg.duration_ms;

    // Calculate distance
    if (seg.type !== "rapid") {
      const dx = seg.to_pos[0] - seg.from_pos[0];
      const dy = seg.to_pos[1] - seg.from_pos[1];
      const dz = seg.to_pos[2] - seg.from_pos[2];
      info.cutDistance += Math.sqrt(dx * dx + dy * dy + dz * dz);
    }
  }

  return Array.from(toolMap.values()).sort((a, b) => a.number - b.number);
}

/**
 * Build tool change markers with timing info.
 */
export function buildToolChangeMarkers(segments: MoveSegment[]): ToolChangeMarker[] {
  const markers: ToolChangeMarker[] = [];
  let currentTool = segments[0]?.tool_number ?? 1;
  let cumulativeTime = 0;

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    const segTool = seg.tool_number ?? 1;

    if (segTool !== currentTool) {
      markers.push({
        lineNumber: seg.line_number,
        position: seg.from_pos,
        fromTool: currentTool,
        toTool: segTool,
        timeMs: cumulativeTime,
        segmentIndex: i,
      });
      currentTool = segTool;
    }

    cumulativeTime += seg.duration_ms;
  }

  return markers;
}

// ---------------------------------------------------------------------------
// Formatting Helpers
// ---------------------------------------------------------------------------

/**
 * Format tool number as display string.
 */
export function formatToolNumber(toolNum: number): string {
  return `T${toolNum}`;
}

/**
 * Format tool time as human-readable string.
 */
export function formatToolTime(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const secs = ms / 1000;
  if (secs < 60) return `${secs.toFixed(1)}s`;
  const mins = Math.floor(secs / 60);
  const s = Math.round(secs % 60);
  return `${mins}m ${s}s`;
}

/**
 * Format distance as human-readable string.
 */
export function formatToolDistance(mm: number): string {
  if (mm < 1) return `${mm.toFixed(2)} mm`;
  if (mm < 1000) return `${mm.toFixed(1)} mm`;
  return `${(mm / 1000).toFixed(2)} m`;
}

// ---------------------------------------------------------------------------
// Color Utility
// ---------------------------------------------------------------------------

function adjustColorLightness(hex: string, amount: number): string {
  // Parse hex color
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);

  // Convert to HSL
  const max = Math.max(r, g, b) / 255;
  const min = Math.min(r, g, b) / 255;
  let h = 0;
  let s = 0;
  let l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r / 255:
        h = ((g / 255 - b / 255) / d + (g < b ? 6 : 0)) / 6;
        break;
      case g / 255:
        h = ((b / 255 - r / 255) / d + 2) / 6;
        break;
      case b / 255:
        h = ((r / 255 - g / 255) / d + 4) / 6;
        break;
    }
  }

  // Adjust lightness
  l = Math.max(0, Math.min(1, l + amount / 100));

  // Convert back to RGB
  const hue2rgb = (p: number, q: number, t: number) => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };

  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const newR = Math.round(hue2rgb(p, q, h + 1 / 3) * 255);
  const newG = Math.round(hue2rgb(p, q, h) * 255);
  const newB = Math.round(hue2rgb(p, q, h - 1 / 3) * 255);

  return `#${newR.toString(16).padStart(2, "0")}${newG.toString(16).padStart(2, "0")}${newB.toString(16).padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export default {
  getToolColor,
  getToolColorDark,
  getToolColorLight,
  analyzeToolUsage,
  buildToolChangeMarkers,
  formatToolNumber,
  formatToolTime,
  formatToolDistance,
};
