/**
 * chipLoadAnalyzer — P6 Step 16: Chip Load Analysis with S-code Tracking
 *
 * Calculates and analyzes chip load throughout the toolpath:
 * - Tracks spindle RPM from S-codes in G-code
 * - Computes chip load per tooth based on feed, RPM, flutes
 * - Identifies sections with problematic chip loads
 * - Provides material-specific recommendations
 *
 * Formula: Chip Load = Feed (mm/min) / (RPM × Number of Flutes)
 */

import type { MoveSegment } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ChipLoadSeverity = "critical" | "warning" | "optimal" | "info";

export interface ChipLoadConfig {
  /** Tool diameter in mm */
  toolDiameter: number;
  /** Number of flutes/teeth */
  fluteCount: number;
  /** Default spindle RPM if not specified in G-code */
  defaultRpm: number;
  /** Optimal chip load range for material (mm/tooth) */
  optimalRange: [number, number];
  /** Material type for recommendations */
  materialType?: MaterialType;
}

export type MaterialType = "softwood" | "hardwood" | "plywood" | "mdf" | "plastic" | "aluminum" | "steel";

export interface ChipLoadPoint {
  /** Segment index */
  segmentIndex: number;
  /** Time offset (ms) */
  timeMs: number;
  /** Feed rate (mm/min) */
  feed: number;
  /** Spindle RPM at this point */
  rpm: number;
  /** Calculated chip load (mm/tooth) */
  chipLoad: number;
  /** Chip load status */
  status: ChipLoadStatus;
  /** G-code line number */
  lineNumber: number;
}

export type ChipLoadStatus = "too_low" | "low" | "optimal" | "high" | "too_high" | "unknown";

export interface ChipLoadIssue {
  /** Issue severity */
  severity: ChipLoadSeverity;
  /** Human-readable message */
  message: string;
  /** Detailed explanation */
  details: string;
  /** Segment range */
  segmentRange: [number, number];
  /** G-code line numbers */
  lineNumbers: number[];
  /** Current chip load */
  currentChipLoad: number;
  /** Suggested chip load */
  suggestedChipLoad: number;
  /** Suggested fix (feed or RPM change) */
  suggestedFix: string;
  /** Duration of issue (ms) */
  durationMs: number;
}

export interface ChipLoadStats {
  /** Minimum chip load observed */
  minChipLoad: number;
  /** Maximum chip load observed */
  maxChipLoad: number;
  /** Average chip load */
  avgChipLoad: number;
  /** Median chip load */
  medianChipLoad: number;
  /** Standard deviation */
  stdDev: number;
  /** Percentage of time in optimal range */
  timeInOptimalPct: number;
  /** Time below optimal (ms) */
  timeBelowOptimalMs: number;
  /** Time above optimal (ms) */
  timeAboveOptimalMs: number;
  /** Number of RPM changes */
  rpmChanges: number;
  /** Unique RPM values used */
  uniqueRpms: number[];
}

export interface ChipLoadReport {
  /** Overall chip load health score (0-100) */
  healthScore: number;
  /** Statistics */
  stats: ChipLoadStats;
  /** Issue list */
  issues: ChipLoadIssue[];
  /** Timeline of chip load values */
  timeline: ChipLoadPoint[];
  /** Summary message */
  summary: string;
  /** Material-specific recommendations */
  recommendations: string[];
}

// ---------------------------------------------------------------------------
// Material Defaults
// ---------------------------------------------------------------------------

const MATERIAL_CHIP_LOADS: Record<MaterialType, { optimal: [number, number]; description: string }> = {
  softwood: { optimal: [0.15, 0.35], description: "Pine, Cedar, Spruce" },
  hardwood: { optimal: [0.10, 0.25], description: "Oak, Maple, Walnut" },
  plywood: { optimal: [0.10, 0.25], description: "Birch/Baltic Plywood" },
  mdf: { optimal: [0.12, 0.30], description: "MDF, Particle Board" },
  plastic: { optimal: [0.08, 0.20], description: "Acrylic, HDPE" },
  aluminum: { optimal: [0.05, 0.15], description: "6061-T6 Aluminum" },
  steel: { optimal: [0.02, 0.08], description: "Mild Steel, Stainless" },
};

// ---------------------------------------------------------------------------
// ChipLoadAnalyzer Class
// ---------------------------------------------------------------------------

export class ChipLoadAnalyzer {
  private config: Required<ChipLoadConfig>;

  constructor(config: Partial<ChipLoadConfig> = {}) {
    const materialType = config.materialType ?? "hardwood";
    const defaultOptimal = MATERIAL_CHIP_LOADS[materialType]?.optimal ?? [0.10, 0.25];

    this.config = {
      toolDiameter: config.toolDiameter ?? 6,
      fluteCount: config.fluteCount ?? 2,
      defaultRpm: config.defaultRpm ?? 18000,
      optimalRange: config.optimalRange ?? defaultOptimal,
      materialType,
    };
  }

  /**
   * Analyze chip load throughout toolpath
   */
  analyze(segments: MoveSegment[]): ChipLoadReport {
    const cutSegments = segments.filter(s => s.type !== "rapid");

    if (cutSegments.length === 0) {
      return this.emptyReport();
    }

    // Build timeline with RPM tracking
    const timeline = this.buildTimeline(segments);
    const stats = this.computeStats(timeline, segments);
    const issues = this.findIssues(timeline, segments);

    const healthScore = this.calculateHealthScore(stats, issues);
    const recommendations = this.generateRecommendations(stats, issues);

    return {
      healthScore,
      stats,
      issues,
      timeline,
      summary: this.generateSummary(healthScore, stats, issues),
      recommendations,
    };
  }

  /**
   * Calculate chip load for given parameters
   */
  calculateChipLoad(feed: number, rpm: number): number {
    if (rpm <= 0 || this.config.fluteCount <= 0) return 0;
    return feed / (rpm * this.config.fluteCount);
  }

  /**
   * Get chip load status
   */
  getChipLoadStatus(chipLoad: number): ChipLoadStatus {
    const [optMin, optMax] = this.config.optimalRange;

    if (chipLoad <= 0) return "unknown";
    if (chipLoad < optMin * 0.5) return "too_low";
    if (chipLoad < optMin) return "low";
    if (chipLoad <= optMax) return "optimal";
    if (chipLoad <= optMax * 1.5) return "high";
    return "too_high";
  }

  // ---------------------------------------------------------------------------
  // Private Methods
  // ---------------------------------------------------------------------------

  private buildTimeline(segments: MoveSegment[]): ChipLoadPoint[] {
    const timeline: ChipLoadPoint[] = [];
    let currentRpm = this.config.defaultRpm;
    let timeMs = 0;

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];

      // Track S-code (RPM) changes from line text
      if (seg.line_text) {
        const sMatch = seg.line_text.match(/S(\d+)/i);
        if (sMatch) {
          currentRpm = parseInt(sMatch[1], 10);
        }
      }

      // Only analyze cutting moves
      if (seg.type !== "rapid" && seg.feed > 0) {
        const chipLoad = this.calculateChipLoad(seg.feed, currentRpm);
        const status = this.getChipLoadStatus(chipLoad);

        timeline.push({
          segmentIndex: i,
          timeMs,
          feed: seg.feed,
          rpm: currentRpm,
          chipLoad,
          status,
          lineNumber: seg.line_number,
        });
      }

      timeMs += seg.duration_ms;
    }

    return timeline;
  }

  private computeStats(timeline: ChipLoadPoint[], segments: MoveSegment[]): ChipLoadStats {
    if (timeline.length === 0) {
      return this.emptyStats();
    }

    const chipLoads = timeline.map(p => p.chipLoad).filter(c => c > 0);
    const sorted = [...chipLoads].sort((a, b) => a - b);

    const sum = chipLoads.reduce((a, b) => a + b, 0);
    const avg = sum / chipLoads.length;
    const median = sorted[Math.floor(sorted.length / 2)];

    const variance = chipLoads.reduce((sum, c) => sum + (c - avg) ** 2, 0) / chipLoads.length;
    const stdDev = Math.sqrt(variance);

    // Time analysis
    const [optMin, optMax] = this.config.optimalRange;
    let timeOptimal = 0;
    let timeBelow = 0;
    let timeAbove = 0;

    for (const point of timeline) {
      const segDuration = segments[point.segmentIndex]?.duration_ms ?? 0;

      if (point.chipLoad < optMin) {
        timeBelow += segDuration;
      } else if (point.chipLoad > optMax) {
        timeAbove += segDuration;
      } else {
        timeOptimal += segDuration;
      }
    }

    const totalTime = timeOptimal + timeBelow + timeAbove;
    const timeInOptimalPct = totalTime > 0 ? (timeOptimal / totalTime) * 100 : 0;

    // RPM tracking
    const rpms = new Set(timeline.map(p => p.rpm));
    let rpmChanges = 0;
    let prevRpm = 0;
    for (const point of timeline) {
      if (point.rpm !== prevRpm && prevRpm > 0) rpmChanges++;
      prevRpm = point.rpm;
    }

    return {
      minChipLoad: Math.round(sorted[0] * 1000) / 1000,
      maxChipLoad: Math.round(sorted[sorted.length - 1] * 1000) / 1000,
      avgChipLoad: Math.round(avg * 1000) / 1000,
      medianChipLoad: Math.round(median * 1000) / 1000,
      stdDev: Math.round(stdDev * 1000) / 1000,
      timeInOptimalPct: Math.round(timeInOptimalPct * 10) / 10,
      timeBelowOptimalMs: Math.round(timeBelow),
      timeAboveOptimalMs: Math.round(timeAbove),
      rpmChanges,
      uniqueRpms: Array.from(rpms).sort((a, b) => a - b),
    };
  }

  private findIssues(timeline: ChipLoadPoint[], segments: MoveSegment[]): ChipLoadIssue[] {
    const issues: ChipLoadIssue[] = [];
    const [optMin, optMax] = this.config.optimalRange;

    // Find consecutive segments with same issue
    let issueStart = -1;
    let issueStatus: ChipLoadStatus | null = null;
    let issuePoints: ChipLoadPoint[] = [];

    const closeIssue = () => {
      if (issueStart === -1 || issuePoints.length === 0) return;

      const totalDuration = issuePoints.reduce(
        (sum, p) => sum + (segments[p.segmentIndex]?.duration_ms ?? 0),
        0
      );

      // Only report if duration is significant (> 1 second)
      if (totalDuration < 1000) {
        issueStart = -1;
        issueStatus = null;
        issuePoints = [];
        return;
      }

      const avgChipLoad = issuePoints.reduce((sum, p) => sum + p.chipLoad, 0) / issuePoints.length;
      const avgFeed = issuePoints.reduce((sum, p) => sum + p.feed, 0) / issuePoints.length;
      const avgRpm = issuePoints[0].rpm;

      const issue = this.createIssue(
        issueStatus!,
        avgChipLoad,
        avgFeed,
        avgRpm,
        issuePoints[0].segmentIndex,
        issuePoints[issuePoints.length - 1].segmentIndex,
        issuePoints.map(p => p.lineNumber),
        totalDuration
      );

      if (issue) issues.push(issue);

      issueStart = -1;
      issueStatus = null;
      issuePoints = [];
    };

    for (const point of timeline) {
      const status = point.status;

      if (status === "optimal" || status === "unknown") {
        closeIssue();
        continue;
      }

      if (issueStatus !== status) {
        closeIssue();
        issueStart = point.segmentIndex;
        issueStatus = status;
      }

      issuePoints.push(point);
    }

    closeIssue();

    // Sort by severity
    const severityOrder: Record<ChipLoadSeverity, number> = {
      critical: 0,
      warning: 1,
      optimal: 2,
      info: 3,
    };
    issues.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

    return issues;
  }

  private createIssue(
    status: ChipLoadStatus,
    avgChipLoad: number,
    avgFeed: number,
    rpm: number,
    startIdx: number,
    endIdx: number,
    lineNumbers: number[],
    durationMs: number
  ): ChipLoadIssue | null {
    const [optMin, optMax] = this.config.optimalRange;
    const midOptimal = (optMin + optMax) / 2;

    switch (status) {
      case "too_low": {
        const suggestedFeed = midOptimal * rpm * this.config.fluteCount;
        return {
          severity: "warning",
          message: `Very low chip load (${(avgChipLoad * 1000).toFixed(2)} μm)`,
          details: `Chip load is well below optimal. This causes rubbing instead of cutting, leading to heat buildup, poor finish, and accelerated tool wear.`,
          segmentRange: [startIdx, endIdx],
          lineNumbers: [...new Set(lineNumbers)].slice(0, 5),
          currentChipLoad: avgChipLoad,
          suggestedChipLoad: midOptimal,
          suggestedFix: `Increase feed to F${Math.round(suggestedFeed)} or reduce RPM to ${Math.round((avgFeed / (midOptimal * this.config.fluteCount)))}`,
          durationMs,
        };
      }

      case "low": {
        const suggestedFeed = optMin * rpm * this.config.fluteCount;
        return {
          severity: "info",
          message: `Low chip load (${(avgChipLoad * 1000).toFixed(2)} μm)`,
          details: `Chip load is below optimal range. Consider increasing feed rate for better chip evacuation and reduced heat.`,
          segmentRange: [startIdx, endIdx],
          lineNumbers: [...new Set(lineNumbers)].slice(0, 5),
          currentChipLoad: avgChipLoad,
          suggestedChipLoad: optMin,
          suggestedFix: `Increase feed to F${Math.round(suggestedFeed)}`,
          durationMs,
        };
      }

      case "high": {
        const suggestedFeed = optMax * rpm * this.config.fluteCount;
        return {
          severity: "info",
          message: `High chip load (${(avgChipLoad * 1000).toFixed(2)} μm)`,
          details: `Chip load is above optimal range. May cause increased tool wear or chipping. Consider reducing feed or increasing RPM.`,
          segmentRange: [startIdx, endIdx],
          lineNumbers: [...new Set(lineNumbers)].slice(0, 5),
          currentChipLoad: avgChipLoad,
          suggestedChipLoad: optMax,
          suggestedFix: `Reduce feed to F${Math.round(suggestedFeed)} or increase RPM`,
          durationMs,
        };
      }

      case "too_high": {
        const suggestedRpm = Math.round(avgFeed / (midOptimal * this.config.fluteCount));
        return {
          severity: "critical",
          message: `Excessive chip load (${(avgChipLoad * 1000).toFixed(2)} μm)`,
          details: `Chip load is dangerously high. Risk of tool breakage, deflection, and poor cut quality. Reduce feed rate or increase spindle speed.`,
          segmentRange: [startIdx, endIdx],
          lineNumbers: [...new Set(lineNumbers)].slice(0, 5),
          currentChipLoad: avgChipLoad,
          suggestedChipLoad: midOptimal,
          suggestedFix: `Reduce feed by ${Math.round((1 - midOptimal / avgChipLoad) * 100)}% or increase RPM to ${suggestedRpm}`,
          durationMs,
        };
      }

      default:
        return null;
    }
  }

  private calculateHealthScore(stats: ChipLoadStats, issues: ChipLoadIssue[]): number {
    let score = 100;

    // Deduct for time outside optimal range
    score -= Math.min(30, (100 - stats.timeInOptimalPct) * 0.3);

    // Deduct for issues
    const criticalCount = issues.filter(i => i.severity === "critical").length;
    const warningCount = issues.filter(i => i.severity === "warning").length;

    score -= criticalCount * 15;
    score -= warningCount * 5;

    // Deduct for high variation
    if (stats.stdDev > stats.avgChipLoad * 0.5) score -= 10;

    return Math.max(0, Math.min(100, Math.round(score)));
  }

  private generateSummary(score: number, stats: ChipLoadStats, issues: ChipLoadIssue[]): string {
    if (issues.length === 0 && stats.timeInOptimalPct > 80) {
      return "Excellent chip load consistency throughout the toolpath.";
    }

    const criticalCount = issues.filter(i => i.severity === "critical").length;
    if (criticalCount > 0) {
      return `${criticalCount} critical chip load issue(s) detected that risk tool breakage.`;
    }

    const warningCount = issues.filter(i => i.severity === "warning").length;
    if (warningCount > 0) {
      return `${warningCount} chip load warning(s) found. ${stats.timeInOptimalPct.toFixed(0)}% time in optimal range.`;
    }

    return `Score: ${score}/100. ${stats.timeInOptimalPct.toFixed(0)}% of cutting time in optimal chip load range.`;
  }

  private generateRecommendations(stats: ChipLoadStats, issues: ChipLoadIssue[]): string[] {
    const recs: string[] = [];
    const [optMin, optMax] = this.config.optimalRange;

    if (stats.avgChipLoad < optMin) {
      recs.push(`Consider increasing feed rates. Average chip load (${(stats.avgChipLoad * 1000).toFixed(2)} μm) is below optimal.`);
    }

    if (stats.avgChipLoad > optMax) {
      recs.push(`Consider reducing feed rates or increasing RPM. Average chip load is above optimal for ${this.config.materialType}.`);
    }

    if (stats.rpmChanges === 0 && stats.uniqueRpms.length === 1) {
      recs.push(`Using single RPM (S${stats.uniqueRpms[0]}). Variable spindle speeds can optimize chip load for different operations.`);
    }

    if (stats.timeInOptimalPct < 50) {
      recs.push(`Only ${stats.timeInOptimalPct.toFixed(0)}% of cut time is in optimal range. Review feed/RPM combinations.`);
    }

    const materialInfo = MATERIAL_CHIP_LOADS[this.config.materialType!];
    if (materialInfo) {
      recs.push(`For ${materialInfo.description}, target chip load: ${optMin.toFixed(2)}-${optMax.toFixed(2)} mm/tooth.`);
    }

    return recs;
  }

  private emptyReport(): ChipLoadReport {
    return {
      healthScore: 100,
      stats: this.emptyStats(),
      issues: [],
      timeline: [],
      summary: "No cutting moves to analyze.",
      recommendations: [],
    };
  }

  private emptyStats(): ChipLoadStats {
    return {
      minChipLoad: 0,
      maxChipLoad: 0,
      avgChipLoad: 0,
      medianChipLoad: 0,
      stdDev: 0,
      timeInOptimalPct: 0,
      timeBelowOptimalMs: 0,
      timeAboveOptimalMs: 0,
      rpmChanges: 0,
      uniqueRpms: [],
    };
  }
}

// ---------------------------------------------------------------------------
// Factory & Export
// ---------------------------------------------------------------------------

export function createChipLoadAnalyzer(config?: Partial<ChipLoadConfig>): ChipLoadAnalyzer {
  return new ChipLoadAnalyzer(config);
}

export { MATERIAL_CHIP_LOADS };
export default ChipLoadAnalyzer;
