/**
 * useSeverityFilter - Severity filter state and helpers for CamIssuesList
 */
import { computed, ref, type Ref } from "vue";

export const SEVERITY_OPTIONS = ["info", "low", "medium", "high", "critical"] as const;
export type SeverityOption = (typeof SEVERITY_OPTIONS)[number];

export function useSeverityFilter() {
  const activeSeverities = ref<SeverityOption[]>([...SEVERITY_OPTIONS]);

  const activeSeveritiesSet = computed(
    () => new Set<SeverityOption>(activeSeverities.value)
  );

  function toggleSeverity(s: SeverityOption) {
    const current = new Set(activeSeverities.value);
    if (current.has(s)) current.delete(s);
    else current.add(s);
    // Avoid empty filter: if user turns everything off, reset to all
    activeSeverities.value =
      current.size === 0 ? [...SEVERITY_OPTIONS] : (Array.from(current) as SeverityOption[]);
  }

  function selectAllSeverities() {
    activeSeverities.value = [...SEVERITY_OPTIONS];
  }

  function selectHighCriticalOnly() {
    activeSeverities.value = ["high", "critical"];
  }

  function severityChipClass(sev: SeverityOption | string | undefined): string {
    const base =
      "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold";
    switch (sev) {
      case "critical":
      case "high":
        return base + " bg-red-500 text-white";
      case "medium":
        return base + " bg-orange-500 text-white";
      case "low":
        return base + " bg-yellow-400 text-black";
      case "info":
      default:
        return base + " bg-gray-300 text-gray-800";
    }
  }

  function severityLabelShort(s: SeverityOption): string {
    switch (s) {
      case "critical":
        return "C";
      case "high":
        return "H";
      case "medium":
        return "M";
      case "low":
        return "L";
      case "info":
      default:
        return "I";
    }
  }

  return {
    activeSeverities,
    activeSeveritiesSet,
    toggleSeverity,
    selectAllSeverities,
    selectHighCriticalOnly,
    severityChipClass,
    severityLabelShort,
    SEVERITY_OPTIONS,
  };
}
