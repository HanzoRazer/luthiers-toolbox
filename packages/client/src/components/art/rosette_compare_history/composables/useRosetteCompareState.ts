/**
 * RosetteCompareHistory state composable.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { CompareHistoryEntry } from './rosetteCompareTypes'

export interface RosetteCompareStateReturn {
  entries: Ref<CompareHistoryEntry[]>
  comparePresets: Ref<boolean>
  presetCompareA: Ref<string | null>
  presetCompareB: Ref<string | null>
  lane: ComputedRef<string>
  effectiveJobId: ComputedRef<string | null>
}

export function useRosetteCompareState(
  propLane: () => string | undefined,
  propJobId: () => string | null | undefined
): RosetteCompareStateReturn {
  const entries = ref<CompareHistoryEntry[]>([])
  const comparePresets = ref<boolean>(false)
  const presetCompareA = ref<string | null>(null)
  const presetCompareB = ref<string | null>(null)

  const lane = computed(() => propLane() ?? 'rosette')
  const effectiveJobId = computed(() => {
    const jid = propJobId()
    return (jid && jid.trim()) || null
  })

  return {
    entries,
    comparePresets,
    presetCompareA,
    presetCompareB,
    lane,
    effectiveJobId
  }
}
