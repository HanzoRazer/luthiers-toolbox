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
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useFretboard } from '@/design-utilities/lutherie/neck/useFretboard'
import { useNeckProfile } from '@/design-utilities/lutherie/neck/useNeckProfile'
import { useNeckTaper } from '@/design-utilities/lutherie/neck/useNeckTaper'
import { useHeadstockTransition, TRANSITION_PRESETS } from '@/design-utilities/lutherie/neck/useHeadstockTransition'

export const useNeckStore = defineStore('neck', () => {

  const fretboard  = useFretboard()
  const taper      = useNeckTaper()
  const transition = useHeadstockTransition()

  const profile = useNeckProfile(
    fretboard.spec as any,
    fretboard.fretStations,
  )

  const activeTab = ref<'taper' | 'fretboard' | 'profile' | 'transition'>('taper')
  const previewFret = ref(1)

  function syncNutWidth(mm: number) {
    fretboard.setSpec('nutWidthMm', mm)
    taper.setSpec('nutWidthMm', mm)
    transition.setSpec('nutWidthMm', mm)
  }

  function syncScaleLength(mm: number) {
    fretboard.setSpec('scaleLengthMm', mm)
    taper.setSpec('scaleLengthMm', mm)
  }

  function syncFretCount(n: number) {
    fretboard.setSpec('fretCount', n)
    taper.setSpec('fretCount', n)
  }

  function syncPitchAngle(deg: number) {
    transition.setSpec('pitchAngleDeg', deg)
  }

  function syncNeckDepth(mm: number) {
    profile.setSpec('depth1mm', mm)
    transition.setSpec('neckDepthMm', mm)
  }

  function loadTransitionPreset(name: string) {
    transition.loadPreset(name)
  }

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

  const fullExportPayload = computed(() => ({
    fretboard:  fretboard.exportPayload.value,
    taper:      taper.exportPayload.value,
    profile:    profile.exportPayload.value,
    transition: transition.exportPayload.value,
  }))

  return {
    fretboard,
    taper,
    profile,
    transition,
    activeTab,
    previewFret,
    syncNutWidth,
    syncScaleLength,
    syncFretCount,
    syncPitchAngle,
    syncNeckDepth,
    loadTransitionPreset,
    summary,
    fullExportPayload,
    transitionPresets: Object.keys(TRANSITION_PRESETS),
  }
})
