/**
 * Composable for candidate selection logic.
 * Extracted from ManufacturingCandidateList.vue
 */
import { computed, ref } from 'vue'

// Generic interface - any object with candidate_id works
export interface SelectableCandidate {
  candidate_id: string
}

export function useCandidateSelection<T extends SelectableCandidate = SelectableCandidate>() {
  const selectedIds = ref<Set<string>>(new Set())
  const lastClickedId = ref<string | null>(null)

  function isSelected(id: string): boolean {
    return selectedIds.value.has(id)
  }

  function toggleSelection(id: string) {
    const newSet = new Set(selectedIds.value)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    selectedIds.value = newSet
    lastClickedId.value = id
  }

  function selectRange(candidates: T[], toId: string) {
    if (!lastClickedId.value) {
      toggleSelection(toId)
      return
    }

    const ids = candidates.map(c => c.candidate_id)
    const fromIdx = ids.indexOf(lastClickedId.value)
    const toIdx = ids.indexOf(toId)

    if (fromIdx === -1 || toIdx === -1) {
      toggleSelection(toId)
      return
    }

    const [start, end] = fromIdx < toIdx ? [fromIdx, toIdx] : [toIdx, fromIdx]
    const newSet = new Set(selectedIds.value)

    for (let i = start; i <= end; i++) {
      newSet.add(ids[i])
    }

    selectedIds.value = newSet
    lastClickedId.value = toId
  }

  function clearSelection() {
    selectedIds.value = new Set()
    lastClickedId.value = null
  }

  function selectAll(candidates: T[]) {
    selectedIds.value = new Set(candidates.map(c => c.candidate_id))
  }

  function selectAllFiltered(filteredCandidates: T[]) {
    const newSet = new Set(selectedIds.value)
    for (const c of filteredCandidates) {
      newSet.add(c.candidate_id)
    }
    selectedIds.value = newSet
  }

  function clearAllFiltered(filteredCandidates: T[]) {
    const filteredIds = new Set(filteredCandidates.map(c => c.candidate_id))
    const newSet = new Set(selectedIds.value)
    for (const id of filteredIds) {
      newSet.delete(id)
    }
    selectedIds.value = newSet
  }

  function invertSelectionFiltered(filteredCandidates: T[]) {
    const newSet = new Set(selectedIds.value)
    for (const c of filteredCandidates) {
      if (newSet.has(c.candidate_id)) {
        newSet.delete(c.candidate_id)
      } else {
        newSet.add(c.candidate_id)
      }
    }
    selectedIds.value = newSet
  }

  function toggleAllFiltered(filteredCandidates: T[]) {
    const filteredIds = filteredCandidates.map(c => c.candidate_id)
    const allSelected = filteredIds.every(id => selectedIds.value.has(id))

    if (allSelected) {
      clearAllFiltered(filteredCandidates)
    } else {
      selectAllFiltered(filteredCandidates)
    }
  }

  function getSelectedCandidates(candidates: T[]): T[] {
    return candidates.filter(c => selectedIds.value.has(c.candidate_id))
  }

  const selectedCount = computed(() => selectedIds.value.size)

  return {
    selectedIds,
    lastClickedId,
    selectedCount,
    isSelected,
    toggleSelection,
    selectRange,
    clearSelection,
    selectAll,
    selectAllFiltered,
    clearAllFiltered,
    invertSelectionFiltered,
    toggleAllFiltered,
    getSelectedCandidates,
  }
}
