/**
 * Toolpath Player Store — P1-P3 Enhanced
 *
 * Owns all playback state for the animated G-code toolpath visualizer.
 * The canvas component is a pure renderer that reads from this store.
 *
 * P1 enhancements: Memory management, progress tracking, downsampling
 * P2 enhancements: Caching layer for repeated simulations
 * P3 enhancements: M-code tracking in segments
 *
 * 2026-05-30 fidelity fixes (TOOLPATH_ANIMATION_AUDIT):
 * - F-X2: cumulative-time search is a strict lower bound; step/seek/jump land
 *   on segment starts consistently.
 * - F-X3: downsampling conserves total cycle time (merges runs instead of
 *   dropping durations).
 * - F-Y1: loadGcode forwards `units` to the backend.
 * - F-Y2: cache key carries a version tag so a backend change invalidates
 *   stale sessionStorage entries.
 * - F-Z1/F-Z2: `warnings` and `tools` from the response are kept and exposed.
 * - F-Z6: cache eviction is least-recently-written, not arbitrary.
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { simulate } from "@/sdk/endpoints/cam/simulate";
import type {
  MoveSegment,
  SimulateBounds,
  SimulateWarnings,
  ToolsInfo,
} from "@/sdk/endpoints/cam/simulate";
import { MeasurementTool, type Measurement, type Point3D } from "@/util/measurementTool";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const MAX_SEGMENTS = 100_000;
const WARNING_THRESHOLD = 75_000;
const CACHE_PREFIX = "gcode-sim-";
const MAX_CACHE_ENTRIES = 20;
/** Bump when backend simulation semantics change, to invalidate stale caches. */
const SIM_VERSION = "2026-05-30";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MemoryInfo {
  segmentCount: number;
  estimatedMB: number;
  isWarning: boolean;
  isCritical: boolean;
}

export interface ParseProgress {
  percent: number;
  stage: "idle" | "uploading" | "simulating" | "complete";
}

export interface LoadOptions {
  units?: "mm" | "inch";
  rapid_mm_min?: number;
  default_feed_mm_min?: number;
  arc_resolution_deg?: number;
  accel_mm_s2?: number;
  junction_deviation_mm?: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function lerp3(
  a: [number, number, number],
  b: [number, number, number],
  t: number,
): [number, number, number] {
  return [
    a[0] + (b[0] - a[0]) * t,
    a[1] + (b[1] - a[1]) * t,
    a[2] + (b[2] - a[2]) * t,
  ];
}

/**
 * Strict lower-bound search over the cumulative end-time array.
 * Returns the index of the segment active at `timeMs`, where segment i owns the
 * half-open interval [cumulative[i-1], cumulative[i]). At an exact boundary the
 * search returns the *next* segment (its start), which is what step/seek/jump
 * rely on. (F-X2)
 */
export function binarySearchCumulative(cumulative: number[], timeMs: number): number {
  if (cumulative.length === 0) return -1;
  let lo = 0;
  let hi = cumulative.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (cumulative[mid] <= timeMs) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

/**
 * Adaptive downsample for very large programs. Rapids and dwells are kept whole
 * (they carry distinct timing/styling); runs of consecutive cut/arc segments are
 * merged into one segment whose duration is the *sum* of the run and whose
 * endpoint is the run's last point. This conserves total cycle time and path
 * endpoints — the previous modulo-stride version silently dropped durations. (F-X3)
 */
export function downsampleSegments(
  segments: MoveSegment[],
  target: number,
): MoveSegment[] {
  if (segments.length <= target || target <= 0) return segments;
  const n = segments.length;
  const step = Math.max(2, Math.ceil(n / target));
  const result: MoveSegment[] = [];
  let i = 0;
  while (i < n) {
    const seg = segments[i];
    if (seg.type === "rapid" || seg.type === "dwell") {
      result.push(seg);
      i++;
      continue;
    }
    let j = i;
    let dur = 0;
    let lastIdx = i;
    while (
      j < n &&
      j - i < step &&
      segments[j].type !== "rapid" &&
      segments[j].type !== "dwell"
    ) {
      dur += segments[j].duration_ms;
      lastIdx = j;
      j++;
    }
    result.push({ ...seg, to_pos: segments[lastIdx].to_pos, duration_ms: dur });
    i = j;
  }
  return result;
}

/** Simple FNV-1a 32-bit hash for cache keys (sync, no crypto). */
function fnv1a(str: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(36);
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

// eslint-disable-next-line max-lines-per-function -- Pinia composition store; logic extracted into helpers above
export const useToolpathPlayerStore = defineStore("toolpathPlayer", () => {
  // ── Raw data ─────────────────────────────────────────────────────────────
  const segments = ref<MoveSegment[]>([]);
  const fullSegments = ref<MoveSegment[]>([]);
  const bounds = ref<SimulateBounds | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ── Fidelity signals from the backend (F-Z1 / F-Z2) ──────────────────────
  const warnings = ref<SimulateWarnings | null>(null);
  const tools = ref<ToolsInfo | null>(null);

  /** True when the simulation could not faithfully model part of the program. */
  const hasFidelityWarnings = computed<boolean>(() => {
    const w = warnings.value;
    if (!w) return false;
    return (
      w.unsupported_g.length > 0 ||
      w.unsupported_m.length > 0 ||
      w.approx_cycles.length > 0 ||
      w.degenerate_arcs > 0 ||
      w.truncated
    );
  });

  // ── Progress tracking (P1) ───────────────────────────────────────────────
  const parseProgress = ref<ParseProgress>({ percent: 0, stage: "idle" });

  // ── Memory info (P1) ─────────────────────────────────────────────────────
  const memoryInfo = computed<MemoryInfo>(() => {
    const count = fullSegments.value.length;
    const mb = (count * 200) / (1024 * 1024);
    return {
      segmentCount: count,
      estimatedMB: mb,
      isWarning: count > WARNING_THRESHOLD,
      isCritical: count > MAX_SEGMENTS,
    };
  });

  // ── Playback state ────────────────────────────────────────────────────────
  const playState = ref<"idle" | "playing" | "paused">("idle");
  const currentTimeMs = ref(0);
  const speed = ref(1);

  // ── P5: Segment selection for G-code line sync ───────────────────────────
  const selectedSegmentIndex = ref<number | null>(null);
  const sourceGcode = ref<string>("");

  // ── P5: Measurement tool ────────────────────────────────────────────────
  const measureMode = ref(false);
  const measureTool = new MeasurementTool();
  const measurements = ref<Measurement[]>([]);
  const pendingMeasureStart = ref<Point3D | null>(null);

  // ── RAF internals ────────────────────────────────────────────────────────
  let _rafHandle = 0;
  let _lastTimestamp = 0;
  let _cumulativeMs: number[] = [];

  function _rebuildCumulative(): void {
    _cumulativeMs = [];
    let acc = 0;
    for (const seg of segments.value) {
      acc += seg.duration_ms;
      _cumulativeMs.push(acc);
    }
  }

  /** Start time of segment `idx` (0 for the first). */
  function _segmentStart(idx: number): number {
    return idx > 0 ? (_cumulativeMs[idx - 1] ?? 0) : 0;
  }

  // ── Computed ──────────────────────────────────────────────────────────────

  const totalDurationMs = computed<number>(() =>
    segments.value.reduce((sum, s) => sum + s.duration_ms, 0),
  );

  const progress = computed<number>(() =>
    totalDurationMs.value > 0
      ? Math.min(currentTimeMs.value / totalDurationMs.value, 1)
      : 0,
  );

  const currentSegmentIndex = computed<number>(() => {
    if (segments.value.length === 0) return -1;
    return binarySearchCumulative(_cumulativeMs, currentTimeMs.value);
  });

  const toolPosition = computed<[number, number, number]>(() => {
    const idx = currentSegmentIndex.value;
    if (idx < 0 || segments.value.length === 0) return [0, 0, 0];

    const seg = segments.value[idx];
    const segStart = _segmentStart(idx);
    const segDuration = seg.duration_ms;

    const t =
      segDuration > 0
        ? Math.min(Math.max((currentTimeMs.value - segStart) / segDuration, 0), 1)
        : 0;

    return lerp3(
      seg.from_pos as [number, number, number],
      seg.to_pos as [number, number, number],
      t,
    );
  });

  const currentSegment = computed<MoveSegment | null>(
    () => segments.value[currentSegmentIndex.value] ?? null,
  );

  // ── P5: Selected segment computed ──────────────────────────────────────────
  const selectedSegment = computed<MoveSegment | null>(
    () => selectedSegmentIndex.value !== null
      ? segments.value[selectedSegmentIndex.value] ?? null
      : null,
  );

  /** Extract G-code source line for a segment (uses line_number if available) */
  const selectedGcodeLine = computed<{ lineNumber: number; text: string } | null>(() => {
    const seg = selectedSegment.value;
    if (!seg || !sourceGcode.value) return null;

    const lineNum = (seg as MoveSegment & { line_number?: number }).line_number;
    if (lineNum === undefined) return null;

    const lines = sourceGcode.value.split("\n");
    if (lineNum < 1 || lineNum > lines.length) return null;

    return {
      lineNumber: lineNum,
      text: lines[lineNum - 1] || "",
    };
  });

  // ── RAF animation tick ────────────────────────────────────────────────────

  function _tick(timestamp: number): void {
    if (playState.value !== "playing") return;

    if (_lastTimestamp > 0) {
      // Clamp wall delta so an NTP correction / tab-resume can't skip the path.
      const wallDelta = Math.min(timestamp - _lastTimestamp, 250);
      const simDelta = wallDelta * speed.value;
      const next = currentTimeMs.value + simDelta;

      if (next >= totalDurationMs.value) {
        currentTimeMs.value = totalDurationMs.value;
        playState.value = "paused";
        _lastTimestamp = 0;
        return;
      }
      currentTimeMs.value = next;
    }

    _lastTimestamp = timestamp;
    _rafHandle = requestAnimationFrame(_tick);
  }

  // ── Cache helpers (P2) ────────────────────────────────────────────────────

  function _cacheKey(gcode: string, opts?: Record<string, unknown>): string {
    return CACHE_PREFIX + SIM_VERSION + "-" + fnv1a(gcode + JSON.stringify(opts ?? {}));
  }

  function _readCache(key: string): unknown {
    try {
      const raw = sessionStorage.getItem(key);
      if (!raw) return null;
      const parsed = JSON.parse(raw) as { _t?: number; data?: unknown };
      return parsed?.data ?? null;
    } catch {
      return null;
    }
  }

  function _writeCache(key: string, data: unknown): void {
    try {
      const keys = Object.keys(sessionStorage).filter((k) =>
        k.startsWith(CACHE_PREFIX),
      );
      if (keys.length >= MAX_CACHE_ENTRIES) {
        // Evict least-recently-written (F-Z6), not an arbitrary key.
        let oldestKey = keys[0];
        let oldestT = Infinity;
        for (const k of keys) {
          let t = 0;
          try {
            t = (JSON.parse(sessionStorage.getItem(k) || "{}")._t as number) ?? 0;
          } catch {
            t = 0;
          }
          if (t < oldestT) {
            oldestT = t;
            oldestKey = k;
          }
        }
        sessionStorage.removeItem(oldestKey);
      }
      sessionStorage.setItem(key, JSON.stringify({ _t: Date.now(), data }));
    } catch {
      // sessionStorage full — silently skip (cache is best-effort).
    }
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  async function loadGcode(gcode: string, options?: LoadOptions): Promise<void> {
    _stopRaf();
    playState.value = "idle";
    currentTimeMs.value = 0;
    loading.value = true;
    error.value = null;
    warnings.value = null;
    tools.value = null;
    parseProgress.value = { percent: 10, stage: "uploading" };

    try {
      sourceGcode.value = gcode;
      selectedSegmentIndex.value = null;

      const cacheKey = _cacheKey(gcode, options as Record<string, unknown>);
      const cached = _readCache(cacheKey) as Awaited<ReturnType<typeof simulate>> | null;

      let result: Awaited<ReturnType<typeof simulate>>;
      if (cached) {
        result = cached;
        parseProgress.value = { percent: 80, stage: "simulating" };
      } else {
        parseProgress.value = { percent: 30, stage: "simulating" };
        result = await simulate({ gcode, ...options });
        _writeCache(cacheKey, result);
      }

      parseProgress.value = { percent: 90, stage: "simulating" };

      // Keep full resolution, then downsample for rendering if needed.
      fullSegments.value = result.segments;
      bounds.value = result.bounds;
      warnings.value = result.warnings ?? null;
      tools.value = result.tools ?? null;

      if (result.segments.length > MAX_SEGMENTS) {
        segments.value = downsampleSegments(result.segments, MAX_SEGMENTS);
      } else {
        segments.value = result.segments;
      }

      _rebuildCumulative();
      parseProgress.value = { percent: 100, stage: "complete" };
    } catch (e) {
      // Preserve the backend's message (e.g. ApiError carries status + detail)
      // rather than collapsing every failure to a generic string. (F-Z5)
      error.value = e instanceof Error ? e.message : "Simulation failed";
      segments.value = [];
      fullSegments.value = [];
      bounds.value = null;
      warnings.value = null;
      tools.value = null;
      _cumulativeMs = [];
    } finally {
      loading.value = false;
    }
  }

  function play(): void {
    if (segments.value.length === 0) return;
    if (currentTimeMs.value >= totalDurationMs.value) {
      currentTimeMs.value = 0;
    }
    playState.value = "playing";
    _lastTimestamp = 0;
    _rafHandle = requestAnimationFrame(_tick);
  }

  function pause(): void {
    playState.value = "paused";
    _stopRaf();
  }

  function stop(): void {
    playState.value = "idle";
    _stopRaf();
    currentTimeMs.value = 0;
    _lastTimestamp = 0;
  }

  function seek(p: number): void {
    currentTimeMs.value = Math.max(
      0,
      Math.min(p * totalDurationMs.value, totalDurationMs.value),
    );
  }

  function setSpeed(s: number): void {
    speed.value = s;
  }

  // ── P5: Segment selection actions ──────────────────────────────────────────
  function selectSegment(index: number | null): void {
    if (index !== null && (index < 0 || index >= segments.value.length)) {
      selectedSegmentIndex.value = null;
      return;
    }
    selectedSegmentIndex.value = index;
  }

  function clearSelection(): void {
    selectedSegmentIndex.value = null;
  }

  /** Jump playback to the *start* of the selected segment. (F-X2) */
  function jumpToSelected(): void {
    if (selectedSegmentIndex.value === null) return;
    currentTimeMs.value = _segmentStart(selectedSegmentIndex.value);
  }

  // ── P5: Measurement actions ───────────────────────────────────────────────
  function toggleMeasureMode(): void {
    measureMode.value = !measureMode.value;
    if (!measureMode.value) {
      measureTool.cancel();
      pendingMeasureStart.value = null;
    }
  }

  function addMeasurePoint(point: Point3D): Measurement | null {
    if (!measureMode.value) return null;

    if (!measureTool.hasPendingStart()) {
      measureTool.setStart(point);
      pendingMeasureStart.value = point;
      return null;
    } else {
      const measurement = measureTool.complete(point);
      pendingMeasureStart.value = null;
      if (measurement) {
        measurements.value = measureTool.getMeasurements();
      }
      return measurement;
    }
  }

  function cancelMeasurement(): void {
    measureTool.cancel();
    pendingMeasureStart.value = null;
  }

  function removeMeasurement(id: string): void {
    measureTool.remove(id);
    measurements.value = measureTool.getMeasurements();
  }

  function clearMeasurements(): void {
    measureTool.clear();
    measurements.value = [];
    pendingMeasureStart.value = null;
  }

  /** Step to the start of the next segment. (F-X2) */
  function stepForward(): void {
    const target = Math.min(currentSegmentIndex.value + 1, segments.value.length - 1);
    if (target < 0) return;
    currentTimeMs.value = _segmentStart(target);
  }

  /** Step to the start of the previous segment. (F-X2) */
  function stepBackward(): void {
    const target = Math.max(currentSegmentIndex.value - 1, 0);
    currentTimeMs.value = _segmentStart(target);
  }

  /** Manually set rendering resolution (percent 10–100 of full segments). */
  function setResolution(pct: number): void {
    const clamped = Math.max(10, Math.min(100, pct));
    const target = Math.floor((clamped / 100) * fullSegments.value.length);
    segments.value =
      target >= fullSegments.value.length
        ? fullSegments.value
        : downsampleSegments(fullSegments.value, target);
    _rebuildCumulative();
  }

  function _stopRaf(): void {
    if (_rafHandle) {
      cancelAnimationFrame(_rafHandle);
      _rafHandle = 0;
    }
  }

  function dispose(): void {
    _stopRaf();
    playState.value = "idle";
  }

  // ── Public API ────────────────────────────────────────────────────────────

  return {
    // State
    segments,
    fullSegments,
    bounds,
    loading,
    error,
    warnings,
    tools,
    hasFidelityWarnings,
    playState,
    currentTimeMs,
    speed,
    parseProgress,
    memoryInfo,

    // P5: Selection state
    selectedSegmentIndex,
    sourceGcode,

    // P5: Measurement state
    measureMode,
    measurements,
    pendingMeasureStart,
    measureTool,

    // Computed
    totalDurationMs,
    progress,
    currentSegmentIndex,
    toolPosition,
    currentSegment,

    // P5: Selection computed
    selectedSegment,
    selectedGcodeLine,

    // Actions
    loadGcode,
    play,
    pause,
    stop,
    seek,
    setSpeed,
    stepForward,
    stepBackward,
    setResolution,
    dispose,

    // P5: Selection actions
    selectSegment,
    clearSelection,
    jumpToSelected,

    // P5: Measurement actions
    toggleMeasureMode,
    addMeasurePoint,
    cancelMeasurement,
    removeMeasurement,
    clearMeasurements,
  };
});
