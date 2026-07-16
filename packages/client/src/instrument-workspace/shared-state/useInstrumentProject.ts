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

// SPINE-005 concurrency control (non-reactive, private to this module).
// `_loadGen` is a monotonic counter: every loadProject() and clearProject() bumps it,
// and any load may write shared state only while its captured generation is still the
// latest. This makes a superseded load a silent no-op — it can never publish another
// Project's data, error, or loading flag (latest-request-wins).
let _loadGen = 0
// `_saveInFlight` is the request-lifecycle single-flight guard for explicit commits. It
// is deliberately NOT a ref and NOT reset by loads, so no two commit requests are ever
// in flight in the same session, even across a Project switch. The reactive `_isSaving`
// flag above is the *display* signal and tracks only the active Project.
let _saveInFlight = false

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
   *
   * Latest-request-wins: concurrent or rapid loads (e.g. route A -> B) are serialized by
   * generation, not dropped. Only the newest request may write shared state; an older
   * request that resolves later is discarded without touching any flag. Switching to a
   * different Project quarantines the prior visible state first, so a failed load never
   * leaves the previous Project renderable under the new Project's identity.
   */
  async function loadProject(id: string): Promise<void> {
    const gen = ++_loadGen
    const switchingProject = _projectId.value !== id

    // The requested identity becomes active immediately (latest-request-wins for observers).
    _projectId.value = id
    if (switchingProject) {
      // Quarantine the previous Project so it cannot render under the new identity.
      _projectName.value = ''
      _state.value = null
      _isDirty.value = false
      _saveError.value = null
      _lastSavedAt.value = null
      _isSaving.value = false   // display only; the in-flight save's own guard still holds
    }
    _isLoading.value = true
    _loadError.value = null

    try {
      const response = await getDesignState(id)
      if (gen !== _loadGen) return   // superseded by a newer load — discard silently
      _projectName.value = response.name
      _state.value = response.design_state
      _isDirty.value = false
      _lastSavedAt.value = response.updated_at
    } catch (err) {
      if (gen !== _loadGen) return   // superseded — do not publish this error under another Project
      _loadError.value = err instanceof Error ? err.message : 'Failed to load project'
    } finally {
      if (gen === _loadGen) _isLoading.value = false
    }
  }

  /**
   * Clear the active project from memory.
   * Call when navigating away from instrument context.
   */
  function clearProject(): void {
    // Bump the load generation so any in-flight load cannot repopulate state after clear.
    _loadGen++
    _projectId.value = null
    _projectName.value = ''
    _state.value = null
    _isDirty.value = false
    _isLoading.value = false
    _isSaving.value = false
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
    // Single-flight: a second explicit commit while one is pending issues no request,
    // returns false, and leaves the caller's draft and the active save's metadata intact.
    if (_saveInFlight) return false

    // Capture the Project this write targets and the load generation at submit time.
    // The server write always stands; we only refuse to apply its response to client
    // state if the active Project has since changed (navigation A -> B mid-save).
    const targetId = _projectId.value
    const genAtSave = _loadGen

    _saveInFlight = true
    _isSaving.value = true
    _saveError.value = null

    try {
      const merged: InstrumentProjectData = { ..._state.value, ...patch }
      const response = await putDesignState(targetId, merged, message)
      if (_projectId.value === targetId && genAtSave === _loadGen) {
        _state.value = response.design_state
        _isDirty.value = false
        _lastSavedAt.value = response.updated_at
      }
      // The commit succeeded on the server regardless of the current active Project.
      return true
    } catch (err) {
      if (_projectId.value === targetId && genAtSave === _loadGen) {
        _saveError.value = err instanceof Error ? err.message : 'Save failed'
      }
      return false
    } finally {
      // Single-flight guarantees exactly one save owns _isSaving at a time, so the
      // completing save always clears the display flag here — even when its response was
      // discarded for a superseded Project (otherwise the "Saving…" indicator could stick
      // true after a same-id reload superseded the save). A newer save cannot have started
      // yet, since its guard is released on the next line, so this never clears another
      // save's indicator.
      _isSaving.value = false
      // Always release the request-lifecycle guard, even when the response was discarded
      // for a superseded Project — otherwise no future save could ever start.
      _saveInFlight = false
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
