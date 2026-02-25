// packages/client/src/stores/useManufacturingPlanStore.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { ManufacturingPlan } from '@/models/rmos';
import { api } from '@/services/apiBase';
import { useAsyncAction } from '@/composables/useAsyncAction';

interface PlanRequest {
  pattern_id: string;
  guitars: number;
  tile_length_mm: number;
  scrap_factor: number;
  record_joblog: boolean;
}

export const useManufacturingPlanStore = defineStore('manufacturingPlan', () => {
  const currentPlan = ref<ManufacturingPlan | null>(null);

  const { loading, error, execute: fetchPlan } = useAsyncAction(
    async (req: PlanRequest) => {
      const res = await api('/api/rosette/manufacturing-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      });
      if (!res.ok) throw new Error(`Failed to fetch plan: ${res.status}`);
      const plan: ManufacturingPlan = await res.json();
      currentPlan.value = plan;
      return plan;
    },
    {
      onError: () => {
        currentPlan.value = null;
        return undefined; // use default message
      },
    },
  );

  return {
    currentPlan,
    loading,
    error,
    fetchPlan,
  };
});
