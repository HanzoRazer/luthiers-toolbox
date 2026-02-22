/**
 * Composable for G-code export functionality.
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'
import { FALLBACK_POSTS, type PostProcessor, type AdaptiveParams } from './bridgeLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface GcodeExportState {
  availablePosts: Ref<PostProcessor[]>
  selectedPostId: Ref<string>
  postMode: Ref<string>
  exportRunning: Ref<boolean>
  loadPosts: () => Promise<void>
  exportGcode: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useGcodeExport(
  toolpathResult: Ref<any>,
  adaptiveParams: Ref<AdaptiveParams>,
  currentStage: Ref<number>,
  exportedGcode: Ref<string | null>,
  exportedFilename: Ref<string | null>
): GcodeExportState {
  const availablePosts = ref<PostProcessor[]>([])
  const selectedPostId = ref('GRBL')
  const postMode = ref('standard')
  const exportRunning = ref(false)

  async function loadPosts(): Promise<void> {
    try {
      const response = await api('/api/posts/')
      if (response.ok) {
        const data = await response.json()
        availablePosts.value = data.posts || []
      } else {
        throw new Error('Failed to load posts')
      }
    } catch (error) {
      console.error('Failed to load posts:', error)
      availablePosts.value = [...FALLBACK_POSTS]
    }
  }

  async function exportGcode(): Promise<void> {
    if (!toolpathResult.value || !selectedPostId.value) return

    exportRunning.value = true
    currentStage.value = 3

    try {
      const response = await api('/api/cam/toolpath/roughing/gcode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          moves: toolpathResult.value.moves,
          units: adaptiveParams.value.units,
          post: selectedPostId.value,
          post_mode: postMode.value
        })
      })

      if (!response.ok) {
        throw new Error(`G-code export failed: ${response.statusText}`)
      }

      const gcode = await response.text()
      exportedGcode.value = gcode

      // Download file
      const blob = new Blob([gcode], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const filename = `bridge_${selectedPostId.value.toLowerCase()}_${Date.now()}.nc`
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)

      exportedFilename.value = filename
      currentStage.value = 4
    } catch (error) {
      console.error('Export error:', error)
      alert(`G-code export failed: ${error}`)
    } finally {
      exportRunning.value = false
    }
  }

  return {
    availablePosts,
    selectedPostId,
    postMode,
    exportRunning,
    loadPosts,
    exportGcode
  }
}
