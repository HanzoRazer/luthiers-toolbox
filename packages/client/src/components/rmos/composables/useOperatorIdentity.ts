/**
 * Composable for operator identity management.
 * Handles localStorage persistence and effective operator ID computation.
 */
import { ref, computed, watch, type Ref, type ComputedRef } from 'vue'

const OPERATOR_ID_KEY = 'rmos.operator_id'

export interface OperatorIdentityState {
  myOperatorId: Ref<string>
  stampDecisionsWithOperator: Ref<boolean>
  effectiveOperatorId: ComputedRef<string>
  getDecidedByOrNull: () => string | null
}

export function useOperatorIdentity(currentOperatorProp: () => string | null | undefined): OperatorIdentityState {
  const myOperatorId = ref<string>('')
  const stampDecisionsWithOperator = ref<boolean>(true)

  // Load from localStorage on init
  try {
    myOperatorId.value = String(localStorage.getItem(OPERATOR_ID_KEY) || '')
  } catch {
    // localStorage not available
  }

  // Persist to localStorage on change
  watch(myOperatorId, (v) => {
    try {
      localStorage.setItem(OPERATOR_ID_KEY, String(v || ''))
    } catch {
      // localStorage not available
    }
  })

  // Effective operator: prop overrides localStorage
  const effectiveOperatorId = computed(() => {
    const fromProp = (currentOperatorProp() ?? '').trim()
    if (fromProp) return fromProp
    return (myOperatorId.value || '').trim()
  })

  // Get decided_by value for API calls
  function getDecidedByOrNull(): string | null {
    if (!stampDecisionsWithOperator.value) return null
    const v = effectiveOperatorId.value
    return v ? v : null
  }

  return {
    myOperatorId,
    stampDecisionsWithOperator,
    effectiveOperatorId,
    getDecidedByOrNull,
  }
}
