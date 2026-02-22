/**
 * SnapshotComparePanel navigation composable.
 */
import { watch, type Ref, type ComputedRef } from 'vue'
import { useToastStore } from '@/stores/toastStore'
import type { AnySnap, SnapshotItem } from './snapshotCompareTypes'

export interface SnapshotCompareNavigationReturn {
  pickBaselineLeft: () => void
  pickMostRecentNonBaselineAsRight: () => void
  swapSides: () => void
  clearCompare: () => void
  stepRight: (delta: number) => void
  stepLeft: (delta: number) => void
  scheduleLiveCompare: () => void
}

export function useSnapshotCompareNavigation(
  leftId: Ref<string>,
  rightId: Ref<string>,
  left: Ref<AnySnap | null>,
  right: Ref<AnySnap | null>,
  error: Ref<string>,
  isOpen: Ref<boolean>,
  autoComparedOnce: Ref<boolean>,
  liveCompare: Ref<boolean>,
  snapshots: () => SnapshotItem[],
  loadSnapshotsForCompare: () => Promise<void>
): SnapshotCompareNavigationReturn {
  const toast = useToastStore()
  let liveTimer: number | null = null

  /**
   * Schedule live compare with debounce.
   */
  function scheduleLiveCompare(): void {
    if (!liveCompare.value) return
    if (!isOpen.value) return
    if (!leftId.value || !rightId.value) return
    if (leftId.value === rightId.value) return

    if (liveTimer) window.clearTimeout(liveTimer)
    liveTimer = window.setTimeout(() => {
      void loadSnapshotsForCompare()
    }, 200)
  }

  /**
   * Find snapshot index by ID.
   */
  function snapshotIndexById(id: string): number {
    const snaps = snapshots()
    return snaps.findIndex((s) => s?.snapshot_id === id)
  }

  /**
   * Pick baseline as left snapshot.
   */
  function pickBaselineLeft(): void {
    const base = snapshots().find((s) => s.baseline === true)
    if (!base) {
      toast.warning('No baseline snapshot found.')
      return
    }
    leftId.value = base.snapshot_id
  }

  /**
   * Pick most recent non-baseline as right snapshot.
   */
  function pickMostRecentNonBaselineAsRight(): void {
    const snaps = snapshots()
    if (!snaps.length) return

    const candidates = snaps.filter(
      (s) => s?.baseline !== true && s?.snapshot_id && s.snapshot_id !== leftId.value
    )

    if (!candidates.length) return

    const sorted = [...candidates].sort((a, b) => {
      const aDate = a.updated_at || a.created_at || ''
      const bDate = b.updated_at || b.created_at || ''
      return String(bDate).localeCompare(String(aDate))
    })

    if (sorted[0]?.snapshot_id) {
      rightId.value = sorted[0].snapshot_id
    }
  }

  /**
   * Swap left and right sides.
   */
  function swapSides(): void {
    const tmp = leftId.value
    leftId.value = rightId.value
    rightId.value = tmp
  }

  /**
   * Clear comparison state.
   */
  function clearCompare(): void {
    leftId.value = ''
    rightId.value = ''
    left.value = null
    right.value = null
    error.value = ''
    autoComparedOnce.value = false
    if (liveTimer) {
      window.clearTimeout(liveTimer)
      liveTimer = null
    }
  }

  /**
   * Step right snapshot by delta.
   */
  function stepRight(delta: number): void {
    const snaps = snapshots()
    if (!snaps.length) return

    const curIdx = snapshotIndexById(rightId.value)
    if (curIdx < 0) {
      pickMostRecentNonBaselineAsRight()
      scheduleLiveCompare()
      return
    }

    let nextIdx = curIdx + delta
    nextIdx = Math.max(0, Math.min(snaps.length - 1, nextIdx))

    const next = snaps[nextIdx]
    if (!next?.snapshot_id) return

    if (next.snapshot_id === leftId.value) {
      const altIdx = Math.max(0, Math.min(snaps.length - 1, nextIdx + delta))
      const alt = snaps[altIdx]
      if (alt?.snapshot_id && alt.snapshot_id !== leftId.value) {
        rightId.value = alt.snapshot_id
        scheduleLiveCompare()
        return
      }
    }

    rightId.value = next.snapshot_id
    scheduleLiveCompare()
  }

  /**
   * Step left snapshot by delta.
   */
  function stepLeft(delta: number): void {
    const snaps = snapshots()
    if (!snaps.length) return

    const curIdx = snapshotIndexById(leftId.value)
    if (curIdx < 0) {
      pickBaselineLeft()
      scheduleLiveCompare()
      return
    }

    let nextIdx = curIdx + delta
    nextIdx = Math.max(0, Math.min(snaps.length - 1, nextIdx))

    const next = snaps[nextIdx]
    if (!next?.snapshot_id) return

    if (next.snapshot_id === rightId.value) {
      const altIdx = Math.max(0, Math.min(snaps.length - 1, nextIdx + delta))
      const alt = snaps[altIdx]
      if (alt?.snapshot_id && alt.snapshot_id !== rightId.value) {
        leftId.value = alt.snapshot_id
        scheduleLiveCompare()
        return
      }
    }

    leftId.value = next.snapshot_id
    scheduleLiveCompare()
  }

  // Auto-select Left=baseline when snapshots list changes and Left is empty
  watch(
    snapshots,
    (snaps) => {
      if (!snaps || !snaps.length) return
      if (leftId.value) return

      const base = snaps.find((s) => s.baseline === true)
      if (base?.snapshot_id) {
        leftId.value = base.snapshot_id
      }
    },
    { immediate: true }
  )

  // Auto-select Right=most recent non-baseline when Left is set
  watch(
    () => [snapshots(), leftId.value],
    () => {
      const snaps = snapshots()
      if (!snaps.length) return

      if (leftId.value && !rightId.value) {
        pickMostRecentNonBaselineAsRight()
        return
      }

      if (leftId.value && rightId.value && leftId.value === rightId.value) {
        rightId.value = ''
        pickMostRecentNonBaselineAsRight()
      }
    },
    { immediate: true }
  )

  // When opening panel, ensure both defaults are set
  watch(
    () => isOpen.value,
    (open) => {
      if (!open) return
      if (!leftId.value) pickBaselineLeft()
      if (leftId.value && !rightId.value) pickMostRecentNonBaselineAsRight()
    }
  )

  // Auto-run Compare when panel opens with both IDs set
  watch(
    () => [isOpen.value, leftId.value, rightId.value],
    async ([open, l, r]) => {
      if (!open) return
      if (!l || !r) return
      if (l === r) return
      if (autoComparedOnce.value) return

      autoComparedOnce.value = true
      await loadSnapshotsForCompare()
    },
    { immediate: true }
  )

  // Reset guards and timer when panel closes
  watch(
    () => isOpen.value,
    (open) => {
      if (!open) {
        autoComparedOnce.value = false
        if (liveTimer) {
          window.clearTimeout(liveTimer)
          liveTimer = null
        }
      }
    }
  )

  // Live compare triggers on id change
  watch(() => [leftId.value, rightId.value], () => {
    scheduleLiveCompare()
  })

  return {
    pickBaselineLeft,
    pickMostRecentNonBaselineAsRight,
    swapSides,
    clearCompare,
    stepRight,
    stepLeft,
    scheduleLiveCompare
  }
}
