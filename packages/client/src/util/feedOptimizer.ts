/**
 * feedOptimizer — P6 Step 14: Advanced Feed Rate Analysis
 *
 * Provides deep analysis of feed rate patterns and optimization hints:
 * - Feed variation analysis (excessive speed changes)
 * - Conservative feed detection (could go faster)
 * - Aggressive feed detection (potential quality issues)
 * - Plunge/entry rate analysis
 * - Feed consistency across similar operations
 * - Material-aware suggestions (when tool info available)
 *
 * Goal: Help users identify feed-related inefficiencies and quality risks
 */

import type { MoveSegment } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type FeedHintSeverity = "critical" | "warning" | "info" | "opportunity";

export type FeedHintCategory =
  | "variation"        // Excessive feed changes
  | "conservative"     // Could go faster
  | "aggressive"       // May cause quality issues
  | "plunge"          // Entry/plunge rate issues
  | "consistency"     // Different feeds for similar ops
  | "transition"      // Poor feed transitions
  | "idle";           // Low engagement at high feed

export interface FeedHint {
  /** Category of hint */
  category: FeedHintCategory;
  /** Severity level */
  severity: FeedHintSeverity;
  /** Human-readable message */
  message: string;
  /** Detailed explanation */
  details: string;
  /** Segment index range */
  segmentRange: [number, number];
  /** G-code line numbers */
  lineNumbers: number[];
  /** Current feed rate */
  currentFeed: number;
  /** Suggested feed rate (if applicable) */
  suggestedFeed?: number;
  /** Estimated time impact (ms, positive = savings, negative = cost) */
  timeImpact: number;
  /** Confidence score 0-1 */
  confidence: number;
}

export interface FeedStats {
  /** Minimum feed used (excluding rapids) */
  minFeed: number;
  /** Maximum feed used */
  maxFeed: number;
  /** Average feed rate */
  avgFeed: number;
  /** Median feed rate */
  medianFeed: number;
  /** Standard deviation */
  stdDev: number;
  /** Number of unique feed values */
  uniqueFeeds: number;
  /** Number of feed changes */
  feedChanges: number;
  /** Feed changes per minute */
  changesPerMinute: number;
  /** Time at each feed bracket */
  feedDistribution: FeedBracket[];
}

export interface FeedBracket {
  /** Feed range label */
  label: string;
  /** Min feed in bracket */
  min: number;
  /** Max feed in bracket */
  max: number;
  /** Time spent in bracket (ms) */
  timeMs: number;
  /** Percentage of total cut time */
  percent: number;
  /** Number of segments */
  segmentCount: number;
}

export interface FeedAnalysisReport {
  /** Overall feed efficiency score (0-100) */
  efficiencyScore: number;
  /** Feed statistics */
  stats: FeedStats;
  /** Optimization hints */
  hints: FeedHint[];
  /** Estimated potential time savings (ms) */
  potentialSavings: number;
  /** Summary message */
  summary: string;
  /** Feed timeline for visualization */
  timeline: FeedTimelinePoint[];
}

export interface FeedTimelinePoint {
  /** Time offset (ms) */
  timeMs: number;
  /** Feed rate */
  feed: number;
  /** Segment index */
  segmentIndex: number;
  /** Is this a feed change? */
  isChange: boolean;
}

export interface FeedOptimizerConfig {
  /** Default safe feed for unknown material (mm/min) */
  defaultSafeFeed?: number;
  /** Maximum recommended feed (mm/min) */
  maxRecommendedFeed?: number;
  /** Minimum practical feed (mm/min) */
  minPracticalFeed?: number;
  /** Threshold for "excessive" variation (% change) */
  variationThreshold?: number;
  /** Plunge feed should be X% of cut feed */
  plungeRatio?: number;
  /** Tool diameter for chip load calculations */
  toolDiameter?: number;
  /** Flute count for chip load calculations */
  fluteCount?: number;
  /** Spindle RPM for chip load calculations */
  spindleRpm?: number;
}

// ---------------------------------------------------------------------------
// FeedOptimizer Class
// ---------------------------------------------------------------------------

export class FeedOptimizer {
  private config: Required<FeedOptimizerConfig>;

  constructor(config: FeedOptimizerConfig = {}) {
    this.config = {
      defaultSafeFeed: config.defaultSafeFeed ?? 1000,
      maxRecommendedFeed: config.maxRecommendedFeed ?? 5000,
      minPracticalFeed: config.minPracticalFeed ?? 50,
      variationThreshold: config.variationThreshold ?? 30,
      plungeRatio: config.plungeRatio ?? 0.5,
      toolDiameter: config.toolDiameter ?? 6,
      fluteCount: config.fluteCount ?? 2,
      spindleRpm: config.spindleRpm ?? 18000,
    };
  }

  /**
   * Analyze feed patterns in segments
   */
  analyze(segments: MoveSegment[]): FeedAnalysisReport {
    const cutSegments = segments.filter(s => s.type !== "rapid");

    if (cutSegments.length === 0) {
      return this.emptyReport();
    }

    const stats = this.computeStats(cutSegments);
    const timeline = this.buildTimeline(segments);
    const hints: FeedHint[] = [];

    // Run all analyzers
    hints.push(...this.analyzeVariation(segments, stats));
    hints.push(...this.analyzeConservativeFeeds(segments, stats));
    hints.push(...this.analyzeAggressiveFeeds(segments, stats));
    hints.push(...this.analyzePlungeRates(segments));
    hints.push(...this.analyzeConsistency(segments));
    hints.push(...this.analyzeTransitions(segments));

    // Sort by severity and impact
    hints.sort((a, b) => {
      const severityOrder = { critical: 0, warning: 1, opportunity: 2, info: 3 };
      if (severityOrder[a.severity] !== severityOrder[b.severity]) {
        return severityOrder[a.severity] - severityOrder[b.severity];
      }
      return Math.abs(b.timeImpact) - Math.abs(a.timeImpact);
    });

    const potentialSavings = hints
      .filter(h => h.timeImpact > 0)
      .reduce((sum, h) => sum + h.timeImpact, 0);

    const efficiencyScore = this.calculateEfficiencyScore(stats, hints);

    return {
      efficiencyScore,
      stats,
      hints,
      potentialSavings: Math.round(potentialSavings),
      summary: this.generateSummary(efficiencyScore, hints, potentialSavings),
      timeline,
    };
  }

  // ---------------------------------------------------------------------------
  // Statistics
  // ---------------------------------------------------------------------------

  private computeStats(cutSegments: MoveSegment[]): FeedStats {
    const feeds = cutSegments.map(s => s.feed).filter(f => f > 0);

    if (feeds.length === 0) {
      return this.emptyStats();
    }

    const sorted = [...feeds].sort((a, b) => a - b);
    const sum = feeds.reduce((a, b) => a + b, 0);
    const avg = sum / feeds.length;
    const median = sorted[Math.floor(sorted.length / 2)];

    const variance = feeds.reduce((sum, f) => sum + (f - avg) ** 2, 0) / feeds.length;
    const stdDev = Math.sqrt(variance);

    const uniqueFeeds = new Set(feeds).size;

    // Count feed changes
    let feedChanges = 0;
    let prevFeed = 0;
    for (const seg of cutSegments) {
      if (seg.feed !== prevFeed && prevFeed !== 0) {
        feedChanges++;
      }
      prevFeed = seg.feed;
    }

    const totalTimeMs = cutSegments.reduce((sum, s) => sum + s.duration_ms, 0);
    const changesPerMinute = totalTimeMs > 0
      ? (feedChanges / totalTimeMs) * 60000
      : 0;

    // Build feed distribution brackets
    const brackets = this.buildFeedBrackets(cutSegments);

    return {
      minFeed: Math.round(sorted[0]),
      maxFeed: Math.round(sorted[sorted.length - 1]),
      avgFeed: Math.round(avg),
      medianFeed: Math.round(median),
      stdDev: Math.round(stdDev),
      uniqueFeeds,
      feedChanges,
      changesPerMinute: Math.round(changesPerMinute * 10) / 10,
      feedDistribution: brackets,
    };
  }

  private buildFeedBrackets(segments: MoveSegment[]): FeedBracket[] {
    const brackets: FeedBracket[] = [
      { label: "Very Slow", min: 0, max: 200, timeMs: 0, percent: 0, segmentCount: 0 },
      { label: "Slow", min: 200, max: 500, timeMs: 0, percent: 0, segmentCount: 0 },
      { label: "Medium", min: 500, max: 1500, timeMs: 0, percent: 0, segmentCount: 0 },
      { label: "Fast", min: 1500, max: 3000, timeMs: 0, percent: 0, segmentCount: 0 },
      { label: "Very Fast", min: 3000, max: Infinity, timeMs: 0, percent: 0, segmentCount: 0 },
    ];

    let totalTime = 0;
    for (const seg of segments) {
      if (seg.type === "rapid") continue;
      totalTime += seg.duration_ms;

      for (const bracket of brackets) {
        if (seg.feed >= bracket.min && seg.feed < bracket.max) {
          bracket.timeMs += seg.duration_ms;
          bracket.segmentCount++;
          break;
        }
      }
    }

    for (const bracket of brackets) {
      bracket.percent = totalTime > 0
        ? Math.round((bracket.timeMs / totalTime) * 1000) / 10
        : 0;
    }

    return brackets.filter(b => b.segmentCount > 0);
  }

  // ---------------------------------------------------------------------------
  // Analyzers
  // ---------------------------------------------------------------------------

  private analyzeVariation(segments: MoveSegment[], stats: FeedStats): FeedHint[] {
    const hints: FeedHint[] = [];

    // Check overall variation
    const cv = stats.stdDev / stats.avgFeed * 100; // Coefficient of variation

    if (cv > 50) {
      hints.push({
        category: "variation",
        severity: "warning",
        message: "High feed rate variation detected",
        details: `Feed varies from F${stats.minFeed} to F${stats.maxFeed} (CV: ${cv.toFixed(0)}%). ` +
          `Constant acceleration/deceleration wastes time and may affect surface finish.`,
        segmentRange: [0, segments.length - 1],
        lineNumbers: [],
        currentFeed: stats.avgFeed,
        timeImpact: 0, // Hard to quantify
        confidence: 0.7,
      });
    }

    // Check for rapid feed oscillation
    let oscillations = 0;
    let lastDirection = 0; // 1 = up, -1 = down
    let oscillationStart = -1;

    for (let i = 1; i < segments.length; i++) {
      const prev = segments[i - 1];
      const curr = segments[i];

      if (curr.type === "rapid" || prev.type === "rapid") continue;

      const change = curr.feed - prev.feed;
      const direction = change > 0 ? 1 : change < 0 ? -1 : 0;

      if (direction !== 0 && direction !== lastDirection && lastDirection !== 0) {
        if (oscillationStart === -1) oscillationStart = i - 2;
        oscillations++;
      }
      lastDirection = direction;
    }

    if (oscillations > 10) {
      hints.push({
        category: "variation",
        severity: "info",
        message: `Feed oscillates ${oscillations} times`,
        details: `Frequent feed changes cause machine vibration and inefficiency. ` +
          `Consider smoothing feed transitions.`,
        segmentRange: [oscillationStart, segments.length - 1],
        lineNumbers: [],
        currentFeed: stats.avgFeed,
        timeImpact: oscillations * 50, // Rough estimate
        confidence: 0.5,
      });
    }

    return hints;
  }

  private analyzeConservativeFeeds(segments: MoveSegment[], stats: FeedStats): FeedHint[] {
    const hints: FeedHint[] = [];

    // Look for long segments at very low feed
    let slowStart = -1;
    let slowTime = 0;
    const SLOW_THRESHOLD = 300;

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];

      if (seg.type === "rapid") {
        if (slowStart !== -1 && slowTime > 5000) {
          hints.push(this.createConservativeHint(segments, slowStart, i - 1, slowTime));
        }
        slowStart = -1;
        slowTime = 0;
        continue;
      }

      if (seg.feed < SLOW_THRESHOLD) {
        if (slowStart === -1) slowStart = i;
        slowTime += seg.duration_ms;
      } else {
        if (slowStart !== -1 && slowTime > 5000) {
          hints.push(this.createConservativeHint(segments, slowStart, i - 1, slowTime));
        }
        slowStart = -1;
        slowTime = 0;
      }
    }

    // Check final segment range
    if (slowStart !== -1 && slowTime > 5000) {
      hints.push(this.createConservativeHint(segments, slowStart, segments.length - 1, slowTime));
    }

    // Check if overall median is well below safe threshold
    if (stats.medianFeed < this.config.defaultSafeFeed * 0.5) {
      const potential = this.config.defaultSafeFeed * 0.8;
      const totalCutTime = segments
        .filter(s => s.type !== "rapid")
        .reduce((sum, s) => sum + s.duration_ms, 0);
      const savings = totalCutTime * (1 - stats.medianFeed / potential);

      hints.push({
        category: "conservative",
        severity: "opportunity",
        message: "Overall feed rates are conservative",
        details: `Median feed F${stats.medianFeed} is well below typical safe rates. ` +
          `Consider testing higher feeds if material and tooling allow.`,
        segmentRange: [0, segments.length - 1],
        lineNumbers: [],
        currentFeed: stats.medianFeed,
        suggestedFeed: Math.round(potential),
        timeImpact: Math.round(savings * 0.3), // Conservative estimate
        confidence: 0.4,
      });
    }

    return hints;
  }

  private createConservativeHint(
    segments: MoveSegment[],
    start: number,
    end: number,
    slowTime: number
  ): FeedHint {
    const avgFeed = segments
      .slice(start, end + 1)
      .filter(s => s.type !== "rapid")
      .reduce((sum, s, _, arr) => sum + s.feed / arr.length, 0);

    const suggestedFeed = Math.min(avgFeed * 2, this.config.defaultSafeFeed);
    const savings = slowTime * (1 - avgFeed / suggestedFeed);

    return {
      category: "conservative",
      severity: savings > 10000 ? "warning" : "opportunity",
      message: `Very slow feed for ${(slowTime / 1000).toFixed(1)}s`,
      details: `Feed F${Math.round(avgFeed)} for extended period. ` +
        `Could potentially increase to F${Math.round(suggestedFeed)} for ~${(savings / 1000).toFixed(1)}s savings.`,
      segmentRange: [start, end],
      lineNumbers: this.getLineNumbers(segments, start, end),
      currentFeed: Math.round(avgFeed),
      suggestedFeed: Math.round(suggestedFeed),
      timeImpact: Math.round(savings),
      confidence: 0.6,
    };
  }

  private analyzeAggressiveFeeds(segments: MoveSegment[], stats: FeedStats): FeedHint[] {
    const hints: FeedHint[] = [];

    // Look for feeds that exceed recommended max
    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];

      if (seg.type === "rapid") continue;

      if (seg.feed > this.config.maxRecommendedFeed) {
        hints.push({
          category: "aggressive",
          severity: "warning",
          message: `Very high feed F${seg.feed}`,
          details: `Feed exceeds typical recommended maximum of F${this.config.maxRecommendedFeed}. ` +
            `Verify this is intentional and tooling can handle it.`,
          segmentRange: [i, i],
          lineNumbers: [seg.line_number],
          currentFeed: seg.feed,
          suggestedFeed: this.config.maxRecommendedFeed,
          timeImpact: -(seg.duration_ms * 0.2), // Would take longer at lower feed
          confidence: 0.5,
        });
      }
    }

    // Check for sudden large feed increases
    for (let i = 1; i < segments.length; i++) {
      const prev = segments[i - 1];
      const curr = segments[i];

      if (curr.type === "rapid" || prev.type === "rapid") continue;

      const increase = ((curr.feed - prev.feed) / prev.feed) * 100;

      if (increase > 100 && curr.feed > 1000) {
        hints.push({
          category: "aggressive",
          severity: "info",
          message: `Feed jumps ${increase.toFixed(0)}% at line ${curr.line_number}`,
          details: `Sudden increase from F${prev.feed} to F${curr.feed}. ` +
            `May cause tool deflection or chatter on entry.`,
          segmentRange: [i - 1, i],
          lineNumbers: [prev.line_number, curr.line_number],
          currentFeed: curr.feed,
          timeImpact: 0,
          confidence: 0.4,
        });
      }
    }

    return hints;
  }

  private analyzePlungeRates(segments: MoveSegment[]): FeedHint[] {
    const hints: FeedHint[] = [];

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];

      if (seg.type === "rapid") continue;

      const zDrop = seg.from_pos[2] - seg.to_pos[2];
      const xyMove = Math.sqrt(
        (seg.to_pos[0] - seg.from_pos[0]) ** 2 +
        (seg.to_pos[1] - seg.from_pos[1]) ** 2
      );

      // Pure or near-pure plunge (Z dominant)
      if (zDrop > 1 && zDrop > xyMove * 2) {
        const idealPlungeFeed = this.config.defaultSafeFeed * this.config.plungeRatio;

        if (seg.feed > idealPlungeFeed * 1.5) {
          hints.push({
            category: "plunge",
            severity: "warning",
            message: `Fast plunge at F${seg.feed}`,
            details: `Plunging ${zDrop.toFixed(1)}mm at high feed. ` +
              `Recommended plunge feed: F${Math.round(idealPlungeFeed)} (${Math.round(this.config.plungeRatio * 100)}% of cut feed).`,
            segmentRange: [i, i],
            lineNumbers: [seg.line_number],
            currentFeed: seg.feed,
            suggestedFeed: Math.round(idealPlungeFeed),
            timeImpact: 0, // Quality issue, not time
            confidence: 0.7,
          });
        } else if (seg.feed < idealPlungeFeed * 0.3) {
          const savings = seg.duration_ms * (1 - seg.feed / idealPlungeFeed);
          hints.push({
            category: "plunge",
            severity: "opportunity",
            message: `Very slow plunge F${seg.feed}`,
            details: `Plunge feed is overly conservative. Could safely increase to F${Math.round(idealPlungeFeed)}.`,
            segmentRange: [i, i],
            lineNumbers: [seg.line_number],
            currentFeed: seg.feed,
            suggestedFeed: Math.round(idealPlungeFeed),
            timeImpact: Math.round(savings),
            confidence: 0.6,
          });
        }
      }
    }

    return hints;
  }

  private analyzeConsistency(segments: MoveSegment[]): FeedHint[] {
    const hints: FeedHint[] = [];

    // Group segments by Z level and move type
    const zLevels = new Map<number, { feeds: number[], segments: number[] }>();

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      if (seg.type === "rapid") continue;

      const zLevel = Math.round(seg.to_pos[2] * 10) / 10; // Round to 0.1mm

      if (!zLevels.has(zLevel)) {
        zLevels.set(zLevel, { feeds: [], segments: [] });
      }

      const level = zLevels.get(zLevel)!;
      level.feeds.push(seg.feed);
      level.segments.push(i);
    }

    // Check for inconsistent feeds at same depth
    for (const [z, data] of zLevels) {
      if (data.feeds.length < 5) continue;

      const uniqueFeeds = new Set(data.feeds);
      if (uniqueFeeds.size > 3) {
        const sorted = [...data.feeds].sort((a, b) => a - b);
        const range = sorted[sorted.length - 1] - sorted[0];
        const median = sorted[Math.floor(sorted.length / 2)];

        if (range > median * 0.5) {
          hints.push({
            category: "consistency",
            severity: "info",
            message: `Inconsistent feeds at Z=${z}mm`,
            details: `${uniqueFeeds.size} different feed rates used at same depth ` +
              `(F${sorted[0]} to F${sorted[sorted.length - 1]}). Consider standardizing.`,
            segmentRange: [data.segments[0], data.segments[data.segments.length - 1]],
            lineNumbers: [],
            currentFeed: median,
            timeImpact: 0,
            confidence: 0.3,
          });
        }
      }
    }

    return hints;
  }

  private analyzeTransitions(segments: MoveSegment[]): FeedHint[] {
    const hints: FeedHint[] = [];

    // Look for rapid -> cut without feed ramp-up
    for (let i = 1; i < segments.length; i++) {
      const prev = segments[i - 1];
      const curr = segments[i];

      if (prev.type === "rapid" && curr.type !== "rapid" && curr.feed > 2000) {
        hints.push({
          category: "transition",
          severity: "info",
          message: `High feed immediately after rapid`,
          details: `Cutting at F${curr.feed} immediately after rapid positioning. ` +
            `Consider a lead-in or reduced entry feed for better surface finish.`,
          segmentRange: [i, i],
          lineNumbers: [curr.line_number],
          currentFeed: curr.feed,
          timeImpact: 0,
          confidence: 0.3,
        });
      }
    }

    return hints;
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  private buildTimeline(segments: MoveSegment[]): FeedTimelinePoint[] {
    const timeline: FeedTimelinePoint[] = [];
    let timeMs = 0;
    let prevFeed = 0;

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      const feed = seg.type === "rapid" ? 0 : seg.feed;
      const isChange = feed !== prevFeed;

      timeline.push({
        timeMs,
        feed,
        segmentIndex: i,
        isChange,
      });

      timeMs += seg.duration_ms;
      prevFeed = feed;
    }

    return timeline;
  }

  private getLineNumbers(segments: MoveSegment[], start: number, end: number): number[] {
    const lines: number[] = [];
    for (let i = start; i <= end && i < segments.length; i++) {
      if (!lines.includes(segments[i].line_number)) {
        lines.push(segments[i].line_number);
      }
    }
    return lines.slice(0, 5); // Limit to first 5
  }

  private calculateEfficiencyScore(stats: FeedStats, hints: FeedHint[]): number {
    let score = 100;

    // Deduct for critical/warning hints
    const criticalCount = hints.filter(h => h.severity === "critical").length;
    const warningCount = hints.filter(h => h.severity === "warning").length;

    score -= criticalCount * 15;
    score -= warningCount * 5;

    // Deduct for high variation
    const cv = stats.stdDev / stats.avgFeed * 100;
    if (cv > 50) score -= 10;
    if (cv > 100) score -= 10;

    // Deduct for excessive feed changes
    if (stats.changesPerMinute > 10) score -= 5;
    if (stats.changesPerMinute > 20) score -= 5;

    // Deduct if mostly at very slow feeds
    const slowBracket = stats.feedDistribution.find(b => b.label === "Very Slow");
    if (slowBracket && slowBracket.percent > 30) score -= 10;

    return Math.max(0, Math.min(100, Math.round(score)));
  }

  private generateSummary(score: number, hints: FeedHint[], savings: number): string {
    if (hints.length === 0) {
      return "Feed rates look well-optimized!";
    }

    const critical = hints.filter(h => h.severity === "critical").length;
    const warnings = hints.filter(h => h.severity === "warning").length;
    const opportunities = hints.filter(h => h.severity === "opportunity").length;

    if (critical > 0) {
      return `${critical} critical feed issue(s) detected that may affect quality or safety.`;
    }

    if (warnings > 0) {
      const savingsStr = savings > 0 ? ` Potential ${(savings / 1000).toFixed(1)}s savings.` : "";
      return `${warnings} feed warning(s) found.${savingsStr}`;
    }

    if (opportunities > 0) {
      const savingsStr = savings > 0 ? ` ~${(savings / 1000).toFixed(1)}s potential savings.` : "";
      return `${opportunities} optimization opportunit${opportunities > 1 ? "ies" : "y"} identified.${savingsStr}`;
    }

    return `Score: ${score}/100. ${hints.length} minor suggestion(s).`;
  }

  private emptyReport(): FeedAnalysisReport {
    return {
      efficiencyScore: 100,
      stats: this.emptyStats(),
      hints: [],
      potentialSavings: 0,
      summary: "No cutting moves to analyze.",
      timeline: [],
    };
  }

  private emptyStats(): FeedStats {
    return {
      minFeed: 0,
      maxFeed: 0,
      avgFeed: 0,
      medianFeed: 0,
      stdDev: 0,
      uniqueFeeds: 0,
      feedChanges: 0,
      changesPerMinute: 0,
      feedDistribution: [],
    };
  }
}

// ---------------------------------------------------------------------------
// Factory & Export
// ---------------------------------------------------------------------------

export function createFeedOptimizer(config?: FeedOptimizerConfig): FeedOptimizer {
  return new FeedOptimizer(config);
}

export default FeedOptimizer;
