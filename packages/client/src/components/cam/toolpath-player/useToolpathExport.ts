/**
 * useToolpathExport — Animation export composable
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Manages P5 animation export logic.
 */

import { ref, type Ref } from 'vue';
import {
  AnimationExporter,
  downloadExport,
  type ExportConfig,
  type ExportProgress,
} from '@/util/animationExporter';

export interface ToolpathExportState {
  showExportPanel: Ref<boolean>;
  isExporting: Ref<boolean>;
  exportProgress: Ref<ExportProgress | null>;
  exportConfig: Ref<Partial<ExportConfig>>;
  startExport: (
    canvasEl: HTMLCanvasElement,
    totalDurationMs: number,
    onStart: () => void,
    onStop: () => void
  ) => Promise<void>;
  cancelExport: (onStop: () => void) => void;
}

export function useToolpathExport(): ToolpathExportState {
  // State
  const showExportPanel = ref(false);
  const isExporting = ref(false);
  const exportProgress = ref<ExportProgress | null>(null);
  const exportConfig = ref<Partial<ExportConfig>>({
    format: 'webm',
    fps: 30,
    quality: 0.8,
    duration: null,
  });

  let exporter: AnimationExporter | null = null;

  // Start export
  async function startExport(
    canvasEl: HTMLCanvasElement,
    totalDurationMs: number,
    onStart: () => void,
    onStop: () => void
  ): Promise<void> {
    if (isExporting.value) return;

    isExporting.value = true;
    showExportPanel.value = false;

    exporter = new AnimationExporter(exportConfig.value);

    // Calculate duration - full animation or custom
    const durationMs = exportConfig.value.duration
      ? exportConfig.value.duration * 1000
      : totalDurationMs;

    // Reset and start playback
    onStart();

    // Wait a frame for reset
    await new Promise(r => setTimeout(r, 50));

    const result = await exporter.exportFromCanvas(
      canvasEl,
      durationMs,
      (progress) => {
        exportProgress.value = progress;
      },
      () => {
        // Frame callback - animation runs via store.play()
      }
    );

    isExporting.value = false;
    onStop();

    if (result.success) {
      downloadExport(result);
      exportProgress.value = {
        phase: 'complete',
        percent: 100,
        message: `Exported ${result.filename}`,
        framesCaptured: exportProgress.value?.totalFrames ?? 0,
        totalFrames: exportProgress.value?.totalFrames ?? 0,
      };

      // Clear progress after 3 seconds
      setTimeout(() => {
        exportProgress.value = null;
      }, 3000);
    } else {
      exportProgress.value = {
        phase: 'error',
        percent: 0,
        message: result.error || 'Export failed',
        framesCaptured: 0,
        totalFrames: 0,
      };
    }
  }

  // Cancel export
  function cancelExport(onStop: () => void): void {
    if (exporter) {
      exporter.cancel();
      exporter = null;
    }
    isExporting.value = false;
    exportProgress.value = null;
    onStop();
  }

  return {
    showExportPanel,
    isExporting,
    exportProgress,
    exportConfig,
    startExport,
    cancelExport,
  };
}
