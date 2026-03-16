/**
 * useToolpathMultiTool — Multi-tool filter state for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Handles tool filtering when G-code uses multiple tools.
 */

import { ref, computed, type ComputedRef, type Ref } from 'vue';
import { analyzeToolUsage } from '@/util/toolpathTools';
import type { MoveSegment } from '@/sdk/endpoints/cam/simulate';

export interface MultiToolConfig {
  segments: ComputedRef<MoveSegment[]>;
}

export interface ToolpathMultiToolState {
  selectedToolFilter: Ref<number | null>;
  hasMultipleTools: ComputedRef<boolean>;
}

export function useToolpathMultiTool(config: MultiToolConfig): ToolpathMultiToolState {
  const selectedToolFilter = ref<number | null>(null);

  const hasMultipleTools = computed(() => {
    const tools = analyzeToolUsage(config.segments.value);
    return tools.length > 1;
  });

  return {
    selectedToolFilter,
    hasMultipleTools,
  };
}
