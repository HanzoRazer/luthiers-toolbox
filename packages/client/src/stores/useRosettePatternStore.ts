// packages/client/src/stores/useRosettePatternStore.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { RosettePattern } from '@/models/rmos';

export const useRosettePatternStore = defineStore('rosettePattern', () => {
  const patterns = ref<RosettePattern[]>([]);
  const selectedPatternId = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const selectedPattern = computed<RosettePattern | null>(() => {
    if (!selectedPatternId.value) return null;
    return patterns.value.find((p) => p.id === selectedPatternId.value) ?? null;
  });

  async function fetchPatterns() {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch('/api/rosette-patterns');
      if (!res.ok) throw new Error(`Failed to fetch patterns: ${res.status}`);
      patterns.value = await res.json();
    } catch (err: any) {
      error.value = err?.message ?? String(err);
    } finally {
      loading.value = false;
    }
  }

  async function createPattern(pattern: RosettePattern) {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch('/api/rosette-patterns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pattern),
      });
      if (!res.ok) throw new Error(`Failed to create pattern: ${res.status}`);
      const created = await res.json();
      patterns.value.push(created);
      selectedPatternId.value = created.id;
      return created;
    } catch (err: any) {
      error.value = err?.message ?? String(err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function updatePattern(patternId: string, updates: Partial<RosettePattern>) {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`/api/rosette-patterns/${patternId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!res.ok) throw new Error(`Failed to update pattern: ${res.status}`);
      const updated = await res.json();
      const idx = patterns.value.findIndex((p) => p.id === patternId);
      if (idx >= 0) {
        patterns.value[idx] = updated;
      }
      return updated;
    } catch (err: any) {
      error.value = err?.message ?? String(err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deletePattern(patternId: string) {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`/api/rosette-patterns/${patternId}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error(`Failed to delete pattern: ${res.status}`);
      patterns.value = patterns.value.filter((p) => p.id !== patternId);
      if (selectedPatternId.value === patternId) {
        selectedPatternId.value = null;
      }
    } catch (err: any) {
      error.value = err?.message ?? String(err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function selectPattern(patternId: string) {
    selectedPatternId.value = patternId;
  }

  return {
    patterns,
    selectedPatternId,
    selectedPattern,
    loading,
    error,
    fetchPatterns,
    createPattern,
    updatePattern,
    deletePattern,
    selectPattern,
  };
});
