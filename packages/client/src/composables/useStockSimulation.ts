/**
 * useStockSimulation — P4 Integration Composable
 *
 * Combines stock material simulation and collision detection
 * for the ToolpathPlayer component.
 *
 * Features:
 * - Reactive stock state
 * - Real-time collision checking
 * - Integration with useToolpathPlayerStore
 */

import { ref, computed, watch, type Ref, type ComputedRef } from "vue";
import { StockSimulator, type StockMaterial, type StockConfig, type RemovalStats } from "@/util/stockSimulator";
import {
  CollisionDetector,
  type CollisionConfig,
  type CollisionReport,
  type Collision,
  type Fixture,
} from "@/util/collisionDetector";
import type { MoveSegment, SimulateBounds } from "@/sdk/endpoints/cam";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface StockSimulationConfig {
  /** Enable stock simulation */
  enabled?: boolean;
  /** Enable collision detection */
  collisionDetection?: boolean;
  /** Stock configuration */
  stock?: StockConfig;
  /** Collision detection configuration */
  collision?: Partial<CollisionConfig>;
}

export interface UseStockSimulationReturn {
  // Stock state
  stock: Ref<StockMaterial | null>;
  removalStats: ComputedRef<RemovalStats>;

  // Collision state
  collisionReport: Ref<CollisionReport | null>;
  activeCollisions: ComputedRef<Collision[]>;
  hasCriticalCollisions: ComputedRef<boolean>;

  // Controls
  initializeStock: (bounds: SimulateBounds) => void;
  simulateToSegment: (index: number) => void;
  resetStock: () => void;
  checkCollisions: () => void;

  // Fixture management
  addFixture: (fixture: Fixture) => void;
  removeFixture: (name: string) => void;
  clearFixtures: () => void;
  fixtures: Ref<Fixture[]>;

  // Configuration
  setToolDiameter: (diameter: number) => void;
  setEnabled: (enabled: boolean) => void;
  setCollisionEnabled: (enabled: boolean) => void;
}

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export function useStockSimulation(
  segments: Ref<MoveSegment[]>,
  currentSegmentIndex: Ref<number>,
  bounds: Ref<SimulateBounds | null>,
  config: StockSimulationConfig = {}
): UseStockSimulationReturn {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------

  const enabled = ref(config.enabled ?? true);
  const collisionEnabled = ref(config.collisionDetection ?? true);

  const stock = ref<StockMaterial | null>(null);
  const collisionReport = ref<CollisionReport | null>(null);
  const fixtures = ref<Fixture[]>([]);

  // Simulators
  const stockSimulator = new StockSimulator();
  let collisionDetector: CollisionDetector | null = null;

  // ---------------------------------------------------------------------------
  // Computed
  // ---------------------------------------------------------------------------

  const removalStats = computed<RemovalStats>(() => {
    return stockSimulator.getStats();
  });

  const activeCollisions = computed<Collision[]>(() => {
    if (!collisionReport.value) return [];
    const idx = currentSegmentIndex.value;
    // Show collisions up to current segment
    return collisionReport.value.collisions.filter((c) => c.segmentIndex <= idx);
  });

  const hasCriticalCollisions = computed<boolean>(() => {
    return activeCollisions.value.some((c) => c.severity === "critical");
  });

  // ---------------------------------------------------------------------------
  // Methods
  // ---------------------------------------------------------------------------

  function initializeStock(newBounds: SimulateBounds): void {
    if (!enabled.value) return;

    // Initialize stock
    const stockConfig: StockConfig = {
      margin: 10,
      resolution: 0.5,
      ...config.stock,
    };

    const newStock = stockSimulator.initializeFromBounds(newBounds, stockConfig);
    stock.value = newStock;

    // Initialize collision detector
    const toolDiameter = config.collision?.toolDiameter ?? 6;
    collisionDetector = new CollisionDetector({
      toolDiameter,
      stock: newStock,
      fixtures: fixtures.value,
      ...config.collision,
    });

    // Run initial collision check
    if (collisionEnabled.value && segments.value.length > 0) {
      checkCollisions();
    }
  }

  function simulateToSegment(index: number): void {
    if (!enabled.value || !stock.value) return;
    stockSimulator.simulateToSegment(segments.value, index);
    // Update reactive ref
    stock.value = stockSimulator.getStock();
  }

  function resetStock(): void {
    stockSimulator.reset();
    stock.value = stockSimulator.getStock();
  }

  function checkCollisions(): void {
    if (!collisionEnabled.value || !collisionDetector) return;
    collisionReport.value = collisionDetector.checkAll(segments.value);
  }

  function addFixture(fixture: Fixture): void {
    fixtures.value.push(fixture);
    if (collisionDetector) {
      collisionDetector.addFixture(fixture);
      checkCollisions();
    }
  }

  function removeFixture(name: string): void {
    fixtures.value = fixtures.value.filter((f) => f.name !== name);
    if (collisionDetector) {
      collisionDetector.clearFixtures();
      fixtures.value.forEach((f) => collisionDetector!.addFixture(f));
      checkCollisions();
    }
  }

  function clearFixtures(): void {
    fixtures.value = [];
    if (collisionDetector) {
      collisionDetector.clearFixtures();
      checkCollisions();
    }
  }

  function setToolDiameter(diameter: number): void {
    stockSimulator.setToolDiameter(diameter);
    if (collisionDetector) {
      collisionDetector.setConfig({ toolDiameter: diameter });
      checkCollisions();
    }
  }

  function setEnabled(value: boolean): void {
    enabled.value = value;
    if (value && bounds.value && !stock.value) {
      initializeStock(bounds.value);
    }
  }

  function setCollisionEnabled(value: boolean): void {
    collisionEnabled.value = value;
    if (value && segments.value.length > 0) {
      checkCollisions();
    }
  }

  // ---------------------------------------------------------------------------
  // Watchers
  // ---------------------------------------------------------------------------

  // Initialize stock when bounds change
  watch(bounds, (newBounds) => {
    if (newBounds && enabled.value) {
      initializeStock(newBounds);
    }
  }, { immediate: true });

  // Simulate to current segment
  watch(currentSegmentIndex, (idx) => {
    if (enabled.value && idx >= 0) {
      simulateToSegment(idx);
    }
  });

  // Re-check collisions when segments change
  watch(segments, () => {
    if (collisionEnabled.value && segments.value.length > 0) {
      checkCollisions();
    }
  });

  // ---------------------------------------------------------------------------
  // Return
  // ---------------------------------------------------------------------------

  return {
    // Stock state
    stock,
    removalStats,

    // Collision state
    collisionReport,
    activeCollisions,
    hasCriticalCollisions,

    // Controls
    initializeStock,
    simulateToSegment,
    resetStock,
    checkCollisions,

    // Fixture management
    addFixture,
    removeFixture,
    clearFixtures,
    fixtures,

    // Configuration
    setToolDiameter,
    setEnabled,
    setCollisionEnabled,
  };
}

export default useStockSimulation;
