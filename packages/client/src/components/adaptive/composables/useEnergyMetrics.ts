/**
 * Composable for energy and heat metrics calculations.
 * Handles energy analysis, heat timeseries, thermal reports, and bottleneck exports.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
import type { Move } from './useToolpathRenderer'

export interface EnergyOutput {
  totals: {
    volume_mm3: number
    energy_j: number
    heat: {
      chip_j: number
      tool_j: number
      work_j: number
    }
  }
  segments: Array<{ energy_j: number }>
}

export interface HeatTimeSeriesOutput {
  total_s?: number
  p_chip?: number[]
  p_tool?: number[]
  p_work?: number[]
  t?: number[]
  bins?: Array<{ t: number; power_w: number }>
}

export interface EnergyMetricsState {
  materialId: Ref<string>
  energyOut: Ref<EnergyOutput | null>
  heatTS: Ref<HeatTimeSeriesOutput | null>
  includeCsvLinks: Ref<boolean>
  chipPct: ComputedRef<number>
  toolPct: ComputedRef<number>
  workPct: ComputedRef<number>
  energyPolyline: ComputedRef<string>
  runEnergy: (moves: Move[], toolD: number, stepoverPct: number, stepdown: number, jobName?: string) => Promise<void>
  exportEnergyCsv: (moves: Move[], toolD: number, stepoverPct: number, stepdown: number, jobName?: string) => Promise<void>
  runHeatTS: (moves: Move[], profileId: string, toolD: number, stepoverPct: number, stepdown: number) => Promise<void>
  exportBottleneckCsv: (moves: Move[], profileId: string, jobName?: string) => Promise<void>
  exportThermalReport: (moves: Move[], profileId: string, toolD: number, stepoverPct: number, stepdown: number) => Promise<void>
  exportThermalBundle: (moves: Move[], profileId: string, toolD: number, stepoverPct: number, stepdown: number) => Promise<void>
}

export function useEnergyMetrics(): EnergyMetricsState {
  const materialId = ref('maple_hard')
  const energyOut = ref<EnergyOutput | null>(null)
  const heatTS = ref<HeatTimeSeriesOutput | null>(null)
  const includeCsvLinks = ref(true)

  const chipPct = computed(() =>
    !energyOut.value ? 0 : (100 * energyOut.value.totals.heat.chip_j) / energyOut.value.totals.energy_j
  )

  const toolPct = computed(() =>
    !energyOut.value ? 0 : (100 * energyOut.value.totals.heat.tool_j) / energyOut.value.totals.energy_j
  )

  const workPct = computed(() =>
    !energyOut.value ? 0 : (100 * energyOut.value.totals.heat.work_j) / energyOut.value.totals.energy_j
  )

  const energyPolyline = computed(() => {
    if (!energyOut.value) return ''
    const seg = energyOut.value.segments
    const cum: number[] = []
    let s = 0
    for (const k of seg) {
      s += k.energy_j
      cum.push(s)
    }
    if (!cum.length) return ''
    const maxY = cum[cum.length - 1]
    const W = 300
    const H = 120
    return cum
      .map((v, i) => {
        const x = (i / (cum.length - 1)) * W
        const y = H - (v / maxY) * H
        return `${x},${y}`
      })
      .join(' ')
  })

  async function runEnergy(
    moves: Move[],
    toolD: number,
    stepoverPct: number,
    stepdown: number,
    jobName?: string
  ) {
    if (!moves.length) {
      alert('No moves available for energy calculation')
      return
    }

    try {
      const body = {
        moves,
        material_id: materialId.value,
        tool_d: toolD,
        stepover: stepoverPct / 100,
        stepdown,
        job_name: jobName || undefined,
      }

      const r = await api('/api/cam/metrics/energy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      energyOut.value = await r.json()
    } catch (e: unknown) {
      alert('Energy calculation failed: ' + e)
    }
  }

  async function exportEnergyCsv(
    moves: Move[],
    toolD: number,
    stepoverPct: number,
    stepdown: number,
    jobName?: string
  ) {
    if (!energyOut.value) {
      alert('Run energy calculation first')
      return
    }

    if (!moves.length) {
      alert('No moves available for CSV export')
      return
    }

    try {
      const body = {
        moves,
        material_id: materialId.value,
        tool_d: toolD,
        stepover: stepoverPct / 100,
        stepdown,
        job_name: jobName || undefined,
      }

      const r = await api('/api/cam/metrics/energy_csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = ''
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (e: unknown) {
      alert('CSV export failed: ' + e)
    }
  }

  async function runHeatTS(
    moves: Move[],
    profileId: string,
    toolD: number,
    stepoverPct: number,
    stepdown: number
  ) {
    if (!moves.length || !materialId.value || !profileId) {
      alert('Run plan first, select material and profile')
      return
    }

    try {
      const body = {
        moves,
        machine_profile_id: profileId,
        material_id: materialId.value,
        tool_d: toolD,
        stepover: stepoverPct / 100,
        stepdown,
        bins: 120,
      }

      const r = await api('/api/cam/metrics/heat_timeseries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      heatTS.value = await r.json()
    } catch (e: unknown) {
      alert('Heat timeseries failed: ' + e)
    }
  }

  async function exportBottleneckCsv(moves: Move[], profileId: string, jobName?: string) {
    if (!moves.length || !profileId) {
      alert('Run plan first and select profile')
      return
    }

    try {
      const body = {
        moves,
        machine_profile_id: profileId,
        job_name: jobName || 'pocket',
      }

      const r = await api('/api/cam/metrics/bottleneck_csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = ''
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (e: unknown) {
      alert('Bottleneck CSV export failed: ' + e)
    }
  }

  async function exportThermalReport(
    moves: Move[],
    profileId: string,
    toolD: number,
    stepoverPct: number,
    stepdown: number
  ) {
    if (!moves.length) {
      alert('Run plan first')
      return
    }

    try {
      const body = {
        moves,
        machine_profile_id: profileId || 'Mach4_Router_4x8',
        material_id: materialId.value || 'maple_hard',
        tool_d: toolD,
        stepover: stepoverPct / 100,
        stepdown,
        bins: 200,
        job_name: 'pocket',
        budgets: {
          chip_j: 500.0,
          tool_j: 150.0,
          work_j: 100.0,
        },
        include_csv_links: includeCsvLinks.value,
      }

      const r = await api('/api/cam/metrics/thermal_report_md', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = ''
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (e: unknown) {
      alert('Thermal report export failed: ' + e)
    }
  }

  async function exportThermalBundle(
    moves: Move[],
    profileId: string,
    toolD: number,
    stepoverPct: number,
    stepdown: number
  ) {
    if (!moves.length) {
      alert('Run plan first')
      return
    }

    try {
      const body = {
        moves,
        machine_profile_id: profileId || 'Mach4_Router_4x8',
        material_id: materialId.value || 'maple_hard',
        tool_d: toolD,
        stepover: stepoverPct / 100,
        stepdown,
        bins: 200,
        job_name: 'pocket',
        budgets: {
          chip_j: 500.0,
          tool_j: 150.0,
          work_j: 100.0,
        },
        include_csv_links: includeCsvLinks.value,
      }

      const r = await api('/api/cam/metrics/thermal_report_bundle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!r.ok) {
        throw new Error(await r.text())
      }

      const blob = await r.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = ''
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (e: unknown) {
      alert('Thermal bundle export failed: ' + e)
    }
  }

  return {
    materialId,
    energyOut,
    heatTS,
    includeCsvLinks,
    chipPct,
    toolPct,
    workPct,
    energyPolyline,
    runEnergy,
    exportEnergyCsv,
    runHeatTS,
    exportBottleneckCsv,
    exportThermalReport,
    exportThermalBundle,
  }
}
