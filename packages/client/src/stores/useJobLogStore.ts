// packages/client/src/stores/useJobLogStore.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { JobLogEntry } from '@/models/rmos';
import { api } from '@/services/apiBase';

export const useJobLogStore = defineStore('jobLog', () => {
  const entries = ref<JobLogEntry[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchJobLog() {
    loading.value = true;
    error.value = null;
    try {
      const res = await api('/api/joblog');
      if (!res.ok) throw new Error(`Failed to fetch joblog: ${res.status}`);
      entries.value = await res.json();
    } catch (err: any) {
      error.value = err?.message ?? String(err);
    } finally {
      loading.value = false;
    }
  }

  return {
    entries,
    loading,
    error,
    fetchJobLog,
  };
});
