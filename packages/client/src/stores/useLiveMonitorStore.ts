/**
 * RMOS N10.1: LiveMonitor Store with Drill-Down Support
 * 
 * Manages WebSocket events and drill-down data for LiveMonitor.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LiveMonitorEvent } from '@/models/live_monitor'
import type { DrilldownResponse } from '@/models/live_monitor_drilldown'
import { api } from '@/services/apiBase';
import { useAsyncAction } from '@/composables/useAsyncAction'

export const useLiveMonitorStore = defineStore('liveMonitor', () => {
  // Event stream state
  const events = ref<LiveMonitorEvent[]>([])
  const eventCounts = ref({
    job: 0,
    pattern: 0,
    material: 0,
    metrics: 0
  })

  // Drill-down state
  const activeDrilldown = ref<DrilldownResponse | null>(null)

  const {
    loading: drilldownLoading,
    error: drilldownError,
    execute: loadDrilldown,
  } = useAsyncAction(
    async (jobId: string) => {
      const res = await api(`/api/rmos/live-monitor/${jobId}/drilldown`)
      if (!res.ok) throw new Error(`Drilldown failed: ${res.status}`)
      const data = (await res.json()) as DrilldownResponse
      activeDrilldown.value = data
      return data
    },
  )

  // Actions
  function addEvent(event: LiveMonitorEvent) {
    events.value.push(event)

    // Update counts
    const [category] = event.type.split(':')
    if (category in eventCounts.value) {
      eventCounts.value[category as keyof typeof eventCounts.value]++
    }
  }

  function clearEvents() {
    events.value = []
    eventCounts.value = {
      job: 0,
      pattern: 0,
      material: 0,
      metrics: 0
    }
  }

  function closeDrilldown() {
    activeDrilldown.value = null
    drilldownError.value = null
  }

  return {
    // State
    events,
    eventCounts,
    activeDrilldown,
    drilldownLoading,
    drilldownError,

    // Actions
    addEvent,
    clearEvents,
    loadDrilldown,
    closeDrilldown
  }
})
