/**
 * CompareLab storage composable.
 */
import type { Ref } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import type { CanonicalGeometry } from '@/utils/geometry'
import { normalizeGeometryPayload } from '@/utils/geometry'
import type { ExportFormat } from './compareLabTypes'
import { STORAGE_KEYS } from './compareLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CompareLabStorageReturn {
  persistGeometry: (geometry: CanonicalGeometry) => void
  loadPersistedGeometry: () => void
  extractNeckContext: () => void
  handleFile: (event: Event) => void
  triggerFileDialog: () => void
  loadExportState: () => void
  saveExportState: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useCompareLabStorage(
  route: RouteLocationNormalizedLoaded,
  fileInput: Ref<HTMLInputElement | null>,
  currentGeometry: Ref<CanonicalGeometry | null>,
  neckProfileContext: Ref<string | null>,
  neckSectionContext: Ref<string | null>,
  selectedPresetId: Ref<string>,
  filenameTemplate: Ref<string>,
  exportFormat: Ref<ExportFormat>
): CompareLabStorageReturn {
  /**
   * Persist geometry to localStorage.
   */
  function persistGeometry(geometry: CanonicalGeometry): void {
    localStorage.setItem(STORAGE_KEYS.GEOMETRY, JSON.stringify(geometry))
  }

  /**
   * Load persisted geometry from localStorage.
   */
  function loadPersistedGeometry(): void {
    const raw = localStorage.getItem(STORAGE_KEYS.GEOMETRY)
    if (!raw) return

    try {
      currentGeometry.value = JSON.parse(raw)
      extractNeckContext()
    } catch (error) {
      console.error('Failed to parse stored geometry', error)
    }
  }

  /**
   * Extract neck context from various sources.
   */
  function extractNeckContext(): void {
    // Priority 1: URL query parameters
    const queryProfile = route.query.neck_profile as string
    const querySection = route.query.neck_section as string

    if (queryProfile) {
      neckProfileContext.value = queryProfile
      localStorage.setItem(STORAGE_KEYS.NECK_PROFILE, queryProfile)
    }
    if (querySection) {
      neckSectionContext.value = querySection
      localStorage.setItem(STORAGE_KEYS.NECK_SECTION, querySection)
    }

    // Priority 2: Geometry metadata
    if (!neckProfileContext.value && currentGeometry.value?.paths?.[0]?.meta) {
      const meta = currentGeometry.value.paths[0].meta
      if (typeof meta.neck_profile === 'string') {
        neckProfileContext.value = meta.neck_profile
        localStorage.setItem(STORAGE_KEYS.NECK_PROFILE, meta.neck_profile)
      }
      if (typeof meta.neck_section === 'string') {
        neckSectionContext.value = meta.neck_section
        localStorage.setItem(STORAGE_KEYS.NECK_SECTION, meta.neck_section)
      }
    }

    // Priority 3: Geometry source string parsing
    if (!neckProfileContext.value && currentGeometry.value?.source) {
      const sourceParts = currentGeometry.value.source.split(':')
      if (sourceParts.length >= 3 && sourceParts[0] === 'NeckLab') {
        neckProfileContext.value = sourceParts[1]
        neckSectionContext.value = sourceParts[2]
        localStorage.setItem(STORAGE_KEYS.NECK_PROFILE, sourceParts[1])
        localStorage.setItem(STORAGE_KEYS.NECK_SECTION, sourceParts[2])
      }
    }

    // Priority 4: localStorage fallback
    if (!neckProfileContext.value) {
      neckProfileContext.value = localStorage.getItem(STORAGE_KEYS.NECK_PROFILE)
    }
    if (!neckSectionContext.value) {
      neckSectionContext.value = localStorage.getItem(STORAGE_KEYS.NECK_SECTION)
    }
  }

  /**
   * Handle file input change.
   */
  function handleFile(event: Event): void {
    const target = event.target as HTMLInputElement
    if (!target.files?.length) return

    const file = target.files[0]
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result))
        const normalized = normalizeGeometryPayload(parsed)
        if (normalized) {
          currentGeometry.value = normalized
          persistGeometry(normalized)
          extractNeckContext()
        }
      } catch (error) {
        console.error('Invalid geometry file', error)
      } finally {
        target.value = ''
      }
    }
    reader.readAsText(file)
  }

  /**
   * Trigger file dialog.
   */
  function triggerFileDialog(): void {
    fileInput.value?.click()
  }

  /**
   * Load export state from localStorage.
   */
  function loadExportState(): void {
    try {
      const savedPresetId = localStorage.getItem(STORAGE_KEYS.PRESET_ID)
      if (savedPresetId) selectedPresetId.value = savedPresetId

      const savedTemplate = localStorage.getItem(STORAGE_KEYS.TEMPLATE)
      if (savedTemplate) filenameTemplate.value = savedTemplate

      const savedFormat = localStorage.getItem(STORAGE_KEYS.FORMAT)
      if (savedFormat && ['svg', 'png', 'csv'].includes(savedFormat)) {
        exportFormat.value = savedFormat as ExportFormat
      }
    } catch (error) {
      console.error('Failed to load export state:', error)
    }
  }

  /**
   * Save export state to localStorage.
   */
  function saveExportState(): void {
    try {
      localStorage.setItem(STORAGE_KEYS.PRESET_ID, selectedPresetId.value)
      localStorage.setItem(STORAGE_KEYS.TEMPLATE, filenameTemplate.value)
      localStorage.setItem(STORAGE_KEYS.FORMAT, exportFormat.value)
    } catch (error) {
      console.error('Failed to save export state:', error)
    }
  }

  return {
    persistGeometry,
    loadPersistedGeometry,
    extractNeckContext,
    handleFile,
    triggerFileDialog,
    loadExportState,
    saveExportState
  }
}
