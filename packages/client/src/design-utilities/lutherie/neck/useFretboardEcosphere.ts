/**
 * useFretboardEcosphere
 *
 * Reactive composable for fretboard ecosphere API operations:
 *   - Build ecosphere via /api/v1/fretboard/compute
 *   - Download DXF via /api/v1/fretboard/dxf
 *   - Tier-aware DXF version selection (R12 free, R2000 pro)
 *
 * Uses the auth store for tier detection. Defaults to free tier
 * if auth context is unavailable.
 */

import { ref, computed } from "vue"
import { useAuthStore } from "@/stores/useAuthStore"
import {
  computeEcosphere,
  exportEcosphereDxf,
  type FretboardInput,
  type FretboardEcosphere,
  type DxfVersion,
} from "@/api/fretboardEcosphere"

export type UserTier = "free" | "pro"

export interface PartialFretboardInput {
  scaleLengthMm: number
  fretCount: number
  temperament?: FretboardInput["temperament"]
  stringCount?: number
  slotWidthMm?: number
  nutWidthMm?: number
  scaleType?: FretboardInput["scaleType"]
  bassScaleLengthMm?: number
  perpendicularFret?: number
  heelWidthMm?: number
  edgeOffsetMm?: number
  radius?: FretboardInput["radius"]
  extensionMm?: number
  intonationOffsetsMm?: Record<number, number>
}

export function useFretboardEcosphere() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastEcosphere = ref<FretboardEcosphere | null>(null)

  const authStore = useAuthStore()

  const currentTier = computed<UserTier>(() => (authStore.isPro ? "pro" : "free"))

  const inferredDxfVersion = computed<DxfVersion>(() => (currentTier.value === "pro" ? "R2000" : "R12"))

  function withDefaults(input: PartialFretboardInput): FretboardInput {
    return {
      stringCount: 6,
      slotWidthMm: 0.58,
      nutWidthMm: 42.0,
      temperament: "equal_12",
      ...input,
      scaleLengthMm: input.scaleLengthMm,
      fretCount: input.fretCount,
    }
  }

  async function build(input: PartialFretboardInput): Promise<FretboardEcosphere> {
    loading.value = true
    error.value = null
    try {
      const result = await computeEcosphere(withDefaults(input))
      lastEcosphere.value = result
      return result
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e)
      error.value = message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function downloadDxf(input: PartialFretboardInput, version?: DxfVersion): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const v = version ?? inferredDxfVersion.value
      const blob = await exportEcosphereDxf(withDefaults(input), v)
      const filename = `fretboard_${input.temperament ?? "equal_12"}_${input.fretCount}fret_${v}.dxf`
      triggerDownload(blob, filename)
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : String(e)
      error.value = message
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    lastEcosphere,
    currentTier,
    inferredDxfVersion,
    withDefaults,
    build,
    downloadDxf,
  }
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
