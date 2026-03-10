/**
 * toolpathAnalytics — P5 Toolpath Statistics & Analytics
 *
 * Computes comprehensive statistics from parsed G-code segments:
 * - Distance metrics (total, rapid, cut, by axis)
 * - Time breakdown (rapid, cut, dwell)
 * - Feed rate distribution (min, max, avg, histogram)
 * - Z depth analysis (min, max, layers)
 * - Move type counts (rapid, linear, arc CW/CCW)
 * - Efficiency metrics
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MoveSegment {
  type: "rapid" | "linear" | "cut" | "arc_cw" | "arc_ccw";
  from_pos: [number, number, number];
  to_pos: [number, number, number];
  feed: number;
  duration_ms: number;
  line_number?: number;
  line_text?: string;
}

export interface DistanceStats {
  /** Total distance traveled (mm) */
  total: number;
  /** Rapid move distance (mm) */
  rapid: number;
  /** Cutting move distance (mm) */
  cut: number;
  /** Arc move distance (mm) */
  arc: number;
  /** X-axis travel (mm) */
  xTravel: number;
  /** Y-axis travel (mm) */
  yTravel: number;
  /** Z-axis travel (mm) */
  zTravel: number;
}

export interface TimeStats {
  /** Total time (ms) */
  total: number;
  /** Rapid move time (ms) */
  rapid: number;
  /** Cutting time (ms) */
  cut: number;
  /** Formatted total */
  formatted: string;
  /** Formatted rapid */
  rapidFormatted: string;
  /** Formatted cut */
  cutFormatted: string;
  /** Cut time percentage */
  cutPercent: number;
}

export interface FeedStats {
  /** Minimum feed rate (mm/min) */
  min: number;
  /** Maximum feed rate (mm/min) */
  max: number;
  /** Average feed rate (mm/min) */
  avg: number;
  /** Weighted average by distance */
  weightedAvg: number;
  /** Feed rate histogram buckets */
  histogram: FeedHistogramBucket[];
}

export interface FeedHistogramBucket {
  /** Bucket range start (mm/min) */
  min: number;
  /** Bucket range end (mm/min) */
  max: number;
  /** Segment count in bucket */
  count: number;
  /** Total distance at this feed range */
  distance: number;
  /** Percentage of total segments */
  percent: number;
}

export interface ZDepthStats {
  /** Minimum Z (deepest cut) */
  min: number;
  /** Maximum Z (highest point) */
  max: number;
  /** Total Z range */
  range: number;
  /** Detected depth layers */
  layers: number[];
  /** Layer count */
  layerCount: number;
  /** Deepest cut depth (positive = below zero) */
  maxDepth: number;
}

export interface MoveTypeStats {
  /** Rapid move count */
  rapid: number;
  /** Linear cut count */
  linear: number;
  /** Arc CW count */
  arcCW: number;
  /** Arc CCW count */
  arcCCW: number;
  /** Total move count */
  total: number;
}

export interface EfficiencyStats {
  /** Cutting efficiency (cut time / total time) */
  cuttingEfficiency: number;
  /** Distance efficiency (cut distance / total distance) */
  distanceEfficiency: number;
  /** Average feed utilization (avg feed / max feed) */
  feedUtilization: number;
  /** Rapid optimization score (lower rapid time = better) */
  rapidScore: number;
}

export interface ToolpathStatistics {
  /** Segment count */
  segmentCount: number;
  /** Line count in source G-code */
  lineCount: number;
  /** Distance statistics */
  distance: DistanceStats;
  /** Time statistics */
  time: TimeStats;
  /** Feed rate statistics */
  feed: FeedStats;
  /** Z depth statistics */
  zDepth: ZDepthStats;
  /** Move type counts */
  moveTypes: MoveTypeStats;
  /** Efficiency metrics */
  efficiency: EfficiencyStats;
  /** Computed timestamp */
  computedAt: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function distance3D(
  a: [number, number, number],
  b: [number, number, number],
): number {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const dz = b[2] - a[2];
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

function formatTime(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const totalSecs = ms / 1000;
  if (totalSecs < 60) return `${totalSecs.toFixed(1)}s`;
  const mins = Math.floor(totalSecs / 60);
  const secs = Math.round(totalSecs % 60);
  if (mins < 60) return `${mins}m ${secs}s`;
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  return `${hrs}h ${remMins}m`;
}

function detectLayers(zValues: number[], tolerance = 0.01): number[] {
  if (zValues.length === 0) return [];

  const sorted = [...new Set(zValues)].sort((a, b) => b - a); // high to low
  const layers: number[] = [];

  for (const z of sorted) {
    // Check if this Z is close to an existing layer
    const existing = layers.find(l => Math.abs(l - z) < tolerance);
    if (!existing) {
      layers.push(z);
    }
  }

  return layers.sort((a, b) => b - a); // Return high to low
}

// ---------------------------------------------------------------------------
// Main Analysis Function
// ---------------------------------------------------------------------------

export function analyzeToolpath(segments: MoveSegment[]): ToolpathStatistics {
  // Initialize accumulators
  let totalDist = 0;
  let rapidDist = 0;
  let cutDist = 0;
  let arcDist = 0;
  let xTravel = 0;
  let yTravel = 0;
  let zTravel = 0;

  let totalTime = 0;
  let rapidTime = 0;
  let cutTime = 0;

  const feeds: number[] = [];
  const feedDistances: { feed: number; dist: number }[] = [];
  const zValues: number[] = [];

  let rapidCount = 0;
  let linearCount = 0;
  let arcCWCount = 0;
  let arcCCWCount = 0;

  let maxLineNumber = 0;

  // Process each segment
  for (const seg of segments) {
    const dist = distance3D(seg.from_pos, seg.to_pos);
    const dx = Math.abs(seg.to_pos[0] - seg.from_pos[0]);
    const dy = Math.abs(seg.to_pos[1] - seg.from_pos[1]);
    const dz = Math.abs(seg.to_pos[2] - seg.from_pos[2]);

    totalDist += dist;
    xTravel += dx;
    yTravel += dy;
    zTravel += dz;
    totalTime += seg.duration_ms;

    // Collect Z values for layer detection
    zValues.push(seg.from_pos[2], seg.to_pos[2]);

    // Track line numbers
    if (seg.line_number && seg.line_number > maxLineNumber) {
      maxLineNumber = seg.line_number;
    }

    // Categorize by type
    switch (seg.type) {
      case "rapid":
        rapidDist += dist;
        rapidTime += seg.duration_ms;
        rapidCount++;
        break;
      case "linear":
      case "cut":
        cutDist += dist;
        cutTime += seg.duration_ms;
        linearCount++;
        if (seg.feed > 0) {
          feeds.push(seg.feed);
          feedDistances.push({ feed: seg.feed, dist });
        }
        break;
      case "arc_cw":
        arcDist += dist;
        cutDist += dist;
        cutTime += seg.duration_ms;
        arcCWCount++;
        if (seg.feed > 0) {
          feeds.push(seg.feed);
          feedDistances.push({ feed: seg.feed, dist });
        }
        break;
      case "arc_ccw":
        arcDist += dist;
        cutDist += dist;
        cutTime += seg.duration_ms;
        arcCCWCount++;
        if (seg.feed > 0) {
          feeds.push(seg.feed);
          feedDistances.push({ feed: seg.feed, dist });
        }
        break;
    }
  }

  // Feed statistics
  const minFeed = feeds.length > 0 ? Math.min(...feeds) : 0;
  const maxFeed = feeds.length > 0 ? Math.max(...feeds) : 0;
  const avgFeed = feeds.length > 0 ? feeds.reduce((a, b) => a + b, 0) / feeds.length : 0;

  // Weighted average by distance
  const totalFeedDist = feedDistances.reduce((sum, fd) => sum + fd.dist, 0);
  const weightedAvg = totalFeedDist > 0
    ? feedDistances.reduce((sum, fd) => sum + fd.feed * fd.dist, 0) / totalFeedDist
    : 0;

  // Feed histogram (5 buckets)
  const feedHistogram = buildFeedHistogram(feedDistances, minFeed, maxFeed, 5);

  // Z depth analysis
  const minZ = zValues.length > 0 ? Math.min(...zValues) : 0;
  const maxZ = zValues.length > 0 ? Math.max(...zValues) : 0;
  const layers = detectLayers(zValues);

  // Efficiency calculations
  const cuttingEfficiency = totalTime > 0 ? cutTime / totalTime : 0;
  const distanceEfficiency = totalDist > 0 ? cutDist / totalDist : 0;
  const feedUtilization = maxFeed > 0 ? avgFeed / maxFeed : 0;
  const rapidScore = totalTime > 0 ? 1 - (rapidTime / totalTime) : 1;

  return {
    segmentCount: segments.length,
    lineCount: maxLineNumber,
    distance: {
      total: totalDist,
      rapid: rapidDist,
      cut: cutDist,
      arc: arcDist,
      xTravel,
      yTravel,
      zTravel,
    },
    time: {
      total: totalTime,
      rapid: rapidTime,
      cut: cutTime,
      formatted: formatTime(totalTime),
      rapidFormatted: formatTime(rapidTime),
      cutFormatted: formatTime(cutTime),
      cutPercent: totalTime > 0 ? (cutTime / totalTime) * 100 : 0,
    },
    feed: {
      min: minFeed,
      max: maxFeed,
      avg: avgFeed,
      weightedAvg,
      histogram: feedHistogram,
    },
    zDepth: {
      min: minZ,
      max: maxZ,
      range: maxZ - minZ,
      layers,
      layerCount: layers.length,
      maxDepth: Math.abs(Math.min(0, minZ)),
    },
    moveTypes: {
      rapid: rapidCount,
      linear: linearCount,
      arcCW: arcCWCount,
      arcCCW: arcCCWCount,
      total: segments.length,
    },
    efficiency: {
      cuttingEfficiency,
      distanceEfficiency,
      feedUtilization,
      rapidScore,
    },
    computedAt: Date.now(),
  };
}

function buildFeedHistogram(
  feedDistances: { feed: number; dist: number }[],
  minFeed: number,
  maxFeed: number,
  bucketCount: number,
): FeedHistogramBucket[] {
  if (feedDistances.length === 0 || maxFeed <= minFeed) {
    return [];
  }

  const range = maxFeed - minFeed;
  const bucketSize = range / bucketCount;
  const buckets: FeedHistogramBucket[] = [];

  for (let i = 0; i < bucketCount; i++) {
    buckets.push({
      min: minFeed + i * bucketSize,
      max: minFeed + (i + 1) * bucketSize,
      count: 0,
      distance: 0,
      percent: 0,
    });
  }

  // Fill buckets
  for (const fd of feedDistances) {
    const idx = Math.min(
      Math.floor((fd.feed - minFeed) / bucketSize),
      bucketCount - 1,
    );
    if (idx >= 0 && idx < buckets.length) {
      buckets[idx].count++;
      buckets[idx].distance += fd.dist;
    }
  }

  // Calculate percentages
  const totalCount = feedDistances.length;
  for (const bucket of buckets) {
    bucket.percent = totalCount > 0 ? (bucket.count / totalCount) * 100 : 0;
  }

  return buckets;
}

// ---------------------------------------------------------------------------
// Formatting Helpers
// ---------------------------------------------------------------------------

export function formatDistance(mm: number): string {
  if (mm < 1) return `${mm.toFixed(2)} mm`;
  if (mm < 1000) return `${mm.toFixed(1)} mm`;
  return `${(mm / 1000).toFixed(2)} m`;
}

export function formatFeed(mmMin: number): string {
  return `${Math.round(mmMin)} mm/min`;
}

export function formatPercent(ratio: number): string {
  return `${(ratio * 100).toFixed(1)}%`;
}

export function formatEfficiency(ratio: number): string {
  const pct = ratio * 100;
  if (pct >= 80) return `${pct.toFixed(0)}% (Excellent)`;
  if (pct >= 60) return `${pct.toFixed(0)}% (Good)`;
  if (pct >= 40) return `${pct.toFixed(0)}% (Fair)`;
  return `${pct.toFixed(0)}% (Poor)`;
}

export default analyzeToolpath;
