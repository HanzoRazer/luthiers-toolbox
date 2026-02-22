/**
 * ArtStudioRelief state composable.
 */
import { ref, type Ref } from 'vue'
import type { BackplotLoop, BackplotFocusPoint } from '@/types/cam'
import type { RiskAnalytics } from '@/api/camRisk'
import type { ReliefPresetConfig } from './artStudioReliefTypes'

// ============================================================================
// Types
// ============================================================================

export interface ArtStudioReliefStateReturn {
  // Design source
  reliefHeightmapPath: Ref<string>

  // Pipeline + backplot state
  results: Ref<Record<string, any> | null>
  selectedPathOpId: Ref<string | null>
  selectedOverlayOpId: Ref<string | null>
  showToolpath: Ref<boolean>
  focusPoint: Ref<BackplotFocusPoint | null>
  selectedIssueIndex: Ref<number | null>
  backplotLoops: Ref<BackplotLoop[]>

  // Risk state
  lastRiskAnalytics: Ref<RiskAnalytics | null>
  lastRiskReportError: Ref<string | null>
  lastRiskReportId: Ref<string | null>

  // Snapshot notes state
  noteEditorVisible: Ref<boolean>
  noteDraft: Ref<string>
  noteSaving: Ref<boolean>
  noteSaveError: Ref<string | null>

  // Preset state
  activePresetName: Ref<string | null>
  activePresetConfig: Ref<ReliefPresetConfig | null>
}

// ============================================================================
// Composable
// ============================================================================

export function useArtStudioReliefState(): ArtStudioReliefStateReturn {
  // Design source
  const reliefHeightmapPath = ref('workspace/art/relief/demo_relief_heightmap.png')

  // Pipeline + backplot state
  const results = ref<Record<string, any> | null>(null)
  const selectedPathOpId = ref<string | null>('relief_finish')
  const selectedOverlayOpId = ref<string | null>('relief_sim')
  const showToolpath = ref(true)
  const focusPoint = ref<BackplotFocusPoint | null>(null)
  const selectedIssueIndex = ref<number | null>(null)
  const backplotLoops = ref<BackplotLoop[]>([])

  // Risk state
  const lastRiskAnalytics = ref<RiskAnalytics | null>(null)
  const lastRiskReportError = ref<string | null>(null)
  const lastRiskReportId = ref<string | null>(null)

  // Snapshot notes state
  const noteEditorVisible = ref(false)
  const noteDraft = ref('')
  const noteSaving = ref(false)
  const noteSaveError = ref<string | null>(null)

  // Preset state
  const activePresetName = ref<string | null>(null)
  const activePresetConfig = ref<ReliefPresetConfig | null>(null)

  return {
    reliefHeightmapPath,
    results,
    selectedPathOpId,
    selectedOverlayOpId,
    showToolpath,
    focusPoint,
    selectedIssueIndex,
    backplotLoops,
    lastRiskAnalytics,
    lastRiskReportError,
    lastRiskReportId,
    noteEditorVisible,
    noteDraft,
    noteSaving,
    noteSaveError,
    activePresetName,
    activePresetConfig
  }
}
