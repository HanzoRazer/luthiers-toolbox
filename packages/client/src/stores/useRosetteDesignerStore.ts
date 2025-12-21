// Patch N11.2 - Rosette Designer store scaffolding

import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface RosetteRing {
  ring_id: number
  radius_mm: number
  width_mm: number
  tile_length_mm: number
  kerf_mm: number
  herringbone_angle_deg: number
  twist_angle_deg: number
}

export interface SegmentationResult {
  segmentation_id: string
  ring_id: number
  tile_count: number
  tile_length_mm: number
  tiles: Array<{
    tile_index: number
    theta_start_deg: number
    theta_end_deg: number
  }>
}

export interface SliceBatch {
  batch_id: string
  ring_id: number
  slices: Array<Record<string, any>>
}

export interface PreviewRingSummary {
  ring_id: number
  radius_mm: number
  width_mm: number
  tile_count: number
  slice_count: number
}

export interface PreviewSnapshotPayload {
  pattern_id: string | null
  rings: PreviewRingSummary[]
}

// N14.1 / N10 - CNC Export interfaces
export interface CNCSegment {
  x_start_mm: number
  y_start_mm: number
  z_start_mm: number
  x_end_mm: number
  y_end_mm: number
  z_end_mm: number
  feed_mm_per_min: number
}

export interface CNCSafety {
  decision: string
  risk_level: string
  requires_override: boolean
  reasons: string[]
}

export interface CNCSimulation {
  passes: number
  estimated_runtime_sec: number
  max_feed_mm_per_min: number
  envelope_ok: boolean
}

export interface CNCExportResult {
  job_id: string
  ring_id: number
  toolpaths: CNCSegment[]
  jig_alignment: {
    origin_x_mm: number
    origin_y_mm: number
    rotation_deg: number
  }
  safety: CNCSafety
  simulation: CNCSimulation
  metadata: Record<string, any>
  operator_report_md?: string | null
}

export const useRosetteDesignerStore = defineStore('rosetteDesigner', () => {
  const rings = ref<RosetteRing[]>([])
  const selectedRingId = ref<number | null>(null)
  const segmentation = ref<SegmentationResult | null>(null)
  const sliceBatch = ref<SliceBatch | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // NEW: preview snapshot state (multi-ring summary)
  const preview = ref<PreviewSnapshotPayload | null>(null)

  // NEW: CNC export configuration + result
  const cncMaterial = ref<'hardwood' | 'softwood' | 'composite'>('hardwood')
  const cncJigOriginX = ref(0)
  const cncJigOriginY = ref(0)
  const cncJigRotationDeg = ref(0)
  const cncExport = ref<CNCExportResult | null>(null)

  function addDefaultRing() {
    const newId = rings.value.length
    const ring: RosetteRing = {
      ring_id: newId,
      radius_mm: 45,
      width_mm: 3,
      tile_length_mm: 5,
      kerf_mm: 0.3,
      herringbone_angle_deg: 0,
      twist_angle_deg: 0,
    }
    rings.value.push(ring)
    selectedRingId.value = newId
  }

  async function segmentSelectedRing() {
    if (selectedRingId.value === null) return
    const ring = rings.value.find(r => r.ring_id === selectedRingId.value)
    if (!ring) return

    loading.value = true
    error.value = null

    try {
      const resp = await fetch('/api/rmos/rosette/segment-ring', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ring }),
      })
      if (!resp.ok) {
        throw new Error(`segment-ring failed with ${resp.status}`)
      }
      segmentation.value = await resp.json()
      sliceBatch.value = null
    } catch (e: any) {
      error.value = e?.message ?? String(e)
    } finally {
      loading.value = false
    }
  }

  async function generateSlicesForSelectedRing() {
    if (!segmentation.value) return
    const ring = rings.value.find(r => r.ring_id === segmentation.value!.ring_id)
    if (!ring) return

    loading.value = true
    error.value = null

    try {
      const payload = {
        ring_id: ring.ring_id,
        segmentation: segmentation.value,
        kerf_mm: ring.kerf_mm,
        herringbone_angle_deg: ring.herringbone_angle_deg,
      }
      const resp = await fetch('/api/rmos/rosette/generate-slices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!resp.ok) {
        throw new Error(`generate-slices failed with ${resp.status}`)
      }
      sliceBatch.value = await resp.json()
    } catch (e: any) {
      error.value = e?.message ?? String(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchPreview(patternId?: string | null) {
    loading.value = true
    error.value = null

    try {
      const body = {
        pattern_id: patternId ?? null,
        rings: rings.value,
      }

      const resp = await fetch('/api/rmos/rosette/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!resp.ok) {
        throw new Error(`preview failed with ${resp.status}`)
      }

      const data = await resp.json()
      preview.value = data as PreviewSnapshotPayload
    } catch (e: any) {
      error.value = e?.message ?? String(e)
    } finally {
      loading.value = false
    }
  }

  async function exportCncForSelectedRing() {
    if (!sliceBatch.value) {
      error.value = 'No slice batch available. Generate slices first.'
      return
    }

    // Determine which ring to export
    let ring = null as RosetteRing | null

    if (selectedRingId.value !== null) {
      ring = rings.value.find(r => r.ring_id === selectedRingId.value) || null
    }

    if (!ring && sliceBatch.value) {
      ring = rings.value.find(r => r.ring_id === sliceBatch.value!.ring_id) || null
    }

    if (!ring) {
      error.value = 'No matching ring found for CNC export.'
      return
    }

    loading.value = true
    error.value = null

    try {
      const payload = {
        ring: {
          ring_id: ring.ring_id,
          radius_mm: ring.radius_mm,
          width_mm: ring.width_mm,
          tile_length_mm: ring.tile_length_mm,
          kerf_mm: ring.kerf_mm,
          herringbone_angle_deg: ring.herringbone_angle_deg,
          twist_angle_deg: ring.twist_angle_deg,
        },
        slice_batch: sliceBatch.value,
        material: cncMaterial.value,
        jig_alignment: {
          origin_x_mm: cncJigOriginX.value,
          origin_y_mm: cncJigOriginY.value,
          rotation_deg: cncJigRotationDeg.value,
        },
        envelope: null, // use server defaults for now
      }

      const resp = await fetch('/api/rmos/rosette/export-cnc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!resp.ok) {
        throw new Error(`export-cnc failed with ${resp.status}`)
      }

      const data = await resp.json()
      cncExport.value = data as CNCExportResult
    } catch (e: any) {
      error.value = e?.message ?? String(e)
    } finally {
      loading.value = false
    }
  }

  return {
    rings,
    selectedRingId,
    segmentation,
    sliceBatch,
    loading,
    error,
    preview,
    cncMaterial,
    cncJigOriginX,
    cncJigOriginY,
    cncJigRotationDeg,
    cncExport,
    addDefaultRing,
    segmentSelectedRing,
    generateSlicesForSelectedRing,
    fetchPreview,
    exportCncForSelectedRing,
  }
})
