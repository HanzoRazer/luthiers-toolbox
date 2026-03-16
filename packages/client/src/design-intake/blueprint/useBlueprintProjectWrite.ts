// packages/client/src/design-intake/blueprint/composables/useBlueprintProjectWrite.ts
/**
 * useBlueprintProjectWrite (BLUE-003)
 *
 * Composable for saving Blueprint Lab pipeline results into the Instrument
 * Project Graph after the 4-phase workflow completes.
 *
 * Used inside BlueprintLab.vue — call saveToProject() when the builder
 * clicks "Save to Project" at the end of the workflow.
 *
 * Flow:
 *   Blueprint Lab workflow completes
 *       ↓
 *   Builder reviews extracted geometry
 *       ↓
 *   Clicks "Save to Project"
 *       ↓
 *   useBlueprintProjectWrite.saveToProject()
 *       ↓
 *   POST /api/blueprint/save-to-project/{project_id}
 *       ↓
 *   BlueprintDerivedGeometry written into InstrumentProjectData.blueprint_geometry
 *
 * Provenance rules (BLUE-004):
 *   - source is always recorded ('photo' | 'dxf' | 'manual')
 *   - confidence from AI phase 1 analysis
 *   - blueprint_original preserved when user manually overrides
 *
 * See docs/PLATFORM_ARCHITECTURE.md — Layer 2 / Blueprint.
 */

import { ref, computed } from 'vue'
import { api } from '@/services/apiBase'

// ---------------------------------------------------------------------------
// Types (matching backend SaveBlueprintToProjectRequest)
// ---------------------------------------------------------------------------

export interface BlueprintPipelineOutputs {
  /** Phase 1 AI analysis result — the 'analysis' dict from AnalysisResponse */
  analysisResult?: Record<string, unknown>
  /** Phase 1.5 calibration result dict */
  calibrationResult?: Record<string, unknown>
  /** Phase 1.5 DimensionResponse dict */
  dimensionResult?: Record<string, unknown>
  /** Phase 3 body_size_mm dict */
  phase3BodySizeMm?: Record<string, number>
  /** Phase 4 linked dimensions */
  phase4LinkedDimensions?: Array<Record<string, unknown>>
  /** Body outline as [[x, y]...] in mm — if available from vectorizer */
  bodyOutlineMm?: Array<[number, number]>
  /** Source: 'photo' | 'dxf' | 'manual' */
  source?: 'photo' | 'dxf' | 'manual'
}

export interface SaveBlueprintResult {
  success: boolean
  project_id: string
  instrument_classification: string | null
  centerline_detected: boolean
  scale_detected: boolean
  confidence: number
  notes: string[]
  message: string
}

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export function useBlueprintProjectWrite() {
  const isSaving = ref(false)
  const saveError = ref<string | null>(null)
  const lastSaveResult = ref<SaveBlueprintResult | null>(null)

  const wasSaved = computed(() => lastSaveResult.value?.success === true)

  /**
   * Save Blueprint pipeline outputs into the active project.
   *
   * @param projectId  UUID of the target project
   * @param outputs    Collected pipeline outputs from useBlueprintWorkflow
   * @param instrumentTypeOverride  Optional explicit instrument type (overrides AI)
   */
  async function saveToProject(
    projectId: string,
    outputs: BlueprintPipelineOutputs,
    instrumentTypeOverride?: string,
  ): Promise<SaveBlueprintResult | null> {
    if (!projectId) {
      saveError.value = 'No active project. Open or create a project before saving blueprint geometry.'
      return null
    }

    isSaving.value = true
    saveError.value = null

    try {
      const payload = {
        analysis_result: outputs.analysisResult ?? null,
        calibration_result: outputs.calibrationResult ?? null,
        dimension_result: outputs.dimensionResult ?? null,
        phase3_body_size_mm: outputs.phase3BodySizeMm ?? null,
        phase4_linked_dimensions: outputs.phase4LinkedDimensions ?? null,
        body_outline_mm: outputs.bodyOutlineMm ?? null,
        source: outputs.source ?? 'photo',
        instrument_type_override: instrumentTypeOverride ?? null,
        commit_message: 'Blueprint import',
      }

      const response = await api(`/api/blueprint/save-to-project/${projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(err.detail || `HTTP ${response.status}`)
      }

      const result: SaveBlueprintResult = await response.json()
      lastSaveResult.value = result
      return result
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save blueprint to project'
      saveError.value = msg
      return null
    } finally {
      isSaving.value = false
    }
  }

  /**
   * Build the pipeline outputs object from useBlueprintWorkflow state.
   *
   * Call this inside BlueprintLab.vue to assemble the payload:
   *
   *   const { buildOutputsFromWorkflow, saveToProject } = useBlueprintProjectWrite()
   *   const outputs = buildOutputsFromWorkflow(workflow)
   *   await saveToProject(projectId, outputs)
   */
  function buildOutputsFromWorkflow(workflow: {
    analysis?: { scale?: string; scale_confidence?: string; blueprint_type?: string; detected_model?: string; dimensions?: unknown[] } | null
    calibration?: { ppi?: number; ppmm?: number; confidence?: number } | null
    vectorizedGeometry?: { body_size_mm?: Record<string, number> } | null
    phase4Result?: { linked_dimensions?: Array<Record<string, unknown>>; dimensions_mm?: [number, number] } | null
    uploadedFile?: File | null
  }): BlueprintPipelineOutputs {
    // Determine source from file type
    let source: 'photo' | 'dxf' | 'manual' = 'photo'
    if (workflow.uploadedFile?.name?.toLowerCase().endsWith('.dxf')) {
      source = 'dxf'
    }

    return {
      analysisResult: workflow.analysis ?? undefined,
      calibrationResult: workflow.calibration ?? undefined,
      dimensionResult: undefined,      // DimensionResponse — wire when /blueprint/dimensions is called
      phase3BodySizeMm: workflow.vectorizedGeometry?.body_size_mm ?? undefined,
      phase4LinkedDimensions: workflow.phase4Result?.linked_dimensions ?? undefined,
      bodyOutlineMm: undefined,         // Body outline points — wire when vectorizer exposes them
      source,
    }
  }

  function clearSaveState() {
    saveError.value = null
    lastSaveResult.value = null
  }

  return {
    // State
    isSaving,
    saveError,
    lastSaveResult,
    wasSaved,
    // Actions
    saveToProject,
    buildOutputsFromWorkflow,
    clearSaveState,
  }
}
