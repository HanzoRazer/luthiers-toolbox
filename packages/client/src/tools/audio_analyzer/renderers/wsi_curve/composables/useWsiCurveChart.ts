/**
 * WsiCurveRenderer chart composable.
 */
import { type Ref, type ComputedRef } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import type { WsiRow, PeakSelectedPayload } from './wsiCurveTypes'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

export interface WsiCurveChartReturn {
  createChart: () => void
  destroyChart: () => void
  downloadChart: () => void
}

export function useWsiCurveChart(
  chartCanvas: Ref<HTMLCanvasElement | null>,
  rows: ComputedRef<WsiRow[]>,
  showCohMean: Ref<boolean>,
  showPhaseDisorder: Ref<boolean>,
  shadeAdmissible: Ref<boolean>,
  emphasizeSelectionPoint: Ref<boolean>,
  selectedNearest: ComputedRef<WsiRow | null>,
  selectedFreqHz: () => number | null | undefined,
  nearestRowByFreq: (freqHz: number) => WsiRow | null,
  nearestRowByLabel: (label: any) => WsiRow | null,
  boolText: (v: boolean) => string,
  entryRelpath: () => string,
  emit: (e: 'peak-selected', payload: PeakSelectedPayload) => void
): WsiCurveChartReturn {
  let chartInstance: Chart | null = null

  /**
   * Create admissible shading plugin.
   */
  function createAdmissibleShadePlugin() {
    return {
      id: 'admissibleShade',
      beforeDatasetsDraw(chart: Chart) {
        if (!shadeAdmissible.value) return
        const { ctx, chartArea, scales } = chart
        const xScale = scales.x as any
        if (!chartArea || !xScale) return

        ctx.save()
        ctx.fillStyle = 'rgba(34, 197, 94, 0.06)'

        let runStartIdx: number | null = null
        const r = rows.value
        for (let i = 0; i < r.length; i++) {
          const ok = !!r[i].admissible
          if (ok && runStartIdx === null) runStartIdx = i
          if ((!ok || i === r.length - 1) && runStartIdx !== null) {
            const runEndIdx = ok && i === r.length - 1 ? i : i - 1
            const x1 = xScale.getPixelForValue(r[runStartIdx].freq_hz)
            const x2 = xScale.getPixelForValue(r[runEndIdx].freq_hz)
            const left = Math.min(x1, x2)
            const right = Math.max(x1, x2)
            if (right >= chartArea.left && left <= chartArea.right) {
              ctx.fillRect(
                Math.max(left, chartArea.left),
                chartArea.top,
                Math.min(right, chartArea.right) - Math.max(left, chartArea.left),
                chartArea.bottom - chartArea.top
              )
            }
            runStartIdx = null
          }
        }
        ctx.restore()
      }
    }
  }

  /**
   * Create selection cursor plugin.
   */
  function createSelectionCursorPlugin() {
    return {
      id: 'selectionCursor',
      afterDraw(chart: Chart) {
        const freqHz = selectedFreqHz() ?? null
        if (!freqHz || !Number.isFinite(freqHz)) return
        const { ctx, chartArea, scales } = chart
        const xScale = scales.x as any
        if (!chartArea || !xScale) return
        const x = xScale.getPixelForValue(freqHz)
        if (x < chartArea.left || x > chartArea.right) return
        ctx.save()
        ctx.strokeStyle = 'rgba(147, 197, 253, 0.85)'
        ctx.lineWidth = 1.5
        ctx.setLineDash([])
        ctx.beginPath()
        ctx.moveTo(x, chartArea.top)
        ctx.lineTo(x, chartArea.bottom)
        ctx.stroke()
        ctx.restore()
      }
    }
  }

  /**
   * Create the Chart.js instance.
   */
  function createChart(): void {
    if (!chartCanvas.value) return
    if (rows.value.length === 0) return

    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }

    const xs = rows.value.map((r) => r.freq_hz)
    const wsiData = rows.value.map((r) => r.wsi)
    const cohData = rows.value.map((r) => r.coh_mean)
    const phaseData = rows.value.map((r) => r.phase_disorder)

    const datasets: any[] = [
      {
        label: 'WSI',
        data: wsiData,
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.10)',
        borderWidth: 1.8,
        pointRadius: 0,
        fill: true,
        tension: 0.1,
        yAxisID: 'y'
      }
    ]

    if (showCohMean.value && cohData.some((v) => v > 0)) {
      datasets.push({
        label: 'coh_mean',
        data: cohData,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.06)',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0.1,
        yAxisID: 'y'
      })
    }

    if (showPhaseDisorder.value && phaseData.some((v) => v > 0)) {
      datasets.push({
        label: 'phase_disorder',
        data: phaseData,
        borderColor: '#60a5fa',
        backgroundColor: 'rgba(96, 165, 250, 0.06)',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0.1,
        yAxisID: 'y'
      })
    }

    const sel = selectedNearest.value
    if (emphasizeSelectionPoint.value && sel) {
      datasets.push({
        label: '__selection_point__',
        data: [{ x: sel.freq_hz, y: sel.wsi }],
        parsing: false,
        showLine: false,
        pointRadius: 5,
        pointHoverRadius: 6,
        pointHitRadius: 10,
        borderWidth: 0,
        pointBackgroundColor: 'rgba(147, 197, 253, 0.95)',
        pointBorderColor: 'rgba(147, 197, 253, 0.95)',
        yAxisID: 'y'
      })
    }

    chartInstance = new Chart(chartCanvas.value, {
      type: 'line',
      data: {
        labels: xs,
        datasets
      },
      plugins: [createAdmissibleShadePlugin(), createSelectionCursorPlugin()],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        onClick: (event: any) => {
          if (!chartInstance) return
          const xScale = (chartInstance as any).scales?.x
          const chartArea = (chartInstance as any).chartArea
          if (!xScale || !chartArea) return
          const xPx = event?.x ?? 0
          if (xPx < chartArea.left || xPx > chartArea.right) return
          const freqGuess = xScale.getValueForPixel(xPx)
          if (!Number.isFinite(freqGuess)) return
          const nearest = nearestRowByFreq(Number(freqGuess))
          if (!nearest) return

          emit('peak-selected', {
            spectrumRelpath: entryRelpath(),
            peakIndex: -1,
            freq_hz: nearest.freq_hz,
            label: undefined,
            raw: nearest
          })
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#ccc',
              usePointStyle: true,
              padding: 16,
              filter: (item: any) => item.text !== '__selection_point__'
            }
          },
          tooltip: {
            backgroundColor: 'rgba(30, 30, 30, 0.95)',
            titleColor: '#fff',
            bodyColor: '#ccc',
            borderColor: '#444',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              title: (items) => {
                if (items.length > 0) return `${Number(items[0].label).toFixed(2)} Hz`
                return ''
              },
              label: (item) => {
                if (item.dataset?.label === '__selection_point__') return ''
                const row = nearestRowByLabel(item.label)
                if (!row) return ''
                return `wsi ${row.wsi.toFixed(3)} | coh_mean ${row.coh_mean.toFixed(3)} | phase_disorder ${row.phase_disorder.toFixed(3)} | admissible ${boolText(row.admissible)}`
              }
            }
          }
        },
        scales: {
          x: {
            type: 'linear',
            title: { display: true, text: 'Frequency (Hz)', color: '#aaa' },
            ticks: { color: '#888' },
            grid: { color: 'rgba(255,255,255,0.06)' }
          },
          y: {
            type: 'linear',
            min: 0,
            max: 1,
            title: { display: true, text: 'WSI / Metrics', color: '#22c55e' },
            ticks: { color: '#9bd5b0' },
            grid: { color: 'rgba(255,255,255,0.06)' }
          }
        }
      }
    })
  }

  /**
   * Destroy the chart instance.
   */
  function destroyChart(): void {
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }
  }

  /**
   * Download chart as PNG.
   */
  function downloadChart(): void {
    if (!chartCanvas.value) return
    const link = document.createElement('a')
    link.download = `wsi_${Date.now()}.png`
    link.href = chartCanvas.value.toDataURL('image/png')
    link.click()
  }

  return {
    createChart,
    destroyChart,
    downloadChart
  }
}
