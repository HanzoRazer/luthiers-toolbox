/**
 * useToolpathAnalysis — Collision detection and optimization analysis composable
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Manages P4 collision detection and optimization suggestion logic.
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue';
import { CollisionDetector, type CollisionReport, type Fixture } from '@/util/collisionDetector';
import { GcodeOptimizer, type OptimizationReport } from '@/util/gcodeOptimizer';
import type { MoveSegment } from '@/sdk/endpoints/cam';

export interface ToolpathBounds {
  x_min: number;
  x_max: number;
  y_min: number;
  y_max: number;
  z_min: number;
  z_max: number;
}

export interface AnalysisConfig {
  enableCollisionDetection: boolean;
  enableOptimization: boolean;
  toolDiameter: number;
  safeZ: number;
  fixtures: Fixture[];
}

export interface ToolpathAnalysisState {
  collisionReport: Ref<CollisionReport | null>;
  optimizationReport: Ref<OptimizationReport | null>;
  showCollisionPanel: Ref<boolean>;
  showOptPanel: Ref<boolean>;
  hasCollisions: ComputedRef<boolean>;
  hasCriticalCollisions: ComputedRef<boolean>;
  hasOptimizations: ComputedRef<boolean>;
  activeCollisions: (segmentIndex: number) => CollisionReport['collisions'];
  runCollisionDetection: (segments: MoveSegment[], bounds: ToolpathBounds | null) => void;
  runOptimizationAnalysis: (segments: MoveSegment[], totalDurationMs: number) => void;
  runAnalysis: (segments: MoveSegment[], bounds: ToolpathBounds | null, totalDurationMs: number) => void;
  clearAnalysis: () => void;
}

export function useToolpathAnalysis(config: AnalysisConfig): ToolpathAnalysisState {
  // State
  const collisionReport = ref<CollisionReport | null>(null);
  const optimizationReport = ref<OptimizationReport | null>(null);
  const showCollisionPanel = ref(false);
  const showOptPanel = ref(false);

  // Computed
  const hasCollisions = computed(() =>
    collisionReport.value !== null && collisionReport.value.collisions.length > 0
  );

  const hasCriticalCollisions = computed(() =>
    collisionReport.value !== null && collisionReport.value.criticalCount > 0
  );

  const hasOptimizations = computed(() =>
    optimizationReport.value !== null && optimizationReport.value.suggestions.length > 0
  );

  // Get collisions active at a given segment index
  function activeCollisions(segmentIndex: number): CollisionReport['collisions'] {
    if (!collisionReport.value) return [];
    return collisionReport.value.collisions.filter(c => c.segmentIndex <= segmentIndex);
  }

  // Run collision detection
  function runCollisionDetection(segments: MoveSegment[], bounds: ToolpathBounds | null): void {
    if (!config.enableCollisionDetection || segments.length === 0) return;

    const detector = new CollisionDetector({
      toolDiameter: config.toolDiameter,
      safeZ: config.safeZ,
      fixtures: config.fixtures,
      stock: bounds ? {
        bounds,
        resolution: 1,
        width: 100,
        height: 100,
        thickness: Math.abs(bounds.z_min) + 5,
        voxels: new Uint8Array(10000).fill(255),
        originalVoxels: new Uint8Array(10000).fill(255),
      } : undefined,
    });

    collisionReport.value = detector.checkAll(segments);
  }

  // Run optimization analysis
  function runOptimizationAnalysis(segments: MoveSegment[], totalDurationMs: number): void {
    if (!config.enableOptimization || segments.length === 0) return;

    const optimizer = new GcodeOptimizer({
      safeZ: config.safeZ,
      stockTopZ: 0,
      originalTime: totalDurationMs,
    });

    optimizationReport.value = optimizer.analyze(segments);
  }

  // Run both analyses
  function runAnalysis(
    segments: MoveSegment[],
    bounds: ToolpathBounds | null,
    totalDurationMs: number
  ): void {
    runCollisionDetection(segments, bounds);
    runOptimizationAnalysis(segments, totalDurationMs);
  }

  // Clear analysis results
  function clearAnalysis(): void {
    collisionReport.value = null;
    optimizationReport.value = null;
    showCollisionPanel.value = false;
    showOptPanel.value = false;
  }

  return {
    collisionReport,
    optimizationReport,
    showCollisionPanel,
    showOptPanel,
    hasCollisions,
    hasCriticalCollisions,
    hasOptimizations,
    activeCollisions,
    runCollisionDetection,
    runOptimizationAnalysis,
    runAnalysis,
    clearAnalysis,
  };
}
