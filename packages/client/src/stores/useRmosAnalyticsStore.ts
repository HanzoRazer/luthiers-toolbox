/**
 * RMOS Analytics Store (MM-4)
 * 
 * State management for material-aware lane analytics.
 */

import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { LaneAnalyticsResponse, RiskTimelineResponse } from '@/models/rmos_analytics';
import { api } from '@/services/apiBase';

export const useRmosAnalyticsStore = defineStore('rmosAnalytics', () => {
  const riskAnalytics = ref<LaneAnalyticsResponse | null>(null);
  const riskTimelines = ref<Map<string, RiskTimelineResponse>>(new Map());
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchRiskAnalytics(limitRecent: number = 200) {
    loading.value = true;
    error.value = null;
    try {
      const response = await api(`/api/rmos/analytics/lane-analytics?limit_recent=${limitRecent}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      riskAnalytics.value = await response.json();
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error';
      console.error('Failed to fetch risk analytics:', e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchRiskTimeline(presetId: string, limit: number = 200) {
    loading.value = true;
    error.value = null;
    try {
      const response = await api(`/api/rmos/analytics/risk-timeline/${presetId}?limit=${limit}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const timeline = await response.json();
      riskTimelines.value.set(presetId, timeline);
      return timeline;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error';
      console.error('Failed to fetch risk timeline:', e);
      return null;
    } finally {
      loading.value = false;
    }
  }

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
