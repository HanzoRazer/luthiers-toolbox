/**
 * useGcodeFetcher — Fetches G-code text from inline or attachment source.
 *
 * Phase 2 of Toolpath Visualizer integration.
 *
 * Handles two cases:
 * 1. Inline G-code (< 200KB): Returns `result.gcode.text` directly
 * 2. Attachment G-code (>= 200KB): Fetches from `/api/rmos/runs_v2/attachments/{sha256}`
 *
 * Usage:
 *   const { gcodeText, isLoading, error } = useGcodeFetcher(result)
 *
 *   <ToolpathPlayer v-if="gcodeText" :gcode="gcodeText" />
 *   <div v-else-if="isLoading">Loading toolpath...</div>
 *   <div v-else-if="error">{{ error }}</div>
 */

import { ref, watch, computed, type Ref } from 'vue'
import { downloadAttachment } from '@/sdk/rmos/runs'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface GcodeResult {
  gcode?: {
    inline?: boolean
    text?: string
    sha256?: string
  } | null
}

export interface UseGcodeFetcherReturn {
  /** The G-code text (inline or fetched from attachment) */
  gcodeText: Ref<string | undefined>
  /** True while fetching from attachment */
  isLoading: Ref<boolean>
  /** Error message if fetch failed */
  error: Ref<string | null>
  /** True if G-code is available (either inline or fetched) */
  hasGcode: Ref<boolean>
  /** True if G-code is stored as attachment (not inline) */
  isAttachment: Ref<boolean>
  /** Manually trigger a refetch (useful after error) */
  refetch: () => Promise<void>
}

// ---------------------------------------------------------------------------
// Cache for fetched attachments (avoid re-fetching same sha256)
// ---------------------------------------------------------------------------

const attachmentCache = new Map<string, string>()

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export function useGcodeFetcher(
  result: Ref<GcodeResult | null | undefined>
): UseGcodeFetcherReturn {
  const gcodeText = ref<string | undefined>(undefined)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Computed helpers
  const isAttachment = computed(() => {
    const gcode = result.value?.gcode
    return gcode != null && !gcode.inline && !!gcode.sha256
  })

  const hasGcode = computed(() => !!gcodeText.value)

  // Fetch attachment by sha256
  async function fetchAttachmentText(sha256: string): Promise<string> {
    // Check cache first
    const cached = attachmentCache.get(sha256)
    if (cached) {
      return cached
    }

    // Fetch from API
    const { blob } = await downloadAttachment(sha256)
    const text = await blob.text()

    // Cache for future use
    attachmentCache.set(sha256, text)

    return text
  }

  // Main fetch logic
  async function refetch(): Promise<void> {
    const gcode = result.value?.gcode

    // No gcode object
    if (!gcode) {
      gcodeText.value = undefined
      error.value = null
      return
    }

    // Case 1: Inline G-code
    if (gcode.inline && gcode.text) {
      gcodeText.value = gcode.text
      error.value = null
      return
    }

    // Case 2: Attachment G-code
    if (!gcode.inline && gcode.sha256) {
      isLoading.value = true
      error.value = null

      try {
        const text = await fetchAttachmentText(gcode.sha256)
        gcodeText.value = text
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Failed to fetch G-code'
        error.value = msg
        gcodeText.value = undefined
      } finally {
        isLoading.value = false
      }
      return
    }

    // No valid gcode source
    gcodeText.value = undefined
    error.value = null
  }

  // Watch for result changes and auto-fetch
  watch(
    () => result.value?.gcode,
    () => {
      refetch()
    },
    { immediate: true, deep: true }
  )

  return {
    gcodeText,
    isLoading,
    error,
    hasGcode,
    isAttachment,
    refetch,
  }
}

export default useGcodeFetcher
