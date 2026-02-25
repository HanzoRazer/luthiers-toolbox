// packages/client/src/stores/useJobLogStore.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { JobLogEntry } from '@/models/rmos';
import { api } from '@/services/apiBase';
import { useAsyncAction } from '@/composables/useAsyncAction';

export const useJobLogStore = defineStore('jobLog', () => {
  const entries = ref<JobLogEntry[]>([]);

  const { loading, error, execute: fetchJobLog } = useAsyncAction(
    async () => {
      const res = await api('/api/joblog');
      if (!res.ok) throw new Error(`Failed to fetch joblog: ${res.status}`);
      const data: JobLogEntry[] = await res.json();
      entries.value = data;
      return data;
    },
  );

  return {
    entries,
    loading,
    error,
    fetchJobLog,
  };
});
