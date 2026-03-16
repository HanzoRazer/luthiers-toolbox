/**
 * useToolpathCanvasExport — Canvas element retrieval + export orchestration
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Handles finding the canvas element and coordinating with useToolpathExport.
 */

import { type Ref, type ComputedRef } from 'vue';
import { useToolpathExport, type ToolpathExportState } from './useToolpathExport';

export interface CanvasExportConfig {
  viewMode: Ref<'2d' | '3d'>;
  canvas2DRef: Ref<{ $el?: HTMLElement } | null>;
  canvas3DRef: Ref<{ $el?: HTMLElement } | null>;
  totalDurationMs: ComputedRef<number>;
  onPlayFromStart: () => void;
  onPause: () => void;
}

export interface ToolpathCanvasExportState extends ToolpathExportState {
  startCanvasExport: () => Promise<void>;
  cancelCanvasExport: () => void;
}

export function useToolpathCanvasExport(config: CanvasExportConfig): ToolpathCanvasExportState {
  const exportState = useToolpathExport();

  function getCanvasElement(): HTMLCanvasElement | null {
    if (config.viewMode.value === '2d' && config.canvas2DRef.value) {
      return config.canvas2DRef.value.$el?.querySelector('canvas') ?? null;
    } else if (config.viewMode.value === '3d' && config.canvas3DRef.value) {
      return config.canvas3DRef.value.$el?.querySelector('canvas') ?? null;
    }
    return null;
  }

  async function startCanvasExport(): Promise<void> {
    const canvasEl = getCanvasElement();

    if (!canvasEl) {
      console.error('Cannot find canvas element for export');
      return;
    }

    await exportState.startExport(
      canvasEl,
      config.totalDurationMs.value,
      config.onPlayFromStart,
      config.onPause
    );
  }

  function cancelCanvasExport(): void {
    exportState.cancelExport(config.onPause);
  }

  return {
    ...exportState,
    startCanvasExport,
    cancelCanvasExport,
  };
}
