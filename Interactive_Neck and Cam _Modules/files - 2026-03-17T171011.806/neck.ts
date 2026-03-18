/**
 * stores/neck.ts
 *
 * Single Pinia store that owns all four neck composable instances and
 * keeps their shared inputs synchronised.
 *
 * Coupling chain (must stay in sync):
 *   useNeckTaper  →  width at every fret  →  useNeckProfile (shoulder width)
 *   useFretboard  →  fretStations, crownComp  →  useNeckProfile (back depth)
 *   useCamSpec    →  pitch angle, nut width  →  useHeadstockTransition
 *
 * The store is the synchronisation point.  Components call store actions
 * rather than reaching into composables directly.
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useFretboard } from '@/composables/useFretboard'
import { useNeckProfile } from '@/composables/useNeckProfile'
import { useNeckTaper } from '@/composables/useNeckTaper'
import { useHeadstockTransition, TRANSITION_PRESETS } from '@/composables/useHeadstockTransition'

export const useNeckStore = defineStore('neck', () => {

  // ── Composable instances ────────────────────────────────────────────────
  const fretboard  = useFretboard()
  const taper      = useNeckTaper()
  const transition = useHeadstockTransition()

  // NeckProfile receives the live fretStations ComputedRef so profileStations
  // stays reactive when fretboard spec changes (radius, scale length, etc.)
  const profile = useNeckProfile(
    fretboard.spec as any,
    fretboard.fretStations,   // ComputedRef<FretStation[]> — NOT .value
  )

  // ── Active sub-tab ──────────────────────────────────────────────────────
  const activeTab = ref<'taper' | 'fretboard' | 'profile' | 'transition'>('taper')

  // Preview fret for cross-section canvas
  const previewFret = ref(1)

  // ── Sync helpers ────────────────────────────────────────────────────────

  /**
   * Keep taper nutWidthMm in sync with fretboard nutWidthMm
   * and with transition nutWidthMm.
   * Call after any nut-width change.
   */
  function syncNutWidth(mm: number) {
    fretboard.setSpec('nutWidthMm', mm)
    taper.setSpec('nutWidthMm', mm)
    transition.setSpec('nutWidthMm', mm)
  }

  /**
   * Keep scale length in sync across taper and fretboard.
   */
  function syncScaleLength(mm: number) {
    fretboard.setSpec('scaleLengthMm', mm)
    taper.setSpec('scaleLengthMm', mm)
  }

  /**
   * Keep fret count in sync.
   */
  function syncFretCount(n: number) {
    fretboard.setSpec('fretCount', n)
    taper.setSpec('fretCount', n)
  }

  /**
   * Keep pitch angle in sync between useCamSpec (if wired) and transition.
   */
  function syncPitchAngle(deg: number) {
    transition.setSpec('pitchAngleDeg', deg)
  }

  /**
   * Keep neck depth at 1st fret in sync with transition.
   */
  function syncNeckDepth(mm: number) {
    profile.setSpec('depth1mm', mm)
    transition.setSpec('neckDepthMm', mm)
  }

  // ── Load transition preset ──────────────────────────────────────────────
  function loadTransitionPreset(name: string) {
    transition.loadPreset(name)
  }

  // ── Derived summaries for the UI status bar ────────────────────────────
  const summary = computed(() => ({
    scale:     fretboard.spec.scaleLengthMm,
    frets:     fretboard.spec.fretCount,
    nutWidth:  taper.spec.nutWidthMm,
    r1:        fretboard.spec.r1Inch,
    r2:        fretboard.spec.r2Inch,
    radType:   fretboard.spec.radiusType,
    crownNut:  fretboard.derived.value.crownNut,
    crown12:   fretboard.derived.value.crown12,
    crownLast: fretboard.derived.value.crownLast,
    backDepth1:  profile.backDepth(1).toFixed(2),
    backDepth12: profile.backDepth(12).toFixed(2),
    thinPoint:   transition.thinPointMm(transition.spec as any).toFixed(1),
    allGatesPass: [
      ...fretboard.gates.value,
      ...profile.gates.value,
      ...taper.gates.value,
      ...transition.gates.value,
    ].every(g => g.status === 'pass'),
  }))

  // ── Export payload (merges all four composables) ───────────────────────
  const fullExportPayload = computed(() => ({
    fretboard:  fretboard.exportPayload.value,
    taper:      taper.exportPayload.value,
    profile:    profile.exportPayload.value,
    transition: transition.exportPayload.value,
  }))

  return {
    // composable instances (read access)
    fretboard,
    taper,
    profile,
    transition,

    // UI state
    activeTab,
    previewFret,

    // sync actions
    syncNutWidth,
    syncScaleLength,
    syncFretCount,
    syncPitchAngle,
    syncNeckDepth,
    loadTransitionPreset,

    // derived
    summary,
    fullExportPayload,

    // re-export preset list for UI
    transitionPresets: Object.keys(TRANSITION_PRESETS),
  }
})
