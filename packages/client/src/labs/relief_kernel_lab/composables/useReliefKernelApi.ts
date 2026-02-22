/**
 * ReliefKernelLab API operations composable.
 */
import type { Ref } from 'vue'
import { api } from '@/services/apiBase'
import type {
  HeightmapData,
  FinishingResult,
  SimBridgeOutput,
  ComparisonRow
} from './reliefKernelTypes'
import { PRESETS } from './reliefKernelTypes'

export interface ReliefKernelApiReturn {
  onFileChange: (event: Event) => Promise<void>
  loadHeightmap: () => Promise<void>
  runFinish: () => Promise<void>
  runSimBridge: () => Promise<void>
  runPresetComparison: () => Promise<void>
  pushSnapshot: () => Promise<void>
}

export function useReliefKernelApi(
  file: Ref<File | null>,
  map: Ref<HeightmapData | null>,
  result: Ref<FinishingResult | null>,
  reliefSimBridgeOut: Ref<SimBridgeOutput | null>,
  toolD: Ref<number>,
  stepdown: Ref<number>,
  scallop: Ref<number>,
  stockThickness: Ref<number>,
  units: Ref<'mm' | 'inch'>,
  useDynamicScallop: Ref<boolean>,
  comparisons: Ref<ComparisonRow[]>,
  isComparing: Ref<boolean>,
  drawCanvas: () => void
): ReliefKernelApiReturn {
  async function onFileChange(event: Event): Promise<void> {
    const target = event.target as HTMLInputElement
    if (!target.files?.length) return
    file.value = target.files[0]
    await loadHeightmap()
  }

  async function loadHeightmap(): Promise<void> {
    if (!file.value) return
    const formData = new FormData()
    formData.append('file', file.value)

    try {
      const uploadRes = await api('/api/upload/heightmap', {
        method: 'POST',
        body: formData
      })
      const { path } = await uploadRes.json()

      const res = await api('/api/cam/relief/map_from_heightfield', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          heightmap_path: path,
          units: units.value,
          z_min: 0.0,
          z_max: -3.0,
          sample_pitch_xy: 0.3,
          smooth_sigma: 0.4
        })
      })
      map.value = await res.json()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('Failed to load heightmap:', err)
      alert(`Failed to load heightmap: ${msg}`)
    }
  }

  async function runFinish(): Promise<void> {
    if (!map.value) return
    const payload = {
      z_grid: map.value.z_grid,
      origin_x: map.value.origin_x,
      origin_y: map.value.origin_y,
      cell_size_xy: map.value.cell_size_xy,
      units: map.value.units,
      tool_d: toolD.value,
      stepdown: stepdown.value,
      scallop_height: scallop.value,
      safe_z: 4.0,
      feed_xy: 600.0,
      feed_z: 250.0,
      pattern: 'RasterX',
      use_dynamic_scallop: useDynamicScallop.value,
      slope_low_deg: 10.0,
      slope_high_deg: 50.0,
      scallop_min: 0.03,
      scallop_max: 0.08
    }

    try {
      const res = await api('/api/cam/relief/finishing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      result.value = await res.json()
      await runSimBridge()
      drawCanvas()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('Failed to generate finishing:', err)
      alert(`Failed: ${msg}`)
    }
  }

  async function runSimBridge(): Promise<void> {
    if (!result.value || !map.value) return

    const simPayload = {
      z_grid_original: map.value.z_grid,
      origin_x: map.value.origin_x,
      origin_y: map.value.origin_y,
      cell_size_xy: map.value.cell_size_xy,
      units: map.value.units,
      moves: result.value.moves,
      tool_d: toolD.value,
      stock_thickness: stockThickness.value,
      min_floor_thickness: 0.5,
      high_load_index: 2.0,
      med_load_index: 1.5
    }

    try {
      const res = await api('/api/cam/relief/sim_bridge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(simPayload)
      })
      reliefSimBridgeOut.value = await res.json()
      drawCanvas()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('Failed sim bridge:', err)
      alert(`Sim bridge failed: ${msg}`)
    }
  }

  async function runPresetComparison(): Promise<void> {
    if (!map.value) {
      alert('Load a heightmap first')
      return
    }

    isComparing.value = true
    comparisons.value = []

    for (const [name, preset] of Object.entries(PRESETS)) {
      try {
        const finishPayload = {
          z_grid: map.value.z_grid,
          origin_x: map.value.origin_x,
          origin_y: map.value.origin_y,
          cell_size_xy: map.value.cell_size_xy,
          units: map.value.units,
          tool_d: toolD.value,
          stepdown: preset.stepdown,
          scallop_height: preset.scallop_height,
          safe_z: 4.0,
          feed_xy: 600.0,
          feed_z: 250.0,
          pattern: 'RasterX',
          use_dynamic_scallop: preset.use_dynamic_scallop,
          slope_low_deg: 10.0,
          slope_high_deg: 50.0,
          scallop_min: 0.03,
          scallop_max: 0.08
        }

        const finishRes = await api('/api/cam/relief/finishing', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(finishPayload)
        })
        const finishOut = await finishRes.json()

        const simPayload = {
          z_grid_original: map.value.z_grid,
          origin_x: map.value.origin_x,
          origin_y: map.value.origin_y,
          cell_size_xy: map.value.cell_size_xy,
          units: map.value.units,
          moves: finishOut.moves,
          tool_d: toolD.value,
          stock_thickness: stockThickness.value,
          min_floor_thickness: preset.min_floor_thickness,
          high_load_index: preset.high_load_index,
          med_load_index: preset.med_load_index
        }

        const simRes = await api('/api/cam/relief/sim_bridge', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(simPayload)
        })
        const simOut = await simRes.json()

        const thin_floor_count = simOut.issues.filter(
          (i: SimBridgeOutput['issues'][0]) => i.type === 'thin_floor'
        ).length
        const high_load_count = simOut.issues.filter(
          (i: SimBridgeOutput['issues'][0]) => i.type === 'high_load'
        ).length

        comparisons.value.push({
          name,
          est_time_s: finishOut.stats.est_time_s,
          risk_score: simOut.risk_score,
          thin_floor_count,
          high_load_count,
          avg_floor_thickness: simOut.stats.avg_floor_thickness,
          min_floor_thickness: simOut.stats.min_floor_thickness,
          max_load_index: simOut.stats.max_load_index
        })
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err)
        console.error(`Failed preset ${name}:`, err)
        alert(`Failed preset ${name}: ${msg}`)
      }
    }

    isComparing.value = false
  }

  async function pushSnapshot(): Promise<void> {
    if (!reliefSimBridgeOut.value || !result.value || !map.value) {
      alert('Run finishing + sim bridge first')
      return
    }

    const snapshot = {
      pipeline_id: 'ReliefKernelLab',
      op_id: 'relief_finish_proto',
      risk_score: reliefSimBridgeOut.value.risk_score,
      total_issues: reliefSimBridgeOut.value.issues.length,
      critical_count: reliefSimBridgeOut.value.issues.filter(
        (i) => i.severity === 'critical'
      ).length,
      avg_floor_thickness: reliefSimBridgeOut.value.stats.avg_floor_thickness,
      min_floor_thickness: reliefSimBridgeOut.value.stats.min_floor_thickness,
      max_load_index: reliefSimBridgeOut.value.stats.max_load_index,
      avg_load_index: reliefSimBridgeOut.value.stats.avg_load_index,
      total_removed_volume: reliefSimBridgeOut.value.stats.total_removed_volume,
      stock_thickness: stockThickness.value,
      meta: {
        tool_d: toolD.value,
        stepdown: stepdown.value,
        scallop: scallop.value,
        use_dynamic_scallop: useDynamicScallop.value
      }
    }

    try {
      await api('/api/cam/jobs/risk_report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(snapshot)
      })
      alert('Snapshot pushed to Risk Timeline')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('Failed to push snapshot:', err)
      alert(`Failed to push: ${msg}`)
    }
  }

  return {
    onFileChange,
    loadHeightmap,
    runFinish,
    runSimBridge,
    runPresetComparison,
    pushSnapshot
  }
}
