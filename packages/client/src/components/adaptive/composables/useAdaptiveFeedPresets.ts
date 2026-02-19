/**
 * Composable for adaptive feed preset management.
 * Handles per-post preset storage and loading.
 */
import { ref, watch, type Ref } from 'vue'

export type AfMode = 'inherit' | 'comment' | 'inline_f' | 'mcode'

export interface AfPreset {
  mode: AfMode
  slowdown_threshold?: number | null
  inline_min_f?: number | null
  mcode_start?: string | null
  mcode_end?: string | null
}

const PRESETS_KEY = 'toolbox.af.presets'

function readPresets(): Record<string, AfPreset> {
  try {
    return JSON.parse(localStorage.getItem(PRESETS_KEY) || '{}')
  } catch {
    return {}
  }
}

function writePresets(p: Record<string, AfPreset>) {
  localStorage.setItem(PRESETS_KEY, JSON.stringify(p))
}

export interface AdaptiveFeedState {
  afMode: Ref<AfMode>
  afInlineMinF: Ref<number>
  afMStart: Ref<string>
  afMEnd: Ref<string>
  savePresetForPost: (postId: string) => void
  loadPresetForPost: (postId: string) => boolean
  resetPresetForPost: (postId: string) => void
  loadPrefs: () => void
  buildAdaptiveOverride: () => Record<string, unknown> | null
}

export function useAdaptiveFeedPresets(): AdaptiveFeedState {
  const afMode = ref<AfMode>('inherit')
  const afInlineMinF = ref(600)
  const afMStart = ref('M52 P')
  const afMEnd = ref('M52 P100')

  function savePresetForPost(postId: string) {
    if (!postId) return
    const presets = readPresets()
    presets[postId] = {
      mode: afMode.value,
      slowdown_threshold: undefined,
      inline_min_f: afMode.value === 'inline_f' ? afInlineMinF.value : undefined,
      mcode_start: afMode.value === 'mcode' ? afMStart.value : undefined,
      mcode_end: afMode.value === 'mcode' ? afMEnd.value : undefined,
    }
    writePresets(presets)
  }

  function loadPresetForPost(postId: string): boolean {
    if (!postId) return false
    const p = readPresets()[postId]
    if (!p) return false
    afMode.value = (p.mode || 'inherit') as AfMode
    if (p.inline_min_f != null) afInlineMinF.value = p.inline_min_f
    if (p.mcode_start) afMStart.value = p.mcode_start
    if (p.mcode_end) afMEnd.value = p.mcode_end
    return true
  }

  function resetPresetForPost(postId: string) {
    if (!postId) return
    const presets = readPresets()
    delete presets[postId]
    writePresets(presets)
    afMode.value = 'inherit'
  }

  function loadPrefs() {
    const saved = localStorage.getItem('toolbox.adaptiveFeed')
    if (saved) {
      try {
        const prefs = JSON.parse(saved)
        afMode.value = prefs.mode || 'inherit'
        afInlineMinF.value = prefs.inline_min_f || 600
        afMStart.value = prefs.mcode_start || 'M52 P'
        afMEnd.value = prefs.mcode_end || 'M52 P100'
      } catch (e) {
        console.warn('Failed to load adaptive feed prefs:', e)
      }
    }
  }

  function savePrefs() {
    localStorage.setItem(
      'toolbox.adaptiveFeed',
      JSON.stringify({
        mode: afMode.value,
        inline_min_f: afInlineMinF.value,
        mcode_start: afMStart.value,
        mcode_end: afMEnd.value,
      })
    )
  }

  // Auto-save on change
  watch([afMode, afInlineMinF, afMStart, afMEnd], savePrefs)

  function buildAdaptiveOverride(): Record<string, unknown> | null {
    if (afMode.value === 'inherit') {
      return null
    }

    const override: Record<string, unknown> = { mode: afMode.value }

    if (afMode.value === 'inline_f') {
      override.inline_min_f = afInlineMinF.value
    }

    if (afMode.value === 'mcode') {
      override.mcode_start = afMStart.value
      override.mcode_end = afMEnd.value
    }

    return override
  }

  return {
    afMode,
    afInlineMinF,
    afMStart,
    afMEnd,
    savePresetForPost,
    loadPresetForPost,
    resetPresetForPost,
    loadPrefs,
    buildAdaptiveOverride,
  }
}
