/**
 * Toolpath stats presentation logic for ToolpathStats.vue.
 * Wraps analyzeToolpath + chart/grade helpers and formatters.
 */
import { computed, type MaybeRefOrGetter, toValue } from "vue";
import {
  analyzeToolpath,
  formatDistance,
  formatFeed,
  formatPercent,
  type MoveSegment,
  type ToolpathStatistics,
} from "@/util/toolpathAnalytics";

// ---------------------------------------------------------------------------
// Tab UI (ids + labels for presenter)
// ---------------------------------------------------------------------------

export type ToolpathStatsTabId =
  | "overview"
  | "distance"
  | "time"
  | "feed"
  | "depth"
  | "efficiency";

export const TOOLPATH_STATS_TAB_IDS: readonly ToolpathStatsTabId[] = [
  "overview",
  "distance",
  "time",
  "feed",
  "depth",
  "efficiency",
] as const;

export function toolpathStatsTabLabel(tab: ToolpathStatsTabId): string {
  switch (tab) {
    case "overview":
      return "Overview";
    case "distance":
      return "Distance";
    case "time":
      return "Time";
    case "feed":
      return "Feed";
    case "depth":
      return "Z Depth";
    case "efficiency":
      return "Efficiency";
    default:
      return tab;
  }
}

// ---------------------------------------------------------------------------
// Move-type chart (colors + row builder)
// ---------------------------------------------------------------------------

const MOVE_TYPE_CHART_SPECS = [
  { key: "rapid" as const, label: "Rapid", color: "#e74c3c" },
  { key: "linear" as const, label: "Linear", color: "#2ecc71" },
  { key: "arcCW" as const, label: "Arc CW", color: "#3498db" },
  { key: "arcCCW" as const, label: "Arc CCW", color: "#9b59b6" },
] as const;

export interface MoveTypeChartRow {
  label: string;
  value: number;
  percent: number;
  color: string;
}

// ---------------------------------------------------------------------------
// Efficiency score / letter grade
// ---------------------------------------------------------------------------

const EFFICIENCY_WEIGHTS = {
  cuttingEfficiency: 0.4,
  distanceEfficiency: 0.3,
  feedUtilization: 0.2,
  rapidScore: 0.1,
} as const;

export interface EfficiencyGrade {
  grade: string;
  color: string;
  label: string;
}

const EFFICIENCY_GRADE_BANDS: readonly {
  minScore: number;
  grade: string;
  color: string;
  label: string;
}[] = [
  { minScore: 85, grade: "A", color: "#2ecc71", label: "Excellent" },
  { minScore: 70, grade: "B", color: "#27ae60", label: "Good" },
  { minScore: 55, grade: "C", color: "#f39c12", label: "Fair" },
  { minScore: 40, grade: "D", color: "#e67e22", label: "Needs Work" },
];

const EFFICIENCY_GRADE_FALLBACK: EfficiencyGrade = {
  grade: "F",
  color: "#e74c3c",
  label: "Poor",
};

const HISTOGRAM_MIN_BAR_HEIGHT_PX = 4;

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export function useToolpathStats(segments: MaybeRefOrGetter<MoveSegment[]>) {
  const stats = computed<ToolpathStatistics | null>(() => {
    const segs = toValue(segments);
    if (!segs || segs.length === 0) return null;
    return analyzeToolpath(segs);
  });

  const moveTypeChartData = computed<MoveTypeChartRow[]>(() => {
    if (!stats.value) return [];
    const { moveTypes } = stats.value;
    const total = moveTypes.total || 1;
    return MOVE_TYPE_CHART_SPECS.map(({ key, label, color }) => {
      const value = moveTypes[key];
      return {
        label,
        value,
        percent: (value / total) * 100,
        color,
      };
    }).filter((d) => d.value > 0);
  });

  const efficiencyScore = computed(() => {
    if (!stats.value) return 0;
    const { efficiency } = stats.value;
    return (
      efficiency.cuttingEfficiency * EFFICIENCY_WEIGHTS.cuttingEfficiency +
      efficiency.distanceEfficiency * EFFICIENCY_WEIGHTS.distanceEfficiency +
      efficiency.feedUtilization * EFFICIENCY_WEIGHTS.feedUtilization +
      efficiency.rapidScore * EFFICIENCY_WEIGHTS.rapidScore
    ) * 100;
  });

  const efficiencyGrade = computed<EfficiencyGrade>(() => {
    const score = efficiencyScore.value;
    for (const band of EFFICIENCY_GRADE_BANDS) {
      if (score >= band.minScore) {
        return { grade: band.grade, color: band.color, label: band.label };
      }
    }
    return { ...EFFICIENCY_GRADE_FALLBACK };
  });

  const axisTravelMax = computed(() => {
    if (!stats.value) return 1e-9;
    const d = stats.value.distance;
    return Math.max(d.xTravel, d.yTravel, d.zTravel, 1e-9);
  });

  function axisBarWidthStyle(travel: number): { width: string } {
    return {
      width: `${(travel / axisTravelMax.value) * 100}%`,
    };
  }

  const rapidTimePercent = computed(() =>
    stats.value ? 100 - stats.value.time.cutPercent : 0,
  );

  function histogramBarHeightPercent(bucketPercent: number): number {
    return Math.max(HISTOGRAM_MIN_BAR_HEIGHT_PX, bucketPercent);
  }

  function layerBarInlineStyle(z: number): Record<string, string> {
    if (!stats.value || stats.value.zDepth.range === 0) {
      return { width: "0%", background: "#2ecc71" };
    }
    const { max, range } = stats.value.zDepth;
    const w = ((max - z) / range) * 100;
    return {
      width: `${w}%`,
      background: z < 0 ? "#e74c3c" : "#2ecc71",
    };
  }

  return {
    stats,
    moveTypeChartData,
    efficiencyScore,
    efficiencyGrade,
    formatDistance,
    formatFeed,
    formatPercent,
    axisBarWidthStyle,
    rapidTimePercent,
    histogramBarHeightPercent,
    layerBarInlineStyle,
  };
}
