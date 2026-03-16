<script setup lang="ts">
/**
 * ModalPanelsLayer — Modal/overlay panels for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Contains: CollisionPanel, OptimizationPanel, GcodeSourcePanel,
 * ExportAnimationPanel, MeasureModeIndicator, KeyboardShortcutsOverlay
 */

import {
  CollisionPanel,
  OptimizationPanel,
  GcodeSourcePanel,
  ExportAnimationPanel,
  MeasureModeIndicator,
  KeyboardShortcutsOverlay,
  MeasurementsPanel,
} from './index';
import type { CollisionReport } from '@/util/collisionDetector';
import type { OptimizationReport } from '@/util/gcodeOptimizer';
import type { ExportConfig, ExportProgress } from '@/util/animationExporter';

interface Shortcut {
  key: string;
  description: string;
  category: 'playback' | 'view' | 'tools' | 'navigation';
}

interface Measurement {
  id: string;
  distance: number;
  deltaX: number;
  deltaY: number;
  deltaZ: number;
}

interface MeasureTool {
  formatDistance: (d: number) => string;
}

interface Props {
  // Collision/Optimization
  showCollisionPanel: boolean;
  collisionReport: CollisionReport | null;
  showOptPanel: boolean;
  optimizationReport: OptimizationReport | null;
  // G-code source
  showGcodePanel: boolean;
  hasSourceGcode: boolean;
  hasSelection: boolean;
  // Export
  showExportPanel: boolean;
  isExporting: boolean;
  exportConfig: Partial<ExportConfig>;
  exportProgress: ExportProgress | null;
  // Measure mode
  measureMode: boolean;
  pendingMeasureStart: boolean;
  // Keyboard shortcuts
  showHelp: boolean;
  shortcuts: Shortcut[];
  // Measurements
  measurements: Measurement[];
  measureTool: MeasureTool;
  measurementsCollapsed: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:showCollisionPanel': [value: boolean];
  'update:showOptPanel': [value: boolean];
  'update:showGcodePanel': [value: boolean];
  clearSelection: [];
  'update:showExportPanel': [value: boolean];
  'update:exportConfig': [config: Partial<ExportConfig> | undefined];
  startExport: [];
  cancelExport: [];
  cancelMeasurement: [];
  hideHelp: [];
  removeMeasurement: [id: string];
  clearMeasurements: [];
  'update:measurementsCollapsed': [value: boolean];
}>();
</script>

<template>
  <!-- Collision Panel -->
  <CollisionPanel
    v-if="props.showCollisionPanel && props.collisionReport"
    :report="props.collisionReport"
    @close="emit('update:showCollisionPanel', false)"
  />

  <!-- Optimization Panel -->
  <OptimizationPanel
    v-if="props.showOptPanel && props.optimizationReport"
    :report="props.optimizationReport"
    @close="emit('update:showOptPanel', false)"
  />

  <!-- G-code Source Panel -->
  <GcodeSourcePanel
    v-if="props.showGcodePanel && props.hasSourceGcode"
    :has-selection="props.hasSelection"
    @close="emit('update:showGcodePanel', false)"
    @clear-selection="emit('clearSelection')"
  />

  <!-- Export Panel -->
  <ExportAnimationPanel
    v-if="props.showExportPanel"
    :is-exporting="props.isExporting"
    :config="props.exportConfig"
    :export-progress="props.exportProgress"
    @close="emit('update:showExportPanel', false)"
    @update:config="emit('update:exportConfig', $event)"
    @start-export="emit('startExport')"
    @cancel-export="emit('cancelExport')"
  />

  <!-- Measure mode indicator -->
  <MeasureModeIndicator
    v-if="props.measureMode"
    :pending-start="props.pendingMeasureStart"
    @cancel="emit('cancelMeasurement')"
  />

  <!-- Keyboard Shortcuts Help Overlay -->
  <KeyboardShortcutsOverlay
    v-if="props.showHelp"
    :shortcuts="props.shortcuts"
    @close="emit('hideHelp')"
  />

  <!-- Measurements Panel -->
  <MeasurementsPanel
    v-if="props.measurements.length > 0"
    :measurements="(props.measurements as any)"
    :measure-tool="props.measureTool"
    :collapsed="props.measurementsCollapsed"
    @remove="emit('removeMeasurement', $event)"
    @clear="emit('clearMeasurements')"
    @update:collapsed="emit('update:measurementsCollapsed', $event)"
  />
</template>
