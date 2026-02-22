/**
 * SpectrumChartRenderer chart rendering composable.
 */
import { type Ref, type ComputedRef } from 'vue'
import { Chart } from 'chart.js'
import type { SpectrumRow, PeakData, PeakSelectedPayload } from './spectrumChartTypes'

// ============================================================================
// Types
// ============================================================================

export interface SpectrumChartRenderReturn {
  createChart: () => void
  downloadChart: () => void
  destroyChart: () => void
}

export interface SpectrumChartRenderOptions {
  chartCanvas: Ref<HTMLCanvasElement | null>
  chartInstance: Ref<Chart | null>
  parsedData: ComputedRef<SpectrumRow[]>
  parsedPeaks: ComputedRef<PeakData[]>
  showCoherence: Ref<boolean>
  showPeaks: Ref<boolean>
  logScale: Ref<boolean>
  selectedFreqHz: () => number | null | undefined
  entryRelpath: () => string
  nearestMagAtFreq: (freqHz: number) => number
  emitPeakSelected: (payload: PeakSelectedPayload) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useSpectrumChartRender(
  options: SpectrumChartRenderOptions
): SpectrumChartRenderReturn {
  const {
    chartCanvas,
    chartInstance,
    parsedData,
    parsedPeaks,
    showCoherence,
    showPeaks,
    logScale,
    selectedFreqHz,
    entryRelpath,
    nearestMagAtFreq,
    emitPeakSelected
  } = options

  /**
   * Create or recreate the Chart.js chart.
   */
  function createChart(): void {
    if (!chartCanvas.value || parsedData.value.length === 0) return

    // Destroy existing chart
    if (chartInstance.value) {
      chartInstance.value.destroy()
      chartInstance.value = null
    }

    const data = parsedData.value
    const labels = data.map((r) => r.freq_hz)
    const magData = data.map((r) => r.H_mag)
    const cohData = data.map((r) => r.coherence)

    const datasets: any[] = [
      {
        label: 'Magnitude',
        data: magData,
        borderColor: '#42b883',
        backgroundColor: 'rgba(66, 184, 131, 0.1)',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: true,
        tension: 0.1,
        yAxisID: 'y'
      }
    ]

    if (showCoherence.value && cohData.some((c) => c > 0)) {
      datasets.push({
        label: 'Coherence (γ²)',
        data: cohData,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.05)',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0.1,
        yAxisID: 'y1'
      })
    }

    // Invisible-ish peaks dataset for robust hit-testing.
    let peaksDatasetIndex = -1
    if (showPeaks.value && parsedPeaks.value.length > 0) {
      const peakPts = parsedPeaks.value.map((p) => ({
        x: p.freq_hz,
        y: nearestMagAtFreq(p.freq_hz)
      }))
      peaksDatasetIndex = datasets.length
      datasets.push({
        label: '__peaks_hit__',
        data: peakPts,
        parsing: false,
        showLine: false,
        pointRadius: 6,
        pointHitRadius: 12,
        pointHoverRadius: 6,
        borderWidth: 0,
        pointBackgroundColor: 'rgba(0,0,0,0)',
        pointBorderColor: 'rgba(0,0,0,0)',
        yAxisID: 'y'
      })
    }

    // Custom plugin to draw vertical lines at peak frequencies
    const peaksOverlayPlugin = {
      id: 'peaksOverlay',
      afterDraw(chart: Chart) {
        if (!showPeaks.value || parsedPeaks.value.length === 0) return
        const { ctx, chartArea, scales } = chart
        const xScale = scales.x
        if (!xScale || !chartArea) return

        ctx.save()
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.7)' // red-500
        ctx.lineWidth = 1
        ctx.setLineDash([4, 4])

        for (const peak of parsedPeaks.value) {
          const x = xScale.getPixelForValue(peak.freq_hz)
          if (x >= chartArea.left && x <= chartArea.right) {
            ctx.beginPath()
            ctx.moveTo(x, chartArea.top)
            ctx.lineTo(x, chartArea.bottom)
            ctx.stroke()

            // Draw label at top
            ctx.fillStyle = 'rgba(239, 68, 68, 0.9)'
            ctx.font = '10px sans-serif'
            ctx.textAlign = 'center'
            ctx.fillText(`${peak.freq_hz.toFixed(0)}`, x, chartArea.top - 4)
          }
        }

        ctx.restore()
      }
    }

    // Cursor plugin: draws selected frequency cursor
    const selectionCursorPlugin = {
      id: 'selectionCursor',
      afterDraw(chart: Chart) {
        const freqHz = selectedFreqHz()
        if (!freqHz || !Number.isFinite(freqHz)) return
        const { ctx, chartArea, scales } = chart
        const xScale = scales.x
        if (!xScale || !chartArea) return
        const x = xScale.getPixelForValue(freqHz)
        if (x < chartArea.left || x > chartArea.right) return
        ctx.save()
        ctx.strokeStyle = 'rgba(147, 197, 253, 0.85)' // blue-ish cursor
        ctx.lineWidth = 1.5
        ctx.setLineDash([])
        ctx.beginPath()
        ctx.moveTo(x, chartArea.top)
        ctx.lineTo(x, chartArea.bottom)
        ctx.stroke()
        ctx.restore()
      }
    }

    chartInstance.value = new Chart(chartCanvas.value, {
      type: 'line',
      data: {
        labels,
        datasets
      },
      plugins: [peaksOverlayPlugin, selectionCursorPlugin],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        onClick: (event: any) => {
          if (!chartInstance.value) return
          if (!showPeaks.value || parsedPeaks.value.length === 0) return
          const els = chartInstance.value.getElementsAtEventForMode(
            event as any,
            'nearest',
            { intersect: true },
            true
          )
          // Prefer the hit-test dataset when present
          const hit = els.find((e: any) => e.datasetIndex === peaksDatasetIndex)
          if (hit) {
            const idx = hit.index
            const peak = parsedPeaks.value[idx]
            if (peak) {
              emitPeakSelected({
                spectrumRelpath: entryRelpath(),
                peakIndex: peak.peakIndex,
                freq_hz: peak.freq_hz,
                label: peak.label,
                raw: peak.raw
              })
            }
            return
          }
          // Fallback: click near a vertical line (within a small pixel threshold)
          const { chartArea, scales } = chartInstance.value as any
          const xScale = scales?.x
          if (!chartArea || !xScale) return
          const xPx = event?.x ?? 0
          let bestPeak: PeakData | null = null
          let bestDx = Infinity
          for (const p of parsedPeaks.value) {
            const px = xScale.getPixelForValue(p.freq_hz)
            const dx = Math.abs(px - xPx)
            if (dx < bestDx) {
              bestDx = dx
              bestPeak = p
            }
          }
          if (bestPeak && bestDx <= 10) {
            emitPeakSelected({
              spectrumRelpath: entryRelpath(),
              peakIndex: bestPeak.peakIndex,
              freq_hz: bestPeak.freq_hz,
              label: bestPeak.label,
              raw: bestPeak.raw
            })
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#ccc',
              usePointStyle: true,
              padding: 16,
              filter: (item: any) => item.text !== '__peaks_hit__'
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
                if (items.length > 0) {
                  return `${Number(items[0].label).toFixed(1)} Hz`
                }
                return ''
              },
              label: (item) => {
                const val = Number(item.raw)
                if (item.dataset.label?.includes('Coherence')) {
                  return `Coherence: ${val.toFixed(3)}`
                }
                if (item.dataset.label === '__peaks_hit__') {
                  return ''
                }
                return `Magnitude: ${val.toFixed(6)}`
              }
            }
          }
        },
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: 'Frequency (Hz)',
              color: '#aaa'
            },
            ticks: { color: '#888' },
            grid: { color: 'rgba(255,255,255,0.06)' }
          },
          y: {
            type: logScale.value ? 'logarithmic' : 'linear',
            position: 'left',
            title: {
              display: true,
              text: 'Magnitude',
              color: '#42b883'
            },
            ticks: { color: '#42b883' },
            grid: { color: 'rgba(255,255,255,0.06)' }
          },
          y1: {
            type: 'linear',
            position: 'right',
            min: 0,
            max: 1,
            title: {
              display: true,
              text: 'Coherence (γ²)',
              color: '#f59e0b'
            },
            ticks: { color: '#f59e0b' },
            grid: { drawOnChartArea: false }
          }
        }
      }
    })
  }

  /**
   * Download chart as PNG.
   */
  function downloadChart(): void {
    if (!chartCanvas.value) return
    const link = document.createElement('a')
    link.download = `spectrum_${Date.now()}.png`
    link.href = chartCanvas.value.toDataURL('image/png')
    link.click()
  }

  /**
   * Destroy chart instance.
   */
  function destroyChart(): void {
    if (chartInstance.value) {
      chartInstance.value.destroy()
      chartInstance.value = null
    }
  }

  return {
    createChart,
    downloadChart,
    destroyChart
  }
}
