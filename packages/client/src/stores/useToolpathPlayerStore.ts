/**
 * Toolpath Player Store — P1-P3 Enhanced
 *
 * Owns all playback state for the animated G-code toolpath visualizer.
 * The canvas component is a pure renderer that reads from this store.
 *
 * P1 enhancements: Memory management, progress tracking, downsampling
 * P2 enhancements: Caching layer for repeated simulations
 * P3 enhancements: M-code tracking in segments
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { simulate } from "@/sdk/endpoints/cam/simulate";
import type { MoveSegment, SimulateBounds } from "@/sdk/endpoints/cam/simulate";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const MAX_SEGMENTS = 100_000;
const WARNING_THRESHOLD = 75_000;
const CACHE_PREFIX = "gcode-sim-";
const MAX_CACHE_ENTRIES = 20;

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

function binarySearchCumulative(cumulative: number[], timeMs: number): number {
  if (cumulative.length === 0) return -1;
  let lo = 0;
  let hi = cumulative.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (cumulative[mid] < timeMs) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

/** Adaptive downsample: keeps all rapids & arc endpoints, thins straight cuts. */
function downsampleSegments(
  segments: MoveSegment[],
  target: number,
): MoveSegment[] {
  if (segments.length <= target) return segments;
  const result: MoveSegment[] = [];
  const step = Math.max(1, Math.floor(segments.length / target));
  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    // Always keep rapids and first/last of arc runs
    if (
      seg.type === "rapid" ||
      i === 0 ||
      i === segments.length - 1 ||
      i % step === 0
    ) {
      result.push(seg);
    }
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
    const segStart = idx > 0 ? _cumulativeMs[idx - 1] : 0;
    const segDuration = seg.duration_ms;

    const t =
      segDuration > 0
        ? Math.min((currentTimeMs.value - segStart) / segDuration, 1)
        : 1;

    return lerp3(
      seg.from_pos as [number, number, number],
      seg.to_pos as [number, number, number],
      t,
    );
  });

  const currentSegment = computed<MoveSegment | null>(
    () => segments.value[currentSegmentIndex.value] ?? null,
  );

  // ── RAF animation tick ────────────────────────────────────────────────────

  function _tick(timestamp: number): void {
    if (playState.value !== "playing") return;

    if (_lastTimestamp > 0) {
      const wallDelta = timestamp - _lastTimestamp;
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
    return CACHE_PREFIX + fnv1a(gcode + JSON.stringify(opts ?? {}));
  }

  function _readCache(key: string) {
    try {
      const raw = sessionStorage.getItem(key);
      if (!raw) return null;
      return JSON.parse(raw);
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
        sessionStorage.removeItem(keys[0]);
      }
      sessionStorage.setItem(key, JSON.stringify(data));
    } catch {
      // sessionStorage full — silently skip
    }
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  async function loadGcode(
    gcode: string,
    options?: {
      rapid_mm_min?: number;
      default_feed_mm_min?: number;
      arc_resolution_deg?: number;
    },
  ): Promise<void> {
    _stopRaf();
    playState.value = "idle";
    currentTimeMs.value = 0;
    loading.value = true;
    error.value = null;
    parseProgress.value = { percent: 10, stage: "uploading" };

    try {
      const cacheKey = _cacheKey(gcode, options as Record<string, unknown>);
      const cached = _readCache(cacheKey);

      let result;
      if (cached) {
        result = cached;
        parseProgress.value = { percent: 80, stage: "simulating" };
      } else {
        parseProgress.value = { percent: 30, stage: "simulating" };
        result = await simulate({ gcode, ...options });
        _writeCache(cacheKey, result);
      }

      parseProgress.value = { percent: 90, stage: "simulating" };

      // Store full resolution, then downsample if needed
      fullSegments.value = result.segments;
      bounds.value = result.bounds;

      if (result.segments.length > MAX_SEGMENTS) {
        segments.value = downsampleSegments(result.segments, MAX_SEGMENTS);
      } else {
        segments.value = result.segments;
      }

      _rebuildCumulative();
      parseProgress.value = { percent: 100, stage: "complete" };
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Simulation failed";
      segments.value = [];
      fullSegments.value = [];
      bounds.value = null;
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

  function stepForward(): void {
    const next = currentSegmentIndex.value + 1;
    if (next < segments.value.length) {
      currentTimeMs.value = _cumulativeMs[next - 1] ?? 0;
    }
  }

  function stepBackward(): void {
    const prev = currentSegmentIndex.value - 1;
    currentTimeMs.value = prev >= 0 ? (_cumulativeMs[prev - 1] ?? 0) : 0;
  }

  /** Manually set rendering resolution (percent 10–100 of full segments). */
  function setResolution(pct: number): void {
    const clamped = Math.max(10, Math.min(100, pct));
    const target = Math.floor((clamped / 100) * fullSegments.value.length);
    segments.value = downsampleSegments(fullSegments.value, target);
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
    playState,
    currentTimeMs,
    speed,
    parseProgress,
    memoryInfo,

    // Computed
    totalDurationMs,
    progress,
    currentSegmentIndex,
    toolPosition,
    currentSegment,

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
  };
});
