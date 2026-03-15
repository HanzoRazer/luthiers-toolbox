/**
 * useToolpathViewControls — 3D view manipulation helpers for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Provides helpers for 3D canvas view manipulation.
 */

import { type Ref } from 'vue';

export interface Canvas3DRef {
  resetView?: () => void;
  setView?: (view: string) => void;
}

export interface ViewControlsConfig {
  viewMode: Ref<'2d' | '3d'>;
  canvas3DRef: Ref<Canvas3DRef | null>;
  enable3D: boolean;
}

export interface ToolpathViewControlsState {
  resetView: () => void;
  setViewTop: () => void;
  setViewFront: () => void;
  setViewSide: () => void;
  toggleViewMode: () => void;
}

export function useToolpathViewControls(config: ViewControlsConfig): ToolpathViewControlsState {
  function resetView(): void {
    if (config.viewMode.value === '3d' && config.canvas3DRef.value) {
      config.canvas3DRef.value.resetView?.();
    }
  }

  function setViewTop(): void {
    if (config.viewMode.value === '3d' && config.canvas3DRef.value) {
      config.canvas3DRef.value.setView?.('top');
    }
  }

  function setViewFront(): void {
    if (config.viewMode.value === '3d' && config.canvas3DRef.value) {
      config.canvas3DRef.value.setView?.('front');
    }
  }

  function setViewSide(): void {
    if (config.viewMode.value === '3d' && config.canvas3DRef.value) {
      config.canvas3DRef.value.setView?.('side');
    }
  }

  function toggleViewMode(): void {
    if (config.enable3D) {
      config.viewMode.value = config.viewMode.value === '2d' ? '3d' : '2d';
    }
  }

  return {
    resetView,
    setViewTop,
    setViewFront,
    setViewSide,
    toggleViewMode,
  };
}
