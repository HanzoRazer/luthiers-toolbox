/**
 * RMOS N10.1: LiveMonitor Store with Drill-Down Support
 * 
 * Manages WebSocket events and drill-down data for LiveMonitor.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LiveMonitorEvent } from '@/models/live_monitor'
import type { DrilldownResponse } from '@/models/live_monitor_drilldown'

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
  const drilldownLoading = ref(false)
  const drilldownError = ref<string | null>(null)

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

  async function loadDrilldown(jobId: string) {
    drilldownLoading.value = true
    drilldownError.value = null

    try {
      const res = await fetch(`/api/rmos/live-monitor/${jobId}/drilldown`)
      if (!res.ok) throw new Error(`Drilldown failed: ${res.status}`)
      const data = (await res.json()) as DrilldownResponse
      activeDrilldown.value = data
    } catch (e: any) {
      drilldownError.value = String(e.message || e)
    } finally {
      drilldownLoading.value = false
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
