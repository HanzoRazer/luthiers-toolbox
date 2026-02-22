/**
 * RiskTimelineRelief state composable.
 */
import { ref, type Ref } from 'vue'
import type { RiskJob, PresetFilter } from './riskTimelineTypes'

export interface RiskTimelineStateReturn {
  jobs: Ref<RiskJob[]>
  loading: Ref<boolean>
  exporting: Ref<boolean>
  presetFilter: Ref<PresetFilter>
  pipelineFilter: Ref<string>
  comparePrev: Ref<boolean>
}

export function useRiskTimelineState(): RiskTimelineStateReturn {
  const jobs = ref<RiskJob[]>([])
  const loading = ref(false)
  const exporting = ref(false)

  const presetFilter = ref<PresetFilter>('Any')
  const pipelineFilter = ref<string>('Any')
  const comparePrev = ref(false)

  return {
    jobs,
    loading,
    exporting,
    presetFilter,
    pipelineFilter,
    comparePrev
  }
}
