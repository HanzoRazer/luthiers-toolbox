/**
 * RMOS Runs Store
 *
 * Pinia store for managing Run Artifact state including:
 * - List pagination with cursor
 * - Filters (status, mode, tool_id, risk_level)
 * - Selected artifact detail
 * - Last selected run ID for diff comparison
 *
 * Target: packages/client/src/stores/rmosRunsStore.ts
 */

import { defineStore } from "pinia";
import { fetchRuns, fetchRun, type RunIndexItem } from "@/api/rmosRuns";

export interface RmosRunsFilters {
  status: string;
  mode: string;
  tool_id_prefix: string;
  risk_level: string;
}

export interface RmosRunsState {
  items: RunIndexItem[];
  nextCursor: string | null;
  loading: boolean;
  selected: any | null;
  lastSelectedRunId: string | null;
  filters: RmosRunsFilters;
}

export const useRmosRunsStore = defineStore("rmosRuns", {
  state: (): RmosRunsState => ({
    items: [],
    nextCursor: null,
    loading: false,
    selected: null,
    // Tracks the previously selected run for "Diff with last selected"
    lastSelectedRunId: null,
    filters: {
      status: "",
      mode: "",
      tool_id_prefix: "",
      risk_level: "",
    },
  }),

  getters: {
    hasMore: (state) => state.nextCursor !== null,
    isEmpty: (state) => state.items.length === 0 && !state.loading,
    canDiffWithLast: (state) =>
      !!state.lastSelectedRunId &&
      state.selected?.run_id !== state.lastSelectedRunId,
  },

  actions: {
    /**
     * Load first page of runs with current filters.
     */
    async loadFirst(limit = 25) {
      this.loading = true;
      try {
        const res = await fetchRuns({
          ...this.cleanFilters(),
          limit,
        });
        this.items = res.items;
        this.nextCursor = res.next_cursor ?? null;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Load next page using cursor pagination.
     */
    async loadMore(limit = 25) {
      if (!this.nextCursor) return;
      this.loading = true;
      try {
        const res = await fetchRuns({
          ...this.cleanFilters(),
          limit,
          cursor: this.nextCursor,
        });
        this.items.push(...res.items);
        this.nextCursor = res.next_cursor ?? null;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Select a run and load its full details.
     * Shifts current selection to lastSelectedRunId before replacing.
     */
    async select(runId: string) {
      // Track previous selection for diff comparison
      if (this.selected?.run_id && this.selected.run_id !== runId) {
        this.lastSelectedRunId = this.selected.run_id;
      }
      this.selected = await fetchRun(runId);
    },

    /**
     * Explicitly set the last selected run ID.
     * Called when clicking a row in the panel.
     */
    setLastSelected(runId: string) {
      this.lastSelectedRunId = runId;
    },

    /**
     * Clear selection state.
     */
    clearSelection() {
      this.selected = null;
    },

    /**
     * Reset filters and reload.
     */
    async resetFilters() {
      this.filters = {
        status: "",
        mode: "",
        tool_id_prefix: "",
        risk_level: "",
      };
      await this.loadFirst();
    },

    /**
     * Remove empty filter values for API call.
     */
    cleanFilters(): Record<string, string> {
      const out: Record<string, string> = {};
      for (const [k, v] of Object.entries(this.filters)) {
        if (v) out[k] = v;
      }
      return out;
    },
  },
});
