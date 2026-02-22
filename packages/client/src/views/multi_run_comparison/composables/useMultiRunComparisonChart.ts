/**
 * MultiRunComparisonView chart composable.
 */
import { computed, watch, nextTick, type Ref, type ComputedRef } from 'vue'
import { Chart, registerables } from 'chart.js'
import type { ComparisonResult } from './multiRunComparisonTypes'

Chart.register(...registerables)

// ============================================================================
// Types
// ============================================================================

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor: string[]
  borderColor: string[]
  borderWidth: number
}

export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface MultiRunComparisonChartReturn {
  chartData: ComputedRef<ChartData>
  destroyChart: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useMultiRunComparisonChart(
  comparisonResult: Ref<ComparisonResult | null>,
  timeChartCanvas: Ref<HTMLCanvasElement | null>
): MultiRunComparisonChartReturn {
  let timeChart: Chart<'bar', number[], string> | null = null

  /**
   * Computed chart data from comparison result.
   */
  const chartData = computed<ChartData>(() => {
    if (!comparisonResult.value) {
      return { labels: [], datasets: [] }
    }

    const runs = comparisonResult.value.runs.filter(
      (r) => r.sim_time_s !== null && r.sim_time_s !== undefined
    )
    const labels = runs.map((r) => r.preset_name)
    const data = runs.map((r) => r.sim_time_s || 0)

    return {
      labels,
      datasets: [
        {
          label: 'Simulation Time (s)',
          data,
          backgroundColor: runs.map((r) =>
            r.preset_id === comparisonResult.value?.best_run_id
              ? 'rgba(34, 197, 94, 0.6)'
              : r.preset_id === comparisonResult.value?.worst_run_id
                ? 'rgba(239, 68, 68, 0.6)'
                : 'rgba(59, 130, 246, 0.6)'
          ),
          borderColor: runs.map((r) =>
            r.preset_id === comparisonResult.value?.best_run_id
              ? 'rgb(34, 197, 94)'
              : r.preset_id === comparisonResult.value?.worst_run_id
                ? 'rgb(239, 68, 68)'
                : 'rgb(59, 130, 246)'
          ),
          borderWidth: 2
        }
      ]
    }
  })

  /**
   * Destroy existing chart instance.
   */
  function destroyChart(): void {
    if (timeChart) {
      timeChart.destroy()
      timeChart = null
    }
  }

  /**
   * Create or update chart when data changes.
   */
  watch(
    () => comparisonResult.value,
    async (newResult) => {
      if (newResult && chartData.value.labels.length > 0) {
        await nextTick()
        if (timeChartCanvas.value) {
          destroyChart()

          timeChart = new Chart(timeChartCanvas.value, {
            type: 'bar',
            data: chartData.value,
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  display: false
                },
                tooltip: {
                  callbacks: {
                    label: (context) => {
                      return `${(context.parsed.y ?? 0).toFixed(2)}s`
                    }
                  }
                }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: 'Time (seconds)'
                  }
                }
              }
            }
          })
        }
      }
    },
    { immediate: true }
  )

  return {
    chartData,
    destroyChart
  }
}
