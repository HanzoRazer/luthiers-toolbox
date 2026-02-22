/**
 * ReliefKernelLab state composable.
 */
import { ref, type Ref } from 'vue'
import type {
  HeightmapData,
  FinishingResult,
  SimBridgeOutput,
  ComparisonRow
} from './reliefKernelTypes'

export interface ReliefKernelStateReturn {
  file: Ref<File | null>
  map: Ref<HeightmapData | null>
  result: Ref<FinishingResult | null>
  reliefSimBridgeOut: Ref<SimBridgeOutput | null>
  toolD: Ref<number>
  stepdown: Ref<number>
  scallop: Ref<number>
  stockThickness: Ref<number>
  units: Ref<'mm' | 'inch'>
  useDynamicScallop: Ref<boolean>
  comparisons: Ref<ComparisonRow[]>
  isComparing: Ref<boolean>
  selectedComparisonName: Ref<string | null>
}

export function useReliefKernelState(): ReliefKernelStateReturn {
  const file = ref<File | null>(null)
  const map = ref<HeightmapData | null>(null)
  const result = ref<FinishingResult | null>(null)
  const reliefSimBridgeOut = ref<SimBridgeOutput | null>(null)

  const toolD = ref(6.0)
  const stepdown = ref(2.0)
  const scallop = ref(0.05)
  const stockThickness = ref(5.0)
  const units = ref<'mm' | 'inch'>('mm')
  const useDynamicScallop = ref(false)

  const comparisons = ref<ComparisonRow[]>([])
  const isComparing = ref(false)
  const selectedComparisonName = ref<string | null>(null)

  return {
    file,
    map,
    result,
    reliefSimBridgeOut,
    toolD,
    stepdown,
    scallop,
    stockThickness,
    units,
    useDynamicScallop,
    comparisons,
    isComparing,
    selectedComparisonName
  }
}
