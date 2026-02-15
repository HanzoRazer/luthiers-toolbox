// packages/client/src/stores/useManufacturingPlanStore.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { ManufacturingPlan } from '@/models/rmos';
import { api } from '@/services/apiBase';

interface PlanRequest {
  pattern_id: string;
  guitars: number;
  tile_length_mm: number;
  scrap_factor: number;
  record_joblog: boolean;
}

export const useManufacturingPlanStore = defineStore('manufacturingPlan', () => {
  const currentPlan = ref<ManufacturingPlan | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchPlan(req: PlanRequest) {
    loading.value = true;
    error.value = null;
    try {
      const res = await api('/api/rosette/manufacturing-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      });
      if (!res.ok) throw new Error(`Failed to fetch plan: ${res.status}`);
      currentPlan.value = await res.json();
    } catch (err: any) {
      error.value = err?.message ?? String(err);
      currentPlan.value = null;
    } finally {
      loading.value = false;
    }
  }

  return {
    currentPlan,
    loading,
    error,
    fetchPlan,
  };
});
