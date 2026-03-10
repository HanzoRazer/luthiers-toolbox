/**
 * useFeatureToggles.ts
 *
 * Composable for managing feature toggles in CAD views.
 * Provides reactive state for checkbox-based display/behavior options.
 */

import { reactive, computed, watch, toRefs } from "vue";

export interface FeatureToggle {
  key: string;
  label: string;
  description?: string;
  checked: boolean;
  disabled?: boolean;
}

export interface FeatureToggleOptions {
  /** Persist toggles to localStorage */
  persist?: boolean;
  /** Storage key for persistence */
  storageKey?: string;
  /** Callback when any toggle changes */
  onChange?: (key: string, value: boolean) => void;
}

/**
 * Create a feature toggles manager for a view.
 *
 * @example
 * ```ts
 * const { toggles, isEnabled, toggle, setToggle, reset } = useFeatureToggles({
 *   showToolpath: true,
 *   showGrid: true,
 *   snapToGrid: false,
 *   animate: false,
 * });
 *
 * // Check if enabled
 * if (isEnabled('showToolpath')) { ... }
 *
 * // Toggle a feature
 * toggle('showGrid');
 *
 * // Set specific value
 * setToggle('animate', true);
 * ```
 */
export function useFeatureToggles<T extends Record<string, boolean>>(
  initialToggles: T,
  options: FeatureToggleOptions = {}
) {
  const { persist = false, storageKey = "feature-toggles", onChange } = options;

  // Load from storage if persisting
  let storedToggles: Partial<T> = {};
  if (persist && typeof window !== "undefined") {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        storedToggles = JSON.parse(stored);
      }
    } catch (e) {
      console.warn("Failed to load feature toggles from storage:", e);
    }
  }

  // Merge initial with stored values
  const toggles = reactive({ ...initialToggles, ...storedToggles }) as T;

  // Watch for changes and persist
  if (persist) {
    watch(
      () => ({ ...toggles }),
      (newToggles) => {
        try {
          localStorage.setItem(storageKey, JSON.stringify(newToggles));
        } catch (e) {
          console.warn("Failed to persist feature toggles:", e);
        }
      },
      { deep: true }
    );
  }

  /**
   * Check if a feature is enabled.
   */
  function isEnabled(key: keyof T): boolean {
    return toggles[key] === true;
  }

  /**
   * Toggle a feature on/off.
   */
  function toggle(key: keyof T): void {
    const newValue = !toggles[key];
    (toggles as Record<string, boolean>)[key as string] = newValue;
    onChange?.(key as string, newValue);
  }

  /**
   * Set a feature to a specific value.
   */
  function setToggle(key: keyof T, value: boolean): void {
    (toggles as Record<string, boolean>)[key as string] = value;
    onChange?.(key as string, value);
  }

  /**
   * Reset all toggles to initial values.
   */
  function reset(): void {
    Object.keys(initialToggles).forEach((key) => {
      (toggles as Record<string, boolean>)[key] = initialToggles[key as keyof T];
    });
  }

  /**
   * Get toggles as an array for rendering.
   */
  const toggleList = computed((): FeatureToggle[] => {
    return Object.entries(toggles).map(([key, checked]) => ({
      key,
      label: formatLabel(key),
      checked: checked as boolean,
    }));
  });

  return {
    toggles,
    ...toRefs(toggles),
    isEnabled,
    toggle,
    setToggle,
    reset,
    toggleList,
  };
}

/**
 * Convert camelCase key to human-readable label.
 */
function formatLabel(key: string): string {
  return key
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
}

/**
 * Create a feature toggles panel configuration.
 * Use with CadFeatureToggles component.
 *
 * @example
 * ```ts
 * const displayToggles = createToggleConfig([
 *   { key: "showToolpath", label: "Show Toolpath", checked: true },
 *   { key: "showRapids", label: "Show Rapid Moves", checked: true },
 *   { key: "showMaterial", label: "Show Material Bounds", checked: false },
 * ]);
 * ```
 */
export function createToggleConfig(
  features: FeatureToggle[]
): Map<string, FeatureToggle> {
  const map = new Map<string, FeatureToggle>();
  features.forEach((f) => map.set(f.key, f));
  return map;
}

export default useFeatureToggles;
