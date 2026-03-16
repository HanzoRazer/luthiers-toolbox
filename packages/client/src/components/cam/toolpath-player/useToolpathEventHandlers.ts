/**
 * useToolpathEventHandlers — Panel event handlers for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Handles: annotation goto, compare segments, tool select, feed hints, chip load issues.
 */

import { type Ref } from 'vue';
import type { Annotation } from '@/util/toolpathAnnotations';
import type { ToolChangeMarker } from '@/util/toolpathTools';
import type { FeedHint } from '@/util/feedOptimizer';
import type { ChipLoadIssue } from '@/util/chipLoadAnalyzer';

export interface EventHandlersConfig {
  segments: { length: number };
  compareSegments: Ref<unknown[]>;
  showCompareOverlay: Ref<boolean>;
  selectedToolFilter: Ref<number | null>;
  navigation: {
    jumpToSegment: (index: number) => void;
    jumpToSegmentRange: (index: number, pause?: boolean) => void;
  };
  seek: (progress: number) => void;
}

export interface ToolpathEventHandlersState {
  handleAnnotationGoto: (annotation: Annotation) => void;
  handleCompareSegments: (segments: unknown[]) => void;
  handleCompareOverlayToggle: (enabled: boolean) => void;
  handleToolSelect: (toolNumber: number | null) => void;
  handleToolChangeClick: (marker: ToolChangeMarker) => void;
  handleFeedHintClick: (hint: FeedHint) => void;
  handleChipLoadIssueClick: (issue: ChipLoadIssue) => void;
}

export function useToolpathEventHandlers(config: EventHandlersConfig): ToolpathEventHandlersState {
  /**
   * Jump to annotation's segment position
   */
  function handleAnnotationGoto(annotation: Annotation): void {
    if (annotation.segmentIndex !== null) {
      const progress = annotation.segmentIndex / Math.max(1, config.segments.length - 1);
      config.seek(Math.min(1, Math.max(0, progress)));
    }
  }

  /**
   * Update compare segments overlay data
   */
  function handleCompareSegments(segments: unknown[]): void {
    config.compareSegments.value = segments;
  }

  /**
   * Toggle compare overlay visibility
   */
  function handleCompareOverlayToggle(enabled: boolean): void {
    config.showCompareOverlay.value = enabled;
  }

  /**
   * Set active tool filter
   */
  function handleToolSelect(toolNumber: number | null): void {
    config.selectedToolFilter.value = toolNumber;
  }

  /**
   * Jump to tool change position
   */
  function handleToolChangeClick(marker: ToolChangeMarker): void {
    config.navigation.jumpToSegment(marker.segmentIndex);
  }

  /**
   * Jump to feed hint position
   */
  function handleFeedHintClick(hint: FeedHint): void {
    config.navigation.jumpToSegmentRange(hint.segmentRange[0], true);
  }

  /**
   * Jump to chip load issue position
   */
  function handleChipLoadIssueClick(issue: ChipLoadIssue): void {
    config.navigation.jumpToSegmentRange(issue.segmentRange[0], true);
  }

  return {
    handleAnnotationGoto,
    handleCompareSegments,
    handleCompareOverlayToggle,
    handleToolSelect,
    handleToolChangeClick,
    handleFeedHintClick,
    handleChipLoadIssueClick,
  };
}
