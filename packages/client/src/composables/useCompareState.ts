/* eslint-disable no-direct-state-mutation */
/**
 * CompareLab State Machine Guard
 * B22.8: Compare Lab State Machine
 *
 * ⚠️ CRITICAL GUARDRAIL - DO NOT VIOLATE
 *
 * IMPORTANT:
 *   The following refs MUST NOT be mutated outside this file:
 *
 *     - isComputingDiff
 *     - diffDisabledReason
 *     - overlayDisabled (computed; never set it directly)
 *
 *   All CompareLab diff operations MUST flow through:
 *
 *       runWithCompareSkeleton(fn)
 *
 *   Rationale:
 *     Components and helpers must not manipulate the lifecycle state manually.
 *     Direct mutation breaks:
 *       - skeleton loading behavior
 *       - overlay disable logic
 *       - double-click protection
 *       - error recovery + toast signaling
 *
 * ❌ NEVER do this in components:
 *   isComputingDiff.value = true        // WRONG - bypasses skeleton wrapper
 *   overlayDisabled.value = false       // WRONG - computed property, read-only
 *   diffDisabledReason.value = null     // WRONG - breaks error tracking
 *
 * ✅ ALWAYS do this instead:
 *   await compareState.runWithCompareSkeleton(() => backendCall())
 *   compareState.computeDiff(baselineId, geometry)
 *
 * Protocol Rules (B22.8):
 *   Rule 1: Single source of truth (this file only)
 *   Rule 2: Wrapper enforcement (use runWithCompareSkeleton)
 *   Rule 3: Disabled state binding (bind to overlayDisabled.value)
 *   Rule 4: Props-down/events-up (no direct calls from children)
 *   Rule 5: Error handling (errors in diffDisabledReason)
 *
 * ESLint Enforcement:
 *   If you see an ESLint warning "no-direct-state-mutation",
 *   it means code outside this composable tried to modify CompareLab core
 *   state incorrectly.
 *
 * Violations will be caught in:
 *   - VSCode (red squiggle as you type)
 *   - ESLint (npm run lint)
 *   - Pre-commit hooks (Husky + lint-staged)
 *   - CI workflow (GitHub Actions)
 *
 * See:
 *   - docs/COMPARELAB_DEV_CHECKLIST.md
 *   - client/src/components/compare/README.md
 *   - .vscode/README.md
 */ import { ref, computed, type Ref, type ComputedRef } from "vue";
import type { CanonicalGeometry } from "@/utils/geometry";

// B22.8: Bounding box for zoom/viewport control
export interface CompareResultBBox {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

// B22.8: Layer info for layer visibility/filtering
export interface CompareLayerInfo {
  id: string;
  inLeft: boolean;
  inRight: boolean;
  hasDiff?: boolean;
  enabled: boolean;
}

export interface DiffSummary {
  segments_baseline: number;
  segments_current: number;
  added: number;
  removed: number;
  unchanged: number;
  overlap_ratio: number;
}

export interface DiffSegment {
  id: string;
  type: string;
  status: "added" | "removed" | "match";
  length: number;
  path_index: number;
}

// B22.8: Extended result with bbox and layers
export interface DiffResult {
  baseline_id: string;
  baseline_name: string;
  summary: DiffSummary;
  segments: DiffSegment[];
  baseline_geometry?: CanonicalGeometry;
  current_geometry?: CanonicalGeometry;
  // Enhanced with skeleton pattern
  fullBBox?: CompareResultBBox;
  diffBBox?: CompareResultBBox;
  layers?: CompareLayerInfo[];
}

export type CompareMode =
  | "side-by-side"
  | "overlay"
  | "delta"
  | "blink"
  | "x-ray";

export interface CompareState {
  // Core state
  isComputingDiff: Ref<boolean>;
  overlayDisabled: ComputedRef<boolean>;
  diffDisabledReason: Ref<string | null>;
  currentMode: Ref<CompareMode>;
  compareResult: Ref<DiffResult | null>;

  // Layer management (B22.8 skeleton enhancement)
  layers: Ref<CompareLayerInfo[]>;
  visibleLayers: ComputedRef<CompareLayerInfo[]>;
  showOnlyMismatchedLayers: Ref<boolean>;
  activeBBox: ComputedRef<CompareResultBBox | null>;
  hasResult: ComputedRef<boolean>;

  // Actions
  computeDiff: (
    baselineId: string,
    currentGeometry: CanonicalGeometry
  ) => Promise<void>;
  setMode: (mode: CompareMode) => void;
  reset: () => void;
  runWithCompareSkeleton: <T>(fn: () => Promise<T>) => Promise<T | undefined>;
  // Layer actions
  setLayerEnabled: (id: string, enabled: boolean) => void;
  setShowOnlyMismatched: (enabled: boolean) => void;
}

const API_BASE = "/api/compare/lab";

export function useCompareState(): CompareState {
  // State refs
  const isComputingDiff = ref(false);
  const diffDisabledReason = ref<string | null>(null);
  const currentMode = ref<CompareMode>("overlay");
  const compareResult = ref<DiffResult | null>(null);

  // Layer state (B22.8 skeleton enhancement)
  const layers = ref<CompareLayerInfo[]>([]);
  const showOnlyMismatchedLayers = ref(false);

  // Computed state
  const overlayDisabled = computed(() => {
    // Disable overlay controls when:
    // 1. Currently computing a diff
    // 2. No compare result available
    // 3. Explicit disabled reason set
    return (
      isComputingDiff.value ||
      !compareResult.value ||
      diffDisabledReason.value !== null
    );
  });

  const hasResult = computed(() => compareResult.value !== null);

  const activeBBox = computed<CompareResultBBox | null>(() => {
    if (!compareResult.value) return null;
    // Prefer diffBBox for zooming to changes, fallback to fullBBox
    return compareResult.value.diffBBox ?? compareResult.value.fullBBox ?? null;
  });

  const visibleLayers = computed(() => {
    if (!showOnlyMismatchedLayers.value) return layers.value;
    return layers.value.filter((l) => l.hasDiff);
  });

  // Generic skeleton wrapper for async operations with double-click protection
  async function runWithCompareSkeleton<T>(
    fn: () => Promise<T>
  ): Promise<T | undefined> {
    // Double-click protection: ignore if already computing
    if (isComputingDiff.value) {
      return undefined;
    }

    isComputingDiff.value = true;
    // Clear previous reason on fresh run
    diffDisabledReason.value = null;

    try {
      const result = await fn();
      return result;
    } catch (err: any) {
      // Extract user-friendly error message
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        "Compare operation failed. Overlay disabled.";
      diffDisabledReason.value = message;
      // Log for debugging but don't rethrow (callers can check diffDisabledReason)
      console.error("[useCompareState] Operation error:", err);
      return undefined;
    } finally {
      isComputingDiff.value = false;
    }
  }

  // Actions
  async function computeDiff(
    baselineId: string,
    currentGeometry: CanonicalGeometry
  ): Promise<void> {
    // Validation
    if (!currentGeometry) {
      diffDisabledReason.value = "No current geometry loaded";
      compareResult.value = null;
      return;
    }

    if (!baselineId) {
      diffDisabledReason.value = "No baseline selected";
      compareResult.value = null;
      return;
    }

    // Clear previous errors
    diffDisabledReason.value = null;

    // Set computing state
    isComputingDiff.value = true;

    try {
      const res = await fetch(`${API_BASE}/diff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baseline_id: baselineId,
          current_geometry: currentGeometry,
        }),
      });

      if (!res.ok) {
        throw new Error(`Diff request failed: ${res.status} ${res.statusText}`);
      }

      const diff: DiffResult = await res.json();
      compareResult.value = diff;

      // Populate layers from response (B22.8 skeleton enhancement)
      if (diff.layers && Array.isArray(diff.layers)) {
        layers.value = diff.layers.map((l) => ({
          id: l.id,
          inLeft: !!l.inLeft,
          inRight: !!l.inRight,
          hasDiff: !!l.hasDiff,
          enabled: true, // Start with all layers visible
        }));
      } else {
        layers.value = [];
      }

      diffDisabledReason.value = null;
    } catch (error) {
      console.error("[useCompareState] Diff computation error:", error);
      diffDisabledReason.value =
        error instanceof Error ? error.message : "Failed to compute diff";
      compareResult.value = null;
      layers.value = [];
    } finally {
      // Always clear computing state
      isComputingDiff.value = false;
    }
  }

  function setMode(mode: CompareMode): void {
    if (overlayDisabled.value) {
      console.warn(
        "[useCompareState] Cannot set mode while overlay disabled:",
        diffDisabledReason.value
      );
      return;
    }
    currentMode.value = mode;
  }

  function reset(): void {
    isComputingDiff.value = false;
    diffDisabledReason.value = null;
    currentMode.value = "overlay";
    compareResult.value = null;
    layers.value = [];
    showOnlyMismatchedLayers.value = false;
  }

  // Layer management actions (B22.8 skeleton enhancement)
  function setLayerEnabled(id: string, enabled: boolean): void {
    layers.value = layers.value.map((layer) =>
      layer.id === id ? { ...layer, enabled } : layer
    );
  }

  function setShowOnlyMismatched(enabled: boolean): void {
    showOnlyMismatchedLayers.value = enabled;
  }

  return {
    // State
    isComputingDiff,
    overlayDisabled,
    diffDisabledReason,
    currentMode,
    compareResult,
    layers,
    visibleLayers,
    showOnlyMismatchedLayers,
    activeBBox,
    hasResult,

    // Actions
    computeDiff,
    setMode,
    reset,
    runWithCompareSkeleton,
    setLayerEnabled,
    setShowOnlyMismatched,
  };
}
