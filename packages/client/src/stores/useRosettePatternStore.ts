/**
 * useRosettePatternStore — compatibility adapter (Phase 5)
 *
 * Delegates to the consolidated useRosetteStore for all manufacturing
 * pattern CRUD operations. Existing consumers (RosettePipelineView,
 * RosettePatternLibrary, RosettePatternLibraryEnhanced) work unchanged.
 *
 * New code should import { useRosetteStore } from '@/stores/rosetteStore' directly.
 */
import { defineStore, storeToRefs } from 'pinia';
import { computed } from 'vue';
import type { RosettePattern } from '@/models/rmos';
import { useRosetteStore } from './rosetteStore';

export const useRosettePatternStore = defineStore('rosettePattern', () => {
  const rosette = useRosetteStore();
  const {
    mfgPatterns: patterns,
    selectedMfgPatternId: selectedPatternId,
    mfgPatternsLoading: loading,
    mfgPatternsError: error,
  } = storeToRefs(rosette);

  const selectedPattern = computed<RosettePattern | null>(() => rosette.selectedMfgPattern);

  // Delegate actions to canonical store
  function fetchPatterns() {
    return rosette.fetchMfgPatterns();
  }

  function createPattern(pattern: RosettePattern) {
    return rosette.createMfgPattern(pattern);
  }

  function updatePattern(patternId: string, updates: Partial<RosettePattern>) {
    return rosette.updateMfgPattern(patternId, updates);
  }

  function deletePattern(patternId: string) {
    return rosette.deleteMfgPattern(patternId);
  }

  function selectPattern(patternId: string) {
    rosette.selectMfgPattern(patternId);
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
