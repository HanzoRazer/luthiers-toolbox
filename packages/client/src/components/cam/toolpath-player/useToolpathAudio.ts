/**
 * useToolpathAudio — Audio sync composable for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Manages P5 audio engine synchronization with playback.
 */

import { watch, type Ref } from 'vue';
import { getAudioEngine, type MoveSegment as AudioMoveSegment } from '@/util/toolpathAudio';
import type { MoveSegment, SimulateBounds } from '@/sdk/endpoints/cam';

export interface AudioSyncConfig {
  segments: Ref<MoveSegment[]>;
  bounds: Ref<SimulateBounds | null>;
  playState: Ref<'idle' | 'playing' | 'paused'>;
  currentSegmentIndex: Ref<number>;
  progress: Ref<number>;
  totalDurationMs: Ref<number>;
}

export interface ToolpathAudioState {
  audioEngine: ReturnType<typeof getAudioEngine>;
}

/**
 * Helper to get cumulative time up to a segment index
 */
function getSegmentStartTime(segments: MoveSegment[], idx: number): number {
  let time = 0;
  for (let i = 0; i < idx; i++) {
    time += segments[i].duration_ms;
  }
  return time;
}

export function useToolpathAudio(config: AudioSyncConfig): ToolpathAudioState {
  const audioEngine = getAudioEngine();

  // Initialize audio engine bounds when segments load
  watch(
    () => config.bounds.value,
    (bounds) => {
      if (bounds) {
        audioEngine.setBounds(bounds.z_min, bounds.z_max, 100, 3000);
      }
    }
  );

  // Sync audio with playback state
  watch(
    () => config.playState.value,
    (state) => {
      if (state === 'playing') {
        audioEngine.start();
      } else {
        audioEngine.stop();
      }
    }
  );

  // Update audio based on current segment
  watch(
    () => [config.currentSegmentIndex.value, config.progress.value] as const,
    ([segIdx, progress]) => {
      const seg = config.segments.value[segIdx];
      if (seg && config.playState.value === 'playing') {
        const segProgress = (progress * config.totalDurationMs.value - getSegmentStartTime(config.segments.value, segIdx)) / seg.duration_ms;
        audioEngine.updateForSegment(seg as AudioMoveSegment, Math.max(0, Math.min(1, segProgress)));
      }
    }
  );

  return {
    audioEngine,
  };
}
