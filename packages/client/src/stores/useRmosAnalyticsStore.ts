/**
 * RMOS Analytics Store (MM-4)
 * 
 * State management for material-aware lane analytics.
 */

import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { LaneAnalyticsResponse, RiskTimelineResponse } from '@/models/rmos_analytics';
import { api } from '@/services/apiBase';
import { useAsyncAction } from '@/composables/useAsyncAction';

export const useRmosAnalyticsStore = defineStore('rmosAnalytics', () => {
  const riskAnalytics = ref<LaneAnalyticsResponse | null>(null);
  const riskTimelines = ref<Map<string, RiskTimelineResponse>>(new Map());
  // Shared loading/error refs for both actions
  const loading = ref(false);
  const error = ref<string | null>(null);

  const sharedRefs = { loading, error };

  const { execute: fetchRiskAnalytics } = useAsyncAction(
    async (limitRecent: number = 200) => {
      const response = await api(`/api/rmos/analytics/lane-analytics?limit_recent=${limitRecent}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data: LaneAnalyticsResponse = await response.json();
      riskAnalytics.value = data;
      return data;
    },
    { refs: sharedRefs },
  );

  const { execute: fetchRiskTimeline } = useAsyncAction(
    async (presetId: string, limit: number = 200) => {
      const response = await api(`/api/rmos/analytics/risk-timeline/${presetId}?limit=${limit}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const timeline: RiskTimelineResponse = await response.json();
      riskTimelines.value.set(presetId, timeline);
      return timeline;
    },
    { refs: sharedRefs },
  );

  function clearAnalytics() {
    riskAnalytics.value = null;
    riskTimelines.value.clear();
    error.value = null;
  }

  return {
    riskAnalytics,
    riskTimelines,
    loading,
    error,
    fetchRiskAnalytics,
    fetchRiskTimeline,
    clearAnalytics,
  };
});
