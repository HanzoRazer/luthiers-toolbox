/**
 * SnapshotComparePanel state composable.
 */
import { ref, computed, watch, onMounted, type Ref, type ComputedRef } from 'vue'
import type { AnySnap } from './snapshotCompareTypes'

const KEYBOARD_HINTS_KEY = 'compare.showKeyboardHints'

export interface SnapshotCompareStateReturn {
  leftId: Ref<string>
  rightId: Ref<string>
  left: Ref<AnySnap | null>
  right: Ref<AnySnap | null>
  loading: Ref<boolean>
  error: Ref<string>
  isOpen: Ref<boolean>
  autoComparedOnce: Ref<boolean>
  liveCompare: Ref<boolean>
  showKeyboardHints: Ref<boolean>
  canCompare: ComputedRef<boolean>
}

export function useSnapshotCompareState(): SnapshotCompareStateReturn {
  const leftId = ref<string>('')
  const rightId = ref<string>('')
  const left = ref<AnySnap | null>(null)
  const right = ref<AnySnap | null>(null)
  const loading = ref(false)
  const error = ref<string>('')
  const isOpen = ref(false)
  const autoComparedOnce = ref(false)
  const liveCompare = ref(false)
  const showKeyboardHints = ref(true)

  const canCompare = computed(
    () => !!leftId.value && !!rightId.value && leftId.value !== rightId.value
  )

  // Restore keyboard hints preference from localStorage
  onMounted(() => {
    const savedHints = localStorage.getItem(KEYBOARD_HINTS_KEY)
    if (savedHints !== null) {
      showKeyboardHints.value = savedHints === 'true'
    }
  })

  // Persist keyboard hints preference
  watch(showKeyboardHints, (val) => {
    localStorage.setItem(KEYBOARD_HINTS_KEY, String(val))
  })

  return {
    leftId,
    rightId,
    left,
    right,
    loading,
    error,
    isOpen,
    autoComparedOnce,
    liveCompare,
    showKeyboardHints,
    canCompare
  }
}
