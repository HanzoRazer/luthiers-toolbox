/**
 * Generic composable for multi-select list management.
 * Domain-agnostic — works with any item that has an `id` field.
 *
 * Extracted & genericized from useCandidateSelection (RMOS domain).
 */
import { computed, ref } from 'vue'

/** Minimum contract an item must satisfy. */
export interface SelectableItem {
  id: string
}

export function useListSelection<T extends SelectableItem = SelectableItem>() {
  const selectedIds = ref<Set<string>>(new Set())
  const lastClickedId = ref<string | null>(null)

  function isSelected(id: string): boolean {
    return selectedIds.value.has(id)
  }

  function toggleSelection(id: string) {
    const next = new Set(selectedIds.value)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    selectedIds.value = next
    lastClickedId.value = id
  }

  /** Shift-click style range selection. */
  function selectRange(items: T[], toId: string) {
    if (!lastClickedId.value) {
      toggleSelection(toId)
      return
    }

    const ids = items.map((item) => item.id)
    const fromIdx = ids.indexOf(lastClickedId.value)
    const toIdx = ids.indexOf(toId)

    if (fromIdx === -1 || toIdx === -1) {
      toggleSelection(toId)
      return
    }

    const [start, end] = fromIdx < toIdx ? [fromIdx, toIdx] : [toIdx, fromIdx]
    const next = new Set(selectedIds.value)

    for (let i = start; i <= end; i++) {
      next.add(ids[i])
    }

    selectedIds.value = next
    lastClickedId.value = toId
  }

  function clearSelection() {
    selectedIds.value = new Set()
    lastClickedId.value = null
  }

  function selectAll(items: T[]) {
    selectedIds.value = new Set(items.map((item) => item.id))
  }

  function selectAllFiltered(filteredItems: T[]) {
    const next = new Set(selectedIds.value)
    for (const item of filteredItems) {
      next.add(item.id)
    }
    selectedIds.value = next
  }

  function clearAllFiltered(filteredItems: T[]) {
    const filteredIds = new Set(filteredItems.map((item) => item.id))
    const next = new Set(selectedIds.value)
    for (const id of filteredIds) {
      next.delete(id)
    }
    selectedIds.value = next
  }

  function invertSelectionFiltered(filteredItems: T[]) {
    const next = new Set(selectedIds.value)
    for (const item of filteredItems) {
      if (next.has(item.id)) {
        next.delete(item.id)
      } else {
        next.add(item.id)
      }
    }
    selectedIds.value = next
  }

  function toggleAllFiltered(filteredItems: T[]) {
    const filteredIds = filteredItems.map((item) => item.id)
    const allSelected = filteredIds.every((id) => selectedIds.value.has(id))
    if (allSelected) {
      clearAllFiltered(filteredItems)
    } else {
      selectAllFiltered(filteredItems)
    }
  }

  function getSelected(items: T[]): T[] {
    return items.filter((item) => selectedIds.value.has(item.id))
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
    getSelected,
  }
}
