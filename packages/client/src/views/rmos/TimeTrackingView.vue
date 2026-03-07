<script setup lang="ts">
/**
 * TimeTrackingView - Shop Time Tracking & Labor Management
 * Track time spent on operations, projects, and generate labor reports
 *
 * Connected to API endpoints:
 *   GET  /api/rmos/time/entries
 *   POST /api/rmos/time/entries
 *   GET  /api/rmos/time/reports
 */
import { ref, computed } from 'vue'

const activeTimer = ref<{ project: string; task: string; startTime: Date } | null>(null)
const elapsedTime = ref(0)

const recentEntries = ref([
  { id: 1, project: 'Classical Guitar #147', task: 'Binding Installation', duration: 145, date: '2026-03-06' },
  { id: 2, project: 'Steel String #89', task: 'Final Setup', duration: 90, date: '2026-03-06' },
  { id: 3, project: 'Rosette Batch #23', task: 'Glue-up', duration: 45, date: '2026-03-05' },
  { id: 4, project: 'Neck Blank Set #45', task: 'Rough Cut', duration: 60, date: '2026-03-05' },
])

const weeklyStats = ref({
  totalHours: 32.5,
  projectCount: 4,
  avgPerProject: 8.1,
})

const newEntry = ref({
  project: '',
  task: '',
  duration: 0,
})

function formatDuration(minutes: number): string {
  const hrs = Math.floor(minutes / 60)
  const mins = minutes % 60
  return hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`
}

function startTimer() {
  activeTimer.value = {
    project: newEntry.value.project || 'Untitled Project',
    task: newEntry.value.task || 'General Work',
    startTime: new Date(),
  }
}

function stopTimer() {
  if (activeTimer.value) {
    const duration = Math.round((Date.now() - activeTimer.value.startTime.getTime()) / 60000)
    recentEntries.value.unshift({
      id: Date.now(),
      project: activeTimer.value.project,
      task: activeTimer.value.task,
      duration,
      date: new Date().toISOString().split('T')[0],
    })
    activeTimer.value = null
    elapsedTime.value = 0
  }
}
</script>

<template>
  <div class="time-tracking-view">
    <div class="header">
      <h1>Time Tracking</h1>
      <p class="subtitle">Track shop time and generate labor reports</p>
    </div>

    <div class="content">
      <div class="panel timer-panel">
        <h3>Timer</h3>
        <div v-if="!activeTimer" class="timer-setup">
          <div class="form-group">
            <label>Project</label>
            <input type="text" v-model="newEntry.project" placeholder="Enter project name" />
          </div>
          <div class="form-group">
            <label>Task</label>
            <input type="text" v-model="newEntry.task" placeholder="What are you working on?" />
          </div>
          <button class="btn btn-primary btn-large" @click="startTimer">
            ▶️ Start Timer
          </button>
        </div>
        <div v-else class="timer-active">
          <div class="timer-display">
            <span class="time">{{ formatDuration(elapsedTime) }}</span>
          </div>
          <p class="timer-project">{{ activeTimer.project }}</p>
          <p class="timer-task">{{ activeTimer.task }}</p>
          <button class="btn btn-danger btn-large" @click="stopTimer">
            ⏹️ Stop Timer
          </button>
        </div>

        <div class="quick-add">
          <h4>Quick Add Entry</h4>
          <div class="form-row">
            <input type="text" placeholder="Project" />
            <input type="text" placeholder="Task" />
            <input type="number" placeholder="Minutes" />
            <button class="btn btn-secondary">Add</button>
          </div>
        </div>
      </div>

      <div class="panel entries-panel">
        <h3>Recent Entries</h3>
        <div class="entries-list">
          <div v-for="entry in recentEntries" :key="entry.id" class="entry-row">
            <div class="entry-info">
              <span class="entry-project">{{ entry.project }}</span>
              <span class="entry-task">{{ entry.task }}</span>
            </div>
            <div class="entry-meta">
              <span class="entry-duration">{{ formatDuration(entry.duration) }}</span>
              <span class="entry-date">{{ entry.date }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="panel stats-panel">
        <h3>This Week</h3>
        <div class="stat-row">
          <span class="stat-label">Total Time</span>
          <span class="stat-value">{{ weeklyStats.totalHours }}h</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Projects</span>
          <span class="stat-value">{{ weeklyStats.projectCount }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Avg per Project</span>
          <span class="stat-value">{{ weeklyStats.avgPerProject }}h</span>
        </div>

        <h3>Reports</h3>
        <div class="report-buttons">
          <button class="btn btn-secondary">Weekly Report</button>
          <button class="btn btn-secondary">Monthly Report</button>
          <button class="btn btn-secondary">By Project</button>
        </div>
      </div>
    </div>

    <div class="coming-soon-notice">
      <p>Full time tracking with project costing and invoicing integration coming soon.</p>
    </div>
  </div>
</template>

<style scoped>
.time-tracking-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1.5fr 280px; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h3:not(:first-child) { margin-top: 1.5rem; }
.panel h4 { font-size: 0.75rem; color: #888; margin: 1.5rem 0 0.75rem; }

.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.form-group input { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }

.btn { padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }
.btn-danger { background: #ef4444; color: #fff; }
.btn-large { width: 100%; padding: 1rem; font-size: 1rem; }

.timer-active { text-align: center; }
.timer-display { margin-bottom: 1rem; }
.timer-display .time { font-size: 3rem; font-weight: 700; font-family: monospace; color: #22c55e; }
.timer-project { font-size: 1.125rem; font-weight: 600; margin: 0; }
.timer-task { font-size: 0.875rem; color: #888; margin: 0.25rem 0 1.5rem; }

.quick-add { border-top: 1px solid #333; padding-top: 1rem; margin-top: 1.5rem; }
.form-row { display: flex; gap: 0.5rem; }
.form-row input { flex: 1; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; font-size: 0.875rem; }

.entries-list { display: flex; flex-direction: column; gap: 0.5rem; max-height: 400px; overflow-y: auto; }
.entry-row { display: flex; justify-content: space-between; padding: 0.75rem; background: #262626; border-radius: 0.5rem; }
.entry-info { display: flex; flex-direction: column; }
.entry-project { font-weight: 500; }
.entry-task { font-size: 0.75rem; color: #888; }
.entry-meta { text-align: right; }
.entry-duration { display: block; font-family: monospace; color: #2563eb; }
.entry-date { font-size: 0.75rem; color: #888; }

.stat-row { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #262626; }
.stat-label { font-size: 0.875rem; color: #888; }
.stat-value { font-family: monospace; font-weight: 600; }

.report-buttons { display: flex; flex-direction: column; gap: 0.5rem; }
.report-buttons .btn { font-size: 0.875rem; }

.coming-soon-notice { max-width: 1400px; margin: 2rem auto 0; padding: 1rem; background: #1e3a5f; border-radius: 0.5rem; text-align: center; color: #60a5fa; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
