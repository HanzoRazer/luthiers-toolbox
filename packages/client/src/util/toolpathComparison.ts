/**
 * toolpathComparison — P5 Toolpath Difference Analysis
 *
 * Computes comprehensive differences between two toolpaths:
 * - Path differences (added, removed, modified segments)
 * - Statistics comparison (time, distance, moves)
 * - Deviation analysis (position offsets)
 * - Summary with improvement metrics
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

export interface SegmentDiff {
  /** Index in base toolpath (-1 if added) */
  baseIndex: number;
  /** Index in compare toolpath (-1 if removed) */
  compareIndex: number;
  /** Diff type */
  type: "same" | "modified" | "added" | "removed";
  /** Position deviation (mm) */
  positionDeviation: number;
  /** Feed deviation (mm/min) */
  feedDeviation: number;
  /** Type changed */
  typeChanged: boolean;
  /** Description of change */
  description: string;
}

export interface ToolpathStats {
  /** Total segments */
  segmentCount: number;
  /** Total time (ms) */
  totalTime: number;
  /** Cut distance (mm) */
  cutDistance: number;
  /** Rapid distance (mm) */
  rapidDistance: number;
  /** Arc distance (mm) */
  arcDistance: number;
  /** Linear moves */
  linearMoves: number;
  /** Rapid moves */
  rapidMoves: number;
  /** Arc moves */
  arcMoves: number;
  /** Min Z depth (mm) */
  minZ: number;
  /** Max Z (mm) */
  maxZ: number;
  /** Min feed (mm/min) */
  minFeed: number;
  /** Max feed (mm/min) */
  maxFeed: number;
  /** Average feed (mm/min) */
  avgFeed: number;
}

export interface StatsDiff {
  /** Field name */
  field: string;
  /** Base value */
  baseValue: number;
  /** Compare value */
  compareValue: number;
  /** Absolute difference */
  difference: number;
  /** Percent change */
  percentChange: number;
  /** Is improvement (lower is better for time/distance) */
  isImprovement: boolean;
  /** Formatted base value */
  baseFormatted: string;
  /** Formatted compare value */
  compareFormatted: string;
  /** Formatted difference */
  diffFormatted: string;
}

export interface ComparisonResult {
  /** Base toolpath stats */
  baseStats: ToolpathStats;
  /** Compare toolpath stats */
  compareStats: ToolpathStats;
  /** Statistical differences */
  statsDiffs: StatsDiff[];
  /** Segment differences */
  segmentDiffs: SegmentDiff[];
  /** Summary metrics */
  summary: {
    /** Total segments changed */
    segmentsChanged: number;
    /** Segments added */
    segmentsAdded: number;
    /** Segments removed */
    segmentsRemoved: number;
    /** Segments modified */
    segmentsModified: number;
    /** Time saved (ms, positive = improvement) */
    timeSaved: number;
    /** Time improvement percent */
    timeImprovement: number;
    /** Distance saved (mm) */
    distanceSaved: number;
    /** Overall verdict */
    verdict: "improved" | "degraded" | "similar";
    /** Human-readable summary */
    summaryText: string;
  };
  /** Computed at timestamp */
  computedAt: number;
}

// ---------------------------------------------------------------------------
// Helper Functions
// ---------------------------------------------------------------------------

function distance3D(a: [number, number, number], b: [number, number, number]): number {
  return Math.sqrt(
    (b[0] - a[0]) ** 2 +
    (b[1] - a[1]) ** 2 +
    (b[2] - a[2]) ** 2
  );
}

function positionKey(pos: [number, number, number]): string {
  return `${pos[0].toFixed(3)},${pos[1].toFixed(3)},${pos[2].toFixed(3)}`;
}

function formatTime(ms: number): string {
  const secs = Math.abs(ms) / 1000;
  const mins = Math.floor(secs / 60);
  const s = (secs % 60).toFixed(1);
  const sign = ms < 0 ? "-" : "";
  return `${sign}${mins}:${s.padStart(4, "0")}`;
}

function formatDistance(mm: number): string {
  const abs = Math.abs(mm);
  const sign = mm < 0 ? "-" : "";
  if (abs >= 1000) {
    return `${sign}${(abs / 1000).toFixed(2)}m`;
  }
  return `${sign}${abs.toFixed(1)}mm`;
}

function formatFeed(feed: number): string {
  return `${Math.round(feed)} mm/min`;
}

function formatPercent(val: number): string {
  const sign = val >= 0 ? "+" : "";
  return `${sign}${val.toFixed(1)}%`;
}

// ---------------------------------------------------------------------------
// Stats Computation
// ---------------------------------------------------------------------------

export function computeToolpathStats(segments: MoveSegment[]): ToolpathStats {
  let cutDistance = 0;
  let rapidDistance = 0;
  let arcDistance = 0;
  let linearMoves = 0;
  let rapidMoves = 0;
  let arcMoves = 0;
  let totalTime = 0;
  let minZ = Infinity;
  let maxZ = -Infinity;
  let minFeed = Infinity;
  let maxFeed = 0;
  let feedSum = 0;
  let feedCount = 0;

  for (const seg of segments) {
    const dist = distance3D(seg.from_pos, seg.to_pos);
    totalTime += seg.duration_ms;

    minZ = Math.min(minZ, seg.from_pos[2], seg.to_pos[2]);
    maxZ = Math.max(maxZ, seg.from_pos[2], seg.to_pos[2]);

    if (seg.type === "rapid") {
      rapidDistance += dist;
      rapidMoves++;
    } else if (seg.type === "arc_cw" || seg.type === "arc_ccw") {
      arcDistance += dist;
      cutDistance += dist;
      arcMoves++;
      if (seg.feed > 0) {
        minFeed = Math.min(minFeed, seg.feed);
        maxFeed = Math.max(maxFeed, seg.feed);
        feedSum += seg.feed;
        feedCount++;
      }
    } else {
      // linear or cut
      cutDistance += dist;
      linearMoves++;
      if (seg.feed > 0) {
        minFeed = Math.min(minFeed, seg.feed);
        maxFeed = Math.max(maxFeed, seg.feed);
        feedSum += seg.feed;
        feedCount++;
      }
    }
  }

  return {
    segmentCount: segments.length,
    totalTime,
    cutDistance,
    rapidDistance,
    arcDistance,
    linearMoves,
    rapidMoves,
    arcMoves,
    minZ: isFinite(minZ) ? minZ : 0,
    maxZ: isFinite(maxZ) ? maxZ : 0,
    minFeed: isFinite(minFeed) ? minFeed : 0,
    maxFeed,
    avgFeed: feedCount > 0 ? feedSum / feedCount : 0,
  };
}

// ---------------------------------------------------------------------------
// Diff Analysis
// ---------------------------------------------------------------------------

/**
 * Compare two toolpaths and compute differences
 */
export function compareToolpaths(
  base: MoveSegment[],
  compare: MoveSegment[],
  options: {
    /** Position tolerance for "same" classification (mm) */
    positionTolerance?: number;
    /** Feed tolerance for "same" classification (mm/min) */
    feedTolerance?: number;
  } = {}
): ComparisonResult {
  const { positionTolerance = 0.01, feedTolerance = 1 } = options;

  const baseStats = computeToolpathStats(base);
  const compareStats = computeToolpathStats(compare);

  // Build position lookup for quick matching
  const baseByEndPos = new Map<string, number[]>();
  base.forEach((seg, i) => {
    const key = positionKey(seg.to_pos);
    const existing = baseByEndPos.get(key) || [];
    existing.push(i);
    baseByEndPos.set(key, existing);
  });

  // Compute segment diffs
  const segmentDiffs: SegmentDiff[] = [];
  const matchedBaseIndices = new Set<number>();

  // First pass: find matching segments
  for (let ci = 0; ci < compare.length; ci++) {
    const cSeg = compare[ci];
    const key = positionKey(cSeg.to_pos);
    const candidates = baseByEndPos.get(key) || [];

    let bestMatch = -1;
    let bestDeviation = Infinity;

    for (const bi of candidates) {
      if (matchedBaseIndices.has(bi)) continue;
      const bSeg = base[bi];

      const fromDev = distance3D(bSeg.from_pos, cSeg.from_pos);
      const toDev = distance3D(bSeg.to_pos, cSeg.to_pos);
      const totalDev = fromDev + toDev;

      if (totalDev < bestDeviation) {
        bestDeviation = totalDev;
        bestMatch = bi;
      }
    }

    if (bestMatch >= 0 && bestDeviation < positionTolerance * 2) {
      const bSeg = base[bestMatch];
      matchedBaseIndices.add(bestMatch);

      const posDev = bestDeviation / 2;
      const feedDev = Math.abs((bSeg.feed || 0) - (cSeg.feed || 0));
      const typeChanged = bSeg.type !== cSeg.type;

      const isSame = posDev < positionTolerance && feedDev < feedTolerance && !typeChanged;

      segmentDiffs.push({
        baseIndex: bestMatch,
        compareIndex: ci,
        type: isSame ? "same" : "modified",
        positionDeviation: posDev,
        feedDeviation: feedDev,
        typeChanged,
        description: isSame
          ? "Unchanged"
          : typeChanged
            ? `Type: ${bSeg.type} → ${cSeg.type}`
            : feedDev > feedTolerance
              ? `Feed: ${Math.round(bSeg.feed || 0)} → ${Math.round(cSeg.feed || 0)}`
              : `Position shifted ${posDev.toFixed(3)}mm`,
      });
    } else {
      // Added segment
      segmentDiffs.push({
        baseIndex: -1,
        compareIndex: ci,
        type: "added",
        positionDeviation: 0,
        feedDeviation: 0,
        typeChanged: false,
        description: `Added ${cSeg.type} move`,
      });
    }
  }

  // Second pass: find removed segments
  for (let bi = 0; bi < base.length; bi++) {
    if (!matchedBaseIndices.has(bi)) {
      const bSeg = base[bi];
      segmentDiffs.push({
        baseIndex: bi,
        compareIndex: -1,
        type: "removed",
        positionDeviation: 0,
        feedDeviation: 0,
        typeChanged: false,
        description: `Removed ${bSeg.type} move`,
      });
    }
  }

  // Sort by base index (removed), then compare index (added/modified)
  segmentDiffs.sort((a, b) => {
    if (a.type === "removed" && b.type !== "removed") return -1;
    if (a.type !== "removed" && b.type === "removed") return 1;
    if (a.type === "removed") return a.baseIndex - b.baseIndex;
    return a.compareIndex - b.compareIndex;
  });

  // Compute stats diffs
  const statsDiffs: StatsDiff[] = [];

  const addStatDiff = (
    field: string,
    baseVal: number,
    compareVal: number,
    formatter: (v: number) => string,
    lowerIsBetter: boolean
  ) => {
    const diff = compareVal - baseVal;
    const pct = baseVal !== 0 ? (diff / baseVal) * 100 : 0;
    const isImprovement = lowerIsBetter ? diff < 0 : diff > 0;

    statsDiffs.push({
      field,
      baseValue: baseVal,
      compareValue: compareVal,
      difference: diff,
      percentChange: pct,
      isImprovement,
      baseFormatted: formatter(baseVal),
      compareFormatted: formatter(compareVal),
      diffFormatted: formatPercent(pct),
    });
  };

  addStatDiff("Total Time", baseStats.totalTime, compareStats.totalTime, formatTime, true);
  addStatDiff("Cut Distance", baseStats.cutDistance, compareStats.cutDistance, formatDistance, true);
  addStatDiff("Rapid Distance", baseStats.rapidDistance, compareStats.rapidDistance, formatDistance, true);
  addStatDiff("Segment Count", baseStats.segmentCount, compareStats.segmentCount, v => v.toString(), true);
  addStatDiff("Linear Moves", baseStats.linearMoves, compareStats.linearMoves, v => v.toString(), true);
  addStatDiff("Rapid Moves", baseStats.rapidMoves, compareStats.rapidMoves, v => v.toString(), true);
  addStatDiff("Arc Moves", baseStats.arcMoves, compareStats.arcMoves, v => v.toString(), false);
  addStatDiff("Max Feed", baseStats.maxFeed, compareStats.maxFeed, formatFeed, false);
  addStatDiff("Avg Feed", baseStats.avgFeed, compareStats.avgFeed, formatFeed, false);

  // Compute summary
  const segmentsAdded = segmentDiffs.filter(d => d.type === "added").length;
  const segmentsRemoved = segmentDiffs.filter(d => d.type === "removed").length;
  const segmentsModified = segmentDiffs.filter(d => d.type === "modified").length;
  const segmentsChanged = segmentsAdded + segmentsRemoved + segmentsModified;

  const timeSaved = baseStats.totalTime - compareStats.totalTime;
  const timeImprovement = baseStats.totalTime > 0
    ? (timeSaved / baseStats.totalTime) * 100
    : 0;

  const totalBase = baseStats.cutDistance + baseStats.rapidDistance;
  const totalCompare = compareStats.cutDistance + compareStats.rapidDistance;
  const distanceSaved = totalBase - totalCompare;

  let verdict: "improved" | "degraded" | "similar";
  if (timeImprovement > 2) {
    verdict = "improved";
  } else if (timeImprovement < -2) {
    verdict = "degraded";
  } else {
    verdict = "similar";
  }

  let summaryText: string;
  if (verdict === "improved") {
    summaryText = `✅ Improved: ${formatTime(timeSaved)} faster (${timeImprovement.toFixed(1)}%), ${segmentsRemoved} segments removed`;
  } else if (verdict === "degraded") {
    summaryText = `⚠️ Slower: ${formatTime(-timeSaved)} longer (${Math.abs(timeImprovement).toFixed(1)}% slower)`;
  } else {
    summaryText = `≈ Similar: ${segmentsChanged} segments changed, timing within 2%`;
  }

  return {
    baseStats,
    compareStats,
    statsDiffs,
    segmentDiffs,
    summary: {
      segmentsChanged,
      segmentsAdded,
      segmentsRemoved,
      segmentsModified,
      timeSaved,
      timeImprovement,
      distanceSaved,
      verdict,
      summaryText,
    },
    computedAt: Date.now(),
  };
}

// ---------------------------------------------------------------------------
// Export default
// ---------------------------------------------------------------------------

export default {
  computeToolpathStats,
  compareToolpaths,
};
