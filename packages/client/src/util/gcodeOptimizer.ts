/**
 * gcodeOptimizer — P4.4 Optimization Suggestions
 *
 * Analyzes G-code toolpaths and suggests improvements:
 * - Redundant rapids (consecutive rapids that could be combined)
 * - Air cutting (cutting moves above material)
 * - Feed rate opportunities (too slow in certain conditions)
 * - Inefficient tool ordering
 *
 * Value: Help users identify why their programs take longer than expected
 */

import type { MoveSegment, SimulateBounds } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type OptimizationCategory =
  | "redundant-rapid"
  | "air-cutting"
  | "feed-opportunity"
  | "path-inefficiency"
  | "retract-optimization"
  | "arc-substitution";

export type OptimizationSeverity = "high" | "medium" | "low";

export interface OptimizationSuggestion {
  /** Category of optimization */
  category: OptimizationCategory;
  /** Severity/impact level */
  severity: OptimizationSeverity;
  /** Human-readable description */
  message: string;
  /** Affected segments (start index) */
  startSegment: number;
  /** Affected segments (end index) */
  endSegment: number;
  /** G-code line numbers involved */
  lineNumbers: number[];
  /** Estimated time savings in ms */
  timeSavings: number;
  /** Estimated distance savings in mm */
  distanceSavings: number;
  /** Suggested fix (if applicable) */
  suggestion?: string;
  /** Additional details */
  details?: Record<string, unknown>;
}

export interface OptimizationReport {
  /** All suggestions */
  suggestions: OptimizationSuggestion[];
  /** Count by category */
  countByCategory: Record<OptimizationCategory, number>;
  /** Total potential time savings (ms) */
  totalTimeSavings: number;
  /** Total potential distance savings (mm) */
  totalDistanceSavings: number;
  /** Percentage improvement possible */
  percentImprovement: number;
  /** Summary message */
  summary: string;
}

export interface OptimizerConfig {
  /** Stock/material top Z (default: 0) */
  stockTopZ?: number;
  /** Safe Z height (default: 5mm) */
  safeZ?: number;
  /** Minimum distance to consider as redundant (mm) */
  minRedundantDistance?: number;
  /** Feed rate threshold for "too slow" detection (mm/min) */
  feedThreshold?: number;
  /** Rapid feed rate for time calculations (mm/min) */
  rapidFeedRate?: number;
  /** Original program time for percentage calculations */
  originalTime?: number;
}

// ---------------------------------------------------------------------------
// GcodeOptimizer Class
// ---------------------------------------------------------------------------

export class GcodeOptimizer {
  private config: Required<OptimizerConfig>;

  constructor(config: OptimizerConfig = {}) {
    this.config = {
      stockTopZ: config.stockTopZ ?? 0,
      safeZ: config.safeZ ?? 5,
      minRedundantDistance: config.minRedundantDistance ?? 0.5,
      feedThreshold: config.feedThreshold ?? 100,
      rapidFeedRate: config.rapidFeedRate ?? 5000,
      originalTime: config.originalTime ?? 0,
    };
  }

  /**
   * Update configuration
   */
  setConfig(config: Partial<OptimizerConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Analyze segments and generate optimization suggestions
   */
  analyze(segments: MoveSegment[]): OptimizationReport {
    const suggestions: OptimizationSuggestion[] = [];

    // Run all analyzers
    suggestions.push(...this.findRedundantRapids(segments));
    suggestions.push(...this.findAirCutting(segments));
    suggestions.push(...this.findFeedOpportunities(segments));
    suggestions.push(...this.findPathInefficiencies(segments));
    suggestions.push(...this.findRetractOptimizations(segments));
    suggestions.push(...this.findArcSubstitutions(segments));

    // Sort by severity and time savings
    suggestions.sort((a, b) => {
      const severityOrder = { high: 0, medium: 1, low: 2 };
      if (severityOrder[a.severity] !== severityOrder[b.severity]) {
        return severityOrder[a.severity] - severityOrder[b.severity];
      }
      return b.timeSavings - a.timeSavings;
    });

    return this.generateReport(suggestions, segments);
  }

  /**
   * Find consecutive rapids that could be combined
   */
  private findRedundantRapids(segments: MoveSegment[]): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];
    let rapidStart = -1;
    let rapidCount = 0;
    let totalRapidDist = 0;

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];

      if (seg.type === "rapid") {
        if (rapidStart === -1) {
          rapidStart = i;
          rapidCount = 1;
          totalRapidDist = this.segmentDistance(seg);
        } else {
          rapidCount++;
          totalRapidDist += this.segmentDistance(seg);
        }
      } else {
        // End of rapid sequence
        if (rapidCount > 2) {
          // Calculate direct distance
          const startPos = segments[rapidStart].from_pos;
          const endPos = segments[i - 1].to_pos;
          const directDist = this.distance3D(startPos, endPos);
          const savings = totalRapidDist - directDist;

          if (savings > this.config.minRedundantDistance) {
            suggestions.push({
              category: "redundant-rapid",
              severity: savings > 20 ? "high" : savings > 5 ? "medium" : "low",
              message: `${rapidCount} consecutive rapids could be combined into direct move`,
              startSegment: rapidStart,
              endSegment: i - 1,
              lineNumbers: this.getLineNumbers(segments, rapidStart, i - 1),
              timeSavings: this.distanceToTime(savings, this.config.rapidFeedRate),
              distanceSavings: Math.round(savings * 100) / 100,
              suggestion: `Replace with single G0 to (${endPos[0].toFixed(2)}, ${endPos[1].toFixed(2)}, ${endPos[2].toFixed(2)})`,
              details: {
                originalMoves: rapidCount,
                originalDistance: Math.round(totalRapidDist * 100) / 100,
                directDistance: Math.round(directDist * 100) / 100,
              },
            });
          }
        }

        rapidStart = -1;
        rapidCount = 0;
        totalRapidDist = 0;
      }
    }

    return suggestions;
  }

  /**
   * Find cutting moves that are above material (air cutting)
   */
  private findAirCutting(segments: MoveSegment[]): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];
    let airCutStart = -1;
    let airCutTime = 0;
    let airCutDist = 0;

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];

      // Skip rapids
      if (seg.type === "rapid") {
        if (airCutStart !== -1 && airCutTime > 100) {
          suggestions.push(this.createAirCutSuggestion(
            segments, airCutStart, i - 1, airCutTime, airCutDist
          ));
        }
        airCutStart = -1;
        airCutTime = 0;
        airCutDist = 0;
        continue;
      }

      // Check if cutting above stock
      const minZ = Math.min(seg.from_pos[2], seg.to_pos[2]);
      if (minZ > this.config.stockTopZ) {
        if (airCutStart === -1) {
          airCutStart = i;
        }
        airCutTime += seg.duration_ms;
        airCutDist += this.segmentDistance(seg);
      } else {
        if (airCutStart !== -1 && airCutTime > 100) {
          suggestions.push(this.createAirCutSuggestion(
            segments, airCutStart, i - 1, airCutTime, airCutDist
          ));
        }
        airCutStart = -1;
        airCutTime = 0;
        airCutDist = 0;
      }
    }

    // Handle end of segments
    if (airCutStart !== -1 && airCutTime > 100) {
      suggestions.push(this.createAirCutSuggestion(
        segments, airCutStart, segments.length - 1, airCutTime, airCutDist
      ));
    }

    return suggestions;
  }

  private createAirCutSuggestion(
    segments: MoveSegment[],
    start: number,
    end: number,
    time: number,
    dist: number
  ): OptimizationSuggestion {
    const rapidTime = this.distanceToTime(dist, this.config.rapidFeedRate);
    const savings = time - rapidTime;

    return {
      category: "air-cutting",
      severity: savings > 5000 ? "high" : savings > 1000 ? "medium" : "low",
      message: `Cutting move above material - could be rapid`,
      startSegment: start,
      endSegment: end,
      lineNumbers: this.getLineNumbers(segments, start, end),
      timeSavings: Math.round(savings),
      distanceSavings: 0, // Same distance, just faster
      suggestion: `Convert to G0 rapid move`,
      details: {
        currentTime: Math.round(time),
        rapidTime: Math.round(rapidTime),
        avgZ: (segments[start].from_pos[2] + segments[end].to_pos[2]) / 2,
      },
    };
  }

  /**
   * Find areas where feed rate could be increased
   */
  private findFeedOpportunities(segments: MoveSegment[]): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];

      // Skip rapids
      if (seg.type === "rapid" || !seg.feed) continue;

      // Check for very slow feed rates
      if (seg.feed < this.config.feedThreshold) {
        const potentialFeed = this.config.feedThreshold * 2;
        const currentTime = seg.duration_ms;
        const fasterTime = currentTime * (seg.feed / potentialFeed);
        const savings = currentTime - fasterTime;

        if (savings > 500) {
          suggestions.push({
            category: "feed-opportunity",
            severity: savings > 5000 ? "high" : savings > 2000 ? "medium" : "low",
            message: `Very slow feed rate: F${seg.feed}`,
            startSegment: i,
            endSegment: i,
            lineNumbers: [seg.line_number],
            timeSavings: Math.round(savings),
            distanceSavings: 0,
            suggestion: `Consider increasing to F${potentialFeed} if material allows`,
            details: {
              currentFeed: seg.feed,
              suggestedFeed: potentialFeed,
              moveType: seg.type,
            },
          });
        }
      }
    }

    return suggestions;
  }

  /**
   * Find inefficient paths (zigzag where parallel would be better, etc.)
   */
  private findPathInefficiencies(segments: MoveSegment[]): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];

    // Look for patterns like: rapid, short cut, rapid, short cut (inefficient zig-zag)
    let patternStart = -1;
    let patternCount = 0;
    let wastedDistance = 0;

    for (let i = 0; i < segments.length - 1; i++) {
      const curr = segments[i];
      const next = segments[i + 1];

      // Pattern: rapid followed by very short cut
      if (curr.type === "rapid" && next.type !== "rapid") {
        const cutDist = this.segmentDistance(next);
        const rapidDist = this.segmentDistance(curr);

        if (cutDist < 5 && rapidDist > cutDist * 2) {
          if (patternStart === -1) {
            patternStart = i;
          }
          patternCount++;
          wastedDistance += rapidDist;
        }
      } else if (patternCount > 3) {
        // End of pattern
        suggestions.push({
          category: "path-inefficiency",
          severity: patternCount > 10 ? "high" : patternCount > 5 ? "medium" : "low",
          message: `Inefficient rapid/cut pattern detected (${patternCount} occurrences)`,
          startSegment: patternStart,
          endSegment: i,
          lineNumbers: this.getLineNumbers(segments, patternStart, i),
          timeSavings: this.distanceToTime(wastedDistance * 0.3, this.config.rapidFeedRate),
          distanceSavings: Math.round(wastedDistance * 0.3 * 100) / 100,
          suggestion: `Consider reordering cuts to minimize rapids`,
          details: {
            patternCount,
            totalRapidDistance: Math.round(wastedDistance),
          },
        });

        patternStart = -1;
        patternCount = 0;
        wastedDistance = 0;
      }
    }

    return suggestions;
  }

  /**
   * Find excessive retract heights
   */
  private findRetractOptimizations(segments: MoveSegment[]): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];
    let highRetracts = 0;
    let totalExcessZ = 0;

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];

      if (seg.type === "rapid") {
        const zMove = seg.to_pos[2] - seg.from_pos[2];
        const excessZ = seg.to_pos[2] - this.config.safeZ;

        // Retract higher than necessary
        if (zMove > 0 && excessZ > 10) {
          highRetracts++;
          totalExcessZ += excessZ;
        }
      }
    }

    if (highRetracts > 5 && totalExcessZ > 50) {
      suggestions.push({
        category: "retract-optimization",
        severity: totalExcessZ > 500 ? "high" : totalExcessZ > 100 ? "medium" : "low",
        message: `${highRetracts} retracts higher than safe Z (${this.config.safeZ}mm)`,
        startSegment: 0,
        endSegment: segments.length - 1,
        lineNumbers: [],
        timeSavings: this.distanceToTime(totalExcessZ * 2, this.config.rapidFeedRate),
        distanceSavings: Math.round(totalExcessZ * 2),
        suggestion: `Consider lowering retract height to safe Z + clearance`,
        details: {
          highRetractCount: highRetracts,
          averageExcess: Math.round(totalExcessZ / highRetracts),
          safeZ: this.config.safeZ,
        },
      });
    }

    return suggestions;
  }

  /**
   * Find linear moves that could be arcs
   */
  private findArcSubstitutions(segments: MoveSegment[]): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];

    // Look for sequences of short linear moves forming curves
    let curveStart = -1;
    let curveSegments = 0;
    let curveLength = 0;

    for (let i = 0; i < segments.length - 1; i++) {
      const seg = segments[i];

      // Skip non-cutting moves
      if (seg.type === "rapid" || seg.type.includes("arc")) {
        if (curveSegments > 8) {
          const arcLength = this.estimateArcLength(segments, curveStart, i - 1);
          const savings = curveLength - arcLength;

          if (savings > 5) {
            suggestions.push({
              category: "arc-substitution",
              severity: "low",
              message: `${curveSegments} linear segments could be single arc`,
              startSegment: curveStart,
              endSegment: i - 1,
              lineNumbers: this.getLineNumbers(segments, curveStart, i - 1),
              timeSavings: this.distanceToTime(savings, segments[curveStart].feed || 1000),
              distanceSavings: Math.round(savings * 100) / 100,
              suggestion: `Consider G2/G3 arc interpolation`,
              details: {
                linearSegments: curveSegments,
                linearLength: Math.round(curveLength * 100) / 100,
                estimatedArcLength: Math.round(arcLength * 100) / 100,
              },
            });
          }
        }

        curveStart = -1;
        curveSegments = 0;
        curveLength = 0;
        continue;
      }

      const dist = this.segmentDistance(seg);

      // Short linear segment at same Z (potential curve)
      if (dist < 3 && Math.abs(seg.from_pos[2] - seg.to_pos[2]) < 0.01) {
        if (curveStart === -1) {
          curveStart = i;
        }
        curveSegments++;
        curveLength += dist;
      } else {
        curveStart = -1;
        curveSegments = 0;
        curveLength = 0;
      }
    }

    return suggestions;
  }

  // ---------------------------------------------------------------------------
  // Helper Methods
  // ---------------------------------------------------------------------------

  private segmentDistance(seg: MoveSegment): number {
    return this.distance3D(seg.from_pos, seg.to_pos);
  }

  private distance3D(a: [number, number, number], b: [number, number, number]): number {
    return Math.sqrt(
      (b[0] - a[0]) ** 2 +
      (b[1] - a[1]) ** 2 +
      (b[2] - a[2]) ** 2
    );
  }

  private distanceToTime(distMm: number, feedMmMin: number): number {
    if (feedMmMin <= 0) return 0;
    return (distMm / feedMmMin) * 60 * 1000; // ms
  }

  private getLineNumbers(segments: MoveSegment[], start: number, end: number): number[] {
    const lines: number[] = [];
    for (let i = start; i <= end && i < segments.length; i++) {
      if (!lines.includes(segments[i].line_number)) {
        lines.push(segments[i].line_number);
      }
    }
    return lines;
  }

  private estimateArcLength(segments: MoveSegment[], start: number, end: number): number {
    // Simplified arc length estimation using chord and sagitta
    const startPos = segments[start].from_pos;
    const endPos = segments[end].to_pos;
    const chordLength = this.distance3D(startPos, endPos);

    // Find midpoint deviation (sagitta)
    const midIdx = Math.floor((start + end) / 2);
    const midPos = segments[midIdx].to_pos;
    const chordMidX = (startPos[0] + endPos[0]) / 2;
    const chordMidY = (startPos[1] + endPos[1]) / 2;
    const sagitta = Math.sqrt(
      (midPos[0] - chordMidX) ** 2 +
      (midPos[1] - chordMidY) ** 2
    );

    // Arc length approximation
    if (sagitta < 0.1) return chordLength;
    const radius = (chordLength * chordLength) / (8 * sagitta) + sagitta / 2;
    const angle = 2 * Math.asin(chordLength / (2 * radius));
    return radius * angle;
  }

  private generateReport(
    suggestions: OptimizationSuggestion[],
    segments: MoveSegment[]
  ): OptimizationReport {
    // Count by category
    const countByCategory: Record<OptimizationCategory, number> = {
      "redundant-rapid": 0,
      "air-cutting": 0,
      "feed-opportunity": 0,
      "path-inefficiency": 0,
      "retract-optimization": 0,
      "arc-substitution": 0,
    };

    let totalTimeSavings = 0;
    let totalDistanceSavings = 0;

    for (const s of suggestions) {
      countByCategory[s.category]++;
      totalTimeSavings += s.timeSavings;
      totalDistanceSavings += s.distanceSavings;
    }

    // Calculate original time if not provided
    let originalTime = this.config.originalTime;
    if (originalTime === 0) {
      originalTime = segments.reduce((sum, s) => sum + s.duration_ms, 0);
    }

    const percentImprovement = originalTime > 0
      ? (totalTimeSavings / originalTime) * 100
      : 0;

    // Generate summary
    let summary: string;
    if (suggestions.length === 0) {
      summary = "No optimization opportunities found - toolpath looks efficient!";
    } else {
      const highCount = suggestions.filter(s => s.severity === "high").length;
      const timeStr = this.formatTime(totalTimeSavings);
      if (highCount > 0) {
        summary = `${highCount} high-impact optimization(s) found - potential ${timeStr} (${percentImprovement.toFixed(1)}%) savings`;
      } else {
        summary = `${suggestions.length} minor optimization(s) found - potential ${timeStr} savings`;
      }
    }

    return {
      suggestions,
      countByCategory,
      totalTimeSavings: Math.round(totalTimeSavings),
      totalDistanceSavings: Math.round(totalDistanceSavings * 100) / 100,
      percentImprovement: Math.round(percentImprovement * 10) / 10,
      summary,
    };
  }

  private formatTime(ms: number): string {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    const mins = Math.floor(ms / 60000);
    const secs = ((ms % 60000) / 1000).toFixed(0);
    return `${mins}m ${secs}s`;
  }
}

// ---------------------------------------------------------------------------
// Factory function
// ---------------------------------------------------------------------------

export function createOptimizer(config?: OptimizerConfig): GcodeOptimizer {
  return new GcodeOptimizer(config);
}

export default GcodeOptimizer;
