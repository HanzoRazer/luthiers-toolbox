/**
 * useToolpathNavigation — Segment navigation helpers for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Provides helpers for jumping to specific segments.
 */

import type { Ref } from 'vue';
import type { MoveSegment } from '@/sdk/endpoints/cam';

export interface NavigationConfig {
  segments: Ref<MoveSegment[]>;
  totalDurationMs: Ref<number>;
  seek: (progress: number) => void;
  pause: () => void;
}

export interface ToolpathNavigationState {
  getSegmentStartTime: (idx: number) => number;
  jumpToSegment: (segmentIndex: number, pauseAfter?: boolean) => void;
  jumpToSegmentRange: (startIdx: number, pauseAfter?: boolean) => void;
}

export function useToolpathNavigation(config: NavigationConfig): ToolpathNavigationState {
  /**
   * Get cumulative time up to a segment index
   */
  function getSegmentStartTime(idx: number): number {
    let time = 0;
    const segs = config.segments.value;
    for (let i = 0; i < idx && i < segs.length; i++) {
      time += segs[i].duration_ms;
    }
    return time;
  }

  /**
   * Jump to a specific segment by index
   */
  function jumpToSegment(segmentIndex: number, pauseAfter = false): void {
    const segs = config.segments.value;
    if (segmentIndex < 0 || segmentIndex >= segs.length) return;

    const time = getSegmentStartTime(segmentIndex);
    const totalMs = config.totalDurationMs.value;
    if (totalMs > 0) {
      config.seek(time / totalMs);
    }

    if (pauseAfter) {
      config.pause();
    }
  }

  /**
   * Jump to the start of a segment range (e.g., for hints/issues)
   */
  function jumpToSegmentRange(startIdx: number, pauseAfter = true): void {
    jumpToSegment(startIdx, pauseAfter);
  }

  return {
    getSegmentStartTime,
    jumpToSegment,
    jumpToSegmentRange,
  };
}
