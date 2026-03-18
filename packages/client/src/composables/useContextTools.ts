import { computed } from 'vue'
import { CALCULATOR_REGISTRY, type ModuleKey } from '@/design-utilities/calculator-registry'

export function useContextTools(module: ModuleKey) {
  const tools = computed(() =>
    CALCULATOR_REGISTRY[module] ?? []
  )
  return { tools }
}
