/**
 * TransferFunctionRenderer chart composable.
 */
import { nextTick, onMounted, onUnmounted, watch, type Ref, type ComputedRef } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import type { TransferFunctionPoint } from './transferFunctionTypes'

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  Title,
  Tooltip,
  Legend
)

export interface TransferFunctionChartReturn {
  createChart: () => void
  downloadChart: () => void
}

export function useTransferFunctionChart(
  chartCanvas: Ref<HTMLCanvasElement | null>,
  chartData: ComputedRef<TransferFunctionPoint[]>,
  showPhase: Ref<boolean>,
  logFreq: Ref<boolean>,
  dbScale: Ref<boolean>,
  bytes: () => Uint8Array
): TransferFunctionChartReturn {
  let chartInstance: Chart | null = null

  /**
   * Create or recreate the chart.
   */
  function createChart(): void {
    if (!chartCanvas.value || chartData.value.length === 0) return

    // Destroy existing chart
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }

    const data = chartData.value
    const labels = data.map((p) => p.freq)
    const magData = data.map((p) => p.mag)
    const phaseData = data.map((p) => p.phase)

    const datasets: unknown[] = [
      {
        label: dbScale.value ? 'Magnitude (dB)' : 'Magnitude',
        data: magData,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        pointRadius: data.length < 100 ? 3 : 0,
        fill: false,
        tension: 0.1,
        yAxisID: 'y'
      }
    ]

    if (showPhase.value) {
      datasets.push({
        label: 'Phase (°)',
        data: phaseData,
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.05)',
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false,
        tension: 0.1,
        yAxisID: 'y1'
      })
    }

    chartInstance = new Chart(chartCanvas.value, {
      type: 'line',
      data: {
        labels,
        datasets: datasets as Chart['data']['datasets']
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#ccc',
              usePointStyle: true,
              padding: 16
            }
          },
          title: {
            display: true,
            text: 'Transfer Function (Bode Plot)',
            color: '#ddd',
            font: { size: 14, weight: 'normal' },
            padding: { bottom: 16 }
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
                if (item.dataset.label?.includes('Phase')) {
                  return `Phase: ${val.toFixed(1)}°`
                }
                if (dbScale.value) {
                  return `Magnitude: ${val.toFixed(2)} dB`
                }
                return `Magnitude: ${val.toFixed(6)}`
              }
            }
          }
        },
        scales: {
          x: {
            type: logFreq.value ? 'logarithmic' : 'linear',
            title: {
              display: true,
              text: 'Frequency (Hz)',
              color: '#aaa'
            },
            ticks: {
              color: '#888',
              callback: function (value) {
                // Better tick labels for log scale
                if (logFreq.value) {
                  const v = Number(value)
                  if ([10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000].includes(v)) {
                    return v >= 1000 ? `${v / 1000}k` : v
                  }
                  return null
                }
                return value
              }
            },
            grid: { color: 'rgba(255,255,255,0.06)' }
          },
          y: {
            type: 'linear',
            position: 'left',
            title: {
              display: true,
              text: dbScale.value ? 'Magnitude (dB)' : 'Magnitude',
              color: '#3b82f6'
            },
            ticks: { color: '#3b82f6' },
            grid: { color: 'rgba(255,255,255,0.06)' }
          },
          y1: {
            type: 'linear',
            position: 'right',
            min: -180,
            max: 180,
            title: {
              display: showPhase.value,
              text: 'Phase (°)',
              color: '#ef4444'
            },
            ticks: {
              color: '#ef4444',
              callback: (value) => `${value}°`
            },
            grid: { drawOnChartArea: false },
            display: showPhase.value
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
    link.download = `bode_plot_${Date.now()}.png`
    link.href = chartCanvas.value.toDataURL('image/png')
    link.click()
  }

  // Lifecycle
  onMounted(() => {
    nextTick(() => createChart())
  })

  onUnmounted(() => {
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }
  })

  // Watch for changes
  watch([showPhase, logFreq, dbScale, bytes], () => {
    nextTick(() => createChart())
  })

  return {
    createChart,
    downloadChart
  }
}
