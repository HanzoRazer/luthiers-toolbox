/**
 * AudioAnalyzer file management composable.
 */
import { computed } from 'vue'
import type { Ref, ShallowRef, ComputedRef, Component } from 'vue'
import { pickRenderer, getRendererCategory } from '@/tools/audio_analyzer/renderers'
import { findSiblingPeaksRelpath } from '@/tools/audio_analyzer/packHelpers'
import type { NormalizedPack, NormalizedFileEntry } from './audioAnalyzerTypes'

// ============================================================================
// Types
// ============================================================================

export interface AudioAnalyzerFilesReturn {
  activeEntry: ComputedRef<NormalizedFileEntry | null>
  activeBytes: ComputedRef<Uint8Array>
  peaksBytes: ComputedRef<Uint8Array | null>
  currentRenderer: ComputedRef<Component | null>
  uniqueKinds: ComputedRef<string[]>
  kindCounts: ComputedRef<Record<string, number>>
  filteredFiles: ComputedRef<NormalizedFileEntry[]>
  getCategory: (kind: string) => string
  formatBytes: (bytes: number) => string
  selectFile: (relpath: string) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useAudioAnalyzerFiles(
  pack: ShallowRef<NormalizedPack | null>,
  activePath: Ref<string>,
  kindFilter: Ref<string>
): AudioAnalyzerFilesReturn {
  // Current active file entry
  const activeEntry = computed<NormalizedFileEntry | null>(() => {
    if (!pack.value || !activePath.value) return null
    return pack.value.files.find((f) => f.relpath === activePath.value) ?? null
  })

  // Current active file bytes
  const activeBytes = computed<Uint8Array>(() => {
    if (!pack.value || !activePath.value) return new Uint8Array(0)
    return pack.value.resolveFile(activePath.value) ?? new Uint8Array(0)
  })

  // Sibling peaks bytes for spectrum CSV files (analysis.json)
  const peaksBytes = computed<Uint8Array | null>(() => {
    if (!pack.value || !activePath.value) return null
    const siblingPath = findSiblingPeaksRelpath(activePath.value)
    if (!siblingPath) return null
    return pack.value.resolveFile(siblingPath) ?? null
  })

  // Dynamically pick renderer based on file kind
  const currentRenderer = computed<Component | null>(() => {
    if (!activeEntry.value) return null
    return pickRenderer(activeEntry.value.kind)
  })

  // Unique kinds for filter dropdown
  const uniqueKinds = computed<string[]>(() => {
    if (!pack.value) return []
    const kinds = new Set(pack.value.files.map((f) => f.kind))
    return Array.from(kinds).sort()
  })

  // Kind counts for debug panel
  const kindCounts = computed<Record<string, number>>(() => {
    if (!pack.value) return {}
    const counts: Record<string, number> = {}
    for (const f of pack.value.files) {
      counts[f.kind] = (counts[f.kind] || 0) + 1
    }
    return counts
  })

  // Filtered file list
  const filteredFiles = computed<NormalizedFileEntry[]>(() => {
    if (!pack.value) return []
    if (!kindFilter.value) return pack.value.files
    return pack.value.files.filter((f) => f.kind === kindFilter.value)
  })

  function getCategory(kind: string): string {
    return getRendererCategory(kind)
  }

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  function selectFile(relpath: string): void {
    activePath.value = relpath
  }

  return {
    activeEntry,
    activeBytes,
    peaksBytes,
    currentRenderer,
    uniqueKinds,
    kindCounts,
    filteredFiles,
    getCategory,
    formatBytes,
    selectFile
  }
}
