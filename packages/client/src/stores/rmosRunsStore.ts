// packages/client/src/stores/rmosRunsStore.ts
/**
 * RMOS Run Artifacts Store (Pinia)
 *
 * Manages:
 * - Run artifact list with filtering
 * - Selected run detail
 * - Last selected run ID (for deterministic diff)
 */

import { defineStore } from "pinia";
import { fetchRuns, fetchRun, type RunIndexItem, type RunArtifactDetail, type FetchRunsParams } from "@/api/rmosRuns";

export interface RmosRunsState {
  items: RunIndexItem[];
  loading: boolean;
  selected: RunArtifactDetail | null;
  lastSelectedRunId: string | null;
  filters: {
    status: string;
    event_type: string;
    tool_id: string;
    workflow_session_id: string;
  };
  error: string | null;
}

export const useRmosRunsStore = defineStore("rmosRuns", {
  state: (): RmosRunsState => ({
    items: [],
    loading: false,
    selected: null,
    lastSelectedRunId: null,
    filters: {
      status: "",
      event_type: "",
      tool_id: "",
      workflow_session_id: "",
    },
    error: null,
  }),

  getters: {
    /**
     * Filter items that have a value in all non-empty filter fields.
     */
    filteredItems(state): RunIndexItem[] {
      return state.items;
    },

    /**
     * Check if we can diff (have both current selection and last selected).
     */
    canDiffWithLast(state): boolean {
      return !!(state.selected && state.lastSelectedRunId && state.selected.run_id !== state.lastSelectedRunId);
    },
  },

  actions: {
    /**
     * Load runs with current filters.
     */
    async loadRuns(limit = 50) {
      this.loading = true;
      this.error = null;
      try {
        const params: FetchRunsParams = {
          limit,
          ...this.cleanFilters(),
        };
        this.items = await fetchRuns(params);
      } catch (err: any) {
        this.error = err.message || "Failed to load runs";
        console.error("[rmosRunsStore] loadRuns error:", err);
      } finally {
        this.loading = false;
      }
    },

    /**
     * Select a run by ID and load its full details.
     * Shifts current selection to lastSelectedRunId before replacing.
     */
    async select(runId: string) {
      // Shift current selected into lastSelected before replacing
      if (this.selected?.run_id && this.selected.run_id !== runId) {
        this.lastSelectedRunId = this.selected.run_id;
      }

      this.error = null;
      try {
        this.selected = await fetchRun(runId);
      } catch (err: any) {
        this.error = err.message || "Failed to fetch run detail";
        console.error("[rmosRunsStore] select error:", err);
      }
    },

    /**
     * Explicitly set the last selected run ID.
     */
    setLastSelected(runId: string) {
      this.lastSelectedRunId = runId;
    },

    /**
     * Clear the current selection.
     */
    clearSelection() {
      this.selected = null;
    },

    /**
     * Update a single filter value.
     */
    setFilter(key: keyof RmosRunsState["filters"], value: string) {
      this.filters[key] = value;
    },

    /**
     * Clear all filters.
     */
    clearFilters() {
      this.filters = {
        status: "",
        event_type: "",
        tool_id: "",
        workflow_session_id: "",
      };
    },

    /**
     * Return only non-empty filter values.
     */
    cleanFilters(): Partial<FetchRunsParams> {
      const out: Partial<FetchRunsParams> = {};
      for (const [k, v] of Object.entries(this.filters)) {
        if (v) {
          (out as any)[k] = v;
        }
      }
      return out;
    },
  },
});
