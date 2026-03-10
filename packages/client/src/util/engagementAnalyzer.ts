/**
 * engagementAnalyzer — P5 Tool Engagement Heatmap
 *
 * Analyzes toolpath segments to calculate relative tool engagement/load.
 * Used to generate heatmap visualization showing cutting intensity.
 *
 * Engagement factors:
 * - Feed rate (higher = more aggressive)
 * - Z depth (deeper = more engagement)
 * - Direction changes (corners = higher load)
 * - Move type (cuts vs rapids)
 * - Chip load estimation
 */

import type { MoveSegment } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface EngagementData {
  /** Segment index */
  index: number;
  /** Normalized engagement 0-1 (0 = no load, 1 = max load) */
  engagement: number;
  /** Raw engagement value before normalization */
  rawValue: number;
  /** Engagement category for coloring */
  category: "none" | "light" | "medium" | "heavy" | "extreme";
}

export interface EngagementConfig {
  /** Tool diameter in mm */
  toolDiameter: number;
  /** Number of flutes */
  flutes: number;
  /** Max feed rate for normalization (mm/min) */
  maxFeed: number;
  /** Max depth for normalization (mm) */
  maxDepth: number;
  /** Weight for feed rate factor (0-1) */
  feedWeight: number;
  /** Weight for depth factor (0-1) */
  depthWeight: number;
  /** Weight for direction change factor (0-1) */
  directionWeight: number;
}

export interface EngagementReport {
  /** Per-segment engagement data */
  segments: EngagementData[];
  /** Statistics */
  stats: {
    min: number;
    max: number;
    average: number;
    hotspotCount: number; // segments > 0.8 engagement
  };
  /** Hotspot segment indices (high engagement areas) */
  hotspots: number[];
}

// ---------------------------------------------------------------------------
// Default config
// ---------------------------------------------------------------------------

const DEFAULT_CONFIG: EngagementConfig = {
  toolDiameter: 6,
  flutes: 2,
  maxFeed: 3000,
  maxDepth: 20,
  feedWeight: 0.4,
  depthWeight: 0.35,
  directionWeight: 0.25,
};

// ---------------------------------------------------------------------------
// Analyzer
// ---------------------------------------------------------------------------

export class EngagementAnalyzer {
  private config: EngagementConfig;

  constructor(config: Partial<EngagementConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Analyze segments and compute engagement data
   */
  analyze(segments: MoveSegment[]): EngagementReport {
    if (segments.length === 0) {
      return {
        segments: [],
        stats: { min: 0, max: 0, average: 0, hotspotCount: 0 },
        hotspots: [],
      };
    }

    // First pass: compute raw engagement values
    const rawData: { index: number; raw: number }[] = [];
    let maxRaw = 0;

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      const raw = this.computeRawEngagement(seg, segments[i - 1], segments[i + 1]);
      rawData.push({ index: i, raw });
      maxRaw = Math.max(maxRaw, raw);
    }

    // Normalize and categorize
    const engagementData: EngagementData[] = rawData.map(({ index, raw }) => {
      const engagement = maxRaw > 0 ? raw / maxRaw : 0;
      return {
        index,
        engagement,
        rawValue: raw,
        category: this.categorize(engagement),
      };
    });

    // Compute stats
    const engagementValues = engagementData.map((d) => d.engagement);
    const sum = engagementValues.reduce((a, b) => a + b, 0);
    const hotspots = engagementData
      .filter((d) => d.engagement > 0.8)
      .map((d) => d.index);

    return {
      segments: engagementData,
      stats: {
        min: Math.min(...engagementValues),
        max: Math.max(...engagementValues),
        average: sum / engagementValues.length,
        hotspotCount: hotspots.length,
      },
      hotspots,
    };
  }

  /**
   * Compute raw engagement for a single segment
   */
  private computeRawEngagement(
    seg: MoveSegment,
    prev?: MoveSegment,
    next?: MoveSegment
  ): number {
    // Rapids have zero engagement
    if (seg.type === "rapid") {
      return 0;
    }

    let engagement = 0;

    // Feed rate factor (higher feed = more engagement)
    const feedFactor = Math.min((seg.feed || 0) / this.config.maxFeed, 1);
    engagement += feedFactor * this.config.feedWeight;

    // Z depth factor (deeper = more engagement)
    const zDepth = Math.abs(Math.min(seg.to_pos[2], 0));
    const depthFactor = Math.min(zDepth / this.config.maxDepth, 1);
    engagement += depthFactor * this.config.depthWeight;

    // Direction change factor (corners = higher load)
    const dirFactor = this.computeDirectionFactor(seg, prev, next);
    engagement += dirFactor * this.config.directionWeight;

    // Boost for arcs (constant engagement)
    if (seg.type === "arc_cw" || seg.type === "arc_ccw") {
      engagement *= 1.1;
    }

    // Boost for plunge moves (Z change during cut)
    const zChange = Math.abs(seg.to_pos[2] - seg.from_pos[2]);
    if (zChange > 0.5) {
      engagement *= 1.2;
    }

    return Math.min(engagement, 1);
  }

  /**
   * Compute direction change factor between segments
   */
  private computeDirectionFactor(
    seg: MoveSegment,
    prev?: MoveSegment,
    next?: MoveSegment
  ): number {
    if (!prev && !next) return 0;

    let maxAngle = 0;

    // Check angle with previous segment
    if (prev && prev.type !== "rapid") {
      const angle = this.angleBetweenSegments(prev, seg);
      maxAngle = Math.max(maxAngle, angle);
    }

    // Check angle with next segment
    if (next && next.type !== "rapid") {
      const angle = this.angleBetweenSegments(seg, next);
      maxAngle = Math.max(maxAngle, angle);
    }

    // Normalize: 0° = 0, 90° = 0.5, 180° = 1
    return maxAngle / Math.PI;
  }

  /**
   * Calculate angle between two segments (in radians)
   */
  private angleBetweenSegments(a: MoveSegment, b: MoveSegment): number {
    const dirA = [
      a.to_pos[0] - a.from_pos[0],
      a.to_pos[1] - a.from_pos[1],
    ];
    const dirB = [
      b.to_pos[0] - b.from_pos[0],
      b.to_pos[1] - b.from_pos[1],
    ];

    const lenA = Math.sqrt(dirA[0] ** 2 + dirA[1] ** 2);
    const lenB = Math.sqrt(dirB[0] ** 2 + dirB[1] ** 2);

    if (lenA < 0.001 || lenB < 0.001) return 0;

    const dot = (dirA[0] * dirB[0] + dirA[1] * dirB[1]) / (lenA * lenB);
    const clamped = Math.max(-1, Math.min(1, dot));

    return Math.acos(clamped);
  }

  /**
   * Categorize engagement level
   */
  private categorize(engagement: number): EngagementData["category"] {
    if (engagement === 0) return "none";
    if (engagement < 0.25) return "light";
    if (engagement < 0.5) return "medium";
    if (engagement < 0.8) return "heavy";
    return "extreme";
  }

  /**
   * Get color for engagement level (for heatmap rendering)
   */
  static getColor(engagement: number): string {
    // Cool (blue) to hot (red) gradient
    if (engagement === 0) return "#333333";
    if (engagement < 0.2) return "#1a4a9e"; // Cool blue
    if (engagement < 0.4) return "#2ecc71"; // Green
    if (engagement < 0.6) return "#f1c40f"; // Yellow
    if (engagement < 0.8) return "#e67e22"; // Orange
    return "#e74c3c"; // Red/hot
  }

  /**
   * Get hex color as number (for Three.js)
   */
  static getColorHex(engagement: number): number {
    if (engagement === 0) return 0x333333;
    if (engagement < 0.2) return 0x1a4a9e;
    if (engagement < 0.4) return 0x2ecc71;
    if (engagement < 0.6) return 0xf1c40f;
    if (engagement < 0.8) return 0xe67e22;
    return 0xe74c3c;
  }

  /**
   * Interpolate between colors for smooth gradient
   */
  static getColorInterpolated(engagement: number): string {
    const stops = [
      { pos: 0, r: 51, g: 51, b: 51 },      // #333333 - none
      { pos: 0.2, r: 26, g: 74, b: 158 },   // #1a4a9e - cool
      { pos: 0.4, r: 46, g: 204, b: 113 },  // #2ecc71 - green
      { pos: 0.6, r: 241, g: 196, b: 15 },  // #f1c40f - yellow
      { pos: 0.8, r: 230, g: 126, b: 34 },  // #e67e22 - orange
      { pos: 1.0, r: 231, g: 76, b: 60 },   // #e74c3c - red
    ];

    // Find surrounding stops
    let lower = stops[0];
    let upper = stops[stops.length - 1];

    for (let i = 0; i < stops.length - 1; i++) {
      if (engagement >= stops[i].pos && engagement <= stops[i + 1].pos) {
        lower = stops[i];
        upper = stops[i + 1];
        break;
      }
    }

    // Interpolate
    const range = upper.pos - lower.pos;
    const t = range > 0 ? (engagement - lower.pos) / range : 0;

    const r = Math.round(lower.r + (upper.r - lower.r) * t);
    const g = Math.round(lower.g + (upper.g - lower.g) * t);
    const b = Math.round(lower.b + (upper.b - lower.b) * t);

    return `rgb(${r},${g},${b})`;
  }

  /**
   * Get interpolated color as hex number (for Three.js)
   */
  static getColorInterpolatedHex(engagement: number): number {
    const colorStr = EngagementAnalyzer.getColorInterpolated(engagement);
    const match = colorStr.match(/rgb\((\d+),(\d+),(\d+)\)/);
    if (!match) return 0x333333;

    const r = parseInt(match[1], 10);
    const g = parseInt(match[2], 10);
    const b = parseInt(match[3], 10);

    return (r << 16) | (g << 8) | b;
  }
}

export default EngagementAnalyzer;
