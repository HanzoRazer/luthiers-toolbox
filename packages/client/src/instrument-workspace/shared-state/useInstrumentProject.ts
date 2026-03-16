// packages/client/src/instrument-workspace/shared-state/useInstrumentProject.ts
/**
 * useInstrumentProject (HUB-001)
 *
 * The primary composable for reading and writing Instrument Project state.
 *
 * ARCHITECTURE RULES (PLATFORM_ARCHITECTURE.md):
 *   - This composable is the ONLY way components should touch project state
 *   - Components read from `spec`, `bridgeState`, `materialSelection`, etc.
 *   - Components call `commitSpec()`, `commitBridgeState()`, etc. on explicit user action
 *   - NEVER auto-commit — always wait for user confirmation
 *   - Derived values (break angle, fret positions, tension) are computed by engines, not stored here
 *
 * Usage:
 *   const { spec, isLoaded, commitSpec, loadProject } = useInstrumentProject()
 *
 *   // Load on mount
 *   onMounted(() => loadProject(projectId))
 *
 *   // Local editing
 *   const localScale = ref(spec.value?.scale_length_mm ?? 648)
 *
 *   // Explicit commit on user action
 *   async function handleSave() {
 *     await commitSpec({ ...spec.value, scale_length_mm: localScale.value })
 *   }
 *
 * Stores scheduled for retirement as this composable is adopted (HUB-002):
 *   instrumentGeometryStore — spec fields migrate here; CAM preview remains in store
 *   geometry.ts store       — bridge geometry migrates to commitBridgeState()
 */

import { ref, computed, readonly } from 'vue'
import {
  getDesignState,
  putDesignState,
  type InstrumentProjectData,
  type InstrumentSpec,
  type BridgeState,
  type NeckState,
  type MaterialSelection,
  type InstrumentCategory,
  INSTRUMENT_DEFAULTS,
} from '@/api/projects'

// ---------------------------------------------------------------------------
// Module-level singleton state
// The project state is shared across all components in the session.
// Only one project is active at a time.
// ---------------------------------------------------------------------------

const _projectId = ref<string | null>(null)
const _projectName = ref<string>('')
const _state = ref<InstrumentProjectData | null>(null)
const _isLoading = ref(false)
const _isSaving = ref(false)
const _loadError = ref<string | null>(null)
const _saveError = ref<string | null>(null)
const _lastSavedAt = ref<string | null>(null)
const _isDirty = ref(false)   // local edits not yet committed

// ---------------------------------------------------------------------------
// Public composable
// ---------------------------------------------------------------------------

export function useInstrumentProject() {

  // --- Readonly state accessors ---

  const projectId = readonly(_projectId)
  const projectName = readonly(_projectName)
  const isLoading = readonly(_isLoading)
  const isSaving = readonly(_isSaving)
  const loadError = readonly(_loadError)
  const saveError = readonly(_saveError)
  const lastSavedAt = readonly(_lastSavedAt)
  const isDirty = readonly(_isDirty)

  /** Whether a project is loaded and has typed design state */
  const isLoaded = computed(() => _state.value !== null && _projectId.value !== null)

  /** Whether project has minimum data for CAM operations */
  const isCamReady = computed(() =>
    _state.value?.spec != null && _state.value?.instrument_type != null
  )

  // --- Sub-state accessors (readonly — never mutate directly) ---

  const instrumentType = computed(() => _state.value?.instrument_type ?? null)
  const spec = computed(() => _state.value?.spec ?? null)
  const blueprintGeometry = computed(() => _state.value?.blueprint_geometry ?? null)
  const bridgeState = computed(() => _state.value?.bridge_state ?? null)
  const neckState = computed(() => _state.value?.neck_state ?? null)
  const materialSelection = computed(() => _state.value?.material_selection ?? null)
  const analyzerObservations = computed(() => _state.value?.analyzer_observations ?? [])
  const manufacturingState = computed(() => _state.value?.manufacturing_state ?? null)

  // Convenience reads used by multiple stages
  const scaleLengthMm = computed(() => spec.value?.scale_length_mm ?? null)
  const fretCount = computed(() => spec.value?.fret_count ?? null)
  const neckAngleDeg = computed(() => spec.value?.neck_angle_degrees ?? null)

  // ---------------------------------------------------------------------------
  // LOAD
  // ---------------------------------------------------------------------------

  /**
   * Load a project's design state from the server.
   * Call on mount or when the active project changes.
   */
  async function loadProject(id: string): Promise<void> {
    if (_isLoading.value) return
    _isLoading.value = true
    _loadError.value = null

    try {
      const response = await getDesignState(id)
      _projectId.value = id
      _projectName.value = response.name
      _state.value = response.design_state
      _isDirty.value = false
      _lastSavedAt.value = response.updated_at
    } catch (err) {
      _loadError.value = err instanceof Error ? err.message : 'Failed to load project'
    } finally {
      _isLoading.value = false
    }
  }

  /**
   * Clear the active project from memory.
   * Call when navigating away from instrument context.
   */
  function clearProject(): void {
    _projectId.value = null
    _projectName.value = ''
    _state.value = null
    _isDirty.value = false
    _loadError.value = null
    _saveError.value = null
    _lastSavedAt.value = null
  }

  // ---------------------------------------------------------------------------
  // COMMIT helpers — explicit user-initiated writes
  // Each commit function writes ONE section of InstrumentProjectData.
  // Never auto-commit on input change.
  // ---------------------------------------------------------------------------

  async function _commit(
    patch: Partial<InstrumentProjectData>,
    message: string,
  ): Promise<boolean> {
    if (!_projectId.value || !_state.value) {
      _saveError.value = 'No active project to commit to.'
      return false
    }
    _isSaving.value = true
    _saveError.value = null

    try {
      const merged: InstrumentProjectData = { ..._state.value, ...patch }
      const response = await putDesignState(_projectId.value, merged, message)
      _state.value = response.design_state
      _isDirty.value = false
      _lastSavedAt.value = response.updated_at
      return true
    } catch (err) {
      _saveError.value = err instanceof Error ? err.message : 'Save failed'
      return false
    } finally {
      _isSaving.value = false
    }
  }

  /**
   * Commit instrument type and spec.
   * Called by Instrument Hub when builder changes core dimensions.
   */
  async function commitSpec(
    newSpec: InstrumentSpec,
    newType?: InstrumentCategory,
  ): Promise<boolean> {
    return _commit(
      {
        spec: newSpec,
        ...(newType ? { instrument_type: newType } : {}),
      },
      'Updated instrument spec',
    )
  }

  /**
   * Commit instrument type only (e.g. when switching from acoustic to electric).
   * Optionally seeds a default spec for the new type.
   */
  async function commitInstrumentType(
    type: InstrumentCategory,
    seedDefaultSpec = false,
  ): Promise<boolean> {
    const patch: Partial<InstrumentProjectData> = { instrument_type: type }
    if (seedDefaultSpec && !_state.value?.spec) {
      const defaults = INSTRUMENT_DEFAULTS[type]
      patch.spec = {
        scale_length_mm: defaults.scale_length_mm ?? 648,
        fret_count: defaults.fret_count ?? 22,
        string_count: defaults.string_count ?? 6,
        nut_width_mm: defaults.nut_width_mm ?? 42,
        heel_width_mm: defaults.heel_width_mm ?? 56,
        neck_angle_degrees: defaults.neck_angle_degrees ?? 0,
        neck_joint_type: defaults.neck_joint_type ?? 'bolt_on',
        body_join_fret: defaults.body_join_fret ?? 14,
        tremolo_style: defaults.tremolo_style ?? 'hardtail',
      }
    }
    return _commit(patch, `Instrument type set to ${type}`)
  }

  /**
   * Commit bridge geometry state.
   * Called by Bridge Lab on explicit "Apply Bridge Geometry" action.
   * Never called automatically on bridge calculator input change.
   */
  async function commitBridgeState(state: BridgeState): Promise<boolean> {
    const withTimestamp: BridgeState = {
      ...state,
      last_committed_at: new Date().toISOString(),
    }
    return _commit({ bridge_state: withTimestamp }, 'Bridge geometry committed')
  }

  /**
   * Commit neck geometry state.
   */
  async function commitNeckState(state: NeckState): Promise<boolean> {
    return _commit({ neck_state: state }, 'Neck geometry committed')
  }

  /**
   * Commit material selection.
   * Called by Instrument Hub material selector on user confirmation.
   */
  async function commitMaterialSelection(selection: MaterialSelection): Promise<boolean> {
    return _commit({ material_selection: selection }, 'Material selection updated')
  }

  /**
   * Mark a local edit without committing.
   * Used to track unsaved changes (shows dirty indicator in UI).
   */
  function markDirty(): void {
    _isDirty.value = true
  }

  // ---------------------------------------------------------------------------
  // UTILITIES
  // ---------------------------------------------------------------------------

  /**
   * Get a default spec for the current or given instrument type.
   * Used to seed inputs when no spec exists yet.
   */
  function getDefaultSpec(type?: InstrumentCategory): Partial<InstrumentSpec> {
    const t = type ?? _state.value?.instrument_type ?? 'electric_guitar'
    return INSTRUMENT_DEFAULTS[t] ?? INSTRUMENT_DEFAULTS.electric_guitar
  }

  /**
   * Whether a specific manufacturing operation has been recorded as complete.
   */
  function isOperationComplete(operation: string): boolean {
    return _state.value?.manufacturing_state?.operations_completed?.includes(operation) ?? false
  }

  return {
    // Identity
    projectId,
    projectName,

    // Loading state
    isLoading,
    isSaving,
    loadError,
    saveError,
    lastSavedAt,
    isDirty,

    // Derived status
    isLoaded,
    isCamReady,

    // Sub-state (readonly computed)
    instrumentType,
    spec,
    blueprintGeometry,
    bridgeState,
    neckState,
    materialSelection,
    analyzerObservations,
    manufacturingState,

    // Convenience reads
    scaleLengthMm,
    fretCount,
    neckAngleDeg,

    // Load / unload
    loadProject,
    clearProject,

    // Explicit commits (never auto-trigger)
    commitSpec,
    commitInstrumentType,
    commitBridgeState,
    commitNeckState,
    commitMaterialSelection,

    // Local tracking
    markDirty,

    // Utilities
    getDefaultSpec,
    isOperationComplete,
  }
}
