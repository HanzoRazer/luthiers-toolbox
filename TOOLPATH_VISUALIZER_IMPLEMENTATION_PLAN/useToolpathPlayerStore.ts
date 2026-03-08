/**
 * Toolpath Player Store
 *
 * Owns all playback state for the animated G-code toolpath visualizer.
 * The canvas component is a pure renderer that reads from this store —
 * no playback logic lives in the component.
 *
 * Playback uses requestAnimationFrame for smooth 60fps animation.
 * The RAF loop lives here so playback persists across component remounts.
 *
 * Key design:
 * - segments[] and bounds come from POST /api/cam/gcode/simulate
 * - currentTimeMs drives all derived state (position, segment index)
 * - cumulativeMs[] enables O(log n) binary-search seek
 * - speed multiplier scales wall-clock delta before advancing currentTimeMs
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { simulate } from "@/sdk/endpoints/cam";
import type { MoveSegment, SimulateBounds } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Helper: 3D linear interpolation
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

// ---------------------------------------------------------------------------
// Helper: binary search over cumulative duration array
// ---------------------------------------------------------------------------

function binarySearchCumulative(cumulative: number[], timeMs: number): number {
  if (cumulative.length === 0) return -1;
  let lo = 0;
  let hi = cumulative.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (cumulative[mid] < timeMs) {
      lo = mid + 1;
    } else {
      hi = mid;
    }
  }
  return lo;
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useToolpathPlayerStore = defineStore("toolpathPlayer", () => {
  // ── Raw data ─────────────────────────────────────────────────────────────
  const segments = ref<MoveSegment[]>([]);
  const bounds = ref<SimulateBounds | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // ── Playback state ────────────────────────────────────────────────────────
  const playState = ref<"idle" | "playing" | "paused">("idle");
  const currentTimeMs = ref(0);
  const speed = ref(1);

  // ── RAF internals (plain values — not reactive, no proxying needed) ───────
  let _rafHandle = 0;
  let _lastTimestamp = 0;

  // ── Precomputed cumulative durations — rebuilt when segments load ──────────
  // cumulativeMs[i] = sum of duration_ms for segments[0..i] inclusive
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

  /** Index of the segment the tool is currently on (or -1 if no segments). */
  const currentSegmentIndex = computed<number>(() => {
    if (segments.value.length === 0) return -1;
    return binarySearchCumulative(_cumulativeMs, currentTimeMs.value);
  });

  /** Interpolated [x, y, z] tool position in mm. */
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

  /** The segment the tool is currently executing (null if no data). */
  const currentSegment = computed<MoveSegment | null>(
    () => segments.value[currentSegmentIndex.value] ?? null,
  );

  // ── RAF animation tick ────────────────────────────────────────────────────

  function _tick(timestamp: number): void {
    if (playState.value !== "playing") return;

    if (_lastTimestamp > 0) {
      const wallDelta = timestamp - _lastTimestamp; // ms of real time
      const simDelta = wallDelta * speed.value;
      const next = currentTimeMs.value + simDelta;

      if (next >= totalDurationMs.value) {
        currentTimeMs.value = totalDurationMs.value;
        playState.value = "paused"; // Stop at end — don't loop
        _lastTimestamp = 0;
        return;
      }
      currentTimeMs.value = next;
    }

    _lastTimestamp = timestamp;
    _rafHandle = requestAnimationFrame(_tick);
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  /** Load G-code from the API and populate segments. Resets playback. */
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

    try {
      const result = await simulate({ gcode, ...options });
      segments.value = result.segments;
      bounds.value = result.bounds;
      _rebuildCumulative();
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Simulation failed";
      segments.value = [];
      bounds.value = null;
      _cumulativeMs = [];
    } finally {
      loading.value = false;
    }
  }

  /** Start or resume playback. */
  function play(): void {
    if (segments.value.length === 0) return;
    // Restart from beginning if already at the end
    if (currentTimeMs.value >= totalDurationMs.value) {
      currentTimeMs.value = 0;
    }
    playState.value = "playing";
    _lastTimestamp = 0;
    _rafHandle = requestAnimationFrame(_tick);
  }

  /** Pause playback, preserving current position. */
  function pause(): void {
    playState.value = "paused";
    _stopRaf();
  }

  /** Stop playback and reset to start. */
  function stop(): void {
    playState.value = "idle";
    _stopRaf();
    currentTimeMs.value = 0;
    _lastTimestamp = 0;
  }

  /** Seek to a progress fraction (0.0 → 1.0). */
  function seek(p: number): void {
    currentTimeMs.value = Math.max(
      0,
      Math.min(p * totalDurationMs.value, totalDurationMs.value),
    );
  }

  /** Set playback speed multiplier (e.g. 0.5, 1, 2, 5, 10). */
  function setSpeed(s: number): void {
    speed.value = s;
  }

  /** Advance to the start of the next segment. */
  function stepForward(): void {
    const next = currentSegmentIndex.value + 1;
    if (next < segments.value.length) {
      // Jump to the moment just after the previous segment ends
      currentTimeMs.value = _cumulativeMs[next - 1] ?? 0;
    }
  }

  /** Jump back to the start of the previous segment. */
  function stepBackward(): void {
    const prev = currentSegmentIndex.value - 1;
    currentTimeMs.value = prev >= 0 ? (_cumulativeMs[prev - 1] ?? 0) : 0;
  }

  // ── Internal: RAF cleanup ─────────────────────────────────────────────────

  function _stopRaf(): void {
    if (_rafHandle) {
      cancelAnimationFrame(_rafHandle);
      _rafHandle = 0;
    }
  }

  /** Call on component unmount to prevent RAF leak. */
  function dispose(): void {
    _stopRaf();
    playState.value = "idle";
  }

  // ── Public API ────────────────────────────────────────────────────────────

  return {
    // State
    segments,
    bounds,
    loading,
    error,
    playState,
    currentTimeMs,
    speed,

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
    dispose,
  };
});
